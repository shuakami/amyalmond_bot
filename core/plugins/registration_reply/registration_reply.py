from core.plugins import Plugin
from core.plugins.tools.plugin_utils import load_plugin_config
from core.utils.logger import get_logger
from core.utils.user_management import add_new_user

logger = get_logger()


class RegistrationReplyPlugin(Plugin):
    def __init__(self, bot_client):
        super().__init__(bot_client)
        self.name = "RegistrationReplyPlugin"
        self.load_responses()

    def load_responses(self):
        """
        使用插件工具集加载插件自定义回复信息
        """
        self.responses = load_plugin_config(__name__, 'registration_replies.json')
        if self.responses:
            logger.info(f"加载自定义回复信息成功: {self.responses}")  # 添加日志确认加载成功
        else:
            self.responses = {}
            logger.warning("未能加载自定义回复信息，使用默认回复内容")

    async def on_registration(self, group_id, user_id, cleaned_content, msg_id):
        """
        自定义用户注册消息处理逻辑

        参数:
            group_id (str): 群组的唯一标识符
            user_id (str): 用户的唯一标识符
            cleaned_content (str): 用户发送的消息内容
            msg_id (str): 消息的唯一标识符
        """
        # 使用插件的自定义回复逻辑
        if user_id not in self.bot_client.pending_users:
            response = self.responses.get("initial_prompt",
                                          "请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~")
            await self.bot_client.api.post_group_message(group_openid=group_id, content=response, msg_id=msg_id)
            self.bot_client.pending_users[user_id] = True
            return True  # 确保返回 True 表示插件已经处理事件
        else:
            if cleaned_content.strip():
                # 添加用户存储逻辑
                if await add_new_user(user_id, cleaned_content.strip()):
                    response = self.responses.get("success_prompt", "原来是{}吗 ... 我已经记住你了~").format(
                        cleaned_content)
                    await self.bot_client.api.post_group_message(group_openid=group_id, content=response, msg_id=msg_id)
                else:
                    response = self.responses.get("error_prompt", "存储用户信息时发生错误，请稍后再试。")
                    await self.bot_client.api.post_group_message(group_openid=group_id, content=response, msg_id=msg_id)
            else:
                response = self.responses.get("repeat_prompt",
                                              "请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~")
                await self.bot_client.api.post_group_message(group_openid=group_id, content=response, msg_id=msg_id)

            self.bot_client.pending_users.pop(user_id, None)  # 移除用户以结束注册流程
            return True  # 同样返回 True 表示事件已处理
