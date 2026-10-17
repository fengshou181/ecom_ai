#!/bin/bash
echo "========================================"
echo "  Doris 数据集总览"
echo "========================================"
echo ""

echo "[1] Olist - 巴西电商数据集 (9张表)"
echo "--------------------------------------------"
mysql -h 127.0.0.1 -P 9030 -u root olist -e "
SELECT 'customers' AS tbl, COUNT(*) AS cnt FROM customers
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL SELECT 'order_reviews', COUNT(*) FROM order_reviews
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL SELECT 'category_translation', COUNT(*) FROM product_category_name_translation;
"
echo ""

echo "[2] Amazon - 亚马逊商品与评论 (3张表)"
echo "--------------------------------------------"
mysql -h 127.0.0.1 -P 9030 -u root amazon -e "
SELECT 'categories' AS tbl, COUNT(*) AS cnt FROM categories
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews;
"
echo ""

echo "[3] Instacart - 杂货配送订单 (6张表)"
echo "--------------------------------------------"
mysql -h 127.0.0.1 -P 9030 -u root instacart -e "
SELECT 'orders' AS tbl, COUNT(*) AS cnt FROM orders
UNION ALL SELECT 'order_products_prior', COUNT(*) FROM order_products_prior
UNION ALL SELECT 'order_products_train', COUNT(*) FROM order_products_train
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'aisles', COUNT(*) FROM aisles
UNION ALL SELECT 'departments', COUNT(*) FROM departments;
"
echo ""

echo "[4] Taobao - 淘宝用户行为 (1张表)"
echo "--------------------------------------------"
mysql -h 127.0.0.1 -P 9030 -u root taobao -e "
SELECT 'user_behavior' AS tbl, COUNT(*) AS cnt FROM user_behavior;
SELECT behavior_type, COUNT(*) AS cnt FROM user_behavior GROUP BY behavior_type ORDER BY cnt DESC;
"
echo ""

echo "[5] Product Samples - 商品样本 (2张表)"
echo "--------------------------------------------"
mysql -h 127.0.0.1 -P 9030 -u root product_samples -e "
SELECT 'products_sample' AS tbl, COUNT(*) AS cnt FROM products_sample
UNION ALL SELECT 'jd_products', COUNT(*) FROM jd_products;
"
