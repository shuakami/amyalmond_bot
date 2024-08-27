import aiohttp
import asyncio
from config import TEA_URL, TEA_SECRET, TEA_MODEL, DIMENSION
from core.utils.logger import get_logger

_log = get_logger()


class TeaClient:
    """
    Tea API 客户端，用于与LLM模型交互以生成向量。
    """

    def __init__(self):
        self.tea_url = TEA_URL
        self.tea_secret = TEA_SECRET
        self.tea_model = TEA_MODEL
        self.dimension = DIMENSION

    async def generate_vector(self, input_text, max_retries=3, timeout=130):
        """
        向Tea API发送请求以生成向量。

        参数:
            input_text (str): 要生成向量的文本内容。
            max_retries (int): 请求失败时的最大重试次数。
            timeout (int): 每次请求的超时时间，单位为秒。

        返回:
            list: 生成的向量（浮点数列表），或None如果请求失败。
        """
        system_prompt = (
            f"你是一个向量提取模型。给定输入文本后，"
            f"你必须只输出该文本的向量表示，格式为用逗号分隔的浮点数列表。"
            f"你必须完全确保向量的长度为 {self.dimension}。(维度：{self.dimension})"
            f"不要输出任何其他文本或信息，也不要在浮点数之间包含多余的空格。"
        )

        payload = {
            "model": self.tea_model,
            "temperature": 0.45,
            "max_tokens": 4000,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.tea_secret}"
        }

        _log.debug(f"Tea API Request payload: {payload}")

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.tea_url, headers=headers, json=payload, timeout=timeout) as response:
                        response.raise_for_status()
                        response_data = await response.json()

                _log.debug(f"Tea API Response data: {response_data}")

                reply = response_data['choices'][0]['message']['content'].strip() if 'choices' in response_data and \
                                                                                     'message' in \
                                                                                     response_data['choices'][
                                                                                         0] else None

                _log.debug(f"Tea API Response reply: {reply}")

                if reply:
                    try:
                        vector_output = [float(x) for x in reply.split(',')]
                        if len(vector_output) == self.dimension:
                            _log.info(f"Generated vector: {vector_output}")
                            return vector_output
                        else:
                            raise ValueError(f"向量长度不匹配，期望{self.dimension}，实际得到{len(vector_output)}")
                    except ValueError as e:
                        _log.error(f"Failed to parse vector: {reply}. Error: {e}")
                        await asyncio.sleep(1)
                else:
                    _log.warning(f"Tea API response did not contain a valid vector for input_text: {input_text}.")
                    return None

            except aiohttp.ClientError as e:
                _log.error(f"Error requesting from Tea API: {e}", exc_info=True)
                await asyncio.sleep(1)

        return None


# 主测试
if __name__ == "__main__":
    async def main():
        # 示例用法
        tea_client = TeaClient()
        test_content = "你好，世界！"
        # 生成向量
        vector_result = await tea_client.generate_vector(test_content)
        # 打印向量
        print(vector_result)


    # 运行测试
    asyncio.run(main())
