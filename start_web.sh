#!/bin/bash
# Web 界面启动脚本

# 默认端口
PORT=${1:-5000}
DEBUG=${2:-false}

echo "============================================"
echo "  Docker 日志监控 Web 界面"
echo "============================================"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

echo "📦 激活虚拟环境..."
source venv/bin/activate

echo "📦 安装/更新依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 创建必要的目录
mkdir -p logs templates static/css static/js

echo ""
echo "-------------------------------------------"
echo "  使用方法: ./start_web.sh [端口号] [debug]"
echo "  示例: ./start_web.sh 8080"
echo "  示例: ./start_web.sh 8080 debug"
echo "-------------------------------------------"
echo ""

# 启动 Web 应用
if [ "$DEBUG" = "debug" ]; then
    python web_app.py --port $PORT --debug
else
    python web_app.py --port $PORT
fi
