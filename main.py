"""
AmyAlmond Project - Main.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/16 11:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.0.0 (Beta_815001)

AmyAlmond 是一个聊天机器人应用，设计用于在群聊中响应用户消息。
它使用 LLM API，根据对话的上下文生成回复。
该机器人能够记住用户名，管理长期记忆，并处理管理员命令。
"""
import asyncio
import os
import random
import subprocess
import sys
import requests
import json
import time
from collections import deque
import re
import botpy
from botpy.message import GroupMessage
from botpy.ext.cog_yaml import read
from botpy.types.message import Reference
import watchdog.events
import watchdog.observers

# 定义目录结构
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "configs")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# 确保目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 配置文件路径
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
SYSTEM_PROMPT_FILE = os.path.join(CONFIG_DIR, "system-prompt.txt")

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

# 数据文件路径
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
LONG_TERM_MEMORY_FILE = os.path.join(DATA_DIR, "long_term_memory_{}.txt")
USER_NAMES_FILE = os.path.join(DATA_DIR, "user_names.json")

# 读取配置文件
test_config = read(CONFIG_FILE)

# 设置日志文件
_log = botpy.logging.get_logger()

# 定义最大上下文记忆条数
MAX_CONTEXT_MESSAGES = 6

# 用户名映射表
USER_NAMES = {}


def clean_content(content):
    return content.replace('<@!', '').replace('>', '')


def get_user_name(user_id):
    """根据用户 ID 获取用户名"""
    if user_id in USER_NAMES:
        return USER_NAMES[user_id]
    else:
        return f"消息来自未知用户："


def load_user_names():
    """从文件加载用户名映射"""
    global USER_NAMES
    try:
        with open(USER_NAMES_FILE, "r", encoding="utf-8") as f:
            USER_NAMES = json.load(f)
    except FileNotFoundError:
        USER_NAMES = {}


def save_user_names():
    """保存用户名映射到文件"""
    with open(USER_NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_NAMES, f, ensure_ascii=False, indent=4)


class ConfigFileHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, client):
        self.client = client

    def on_modified(self, event):
        if event.src_path.endswith(SYSTEM_PROMPT_FILE):
            self.client.reload_system_prompt()


