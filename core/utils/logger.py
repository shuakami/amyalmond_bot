"""
AmyAlmond Project - core/utils/logger.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/18 11:35
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.5 (Beta_820003)

logger.py 用于日志记录
"""

import botpy.logging
import logging
import os


def get_logger():
    logger = botpy.logging.get_logger()

    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # 默认配置
    log_level = "INFO"
    debug_mode = False
    log_file = None

    # 尝试读取配置文件
    try:
        import yaml
        config_path = os.path.join(project_root, "configs", "config.yaml")
        # print(f"读取配置文件: {config_path}")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            log_level = config.get("log_level", "INFO").upper()
            # print(f"读取到的日志级别: {log_level}")
            # print(f"读取到的debug模式: {debug_mode}")
            debug_mode = config.get("debug", False)
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "bot.log")
    except Exception as e:
        logger.warning(f"无法读取配置文件，使用默认日志配置: {e}")

    # 设置日志级别
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # 如果debug模式开启，设置为DEBUG级别
    if debug_mode:
        logger.setLevel(logging.DEBUG)

    # 添加文件处理器
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"无法添加文件处理器: {e}")

    logger.debug("日志系统初始化完成")
    return logger


# 全局logger对象
_log = get_logger()
