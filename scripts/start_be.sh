#!/bin/bash
# 启动 BE 并注册到 FE

DORIS_HOME="/opt/doris/current"

echo "=== 启动 BE ==="

# 先清理之前的测试数据（如果有）
rm -rf /data/doris/be/storage/*
chown -R doris:doris /data/doris/be

# 启动 BE（后台模式）
sudo -u doris bash -c "
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export DORIS_HOME=${DORIS_HOME}
${DORIS_HOME}/be/bin/start_be.sh --daemon
" 2>&1

echo ""
echo "等待 BE 启动 (20秒)..."
sleep 20

echo ""
echo "=== BE 进程 ==="
ps aux | grep "doris_be" | grep -v grep

echo ""
echo "=== BE 日志（启动信息）==="
grep -i "start\|ready\|success\|error\|fail" ${DORIS_HOME}/be/log/be.INFO 2>/dev/null | tail -15 || echo "无日志"

echo ""
echo "=== BE 端口 ==="
ss -tlnp | grep -E "9050|9060|8040" || netstat -tlnp 2>/dev/null | grep -E "9050|9060|8040" || echo "未检测到端口"

echo ""
echo "=== 注册 BE 到 FE ==="
# 获取 FE 的 IP
FE_IP=$(hostname -I | awk '{print $1}')
echo "FE IP: ${FE_IP}"

# 使用 MySQL 客户端添加 BE
mysql -h 127.0.0.1 -P 9030 -u root -e "
ALTER SYSTEM ADD BACKEND '${FE_IP}:9050';
SHOW BACKENDS\G
" 2>&1

echo ""
echo "=== 完成 ==="
