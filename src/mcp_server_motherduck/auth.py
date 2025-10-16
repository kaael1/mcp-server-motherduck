import os
import logging
from typing import Optional
from fastapi import HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("mcp_server_motherduck")


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticação Bearer Token"""
    
    def __init__(self, app, auth_token: str):
        super().__init__(app)
        self.auth_token = auth_token
    
    async def dispatch(self, request: Request, call_next):
        # Rotas que não precisam de autenticação
        public_routes = ["/health", "/docs", "/openapi.json", "/redoc"]
        
        # Normalizar path (remover trailing slash)
        path = request.url.path.rstrip('/')
        
        if path in public_routes:
            return await call_next(request)
        
        # Verificar Authorization header (case insensitive)
        authorization = request.headers.get("authorization") or request.headers.get("Authorization")
        
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning(f"Missing or invalid Authorization header for {request.url.path}")
            return Response(
                content='{"error": "Missing or invalid Authorization header"}',
                status_code=401,
                media_type="application/json"
            )
        
        token = authorization.replace("Bearer ", "")
        if token != self.auth_token:
            logger.warning(f"Invalid token for {request.url.path}")
            return Response(
                content='{"error": "Invalid token"}',
                status_code=401,
                media_type="application/json"
            )
        
        return await call_next(request)


def setup_cors(app, allowed_origins: Optional[str] = None):
    """Configurar CORS para o aplicativo"""
    
    if allowed_origins:
        origins = [origin.strip() for origin in allowed_origins.split(",")]
    else:
        # Origens padrão
        origins = [
            "https://quati.ai",
            "https://*.vercel.app",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3010"
        ]
    
    # Sempre adicionar localhost:3010 para testes
    if "http://localhost:3010" not in origins:
        origins.append("http://localhost:3010")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS configurado para origens: {origins}")


def get_auth_token() -> str:
    """Obter token de autenticação das variáveis de ambiente"""
    token = os.getenv("AUTH_TOKEN")
    if not token:
        raise ValueError("AUTH_TOKEN environment variable is required")
    return token


def get_allowed_origins() -> Optional[str]:
    """Obter origens permitidas das variáveis de ambiente"""
    return os.getenv("ALLOWED_ORIGINS")
