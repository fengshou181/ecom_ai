#!/bin/bash
# 修复所有系统限制并启动 BE

DORIS_HOME="/opt/doris/current"

echo "=== 调整系统限制 ==="

# 1. 文件描述符限制
echo "* soft nofile 655350" >> /etc/security/limits.conf
echo "* hard nofile 655350" >> /etc/security/limits.conf
echo "root soft nofile 655350" >> /etc/security/limits.conf
echo "root hard nofile 655350" >> /etc/security/limits.conf
echo "doris soft nofile 655350" >> /etc/security/limits.conf
echo "doris hard nofile 655350" >> /etc/security/limits.conf

# 2. 进程数限制
echo "* soft nproc 655350" >> /etc/security/limits.conf
echo "* hard nproc 655350" >> /etc/security/limits.conf

# 3. 当前会话生效
ulimit -n 655350
ulimit -u 655350

echo "  文件描述符限制: $(ulimit -n)"
echo "  进程数限制: $(ulimit -u)"

# 4. vm.max_map_count
sysctl -w vm.max_map_count=2000000 > /dev/null 2>&1

echo ""
echo "=== 检查 BE 启动脚本的 swap 检查 ==="
grep -n -A3 "swap" ${DORIS_HOME}/be/bin/start_be.sh | head -15

echo ""
echo "=== 以 doris 用户身份，设置 ulimit 后启动 BE ==="
# 清理旧数据
rm -rf /data/doris/be/storage/*
chown -R doris:doris /data/doris/be

# 用 su 切换用户，确保 ulimit 生效
su - doris -c "
ulimit -n 655350
ulimit -u 655350
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export DORIS_HOME=${DORIS_HOME}
${DORIS_HOME}/be/bin/start_be.sh --daemon
" 2>&1

echo ""
echo "等待 BE 启动 (35秒)..."
sleep 35

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
    tail -30 ${DORIS_HOME}/be/log/be.out
fi
if [ -f ${DORIS_HOME}/be/log/be.INFO ]; then
    echo "--- be.INFO ---"
    grep -i "start\|ready\|success\|error\|fail\|exception" ${DORIS_HOME}/be/log/be.INFO | tail -20
fi

echo ""
echo "=== FE 中 BE 状态 ==="
mysql -h 127.0.0.1 -P 9030 -u root -e "SHOW BACKENDS\G" 2>&1 | head -30
