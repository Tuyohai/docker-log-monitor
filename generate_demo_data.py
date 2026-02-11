#!/usr/bin/env python3
"""
生成演示数据 - 用于测试 Web 界面
"""
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from web_app import app, db, ErrorLog
from datetime import datetime, timedelta
import random

def generate_demo_data():
    """生成演示错误数据"""
    with app.app_context():
        # 清空现有数据
        ErrorLog.query.delete()
        
        containers = ['web-app', 'api-server', 'database', 'redis', 'nginx']
        error_types = [
            'NullPointerException', 'TimeoutException', 'ConnectionError', 
            'OutOfMemoryError', 'FileNotFoundException', 'SQLException',
            'HTTP 500', 'HTTP 404', 'HTTP 503'
        ]
        severities = ['critical', 'error', 'warning']
        statuses = ['new', 'investigating', 'resolved']
        
        error_messages = [
            'Failed to connect to database: Connection refused',
            'Timeout waiting for response from upstream server',
            'Memory allocation failed: Out of memory',
            'Cannot find configuration file: /etc/app/config.yaml',
            'SQL query execution failed: Syntax error near SELECT',
            'HTTP request failed with status code 500',
            'Port 8080 is already in use',
            'Invalid JSON format in request body',
            'Authentication failed: Invalid credentials',
            'File system full: Cannot write to disk'
        ]
        
        ai_analyses = [
            '这个错误通常发生在应用无法连接到数据库服务时。可能的原因包括：\n1. 数据库服务未启动\n2. 网络连接问题\n3. 数据库地址或端口配置错误\n4. 防火墙规则阻止连接',
            '上游服务响应超时，说明服务处理请求的时间超过了预设的超时阈值。可能原因：\n1. 服务负载过高\n2. 数据库查询慢\n3. 外部依赖响应慢\n4. 网络延迟',
            '内存不足错误表示应用已经耗尽了可用内存。常见原因：\n1. 内存泄漏\n2. 处理的数据量过大\n3. 并发请求过多\n4. JVM 堆内存设置过小',
            '配置文件未找到，应用无法正常启动。需要检查：\n1. 文件路径是否正确\n2. 文件是否存在\n3. 文件权限是否正确\n4. 挂载卷配置是否正确'
        ]
        
        ai_solutions = [
            '建议的解决方案：\n1. 检查数据库服务状态：docker ps | grep database\n2. 验证数据库连接配置\n3. 检查网络连通性：ping database-host\n4. 查看数据库服务日志',
            '解决建议：\n1. 增加超时时间配置\n2. 优化服务性能，减少响应时间\n3. 添加缓存减轻服务压力\n4. 实现请求重试机制',
            '处理步骤：\n1. 增加容器内存限制：docker update --memory 2g container-name\n2. 检查代码是否有内存泄漏\n3. 优化数据处理逻辑\n4. 考虑实现数据分页',
            '修复方法：\n1. 确认配置文件路径正确\n2. 检查 docker-compose.yml 中的 volumes 配置\n3. 重新挂载配置目录\n4. 复制配置文件到正确位置'
        ]
        
        # 生成过去7天的错误数据
        now = datetime.utcnow()
        
        for i in range(100):
            # 随机选择时间（过去7天）
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            timestamp = now - timedelta(days=days_ago, hours=hours_ago)
            
            error = ErrorLog(
                timestamp=timestamp,
                container_name=random.choice(containers),
                error_type=random.choice(error_types),
                error_message=random.choice(error_messages),
                log_content=f"[{timestamp.isoformat()}] ERROR: {random.choice(error_messages)}\nStack trace...",
                severity=random.choice(severities),
                ai_analysis=random.choice(ai_analyses),
                ai_solution=random.choice(ai_solutions),
                status=random.choice(statuses) if random.random() > 0.3 else 'new'
            )
            db.session.add(error)
        
        db.session.commit()
        print(f"✓ 成功生成 100 条演示数据")
        print(f"✓ 时间范围：{(now - timedelta(days=7)).strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}")
        print(f"✓ 容器数量：{len(containers)}")
        print(f"✓ 错误类型：{len(error_types)}")

if __name__ == '__main__':
    print("正在生成演示数据...")
    generate_demo_data()
    print("\n可以启动 Web 应用查看数据: python web_app.py")
