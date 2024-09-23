"""
AmyAlmond Project - core/utils/file_handler.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

file_handler.py 用于监控系统提示文件的修改，并在文件发生变化时重新加载系统提示
"""

import watchdog.events

# logger.py模块 - <用于记录日志>
from .logger import get_logger
# config.py模块 - <获取系统提示文件的路径>
from config import SYSTEM_PROMPT_FILE

_log = get_logger()


class ConfigFileHandler(watchdog.events.FileSystemEventHandler):
    """
    监控系统提示文件修改的处理器类
    """

    def __init__(self, client):
        self.client = client

    def on_modified(self, event):
        """
        当系统提示文件被修改时，重新加载系统提示

        参数:
            event (watchdog.events.FileSystemEvent): 文件系统事件对象
        """
        if event.src_path.endswith(SYSTEM_PROMPT_FILE):
            self.client.reload_system_prompt()
            _log.info("<FILE MODIFIED> 系统提示文件已修改:")
            _log.info(f"   ↳ 文件路径: {event.src_path}")
            _log.info("    ↳ 操作: 已重新加载")
