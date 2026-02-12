"""Embedder — 使用 sentence-transformers 生成向量，存入 ChromaDB"""
from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from app.config import get_settings


COLLECTION_NAME = "schema_embeddings"


class SchemaEmbedder:
    """Schema 向量化 + ChromaDB 存储管理"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.Client(ChromaSettings(
            anonymized_telemetry=False,
            persist_directory=settings.CHROMA_PERSIST_DIR,
            is_persistent=True,
        ))
        # 使用 ChromaDB 内置的 default embedding function
        # （内部会使用 all-MiniLM-L6-v2）
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def index_documents(self, docs: list[dict]) -> int:
        """
        批量索引文档到 ChromaDB

        docs: [{"id": "table_name", "text": "...", "metadata": {...}}]
        返回: 索引的文档数量
        """
        if not docs:
            return 0

        ids = [d["id"] for d in docs]
        documents = [d["text"] for d in docs]
        metadatas = [d["metadata"] for d in docs]

        # upsert: 如果已存在则更新
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"已索引 {len(docs)} 个 Schema 文档到 ChromaDB")
        return len(docs)

    def get_collection_count(self) -> int:
        """获取当前集合中的文档数量"""
        return self.collection.count()

    def reset(self):
        """清空并重建集合"""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB 集合已重置")
