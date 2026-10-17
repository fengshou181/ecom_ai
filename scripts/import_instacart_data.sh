#!/bin/bash
# Instacart 数据集导入脚本

DATA_DIR="/mnt/e/ecom_ai/data/raw/instacart"
FE_HOST="127.0.0.1"
FE_HTTP_PORT="8030"
DB="instacart"
USER="root"
PASS=""

echo "========================================"
echo "  导入 Instacart 数据集"
echo "========================================"
echo ""

# Stream Load 函数
stream_load() {
    local table=$1
    local file=$2
    local columns=$3
    local filter_ratio=${4:-0.01}
    
    echo "正在导入 $table ..."
    
    result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
        -H "column_separator:," \
        -H "columns: ${columns}" \
        -H "format: csv" \
        -H "skip_header: 1" \
        -H "enclose: \"" \
        -H "max_filter_ratio: ${filter_ratio}" \
        -H "timeout: 600" \
        -T "${file}" \
        "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/${table}/_stream_load")
    
    status=$(echo "$result" | grep '"Status"' | sed 's/.*: "\(.*\)".*/\1/')
    loaded=$(echo "$result" | grep '"NumberLoadedRows"' | sed 's/.*: \(.*\),/\1/')
    filtered=$(echo "$result" | grep '"NumberFilteredRows"' | sed 's/.*: \(.*\),/\1/')
    msg=$(echo "$result" | grep '"Message"' | sed 's/.*: "\(.*\)".*/\1/')
    
    echo "  状态: $status"
    echo "  导入: $loaded 行, 过滤: $filtered 行"
    if [ "$status" != "Success" ]; then
        echo "  错误: $msg"
    fi
    echo ""
}

# 1. aisles
stream_load "aisles" "${DATA_DIR}/aisles.csv" \
    "aisle_id,aisle" "0"

# 2. departments
stream_load "departments" "${DATA_DIR}/departments.csv" \
    "department_id,department" "0"

# 3. products
stream_load "products" "${DATA_DIR}/products.csv" \
    "product_id,product_name,aisle_id,department_id" "0"

# 4. orders
stream_load "orders" "${DATA_DIR}/orders.csv" \
    "order_id,user_id,eval_set,order_number,order_dow,order_hour_of_day,days_since_prior_order" "0.001"

# 5. order_products_train
stream_load "order_products_train" "${DATA_DIR}/order_products__train.csv" \
    "order_id,product_id,add_to_cart_order,reordered" "0"

# 6. order_products_prior (最大，3200万行)
echo "正在导入 order_products_prior (3200万行，需要较长时间) ..."
start_time=$(date +%s)
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: order_id,product_id,add_to_cart_order,reordered" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.001" \
    -H "timeout: 1800" \
    -T "${DATA_DIR}/order_products__prior.csv" \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/order_products_prior/_stream_load")

end_time=$(date +%s)
elapsed=$((end_time - start_time))

status=$(echo "$result" | grep '"Status"' | sed 's/.*: "\(.*\)".*/\1/')
loaded=$(echo "$result" | grep '"NumberLoadedRows"' | sed 's/.*: \(.*\),/\1/')
filtered=$(echo "$result" | grep '"NumberFilteredRows"' | sed 's/.*: \(.*\),/\1/')
msg=$(echo "$result" | grep '"Message"' | sed 's/.*: "\(.*\)".*/\1/')

echo "  状态: $status"
echo "  导入: $loaded 行, 过滤: $filtered 行"
echo "  耗时: ${elapsed} 秒"
if [ "$status" != "Success" ]; then
    echo "  错误: $msg"
fi
echo ""

echo "========================================"
echo "  验证各表数据量"
echo "========================================"
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT COUNT(*) as aisles_count FROM aisles;
SELECT COUNT(*) as departments_count FROM departments;
SELECT COUNT(*) as products_count FROM products;
SELECT COUNT(*) as orders_count FROM orders;
SELECT COUNT(*) as order_products_train_count FROM order_products_train;
SELECT COUNT(*) as order_products_prior_count FROM order_products_prior;
"
echo ""
echo "✓ Instacart 数据集导入完成！"
