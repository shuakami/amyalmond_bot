import yaml
import getpass
import sys
from pathlib import Path
from pymongo import MongoClient, errors

# 配置文件路径
MONGO_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs/mongodb.yaml"
PROJECT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "configs/config.yaml"


def prompt_user_for_mongo_credentials():
    print("+-----------------------------------------------------+")
    print("| MongoDB 配置尚未设置。请输入用户名和密码：           |")
    print("+-----------------------------------------------------+")

    username = input("请输入 MongoDB 用户名: ").strip()
    while not username:
        print("用户名不能为空，请重新输入。")
        username = input("请输入 MongoDB 用户名: ").strip()

    password = getpass.getpass("请输入 MongoDB 密码: ").strip()
    while not password:
        print("密码不能为空，请重新输入。")
        password = getpass.getpass("请输入 MongoDB 密码: ").strip()

    return username, password


def update_mongo_config(username, password):
    try:
        # 确保配置目录存在
        if not MONGO_CONFIG_PATH.parent.exists():
            MONGO_CONFIG_PATH.parent.mkdir(parents=True)

        # 加载现有的 mongodb.yaml 配置文件，如果存在
        config = {}
        if MONGO_CONFIG_PATH.exists():
            with open(MONGO_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

        # 更新 mongodb.yaml 文件中的配置
        config['mongodb'] = {'username': username, 'password': password}

        # 保存更新后的配置到 mongodb.yaml 文件
        with open(MONGO_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        # 更新项目根目录的 config.yaml 文件
        if PROJECT_CONFIG_PATH.exists():
            with open(PROJECT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                project_config_lines = f.readlines()
        else:
            project_config_lines = []

        # 移除旧的 MongoDB 配置
        new_config_lines = []
        inside_mongodb_block = False
        for line in project_config_lines:
            if line.strip() == '# ---------- MongoDB Configuration ----------':
                inside_mongodb_block = True
                continue
            if line.strip() == '# ---------- End MongoDB Configuration ------':
                inside_mongodb_block = False
                continue
            if not inside_mongodb_block:
                new_config_lines.append(line)

        # 将新的 MongoDB 配置添加到文件末尾
        new_config_lines.append('\n')
        new_config_lines.append('# ---------- MongoDB Configuration ----------\n')
        new_config_lines.append(f'mongodb_url: "mongodb://localhost:27017"\n')
        new_config_lines.append(f'mongodb_username: "{username}"\n')
        new_config_lines.append(f'mongodb_password: "{password}"\n')
        new_config_lines.append('# ---------- End MongoDB Configuration ------\n')

        # 保存更新后的内容到 config.yaml 文件
        with open(PROJECT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_config_lines)

        print(f"> MongoDB 配置已保存至：{MONGO_CONFIG_PATH} 和 {PROJECT_CONFIG_PATH}")
        print(f"> -------------------------------------------------")
        print(f"> 请不要擅自修改已添加的配置内容及注释，否则可能导致配置系统无法正常工作。")
        print(f"> -------------------------------------------------")

    except Exception as e:
        print(f"! 保存 MongoDB 配置时出错：{e}")
        raise


def apply_mongo_config(username, password):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client.admin

        # 创建管理员用户
        db.command("createUser", username, pwd=password, roles=[{"role": "root", "db": "admin"}])

        print("> MongoDB 配置已成功应用。")

        # 验证连接是否成功
        test_mongo_connection(username, password)

    except errors.OperationFailure as err:
        print(f"! 应用 MongoDB 配置时失败：{err}")
        # 如果报错already exists
        if "already exists" in str(err):
            print("> 用户已存在，跳过创建用户步骤。")
        raise
    except Exception as e:
        print(f"! 应用 MongoDB 配置时出错：{e}")
        # 如果报错already exists
        if "already exists" in str(e):
            print("> 用户已存在，跳过创建用户步骤。")
            # 检测一下链接
            if test_mongo_connection(username, password):
                print("> 使用新的用户名和密码连接 MongoDB 成功！")
        raise


def test_mongo_connection(username, password):
    try:
        uri = f"mongodb://{username}:{password}@localhost:27017/"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("> 使用新的用户名和密码连接 MongoDB 成功！")
        return True
    except errors.ServerSelectionTimeoutError as err:
        print(f"! 使用新的用户名和密码无法连接到MongoDB服务器：{err}")
        return False
    except Exception as e:
        print(f"! 测试 MongoDB 连接时发生错误：{e}")
        return False


def configure_mongodb():
    try:
        # 提示用户输入用户名和密码
        username, password = prompt_user_for_mongo_credentials()

        # 更新配置文件
        update_mongo_config(username, password)

        # 应用到 MongoDB 并验证
        apply_mongo_config(username, password)

    except Exception as e:
        print(f"! 配置 MongoDB 时发生错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    print("> 开始MongoDB配置...")
    print(f"> MongoDB 配置文件路径：{MONGO_CONFIG_PATH}")
    print(f"> 项目配置文件路径：{PROJECT_CONFIG_PATH}")
    configure_mongodb()
    print("> MongoDB配置完成。")
    sys.exit(0)
