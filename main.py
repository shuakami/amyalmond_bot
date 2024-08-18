"""
AmyAlmond Project - Main.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/17 16:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.1.0 (Alpha_817001)

Main.py 用于启动 AmyAlmond 机器人，加载配置文件和客户端
"""

import botpy

# bot_client.py模块 - <机器人客户端模块化文件>
from bot_client import MyClient, _log
# config.py模块 - <配置管理模块化文件>
from config import test_config


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
    if "appid" not in test_config or "secret" not in test_config:
        _log.critical("机器人的 appid 或 secret 缺失,请检查 config.yaml 文件")
        exit(1)
    client.run(appid=test_config["appid"], secret=test_config["secret"])