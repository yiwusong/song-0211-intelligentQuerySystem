"""依赖注入 — 数据库连接池、ChromaDB 客户端等（Phase 3 完善）"""

from app.config import get_settings


def get_db_pool():
    """获取数据库连接池（Phase 3 实现）"""
    raise NotImplementedError("数据库连接池将在 Phase 3 实现")


def get_chroma_client():
    """获取 ChromaDB 客户端（Phase 3 实现）"""
    raise NotImplementedError("ChromaDB 客户端将在 Phase 3 实现")
