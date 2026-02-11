#!/usr/bin/env python3
"""
Web界面应用 - 提供错误监控仪表盘和配置管理
"""
import os
import json
import yaml
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import docker

app = Flask(__name__)
CORS(app)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据库模型
class ErrorLog(db.Model):
    """错误日志模型"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    container_name = db.Column(db.String(200), nullable=False)
    error_type = db.Column(db.String(100))
    error_message = db.Column(db.Text, nullable=False)
    log_content = db.Column(db.Text)
    severity = db.Column(db.String(20))  # critical, error, warning
    ai_analysis = db.Column(db.Text)
    ai_solution = db.Column(db.Text)
    status = db.Column(db.String(20), default='new')  # new, investigating, resolved
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'container_name': self.container_name,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'log_content': self.log_content,
            'severity': self.severity,
            'ai_analysis': self.ai_analysis,
            'ai_solution': self.ai_solution,
            'status': self.status
        }

# 创建数据库表
with app.app_context():
    db.create_all()

# API 路由
@app.route('/')
def index():
    """首页 - 仪表盘"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """获取统计数据"""
    now = datetime.utcnow()
    
    # 总错误数
    total_errors = ErrorLog.query.count()
    
    # 今日错误数
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_errors = ErrorLog.query.filter(ErrorLog.timestamp >= today_start).count()
    
    # 未解决错误数
    unresolved = ErrorLog.query.filter(ErrorLog.status != 'resolved').count()
    
    # 严重错误数
    critical_errors = ErrorLog.query.filter(ErrorLog.severity == 'critical').count()
    
    # 按容器统计
    containers = db.session.query(
        ErrorLog.container_name,
        db.func.count(ErrorLog.id).label('count')
    ).group_by(ErrorLog.container_name).all()
    
    # 按错误类型统计
    error_types = db.session.query(
        ErrorLog.error_type,
        db.func.count(ErrorLog.id).label('count')
    ).group_by(ErrorLog.error_type).limit(10).all()
    
    # 最近7天趋势
    seven_days_ago = now - timedelta(days=7)
    daily_stats = db.session.query(
        db.func.date(ErrorLog.timestamp).label('date'),
        db.func.count(ErrorLog.id).label('count')
    ).filter(ErrorLog.timestamp >= seven_days_ago).group_by(
        db.func.date(ErrorLog.timestamp)
    ).all()
    
    return jsonify({
        'total_errors': total_errors,
        'today_errors': today_errors,
        'unresolved': unresolved,
        'critical_errors': critical_errors,
        'containers': [{'name': c[0], 'count': c[1]} for c in containers],
        'error_types': [{'type': e[0] or 'Unknown', 'count': e[1]} for e in error_types],
        'daily_trend': [{'date': str(d[0]), 'count': d[1]} for d in daily_stats]
    })

@app.route('/api/errors')
def get_errors():
    """获取错误列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    severity = request.args.get('severity', '')
    container = request.args.get('container', '')
    search = request.args.get('search', '')
    
    query = ErrorLog.query
    
    # 过滤条件
    if status:
        query = query.filter(ErrorLog.status == status)
    if severity:
        query = query.filter(ErrorLog.severity == severity)
    if container:
        query = query.filter(ErrorLog.container_name == container)
    if search:
        query = query.filter(
            db.or_(
                ErrorLog.error_message.like(f'%{search}%'),
                ErrorLog.log_content.like(f'%{search}%')
            )
        )
    
    # 分页
    pagination = query.order_by(ErrorLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'errors': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/errors/<int:error_id>')
def get_error_detail(error_id):
    """获取错误详情"""
    error = ErrorLog.query.get_or_404(error_id)
    return jsonify(error.to_dict())

@app.route('/api/errors/<int:error_id>/status', methods=['PUT'])
def update_error_status(error_id):
    """更新错误状态"""
    error = ErrorLog.query.get_or_404(error_id)
    data = request.json
    error.status = data.get('status', error.status)
    db.session.commit()
    return jsonify({'success': True, 'error': error.to_dict()})

@app.route('/api/containers')
def get_containers():
    """获取Docker容器列表"""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        container_list = []
        for container in containers:
            container_list.append({
                'id': container.id[:12],
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created']
            })
        
        return jsonify({'containers': container_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/containers/<container_id>/logs')
def get_container_logs(container_id):
    """获取容器日志"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        logs = container.logs(tail=100).decode('utf-8')
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config')
def get_config():
    """获取配置"""
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return jsonify({'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['PUT'])
def update_config():
    """更新配置"""
    try:
        data = request.json
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data['config'], f, allow_unicode=True)
        return jsonify({'success': True, 'message': '配置已更新'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/status')
def get_monitor_status():
    """获取监控状态"""
    # 检查监控进程是否运行
    # 这里可以通过检查进程或日志文件来判断
    return jsonify({
        'running': True,  # 实际应该检查进程状态
        'uptime': '2h 15m',
        'last_check': datetime.utcnow().isoformat()
    })

# 辅助函数：添加错误日志（供其他模块调用）
def add_error_log(container_name, error_message, error_type=None, 
                  log_content=None, severity='error', ai_analysis=None, ai_solution=None):
    """添加错误日志到数据库"""
    error = ErrorLog(
        container_name=container_name,
        error_message=error_message,
        error_type=error_type,
        log_content=log_content,
        severity=severity,
        ai_analysis=ai_analysis,
        ai_solution=ai_solution
    )
    db.session.add(error)
    db.session.commit()
    return error.id

if __name__ == '__main__':
    import argparse
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='Docker 日志监控 Web 界面')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Web 服务端口 (默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    print(f"🚀 启动 Web 界面...")
    print(f"📍 访问地址: http://localhost:{args.port}")
    print(f"🔧 调试模式: {'开启' if args.debug else '关闭'}")
    print(f"按 Ctrl+C 停止服务\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
