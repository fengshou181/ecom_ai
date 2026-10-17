#!/bin/bash
# 修复 Doris FE 配置并启动

DORIS_HOME="/opt/doris/current"

echo "=== 修复 FE 配置 ==="

# 重新写 fe.conf
cat > ${DORIS_HOME}/fe/conf/fe.conf << 'EOF'
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

#####################################################################
##  meta data dir
#####################################################################
meta_dir = /data/doris/fe

#####################################################################
##  port info
#####################################################################
http_port = 8030
rpc_port = 9020
query_port = 9030
edit_log_port = 9010

#####################################################################
##  other
#####################################################################
priority_networks = 172.27.0.0/16

# JVM 参数（Java 17 兼容）
JAVA_OPTS = "-Xmx4096m -Xms4096m -XX:+UseG1GC -Xlog:gc*:file=${DORIS_HOME}/fe/log/fe.gc.log"

# Java 17 特殊参数
JAVA_OPTS_FOR_JDK_9_TO_17 = "-Xmx4096m -Xms4096m -XX:+UseG1GC \
--add-opens=java.base/java.lang=ALL-UNNAMED \
--add-opens=java.base/java.util=ALL-UNNAMED \
--add-opens=java.base/java.lang.reflect=ALL-UNNAMED \
--add-opens=java.base/java.text=ALL-UNNAMED \
--add-opens=java.desktop/java.awt.font=ALL-UNNAMED \
--add-opens=java.base/java.io=ALL-UNNAMED \
--add-opens=java.base/java.nio=ALL-UNNAMED \
--add-opens=java.base/jdk.internal.ref=ALL-UNNAMED \
--add-opens=java.base/sun.nio.ch=ALL-UNNAMED \
--add-opens=java.base/sun.nio.cs=ALL-UNNAMED \
--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED"

# 日志
log_roll_size_mb = 1024
sys_log_roll_num = 10
sys_log_level = INFO
audit_log_roll_num = 90
audit_log_modules = ""
slow_query_log_threshold = 5000

# 存储引擎
default_rowset_type = beta

# 单机模式副本数
default_replication_num = 1
EOF

echo "  FE 配置已修复"

echo ""
echo "=== 修复 BE 配置 ==="
cat > ${DORIS_HOME}/be/conf/be.conf << 'EOF'
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

#####################################################################
##  storage dir
#####################################################################
storage_root_path = /data/doris/be/storage

#####################################################################
##  port info
#####################################################################
be_port = 9060
webserver_port = 8040
heartbeat_service_port = 9050
brpc_port = 8060

#####################################################################
##  other
#####################################################################
priority_networks = 172.27.0.0/16

# 内存
mem_limit = 8GB
tablet_map_max_num = 1024000

# 日志
sys_log_roll_mode = SIZE-MB_1024
sys_log_roll_num = 10
sys_log_level = INFO
log_buffer_level = -1

# 存储
default_rowset_type = beta
EOF

echo "  BE 配置已修复"

# 设置权限
chown -R doris:doris ${DORIS_HOME}/fe/conf
chown -R doris:doris ${DORIS_HOME}/be/conf

echo ""
echo "=== 启动 FE（后台模式）==="
sudo -u doris bash -c "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64; ${DORIS_HOME}/fe/bin/start_fe.sh --daemon" 2>&1

echo ""
echo "等待 FE 启动 (30秒)..."
sleep 30

echo ""
echo "=== FE 进程状态 ==="
ps aux | grep -i "PaloFe" | grep -v grep

echo ""
echo "=== FE 日志 (最后20行) ==="
tail -20 ${DORIS_HOME}/fe/log/fe.out 2>&1 | grep -E "started|START|error|ERROR|Exception|warn|WARN" | head -20

echo ""
echo "=== 测试 FE 端口 ==="
netstat -tlnp 2>/dev/null | grep -E "8030|9030|9010" || ss -tlnp | grep -E "8030|9030|9010"
