"""
AmyAlmond Project - core/utils/user_management.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei

Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.0 (Pre_827001)

user_management.py - 用户管理模块，负责用户名映射的加载和保存
"""

import json
from config import USER_NAMES_FILE

USER_NAMES = {}


def clean_content(content):
    return content.replace('<@!', '').replace('>', '')


def get_user_name(user_id):
    """根据用户 ID 获取用户名"""
    return USER_NAMES.get(user_id, f"消息来自未知用户：")


def load_user_names():
    """从文件加载用户名映射"""
    global USER_NAMES
    try:
        with open(USER_NAMES_FILE, "r", encoding="utf-8") as f:
            USER_NAMES = json.load(f)
    except FileNotFoundError:
        USER_NAMES = {}


def save_user_names():
    """保存用户名映射到文件"""
    with open(USER_NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_NAMES, f, ensure_ascii=False, indent=4)


async def add_new_user(user_id, nickname):
    global USER_NAMES
    USER_NAMES[user_id] = f"消息来自{nickname}："
    save_user_names()
    return True


def is_user_registered(user_id):
    return user_id in USER_NAMES
