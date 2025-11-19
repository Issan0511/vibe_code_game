import pygame


class Player:
    def __init__(self, x_screen, ground_y, config):
        # 基本設定
        self.x_screen = x_screen  # 画面内での固定x位置（世界座標は camera_x + x_screen）
        self.width = config['player']['width']
        self.height = config['player']['height']
        self.color = tuple(config['player']['color'])

        # 靴
        shoe_conf = config['player']['shoe']
        self.shoe_width = shoe_conf['width']
        self.shoe_height = shoe_conf['height']
        self.shoe_color = tuple(shoe_conf['color'])

        # 画像読み込み
        try:
            self.image = pygame.image.load('assets/player.png').convert_alpha()
            # 画像を適切なサイズにスケール（1.2倍）
            self.image = pygame.transform.scale(self.image, (int(self.width * 1.2), int(self.height * 1.2)))
            self.use_image = True
        except:
            self.image = None
            self.use_image = False

        # 物理パラメータ
        self.ground_y = ground_y
        self.gravity = config['physics']['gravity']
        self.jump_strength = -10      # 元の JUMP_STRENGTH と同じ
        self.max_jump_time = 15       # MAX_JUMP_TIME と同じ

        # 状態
        self.y = self.ground_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0
        self.facing_right = False  # デフォルトは左向き
        
        # 複数段ジャンプ
        self.max_jumps = 1  # デフォルトは1回（通常ジャンプ）
        self.jump_count = 0  # 現在のジャンプ回数

    # 入力関連 ---------------------------------
    def start_jump(self):
        if self.jump_count < self.max_jumps:
            self.vy = self.jump_strength
            self.is_jumping = True
            self.jump_held = True
            self.jump_time = 0
            self.jump_count += 1

    def release_jump(self):
        self.jump_held = False

    def reset(self):
        """プレイヤーの状態を初期状態にリセット"""
        self.y = self.ground_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0

    # 物理更新 ---------------------------------
    def update(self):
        # 可変ジャンプ（押し続けている間は重力を軽減）
        if self.jump_held and self.is_jumping and self.jump_time < self.max_jump_time and self.vy < 0:
            self.vy += self.gravity * 0.3
            self.jump_time += 1
        else:
            self.vy += self.gravity

        self.y += self.vy
        
        # 地面判定は main.py で行う（崖判定のため）

    def land_on(self, surface_y):
        """platform や地面の上に着地するときに呼ぶ"""
        self.y = surface_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0
        self.jump_count = 0  # 着地したらジャンプカウントをリセット

    # 敵を踏んだときのバウンド ------------------
    def stomp_enemy(self, jump_key_pressed: bool):
        if jump_key_pressed:
            # ジャンプキーあり → 大ジャンプ
            self.vy = self.jump_strength * 1.3
            self.is_jumping = True
            self.jump_held = True
            self.jump_time = 0
        else:
            # ジャンプキーなし → 小ジャンプ
            self.vy = self.jump_strength * 0.4
            self.is_jumping = True
            self.jump_held = False
            self.jump_time = 0

    # 描画・当たり判定 --------------------------
    def get_rect(self):
        return pygame.Rect(
            self.x_screen - self.width // 2,
            self.y,
            self.width,
            self.height,
        )

    def get_shoe_rect(self):
        return pygame.Rect(
            self.x_screen - self.shoe_width // 2,
            self.y + self.height - self.shoe_height,
            self.shoe_width,
            self.shoe_height,
        )

    def draw(self, surface):
        if self.use_image and self.image:
            # 画像を描画（中央揃え、サイズ調整を考慮）
            image_width = int(self.width * 1.2)
            image_height = int(self.height * 1.2)
            image_x = self.x_screen - image_width // 2
            image_y = self.y - (image_height - self.height)  # 足元を基準に
            
            # 向きに応じて反転
            if self.facing_right:
                surface.blit(self.image, (image_x, image_y))

            else:
                flipped_image = pygame.transform.flip(self.image, True, False)
                surface.blit(flipped_image, (image_x, image_y))                
        else:
            # フォールバック: 矩形描画
            pygame.draw.rect(surface, self.color, self.get_rect())
            pygame.draw.rect(surface, self.shoe_color, self.get_shoe_rect())

    # リセット -----------------------------------
    def reset(self):
        self.y = self.ground_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0
        self.jump_count = 0
