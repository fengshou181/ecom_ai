#!/bin/bash
# 淘宝用户行为数据导入脚本

DATA_FILE="/mnt/e/ecom_ai/data/raw/taobao_behavior/UserBehavior.csv"
FE_HOST="127.0.0.1"
FE_HTTP_PORT="8030"
DB="taobao"
TABLE="user_behavior"
USER="root"
PASS=""

echo "========================================"
echo "  导入淘宝用户行为数据"
echo "========================================"
echo ""
echo "文件: $DATA_FILE"
echo "预估行数: ~1 亿行"
echo ""

start_time=$(date +%s)

echo "开始导入 (数据量较大，请耐心等待) ..."
result=$(curl -s --location-trusted -u "${USER}:${PASS}" \
    -H "column_separator:," \
    -H "columns: user_id,item_id,category_id,behavior_type,timestamp" \
    -H "format: csv" \
    -H "max_filter_ratio: 0.001" \
    -H "timeout: 3600" \
    -T "${DATA_FILE}" \
    "http://${FE_HOST}:${FE_HTTP_PORT}/api/${DB}/${TABLE}/_stream_load")

end_time=$(date +%s)
elapsed=$((end_time - start_time))

status=$(echo "$result" | grep '"Status"' | sed 's/.*: "\(.*\)".*/\1/')
total=$(echo "$result" | grep '"NumberTotalRows"' | sed 's/.*: \(.*\),/\1/')
loaded=$(echo "$result" | grep '"NumberLoadedRows"' | sed 's/.*: \(.*\),/\1/')
filtered=$(echo "$result" | grep '"NumberFilteredRows"' | sed 's/.*: \(.*\),/\1/')
msg=$(echo "$result" | grep '"Message"' | sed 's/.*: "\(.*\)".*/\1/')
load_bytes=$(echo "$result" | grep '"LoadBytes"' | sed 's/.*: \(.*\),/\1/')

echo ""
echo "========================================"
echo "  导入结果"
echo "========================================"
echo "  状态: $status"
echo "  总行数: $total"
echo "  成功导入: $loaded 行"
echo "  过滤行数: $filtered 行"
echo "  数据量: $load_bytes 字节"
echo "  耗时: ${elapsed} 秒"
if [ "$status" != "Success" ]; then
    echo "  错误: $msg"
fi
echo ""

echo "========================================"
echo "  数据验证"
echo "========================================"
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT COUNT(*) as total_rows FROM user_behavior;
"
echo ""
echo "行为类型分布:"
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT behavior_type, COUNT(*) as cnt
FROM user_behavior
GROUP BY behavior_type
ORDER BY cnt DESC;
"
echo ""
echo "用户数:"
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT COUNT(DISTINCT user_id) as user_count FROM user_behavior;
"
echo ""
echo "商品数:"
mysql -h ${FE_HOST} -P 9030 -u ${USER} ${DB} -e "
SELECT COUNT(DISTINCT item_id) as item_count FROM user_behavior;
"
echo ""
echo "✓ 淘宝用户行为数据导入完成！"
