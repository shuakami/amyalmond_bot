import ctypes
import shutil
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
from tools.setup.elasticsearch.elasticsearch_configs import configure_elasticsearch


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


def download_and_install_elasticsearch(os_name: str, os_version: str):
    try:
        if os_name == "Windows":
            install_elasticsearch_on_windows()
        elif os_name == "Linux":
            install_elasticsearch_on_linux(os_version)
        elif os_name == "Darwin":
            install_elasticsearch_on_mac(os_version)
        else:
            print(f"! 不支持的操作系统：{os_name}")
            sys.exit(1)
    except Exception as e:
        print(f"! 在 {os_name} {os_version} 上安装Elasticsearch失败：{e}")
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


def install_elasticsearch_on_windows():
    if check_elasticsearch_installed():
        print("> Elasticsearch 已经安装，无需再次安装。")
        return

    installer_zip = "elasticsearch_install.zip"
    install_dir = "C:\\Elasticsearch\\8.15.0"  # 更改解压路径为非系统管理的路径

    try:
        # 如果文件大小在380~520MB，则判定已经有
        if os.path.exists(installer_zip) and 380 * 1024 * 1024 < os.path.getsize(installer_zip) < 520 * 1024 * 1024:
            print("> 检测到现有的 Elasticsearch ZIP 文件，可以直接安装。")
        else:
            print("> 未找到有效的 Elasticsearch ZIP 文件，正在从官方渠道下载...")
            download_url = "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.15.0-windows-x86_64.zip"
            show_progress_bar(download_url, installer_zip)

            # 解压前先检查有没有C:\\Elasticsearch\\8.15.0，如果有，先删除C:\\Elasticsearch
            if os.path.exists(install_dir):
                shutil.rmtree(install_dir)

        print("> 正在解压 Elasticsearch ZIP 文件...")
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        shutil.unpack_archive(installer_zip, install_dir)

        print("> 开始启动 Elasticsearch 服务...")
        print("> 请在打开的文件夹内，以管理员身份运行 elasticsearch.bat，并等待 Elasticsearch 启动完成。")
        # 帮用户打开启动bat所在目录，告诉他必须用管理员权限
        subprocess.Popen(["explorer", f"/open,{os.path.join(install_dir, 'elasticsearch-8.15.0', 'bin')}"])
        # 弹窗说明
        show_windows_message("启动提示", "请以管理员身份运行 elasticsearch.bat，并等待 Elasticsearch 启动完成。")
        print("> 我们会在 75 秒后检查 Elasticsearch 是否已经启动。")

        time.sleep(75)

        print("> 接下来会开始检查 Elasticsearch 是否已经启动：")
        print(
            "> - 请注意，如果您是首次启动/或安装，此脚本可能会报安装失败，您需要关闭刚刚打开的elasticsearch.bat窗口，再启动elasticsearch.bat，等待25秒钟。")
        print(
            "> - 然后，打开您的项目文件夹，执行 python tools/setup/elasticsearch/elasticsearch_configs.py 后按照脚本提示完成配置")

        if check_elasticsearch_installed():
            print("> Elasticsearch 安装成功！")
            show_windows_message("Elasticsearch 安装成功", "Elasticsearch 已成功安装并正在运行。")
            print("> 帮助您启动配置脚本.....")
            # 启动配置脚本
            configure_elasticsearch()
        else:
            print("! Elasticsearch 安装失败。")
            show_windows_message("Elasticsearch 安装失败", "Elasticsearch 安装失败，请检查日志并尝试重新安装。")

    except PermissionError as e:
        print(f"! 权限错误，无法访问安装目录：{e}")
        show_windows_message("权限错误", "无法访问安装目录。将使用压缩软件打开安装文件，您需要手动解压到合适的位置。")

        try:
            # 打开压缩文件以便用户手动解压
            subprocess.Popen(["explorer", f"/select,{os.path.abspath(installer_zip)}"])

            time.sleep(2)

            # 帮用户打开安装目录
            subprocess.run(["explorer", install_dir])

            time.sleep(1)

            show_windows_message("解压提示", f"请将 {installer_zip} 解压到目录：\n{install_dir}")

            show_windows_message("启动提示", "解压完成后，点击“确定”将尝试启动 Elasticsearch。")

            print(f"! 无法启动 Elasticsearch")
            show_windows_message("启动失败",
                                 f"无法启动 Elasticsearch。请手动进入目录并运行 elasticsearch.bat：\n{os.path.join(install_dir, 'bin')}")

        except Exception as open_err:
            print(f"! 打开压缩文件失败：{open_err}")
            show_windows_message("错误",
                                 f"无法打开压缩文件。请手动解压并运行 Elasticsearch：{os.path.abspath(installer_zip)}")

    except Exception as e:
        print(f"! 安装过程中发生了错误：{e}")
        show_windows_message("安装错误", f"安装过程中发生错误：{e}")


