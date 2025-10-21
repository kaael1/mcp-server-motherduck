import anyio
import logging
import click
from .server import build_application
from .configs import SERVER_VERSION, SERVER_LOCALHOST, UVICORN_LOGGING_CONFIG

__version__ = SERVER_VERSION

logger = logging.getLogger("mcp_server_motherduck")
logging.basicConfig(
    level=logging.INFO, format="[motherduck] %(levelname)s - %(message)s"
)


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "stream"]),
    default="stdio",
    help="(Default: `stdio`) Transport type",
)
@click.option(
    "--db-path",
    default="md:",
    help="(Default: `md:`) Path to local DuckDB database file or MotherDuck database",
)
@click.option(
    "--motherduck-token",
    default=None,
    help="(Default: env var `motherduck_token`) Access token to use for MotherDuck database connections",
)
@click.option(
    "--home-dir",
    default=None,
    help="(Default: env var `HOME`) Home directory for DuckDB",
)
@click.option(
    "--saas-mode",
    is_flag=True,
    help="Flag for connecting to MotherDuck in SaaS mode",
)
@click.option(
    "--read-only",
    is_flag=True,
    help="Flag for connecting to DuckDB in read-only mode. Only supported for local DuckDB databases. Also makes use of short lived connections so multiple MCP clients or other systems can remain active (though each operation must be done sequentially).",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="(Default: `False`) Enable JSON responses instead of SSE streams. Only supported for `stream` transport.",
)
def main(
    port,
    transport,
    db_path,
    motherduck_token,
    home_dir,
    saas_mode,
    read_only,
    json_response,
):
    """Main entry point for the package."""

    logger.info("🦆 MotherDuck MCP Server v" + SERVER_VERSION)
    logger.info("Ready to execute SQL queries via DuckDB/MotherDuck")

    app, init_opts = build_application(
        db_path=db_path,
        motherduck_token=motherduck_token,
        home_dir=home_dir,
        saas_mode=saas_mode,
        read_only=read_only,
    )

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        logger.info("MCP server initialized in \033[32msse\033[0m mode")

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await app.run(read_stream, write_stream, init_opts)
            return Response()

        logger.info(
            f"🦆 Connect to MotherDuck MCP Server at \033[1m\033[36mhttp://{SERVER_LOCALHOST}:{port}/sse\033[0m"
        )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(
            starlette_app,
            host=SERVER_LOCALHOST,
            port=port,
            log_config=UVICORN_LOGGING_CONFIG,
        )

    elif transport == "stream":
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from collections.abc import AsyncIterator
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.types import Receive, Scope, Send
        from starlette.responses import JSONResponse, FileResponse
        from fastapi import UploadFile, File, HTTPException
        import contextlib
        import os
        import uuid
        import json
        from .auth import AuthMiddleware, setup_cors, get_auth_token, get_allowed_origins

        logger.info("MCP server initialized in \033[32mhttp-streamable\033[0m mode")

        # Create the session manager with true stateless mode
        session_manager = StreamableHTTPSessionManager(
            app=app,
            event_store=None,
            json_response=json_response,
            stateless=True,
        )

        async def handle_streamable_http(
            scope: Scope, receive: Receive, send: Send
        ) -> None:
            await session_manager.handle_request(scope, receive, send)

        # Health check endpoint (no authentication required)
        async def health_check(request):
            return JSONResponse({
                "status": "ok",
                "service": "duckdb-mcp-server",
                "version": SERVER_VERSION
            })

        # Upload Excel file endpoint
        async def upload_excel(request):
            try:
                # Get form data
                form = await request.form()
                file = form.get("file")
                
                if not file:
                    raise HTTPException(status_code=400, detail="No file provided")
                
                # Validate file format
                if not file.filename.endswith(('.xlsx', '.xls')):
                    raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are supported")
                
                # Read file content
                content = await file.read()
                
                # Validate file size (max 50MB)
                max_size = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB default
                if len(content) > max_size:
                    raise HTTPException(status_code=400, detail=f"File size exceeds {max_size // (1024*1024)}MB limit")
                
                # Generate unique file ID
                file_id = str(uuid.uuid4())
                
                # Create directory if it doesn't exist
                # Use /app/excel_files for Railway persistence instead of /tmp
                excel_files_path = os.getenv("EXCEL_FILES_PATH", "/app/excel_files")
                os.makedirs(excel_files_path, exist_ok=True)
                
                # Log directory creation for debug
                logger.info(f"📁 Excel files directory: {excel_files_path}")
                logger.info(f"📁 Directory exists: {os.path.exists(excel_files_path)}")
                logger.info(f"📁 Directory writable: {os.access(excel_files_path, os.W_OK)}")
                
                # Save file
                file_path = os.path.join(excel_files_path, f"{file_id}.xlsx")
                # Normalize path separators for DuckDB compatibility
                file_path = file_path.replace("\\", "/")
                with open(file_path, "wb") as f:
                    f.write(content)
                
                logger.info(f"File uploaded: {file.filename} -> {file_id}")
                
                return JSONResponse({
                    "fileId": file_id,
                    "filename": file.filename,
                    "path": file_path,
                    "size": len(content)
                })
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

        # Download Excel file endpoint
        async def download_excel(request):
            file_id = request.path_params.get("file_id")
            if not file_id:
                raise HTTPException(status_code=400, detail="File ID is required")
            
            excel_files_path = os.getenv("EXCEL_FILES_PATH", "/tmp/excel_files")
            file_path = os.path.join(excel_files_path, f"{file_id}.xlsx")
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileResponse(
                file_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=f"result_{file_id}.xlsx"
            )

        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            """Context manager for session manager."""
            async with session_manager.run():
                logger.info("MCP server started with StreamableHTTP session manager")
                try:
                    yield
                finally:
                    logger.info(
                        "🦆 MotherDuck MCP Server in \033[32mhttp-streamable\033[0m mode shutting down"
                    )

        logger.info(
            f"🦆 Connect to MotherDuck MCP Server at \033[1m\033[36mhttp://{SERVER_LOCALHOST}:{port}/mcp\033[0m"
        )

        # Create an ASGI application using the transport
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/health", endpoint=health_check, methods=["GET"]),
                Route("/upload", endpoint=upload_excel, methods=["POST"]),
                Route("/download/{file_id:str}", endpoint=download_excel, methods=["GET"]),
                Mount("/mcp", app=handle_streamable_http),
            ],
            lifespan=lifespan,
        )

        # Setup authentication and CORS
        try:
            auth_token = get_auth_token()
            starlette_app.add_middleware(AuthMiddleware, auth_token=auth_token)
            logger.info("Authentication middleware configured")
        except ValueError as e:
            logger.warning(f"Authentication not configured: {e}")
        
        setup_cors(starlette_app, get_allowed_origins())

        import uvicorn
        
        # Use PORT environment variable if available (Railway provides this)
        railway_port = os.getenv("PORT")
        if railway_port:
            port = int(railway_port)
            logger.info(f"Using Railway PORT: {port}")

        # Force 0.0.0.0 for Railway deployment
        host = "0.0.0.0"
        logger.info(f"Starting server on {host}:{port}")
        
        uvicorn.run(
            starlette_app,
            host=host,
            port=port,
            log_config=UVICORN_LOGGING_CONFIG,
        )

    else:
        from mcp.server.stdio import stdio_server

        logger.info("MCP server initialized in \033[32mstdio\033[0m mode")
        logger.info("Waiting for client connection")

        async def arun():
            async with stdio_server() as (read_stream, write_stream):
                await app.run(read_stream, write_stream, init_opts)

        anyio.run(arun)
        # This will only be reached when the server is shutting down
        logger.info(
            "🦆 MotherDuck MCP Server in \033[32mstdio\033[0m mode shutting down"
        )


# Optionally expose other important items at package level
__all__ = ["main"]

if __name__ == "__main__":
    main()
