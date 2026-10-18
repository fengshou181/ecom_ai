# -*- coding: utf-8 -*-
"""Doris 只读查询客户端"""
import pymysql
import pandas as pd
import config


def get_connection():
    return pymysql.connect(
        host=config.DORIS_HOST,
        port=config.DORIS_PORT,
        user=config.DORIS_USER,
        password=config.DORIS_PASSWORD,
        charset="utf8mb4",
        connect_timeout=10,
        read_timeout=config.QUERY_TIMEOUT_SECONDS,
    )


def query(sql: str) -> pd.DataFrame:
    """执行只读 SQL，返回 DataFrame。连接失败时附带排查提示。"""
    try:
        conn = get_connection()
    except Exception as e:
        raise ConnectionError(
            f"无法连接 Doris ({config.DORIS_HOST}:{config.DORIS_PORT})。"
            f"请确认 WSL 与 Doris 已启动，并用 `wsl -d Ubuntu-22.04 -- hostname -I` 核对 IP。"
            f"原始错误: {e}"
        )
    try:
        with conn:
            # SSCursor 流式读取：避免默认游标在 execute 时把全部结果一次性拉进内存
            with conn.cursor(pymysql.cursors.SSCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchmany(config.SQL_MAX_RESULT_ROWS + 1)
                if len(rows) > config.SQL_MAX_RESULT_ROWS:
                    raise RuntimeError(
                        f"结果行数超过客户端预算 {config.SQL_MAX_RESULT_ROWS}，已中止读取"
                    )
                cols = [d[0] for d in cur.description] if cur.description else []
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        raise RuntimeError(f"SQL 执行失败: {e}\nSQL: {sql}")
