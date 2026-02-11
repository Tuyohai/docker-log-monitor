"""
Azure OpenAI 错误分析模块
使用 AI 分析 Docker 容器错误日志
"""
import logging
from typing import Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class ErrorAnalyzer:
    """使用 Azure OpenAI 分析错误的分析器"""

    def __init__(self, endpoint: str, api_key: str, deployment_name: str,
                 api_version: str = "2024-02-15-preview"):
        """
        初始化错误分析器

        Args:
            endpoint: Azure OpenAI 端点
            api_key: API 密钥
            deployment_name: 模型部署名称
            api_version: API 版本
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.client = None

    def connect(self):
        """初始化 Azure OpenAI 客户端"""
        try:
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version
            )
            logger.info("Azure OpenAI 客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化 Azure OpenAI 客户端失败: {e}")
            return False

    def analyze_error(self, error_log: str, container_name: str,
                      container_image: str = "unknown") -> Optional[str]:
        """
        分析错误日志并返回分析结果

        Args:
            error_log: 错误日志内容
            container_name: 容器名称
            container_image: 容器镜像

        Returns:
            分析结果字符串或 None
        """
        if not self.client:
            if not self.connect():
                return "AI 分析服务不可用"

        try:
            # 构建分析提示
            system_prompt = """你是一个专业的运维和开发专家，擅长分析容器错误日志。
请根据提供的错误日志，分析并给出：
1. **错误类型**: 简要说明这是什么类型的错误
2. **可能原因**: 列出 2-3 个最可能的原因
3. **解决建议**: 提供具体的解决方案或排查方向

请用中文回答，简洁明了，突出重点。"""

            user_prompt = f"""容器信息:
- 容器名称: {container_name}
- 容器镜像: {container_image}

错误日志:
```
{error_log}
```

请分析这个错误。"""

            # 调用 Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            analysis = response.choices[0].message.content
            logger.info(f"成功分析错误日志 (token 使用: {response.usage.total_tokens})")
            return analysis

        except Exception as e:
            logger.error(f"分析错误日志失败: {e}")
            return f"AI 分析失败: {str(e)}"

    def analyze_error_batch(self, errors: list) -> list:
        """
        批量分析多个错误

        Args:
            errors: 错误列表，每个错误是一个包含 error_log, container_name 等信息的字典

        Returns:
            分析结果列表
        """
        results = []
        for error in errors:
            analysis = self.analyze_error(
                error_log=error.get('error_log', ''),
                container_name=error.get('container_name', 'unknown'),
                container_image=error.get('container_image', 'unknown')
            )
            results.append({
                'error': error,
                'analysis': analysis
            })
        return results
