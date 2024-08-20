"""
AmyAlmond Project - core/llm/llm_client.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.5 (Beta_820003)

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