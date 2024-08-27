import socket
import sys
import subprocess
import time
import yaml
import psutil
from pathlib import Path

# 配置文件路径
DEFAULT_WINDOWS_PATH = Path(r"C:\Elasticsearch\8.15.0\elasticsearch-8.15.0\bin")
DEFAULT_LINUX_PATH = Path("/usr/share/elasticsearch/bin")
ELASTIC_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs/elasticsearch.yaml"


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


def check_elasticsearch_installed():
    os_name, os_version = detect_os_and_version()

    if os_name == "Windows":
        return check_elasticsearch_installed_windows()
    elif os_name == "Linux":
        return check_elasticsearch_installed_linux()
    else:
        print(f"! 暂不支持的操作系统：{os_name}")
        sys.exit(1)


def check_elasticsearch_installed_windows():
    # 检查默认安装路径
    if DEFAULT_WINDOWS_PATH.exists():
        print(f"> 检测到Elasticsearch安装在默认路径：{DEFAULT_WINDOWS_PATH}")
        save_elasticsearch_config(DEFAULT_WINDOWS_PATH)
        return True

    # 提示用户手动输入路径
    print("! 请注意，如果你现在在执行main.py，而且你没有安装的话 下面的安装路径可以直接回车或者编一个哦~")
    user_path = input("无法自动检测到Elasticsearch安装路径，请手动输入：")
    user_path = Path(user_path)
    if user_path.exists():
        save_elasticsearch_config(user_path)
        return True
    else:
        print(f"! 输入的路径无效：{user_path}")
        sys.exit(1)


def check_elasticsearch_installed_linux():
    # 检查默认路径
    possible_paths = [DEFAULT_LINUX_PATH, Path("/usr/local/elasticsearch/bin")]
    for path in possible_paths:
        if path.exists():
            print(f"> 检测到Elasticsearch安装在路径：{path}")
            save_elasticsearch_config(path)
            return True

    # 通过包管理器检测安装
    try:
        result = subprocess.run(["which", "elasticsearch"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            install_path = Path(result.stdout.decode().strip())
            print(f"> 通过包管理器检测到Elasticsearch安装路径：{install_path}")
            save_elasticsearch_config(install_path)
            return True
    except Exception as e:
        print(f"! 无法通过包管理器检测到Elasticsearch安装路径：{e}")

    print("! 无法检测到Elasticsearch安装。请检查您的安装状态。")
    sys.exit(1)


def save_elasticsearch_config(install_path):
    # 确保配置目录存在
    if not ELASTIC_CONFIG_PATH.parent.exists():
        ELASTIC_CONFIG_PATH.parent.mkdir(parents=True)

    config = {"elasticsearch": {"install_path": str(install_path)}}
    with open(ELASTIC_CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    print(f"> Elasticsearch安装路径已保存到配置文件：{ELASTIC_CONFIG_PATH}")


def is_elasticsearch_running():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == "elasticsearch":
            print("> Elasticsearch正在运行")
            return True
    print("> Elasticsearch未运行")
    return False


def start_elasticsearch():
    os_name, os_version = detect_os_and_version()

    if os_name == "Windows":
        return start_elasticsearch_windows()
    elif os_name == "Linux":
        return start_elasticsearch_linux()
    else:
        print(f"! 暂不支持的操作系统：{os_name}")
        sys.exit(1)


def start_elasticsearch_windows():
    try:
        with open(ELASTIC_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            install_path = Path(config['elasticsearch']['install_path'])

        print("> 正在尝试启动Elasticsearch服务...")

        # 直接运行 elasticsearch.bat 并确保它在后台运行
        subprocess.Popen([str(install_path / "elasticsearch.bat")], creationflags=subprocess.CREATE_NEW_CONSOLE)

        # 等待Elasticsearch启动（检查端口是否开放）
        for _ in range(20):  # 尝试20次
            if is_port_open("127.0.0.1", 9200):
                print("> Elasticsearch已成功启动并监听端口9200。")
                return True
            time.sleep(2)

        print("! Elasticsearch启动失败，未能在预期端口上监听。")
        return False

    except Exception as e:
        print(f"! 启动Elasticsearch服务失败：{e}")
        return False


def start_elasticsearch_linux():
    try:
        print("> 正在尝试启动Elasticsearch服务...")

        # 检查 systemctl 是否可用
        if subprocess.run(["which", "systemctl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            subprocess.run(["sudo", "systemctl", "start", "elasticsearch"], check=True)
        else:
            subprocess.run(["sudo", "service", "elasticsearch", "start"], check=True)

        print("> Elasticsearch已成功启动。")
    except Exception as e:
        print(f"! 启动Elasticsearch服务失败：{e}")
        sys.exit(1)


def stop_all_elasticsearch_processes():
    print("> 正在停止所有Elasticsearch相关进程...")

    # 定义要终止的进程名称列表
    elasticsearch_related_processes = ["elasticsearch", "controller.exe", "OpenJDK Platform binary", "java.exe"]

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in elasticsearch_related_processes:
                print(f"> 正在终止进程：{proc.info['name']} (PID: {proc.info['pid']})")
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"! 无法终止进程：{proc.info['name']} (PID: {proc.info['pid']}) - 权限不足或进程已结束。")
            continue

    print("> 所有Elasticsearch相关进程终止命令已发送。")


def check_elasticsearch_connection():
    try:
        print("> 正在测试Elasticsearch是否已启动...")
        # 通过ping本地端口检查服务是否启动
        if is_port_open("127.0.0.1", 9200):
            print("> Elasticsearch已经成功启动并在9200端口监听。")
            return True
        else:
            print("! Elasticsearch未能在9200端口启动。")
            return False
    except Exception as e:
        print(f"! 检查Elasticsearch连接时发生错误：{e}")
        return False


if __name__ == "__main__":
    print("> 开始Elasticsearch启动检测...")

    # 添加连接测试
    if check_elasticsearch_connection():
        print("> Elasticsearch已经在运行，连接正常。")
        sys.exit(0)

    if not check_elasticsearch_installed():
        print("! Elasticsearch未安装或安装检测失败。")
        sys.exit(1)

    if not is_elasticsearch_running():
        print("> Elasticsearch未运行，尝试启动...")
        stop_all_elasticsearch_processes()
        start_elasticsearch()

    if not check_elasticsearch_connection():
        print("! Elasticsearch启动失败或无法连接，请检查安装和配置。")
        sys.exit(1)

    print("> Elasticsearch准备就绪。")
    sys.exit(0)
