# -*- coding: utf-8 -*-
"""冒烟测试：5 库各一条端到端问答（需 Doris + Ollama，RUN_INTEGRATION=1 运行）"""
import pytest

from sql_chain import ask

SMOKE_CASES = [
    ("olist 已交付订单的商品金额合计是多少", 13221498.11),
    ("amazon 评论的 5 星占比是多少", 0.6377),
    ("instacart 订单商品项总数是多少", 33819108),
    ("淘宝 PV 到购买的转化率是多少", 0.022469),
    ("product_samples 里有多少条商品样本", 25),
]


@pytest.mark.integration
@pytest.mark.parametrize("question,expected", SMOKE_CASES)
def test_smoke(question, expected):
    r = ask(question)
    assert not r["error"], f"执行失败: {r['error']}"
    assert r["dataframe"] is not None and len(r["dataframe"]) > 0
    got = float(r["dataframe"].iloc[0, -1])
    assert abs(got - expected) <= abs(expected) * 0.01, f"期望 {expected}，实际 {got}"
