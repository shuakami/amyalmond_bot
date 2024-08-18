"""
AmyAlmond Project - config.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/18 10:35
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.0 (Alpha_817002)

config.py - 配置文件读取与验证
"""
import os
from botpy.ext.cog_yaml import read
from logger import _log

# 定义目录结构
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "configs")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# 确保目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 配置文件路径
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
SYSTEM_PROMPT_FILE = os.path.join(CONFIG_DIR, "system-prompt.txt")

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

# 数据文件路径
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
LONG_TERM_MEMORY_FILE = os.path.join(DATA_DIR, "long_term_memory_{}.txt")
USER_NAMES_FILE = os.path.join(DATA_DIR, "user_names.json")

# 读取配置文件
test_config = {}
if os.path.exists(CONFIG_FILE):
    loaded_config = read(CONFIG_FILE)
    if loaded_config:
        test_config.update(loaded_config)
    else:
        print(f"")
        _log.critical(f"配置文件为空: {CONFIG_FILE}")
        _log.critical(f"请检查配置文件是否正确填写，并确保其格式为 YAML")
        exit(1)
else:
    print(f"")
    _log.critical(f"找不到配置文件: {CONFIG_FILE}")
    _log.critical(f"请确保在 {CONFIG_DIR} 目录下存在 config.yaml 文件")
    exit(1)

# 配置参数
MAX_CONTEXT_MESSAGES = 6
OPENAI_SECRET = test_config.get("openai_secret", "")
OPENAI_MODEL = test_config.get("openai_model", "gpt-4o-mini")
OPENAI_API_URL = test_config.get("openai_api_url", "https://api.openai-hk.com/v1/chat/completions")
ADMIN_ID = test_config.get("admin_id", "")

# 日志配置
LOG_LEVEL = test_config.get("log_level", "INFO").upper()
DEBUG_MODE = test_config.get("debug", False)

# 验证关键配置
if not OPENAI_SECRET:
    _log.warning("OpenAI API 密钥缺失,请检查 config.yaml 文件")
if not OPENAI_MODEL:
    _log.warning("OpenAI 模型缺失,请检查 config.yaml 文件")
if not OPENAI_API_URL:
    _log.warning("OpenAI API URL 缺失,请检查 config.yaml 文件")
if not ADMIN_ID:
    _log.warning("管理员 ID 缺失,请检查 config.yaml 文件")

# DEBUG情况下
if DEBUG_MODE:
    if OPENAI_SECRET and OPENAI_MODEL and OPENAI_API_URL and ADMIN_ID:
        masked_secret = '*' * (len(OPENAI_SECRET) - 4) + OPENAI_SECRET[-4:]
        masked_admin_id = '*' * (len(ADMIN_ID) - 4) + ADMIN_ID[-4:]
        print("")
        _log.debug(f"OpenAI API 密钥: {masked_secret}")
        _log.debug(f"OpenAI 模型: {OPENAI_MODEL}")
        _log.debug(f"OpenAI API URL: {OPENAI_API_URL}")
        _log.debug(f"管理员 ID: {masked_admin_id}")
    _log.debug(f"日志级别: {LOG_LEVEL}")
    _log.debug(f"调试模式: 已启用")