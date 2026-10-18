# -*- coding: utf-8 -*-
"""构建 Chroma 知识库：表文档 + 字段文档 + 示例SQL + 业务知识"""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import config
import schema_extractor as se

BUSINESS_DOCS = [
    "数据集背景: olist 是巴西电商 Olist 两年真实订单数据; amazon 是亚马逊商品评论; instacart 是生鲜杂货订单; taobao 是淘宝用户行为(PV/收藏/加购/购买); product_samples 是爬虫采集的京东商品样本。",
    "口径定义: 淘宝 PV 到购买转化率 = buy 行为数 / pv 行为数; 交付 GMV = delivered 订单的 price 求和(不含运费); 用户复购率 = 购买订单数>=2 的用户占比(用户粒度), 商品项重复购买占比 = SUM(reordered)/COUNT(*)(商品项粒度), 两者不同; 完整口径见 docs/METRICS.md 指标字典。",
    "可回答范围: 各数据集的销售/GMV/趋势、用户行为转化、评分分布、热销商品、交付时长等统计问题。系统会生成 SQL 查询 Apache Doris 宽表后回答。",
]

EXAMPLE_SQL_TEMPLATES = [
    # olist
    ("olist 每月 GMV 趋势怎么算?",
     "SELECT DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS ym, SUM(price) AS gmv "
     "FROM {olist} WHERE order_status = 'delivered' GROUP BY ym ORDER BY ym"),
    ("olist 平均交付天数怎么算?",
     "SELECT AVG(delivery_days) AS avg_days FROM {olist} "
     "WHERE order_status = 'delivered' AND delivery_days IS NOT NULL"),
    ("olist 已交付订单的 GMV 合计怎么算?",
     "SELECT SUM(price) FROM {olist} WHERE order_status = 'delivered'"),
    ("olist 已交付订单的客单价怎么算?（订单级口径：SUM(price)/COUNT(DISTINCT order_id)，不能用 AVG(price)）",
     "SELECT SUM(price) / COUNT(DISTINCT order_id) AS aov FROM {olist} WHERE order_status = 'delivered'"),
    ("olist 一共有多少个订单?（注意：一行是一个订单商品项，订单数必须 COUNT(DISTINCT order_id)）",
     "SELECT COUNT(DISTINCT order_id) FROM {olist}"),
    ("olist 2017 年已交付的订单有多少个?",
     "SELECT COUNT(DISTINCT order_id) FROM {olist} "
     "WHERE order_status = 'delivered' AND YEAR(order_purchase_timestamp) = 2017"),
    ("olist 销售额最高的商品类目?",
     "SELECT product_category_name_english, SUM(price) AS s FROM {olist} "
     "WHERE order_status = 'delivered' GROUP BY product_category_name_english ORDER BY s DESC LIMIT 1"),
    # amazon
    ("amazon 评论的 5 星占比怎么算?",
     "SELECT SUM(CASE WHEN score = 5 THEN 1 ELSE 0 END) / COUNT(*) AS five_star_ratio FROM {amazon}"),
    ("amazon 评论数最多的类目?",
     "SELECT category_name, COUNT(*) AS c FROM {amazon} "
     "GROUP BY category_name ORDER BY c DESC LIMIT 1"),
    ("amazon 评论数超过 100 的类目中平均评分最高的类目?",
     "SELECT category_name, AVG(score) AS a FROM {amazon} "
     "GROUP BY category_name HAVING COUNT(*) > 100 ORDER BY a DESC LIMIT 1"),
    # instacart
    ("instacart 商品项重复购买占比怎么算?（商品项粒度，不是用户复购率）",
     "SELECT SUM(reordered) / COUNT(*) AS reorder_ratio FROM {instacart}"),
    ("instacart 用户复购率怎么算?（用户粒度：购买订单数>=2 的用户占比，必须用嵌套子查询按 user_id 聚合）",
     "SELECT AVG(order_cnt >= 2) AS repurchase_rate FROM "
     "(SELECT user_id, COUNT(DISTINCT order_id) AS order_cnt FROM {instacart} GROUP BY user_id) t"),
    ("instacart 最热销的商品?",
     "SELECT product_name, COUNT(*) AS c FROM {instacart} "
     "GROUP BY product_name ORDER BY c DESC LIMIT 1"),
    ("instacart 首次下单的商品项占比?",
     "SELECT SUM(is_first_order) / COUNT(*) AS first_ratio FROM {instacart}"),
    ("instacart 商品项数最多的部门?",
     "SELECT department, COUNT(*) AS c FROM {instacart} "
     "GROUP BY department ORDER BY c DESC LIMIT 1"),
    # taobao
    ("淘宝 PV 到购买转化率怎么算?",
     "SELECT SUM(is_buy) / SUM(is_pv) AS pv_to_buy FROM {taobao}"),
    ("淘宝某一天的 PV 怎么算?（日期用 behavior_date 字段，不要用 ts）",
     "SELECT SUM(is_pv) FROM {taobao} WHERE behavior_date = '2017-11-25'"),
    ("淘宝独立用户数怎么算?",
     "SELECT COUNT(DISTINCT user_id) FROM {taobao}"),
    ("淘宝行为数最多的类目 ID?",
     "SELECT category_id, COUNT(*) AS c FROM {taobao} "
     "GROUP BY category_id ORDER BY c DESC LIMIT 1"),
    # product_samples
    ("京东商品样本有多少条?",
     "SELECT COUNT(*) FROM {jd}"),
    ("京东商品样本中名称包含某关键词的商品数?（模糊匹配用 LIKE '%关键词%'）",
     "SELECT COUNT(*) FROM {jd} WHERE name LIKE '%耳机%'"),
    ("京东商品样本中最长商品名的字符数?（用 product_samples.jd_products 的 name 字段，字符数用 CHAR_LENGTH；不要用 olist 的 product_name_lenght）",
     "SELECT MAX(CHAR_LENGTH(name)) FROM {jd}"),
    ("京东商品名称的字符长度怎么统计?（京东=jd_products.name，字符数=CHAR_LENGTH）",
     "SELECT MAX(CHAR_LENGTH(name)) AS max_chars, AVG(CHAR_LENGTH(name)) AS avg_chars FROM {jd}"),
]


