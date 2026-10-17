# -*- coding: utf-8 -*-
"""sql_validator 单元测试：解析树校验 + 表白名单 + LIMIT 补全"""
import pytest

from sql_validator import validate, UnsafeSqlError


def test_allows_select_and_appends_limit():
    out = validate("SELECT COUNT(*) FROM taobao.taobao_user_behavior_wide")
    assert "LIMIT" in out.upper()


def test_keeps_existing_limit():
    sql = "SELECT * FROM olist.olist_order_item_wide LIMIT 10"
    assert validate(sql) == sql


def test_rejects_drop():
    with pytest.raises(UnsafeSqlError):
        validate("DROP TABLE taobao.taobao_user_behavior_wide")


def test_rejects_insert():
    with pytest.raises(UnsafeSqlError):
        validate("INSERT INTO olist.olist_order_item_wide SELECT * FROM olist.olist_order_item_wide")


def test_rejects_multi_statements():
    with pytest.raises(UnsafeSqlError):
        validate("SELECT 1; SELECT 2")


def test_rejects_update_disguised():
    with pytest.raises(UnsafeSqlError):
        validate("UPDATE olist.olist_order_item_wide SET price = 0")


def test_rejects_unknown_database():
    with pytest.raises(UnsafeSqlError, match="不在允许查询的库"):
        validate("SELECT * FROM mysql.user")


def test_rejects_unqualified_table():
    with pytest.raises(UnsafeSqlError, match="缺少库名前缀"):
        validate("SELECT * FROM olist_order_item_wide")


def test_allows_cte():
    out = validate("WITH t AS (SELECT 1 AS x) SELECT * FROM t")
    assert "LIMIT" in out.upper()


def test_rejects_union():
    """UNION 是经典注入拼接向量，本应用不需要，一律拒绝"""
    with pytest.raises(UnsafeSqlError, match="UNION"):
        validate("SELECT 1 AS a UNION SELECT 2")


def test_rejects_union_injection():
    with pytest.raises(UnsafeSqlError):
        validate("SELECT name FROM product_samples.jd_products UNION SELECT password FROM mysql.user")


def test_allows_subquery():
    out = validate("SELECT * FROM (SELECT score FROM amazon.amazon_review_wide) s")
    assert "LIMIT" in out.upper()
