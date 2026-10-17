#!/bin/bash
# 导出各库各表的前 20 条样本数据为 JSON，供 HTML 页面使用

OUTPUT_DIR="/mnt/e/ecom_ai/assets/data_samples"
mkdir -p "$OUTPUT_DIR"

export_db() {
    local db=$1
    local table=$2
    local outfile="$OUTPUT_DIR/${db}__${table}.json"
    
    mysql -h 127.0.0.1 -P 9030 -u root "$db" -e "
    SELECT * FROM \`$table\` LIMIT 20;
    " | python3 -c "
import sys, json, csv
reader = csv.reader(sys.stdin, delimiter='\t')
headers = next(reader)
rows = list(reader)
print(json.dumps({'columns': headers, 'rows': rows[:20]}, ensure_ascii=False))
" > "$outfile" 2>/dev/null
    echo "  导出: $db.$table -> ${db}__${table}.json ($(wc -c < "$outfile") bytes)"
}

echo "导出样本数据..."

# Olist
echo "[olist]"
export_db olist customers
export_db olist orders
export_db olist order_items
export_db olist products
export_db olist sellers
export_db olist order_payments
export_db olist order_reviews
export_db olist geolocation
export_db olist product_category_name_translation

# Amazon
echo "[amazon]"
export_db amazon categories
export_db amazon products
export_db amazon reviews

# Instacart
echo "[instacart]"
export_db instacart aisles
export_db instacart departments
export_db instacart products
export_db instacart orders
export_db instacart order_products_train
export_db instacart order_products_prior

# Taobao
echo "[taobao]"
export_db taobao user_behavior

# Product samples
echo "[product_samples]"
export_db product_samples products_sample
export_db product_samples jd_products

echo ""
echo "完成！样本数据已导出到 $OUTPUT_DIR"
