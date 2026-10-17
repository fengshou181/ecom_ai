#!/bin/bash
# 商品样本数据导入脚本

DATA_DIR="/mnt/e/ecom_ai/data/raw/product_data"
FE_HOST="127.0.0.1"
FE_HTTP_PORT="8030"
DB="product_samples"
USER="root"
PASS=""

echo "========================================"
echo "  导入商品样本数据"
echo "========================================"
echo ""

# 1. products.csv (1000行样本)
echo "正在导入 products_sample ..."
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: availability,category,description,detail_url,in_stock,price,price_excl_tax,price_incl_tax,product_type,rating,review_count,tax,title,upc" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.1" \
    -T "${DATA_DIR}/products.csv" \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/products_sample/_stream_load")

status=$(echo "$result" | grep '"Status"' | sed 's/.*: "\(.*\)".*/\1/')
loaded=$(echo "$result" | grep '"NumberLoadedRows"' | sed 's/.*: \(.*\),/\1/')
filtered=$(echo "$result" | grep '"NumberFilteredRows"' | sed 's/.*: \(.*\),/\1/')
echo "  状态: $status"
echo "  导入: $loaded 行, 过滤: $filtered 行"
echo ""

# 2. jd_products.csv (25行样本)
echo "正在导入 jd_products ..."
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: name,price,shop,comments,url" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.1" \
    -T "${DATA_DIR}/jd_products.csv" \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/jd_products/_stream_load")

status=$(echo "$result" | grep '"Status"' | sed 's/.*: "\(.*\)".*/\1/')
loaded=$(echo "$result" | grep '"NumberLoadedRows"' | sed 's/.*: \(.*\),/\1/')
filtered=$(echo "$result" | grep '"NumberFilteredRows"' | sed 's/.*: \(.*\),/\1/')
echo "  状态: $status"
echo "  导入: $loaded 行, 过滤: $filtered 行"
echo ""

echo "========================================"
echo "  验证"
echo "========================================"
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT COUNT(*) as products_sample_count FROM products_sample;
SELECT COUNT(*) as jd_products_count FROM jd_products;
"
echo ""
echo "✓ 商品样本数据导入完成！"
