# 数据统计（DATA_STATS）

> 本文件由 `scripts/refresh_stats.py` 自动生成，**是全部文档中数据口径的唯一事实源**。
> 生成时间：2026-10-18 00:00:45

## 总览

| 指标 | 值 |
|------|-----|
| 数据库数 | 5 |
| 表总数 | 25 |
| 总行数 | 275,207,344 |

## olist（10 张表，共 1,663,400 行）

| 表 | 行数 | 备注 |
|----|------|------|
| customers | 99,441 |  |
| geolocation | 1,000,163 |  |
| olist_order_item_wide | 112,651 | （宽表） |
| order_items | 112,651 |  |
| order_payments | 103,887 |  |
| order_reviews | 99,046 |  |
| orders | 99,442 |  |
| product_category_name_translation | 72 |  |
| products | 32,952 |  |
| sellers | 3,095 |  |

## amazon（4 张表，共 2,132,289 行）

| 表 | 行数 | 备注 |
|----|------|------|
| amazon_review_wide | 409,961 | （宽表） |
| categories | 249 |  |
| products | 1,312,118 |  |
| reviews | 409,961 |  |

## instacart（7 张表，共 71,109,026 行）

| 表 | 行数 | 备注 |
|----|------|------|
| aisles | 135 |  |
| departments | 22 |  |
| instacart_order_product_wide | 33,819,108 | （宽表） |
| order_products_prior | 32,434,490 |  |
| order_products_train | 1,384,618 |  |
| orders | 3,421,084 |  |
| products | 49,569 |  |

## taobao（2 张表，共 200,301,614 行）

| 表 | 行数 | 备注 |
|----|------|------|
| taobao_user_behavior_wide | 100,150,807 | （宽表） |
| user_behavior | 100,150,807 |  |

## product_samples（2 张表，共 1,015 行）

| 表 | 行数 | 备注 |
|----|------|------|
| jd_products | 25 | （宽表） |
| products_sample | 990 |  |

## 数据更新日历

| 数据集 | 性质 | 更新策略 |
|--------|------|----------|
| olist / amazon / instacart / taobao | 静态学术数据集 | **无需更新**，入库即最终态 |
| product_samples.jd_products | 爬虫样本 | 建议**每月刷新一次**（月初） |

### jd_products 月度刷新链路（按序执行）

1. 采集：京东商品采集脚本（本地 `scripts/03~09`，开源仓库从略）
2. 入库：重跑对应 Doris 导入脚本（TRUNCATE 后重新 STREAM LOAD）
3. 统计：`conda run -n pds python scripts/refresh_stats.py`（重新生成本文件）
4. 看板：`conda run -n pds python scripts/16_refresh_dashboard_data.py`，然后 website 目录 commit + push
5. 知识库：`conda run -n pds python rag/knowledge_builder.py`（表文档内嵌行数，数据变了必须重建）
6. 回归：`conda run -n pds python rag/evals/run_eval.py`，对比 docs/benchmark/ 历史报告

### 日常巡检

`conda run -n pds python scripts/health_check.py`：宽表行数异动 + 关键字段空值率告警，
基线快照在 docs/health/last_snapshot.json，退出码 0=健康 1=有告警。
