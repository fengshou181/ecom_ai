# RAG Text-to-SQL 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 E:\ecom_ai 下搭建本地 Text-to-SQL RAG 问答系统：中文提问 → Chroma 检索 schema → Ollama qwen2.5:7b 生成 SQL → Doris 执行 → 自然语言解读，Streamlit 提供聊天界面，覆盖全部 5 库。

**Architecture:** 检索（Chroma + bge-small-zh）→ 生成（LangChain ChatOllama）→ 校验（sql_validator）→ 执行（pymysql）→ 解读（ChatOllama）。知识库含 4 类文档：表级/字段级/示例SQL/业务知识。

**Tech Stack:** Python（conda pds 环境）+ LangChain 1.x（langchain-ollama / langchain-chroma / langchain-huggingface）+ Chroma + sentence-transformers + Ollama（qwen2.5:7b）+ pymysql + Streamlit。

**Spec:** `E:\ecom_ai\docs\superpowers\specs\2026-10-17-rag-text2sql-design.md`

**注意：**
- ecom_ai 主目录不是 git 仓库，所有"提交"步骤跳过（无需 git commit）。
- 项目无 pytest 基础设施，验证方式为"运行脚本 + 预期输出"断言。
- 所有新文件均在 `E:\ecom_ai\rag\` 下创建。

---

### Task 1: 环境准备（Ollama + Python 依赖）

**Files:** 无（系统级安装）

- [x] **Step 1: 安装 Ollama**

下载 https://ollama.com/download/windows 安装包并安装（或 `winget install Ollama.Ollama`）。

- [x] **Step 2: 拉取模型**

Run: `ollama pull qwen2.5:7b`
Expected: 结尾显示 `success`（约 4.7GB）

- [x] **Step 3: 验证 Ollama 服务**

Run: `ollama run qwen2.5:7b "用一句话介绍你自己"`
Expected: 输出中文自我介绍（Ctrl+D 退出）

- [x] **Step 4: 安装 Python 依赖**

Run: `conda run -n pds pip install pymysql langchain-ollama langchain-chroma langchain-huggingface`
Expected: `Successfully installed ...`

- [x] **Step 5: 验证导入**

Run: `conda run -n pds python -c "import pymysql, langchain_ollama, langchain_chroma, langchain_huggingface; print('OK')"`
Expected: `OK`

---

### Task 2: 配置模块 config.py

**Files:**
- Create: `E:\ecom_ai\rag\config.py`

- [x] **Step 1: 创建 config.py**

```python
# -*- coding: utf-8 -*-
"""RAG 系统集中配置"""
import os

# Doris（WSL2，IP 可能变化，可用环境变量覆盖）
DORIS_HOST = os.getenv("ECOM_DORIS_HOST", "172.27.71.235")
DORIS_PORT = int(os.getenv("ECOM_DORIS_PORT", "9030"))
DORIS_USER = "root"
DORIS_PASSWORD = ""
DORIS_DATABASES = ["olist", "amazon", "instacart", "taobao", "product_samples"]

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("ECOM_OLLAMA_MODEL", "qwen2.5:7b")

# 嵌入模型（本地，首次自动下载约 100MB）
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

# Chroma 持久化目录
CHROMA_DIR = r"E:\ecom_ai\models\chroma_db"
CHROMA_COLLECTION = "ecom_schema"

# 检索与执行
RETRIEVE_TOP_K = 8
SQL_DEFAULT_LIMIT = 1000
QUERY_TIMEOUT_SECONDS = 30
SQL_MAX_RETRIES = 2
```

- [x] **Step 2: 验证导入**

Run: `conda run -n pds python -c "import sys; sys.path.insert(0, r'E:\ecom_ai\rag'); import config; print(config.DORIS_HOST, config.DORIS_DATABASES)"`
Expected: `172.27.71.235 ['olist', 'amazon', 'instacart', 'taobao', 'product_samples']`

---

### Task 3: Doris 客户端 doris_client.py

**Files:**
- Create: `E:\ecom_ai\rag\doris_client.py`

- [x] **Step 1: 创建 doris_client.py**

```python
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
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description] if cur.description else []
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        raise RuntimeError(f"SQL 执行失败: {e}\nSQL: {sql}")
```

- [x] **Step 2: 验证查询（需 WSL + Doris 已启动）**

Run: `conda run -n pds python -c "import sys; sys.path.insert(0, r'E:\ecom_ai\rag'); import doris_client; print(doris_client.query('SHOW DATABASES'))"`
Expected: 输出含 olist / amazon / instacart / taobao / product_samples 的 DataFrame

---

### Task 4: SQL 安全校验 sql_validator.py

**Files:**
- Create: `E:\ecom_ai\rag\sql_validator.py`

- [x] **Step 1: 创建 sql_validator.py**

```python
# -*- coding: utf-8 -*-
"""SQL 安全校验：只允许 SELECT，自动补 LIMIT"""
import re
import config

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|LOAD|OUTFILE|DUMPFILE|CALL|EXEC|SET)\b",
    re.IGNORECASE,
)
_LIMIT = re.compile(r"\blimit\s+\d+", re.IGNORECASE)


