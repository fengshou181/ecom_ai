-- ============================================================
-- Olist 电商订单商品宽表 (7表整合)
-- 粒度: 订单项 (order_id + order_item_id)
-- 整合表: orders + customers + order_items + products + 
--         product_category_name_translation + sellers + 
--         order_payments(聚合) + order_reviews(聚合)
-- ============================================================

-- 1. 删除已存在的宽表
DROP TABLE IF EXISTS olist.olist_order_item_wide;

-- 2. 创建宽表 (Doris Duplicate Key 模型)
CREATE TABLE olist.olist_order_item_wide (
    -- ===== 主键 =====
    order_id VARCHAR(50) COMMENT '订单ID',
    order_item_id INT COMMENT '订单项序号',
    
    -- ===== 订单信息 (orders表) =====
    order_status VARCHAR(20) COMMENT '订单状态',
    order_purchase_timestamp DATETIME COMMENT '下单时间',
    order_approved_at DATETIME COMMENT '支付确认时间',
    order_delivered_carrier_date DATETIME COMMENT '物流揽收时间',
    order_delivered_customer_date DATETIME COMMENT '送达时间',
    order_estimated_delivery_date DATETIME COMMENT '预计送达时间',
    
    -- ===== 客户信息 (customers表) =====
    customer_id VARCHAR(50) COMMENT '客户ID',
    customer_unique_id VARCHAR(50) COMMENT '客户唯一标识',
    customer_zip_code_prefix INT COMMENT '客户邮编前缀',
    customer_city VARCHAR(100) COMMENT '客户城市',
    customer_state VARCHAR(10) COMMENT '客户州',
    
    -- ===== 商品信息 (products表 + 分类翻译表) =====
    product_id VARCHAR(50) COMMENT '商品ID',
    product_category_name VARCHAR(100) COMMENT '商品分类名(葡萄牙语)',
    product_category_name_english VARCHAR(100) COMMENT '商品分类名(英语)',
    product_name_lenght INT COMMENT '商品名称长度',
    product_description_lenght INT COMMENT '商品描述长度',
    product_photos_qty INT COMMENT '商品图片数量',
    product_weight_g INT COMMENT '商品重量(克)',
    product_length_cm INT COMMENT '商品长度(厘米)',
    product_height_cm INT COMMENT '商品高度(厘米)',
    product_width_cm INT COMMENT '商品宽度(厘米)',
    
    -- ===== 卖家信息 (sellers表) =====
    seller_id VARCHAR(50) COMMENT '卖家ID',
    seller_zip_code_prefix INT COMMENT '卖家邮编前缀',
    seller_city VARCHAR(100) COMMENT '卖家城市',
    seller_state VARCHAR(10) COMMENT '卖家州',
    
    -- ===== 订单项信息 (order_items表) =====
    shipping_limit_date DATETIME COMMENT '发货截止日期',
    price DOUBLE COMMENT '商品单价',
    freight_value DOUBLE COMMENT '运费',
    
    -- ===== 支付信息 (order_payments表 - 按订单聚合) =====
    payment_total_value DOUBLE COMMENT '订单总支付金额',
    payment_main_type VARCHAR(30) COMMENT '主要支付方式',
    payment_installments_max INT COMMENT '最大分期数',
    payment_method_count INT COMMENT '支付方式数量',
    
    -- ===== 评论信息 (order_reviews表 - 按订单聚合) =====
    review_score_avg DOUBLE COMMENT '平均评分',
    review_count INT COMMENT '评论数量',
    latest_review_title VARCHAR(200) COMMENT '最新评论标题',
    latest_review_message TEXT COMMENT '最新评论内容',
    latest_review_date DATETIME COMMENT '最新评论时间',
    
    -- ===== 计算字段 =====
    item_total_value DOUBLE COMMENT '订单项总价值 = 单价 + 运费',
    delivery_days INT COMMENT '实际配送天数(送达-揽收)',
    delivery_delay_days INT COMMENT '延迟天数(实际送达-预计送达)',
    is_delivered_on_time TINYINT COMMENT '是否按时送达 1=是 0=否'
) 
ENGINE=OLAP
DUPLICATE KEY(order_id, order_item_id)
COMMENT 'Olist电商订单商品宽表(7表整合)'
DISTRIBUTED BY HASH(order_id) BUCKETS 10
PROPERTIES (
    "replication_num" = "1",
    "compression" = "LZ4"
);