def build_docs() -> list:
    meta = se.extract_all_tables()
    docs = []
    for db, tables in meta.items():
        for t in tables:
            full = f"{db}.{t['table']}"
            tag = "宽表" if t["is_wide"] else "原始表"
            cols = t["columns"] if t["is_wide"] else t["columns"][:15]
            col_lines = "\n".join(f"  {n} {ty} -- {c}" for n, ty, c in cols)
            docs.append(Document(
                page_content=f"{tag} {full}（约 {t['rows']:,} 行）字段列表:\n{col_lines}",
                metadata={"type": "table", "db": db, "table": t["table"], "is_wide": t["is_wide"]},
            ))
            if t["is_wide"]:
                for n, ty, c in t["columns"]:
                    if c:
                        docs.append(Document(
                            page_content=f"字段 {full}.{n} 类型 {ty}，含义: {c}",
                            metadata={"type": "column", "db": db, "table": t["table"]},
                        ))
                docs.append(Document(
                    page_content=f"统计 {full} 总行数: SELECT COUNT(*) FROM {full}",
                    metadata={"type": "example", "db": db},
                ))
    table_map = {}
    for db, tables in meta.items():
        for t in tables:
            if t["is_wide"]:
                table_map[db] = f"{db}.{t['table']}"
    fmt = {"olist": table_map.get("olist", "olist.olist_order_item_wide"),
           "taobao": table_map.get("taobao", "taobao.taobao_user_behavior_wide"),
           "amazon": table_map.get("amazon", "amazon.amazon_review_wide"),
           "instacart": table_map.get("instacart", "instacart.instacart_order_product_wide"),
           "jd": table_map.get("product_samples", "product_samples.jd_products")}
    for q, tpl in EXAMPLE_SQL_TEMPLATES:
        db_key = ("olist" if "{olist}" in tpl else "taobao" if "{taobao}" in tpl else
                  "amazon" if "{amazon}" in tpl else "instacart" if "{instacart}" in tpl else "jd")
        db_name = {"olist": "olist", "taobao": "taobao", "amazon": "amazon",
                   "instacart": "instacart", "jd": "product_samples"}[db_key]
        docs.append(Document(page_content=f"示例问题: {q}\n参考SQL: {tpl.format(**fmt)}",
                             metadata={"type": "example", "db": db_name}))
    for text in BUSINESS_DOCS:
        docs.append(Document(page_content=text, metadata={"type": "business"}))
    return docs


def rebuild():
    docs = build_docs()
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    store = Chroma(
        collection_name=config.CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=config.CHROMA_DIR,
    )
    store.delete_collection()
    store = Chroma(
        collection_name=config.CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=config.CHROMA_DIR,
    )
    store.add_documents(docs)
    print(f"知识库构建完成: {len(docs)} 条文档 -> {config.CHROMA_DIR}")


if __name__ == "__main__":
    rebuild()
