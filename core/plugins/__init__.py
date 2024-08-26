"""
AmyAlmond Plugins - core/plugins/__init__.py
Plugins核心定义
"""


class Plugin:
    """
    插件基类，定义了插件需要实现的方法
    """

    def __init__(self, bot_client, name=None):
        """
        初始化插件

        参数:
            bot_client (BotClient): 机器人客户端实例
            name (str): 插件名称
        """
        self.bot_client = bot_client
        self.name = name if name else self.__class__.__name__

    async def on_message(self, message, reply_content):
        """
        当收到消息时调用的方法

        参数:
            message (Message): 收到的消息对象
            reply_content (str): 待处理的回复内容
        """
        return reply_content

    async def on_ready(self):
        """
        当机器人启动完成时调用的方法
        """
        pass