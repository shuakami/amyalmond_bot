"""
AmyAlmond Project - core/utils/utils.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.5 (Alpha_819002)

utils.py - 工具函数模块
"""

import re
from typing import Optional
# logger.py模块 - <用于记录日志>
from .logger import get_logger

_log = get_logger()


def extract_memory_content(message: object) -> Optional[str]:
    """
    从消息中提取记忆内容。支持字符串和字节类型，并尝试转换其他类型到字符串。

    参数:
        message (object): 需要检查的消息内容，可以是任何类型。

    返回:
        Optional[str]: 如果找到匹配的记忆内容则返回该内容的字符串形式，否则返回None。

    异常处理:
        在尝试转换或正则表达式匹配时发生的任何异常都将被捕获，并返回None，同时记录警告。
    """
    try:
        # 尝试将message转换为字符串
        if not isinstance(message, (str, bytes)):
            message_str = str(message)
        elif isinstance(message, bytes):
            message_str = message.decode('utf-8', errors='replace')  # 用replace处理解码错误
        else:
            message_str = message

        # 使用正则表达式查找记忆内容
        match = re.search(r'<memory>(.*?)</memory>', message_str, re.DOTALL)
        if match:
            # 使用strip()来清除前后空白
            return match.group(1).strip()
    except (TypeError, ValueError, UnicodeDecodeError, AttributeError) as e:
        # 捕获可能出现的任何类型错误
        _log.warning(f"Warning: Could not extract memory content due to: {e}. Input was: {message}")
    return None


def load_system_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
