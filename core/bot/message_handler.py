"""
AmyAlmond Project - message_handler.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

message_handler.py 负责处理群组消息，包括动态消息队列管理、智能记忆注入、与Elasticsearch集成等功能。
"""

import asyncio

from botpy.message import GroupMessage
from botpy.types.message import Reference
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import MAX_CONTEXT_TOKENS

from core.bot.memory_utils import process_reply_content, handle_long_term_memory, manage_memory_insertion
# user_registration.py模块 - <处理新用户注册>
from core.bot.user_registration import handle_new_user_registration
# elasticsearch_index_manager.py模块 - <用于与Elasticsearch交互>
from core.db.elasticsearch_index_manager import ElasticsearchIndexManager
# logger.py模块 - <日志记录模块>
from core.utils.logger import get_logger
# user_management.py模块 - <用于用户内容清理、用户名获取、用户注册检查及新增用户处理>
from core.utils.user_management import clean_content, get_user_name, is_user_registered
# utils.py模块 - <从回复消息中提取记忆内容>
from core.utils.utils import calculate_token_count
# ace.py模块 - <安全性检查>
from core.ace.ace import ACE

_log = get_logger()


class MessageHandler:
    """
    负责处理群组消息的类，包括消息队列管理、记忆注入、新用户注册、智能查询选择等功能。
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
        self.es_manager = ElasticsearchIndexManager()  # 初始化Elasticsearch管理器
        self.message_queues = {}  # 每个群组一个消息队列
        self.locks = {}  # 每个群组一个锁
        self.processed_messages: set[int] = set()   # 记录已经处理过的消息ID
        self.queue_loop = asyncio.get_event_loop()  # 创建一个事件循环

        # 初始化ACE实例
        self.ace = ACE()

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

        # 检查消息是否已处理
        if message_id in self.processed_messages:
            _log.info(f"<SKIP> 消息 {message_id} 已经处理过，跳过。")
            return

        _log.info(f"<RECEIVED> 新消息 +++++++++++++")
        _log.info(f"   ↳ 用户: {user_name} ({user_id})")
        _log.info(f"   ↳ 群组: {group_id}")
        _log.info(f"   ↳ 内容: '{cleaned_content}'")
        _log.info("")

        # 进行用户输入验证
        if not self.ace.validate_user_input(cleaned_content):
            _log.warning(f"<ACE> 🚫消息违法，已被拒绝: {cleaned_content}")
            return

        # 检查请求频率
        if not self.ace.check_request_frequency(user_id):
            _log.warning(f"<ACE> 🚫{user_name} ({user_id}) 请求过于频繁，消息被拒绝")
            return

        # 添加消息ID到已处理集合中
        self.processed_messages.add(message_id)

        # 触发插件的 before_message_queue 事件
        plugin_result = await self.client.plugin_manager.event_bus.publish(
            "before_llm_message",
            message=message,
            reply_message=cleaned_content
        )

        # 如果某个插件要求停止继续处理，直接返回插件的回复
        if plugin_result is False:
            _log.info(f"插件已处理消息，跳过消息队列。")
            return

        # 清理过期的消息ID以避免集合过大
        if len(self.processed_messages) > 1000:
            _log.debug("<CLEANUP> 清理过期的消息ID...")
            self.processed_messages = set(list(self.processed_messages)[-500:])

        # 为新的群组初始化队列和锁
        if group_id not in self.message_queues:
            _log.debug(f"<INIT> 初始化群组 {group_id} 的消息队列和锁...")
            self.message_queues[group_id] = asyncio.Queue()
            self.locks[group_id] = asyncio.Semaphore(1)

        # 使用事件总线将消息发布出去，插件可以在此时对消息进行处理
        await self.client.plugin_manager.event_bus.publish("before_message_queue", message, cleaned_content)

        # 将消息放入对应群组的队列中
        await self.message_queues[group_id].put((user_name, cleaned_content, message))
        _log.debug(f"<QUEUE> 消息已加入群组 {group_id} 的队列")
        await self.process_message_queue(group_id)

    async def process_message_queue(self, group_id):
        async with self.locks[group_id]:  # 确保同一时间只有一个任务在处理该群组的消息
            _log.debug(f"<PROCESS> 开始处理群组 {group_id} 的消息队列...")
            while not self.message_queues[group_id].empty():
                user_name, cleaned_content, message = await self.message_queues[group_id].get()

                try:
                    _log.debug("<PMQ 消息队列> 🚀开始处理消息")
                    _log.debug(f"   ↳ 群组: {group_id}")
                    _log.debug(f"   ↳ 用户: {user_name} ({message.author.member_openid})")
                    _log.debug(f"   ↳ 内容: '{cleaned_content}'")

                    # 处理新用户注册
                    if not is_user_registered(message.author.member_openid):
                        _log.info(f"<REGISTER> 用户 {message.author.member_openid} 尚未注册，正在处理注册...")
                        await handle_new_user_registration(self.client, group_id, message.author.member_openid,
                                                           cleaned_content, message.id)
                        continue


                    # 在处理消息之前，通过事件总线触发插件逻辑
                    await self.client.plugin_manager.event_bus.publish("before_message_process", message,
                                                                       cleaned_content)

                    _log.debug(f"<COMPRESS> 正在压缩群组 {group_id} 的消息历史...")
                    context = await self.memory_manager.compress_memory(group_id, self.client.get_gpt_response)

                    # 初始化 formatted_message 变量
                    formatted_message = f"{user_name}: {cleaned_content}"

                    # 判断消息是否与上下文相似
                    if self.is_similar_to_context(cleaned_content, context):
                        _log.info(f"消息与上下文相似，跳过主动记忆调用。")
                    else:
                        # 将用户消息添加到历史记录中
                        _log.debug(f"<HISTORY> 添加消息到历史记录: {formatted_message}")
                        self.memory_manager.add_message_to_history(group_id,
                                                                   {"role": "user", "content": formatted_message})
                        context = await manage_memory_insertion(self.memory_manager, group_id, cleaned_content, context,
                                                                formatted_message)

                    # 动态消息队列长度调整 - 基于Token计数
                    current_token_count = calculate_token_count(context)
                    _log.debug(f"<TOKENS> 当前Token计数: {current_token_count}")
                    while current_token_count > MAX_CONTEXT_TOKENS:
                        context = context[1:]  # 移除最早的一条消息
                        current_token_count = calculate_token_count(context)
                        _log.debug(f"<TOKENS> 移除最早消息后Token计数: {current_token_count}")

                    # 在获取 LLM 回复之前，发布事件以允许插件进行处理
                    await self.client.plugin_manager.event_bus.publish("before_llm_response", context,
                                                                       formatted_message)

                    # 获取 LLM 的回复
                    context = [msg for msg in context if msg.get('content') and msg['content'].strip()]
                    _log.debug("<LLM> 正在获取LLM回复...")
                    reply_content = await self.client.get_gpt_response(context, formatted_message)

                    # 如果获取 LLM 回复失败，则使用原始消息作为回复内容
                    if reply_content is None:
                        _log.warning("   ↳ 未能获取LLM回复，使用原始消息作为回复内容")
                        reply_content = cleaned_content

                    # 处理长记忆的情况
                    if "<get memory>" in reply_content:
                        _log.debug("<MEMORY> LOADING")
                        _log.debug(">>> 🔄检测到 <get memory> 标记，正在检索长记忆...")
                        reply_content = await handle_long_term_memory(self.memory_manager, group_id, cleaned_content,
                                                                      formatted_message, context, self.client)
                    # 提取并存储新记忆内容
                    reply_content = await process_reply_content(self.memory_manager, group_id, message, reply_content)

                    # 生成并发送回复消息，包含消息处理时间
                    reply_message = reply_content or '抱歉，我暂时无法回复你的消息'

                    _log.debug(f"<PLUGIN> 插件处理前的消息: {reply_message}")

                    # 使用事件总线调用插件处理回复消息
                    plugin_result = await self.client.plugin_manager.event_bus.publish(
                        "before_send_reply",
                        message=message,
                        reply_message=reply_message
                    )

                    if plugin_result is not None:
                        reply_message = plugin_result

                    _log.debug(f"<PLUGIN> 插件处理后的消息: {reply_message}")

                    # 发送最终的回复消息
                    _log.info("<SEND> 发送回复消息:")
                    _log.info(f"   ↳ 目标群组: {group_id}")
                    _log.info(f"   ↳ 回复内容: {reply_message}")
                    message_reference = Reference(message_id=message.id, ignore_get_message_error=True)
                    await self.client.api.post_group_message(
                        group_openid=group_id,
                        content=reply_message,
                        msg_id=message.id,
                        message_reference=message_reference
                    )

                    # 将用户消息和机器人的回复存储到数据库
                    _log.debug(">>> 存储用户消息到数据库...")
                    await self.memory_manager.store_memory(group_id, message, "user", formatted_message)
                    _log.debug(">>> 存储机器人回复到数据库...")
                    await self.memory_manager.store_memory(group_id, message, "assistant", reply_content)

                except Exception as e:
                    _log.error(f"<ERROR> 🚨处理群组 {group_id} 的消息时出错:")
                    _log.error(f"   ↳ 错误详情: {e}", exc_info=True)
                finally:
                    _log.debug("<COMPLETE> 消息处理完成，标记任务完成")
                    self.message_queues[group_id].task_done()

    @staticmethod
    def is_similar_to_context(content, context, threshold=0.75):
        """
        判断当前消息是否与上下文中的消息相似。

        参数:
            content (str): 当前消息内容
            context (list): 消息上下文，包含之前的对话内容
            threshold (float): 相似度阈值，默认0.75

        返回:
            bool: 如果相似度超过阈值，返回 True，否则返回 False
        """
        if not context:
            return False

        # 提取上下文中的内容
        context_contents = [msg['content'] for msg in context if 'content' in msg and msg['content'].strip()]
        documents = context_contents + [content]

        # 计算TF-IDF向量
        vectorizer = TfidfVectorizer().fit_transform(documents)
        vectors = vectorizer.toarray()

        # 计算当前消息与上下文中每条消息的相似度
        cosine_similarities = cosine_similarity([vectors[-1]], vectors[:-1]).flatten()

        # 如果有任何一条消息的相似度超过阈值，返回True
        return any(similarity > threshold for similarity in cosine_similarities)