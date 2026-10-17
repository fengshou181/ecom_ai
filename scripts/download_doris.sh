#!/bin/bash
# 下载 Doris 二进制包

echo "=== 尝试 Doris 官方下载地址 ==="

# Doris 2.1.7 稳定版（已知有二进制包的版本）
URLS=(
    "https://apache-doris-releases.oss-accelerate.aliyuncs.com/apache-doris-2.1.7-bin-x64.tar.gz"
    "https://doris-build-1308700295.cos.ap-beijing.myqcloud.com/release/2.1.7/apache-doris-2.1.7-bin-x64.tar.gz"
    "https://github.com/apache/doris/releases/download/2.1.7-rc04/apache-doris-2.1.7-bin-x64.tar.gz"
)

for url in "${URLS[@]}"; do
    echo ""
    echo "尝试: $url"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -L "$url")
    echo "  HTTP 状态: ${HTTP_CODE}"
    if [ "${HTTP_CODE}" = "200" ] || [ "${HTTP_CODE}" = "302" ]; then
        echo "  ✅ 可用！"
        DOWNLOAD_URL="$url"
        break
    fi
done

if [ -z "${DOWNLOAD_URL}" ]; then
    echo ""
    echo "❌ 没有找到可用的下载链接"
    exit 1
fi

echo ""
echo "下载链接: ${DOWNLOAD_URL}"
echo ""
echo "开始下载..."
mkdir -p /opt/doris
cd /opt/doris
wget -q --show-progress -O apache-doris-bin.tar.gz "${DOWNLOAD_URL}" 2>&1

echo ""
echo "下载完成！文件大小: $(ls -lh apache-doris-bin.tar.gz | awk '{print $5}')"
