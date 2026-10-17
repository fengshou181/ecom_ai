# -*- coding: utf-8 -*-
"""dashboard-data.js 结构测试：确保看板数据文件可解析且关键结构完整"""
import json
import re
from pathlib import Path

import pytest

DATA_FILE = Path(__file__).resolve().parent.parent / "website" / "dashboard-data.js"

EXPECTED_SECTIONS = {
    "olist": ["kpi", "monthly", "status", "category", "state", "payment", "delivery"],
    "amazon": ["kpi", "score", "pie", "trend", "price"],
    "instacart": ["kpi", "hour", "dow", "dept", "aisle", "reorder", "basket"],
    "taobao": ["kpi", "funnel", "type", "hour", "dow", "category", "user"],
}


@pytest.fixture(scope="module")
def data():
    if not DATA_FILE.exists():
        pytest.skip("dashboard-data.js 不存在（先跑 scripts/16_refresh_dashboard_data.py）")
    text = DATA_FILE.read_text(encoding="utf-8")
    m = re.search(r"window\.DASHBOARD_DATA\s*=\s*(\{.*\})\s*;?\s*$", text, re.S)
    assert m, "dashboard-data.js 格式不符合 window.DASHBOARD_DATA = {...}"
    return json.loads(m.group(1))


def test_meta_present(data):
    assert data["meta"]["generated_at"]
    assert data["meta"]["source"]


def test_all_sections_present(data):
    for db, keys in EXPECTED_SECTIONS.items():
        assert db in data, f"缺少库 {db}"
        for k in keys:
            assert k in data[db], f"{db} 缺少 {k}"


def test_olist_monthly_not_empty(data):
    monthly = data["olist"]["monthly"]
    labels = monthly.get("labels") or monthly.get("months")
    assert labels and len(labels) >= 12


def test_taobao_funnel_has_four_stages(data):
    funnel = data["taobao"]["funnel"]
    assert all(k in funnel for k in ("pv", "cart", "fav", "buy"))
    assert all(isinstance(v, (int, float)) and v > 0 for v in funnel.values())
