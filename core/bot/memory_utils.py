# memory_utils.py
import random
from core.utils.utils import extract_memory_content, calculate_token_count
from core.utils.logger import get_logger

_log = get_logger()

async def manage_memory_insertion(memory_manager, group_id, cleaned_content, context):
    """
    检查是否需要插入记忆，并在需要时进行插入。

    参数:
        memory_manager (MemoryManager): 记忆管理器实例
        group_id (str): 群组的唯一标识符
        cleaned_content (str): 用户发送的消息内容
        context (list): 当前上下文消息列表

    返回:
        list: 可能更新后的上下文消息列表
    """
    if not is_critical_context_present(context, cleaned_content):
        _log.debug("正在检索相关记忆...")
        memory_to_insert = await memory_manager.retrieve_memory(group_id, cleaned_content)
        if memory_to_insert:
            _log.debug("找到相关记忆，准备插入上下文...")
            if not any(mem['content'] == memory_to_insert['content'] for mem in context):
                insert_position = random.randint(0, len(context))
                context.insert(insert_position, memory_to_insert)
                _log.info(f"记忆插入到上下文位置: {insert_position}")
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
    _log.debug("检测到 <get memory> 标记，正在检索长记忆...")

    long_term_memory = await memory_manager.retrieve_memory(group_id, cleaned_content)
    if long_term_memory:
        user_input_with_memory = f"{formatted_message}\n{long_term_memory['content']}"
        reply_content = await client.get_gpt_response(context, user_input_with_memory)
        return reply_content
    else:
        _log.warning(f"未能检索到相关的长记忆，继续处理当前对话。")
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
    _log.debug("提取新记忆内容...")
    memory_content = extract_memory_content(reply_content)
    if memory_content:
        _log.debug(f"存储新的记忆内容: {memory_content}")
        await memory_manager.store_memory(group_id, message, "assistant", memory_content)

        # 清除回复内容中的<memory>标记
        reply_content = reply_content.replace(f"<memory>{memory_content}</memory>", "")

    return reply_content