class UnsafeSqlError(ValueError):
    pass


def validate(sql: str) -> str:
    """校验并规范化 SQL，返回可安全执行的 SQL；不合法时抛 UnsafeSqlError。"""
    if not sql or not sql.strip():
        raise UnsafeSqlError("SQL 为空")
    cleaned = sql.strip().rstrip(";")
    if ";" in cleaned:
        raise UnsafeSqlError("只允许单条 SELECT 语句")
    if not re.match(r"^\s*select\b", cleaned, re.IGNORECASE):
        raise UnsafeSqlError("只允许 SELECT 查询")
    m = _FORBIDDEN.search(cleaned)
    if m:
        raise UnsafeSqlError(f"包含被禁止的关键字: {m.group(0)}")
    if not _LIMIT.search(cleaned):
        cleaned = f"{cleaned} LIMIT {config.SQL_DEFAULT_LIMIT}"
    return cleaned
```

- [x] **Step 2: 创建自检脚本并运行**

```python
# 临时运行（不落盘文件）：
conda run -n pds python -c "
import sys; sys.path.insert(0, r'E:\ecom_ai\rag')
from sql_validator import validate, UnsafeSqlError
assert validate('select * from t') == 'select * from t LIMIT 1000'
assert validate('SELECT a FROM t LIMIT 5;') == 'SELECT a FROM t LIMIT 5'
for bad in ['delete from t', 'select * from t; select 1', 'select * from t limit 1 union drop table x', '', 'update t set a=1']:
    try:
        validate(bad); raise AssertionError('应被拒绝: ' + bad)
    except UnsafeSqlError:
        pass
print('validator OK')
"
```

Expected: `validator OK`（注意：`'select * from t limit 1 union drop table x'` 因含 DROP 被拒）

---

### Task 5: Schema 抽取 schema_extractor.py

**Files:**
- Create: `E:\ecom_ai\rag\schema_extractor.py`

- [x] **Step 1: 创建 schema_extractor.py**

```python
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
    """返回 {db: {'table': str, 'columns': [...]}}"""
    out = {}
    for db, table in get_wide_tables().items():
        if table:
            out[db] = {"table": table, "columns": get_columns(db, table)}
    return out
```

- [x] **Step 2: 验证抽取**

Run: `conda run -n pds python -c "import sys; sys.path.insert(0, r'E:\ecom_ai\rag'); import schema_extractor as se; m = se.get_wide_tables(); print(m); assert all(v for v in m.values()), '存在未找到宽表的库'; c = se.get_columns('olist', m['olist']); print(len(c), c[:3]); assert len(c) > 10"`
Expected: 打印 5 库宽表名映射；olist 字段数 > 10 且前 3 个字段带注释

---

### Task 6: 知识库构建 knowledge_builder.py

**Files:**
- Create: `E:\ecom_ai\rag\knowledge_builder.py`

- [x] **Step 1: 创建 knowledge_builder.py**

```python
# -*- coding: utf-8 -*-
"""构建 Chroma 知识库：表文档 + 字段文档 + 示例SQL + 业务知识"""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import config
import schema_extractor as se

BUSINESS_DOCS = [
    "数据集背景: olist 是巴西电商 Olist 两年真实订单数据; amazon 是亚马逊商品评论; instacart 是生鲜杂货订单; taobao 是淘宝用户行为(PV/收藏/加购/购买); product_samples 是爬虫采集的商品样本。",
    "口径定义: 淘宝 PV 到购买转化率 = buy 行为数 / pv 行为数; GMV = 商品价格 price 求和(仅统计 delivered 订单); 复购率 = 购买次数>=2 的用户占比。",
    "可回答范围: 各数据集的销售/GMV/趋势、用户行为转化、评分分布、热销商品、交付时长等统计问题。系统会生成 SQL 查询 Apache Doris 宽表后回答。",
]

