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
            logger.error("<ERROR> 🚨无法加载自定义回复，插件将无法正常工作。")
        else:
            logger.info("<PLUGIN INIT> CustomReplyPlugin 初始化成功")
            logger.debug(f"   ↳ 加载的自定义回复: {self.custom_replies}")

    async def on_message(self, message, reply_message):
        try:
            logger.debug("<PLUGIN EXEC> CustomReplyPlugin 被调用:")
            logger.debug(f"   ↳ 当前回复消息: {reply_message}")

            if self.custom_replies:
                custom_reply = random.choice(self.custom_replies)
                if reply_message:
                    reply_message = f"{reply_message}\n---\n{custom_reply}"
                else:
                    reply_message = custom_reply

                logger.info("<REPLY ADDED> 添加自定义回复:")
                logger.info(f"   ↳ 内容: {custom_reply}")
            else:
                logger.warning("<PLUGIN SKIP> 未加载自定义回复，跳过插件执行。")

            logger.debug("<FINAL REPLY> 最终回复消息:")
            logger.debug(f"   ↳ 内容: {reply_message}")
            return reply_message

        except Exception as e:
            logger.error("<ERROR> 🚨CustomReplyPlugin 执行过程中发生错误:")
            logger.error(f"   ↳ 错误详情: {e}", exc_info=True)
            return reply_message
