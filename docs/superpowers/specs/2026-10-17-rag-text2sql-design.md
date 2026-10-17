# RAG 智能问答系统（Text-to-SQL）设计文档

- 日期：2026-10-17
- 项目：ecom_ai（E:\ecom_ai）
- 状态：已实现并验证（2026-10-17，5 库基准 5/5 通过；后续调优见第 12 节变更记录）

## 1. 目标

基于本地大模型构建电商数据自然语言问答系统：用户用中文提问，系统自动检索相关表结构、生成 SQL、查询 Apache Doris、并用自然语言解读结果。覆盖 olist / amazon / instacart / taobao / product_samples 全部 5 个数据库。

## 2. 已确认的关键决策

| 决策点 | 结论 |
|--------|------|
| LLM | 本地 Ollama，模型 qwen2.5:7b（备选降级 qwen2.5:3b） |
| 交互界面 | Streamlit 网页（同时完成 README 待办"Streamlit 交互界面"） |
| 问答范围 | 全 5 库 |
| 架构方案 | Text-to-SQL RAG，Chroma 内同时存放少量业务知识文档作兜底 |
| 嵌入模型 | BAAI/bge-small-zh-v1.5（sentence-transformers，本地 CPU 运行） |

## 3. 运行环境

- OS：Windows 11，conda `pds` 环境（已有 langchain 1.4.2 / chromadb 1.5.9 / sentence-transformers 6.1.0 / streamlit 1.64.0 / SQLAlchemy）
- 需补装：`pymysql`、`ollama`（Python 客户端）
- 需安装：Ollama for Windows + `ollama pull qwen2.5:7b`（约 4.7GB）
- Doris：WSL2 Ubuntu-22.04，Doris 2.1.7，MySQL 协议 9030 端口，root 空密码；WSL IP 动态（当前 172.27.71.235），连接配置需支持改 IP
- 硬件：Ryzen 5 5600H / 32GB 内存 / RTX 3050 Ti 4GB（Ollama 自动 GPU 分流）

## 4. 总体架构

```
用户提问 (Streamlit)
  → 检索层: 问题嵌入 → Chroma top-k（表/字段/示例SQL）
  → 生成层: Prompt 组装 → qwen2.5:7b 生成 SQL
  → 安全层: SQL 校验（仅 SELECT / 禁危险关键字 / 自动 LIMIT）
  → 执行层: pymysql → Doris（只读，30s 超时）
  → 解读层: qwen2.5 将结果转自然语言
  → 界面: 回答文本 + SQL(可折叠) + 结果表格
```

## 5. 目录结构与模块职责（E:\ecom_ai\rag\）

| 文件 | 职责 |
|------|------|
| `config.py` | 集中配置：Doris host/port/user、Ollama base_url 与模型名、Chroma 持久化路径、嵌入模型名、LIMIT 上限（1000）、查询超时（30s）、重试次数（2） |
| `doris_client.py` | pymysql 连接封装；`query(sql) -> pandas.DataFrame`；连接失败时给出 WSL IP 检查提示 |
| `schema_extractor.py` | 从 Doris `information_schema.COLUMNS` 抽取 5 库宽表的字段名/类型/注释；从建表 SQL 文件头部注释提取表粒度说明 |
| `knowledge_builder.py` | 构建 Chroma 知识库（4 类文档，见第 6 节）；支持全量重建 |
| `retriever.py` | 问题嵌入 + top-k 检索（默认 k=8），返回拼接好的 schema 上下文字符串 |
| `sql_validator.py` | SQL 安全校验：必须以 SELECT 开头；拒绝 DELETE/DROP/INSERT/UPDATE/ALTER/TRUNCATE/GRANT 等；无 LIMIT 时自动追加 LIMIT 1000 |
| `sql_chain.py` | 核心链路：检索 → 生成 SQL → 校验 → 执行 → 失败重试（≤2 次，错误回喂）→ 结果解读；返回 dict（answer/sql/dataframe/error） |
| `app.py` | Streamlit 聊天界面：会话历史、SQL 折叠展示、表格渲染、错误提示 |
| `cli.py` | 命令行入口；内置 5 个基准问题（每库 1 个）用于端到端验证 |

模块间依赖：app/cli → sql_chain → (retriever, doris_client, sql_validator)；knowledge_builder → (schema_extractor, doris_client)。

## 6. Chroma 知识库内容（4 类文档）

1. **表级文档**：库名、表名、粒度说明（来自 `scripts/sql/create_*_wide_table.sql` 头部注释）
2. **字段级文档**：`库.表.字段` + 类型 + 中文注释（来自 information_schema，每字段一条）
3. **示例 SQL**：每数据集 3-5 个典型查询（GMV 趋势、复购率、转化漏斗、评分分布等，从 EDA 脚本提炼），格式为"问题 → SQL"对
4. **业务知识**：数据集背景、口径定义（如"PV 到购买转化率 = buy/pv"）、可回答问题范围说明

