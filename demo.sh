#!/bin/bash
# 快速启动演示 - 安装依赖、生成演示数据、启动 Web 界面

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
pip3 install -q Flask Flask-CORS Flask-SQLAlchemy docker PyYAML requests openai

echo ""
echo "🎲 生成演示数据..."
python3 generate_demo_data.py

echo ""
echo "🚀 启动 Web 界面..."
echo "-------------------------------------------"
echo "  访问地址: http://localhost:5000"
echo "  按 Ctrl+C 停止服务"
echo "-------------------------------------------"
echo ""

python3 web_app.py
