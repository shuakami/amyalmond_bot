import sys
import os
import subprocess


from game import play_game


def run_external_script(script_relative_path):
    """分离运行外部脚本"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.abspath(os.path.join(script_dir, script_relative_path))
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"执行 {script_path} 时出错: {e}")
        return False
    return True


def manage_mongodb(action):
    """管理MongoDB的安装、启动和配置"""
    if action == '1':  # 安装
        print("开始安装MongoDB...")
        if not run_external_script("install/mongodb/mongodb_install.py"):
            print("MongoDB安装失败。")
            return False
    elif action == '2':  # 启动
        print("开始启动MongoDB...")
        if not run_external_script("setup/mongodb/mongodb_setup.py"):
            print("MongoDB启动失败。")
            return False
    elif action == '3':  # 配置
        if not run_external_script("setup/mongodb/mongodb_setup_configs.py"):
            print("MongoDB启动失败。")
            return False
    return True


def print_help():
    """打印帮助信息，详细解释各个操作及其使用方法"""
    help_text = """
    +----------------------------------------------------------------------------------+
    |                                  帮助文档                                          |
    +----------------------------------------------------------------------------------+
    |   欢迎来到数据库管理工具的帮助页面！                                               |
    |   在这里，我们将详细介绍每一个功能的作用，以及如何使用这个工具来高效地管理你的数据库。|
    +----------------------------------------------------------------------------------+

    1. 安装 (帮助你安装数据库)
       - 这个选项将引导你通过一个简单的步骤来安装MongoDB或Elasticsearch数据库。
       - 安装过程是自动化的，你只需要选择数据库类型，然后工具将自动运行对应的安装脚本。
       - 适用于初次使用该数据库或在新环境中重新搭建数据库的用户。

    2. 启动 (帮助你启动数据库)
       - 如果你已经安装了数据库，并且需要启动它们，那么这个选项适合你。
       - 启动操作将执行预设的启动脚本，确保数据库正确启动，并且能够接受连接。
       - 通常用于在服务器重新启动后，或者需要手动启动数据库的场景。

    3. 配置 (配置数据库账号密码)
       - 此选项用于配置数据库的基本安全设置，比如账号和密码。
       - 对于MongoDB和Elasticsearch，我们提供了专用的配置脚本来设置数据库的账号和密码。
       - 强烈建议在生产环境中进行适当的配置，以确保数据库的安全性。

    4. 升级原数据库（数据迁移）
       - 当你需要将现有的数据库升级到新版本或迁移数据时，选择这个选项。
       - 该操作将自动调用升级脚本，确保数据在升级过程中不会丢失。
       - 请在操作之前备份你的数据，以防万一。

    +----------------------------------------------------------------------------------+
    |   注意：每一个操作都有它特定的目的，请根据你的需求选择相应的功能。                
    |   如果你在使用过程中遇到了问题，建议参考对应的日志文件，以获取更详细的信息。        
    |   我们的目标是让你以最少的操作成本，完成对数据库的管理工作。                      
    +----------------------------------------------------------------------------------+




    egg you cai dan o
    """
    print(help_text)

def manage_elasticsearch(action):
    """管理Elasticsearch的安装、启动和配置"""
    if action == '1':  # 安装
        print("开始安装Elasticsearch...")
        if not run_external_script("install/elasticsearch/elasticsearch_install.py"):
            print("Elasticsearch安装失败。")
            return False
    elif action == '2':  # 启动
        print("开始启动Elasticsearch...")
        if not run_external_script("setup/elasticsearch/elasticsearch_setup.py"):
            print("Elasticsearch启动失败。")
            return False
    elif action == '3':  # 配置
        print("开始配置Elasticsearch...")
        if not run_external_script("setup/elasticsearch/elasticsearch_configs.py"):
            print("Elasticsearch启动失败。")
            return False
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'egg':
        play_game()
        sys.exit(0)

    print("+----------------------------------------+")
    print("|   欢迎使用数据库管理工具                   |")
    print("+----------------------------------------+")
    print("|   请选择操作:                            |")
    print("|   1. 安装 (帮助你安装数据库)               |")
    print("|   2. 启动 (帮助你启动数据库)               |")
    print("|   3. 配置 (配置数据库账号密码)             |")
    print("|   4. 升级原数据库（数据迁移）               |")
    print("|   需要帮助请按在脚本后缀加h(就是h，不是-h）    |")
    print("+----------------------------------------+")

    if len(sys.argv) > 1 and sys.argv[1] == 'h':
        print_help()
        sys.exit(0)

    choice = input("请输入数字选择操作: ")

    if choice == '4':
        print("开始升级原数据库...")
        if not run_external_script("upgrade/db_upgrade.py"):
            print("数据库升级失败。")
            sys.exit(1)

    if choice not in ['1', '2', '3']:
        print("无效的选择，程序将退出。")
        sys.exit(1)

    print("+----------------------------------------+")
    print("|   请选择数据库：                          |")
    print("|   1. MongoDB                           |")
    print("|   2. Elasticsearch                     |")
    print("+----------------------------------------+")

    db_choice = input("请输入数字选择数据库: ")

    if db_choice == '1':
        print(f"您选择了MongoDB，执行 {choice} 操作。")
        if not manage_mongodb(choice):
            print("MongoDB操作失败。")
            sys.exit(1)
    elif db_choice == '2':
        print(f"您选择了Elasticsearch，执行 {choice} 操作。")
        if not manage_elasticsearch(choice):
            print("Elasticsearch操作失败。")
            sys.exit(1)
    else:
        print("无效的选择，程序将退出。")
        sys.exit(1)

    print("操作完成。")
    sys.exit(0)
