"""
AmyAlmond Project - core/utils/logger.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.0 (Pre_827001)

logger.py 用于日志记录
"""

import botpy.logging
import logging
import os
from logging.handlers import RotatingFileHandler
import gzip
import shutil


class GZipRotator:
    """自定义日志文件压缩器，将旧日志文件压缩为.gz格式"""

    def __call__(self, source, dest):
        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)


def get_logger():
    logger = botpy.logging.get_logger()

    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # 默认配置
    log_level = "INFO"
    debug_mode = False
    log_file = None
    max_log_size = 10 * 1024 * 1024  # 10 MB
    backup_count = 5  # 保留5个旧日志文件

    # 尝试读取配置文件
    try:
        import yaml
        config_path = os.path.join(project_root, "configs", "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            log_level = config.get("log_level", "INFO").upper()
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
            # 使用RotatingFileHandler来自动滚动日志文件
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_log_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

            # 设置压缩器，用于将旧日志文件压缩为.gz
            file_handler.rotator = GZipRotator()

        except Exception as e:
            logger.error(f"无法添加文件处理器: {e}")

    logger.debug("日志系统初始化完成")
    return logger


# 全局logger对象
_log = get_logger()
