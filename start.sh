#!/bin/bash

# Docker 日志监控系统启动脚本

echo "=================================="
echo "Docker 日志监控系统"
echo "=================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

# 检查配置文件
if [ ! -f "config/config.yaml" ]; then
    echo "错误: 未找到配置文件 config/config.yaml"
    echo "请先配置 config/config.yaml"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip3 list | grep -q "docker" || {
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
}

# 创建日志目录
mkdir -p logs

# 启动程序
echo ""
echo "启动监控系统..."
echo "按 Ctrl+C 停止监控"
echo ""

python3 main.py
