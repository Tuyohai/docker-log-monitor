#!/bin/bash
# Web 界面启动脚本

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "安装/更新依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 创建必要的目录
mkdir -p logs templates static/css static/js

# 启动 Web 应用
echo "启动 Web 界面..."
echo "访问地址: http://localhost:5000"
python web_app.py