# 表名用运行时实际宽表名填充（防表名记忆错误）
EXAMPLE_SQL_TEMPLATES = [
    ("olist 每月 GMV 趋势怎么算?",
     "SELECT DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS ym, SUM(price) AS gmv "
     "FROM {olist} WHERE order_status = 'delivered' GROUP BY ym ORDER BY ym"),
    ("olist 平均交付天数怎么算?",
     "SELECT AVG(DATEDIFF(order_delivered_customer_date, order_purchase_timestamp)) AS avg_days "
     "FROM {olist} WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL"),
    ("淘宝 PV 到购买转化率怎么算?",
     "SELECT SUM(CASE WHEN behavior_type='buy' THEN 1 ELSE 0 END) / SUM(CASE WHEN behavior_type='pv' THEN 1 ELSE 0 END) AS pv_to_buy "
     "FROM {taobao}"),
]


def build_docs() -> list:
    meta = se.extract_all()
    docs = []
    for db, info in meta.items():
        table = info["table"]
        full = f"{db}.{table}"
        col_lines = "\n".join(f"  {n} {t} -- {c}" for n, t, c in info["columns"])
        docs.append(Document(
            page_content=f"宽表 {full} 字段列表:\n{col_lines}",
            metadata={"type": "table", "db": db, "table": table},
        ))
        for n, t, c in info["columns"]:
            if c:
                docs.append(Document(
                    page_content=f"字段 {full}.{n} 类型 {t}，含义: {c}",
                    metadata={"type": "column", "db": db, "table": table},
                ))
        docs.append(Document(
            page_content=f"统计 {full} 总行数: SELECT COUNT(*) FROM {full}",
            metadata={"type": "example", "db": db},
        ))
    table_map = {db: f"{db}.{info['table']}" for db, info in meta.items()}
    for q, tpl in EXAMPLE_SQL_TEMPLATES:
        sql = tpl.format(olist=table_map.get("olist", "olist.olist_order_item_wide"),
                         taobao=table_map.get("taobao", "taobao.user_behavior"))
        docs.append(Document(page_content=f"示例问题: {q}\n参考SQL: {sql}",
                             metadata={"type": "example"}))
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
```

- [x] **Step 2: 构建知识库**

Run: `conda run -n pds python E:\ecom_ai\rag\knowledge_builder.py`
Expected: `知识库构建完成: N 条文档 -> E:\ecom_ai\models\chroma_db`（N 约 200+；首次运行会下载嵌入模型约 100MB）

- [x] **Step 3: 验证检索可用**

Run: `conda run -n pds python -c "import sys; sys.path.insert(0, r'E:\ecom_ai\rag'); import config; from langchain_chroma import Chroma; from langchain_huggingface import HuggingFaceEmbeddings; s = Chroma(collection_name=config.CHROMA_COLLECTION, embedding_function=HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL), persist_directory=config.CHROMA_DIR); r = s.similarity_search('olist 的运费字段叫什么', k=3); [print(d.page_content[:80]) for d in r]"`
Expected: 返回与 freight_value / 运费 相关的文档

---

### Task 7: 检索器 retriever.py

**Files:**
- Create: `E:\ecom_ai\rag\retriever.py`

- [x] **Step 1: 创建 retriever.py**

```python
# -*- coding: utf-8 -*-
"""检索与问题相关的 schema 上下文"""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import config

_store = None


def get_store():
    global _store
    if _store is None:
        _store = Chroma(
            collection_name=config.CHROMA_COLLECTION,
            embedding_function=HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL),
            persist_directory=config.CHROMA_DIR,
        )
    return _store


def retrieve_context(question: str, k: int = None) -> str:
    """返回拼接的上下文：相关表/字段/示例SQL/业务知识。"""
    k = k or config.RETRIEVE_TOP_K
    docs = get_store().similarity_search(question, k=k)
    if not docs:
        return ""
    parts = [f"【{d.metadata.get('type', 'doc')}】{d.page_content}" for d in docs]
    return "\n\n".join(parts)
