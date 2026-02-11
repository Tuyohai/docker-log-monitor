"""
Docker 日志监控主程序
监控 Docker 容器日志，检测错误，AI 分析并发送飞书通知
"""
import os
import sys
import yaml
import logging
import signal
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Set
from pathlib import Path

from docker_monitor import DockerLogMonitor
from error_analyzer import ErrorAnalyzer
from feishu_notifier import FeishuNotifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class LogMonitorApp:
    """日志监控应用主类"""

    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        初始化监控应用

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.docker_monitor = None
        self.error_analyzer = None
        self.feishu_notifier = None

        # 错误去重缓存
        self.error_cache: Dict[str, datetime] = {}
        self.rate_limit_counter: Dict[str, int] = defaultdict(int)
        self.last_rate_reset = datetime.now()

        # 错误关键词
        self.error_keywords: Set[str] = set()
        self.case_sensitive = False

        # 通知设置
        self.dedup_window = 300  # 秒
        self.max_rate_per_minute = 10

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"成功加载配置文件: {self.config_path}")

            # 加载错误检测配置
            error_config = self.config.get('error_detection', {})
            self.error_keywords = set(kw.lower() for kw in error_config.get('keywords', []))
            self.case_sensitive = error_config.get('case_sensitive', False)

            # 加载通知配置
            notif_config = self.config.get('notification', {})
            self.dedup_window = notif_config.get('dedup_window', 300)
            self.max_rate_per_minute = notif_config.get('max_rate_per_minute', 10)

            logger.info(f"错误关键词: {self.error_keywords}")
            logger.info(f"去重窗口: {self.dedup_window}秒, 最大频率: {self.max_rate_per_minute}/分钟")

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    def initialize_components(self):
        """初始化各个组件"""
        try:
            # 初始化 Docker 监控器
            docker_config = self.config.get('docker', {})
            log_settings = docker_config.get('log_settings', {})

            self.docker_monitor = DockerLogMonitor(
                containers=docker_config.get('containers', []),
                error_callback=self.on_log_line,
                tail=log_settings.get('tail', 'latest'),
                follow=log_settings.get('follow', True),
                timestamps=log_settings.get('timestamps', True)
            )

            # 初始化错误分析器
            ai_config = self.config.get('azure_openai', {})
            self.error_analyzer = ErrorAnalyzer(
                endpoint=ai_config.get('endpoint'),
                api_key=ai_config.get('api_key'),
                deployment_name=ai_config.get('deployment_name'),
                api_version=ai_config.get('api_version', '2024-02-15-preview')
            )

            # 初始化飞书通知器
            feishu_config = self.config.get('feishu', {})
            self.feishu_notifier = FeishuNotifier(
                webhook_url=feishu_config.get('webhook_url')
            )

            logger.info("所有组件初始化完成")

        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            sys.exit(1)

    def on_log_line(self, container_name: str, container_id: str,
                    log_line: str, timestamp: datetime):
        """
        日志行回调函数，检测是否包含错误

        Args:
            container_name: 容器名称
            container_id: 容器 ID
            log_line: 日志行
            timestamp: 时间戳
        """
        # 检测是否是错误日志
        if not self.is_error_log(log_line):
            return

        logger.info(f"检测到错误日志: [{container_name}] {log_line[:100]}...")

        # 检查去重
        error_key = self.generate_error_key(container_name, log_line)
        if self.is_duplicate_error(error_key):
            logger.debug(f"重复错误，已跳过: {error_key}")
            return

        # 检查发送频率限制
        if not self.check_rate_limit(container_name):
            logger.warning(f"容器 {container_name} 已达到最大通知频率限制")
            return

        # 获取容器信息
        container_info = self.docker_monitor.get_container_info(container_name)
        container_image = container_info.get('image', 'unknown') if container_info else 'unknown'

        # 使用 AI 分析错误
        analysis = self.error_analyzer.analyze_error(
            error_log=log_line,
            container_name=container_name,
            container_image=container_image
        )

        # 发送飞书通知
        success = self.feishu_notifier.send_error_notification(
            container_name=container_name,
            container_id=container_id,
            error_log=log_line,
            analysis=analysis or "AI 分析不可用",
            timestamp=timestamp,
            container_image=container_image
        )

        if success:
            logger.info(f"成功发送错误通知: [{container_name}]")
            # 更新去重缓存
            self.error_cache[error_key] = timestamp
        else:
            logger.error(f"发送错误通知失败: [{container_name}]")

    def is_error_log(self, log_line: str) -> bool:
        """
        判断日志行是否包含错误

        Args:
            log_line: 日志行

        Returns:
            是否是错误日志
        """
        check_line = log_line if self.case_sensitive else log_line.lower()

        for keyword in self.error_keywords:
            if keyword in check_line:
                return True

        return False

    def generate_error_key(self, container_name: str, log_line: str) -> str:
        """
        生成错误的唯一标识键

        Args:
            container_name: 容器名称
            log_line: 日志行

        Returns:
            错误键
        """
        # 简单使用容器名 + 日志前 200 字符作为键
        return f"{container_name}:{log_line[:200]}"

    def is_duplicate_error(self, error_key: str) -> bool:
        """
        检查是否是重复错误

        Args:
            error_key: 错误键

        Returns:
            是否是重复错误
        """
        if error_key not in self.error_cache:
            return False

        last_time = self.error_cache[error_key]
        time_diff = (datetime.now() - last_time).total_seconds()

        return time_diff < self.dedup_window

    def check_rate_limit(self, container_name: str) -> bool:
        """
        检查发送频率限制

        Args:
            container_name: 容器名称

        Returns:
            是否可以发送
        """
        now = datetime.now()

        # 每分钟重置计数器
        if (now - self.last_rate_reset).total_seconds() >= 60:
            self.rate_limit_counter.clear()
            self.last_rate_reset = now

        # 检查当前容器的发送次数
        if self.rate_limit_counter[container_name] >= self.max_rate_per_minute:
            return False

        self.rate_limit_counter[container_name] += 1
        return True

    def start(self):
        """启动监控应用"""
        logger.info("=" * 50)
        logger.info("Docker 日志监控系统启动")
        logger.info("=" * 50)

        # 加载配置
        self.load_config()

        # 初始化组件
        self.initialize_components()

        # 测试飞书连接
        logger.info("测试飞书 Webhook 连接...")
        if self.feishu_notifier.test_connection():
            logger.info("飞书 Webhook 连接正常")
        else:
            logger.warning("飞书 Webhook 连接失败，请检查配置")

        # 启动 Docker 日志监控
        self.docker_monitor.start_monitoring()

        logger.info("监控系统运行中，按 Ctrl+C 停止...")

        # 保持主线程运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭...")
            self.stop()

    def stop(self):
        """停止监控应用"""
        if self.docker_monitor:
            self.docker_monitor.stop_monitoring()

        logger.info("监控系统已停止")
        sys.exit(0)


def main():
    """主函数"""
    # 创建日志目录
    Path('logs').mkdir(exist_ok=True)

    # 创建应用实例
    app = LogMonitorApp()

    # 注册信号处理
    signal.signal(signal.SIGINT, lambda s, f: app.stop())
    signal.signal(signal.SIGTERM, lambda s, f: app.stop())

    # 启动应用
    app.start()


if __name__ == '__main__':
    main()
