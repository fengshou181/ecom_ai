#!/bin/bash
# 修复 FE 配置 - JAVA_OPTS 单行版本

DORIS_HOME="/opt/doris/current"

echo "=== 修复 FE 配置（单行 JAVA_OPTS）==="

cat > ${DORIS_HOME}/fe/conf/fe.conf << 'EOF'
meta_dir = /data/doris/fe
http_port = 8030
rpc_port = 9020
query_port = 9030
edit_log_port = 9010
priority_networks = 172.27.0.0/16
default_rowset_type = beta
default_replication_num = 1
sys_log_level = INFO
log_roll_size_mb = 1024
sys_log_roll_num = 10
EOF

echo "  基础配置已写入"

# 追加 JAVA_OPTS（确保单行，无换行）
echo 'JAVA_OPTS = "-Xmx4096m -Xms4096m -XX:+UseG1GC -Dlog4j2.formatMsgNoLookups=true"' >> ${DORIS_HOME}/fe/conf/fe.conf
echo 'JAVA_OPTS_FOR_JDK_9_TO_17 = "-Xmx4096m -Xms4096m -XX:+UseG1GC --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.text=ALL-UNNAMED --add-opens=java.desktop/java.awt.font=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/jdk.internal.ref=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED -Dlog4j2.formatMsgNoLookups=true"' >> ${DORIS_HOME}/fe/conf/fe.conf

echo "  JAVA_OPTS 已追加（单行）"

# 设置权限
chown doris:doris ${DORIS_HOME}/fe/conf/fe.conf

echo ""
echo "=== 验证配置 ==="
cat ${DORIS_HOME}/fe/conf/fe.conf

echo ""
echo "=== 启动 FE ==="
sudo -u doris bash -c "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64; ${DORIS_HOME}/fe/bin/start_fe.sh --daemon" 2>&1

echo ""
echo "等待 FE 启动 (30秒)..."
sleep 30

echo ""
echo "=== FE 进程 ==="
ps aux | grep -i "PaloFe\|fe.jar" | grep -v grep

echo ""
echo "=== FE 日志（关键信息）==="
grep -i "started\|start\|ready\|error\|exception" ${DORIS_HOME}/fe/log/fe.out 2>/dev/null | tail -10 || echo "无日志文件"

echo ""
echo "=== 端口监听 ==="
ss -tlnp | grep -E "8030|9030|9010" || netstat -tlnp 2>/dev/null | grep -E "8030|9030|9010" || echo "无监听端口"