def check_elasticsearch_installed():
    try:
        if platform.system() == "Windows":
            # 检查是否有 Elasticsearch 服务在运行
            try:
                result = subprocess.run(["sc", "query", "elasticsearch-service-x64"], capture_output=True, text=True)
                print(f"> 检查 Elasticsearch 服务状态：{result.stdout}")
                if "RUNNING" in result.stdout:
                    return True
            except FileNotFoundError:
                print("! 找不到 'sc' 命令，可能服务未安装。")

            # 检查是否有本地运行的 Elasticsearch 实例
            try:
                result = subprocess.run(["curl", "-X", "GET", "https://localhost:9200"], capture_output=True, text=True)
                if result.returncode == 0:
                    if "You Know, for Search" in result.stdout:
                        print("> Elasticsearch 服务正在运行。")
                        return True
                    if '"status":401' in result.stdout:
                        print("> Elasticsearch 服务正在运行，并需要认证。")
                        return True
            except FileNotFoundError:
                print("! 找不到 'curl' 命令，可能未正确安装。")

        elif platform.system() == "Linux":
            # 检查是否有 Elasticsearch 安装
            try:
                result = subprocess.run(["which", "elasticsearch"], capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            except FileNotFoundError:
                print("! 找不到 'elasticsearch' 命令，可能未安装。")

            # 检查是否有 Elasticsearch 服务在运行
            try:
                result = subprocess.run(["systemctl", "is-active", "--quiet", "elasticsearch"], capture_output=True)
                if result.returncode == 0:
                    return True
            except FileNotFoundError:
                print("! 找不到 'systemctl' 命令，可能服务未安装或未启动。")

        elif platform.system() == "Darwin":
            # 检查 Homebrew 管理的服务状态
            try:
                result = subprocess.run(["brew", "services", "list"], capture_output=True, text=True)
                if "elasticsearch" in result.stdout and "started" in result.stdout:
                    return True
            except FileNotFoundError:
                print("! 找不到 'brew' 命令，可能 Homebrew 未安装。")

        # 作为最后的检查，尝试通过 Elasticsearch 自身的命令行工具检测
        try:
            result = subprocess.run(["elasticsearch", "--version"], capture_output=True, text=True)
            if result.returncode == 0 and "Elasticsearch" in result.stdout:
                print(f"> 检查环境变量：{result.stdout}")
                return True
        except FileNotFoundError:
            print("! 找不到 'elasticsearch' 命令，可能未正确设置环境变量。")

        # 再次检查是否有本地运行的 Elasticsearch 实例
        urls = ["http://localhost:9200", "https://localhost:9200"]
        for url in urls:
            try:
                print(f"> 尝试连接 {url}...")
                result = subprocess.run(["curl", "-X", "GET", url], capture_output=True, text=True)
                if result.returncode == 0:
                    if "You Know, for Search" in result.stdout:
                        print("> Elasticsearch 服务正在运行。")
                        return True
                    if '"status":401' in result.stdout:
                        print("> Elasticsearch 服务正在运行，并需要认证。")
                        return True
                else:
                    print(f"! 访问 Elasticsearch 失败：{result.stdout}")
            except FileNotFoundError:
                print("! 找不到 'curl' 命令，可能未正确安装。")
            except Exception as e:
                print(f"! 连接 {url} 时出错：{e}")

        return False

    except Exception as e:
        print(f"! 检查 Elasticsearch 安装状态时出错：{e}")

    return False


def install_elasticsearch_on_linux(os_version: str):
    try:
        distro_name = distro.id()
        print(f"> 检测到的Linux发行版: {distro_name} {os_version}")

        if "ubuntu" in distro_name or "debian" in distro_name:
            print("> 正在导入 GPG 密钥并添加 Elasticsearch 仓库源...")
            # 导入GPG密钥
            subprocess.run(
                ["wget", "-qO", "-", "https://artifacts.elastic.co/GPG-KEY-elasticsearch", "|", "sudo", "apt-key", "add", "-"],
                shell=True,
                check=True
            )
            # 添加 Elasticsearch软件源
            subprocess.run(
                ["sudo", "sh", "-c",
                 'echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" > /etc/apt/sources.list.d/elastic-7.x.list'],
                check=True
            )
            # 更新软件包列表并安装 Elasticsearch
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "elasticsearch"], check=True)

            # 启动并设置 Elasticsearch 开机自启
            subprocess.run(["sudo", "systemctl", "enable", "--now", "elasticsearch.service"], check=True)

        elif "centos" in distro_name or "rhel" in distro_name or "fedora" in distro_name:
            print("> 正在导入 GPG 密钥并添加 Elasticsearch 仓库源...")
            subprocess.run(["sudo", "rpm", "--import", "https://artifacts.elastic.co/GPG-KEY-elasticsearch"], check=True)
            subprocess.run(["sudo", "yum", "install", "-y",
                            "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.15.0-x86_64.rpm"],
                           check=True)

        else:
            print(f"! 未支持的 Linux 发行版: {distro_name}")
            sys.exit(1)

        print("> Elasticsearch安装完成。")

    except subprocess.CalledProcessError as e:
        print(f"! 安装Elasticsearch时出错：{e}")
        sys.exit(1)




def install_elasticsearch_on_mac(os_version: str):
    try:
        print(f"> 检测到的macOS版本: {os_version}")
        print("> 正在使用Homebrew安装Elasticsearch...")

        subprocess.run(["brew", "tap", "elastic/tap"], check=True)
        subprocess.run(["brew", "install", "elasticsearch"], check=True)

        print("> Elasticsearch安装完成。")

    except subprocess.CalledProcessError as e:
        print(f"! 安装Elasticsearch时出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    os_name, os_version = detect_os_and_version()

    if not os_name or not os_version:
        print("! 无法检测操作系统或版本。")
        sys.exit(1)

    print(f"> 开始为 {os_name} {os_version} 安装Elasticsearch...")
    download_and_install_elasticsearch(os_name, os_version)
