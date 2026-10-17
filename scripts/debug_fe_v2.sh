#!/bin/bash
# 排查 FE 启动问题

DORIS_HOME="/opt/doris/current"

echo "=== FE 日志目录 ==="
ls -la ${DORIS_HOME}/fe/log/

echo ""
echo "=== 所有日志文件 ==="
find ${DORIS_HOME}/fe/log -type f 2>/dev/null

echo ""
echo "=== fe.out 内容 ==="
cat ${DORIS_HOME}/fe/log/fe.out 2>/dev/null || echo "fe.out 不存在"

echo ""
echo "=== fe.log 最后 50 行 ==="
tail -50 ${DORIS_HOME}/fe/log/fe.log 2>/dev/null || echo "fe.log 不存在"

echo ""
echo "=== fe.warn.log 最后 30 行 ==="
tail -30 ${DORIS_HOME}/fe/log/fe.warn.log 2>/dev/null || echo "fe.warn.log 不存在"

echo ""
echo "=== 检查 FE jar 包 ==="
ls ${DORIS_HOME}/fe/lib/ | grep -i "fe\|palo" | head -5

echo ""
echo "=== 检查 start_fe.sh 中的 JAVA_OPTS 处理 ==="
grep -n "JAVA_OPTS" ${DORIS_HOME}/fe/bin/start_fe.sh | head -20

echo ""
echo "=== 检查 profile_fe.sh ==="
cat ${DORIS_HOME}/fe/bin/profile_fe.sh
