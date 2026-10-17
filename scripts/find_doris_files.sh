#!/bin/bash
# 查找 Doris 2.1.11 的具体文件

echo "=== Doris 2.1.11 目录内容 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/2.1/2.1.11/' | grep -oP 'href="[^"]+"'

echo ""
echo "=== 尝试列出关键字 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/2.1/2.1.11/' | grep -i "bin\|x64\|tar" | head -20
