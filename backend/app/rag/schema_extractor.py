"""Schema Extractor — 从 PostgreSQL information_schema 提取表结构 + 注释"""
from __future__ import annotations

from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


class SchemaExtractor:
    """从 PostgreSQL 提取完整的 Schema 信息（表名、字段、类型、注释、外键）"""

    async def extract(self, session: AsyncSession, schema_name: str = "public") -> list[dict]:
        """
        提取指定 schema 下所有表的结构信息

        返回格式:
        [
          {
            "table_name": "orders",
            "table_comment": "订单表",
            "columns": [
              {"name": "id", "type": "integer", "nullable": false, "comment": "订单ID"},
              ...
            ],
            "foreign_keys": [
              {"column": "user_id", "ref_table": "users", "ref_column": "id"},
              ...
            ]
          }
        ]
        """
        tables = []

        try:
            # 1) 获取所有表
            table_rows = await session.execute(text("""
                SELECT t.table_name,
                       obj_description((quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass, 'pg_class') AS table_comment
                FROM information_schema.tables t
                WHERE t.table_schema = :schema
                  AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """), {"schema": schema_name})
            table_list = table_rows.fetchall()

            for table_row in table_list:
                table_name = table_row[0]
                table_comment = table_row[1] or ""

                # 2) 获取列信息 + 注释
                col_rows = await session.execute(text("""
                    SELECT c.column_name,
                           c.data_type,
                           c.is_nullable,
                           c.column_default,
                           col_description((quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass, c.ordinal_position) AS col_comment
                    FROM information_schema.columns c
                    WHERE c.table_schema = :schema
                      AND c.table_name = :table
                    ORDER BY c.ordinal_position
                """), {"schema": schema_name, "table": table_name})

                columns = []
                for col in col_rows.fetchall():
                    columns.append({
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES",
                        "default": col[3],
                        "comment": col[4] or "",
                    })

                # 3) 获取外键关系
                fk_rows = await session.execute(text("""
                    SELECT kcu.column_name,
                           ccu.table_name  AS ref_table,
                           ccu.column_name AS ref_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                      ON tc.constraint_name = ccu.constraint_name
                      AND tc.table_schema = ccu.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = :schema
                      AND tc.table_name = :table
                """), {"schema": schema_name, "table": table_name})

                foreign_keys = []
                for fk in fk_rows.fetchall():
                    foreign_keys.append({
                        "column": fk[0],
                        "ref_table": fk[1],
                        "ref_column": fk[2],
                    })

                tables.append({
                    "table_name": table_name,
                    "table_comment": table_comment,
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                })

            logger.info(f"Schema 提取完成：共 {len(tables)} 张表")
            return tables

        except Exception as e:
            logger.error(f"Schema 提取失败: {e}")
            raise

    def format_for_prompt(self, tables: list[dict]) -> str:
        """将 Schema 信息格式化为 LLM 友好的文本"""
        lines = []
        for t in tables:
            lines.append(f"### 表: {t['table_name']}  ({t['table_comment']})")
            lines.append("| 字段 | 类型 | 可空 | 说明 |")
            lines.append("|------|------|------|------|")
            for col in t["columns"]:
                nullable = "✓" if col["nullable"] else "✗"
                lines.append(f"| {col['name']} | {col['type']} | {nullable} | {col['comment']} |")

            if t["foreign_keys"]:
                fk_strs = [f"{fk['column']} → {fk['ref_table']}.{fk['ref_column']}" for fk in t["foreign_keys"]]
                lines.append(f"外键关系: {', '.join(fk_strs)}")
            lines.append("")

        return "\n".join(lines)

    def format_for_embedding(self, tables: list[dict]) -> list[dict]:
        """将每张表格式化为可嵌入的文档

        返回 [{"id": "table_name", "text": "...", "metadata": {...}}]
        """
        docs = []
        for t in tables:
            col_descs = []
            for col in t["columns"]:
                desc = f"{col['name']}({col['type']}): {col['comment']}"
                col_descs.append(desc)

            text = (
                f"表 {t['table_name']}（{t['table_comment']}）包含以下字段：\n"
                + "\n".join(col_descs)
            )

            if t["foreign_keys"]:
                fk_strs = [f"{fk['column']} 关联 {fk['ref_table']}.{fk['ref_column']}" for fk in t["foreign_keys"]]
                text += "\n外键关系：" + "；".join(fk_strs)

            docs.append({
                "id": t["table_name"],
                "text": text,
                "metadata": {
                    "table_name": t["table_name"],
                    "table_comment": t["table_comment"],
                    "column_count": len(t["columns"]),
                }
            })
        return docs
