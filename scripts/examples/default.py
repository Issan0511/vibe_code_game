# 来場者がいじるスクリプト（デフォルト版）

memory = {}

def on_init(state, api):
    # ---------- プレイヤーの速さ1.5倍 ----------
    max_speed = api.get_config("physics.max_speed")
    acceleration = api.get_config("physics.acceleration")
    api.set_config("physics.max_speed", max_speed * 1.5)
    api.set_config("physics.acceleration", acceleration * 1.5)
    pass
  
def on_tick(state, api):
    # # プレイヤー位置と現在時刻を取得
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

    