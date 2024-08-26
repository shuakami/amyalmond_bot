"""
AmyAlmond Project - core/utils/utils.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.2.0 (Beta_826010)

utils.py - 工具函数模块
"""

import re
import platform
from typing import Optional, Tuple
# logger.py模块 - <用于记录日志>
from core.utils.logger import get_logger

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


def calculate_token_count(messages: list) -> int:
    """
    计算消息列表中的token数量，用于确保消息上下文不会超出LLM的token限制。

    参数:
        messages (list): 包含消息字典的列表，每个字典包含角色和内容。

    返回:
        int: 消息列表中的总token数量。
    """
    total_tokens = 0

    # 逐条消息计算token数量
    for message in messages:
        content = message.get('content', '')
        tokens = tokenize(content)
        total_tokens += len(tokens)

    return total_tokens


def tokenize(text: str) -> list:
    """
    将给定的文本拆分为token列表。

    参数:
        text (str): 需要token化的文本。

    返回:
        list: 包含文本中token的列表。
    """
    # 使用简单的正则表达式模拟GPT的token化规则
    tokens = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    return tokens


def detect_os_and_version() -> Tuple[Optional[str], Optional[str]]:
    """
    检测当前用户的操作系统和版本。

    返回:
        Tuple[Optional[str], Optional[str]]: 一个元组，包含操作系统名称和版本信息。
        如果检测失败，返回 (None, None)。
    """
    try:
        os_name = platform.system()
        os_version = None

        if os_name == "Windows":
            os_version = platform.release()
        elif os_name == "Linux":
            try:
                # 尝试获取更详细的Linux版本信息
                with open("/etc/os-release", "r") as f:
                    release_info = f.read()
                match = re.search(r'PRETTY_NAME="([^"]+)"', release_info)
                if match:
                    os_version = match.group(1)
                else:
                    os_version = platform.version()  # 备用方法获取Linux内核版本
            except FileNotFoundError:
                os_version = platform.version()
        elif os_name == "Darwin":
            os_version = platform.mac_ver()[0]  # 获取macOS版本
        else:
            _log.warning(f"Warning: Unrecognized operating system: {os_name}")

        return os_name, os_version

    except Exception as e:
        _log.error(f"Error: Failed to detect OS and version due to: {e}")
        return None, None
