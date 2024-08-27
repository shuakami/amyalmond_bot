# core/plugins/plugin_manager.py
import os
from core.plugins import Plugin
from core.plugins.plugins import load_plugins
from core.utils.logger import get_logger
from core.plugins.event_bus import EventBus

logger = get_logger()

class PluginManager:
    def __init__(self, bot_client):
        self.bot_client = bot_client
        self.plugins = load_plugins(bot_client)  # 加载插件
        self.event_bus = EventBus()  # 初始化事件总线

    def register_plugins(self):
        """
        注册插件的事件处理方法
        """
        for plugin in self.plugins:
            self.event_bus.subscribe("on_message", plugin.on_message)
            self.event_bus.subscribe("on_ready", plugin.on_ready)
            self.event_bus.subscribe("before_send_reply", plugin.on_message)  # 添加这行
            logger.info(f"已注册插件: {plugin.name}")

    async def process_message(self, message, reply_content):
        """
        处理消息并通过事件总线调用所有已启用的插件

        参数:
            message (botpy.Message): 接收到的原始消息对象。
            reply_content (str): 待处理的回复内容字符串。

        返回:
            str: 处理后的回复内容字符串。
        """
        await self.event_bus.publish("on_message", message, reply_content)

    async def on_ready(self):
        """
        当机器人准备好时调用，通过事件总线触发所有插件的 on_ready 方法
        """
        await self.event_bus.publish("on_ready")
