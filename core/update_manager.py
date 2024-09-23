import aiohttp
import json
import os
import asyncio
from datetime import datetime, timedelta
from core.utils.logger import get_logger
from core.utils.version_utils import is_newer_version
import subprocess
import sys
import urllib.parse
import platform

_log = get_logger()

FETCH_RELEASE_URL = "https://bot.luoxiaohei.cn/api/fetchLatestRelease"
AUTO_UPDATE_SCRIPT_URL = "https://bot.luoxiaohei.cn/auto_update.py"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENT_VERSION = "1.1.5 (Alpha_829001)"
CONFIG_PATH = os.path.join(ROOT_DIR, "configs", "update_config.json")

async def fetch_latest_release():
    """
    获取最新版本的发布信息。
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(FETCH_RELEASE_URL) as response:
            if response.status == 200:
                return await response.json()
            else:
                _log.warning(f"获取最新版本信息失败，状态码: {response.status}")
                return None

async def prompt_user_for_update(stable_version_info, dev_version_info):
    """
    询问用户是否要更新到最新版本以及选择更新的版本类型。
    """
    stable_version = stable_version_info.get("latestVersion")
    dev_version = dev_version_info.get("latestVersion")
    print(f"检测到新版本: 稳定版: {stable_version}, 开发版: {dev_version}。您当前版本是: {CURRENT_VERSION}。")
    print("请选择更新选项:")
    print("1. 更新到最新稳定版")
    print("2. 更新到最新开发版")
    print("3. 不更新")
    print("4. 不更新，且7天内不再提示")

    user_choice = input("请输入您的选择 (1/2/3/4): ")
    if user_choice == "1":
        await handle_user_choice("stable", stable_version_info)
    elif user_choice == "2":
        await handle_user_choice("development", dev_version_info)
    elif user_choice == "3":
        _log.info("已选择不更新。")
    elif user_choice == "4":
        _log.info("已选择不更新，并在7天内不再提示。")
        # 保存配置以便7天内不再提示
        update_config = {
            "snooze_until": (datetime.now() + timedelta(days=7)).isoformat()
        }
        # 如果没有自动创建
        with open(CONFIG_PATH, 'w') as f:
            json.dump(update_config, f)
    else:
        print("无效选择，请重新输入。")
        await prompt_user_for_update(stable_version_info, dev_version_info)


async def handle_user_choice(choice, version_info):
    """
    处理用户的更新选择。
    """
    download_url = version_info.get("downloadUrl")
    full_download_url = f"https://bot.luoxiaohei.cn{download_url}"  # 拼接完整的下载URL

    if choice in ["stable", "development"]:
        # 正确解析下载URL并获取文件名
        parsed_url = urllib.parse.urlparse(full_download_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        actual_download_url = query_params.get('url', [None])[0]
        if actual_download_url:
            zip_file_name = os.path.basename(urllib.parse.unquote(actual_download_url))
        else:
            _log.error("无法解析下载的URL")
            return

        zip_download_path = os.path.join(ROOT_DIR, zip_file_name)

        await download_file_with_progress(full_download_url, zip_download_path)
        await download_file_with_progress(AUTO_UPDATE_SCRIPT_URL, os.path.join(ROOT_DIR, "auto_update.py"))

        _log.info("更新文件已下载，准备退出程序并执行更新。")
        await shutdown_and_update(zip_download_path)

async def download_file_with_progress(url, dest_path):
    """
    下载文件到指定路径，并显示下载进度条。
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                total_size = int(response.headers.get('content-length', 0))
                with open(dest_path, 'wb') as f:
                    downloaded_size = 0
                    async for data in response.content.iter_chunked(1024):
                        f.write(data)
                        downloaded_size += len(data)
                        progress = (downloaded_size / total_size) * 100
                        print(f'\r下载进度: [{progress:.2f}%]', end='')
                print()  # 换行
                _log.info(f"文件已下载到 {dest_path}")
            else:
                _log.error(f"下载文件失败，状态码: {response.status}")

async def handle_updates():
    """
    检查是否有新版本可用，并根据版本类型（正式版或开发版）提醒用户更新。
    """
    version_info_list = await fetch_latest_release()

    if version_info_list:
        stable_info = version_info_list.get('stable', None)
        dev_info = version_info_list.get('development', None)

        stable_version = stable_info.get("latestVersion") if stable_info else None
        dev_version = dev_info.get("latestVersion") if dev_info else None

        if stable_version or dev_version:
            # 检查更新配置文件
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    if config.get('snooze_until'):
                        snooze_until = datetime.fromisoformat(config.get('snooze_until'))
                        if snooze_until > datetime.now():
                            _log.info("更新检查已被用户暂停，直到指定日期。")
                            return

            # 如果有更高版本的更新，提示用户
            if (stable_info and is_newer_version(CURRENT_VERSION, stable_version)[0]) or (dev_info and is_newer_version(CURRENT_VERSION, dev_version)[0]):
                await prompt_user_for_update(stable_info, dev_info)
            else:
                _log.info("当前版本已是最新，无需更新。")

    else:
        _log.warning("<WARN> 无法检查更新")

async def shutdown_and_update(zip_download_path):
    """
    关闭所有进程并执行更新。
    """
    _log.info("正在退出所有进程以便进行更新...")
    await asyncio.sleep(1)  # 等待其他任务完成

    # 获取当前操作系统类型
    current_os = platform.system()

    # 切换到项目根目录
    os.chdir(ROOT_DIR)

    # 启动更新脚本
    if current_os == "Windows":
        # Windows 下使用 PowerShell 启动新窗口运行 Python 脚本，并确保在根目录下
        subprocess.Popen(
            f'start powershell -Command "{sys.executable} {os.path.join(ROOT_DIR, "auto_update.py")} {zip_download_path}"',
            shell=True
        )

    elif current_os == "Linux":
        # Linux 下使用终端模拟器（如 gnome-terminal）确保在根目录下
        subprocess.Popen(
            f'gnome-terminal -- bash -c "cd {ROOT_DIR} && {sys.executable} auto_update.py {zip_download_path}"',
            shell=True
        )

    elif current_os == "Darwin":  # macOS 的系统标识符
        # macOS 使用 open -a Terminal 启动脚本
        subprocess.Popen(
            f'open -a Terminal "{sys.executable} {os.path.join(ROOT_DIR, "auto_update.py")} {zip_download_path}"',
            shell=True
        )

    else:
        _log.error(f"不支持的操作系统: {current_os}")
        return

    _log.info("更新脚本已启动，主程序即将退出。")

    # 使用 os._exit() 退出当前进程
    os._exit(0)

# 主测试
async def test():
 await shutdown_and_update("v1.2.0-Stable_827001.zip")

if __name__ == "__main__":
    asyncio.run(test())
