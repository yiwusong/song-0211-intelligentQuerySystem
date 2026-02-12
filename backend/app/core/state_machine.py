"""查询状态机 — 编排完整查询流程

流程: SchemaRetrieval → LLMGeneration → SQLValidation → SQLExecution → ResultStreaming
校验失败自动重试，最多 3 次
"""
from __future__ import annotations

import json
from enum import Enum
from typing import AsyncGenerator
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_engine import LLMEngine
from app.rag.retriever import SchemaRetriever
from app.security.sql_firewall import SQLFirewall, SQLFirewallError
from app.security.query_limiter import QueryLimiter, QueryLimiterError
from app.db.executor import SQLExecutor, QueryResult


class QueryState(str, Enum):
    """查询状态枚举"""
    INIT = "init"
    SCHEMA_RETRIEVAL = "schema_retrieval"
    LLM_GENERATION = "llm_generation"
    SQL_VALIDATION = "sql_validation"
    SQL_EXECUTION = "sql_execution"
    RESULT_STREAMING = "result_streaming"
    COMPLETED = "completed"
    ERROR = "error"


class QueryStateMachine:
    """
    查询状态机：编排 Schema 检索 → LLM 生成 → SQL 校验 → 执行 → 结果流式输出

    通过 SSE events yield 每个阶段的结果
    """

    def __init__(
        self,
        llm_engine: LLMEngine,
        retriever: SchemaRetriever,
        firewall: SQLFirewall,
        limiter: QueryLimiter,
        executor: SQLExecutor,
        max_retries: int = 3,
    ):
        self.llm = llm_engine
        self.retriever = retriever
        self.firewall = firewall
        self.limiter = limiter
        self.executor = executor
        self.max_retries = max_retries

    async def run(
        self,
        question: str,
        session: AsyncSession,
        client_id: str = "default",
    ) -> AsyncGenerator[dict, None]:
        """
        执行完整查询流程，逐步 yield SSE 事件

        yield 的 dict 格式: {"event": str, "data": str}
        """
        state = QueryState.INIT

        # ── 速率检查 ──
        try:
            self.limiter.check_rate_limit(client_id)
        except QueryLimiterError as e:
            yield self._event("error", {"code": e.code, "message": e.message})
            return

        # ── Stage 1: Schema Retrieval ──
        state = QueryState.SCHEMA_RETRIEVAL
        yield self._event("state", {"state": state.value})

        schema_context = self.retriever.retrieve_as_context(question)
        logger.info(f"Schema 上下文长度: {len(schema_context)} 字符")

        # ── Stage 2: LLM 流式生成 ──
        state = QueryState.LLM_GENERATION
        yield self._event("state", {"state": state.value})

        full_thinking = ""
        sql = ""
        viz_config = ""
        chart_type = "bar"
        llm_error = None

        async for event_type, content in self.llm.generate_stream(question, schema_context):
            if event_type == "thinking_delta":
                yield self._event("thought", {"content": content, "done": False})
            elif event_type == "thinking_full":
                full_thinking = content
                yield self._event("thought", {"content": full_thinking, "done": True})
            elif event_type == "sql":
                sql = content
            elif event_type == "chart_type":
                chart_type = content
            elif event_type == "viz_config":
                viz_config = content
            elif event_type == "error":
                llm_error = content
                break

        if llm_error:
            yield self._event("error", json.loads(llm_error))
            return

        if not sql:
            yield self._event("thought", {"content": full_thinking or "无法为该问题生成 SQL 查询", "done": True})
            yield self._event("error", {"code": "NO_SQL", "message": "模型未生成有效 SQL"})
            return

        # ── Stage 3: SQL 校验（带重试） ──
        state = QueryState.SQL_VALIDATION
        yield self._event("state", {"state": state.value})

        safe_sql = None
        for attempt in range(self.max_retries):
            try:
                safe_sql = self.firewall.validate(sql)
                break
            except SQLFirewallError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"SQL 校验失败 (第 {attempt + 1} 次): {e.message}")
                    # TODO: 可以让 LLM 修正 SQL
                    yield self._event("thought", {
                        "content": f"SQL 校验未通过: {e.message}，尝试重新生成...",
                        "done": False,
                    })
                else:
                    yield self._event("error", {"code": e.code, "message": e.message})
                    return

        if not safe_sql:
            yield self._event("error", {"code": "VALIDATION_FAILED", "message": "SQL 校验失败"})
            return

        # 推送 SQL
        yield self._event("sql", {"content": safe_sql, "raw": sql})

        # ── Stage 4: SQL 执行 ──
        state = QueryState.SQL_EXECUTION
        yield self._event("state", {"state": state.value})

        try:
            result: QueryResult = await self.limiter.execute_with_timeout(
                self.executor.execute(session, safe_sql)
            )
        except QueryLimiterError as e:
            yield self._event("error", {"code": e.code, "message": e.message})
            return
        except Exception as e:
            logger.error(f"SQL 执行异常: {e}")
            yield self._event("error", {
                "code": "EXECUTION_ERROR",
                "message": f"查询执行失败: {str(e)}",
            })
            return

        # ── Stage 5: 结果 + 可视化 ──
        state = QueryState.RESULT_STREAMING
        yield self._event("state", {"state": state.value})

        # 推送查询结果数据
        yield self._event("data", result.to_dict())

        # 推送 LLM 推荐的图表类型
        yield self._event("chart_type", {"type": chart_type})

        # 推送可视化配置（用实际数据填充）
        if viz_config:
            try:
                echarts_option = json.loads(viz_config)
                filled_option = self._fill_echarts_data(echarts_option, result)
                yield self._event("viz_config", filled_option)
            except json.JSONDecodeError:
                logger.warning("viz_config JSON 解析失败，跳过可视化")

        # ── 完成 ──
        state = QueryState.COMPLETED
        yield self._event("state", {"state": state.value})
        yield self._event("done", {"message": "查询完成"})

    def _fill_echarts_data(self, option: dict, result: QueryResult) -> dict:
        """将查询结果填充到 ECharts option 中"""
        echarts_data = result.to_echarts_data()

        # 填充 xAxis data
        if "xAxis" in option:
            if isinstance(option["xAxis"], dict):
                option["xAxis"]["data"] = echarts_data["categories"]
            elif isinstance(option["xAxis"], list) and option["xAxis"]:
                option["xAxis"][0]["data"] = echarts_data["categories"]

        # 填充 series data
        if "series" in option and echarts_data.get("series"):
            series_values = list(echarts_data["series"].values())
            for i, series_item in enumerate(option["series"]):
                if i < len(series_values):
                    series_item["data"] = series_values[i]
                    # 如果没有 name，用列名
                    if "name" not in series_item:
                        series_keys = list(echarts_data["series"].keys())
                        if i < len(series_keys):
                            series_item["name"] = series_keys[i]

        # 如果是饼图，填充 data 为 [{name, value}] 格式
        if "series" in option:
            for series_item in option["series"]:
                if series_item.get("type") == "pie" and echarts_data.get("series"):
                    first_value_key = list(echarts_data["series"].keys())[0]
                    values = echarts_data["series"][first_value_key]
                    series_item["data"] = [
                        {"name": cat, "value": val}
                        for cat, val in zip(echarts_data["categories"], values)
                        if val is not None
                    ]

        return option

    @staticmethod
    def _event(event_type: str, data) -> dict:
        """构造 SSE 事件"""
        return {
            "event": event_type,
            "data": json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data),
        }
