# 来場者がいじるスクリプト（デフォルト版）

memory = {}

def on_init(state, api):
    # ---------- プレイヤーの速さ1.5倍 ----------
    # max_speed = api.get_config("physics.max_speed")
    # acceleration = api.get_config("physics.acceleration")
    # api.set_config("physics.max_speed", max_speed * 1.5)
    # api.set_config("physics.acceleration", acceleration * 1.5)


    
    # ---- 2段ジャンプを有効化 ----
    api.set_max_jumps(3)
    pass
  
def on_tick(state, api):
    # プレイヤー位置と現在時刻を取得
    px = state["player"]["x"]
    py = state["player"]["y"]
    now = state["world"]["time_ms"]

    # ---- 敵の出現頻度を減らす ----
    # 2秒ごと（2000ms）に25%の確率で敵を出現させる（敵の総数を抑える）
    api.spawn_enemy_periodically(state, memory, interval_ms=2000, spawn_chance=0.25, offset_x=400)

    # ---- 出現した敵を追尾させる（メインの追尾処理） ----
    # chase_distance=800: 遠くからでも追いかける（単位: ピクセル）
    # jump_chance=0.02: 2%の確率でジャンプして障害物を越える動作をする
    api.enemy_chase_and_jump(state, memory, chase_distance=800, jump_chance=0.02, jump_cooldown_ms=700)

    # ---- 追跡を強化するための補助処理（個別の速度調整） ----
    # 各敵に対してプレイヤー方向へ一定の横速度を与えて確実に接近させる
    # vx=4.0 は敵の移動速度（ピクセル/フレーム相当）を示す目安
    for enemy in state["enemies"]:
        enemy_id = enemy["id"]
        dx = px - enemy["x"]
        dist = abs(dx) or 1.0
        vx = 4.0 * (dx / dist)
        api.set_enemy_vel(enemy_id, vx)

    # # プレイヤー位置と現在時刻を取得（参考のまま残す）
    # px = state["player"]["x"]
    # py = state["player"]["y"]
    # now = state["world"]["time_ms"]

    # # ---------- ゴールに仕掛けるトラップの処理 ----------
    # api.goal_move_on_approach()
    # # ---------- プレイヤーに追従する敵の処理 ----------
    # api.enemy_chase_and_jump()
    # # ---------- 一定間隔で敵が出現する処理 ----------
    # api.spawn_enemy_periodically()
    # # ---------- 足場が動く処理 ----------
    # api.platform_oscillate()
    pass
