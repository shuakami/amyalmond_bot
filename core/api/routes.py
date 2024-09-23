from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.api.controllers import plugin_controller, configs_controller, db_controller, es_controller
from core.api.websocket_manager import websocket_manager
from core.utils.logger import get_logger
import asyncio

router = APIRouter()
logger = get_logger()

# 普通API插件管理
router.include_router(plugin_controller.router, prefix="/plugins", tags=["plugins"])
router.include_router(configs_controller.router, prefix="/configs", tags=["configs"])
router.include_router(db_controller.router, prefix="/db", tags=["db"])
router.include_router(es_controller.router, prefix="/es", tags=["es"])

# WebSocket日志推送
@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("新的WebSocket连接尝试")
    await websocket_manager.connect(websocket)
    logger.info(f"WebSocket连接成功建立: {websocket.client}")

    # 启动后台任务定期推送日志
    log_task = asyncio.create_task(websocket_manager.push_logs_to_websocket(websocket))

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"收到WebSocket消息: {data[:50]}...")  # 记录消息的前50个字符
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {websocket.client}")
    finally:
        # 断开连接时取消日志推送任务
        log_task.cancel()
        await websocket_manager.disconnect(websocket)

