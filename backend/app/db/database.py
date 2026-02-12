"""Database — 异步 PostgreSQL 连接池管理"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger

from app.config import get_settings


# 模块级别变量
_engine = None
_session_factory = None


async def init_db():
    """初始化数据库引擎和会话工厂"""
    global _engine, _session_factory

    settings = get_settings()
    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        # 只读：在连接级别设置 default_transaction_read_only
        connect_args={
            "server_settings": {
                "default_transaction_read_only": "on"
            }
        }
    )
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info(f"数据库引擎已初始化: {settings.DATABASE_URL.split('@')[-1]}")


async def close_db():
    """关闭数据库连接池"""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("数据库连接池已关闭")


async def get_session() -> AsyncSession:
    """获取一个异步数据库会话"""
    if _session_factory is None:
        raise RuntimeError("数据库尚未初始化，请先调用 init_db()")
    async with _session_factory() as session:
        yield session


def get_engine():
    """获取数据库引擎（用于原始连接）"""
    if _engine is None:
        raise RuntimeError("数据库尚未初始化，请先调用 init_db()")
    return _engine
