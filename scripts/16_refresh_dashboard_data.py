# -*- coding: utf-8 -*-
"""刷新看板数据：查 Doris 宽表 -> 生成 website/dashboard-data.js

用法:
    conda run -n pds python scripts/16_refresh_dashboard_data.py

产出:
    website/dashboard-data.js  (window.DASHBOARD_DATA = {...})
    website/ecommerce-dashboard.html 优先读取该文件，缺失时回退到页面内置硬编码值。
"""
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "rag"))

from doris_client import query  # noqa: E402

OUT_PATH = os.path.join(BASE, "website", "dashboard-data.js")


def scalar(sql):
    df = query(sql)
    if df.empty:
        return None
    v = df.iloc[0, 0]
    return float(v) if v is not None else None


def pairs(sql):
    """返回 [(label, value), ...]"""
    df = query(sql)
    return list(df.itertuples(index=False, name=None))


def top10(sql):
    """返回 (labels, values)"""
    rows = pairs(sql)
    return [str(r[0]) for r in rows], [float(r[1]) for r in rows]


# ---------------- Olist ----------------

def collect_olist(data, checks):
    T = "olist.olist_order_item_wide"

    # KPI：口径已验证 = 全量 item_total_value（价格+运费）
    gmv = scalar(f"SELECT ROUND(SUM(item_total_value)/10000,2) FROM {T}")
    aov = scalar(f"SELECT ROUND(AVG(item_total_value),2) FROM {T}")
    print(f"[olist] GMV={gmv} (硬编码 1584) AOV={aov} (硬编码 140.64)")
    checks.append(("olist.KPI 总GMV(万)", gmv, 1584.36))
    checks.append(("olist.KPI 平均客单价", aov, 140.64))

    ontime = scalar(f"SELECT ROUND(AVG(is_delivered_on_time)*100,2) FROM {T} WHERE order_status='delivered'")
    customers = scalar(f"SELECT COUNT(DISTINCT customer_unique_id) FROM {T}")
    checks.append(("olist.KPI 准时送达率", ontime, 92.09))
    checks.append(("olist.KPI 活跃客户(万)", round(customers / 10000, 1), 9.5))

    data["olist"] = {
        "kpi": {"gmv": f"{gmv:,.0f}", "aov": f"{aov}", "ontime": f"{ontime}", "customers": f"{customers/10000:.1f}"},
    }

    # 月度趋势（全量 item_total_value，剔除空月）
    rows = pairs(
        f"""SELECT DATE_FORMAT(order_purchase_timestamp,'%Y-%m') ym, ROUND(SUM(item_total_value)/10000,2) v
            FROM {T} GROUP BY ym HAVING v >= 0.01 ORDER BY ym"""
    )
    data["olist"]["monthly"] = {"labels": [str(r[0]) for r in rows], "values": [float(r[1]) for r in rows]}
    checks.append(("olist.月度GMV", data["olist"]["monthly"]["values"],
                   # 硬编码 2016-09 写作 0.35 系手工误差，Doris 真实值 0.04（0.0355）；尾部 0.02 为 2018-09
                   [0.04, 5.68, 13.72, 28.63, 43.2, 41.24, 58.62, 50.3, 58.5, 66.82, 72.04, 76.93,
                    117.91, 86.35, 110.73, 98.69, 115.51, 115.97, 114.98, 102.27, 105.87, 100.33, 0.02]))

    # 订单状态占比（订单级，取前5）
    total_orders = scalar(f"SELECT COUNT(DISTINCT order_id) FROM {T}")
    rows = pairs(
        f"""SELECT order_status, COUNT(*) FROM (
                SELECT order_id, MIN(order_status) order_status FROM {T} GROUP BY order_id
            ) t GROUP BY order_status ORDER BY 2 DESC LIMIT 5"""
    )
    data["olist"]["status"] = {"labels": [STATUS_ZH.get(r[0], r[0]) for r in rows],
                               "values": [round(r[1] * 100.0 / total_orders, 2) for r in rows]}
    checks.append(("olist.状态分布", data["olist"]["status"]["values"], [97.78, 1.12, 0.47, 0.32, 0.31]))

    # 品类 Top10
    labels, values = top10(
        f"""SELECT product_category_name_english, ROUND(SUM(item_total_value)/10000,2)
            FROM {T} GROUP BY 1 ORDER BY 2 DESC LIMIT 10"""
    )
    data["olist"]["category"] = {"labels": labels, "values": values}
    checks.append(("olist.品类Top10", values, [144.12, 130.55, 124.17, 115.67, 105.93, 90.25, 77.84, 71.93, 68.54, 58.42]))

    # 州 Top10
    labels, values = top10(
        f"""SELECT customer_state, ROUND(SUM(item_total_value)/10000,2)
            FROM {T} GROUP BY 1 ORDER BY 2 DESC LIMIT 10"""
    )
    data["olist"]["state"] = {"labels": labels, "values": values}
    checks.append(("olist.州Top10", values, [592.17, 212.97, 185.62, 88.58, 80.09, 61.15, 61.02, 35.32, 34.77, 32.48]))

    # 支付方式（行级占比，排除脏行）
    pay_where = f"WHERE payment_main_type IS NOT NULL AND payment_main_type <> '\"payment_type\"'"
    pay_total = scalar(f"SELECT COUNT(*) FROM {T} {pay_where}")
    pay_rows = pairs(f"SELECT payment_main_type, COUNT(*) FROM {T} {pay_where} GROUP BY 1 ORDER BY 2 DESC")
    pay = [(r[0], round(r[1] * 100.0 / pay_total, 2)) for r in pay_rows]
    print(f"[olist] 支付: {pay} (硬编码 credit 75.25/boleto 20.3/voucher 2.95/debit 1.5)")
    data["olist"]["payment"] = {"labels": [PAY_ZH.get(p, p) for p, _ in pay], "values": [v for _, v in pay]}

    # 配送时长分布 (delivered)
    d_total = scalar(f"SELECT COUNT(*) FROM {T} WHERE order_status='delivered' AND delivery_days IS NOT NULL")
    rows = pairs(
        f"""SELECT CASE WHEN delivery_days<=3 THEN '0-3天' WHEN delivery_days<=7 THEN '4-7天'
                        WHEN delivery_days<=14 THEN '8-14天' WHEN delivery_days<=30 THEN '15-30天'
                        ELSE '30天+' END b, COUNT(*)
            FROM {T} WHERE order_status='delivered' AND delivery_days IS NOT NULL GROUP BY b"""
    )
    order_map = {b: i for i, b in enumerate(["0-3天", "4-7天", "8-14天", "15-30天", "30天+"])}
    rows.sort(key=lambda r: order_map.get(r[0], 99))
    data["olist"]["delivery"] = {"labels": [r[0] for r in rows], "values": [round(r[1] * 100.0 / d_total, 2) for r in rows]}
    checks.append(("olist.配送时长", data["olist"]["delivery"]["values"], [21.7, 33.03, 28.9, 13.8, 2.53]))


