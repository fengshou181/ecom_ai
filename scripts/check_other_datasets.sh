#!/bin/bash
# 检查所有待导入数据集的结构和大小

echo "========================================"
echo "  待导入数据集概览"
echo "========================================"
echo ""

DATA_BASE="/mnt/e/ecom_ai/data/raw"

# 1. 淘宝用户行为
echo "[1] 淘宝用户行为 (taobao_behavior)"
TAOBAO_FILE="$DATA_BASE/taobao_behavior/UserBehavior.csv"
if [ -f "$TAOBAO_FILE" ]; then
    lines=$(wc -l < "$TAOBAO_FILE")
    size=$(du -h "$TAOBAO_FILE" | awk '{print $1}')
    echo "  文件: UserBehavior.csv"
    echo "  大小: $size"
    echo "  行数: $lines"
    echo "  字段: $(head -1 "$TAOBAO_FILE")"
else
    echo "  ⚠ 文件不存在"
fi
echo ""

# 2. Amazon Reviews
echo "[2] Amazon Reviews (amazon_reviews)"
for f in "$DATA_BASE"/amazon_reviews/*.csv; do
    fname=$(basename "$f")
    lines=$(wc -l < "$f")
    size=$(du -h "$f" | awk '{print $1}')
    echo "  $fname: $size, $lines 行"
    echo "    字段: $(head -1 "$f")"
done
echo ""

# 3. Instacart
echo "[3] Instacart 杂货配送"
total_lines=0
for f in "$DATA_BASE"/instacart/*.csv; do
    fname=$(basename "$f")
    lines=$(wc -l < "$f")
    size=$(du -h "$f" | awk '{print $1}')
    total_lines=$((total_lines + lines))
    echo "  $fname: $size, $lines 行"
    echo "    字段: $(head -1 "$f")"
done
echo "  合计: $total_lines 行"
echo ""

# 4. 商品数据
echo "[4] 商品数据 (product_data)"
for f in "$DATA_BASE"/product_data/*.csv; do
    fname=$(basename "$f")
    lines=$(wc -l < "$f")
    size=$(du -h "$f" | awk '{print $1}')
    echo "  $fname: $size, $lines 行"
    echo "    字段: $(head -1 "$f")"
done
echo ""

echo "========================================"
