"""核心查询接口 — SSE 流式响应，全链路串联"""

import json
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.state_machine import QueryStateMachine
from app.core.llm_engine import LLMEngine
from app.rag.embedder import SchemaEmbedder
from app.rag.retriever import SchemaRetriever
from app.security.sql_firewall import SQLFirewall
from app.security.query_limiter import QueryLimiter
from app.db.executor import SQLExecutor
from app.db.database import get_session
from app.config import get_settings

router = APIRouter()


class QueryRequest(BaseModel):
    """查询请求体"""
    question: str


def _build_state_machine() -> QueryStateMachine:
    """构建查询状态机实例（含全部依赖）"""
    settings = get_settings()

    llm = LLMEngine()
    embedder = SchemaEmbedder()
    retriever = SchemaRetriever(embedder)
    firewall = SQLFirewall(max_rows=settings.SQL_MAX_ROWS)
    limiter = QueryLimiter(
        timeout_ms=settings.SQL_TIMEOUT_MS,
        max_requests_per_minute=30,
    )
    executor = SQLExecutor()

    return QueryStateMachine(
        llm_engine=llm,
        retriever=retriever,
        firewall=firewall,
        limiter=limiter,
        executor=executor,
        max_retries=settings.SQL_MAX_RETRIES,
    )


async def _sse_event_generator(question: str, session: AsyncSession):
    """SSE 事件生成器 — 驱动状态机并 yield 事件"""
    sm = _build_state_machine()

    async for event in sm.run(question, session):
        yield event


@router.post("/api/query")
async def query(request: QueryRequest, session: AsyncSession = Depends(get_session)):
    """自然语言查询接口 — 返回 SSE 事件流"""
    logger.info(f"收到查询: {request.question[:100]}")

    return EventSourceResponse(
        _sse_event_generator(request.question, session),
        media_type="text/event-stream",
    )


# ── Mock 模式（用于前端开发测试，无需数据库） ──

