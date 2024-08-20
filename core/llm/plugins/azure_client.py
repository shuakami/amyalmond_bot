"""
[官方] Azure OpenAI API 客户端，实现了 LLMClient 接口。
提供商: Microsoft Azure（https://azure.microsoft.com/zh-cn/）
文档: https://learn.microsoft.com/en-us/azure/cognitive-services/openai/
"""
import time
import httpx
from core.utils.logger import get_logger
from core.llm.llm_client import LLMClient

_log = get_logger()


class AzureClient(LLMClient):
    """
    Azure API 客户端，实现了 LLMClient 接口。

    支持模型:
        - text-davinci-003
        - text-davinci-002
        - text-curie-001
        - text-babbage-001
        - text-ada-001
        - code-davinci-002
        - code-cushman-001
    """

    async def on_message(self, message, reply_message):
        pass

    def __init__(self, azure_secret, azure_model, azure_api_url):
        self.azure_secret = azure_secret
        self.azure_model = azure_model
        self.azure_api_url = azure_api_url

        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

    async def get_response(self, context, user_input, system_prompt):
        """
        根据给定的上下文和用户输入,从 Azure 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容
            system_prompt (str): 系统提示

        返回:
            str: Azure 模型生成的回复内容

        异常:
            httpx.HTTPStatusError: 当请求 Azure API 出现问题时引发
        """
        # 检查是否为重复请求
        if time.time() - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning(f"Duplicate request detected and ignored: {user_input}")
            return None

        payload = {
            "model": self.azure_model,
            "temperature": 0.85,
            "top_p": 1,
            "presence_penalty": 1,
            "max_tokens": 3450,
            "messages": [
                            {"role": "system", "content": system_prompt}
                        ] + context + [
                            {"role": "user", "content": user_input}
                        ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.azure_secret}"
        }

        # 记录请求的payload
        _log.debug(f"Request payload: {payload}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.azure_api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

            # 记录完整的响应数据
            _log.debug(f"Response data: {response_data}")

            reply = response_data['choices'][0]['message']['content'] if 'choices' in response_data and \
                                                                         response_data['choices'][0]['message'][
                                                                             'content'] else None

            #  更新 last_request_time 和 last_request_content
            self.last_request_time = time.time()
            self.last_request_content = user_input

            if reply is None:
                _log.warning(f"Azure response is empty for user input: {user_input}.")
            else:
                # 记录 Azure 的回复内容
                _log.info(f"Azure response: {reply}")

            return reply
        except httpx.HTTPStatusError as e:
            _log.error(f"Error requesting from Azure API: {e}", exc_info=True)
            return "子网故障,过来楼下检查一下/。"