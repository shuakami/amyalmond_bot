import socket
import sys
import subprocess
import time
import yaml
import psutil
from pathlib import Path
from pymongo import MongoClient, errors

# 配置文件路径
DEFAULT_WINDOWS_PATH = Path(r"C:\Program Files\MongoDB\Server\7.0\bin")
DEFAULT_LINUX_PATH = Path("/usr/bin/mongod")
DEFAULT_DB_PATH = Path(r"C:\data\db")
MONGO_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs/mongodb.yaml"


def detect_os_and_version():
    if sys.platform.startswith('win'):
        return "Windows", sys.getwindowsversion().platform_version
    elif sys.platform.startswith('linux'):
        return "Linux", subprocess.getoutput('uname -r')
    else:
        return sys.platform, "Unknown"


def is_port_open(host, port):
    """检查指定主机的端口是否开放"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()


def check_mongodb_installed():
    os_name, os_version = detect_os_and_version()

    if os_name == "Windows":
        return check_mongodb_installed_windows()
    elif os_name == "Linux":
        return check_mongodb_installed_linux()
    else:
        print(f"! 暂不支持的操作系统：{os_name}")
        sys.exit(1)


def check_mongodb_installed_windows():
    # 检查默认安装路径
    if DEFAULT_WINDOWS_PATH.exists():
        print(f"> 检测到MongoDB安装在默认路径：{DEFAULT_WINDOWS_PATH}")
        save_mongodb_config(DEFAULT_WINDOWS_PATH)
        return True

    # 尝试通过注册表检测
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\MongoDB\Server")
        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        install_path = Path(install_path)
        print(f"> 通过注册表检测到MongoDB安装路径：{install_path}")
        save_mongodb_config(install_path)
        return True
    except Exception as e:
        print(f"! 无法通过注册表检测到MongoDB安装路径：{e}")

    # 如果前面的方法都失败，提示用户手动输入路径
    print("! 请注意，如果你现在在执行main.py，而且你没有安装的话，下面的安装路径可以直接回车或者编一个哦~")
    user_path = input("无法自动检测到MongoDB安装路径，请手动输入：")
    user_path = Path(user_path)
    if user_path.exists():
        save_mongodb_config(user_path)
        return True
    else:
        print(f"! 输入的路径无效：{user_path}")
        sys.exit(1)


def check_mongodb_installed_linux():
    # 检查默认路径
    possible_paths = [DEFAULT_LINUX_PATH, Path("/usr/local/bin/mongod")]
    for path in possible_paths:
        if path.exists():
            print(f"> 检测到MongoDB安装在路径：{path}")
            save_mongodb_config(path)
            return True

    # 通过包管理器检测安装
    try:
        result = subprocess.run(["which", "mongod"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            install_path = Path(result.stdout.decode().strip())
            print(f"> 通过包管理器检测到MongoDB安装路径：{install_path}")
            save_mongodb_config(install_path)
            return True

        # 针对Ubuntu/Debian
        result = subprocess.run(["dpkg", "-l", "|", "grep", "mongodb"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("> 检测到MongoDB已通过dpkg安装")
            save_mongodb_config(Path("/usr/bin/mongod"))
            return True

        # 针对CentOS/RHEL
        result = subprocess.run(["rpm", "-qa", "|", "grep", "mongodb"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("> 检测到MongoDB已通过rpm安装")
            save_mongodb_config(Path("/usr/bin/mongod"))
            return True
    except Exception as e:
        print(f"! 无法通过包管理器检测到MongoDB安装路径：{e}")

    print("! 无法检测到MongoDB安装。请检查您的安装状态。")
    sys.exit(1)


def save_mongodb_config(install_path):
    # 确保配置目录存在
    if not MONGO_CONFIG_PATH.parent.exists():
        MONGO_CONFIG_PATH.parent.mkdir(parents=True)

    config = {"mongodb": {"install_path": str(install_path)}}
    with open(MONGO_CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    print(f"> MongoDB安装路径已保存到配置文件：{MONGO_CONFIG_PATH}")


def is_mongodb_running():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == "mongod.exe" or proc.info['name'] == "mongod":
            print("> MongoDB正在运行")
            return True
    print("> MongoDB未运行")
    return False


def start_mongodb():
    os_name, os_version = detect_os_and_version()

    if os_name == "Windows":
        return start_mongodb_windows()
    elif os_name == "Linux":
        return start_mongodb_linux()
    else:
        print(f"! 暂不支持的操作系统：{os_name}")
        sys.exit(1)


def start_mongodb_windows():
    try:
        with open(MONGO_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            install_path = Path(config['mongodb']['install_path'])

        db_path = DEFAULT_DB_PATH
        if not db_path.exists():
            db_path.mkdir(parents=True)  # 确保数据目录存在

        print("> 正在尝试启动MongoDB服务...")

        subprocess.Popen(
            [str(install_path / "mongod.exe"), "--dbpath", str(db_path), "--quiet"],
            creationflags=subprocess.DETACHED_PROCESS
        )
        # 等待MongoDB启动（检查端口是否开放）
        for _ in range(10):  # 尝试10次
            if is_port_open("127.0.0.1", 27017):
                print("> MongoDB已成功启动并监听端口27017。")
                return True
            time.sleep(1)

        print("! MongoDB启动失败，未能在预期端口上监听。")
        return False

    except Exception as e:
        print(f"! 启动MongoDB服务失败：{e}")
        return False


def start_mongodb_linux():
    try:
        print("> 正在尝试启动MongoDB服务...")

        # 检查 systemctl 是否可用
        if subprocess.run(["which", "systemctl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            subprocess.run(["sudo", "systemctl", "start", "mongod"], check=True)
        else:
            subprocess.run(["sudo", "service", "mongod", "start"], check=True)

        print("> MongoDB已成功启动。")
    except Exception as e:
        print(f"! 启动MongoDB服务失败：{e}")
        sys.exit(1)


def stop_all_mongodb_processes():
    print("> 正在停止所有MongoDB进程...")
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == "mongod.exe" or proc.info['name'] == "mongod":
            print(f"> 正在终止进程：{proc.info['pid']}")
            proc.terminate()

    print("> 所有MongoDB进程已停止。")


def check_mongodb_connection():
    try:
        print("> 正在测试与MongoDB的连接...")
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        # 尝试连接到MongoDB服务器
        client.server_info()  # 发送一个ping以确认连接成功
        print("> MongoDB连接成功！")
        return True
    except errors.ServerSelectionTimeoutError as err:
        print(f"! 无法连接到MongoDB服务器：{err}")
        return False
    except Exception as e:
        print(f"! 连接MongoDB时发生错误：{e}")
        return False


if __name__ == "__main__":
    print("> 开始MongoDB启动检测...")
    if not check_mongodb_installed():
        print("! MongoDB未安装或安装检测失败。")
        sys.exit(1)

    if not is_mongodb_running():
        print("> MongoDB未运行，尝试启动...")

    if not is_mongodb_running():
        print("MongoDB未运行，尝试启动...")
        stop_all_mongodb_processes()
        start_mongodb()

    if not check_mongodb_connection():
        print("MongoDB启动失败或无法连接，请检查安装和配置。")
        sys.exit(1)

    print("MongoDB已成功启动并连接！系统准备就绪。")
    # 退出此进程
    sys.exit(0)
