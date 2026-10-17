#!/bin/bash
# 测试 Amazon products 导入，查看错误详情

FE_HOST="127.0.0.1"
FE_HTTP_PORT="8030"
DB="amazon"
USER="root"
PASS=""

echo "=== 测试 products 导入 (高过滤比例) ==="
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: asin,title,imgUrl,productURL,stars,reviews,price,listPrice,category_id,isBestSeller,boughtInLastMonth" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.5" \
    -H "timeout: 300" \
    -T /mnt/e/ecom_ai/data/raw/amazon_reviews/amazon_products.csv \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/products/_stream_load")

echo "$result"
echo ""
echo "=== ErrorURL ==="
echo "$result" | grep -o '"ErrorURL":"[^"]*"' | sed 's/"ErrorURL":"//;s/"//'
