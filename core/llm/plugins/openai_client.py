import asyncio
import time
import httpx
from core.utils.logger import get_logger
from core.llm.llm_client import LLMClient
from config import REQUEST_TIMEOUT

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

        # 从配置文件中读取超时设置，默认为7秒
        self.timeout = REQUEST_TIMEOUT or 7

    async def get_response(self, context, user_input, system_prompt, retries=2):
        """
        根据给定的上下文和用户输入,从 OpenAI 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容
            system_prompt (str): 系统提示
            retries (int): 出现错误时的最大重试次数，默认值为2次

        返回:
            str: OpenAI 模型生成的回复内容

        异常:
            httpx.HTTPStatusError: 当请求 OpenAI API 出现问题时引发
        """
        # 检查是否为重复请求
        if time.time() - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning("<DUPLICATE> 检测到重复请求，已忽略:")
            _log.warning(f"   ↳ 用户输入: {user_input}")
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

        # 记录请求的 payload 和 headers
        _log.debug("<REQUEST> 请求参数:")
        _log.debug(f"   ↳ Payload: {payload}")
        _log.debug(f"   ↳ Headers: {headers}")

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.openai_api_url, headers=headers, json=payload)
                    response.raise_for_status()
                    response_data = response.json()

                # 记录完整的响应数据
                _log.debug("<RESPONSE> 完整响应数据:")
                _log.debug(f"   ↳ {response_data}")

                reply = response_data['choices'][0]['message']['content'] if 'choices' in response_data and \
                                                                             response_data['choices'][0]['message'][
                                                                                 'content'] else None

                # 更新 last_request_time 和 last_request_content
                self.last_request_time = time.time()
                self.last_request_content = user_input

                if reply is None:
                    _log.warning("<RESPONSE> OpenAI 回复为空:")
                    _log.warning(f"   ↳ 用户输入: {user_input}")
                else:
                    # 记录 OpenAI 的回复内容
                    _log.info("<RESPONSE> OpenAI 回复:")
                    _log.info(f"   ↳ 内容: {reply}")

                return reply

            except httpx.HTTPStatusError as e:
                _log.error("<ERROR> 🚨请求错误:")
                _log.error(f"   ↳ 状态码: {e.response.status_code}")
                _log.error(f"   ↳ 错误详情: {e}")
                _log.error(f"   ↳ 返回内容: {e.response.text}")
                if e.response.status_code in {503, 504, 500}:  # 处理常见错误状态码
                    _log.info(f"请求失败，状态码：{e.response.status_code}。正在尝试重试...({attempt + 1}/{retries})")
                    if attempt < retries:
                        await asyncio.sleep(2)  # 等待2秒后重试
                        continue
                return f"请求失败，状态码：{e.response.status_code}。请稍后再试。"


            except httpx.RequestError as e:
                _log.error("<ERROR> 请求异常:")
                _log.error(f"   ↳ 错误详情: {e}")
                _log.error(f"   ↳ 错误类型: {type(e)}")
                if attempt < retries:
                    _log.info(f"请求异常，正在尝试重试...({attempt + 1}/{retries})")
                    await asyncio.sleep(2)  # 等待2秒后重试
                    continue
                return "请求超时或网络错误，请稍后再试。"


            except Exception as e:

                _log.error("<ERROR> 未知错误:")
                _log.error(f"   ↳ 错误详情: {e}")
                _log.error(f"   ↳ 错误类型: {type(e)}")
                if attempt < retries:
                    _log.info(f"发生未知错误，正在尝试重试...({attempt + 1}/{retries})")
                    await asyncio.sleep(2)  # 等待2秒后重试
                    continue

                return "发生未知错误，请联系管理员。"

        return "请求失败，请稍后再试。"

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
    openai_secret = "sk-s2lDjPP1AdigpPBO53845f5d134a406d96CbE24aEeBe2d36"
    openai_model = "Meta-Llama-3.1-8B-Instruct"
    openai_api_url = "https://ngedlktfticp.cloud.sealos.io/v1/chat/completions"
    # 我可以把我的秘钥公开，因为额度很小，而且是用来测试的。但你一定不要像我一样把秘钥明文写在代码中。

    # 创建 OpenAIClient 实例
    client = OpenAIClient(openai_secret=openai_secret, openai_model=openai_model, openai_api_url=openai_api_url)

    # 运行测试
    asyncio.run(client.test())
