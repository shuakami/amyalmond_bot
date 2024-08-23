import sys
import os
import subprocess
from pymongo import MongoClient, errors
from elasticsearch import Elasticsearch, exceptions

from core.db.setup.elasticsearch.elasticsearch_setup import check_elasticsearch_connection
from core.db.setup.mongodb.mongodb_setup import check_mongodb_connection
from core.utils.logger import get_logger
from core.utils.utils import detect_os_and_version
from config import MONGODB_URI, MONGODB_USERNAME, MONGODB_PASSWORD, ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, \
    ELASTICSEARCH_PASSWORD

_log = get_logger()


def run_external_script(script_relative_path):
    """分离运行外部脚本"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.abspath(os.path.join(script_dir, script_relative_path))
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        _log.error(f"执行 {script_path} 时出错: {e}")
        return False
    return True


def check_mongodb():
    """检查MongoDB连接，如果失败则尝试启动并重试连接"""
    try:
        _log.info("<---------------------------------------->")
        _log.info("正在检查MongoDB连接...")
        _log.info("如果你没有安装，并且接下来看到一堆报错，那是正常的。")
        client = MongoClient(MONGODB_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD,
                             serverSelectionTimeoutMS=5000)
        client.server_info()  # 发送一个ping以确认连接成功
        _log.info("MongoDB连接正常。")
        return True
    except errors.ServerSelectionTimeoutError:
        _log.warning("无法连接到MongoDB，尝试启动MongoDB服务...")
        if not run_external_script("setup/mongodb/mongodb_setup.py"):
            _log.error("启动MongoDB失败，尝试重新安装MongoDB...")
            os_name, os_version = detect_os_and_version()
            if not run_external_script("install/mongodb/mongodb_install.py"):
                _log.error("重新安装MongoDB后仍无法启动，请检查系统配置。")
                return False
            if not run_external_script("setup/mongodb/mongodb_setup.py"):
                _log.error("启动MongoDB失败，请检查系统配置。")
                return False
        return check_mongodb_connection()
    except Exception as e:
        _log.error(f"MongoDB连接检测时发生错误：{e}")
        return False


def check_elasticsearch():
    """检查Elasticsearch连接，如果失败则尝试启动并重试连接"""
    try:
        _log.info("正在检查Elasticsearch连接...")
        _log.info("如果你没有安装，并且接下来看到一堆报错，那是正常的。")
        es = Elasticsearch(
            ELASTICSEARCH_URL,
            basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
            request_timeout=10,
            verify_certs=False
        )
        es.info()  # 测试连接
        _log.info("Elasticsearch连接正常。")
        return True
    except exceptions.ConnectionError:
        _log.warning("无法连接到Elasticsearch，尝试启动Elasticsearch服务...")
        if not run_external_script("setup/elasticsearch/elasticsearch_setup.py"):
            _log.error("启动Elasticsearch失败，尝试重新安装Elasticsearch...")
            os_name, os_version = detect_os_and_version()
            if not run_external_script("install/elasticsearch/elasticsearch_install.py"):
                _log.error("重新安装Elasticsearch后仍无法启动，请检查系统配置。")
                return False
            if not run_external_script("setup/elasticsearch/elasticsearch_setup.py"):
                _log.error("启动Elasticsearch失败，请检查系统配置。")
                return False
        return check_elasticsearch_connection()
    except Exception as e:
        _log.error(f"Elasticsearch连接检测时发生错误：{e}")
        return False


def check_databases():
    """检查所有数据库的状态"""
    mongodb_status = check_mongodb()
    elasticsearch_status = check_elasticsearch()

    if mongodb_status and elasticsearch_status:
        _log.info("所有数据库连接正常。")
        _log.info("<---------------------------------------->")
        return True
    else:
        _log.error("数据库连接异常，请检查日志以获取详细信息。")
        _log.info("<---------------------------------------->")
        return False


if __name__ == "__main__":
    try:
        check_databases()
        sys.exit(0)
    except SystemExit as e:
        # 捕获退出异常并确保退出
        sys.exit(e.code)
    except Exception as e:
        _log.error(f"运行时发生未处理的异常：{e}")
        sys.exit(1)
