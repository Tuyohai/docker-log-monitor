# Docker 日志监控系统

一个智能的 Docker 容器日志监控系统，能够实时监控容器日志，自动检测错误，使用 AI 分析错误原因，并将分析结果发送到飞书群聊。

## 功能特性

- **实时日志监控**: 持续监控指定 Docker 容器的日志输出
- **智能错误检测**: 基于关键词自动识别错误日志
- **AI 错误分析**: 使用 Azure OpenAI 分析错误原因并提供解决建议
- **飞书消息通知**: 自动将错误日志和分析结果发送到飞书群聊
- **Web 管理界面**: 功能丰富的可视化管理界面
  - 📊 实时监控仪表盘 - 错误统计、趋势图表
  - 📝 错误日志管理 - 查看、搜索、过滤错误记录
  - 🐳 容器监控 - 查看容器状态和日志
  - ⚙️ 在线配置管理 - 无需重启即可修改配置
- **错误去重**: 避免重复发送相同的错误通知
- **频率限制**: 防止消息轰炸，控制通知频率
- **多容器支持**: 同时监控多个容器
- **数据持久化**: SQLite 数据库存储所有错误记录

## 项目结构

```
docker-log-monitor/
├── config/
│   ├── config.yaml          # 主配置文件
│   └── .env.example         # 环境变量示例
├── logs/                    # 日志文件目录
├── templates/               # Web 界面 HTML 模板
│   └── dashboard.html       # 仪表盘页面
├── static/                  # 静态资源
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── app.js           # 前端脚本
├── main.py                  # 主程序入口
├── docker_monitor.py        # Docker 日志监控模块
├── error_analyzer.py        # AI 错误分析模块
├── feishu_notifier.py       # 飞书消息发送模块
├── web_app.py               # Web 管理界面应用
├── start_web.sh             # Web 界面启动脚本
├── requirements.txt         # Python 依赖
├── docker-compose.yml       # Docker Compose 配置
└── README.md               # 项目文档
```

## 快速开始

### 演示模式（快速体验 Web 界面）

如果你想快速体验 Web 管理界面，可以使用演示模式：

```bash
# 一键启动演示（会生成测试数据）
chmod +x demo.sh
./demo.sh
```

然后访问 http://localhost:5000 查看界面效果。

### 生产环境部署

## 安装步骤

### 1. 克隆项目

```bash
cd docker-log-monitor
```

### 2. 安装 Python 依赖

要求：Python 3.8+

```bash
pip install -r requirements.txt
```

### 3. 配置项目

#### 方法一：使用配置文件（推荐）

编辑 `config/config.yaml`，配置以下内容：

```yaml
docker:
  containers:
    - "your-container-name"    # 替换为你要监控的容器名称

azure_openai:
  endpoint: "https://your-resource.openai.azure.com/"  # Azure OpenAI 端点
  api_key: "your-api-key"                              # API 密钥
  deployment_name: "gpt-4"                             # 部署名称
  api_version: "2024-02-15-preview"

feishu:
  webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your-token"  # 飞书机器人 Webhook
```

#### 方法二：使用环境变量

复制并编辑环境变量文件：

```bash
cp config/.env.example config/.env
# 然后编辑 .env 文件
```

### 4. 获取飞书 Webhook URL

1. 在飞书群聊中，点击群设置 → 群机器人
2. 添加自定义机器人
3. 复制 Webhook URL 到配置文件

### 5. 配置 Azure OpenAI

1. 登录 Azure Portal
2. 创建或使用现有的 Azure OpenAI 资源
3. 部署 GPT 模型（推荐 GPT-4）
4. 获取端点、API 密钥和部署名称
5. 将信息填入配置文件

## 使用方法

### 方式 1: 启动监控程序（命令行）

```bash
python main.py
```

或者在后台运行：

```bash
nohup python main.py > output.log 2>&1 &
```

### 方式 2: 启动 Web 管理界面（推荐）

#### 快速启动

```bash
# 使用启动脚本
chmod +x start_web.sh
./start_web.sh
```

或者手动启动：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 应用
python web_app.py
```

#### 访问界面

打开浏览器访问：`http://localhost:5000`

#### Web 界面功能

