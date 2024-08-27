import random
import os
import time
import keyboard

GAME_WIDTH = 40
GAME_HEIGHT = 25
MAX_LEVEL = 15  # 提升最大等级

# 颜色定义
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

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
        self.lives = 7
        self.shield = 0
        self.score = 0


class Obstacle(GameObject):
    def __init__(self, x, y, char, speed, damage=1):
        super().__init__(x, y, Colors.RED + char + Colors.RESET)  # 使用红色显示所有敌方攻击
        self.speed = speed
        self.damage = damage


class Boss(Obstacle):
    def __init__(self, x, y, level):
        super().__init__(x, y, 'B', 0.5 * level, damage=level)
        self.max_health = 2 * level
        self.health = self.max_health
        self.size = 7
        self.attack_cooldown = 2.0
        self.last_attack_time = time.time()

    def range_attack(self, obstacles, player):
        current_time = time.time()
        if current_time - self.last_attack_time > self.attack_cooldown:
            predicted_x = player.x
            if player.x < self.x:
                predicted_x = min(GAME_WIDTH - 1, player.x + random.randint(1, 3))
            elif player.x > self.x:
                predicted_x = max(0, player.x - random.randint(1, 3))

            attack_patterns = [
                ('vertical', 5),
                ('horizontal', 3),
                ('cross', 3),
                ('scatter', 10),  # 增加散射攻击
                ('compress', 5)  # 增加压缩攻击
            ]

            selected_pattern, repeats = random.choice(attack_patterns)

            for _ in range(repeats):
                if selected_pattern == 'vertical':
                    for i in range(self.size + 2):
                        target_x = self.x + i - 1
                        target_x = max(0, min(GAME_WIDTH - 1, target_x))
                        if abs(target_x - predicted_x) < 3:
                            obstacles.append(Obstacle(target_x, self.y + 1, Colors.RED + '|' + Colors.RESET, 1.5, damage=1))

                elif selected_pattern == 'horizontal':
                    for y_offset in range(1, 4):
                        if abs(predicted_x - self.x) < 3:
                            obstacles.append(Obstacle(self.x, self.y + y_offset, Colors.RED + '─' + Colors.RESET, 0.5, damage=1))

                elif selected_pattern == 'cross':
                    for i in range(-2, 3):
                        if 0 <= self.x + i < GAME_WIDTH and abs(self.x + i - predicted_x) < 3:
                            obstacles.append(Obstacle(self.x + i, self.y + 1, Colors.RED + '┼' + Colors.RESET, 1.0, damage=1))
                        if 0 <= self.y + 1 + i < GAME_HEIGHT:
                            obstacles.append(Obstacle(self.x, self.y + 1 + i, Colors.RED + '┼' + Colors.RESET, 1.0, damage=1))

                elif selected_pattern == 'scatter':
                    # 随机散射攻击
                    for _ in range(5):
                        scatter_x = random.randint(0, GAME_WIDTH - 1)
                        obstacles.append(Obstacle(scatter_x, self.y + 1, Colors.RED + '•' + Colors.RESET, 1.0, damage=1))

                elif selected_pattern == 'compress':
                    # 压缩攻击：从左右向中间压缩
                    for i in range(self.size):
                        left_x = max(0, self.x - i)
                        right_x = min(GAME_WIDTH - 1, self.x + i + self.size)
                        obstacles.append(Obstacle(left_x, self.y + 1, Colors.RED + '|' + Colors.RESET, 1.5, damage=1))
                        obstacles.append(Obstacle(right_x, self.y + 1, Colors.RED + '|' + Colors.RESET, 1.5, damage=1))

            self.last_attack_time = current_time
            self.attack_cooldown = max(0.5, self.attack_cooldown * 0.9)  # 加快攻击频率


