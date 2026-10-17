#!/bin/bash
# Apache Doris 一键部署脚本（WSL2 单机版）
# 包含 FE + BE 配置、启动、初始化

set -e

DORIS_VERSION="2.1.7"
DORIS_PKG="/mnt/e/ecom_ai/apache-doris-${DORIS_VERSION}-bin-x64.tar.gz"
INSTALL_DIR="/opt/doris"
FE_DIR="${INSTALL_DIR}/fe"
BE_DIR="${INSTALL_DIR}/be"
FE_META_DIR="/data/doris/fe"
BE_STORAGE_DIR="/data/doris/be/storage"
FE_HTTP_PORT=8030
FE_QUERY_PORT=9030
FE_EDIT_LOG_PORT=9010
BE_HEARTBEAT_PORT=9050
BE_BE_PORT=9060
BE_HTTP_PORT=8040
PRIORITY_NETWORKS="172.27.0.0/16"

echo "=========================================="
echo "  Apache Doris 单机部署脚本"
echo "=========================================="
echo ""

# 检查安装包
if [ ! -f "${DORIS_PKG}" ]; then
    echo "❌ 错误：找不到安装包 ${DORIS_PKG}"
    exit 1
fi

echo "安装包: ${DORIS_PKG}"
echo "文件大小: $(ls -lh ${DORIS_PKG} | awk '{print $5}')"
echo ""

# 1. 解压安装
echo "[1/6] 解压安装..."
mkdir -p ${INSTALL_DIR}
cd ${INSTALL_DIR}

if [ -d "doris-${DORIS_VERSION}" ]; then
    echo "  已存在安装目录，跳过解压"
else
    tar -xzf ${DORIS_PKG}
    echo "  解压完成"
fi

ln -sf "apache-doris-${DORIS_VERSION}-bin-x64" current
echo "  安装目录: ${INSTALL_DIR}/current"

# 2. 创建数据目录
echo ""
echo "[2/6] 创建数据目录..."
mkdir -p ${FE_META_DIR}
mkdir -p ${BE_STORAGE_DIR}
mkdir -p /data/doris/be/log
chown -R doris:doris /data/doris
echo "  FE 元数据目录: ${FE_META_DIR}"
echo "  BE 存储目录: ${BE_STORAGE_DIR}"

# 3. 配置 FE
echo ""
echo "[3/6] 配置 FE..."
FE_CONF="${INSTALL_DIR}/current/fe/conf/fe.conf"

# 备份原始配置
cp ${FE_CONF} ${FE_CONF}.bak

# 修改配置
cat > ${FE_CONF} << EOF
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
meta_dir = ${FE_META_DIR}

#####################################################################
##  port info
#####################################################################
http_port = ${FE_HTTP_PORT}
rpc_port = 9020
query_port = ${FE_QUERY_PORT}
edit_log_port = ${FE_EDIT_LOG_PORT}

#####################################################################
##  other
#####################################################################
priority_networks = ${PRIORITY_NETWORKS}

# 内存配置（WSL2 环境，给 FE 4GB）
JAVA_OPTS = "-Xmx4096m -Xms4096m -XX:+UseG1GC -Xlog:gc*:${INSTALL_DIR}/current/fe/log/fe.gc.log"

# 日志级别
log_roll_size_mb = 1024
sys_log_roll_num = 10
sys_log_level = INFO
audit_log_roll_num = 90
audit_log_modules = ""
slow_query_log_threshold = 5000

# 存储引擎
default_rowset_type = beta

# 单机模式下，副本数设为 1
default_replication_num = 1
EOF

echo "  FE 配置完成"

# 4. 配置 BE
echo ""
echo "[4/6] 配置 BE..."
BE_CONF="${INSTALL_DIR}/current/be/conf/be.conf"

# 备份原始配置
cp ${BE_CONF} ${BE_CONF}.bak

# 修改配置
cat > ${BE_CONF} << EOF
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
storage_root_path = ${BE_STORAGE_DIR}

#####################################################################
##  port info
#####################################################################
be_port = ${BE_BE_PORT}
webserver_port = ${BE_HTTP_PORT}
heartbeat_service_port = ${BE_HEARTBEAT_PORT}
brpc_port = 8060

#####################################################################
##  other
#####################################################################
priority_networks = ${PRIORITY_NETWORKS}

# 内存配置（WSL2 环境，给 BE 8GB）
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

echo "  BE 配置完成"

# 5. 设置权限
echo ""
echo "[5/6] 设置权限..."
chown -R doris:doris ${INSTALL_DIR}
chown -R doris:doris /data/doris
echo "  权限设置完成"

# 6. 配置环境变量
echo ""
echo "[6/6] 配置环境变量..."
cat > /etc/profile.d/doris.sh << EOF
export DORIS_HOME=${INSTALL_DIR}/current
export PATH=\$PATH:\$DORIS_HOME/fe/bin:\$DORIS_HOME/be/bin
EOF
chmod +x /etc/profile.d/doris.sh
source /etc/profile.d/doris.sh
echo "  环境变量配置完成"

echo ""
echo "=========================================="
echo "  ✅ Doris 部署完成！"
echo "=========================================="
echo ""
echo "  版本: ${DORIS_VERSION}"
echo "  安装目录: ${INSTALL_DIR}/current"
echo ""
echo "  FE 配置: ${FE_CONF}"
echo "  BE 配置: ${BE_CONF}"
echo ""
echo "  启动 FE: sudo -u doris ${FE_DIR}/bin/start_fe.sh --daemon"
echo "  启动 BE: sudo -u doris ${BE_DIR}/bin/start_be.sh --daemon"
echo ""
echo "  FE HTTP 端口: ${FE_HTTP_PORT}"
echo "  FE 查询端口: ${FE_QUERY_PORT}"
echo "  用户名: root"
echo "  密码: (空)"
echo ""
echo "  MySQL 客户端连接: mysql -h 127.0.0.1 -P ${FE_QUERY_PORT} -u root"
