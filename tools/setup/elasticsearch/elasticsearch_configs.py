import yaml
import getpass
import sys
import subprocess
from pathlib import Path
from elasticsearch import Elasticsearch, exceptions

try:
    from config import ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD

    config_exists = True
except ImportError:
    config_exists = False
    # 默认的用户名和密码在未导入配置时提示用户输入
    ELASTICSEARCH_USERNAME = "elastic"
    ELASTICSEARCH_PASSWORD = None

# 默认安装路径
DEFAULT_WINDOWS_PATH = Path(r"C:\Elasticsearch\8.15.0\elasticsearch-8.15.0\bin")
DEFAULT_LINUX_PATH = Path("/usr/share/elasticsearch/bin")

# 配置文件路径
ELASTIC_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs/elasticsearch.yaml"
PROJECT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "configs/config.yaml"


def prompt_user_for_password():
    print("+-----------------------------------------------------+")
    print("| Elasticsearch 配置尚未设置或无效，请输入密码：      |")
    print("| 如果您不知道（或者是首次安装/启动），随便输入一个吧 |")
    print("| 如果您刚重置完密码，请输入新密码。                 |")
    print("+-----------------------------------------------------+")

    password = getpass.getpass("请输入 Elasticsearch 密码: ").strip()
    while not password:
        print("密码不能为空，请重新输入。")
        password = getpass.getpass("请输入 Elasticsearch 密码: ").strip()

    return password


