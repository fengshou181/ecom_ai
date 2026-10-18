# -*- coding: utf-8 -*-
"""RAG 系统集中配置（密钥从 .env / 环境变量读取，不入库）"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Doris（WSL2，IP 可能变化，可用环境变量覆盖）
DORIS_HOST = os.getenv("ECOM_DORIS_HOST", "172.27.71.235")
DORIS_PORT = int(os.getenv("ECOM_DORIS_PORT", "9030"))
DORIS_USER = os.getenv("ECOM_DORIS_USER", "rag_readonly")
DORIS_PASSWORD = os.getenv("ECOM_DORIS_PASSWORD", "")  # 在 .env 中配置，见 .env.example
DORIS_DATABASES = ["olist", "amazon", "instacart", "taobao", "product_samples"]

# Ollama
# 模型选型结论（2026-10-18 A/B，30 题评测集，见 docs/benchmark/2026-10-17.md 与 2026-10-18.md）：
# 3b 准确率 86.7% / P50 1.1s / 内存 ~2GB；7b 准确率 90.0% / P50 5.2s / 内存 ~4.7GB。
# 准确率仅差 1 题且 7b 失败为执行错误，本机 CPU 推理下 3b 性价比明显更高，定为默认。
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("ECOM_OLLAMA_MODEL", "qwen2.5:3b")

# 嵌入模型（本地，首次自动下载约 100MB）
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

# Chroma 持久化目录
CHROMA_DIR = r"E:\ecom_ai\models\chroma_db"
CHROMA_COLLECTION = "ecom_schema"

# 检索与执行
RETRIEVE_TOP_K = 6
SQL_DEFAULT_LIMIT = 1000      # 模型未写 LIMIT 时补的默认值
SQL_MAX_LIMIT = 1000          # 外层 LIMIT 硬上限（超出封顶）
SQL_MAX_RESULT_ROWS = 100000  # 客户端读取行数预算（兜底防内存耗尽）
QUERY_TIMEOUT_SECONDS = 30
SQL_MAX_RETRIES = 2

# 用户/模型只写库名未写表名时的兜底映射（各库主数据表）
DATABASE_DEFAULT_TABLE = {
    "olist": "olist.olist_order_item_wide",
    "amazon": "amazon.amazon_review_wide",
    "instacart": "instacart.instacart_order_product_wide",
    "taobao": "taobao.taobao_user_behavior_wide",
    "product_samples": "product_samples.jd_products",
}
