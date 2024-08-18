"""
AmyAlmond Project - utils.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.0 (Alpha_817001)

utils.py - 工具函数模块
"""

import re


def extract_memory_content(message):
    match = re.search(r'<memory>(.*?)</memory>', message, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def load_system_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
