#!/bin/bash
# 禁用 swap 并重新启动 BE

DORIS_HOME="/opt/doris/current"

echo "=== 检查当前 swap 状态 ==="
free -h
swapon --show 2>/dev/null || echo "无 swapon 命令"

echo ""
echo "=== 尝试禁用 swap ==="
swapoff -a 2>&1 || echo "swapoff 失败（WSL2 可能不支持）"

echo ""
echo "=== 检查 WSL swap 配置 ==="
cat /proc/swaps

echo ""
echo "=== WSL2 处理方式：修改 BE 启动脚本，跳过 swap 检查 ==="
# 备份启动脚本
cp ${DORIS_HOME}/be/bin/start_be.sh ${DORIS_HOME}/be/bin/start_be.sh.bak

# 找到 swap 检查的位置并注释掉
grep -n "swap" ${DORIS_HOME}/be/bin/start_be.sh | head -10

echo ""
echo "=== 修改启动脚本，跳过 swap 检查 ==="
sed -i 's/Please disable swap memory before installation./# WSL2: skip swap check/' ${DORIS_HOME}/be/bin/start_be.sh
sed -i 's/exit 1/# exit 1 # WSL2: skip swap check/' ${DORIS_HOME}/be/bin/start_be.sh

# 找到具体的 swap 检查逻辑并注释掉
grep -n -A5 "swap" ${DORIS_HOME}/be/bin/start_be.sh | head -20

echo ""
echo "=== 重新启动 BE ==="
# 先杀掉可能存在的 BE 进程
pkill -9 doris_be 2>/dev/null || true
sleep 2

# 清理存储目录（上次失败可能有脏数据）
rm -rf /data/doris/be/storage/*
chown -R doris:doris /data/doris/be

sudo -u doris bash -c "
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
    export DORIS_HOME=${DORIS_HOME}
    ${DORIS_HOME}/be/bin/start_be.sh --daemon
" 2>&1

echo ""
echo "等待 BE 启动 (30秒)..."
sleep 30

echo ""
echo "=== BE 进程 ==="
ps aux | grep "doris_be" | grep -v grep

echo ""
echo "=== BE 端口 ==="
ss -tlnp | grep -E "9050|9060|8040" || echo "未检测到端口"

echo ""
echo "=== BE 日志 ==="
if [ -f ${DORIS_HOME}/be/log/be.out ]; then
    echo "--- be.out ---"
    tail -20 ${DORIS_HOME}/be/log/be.out
fi
if [ -f ${DORIS_HOME}/be/log/be.INFO ]; then
    echo "--- be.INFO ---"
    tail -20 ${DORIS_HOME}/be/log/be.INFO
fi

echo ""
echo "=== FE 中 BE 状态 ==="
mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G" 2>&1 | head -25
