import pygame


class Enemy:
    _next_id = 0

    def __init__(self, world_x, y, move_range=100, speed=2, width=40, height=40, use_gravity=True):
        """
        world_x: 世界座標でのx
        y      : 画面上でのy（地面にいる感じ）
        move_range: 中心から左右にどれくらい動くか
        speed  : 左右の移動速度
        use_gravity: 重力を適用するかどうか
        """
        self.id = Enemy._next_id
        Enemy._next_id += 1
        self.center_x = world_x
        self.world_x = world_x
        self.y = y
        self.move_range = move_range
        self.speed = speed
        self.width = width
        self.height = height
        self.direction = 1  # 1:右へ, -1:左へ
        self.color = (255, 80, 80)
        self.use_gravity = use_gravity
        self.vx = 0  # x方向の速度（API制御用）
        self.vy = 0  # y方向の速度
        self.use_api_control = False  # APIからの制御を使うかどうか

    def move_patrol(self):
        """左右に往復運動"""
        self.world_x += self.speed * self.direction
        if self.world_x > self.center_x + self.move_range:
            self.world_x = self.center_x + self.move_range
            self.direction *= -1
        elif self.world_x < self.center_x - self.move_range:
            self.world_x = self.center_x - self.move_range
            self.direction *= -1

    def update(self, platforms, ground_y, gravity):
        # 移動処理
        if self.use_api_control:
            # APIから速度が設定されている場合
            self.world_x += self.vx
            # API制御の場合もY方向の速度は重力で制御される
            # （vyがAPIで設定されても重力が上書きする）
        else:
            # 通常の往復運動
            self.move_patrol()
        
        # 重力を適用
        if self.use_gravity:
            self.vy += gravity
            self.y += self.vy
            
            # 地面判定
            if self.y >= ground_y:
                self.y = ground_y
                self.vy = 0
            
            # 段差との判定
            enemy_rect_world = pygame.Rect(
                self.world_x - self.width // 2,
                self.y - self.height,
                self.width,
                self.height
            )
            
            for platform in platforms:
                platform_rect_world = pygame.Rect(
                    platform.world_x,
                    platform.y,
                    platform.width,
                    platform.height
                )
                
                if enemy_rect_world.colliderect(platform_rect_world):
                    # 上から乗った場合
                    if self.vy > 0 and enemy_rect_world.bottom <= platform_rect_world.top + 10:
                        self.y = platform_rect_world.top
                        self.vy = 0

    def draw(self, surface, camera_x):
        # world_x を camera_x でずらして画面上の位置に変換
        screen_x = int(self.world_x - camera_x)
        rect = pygame.Rect(screen_x - self.width // 2,
                           self.y - self.height,  # yは足元位置として使う
                           self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)

    def get_rect(self, camera_x):
        """当たり判定用の矩形を返す"""
        screen_x = int(self.world_x - camera_x)
        return pygame.Rect(screen_x - self.width // 2,
                          self.y - self.height,
                          self.width, self.height)
