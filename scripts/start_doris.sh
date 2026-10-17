#!/bin/bash
# 完整启动 Doris：FE + BE

DORIS_HOME="/opt/doris/current"

echo "=========================================="
echo "  Apache Doris 启动脚本"
echo "=========================================="
echo ""

# 1. 检查并启动 FE
echo "[1/3] 检查 FE 状态..."
FE_PID=$(jps -l 2>/dev/null | grep DorisFE | awk '{print $1}')
if [ -n "${FE_PID}" ]; then
    echo "  FE 已在运行 (PID: ${FE_PID})"
else
    echo "  启动 FE..."
    sudo -u doris bash -c "
        export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
        export DORIS_HOME=${DORIS_HOME}
        ${DORIS_HOME}/fe/bin/start_fe.sh --daemon
    " 2>&1
    echo "  等待 FE 启动 (25秒)..."
    sleep 25

    FE_PID=$(jps -l 2>/dev/null | grep DorisFE | awk '{print $1}')
    if [ -n "${FE_PID}" ]; then
        echo "  ✅ FE 启动成功 (PID: ${FE_PID})"
    else
        echo "  ❌ FE 启动失败"
        exit 1
    fi
fi

# 2. 启动 BE
echo ""
echo "[2/3] 启动 BE..."
BE_PID=$(pgrep -f doris_be 2>/dev/null || echo "")
if [ -n "${BE_PID}" ]; then
    echo "  BE 已在运行 (PID: ${BE_PID})"
else
    sudo -u doris bash -c "
        export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
        export DORIS_HOME=${DORIS_HOME}
        ${DORIS_HOME}/be/bin/start_be.sh --daemon
    " 2>&1
    echo "  等待 BE 启动 (20秒)..."
    sleep 20

    BE_PID=$(pgrep -f doris_be 2>/dev/null || echo "")
    if [ -n "${BE_PID}" ]; then
        echo "  ✅ BE 启动成功 (PID: ${BE_PID})"
    else
        echo "  ❌ BE 启动失败"
        echo ""
        echo "  BE 日志:"
        tail -30 ${DORIS_HOME}/be/log/be.out 2>/dev/null || tail -30 ${DORIS_HOME}/be/log/be.INFO 2>/dev/null || echo "无日志"
        exit 1
    fi
fi

# 3. 注册 BE 到 FE
echo ""
echo "[3/3] 注册 BE 到 FE..."

FE_IP=$(hostname -I | awk '{print $1}')
echo "  FE IP: ${FE_IP}"

# 检查 BE 是否已注册
BE_COUNT=$(mysql -h 127.0.0.1 -P 9030 -u root -N -e "SELECT COUNT(*) FROM information_schema.backends;" 2>/dev/null || echo "0")

if [ "${BE_COUNT}" -gt 0 ] 2>/dev/null; then
    echo "  BE 已注册 (数量: ${BE_COUNT})"
else
    echo "  添加 BE 到集群..."
    mysql -h 127.0.0.1 -P 9030 -u root -e "ALTER SYSTEM ADD BACKEND '${FE_IP}:9050';" 2>&1
    sleep 3
fi

echo ""
echo "=========================================="
echo "  ✅ Doris 启动完成！"
echo "=========================================="
echo ""
echo "  FE HTTP: http://${FE_IP}:8030"
echo "  FE MySQL: ${FE_IP}:9030"
echo "  用户名: root"
echo "  密码: (空)"
echo ""
echo "  BE 状态:"
mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G" 2>&1 | head -30
echo ""
echo "  连接命令: mysql -h 127.0.0.1 -P 9030 -u root"
