FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装 Docker CLI（用于连接宿主机 Docker）
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY *.py .
COPY config/ config/

# 创建日志目录
RUN mkdir -p logs

# 设置时区（可选）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 运行应用
CMD ["python", "-u", "main.py"]
