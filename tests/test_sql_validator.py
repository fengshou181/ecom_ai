# -*- coding: utf-8 -*-
"""sql_validator 单元测试：解析树校验 + 表白名单 + LIMIT 补全"""
import pytest

from sql_validator import validate, UnsafeSqlError


def test_allows_select_and_appends_limit():
    out = validate("SELECT COUNT(*) FROM taobao.taobao_user_behavior_wide")
    assert "LIMIT" in out.upper()


def test_keeps_existing_limit():
    out = validate("SELECT * FROM olist.olist_order_item_wide LIMIT 10")
    assert out.rstrip().endswith("LIMIT 10")


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


# ---- 2026-10-18 检查报告 P0 安全回归 ----

def test_rejects_cte_name_collision_bypass():
    """CTE 名与真实表同名时，限定表仍必须过白名单（核心绕过场景）"""
    with pytest.raises(UnsafeSqlError, match="不在允许查询的库"):
        validate("WITH user AS (SELECT 1 AS x) SELECT * FROM mysql.user")


def test_allows_qualified_table_sharing_cte_name():
    """CTE 名与真实表同名但限定表白名单通过时应放行"""
    out = validate("WITH jd_products AS (SELECT 1 AS x) SELECT * FROM product_samples.jd_products")
    assert "product_samples" in out


def test_allows_nested_cte():
    out = validate("WITH a AS (SELECT 1 AS x), b AS (SELECT x FROM a) SELECT * FROM b")
    assert "LIMIT" in out.upper()


def test_rejects_catalog_reference():
    with pytest.raises(UnsafeSqlError, match="catalog"):
        validate("SELECT * FROM internal.olist.olist_order_item_wide")


def test_outer_limit_added_when_only_subquery_has_limit():
    out = validate("SELECT * FROM (SELECT score FROM amazon.amazon_review_wide LIMIT 1) s")
    assert out.upper().rstrip().endswith("LIMIT 1000")


def test_limit_keyword_in_string_literal_does_not_count():
    out = validate("SELECT COUNT(*) FROM taobao.taobao_user_behavior_wide WHERE behavior_type = 'limit 1'")
    assert "LIMIT 1000" in out.upper()


def test_trailing_comment_cannot_swallow_limit():
    out = validate("SELECT COUNT(*) FROM olist.olist_order_item_wide -- 注释")
    assert "--" not in out
    assert out.upper().rstrip().endswith("LIMIT 1000")


def test_huge_limit_is_capped():
    out = validate("SELECT * FROM olist.olist_order_item_wide LIMIT 1000000000")
    assert out.rstrip().endswith("LIMIT 1000")


def test_mixed_case_limit_preserved():
    out = validate("SELECT * FROM olist.olist_order_item_wide LiMiT 5")
    assert out.rstrip().endswith("LIMIT 5")


def test_rejects_zero_limit():
    with pytest.raises(UnsafeSqlError, match="正整数"):
        validate("SELECT * FROM olist.olist_order_item_wide LIMIT 0")


def test_rejects_non_literal_limit():
    with pytest.raises(UnsafeSqlError):
        validate("SELECT * FROM olist.olist_order_item_wide LIMIT 1+1")
