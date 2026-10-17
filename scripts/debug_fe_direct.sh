#!/bin/bash
# 直接运行 FE 看错误

DORIS_HOME="/opt/doris/current"
export DORIS_HOME
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
export JAVA="${JAVA_HOME}/bin/java"

echo "DORIS_HOME: ${DORIS_HOME}"
echo "JAVA: ${JAVA}"
echo ""

# 先修正配置 - 用 JAVA_OPTS_FOR_JDK_17
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
JAVA_OPTS_FOR_JDK_17 = "-Xmx4096m -Xms4096m -XX:+UseG1GC --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.text=ALL-UNNAMED --add-opens=java.desktop/java.awt.font=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/jdk.internal.ref=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED -Dlog4j2.formatMsgNoLookups=true"
EOF

chown doris:doris ${DORIS_HOME}/fe/conf/fe.conf

echo "=== 配置已更新 ==="
echo ""

# 直接以 doris 用户运行 FE（前台模式，30秒后自动退出）
echo "=== 直接运行 FE（前台模式，15秒）==="
cd ${DORIS_HOME}/fe

sudo -u doris timeout 15 bash -c "
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export DORIS_HOME=/opt/doris/current
cd /opt/doris/current/fe
./bin/start_fe.sh
" 2>&1 || true

echo ""
echo "=== 运行结束，检查日志 ==="
ls -la ${DORIS_HOME}/fe/log/

echo ""
echo "=== fe.out 内容 ==="
cat ${DORIS_HOME}/fe/log/fe.out 2>/dev/null | head -50 || echo "无 fe.out"
