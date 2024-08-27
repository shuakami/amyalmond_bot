"""
[官方] Anthropic API 客户端，实现了 LLMClient 接口。
提供商: Anthropic (https://www.anthropic.com/)
文档: https://docs.anthropic.com/
"""
import time
import httpx
from core.utils.logger import get_logger
from core.llm.llm_client import LLMClient

_log = get_logger()


class AnthropicClient(LLMClient):
    """
    Anthropic API 客户端，实现了 LLMClient 接口。

    支持模型:
        - claude-v1
        - claude-instant-v1
    """

    async def on_message(self, message, reply_message):
        pass

    def __init__(self, anthropic_secret, anthropic_model, anthropic_api_url):
        self.anthropic_secret = anthropic_secret
        self.anthropic_model = anthropic_model
        self.anthropic_api_url = anthropic_api_url

        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

    async def get_response(self, context, user_input, system_prompt):
        """
        根据给定的上下文和用户输入,从 Anthropic 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容
            system_prompt (str): 系统提示

        返回:
            str: Anthropic 模型生成的回复内容

        异常:
            httpx.HTTPStatusError: 当请求 Anthropic API 出现问题时引发
        """
        # 检查是否为重复请求
        if time.time() - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning(f"Duplicate request detected and ignored: {user_input}")
            return None

        # Anthropic 使用稍微不同的 prompt 格式，将 system_prompt 附加到 user_input 前面
        prompt = f"{system_prompt} {user_input}"

        payload = {
            "model": self.anthropic_model,
            "prompt": prompt,
            "max_tokens_to_sample": 3450, # 与 OpenAI 的 max_tokens 参数对应
            "temperature": 0.85,
            "top_p": 1,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.anthropic_secret}"
        }

        # 记录请求的payload
        _log.debug(f"Request payload: {payload}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.anthropic_api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

            # 记录完整的响应数据
            _log.debug(f"Response data: {response_data}")

            # Anthropic 的响应结构与 OpenAI 不同，需要提取 'completion' 字段
            reply = response_data.get('completion')

            #  更新 last_request_time 和 last_request_content
            self.last_request_time = time.time()
            self.last_request_content = user_input

            if reply is None:
                _log.warning(f"Anthropic response is empty for user input: {user_input}.")
            else:
                # 记录 Anthropic 的回复内容
                _log.info(f"Anthropic response: {reply}")

            return reply
        except httpx.HTTPStatusError as e:
            _log.error(f"Error requesting from Anthropic API: {e}", exc_info=True)
            return "子网故障,过来楼下检查一下/。"