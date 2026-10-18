# -*- coding: utf-8 -*-
"""SQL 安全校验：sqlglot 解析树校验（只读 SELECT + 表白名单 + 外层 LIMIT 封顶）

安全边界：
1. 只允许单条 SELECT（含子查询/CTE），拒绝 UNION 与一切写操作
2. 表白名单按"限定名"判断：带库前缀的真实表必须在白名单库内；
   只有未限定且命中当前查询 CTE 名的引用才豁免（防止 `WITH user AS (...) SELECT * FROM mysql.user` 绕过）
3. 外层 LIMIT 由 AST 强制设置/封顶后重新序列化，
   子查询 LIMIT、字符串字面量、SQL 注释均无法绕过
"""
import sqlglot
from sqlglot import exp

import config

# 只允许查询这 5 个库下的表
ALLOWED_DATABASES = frozenset(db.lower() for db in config.DORIS_DATABASES)


class UnsafeSqlError(ValueError):
    pass


def _check_tables(ast) -> None:
    """表白名单：带库前缀的真实表必须在白名单库内；未限定引用仅当命中 CTE 名时豁免。"""
    cte_names = {c.alias.lower() for c in ast.find_all(exp.CTE) if c.alias}
    for table in ast.find_all(exp.Table):
        name = (table.name or "").lower()
        db = (table.db or "").lower()
        catalog = (table.catalog or "").lower()
        if not db and not catalog:
            # 未限定引用：只允许是 CTE，否则拒绝
            if name in cte_names:
                continue
            raise UnsafeSqlError(f"表 {table.name} 缺少库名前缀")
        # 限定真实表：无论是否与 CTE 同名，一律校验白名单
        if catalog:
            raise UnsafeSqlError(f"不允许带 catalog 的引用: {catalog}.{db}.{name}")
        if db not in ALLOWED_DATABASES:
            raise UnsafeSqlError(f"表 {db}.{table.name} 不在允许查询的库中")


def _root_select(ast) -> exp.Select:
    """取根 SELECT（根节点允许是 Select 或括号包裹的 Subquery）。"""
    root = ast.this if isinstance(ast, exp.Subquery) else ast
    if not isinstance(root, exp.Select):
        raise UnsafeSqlError(f"只允许 SELECT 查询，收到: {type(ast).__name__}")
    return root


def _enforce_limit(root: exp.Select) -> None:
    """对根 SELECT 强制设置/封顶 LIMIT（只看最外层，子查询 LIMIT 不算数）。"""
    max_limit = config.SQL_MAX_LIMIT
    limit = root.args.get("limit")
    if limit is None:
        root.set("limit", exp.Limit(expression=exp.Literal.number(config.SQL_DEFAULT_LIMIT)))
        return
    # LIMIT 必须是正整数数字字面量（拒绝 1+1 等表达式，防止常量折叠绕过封顶）
    expr = limit.expression
    while isinstance(expr, exp.Paren):
        expr = expr.this
    if not isinstance(expr, exp.Literal) or expr.is_string:
        raise UnsafeSqlError("LIMIT 必须是整数字面量")
    try:
        n = int(expr.this)
    except (ValueError, TypeError):
        raise UnsafeSqlError("LIMIT 必须是整数字面量")
    if n < 1:
        raise UnsafeSqlError("LIMIT 必须为正整数")
    if n > max_limit:
        root.set("limit", exp.Limit(expression=exp.Literal.number(max_limit)))


def validate(sql: str) -> str:
    """校验并规范化 SQL，返回可安全执行的 SQL（重新序列化）；不合法时抛 UnsafeSqlError。"""
    if not sql or not sql.strip():
        raise UnsafeSqlError("SQL 为空")
    try:
        statements = [s for s in sqlglot.parse(sql.strip().rstrip(";"), read="mysql") if s is not None]
    except Exception as e:
        raise UnsafeSqlError(f"SQL 解析失败: {e}")
    if len(statements) != 1:
        raise UnsafeSqlError("只允许单条 SELECT 语句")
    ast = statements[0]
    if list(ast.find_all(exp.Union)):
        raise UnsafeSqlError("不允许 UNION（防止注入拼接，分析查询用不到）")
    root = _root_select(ast)
    _check_tables(ast)
    _enforce_limit(root)
    # 从 AST 重新序列化：注释被丢弃，杜绝"LIMIT 追加进注释"等文本级绕过
    return ast.sql(dialect="mysql")
