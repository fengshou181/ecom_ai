# 电商市场数据分析 AI 助手 (ecom_ai)

> 基于多源电商数据，搭建自动化分析 + RAG 智能问答系统，并将分析成果展示在个人作品集网站上。

---

## 项目概览

| 属性 | 值 |
|------|-----|
| **项目名称** | 电商市场数据分析 AI 助手 |
| **项目路径** | E:\ecom_ai |
| **所有者** | 郑年丰（丰年） |
| **职业** | 数据工程师 / Data Engineer |
| **个人域名** | zfengnian.top |
| **GitHub 仓库** | fengshou181/portfolio（website 子目录的 Git 仓库） |
| **技术栈** | Apache Doris + PySpark + Python + Chart.js + Cloudflare Pages |

---

## 项目目标

1. 多源电商数据整合 - 将 Olist、Amazon、Instacart、淘宝 4 个数据集统一导入 Apache Doris
2. 宽表建模 - 为每个数据集构建多表整合的分析宽表
3. 探索性数据分析 (EDA) - 多维度可视化分析，生成 HTML 报告
4. 数据可视化看板 - 将分析成果整合到个人作品集网站
5. RAG 智能问答 - 基于 Chroma + LangChain + 本地 Ollama 的 Text-to-SQL 问答系统（已完成）

---

## 完整目录结构

E:\ecom_ai\
├── README.md                          # 本文档（项目总说明）
├── DORIS连接指南.md                     # Apache Doris 连接配置指南
├── browse_data.py                     # Doris 数据交互式浏览脚本
├── dataset_browser.html               # 网页版数据表格查看器
├── ecom_ai.duckdb                     # DuckDB 嵌入式分析数据库
│
├── data/                              # 数据目录
│   ├── raw/                           # 原始数据（不要修改）
│   │   ├── olist/                    # Olist 巴西电商 9 张表 CSV
│   │   ├── amazon_reviews/            # Amazon 商品与评论 CSV
│   │   ├── instacart/                 # Instacart 生鲜杂货 6 张表 CSV
│   │   ├── taobao_behavior/           # 淘宝用户行为（1亿+条）
│   │   └── product_data/             # 爬虫采集的商品数据
│   ├── processed/                    # 清洗后的数据
│   │   └── olist/                    # Olist 宽表（CSV + Parquet）
│   └── analysis/                      # 分析结果
│
├── scripts/                           # 代码脚本
│   ├── sql/                           # SQL 脚本（宽表建表+填充）
│   ├── 02_product_spider.py           # 电商商品爬虫（练习）
│   ├── 03_jd_spider.py                # 京东商品爬虫（DrissionPage）
│   ├── 04~09_jd_*.py                 # 京东爬虫调试工具集
│   ├── 10_taobao_eda_pyspark.py       # 淘宝 EDA（PySpark）
│   ├── 11_olist_eda.py                # Olist EDA 分析
│   ├── 12_taobao_data_cleaning.py     # 淘宝数据清洗
│   ├── 13_olist_data_cleaning.py      # Olist 数据清洗
│   ├── 14_olist_integration.py        # Olist 9表整合为宽表
│   ├── 15_build_duckdb_warehouse.py  # DuckDB 统一数仓构建
│   ├── 16_refresh_dashboard_data.py  # 看板数据刷新（查 Doris 生成 website/dashboard-data.js）
│   ├── refresh_stats.py              # 统计刷新（生成 docs/DATA_STATS.md，数据口径事实源）
│   ├── deploy_doris.sh                # Doris 部署脚本
│   ├── start_doris.sh / start_be.sh  # 启动 Doris
│   ├── import_*.sh                    # 各数据集导入脚本
│   ├── create_*_tables.sql            # 各数据集建表 SQL
│   └── check_doris_health.sh          # Doris 健康检查
│
├── assets/data_samples/               # JSON 格式样本数据
├── docs/eda_report.html               # EDA 可视化报告（22张图表）
├── docs/DATA_STATS.md                 # 数据统计（refresh_stats.py 自动生成，口径事实源）
├── models/chroma_db/                  # Chroma 向量库（118 条 schema 知识文档）
├── rag/                               # RAG 智能问答系统（2026-10-17 搭建，全本地）
│   ├── config.py                      # 集中配置（Doris/Ollama/Chroma，WSL IP 可用环境变量覆盖）
│   ├── doris_client.py                # Doris 只读查询客户端（30s 超时）
│   ├── sql_validator.py               # SQL 安全校验（仅 SELECT + 自动 LIMIT 1000）
│   ├── schema_extractor.py            # 宽表元数据抽取
│   ├── knowledge_builder.py           # Chroma 知识库构建（表/字段/示例SQL/业务知识）
│   ├── retriever.py                   # 相关 schema 检索（bge-small-zh 嵌入）
│   ├── sql_chain.py                   # Text-to-SQL 核心链路（生成→校验→执行→重试≤2）
│   ├── cli.py                         # 命令行入口（--bench 5库基准验证）
│   └── app.py                         # Streamlit 聊天界面（端口 8501）
├── output/reports/                    # 分析报告输出
│
├── website/                           # 个人作品集网站（独立 Git 仓库）
│   ├── .github/workflows/deploy.yml   # Cloudflare Pages 部署工作流
│   ├── TRAE_CN_项目说明.md             # 网站详细技术文档（AI 必读）
│   ├── index.html                     # 首页
│   ├── ecommerce-dashboard.html       # 电商数据看板
│   ├── dashboard-data.js              # 看板外置数据（16_refresh_dashboard_data.py 生成）
│   ├── about/skills/experience/projects.html
│   ├── articles/moments/friends/guestbook/contact/changelog.html
│   ├── style.css / common.js
│   └── images/
│
└── .idea/                             # PyCharm 配置

