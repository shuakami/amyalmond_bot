import random
import sys
import os
import subprocess
import time
import keyboard


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


GAME_WIDTH = 40
GAME_HEIGHT = 25
MAX_LEVEL = 6


class GameObject:
    def __init__(self, x, y, char):
        self.x = x
        self.y = y
        self.char = char

    def move(self, dx, dy):
        self.x += dx
        self.y += dy


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, '|')
        self.lives = 3
        self.shield = 0
        self.score = 0


class Obstacle(GameObject):
    def __init__(self, x, y, char, speed):
        super().__init__(x, y, char)
        self.speed = speed


class PowerUp(GameObject):
    def __init__(self, x, y, type):
        super().__init__(x, y, '⭐')
        self.type = type


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_game_state(player, obstacles, powerups, game_width, game_height, level):
    clear_screen()
    game_board = [[' ' for _ in range(game_width)] for _ in range(game_height)]

    game_board[player.y][player.x] = 'O' if player.shield > 0 else '|'

    for obj in obstacles + powerups:
        if 0 <= obj.y < game_height and 0 <= obj.x < game_width:
            game_board[int(obj.y)][int(obj.x)] = obj.char

    for row in game_board:
        print(''.join(row))

    print(f"+{'=' * (game_width - 2)}+")
    print(f"得分: {player.score} | 等级: {level} | 生命: {'❤' * player.lives} | 护盾: {player.shield} | 满级为{MAX_LEVEL}级")


def show_credits():
    clear_screen()
    credits = """
    +----------------------------------------+
    |                项目鸣谢                |
    |                                        |
    |        @Shuakami | @xiaoyueyoqwq       |
    |                                        |
    +----------------------------------------+
    """
    print(credits)
    time.sleep(3)


def show_game_over(player, level):
    clear_screen()
    game_over_text = f"""
    +----------------------------------------+
    |                                        
    |              GAME OVER!               
    |                                        
    |            你的得分: {player.score:<5}    
    |            最终等级: {level:<5}           
    |                                        
    |         按 R 重新开始，按 Q 退出          
    +----------------------------------------+
    """
    show_credits()
    print(game_over_text)



def play_game():
    player = Player(GAME_WIDTH // 2, GAME_HEIGHT - 1)
    obstacles = []
    powerups = []
    level = 1
    last_move_time = time.time()
    move_cooldown = 0.08
    last_level_up_time = time.time()
    level_up_interval = 30
    game_speed = 0.1
    last_obstacle_time = time.time()
    obstacle_interval = 1.0
    boss_spawned = False

    def spawn_obstacle():
        obstacle_type = random.choices(['⬛', '|', '↓', '◆', '⚡'], weights=[30, 25, 20, 15, 10], k=1)[0]
        if obstacle_type == '⚡':  # 智能导弹
            speed = 1.0 + level * 0.1  # 智能导弹的速度降低
        else:
            speed = random.uniform(1.0, 2.0) * (1 + level * 0.15)
        if obstacle_type == '|':
            return Obstacle(random.randint(0, GAME_WIDTH - 1), 0, obstacle_type, 0)
        else:
            return Obstacle(random.randint(0, GAME_WIDTH - 1), 0, obstacle_type, speed)

    def spawn_boss():
        return Obstacle(random.randint(0, GAME_WIDTH - 1), 0, 'B', 0.5 * level)

    def spawn_powerup():
        return PowerUp(random.randint(0, GAME_WIDTH - 1), 0, random.choice(['shield', 'life', 'slow', 'score']))

    while True:
        current_time = time.time()

        # 生成新的障碍物
        if current_time - last_obstacle_time > obstacle_interval:
            obstacles.append(spawn_obstacle())
            last_obstacle_time = current_time
            obstacle_interval = max(0.3, obstacle_interval * 0.98)

        # 生成道具
        if random.random() < 0.07 + (level * 0.005):
            powerups.append(spawn_powerup())

        # 生成 BOSS
        if level == MAX_LEVEL and not boss_spawned:
            obstacles.append(spawn_boss())
            boss_spawned = True

        # 移动物体
        for obj in obstacles:
            if obj.char == '|':  # 激光缓慢移动
                obj.move(0, 0.5)
            elif obj.char == '◆':  # 智能导弹预判
                if random.random() < 0.1 * level:  # 增加智能导弹的预判难度
                    dx = 1 if obj.x < player.x else -1 if obj.x > player.x else 0
                    obj.move(dx, obj.speed)
                else:
                    obj.move(0, obj.speed)
            else:
                obj.move(0, obj.speed)

        for powerup in powerups:
            powerup.move(0, 0.5)

        # 移除超出屏幕的物体
        obstacles = [obj for obj in obstacles if obj.y < GAME_HEIGHT]
        powerups = [obj for obj in powerups if obj.y < GAME_HEIGHT]

        # 检查碰撞
        for obj in obstacles[:]:
            if obj.x == player.x and int(obj.y) == player.y:
                if player.shield > 0:
                    player.shield -= 1
                    obstacles.remove(obj)
                elif obj.char == 'B':
                    player.lives -= 3
                    obstacles.remove(obj)
                    if player.lives <= 0:
                        show_game_over(player, level)
                        while True:
                            if keyboard.is_pressed('r'):
                                return play_game()
                            elif keyboard.is_pressed('q'):
                                return
                else:
                    player.lives -= 1
                    obstacles.remove(obj)
                    if player.lives <= 0:
                        show_game_over(player, level)
                        while True:
                            if keyboard.is_pressed('r'):
                                return play_game()
                            elif keyboard.is_pressed('q'):
                                return

        for powerup in powerups[:]:
            if powerup.x == player.x and int(powerup.y) == player.y:
                if powerup.type == 'shield':
                    player.shield = min(player.shield + 2, 5)
                elif powerup.type == 'life':
                    player.lives = min(player.lives + 1, 5)
                elif powerup.type == 'slow':
                    game_speed *= 1.2
                elif powerup.type == 'score':
                    player.score += 100
                powerups.remove(powerup)

        # 玩家移动
        if current_time - last_move_time > move_cooldown:
            if keyboard.is_pressed('a') and player.x > 0:
                player.move(-1, 0)
                last_move_time = current_time
            elif keyboard.is_pressed('d') and player.x < GAME_WIDTH - 1:
                player.move(1, 0)
                last_move_time = current_time

        # 更新分数
        player.score += 1 + level

        # 提升等级
        if current_time - last_level_up_time > level_up_interval and level < MAX_LEVEL:
            level += 1
            last_level_up_time = current_time
            game_speed = max(game_speed * 0.9, 0.05)

        # 打印游戏状态
        print_game_state(player, obstacles, powerups, GAME_WIDTH, GAME_HEIGHT, level)

        # 控制游戏速度
        time.sleep(game_speed)


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
