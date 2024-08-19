"""
AmyAlmond Project - core/memory/memory_manager.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.5 (Alpha_819002)

memory_manager.py 包含管理消息历史和长期记忆的主要类和方法
"""

import json
import os
from collections import deque

# config.py模块 - <配置文件包含常量和路径>
from config import MAX_CONTEXT_MESSAGES, MEMORY_FILE, LONG_TERM_MEMORY_FILE
# logger.py模块 - <日志记录模块>
from core.utils.logger import get_logger

_log = get_logger()


class MemoryManager:
    """
    管理消息历史和长期记忆的类
    """

    def __init__(self):
        """
        初始化 MemoryManager 实例,创建一个空的消息历史记录字典
        """
        self.message_history = {}

    async def append_to_long_term_memory(self, group_id, content):
        """
        将内容追加到长期记忆文件中

        参数:
            group_id (str): 群组的唯一标识符
            content (str): 需要存储的内容
        """
        try:
            with open(LONG_TERM_MEMORY_FILE.format(group_id), "a", encoding="utf-8") as f:
                f.write(content + "\n")
            _log.info(f"已将内容添加到群组 {group_id} 的长期记忆中")
        except Exception as e:
            _log.error(f"将内容添加到群组 {group_id} 的长期记忆时发生错误: {e}")

    async def load_memory(self):
        """
        加载内存中的消息历史和长期记忆文件

        读取 memory_file 文件中的数据,并加载每个群组的消息历史。
        如果长期记忆文件存在,也会加载并添加到消息历史中
        """
        _log.info("Loading memory...")

        # 检查 memory_file 是否存在
        if not os.path.exists(MEMORY_FILE):
            _log.info(f"记忆文件 {MEMORY_FILE} 不存在,将从空记忆开始。")
            return

        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                _log.info(f"Reading memory file: {MEMORY_FILE}")
                data = json.load(f)
        except json.JSONDecodeError as e:
            _log.warning(f"记忆文件 {MEMORY_FILE} 格式有误,将从空记忆开始。错误信息: {e}")
            return
        except Exception as e:
            _log.error(f"读取记忆文件 {MEMORY_FILE} 时发生错误: {e}")
            return

        _log.info(f"Memory file content: {data}")
        for group_id, messages in data.items():
            _log.info(f"Processing group: {group_id}")
            if not isinstance(messages, list):
                _log.warning(f"群组 {group_id} 的数据格式不正确,将跳过该群组。")
                continue

            self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_MESSAGES)
            for message in messages:
                if isinstance(message, dict) and 'role' in message and 'content' in message:
                    self.message_history[group_id].append(message)
                else:
                    _log.warning(f"群组 {group_id} 中包含无效的消息,将跳过该消息: {message}")

            _log.info(f"Loaded {len(self.message_history[group_id])} messages for group {group_id}")

            # 尝试加载长期记忆文件
            try:
                long_term_memory_file = LONG_TERM_MEMORY_FILE.format(group_id)
                if os.path.exists(long_term_memory_file):
                    with open(long_term_memory_file, "r", encoding="utf-8") as f:
                        long_term_memory = f.read()
                        self.message_history[group_id].appendleft({"role": "system", "content": long_term_memory})
                        _log.info(f"Loaded long-term memory for group {group_id}")
                else:
                    _log.info(f"群组 {group_id} 的长期记忆文件不存在,将跳过加载。")
            except Exception as e:
                _log.warning(f"加载群组 {group_id} 的长期记忆时发生错误: {e}")

        _log.info("Memory loading completed")

    async def save_memory(self):
        """
        将当前的消息历史保存到内存文件中

        将每个群组的消息历史保存到 memory_file 中,以便下次加载
        """
        _log.info("Saving memory...")
        try:
            data = {}
            for group_id, messages in self.message_history.items():
                if len(messages) > MAX_CONTEXT_MESSAGES:
                    messages = list(messages)[-MAX_CONTEXT_MESSAGES:]
                data[group_id] = list(messages)
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            _log.error(f"Error saving memory: {e}")

    async def compress_memory(self, group_id, get_gpt_response):
        """
        压缩消息历史,以减少内存占用

        如果消息历史超过最大允许条数,会使用 GPT 模型生成一个摘要并替换历史记录

        参数:
            group_id (str): 群组的唯一标识符
            get_gpt_response (function): 用于获取 GPT 回复的函数

        返回:
            list: 压缩后的消息历史
        """
        message_history = self.get_message_history(group_id)
        if len(message_history) > MAX_CONTEXT_MESSAGES:
            summary = await get_gpt_response(
                list(message_history), "请用一句话总结以上对话"
            )
            message_history.clear()
            message_history.append({"role": "assistant", "content": summary})
        return list(message_history)

    async def read_long_term_memory(self, group_id):
        """
        读取长期记忆文件的内容

        参数:
            group_id (str): 群组的唯一标识符

        返回:
            str: 长期记忆的内容,如果文件不存在则返回提示信息
        """
        try:
            with open(LONG_TERM_MEMORY_FILE.format(group_id), "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "暂无长期记忆,请先与我聊天以建立对话记忆"

    def get_message_history(self, group_id):
        """
        获取指定群组的消息历史

        参数:
            group_id (str): 群组的唯一标识符

        返回:
            deque: 包含消息历史的双端队列
        """
        return self.message_history.get(group_id, deque(maxlen=MAX_CONTEXT_MESSAGES))

    def add_message_to_history(self, group_id, message):
        """
        添加一条消息到指定群组的消息历史中

        参数:
            group_id (str): 群组的唯一标识符
            message (dict): 包含角色和内容的消息字典
        """
        if group_id not in self.message_history:
            self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_MESSAGES)
        self.message_history[group_id].append(message)
