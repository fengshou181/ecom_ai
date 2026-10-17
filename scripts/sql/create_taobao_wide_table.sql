-- ============================================================
-- 淘宝用户行为宽表 (单表增强)
-- 粒度: 用户行为记录
-- 增强: 时间维度字段、行为类型分类
-- ============================================================

-- 1. 删除已存在的宽表
DROP TABLE IF EXISTS taobao.taobao_user_behavior_wide;

-- 2. 创建宽表
CREATE TABLE taobao.taobao_user_behavior_wide (
    -- ===== Key 列 (必须是前缀) =====
    user_id BIGINT COMMENT '用户ID',
    item_id BIGINT COMMENT '商品ID',
    ts BIGINT COMMENT '行为时间戳',
    
    -- ===== 基础信息 =====
    category_id BIGINT COMMENT '商品类目ID',
    behavior_type VARCHAR(10) COMMENT '行为类型: pv/cart/fav/buy',
    
    -- ===== 时间维度 =====
    behavior_date DATE COMMENT '行为日期',
    behavior_hour INT COMMENT '行为小时(0-23)',
    behavior_dow INT COMMENT '星期几(0=周一, 6=周日)',
    behavior_week INT COMMENT '一年中第几周',
    behavior_month INT COMMENT '月份',
    
    -- ===== 行为分类 =====
    is_pv TINYINT COMMENT '是否浏览',
    is_cart TINYINT COMMENT '是否加购',
    is_fav TINYINT COMMENT '是否收藏',
    is_buy TINYINT COMMENT '是否购买',
    behavior_category VARCHAR(20) COMMENT '行为大类: view/interact/purchase',
    
    -- ===== 时段分类 =====
    time_period VARCHAR(20) COMMENT '时段: 凌晨/上午/下午/晚上/深夜',
    is_weekend TINYINT COMMENT '是否周末'
) 
ENGINE=OLAP
DUPLICATE KEY(user_id, item_id, ts)
COMMENT '淘宝用户行为宽表(时间维度增强)'
DISTRIBUTED BY HASH(user_id) BUCKETS 30
PROPERTIES (
    "replication_num" = "1",
    "compression" = "LZ4"
);