STATUS_ZH = {"delivered": "已送达", "shipped": "运输中", "canceled": "已取消",
             "invoiced": "已开票", "processing": "处理中", "unavailable": "不可用", "created": "已创建"}
PAY_ZH = {"credit_card": "信用卡", "boleto": "boleto", "voucher": "代金券",
          "debit_card": "借记卡", "not_defined": "未定义"}


# ---------------- Amazon ----------------

def collect_amazon(data, checks):
    T = "amazon.amazon_review_wide"
    reviews = scalar(f"SELECT COUNT(*) FROM {T}")
    products = scalar(f"SELECT COUNT(DISTINCT product_id) FROM {T}")
    avg_score = scalar(f"SELECT ROUND(AVG(score),2) FROM {T}")
    s_total = reviews
    five = scalar(f"SELECT ROUND(SUM(CASE WHEN score=5 THEN 1 ELSE 0 END)*100.0/{s_total},2) FROM {T}")
    checks.append(("amazon.KPI 5星占比", five, 63.77))

    data["amazon"] = {
        "kpi": {"reviews": f"{reviews/10000:.2f}", "products": f"{products/10000:.2f}",
                "score": f"{avg_score}", "five": f"{five}"},
    }

    rows = pairs(f"SELECT score, COUNT(*) FROM {T} WHERE score IS NOT NULL GROUP BY score ORDER BY score")
    score_pct = {int(r[0]): round(r[1] * 100.0 / s_total, 2) for r in rows}
    data["amazon"]["score"] = {"labels": ["1星", "2星", "3星", "4星", "5星"],
                               "values": [score_pct.get(i, 0) for i in range(1, 6)]}
    checks.append(("amazon.评分分布", data["amazon"]["score"]["values"], [9.75, 5.27, 7.34, 13.88, 63.77]))
    data["amazon"]["pie"] = {"labels": ["5星", "4星", "3星", "2星", "1星"],
                             "values": [score_pct.get(i, 0) for i in range(5, 0, -1)]}

    rows = pairs(f"SELECT YEAR(review_date) y, COUNT(*) FROM {T} WHERE review_date IS NOT NULL GROUP BY y ORDER BY y")
    data["amazon"]["trend"] = {"labels": [str(int(r[0])) for r in rows], "values": [int(r[1]) for r in rows]}
    checks.append(("amazon.年度趋势", data["amazon"]["trend"]["values"],
                   [6, 28, 12, 51, 82, 345, 757, 4235, 13598, 20805, 33641, 58978, 123334, 154088]))

    rows = pairs(
        f"""SELECT CASE WHEN price=0 THEN '免费' WHEN price<10 THEN '$0-10' WHEN price<=25 THEN '$10-25'
                        WHEN price<=50 THEN '$25-50' WHEN price<=100 THEN '$50-100' ELSE '$100-200' END b, COUNT(*)
            FROM {T} WHERE price IS NOT NULL AND price<200 GROUP BY b"""
    )
    order_map = {b: i for i, b in enumerate(["免费", "$0-10", "$10-25", "$25-50", "$50-100", "$100-200"])}
    rows.sort(key=lambda r: order_map.get(r[0], 99))
    data["amazon"]["price"] = {"labels": [r[0] for r in rows], "values": [int(r[1]) for r in rows]}
    checks.append(("amazon.价格分布", data["amazon"]["price"]["values"], [451, 474, 3590, 1451, 355, 15]))


