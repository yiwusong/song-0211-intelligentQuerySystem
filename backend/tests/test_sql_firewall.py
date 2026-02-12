"""SQL 防火墙单元测试"""

import pytest
import sys
import os

# 把 backend 加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.security.sql_firewall import SQLFirewall, SQLFirewallError


@pytest.fixture
def firewall():
    return SQLFirewall(max_rows=100)


class TestSQLFirewall:
    """SQL 防火墙测试"""

    def test_valid_select(self, firewall):
        sql = "SELECT * FROM orders"
        result = firewall.validate(sql)
        assert "SELECT" in result.upper()

    def test_auto_limit(self, firewall):
        sql = "SELECT * FROM orders"
        result = firewall.validate(sql)
        assert "LIMIT" in result.upper()

    def test_existing_limit_preserved(self, firewall):
        sql = "SELECT * FROM orders LIMIT 50"
        result = firewall.validate(sql)
        assert "50" in result

    def test_excessive_limit_capped(self, firewall):
        sql = "SELECT * FROM orders LIMIT 9999"
        result = firewall.validate(sql)
        # 超过 max_rows=100 应被限制
        assert "100" in result

    def test_block_insert(self, firewall):
        with pytest.raises(SQLFirewallError) as exc_info:
            firewall.validate("INSERT INTO orders (user_id) VALUES (1)")
        assert exc_info.value.code in ("BLOCKED_STATEMENT", "NON_SELECT")

    def test_block_update(self, firewall):
        with pytest.raises(SQLFirewallError) as exc_info:
            firewall.validate("UPDATE orders SET status = 'cancelled'")
        assert exc_info.value.code in ("BLOCKED_STATEMENT", "NON_SELECT")

    def test_block_delete(self, firewall):
        with pytest.raises(SQLFirewallError) as exc_info:
            firewall.validate("DELETE FROM orders")
        assert exc_info.value.code in ("BLOCKED_STATEMENT", "NON_SELECT")

    def test_block_drop(self, firewall):
        with pytest.raises(SQLFirewallError) as exc_info:
            firewall.validate("DROP TABLE orders")
        assert exc_info.value.code in ("BLOCKED_STATEMENT", "NON_SELECT")

    def test_empty_sql(self, firewall):
        with pytest.raises(SQLFirewallError) as exc_info:
            firewall.validate("")
        assert exc_info.value.code == "EMPTY_SQL"

    def test_complex_select_with_join(self, firewall):
        sql = """
        SELECT o.id, u.name, o.total_amount
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.status = 'completed'
        ORDER BY o.total_amount DESC
        """
        result = firewall.validate(sql)
        assert "SELECT" in result.upper()
        assert "JOIN" in result.upper()

    def test_select_with_subquery(self, firewall):
        sql = """
        SELECT * FROM orders
        WHERE user_id IN (SELECT id FROM users WHERE city = '北京')
        """
        result = firewall.validate(sql)
        assert "SELECT" in result.upper()

    def test_select_with_aggregation(self, firewall):
        sql = """
        SELECT city, COUNT(*) as cnt
        FROM users
        GROUP BY city
        ORDER BY cnt DESC
        """
        result = firewall.validate(sql)
        assert "GROUP BY" in result.upper()
