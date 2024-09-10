# core/plugins/add_hi_plugin/add_hi_plugin.py

from core.plugins import Plugin
from core.utils.logger import get_logger

logger = get_logger()

class AddHiPlugin(Plugin):
    def __init__(self, bot_client):
        super().__init__(bot_client)
        logger.info("<PLUGIN INIT> AddHiPlugin 初始化成功")

    async def on_message(self, message, reply_message):
        try:
            logger.debug("<PLUGIN EXEC> AddHiPlugin 被调用:")
            logger.debug(f"   ↳ 当前回复消息: {reply_message}")

            reply_message = f"{reply_message} hi"
            logger.info("<REPLY ADDED> 添加 'hi':")
            logger.info(f"   ↳ 内容: {reply_message}")

            logger.debug("<FINAL REPLY> 最终回复消息:")
            logger.debug(f"   ↳ 内容: {reply_message}")
            return reply_message

        except Exception as e:
            logger.error("<ERROR> 🚨AddHiPlugin 执行过程中发生错误:")
            logger.error(f"   ↳ 错误详情: {e}", exc_info=True)
            return reply_message
