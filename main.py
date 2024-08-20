"""
AmyAlmond Project - Main.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/19 20:13
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.5 (Beta_820003)

Main.py 用于启动 AmyAlmond 机器人，加载配置文件和客户端
"""

import botpy

# bot_client.py模块 - <机器人客户端模块化文件>
from core.bot.bot_client import MyClient
# log.py模块 - <日志管理模块化文件>
from core.utils.logger import get_logger
# config.py模块 - <配置管理模块化文件>
from config import test_config
# plugins.py 模块 - <插件加载模块>
from core.plugins.plugins import load_plugins

# 获取 logger 对象
logger = get_logger()

if __name__ == "__main__":
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

    # 将插件列表存储到 client 实例中
    client.plugins = plugins

    # 注册插件的事件处理方法
    for plugin in plugins:
        client.register_event_handler(plugin.on_message, "on_message")
        client.register_event_handler(plugin.on_ready, "on_ready")
        logger.info(f"已加载插件: {plugin.name}")

    if "appid" not in test_config or "secret" not in test_config:
        logger.critical("机器人的 appid 或 secret 缺失,请检查 config.yaml 文件")
        exit(1)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
