# core/db/setup/elasticsearch/elasticsearch_configs.py
# Elasticsearch 配置脚本，负责初始化和更新 Elasticsearch 配置。
import yaml
import getpass
import sys
import subprocess
from pathlib import Path
from elasticsearch import Elasticsearch, exceptions
from core.utils.logger import get_logger

try:
    from config import ELASTICSEARCH_URL, ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD

    config_exists = True
except ImportError:
    config_exists = False

_log = get_logger()

# 默认安装路径
DEFAULT_WINDOWS_PATH = Path(r"C:\Elasticsearch\8.15.0\elasticsearch-8.15.0\bin")
DEFAULT_LINUX_PATH = Path("/usr/share/elasticsearch/bin")

# 配置文件路径
ELASTIC_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs/elasticsearch.yaml"
PROJECT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "configs/config.yaml"


def prompt_user_for_password():
    print("Elasticsearch 配置尚未设置或无效。请输入密码：")
    print("如果您不知道（或者是首次安装/启动）就随便输入一个吧 | 如果您刚重置完密码就输入新密码吧~")

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

        _log.info(f"Elasticsearch 配置已保存至：{ELASTIC_CONFIG_PATH} 和 {PROJECT_CONFIG_PATH}")
        _log.info(f"-----------")
        _log.info(f"请不要擅自修改已经添加的配置内容以及注释，否则可能导致配置系统无法正常工作。")
        _log.info(f"PLEASE DO NOT MODIFY THE ADDED CONFIGURATION CONTENTS AND COMMENTS, OR ELSE THE CONFIGURATION SYSTEM MAY NOT WORK PROPERLY.")
        _log.info(f"-----------")

    except Exception as e:
        _log.error(f"保存 Elasticsearch 配置时出错：{e}")
        raise


def test_elasticsearch_connection(password):
    try:
        es = Elasticsearch(
            "https://localhost:9200",
            basic_auth=("elastic", password),
            request_timeout=10,
            verify_certs=False
        )
        es.info()  # 测试连接
        _log.info("使用新的密码连接 Elasticsearch 成功！")
        return True
    except exceptions.AuthenticationException:
        _log.error("认证失败：密码错误。")
        return False
    except exceptions.ConnectionError as err:
        _log.error(f"无法连接到Elasticsearch服务器：{err}")
        return False
    except Exception as e:
        _log.error(f"测试 Elasticsearch 连接时发生错误：{e}")
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
        _log.error(f"无法重置 Elasticsearch 密码：{e}")
        sys.exit(1)


def configure_elasticsearch():
    try:
        if config_exists:
            _log.info("检测到现有的 Elasticsearch 配置，正在测试连接...")
            if test_elasticsearch_connection(ELASTICSEARCH_PASSWORD):
                _log.info("现有 Elasticsearch 配置有效，跳过配置过程。")
                return
            else:
                _log.warning("现有 Elasticsearch 配置无效，将进行重新配置。")

        # 提示用户输入密码
        password = prompt_user_for_password()

        # 更新配置文件
        update_elasticsearch_config(password)

        # 测试新配置的连接
        if not test_elasticsearch_connection(password):
            _log.error("Elasticsearch 配置失败，密码可能错误。")
            print("密码可能错误，将帮助您重置密码。")
            reset_elasticsearch_password()
            sys.exit(1)

    except Exception as e:
        _log.error(f"配置 Elasticsearch 时发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    _log.info("开始Elasticsearch配置...")
    _log.info(f"Elasticsearch 配置文件路径：{ELASTIC_CONFIG_PATH}")
    _log.info(f"项目配置文件路径：{PROJECT_CONFIG_PATH}")
    configure_elasticsearch()
    _log.info("Elasticsearch配置完成。")
    sys.exit(0)
