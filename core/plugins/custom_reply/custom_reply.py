# core/plugins/custom_reply.py
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
            logger.error("Failed to load custom replies. Plugin will not function correctly.")

    async def on_message(self, message, reply_message):
        try:
            logger.debug(f"CustomReplyPlugin called with reply_message: {reply_message}")
            if self.custom_replies:
                custom_reply = random.choice(self.custom_replies)
                reply_message = f"{reply_message}\n---\n{custom_reply}"
                logger.info(f"Custom reply added: {custom_reply}")
            else:
                logger.warning("No custom replies loaded. Skipping plugin execution.")
            logger.debug(f"Final reply_message: {reply_message}")
            return reply_message
        except Exception as e:
            logger.error(f"Error in CustomReplyPlugin: {e}", exc_info=True)
            return reply_message
