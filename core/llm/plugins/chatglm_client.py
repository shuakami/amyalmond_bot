"""
[官方] ChatGLM API 客户端，实现了 LLMClient 接口。
提供商: 智谱AI (https://www.zhipuai.cn/)
文档: https://open.bigmodel.cn/docs/api

请注意：如需使用，请先取消 第10行 和 49-54行 的注释，并安装jwt包。
"""
import time
import httpx
# import jwt
from core.utils.logger import get_logger
from core.llm.llm_client import LLMClient

_log = get_logger()


class ChatGLMClient(LLMClient):
    """
    ChatGLM API 客户端，实现了 LLMClient 接口。

    支持模型:
        - glm-4
    """

    async def on_message(self, message, reply_message):
        pass

    def __init__(self, chatglm_secret, chatglm_model, chatglm_api_url):
        self.chatglm_secret = chatglm_secret
        self.chatglm_model = chatglm_model
        self.chatglm_api_url = chatglm_api_url

        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

    def generate_token(self, exp_seconds: int = 3600):
        """生成JWT Token"""
        try:
            id, secret = self.chatglm_secret.split(".")
        except Exception as e:
            raise Exception("Invalid apikey", e)

        payload = {
            "api_key": id,
            "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
            "timestamp": int(round(time.time() * 1000)),
        }
        # return jwt.encode(
        #     payload,
        #     secret,
        #     algorithm="HS256",
        #     headers={"alg": "HS256", "sign_type": "SIGN"},
        # )

    async def get_response(self, context, user_input, system_prompt):
        """
        根据给定的上下文和用户输入,从 ChatGLM 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容
            system_prompt (str): 系统提示

        返回:
            str: ChatGLM 模型生成的回复内容

        异常:
            httpx.HTTPStatusError: 当请求 ChatGLM API 出现问题时引发
        """
        # 检查是否为重复请求
        if time.time() - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning(f"Duplicate request detected and ignored: {user_input}")
            return None

        payload = {
            "model": self.chatglm_model,
            "messages": [
                            {"role": "system", "content": system_prompt}
                        ] + context + [
                            {"role": "user", "content": user_input}
                        ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.generate_token()}"
        }

        # 记录请求的payload
        _log.debug(f"Request payload: {payload}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.chatglm_api_url, headers=headers, json=payload)
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
                _log.warning(f"ChatGLM response is empty for user input: {user_input}.")
            else:
                # 记录 ChatGLM 的回复内容
                _log.info(f"ChatGLM response: {reply}")

            return reply
        except httpx.HTTPStatusError as e:
            _log.error(f"Error requesting from ChatGLM API: {e}", exc_info=True)
            return "子网故障,过来楼下检查一下/。"