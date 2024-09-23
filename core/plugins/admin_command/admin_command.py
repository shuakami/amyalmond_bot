from core.plugins import Plugin
from core.utils.logger import get_logger

logger = get_logger()


class AdminCommandPlugin(Plugin):
    """
    处理管理员指令的插件
    """

    def __init__(self, bot_client):
        super().__init__(bot_client)
        self.name = "AdminCommandPlugin"

    async def before_llm_message(self, message, reply_message, **kwargs):
        """
        在 LLM 处理消息之前处理管理员指令
        """
        user_id = message.author.member_openid
        cleaned_content = message.content.strip().lower()
        group_id = message.group_openid

        # 判断是否为管理员命令
        if user_id == self.bot_client.ADMIN_ID:
            if cleaned_content == "restart":
                logger.info("<ADMIN> 收到管理员restart命令")
                await self.bot_client.restart_bot(group_id, message.id)
                return False  # 阻止消息进入 LLM 处理
            elif cleaned_content == "reload":
                logger.info("<ADMIN> 收到管理员reload命令")
                await self.bot_client.hot_reload(group_id, message.id)
                return False  # 阻止消息进入 LLM 处理

        return True  # 继续进入 LLM 处理
