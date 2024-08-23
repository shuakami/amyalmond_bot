import asyncio
import time
import httpx
from core.utils.logger import get_logger
from core.llm.llm_client import LLMClient

_log = get_logger()


class OpenAIClient(LLMClient):
    """
    OpenAI API 客户端，实现了 LLMClient 接口。
    """

    async def on_message(self, message, reply_message):
        pass

    def __init__(self, openai_secret, openai_model, openai_api_url):
        self.openai_secret = openai_secret
        self.openai_model = openai_model
        self.openai_api_url = openai_api_url

        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

    async def get_response(self, context, user_input, system_prompt):
        """
        根据给定的上下文和用户输入,从 OpenAI 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容
            system_prompt (str): 系统提示

        返回:
            str: OpenAI 模型生成的回复内容

        异常:
            httpx.HTTPStatusError: 当请求 OpenAI API 出现问题时引发
        """
        # 检查是否为重复请求
        if time.time() - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning(f"Duplicate request detected and ignored: {user_input}")
            return None

        payload = {
            "model": self.openai_model,
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
            "Authorization": f"Bearer {self.openai_secret}"
        }

        # 记录请求的payload
        _log.debug(f"Request payload: {payload}")

        # 打印请求头
        _log.debug(f"Request headers: {headers}")

        # 打印一遍全配置
        _log.debug(f"Full configuration: {self.__dict__}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.openai_api_url, headers=headers, json=payload)
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
                _log.warning(f"OpenAI response is empty for user input: {user_input}.")
            else:
                # 记录 OpenAI 的回复内容
                _log.info(f"OpenAI response: {reply}")

            return reply
        except httpx.HTTPStatusError as e:
            _log.error(f"Error requesting from OpenAI API: {e}", exc_info=True)
            return "子网故障,过来楼下检查一下/。"


    async def test(self):
        """
        测试 OpenAIClient 类的方法
        """
        context = [
            {"role": "user", "content": "你好！"}
        ]
        user_input = "你还记得我之前说了多少个“你好”吗"
        system_prompt = "你是一个友好的助手。"

        response = await self.get_response(context, user_input, system_prompt)
        print("API Response:", response)


# 使用方法
if __name__ == "__main__":
    # 配置 OpenAIClient
    openai_secret = "hk-x4xh1d1000010138e640592513caf599a394f11c49568645"
    openai_model = "gpt-4o-mini"
    openai_api_url = "https://api.openai-hk.com/v1/chat/completions"

    # 创建 OpenAIClient 实例
    client = OpenAIClient(openai_secret=openai_secret, openai_model=openai_model, openai_api_url=openai_api_url)

    # 运行测试
    asyncio.run(client.test())