持久化路径：`E:\ecom_ai\models\chroma_db\`

## 7. 查询时数据流

1. 用户问题 → bge-small-zh 嵌入 → Chroma 检索 top-8（表+字段+示例混合）
2. 组装 Prompt（schema 上下文 + 示例 SQL + Doris SQL 方言注意事项 + 用户问题）→ qwen2.5:7b 生成 SQL
3. validator 校验；不合法 → 错误信息回喂 LLM 重新生成（计入重试次数）
4. pymysql 执行 → DataFrame
5. 问题 + 结果（截断展示，如前 50 行）→ qwen2.5 生成中文解读
6. Streamlit 展示：解读文本 / SQL（折叠）/ 结果表格

## 8. 错误处理

| 场景 | 策略 |
|------|------|
| SQL 语法/执行错误 | 错误回喂 LLM 重试，最多 2 次；仍失败则展示错误与最后 SQL |
| 查询结果为空 | 回答"未查到数据"，建议调整条件 |
| Ollama 未启动/超时 | 界面提示"请检查 ollama serve 是否运行" |
| Doris 连接失败 | 提示检查 WSL 与 Doris 状态、WSL IP 是否变化 |
| 检索不到相关表 | 降级：仅用业务知识文档回答（不执行 SQL） |
| 与数据无关的问题 | 礼貌拒绝并说明可问范围 |

## 9. 安全设计

- validator 强制只读（仅 SELECT），DDL/DML 一律拦截
- SQL 无 LIMIT 时自动追加 `LIMIT 1000`
- 单条查询 30s 超时（防止 taobao 亿级表全表扫描卡死）
- 全链路本地运行，无数据出机

## 10. 测试策略

- `cli.py` 内置基准问题 5 个（每库 1 个，如"olist 两年 GMV 增长多少""淘宝 PV 到购买转化率是多少"），全部跑通即端到端可用
- validator 规则、schema 抽取结果用直接断言验证（脚本内自检）

## 11. 实施依赖清单

1. 安装 Ollama（Windows）→ `ollama pull qwen2.5:7b`
2. `pip install pymysql ollama`（pds 环境）
3. 首次构建知识库：启动 WSL + Doris，运行 knowledge_builder
4. 嵌入模型首次使用自动从 HuggingFace 下载（约 100MB；网络受限时切换 ModelScope 源）

## 12. 变更记录（实施后调优，2026-10-17）

实现按本设计跑通后，当天完成一轮性能优化（ABC 组合），实测 5 库基准 **5/5 通过、总耗时 76.1s**（热态单问 0.5–2.5s；首问 ~70s 为 Ollama 模型冷加载，仅发生一次）。

| 变更 | 原设计 | 实际 | 依据 |
|------|--------|------|------|
| LLM 模型 | qwen2.5:7b | **qwen2.5:3b**（config.py:14） | RTX 3050 Ti 4GB 显存无法全量装载 7b；3b 内存占用 4.7GB→2GB，推理显著提速，准确率靠上下文兜底维持 |
| 检索 top_k | 8 | **6**（config.py:24） | top_k=4 时 amazon / product_samples 两题退化（上下文不足）；6 为准确率与 prompt 长度的折中 |
| 结果解读层 | qwen2.5 生成中文解读（§4/§7） | **已删除**，改为 `format_answer()` 纯格式化直出（sql_chain.py:62） | 每问省一次完整 LLM 推理，热态延迟降至 0.5–2.5s；代价是回答退化为结果表格 |
| 表名兜底 | 无 | 新增 `_qualify_tables()`（sql_chain.py:46）+ `DATABASE_DEFAULT_TABLE`（config.py:30） | 3b 偶发漏写库名前缀（`FROM product_samples`），程序级补全为该库主数据表，比重试可靠 |

当前有效的性能数据来自 `cli.py --bench`（仅判"有无回答"）。精确的 P50/P95 延迟与口径准确率待 RAG 评测集（`docs/2026-10-17-项目改进建议.md` §2.1）建成后补齐。

## 13. 模型选型 A/B（2026-10-18）

评测集建成后对 3b / 7b 做了同集对比（30 用例，报告见 `docs/benchmark/2026-10-17.md`、`2026-10-18.md`）：

| 指标 | qwen2.5:3b | qwen2.5:7b |
|------|-----------|-----------|
| 执行成功率 | 100% | 93.3% |
| 结果准确率 | 86.7% | 90.0% |
| P50 / P95 延迟 | 1.1s / 2.8s | 5.2s / 21.6s |
| 平均重试 | 0.00 | 0.13 |

结论：**维持 3b 为默认**。准确率仅差 1 题且 7b 失败为执行错误（ORDER BY/HAVING 引用未定义别名），本机 CPU 推理下 3b 延迟低 5 倍、内存省一半。7b 在语义理解类难题（聚合幻觉）上更强，后续若上 GPU 可用评测集随时复测。选型依据已固化在 config.py 注释中。
