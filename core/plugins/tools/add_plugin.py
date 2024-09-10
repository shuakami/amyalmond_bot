"""
AmyAlmond - Plugin Creation Tool
This module helps users create plugins using LLM responses.
"""

from core.llm.llm_factory import LLMFactory

async def create_plugin(system_prompt, user_input):
    """
    利用 LLM 帮助用户创建插件

    Args:
        system_prompt (list or str): 机器人系统提示词。如果为str则转换为列表。
        user_input (str): 用户输入的插件需求

    Returns:
        str: 生成的插件代码或插件创建结果
    """
    # 确保 system_prompt 是字符串，将其合并为一个提示
    if isinstance(system_prompt, list):
        system_prompt = "，".join(system_prompt)  # 将列表转换为一个逗号分隔的字符串

    # 创建 LLM 客户端实例
    factory = LLMFactory()
    client = factory.create_llm_client()  # 使用工厂类创建 LLM 客户端
    # context为空
    context = []
    print("user_input:", user_input)
    print("system_prompt:", system_prompt)

    # 获取 LLM 回复
    try:
        llm_response = await client.get_response(context, user_input, system_prompt)
        return llm_response
    except Exception as e:
        return f"<ERROR> 插件创建失败: {e}"
