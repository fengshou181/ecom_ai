#!/bin/bash
# 查找 Doris 二进制包的下载地址

echo "=== 1. 官方下载站 ==="
curl -s --connect-timeout 15 -L 'https://apache-doris-releases.oss-accelerate.aliyuncs.com/' 2>&1 | head -5

echo ""
echo "=== 2. 试试 GitHub releases ==="
curl -s --connect-timeout 15 'https://api.github.com/repos/apache/doris/releases/latest' 2>&1 | grep -oP '"browser_download_url": "[^"]+"' | head -10

echo ""
echo "=== 3. 试试 3.0 版本有没有二进制 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/3.0/3.0.8-rc01/' | grep -i "bin\|tar\|x64" | head -10

echo ""
echo "=== 4. 试试 4.0 版本 ==="
curl -s --connect-timeout 10 'https://mirrors.tuna.tsinghua.edu.cn/apache/doris/4.0/' | grep -oP 'href="[^"]+/"' | head -10
