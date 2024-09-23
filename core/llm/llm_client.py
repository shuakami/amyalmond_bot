"""
AmyAlmond Project - core/llm/llm_client.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

llm_client.py - 定义了 LLM 客户端接口。
"""
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """
    LLM 客户端接口,定义了所有 LLM 客户端都需要实现的方法。
    """

    @abstractmethod
    async def on_message(self, message, reply_message):
        """
        处理消息事件。

        Args:
            message (botpy.Message): 接收到的消息对象。
            reply_message (str): 待处理的回复消息。

        Returns:
            str: 处理后的回复消息。
        """
        pass

    @abstractmethod
    async def get_response(self, context, user_input, system_prompt):
        """
        根据上下文和用户输入，获取 LLM 模型的回复。

        Args:
            context (list): 对话上下文，包含之前的对话内容。
            user_input (str): 用户输入的内容。
            system_prompt (str): 系统提示。

        Returns:
            str: LLM 模型生成的回复内容。
        """
        pass