1. **仪表盘**: 
   - 实时错误统计（总数、今日、未解决、严重错误）
   - 7天错误趋势图
   - 错误类型分布饼图
   - 最近错误列表

2. **错误日志**:
   - 查看所有错误记录
   - 按容器、状态、严重度过滤
   - 搜索错误内容
   - 查看详细的 AI 分析和解决方案
   - 更新错误处理状态（新错误/调查中/已解决）

3. **容器管理**:
   - 查看所有 Docker 容器状态
   - 实时查看容器日志
   - 容器健康状况监控

4. **配置管理**:
   - 在线编辑 config.yaml
   - 无需重启即可更新配置
   - 配置验证和错误提示

### 方式 3: 使用 Docker Compose（生产环境推荐）

```bash
# 同时启动监控程序和 Web 界面
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

Docker Compose 会启动两个服务：
- `log-monitor`: 后台监控程序
- `web-dashboard`: Web 管理界面（端口 5000）

### 停止监控

按 `Ctrl+C` 或发送 SIGTERM 信号：

```bash
kill <pid>
```

## Docker 部署

如果你想在 Docker 容器中运行监控系统：

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 Docker CLI（用于连接宿主机 Docker）
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 2. 构建镜像

```bash
docker build -t docker-log-monitor .
```

### 3. 运行容器

```bash
docker run -d \
  --name log-monitor \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  docker-log-monitor
```

**重要**：必须挂载 `/var/run/docker.sock` 才能访问宿主机的 Docker 守护进程。

## 配置说明

### 错误检测配置

在 `config/config.yaml` 中配置错误关键词：

```yaml
error_detection:
  keywords:
    - "error"
    - "exception"
    - "fatal"
    - "fail"
    - "panic"
    - "traceback"
  case_sensitive: false      # 是否区分大小写
  context_lines: 5           # 错误上下文行数
```

### 通知配置

```yaml
notification:
  dedup_window: 300          # 去重时间窗口（秒）
  max_rate_per_minute: 10    # 最大通知频率（每分钟）
```

## 系统要求

- Python 3.8 或更高版本
- Docker 已安装并运行
- 可访问 Docker 守护进程（本地或远程）
- Azure OpenAI API 访问权限
- 飞书机器人 Webhook URL

## 常见问题

### 1. 无法连接到 Docker 守护进程

**错误**: `Error while fetching server API version`

**解决方案**:
- 确保 Docker 正在运行
- 如果使用 Docker Desktop，确保已启动
- 检查 Docker socket 权限：`sudo chmod 666 /var/run/docker.sock`

### 2. 飞书消息发送失败

**可能原因**:
- Webhook URL 错误
- 飞书机器人被移除
- 网络连接问题

**解决方案**:
- 验证 Webhook URL 是否正确
- 重新添加飞书机器人并更新 URL
- 检查网络连接

### 3. Azure OpenAI API 调用失败

**可能原因**:
- API 密钥错误
- 端点 URL 错误
- 部署名称不匹配
- 配额已用尽

**解决方案**:
- 检查 Azure Portal 中的配置信息
- 验证 API 密钥是否有效
- 检查配额使用情况

### 4. 容器未找到

**错误**: `容器未找到: xxx`

**解决方案**:
- 使用 `docker ps` 确认容器名称
- 确保容器正在运行
- 使用容器 ID 而不是名称

## 日志查看

系统日志保存在 `logs/monitor.log` 文件中：

```bash
tail -f logs/monitor.log
```

## 高级用法

### 监控特定容器标签

修改 `docker_monitor.py`，使用 Docker API 的过滤功能：

```python
# 获取带有特定标签的容器
containers = client.containers.list(filters={"label": "monitor=true"})
```

### 自定义错误分析提示

修改 `error_analyzer.py` 中的 `system_prompt` 来定制 AI 分析风格。

### 添加更多通知渠道

参考 `feishu_notifier.py` 的实现，可以轻松添加：
- 企业微信
- 钉钉
- Slack
- 邮件等

## 性能建议

1. **限制监控的容器数量**: 建议不超过 10 个容器
2. **调整错误关键词**: 避免过于宽泛的关键词导致误报
3. **合理设置去重窗口**: 防止重复通知
4. **使用 Azure OpenAI 批处理**: 对于高频错误，考虑批量分析

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过 Issue 反馈。

---

**祝使用愉快！**
