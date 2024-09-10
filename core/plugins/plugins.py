"""
AmyAlmond Plugins - core/plugins/plugins.py
Plugins核心模块
"""
import importlib
import inspect
import os
import traceback
import yaml

from core.plugins import Plugin
from core.utils.logger import get_logger

# 获取 logger 对象
logger = get_logger()


def load_plugins(bot_client):
    """
    加载插件并返回插件实例、路径和配置信息

    Args:
        bot_client (MyClient): BotClient 实例
    """
    plugins = []
    plugin_paths = []  # 用于存储插件路径
    plugin_configs = []  # 用于存储插件的配置信息
    plugin_priorities = []  # 用于存储插件优先级
    plugins_dir = os.path.join("core", "plugins")

    if not os.path.isdir(plugins_dir):
        logger.error(f"<ERROR> 插件目录不存在: '{plugins_dir}'")
        return plugins, plugin_paths, plugin_configs, plugin_priorities

    logger.info(f"<AAPL> LOADING >>>>>>")
    logger.info(f"   ↳ 插件目录: '{plugins_dir}'")

    for plugin_folder in os.listdir(plugins_dir):
        plugin_dir = os.path.join(plugins_dir, plugin_folder)
        if os.path.isdir(plugin_dir):
            plugin_name = plugin_folder  # 插件名与文件夹名相同
            plugin_file = os.path.join(plugin_dir, f"{plugin_name}.py")
            yaml_file = os.path.join(plugin_dir, f"{plugin_name}.yaml")

            if os.path.exists(plugin_file) and os.path.exists(yaml_file):
                full_module_name = f"core.plugins.{plugin_name}.{plugin_name}"
                try:
                    logger.info(f"<LOAD> 尝试加载插件: {full_module_name}")

                    # 加载 YAML 配置文件
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        plugin_config = yaml.safe_load(f)

                    # 输出插件配置信息，便于调试
                    plugin_id = plugin_config.get('plugin_id', '无UUID')
                    version = plugin_config.get('version', '未知版本')
                    author = plugin_config.get('author', '未知作者')
                    priority = plugin_config.get('priority', 0)  # 从配置中获取优先级，默认为 0
                    logger.debug(f"<PLUGIN CONFIG> 插件ID: {plugin_id}, 版本: {version}, 作者: {author}, 优先级: {priority}")

                    # 动态导入插件模块
                    module = importlib.import_module(full_module_name)

                    # 输出模块中的所有类，方便调试
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                            plugin = obj(bot_client)
                            plugins.append(plugin)
                            plugin_paths.append(plugin_dir)  # 存储插件路径
                            plugin_configs.append(plugin_config)  # 存储插件配置
                            plugin_priorities.append(priority)  # 存储插件优先级
                            logger.info(f"<PLUGIN> 成功加载插件: {name}")

                except Exception as e:
                    logger.error(f"<ERROR> 加载插件时发生错误: {e}")
                    logger.debug(traceback.format_exc())

    logger.info(f"<LOAD> 插件加载完成，总数量: {len(plugins)}")
    return plugins, plugin_paths, plugin_configs, plugin_priorities  # 返回插件实例、路径、配置信息和优先级
