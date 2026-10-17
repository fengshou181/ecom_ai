#!/bin/bash
# Doris 连接健康检查脚本

echo "========================================"
echo "  Apache Doris 连接健康检查"
echo "========================================"
echo ""

# 1. 进程状态
echo "[1/6] 进程状态检查"
FE_COUNT=$(ps aux | grep DorisFE | grep -v grep | wc -l)
BE_COUNT=$(ps aux | grep doris_be | grep -v grep | wc -l)
echo "  FE 进程数: $FE_COUNT"
echo "  BE 进程数: $BE_COUNT"
if [ "$FE_COUNT" -ge 1 ] && [ "$BE_COUNT" -ge 1 ]; then
    echo "  ✓ 进程运行正常"
else
    echo "  ✗ 进程异常"
fi
echo ""

# 2. MySQL 连接测试
echo "[2/6] MySQL 连接测试"
RESULT=$(mysql -h 127.0.0.1 -P 9030 -u root -e 'SELECT 1 as connect_test;' 2>&1)
if echo "$RESULT" | grep -q "connect_test"; then
    echo "  ✓ MySQL 连接成功 (127.0.0.1:9030, user: root)"
else
    echo "  ✗ 连接失败: $RESULT"
fi
echo ""

# 3. FE 状态
echo "[3/6] FE 状态"
mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW FRONTENDS\G" 2>&1 | grep -E 'Name|Host|Alive|Version|Role' | sed 's/^/  /'
FE_ALIVE=$(mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW FRONTENDS\G" 2>&1 | grep 'Alive' | awk '{print $2}')
if [ "$FE_ALIVE" = "true" ]; then
    echo "  ✓ FE 运行正常"
else
    echo "  ✗ FE 异常"
fi
echo ""

# 4. BE 状态
echo "[4/6] BE 状态"
mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G" 2>&1 | grep -E 'BackendId|Host|Alive|Version|TabletNum|UsedPct|AvailCapacity' | sed 's/^/  /'
BE_ALIVE=$(mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G" 2>&1 | grep 'Alive' | awk '{print $2}')
if [ "$BE_ALIVE" = "true" ]; then
    echo "  ✓ BE 运行正常"
else
    echo "  ✗ BE 异常"
fi
echo ""

# 5. 数据库和表
echo "[5/6] 数据库 & 表统计"
DBS=$(mysql -h 127.0.0.1 -P 9030 -u root -N -e 'SHOW DATABASES;' 2>&1 | grep -v 'information_schema' | grep -v '__internal_schema')
echo "  数据库列表:"
echo "$DBS" | sed 's/^/    - /'
echo ""
echo "  olist 库各表数据量:"
TABLES="customers geolocation order_items order_payments order_reviews orders products sellers product_category_name_translation"
for tbl in $TABLES; do
    cnt=$(mysql -h 127.0.0.1 -P 9030 -u root olist -N -e "SELECT COUNT(*) FROM $tbl;" 2>&1)
    printf "    - %-40s %'d 行\n" "$tbl" "$cnt"
done
echo ""

# 6. 查询性能测试
echo "[6/6] 查询性能测试"
START=$(date +%s%N)
mysql -h 127.0.0.1 -P 9030 -u root olist -e "
SELECT
    o.order_status,
    COUNT(DISTINCT o.order_id) as order_count,
    ROUND(SUM(oi.price), 2) as total_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_status
ORDER BY order_count DESC;
" > /dev/null 2>&1
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo "  多表 JOIN + 聚合查询: ${ELAPSED}ms"
if [ "$ELAPSED" -lt 5000 ]; then
    echo "  ✓ 查询性能良好"
else
    echo "  ⚠ 查询较慢"
fi
echo ""

echo "========================================"
echo "  检查完成 ✓"
echo "========================================"