# ---------------- Instacart ----------------

def collect_instacart(data, checks):
    T = "instacart.instacart_order_product_wide"
    orders = scalar(f"SELECT COUNT(DISTINCT order_id) FROM {T}")
    users = scalar(f"SELECT COUNT(DISTINCT user_id) FROM {T}")
    items = scalar(f"SELECT COUNT(*) FROM {T}")
    reorder = scalar(f"SELECT ROUND(SUM(reordered)*100.0/COUNT(*),2) FROM {T}")
    per_order = round(items / orders, 1)
    checks.append(("instacart.KPI 复购率", reorder, 59.01))
    checks.append(("instacart.KPI 平均每单", per_order, 10.1))

    data["instacart"] = {
        "kpi": {"orders": f"{orders/10000:.1f}", "users": f"{users/10000:.1f}",
                "reorder": f"{reorder}", "per_order": f"{per_order}"},
    }

    rows = pairs(f"SELECT order_hour_of_day h, COUNT(DISTINCT order_id) FROM {T} WHERE order_hour_of_day IS NOT NULL GROUP BY h ORDER BY h")
    data["instacart"]["hour"] = {"labels": [str(int(r[0])) for r in rows],
                                 "values": [round(r[1] / 10000, 2) for r in rows]}
    checks.append(("instacart.24h分布", data["instacart"]["hour"]["values"],
                   [2.22, 1.21, 0.74, 0.53, 0.54, 0.94, 2.99, 9.0, 17.47, 25.25, 28.25, 27.86, 26.68,
                    27.19, 27.67, 27.72, 26.64, 22.34, 17.86, 13.73, 10.21, 7.65, 6.0, 3.91]))

    rows = pairs(f"SELECT order_dow d, COUNT(DISTINCT order_id) FROM {T} WHERE order_dow IS NOT NULL GROUP BY d ORDER BY d")
    print(f"[instacart] dow 0-6 原始: {[(int(r[0]), round(r[1]/10000,2)) for r in rows]}")
    dow_vals = {int(r[0]): round(r[1] / 10000, 2) for r in rows}
    dow_labels, dow_offset = resolve_dow(dow_vals, [58.52, 57.64, 45.81, 42.81, 41.72, 44.34, 43.77], "instacart")
    data["instacart"]["dow"] = {"labels": dow_labels, "values": [dow_vals.get((i + dow_offset) % 7) for i in range(7)]}

    labels, values = top10(f"SELECT department, ROUND(COUNT(*)/1000000,2) FROM {T} WHERE department IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10")
    data["instacart"]["dept"] = {"labels": labels, "values": values}
    checks.append(("instacart.部门Top10", values, [9.89, 5.63, 3.0, 2.8, 2.33, 1.96, 1.22, 1.11, 1.1, 0.91]))

    labels, values = top10(f"SELECT aisle, COUNT(*) FROM {T} WHERE aisle IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10")
    data["instacart"]["aisle"] = {"labels": labels, "values": [int(v) for v in values]}
    checks.append(("instacart.过道Top10", data["instacart"]["aisle"]["values"],
                   [3792661, 3568630, 1843806, 1507583, 1021462, 923659, 878150, 752305, 664493, 608469]))

    rows = pairs(
        f"""SELECT CAST(days_since_prior_order AS INT) d, COUNT(DISTINCT order_id)
            FROM {T} WHERE days_since_prior_order IS NOT NULL AND days_since_prior_order BETWEEN 0 AND 30
            GROUP BY d ORDER BY d"""
    )
    data["instacart"]["reorder"] = {"labels": [str(int(r[0])) for r in rows], "values": [int(r[1]) for r in rows]}
    checks.append(("instacart.复购间隔", data["instacart"]["reorder"]["values"],
                   [66562, 143727, 191219, 214681, 219094, 211716, 236452, 315335, 178630, 116052, 93417,
                    79321, 74371, 81217, 97580, 64858, 45634, 38156, 34878, 33267, 37315, 43883, 30957,
                    23103, 20008, 18564, 18338, 21134, 25731, 18418, 346256]))

    rows = pairs(
        f"""SELECT items, COUNT(*) FROM (
                SELECT order_id, COUNT(*) items FROM {T} GROUP BY order_id
            ) t WHERE items BETWEEN 1 AND 30 GROUP BY items ORDER BY items"""
    )
    data["instacart"]["basket"] = {"labels": [str(int(r[0])) for r in rows], "values": [int(r[1]) for r in rows]}
    checks.append(("instacart.购物篮", data["instacart"]["basket"]["values"],
                   [163593, 194362, 215060, 230299, 237225, 236383, 228547, 211357, 191564, 172103, 153495,
                    136963, 121714, 108077, 95475, 84714, 74468, 65348, 57290, 50198, 43720, 38049, 33134,
                    28357, 24692, 21269, 18348, 15781, 13667, 11804]))


