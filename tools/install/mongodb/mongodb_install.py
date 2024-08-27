import ctypes
import os
import platform
import subprocess
import sys
import time
import urllib.request
import distro
from tqdm import tqdm

# 手动指定项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
# 将项目根目录添加到 Python 的搜索路径中
sys.path.append(project_root)
from tools.setup.mongodb.mongodb_setup_configs import configure_mongodb


def detect_os_and_version():
    os_name = platform.system()
    if os_name == "Windows":
        os_version = platform.version()
    elif os_name == "Linux":
        os_version = platform.release()
    elif os_name == "Darwin":
        os_version = platform.mac_ver()[0]
    else:
        os_name, os_version = None, None
    return os_name, os_version


def show_windows_message(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)


def download_and_install_mongodb(os_name: str, os_version: str):
    try:
        if os_name == "Windows":
            install_mongodb_on_windows()
        elif os_name == "Linux":
            install_mongodb_on_linux(os_version)
        elif os_name == "Darwin":
            install_mongodb_on_mac(os_version)
        else:
            print(f"! 不支持的操作系统：{os_name}")
            sys.exit(1)
    except Exception as e:
        print(f"! 在 {os_name} {os_version} 上安装MongoDB失败：{e}")
        sys.exit(1)


def show_progress_bar(url, path):
    response = urllib.request.urlopen(url)
    total_size = int(response.info().get('Content-Length').strip())
    block_size = 1024
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)

    with open(path, 'wb') as file:
        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            file.write(buffer)
            progress_bar.update(len(buffer))
    progress_bar.close()


def install_mongodb_on_windows():
    if check_mongodb_installed():
        print("> MongoDB 已经安装，无需再次安装。")
        return

    installer_path = "mongodb_installer.msi"

    try:
        print(f"> 检测路径：{os.path.abspath(installer_path)}")
        if os.path.exists(installer_path) and 500 * 1024 * 1024 <= os.path.getsize(installer_path) <= 650 * 1024 * 1024:
            print("> 检测到现有的 MongoDB 安装文件，可以直接安装。")
        else:
            print("> 未找到有效的 MongoDB 安装文件，正在从官方渠道下载...")
            download_url = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.2.0-signed.msi"
            show_progress_bar(download_url, installer_path)

        print("> 开始交互式安装 MongoDB...")

        print("> 提示用户安装即将开始...")
        show_windows_message(
            "MongoDB 安装提示",
            "即将打开 MongoDB 安装程序。"
        )

        subprocess.Popen(["msiexec", "/i", installer_path])

        time.sleep(3)
        show_windows_message(
            "MongoDB 安装提示",
            "您现在应该看到了 MongoDB 的安装程序弹出。\n"
            "请点击下面的 'Next' 按钮，然后点此消息的“确定”。"
        )

        time.sleep(1)

        # 勾选协议（英文）
        show_windows_message(
            "Mongodb 安装提示",
            "请勾选 'I accept the terms in the License Agreement'，然后点击 'Next'。\n"
            "最后点击此消息的“确定”。"
        )

        time.sleep(1)

        show_windows_message(
            "MongoDB 安装提示",
            "请选择 'Complete' 安装模式，点击 'Next'。"
            "\n最后点击此消息的“确定”。"
        )

        show_windows_message(
            "Mongodb 安装提示",
            "注意！在此步，不要勾选Install Mongodb compass，不要勾选！不要勾选！不要勾选！\n"
            "除非您挂了🪜，否则——不——要——勾——选！"
            "最后点击此消息的“确定”。"
        )

        time.sleep(1)

        show_windows_message(
            "Mongodb 安装提示",
            "继续 'Next'。\n"
            "最后点击此消息的“确定”。"
        )

        show_windows_message(
            "MongoDB 安装提示",
            "点击 'Install' 按钮开始安装。"
            "\n然后点击此消息的“确定”。"
        )

        time.sleep(10)

        show_windows_message(
            "MongoDB 安装提示",
            "安装可能需要一些时间，请耐心等待。（3-5分钟）\n安装完成后请点击 'Finish' 按钮。"
            "\n最后点击此消息的“确定”。"
            "\n如果卡了很长时间，请看看任务栏有没有Windows UAC弹窗。"
        )

        time.sleep(5)

        show_windows_message(
            "Mongodb 安装提示",
            "如果已经安装完成，请确定此弹窗，然后去控制台继续下一步"
        )

        input("如果您已完成安装，请按回车确认：")

        if check_mongodb_installed():
            print("> MongoDB 安装成功！您已打败全国99.9%的用户！")
            show_windows_message("MongoDB 安装成功", "MongoDB 已成功安装并正在运行。")
            print("> 帮助您启动配置脚本.....")
            # 启动配置脚本
            configure_mongodb()
        else:
            print("! MongoDB 安装失败。")
            show_windows_message("MongoDB 安装失败", "MongoDB 安装失败，请检查日志并尝试重新安装。")

    except Exception as e:
        print(f"! 交互式安装过程中发生了错误：{e}")
        show_windows_message("安装错误", f"安装过程中发生错误：{e}")


