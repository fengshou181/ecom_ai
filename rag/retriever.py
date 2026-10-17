# -*- coding: utf-8 -*-
"""检索与问题相关的 schema 上下文：库路由 + 表级保底注入 + 库内 top-k"""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import config

_store = None

DB_KEYWORDS = {
    "olist": ["olist", "巴西", "交付", "配送", "卖家", "类目销售"],
    "amazon": ["amazon", "亚马逊", "评论", "评分", "5星", "五星", "好评"],
    "instacart": ["instacart", "生鲜", "杂货", "复购", "部门", "热销商品", "香蕉"],
    "taobao": ["淘宝", "taobao", "pv", "uv", "转化率", "收藏", "加购", "用户行为", "行为数"],
    "product_samples": ["京东", "jd", "商品样本", "product_samples", "店铺", "样本"],
}


def get_store():
    global _store
    if _store is None:
        _store = Chroma(
            collection_name=config.CHROMA_COLLECTION,
            embedding_function=HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL),
            persist_directory=config.CHROMA_DIR,
        )
    return _store


def route_dbs(question: str) -> list:
    """按关键词把问题路由到库，未命中返回空列表。"""
    q = question.lower()
    return [db for db, kws in DB_KEYWORDS.items() if any(kw.lower() in q for kw in kws)]


def _fetch_wide_table_docs(store, dbs: list) -> list:
    """表级保底注入：确定性取回目标库的宽表文档。"""
    out = []
    for db in dbs:
        res = store.get(where={"$and": [{"db": db}, {"type": "table"}, {"is_wide": True}]})
        docs = res.get("documents") or []
        if not docs:
            res = store.get(where={"$and": [{"db": db}, {"type": "table"}]})
            docs = (res.get("documents") or [])[:1]
        out.extend(docs)
    return out


def retrieve_context(question: str, k: int = None) -> str:
    """返回拼接的上下文：保底宽表文档 + 库内向量检索 + 全局补充（示例SQL/业务知识）。"""
    k = k or config.RETRIEVE_TOP_K
    store = get_store()
    dbs = route_dbs(question)
    parts, seen = [], set()

    def add(content: str, type_: str):
        if content and content not in seen:
            seen.add(content)
            parts.append(f"【{type_}】{content}")

    # 1. 表级保底注入：路由到库后宽表结构必进上下文
    for content in _fetch_wide_table_docs(store, dbs):
        add(content, "table")

    # 2. 库内 top-k：字段/示例在目标库内检索，避免跨库挤占
    if dbs:
        per = max(2, k // len(dbs))
        for db in dbs:
            for d in store.similarity_search(question, k=per, filter={"db": db}):
                add(d.page_content, d.metadata.get("type", "doc"))

    # 3. 全局补充：未路由问题的兜底 + 示例SQL/业务知识
    for d in store.similarity_search(question, k=k):
        add(d.page_content, d.metadata.get("type", "doc"))

    return "\n\n".join(parts)