def update_elasticsearch_config(password):
    try:
        # 确保配置目录存在
        if not ELASTIC_CONFIG_PATH.parent.exists():
            ELASTIC_CONFIG_PATH.parent.mkdir(parents=True)

        # 加载现有的 elasticsearch.yaml 配置文件，如果存在
        config = {}
        if ELASTIC_CONFIG_PATH.exists():
            with open(ELASTIC_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

        # 更新 elasticsearch.yaml 文件中的配置
        config['elasticsearch'] = {'username': 'elastic', 'password': password}

        # 保存更新后的配置到 elasticsearch.yaml 文件
        with open(ELASTIC_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        # 更新项目根目录的 config.yaml 文件
        if PROJECT_CONFIG_PATH.exists():
            with open(PROJECT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                project_config_lines = f.readlines()
        else:
            project_config_lines = []

        # 移除旧的 Elasticsearch 配置
        new_config_lines = []
        inside_elasticsearch_block = False
        for line in project_config_lines:
            if line.strip() == '# ---------- Elasticsearch Configuration ----------':
                inside_elasticsearch_block = True
                continue
            if line.strip() == '# ---------- End Elasticsearch Configuration ------':
                inside_elasticsearch_block = False
                continue
            if not inside_elasticsearch_block:
                new_config_lines.append(line)

        # 将新的 Elasticsearch 配置添加到文件末尾
        new_config_lines.append('\n')
        new_config_lines.append('# ---------- Elasticsearch Configuration ----------\n')
        new_config_lines.append(f'elasticsearch_url: "http://localhost:9200"\n')
        new_config_lines.append(f'elasticsearch_username: "elastic"\n')
        new_config_lines.append(f'elasticsearch_password: "{password}"\n')
        new_config_lines.append('# ---------- End Elasticsearch Configuration ------\n')

        # 保存更新后的内容到 config.yaml 文件
        with open(PROJECT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_config_lines)

        print(f"> Elasticsearch 配置已保存至：{ELASTIC_CONFIG_PATH} 和 {PROJECT_CONFIG_PATH}")
        print(f"> -------------------------------------------------")
        print(f"> 请不要擅自修改已添加的配置内容及注释，否则可能导致配置系统无法正常工作。")
        print(f"> PLEASE DO NOT MODIFY THE ADDED CONFIGURATION CONTENTS AND COMMENTS,")
        print(f"> OR ELSE THE CONFIGURATION SYSTEM MAY NOT WORK PROPERLY.")
        print(f"> -------------------------------------------------")

    except Exception as e:
        print(f"! 保存 Elasticsearch 配置时出错：{e}")
        raise


def test_elasticsearch_connection(password):
    urls = ["https://localhost:9200", "http://localhost:9200"]
    for url in urls:
        try:
            es = Elasticsearch(
                url,
                basic_auth=("elastic", password),
                request_timeout=10,
                verify_certs=False
            )
            es.info()  # 测试连接
            print("")
            print(f"-------------------------")
            print(f"> 使用密码连接到 {url} 成功！[请看清楚是HTTP还是HTTPS]")
            print(f"-------------------------")
            return True
        except exceptions.AuthenticationException:
            print("! 认证失败：密码错误。")
            return False
        except exceptions.ConnectionError as err:
            print(f"! 无法连接到 {url}：{err}")
        except Exception as e:
            print(f"! 测试连接到 {url} 时发生错误：{e}")

    print("! 无法通过 HTTP 或 HTTPS 连接到 Elasticsearch 服务器。")
    return False


def reset_elasticsearch_password():
    try:
        if sys.platform == "win32":
            # 运行 elasticsearch-reset-password.bat
            subprocess.run(
                ["cmd", "/c", "start", "cmd", "/k", str(DEFAULT_WINDOWS_PATH / "elasticsearch-reset-password.bat"),
                 "-u", "elastic", "-i"],
                shell=True,
            )

            # 打印详细帮助提示
            print("\n已启动 Elasticsearch 密码重置工具，请按照以下步骤操作：")
            print("1. 在新打开的命令行窗口中，你会看到提示：")
            print("   'This tool will reset the password of the [elastic] user.'")
            print("2. 输入 'y' 确认重置密码，然后按 Enter 键。")
            print("3. 系统会提示你输入新密码，并再次确认密码。")
            print("4. 成功设置新密码后，记下这个密码。")
            print("5. 关闭命令行窗口，并重新运行配置脚本以测试连接。")

            # 退出程序
            sys.exit(0)

        else:
            # 运行 elasticsearch-reset-password 工具
            subprocess.run(
                [str(DEFAULT_LINUX_PATH / "elasticsearch-reset-password"), "-u", "elastic", "-i"],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )

            # 打印详细帮助提示
            print("\n已启动 Elasticsearch 密码重置工具，请按照以下步骤操作：")
            print("1. 在终端中，你会看到提示：")
            print("   'This tool will reset the password of the [elastic] user.'")
            print("2. 输入 'y' 确认重置密码，然后按 Enter 键。")
            print("3. 系统会提示你输入新密码，并再次确认密码。")
            print("4. 成功设置新密码后，记下这个密码。")
            print("5. 关闭命令行窗口，并重新运行本配置脚本以测试连接。")

            # 退出程序
            sys.exit(0)

    except Exception as e:
        print(f"! 无法重置 Elasticsearch 密码：{e}")
        sys.exit(1)


def configure_elasticsearch():
    try:
        if config_exists:
            print("> 检测到现有的 Elasticsearch 配置，正在测试连接...")
            if test_elasticsearch_connection(ELASTICSEARCH_PASSWORD):
                print("> 现有 Elasticsearch 配置有效，跳过配置过程。")
                return
            else:
                print("> 现有 Elasticsearch 配置无效，将进行重新配置。")

        # 提示用户输入密码
        password = prompt_user_for_password()

        # 更新配置文件
        update_elasticsearch_config(password)

        # 测试新配置的连接
        if not test_elasticsearch_connection(password):
            print("! Elasticsearch 配置失败，密码可能错误。")
            print("密码可能错误，将帮助您重置密码。")
            reset_elasticsearch_password()
            sys.exit(1)

    except Exception as e:
        print(f"! 配置 Elasticsearch 时发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    print("> 开始 Elasticsearch 配置...")
    print(f"> Elasticsearch 配置文件路径：{ELASTIC_CONFIG_PATH}")
    print(f"> 项目配置文件路径：{PROJECT_CONFIG_PATH}")
    configure_elasticsearch()
    print("> Elasticsearch 配置完成。")
    sys.exit(0)
