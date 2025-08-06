"""
Uygulama yapılandırması ve ayarları
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    
    # App Settings
    APP_NAME: str = "AI Satış Stratejisi Projesi"
    VERSION: str = "1.0.0"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # MCP & A2A Settings (PRD'de belirtilen)
    MCP_NODE_URL: str = os.getenv("MCP_NODE_URL", "")
    MCP_CONTEXT_STORE: str = os.getenv("MCP_CONTEXT_STORE", "")
    A2A_ORCHESTRATOR_URL: str = os.getenv("A2A_ORCHESTRATOR_URL", "")
    A2A_AGENT_TIMEOUT: int = int(os.getenv("A2A_AGENT_TIMEOUT", "30"))
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra env vars not explicitly defined


# Global settings instance
settings = Settings() 