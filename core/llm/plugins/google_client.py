"""
[官方] Google AI Platform 客户端，实现了 LLMClient 接口。
提供商: Google Cloud Platform (https://cloud.google.com/)
文档: https://cloud.google.com/vertex-ai/docs/generative-ai/language/overview

请注意：如需使用，请先取消 第12-13行 和 38-40行 的注释，并安装对应的包。
"""
import time
import asyncio
from typing import List, Dict

# from google.api_core.client_options import ClientOptions
# from google.cloud import aiplatform_v1

from core.utils.logger import get_logger
from core.llm.llm_client import LLMClient
_log = get_logger()


class GoogleClient(LLMClient):
    """
    Google AI Platform 客户端，实现了 LLMClient 接口。

    支持模型:
        - text-bison-001
        - code-bison-001
        - image-bison-001
    """

    async def on_message(self, message, reply_message):
        pass

    def __init__(self, google_api_key: str, google_model: str, google_api_url: str):
        self.google_api_key = google_api_key
        self.google_model = google_model
        self.google_api_url = google_api_url

        # 使用 google.api_core.client_options 设置 API 密钥
        # client_options = ClientOptions(api_key=self.google_api_key)
        # self.client = aiplatform_v1.PredictionServiceClient(client_options=client_options)

        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

    async def get_response(self, context: List[Dict], user_input: str, system_prompt: str) -> str:
        """
        根据给定的上下文和用户输入,从 Google AI Platform 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容
            system_prompt (str): 系统提示

        返回:
            str: Google AI Platform 模型生成的回复内容

        异常:
            Exception: 当请求 Google AI Platform API 出现问题时引发
        """
        # 检查是否为重复请求
        if time.time() - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning(f"Duplicate request detected and ignored: {user_input}")
            return None

        # 构建请求实例
        endpoint = f"{self.google_api_url}/projects//locations//publishers//models/{self.google_model}:predict"
        # 将上下文信息合并到单个字符串中
        prompt = system_prompt + "".join([f"{message['role']}: {message['content']}" for message in context]) + f"user: {user_input}"

        # 构建请求参数
        parameters = {}
        # 构建请求体
        instance = {"content": prompt}
        response = await asyncio.to_event_loop(self.client.predict(
            endpoint=endpoint,
            instances=[instance],
            parameters=parameters,
        ))
        #  更新 last_request_time 和 last_request_content
        self.last_request_time = time.time()
        self.last_request_content = user_input
        # 处理响应
        if response.predictions:
            reply = response.predictions[0]['content']
            _log.info(f"Google AI Platform response: {reply}")
            return reply
        else:
            _log.warning(f"Google AI Platform response is empty for user input: {user_input}.")
            return "子网故障,过来楼下检查一下/。"