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
        self.color = (0, 0, 0)

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
        pygame.draw.rect(surface, (255, 255, 255), rect)  # 白で塗りつぶし
        pygame.draw.rect(surface, self.color, rect, 3)  # 黒枠線(線幅3px)

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

        # Load images
        self.images = []
        try:
            for i in range(1, 5):
                img = pygame.image.load(f'assets/goal/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (self.width, self.height))
                self.images.append(img)
            self.use_image = True
        except Exception as e:
            print(f"Failed to load goal images: {e}")
            self.use_image = False

        # Animation state
        self.animation_timer = 0
        self.current_frame_index = 0
        self.ANIMATION_SPEED = 6

    def draw(self, surface, camera_x):
        screen_x = int(self.world_x - camera_x)
        
        if self.use_image and self.images:
            # Update animation
            self.animation_timer += 1
            if self.animation_timer >= self.ANIMATION_SPEED:
                self.animation_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.images)
            
            current_img = self.images[self.current_frame_index]
            surface.blit(current_img, (screen_x, self.y - self.height))
        else:
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
    config から platforms, cliffs, goal をまとめて生成
    """
    PLATFORM_HEIGHT = 20  # 足場の高さ（固定値）
    
    platforms = [
        Platform(
            world_x=p['world_x'],
            y=ground_y - p['y_offset'],
            width=p['width'],
            height=PLATFORM_HEIGHT
        )
        for p in config['platforms']
    ]

    # cliffs = config.get('cliffs', [])

    goal_initial_y = ground_y + config['goal'].get('world_y', 0)
    goal = Goal(
        world_x=config['goal']['world_x'],
        y=goal_initial_y,
        width=config['goal']['width'],
        height=config['goal']['height'],
        color=tuple(config['goal']['color'])
    )

    return platforms, goal


def is_on_ground(world_x, cliffs=None):
    """指定された世界座標 x が地面上かどうか。
    
    cliffs (崖のリスト) に含まれる区間であれば False (地面なし)、
    そうでなければ True (地面あり) を返す。
    """
    if not cliffs:
        return True

    for cliff in cliffs:
        if cliff['start_x'] <= world_x <= cliff['end_x']:
            return False
    
    return True
