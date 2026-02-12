"""Retriever — 根据用户问题，从 ChromaDB 中检索最相关的 Schema 信息"""
from __future__ import annotations

from loguru import logger
from app.rag.embedder import SchemaEmbedder


class SchemaRetriever:
    """语义检索：根据用户自然语言问题检索最相关的表结构"""

    def __init__(self, embedder: SchemaEmbedder):
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        检索与查询最相关的 Schema 文档

        返回: [{"id": "table_name", "text": "...", "metadata": {...}, "distance": float}]
        """
        if self.embedder.get_collection_count() == 0:
            logger.warning("ChromaDB 集合为空，无法检索")
            return []

        results = self.embedder.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.embedder.get_collection_count()),
        )

        docs = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                docs.append({
                    "id": doc_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })

        logger.info(f"检索到 {len(docs)} 个相关 Schema 文档 (query: {query[:50]}...)")
        return docs

    def retrieve_as_context(self, query: str, top_k: int = 5) -> str:
        """检索并拼接为 LLM prompt context 文本"""
        docs = self.retrieve(query, top_k)
        if not docs:
            return ""
        return "\n\n".join(d["text"] for d in docs)
