"""SQL 防火墙 — 使用 sqlglot 做 AST 级安全检查"""

import sqlglot
from sqlglot import exp
from loguru import logger


class SQLFirewallError(Exception):
    """SQL 安全校验失败"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# 禁止的 SQL 语句类型
BLOCKED_STATEMENT_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,  # TRUNCATE, GRANT, etc.
)

# 禁止的危险函数
BLOCKED_FUNCTIONS = {
    "pg_sleep", "pg_terminate_backend", "pg_cancel_backend",
    "lo_import", "lo_export",
    "dblink", "dblink_exec",
    "copy",
}


class SQLFirewall:
    """SQL 安全防火墙：AST 级分析，仅允许安全的 SELECT 查询"""

    def __init__(self, max_rows: int = 1000):
        self.max_rows = max_rows

    def validate(self, sql: str) -> str:
        """
        验证 SQL 安全性并返回处理后的 SQL

        1. 只允许 SELECT 语句
        2. 禁止危险函数
        3. 禁止子查询中的写操作
        4. 自动添加 LIMIT（如果缺失）

        返回: 安全处理后的 SQL
        抛出: SQLFirewallError
        """
        if not sql or not sql.strip():
            raise SQLFirewallError("EMPTY_SQL", "SQL 语句为空")

        sql = sql.strip().rstrip(";")

        try:
            parsed = sqlglot.parse(sql, dialect="postgres")
        except Exception as e:
            raise SQLFirewallError("PARSE_ERROR", f"SQL 语法解析失败: {str(e)}")

        if not parsed:
            raise SQLFirewallError("PARSE_ERROR", "SQL 解析结果为空")

        safe_statements = []
        for statement in parsed:
            if statement is None:
                continue

            # 检查 1: 必须是 SELECT
            if isinstance(statement, BLOCKED_STATEMENT_TYPES):
                stmt_type = type(statement).__name__
                raise SQLFirewallError(
                    "BLOCKED_STATEMENT",
                    f"禁止执行 {stmt_type} 操作，仅允许 SELECT 查询"
                )

            if not isinstance(statement, exp.Select):
                stmt_type = type(statement).__name__
                raise SQLFirewallError(
                    "NON_SELECT",
                    f"不支持的语句类型: {stmt_type}，仅允许 SELECT 查询"
                )

            # 检查 2: 遍历 AST 查找危险节点
            self._check_dangerous_nodes(statement)

            # 检查 3: 自动添加 LIMIT
            statement = self._ensure_limit(statement)
            safe_statements.append(statement)

        # 重新生成安全 SQL
        safe_sql = "; ".join(
            stmt.sql(dialect="postgres") for stmt in safe_statements
        )

        logger.debug(f"SQL 防火墙通过: {safe_sql[:100]}...")
        return safe_sql

    def _check_dangerous_nodes(self, node: exp.Expression):
        """递归检查 AST 中的危险节点"""

        # 检查子查询中的写操作
        for subquery in node.find_all(exp.Subquery):
            inner = subquery.this
            if isinstance(inner, BLOCKED_STATEMENT_TYPES):
                raise SQLFirewallError(
                    "BLOCKED_SUBQUERY",
                    "子查询中包含禁止的写操作"
                )

        # 检查危险函数
        for func in node.find_all(exp.Anonymous):
            func_name = func.name.lower() if hasattr(func, 'name') else ""
            if func_name in BLOCKED_FUNCTIONS:
                raise SQLFirewallError(
                    "BLOCKED_FUNCTION",
                    f"禁止调用危险函数: {func_name}"
                )

        for func in node.find_all(exp.Func):
            func_name = ""
            if hasattr(func, 'sql_name'):
                func_name = func.sql_name().lower()
            elif hasattr(func, 'key'):
                func_name = func.key.lower()

            if func_name in BLOCKED_FUNCTIONS:
                raise SQLFirewallError(
                    "BLOCKED_FUNCTION",
                    f"禁止调用危险函数: {func_name}"
                )

    def _ensure_limit(self, statement: exp.Select) -> exp.Select:
        """如果 SELECT 没有 LIMIT，自动添加"""
        limit_node = statement.find(exp.Limit)
        if limit_node is None:
            statement = statement.limit(self.max_rows)
            logger.debug(f"自动添加 LIMIT {self.max_rows}")
        else:
            # 如果用户指定的 LIMIT 超过最大值，强制限制
            try:
                limit_val = int(limit_node.expression.this)
                if limit_val > self.max_rows:
                    # 替换为最大限制
                    statement = statement.limit(self.max_rows)
                    logger.debug(f"LIMIT {limit_val} 超过最大限制，已替换为 {self.max_rows}")
            except (AttributeError, ValueError, TypeError):
                pass

        return statement