# 多场景 Mock 数据
MOCK_SCENARIOS = {
    "城市": {
        "thinking": "用户想查询各城市的用户分布情况。\n\n1. 选择 users 表作为主表\n2. 按 city 字段分组统计\n3. 按用户数降序排列\n4. 分类对比型数据，推荐使用柱形图展示",
        "chart_type": "bar",
        "sql": "SELECT city, COUNT(*) AS user_count FROM users GROUP BY city ORDER BY user_count DESC LIMIT 100",
        "data": {
            "columns": ["city", "user_count"],
            "rows": [
                ["北京", 68], ["上海", 62], ["广州", 55], ["深圳", 53],
                ["杭州", 49], ["成都", 47], ["武汉", 44], ["南京", 42],
                ["重庆", 40], ["西安", 40],
            ],
            "row_count": 10,
            "execution_time_ms": 8.3,
        },
        "viz": {
            "title": {"text": "各城市用户分布", "textStyle": {"color": "#f1f5f9"}},
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "重庆", "西安"],
                "axisLabel": {"color": "#94a3b8"},
            },
            "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#1e293b"}}},
            "series": [{"type": "bar", "data": [68, 62, 55, 53, 49, 47, 44, 42, 40, 40], "name": "用户数",
                        "itemStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                                 "colorStops": [{"offset": 0, "color": "#6366f1"}, {"offset": 1, "color": "#4f46e5"}]},
                                       "borderRadius": [4, 4, 0, 0]}}],
        },
    },
    "热销": {
        "thinking": "用户想查询热销商品排行。\n\n1. 关联 order_items 和 products 表\n2. 按销售数量汇总\n3. 取 TOP10 排序\n4. 分类对比型数据，推荐使用柱形图展示",
        "chart_type": "bar",
        "sql": "SELECT p.name, SUM(oi.quantity) AS total_sold, SUM(oi.quantity * oi.unit_price) AS revenue FROM order_items oi JOIN products p ON p.id = oi.product_id GROUP BY p.name ORDER BY total_sold DESC LIMIT 10",
        "data": {
            "columns": ["name", "total_sold", "revenue"],
            "rows": [
                ["智能手机 A1B2", 856, 2145800.00], ["无线耳机 C3D4", 742, 185500.00],
                ["笔记本电脑 E5F6", 623, 3115000.00], ["运动T恤 G7H8", 598, 89700.00],
                ["智能手表 I9J0", 534, 801000.00], ["蓝牙音箱 K1L2", 487, 243500.00],
                ["充电宝 M3N4", 456, 68400.00], ["机械键盘 O5P6", 423, 253800.00],
                ["瑜伽垫 Q7R8", 398, 39800.00], ["进口咖啡 S9T0", 376, 112800.00],
            ],
            "row_count": 10,
            "execution_time_ms": 15.7,
        },
        "viz": {
            "title": {"text": "热销商品 TOP10", "textStyle": {"color": "#f1f5f9"}},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "20%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#1e293b"}}},
            "yAxis": {
                "type": "category",
                "data": ["进口咖啡", "瑜伽垫", "机械键盘", "充电宝", "蓝牙音箱", "智能手表", "运动T恤", "笔记本电脑", "无线耳机", "智能手机"],
                "axisLabel": {"color": "#94a3b8"},
            },
            "series": [{"type": "bar", "data": [376, 398, 423, 456, 487, 534, 598, 623, 742, 856], "name": "销量",
                        "itemStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 0,
                                                 "colorStops": [{"offset": 0, "color": "#4f46e5"}, {"offset": 1, "color": "#22c55e"}]},
                                       "borderRadius": [0, 4, 4, 0]}}],
        },
    },
    "订单状态": {
        "thinking": "用户想查询订单状态的统计分布。\n\n1. 选择 orders 表\n2. 按 status 字段分组统计\n3. 按数量降序排列\n4. 占比分布型数据，推荐使用饼状图展示",
        "chart_type": "pie",
        "sql": "SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status ORDER BY cnt DESC LIMIT 100",
        "data": {
            "columns": ["status", "cnt"],
            "rows": [["completed", 1234], ["paid", 987], ["shipped", 654], ["pending", 321], ["cancelled", 123]],
            "row_count": 5,
            "execution_time_ms": 6.1,
        },
        "viz": {
            "title": {"text": "订单状态统计", "textStyle": {"color": "#f1f5f9"}},
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "legend": {"orient": "vertical", "right": "5%", "top": "center", "textStyle": {"color": "#94a3b8"}},
            "series": [{"type": "pie", "radius": ["40%", "70%"], "center": ["40%", "50%"],
                        "data": [
                            {"name": "completed", "value": 1234, "itemStyle": {"color": "#22c55e"}},
                            {"name": "paid", "value": 987, "itemStyle": {"color": "#6366f1"}},
                            {"name": "shipped", "value": 654, "itemStyle": {"color": "#3b82f6"}},
                            {"name": "pending", "value": 321, "itemStyle": {"color": "#f59e0b"}},
                            {"name": "cancelled", "value": 123, "itemStyle": {"color": "#ef4444"}},
                        ],
                        "label": {"color": "#94a3b8"}}],
        },
    },
    "销售趋势": {
        "thinking": "用户想查询近30天的销售趋势。\n\n1. 选择 orders 表\n2. 按天聚合，统计订单量和销售额\n3. 过滤最近30天的数据\n4. 时间趋势型数据，推荐使用曲线图展示",
        "sql": "SELECT DATE_TRUNC('day', created_at)::date AS date, COUNT(*) AS order_count, SUM(total_amount) AS total_sales FROM orders WHERE created_at >= NOW() - INTERVAL '30 days' GROUP BY date ORDER BY date ASC LIMIT 100",
        "chart_type": "line",
        "data": {
            "columns": ["date", "order_count", "total_sales"],
            "rows": [[f"2026-01-{13+i}", 120 + i * 5 + (i % 3) * 15, round(55000 + i * 2000 + (i % 4) * 8000, 2)] for i in range(30)],
            "row_count": 30,
            "execution_time_ms": 18.2,
        },
        "viz": {
            "title": {"text": "近30天销售趋势", "textStyle": {"color": "#f1f5f9"}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
            "legend": {"data": ["销售额", "订单数"], "textStyle": {"color": "#94a3b8"}, "top": 30},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "top": 70, "containLabel": True},
            "xAxis": {"type": "category",
                       "data": [f"1/{13+i}" for i in range(30)],
                       "axisLabel": {"color": "#94a3b8", "rotate": 45, "fontSize": 10}},
            "yAxis": [
                {"type": "value", "name": "销售额", "nameTextStyle": {"color": "#94a3b8"},
                 "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "#1e293b"}}},
                {"type": "value", "name": "订单数", "nameTextStyle": {"color": "#94a3b8"},
                 "axisLabel": {"color": "#94a3b8"}, "splitLine": {"show": False}},
            ],
            "series": [
                {"name": "销售额", "type": "line",
                 "data": [round(55000 + i * 2000 + (i % 4) * 8000, 2) for i in range(30)],
                 "smooth": True, "itemStyle": {"color": "#6366f1"}, "lineStyle": {"width": 2},
                 "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                          "colorStops": [{"offset": 0, "color": "rgba(99, 102, 241, 0.3)"},
                                                         {"offset": 1, "color": "rgba(99, 102, 241, 0)"}]}}},
                {"name": "订单数", "type": "line", "yAxisIndex": 1,
                 "data": [120 + i * 5 + (i % 3) * 15 for i in range(30)],
                 "smooth": True, "itemStyle": {"color": "#22c55e"}, "lineStyle": {"width": 2},
                 "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                          "colorStops": [{"offset": 0, "color": "rgba(34, 197, 94, 0.3)"},
                                                         {"offset": 1, "color": "rgba(34, 197, 94, 0)"}]}}},
            ],
        },
    },
}


