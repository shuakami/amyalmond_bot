"""
AmyAlmond Project - message_handler.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.0 (Alpha_817001)

message_handler.py 负责处理群组消息，包括消息队列的管理和新用户注册等功能
"""

import asyncio
import time
from datetime import datetime


from botpy.message import GroupMessage
from botpy.types.message import Reference

# user_management.py模块 - <用于用户内容清理、用户名获取、用户注册检查及新增用户处理>
from user_management import clean_content, get_user_name, is_user_registered, add_new_user
# utils.py模块 - <从回复消息中提取记忆内容>
from utils import extract_memory_content
# logger.py模块 - <日志记录>
from logger import get_logger

_log = get_logger()


class MessageHandler:
    """
    负责处理群组消息的类，包括消息队列管理和新用户注册等功能
    """

    def __init__(self, client, memory_manager):
        """
        初始化 MessageHandler 实例，创建消息队列、锁、处理消息ID的集合和事件循环

        参数:
            client (BotClient): 机器人客户端实例
            memory_manager (MemoryManager): 记忆管理器实例
        """
        self.client = client
        self.memory_manager = memory_manager
        self.message_queues = {}  # 每个群组一个消息队列
        self.locks = {}  # 每个群组一个锁
        self.processed_messages = set()  # 记录已经处理过的消息ID
        self.queue_loop = asyncio.get_event_loop()  # 创建一个事件循环
        self.queue_timer = {}  # 初始化 queue_timer

    async def handle_group_message(self, message: GroupMessage):
        """
        处理收到的群组消息，分发到相应的消息队列中，并启动消息处理任务

        参数:
            message (GroupMessage): 收到的群组消息
        """
        group_id = message.group_openid
        user_id = message.author.member_openid
        user_name = get_user_name(user_id)
        cleaned_content = clean_content(message.content)
        message_id = message.id

        _log.info(f"Received message: '{cleaned_content}' from user: {user_name}({user_id}) in group: {group_id}")

        # 检查消息是否已处理
        if message_id in self.processed_messages:
            _log.info(f"Message {message_id} has already been processed. Skipping.")
            return

        # 添加消息ID到已处理集合中
        self.processed_messages.add(message_id)

        # 清理过期的消息ID以避免集合过大
        if len(self.processed_messages) > 1000:
            self.processed_messages = set(list(self.processed_messages)[-500:])

        # 为新的群组初始化队列和锁
        if group_id not in self.message_queues:
            self.message_queues[group_id] = asyncio.Queue()
            self.locks[group_id] = asyncio.Lock()

        # 将消息放入对应群组的队列中
        await self.message_queues[group_id].put((user_name, cleaned_content, message))

        # 启动消息处理任务（如果尚未启动）
        if not self.locks[group_id].locked():
            await self.queue_loop.create_task(self.process_message_queue(group_id))

    async def process_message_queue(self, group_id):
        """
        处理群组消息队列中的消息，确保同一时间只有一个任务在处理该群组的消息

        参数:
            group_id (str): 群组的唯一标识符
        """
        async with self.locks[group_id]:  # 确保同一时间只有一个任务在处理该群组的消息
            while not self.message_queues[group_id].empty():
                user_name, cleaned_content, message = await self.message_queues[group_id].get()

                try:
                    _log.info(f"Processing message from queue for group {group_id}: {cleaned_content}")

                    # 处理管理员指令
                    if message.author.member_openid == self.client.ADMIN_ID:
                        if cleaned_content.strip().lower() == "restart":
                            await self.client.restart_bot(group_id, message.id)
                            continue
                        elif cleaned_content.strip().lower() == "reload":
                            await self.client.hot_reload(group_id, message.id)
                            continue

                    # 处理新用户注册
                    if not is_user_registered(message.author.member_openid):
                        await self.handle_new_user_registration(group_id, message.author.member_openid, cleaned_content, message.id)
                        continue

                    # 将用户消息添加到历史记录，并处理队列中的消息
                    self.memory_manager.add_message_to_history(group_id, {"role": "user", "content": f"{user_name}: {cleaned_content}"})
                    context = await self.memory_manager.compress_memory(group_id, self.client.get_gpt_response)

                    user_input_with_name = f"[{user_name}: {cleaned_content}]"
                    reply_content = await self.client.get_gpt_response(context, user_input_with_name)

                    # 处理长记忆的情况
                    if reply_content is not None and "<get memory>" in reply_content:
                        long_term_memory = await self.memory_manager.read_long_term_memory(group_id)
                        user_input_with_memory = f"{user_input_with_name}\n{long_term_memory}"
                        reply_content = await self.client.get_gpt_response(context, user_input_with_memory)

                    # 提取并存储新记忆内容
                    memory_content = extract_memory_content(reply_content)
                    if memory_content:
                        await self.memory_manager.append_to_long_term_memory(group_id, memory_content)
                        reply_content = reply_content.replace(f"<memory>{memory_content}</memory>", "")

                    # 生成并发送回复消息，包含消息处理时间
                    message_datetime = datetime.fromisoformat(message.timestamp)
                    message_timestamp = message_datetime.timestamp()
                    reply_message = f"{reply_content}\n---\n本次消息花费了 {int((time.time() - message_timestamp) * 1000)} 毫秒，请及时支付电费账单。"

                    message_reference = Reference(message_id=message.id)
                    await self.client.api.post_group_message(
                        group_openid=group_id,
                        content=reply_message,
                        msg_id=message.id,
                        message_reference=message_reference
                    )

                    # 将机器人回复添加到历史记录中，并保存记忆
                    self.memory_manager.add_message_to_history(group_id, {"role": "assistant", "content": reply_content})
                    await self.memory_manager.save_memory()

                except Exception as e:
                    _log.error(f"Error processing message for group {group_id}: {e}", exc_info=True)
                finally:
                    self.message_queues[group_id].task_done()

    async def handle_new_user_registration(self, group_id, user_id, cleaned_content, msg_id):
        """
        处理新用户注册，检查用户是否已注册，并提示用户提供昵称

        参数:
            group_id (str): 群组的唯一标识符
            user_id (str): 用户的唯一标识符
            cleaned_content (str): 用户发送的消息内容
            msg_id (str): 消息的唯一标识符
        """
        try:
            if user_id not in self.client.pending_users:
                _log.info(f"User {user_id} not registered. Prompting for nickname.")
                await self.client.api.post_group_message(
                    group_openid=group_id,
                    content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                    msg_id=msg_id
                )
                self.client.pending_users[user_id] = True
            else:
                if cleaned_content.strip():
                    if await add_new_user(user_id, cleaned_content.strip()):
                        _log.info(f"New user {user_id} registered with nickname: {cleaned_content.strip()}")
                        await self.client.api.post_group_message(
                            group_openid=group_id,
                            content=f"原来是{cleaned_content}吗 ... 我已经记住你了~",
                            msg_id=msg_id
                        )
                    else:
                        _log.info(f"User {user_id} nickname already registered.")
                        await self.client.api.post_group_message(
                            group_openid=group_id,
                            content="你的昵称已经录入~",
                            msg_id=msg_id
                        )
                else:
                    _log.info(f"User {user_id} did not provide a nickname. Prompting again.")
                    await self.client.api.post_group_message(
                        group_openid=group_id,
                        content="请@我，然后回复你的昵称，这将会自动录入我的记忆，方便我永远记得你~",
                        msg_id=msg_id
                    )
                self.client.pending_users.pop(user_id, None)
        except Exception as e:
            _log.error(f"Error during new user registration for group {group_id}: {e}", exc_info=True)
