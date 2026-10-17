#!/bin/bash
# 检查淘宝用户行为数据格式
echo "=== 文件信息 ==="
ls -lh /mnt/e/ecom_ai/data/raw/taobao_behavior/UserBehavior.csv
wc -l /mnt/e/ecom_ai/data/raw/taobao_behavior/UserBehavior.csv
echo ""
echo "=== 前 5 行 ==="
head -5 /mnt/e/ecom_ai/data/raw/taobao_behavior/UserBehavior.csv
echo ""
echo "=== 行为类型分布 ==="
cut -d',' -f4 /mnt/e/ecom_ai/data/raw/taobao_behavior/UserBehavior.csv | sort | uniq -c | sort -rn
