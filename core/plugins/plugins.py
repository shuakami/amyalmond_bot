"""
AmyAlmond Plugins - core/plugins/plugins.py
Plugins核心模块
"""
import importlib
import inspect
import os
import traceback

from core.plugins import Plugin
from core.utils.logger import get_logger

# 获取 logger 对象
logger = get_logger()


def load_plugins(bot_client):
    """
    加载插件

    Args:
        bot_client (MyClient): BotClient 实例
    """
    plugins = []
    plugins_dir = os.path.join("core", "plugins")

    if not os.path.isdir(plugins_dir):
        logger.error(f"<ERROR> 插件目录不存在:")
        logger.error(f"   ↳ 目录路径: '{plugins_dir}'")
        return plugins

    logger.info(f"<AAPL> LOADING >>>>>>")
    logger.info(f"   ↳ 插件目录: '{plugins_dir}'")

    for plugin_folder in os.listdir(plugins_dir):
        plugin_dir = os.path.join(plugins_dir, plugin_folder)
        if os.path.isdir(plugin_dir):
            plugin_name = plugin_folder  # 插件名与文件夹名相同
            plugin_file = os.path.join(plugin_dir, f"{plugin_name}.py")
            amy_file = os.path.join(plugin_dir, f"{plugin_name}.amy")

            if os.path.exists(plugin_file) and os.path.exists(amy_file):
                full_module_name = f"core.plugins.{plugin_name}.{plugin_name}"
                try:
                    logger.info(f"<LOAD> 尝试加载插件:")
                    logger.info(f"   ↳ 插件名称: {full_module_name}")
                    module = importlib.import_module(full_module_name)

                    # 输出模块中的所有类，方便调试
                    logger.debug("<DEBUG> 模块中的类信息:")
                    logger.debug(f"   ↳ 模块: {full_module_name}")
                    logger.debug(f"   ↳ 类: {[name for name, obj in inspect.getmembers(module, inspect.isclass)]}")

                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                            try:
                                plugin = obj(bot_client)
                                plugins.append(plugin)
                                logger.info(f"<PLUGIN> 成功加载插件:")
                                logger.info(f"   ↳ 类名: {name}")
                            except Exception as e:
                                logger.error(f"<ERROR> 初始化插件时发生错误:")
                                logger.error(f"   ↳ 插件名称: {full_module_name}")
                                logger.error(f"   ↳ 错误详情: {e}")
                                logger.debug(traceback.format_exc())

                except (ImportError, ModuleNotFoundError) as e:
                    logger.error(f"<ERROR> 导入插件失败:")
                    logger.error(f"   ↳ 插件名称: {full_module_name}")
                    logger.error(f"   ↳ 错误详情: {e}")
                    logger.debug(traceback.format_exc())
                except Exception as e:
                    logger.error(f"<ERROR> 加载插件时发生错误:")
                    logger.error(f"   ↳ 插件名称: {full_module_name}")
                    logger.error(f"   ↳ 错误详情: {e}")
                    logger.debug(traceback.format_exc())

    logger.info(f"<LOAD> 插件加载完成:")
    logger.info(f"   ↳ 总插件数量: {len(plugins)}")
    return plugins
