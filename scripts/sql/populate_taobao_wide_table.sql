-- ============================================================
-- 填充淘宝用户行为宽表
-- ============================================================

INSERT INTO taobao.taobao_user_behavior_wide
SELECT
    -- Key 列
    user_id,
    item_id,
    ts,
    
    -- 基础信息
    category_id,
    behavior_type,
    
    -- 时间维度
    DATE(FROM_UNIXTIME(ts)) AS behavior_date,
    HOUR(FROM_UNIXTIME(ts)) AS behavior_hour,
    (DAYOFWEEK(FROM_UNIXTIME(ts)) + 5) % 7 AS behavior_dow,
    WEEK(FROM_UNIXTIME(ts)) AS behavior_week,
    MONTH(FROM_UNIXTIME(ts)) AS behavior_month,
    
    -- 行为分类标记
    CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END AS is_pv,
    CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END AS is_cart,
    CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END AS is_fav,
    CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END AS is_buy,
    CASE 
        WHEN behavior_type = 'pv' THEN 'view'
        WHEN behavior_type IN ('cart', 'fav') THEN 'interact'
        WHEN behavior_type = 'buy' THEN 'purchase'
    END AS behavior_category,
    
    -- 时段分类
    CASE 
        WHEN HOUR(FROM_UNIXTIME(ts)) BETWEEN 0 AND 5 THEN '凌晨'
        WHEN HOUR(FROM_UNIXTIME(ts)) BETWEEN 6 AND 11 THEN '上午'
        WHEN HOUR(FROM_UNIXTIME(ts)) BETWEEN 12 AND 17 THEN '下午'
        WHEN HOUR(FROM_UNIXTIME(ts)) BETWEEN 18 AND 22 THEN '晚上'
        ELSE '深夜'
    END AS time_period,
    
    -- 是否周末
    CASE WHEN (DAYOFWEEK(FROM_UNIXTIME(ts)) + 5) % 7 >= 5 THEN 1 ELSE 0 END AS is_weekend
    
FROM (
    SELECT 
        user_id,
        item_id,
        category_id,
        behavior_type,
        timestamp AS ts
    FROM taobao.user_behavior
) t;
