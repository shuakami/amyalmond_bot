"""
AmyAlmond Project - core/utils/logger.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.2.3 (Alpha_829001)

logger.py 用于智能日志记录，自动捕获并打包。
"""

import logging
import os
import re
import sys
import gzip
import shutil
import traceback
import zipfile
from logging.handlers import RotatingFileHandler
from datetime import datetime
import yaml
import inspect
from colorama import init, Fore, Style

# Initialize colorama for colored logs
init(autoreset=True)


class CustomFormatter(logging.Formatter):
    """自定义日志格式化器，应用特殊格式和颜色"""

    format_prefix = "< SYSTEM START > \n========================================================================\n"
    format_suffix = "\n< SYSTEM END > \n========================================================================"

    FORMATS = {
        logging.DEBUG: f"{Fore.CYAN}[DEBUG]   {{module}}:{{lineno}} [{{funcName}}]    {{message}}{Style.RESET_ALL}",
        logging.INFO: f"{Fore.GREEN}✅ [INFO]   {{module}}:{{lineno}} [{{funcName}}]    {{message}}{Style.RESET_ALL}",
        logging.WARNING: f"{Fore.YELLOW}⚠️ [WARNING]   {{module}}:{{lineno}} [{{funcName}}]    {{message}}{Style.RESET_ALL}",
        logging.ERROR: f"{Fore.RED}❌ [ERROR]   {{module}}:{{lineno}} [{{funcName}}]    {{message}}{Style.RESET_ALL}",
        logging.CRITICAL: f"{Fore.RED}🔥 [CRITICAL] {{module}}:{{lineno}} [{{funcName}}]    {{message}}{Style.RESET_ALL}",
    }

    def format(self, record):
        # Check if the log should use the custom format
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.DEBUG])
        formatter = logging.Formatter(log_fmt)
        formatted_log = formatter.format(record)

        # If the log is critical, wrap with system start and end
        if record.levelno == logging.CRITICAL:
            formatted_log = f"{self.format_prefix}{formatted_log}{self.format_suffix}"

        return formatted_log


class GZipRotator:
    """自定义日志文件压缩器，将旧日志文件压缩为.gz格式"""

    def __call__(self, source, dest):
        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)


