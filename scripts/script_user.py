# 来場者がいじるスクリプト（デフォルト版）

memory = {}

def on_init(state, api):
    # ---------- プレイヤーの速さ1.5倍 ----------
    # max_speed = api.get_config("physics.max_speed")
    # acceleration = api.get_config("physics.acceleration")
    # api.set_config("physics.max_speed", max_speed * 1.5)
    # api.set_config("physics.acceleration", acceleration * 1.5)
    pass
  
def on_tick(state, api):
    # # プレイヤー位置と現在時刻を取得
    # px = state["player"]["x"]
    # py = state["player"]["y"]
    # now = state["world"]["time_ms"]

    # # ---------- ゴールに仕掛けるトラップの処理 (明示的な引数) ----------
    # api.goal_move_on_approach(state, memory, approach_distance=50, move_dy=-200, spawn_enemy_at_goal=True)
    # # ---------- プレイヤーに追従する敵の処理 (明示的な引数) ----------
    # api.enemy_chase_and_jump(state, memory, chase_distance=150, jump_chance=0.01, jump_cooldown_ms=500)
    # # ---------- 一定間隔で敵が出現する処理 (明示的にデフォルトを指定) ----------
    # api.spawn_enemy_periodically(state, memory, interval_ms=1000, spawn_chance=0.5, offset_x=400)
    # # ---------- 足場が動く処理 (明示的にデフォルトを指定) ----------
    # api.platform_oscillate(memory, platform_indices=[0, 1], speeds=[(0, -1), (0, 1)], move_range=80)

    pass

    