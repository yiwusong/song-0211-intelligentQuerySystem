"""Schema 管理接口 — 查询索引状态 + 手动刷新"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.rag.schema_extractor import SchemaExtractor
from app.rag.embedder import SchemaEmbedder
from app.db.database import get_session

router = APIRouter()


@router.get("/api/schema/status")
async def schema_status():
    """查询 Schema 向量索引状态"""
    try:
        embedder = SchemaEmbedder()
        count = embedder.get_collection_count()
        return {
            "status": "ready" if count > 0 else "empty",
            "tables_indexed": count,
            "message": f"已索引 {count} 张表" if count > 0 else "索引为空，请刷新",
        }
    except Exception as e:
        logger.error(f"获取 Schema 状态失败: {e}")
        return {
            "status": "error",
            "tables_indexed": 0,
            "message": f"获取状态失败: {str(e)}",
        }


@router.post("/api/schema/refresh")
async def schema_refresh(session: AsyncSession = Depends(get_session)):
    """手动刷新 Schema 向量索引：重新提取表结构并重建向量"""
    try:
        extractor = SchemaExtractor()
        embedder = SchemaEmbedder()

        # 重置向量集合
        embedder.reset()

        # 重新提取 Schema
        tables = await extractor.extract(session)

        if not tables:
            return {
                "status": "warning",
                "tables_indexed": 0,
                "message": "未提取到任何表结构，请检查数据库连接",
            }

        # 重新索引
        docs = extractor.format_for_embedding(tables)
        count = embedder.index_documents(docs)

        logger.info(f"Schema 索引刷新完成: {count} 张表")
        return {
            "status": "refreshed",
            "tables_indexed": count,
            "tables": [t["table_name"] for t in tables],
            "message": f"成功刷新 {count} 张表的向量索引",
        }

    except Exception as e:
        logger.error(f"Schema 刷新失败: {e}")
        return {
            "status": "error",
            "tables_indexed": 0,
            "message": f"刷新失败: {str(e)}",
        }


@router.get("/api/schema/tables")
async def schema_tables(session: AsyncSession = Depends(get_session)):
    """获取数据库中所有表的详细结构信息"""
    try:
        extractor = SchemaExtractor()
        tables = await extractor.extract(session)

        return {
            "status": "ok",
            "table_count": len(tables),
            "tables": tables,
        }

    except Exception as e:
        logger.error(f"获取表结构失败: {e}")
        return {
            "status": "error",
            "table_count": 0,
            "tables": [],
            "message": f"获取失败: {str(e)}",
        }