```

- [x] **Step 2: 验证**

Run: `conda run -n pds python -c "import sys; sys.path.insert(0, r'E:\ecom_ai\rag'); from retriever import retrieve_context; c = retrieve_context('淘宝用户转化率'); print(c[:500]); assert len(c) > 100"`
Expected: 输出含 taobao / behavior_type 相关上下文

---

### Task 8: 核心链路 sql_chain.py

**Files:**
- Create: `E:\ecom_ai\rag\sql_chain.py`

- [x] **Step 1: 创建 sql_chain.py**

```python
# -*- coding: utf-8 -*-
"""Text-to-SQL 核心链路：检索→生成→校验→执行→重试→解读"""
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import config
import doris_client
from retriever import retrieve_context
from sql_validator import validate, UnsafeSqlError

SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是 Apache Doris（MySQL 方言）数据分析助手。根据给定的表结构和示例，"
     "为用户问题生成一条可执行的 SELECT 查询。只输出 SQL 本身，不要任何解释或 markdown 标记。"
     "要求：只使用给定上下文中存在的表和字段；注意 Doris 使用 MySQL 方言；"
     "聚合查询注意 GROUP BY；时间过滤注意字段类型。\n\n相关上下文:\n{context}"),
    ("human", "{question}"),
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是数据分析助手。根据用户问题、执行的 SQL 和查询结果，用简洁中文回答。"
     "给出关键数字与结论，不超过 150 字。结果为空时说明未查到数据并建议调整条件。"),
    ("human", "问题: {question}\nSQL: {sql}\n查询结果(前50行):\n{result}"),
])

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0,
        )
    return _llm


def _clean_sql(text: str) -> str:
    """剥离 LLM 输出中的 markdown 代码块包裹。"""
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)
    return text.strip()


def generate_sql(question: str, context: str, error_hint: str = "") -> str:
    prompt = SQL_PROMPT
    q = question if not error_hint else f"{question}\n(上一次SQL执行报错: {error_hint}，请修正后重新生成)"
    chain = prompt | get_llm() | StrOutputParser()
    return _clean_sql(chain.invoke({"context": context, "question": q}))


def interpret(question: str, sql: str, df) -> str:
    preview = df.head(50).to_string(index=False) if len(df) else "(空结果集)"
    chain = ANSWER_PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({"question": question, "sql": sql, "result": preview})


def ask(question: str) -> dict:
    """端到端问答。返回 {answer, sql, dataframe, error}。"""
    result = {"answer": "", "sql": "", "dataframe": None, "error": ""}
    try:
        context = retrieve_context(question)
    except Exception as e:
        result["error"] = f"知识库检索失败: {e}（请先运行 knowledge_builder.py）"
        return result
    last_err = ""
    for attempt in range(config.SQL_MAX_RETRIES + 1):
        try:
            raw_sql = generate_sql(question, context, last_err)
            safe_sql = validate(raw_sql)
            df = doris_client.query(safe_sql)
            result["sql"] = safe_sql
            result["dataframe"] = df
            result["answer"] = interpret(question, safe_sql, df)
            return result
        except UnsafeSqlError as e:
            last_err = f"SQL 安全校验未通过: {e}"
        except Exception as e:
            last_err = str(e)
    result["sql"] = raw_sql if "raw_sql" in dir() else ""
    result["error"] = f"多次尝试后仍失败: {last_err}"
    return result
