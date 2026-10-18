# 指标字典（单一事实源）

> 看板、RAG 知识库、评测用例中的所有指标命名以本字典为准。
> 同名指标必须同口径；口径不同必须使用不同名称。
> 最后更新：2026-10-18

## olist（巴西电商，宽表粒度 = 订单商品项）

| 指标名 | 公式 | 粒度 | 状态过滤 | 运费 | 单位 |
|---|---|---|---|---|---|
| 交付 GMV | `SUM(price)` | 商品项求和 | `order_status='delivered'` | 不含 | R$ |
| 商品项总额（含运费） | `SUM(item_total_value)` | 商品项求和 | 无（全状态） | 含 | R$ |
| 交付订单客单价 | `SUM(price) / COUNT(DISTINCT order_id)` | 订单级 | `order_status='delivered'` | 不含 | R$/单 |
| 平均商品项金额（含运费） | `AVG(item_total_value)` | 商品项级 | 无 | 含 | R$/项 |
| 订单数 | `COUNT(DISTINCT order_id)` | 订单级 | 按问题定 | — | 单 |
| 平均交付天数 | `AVG(delivery_days)` | 商品项级（同一订单多行同值） | delivered 且非空 | — | 天 |

- 看板快照使用「商品项总额（含运费）」「平均商品项金额（含运费）」（全状态、含运费），RAG 分析默认使用「交付 GMV」（delivered、不含运费）。**两者不同名不同义，不可直接比较。**
- 连接支付/评论等一对多表前，必须先核验 `(order_id, order_item_id)` 唯一性，避免金额重复累计。

## instacart（生鲜杂货，宽表粒度 = 订单商品项）

| 指标名 | 公式 | 粒度 | 说明 |
|---|---|---|---|
| 商品项重复购买占比 | `SUM(reordered) / COUNT(*)` | 商品项级 | reordered=1 表示该商品项是老用户复购 |
| 用户复购率 | `购买订单数>=2 的用户数 / 总用户数` | 用户级 | `SELECT AVG(order_cnt >= 2) FROM (SELECT user_id, COUNT(DISTINCT order_id) AS order_cnt FROM ... GROUP BY user_id) t` |

- **「复购率」一词单独出现时默认指用户复购率**；两个指标不得混用。历史基准值 59.01% 是商品项重复购买占比，不是用户复购率。

## taobao（用户行为，粒度 = 单条行为）

| 指标名 | 公式 | 说明 |
|---|---|---|
| PV→购买转化率 | `SUM(is_buy) / SUM(is_pv)` | 行为数口径（≈2.25%） |
| 日期过滤 | 用 `behavior_date`，不要用 `ts` | ts 是时间戳 |

## amazon（商品评论，粒度 = 单条评论）

| 指标名 | 公式 | 说明 |
|---|---|---|
| 5 星占比 | `SUM(score=5) / COUNT(*)` | score 为 1-5 整数 |
| 平均评分 | `AVG(score)` | 不加额外价格过滤 |

## product_samples（京东商品样本）

| 指标名 | 公式 | 说明 |
|---|---|---|
| 名称字符数 | `CHAR_LENGTH(name)` | 中文字符数；`LENGTH` 是字节数，含义不同不得混用 |
