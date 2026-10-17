#!/bin/bash
# 重新导入 categories 表
curl -s --location-trusted -u root: \
    -H "column_separator:," \
    -H "columns: id,category_name" \
    -H "format: csv" \
    -H "skip_header: 1" \
    -H "enclose: \"" \
    -T /mnt/e/ecom_ai/data/raw/amazon_reviews/amazon_categories.csv \
    "http://127.0.0.1:8030/api/amazon/categories/_stream_load" | grep -E '"Status"|"NumberLoadedRows"'
