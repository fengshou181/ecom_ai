#!/bin/bash
echo "========================================"
echo "  Apache Doris 数据总览"
echo "========================================"
echo ""

echo "数据库列表:"
mysql -h 127.0.0.1 -P 9030 -u root -N -e 'SHOW DATABASES;' | grep -v 'information_schema' | grep -v '__internal_schema' | grep -v 'mysql' | sed 's/^/  - /'
echo ""

echo "[olist] - Olist 巴西电商数据集"
mysql -h 127.0.0.1 -P 9030 -u root olist -e "
SELECT 'customers' AS tbl, COUNT(*) AS cnt FROM customers
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL SELECT 'order_reviews', COUNT(*) FROM order_reviews
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL SELECT 'category_translation', COUNT(*) FROM product_category_name_translation
ORDER BY tbl;
"
echo ""

echo "[amazon] - Amazon 商品与评论"
mysql -h 127.0.0.1 -P 9030 -u root amazon -e "
SELECT 'categories' AS tbl, COUNT(*) AS cnt FROM categories
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
ORDER BY tbl;
"
echo ""

echo "[instacart] - Instacart 杂货配送"
mysql -h 127.0.0.1 -P 9030 -u root instacart -e "
SELECT 'aisles' AS tbl, COUNT(*) AS cnt FROM aisles
UNION ALL SELECT 'departments', COUNT(*) FROM departments
UNION ALL SELECT 'products', COUNT(*) AS cnt FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_products_train', COUNT(*) FROM order_products_train
UNION ALL SELECT 'order_products_prior', COUNT(*) FROM order_products_prior
ORDER BY tbl;
"
echo ""

echo "[taobao] - 淘宝用户行为"
mysql -h 127.0.0.1 -P 9030 -u root taobao -e "
SELECT 'user_behavior' AS tbl, COUNT(*) AS cnt FROM user_behavior;
"
echo ""

echo "[product_samples] - 商品样本数据"
mysql -h 127.0.0.1 -P 9030 -u root product_samples -e "
SELECT 'products_sample' AS tbl, COUNT(*) AS cnt FROM products_sample
UNION ALL SELECT 'jd_products', COUNT(*) FROM jd_products
ORDER BY tbl;
"
echo ""

echo "========================================"
echo "  数据总量统计"
echo "========================================"
mysql -h 127.0.0.1 -P 9030 -u root -e "
SELECT 
  (SELECT COUNT(*) FROM olist.customers) +
  (SELECT COUNT(*) FROM olist.geolocation) +
  (SELECT COUNT(*) FROM olist.order_items) +
  (SELECT COUNT(*) FROM olist.order_payments) +
  (SELECT COUNT(*) FROM olist.order_reviews) +
  (SELECT COUNT(*) FROM olist.orders) +
  (SELECT COUNT(*) FROM olist.products) +
  (SELECT COUNT(*) FROM olist.sellers) +
  (SELECT COUNT(*) FROM olist.product_category_name_translation) +
  (SELECT COUNT(*) FROM amazon.categories) +
  (SELECT COUNT(*) FROM amazon.products) +
  (SELECT COUNT(*) FROM amazon.reviews) +
  (SELECT COUNT(*) FROM instacart.aisles) +
  (SELECT COUNT(*) FROM instacart.departments) +
  (SELECT COUNT(*) FROM instacart.products) +
  (SELECT COUNT(*) FROM instacart.orders) +
  (SELECT COUNT(*) FROM instacart.order_products_train) +
  (SELECT COUNT(*) FROM instacart.order_products_prior) +
  (SELECT COUNT(*) FROM taobao.user_behavior) +
  (SELECT COUNT(*) FROM product_samples.products_sample) +
  (SELECT COUNT(*) FROM product_samples.jd_products)
AS total_rows;
"
echo ""
echo "✓ 全部数据集已就绪"
