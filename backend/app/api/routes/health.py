"""健康检查接口 — 含数据库连通性检测"""

from fastapi import APIRouter
from loguru import logger
from sqlalchemy import text

from app.config import get_settings
from app.db.database import get_engine
from app.rag.embedder import SchemaEmbedder

router = APIRouter()


@router.get("/health")
async def health_check():
    """服务健康检查（含数据库 + ChromaDB 状态）"""
    settings = get_settings()

    result = {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model": settings.OPENAI_MODEL,
        "database": "unknown",
        "schema_index": "unknown",
    }

    # 检查数据库
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        result["database"] = "connected"
    except Exception as e:
        result["database"] = f"disconnected: {str(e)[:100]}"
        result["status"] = "degraded"

    # 检查 ChromaDB
    try:
        embedder = SchemaEmbedder()
        count = embedder.get_collection_count()
        result["schema_index"] = f"ready ({count} tables)"
    except Exception as e:
        result["schema_index"] = f"error: {str(e)[:100]}"
        result["status"] = "degraded"

    return result
