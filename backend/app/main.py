"""FastAPI 应用入口 — CORS 配置 + 路由挂载 + 生命周期管理"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.api.routes import health, query, schema
from app.db.database import init_db, close_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ---- Startup ----
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info(f"📡 CORS 允许来源: {settings.CORS_ORIGINS}")
    logger.info(f"🤖 LLM 模型: {settings.OPENAI_MODEL}")

    # 初始化数据库
    try:
        await init_db()
        logger.info("✅ 数据库连接池已初始化")

        # 初始化 Schema 索引
        await _init_schema_index()
    except Exception as e:
        logger.warning(f"⚠️ 数据库初始化失败（Mock 模式仍可用）: {e}")

    yield

    # ---- Shutdown ----
    logger.info("👋 服务关闭中...")
    await close_db()


async def _init_schema_index():
    """启动时提取 Schema 并构建向量索引"""
    from app.db.database import get_engine
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from app.rag.schema_extractor import SchemaExtractor
    from app.rag.embedder import SchemaEmbedder

    engine = get_engine()
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        extractor = SchemaExtractor()
        tables = await extractor.extract(session)

        if tables:
            embedder = SchemaEmbedder()
            docs = extractor.format_for_embedding(tables)
            count = embedder.index_documents(docs)
            logger.info(f"✅ Schema 向量索引已构建: {count} 个文档")
        else:
            logger.warning("⚠️ 未提取到任何表结构")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自然语言驱动的智能 SQL 查询与数据可视化系统",
    lifespan=lifespan,
)

# ---- CORS 中间件 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 挂载路由 ----
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, tags=["Query"])
app.include_router(schema.router, tags=["Schema"])
