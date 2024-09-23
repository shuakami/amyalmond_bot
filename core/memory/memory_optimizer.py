# core/memory/memory_optimizer.py
from core.llm.plugins.openai_client import OpenAIClient

class MemoryOptimizer:
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client

    async def optimize_memory(self, messages):
        """
        使用LLM优化消息内容，提取出重要信息。

        参数:
            messages (list): 要优化的消息列表

        返回:
            str: 优化后的记忆内容
        """
        joined_messages = "\n".join(messages)
        system_prompt = "你是高级算法机器，请在不忽略关键人名或数据以及细节的情况下总结无损压缩对话，提取重要的细节并删除冗余、不重要信息。"
        response = await self.openai_client.get_response(
            context=[],
            user_input=joined_messages,
            system_prompt=system_prompt
        )
        return response.strip() if response else ""
