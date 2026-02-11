"""
飞书消息发送模块
发送错误日志和分析结果到飞书群聊
"""
import logging
import requests
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeishuNotifier:
    """飞书消息通知器"""

    def __init__(self, webhook_url: str):
        """
        初始化飞书通知器

        Args:
            webhook_url: 飞书自定义机器人 Webhook URL
        """
        self.webhook_url = webhook_url

    def send_error_notification(self, container_name: str, container_id: str,
                                error_log: str, analysis: str,
                                timestamp: datetime, container_image: str = "unknown") -> bool:
        """
        发送错误通知到飞书群聊

        Args:
            container_name: 容器名称
            container_id: 容器 ID
            error_log: 错误日志
            analysis: AI 分析结果
            timestamp: 错误时间戳
            container_image: 容器镜像

        Returns:
            是否发送成功
        """
        try:
            # 构建消息卡片
            card = self._build_error_card(
                container_name=container_name,
                container_id=container_id,
                container_image=container_image,
                error_log=error_log,
                analysis=analysis,
                timestamp=timestamp
            )

            # 发送消息
            response = requests.post(
                self.webhook_url,
                json=card,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"成功发送飞书通知: 容器 {container_name}")
                    return True
                else:
                    logger.error(f"飞书 API 返回错误: {result}")
                    return False
            else:
                logger.error(f"发送飞书消息失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送飞书消息时发生异常: {e}")
            return False

    def _build_error_card(self, container_name: str, container_id: str,
                         container_image: str, error_log: str,
                         analysis: str, timestamp: datetime) -> dict:
        """
        构建飞书消息卡片

        Args:
            container_name: 容器名称
            container_id: 容器 ID
            container_image: 容器镜像
            error_log: 错误日志
            analysis: AI 分析结果
            timestamp: 时间戳

        Returns:
            消息卡片 JSON
        """
        # 限制日志长度
        max_log_length = 3000
        if len(error_log) > max_log_length:
            error_log = error_log[:max_log_length] + "\n... (日志过长，已截断)"

        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        card = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚨 Docker 容器错误告警"
                    },
                    "template": "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**容器名称**\n{container_name}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**容器 ID**\n{container_id}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**容器镜像**\n{container_image}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**发生时间**\n{time_str}"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**📋 错误日志**\n```\n{error_log}\n```"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**🤖 AI 分析**\n{analysis}"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": "由 Docker 日志监控系统自动发送"
                            }
                        ]
                    }
                ]
            }
        }

        return card

    def send_simple_message(self, content: str) -> bool:
        """
        发送简单文本消息

        Args:
            content: 消息内容

        Returns:
            是否发送成功
        """
        try:
            message = {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }

            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('code') == 0
            return False

        except Exception as e:
            logger.error(f"发送飞书简单消息时发生异常: {e}")
            return False

    def test_connection(self) -> bool:
        """
        测试飞书 Webhook 连接

        Returns:
            连接是否正常
        """
        return self.send_simple_message("✅ Docker 日志监控系统启动成功！")
