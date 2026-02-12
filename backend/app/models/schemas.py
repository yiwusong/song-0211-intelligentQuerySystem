"""Pydantic 数据模型"""

from pydantic import BaseModel
from typing import Any, Optional


class QueryRequest(BaseModel):
    """查询请求"""
    question: str


class QueryResponse(BaseModel):
    """LLM 结构化输出"""
    thinking: str
    sql: str
    echarts_option: dict[str, Any]


class SSEEvent(BaseModel):
    """SSE 事件"""
    event: str  # thought | sql | viz_config | error
    data: dict[str, Any]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str


class SchemaStatusResponse(BaseModel):
    """Schema 索引状态"""
    status: str
    message: str
    tables_indexed: int


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    detail: Optional[str] = None