---

## Apache Doris 数据库

### 部署信息
- Doris 版本: 2.1.7
- 部署方式: WSL2 + Ubuntu 22.04
- 架构: 1 FE + 1 BE（单机）
- MySQL 协议端口: 9030
- 连接: Host=WSL2 IP, User=root, Password=空

### 数据库一览
> 精确数字见 `docs/DATA_STATS.md`（由 `scripts/refresh_stats.py` 自动生成，是全部文档数据口径的唯一事实源）。

| 数据库 | 说明 | 表数 | 数据量 |
|--------|------|------|--------|
| olist | 巴西电商 | 9+1宽表 | 共 166万，宽表 11.3万 |
| amazon | 亚马逊评论 | 3+1宽表 | 共 213万，宽表 41.0万 |
| instacart | 生鲜杂货 | 6+1宽表 | 共 7111万，宽表 3382万 |
| taobao | 淘宝行为 | 1+1宽表 | 2亿（原始+宽表各 1亿） |
| product_samples | 商品样本 | 2 | 1015 |
共 25 张表、2.75 亿行（宽表与原始表存在重复计入，口径见 DATA_STATS.md）。

### 连接方式
WSL2 IP 每次重启可能变化，获取最新 IP: wsl -d Ubuntu-22.04 -- hostname -I
Python 连接: pymysql.connect(host="WSL2_IP", port=9030, user="root", password="")
也可用 DataGrip/DBeaver，选 MySQL 数据源，端口 9030。
详见 DORIS连接指南.md

---

## 数据集详情

### 1. Olist 巴西电商 (olist)
9 张原始表 + 1 张宽表 olist_order_item_wide（112,651 行）
核心发现: 两年 GMV 增长超 10 倍; 平均交付 12 天; 评论 5 分占比 57%

### 2. Amazon 评论 (amazon)
3 张原始表 + 1 张宽表 amazon_review_wide（409,961 行）
核心发现: 5 星好评占 63.8%

### 3. Instacart 生鲜杂货 (instacart)
6 张原始表 + 1 张宽表 instacart_order_product_wide（33,819,108 行）
核心发现: 生鲜复购率超 70%, 香蕉最热销

### 4. 淘宝用户行为 (taobao)
1 张表, 100,150,807 行
字段: user_id, item_id, category_id, behavior_type(pv/fav/cart/buy), timestamp
核心发现: PV 到购买转化率 2.25%

---

## 个人作品集网站

### 基本信息
- 路径: E:\ecom_ai\website
- 域名: zfengnian.top
- 托管: Cloudflare Pages (项目名 fengnian-portfolio)
- GitHub 仓库: fengshou181/portfolio
- 自动部署: Cloudflare Pages Git 集成 (push 到 main 自动部署)
- 技术栈: HTML + CSS + 原生JS + Chart.js 4.x
- 页面数: 12 个 HTML 页面

### 部署流程
1. 在 E:\ecom_ai\website 修改文件
2. git add . && git commit -m "更新" && git push
3. Cloudflare 自动部署, zfengnian.top 自动更新

### 网站详细文档
详见 website/TRAE_CN_项目说明.md (AI 必读)

### 电商数据看板
ecommerce-dashboard.html: Chart.js 4.x, 4 个数据集 Tab, 22 张图表 + 漏斗
数据来自外置 dashboard-data.js（scripts/16_refresh_dashboard_data.py 查 Doris 生成），缺失时回退内置数据

---

## EDA 分析报告
docs/eda_report.html: 22 张可视化图表, 覆盖 4 个数据集

---

## 项目进度

