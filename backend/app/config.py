"""全局配置 — 基于 Pydantic Settings，从 .env 文件读取环境变量"""
from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # ---- 项目信息 ----
    APP_NAME: str = "松哥的智能数据分析系统"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ---- LLM ----
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.2-chat"

    # ---- PostgreSQL ----
    DATABASE_URL: str = "postgresql+asyncpg://readonly_user:password@localhost:5432/demo_ecommerce"

    # ---- ChromaDB ----
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ---- Server ----
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ---- Security ----
    SQL_MAX_ROWS: int = 1000
    SQL_TIMEOUT_MS: int = 30000
    SQL_MAX_RETRIES: int = 3

    # ---- CORS ----
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """缓存配置单例"""
    return Settings()
