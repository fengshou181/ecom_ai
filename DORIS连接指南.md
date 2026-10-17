# Apache Doris 连接配置指南

## 方式一：PyCharm Database 工具（推荐，图形化查看）

### 配置步骤：
1. 打开 PyCharm 右侧边栏的 **Database** 工具
2. 点击 `+` → **Data Source** → **MySQL**
3. 填写以下信息：
   - **Host**: WSL2 IP（重启后可能变化，见下方说明；推荐统一从 `rag/config.py` 的 `ECOM_DORIS_HOST` 环境变量读取）
   - **Port**: `9030`
   - **User**: `rag_readonly`（只读账号；root 空密码仅限本机运维，勿写入任何配置）
   - **Password**: 见项目根目录 `.env`（格式参考 `.env.example`）
   - **Database**: 可留空，连接后可查看所有库
4. 点击 **Test Connection** 测试连接
5. 点击 **Apply** → **OK**

配置成功后，可以在 Database 面板中：
- 浏览所有数据库、表结构
- 双击表名查看数据
- 写 SQL 查询并执行
- 导出查询结果

### ⚠️ WSL2 IP 变化问题
WSL2 每次重启后 IP 可能变化。获取最新 IP：
```bash
wsl -d Ubuntu-22.04 -- hostname -I
```

---

## 方式二：Python 脚本（pymysql + pandas）

### 安装依赖：
```bash
pip install pymysql pandas
```

### 快速开始：
运行 `doris_connect_example.py` 查看所有数据集概况。

### 基本用法：
```python
import pymysql
import pandas as pd

# 连接配置
conn = pymysql.connect(
    host="<WSL2_IP>",      # 见上方获取方式；生产代码请从 rag/config.py 或 ECOM_DORIS_HOST 读取
    port=9030,
    user="rag_readonly",  # 只读账号，root 仅限运维
    password="<见 .env>",
    database="taobao",     # 可选：指定数据库
    charset="utf8mb4",
)

# 查询并返回 DataFrame
df = pd.read_sql("SELECT * FROM user_behavior LIMIT 100", conn)
print(df)

conn.close()
```

---

## 可用数据库

> 以下数字与 `docs/DATA_STATS.md`（由 `scripts/refresh_stats.py` 自动生成）保持一致，**口径以该文件为准**。

| 数据库 | 说明 | 表数 | 数据量 |
|--------|------|------|--------|
| `olist` | 巴西电商数据集 | 10（含宽表） | 共 166万，宽表 11.3万 |
| `amazon` | 亚马逊商品与评论 | 4（含宽表） | 共 213万，宽表 41.0万 |
| `instacart` | 杂货配送订单 | 7（含宽表） | 共 7111万，宽表 3382万 |
| `taobao` | 淘宝用户行为 | 2（含宽表） | 2亿（原始+宽表各 1亿） |
| `product_samples` | 商品样本数据 | 2（含宽表） | 1015 |

---

## 常用 SQL 示例

### Olist - 订单金额统计
```sql
SELECT 
    DATE(o.order_purchase_timestamp) AS order_date,
    COUNT(*) AS order_count,
    SUM(oi.price + oi.freight_value) AS total_amount
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY order_date
ORDER BY order_date;
```

### 淘宝 - 用户行为漏斗
```sql
SELECT 
    behavior_type,
    COUNT(*) AS cnt
FROM user_behavior
GROUP BY behavior_type
ORDER BY cnt DESC;
```

### Instacart - 复购率最高的商品
```sql
SELECT 
    p.product_name,
    COUNT(*) AS total_orders,
    SUM(reordered) AS reordered_cnt,
    ROUND(SUM(reordered) / COUNT(*) * 100, 2) AS reorder_rate
FROM order_products_prior op
JOIN products p ON op.product_id = p.product_id
GROUP BY p.product_name
HAVING total_orders > 1000
ORDER BY reorder_rate DESC
LIMIT 20;
```

## 宽表说明

| 宽表 | 粒度 | 构建口径 |
|------|------|----------|
| olist.olist_order_item_wide | 订单商品项（一行=一个订单中的一个商品） | 订单+商品+支付+评论+客户多表 JOIN；金额含 price/freight/item_total_value，订单数需 COUNT(DISTINCT order_id) |
| amazon.amazon_review_wide | 一条评论 | reviews JOIN products，含 score/category_name/price |
| instacart.instacart_order_product_wide | 订单商品项 | order_products JOIN orders/products/aisles/departments，含 reordered/is_first_order |
| taobao.taobao_user_behavior_wide | 一条用户行为 | 原始行为表展开 is_pv/is_cart/is_fav/is_buy 标志位与 behavior_date（不要用 ts 过滤日期） |
| product_samples.jd_products | 一条商品样本 | 爬虫小样本 25 行；price/shop/comments 列因 CSV 字段错位基本为空，可查字段为 name/url |

## 账号与权限

- RAG 及应用查询一律使用只读账号 `rag_readonly`（SELECT_PRIV on 5 库），密码配置在项目根目录 `.env`（格式见 `.env.example`，可被 ECOM_DORIS_PASSWORD 覆盖）
- root 仅用于运维操作（建表/导数/授权），不要写进任何应用配置

## 备份策略

- 原始数据可重导：data/raw/ 下 CSV + scripts/ 导入脚本即完整恢复路径，这是最可靠的"备份"
- 如需 Doris 层备份：用 `mysqldump -h <WSL_IP> -P 9030 -uroot --no-tablespaces <db> > backup.sql` 导出小库（product_samples）；大库（taobao/instacart）依赖原始 CSV 重导即可
- WSL 发行版整体备份：`wsl --export Ubuntu-22.04 D:\backup\ubuntu2204.tar`（含 Doris 全部数据，建议每月一次）

## 环境变量优先级

| 变量 | 默认 | 说明 |
|------|------|------|
| ECOM_DORIS_HOST | 172.27.71.235 | WSL IP 变化时用它覆盖，不改代码 |
| ECOM_DORIS_PORT | 9030 | FE MySQL 端口 |
| ECOM_DORIS_USER | rag_readonly | 查询账号 |
| ECOM_DORIS_PASSWORD | （见 .env，无默认值） | 账号密码 |
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama 服务地址 |
| ECOM_OLLAMA_MODEL | qwen2.5:3b | RAG 生成模型 |
