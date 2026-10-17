#!/bin/bash
# 查看 Instacart products 导入错误

result=$(curl -s --location-trusted -u root: \
    -H "column_separator:," \
    -H "columns: product_id,product_name,aisle_id,department_id" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.1" \
    -T /mnt/e/ecom_ai/data/raw/instacart/products.csv \
    "http://127.0.0.1:8030/api/instacart/products/_stream_load")

echo "$result" | grep -E '"Status"|"NumberLoadedRows"|"NumberFilteredRows"|"ErrorURL"'
echo ""

# 获取错误 URL
error_url=$(echo "$result" | grep -o '"ErrorURL":"[^"]*"' | sed 's/"ErrorURL":"//;s/"//')
if [ -n "$error_url" ]; then
    echo "=== 错误详情 (前 10 条) ==="
    curl -s "$error_url" | head -20
fi
