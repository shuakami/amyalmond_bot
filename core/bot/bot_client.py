"""
AmyAlmond Project - bot_client.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.2 (Stable_818005)

bot_client.py 包含 AmyAlmond 机器人的主要客户端类，链接其他模块进行处理。
"""
import asyncio
import random
import subprocess
import sys
import time
import watchdog.observers
import requests
import botpy
from botpy.message import GroupMessage

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
            raise ValueError("OpenAI API key is missing in config.yaml")
        if not self.openai_model:
            raise ValueError("OpenAI model is missing in config.yaml")
        if not self.openai_api_url:
            raise ValueError("OpenAI API URL is missing in config.yaml")
        if not self.ADMIN_ID:
            raise ValueError("Admin ID is missing in config.yaml")

        # 初始化 last_request_time 和 last_request_content
        self.last_request_time = 0
        self.last_request_content = None

        # 设置文件监视器
        self.observer = watchdog.observers.Observer()
        event_handler = ConfigFileHandler(self)
        self.observer.schedule(event_handler, path='.', recursive=False)
        self.observer.start()

    def load_system_prompt(self):
        """
        加载机器人SystemPrompt
        """
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        _log.info(f"SystemPromptStatus: {len(self.system_prompt)}")

    def reload_system_prompt(self):
        """
        重新加载机器人SystemPrompt
        """
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        _log.info("System prompt reloaded")

    async def on_ready(self):
        """
        当机器人准备好时调用
        """
        _log.info(f"Robot 「{self.robot.name}」 is ready!")
        load_user_names()
        await self.memory_manager.load_memory()

        # 启动 Keep-Alive 任务
        await asyncio.create_task(keep_alive(self.openai_api_url, self.openai_secret))

    async def on_group_at_message_create(self, message: GroupMessage):
        """
        当接收到群组中提及机器人的消息时调用

        参数:
            message (GroupMessage): 接收到的消息对象
        """
        await self.message_handler.handle_group_message(message)

    async def get_gpt_response(self, context, user_input):
        """
        根据给定的上下文和用户输入,从 GPT 模型获取回复

        参数:
            context (list): 对话上下文,包含之前的对话内容
            user_input (str): 用户的输入内容

        返回:
            str: GPT 模型生成的回复内容

        异常:
            requests.exceptions.RequestException: 当请求 OpenAI API 出现问题时引发
        """
        # 检查是否为重复请求
        if self.last_request_time - self.last_request_time < 0.6 and user_input == self.last_request_content and "<get memory>" not in user_input:
            _log.warning(f"Duplicate request detected and ignored: {user_input}")
            return None

        payload = {
            "model": self.openai_model,
            "temperature": 0.85,
            "top_p": 1,
            "presence_penalty": 1,
            "max_tokens": 3450,
            "messages": [
                            {"role": "system", "content": self.system_prompt}
                        ] + context + [
                            {"role": "user", "content": user_input}
                        ]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_secret}"
        }

        # 记录请求的payload
        _log.debug(f"Request payload: {payload}")

        try:
            response = requests.post(self.openai_api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()

            # 记录完整的响应数据
            _log.debug(f"Response data: {response_data}")

            reply = response_data['choices'][0]['message']['content'] if 'choices' in response_data and \
                                                                         response_data['choices'][0]['message'][
                                                                             'content'] else None

            #  更新 last_request_time 和 last_request_content
            self.last_request_time = time.time()
            self.last_request_content = user_input

            if reply is None:
                _log.warning(f"GPT response is empty for user input: {user_input}.")
            else:
                # 记录GPT的回复内容
                _log.info(f"GPT response: {reply}")

            return reply
        except requests.exceptions.RequestException as e:
            _log.error(f"Error requesting from OpenAI API: {e}", exc_info=True)
            return "子网故障,过来楼下检查一下/。"

    async def restart_bot(self, group_id, msg_id):
        """
        重启机器人

        参数:
            group_id (str): 群组ID
            msg_id (str): 消息ID
        """
        await self.api.post_group_message(
            group_openid=group_id,
            content=f"子网重启，请稍后... ({random.randint(1000, 9999)})",
            msg_id=msg_id
        )

        _log.info("Restarting bot...")

        self.observer.stop()
        self.observer.join()

        for task in self.message_handler.queue_timer.values():
            task.cancel()
        self.message_handler.queue_timer.clear()

        _log.info("Restart command received. Restarting bot...")

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
        _log.info("Hot reloading...")
        self.system_prompt = load_system_prompt(SYSTEM_PROMPT_FILE)
        load_user_names()
        await self.memory_manager.load_memory()
        _log.info("Hot reload completed")
        await self.api.post_group_message(
            group_openid=group_id,
            content="热重载完成，系统已更新。",
            msg_id=msg_id
        )
