"""
AmyAlmond Project - core/llm/plugins/inject_memory_client.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

inject_memory_client.py - 实现与 LLM 交互的客户端，用于处理记忆提取和注入任务
"""

import httpx
from core.utils.logger import get_logger

_log = get_logger()


class InjectMemoryClient:
    """
    用于与 LLM 交互的客户端类，专注于记忆提取和注入任务
    """

    def __init__(self, openai_secret, openai_model, openai_api_url):
        self.openai_secret = openai_secret
        self.openai_model = openai_model
        self.openai_api_url = openai_api_url
        self.last_request_time = 0
        self.last_request_content = None

    async def get_keywords_for_memory_retrieval(self, prompt):
        """
        从 LLM 获取用于记忆查询的关键词

        参数:
            prompt (str): 需要提取关键词的提示内容

        返回:
            str: LLM 生成的关键词
        """
        payload = {
            "openai_model": self.openai_model,
            "temperature": 0.7,
            "max_tokens": 100,
            "messages": [{"role": "system", "content": "请提取此Prompt中的关键词用于记忆查询，请注意语义联想搜索。"},
                         {"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_secret}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.openai_api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

            keywords = response_data['choices'][0]['message']['content'] if 'choices' in response_data and \
                                                                            response_data['choices'][0]['message'][
                                                                                'content'] else None

            if keywords is None:
                _log.warning(f"LLM response is empty for prompt: {prompt}.")
            else:
                _log.info(f"LLM provided keywords: {keywords}")

            return keywords
        except httpx.HTTPStatusError as e:
            _log.error(f"Error requesting keywords from LLM API: {e}", exc_info=True)
            return ""

    async def get_memory_summary(self, context):
        """
        从 LLM 获取当前对话的摘要

        参数:
            context (list): 包含之前的对话内容

        返回:
            str: LLM 生成的对话摘要
        """
        payload = {
            "openai_model": self.openai_model,
            "temperature": 0.7,
            "max_tokens": 200,
            "messages": context + [{"role": "system", "content": "请总结以上对话内容。"}]
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_secret}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.openai_api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

            summary = response_data['choices'][0]['message']['content'] if 'choices' in response_data and \
                                                                           response_data['choices'][0]['message'][
                                                                               'content'] else None

            if summary is None:
                _log.warning(f"LLM response is empty for context summary.")
            else:
                _log.info(f"LLM provided summary: {summary}")

            return summary
        except httpx.HTTPStatusError as e:
            _log.error(f"Error requesting summary from LLM API: {e}", exc_info=True)
            return ""
