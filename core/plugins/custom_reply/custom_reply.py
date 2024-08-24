"""
AmyAlmond Plugins - core/plugins/custom_reply/custom_reply.py
"""
import random
from core.plugins import Plugin
from core.plugins.tools.plugin_utils import load_plugin_config
from core.utils.logger import get_logger

logger = get_logger()


class CustomReplyPlugin(Plugin):
    def __init__(self, bot_client):
        super().__init__(bot_client)
        self.custom_replies = load_plugin_config(__name__, "custom_replies.json")
        if not self.custom_replies:
            logger.error(f"Failed to load custom replies. Plugin will not function correctly.")

    async def on_message(self, message, reply_message):
        logger.debug(f"CustomReplyPlugin called with reply_message: {reply_message}")

        # 定义插件操作标识符
        plugin_placeholder = "<!-- Plugin Content -->"

        # 直接使用随机回复替换占位符
        if self.custom_replies:
            reply = random.choice(self.custom_replies)
            reply_message = reply_message.replace(plugin_placeholder, reply)
            logger.debug(f"Custom reply added: {reply}")
        else:
            logger.warning(f"No custom replies loaded. Skipping plugin execution.")

        logger.debug(f"Final reply_message: {reply_message}")
        return reply_message
