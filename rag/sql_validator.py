# -*- coding: utf-8 -*-
"""SQL 安全校验：sqlglot 解析树校验（只读 SELECT + 表白名单），自动补 LIMIT"""
import re

import sqlglot
from sqlglot import exp

import config

_LIMIT = re.compile(r"\blimit\s+\d+", re.IGNORECASE)

# 只允许查询这 5 个库下的表
ALLOWED_DATABASES = frozenset(db.lower() for db in config.DORIS_DATABASES)


class UnsafeSqlError(ValueError):
    pass


def _check_tables(ast) -> None:
    """表白名单：所有引用的表必须带库前缀且库在白名单内（CTE 名除外）。"""
    cte_names = {c.alias.lower() for c in ast.find_all(exp.CTE) if c.alias}
    for table in ast.find_all(exp.Table):
        name = (table.name or "").lower()
        if name in cte_names:
            continue
        db = (table.db or "").lower()
        if not db:
            raise UnsafeSqlError(f"表 {table.name} 缺少库名前缀")
        if db not in ALLOWED_DATABASES:
            raise UnsafeSqlError(f"表 {db}.{table.name} 不在允许查询的库中")


def validate(sql: str) -> str:
    """校验并规范化 SQL，返回可安全执行的 SQL；不合法时抛 UnsafeSqlError。"""
    if not sql or not sql.strip():
        raise UnsafeSqlError("SQL 为空")
    cleaned = sql.strip().rstrip(";")
    try:
        statements = [s for s in sqlglot.parse(cleaned, read="mysql") if s is not None]
    except Exception as e:
        raise UnsafeSqlError(f"SQL 解析失败: {e}")
    if len(statements) != 1:
        raise UnsafeSqlError("只允许单条 SELECT 语句")
    ast = statements[0]
    if list(ast.find_all(exp.Union)):
        raise UnsafeSqlError("不允许 UNION（防止注入拼接，分析查询用不到）")
    if not isinstance(ast, (exp.Select, exp.Subquery)):
        raise UnsafeSqlError(f"只允许 SELECT 查询，收到: {type(ast).__name__}")
    _check_tables(ast)
    if not _LIMIT.search(cleaned):
        cleaned = f"{cleaned} LIMIT {config.SQL_DEFAULT_LIMIT}"
    return cleaned
