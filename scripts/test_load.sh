#!/bin/bash
# 测试 customers 表的导入

RESULT=$(curl -s --location-trusted -u root: \
    -H "column_separator:," \
    -H "columns: customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.5" \
    -T /mnt/e/ecom_ai/data/raw/olist/olist_customers_dataset.csv \
    "http://127.0.0.1:8030/api/olist/customers/_stream_load")

echo "$RESULT"
echo ""
echo "--- Error URL ---"
echo "$RESULT" | grep -o '"ErrorURL":"[^"]*"' | head -1
