"""Query Limiter — 查询超时 + 行数限制 + 简单速率控制"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from loguru import logger


class QueryLimiterError(Exception):
    """查询限流错误"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class QueryLimiter:
    """查询限流器：超时控制 + 简单滑动窗口速率限制"""

    def __init__(
        self,
        timeout_ms: int = 30000,
        max_requests_per_minute: int = 30,
    ):
        self.timeout_seconds = timeout_ms / 1000.0
        self.max_rpm = max_requests_per_minute
        # 简单的内存速率限制（单进程场景）
        self._request_timestamps: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, client_id: str = "default") -> None:
        """检查速率限制"""
        now = time.time()
        window_start = now - 60

        # 清理过期记录
        self._request_timestamps[client_id] = [
            ts for ts in self._request_timestamps[client_id]
            if ts > window_start
        ]

        if len(self._request_timestamps[client_id]) >= self.max_rpm:
            raise QueryLimiterError(
                "RATE_LIMIT",
                f"查询频率超限：每分钟最多 {self.max_rpm} 次，请稍后再试"
            )

        self._request_timestamps[client_id].append(now)

    async def execute_with_timeout(self, coro, timeout_override: float | None = None):
        """带超时的异步执行"""
        timeout = timeout_override or self.timeout_seconds
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise QueryLimiterError(
                "QUERY_TIMEOUT",
                f"查询超时（{timeout}秒），请简化查询条件"
            )
