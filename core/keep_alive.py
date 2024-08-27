"""
AmyAlmond Project - core/keep_alive.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.0 (Pre_827001)

keep_alive.py 包含 Keep-Alive 机制的实现,用于监控 API 的连接状态。
"""

import asyncio
import aiohttp
from core.utils.logger import get_logger
from core.utils.version_utils import is_newer_version
from config import OPENAI_SECRET, OPENAI_API_URL, OPENAI_KEEP_ALIVE, UPDATE_KEEP_ALIVE

_log = get_logger()

CURRENT_VERSION = "1.2.0 (Pre_827001)"
GITHUB_REPO = "shuakami/amyalmond_bot"

PRIMARY_API_URL = "https://api.amyalmond.mrsunny.top/api/github-status"
FALLBACK_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


async def fetch_version_info(url):
    """
    从指定的 URL 获取版本信息。

    参数:
        url (str): 要获取版本信息的 API 地址。

    返回:
        dict: 如果成功返回包含版本信息的字典，否则返回 None。
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    _log.warning(f"无法从 {url} 获取最新版本信息，状态码: {response.status}")
        except aiohttp.ClientError as e:
            _log.error(f"通过 {url} 获取最新版本时发生错误: {e}")
        except Exception as e:
            _log.error(f"未知错误: {e}")
    return None


async def get_latest_version():
    """
    获取最新版本信息，首先尝试从主 API 获取，如果失败则切换到备用 API。

    返回:
        list: 包含最新版本信息的列表，如果获取失败返回空列表。
    """
    version_info = await fetch_version_info(PRIMARY_API_URL)

    if not version_info:
        _log.warning(f"主API {PRIMARY_API_URL} 不可用，切换到备用API")
        version_info = await fetch_version_info(FALLBACK_API_URL)

    if isinstance(version_info, dict):
        # 如果返回的是单个版本信息，将其转换为列表
        return [version_info]
    elif isinstance(version_info, list):
        return version_info
    else:
        return []


async def check_for_updates():
    """
    检查是否有新版本可用，并根据版本类型（正式版或开发版）提醒用户更新。
    """
    if not UPDATE_KEEP_ALIVE:
        _log.warning("更新检查已关闭，建议打开以获取最新功能和修复~")
        return

    version_info_list = await get_latest_version()

    if version_info_list:
        stable_version = None
        dev_version = None

        for version_info in version_info_list:
            version_str = version_info.get("latestVersion")
            release_type = version_info.get("type", "Stable")

            if release_type == "Stable" and (not stable_version or is_newer_version(stable_version, version_str)[0]):
                stable_version = version_str
            elif release_type != "Stable" and (not dev_version or is_newer_version(dev_version, version_str)[0]):
                dev_version = version_str

        if stable_version:
            needs_update, message = is_newer_version(CURRENT_VERSION, stable_version)
            if needs_update:
                _log.info(f"新正式版可用: {stable_version}. 当前版本: {CURRENT_VERSION}. 请立即更新。")
            else:
                _log.info(f"当前版本: {CURRENT_VERSION}，最新稳定版: {stable_version}，{message}")

        if dev_version:
            needs_update, message = is_newer_version(CURRENT_VERSION, dev_version)
            if needs_update:
                _log.info(f"新开发版可用: {dev_version}. 当前版本: {CURRENT_VERSION}. 如果您是开发者，考虑尝试更新。")
            else:
                _log.info(f"当前版本: {CURRENT_VERSION}，最新开发版: {dev_version}，{message}")

    else:
        _log.warning("无法检查更新。")


async def keep_alive(api_url=OPENAI_API_URL, api_key=OPENAI_SECRET):
    """
    实现 Keep-Alive 机制，用于监控 API 的连接状态。

    参数:
        api_url (str): 要监控的 API 地址。
        api_key (str): 用于 API 认证的密钥。
    """

    if not UPDATE_KEEP_ALIVE and not OPENAI_KEEP_ALIVE:
        _log.warning("您已关闭 更新检查 和 OpenAI API 的 Keep-Alive 功能~")
        return
    if not UPDATE_KEEP_ALIVE:
        _log.warning("您已关闭 更新检查 的 Keep-Alive 功能，建议打开以保持程序最新~")
        return
    if not OPENAI_KEEP_ALIVE:
        _log.warning("您已关闭 OpenAI API 的 Keep-Alive 功能，建议打开以保持 API 连接正常~")
        return

    headers = {"Authorization": f"Bearer {api_key}"}

    # 在启动时检查一次更新
    await check_for_updates()

    while True:
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(api_url) as response:
                    if response.status == 404:
                        _log.info("OpenAI API 连接正常")
                    elif response.status == 401:
                        _log.warning("OpenAI API 认证失败,请检查 API 密钥是否正确")
                    else:
                        _log.warning(f"OpenAI API 连接异常,状态码: {response.status}")
                        _log.warning(f"详细信息: {await response.text()},请检查 API 状态")
        except aiohttp.ClientError as e:
            _log.error(f"OpenAI API 连接错误: {e}")
        except Exception as e:
            _log.error(f"OpenAI API 监控出现未知错误: {e}")

        # 每隔3分钟检查一次连接状态
        await asyncio.sleep(180)


async def update_check_loop():
    """
    定期检查更新的循环。
    """
    while True:
        await check_for_updates()
        # 每隔15分钟检查一次更新
        await asyncio.sleep(900)