DOW_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def resolve_dow(val_map, hardcoded, tag):
    """将 SQL dow 0-6 与硬编码 周一..周日 旋转匹配，返回 (labels, offset)"""
    for offset in range(7):
        if all(abs(val_map.get((i + offset) % 7, -1) - hardcoded[i]) < 0.05 * max(hardcoded[i], 1) for i in range(7)):
            print(f"[{tag}] dow 映射: SQL dow{(0 + offset) % 7} -> 周一 (offset={offset})")
            return DOW_ZH, offset
    print(f"[{tag}] dow 无法精确旋转匹配，按 0=周(zhou)一 处理")
    return DOW_ZH, 0


# ---------------- Taobao ----------------

def collect_taobao(data, checks):
    T = "taobao.taobao_user_behavior_wide"
    total = scalar(f"SELECT COUNT(*) FROM {T}")
    pv = scalar(f"SELECT SUM(is_pv) FROM {T}")
    cart = scalar(f"SELECT SUM(is_cart) FROM {T}")
    fav = scalar(f"SELECT SUM(is_fav) FROM {T}")
    buy = scalar(f"SELECT SUM(is_buy) FROM {T}")
    cvr = round(buy * 100.0 / pv, 2)
    checks.append(("taobao.漏斗 PV", int(pv), 89716264))
    checks.append(("taobao.漏斗 Cart", int(cart), 5530446))
    checks.append(("taobao.漏斗 Fav", int(fav), 2888258))
    checks.append(("taobao.漏斗 Buy", int(buy), 2015839))

    data["taobao"] = {
        "kpi": {"total": f"{total/1e8:.2f}", "pv": f"{pv/1e4:,.0f}", "buy": f"{buy/1e4:,.0f}", "cvr": f"{cvr}"},
        "funnel": {"pv": int(pv), "cart": int(cart), "fav": int(fav), "buy": int(buy)},
    }

    data["taobao"]["type"] = {"labels": ["浏览 PV", "加购 Cart", "收藏 Fav", "购买 Buy"],
                              "values": [round(x * 100.0 / total, 2) for x in (pv, cart, fav, buy)]}
    checks.append(("taobao.行为占比", data["taobao"]["type"]["values"], [89.58, 5.52, 2.88, 2.01]))

    rows = pairs(f"SELECT behavior_hour h, COUNT(*) FROM {T} WHERE behavior_hour IS NOT NULL GROUP BY h ORDER BY h")
    data["taobao"]["hour"] = {"labels": [str(int(r[0])) for r in rows],
                              "values": [round(r[1] / 10000, 1) for r in rows]}
    checks.append(("taobao.24h分布", data["taobao"]["hour"]["values"],
                   [340.3, 158.2, 85.5, 58.4, 50.0, 64.6, 136.7, 248.9, 340.4, 418.3, 487.9, 474.3, 477.3,
                    521.0, 519.2, 536.7, 515.4, 470.0, 479.9, 602.5, 730.9, 837.5, 830.7, 630.4]))

    rows = pairs(f"SELECT behavior_dow d, COUNT(*) FROM {T} WHERE behavior_dow IS NOT NULL GROUP BY d ORDER BY d")
    print(f"[taobao] dow 0-6 原始(千万): {[(int(r[0]), round(r[1]/1e7,2)) for r in rows]}")
    dow_vals = {int(r[0]): round(r[1] / 1e7, 2) for r in rows}
    dow_labels, dow_offset = resolve_dow(dow_vals, [1.01, 0.99, 1.03, 1.05, 1.09, 2.42, 2.43], "taobao")
    data["taobao"]["dow"] = {"labels": dow_labels, "values": [dow_vals.get((i + dow_offset) % 7) for i in range(7)]}

    labels, values = top10(
        f"""SELECT CAST(category_id AS CHAR), ROUND(SUM(is_pv)/1000000,2)
            FROM {T} WHERE is_pv=1 GROUP BY 1 ORDER BY 2 DESC LIMIT 10"""
    )
    data["taobao"]["category"] = {"labels": labels, "values": values}
    checks.append(("taobao.类目Top10", values, [4.48, 3.15, 3.15, 2.98, 2.8, 2.03, 1.87, 1.79, 1.51, 1.42]))

    rows = pairs(
        f"""SELECT CASE WHEN c<=10 THEN '1-10次' WHEN c<=50 THEN '11-50次' WHEN c<=100 THEN '51-100次'
                        WHEN c<=200 THEN '101-200次' WHEN c<=500 THEN '201-500次' ELSE '500次+' END b, COUNT(*)
            FROM (SELECT user_id, COUNT(*) c FROM {T} GROUP BY user_id) t GROUP BY b"""
    )
    order_map = {b: i for i, b in enumerate(["1-10次", "11-50次", "51-100次", "101-200次", "201-500次", "500次+"])}
    rows.sort(key=lambda r: order_map.get(r[0], 99))
    data["taobao"]["user"] = {"labels": [r[0] for r in rows], "values": [int(r[1]) for r in rows]}
    checks.append(("taobao.用户活跃度", data["taobao"]["user"]["values"], [23591, 310344, 283629, 250083, 117465, 2881]))


