#!/bin/bash
# 以 doris 用户启动 BE
ulimit -n 655350
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export DORIS_HOME=/opt/doris/current
/opt/doris/current/be/bin/start_be.sh --daemon
echo "BE started"
