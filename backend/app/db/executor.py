"""SQL Executor — 安全执行查询并返回结构化结果"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


class QueryResult:
    """查询结果封装"""

    def __init__(
        self,
        columns: list[str],
        rows: list[list],
        row_count: int,
        execution_time_ms: float,
    ):
        self.columns = columns
        self.rows = rows
        self.row_count = row_count
        self.execution_time_ms = execution_time_ms

    def to_dict(self) -> dict:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "execution_time_ms": round(self.execution_time_ms, 2),
        }

    def to_echarts_data(self) -> dict:
        """转换为 ECharts 友好的数据格式"""
        if not self.rows:
            return {"categories": [], "values": []}

        # 第一列作为分类轴，后续列作为数值
        categories = [str(row[0]) for row in self.rows]
        series_data = {}

        for i, col in enumerate(self.columns[1:], start=1):
            series_data[col] = [row[i] if i < len(row) else None for row in self.rows]

        return {
            "categories": categories,
            "series": series_data,
        }


class SQLExecutor:
    """安全的 SQL 执行器"""

    async def execute(self, session: AsyncSession, sql: str) -> QueryResult:
        """
        执行 SQL 并返回结构化结果

        注意: SQL 应该已经通过 SQLFirewall 验证
        """
        import time
        start = time.perf_counter()

        try:
            result = await session.execute(text(sql))
            elapsed_ms = (time.perf_counter() - start) * 1000

            columns = list(result.keys())
            rows = []
            for row in result.fetchall():
                # 将每行转为 JSON-serializable 的 list
                rows.append([self._serialize_value(v) for v in row])

            logger.info(f"SQL 执行完成: {len(rows)} 行, {elapsed_ms:.1f}ms")

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(f"SQL 执行失败 ({elapsed_ms:.1f}ms): {e}")
            raise

    @staticmethod
    def _serialize_value(value):
        """将数据库值转为 JSON 可序列化格式"""
        if value is None:
            return None
        if isinstance(value, (int, float, str, bool)):
            return value
        # Decimal -> float
        from decimal import Decimal
        if isinstance(value, Decimal):
            return float(value)
        # datetime -> ISO string
        from datetime import datetime, date
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        # 其他类型转字符串
        return str(value)
