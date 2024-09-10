import asyncio
from fastapi import WebSocket
from typing import List
import logging
from starlette.websockets import WebSocketDisconnect

from core.utils.logger import get_latest_logs

logger = logging.getLogger("bot_logger")


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """处理新的 WebSocket 连接"""
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"新的 WebSocket 连接已建立，当前连接总数: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """处理 WebSocket 断开连接"""
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket 连接已断开，当前连接总数: {len(self.active_connections)}")

    async def push_logs_to_websocket(self, websocket: WebSocket):
        """定期读取日志文件并推送给WebSocket客户端"""
        last_read_position = 0
        try:
            while True:
                latest_logs = get_latest_logs()

                if latest_logs:
                    new_logs = "".join(latest_logs[last_read_position:])
                    if new_logs:  # 仅在有新日志时发送
                        await websocket.send_text(new_logs)
                        last_read_position = len(latest_logs)

                await asyncio.sleep(2)  # 每2秒推送一次
        except WebSocketDisconnect:
            logger.info("客户端已断开连接，停止日志推送")
        except Exception as e:
            logger.error(f"推送日志过程中出现错误: {e}")
            await self.disconnect(websocket)


websocket_manager = WebSocketManager()
