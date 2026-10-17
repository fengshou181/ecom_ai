#!/bin/bash
# 查看 FE 启动日志的关键信息

DORIS_HOME="/opt/doris/current"

echo "=== fe.log 最后 60 行 ==="
tail -60 ${DORIS_HOME}/fe/log/fe.log

echo ""
echo "=== fe.log 中的错误/异常 ==="
grep -i "error\|exception\|fail\|fatal" ${DORIS_HOME}/fe/log/fe.log | tail -20

echo ""
echo "=== fe.warn.log 全部内容 ==="
cat ${DORIS_HOME}/fe/log/fe.warn.log
