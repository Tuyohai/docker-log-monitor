# 端口配置使用说明

## 命令行启动方式

### 1. 使用 web_app.py 直接启动

```bash
# 默认端口 5000
python web_app.py

# 指定端口
python web_app.py --port 8080

# 指定主机和端口
python web_app.py --host 127.0.0.1 --port 8000

# 启用调试模式
python web_app.py --port 8080 --debug

# 查看帮助
python web_app.py --help
```

### 2. 使用启动脚本 start_web.sh

```bash
# 默认端口 5000
./start_web.sh

# 指定端口 8080
./start_web.sh 8080

# 指定端口并启用调试模式
./start_web.sh 8080 debug
```

### 3. 使用演示脚本 demo.sh

```bash
# 默认端口 5000
./demo.sh

# 指定端口 8080
./demo.sh 8080
```

## Docker Compose 方式

### 方法 1: 使用环境变量

```bash
# 默认端口 5000
docker-compose up -d

# 自定义端口
WEB_PORT=8080 docker-compose up -d
```

### 方法 2: 使用 .env 文件

1. 复制示例文件：
```bash
cp .env.example .env
```

2. 编辑 .env 文件：
```bash
# .env 文件内容
WEB_PORT=8080
```

3. 启动服务：
```bash
docker-compose up -d
```

## 访问 Web 界面

根据您设置的端口访问：
- 默认端口：http://localhost:5000
- 自定义端口：http://localhost:YOUR_PORT

## 端口冲突解决

如果 5000 端口已被占用，您可以：

1. 查找占用端口的进程：
```bash
lsof -i :5000
```

2. 使用其他端口启动：
```bash
./demo.sh 8080
# 或
python web_app.py --port 8080
```

## 示例

### 在 8080 端口启动演示
```bash
./demo.sh 8080
```
访问：http://localhost:8080

### 在生产环境使用 3000 端口
```bash
# 方式 1: 直接指定
python web_app.py --port 3000

# 方式 2: Docker Compose
WEB_PORT=3000 docker-compose up -d
```
访问：http://localhost:3000
