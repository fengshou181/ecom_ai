# -*- coding: utf-8 -*-
"""从 Doris information_schema 抽取 5 库的表/字段元数据"""
import config
import doris_client


def get_wide_tables() -> dict:
    """返回 {库名: 宽表名}。优先取表名含 wide 的表，否则取该库第一张表。"""
    result = {}
    for db in config.DORIS_DATABASES:
        df = doris_client.query(
            f"SELECT TABLE_NAME FROM information_schema.TABLES "
            f"WHERE TABLE_SCHEMA = '{db}' ORDER BY TABLE_NAME"
        )
        tables = df["TABLE_NAME"].tolist()
        wide = [t for t in tables if "wide" in t.lower()]
        result[db] = wide[0] if wide else (tables[0] if tables else None)
    return result


def get_columns(db: str, table: str):
    """返回 [(column_name, data_type, comment), ...]"""
    df = doris_client.query(
        f"SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT FROM information_schema.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{db}' AND TABLE_NAME = '{table}' ORDER BY ORDINAL_POSITION"
    )
    return list(df.itertuples(index=False, name=None))


def extract_all() -> dict:
    """返回 {db: {'table': str, 'columns': [...]}}（仅宽表，兼容旧调用）"""
    out = {}
    for db, table in get_wide_tables().items():
        if table:
            out[db] = {"table": table, "columns": get_columns(db, table)}
    return out


def extract_all_tables() -> dict:
    """返回 {db: [{'table', 'is_wide', 'rows', 'columns'}]}，覆盖库内全部表并带行数统计。"""
    wide_map = get_wide_tables()
    out = {}
    for db in config.DORIS_DATABASES:
        df = doris_client.query(
            f"SELECT TABLE_NAME FROM information_schema.TABLES "
            f"WHERE TABLE_SCHEMA = '{db}' ORDER BY TABLE_NAME"
        )
        tables = []
        for t in df["TABLE_NAME"].tolist():
            rows = int(doris_client.query(f"SELECT COUNT(*) AS c FROM {db}.`{t}`").iloc[0, 0])
            tables.append({
                "table": t,
                "is_wide": t == wide_map.get(db),
                "rows": rows,
                "columns": get_columns(db, t),
            })
        out[db] = tables
    return out
