"""
AmyAlmond Project - Main.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/22 22:45
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.2.0 (Alpha_823006)

Main.py 用于启动 AmyAlmond 机器人，加载配置文件和客户端
"""

import botpy
import sys
from core.utils.logger import get_logger
from config import test_config
from core.bot.bot_client import MyClient
from core.plugins.plugins import load_plugins
from core.db.db_status_checker import check_databases

# 获取 logger 对象
logger = get_logger()


def start_bot():
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

    # 加载插件
    plugins = load_plugins(client)
    client.plugins = plugins

    # 注册插件的事件处理方法
    for plugin in plugins:
        client.register_event_handler(plugin.on_message, "on_message")
        client.register_event_handler(plugin.on_ready, "on_ready")
        logger.info(f"已加载插件: {plugin.name}")

    # 验证配置
    if "appid" not in test_config or "secret" not in test_config:
        logger.critical("机器人的 appid 或 secret 缺失,请检查 config.yaml 文件")
        sys.exit(1)

    # 启动机器人客户端
    client.run(appid=test_config["appid"], secret=test_config["secret"])


if __name__ == "__main__":
    try:
        # 检查数据库状态
        if not check_databases():
            logger.critical("<AmyAlmond_安全> 数据库连接失败，程序将安全退出。")
            sys.exit(1)

        # 如果数据库检查通过，启动机器人
        start_bot()

    except Exception as e:
        logger.critical(f"<AmyAlmond_Core> 主程序发生未处理的异常: {e}")
        sys.exit(1)
