import pygame
import sys
import json
import random
import importlib
import script_user
from api import GameAPI
from player import Player
from enemy import Enemy
from level import load_level, is_on_ground

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

# 背景画像の読み込み
try:
    bg_image = pygame.image.load('background.png').convert()
    bg_width = bg_image.get_width()
    bg_height = bg_image.get_height()
except:
    bg_image = None
    bg_width = SCREEN_WIDTH
    bg_height = SCREEN_HEIGHT

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
# レベル（足場・地面・ゴール）をロード
# =========================
platforms, ground_segments, goal = load_level(config, GROUND_Y)

# =========================
# ゲーム状態とAPI
# =========================
state_ref = {
    "GRAVITY": GRAVITY,
    "MAX_SPEED": MAX_SPEED,
    "GROUND_Y": GROUND_Y,
    "config": config,
    "enemies": enemies,
    "platforms": platforms,
    "bg_color": tuple(config['background']['color']),
    "goal": goal,
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
            # R キーでリセット
            if event.key == pygame.K_r:
                # プレイヤーの位置をリセット
                player.reset()
                camera_x = 0.0
                camera_vx = 0.0
                
                # ゴールをリセット
                goal.reset_position()
                
                # 足場をリセット
                for platform in platforms:
                    platform.reset_position()
                
                # script_user のメモリをリセット
                try:
                    if hasattr(script_user, 'on_init'):
                        state_dict = make_state()
                        script_user.on_init(state_dict, api)
                        # メモリもリセット
                        if hasattr(script_user, 'memory'):
                            script_user.memory["goal_approached"] = False
                except Exception as e:
                    print("script_user.on_init error:", e)
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
        # 足場の更新
        # =========================
        platform_moves = {}  # 各足場の移動量を記録
        for i, platform in enumerate(platforms):
            dy = platform.update()
            platform_moves[i] = dy

        # =========================
        # プレイヤーの物理演算（ジャンプ）
        # =========================
        player.update()

        # 段差との判定
        player_rect = player.get_rect()
        player_on_platform = None  # プレイヤーが乗っている足場
        
        for i, platform in enumerate(platforms):
            platform_rect = platform.get_rect(camera_x)
            if player_rect.colliderect(platform_rect):
                # 上から乗った場合
                if player.vy > 0 and player_rect.bottom <= platform_rect.top + 10:
                    player.land_on(platform_rect.top)
                    player_on_platform = i
        
        # 地面判定（崖でない場所のみ）
        player_world_x = camera_x + player.x_screen
        if player.y >= GROUND_Y - player.height and player.vy > 0:
            if is_on_ground(ground_segments, player_world_x):
                # 地面がある場所に着地
                player.land_on(GROUND_Y)
            # 地面がない場所（崖）では着地しない
                    
        # プレイヤーが足場に乗っている場合、足場の移動に追従
        if player_on_platform is not None:
            dy = platform_moves[player_on_platform]
            if dy != 0:
                player.y += dy  # 足場の上下移動に追従

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
            enemy.update(platforms, GROUND_Y, GRAVITY, lambda x: is_on_ground(ground_segments, x))

        # 画面外に落ちた敵を削除
        enemies[:] = [e for e in enemies if e.y < SCREEN_HEIGHT + 100]

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

        # 崖判定（プレイヤーが地面の範囲外で、足場にも乗っていない場合）
        player_world_x = camera_x + player.x_screen
        if player.y >= GROUND_Y and not is_on_ground(ground_segments, player_world_x) and player_on_platform is None:
            game_over = True
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
    # 背景画像のスクロール描画
    if bg_image:
        # カメラ位置に応じた背景のオフセットを計算（視差効果のため、少し遅めにスクロール）
        bg_scroll_x = int(camera_x * 0.5) % bg_width
        
        # 画面を埋めるために必要な枚数を計算
        num_tiles = (SCREEN_WIDTH // bg_width) + 2
        
        for i in range(num_tiles):
            x_pos = i * bg_width - bg_scroll_x
            # 背景画像を縦に拡大して描画
            scaled_bg = pygame.transform.scale(bg_image, (bg_width, SCREEN_HEIGHT))
            screen.blit(scaled_bg, (x_pos, 0))
    else:
        # 背景画像が読み込めない場合は単色
        screen.fill(state_ref["bg_color"])

    # 地面（セグメントごとに描画）
    for segment in ground_segments:
        # 世界座標をスクリーン座標に変換
        screen_start_x = int(segment['start_x'] - camera_x)
        screen_end_x = int(segment['end_x'] - camera_x)
        
        # 画面内に描画する部分のみ計算
        visible_start_x = max(screen_start_x, 0)
        visible_end_x = min(screen_end_x, SCREEN_WIDTH)
        
        if visible_start_x < visible_end_x:
            ground_width = visible_end_x - visible_start_x
            ground_rect = pygame.Rect(visible_start_x, GROUND_Y, ground_width, SCREEN_HEIGHT - GROUND_Y)
            pygame.draw.rect(screen, tuple(config['ground']['color']), ground_rect)

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
