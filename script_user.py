# 来場者がいじるスクリプト

memory = {}

def on_init(state, api):
    # 初期化: 最終出現時刻と、速度を付与済みの敵IDリストを用意
    memory.setdefault("last_spawn_ms", -9999)
    memory.setdefault("handled_enemies", [])

    # ゴールトラップ用の状態を初期化
    # goal_trap_armed: トラップが発動可能か
    # goal_trap_last_trigger_ms: 最終発動時刻
    # goal_trap_cooldown: リチャージ時間（ms）
    # trap_active: トラップが現在アクティブか
    # trap_end_ms: トラップ効果の終了時刻
    # goal_original_pos: トラップ発動前のゴール位置を保存
    # trap_platforms: トラップで落とす／動かす足場のインデックスリスト
    memory.setdefault("goal_trap_armed", True)
    memory.setdefault("goal_trap_last_trigger_ms", -9999)
    memory.setdefault("goal_trap_cooldown", 10000)
    memory.setdefault("trap_active", False)
    memory.setdefault("trap_end_ms", -1)
    memory.setdefault("goal_original_pos", None)
    memory.setdefault("trap_platforms", [0, 1])
    memory.setdefault("trap_platform_fall_vy", 6.0)

def on_tick(state, api):
    # プレイヤー位置と現在時刻を取得
    px = state["player"]["x"]
    py = state["player"]["y"]
    now = state["world"]["time_ms"]

    # ---------- ゴールに仕掛けるトラップの処理 ----------
    goal = api.get_goal_pos()
    # 発動条件: ゴールが存在し、トラップが装填されており、クールダウン明け、かつプレイヤーが近い
    if goal is not None:
        gx = goal.get("x")
        gy = goal.get("y")
        # 近接判定距離（横・縦ともに）
        approach_distance = 80

        # トラップを発動する条件
        if (memory.get("goal_trap_armed")
                and now - memory.get("goal_trap_last_trigger_ms", -9999) >= memory.get("goal_trap_cooldown", 10000)
                and abs(px - gx) <= approach_distance
                and abs(py - gy) <= approach_distance):
            # 発動: ゴールを上に逃がしつつ、ゴール付近に敵を複数出現させ、足場を落とす
            memory["goal_original_pos"] = {"x": gx, "y": gy}
            # ゴールを相対移動（上に逃がす）
            api.move_goal(0, -180)

            # ゴール周辺に敵を3体出現させる（左右に分散）
            offsets = [-80.0, 0.0, 80.0]
            for off in offsets:
                api.spawn_enemy(x=gx + off, y=gy)

            # 足場を落とす（存在すれば）
            for pi in memory.get("trap_platforms", []):
                api.set_platform_velocity(pi, vx=0, vy=memory.get("trap_platform_fall_vy", 6.0))

            # トラップ状態をセット
            memory["trap_active"] = True
            memory["trap_end_ms"] = now + 3500
            memory["goal_trap_last_trigger_ms"] = now
            memory["goal_trap_armed"] = False

    # トラップ効果の終了処理（一定時間後に元に戻す）
    if memory.get("trap_active"):
        if now >= memory.get("trap_end_ms", 0):
            orig = memory.get("goal_original_pos")
            if orig is not None:
                # ゴールを元の位置に戻す
                api.set_goal_pos(orig.get("x"), orig.get("y"))
                memory["goal_original_pos"] = None

            # 足場の移動を停止
            for pi in memory.get("trap_platforms", []):
                api.stop_platform(pi)

            memory["trap_active"] = False
            # トラップはクールダウン後に再装填される（on_tick の後半で再装填処理あり）

    # クールダウンが終われば再装填
    if (not memory.get("goal_trap_armed")
            and now - memory.get("goal_trap_last_trigger_ms", -9999) >= memory.get("goal_trap_cooldown", 10000)
            and not memory.get("trap_active", False)):
        memory["goal_trap_armed"] = True

    # ---------- 既存の敵出現＆挙動処理（そのまま保持） ----------
    # 3秒ごとにプレイヤーの右上に敵を出現させる
    # 右上のオフセットは (x+400, y-400)
    if now - memory["last_spawn_ms"] >= 3000:
        spawn_x = px + 400.0
        spawn_y = py - 400.0
        api.spawn_enemy(x=spawn_x, y=spawn_y)
        memory["last_spawn_ms"] = now

    # 出現した敵に一度だけ左向きの速度を与え、右上から降ってくる挙動にする
    # 出現直後は位置がプレイヤーの右かつ上にあるはずなので、それを目印にする
    for enemy in state["enemies"]:
        eid = enemy["id"]
        # すでに速度付与済みならスキップ
        if eid in memory["handled_enemies"]:
            continue
        # 右上から来る敵の判定 (プレイヤーの右側かつ上にいる)
        if enemy["x"] > px + 150 and enemy["y"] < py - 50:
            # 左方向の水平速度を与える（垂直は重力に任せる）
            api.set_enemy_vel(eid, -3.0)
            memory["handled_enemies"].append(eid)

    # handled_enemies が無限に増えないように適度に trims
    if len(memory["handled_enemies"]) > 500:
        memory["handled_enemies"] = memory["handled_enemies"][-500:]
