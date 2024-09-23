"""
AmyAlmond Project - core/bot/bot_client.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei

Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

bot_client.py 包含 AmyAlmond 机器人的主要客户端类，链接其他模块进行处理。
"""
import asyncio
import random
import subprocess
import sys
import watchdog.observers
import botpy
from botpy.message import GroupMessage

from core.plugins.plugin_manager import PluginManager
# user_management.py模块 - <用户管理模块化文件>
from core.utils.user_management import load_user_names
# utils.py模块 - <工具模块化文件>
from core.utils.utils import load_system_prompt
# config.py模块 - <配置管理模块化文件>
from config import SYSTEM_PROMPT_FILE, test_config
# file_handler.py模块 - <文件处理模块化文件>
from core.utils.file_handler import ConfigFileHandler
# logger.py模块 - <日志记录模块>
from core.utils.logger import get_logger
# message_handler.py模块 - <消息处理模块化文件>
from core.bot.message_handler import MessageHandler
# memory_manager.py模块 - <内存管理模块化文件>
from core.memory.memory_manager import MemoryManager
# keep_alive.py模块 - <Keep-Alive机制模块化文件>
from core.keep_alive import keep_alive
# llm_client.py模块 - <LLM客户端模块化文件>
from core.llm.llm_factory import LLMFactory

_log = get_logger()


class MyClient(botpy.Client):
    """
    AmyAlmond 项目的主要客户端类,继承自 botpy.Client
    处理机器人的各种事件和请求
    """

    def __init__(self, *args, **kwargs):
        """
        初始化客户端

        初始化待处理用户列表、加载系统提示、设置内存管理器和消息处理器
        读取配置并验证必要的配置项是否设置
        初始化文件系统观察器以监听配置文件变化
        """
        super().__init__(*args, **kwargs)
        # 初始化插件管理器
        self.plugin_manager = PluginManager(self)

        # 初始化 LLM 客户端
        llm_factory = LLMFactory()
        self.llm_client = llm_factory.create_llm_client()

        # 加载插件
        self.plugin_manager.register_plugins()

        self.pending_users = {}
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        self.memory_manager = MemoryManager()
        self.message_handler = MessageHandler(self, self.memory_manager)

        # 读取配置
        self.openai_secret = test_config.get("openai_secret", "")
        self.openai_model = test_config.get("openai_model", "gpt-4o-mini")
        self.openai_api_url = test_config.get("openai_api_url", "https://api.openai-hk.com/v1/chat/completions")
        self.ADMIN_ID = test_config.get("admin_id", "")

        if not self.openai_secret:
            _log.critical("<ERROR> OpenAI API 密钥缺失，请检查 config.yaml 文件")
            raise ValueError("OpenAI API key is missing in config.yaml")
        if not self.openai_model:
            _log.critical("<ERROR> OpenAI 模型缺失，请检查 config.yaml 文件")
            raise ValueError("OpenAI model is missing in config.yaml")
        if not self.openai_api_url:
            _log.critical("<ERROR> OpenAI API URL 缺失，请检查 config.yaml 文件")
            raise ValueError("OpenAI API URL is missing in config.yaml")
        if not self.ADMIN_ID:
            _log.critical("<ERROR> 管理员 ID 缺失，请检查 config.yaml 文件")
            raise ValueError("Admin ID is missing in config.yaml")


        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

        # 设置文件监视器
        self.observer = watchdog.observers.Observer()
        event_handler = ConfigFileHandler(self)
        self.observer.schedule(event_handler, path='.', recursive=False)
        self.observer.start()

    async def on_message(self, message: botpy.message):
        """
        当收到消息时调用

        Args:
            message (botpy.Message): 收到的消息对象
        """
        # 通过事件总线发布 on_message 事件，让所有订阅的插件处理该消息
        await self.plugin_manager.event_bus.publish("on_message", message)

    def load_system_prompt(self):
        """
        加载机器人SystemPrompt
        """
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        _log.info(f">>> SYSTEM PROMPT LOADED")
        _log.info(f"   ↳ Prompt count: {len(self.system_prompt)}")

    def reload_system_prompt(self):
        """
        重新加载机器人SystemPrompt
        """
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        _log.info(">>> SYSTEM PROMPT RELOADED")

    async def on_ready(self):
        """
        当机器人准备好时调用
        """
        _log.info(f">>> ROBOT 「{self.robot.name}」 IS READY!")
        load_user_names()

        # 加载记忆
        _log.info(">>> MEMORY LOADING...")
        await self.memory_manager.load_memory()
        _log.info("   ↳ 记忆加载完成")

        # 启动 Keep-Alive 任务
        await asyncio.create_task(keep_alive(self.openai_api_url, self.openai_secret))

        # 通知插件准备就绪
        await self.plugin_manager.on_ready()

    async def on_group_at_message_create(self, message: GroupMessage):
        """
        当接收到群组中提及机器人的消息时调用

        参数:
            message (GroupMessage): 接收到的消息对象
        """
        await self.message_handler.handle_group_message(message)

    async def get_gpt_response(self, context, user_input):
        """
        根据给定的上下文和用户输入,从 LLM 模型获取回复
        """
        return await self.llm_client.get_response(context, user_input, self.system_prompt)

    async def restart_bot(self, group_id, msg_id):
        """
        重启机器人

        参数:
            group_id (str): 羡组ID
            msg_id (str): 消息ID
        """
        await self.api.post_group_message(
            group_openid=group_id,
            content=f"子网重启，请稍后... ({random.randint(1000, 9999)})",
            msg_id=msg_id
        )

        _log.info(">>> RESTARTING BOT...")

        self.observer.stop()
        self.observer.join()

        _log.info(">>> BOT RESTART COMMAND RECEIVED, SHUTTING DOWN...")

        python = sys.executable
        subprocess.Popen([python] + sys.argv)

        sys.exit()

    async def hot_reload(self, group_id, msg_id):
        """
        热重载系统

        参数:
            group_id (str): 群组ID
            msg_id (str): 消息ID
        """
        _log.info(">>> HOT RELOAD INITIATED...")
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        load_user_names()
        _log.info("   ↳ 热重载完成，系统已更新")
        await self.api.post_group_message(
            group_openid=group_id,
            content="热重载完成，系统已更新。",
            msg_id=msg_id
        )