# ---------------- 主流程 ----------------

def main():
    data = {
        "meta": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_label": datetime.now().strftime("%Y.%m"),
            "source": "Apache Doris",
        }
    }
    checks = []
    collect_olist(data, checks)
    collect_amazon(data, checks)
    collect_instacart(data, checks)
    collect_taobao(data, checks)

    # 核对输出
    diff = 0
    print("\n========== 硬编码核对 ==========")
    for name, actual, expect in checks:
        if isinstance(expect, list):
            ok = (isinstance(actual, list) and len(actual) == len(expect)
                  and all(abs(a - e) <= max(abs(e) * 0.02, 0.02) for a, e in zip(actual, expect)))
        else:
            ok = actual is not None and abs(actual - expect) <= max(abs(expect) * 0.02, 0.02)
        mark = "OK  " if ok else "DIFF"
        if not ok:
            diff += 1
        print(f"[{mark}] {name}: 实际={actual} 参考={expect}")

    js = ("// 由 scripts/16_refresh_dashboard_data.py 自动生成，请勿手改\n"
          "// 重新生成: conda run -n pds python scripts/16_refresh_dashboard_data.py\n"
          "window.DASHBOARD_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")

    # 校验失败：保留最后有效产物，不覆盖正式文件，差异落单独日志
    if diff:
        log_path = OUT_PATH + ".diff.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"校验失败 {datetime.now():%Y-%m-%d %H:%M:%S}，{diff}/{len(checks)} 项不一致\n")
            for name, actual, expect in checks:
                f.write(f"{name}\n  实际={actual}\n  参考={expect}\n")
        print(f"\n校验失败（{diff} 项），已保留最后有效文件: {OUT_PATH}")
        print(f"差异明细: {log_path}")
        sys.exit(1)

    # 原子发布：先写临时文件再替换，避免半截文件进入部署
    tmp_path = OUT_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(js)
    os.replace(tmp_path, OUT_PATH)

    print(f"\n已生成 {OUT_PATH}")
    print(f"核对结果: {len(checks)}/{len(checks)} 一致")
    sys.exit(0)


if __name__ == "__main__":
    main()
