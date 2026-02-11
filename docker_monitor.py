"""
Docker 日志监控模块
监控 Docker 容器日志并检测错误
"""
import docker
import logging
from typing import List, Callable, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class DockerLogMonitor:
    """Docker 容器日志监控器"""

    def __init__(self, containers: List[str], error_callback: Callable,
                 tail: str = "latest", follow: bool = True, timestamps: bool = True):
        """
        初始化 Docker 日志监控器

        Args:
            containers: 要监控的容器名称或 ID 列表
            error_callback: 检测到错误时的回调函数
            tail: 从哪里开始读取日志 ("latest" 或数字)
            follow: 是否持续跟随日志流
            timestamps: 是否包含时间戳
        """
        self.containers = containers
        self.error_callback = error_callback
        self.tail = tail
        self.follow = follow
        self.timestamps = timestamps
        self.client = None
        self.monitor_threads = []
        self.stop_flag = threading.Event()

    def connect(self):
        """连接到 Docker 守护进程"""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("成功连接到 Docker 守护进程")
            return True
        except Exception as e:
            logger.error(f"连接 Docker 守护进程失败: {e}")
            return False

    def start_monitoring(self):
        """开始监控所有配置的容器"""
        if not self.client:
            if not self.connect():
                raise Exception("无法连接到 Docker 守护进程")

        logger.info(f"开始监控 {len(self.containers)} 个容器的日志")

        for container_ref in self.containers:
            thread = threading.Thread(
                target=self._monitor_container,
                args=(container_ref,),
                daemon=True
            )
            thread.start()
            self.monitor_threads.append(thread)
            logger.info(f"已启动容器 '{container_ref}' 的监控线程")

    def stop_monitoring(self):
        """停止监控所有容器"""
        logger.info("正在停止日志监控...")
        self.stop_flag.set()

        for thread in self.monitor_threads:
            thread.join(timeout=5)

        logger.info("所有监控线程已停止")

    def _monitor_container(self, container_ref: str):
        """
        监控单个容器的日志

        Args:
            container_ref: 容器名称或 ID
        """
        try:
            container = self.client.containers.get(container_ref)
            logger.info(f"开始监控容器: {container.name} ({container.short_id})")

            # 获取日志流
            log_stream = container.logs(
                stream=True,
                follow=self.follow,
                tail=self.tail if self.tail != "latest" else "0",
                timestamps=self.timestamps
            )

            for log_line in log_stream:
                if self.stop_flag.is_set():
                    break

                try:
                    # 解码日志行
                    log_text = log_line.decode('utf-8').strip()

                    if log_text:
                        # 调用回调函数处理日志行
                        self.error_callback(
                            container_name=container.name,
                            container_id=container.short_id,
                            log_line=log_text,
                            timestamp=datetime.now()
                        )
                except Exception as e:
                    logger.error(f"处理容器 {container.name} 的日志时出错: {e}")

        except docker.errors.NotFound:
            logger.error(f"容器未找到: {container_ref}")
        except Exception as e:
            logger.error(f"监控容器 {container_ref} 时发生错误: {e}")

    def get_container_info(self, container_ref: str) -> Optional[dict]:
        """
        获取容器信息

        Args:
            container_ref: 容器名称或 ID

        Returns:
            容器信息字典或 None
        """
        try:
            container = self.client.containers.get(container_ref)
            return {
                'name': container.name,
                'id': container.short_id,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown'
            }
        except Exception as e:
            logger.error(f"获取容器信息失败: {e}")
            return None
