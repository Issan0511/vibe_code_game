import pygame
import sys
import json
import random
import importlib
import script_user
from api import GameAPI

# =========================
# 設定の読み込み
# =========================
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 設定値を変数に展開
SCREEN_WIDTH = config['screen']['width']
SCREEN_HEIGHT = config['screen']['height']
FPS = config['screen']['fps']

PLAYER_X = config['player']['x']
GROUND_Y = SCREEN_HEIGHT - config['ground']['y_offset']

BG_SCROLL_SPEED = config['physics']['bg_scroll_speed']
ACCELERATION = config['physics']['acceleration']
DECELERATION = config['physics']['deceleration']
MAX_SPEED = config['physics']['max_speed']

# =========================
# 初期化
# =========================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("横スクロールゲーム（背景スクロール）")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 24)

# =========================
# プレイヤー
# =========================
player_width, player_height = config['player']['width'], config['player']['height']
player_y = GROUND_Y - player_height
player_vy = 0  # y方向の速度
player_color = tuple(config['player']['color'])

# 靴の設定
shoe_width, shoe_height = config['player']['shoe']['width'], config['player']['shoe']['height']
shoe_color = tuple(config['player']['shoe']['color'])

# ジャンプ関連の定数
GRAVITY = config['physics']['gravity']
JUMP_STRENGTH = -10  # configより小さく調整（元は-15）
is_jumping = False
jump_held = False  # ジャンプキーが押され続けているか
jump_time = 0  # ジャンプキーを押している時間
MAX_JUMP_TIME = 15  # 最大ジャンプ持続時間（フレーム数）

# ゲーム状態
game_over = False
game_clear = False

# =========================
# 背景（単色＋地面を自前描画）
#   → 実際には画像を読み込んでもOK
# =========================
BG_WIDTH = config['background']['tile_width']
camera_x = 0.0           # カメラのx位置（世界座標）
camera_vx = 0.0          # カメラの速度（慣性用）

# =========================
# 敵クラス（左右に動く）
# =========================
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

# =========================
# 段差クラス
# =========================
class Platform:
    def __init__(self, world_x, y, width, height):
        self.world_x = world_x
        self.y = y
        self.width = width
        self.height = height
        self.color = (139, 69, 19)

    def draw(self, surface, camera_x):
        screen_x = int(self.world_x - camera_x)
        rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)

    def get_rect(self, camera_x):
        screen_x = int(self.world_x - camera_x)
        return pygame.Rect(screen_x, self.y, self.width, self.height)

