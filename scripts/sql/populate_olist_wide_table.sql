-- ============================================================
-- 填充 Olist 订单商品宽表
-- ============================================================

INSERT INTO olist.olist_order_item_wide
SELECT
    -- 主键
    oi.order_id,
    oi.order_item_id,
    
    -- 订单信息
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    
    -- 客户信息
    c.customer_id,
    c.customer_unique_id,
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    
    -- 商品信息
    p.product_id,
    p.product_category_name,
    pcnt.product_category_name_english,
    p.product_name_lenght,
    p.product_description_lenght,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    
    -- 卖家信息
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    
    -- 订单项信息
    oi.shipping_limit_date,
    oi.price,
    oi.freight_value,
    
    -- 支付信息 (聚合)
    pay.payment_total_value,
    pay.payment_main_type,
    pay.payment_installments_max,
    pay.payment_method_count,
    
    -- 评论信息 (聚合)
    rev.review_score_avg,
    rev.review_count,
    rev.latest_review_title,
    rev.latest_review_message,
    rev.latest_review_date,
    
    -- 计算字段
    oi.price + oi.freight_value AS item_total_value,
    DATEDIFF(o.order_delivered_customer_date, o.order_delivered_carrier_date) AS delivery_days,
    DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date) AS delivery_delay_days,
    CASE 
        WHEN o.order_delivered_customer_date IS NULL THEN NULL
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 1
        ELSE 0
    END AS is_delivered_on_time
    
FROM olist.order_items oi

-- 关联订单表
LEFT JOIN olist.orders o ON oi.order_id = o.order_id

-- 关联客户表
LEFT JOIN olist.customers c ON o.customer_id = c.customer_id

-- 关联商品表
LEFT JOIN olist.products p ON oi.product_id = p.product_id

-- 关联商品分类翻译表
LEFT JOIN olist.product_category_name_translation pcnt 
    ON p.product_category_name = pcnt.product_category_name

-- 关联卖家表
LEFT JOIN olist.sellers s ON oi.seller_id = s.seller_id

-- 关联支付聚合数据 (按订单)
LEFT JOIN (
    SELECT 
        order_id,
        SUM(payment_value) AS payment_total_value,
        MAX(CASE WHEN rn = 1 THEN payment_type END) AS payment_main_type,
        MAX(payment_installments) AS payment_installments_max,
        COUNT(*) AS payment_method_count
    FROM (
        SELECT 
            order_id,
            payment_type,
            payment_installments,
            payment_value,
            ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC) AS rn
        FROM olist.order_payments
    ) p
    GROUP BY order_id
) pay ON oi.order_id = pay.order_id

-- 关联评论聚合数据 (按订单)
LEFT JOIN (
    SELECT 
        order_id,
        AVG(review_score) AS review_score_avg,
        COUNT(*) AS review_count,
        MAX(CASE WHEN rn = 1 THEN review_comment_title END) AS latest_review_title,
        MAX(CASE WHEN rn = 1 THEN review_comment_message END) AS latest_review_message,
        MAX(CASE WHEN rn = 1 THEN review_creation_date END) AS latest_review_date
    FROM (
        SELECT 
            order_id,
            review_score,
            review_comment_title,
            review_comment_message,
            review_creation_date,
            ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date DESC) AS rn
        FROM olist.order_reviews
    ) r
    GROUP BY order_id
) rev ON oi.order_id = rev.order_id

ORDER BY oi.order_id, oi.order_item_id;
