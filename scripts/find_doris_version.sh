#!/bin/bash
# 查找 Doris 具体版本

echo "=== Doris 2.1 版本列表 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/2.1/' | grep -oP 'href="[^"]+/"' | head -20

echo ""
echo "=== Doris 3.0 版本列表 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/3.0/' | grep -oP 'href="[^"]+/"' | head -20
