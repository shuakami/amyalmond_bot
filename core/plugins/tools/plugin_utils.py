"""
AmyAlmond Plugins - core/plugins/tools/plugin_utils.py
插件工具模块
"""
import os
import json
from core.utils.logger import get_logger

PLUGIN_LOGGER_NAME = "AmyAlmond Plugins"


def get_plugin_logger():
    """
    获取插件专用的 logger 对象，用于记录插件日志信息。

    Args:
        name (str): 插件名称。

    Returns:
        logging.Logger: 插件专用的 logger 对象。
    """
    logger = get_logger()
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
            get_plugin_logger().debug(f"Plugin {plugin_name} requested config file: {config_path}")
            get_plugin_logger().info(f"Successfully loaded config file from {config_path}")
            get_plugin_logger().debug(f"Config content: {config}")
            return config
    except FileNotFoundError:
        get_plugin_logger().error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        get_plugin_logger().error(f"Failed to load config file from {config_path}: {e}")
        return {}
