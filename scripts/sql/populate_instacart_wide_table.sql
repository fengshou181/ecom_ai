-- ============================================================
-- 填充 Instacart 订单商品宽表
-- 合并 order_products_prior + order_products_train
-- ============================================================

INSERT INTO instacart.instacart_order_product_wide
SELECT
    -- 订单商品信息
    op.order_id,
    op.product_id,
    op.add_to_cart_order,
    op.reordered,
    op.dataset_type,
    
    -- 订单信息
    o.user_id,
    o.eval_set,
    o.order_number,
    o.order_dow,
    o.order_hour_of_day,
    o.days_since_prior_order,
    
    -- 商品信息
    p.product_name,
    p.aisle_id,
    p.department_id,
    
    -- 过道信息
    a.aisle,
    
    -- 部门信息
    d.department,
    
    -- 计算字段
    CASE WHEN o.days_since_prior_order IS NULL THEN 1 ELSE 0 END AS is_first_order
    
FROM (
    -- 合并 prior 和 train
    SELECT order_id, product_id, add_to_cart_order, reordered, 'prior' as dataset_type
    FROM instacart.order_products_prior
    UNION ALL
    SELECT order_id, product_id, add_to_cart_order, reordered, 'train' as dataset_type
    FROM instacart.order_products_train
) op

LEFT JOIN instacart.orders o ON op.order_id = o.order_id
LEFT JOIN instacart.products p ON op.product_id = p.product_id
LEFT JOIN instacart.aisles a ON p.aisle_id = a.aisle_id
LEFT JOIN instacart.departments d ON p.department_id = d.department_id;