class PowerUp(GameObject):
    def __init__(self, x, y, type):
        super().__init__(x, y, '⭐')
        self.type = type


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_game_state(player, obstacles, powerups, game_width, game_height, level, boss=None):
    clear_screen()
    game_board = [[' ' for _ in range(game_width)] for _ in range(game_height)]

    game_board[player.y][player.x] = Colors.GREEN + 'M' + Colors.RESET if player.shield > 0 else 'M'  # 导弹模式

    for obj in obstacles + powerups:
        if 0 <= obj.y < game_height and 0 <= obj.x < game_width:
            game_board[int(obj.y)][int(obj.x)] = obj.char

    if boss:
        # 显示Boss占据的区域
        for i in range(boss.size):
            game_board[int(boss.y)][int(boss.x) + i] = Colors.RED + 'B' + Colors.RESET

    for row in game_board:
        print(''.join(row))

    print(f"+{'=' * (game_width - 2)}+")
    print(
        f"得分: {player.score} | 等级: {level} | 生命: {Colors.RED}{'❤' * player.lives}{Colors.RESET} | 护盾: {Colors.BLUE}{player.shield}{Colors.RESET} | 满级为{MAX_LEVEL}级")
    if boss:
        print(f"Boss 血量: {Colors.RED}{boss.health}/{boss.max_health}{Colors.RESET} | 您需要在战胜boss的同时躲避它的攻击")


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
    player = Player(GAME_WIDTH // 2, GAME_HEIGHT - 2)
    obstacles = []
    powerups = []
    level = 1
    last_move_time = time.time()
    last_missile_time = time.time()  # 记录上次发射导弹的时间
    move_cooldown = 0.08
    missile_cooldown = 0.5  # 导弹发射的冷却时间
    last_level_up_time = time.time()
    level_up_interval = 20
    game_speed = 0.1
    last_obstacle_time = time.time()
    obstacle_interval = 0.8
    boss = None
    missile_mode = False

    def spawn_obstacle():
        obstacle_type = random.choices(['⬛', '|', '↓', '◆', '⚡'], weights=[30, 25, 20, 15, 10], k=1)[0]
        speed = random.uniform(1.5, 2.5) * (1 + level * 0.2)
        if obstacle_type == '⚡':
            return Obstacle(random.randint(0, GAME_WIDTH - 1), 0, obstacle_type, speed)
        elif obstacle_type == '|':
            return Obstacle(random.randint(0, GAME_WIDTH - 1), 0, obstacle_type, 0.5)
        else:
            return Obstacle(random.randint(0, GAME_WIDTH - 1), 0, obstacle_type, speed)

    def spawn_boss():
        return Boss(random.randint(0, GAME_WIDTH - 7), 0, level)  # BOSS从屏幕顶部中间生成

    def spawn_powerup():
        powerup_type = random.choices(['shield', 'life', 'slow', 'score'], weights=[30, 30, 20, 20], k=1)[0]
        return PowerUp(random.randint(0, GAME_WIDTH - 1), 0, powerup_type)

    while True:
        current_time = time.time()

        # 生成新的障碍物
        if current_time - last_obstacle_time > obstacle_interval:
            obstacles.append(spawn_obstacle())
            last_obstacle_time = current_time
            obstacle_interval = max(0.3, obstacle_interval * 0.98)

        # 生成道具 (降低概率)
        if random.random() < 0.03 + (level * 0.003):  # 概率降低
            powerups.append(spawn_powerup())

            def spawn_boss():
                return Boss(random.randint(0, GAME_WIDTH - 7), 0, level)  # BOSS从屏幕顶部中间生成

            while True:
                current_time = time.time()



                # 生成新的障碍物
                if current_time - last_obstacle_time > obstacle_interval:
                    obstacles.append(spawn_obstacle())
                    last_obstacle_time = current_time
                    obstacle_interval = max(0.3, obstacle_interval * 0.98)

                # 生成道具
                if random.random() < 0.03 + (level * 0.003):
                    powerups.append(spawn_powerup())

                # 生成 BOSS
                if level % 3 == 0 and not boss:
                    boss = spawn_boss()
                    missile_mode = True  # 进入导弹模式


                # BOSS范围攻击
                if boss:
                    boss.range_attack(obstacles,player)

                    # 发射导弹攻击BOSS
                    if missile_mode and boss and current_time - last_missile_time > missile_cooldown:
                        obstacles.append(
                            Obstacle(player.x, player.y - 1, Colors.CYAN + '↑' + Colors.RESET, -2, damage=5))
                        last_missile_time = current_time

                # 检查导弹与BOSS的碰撞
                for obj in obstacles[:]:
                    if obj.char == '↑' and boss and boss.x <= obj.x < boss.x + boss.size and obj.y <= boss.y + 1:
                        boss.health -= obj.damage
                        obstacles.remove(obj)
                        if boss.health <= 0:
                            player.score += 1000 * level
                            boss = None  # BOSS被击败
                            missile_mode = False

                # 移动物体
                for obj in obstacles:
                    if obj.char == '|':
                        obj.move(0, 0.5)
                    elif obj.char == '◆':
                        if random.random() < 0.1 * level:
                            dx = 1 if obj.x < player.x else -1 if obj.x > player.x else 0
                            obj.move(dx, obj.speed)
                        else:
                            obj.move(0, obj.speed)
                    else:
                        obj.move(0, obj.speed)

                for powerup in powerups:
                    powerup.move(0, 0.5)

                if boss:
                    boss.move(random.choice([-1, 0, 1]), 0)

                # 移除超出屏幕的物体
                obstacles = [obj for obj in obstacles if obj.y < GAME_HEIGHT]
                powerups = [obj for obj in powerups if obj.y < GAME_HEIGHT]

                # 检查碰撞
                for obj in obstacles[:]:
                    if obj.x == player.x and int(obj.y) == player.y:
                        if player.shield > 0:
                            player.shield -= obj.damage
                            if player.shield < 0:
                                player.lives += player.shield  # 如果护盾不够，剩余伤害作用到生命值上
                                player.shield = 0
                        else:
                            player.lives -= obj.damage
                        obstacles.remove(obj)
                        if player.lives <= 0:
                            show_game_over(player, level)
                            while True:
                                if keyboard.is_pressed('r'):
                                    return play_game()
                                elif keyboard.is_pressed('q'):
                                    return

                if boss and int(boss.y) + 1 == player.y and boss.x <= player.x < boss.x + boss.size:
                    boss.health -= 5  # 玩家导弹攻击BOSS
                    if boss.health <= 0:
                        player.score += 1000 * level
                        boss = None  # BOSS被击败
                        missile_mode = False

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
                print_game_state(player, obstacles, powerups, GAME_WIDTH, GAME_HEIGHT, level, boss)

                # 控制游戏速度
                time.sleep(game_speed)

                # 检查 Boss 是否被击败
                if boss and boss.health <= 0:
                    boss = None  # Boss 被击败
                    player.score += 1000 * level  # 获得奖励分数

        if __name__ == "__main__":
            play_game()