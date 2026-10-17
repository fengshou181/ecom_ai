#!/bin/bash
# 修复 BE 启动问题并重新启动

DORIS_HOME="/opt/doris/current"

echo "=== 调整系统参数 ==="
# 设置 vm.max_map_count
sysctl -w vm.max_map_count=2000000

# 永久生效
echo "vm.max_map_count=2000000" >> /etc/sysctl.conf

# 检查其他必要参数
sysctl vm.max_map_count

echo ""
echo "=== 检查 BE 配置 ==="
cat ${DORIS_HOME}/be/conf/be.conf

echo ""
echo "=== 启动 BE ==="
sudo -u doris bash -c "
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
    export DORIS_HOME=${DORIS_HOME}
    ${DORIS_HOME}/be/bin/start_be.sh --daemon
" 2>&1

echo ""
echo "等待 BE 启动 (25秒)..."
sleep 25

echo ""
echo "=== BE 进程 ==="
ps aux | grep "doris_be" | grep -v grep

echo ""
echo "=== BE 端口 ==="
ss -tlnp | grep -E "9050|9060|8040" || echo "未检测到端口"

echo ""
echo "=== BE 日志（最后30行）==="
tail -30 ${DORIS_HOME}/be/log/be.out 2>/dev/null || tail -30 ${DORIS_HOME}/be/log/be.INFO 2>/dev/null || echo "无日志"

echo ""
echo "=== 注册 BE ==="
FE_IP=$(hostname -I | awk '{print $1}')
mysql -h 127.0.0.1 -P 9030 -u root -e "ALTER SYSTEM ADD BACKEND '${FE_IP}:9050';" 2>&1
sleep 3

echo ""
echo "=== BE 状态 ==="
mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G" 2>&1
