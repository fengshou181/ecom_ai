#!/bin/bash
# 调试 FE 启动问题

set -e

echo "=== 检查 Java 环境 ==="
java -version
echo "JAVA_HOME: $JAVA_HOME"

echo ""
echo "=== 检查 Doris FE 目录 ==="
ls -la /opt/doris/current/fe/
ls -la /opt/doris/current/fe/bin/

echo ""
echo "=== 检查配置文件 ==="
cat /opt/doris/current/fe/conf/fe.conf | head -30

echo ""
echo "=== 手动启动 FE（前台模式，5秒后停止）==="
cd /opt/doris/current/fe
timeout 10 bash -c '
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
./bin/start_fe.sh 2>&1
' || true

echo ""
echo "=== 检查日志目录 ==="
ls -la /opt/doris/current/fe/log/ 2>&1 || echo "日志目录不存在"

echo ""
echo "=== 检查是否有 hs_err 错误文件 ==="
find /opt/doris -name "hs_err*" 2>/dev/null || echo "无错误文件"
