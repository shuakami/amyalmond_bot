"""
AmyAlmond Plugins - core/plugins/tools/plugin_utils.py
插件工具模块
"""
import logging
import os
import json
from logging.handlers import RotatingFileHandler

PLUGIN_LOGGER_NAME = "AmyAlmond Plugins"

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
LOG_FILE = os.path.join(LOG_DIR, "plugin.log")
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # 保留5个旧日志文件

# 创建日志目录
os.makedirs(LOG_DIR, exist_ok=True)


def get_plugin_logger():
    """
    获取插件专用的 logger 对象，用于记录插件日志信息，并添加前缀 <AmyAlmond Plugins LOG>。

    Returns:
        logging.Logger: 插件专用的 logger 对象。
    """
    logger = logging.getLogger(PLUGIN_LOGGER_NAME)

    if not logger.handlers:
        # 设置日志处理器和格式化器
        handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
        formatter = logging.Formatter('<AAPL> %(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    return logger


def load_plugin_config(plugin_name, filename="config.json"):
    """
    从插件配置目录加载 JSON 格式的配置文件。

    Args:
        plugin_name (str): 插件名称，用于日志记录。
        filename (str, optional): 配置文件名，默认为 "config.json"。

    Returns:
        dict: 加载的配置信息，如果文件不存在或加载失败，则返回空字典 {}。
    """

    # 获取插件配置目录的绝对路径
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "plugins", "config"))

    # 拼接配置文件的绝对路径
    config_path = os.path.join(config_dir, filename)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            get_plugin_logger().debug(f"插件 {plugin_name} 请求了配置文件: {config_path}")
            get_plugin_logger().info(f"成功加载了来自 {config_path} 的配置文件")
            get_plugin_logger().debug(f"配置内容: {config}")
            return config
    except FileNotFoundError:
        get_plugin_logger().error(f"未找到配置文件: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        get_plugin_logger().error(f"无法加载来自 {config_path} 的配置文件: {e}")
        return {}
