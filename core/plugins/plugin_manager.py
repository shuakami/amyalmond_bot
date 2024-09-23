"""
AmyAlmond Plugins - core/plugins/plugin_manager.py
插件管理模块
"""
import os
import zipfile
import shutil
from core.plugins.plugins import load_plugins
from core.utils.logger import get_logger
from core.plugins.event_bus import EventBus
import yaml

logger = get_logger()

class PluginManager:
    def __init__(self, bot_client):
        self.bot_client = bot_client
        self.plugins = {}
        self.load_plugins()
        self.event_bus = EventBus()

    def load_plugins(self):
        """
        加载所有插件并存储它们的实例、路径、配置信息和优先级
        """
        loaded_plugins, plugin_paths, plugin_configs, plugin_priorities = load_plugins(self.bot_client)
        for plugin, path, config, priority in zip(loaded_plugins, plugin_paths, plugin_configs, plugin_priorities):
            plugin_name = plugin.name
            self.plugins[plugin_name] = {
                "instance": plugin,
                "path": path,
                "config": config,
                "priority": priority  # 将插件优先级存储
            }
        logger.info(f"插件已加载，总数: {len(self.plugins)}")

    def register_plugins(self):
        """
        注册启用的插件事件处理方法，并根据插件自身的优先级进行注册。
        """
        for plugin_name, plugin_data in self.plugins.items():
            plugin = plugin_data["instance"]
            priority = plugin_data.get('priority', 0)  # 获取插件优先级，默认为 0

            # 注册 before_llm_message 事件
            if hasattr(plugin, 'before_llm_message'):
                self.event_bus.subscribe("before_llm_message", plugin.before_llm_message, plugin_name, priority)
                logger.info(f"{plugin_name} 订阅了 before_llm_message 事件，优先级为 {priority}")

            # 注册其他插件事件
            self.event_bus.subscribe("on_message", plugin.on_message, plugin_name, priority)
            self.event_bus.subscribe("on_ready", plugin.on_ready, plugin_name, priority)
            self.event_bus.subscribe("before_send_reply", plugin.on_message, plugin_name, priority)

            logger.info(f"插件已注册: {plugin_name}")

    def install_plugin(self, zip_path):
        """
        安装插件，支持上传ZIP文件进行安装
        """
        plugins_dir = os.path.join("core", "plugins")
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("提供的文件不是有效的ZIP文件")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(plugins_dir)
        self.load_plugins()  # 重新加载插件

    def uninstall_plugin(self, plugin_name):
        """
        卸载指定的插件
        """
        if plugin_name in self.plugins:
            # 先从内存中删除插件实例
            plugin_data = self.plugins.pop(plugin_name, None)
            if plugin_data:
                plugin_path = plugin_data["path"]
                if os.path.isdir(plugin_path):
                    shutil.rmtree(plugin_path)
                    logger.info(f"插件已卸载: {plugin_name}")
                    self.load_plugins()  # 重新加载插件
                else:
                    logger.warning(f"插件 {plugin_name} 对应的目录不存在,但已从插件列表中删除")
            else:
                logger.warning(f"插件 {plugin_name} 不存在,无法获取其路径信息")
        else:
            logger.warning(f"插件 {plugin_name} 不存在,无法卸载")

    async def handle_event(self, event_type, **kwargs):
        """
        处理特定事件类型 'on_registration'。

        参数:
            event_type (str): 事件类型
            kwargs (dict): 事件相关参数

        返回:
            bool: 如果有插件处理了事件，返回 True；否则返回 False
        """
        if event_type in self.event_bus.subscribers:
            return await self.event_bus.publish(event_type, **kwargs)
        return False

    def get_plugin_list(self):
        """
        获取当前所有插件的详细信息，包括配置信息
        """
        plugin_list = []
        for name, data in self.plugins.items():
            config = data.get("config", {})
            plugin_list.append({
                "name": name,
                "version": config.get("version", "未知"),
                "author": config.get("author", "未知"),
                "plugin_id": config.get("plugin_id", "无UUID"),
                "description": config.get("description", "无描述"),
                "dependencies": config.get("dependencies", [])
            })
        return plugin_list

    def reload_plugins(self):
        """
         热重载所有插件
         """
        self.plugins.clear()  # 清除已加载的插件
        self.load_plugins()  # 重新加载插件
        self.register_plugins()  # 重新注册插件事件
        logger.info("插件已热重载")
