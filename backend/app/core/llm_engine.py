"""LLM Engine — 对接 OpenAI 兼容 API (gpt-5.2-chat)
流式调用 + 结构化 JSON 输出解析
"""
from __future__ import annotations

import json
from typing import AsyncGenerator
from openai import AsyncOpenAI
from loguru import logger

from app.config import get_settings
from app.core.prompt_templates import build_system_prompt


class LLMEngine:
    """LLM 引擎：流式调用大模型并解析结构化输出"""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.model = settings.OPENAI_MODEL

    async def generate_stream(
        self,
        question: str,
        schema_context: str,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """
        流式调用 LLM，逐步 yield (event_type, content)

        event_type: 'thinking' | 'sql' | 'viz_config' | 'error'
        """
        system_prompt = build_system_prompt(schema_context)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                stream=True,
                temperature=0.1,
                max_tokens=4096,
            )

            full_content = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_content += delta

                    # 流式推送 thinking 事件（逐步增长的全文）
                    yield ("thinking_delta", delta)

            # 流式结束后，解析完整 JSON 输出
            parsed = self._parse_response(full_content)
            if parsed:
                yield ("thinking_full", parsed.get("thinking", ""))
                yield ("sql", parsed.get("sql", ""))

                echarts_option = parsed.get("echarts_option", {})
                if echarts_option:
                    yield ("viz_config", json.dumps(echarts_option, ensure_ascii=False))
            else:
                # JSON 解析失败，尝试直接提取
                yield ("error", json.dumps({
                    "code": "PARSE_FAILED",
                    "message": "模型输出格式异常，无法解析为结构化 JSON",
                }, ensure_ascii=False))

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            yield ("error", json.dumps({
                "code": "LLM_ERROR",
                "message": f"模型调用失败: {str(e)}",
            }, ensure_ascii=False))

    async def generate(
        self,
        question: str,
        schema_context: str,
    ) -> dict | None:
        """非流式调用 LLM，返回完整解析结果"""
        system_prompt = build_system_prompt(schema_context)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            content = response.choices[0].message.content or ""
            return self._parse_response(content)

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return None

    def _parse_response(self, content: str) -> dict | None:
        """从模型输出中提取 JSON 结构"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        import re
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取第一个 { ... } 块
        brace_start = content.find('{')
        brace_end = content.rfind('}')
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(content[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass

        logger.warning(f"无法解析 LLM 输出: {content[:200]}...")
        return None
