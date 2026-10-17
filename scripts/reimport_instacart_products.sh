#!/bin/bash
# 重新导入 Instacart products 表

# 清空表
mysql -h 127.0.0.1 -P 9030 -u root instacart -e 'TRUNCATE TABLE products;'

# 重新导入
result=$(curl -s --location-trusted -u root: \
    -H "column_separator:," \
    -H "columns: product_id,product_name,aisle_id,department_id" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -H "max_filter_ratio: 0.01" \
    -T /mnt/e/ecom_ai/data/raw/instacart/products.csv \
    "http://127.0.0.1:8030/api/instacart/products/_stream_load")

echo "$result" | grep -E '"Status"|"NumberLoadedRows"|"NumberFilteredRows"'
echo ""
echo "验证:"
mysql -h 127.0.0.1 -P 9030 -u root instacart -e 'SELECT COUNT(*) as products_count FROM products;'
