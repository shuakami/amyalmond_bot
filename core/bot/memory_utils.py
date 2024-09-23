"""
AmyAlmond Project - core/bot/memory_utils.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

memory_utils.py - 负责处理记忆相关的功能
"""
from core.utils.utils import extract_memory_content
from core.utils.logger import get_logger

_log = get_logger()

async def manage_memory_insertion(memory_manager, group_id, cleaned_content, context, user_message):
    """
    检查是否需要插入记忆，并在需要时进行插入。插入位置为用户消息之后。

    参数:
        memory_manager (MemoryManager): 记忆管理器实例
        group_id (str): 群组的唯一标识符
        cleaned_content (str): 用户发送的消息内容
        context (list): 当前上下文消息列表
        user_message (str): 用户的原始消息

    返回:
        list: 可能更新后的上下文消息列表
    """
    memory_to_insert = await memory_manager.retrieve_memory(group_id, cleaned_content)
    if memory_to_insert:
        memory_content = memory_to_insert['content']
        memory_insertion = f"{user_message}\n---\n<在数据库查找到的你的长期记忆，请谨慎使用：{memory_content}>"

        # 查找最后一个用户消息的位置，将记忆插入到其后
        inserted = False
        for i in range(len(context) - 1, -1, -1):
            if context[i]['role'] == 'user' and context[i]['content'] == user_message:
                context.insert(i + 1, {"role": "user", "content": memory_insertion})
                inserted = True
                _log.info(">>> 记忆已插入到用户消息之后")
                break

        # 如果没有找到匹配的用户消息，默认追加到上下文末尾
        if not inserted:
            context.append({"role": "user", "content": memory_insertion})
            _log.info(">>> 未找到匹配的用户消息，记忆已追加到上下文末尾")

    else:
        _log.info(">>> 没有找到需要插入的记忆内容")

    return context




def is_critical_context_present(context, content):
    """
    检查上下文中是否包含与当前消息相关的关键信息。
    如果上下文中已经包含相关信息，则返回 True，否则返回 False。
    """
    # 根据关键字或语义分析判断是否存在关键上下文信息
    for msg in context:
        if content in msg['content']:
            return True
    return False

async def handle_long_term_memory(memory_manager, group_id, cleaned_content, formatted_message, context, client):
    """
    处理长记忆的插入和更新。

    参数:
        memory_manager (MemoryManager): 记忆管理器实例
        group_id (str): 群组的唯一标识符
        cleaned_content (str): 用户发送的消息内容
        formatted_message (str): 格式化后的用户消息
        context (list): 当前上下文消息列表
        client (BotClient): 机器人客户端实例

    返回:
        str: 更新后的回复内容
    """
    _log.debug(">>> 检测到 <get memory> 标记，正在检索长记忆...")

    long_term_memory = await memory_manager.retrieve_memory(group_id, cleaned_content)
    if long_term_memory:
        user_input_with_memory = f"{formatted_message}\n{long_term_memory['content']}"
        reply_content = await client.get_gpt_response(context, user_input_with_memory)
        return reply_content
    else:
        _log.warning(">>> 未能检索到相关的长记忆，继续处理当前对话。")
        return None

async def process_reply_content(memory_manager, group_id, message, reply_content):
    """
    处理并存储回复内容中的记忆，并清除标记。

    参数:
        memory_manager (MemoryManager): 记忆管理器实例
        group_id (str): 群组的唯一标识符
        message (GroupMessage): 收到的群组消息
        reply_content (str): LLM生成的回复内容

    返回:
        str: 更新后的回复内容
    """
    _log.debug(">>> 提取新记忆内容...")
    memory_content = extract_memory_content(reply_content)
    if memory_content:
        _log.debug(f">>> 存储新的记忆内容: {memory_content}")
        await memory_manager.store_memory(group_id, message, "assistant", memory_content)

        # 清除回复内容中的<memory>标记
        reply_content = reply_content.replace(f"<memory>{memory_content}</memory>", "")

    return reply_content
