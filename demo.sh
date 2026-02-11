#!/bin/bash
# 快速启动演示 - 安装依赖、生成演示数据、启动 Web 界面

# 默认端口
PORT=${1:-5000}

echo "============================================"
echo "  Docker 日志监控系统 - Web 界面演示"
echo "============================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    exit 1
fi

echo "📦 安装依赖..."
pip3 install -q Flask Flask-CORS Flask-SQLAlchemy docker PyYAML requests openai 2>/dev/null || {
    echo "⚠️  依赖安装可能失败，但继续尝试启动..."
}

echo ""
echo "🎲 生成演示数据..."
python3 generate_demo_data.py

echo ""
echo "-------------------------------------------"
echo "  使用方法: ./demo.sh [端口号]"
echo "  示例: ./demo.sh 8080"
echo "-------------------------------------------"
echo ""

python3 web_app.py --port $PORT
