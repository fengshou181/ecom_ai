#!/bin/bash
# 下载并部署 Apache Doris

set -e

DORIS_VERSION="2.1.11"
DORIS_URL="https://mirrors.tuna.tsinghua.edu.cn/apache/doris/2.1/${DORIS_VERSION}/apache-doris-${DORIS_VERSION}-bin-x64.tar.gz"
INSTALL_DIR="/opt/doris"

echo "=========================================="
echo "  Apache Doris 部署脚本"
echo "=========================================="
echo ""

# 1. 创建目录
mkdir -p ${INSTALL_DIR}
cd ${INSTALL_DIR}

# 2. 测试下载链接
echo "[1/5] 测试下载链接..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "${DORIS_URL}")
if [ "${HTTP_CODE}" != "200" ]; then
    echo "  链接不可用 (HTTP ${HTTP_CODE})，尝试其他版本..."
    # 试试 2.1.11 的 rc 版本
    DORIS_URL="https://mirrors.tuna.tsinghua.edu.cn/apache/doris/2.1/${DORIS_VERSION}-rc04/apache-doris-${DORIS_VERSION}-bin-x64.tar.gz"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "${DORIS_URL}")
    if [ "${HTTP_CODE}" != "200" ]; then
        echo "  错误：找不到可用的下载链接"
        exit 1
    fi
fi
echo "  下载链接可用: ${DORIS_URL}"

# 3. 下载
echo ""
echo "[2/5] 正在下载 Apache Doris ${DORIS_VERSION}..."
echo "  这可能需要几分钟，请耐心等待..."
wget -q --show-progress -O "apache-doris-${DORIS_VERSION}-bin-x64.tar.gz" "${DORIS_URL}" 2>&1

FILE_SIZE=$(ls -lh "apache-doris-${DORIS_VERSION}-bin-x64.tar.gz" | awk '{print $5}')
echo "  下载完成！文件大小: ${FILE_SIZE}"

# 4. 解压
echo ""
echo "[3/5] 正在解压..."
tar -xzf "apache-doris-${DORIS_VERSION}-bin-x64.tar.gz"
echo "  解压完成"

# 5. 重命名并设置权限
echo ""
echo "[4/5] 配置目录结构..."
mv "apache-doris-${DORIS_VERSION}-bin-x64" "doris-${DORIS_VERSION}"
ln -sf "doris-${DORIS_VERSION}" current
chown -R doris:doris ${INSTALL_DIR}

# 创建数据目录
mkdir -p /data/doris/fe
mkdir -p /data/doris/be/storage
chown -R doris:doris /data/doris

echo "  安装目录: ${INSTALL_DIR}/current"
echo "  FE 数据目录: /data/doris/fe"
echo "  BE 数据目录: /data/doris/be"

# 6. 配置环境变量
echo ""
echo "[5/5] 配置环境变量..."
cat >> /etc/profile.d/doris.sh << 'EOF'
export DORIS_HOME=/opt/doris/current
export PATH=$PATH:$DORIS_HOME/fe/bin:$DORIS_HOME/be/bin
EOF

source /etc/profile.d/doris.sh

echo ""
echo "=========================================="
echo "  ✅ Doris 部署完成！"
echo "=========================================="
echo ""
echo "  版本: ${DORIS_VERSION}"
echo "  目录: ${INSTALL_DIR}/current"
echo ""
echo "  FE 目录: ${INSTALL_DIR}/current/fe"
echo "  BE 目录: ${INSTALL_DIR}/current/be"
echo ""
echo "  下一步：配置并启动 FE 和 BE"
