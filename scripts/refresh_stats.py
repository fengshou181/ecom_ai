# -*- coding: utf-8 -*-
"""刷新数据统计：连接 Doris 统计各库表行数与容量，生成 docs/DATA_STATS.md（数据口径单一事实源）"""
import sys
import io
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))
from doris_client import query

DATABASES = ["olist", "amazon", "instacart", "taobao", "product_samples"]
WIDE_TABLES = {
    "olist": "olist_order_item_wide",
    "amazon": "amazon_review_wide",
    "instacart": "instacart_order_product_wide",
    "taobao": "taobao_user_behavior_wide",
    "product_samples": "jd_products",
}
OUT = Path(__file__).resolve().parent.parent / "docs" / "DATA_STATS.md"

UPDATE_CALENDAR = [
    "## 数据更新日历",
    "",
    "| 数据集 | 性质 | 更新策略 |",
    "|--------|------|----------|",
    "| olist / amazon / instacart / taobao | 静态学术数据集 | **无需更新**，入库即最终态 |",
    "| product_samples.jd_products | 爬虫样本 | 建议**每月刷新一次**（月初） |",
    "",
    "### jd_products 月度刷新链路（按序执行）",
    "",
    "1. 采集：京东商品采集脚本（本地 `scripts/03~09`，开源仓库从略）",
    "2. 入库：重跑对应 Doris 导入脚本（TRUNCATE 后重新 STREAM LOAD）",
    "3. 统计：`conda run -n pds python scripts/refresh_stats.py`（重新生成本文件）",
    "4. 看板：`conda run -n pds python scripts/16_refresh_dashboard_data.py`，然后 website 目录 commit + push",
    "5. 知识库：`conda run -n pds python rag/knowledge_builder.py`（表文档内嵌行数，数据变了必须重建）",
    "6. 回归：`conda run -n pds python rag/evals/run_eval.py`，对比 docs/benchmark/ 历史报告",
    "",
    "### 日常巡检",
    "",
    "`conda run -n pds python scripts/health_check.py`：宽表行数异动 + 关键字段空值率告警，",
    "对比基线在 docs/health/baseline.json（经批准的基线，告警时不会自动推进），",
    "最近观测快照在 docs/health/last_snapshot.json（每次运行都更新，用于审计）。",
    "确认数据变更符合预期后执行 `health_check.py --approve` 迁移基线。退出码 0=健康 1=有告警。",
    "",
]


def main():
    lines = []
    total_rows = 0
    total_tables = 0
    for db in DATABASES:
        tables = [r[0] for r in query(f"SHOW TABLES FROM {db}").values.tolist()]
        rows = []
        for t in tables:
            cnt = int(query(f"SELECT COUNT(*) AS c FROM {db}.{t}").iloc[0, 0])
            tag = "（宽表）" if t == WIDE_TABLES.get(db) else ""
            rows.append((t, cnt, tag))
            total_rows += cnt
        total_tables += len(tables)
        lines.append((db, rows))

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = [f"# 数据统计（DATA_STATS）",
           f"",
           f"> 本文件由 `scripts/refresh_stats.py` 自动生成，**是全部文档中数据口径的唯一事实源**。",
           f"> 生成时间：{ts}",
           f"",
           f"## 总览",
           f"",
           f"| 指标 | 值 |",
           f"|------|-----|",
           f"| 数据库数 | {len(DATABASES)} |",
           f"| 表总数 | {total_tables} |",
           f"| 总行数 | {total_rows:,} |",
           f""]
    for db, rows in lines:
        subtotal = sum(r[1] for r in rows)
        out += [f"## {db}（{len(rows)} 张表，共 {subtotal:,} 行）",
                f"",
                f"| 表 | 行数 | 备注 |",
                f"|----|------|------|"]
        for t, cnt, tag in rows:
            out.append(f"| {t} | {cnt:,} | {tag} |")
        out.append("")
    out += UPDATE_CALENDAR
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"已生成 {OUT}（{total_tables} 张表，共 {total_rows:,} 行）")


if __name__ == "__main__":
    main()
