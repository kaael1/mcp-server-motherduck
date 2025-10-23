import logging
import json
import os
from pydantic import AnyUrl
from typing import Literal
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .configs import SERVER_VERSION
from .database import DatabaseClient
from .prompt import PROMPT_TEMPLATE


logger = logging.getLogger("mcp_server_motherduck")


def build_application(
    db_path: str,
    motherduck_token: str | None = None,
    home_dir: str | None = None,
    saas_mode: bool = False,
    read_only: bool = False,
):
    logger.info("Starting MotherDuck MCP Server")
    server = Server("mcp-server-motherduck")
    db_client = DatabaseClient(
        db_path=db_path,
        motherduck_token=motherduck_token,
        home_dir=home_dir,
        saas_mode=saas_mode,
        read_only=read_only,
    )

    logger.info("Registering handlers")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """
        List available note resources.
        Each note is exposed as a resource with a custom note:// URI scheme.
        """
        logger.info("No resources available to list")
        return []

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        """
        Read a specific note's content by its URI.
        The note name is extracted from the URI host component.
        """
        logger.info(f"Reading resource: {uri}")
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """
        List available prompts.
        Each prompt can have optional arguments to customize its behavior.
        """
        logger.info("Listing prompts")
        # TODO: Check where and how this is used, and how to optimize this.
        # Check postgres and sqlite servers.
        return [
            types.Prompt(
                name="duckdb-motherduck-initial-prompt",
                description="A prompt to initialize a connection to duckdb or motherduck and start working with it",
            )
        ]

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        """
        Generate a prompt by combining arguments with server state.
        The prompt includes all current notes and can be customized via arguments.
        """
        logger.info(f"Getting prompt: {name}::{arguments}")
        # TODO: Check where and how this is used, and how to optimize this.
        # Check postgres and sqlite servers.
        if name != "duckdb-motherduck-initial-prompt":
            raise ValueError(f"Unknown prompt: {name}")

        return types.GetPromptResult(
            description="Initial prompt for interacting with DuckDB/MotherDuck",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=PROMPT_TEMPLATE),
                )
            ],
        )

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        logger.info("Listing tools")
        return [
            types.Tool(
                name="query",
                description="Use this to execute a query on the MotherDuck or DuckDB database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute that is a dialect of DuckDB SQL. Use {{file}} or sheet name directly in FROM clause.",
                        },
                        "fileId": {
                            "type": "string",
                            "description": "Optional file ID for Excel file analysis.",
                        },
                        "sheet": {
                            "type": "string",
                            "description": "Optional sheet name for Excel files. If not provided, uses first sheet.",
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="discover_structure",
                description="Discover schema and structure of Excel sheets with sample data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fileId": {
                            "type": "string",
                            "description": "File ID of the uploaded Excel file",
                        },
                        "sheet": {
                            "type": "string",
                            "description": "Sheet name to analyze, or '*' for all sheets",
                            "default": "*",
                        },
                        "sampleRows": {
                            "type": "integer",
                            "description": "Number of sample rows to return",
                            "default": 5,
                        },
                    },
                    "required": ["fileId"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        Tools can modify server state and notify clients of changes.
        """
        logger.info(f"🔧 Tool received: {name}")
        try:
            if name == "query":
                if arguments is None:
                    return [
                        types.TextContent(type="text", text="Error: No query provided")
                    ]
                
                query = arguments["query"]
                file_id = arguments.get("fileId")
                sheet = arguments.get("sheet")
                
                # Se fileId fornecido, substituir placeholder
                if file_id:
                    excel_files_path = os.getenv("EXCEL_FILES_PATH", "/app/excel_files")
                    file_path = os.path.join(excel_files_path, f"{file_id}.xlsx")
                    file_path = file_path.replace("\\", "/")
                    
                    if not os.path.exists(file_path):
                        logger.error(f"❌ File not found: {file_path}")
                        try:
                            files_in_dir = os.listdir(excel_files_path)
                            logger.error(f"📂 Files in directory: {files_in_dir}")
                        except Exception as e:
                            logger.error(f"📂 Cannot list directory: {e}")
                        
                        error_response = {
                            "success": False,
                            "error": f"File not found: {file_id}",
                            "query": query,
                            "data": [],
                            "columns": [],
                            "rowCount": 0
                        }
                        return [types.TextContent(type="text", text=json.dumps(error_response))]
                    
                    # Se sheet especificada, construir query read_xlsx completa
                    if sheet:
                        # Substituir "FROM sheet_name" por read_xlsx call
                        import re
                        pattern = rf'FROM\s+["\']?{re.escape(sheet)}["\']?'
                        replacement = f"FROM read_xlsx('{file_path}', sheet='{sheet}', all_varchar=true, ignore_errors=true)"
                        query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
                        logger.info(f"📊 Executing query with sheet: {sheet}")
                    else:
                        # Substituir {{file}} placeholder
                        query = query.replace("{{file}}", file_path)
                    
                    logger.info(f"📁 Executing query with file: {file_path}")
                
                # Executar query
                tool_response = db_client.query_json(query)
                
                logger.info(f"✅ Query executed: {tool_response.get('rowCount', 0)} rows")
                
                # Converter dict para JSON string
                response_text = json.dumps(tool_response, indent=2)
                
                return [types.TextContent(type="text", text=response_text)]

            elif name == "discover_structure":
                if arguments is None:
                    return [types.TextContent(type="text", text="Error: No fileId provided")]
                
                file_id = arguments.get("fileId")
                sheet = arguments.get("sheet", "*")
                sample_rows = arguments.get("sampleRows", 5)
                
                if not file_id:
                    return [types.TextContent(type="text", text="Error: fileId is required")]
                
                excel_files_path = os.getenv("EXCEL_FILES_PATH", "/app/excel_files")
                file_path = os.path.join(excel_files_path, f"{file_id}.xlsx")
                file_path = file_path.replace("\\", "/")
                
                logger.info(f"🔍 Discovering structure for file: {file_id}, sheet: {sheet}")
                
                result = db_client.discover_excel_structure(file_path, sheet, sample_rows)
                
                response_text = json.dumps(result, indent=2)
                return [types.TextContent(type="text", text=response_text)]

            return [types.TextContent(type="text", text=f"Unsupported tool: {name}")]

        except Exception as e:
            logger.error(f"❌ Error executing tool {name}: {e}", exc_info=True)
            raise ValueError(f"Error executing tool {name}: {str(e)}")

    initialization_options = InitializationOptions(
        server_name="motherduck",
        server_version=SERVER_VERSION,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    return server, initialization_options