class MyClient(botpy.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_users = {}
        self.message_history = {}
        self.message_queue = {}
        self.queue_timer = {}
        self.load_system_prompt()

        # 读取配置 ####################################################################
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
        #############################################################################

        # 设置文件监视器
        self.observer = watchdog.observers.Observer()
        event_handler = ConfigFileHandler(self)
        self.observer.schedule(event_handler, path='.', recursive=False)
        self.observer.start()

    def load_system_prompt(self):
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        _log.info(f"SystemPromptStatus: {len(self.system_prompt)}")

    def reload_system_prompt(self):
        self.load_system_prompt()
        _log.info("System prompt reloaded")

    async def on_ready(self):
        _log.info(f"Robot 「{self.robot.name}」 is ready!")
        load_user_names()
        await self.load_memory()

    async def on_group_at_message_create(self, message: GroupMessage):
        try:
            group_id = message.group_openid
            cleaned_content = clean_content(message.content)
            user_id = message.author.member_openid
            user_name = get_user_name(user_id)

            _log.info(f"Received message: '{cleaned_content}' from user: {user_name}({user_id}) in group: {group_id}")

            # 处理管理员指令
            if user_id == self.ADMIN_ID:
                if cleaned_content.strip().lower() == "restart":
                    await self.restart_bot(group_id, message.id)
                    return
                elif cleaned_content.strip().lower() == "reload":
                    await self.hot_reload(group_id, message.id)
                    return

            # 如果用户不在映射表中
            if user_id not in USER_NAMES:
                if user_id not in self.pending_users:
                    # 如果用户是第一次发送消息，提示用户输入昵称
                    await self.api.post_group_message(
                        group_openid=group_id,
                        content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                        msg_id=message.id
                    )
                    self.pending_users[user_id] = True
                    _log.info(f"Prompted new user for nickname: {user_id}")
                else:
                    # 如果用户已经被提示输入昵称，保存他们的下一条消息作为昵称
                    if cleaned_content.strip():  # 确保消息不为空
                        if await self.add_new_user(user_id, cleaned_content.strip()):
                            await self.api.post_group_message(
                                group_openid=group_id,
                                content=f"原来是{cleaned_content}吗 ... 我已经记住你了~",
                                msg_id=message.id
                            )
                            _log.info(f"New user registered: {user_id} - {cleaned_content}")
                        else:
                            await self.api.post_group_message(
                                group_openid=group_id,
                                content="你的昵称已经录入~",
                                msg_id=message.id
                            )
                    else:
                        await self.api.post_group_message(
                            group_openid=group_id,
                            content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                            msg_id=message.id
                        )
                    # 从 pending_users 中移除该用户
                    self.pending_users.pop(user_id, None)
                return

            if group_id not in self.message_history:
                self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_MESSAGES)

            await self.add_message_to_queue(group_id, user_name, cleaned_content)

            if group_id not in self.queue_timer:
                self.queue_timer[group_id] = asyncio.create_task(
                    self.process_message_queue(group_id, message, cleaned_content)
                )

        except Exception as e:
            _log.error(f"Error processing message: {e}", exc_info=True)

    async def add_message_to_queue(self, group_id, user_name, message):
        if group_id not in self.message_queue:
            self.message_queue[group_id] = []
        self.message_queue[group_id].append(f"{user_name}: {message}")

    async def process_message_queue(self, group_id, message: GroupMessage, cleaned_content):
        await asyncio.sleep(2)

        messages = self.message_queue.pop(group_id, [])
        combined_message = "\n".join(messages)

        _log.info(f"Processing message queue for group {group_id}: {combined_message}")

        del self.queue_timer[group_id]

        if group_id not in self.message_history:
            self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_MESSAGES)

        self.message_history[group_id].append({"role": "user", "content": combined_message})

        context = await self.compress_memory(group_id)

        user_input_with_name = f"[{combined_message}]"

        start_time = time.time()
        reply_content = await self.get_gpt_response(context, user_input_with_name)
        end_time = time.time()
        api_request_time = round((end_time - start_time) * 1000)

        _log.info(f"GPT response received in {api_request_time}ms for group {group_id}")

        if "<get memory>" in reply_content:
            long_term_memory = await self.read_long_term_memory(group_id)
            user_input_with_memory = f"{user_input_with_name}\n{long_term_memory}"
            reply_content = await self.get_gpt_response(context, user_input_with_memory)
            _log.info(f"Retrieved and used long-term memory for group {group_id}")

        memory_content = self.extract_memory_content(reply_content)
        if memory_content:
            await self.append_to_long_term_memory(group_id, memory_content)
            reply_content = reply_content.replace(f"<memory>{memory_content}</memory>", "")
            _log.info(f"Appended new memory for group {group_id}: {memory_content}")

        dingni = api_request_time // 1

        reply_message = f"{reply_content}\n---\n" \
                        f"本次消息花费了 {dingni} 丁尼，请及时支付电费账单。"

        message_reference = Reference(message_id=message.id)
        await self.api.post_group_message(
            group_openid=group_id,
            content=reply_message,
            msg_id=message.id,
            message_reference=message_reference
        )

        _log.info(f"Sent reply to group {group_id}: {reply_content}")

        self.message_history[group_id].append({"role": "assistant", "content": reply_content})

        await self.save_memory()

    def extract_memory_content(self, message):
        match = re.search(r'<memory>(.*?)</memory>', message, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def append_to_long_term_memory(self, group_id, content):
        with open(LONG_TERM_MEMORY_FILE.format(group_id), "a", encoding="utf-8") as f:
            f.write(content + "\n")

    async def read_long_term_memory(self, group_id):
        try:
            with open(LONG_TERM_MEMORY_FILE.format(group_id), "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "暂无长期记忆"

    async def get_gpt_response(self, context, user_input):
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
        try:
            _log.info(f"Requesting from OpenAI API with payload: {payload}")
            response = requests.post("https://api.openai-hk.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            return response_data['choices'][0]['message']['content'] if 'choices' in response_data else '无法生成回应。'
        except requests.exceptions.RequestException as e:
            _log.error(f"Error requesting from OpenAI API: {e}")
            return "子网故障，过来楼下检查一下/。"

    async def compress_memory(self, group_id):
        if len(self.message_history[group_id]) > MAX_CONTEXT_MESSAGES:
            summary = await self.get_gpt_response(
                self.message_history[group_id], "请用一句话总结以上对话"
            )
            self.message_history[group_id].clear()
            self.message_history[group_id].append({"role": "assistant", "content": summary})
        return list(self.message_history[group_id])

    async def load_memory(self):
        _log.info("Loading memory...")
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    _log.info(f"Reading memory file: {MEMORY_FILE}")
                    data = json.load(f)
                    _log.info(f"Memory file content: {data}")
                    for group_id, messages in data.items():
                        _log.info(f"Processing group: {group_id}")
                        if not isinstance(messages, list):
                            _log.warning(f"Unexpected data type for group {group_id}: {type(messages)}")
                            continue
                        self.message_history[group_id] = deque(maxlen=MAX_CONTEXT_MESSAGES)
                        for message in messages:
                            if isinstance(message, dict) and 'role' in message and 'content' in message:
                                self.message_history[group_id].append(message)
                            else:
                                _log.warning(f"Skipping invalid message in group {group_id}: {message}")
                        _log.info(f"Loaded {len(self.message_history[group_id])} messages for group {group_id}")
            else:
                _log.info(f"Memory file {MEMORY_FILE} does not exist. Starting with empty memory.")

            for group_id in self.message_history:
                try:
                    long_term_memory_file = LONG_TERM_MEMORY_FILE.format(group_id)
                    if os.path.exists(long_term_memory_file):
                        with open(long_term_memory_file, "r", encoding="utf-8") as f:
                            long_term_memory = f.read()
                            self.message_history[group_id].appendleft({"role": "system", "content": long_term_memory})
                            _log.info(f"Loaded long-term memory for group {group_id}")
                    else:
                        _log.info(f"No long-term memory file found for group {group_id}")
                except Exception as e:
                    _log.error(f"Error loading long-term memory for group {group_id}: {e}")

        except json.JSONDecodeError as e:
            _log.error(f"JSON decoding error in memory file: {e}")
        except Exception as e:
            _log.error(f"Error loading memory: {e}", exc_info=True)

        _log.info("Memory loading completed")

    async def save_memory(self):
        _log.info("Saving memory...")
        try:
            data = {}
            for group_id, messages in self.message_history.items():
                if len(messages) > MAX_CONTEXT_MESSAGES:
                    messages = list(messages)[-MAX_CONTEXT_MESSAGES:]
                data[group_id] = list(messages)
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            _log.error(f"Error saving memory: {e}")

    async def add_new_user(self, user_id, nickname):
        USER_NAMES[user_id] = f"消息来自{nickname}："
        save_user_names()
        _log.info(f"Added new user: {user_id} - {nickname}")
        load_user_names()  # 重新加载用户名映射以确保更新生效

    async def restart_bot(self, group_id, msg_id):

        await self.api.post_group_message(
            group_openid=group_id,
            content=f"子网重启，请稍后... ({random.randint(1000, 9999)})",
            msg_id=msg_id
        )

        _log.info("Restarting bot...")

        # 停止文件监视器
        self.observer.stop()
        self.observer.join()

        # 清理异步任务和队列
        for task in self.queue_timer.values():
            task.cancel()
        self.queue_timer.clear()

        _log.info("Restart command received. Restarting bot...")

        # 使用 subprocess.Popen 重新启动 Python 解释器
        python = sys.executable
        subprocess.Popen([python] + sys.argv)

        # 退出当前进程
        sys.exit()

    async def hot_reload(self, group_id, msg_id):
        _log.info("Hot reloading...")
        self.load_system_prompt()
        load_user_names()
        await self.load_memory()
        _log.info("Hot reload completed")
        await self.api.post_group_message(
            group_openid=group_id,
            content="热重载完成，系统已更新。",
            msg_id=msg_id
        )


if __name__ == "__main__":
    print("")
    print("     _                       _    _                           _ ")
    print("    / \\   _ __ ___  _   _   / \\  | |_ __ ___   ___  _ __   __| |")
    print("   / _ \\ | '_ ` _ \\| | | | / _ \\ | | '_ ` _ \\ / _ \\| '_ \\ / _` |")
    print("  / ___ \\| | | | | | |_| |/ ___ \\| | | | | | | (_) | | | | (_| |")
    print(" /_/   \\_|_| |_| |_|\\__, /_/   \\_|_|_| |_| |_|\\___/|_| |_|\\__,_|")
    print("                    |___/                                       ")
    print("")
    intents = botpy.Intents(public_messages=True, public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