def check_mongodb_installed():
    try:
        if platform.system() == "Windows":
            # Windows 下的检测逻辑
            result = subprocess.run(["sc", "query", "MongoDB"], capture_output=True, text=True)
            print(f"> 检查 MongoDB 服务状态：{result.stdout}")
            if "RUNNING" in result.stdout:
                return True

            default_install_path = r"C:\Program Files\MongoDB\Server\7.0\bin"
            if os.path.exists(default_install_path):
                print(f"> 检查默认安装路径：{default_install_path}")
                return True

        elif platform.system() == "Linux":
            # Linux 下的检测逻辑
            result = subprocess.run(["which", "mongod"], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            result = subprocess.run(["systemctl", "is-active", "--quiet", "mongod"], capture_output=True)
            if result.returncode == 0:
                return True

        elif platform.system() == "Darwin":
            # macOS 下的检测逻辑
            result = subprocess.run(["brew", "services", "list"], capture_output=True, text=True)
            if "mongodb-community" in result.stdout and "started" in result.stdout:
                return True

        # 检查环境变量中是否能找到 mongo 命令
        result = subprocess.run(["mongo", "--version"], capture_output=True, text=True)
        if result.returncode == 0 and "MongoDB" in result.stdout:
            print(f"> 检查环境变量：{result.stdout}")
            return True

    except Exception as e:
        print(f"! 检查 MongoDB 安装状态时出错：{e}")

    return False


def install_mongodb_on_linux(os_version: str):
    try:
        distro_name = distro.id()
        print(f"> 检测到的Linux发行版: {distro_name} {os_version}")

        if "ubuntu" in distro_name or "debian" in distro_name:
            print("> 正在更新软件包列表并安装 MongoDB（基于Debian）...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "mongodb-org"], check=True)

        elif "centos" in distro_name or "rhel" in distro_name or "fedora" in distro_name:
            print("> 正在刷新缓存并安装 MongoDB（基于RHEL）...")
            subprocess.run(["sudo", "yum", "makecache"], check=True)
            subprocess.run(["sudo", "yum", "install", "-y", "mongodb-org"], check=True)

        else:
            print(f"! 未支持的 Linux 发行版: {distro_name}")
            sys.exit(1)

        print("> MongoDB安装完成。")

    except subprocess.CalledProcessError as e:
        print(f"! 安装MongoDB时出错：{e}")
        sys.exit(1)


def install_mongodb_on_mac(os_version: str):
    try:
        print(f"> 检测到的macOS版本: {os_version}")
        print("> 正在使用Homebrew安装MongoDB...")

        subprocess.run(["brew", "tap", "mongodb/brew"], check=True)
        subprocess.run(["brew", "install", "mongodb-community"], check=True)

        print("> MongoDB安装完成。")

    except subprocess.CalledProcessError as e:
        print(f"! 安装MongoDB时出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    os_name, os_version = detect_os_and_version()

    if not os_name or not os_version:
        print("! 无法检测操作系统或版本。")
        sys.exit(1)

    print(f"> 开始为 {os_name} {os_version} 安装MongoDB...")
    download_and_install_mongodb(os_name, os_version)
