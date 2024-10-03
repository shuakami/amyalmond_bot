"""
AmyAlmond Project - Main.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

Main.py 用于启动 AmyAlmond 机器人，加载配置文件和客户端
"""

import asyncio
import subprocess
import sys
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import botpy
from core.api.routes import router as api_router
from core.bot.bot_client import MyClient
from core.utils.logger import get_logger, handle_critical_error
from config import test_config

logger = get_logger()

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)

async def check_port_occupied(port):
    """
    异步检查指定端口是否被占用。
    """
    try:
        netstat_command = ["netstat", "-an"]
        proc = await asyncio.create_subprocess_exec(
            *netstat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, _ = await proc.communicate()
        return str(port) in output.decode()
    except Exception as e:
        logger.error(f"检查端口 {port} 时出错: {e}")
        return True

async def kill_process_by_port(port):
    """
    异步结束占用指定端口的进程。
    """
    try:
        netstat_command = ["netstat", "-an"]
        proc = await asyncio.create_subprocess_exec(
            *netstat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, _ = await proc.communicate()
        for line in output.decode().splitlines():
            if f":{port}" in line and "LISTEN" in line:
                pid = int(line.split()[-1])
                taskkill_command = ["kill", "-9", str(pid)]
                await asyncio.create_subprocess_exec(*taskkill_command)
                logger.info(f"已结束占用端口 {port} 的进程 (PID: {pid})")
                return
    except Exception as e:
        logger.error(f"结束端口 {port} 的进程时出错: {e}")

async def start_uvicorn():
    """
    使用异步启动 Uvicorn 服务器
    """
    port = 10417
    max_retries = 5
    retry_delay = 2  # 减少重试间隔以加快启动

    for i in range(max_retries):
        if not await check_port_occupied(port):
            uvicorn_command = [
                sys.executable, "-m", "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--log-config", "uvicorn_log_config.json"
            ]
            subprocess.Popen(uvicorn_command)
            logger.info("Uvicorn server started in a separate process.")
            return
        else:
            await kill_process_by_port(port)
            logger.info(f"端口 {port} 被占用，已尝试结束占用进程，重试 ({i + 1}/{max_retries})...")
            await asyncio.sleep(retry_delay)

    logger.error(f"尝试启动 Uvicorn 服务器失败，端口 {port} 一直被占用。")

def run_bot():
    """
    运行机器人客户端，保留同步逻辑
    """
    try:
        intents = botpy.Intents(public_messages=True, public_guild_messages=True)
        client = MyClient(intents=intents)

        logger.info(">>> PLUGIN MANAGER INITIALIZED")
        logger.info("   ↳ 插件已成功加载并注册")

        # 检查配置文件中的必要参数
        if "appid" not in test_config or "secret" not in test_config:
            logger.critical("<ERROR> 机器人的 appid 或 secret 缺失")
            logger.critical("   ↳ 请检查 config.yaml 文件")
            sys.exit(1)

        logger.info(">>> CLIENT RUNNING...")
        client.run(appid=test_config["appid"], secret=test_config["secret"])

    except Exception as e:
        # 捕获所有未处理的异常并记录
        logger.error(f"<ERROR> 在 run_bot 中捕获到未处理的异常: {e}", exc_info=True)
        handle_critical_error(sys.exc_info())

async def main():
    print("")
    print("     _                       _    _                           _ ")
    print("    / \\   _ __ ___  _   _   / \\  | |_ __ ___   ___  _ __   __| |")
    print("   / _ \\ | '_ ` _ \\| | | | / _ \\ | | '_ ` _ \\ / _ \\| '_ \\ / _` |")
    print("  / ___ \\| | | | | | |_| |/ ___ \\| | | | | | | (_) | | | | (_| |")
    print(" /_/   \\_|_| |_| |_|\\__, /_/   \\_|_|_| |_| |_|\\___/|_| |_|\\__,_|")
    print("                    |___/                                       ")
    print("")

    logger.info(">>> SYSTEM INITIATING...")

    # 并行启动 Uvicorn 服务器和机器人客户端
    uvicorn_task = asyncio.create_task(start_uvicorn())

    # 运行机器人客户端（同步）
    bot_task = asyncio.to_thread(run_bot)

    await asyncio.gather(uvicorn_task, bot_task)

if __name__ == "__main__":
    # 在主线程中创建事件循环
    asyncio.run(main())
