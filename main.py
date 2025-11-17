import pygame
import sys
import json
import random
import importlib
import script_user
from api import GameAPI
from player import Player
from enemy import Enemy

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
GRAVITY = config['physics']['gravity']
player = Player(PLAYER_X, GROUND_Y, config)

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
            "x": camera_x + player.x_screen,  # 世界座標
            "screen_x": player.x_screen,  # 画面座標
            "y": player.y,
            "vy": player.vy,
            "on_ground": not player.is_jumping,
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
            if event.key == pygame.K_SPACE:
                player.start_jump()
        # スペースキーを離したらジャンプ持続終了
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                player.release_jump()

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
        player.update()

        # 段差との判定
        player_rect = player.get_rect()
        for platform in platforms:
            platform_rect = platform.get_rect(camera_x)
            if player_rect.colliderect(platform_rect):
                # 上から乗った場合
                if player.vy > 0 and player_rect.bottom <= platform_rect.top + 10:
                    player.land_on(platform_rect.top)

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
        shoe_rect = player.get_shoe_rect()
        
        # 敵との衝突判定
        enemies_to_remove = []
        enemy_bounced = False  # 敵を踏んだかどうか
        for enemy in enemies:
            enemy_rect = enemy.get_rect(camera_x)
            # 靴との当たり判定（敵が死ぬ）
            if shoe_rect.colliderect(enemy_rect) and player.vy > 0:
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
            player.stomp_enemy(keys[pygame.K_SPACE])

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
            player.reset()
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
    player.draw(screen)

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
