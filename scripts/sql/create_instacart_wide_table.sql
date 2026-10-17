-- ============================================================
-- Instacart 订单商品宽表 (5表整合)
-- 粒度: 订单商品项 (order_id + product_id)
-- 整合表: order_products_train + order_products_prior (合并) 
--         + orders + products + aisles + departments
-- ============================================================

-- 1. 删除已存在的宽表
DROP TABLE IF EXISTS instacart.instacart_order_product_wide;

-- 2. 创建宽表
CREATE TABLE instacart.instacart_order_product_wide (
    -- ===== 订单商品信息 =====
    order_id INT COMMENT '订单ID',
    product_id INT COMMENT '商品ID',
    add_to_cart_order INT COMMENT '加入购物车顺序',
    reordered TINYINT COMMENT '是否重复购买 1=是 0=否',
    dataset_type VARCHAR(10) COMMENT '数据集类型: prior/train',
    
    -- ===== 订单信息 =====
    user_id INT COMMENT '用户ID',
    eval_set VARCHAR(10) COMMENT '评估集: prior/train/test',
    order_number INT COMMENT '用户第N笔订单',
    order_dow INT COMMENT '订单星期几(0-6)',
    order_hour_of_day INT COMMENT '订单小时(0-23)',
    days_since_prior_order DOUBLE COMMENT '距上一单天数',
    
    -- ===== 商品信息 =====
    product_name VARCHAR(300) COMMENT '商品名称',
    aisle_id INT COMMENT '过道ID',
    department_id INT COMMENT '部门ID',
    
    -- ===== 过道信息 =====
    aisle VARCHAR(100) COMMENT '过道名称',
    
    -- ===== 部门信息 =====
    department VARCHAR(50) COMMENT '部门名称',
    
    -- ===== 计算字段 =====
    is_first_order TINYINT COMMENT '是否首单(days_since_prior_order为空)'
) 
ENGINE=OLAP
DUPLICATE KEY(order_id, product_id)
COMMENT 'Instacart订单商品宽表(5表整合)'
DISTRIBUTED BY HASH(order_id) BUCKETS 20
PROPERTIES (
    "replication_num" = "1",
    "compression" = "LZ4"
);