```

- [x] **Step 2: 端到端验证（Ollama + Doris 都需在运行）**

Run: `conda run -n pds python -c "import sys; sys.path.insert(0, r'E:\ecom_ai\rag'); from sql_chain import ask; r = ask('olist 有多少张订单商品宽表记录？统计一下总行数'); print('SQL:', r['sql']); print('ERROR:', r['error']); print('ANSWER:', r['answer'][:300]); assert r['answer'] and not r['error']"`
Expected: 输出生成的 SQL 与中文回答，error 为空

---

### Task 9: 命令行入口 cli.py（基准验证）

**Files:**
- Create: `E:\ecom_ai\rag\cli.py`

- [x] **Step 1: 创建 cli.py**

```python
# -*- coding: utf-8 -*-
"""命令行问答入口 + 5 库基准验证"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from sql_chain import ask

BENCHMARK = [
    "olist 数据集的 GMV 总额是多少？",
    "amazon 评论的 5 星占比是多少？",
    "instacart 订单总数大约多少？",
    "淘宝 PV 到购买的转化率是多少？",
    "product_samples 里有多少条商品样本？",
]


def chat():
    print("电商数据问答 (输入 exit 退出)")
    while True:
        q = input("\n问> ").strip()
        if q.lower() in ("exit", "quit", ""):
            break
        r = ask(q)
        if r["error"]:
            print("出错:", r["error"])
            continue
        print("SQL:", r["sql"])
        print("答:", r["answer"])


def benchmark():
    for q in BENCHMARK:
        r = ask(q)
        status = "OK" if r["answer"] and not r["error"] else "FAIL"
        print(f"[{status}] {q}\n  SQL: {r['sql']}\n  答: {r['answer'][:150]}\n  错: {r['error']}\n")


if __name__ == "__main__":
    benchmark() if "--bench" in sys.argv else chat()
```

- [x] **Step 2: 运行基准**

Run: `conda run -n pds python E:\ecom_ai\rag\cli.py --bench`
Expected: 5 个问题至少 4 个 `[OK]`（ollama 首次加载模型较慢属正常）

---

### Task 10: Streamlit 界面 app.py

**Files:**
- Create: `E:\ecom_ai\rag\app.py`

- [x] **Step 1: 创建 app.py**

```python
# -*- coding: utf-8 -*-
"""电商数据 RAG 问答 - Streamlit 聊天界面"""
import streamlit as st
from sql_chain import ask

st.set_page_config(page_title="电商数据智能问答", page_icon="🛒", layout="wide")
st.title("🛒 电商数据智能问答")
st.caption("基于 Ollama qwen2.5 + Chroma + Apache Doris 的本地 Text-to-SQL RAG")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("查看生成的 SQL"):
                st.code(msg["sql"], language="sql")
        if msg.get("df") is not None and len(msg["df"]):
            st.dataframe(msg["df"], use_container_width=True)

if question := st.chat_input("例如: olist 每月 GMV 趋势 / 淘宝 PV 到购买转化率"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("思考中（本地模型生成可能需要 10-60 秒）..."):
            r = ask(question)
        if r["error"]:
            st.error(r["error"])
            st.session_state.messages.append({"role": "assistant", "content": f"出错了: {r['error']}"})
        else:
            st.markdown(r["answer"])
            with st.expander("查看生成的 SQL"):
                st.code(r["sql"], language="sql")
            if r["dataframe"] is not None and len(r["dataframe"]):
                st.dataframe(r["dataframe"], use_container_width=True)
            st.session_state.messages.append(
                {"role": "assistant", "content": r["answer"], "sql": r["sql"], "df": r["dataframe"]}
            )
```

- [x] **Step 2: 启动并验证**

Run: `conda run -n pds python -m streamlit run E:\ecom_ai\rag\app.py --server.port 8501`
Expected: 浏览器打开 http://localhost:8501，输入"olist 的 GMV 总额"能得到回答 + SQL + 表格

---

## 自审记录

- **Spec 覆盖**: 模块 config/doris_client/schema_extractor/knowledge_builder/retriever/sql_validator/sql_chain/app/cli 全部有对应 Task；知识库 4 类文档在 Task 6；安全与错误处理在 Task 4/8；测试策略在 Task 9 benchmark；依赖清单在 Task 1。✔
- **占位符**: 无 TBD/TODO，所有代码完整。✔
- **类型一致**: `ask()` 返回 `{answer, sql, dataframe, error}`，cli.py 与 app.py 均按此结构消费；`retrieve_context(question, k)`、`validate(sql)->str`、`se.extract_all()->dict` 签名前后一致。✔
- **注意**: Chroma 1.5.9 与 langchain-chroma 若出现兼容问题，降级方案为 knowledge_builder/retriever 改用 chromadb 原生 API（PersistentClient + embedding_function=SentenceTransformerEmbeddingFunction）。

---

## 实施后偏差（2026-10-17 补记）

Task 1-10 全部按计划完成并验证（基准 5/5 通过）。与计划的偏差：

1. **LLM 由 qwen2.5:7b 降级为 qwen2.5:3b**：RTX 3050 Ti 4GB 显存无法全量装载 7b，热态延迟与内存占用均改善（详见设计文档 §12 变更记录）。
2. **RETRIEVE_TOP_K 由 8 调整为 6**：top_k=4 实测 amazon / product_samples 退化，6 为折中。
3. **删除解读层 `interpret()`**：改为 `format_answer()` 纯格式化直出，每问省一次 LLM 推理，热态单问 0.5–2.5s。
4. **新增表名兜底 `_qualify_tables()`**：3b 偶发漏写库名前缀，程序级补全为各库主数据表。
5. **cli.py benchmark 增加逐题计时与汇总**（判据仍为"有无回答"，口径准确率待评测集补齐）。
