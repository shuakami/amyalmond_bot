"""
AmyAlmond Project - core/llm/llm_factory.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

llm_factory.py - LLM 工厂类，用于根据配置文件创建相应的 LLM 客户端。
"""

from core.llm.llm_client import LLMClient
from core.llm.plugins.aliyun_client import AliyunClient
from core.llm.plugins.anthropic_client import AnthropicClient
from core.llm.plugins.azure_client import AzureClient
from core.llm.plugins.chatglm_client import ChatGLMClient
from core.llm.plugins.google_client import GoogleClient
from core.llm.plugins.openai_client import OpenAIClient
from config import test_config
from core.utils.logger import get_logger

_log = get_logger()


class LLMFactory:
    """
    LLM 工厂类，用于根据配置文件创建相应的 LLM 客户端。
    """

    def create_llm_client(self) -> LLMClient:
        """
        根据配置文件创建 LLM 客户端。

        Returns:
            LLMClient: LLM 客户端实例。
        """

        # 如果用户没有设置，警告一下
        if not test_config.get("llm_provider"):
            _log.warning("🔥你没有在配置文件中设置 LLM 提供商，已使用默认 OpenAI。🔥")

        # 打印当前LLM
        _log.info(f"🔥当前LLM厂商： {test_config.get('llm_provider', 'openai')}🔥")

        llm_provider = test_config.get("llm_provider", "openai").lower()  # 转换为小写字母

        # 定义一部字典来存储提供商和对应的配置项
        provider_configs = {
            "openai": ["openai_secret", "openai_model", "openai_api_url"],
            "azure": ["azure_secret", "azure_model", "azure_api_url"],
            "google": ["google_api_key", "google_model", "google_api_url"],
            "anthropic": ["anthropic_secret", "anthropic_model", "anthropic_api_url"],
            "aliyun": ["aliyun_secret", "aliyun_model", "aliyun_api_url"],
            "chatglm": ["chatglm_secret", "chatglm_model", "chatglm_api_url"],
            "free_chatgpt_api": ["free_chatgpt_api_secret", "free_chatgpt_api_model", "free_chatgpt_api_url"]
        }

        # 检查配置项是否存在
        if llm_provider in provider_configs:
            required_configs = provider_configs[llm_provider]
            missing_configs = [config for config in required_configs if not test_config.get(config)]
            if missing_configs:
                _log.error(f"🔥 请在配置文件中填写 {llm_provider} 的相关配置项：{'、'.join(missing_configs)} 🔥")
                # 中断程序执行
                raise SystemExit(1)

        llm_provider = test_config.get("llm_provider", "openai")
        if llm_provider == "openai":
            return OpenAIClient(test_config.get("openai_secret"),
                                test_config.get("openai_model"),
                                test_config.get("openai_api_url"))
        elif llm_provider == "azure":
            return AzureClient(test_config.get("azure_secret"),
                               test_config.get("azure_model"),
                               test_config.get("azure_api_url"))
        elif llm_provider == "google":
            return GoogleClient(test_config.get("google_api_key"),
                                test_config.get("google_model"),
                                test_config.get("google_api_url"))
        elif llm_provider == "anthropic":
            return AnthropicClient(test_config.get("anthropic_secret"),
                                   test_config.get("anthropic_model"),
                                   test_config.get("anthropic_api_url"))
        elif llm_provider == "aliyun":
            return AliyunClient(test_config.get("aliyun_secret"),
                                test_config.get("aliyun_model"),
                                test_config.get("aliyun_api_url"))
        elif llm_provider == "chatglm":
            return ChatGLMClient(test_config.get("chatglm_secret"),
                                 test_config.get("chatglm_model"),
                                 test_config.get("chatglm_api_url"))
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
