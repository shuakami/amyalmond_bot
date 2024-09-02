"""
AmyAlmond Project - Main.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.4 (Alpha_902002)

Main.py 用于启动 AmyAlmond 机器人，加载配置文件和客户端
"""

import botpy
import sys
from core.bot.bot_client import MyClient
from core.utils.logger import get_logger, handle_critical_error
from config import test_config
from core.plugins.plugin_manager import PluginManager

# 获取 logger 对象
logger = get_logger()


def main():
    try:
        # 启动标志
        print("")
        print("     _                       _    _                           _ ")
        print("    / \\   _ __ ___  _   _   / \\  | |_ __ ___   ___  _ __   __| |")
        print("   / _ \\ | '_ ` _ \\| | | | / _ \\ | | '_ ` _ \\ / _ \\| '_ \\ / _` |")
        print("  / ___ \\| | | | | | |_| |/ ___ \\| | | | | | | (_) | | | | (_| |")
        print(" /_/   \\_|_| |_| |_|\\__, /_/   \\_|_|_| |_| |_|\\___/|_| |_|\\__,_|")
        print("                    |___/                                       ")
        print("")

        logger.info(">>> SYSTEM INITIATING...")
        intents = botpy.Intents(public_messages=True, public_guild_messages=True)
        client = MyClient(intents=intents)

        # 创建插件管理器实例
        plugin_manager = PluginManager(client)
        logger.info(">>> PLUGIN MANAGER INITIALIZED")

        # 加载并注册插件
        plugin_manager.register_plugins()
        logger.info("   ↳ 插件已成功加载并注册")

        # 将插件管理器存储到 client 实例中
        client.plugin_manager = plugin_manager

        # 检查配置文件中的必要参数
        if "appid" not in test_config or "secret" not in test_config:
            logger.critical("<ERROR> 机器人的 appid 或 secret 缺失")
            logger.critical("   ↳ 请检查 config.yaml 文件")
            sys.exit(1)

        logger.info(">>> CLIENT RUNNING...")
        client.run(appid=test_config["appid"], secret=test_config["secret"])

    except Exception as e:
        # 捕获所有未处理的异常并记录
        logger.error(f"<ERROR> 在 main 中捕获到未处理的异常: {e}", exc_info=True)
        handle_critical_error(sys.exc_info())


if __name__ == "__main__":
    main()
