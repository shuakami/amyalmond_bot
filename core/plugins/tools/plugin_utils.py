"""
AmyAlmond Plugins - core/plugins/tools/plugin_utils.py
插件工具模块
"""

import os
import json
from core.utils.logger import get_logger

logger = get_logger()

PLUGIN_LOGGER_NAME = "AmyAlmond Plugins"


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
            logger.debug(f"<APPL> 插件 {plugin_name} 请求了配置文件: {config_path}")
            logger.info(f"<APPL> 成功加载了来自 {config_path} 的配置文件")
            logger.debug(f"<APPL> 配置内容: {config}")
            return config
    except FileNotFoundError:
        logger.error(f"<APPL> 未找到配置文件: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"<APPL> 无法加载来自 {config_path} 的配置文件: {e}")
        return {}
