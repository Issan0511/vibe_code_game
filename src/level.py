# level.py
import pygame

class Platform:
    def __init__(self, world_x, y, width, height):
        self.initial_world_x = world_x
        self.initial_y = y

        self.world_x = world_x
        self.y = y
        self.width = width
        self.height = height
        self.color = (139, 69, 19)

        # 移動関連
        self.vx = 0
        self.vy = 0
        self.move_enabled = False

    # ---- 移動制御 ----
    def set_velocity(self, vx, vy):
        self.vx = vx
        self.vy = vy
        self.move_enabled = True

    def stop(self):
        self.vx = 0
        self.vy = 0
        self.move_enabled = False

    def update(self):
        if self.move_enabled:
            prev_y = self.y
            self.world_x += self.vx
            self.y += self.vy
            return self.y - prev_y
        return 0

    # ---- 描画・当たり判定 ----
    def draw(self, surface, camera_x):
        screen_x = int(self.world_x - camera_x)
        rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)

    def get_rect(self, camera_x):
        screen_x = int(self.world_x - camera_x)
        return pygame.Rect(screen_x, self.y, self.width, self.height)

    # ---- リセット ----
    def reset_position(self):
        self.world_x = self.initial_world_x
        self.y = self.initial_y
        self.stop()


class Goal:
    def __init__(self, world_x, y, width=60, height=80, color=None):
        self.initial_world_x = world_x
        self.initial_y = y

        self.world_x = world_x
        self.y = y
        self.width = width
        self.height = height
        self.color = color if color else (255, 215, 0)

    def draw(self, surface, camera_x):
        screen_x = int(self.world_x - camera_x)
        rect = pygame.Rect(screen_x, self.y - self.height, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.line(
            surface, (100, 100, 100),
            (screen_x + 10, self.y - self.height),
            (screen_x + 10, self.y), 3
        )

    def get_rect(self, camera_x):
        screen_x = int(self.world_x - camera_x)
        return pygame.Rect(screen_x, self.y - self.height, self.width, self.height)

    def reset_position(self):
        self.world_x = self.initial_world_x
        self.y = self.initial_y


def load_level(config, ground_y):
    """
    config から platforms, ground_segments, goal をまとめて生成
    """
    platforms = [
        Platform(
            world_x=p['world_x'],
            y=ground_y - p['y_offset'],
            width=p['width'],
            height=p['height']
        )
        for p in config['platforms']
    ]

    ground_segments = config.get('ground_segments', [{"start_x": 0, "end_x": 10000}])

    goal_initial_y = ground_y + config['goal'].get('world_y', 0)
    goal = Goal(
        world_x=config['goal']['world_x'],
        y=goal_initial_y,
        width=config['goal']['width'],
        height=config['goal']['height'],
        color=tuple(config['goal']['color'])
    )

    return platforms, ground_segments, goal


def is_on_ground(ground_segments, world_x):
    """指定された世界座標 x が地面セグメント上かどうか"""
    for segment in ground_segments:
        if segment['start_x'] <= world_x <= segment['end_x']:
            return True
    return False