# =========================
# ゴールクラス
# =========================
class Goal:
    def __init__(self, world_x, y, width=60, height=80, color=None):
        self.world_x = world_x
        self.y = y
        self.width = width
        self.height = height
        self.color = color if color else (255, 215, 0)

    def draw(self, surface, camera_x):
        screen_x = int(self.world_x - camera_x)
        rect = pygame.Rect(screen_x, self.y - self.height, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        # 旗のポール
        pygame.draw.line(surface, (100, 100, 100), 
                        (screen_x + 10, self.y - self.height),
                        (screen_x + 10, self.y), 3)

    def get_rect(self, camera_x):
        screen_x = int(self.world_x - camera_x)
        return pygame.Rect(screen_x, self.y - self.height, self.width, self.height)

# =========================
# 敵を複数配置
# =========================
enemies = [
    Enemy(world_x=e['world_x'], y=GROUND_Y, 
          move_range=e['move_range'], speed=e['speed'],
          width=e['width'], height=e['height'],
          use_gravity=e.get('use_gravity', True))
    for e in config['enemies']
]

# =========================
# 段差を配置
# =========================
platforms = [
    Platform(world_x=p['world_x'], y=GROUND_Y - p['y_offset'],
             width=p['width'], height=p['height'])
    for p in config['platforms']
]

# =========================
# ゴール
# =========================
goal = Goal(world_x=config['goal']['world_x'], y=GROUND_Y,
            width=config['goal']['width'], height=config['goal']['height'],
            color=tuple(config['goal']['color']))

# =========================
# ゲーム状態とAPI
# =========================
state_ref = {
    "GRAVITY": GRAVITY,
    "MAX_SPEED": MAX_SPEED,
    "GROUND_Y": GROUND_Y,
    "config": config,
    "enemies": enemies,
    "bg_color": tuple(config['background']['color']),
}
api = GameAPI(state_ref)

# =========================
# 状態スナップショット関数
# =========================
def make_state():
    return {
        "player": {
            "x": camera_x + PLAYER_X,  # 世界座標
            "screen_x": PLAYER_X,  # 画面座標
            "y": player_y,
            "vy": player_vy,
            "on_ground": False,  # 必要なら判定結果を入れる
        },
        "world": {
            "time_ms": pygame.time.get_ticks(),
            "camera_x": camera_x,
            "gravity": GRAVITY,
        },
        "enemies": [
            {"id": e.id, "x": e.world_x, "y": e.y}
            for e in enemies
        ],
    }

# =========================
# script_user の初期化関数を呼ぶ
# =========================
try:
    if hasattr(script_user, 'on_init'):
        state_dict = make_state()
        script_user.on_init(state_dict, api)
except Exception as e:
    print("script_user.on_init error:", e)

# =========================
# メインループ
# =========================
running = True
while running:
    dt = clock.tick(FPS)  # ミリ秒
    # =========================
    # イベント処理
    # =========================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # スペースキーでジャンプ開始
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_jumping:
                player_vy = JUMP_STRENGTH
                is_jumping = True
                jump_held = True
                jump_time = 0
        # スペースキーを離したらジャンプ持続終了
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                jump_held = False

    # =========================
    # 入力処理
    # =========================
    if not game_over and not game_clear:
        keys = pygame.key.get_pressed()
        
        # 慣性を使った横移動（configから毎フレーム取得）
        accel = config['physics']['acceleration']
        decel = config['physics']['deceleration']
        max_spd = config['physics']['max_speed']

        if keys[pygame.K_RIGHT]:
            camera_vx += accel
            if camera_vx > max_spd:
                camera_vx = max_spd
        elif keys[pygame.K_LEFT]:
            camera_vx -= accel
            if camera_vx < -max_spd:
                camera_vx = -max_spd
        else:
            # キーが押されていない時は減速
            if camera_vx > 0:
                camera_vx -= decel
                if camera_vx < 0:
                    camera_vx = 0
            elif camera_vx < 0:
                camera_vx += decel
                if camera_vx > 0:
                    camera_vx = 0
        
        camera_x += camera_vx

        # =========================
        # プレイヤーの物理演算（ジャンプ）
        # =========================
        # ジャンプキーが押され続けている場合、上昇力を追加
        if jump_held and is_jumping and jump_time < MAX_JUMP_TIME and player_vy < 0:
            player_vy += GRAVITY * 0.3  # 重力を軽減して上昇を持続
            jump_time += 1
        else:
            player_vy += GRAVITY
        
        player_y += player_vy

        # 地面判定
        on_ground = False
        if player_y >= GROUND_Y - player_height:
            player_y = GROUND_Y - player_height
            player_vy = 0
            is_jumping = False
            jump_held = False
            jump_time = 0
            on_ground = True

        # 段差との判定
        player_rect = pygame.Rect(PLAYER_X - player_width // 2, player_y, player_width, player_height)
        for platform in platforms:
            platform_rect = platform.get_rect(camera_x)
            if player_rect.colliderect(platform_rect):
                # 上から乗った場合
                if player_vy > 0 and player_rect.bottom <= platform_rect.top + 10:
                    player_y = platform_rect.top - player_height
                    player_vy = 0
                    is_jumping = False
                    jump_held = False
                    jump_time = 0
                    on_ground = True

        # =========================
        # 更新処理
        # =========================
        # ---- script_user を呼ぶ ----
        try:
            state_dict = make_state()
            script_user.on_tick(state_dict, api)
        except Exception as e:
            # スクリプトが壊れてもゲームは落とさない
            print("script_user error:", e)

        for enemy in enemies:
            enemy.update(platforms, GROUND_Y, GRAVITY)

        # =========================
        # 当たり判定
        # =========================
        # 靴の当たり判定矩形を作成（プレイヤーの下部）
        shoe_rect = pygame.Rect(
            PLAYER_X - shoe_width // 2,
            player_y + player_height - shoe_height,
            shoe_width,
            shoe_height
        )
        
        # 敵との衝突判定
        enemies_to_remove = []
        enemy_bounced = False  # 敵を踏んだかどうか
        for enemy in enemies:
            enemy_rect = enemy.get_rect(camera_x)
            # 靴との当たり判定（敵が死ぬ）
            if shoe_rect.colliderect(enemy_rect) and player_vy > 0:
                enemies_to_remove.append(enemy)
                enemy_bounced = True  # 敵を踏んだ
            # プレイヤー本体との当たり判定（ゲームオーバー）
            elif player_rect.colliderect(enemy_rect):
                game_over = True
        
        # 敵を削除
        for enemy in enemies_to_remove:
            enemies.remove(enemy)
        
        # 敵を踏んだ場合のジャンプ処理
        if enemy_bounced:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                # ジャンプキーあり → 大ジャンプ（通常より高い）
                player_vy = JUMP_STRENGTH * 1.3  # 通常の1.3倍の力
                is_jumping = True
                jump_held = True
                jump_time = 0
            else:
                # ジャンプキーなし → 小ジャンプ
                player_vy = JUMP_STRENGTH * 0.4  # 通常の40%の力
                is_jumping = True
                jump_held = False
                jump_time = 0

        # ゴール判定
        goal_rect = goal.get_rect(camera_x)
        if player_rect.colliderect(goal_rect):
            game_clear = True
    else:
        # ゲーム終了後、Rキーでリスタート
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            # リセット
            game_over = False
            game_clear = False
            camera_x = 0.0
            camera_vx = 0.0
            player_y = GROUND_Y - player_height
            player_vy = 0
            is_jumping = False
            jump_held = False
            jump_time = 0
            # 敵をリセット
            enemies.clear()
            enemies.extend([
                Enemy(world_x=e['world_x'], y=GROUND_Y, 
                      move_range=e['move_range'], speed=e['speed'],
                      width=e['width'], height=e['height'],
                      use_gravity=e.get('use_gravity', True))
                for e in config['enemies']
            ])
            # スクリプトを再読み込み
            importlib.reload(script_user)
            # 初期化関数を再実行
            try:
                if hasattr(script_user, 'on_init'):
                    state_dict = make_state()
                    script_user.on_init(state_dict, api)
            except Exception as e:
                print("script_user.on_init error:", e)

    # =========================
    # 描画
    # =========================
    # 背景
    screen.fill(state_ref["bg_color"])

    # 地面
    ground_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
    pygame.draw.rect(screen, tuple(config['ground']['color']), ground_rect)

    # 簡単な「山」をタイル風に描画（背景スクロールの雰囲気用）
    # camera_x に応じて位置をずらす
    tile_offset = int(camera_x) % BG_WIDTH
    for i in range(-1, 3):  # 画面外まで少し余分に描画
        base_x = i * BG_WIDTH - tile_offset
        # 山1
        pygame.draw.polygon(
            screen,
            (34, 139, 34),
            [
                (base_x + 100, GROUND_Y),
                (base_x + 200, GROUND_Y - 120),
                (base_x + 300, GROUND_Y),
            ],
        )
        # 山2
        pygame.draw.polygon(
            screen,
            (34, 139, 34),
            [
                (base_x + 400, GROUND_Y),
                (base_x + 520, GROUND_Y - 150),
                (base_x + 640, GROUND_Y),
            ],
        )

    # プレイヤー（画面上で位置固定）
    player_rect = pygame.Rect(
        PLAYER_X - player_width // 2,
        player_y,
        player_width,
        player_height,
    )
    pygame.draw.rect(screen, player_color, player_rect)
    
    # 靴を描画（プレイヤーの下部）
    shoe_rect = pygame.Rect(
        PLAYER_X - shoe_width // 2,
        player_y + player_height - shoe_height,
        shoe_width,
        shoe_height
    )
    pygame.draw.rect(screen, shoe_color, shoe_rect)

    # 段差
    for platform in platforms:
        platform.draw(screen, camera_x)

    # 敵
    for enemy in enemies:
        enemy.draw(screen, camera_x)

    # ゴール
    goal.draw(screen, camera_x)

    # 情報表示
    if game_over:
        info_text = "GAME OVER! Rキーでリスタート"
        text_surf = font.render(info_text, True, (255, 0, 0))
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text_surf, text_rect)
    elif game_clear:
        info_text = "GOAL! ゲームクリア! Rキーでリスタート"
        text_surf = font.render(info_text, True, (0, 200, 0))
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text_surf, text_rect)
    else:
        info_text = f"左右キーで背景スクロール / スペースでジャンプ / Enemies: {len(enemies)}"
        text_surf = font.render(info_text, True, (0, 0, 0))
        screen.blit(text_surf, (10, 10))

    pygame.display.flip()

# 終了処理
pygame.quit()
sys.exit()
