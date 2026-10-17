#!/bin/bash
# 查找 Doris 下载地址

echo "=== 清华镜像 Doris 根目录 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/' | grep -oP 'href="[^"]+"' | head -20

echo ""
echo "=== 阿里云镜像 Doris 根目录 ==="
curl -s --connect-timeout 10 'https://mirrors.aliyun.com/apache/doris/' | grep -oP 'href="[^"]+"' | head -20
