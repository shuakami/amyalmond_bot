"""
AmyAlmond Project - config.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

config.py - 配置文件读取与验证
"""
import os
from botpy.ext.cog_yaml import read
from core.utils.logger import get_logger
import subprocess
import time
from ruamel.yaml import YAML

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
logger.info("")
logger.info(">>> CONFIG LOADING...")
if os.path.exists(CONFIG_FILE):
    loaded_config = read(CONFIG_FILE)
    if loaded_config:
        test_config.update(loaded_config)
        logger.info("   ↳ 配置文件加载成功")
    else:
        logger.critical("<ERROR> 配置文件为空")
        logger.critical(f"   ↳ 路径: {CONFIG_FILE}")
        logger.critical("   ↳ 请检查配置文件是否正确填写，并确保其格式为 YAML")
        exit(1)
else:
    logger.critical("<ERROR> 找不到配置文件")
    logger.critical(f"   ↳ 路径: {CONFIG_FILE}")
    logger.critical(f"   ↳ 请确保在 {CONFIG_DIR} 目录下存在 config.yaml 文件")
    exit(1)

# 配置参数
MAX_CONTEXT_TOKENS = test_config.get("max_context_tokens", None)
ELASTICSEARCH_QUERY_TERMS = test_config.get("elasticsearch_query_terms", None)

# 检查是否需要自动调优
if MAX_CONTEXT_TOKENS is None or ELASTICSEARCH_QUERY_TERMS is None:
    logger.warning("<WARNING> 未找到必要的配置参数，正在调用自动调优程序...")
    try:
        start_time = time.time()
        # 调用 auto_tune.py 自动调优
        result = subprocess.run(["python", "core/db/auto_tune.py"], timeout=60)
        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            logger.info("<INFO> 自动调优完成")
            logger.info(f"   ↳ 耗时: {elapsed_time:.2f} 秒")
            # 重新读取配置文件
            if os.path.exists(CONFIG_FILE):
                loaded_config = read(CONFIG_FILE)
                if loaded_config:
                    test_config.update(loaded_config)
                    MAX_CONTEXT_TOKENS = test_config.get("max_context_tokens", 2400)  # 默认值 2400
                    ELASTICSEARCH_QUERY_TERMS = test_config.get("elasticsearch_query_terms", 16)  # 默认值 16
                else:
                    logger.critical("<ERROR> 配置文件读取失败，使用默认值")
                    MAX_CONTEXT_TOKENS = 2400
                    ELASTICSEARCH_QUERY_TERMS = 8
        else:
            logger.error("<ERROR> 自动调优程序执行失败，使用默认值")
            MAX_CONTEXT_TOKENS = 2400
            ELASTICSEARCH_QUERY_TERMS = 16
    except subprocess.TimeoutExpired:
        logger.error("<ERROR> 自动调优超时，使用默认值")
        MAX_CONTEXT_TOKENS = 2400
        ELASTICSEARCH_QUERY_TERMS = 16



# 其他配置
REQUEST_LIMIT_TIME_FRAME = test_config.get("request_limit_time_frame", 10)
REQUEST_LIMIT_COUNT = test_config.get("request_limit_count", 7)
GLOBAL_RATE_LIMIT = test_config.get("global_rate_limit", 75)

MEMORY_THRESHOLD = 150
FORGET_THRESHOLD = 5


MEMORY_BATCH_SIZE = test_config.get("memory_batch_size", 1)
REQUEST_TIMEOUT= test_config.get("request_timeout", 7)

MONGODB_URI = test_config.get("mongodb_url", "")
MONGODB_USERNAME = test_config.get("mongodb_username", "")
MONGODB_PASSWORD = test_config.get("mongodb_password", "")

ELASTICSEARCH_URL = test_config.get("elasticsearch_url", "")
ELASTICSEARCH_USERNAME = test_config.get("elasticsearch_username", "")
ELASTICSEARCH_PASSWORD = test_config.get("elasticsearch_password", "")

OPENAI_SECRET = test_config.get("openai_secret", "")
OPENAI_MODEL = test_config.get("openai_model", "gpt-4o-mini")
OPENAI_API_URL = test_config.get("openai_api_url", "https://api.openai-hk.com/v1/chat/completions")

ADMIN_ID = test_config.get("admin_id", "")

# KEEP_ALIVE 配置
OPENAI_KEEP_ALIVE = test_config.get("openai_keep_alive", True)
UPDATE_KEEP_ALIVE = test_config.get("update_keep_alive", True)

# 日志配置
LOG_LEVEL = test_config.get("log_level", "INFO").upper()
DEBUG_MODE = test_config.get("debug", False)

# 验证关键配置
if not MONGODB_USERNAME:
    logger.warning("<WARNING> MongoDB 用户名缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")
if not MONGODB_PASSWORD:
    logger.warning("<WARNING> MongoDB 密码缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")
if not MONGODB_URI:
    logger.warning("<WARNING> MongoDB URI 缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")
if not OPENAI_SECRET:
    logger.warning("<WARNING> OpenAI API 密钥缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")
if not OPENAI_MODEL:
    logger.warning("<WARNING> OpenAI 模型缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")
if not OPENAI_API_URL:
    logger.warning("<WARNING> OpenAI API URL 缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")
if not ADMIN_ID:
    logger.warning("<WARNING> 管理员 ID 缺失")
    logger.warning(f"   ↳ 请检查配置文件: {CONFIG_FILE}")

def _write_config():
    """将配置写入 config.yaml 文件，保留原始格式"""
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        yaml_data = yaml.load(f)

    # 更新配置项的值
    for key, value in test_config.items():
        if key in yaml_data:
            yaml_data[key] = value
        else:
            yaml_data[key] = value

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f)

def get_all_config():
    """获取所有配置"""
    return test_config

def add_config(key, value):
    """添加新的配置项"""
    if key in test_config:
        logger.warning(f"<WARNING> 配置项 '{key}' 已存在，无法添加")
        return False
    test_config[key] = value
    _write_config()
    logger.info(f"<INFO> 配置项 '{key}' 添加成功")
    return True

def update_config(key, value):
    """修改或添加配置项"""
    test_config[key] = value  # 如果 key 不存在，则添加新的配置项
    _write_config()
    logger.info(f"<INFO> 配置项 '{key}' 修改成功")
    return True

def delete_config(key):
    """删除配置项"""
    if key not in test_config:
        logger.warning(f"<WARNING> 配置项 '{key}' 不存在，无法删除")
        return False
    del test_config[key]
    _write_config()
    logger.info(f"<INFO> 配置项 '{key}' 删除成功")
    return True



# DEBUG情况下
if DEBUG_MODE:
    if OPENAI_SECRET and OPENAI_MODEL and OPENAI_API_URL and ADMIN_ID:
        masked_secret = '*' * (len(OPENAI_SECRET) - 4) + OPENAI_SECRET[-4:]
        masked_admin_id = '*' * (len(ADMIN_ID) - 4) + ADMIN_ID[-4:]
        logger.info("")
        logger.info("<CONFIG> OpenAI API Configuration")
        logger.info(f"   ↳ API Key   : {masked_secret}")
        logger.info(f"   ↳ Model     : {OPENAI_MODEL}")
        logger.info(f"   ↳ API URL   : {OPENAI_API_URL}")
        logger.info(f"   ↳ Admin ID  : {masked_admin_id}")
        logger.info(f"   ↳ Log Level : {LOG_LEVEL}")
        logger.info(f"   ↳ Debug Mode: {'Enabled' if DEBUG_MODE else 'Disabled'}")