def handle_critical_error(exc_info):
    """
    捕获严重错误，记录详细信息并打包相关文件。
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    error_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_dir = os.path.join(project_root, "error_logs", error_time)
    os.makedirs(error_log_dir, exist_ok=True)

    # 记录错误堆栈信息
    error_file = os.path.join(error_log_dir, "error.log")
    with open(error_file, 'w', encoding='utf-8') as f:
        traceback.print_exception(*exc_info, file=f)

    # 记录前后200行的日志
    capture_log_context(project_root, error_log_dir)

    # 记录配置文件信息
    capture_config_info(project_root, error_log_dir)

    # 捕获控制台日志
    capture_console_log(project_root, error_log_dir)

    # 延迟导入log_db_status.py
    from core.db.log_db_status import log_elasticsearch_status, log_mongodb_status

    # 记录数据库状态信息
    log_elasticsearch_status(error_log_dir)
    log_mongodb_status(error_log_dir)

    # 打包日志文件
    zip_file = os.path.join(project_root, "error_logs",
                            f"请提交这个压缩包到amyalmond_bot官方issue_error_{error_time}.zip")
    with zipfile.ZipFile(zip_file, 'w') as z:
        for folder_name, subfolders, filenames in os.walk(error_log_dir):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                z.write(file_path, os.path.relpath(file_path, error_log_dir))

    # 删除原始错误文件
    shutil.rmtree(error_log_dir)

    # 提示用户上传问题，并打开日志所在目录
    _log.critical(f"{Fore.RED}🔥 严重错误发生，错误日志已打包：{zip_file}")
    _log.info(f"{Fore.BLUE}🔗 请提交问题至：https://github.com/shuakami/amyalmond_bot/issues/new")
    open_log_directory(zip_file)


def capture_log_context(project_root, error_log_dir):
    """
    捕获发生错误前后的日志上下文信息
    """
    logs_dir = os.path.join(project_root, "logs")
    for log_file in os.listdir(logs_dir):
        if log_file.endswith(".log"):
            log_path = os.path.join(logs_dir, log_file)
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            log_context_file = os.path.join(error_log_dir, f"{log_file}.amy.error")
            with open(log_context_file, 'w', encoding='utf-8') as f:
                f.write("日志上下文信息（发生错误前后200行）：\n")
                if len(lines) > 400:
                    f.writelines(lines[-400:])  # 最后400行，包含前后200行
                else:
                    f.writelines(lines)


def capture_console_log(project_root, error_log_dir):
    """
    捕获控制台日志输出
    """
    console_log_file = os.path.join(error_log_dir, "console.log")
    with open(console_log_file, 'w', encoding='utf-8') as f:
        f.write("控制台日志输出：\n")
        f.write("".join(console_output))  # 将全局变量 console_output 中的内容写入文件


def capture_config_info(project_root, error_log_dir):
    """
    捕获并打码配置文件中的敏感信息
    """
    config_file = os.path.join(project_root, "configs", "config.yaml")
    config_backup_file = os.path.join(error_log_dir, "config.yaml")
    with open(config_file, 'r', encoding='utf-8') as f:
        config_content = f.read()

    # 使用正则表达式打码敏感信息
    config_content = re.sub(r'(\w+_secret: ")(\w{4})(\w+)(")', r'\1\2********\4', config_content)
    config_content = re.sub(r'(\w+_password: ")(\w{2})(\w+)(")', r'\1\2****\4', config_content)
    config_content = re.sub(r'(appid: ")(\w{4})(\w+)(")', r'\1\2********\4', config_content)
    config_content = re.sub(r'(secret: ")(\w{4})(\w+)(")', r'\1\2********\4', config_content)
    config_content = re.sub(r'(openai_secret: ")(sk-[\w]{4})([\w]+)(")', r'\1\2********\4', config_content)

    with open(config_backup_file, 'w', encoding='utf-8') as f:
        f.write(config_content)


def open_log_directory(zip_file):
    """
    打开日志文件所在目录
    """
    log_dir = os.path.dirname(zip_file)
    if sys.platform == "win32":
        os.startfile(log_dir)
    elif sys.platform == "darwin":
        os.system(f"open {log_dir}")
    elif sys.platform == "linux":
        os.system(f"xdg-open {log_dir}")
    else:
        _log.error(f"无法识别的平台: {sys.platform}，请手动打开日志目录。")


def get_logger():
    """
    获取一个日志记录器对象，自动识别调用者的模块名称
    """
    caller_frame = inspect.stack()[1]
    module_name = inspect.getmodule(caller_frame[0]).__name__

    logger = logging.getLogger(module_name)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    log_level = "INFO"
    debug_mode = False
    log_dir = os.path.join(project_root, "logs")
    log_file = os.path.join(log_dir, f"{module_name}.log")
    max_log_size = 10 * 1024 * 1024  # 10 MB
    backup_count = 5  # 保留5个旧日志文件

    os.makedirs(log_dir, exist_ok=True)

    try:
        config_path = os.path.join(project_root, "configs", "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            log_level = config.get("log_level", "INFO").upper()
            debug_mode = config.get("debug", False)
    except Exception as e:
        logger.warning(f"{Fore.YELLOW}⚠️ 无法读取配置文件，使用默认日志配置: {e}")

    logger.setLevel(getattr(logging, log_level, logging.INFO))

    if debug_mode:
        logger.setLevel(logging.DEBUG)

    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_log_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(CustomFormatter())
        logger.addHandler(file_handler)
        file_handler.rotator = GZipRotator()

        # 添加控制台日志记录
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)

        # 捕获控制台输出的日志
        global console_output
        console_output = []

        class ConsoleLogCapture:
            def write(self, msg):
                console_output.append(msg)

            def flush(self):
                pass

        sys.stdout = sys.stderr = ConsoleLogCapture()

    except Exception as e:
        logger.error(f"{Fore.RED}❌ 无法添加文件处理器: {e}")

    return logger


def setup_global_exception_handler():
    """
    设置全局未处理异常的处理器，捕获异常并触发智能日志系统。
    """

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        _log.critical(f"{Fore.RED}Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        handle_critical_error((exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


# 全局logger对象
_log = get_logger()

# 在启动时设置全局异常处理器
setup_global_exception_handler()
