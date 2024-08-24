"""
AmyAlmond Project - config.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/19 20:13
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.2.0 (Beta_824001)

config.py - 配置文件读取与验证
"""
import os
from botpy.ext.cog_yaml import read
from core.utils.logger import get_logger

# 获取 logger 对象
logger = get_logger()

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
FAISS_INDEX_PATH = "./data/faiss_index.bin"

# 读取配置文件
test_config = {}
if os.path.exists(CONFIG_FILE):
    loaded_config = read(CONFIG_FILE)
    if loaded_config:
        test_config.update(loaded_config)
    else:
        print(f"")
        logger.critical(f"配置文件为空: {CONFIG_FILE}")
        logger.critical(f"请检查配置文件是否正确填写，并确保其格式为 YAML")
        exit(1)
else:
    print(f"")
    logger.critical(f"找不到配置文件: {CONFIG_FILE}")
    logger.critical(f"请确保在 {CONFIG_DIR} 目录下存在 config.yaml 文件")
    exit(1)

# 配置参数
MAX_CONTEXT_MESSAGES = 6
DIMENSION = 256  # 默认向量维度

MAX_CONTEXT_TOKENS = 1400
MEMORY_THRESHOLD = 150

MONGODB_URI = test_config.get("mongodb_url", "")
MONGODB_USERNAME = test_config.get("mongodb_username", "")
MONGODB_PASSWORD = test_config.get("mongodb_password", "")

ELASTICSEARCH_URL = test_config.get("elasticsearch_url", "")
ELASTICSEARCH_USERNAME = test_config.get("elasticsearch_username", "")
ELASTICSEARCH_PASSWORD = test_config.get("elasticsearch_password", "")

OPENAI_SECRET = test_config.get("openai_secret", "")
OPENAI_MODEL = test_config.get("openai_model", "gpt-4o-mini")
OPENAI_API_URL = test_config.get("openai_api_url", "https://api.openai-hk.com/v1/chat/completions")

# TEA_URL = test_config.get("tea_url", "")
# TEA_SECRET = test_config.get("tea_secret", "")
# TEA_MODEL = test_config.get("tea_model", "gpt-4o-mini")

ADMIN_ID = test_config.get("admin_id", "")

# KEEP_ALIVE 配置
OPENAI_KEEP_ALIVE = test_config.get("openai_keep_alive", True)
UPDATE_KEEP_ALIVE = test_config.get("update_keep_alive", True)

# 日志配置
LOG_LEVEL = test_config.get("log_level", "INFO").upper()
DEBUG_MODE = test_config.get("debug", False)

# 验证关键配置
if not MONGODB_USERNAME:
    logger.warning("MongoDB 用户名缺失,请检查 config.yaml 文件")
if not MONGODB_PASSWORD:
    logger.warning("MongoDB 密码缺失,请检查 config.yaml 文件")
if not MONGODB_URI:
    logger.warning("MongoDB URI 缺失,请检查 config.yaml 文件")
if not OPENAI_SECRET:
    logger.warning("OpenAI API 密钥缺失,请检查 config.yaml 文件")
if not OPENAI_MODEL:
    logger.warning("OpenAI 模型缺失,请检查 config.yaml 文件")
if not OPENAI_API_URL:
    logger.warning("OpenAI API URL 缺失,请检查 config.yaml 文件")
if not ADMIN_ID:
    logger.warning("管理员 ID 缺失,请检查 config.yaml 文件")

# DEBUG情况下
if DEBUG_MODE:
    if OPENAI_SECRET and OPENAI_MODEL and OPENAI_API_URL and ADMIN_ID:
        masked_secret = '*' * (len(OPENAI_SECRET) - 4) + OPENAI_SECRET[-4:]
        masked_admin_id = '*' * (len(ADMIN_ID) - 4) + ADMIN_ID[-4:]
        print("")
        logger.debug(f"OpenAI API 密钥: {masked_secret}")
        logger.debug(f"OpenAI 模型: {OPENAI_MODEL}")
        logger.debug(f"OpenAI API URL: {OPENAI_API_URL}")
        logger.debug(f"管理员 ID: {masked_admin_id}")
    logger.debug(f"日志级别: {LOG_LEVEL}")
    logger.debug(f"调试模式: 已启用")
