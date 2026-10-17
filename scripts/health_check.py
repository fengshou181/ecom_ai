# -*- coding: utf-8 -*-
"""数据健康检查：宽表行数异动 + 关键字段空值率告警。

- 首次运行生成基线快照 docs/health/last_snapshot.json，后续运行与快照对比
- 静态数据集（olist/amazon/instacart/taobao）行数应恒定，任何变化都告警
- jd_products 为月度刷新样本，行数变化仅提示
- 用法：conda run -n pds python scripts/health_check.py；退出码 0=健康 1=有告警
"""
import sys
import io
import json
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))
from doris_client import query

# {库.宽表: {"static": 是否静态数据集, "key_fields": 关键字段(空值率需<阈值), "null_threshold": 空值率告警阈值}}
CHECKS = {
    "olist.olist_order_item_wide": {
        "static": True,
        "key_fields": ["order_id", "price", "order_status", "order_purchase_timestamp"],
        "null_threshold": 0.001,
    },
    "amazon.amazon_review_wide": {
        "static": True,
        "key_fields": ["review_id", "score"],
        "null_threshold": 0.001,
    },
    "instacart.instacart_order_product_wide": {
        "static": True,
        "key_fields": ["order_id", "product_id", "product_name"],
        "null_threshold": 0.001,
    },
    "taobao.taobao_user_behavior_wide": {
        "static": True,
        "key_fields": ["user_id", "item_id", "behavior_type", "behavior_date"],
        "null_threshold": 0.001,
    },
    "product_samples.jd_products": {
        "static": False,
        "key_fields": ["name"],
        "null_threshold": 0.05,
    },
}

SNAPSHOT = Path(__file__).resolve().parent.parent / "docs" / "health" / "last_snapshot.json"


def collect() -> dict:
    snap = {"checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "tables": {}}
    for full, cfg in CHECKS.items():
        cnt = int(query(f"SELECT COUNT(*) AS c FROM {full}").iloc[0, 0])
        nulls = {}
        for col in cfg["key_fields"]:
            sql = (f"SELECT SUM(CASE WHEN `{col}` IS NULL OR CAST(`{col}` AS CHAR) = '' THEN 1 ELSE 0 END) / COUNT(*) AS r "
                   f"FROM {full}")
            r = query(sql).iloc[0, 0]
            nulls[col] = round(float(r or 0), 6)
        snap["tables"][full] = {"rows": cnt, "null_rates": nulls}
    return snap


def main() -> int:
    snap = collect()
    problems, notes = [], []

    if SNAPSHOT.exists():
        prev = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        for full, cur in snap["tables"].items():
            old = prev["tables"].get(full)
            if not old:
                notes.append(f"[新增] {full}（基线中无记录）")
                continue
            if cur["rows"] != old["rows"]:
                delta = cur["rows"] - old["rows"]
                if CHECKS[full]["static"]:
                    problems.append(f"[行数异动] {full}: {old['rows']:,} -> {cur['rows']:,}（{delta:+,}，静态数据集不应变化）")
                else:
                    notes.append(f"[行数变化] {full}: {old['rows']:,} -> {cur['rows']:,}（{delta:+,}，样本表属预期）")
    else:
        notes.append("首次运行，已建立基线快照")

    for full, cur in snap["tables"].items():
        th = CHECKS[full]["null_threshold"]
        for col, rate in cur["null_rates"].items():
            if rate > th:
                problems.append(f"[空值率超标] {full}.{col}: {rate:.2%}（阈值 {th:.1%}）")

    print(f"检查时间: {snap['checked_at']}")
    for full, cur in snap["tables"].items():
        nulls = "，".join(f"{c}={r:.2%}" for c, r in cur["null_rates"].items())
        print(f"  {full}: {cur['rows']:,} 行 | 空值率 {nulls}")
    for n in notes:
        print(n)
    if problems:
        print("\n!!! 告警:")
        for p in problems:
            print(" ", p)
    else:
        print("\n✓ 全部健康")

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"快照已更新: {SNAPSHOT}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