def _match_mock_scenario(question: str) -> dict:
    """根据问题关键词匹配 Mock 场景"""
    q = question.lower()
    if any(kw in q for kw in ["城市", "用户分布", "地区", "地域"]):
        return MOCK_SCENARIOS["城市"]
    if any(kw in q for kw in ["热销", "top", "排行", "畅销", "销量"]):
        return MOCK_SCENARIOS["热销"]
    if any(kw in q for kw in ["状态", "订单统计", "订单分布"]):
        return MOCK_SCENARIOS["订单状态"]
    # 默认返回销售趋势
    return MOCK_SCENARIOS["销售趋势"]


async def _mock_event_generator(question: str):
    """Mock SSE 事件生成器 — 根据问题匹配不同模拟数据"""
    scenario = _match_mock_scenario(question)

    yield {"event": "state", "data": json.dumps({"state": "schema_retrieval"})}
    await asyncio.sleep(0.3)

    yield {"event": "state", "data": json.dumps({"state": "llm_generation"})}

    # 流式 thinking（逐字推送）
    thinking_text = scenario["thinking"]
    for char in thinking_text:
        yield {
            "event": "thought",
            "data": json.dumps({"content": char, "done": False}, ensure_ascii=False),
        }
        await asyncio.sleep(0.02)

    yield {
        "event": "thought",
        "data": json.dumps({"content": thinking_text, "done": True}, ensure_ascii=False),
    }
    await asyncio.sleep(0.2)

    yield {"event": "state", "data": json.dumps({"state": "sql_validation"})}
    await asyncio.sleep(0.2)

    yield {
        "event": "sql",
        "data": json.dumps({"content": scenario["sql"], "raw": scenario["sql"]}, ensure_ascii=False),
    }
    await asyncio.sleep(0.3)

    yield {"event": "state", "data": json.dumps({"state": "sql_execution"})}
    await asyncio.sleep(0.3)

    yield {
        "event": "data",
        "data": json.dumps(scenario["data"], ensure_ascii=False),
    }

    yield {
        "event": "chart_type",
        "data": json.dumps({"type": scenario.get("chart_type", "bar")}, ensure_ascii=False),
    }

    yield {
        "event": "viz_config",
        "data": json.dumps(scenario["viz"], ensure_ascii=False),
    }

    yield {"event": "state", "data": json.dumps({"state": "completed"})}
    yield {"event": "done", "data": json.dumps({"message": "查询完成"}, ensure_ascii=False)}


@router.post("/api/query/mock")
async def query_mock(request: QueryRequest):
    """Mock 查询接口（无需数据库，根据问题关键词返回对应模拟数据）"""
    logger.info(f"[Mock] 收到查询: {request.question[:100]}")
    return EventSourceResponse(
        _mock_event_generator(request.question),
        media_type="text/event-stream",
    )
