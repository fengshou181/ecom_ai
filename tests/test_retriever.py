# -*- coding: utf-8 -*-
"""retriever 库路由单元测试"""
from retriever import route_dbs


def test_route_taobao():
    assert route_dbs("淘宝 PV 到购买的转化率是多少") == ["taobao"]


def test_route_olist():
    assert route_dbs("olist 订单的平均交付天数") == ["olist"]


def test_route_amazon():
    assert route_dbs("亚马逊评论的 5 星占比") == ["amazon"]


def test_route_instacart():
    assert route_dbs("instacart 生鲜复购率") == ["instacart"]


def test_route_jd():
    assert route_dbs("京东商品样本有多少条") == ["product_samples"]


def test_route_multi():
    dbs = route_dbs("olist 和 amazon 哪个的评分更高")
    assert "olist" in dbs and "amazon" in dbs


def test_route_none():
    assert route_dbs("今天天气怎么样") == []
