#!/bin/bash
echo "========================================"
echo "  Amazon + Instacart 数据验证"
echo "========================================"
echo ""

echo "[Amazon]"
mysql -h 127.0.0.1 -P 9030 -u root amazon -e "
SELECT 'categories' AS tbl, COUNT(*) AS cnt FROM categories
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews;
"
echo ""

echo "  商品分类 Top 10 (按商品数):"
mysql -h 127.0.0.1 -P 9030 -u root amazon -e "
SELECT c.category_name, COUNT(*) as product_count
FROM products p
JOIN categories c ON p.category_id = c.id
GROUP BY c.category_name
ORDER BY product_count DESC
LIMIT 10;
"
echo ""

echo "[Instacart]"
mysql -h 127.0.0.1 -P 9030 -u root instacart -e "
SELECT 'aisles' AS tbl, COUNT(*) AS cnt FROM aisles
UNION ALL
SELECT 'departments', COUNT(*) FROM departments
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_products_train', COUNT(*) FROM order_products_train
UNION ALL
SELECT 'order_products_prior', COUNT(*) FROM order_products_prior;
"
echo ""

echo "  最热门商品 Top 10:"
mysql -h 127.0.0.1 -P 9030 -u root instacart -e "
SELECT p.product_name, COUNT(*) as order_count
FROM order_products_prior op
JOIN products p ON op.product_id = p.product_id
GROUP BY p.product_name
ORDER BY order_count DESC
LIMIT 10;
"
echo ""

echo "  订单时间分布（按小时）:"
mysql -h 127.0.0.1 -P 9030 -u root instacart -e "
SELECT order_hour_of_day, COUNT(*) as order_count
FROM orders
GROUP BY order_hour_of_day
ORDER BY order_hour_of_day;
" 2>&1 | head -30

echo ""
echo "✓ 验证完成！"
