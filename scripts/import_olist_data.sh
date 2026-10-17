#!/bin/bash
# Olist 数据集导入脚本 - 使用 Doris Stream Load

DATA_DIR="/mnt/e/ecom_ai/data/raw/olist"
FE_HOST="127.0.0.1"
FE_HTTP_PORT="8030"
DB="olist"
USER="root"
PASS=""

# Stream Load 函数
stream_load() {
    local table=$1
    local file=$2
    local columns=$3
    
    echo "正在导入 $table ..."
    
    result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
        -H "column_separator:," \
        -H "columns: ${columns}" \
        -H "format: csv" \
        -H "skip_header: 1" \
        -H "enclose: \"" \
        -H "max_filter_ratio: 0.01" \
        -T "${file}" \
        "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/${table}/_stream_load")
    
    echo "$result" | grep -E '"Status"|"NumberLoadedRows"|"NumberFilteredRows"|"Message"'
    echo ""
}

# 清空之前可能部分导入的表
echo "清空已有数据..."
mysql -h ${FE_HOST} -P 9030 -u ${USER} -e "
USE ${DB};
TRUNCATE TABLE customers;
TRUNCATE TABLE geolocation;
TRUNCATE TABLE order_reviews;
TRUNCATE TABLE sellers;
" 2>/dev/null
echo "已清空"
echo ""

# 1. customers
stream_load "customers" "${DATA_DIR}/olist_customers_dataset.csv" \
    "customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state"

# 2. geolocation (大数据量，给更高的超时)
echo "正在导入 geolocation (数据量较大，请稍候) ..."
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: geolocation_zip_code_prefix,geolocation_lat,geolocation_lng,geolocation_city,geolocation_state" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.01" \
    -H "timeout: 300" \
    -T "${DATA_DIR}/olist_geolocation_dataset.csv" \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/geolocation/_stream_load")
echo "$result" | grep -E '"Status"|"NumberLoadedRows"|"NumberFilteredRows"|"Message"'
echo ""

# 3. order_items
stream_load "order_items" "${DATA_DIR}/olist_order_items_dataset.csv" \
    "order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value"

# 4. order_payments
stream_load "order_payments" "${DATA_DIR}/olist_order_payments_dataset.csv" \
    "order_id,payment_sequential,payment_type,payment_installments,payment_value"

# 5. order_reviews (含文本字段)
echo "正在导入 order_reviews (含文本字段) ..."
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.05" \
    -H "timeout: 300" \
    -T "${DATA_DIR}/olist_order_reviews_dataset.csv" \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/order_reviews/_stream_load")
echo "$result" | grep -E '"Status"|"NumberLoadedRows"|"NumberFilteredRows"|"Message"'
echo ""

# 6. orders
stream_load "orders" "${DATA_DIR}/olist_orders_dataset.csv" \
    "order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date"

# 7. products
stream_load "products" "${DATA_DIR}/olist_products_dataset.csv" \
    "product_id,product_category_name,product_name_lenght,product_description_lenght,product_photos_qty,product_weight_g,product_length_cm,product_height_cm,product_width_cm"

# 8. sellers
stream_load "sellers" "${DATA_DIR}/olist_sellers_dataset.csv" \
    "seller_id,seller_zip_code_prefix,seller_city,seller_state"

# 9. product_category_name_translation
stream_load "product_category_name_translation" "${DATA_DIR}/product_category_name_translation.csv" \
    "product_category_name,product_category_name_english"

echo "所有表导入完成！"
echo "=============================="
echo "验证各表数据量："
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT 'customers' AS tbl, COUNT(*) AS cnt FROM customers
UNION ALL
SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM order_reviews
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL
SELECT 'category_translation', COUNT(*) FROM product_category_name_translation
ORDER BY tbl;
"
