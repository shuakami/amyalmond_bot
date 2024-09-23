import logging
import os
import platform
import shutil
import sys
import traceback
import zipfile
from logging.handlers import RotatingFileHandler
from datetime import datetime
import yaml

# 初始化日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 读取配置文件
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs", "config.yaml")

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)
else:
    config = {}

# 获取日志级别和调试模式配置
LOG_LEVEL = config.get('log_level', 'INFO').upper()
DEBUG_MODE = config.get('debug', False)

# 自定义日志格式
class CustomFormatter(logging.Formatter):
    """自定义日志格式化器，应用特殊格式和颜色"""

    FORMATS = {
        logging.DEBUG: "[DEBUG]   {module}:{lineno} [{funcName}]    {message}",
        logging.INFO: "[INFO]   {module}:{lineno} [{funcName}]    {message}",
        logging.WARNING: "[WARNING]   {module}:{lineno} [{funcName}]    {message}",
        logging.ERROR: "[ERROR]   {module}:{lineno} [{funcName}]    {message}",
        logging.CRITICAL: "[CRITICAL]   {module}:{lineno} [{funcName}]    {message}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.DEBUG])
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)

# 获取logger对象
def get_logger():
    """获取并配置一个日志记录器"""
    logger = logging.getLogger("bot_logger")

    # 确保日志配置只进行两次
    if not getattr(logger, '_initialized', False):
        # 设置日志级别
        log_level = getattr(logging, LOG_LEVEL, logging.INFO)
        logger.setLevel(log_level)

        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # 文件处理器
        log_file = os.path.join(LOG_DIR, "bot.log")
        file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
        file_handler.setFormatter(CustomFormatter())
        logger.addHandler(file_handler)

    return logger

# 捕获并处理严重错误
def handle_critical_error(exc_info):
    """捕获严重错误，记录并打包相关文件"""
    logger = get_logger()
    logger.critical("捕获到未处理的异常", exc_info=exc_info)

    error_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_dir = os.path.join(LOG_DIR, f"error_logs_{error_time}")
    os.makedirs(error_log_dir, exist_ok=True)

    # 记录错误堆栈信息
    error_file = os.path.join(error_log_dir, "error.log")
    with open(error_file, 'w', encoding='utf-8') as f:
        traceback.print_exception(*exc_info, file=f)

    # 打包日志文件
    zip_file = os.path.join(LOG_DIR, f"error_{error_time}.zip")
    with zipfile.ZipFile(zip_file, 'w') as z:
        for folder_name, _, filenames in os.walk(error_log_dir):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                z.write(file_path, os.path.relpath(file_path, error_log_dir))

    # 删除原始错误文件
    shutil.rmtree(error_log_dir)
    logger.info(f"错误日志已打包: {zip_file}")

    # 打开打包zip路径
    if platform.system() == "Windows":
        os.system(f"start {zip_file}")
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open {zip_file}")
    elif platform.system() == "Linux":
        os.system(f"xdg-open {zip_file}")

# 设置全局未处理异常处理器
def setup_global_exception_handler():
    """设置全局未处理异常的处理器"""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if not issubclass(exc_type, KeyboardInterrupt):
            handle_critical_error((exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

# 获取实时日志
def get_latest_logs():
    """获取整个日志文件的最新内容"""
    log_file_path = os.path.join(LOG_DIR, "bot.log")
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        return []

# 初始化全局日志记录器
_log = get_logger()

# 在启动时设置全局异常处理器
setup_global_exception_handler()