### 已完成
- [x] 数据采集 (Olist/Amazon/Instacart/淘宝/商品样本)
- [x] 爬虫开发 (京东 DrissionPage + 练习爬虫)
- [x] Doris 部署 (WSL2 + Ubuntu 22.04 + Doris 2.1.7)
- [x] 数据导入 (5库21表约1.4亿行)
- [x] 宽表建模 (4个数据集宽表)
- [x] EDA 分析 (4个数据集)
- [x] 可视化报告 (eda_report.html, 22张图表)
- [x] 网站开发 (12页面作品集)
- [x] 数据看板 (ecommerce-dashboard.html)
- [x] 网站部署 (Cloudflare Pages + zfengnian.top)
- [x] DuckDB 数仓构建

### 已完成（2026-10-17 新增）
- [x] RAG 智能问答系统 (Ollama qwen2.5:3b + Chroma + LangChain，Text-to-SQL，全本地零成本，基准 5/5 通过)
- [x] RAG 性能优化 (7b→3b + top_k 8→6 + 砍 LLM 解读环节，热态单问 0.5-2.5s)
- [x] Streamlit 交互界面 (rag/app.py，http://localhost:8501)
- [x] 数据看板实时化 (dashboard-data.js 外置数据 + 自动刷新脚本，已上线)

### 待完成
- [ ] RAG 评测集 (rag/evals/，30+ 用例，见 docs/2026-10-17-项目改进建议.md)
- [ ] 网站域名缓存清除

---

## 重要约束

### Doris 相关
1. WSL2 IP 会变化 - 每次重启后需更新连接配置
2. BE 内存限制需用百分比格式 (mem_limit = 80%)
3. Stream Load 需设置 max_filter_ratio = 1%
4. CSV 含双引号会导致字段错位

### 爬虫相关
1. 京东爬虫必须同一浏览器会话 - 更换环境导致 Cookie 失效
2. 京东爬虫仅适用于少量数据 (几十到几百条)
3. 京东 PC 端强制登录
4. 京东新版采用 React CSS Modules - 类名带哈希

### 网站部署相关
1. 网站通过 Cloudflare Pages Git 集成部署
2. Cloudflare CDN 缓存 - 更新后可能需手动清除
3. 自定义域名 zfengnian.top - DNS 指向 fengnian-portfolio.pages.dev

---

## 快速开始

### 0. 环境初始化（新机器）
conda create -n pds python=3.11 -y && conda activate pds
pip install -r requirements.txt
ollama pull qwen2.5:3b   # RAG 用本地模型

### 1. 启动 Doris (在 WSL2 中)
cd /opt/apache-doris-2.1.7
sh bin/start_fe.sh --daemon
sh bin/start_be.sh --daemon

### 2. 连接 Doris
Python: pymysql.connect(host="<WSL2_IP>", port=9030, user="rag_readonly", password="<见 .env>")
或 DataGrip/DBeaver, MySQL 数据源, 端口 9030（连接参数以 rag/config.py 环境变量为准，root 空密码仅限本机运维）

### 3. 运行 EDA
cd E:\ecom_ai
python scripts/11_olist_eda.py
python scripts/10_taobao_eda_pyspark.py (需 PySpark)

### 4. 本地预览网站
cd E:\ecom_ai\website
python -m http.server 8000

### 5. 部署网站更新
cd E:\ecom_ai\website
git add . && git commit -m "update" && git push

### 6. 启动 RAG 智能问答
前置: Doris 已启动 + Ollama 服务运行中 (ollama serve) + 模型已拉取 (ollama pull qwen2.5:3b)
网页: conda run -n pds python -m streamlit run E:\ecom_ai\rag\app.py --server.port 8501
命令行: conda run -n pds python E:\ecom_ai\rag\cli.py (交互模式)
基准验证: conda run -n pds python E:\ecom_ai\rag\cli.py --bench (5库各1问)
WSL IP 变化后: set ECOM_DORIS_HOST=新IP 再启动，或直接改 rag/config.py

---

## 技术栈总结
| 模块 | 技术 |
|------|------|
| OLAP 数据库 | Apache Doris 2.1.7 (WSL2) |
| 大数据处理 | PySpark 3.5.3 |
| 嵌入式分析 | DuckDB |
| 数据处理 | Python + Pandas |
| 爬虫 | DrissionPage + BeautifulSoup |
| 数据可视化 | Chart.js 4.x + Matplotlib/Plotly |
| 前端 | HTML + CSS + 原生JS |
| 托管 | Cloudflare Pages + GitHub |
| 本地大模型 | Ollama (qwen2.5:3b) |
| 向量数据库 | Chroma 1.5.9 (bge-small-zh-v1.5 嵌入) |
| RAG 框架 | LangChain 1.4.2 (Text-to-SQL) |
| Web 界面 | Streamlit 1.64.0 |
| 开发环境 | PyCharm + WSL2 + Ubuntu 22.04 |
| JDK | OpenJDK 21 |
| Python 环境 | conda pds 环境 |

---

*本文档最后更新于 2026-10-17，用于帮助 AI 助手快速理解项目全貌。*
