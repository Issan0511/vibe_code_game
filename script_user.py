# 来場者がいじるスクリプト

# 簡単なメモリ（状態を覚えておきたいとき用）
memory = {
    "last_spawn_time": 0,
    "enemy_jump_cooldown": {},  # 敵ごとのジャンプクールダウン
    "goal_approached": False,  # ゴール接近済みフラグ
    "platform_initial_y": {},  # 足場の初期y座標
    "platform_range": 80,  # 足場の移動範囲（ピクセル）
}

def on_init(state, api):
    """
    ゲーム起動時 または script_user リロード時に1回だけ呼ばれる。
    state: make_state() が作った dict
    api  : GameAPI のインスタンス
    """
    # プレイヤーの速さを2倍に上書き（元の値から計算）
    original_accel = api.get_original_config("physics.acceleration")
    original_decel = api.get_original_config("physics.deceleration")
    original_max_speed = api.get_original_config("physics.max_speed")
    
    if original_accel is not None:
        api.set_config("physics.acceleration", original_accel * 2)
    if original_decel is not None:
        api.set_config("physics.deceleration", original_decel * 2)
    if original_max_speed is not None:
        api.set_config("physics.max_speed", original_max_speed * 2)
    
    # 足場を上下に動かす
    api.set_platform_velocity(0, 0, -1)  # 最初の足場を上に移動
    api.set_platform_velocity(1, 0, 1)   # 2番目の足場を下に移動
    
    # ここに他の初期化処理を追加できる
    # 例: 背景色を変更
    # api.set_bg_color((100, 150, 200))

def on_tick(state, api):
    """
    毎フレーム main から呼ばれる。
    state: make_state() が作った dict
    api  : GameAPI のインスタンス
    """
    now = state["world"]["time_ms"]
    px = state["player"]["x"]
    py = state["player"]["y"]

    # 1) 1秒ごとにプレイヤーの先に敵を出す（1/2の確率で）
    if now - memory["last_spawn_time"] > 1000:
        memory["last_spawn_time"] = now
        if api.rand() < 0.5:
            api.spawn_enemy(x=px + 400, y=py)

    # 2) 全敵をプレイヤー追尾にする（X方向のみ、Y方向は重力に任せる）
    for enemy in state["enemies"]:
        enemy_id = enemy["id"]
        dx = px - enemy["x"]
        dist = abs(dx) or 1.0
        
        # 敵が近い場合はジャンプの判定
        if abs(dx) < 150:  # プレイヤーから150ピクセル以内
            # クールダウン管理
            if enemy_id not in memory["enemy_jump_cooldown"]:
                memory["enemy_jump_cooldown"][enemy_id] = 0
            
            # クールダウンが終わっていれば、一定確率でジャンプ
            if now - memory["enemy_jump_cooldown"][enemy_id] > 500:  # 500ms のクールダウン
                if api.rand() < 0.01:  # 1%の確率でジャンプ
                    api.enemy_jump(enemy_id)
                    memory["enemy_jump_cooldown"][enemy_id] = now
        
        # 追跡処理
        speed = 2.0
        # vx = speed * (dx / dist) if abs(dx) > 5 else 0  # 近すぎる場合は停止
        # api.set_enemy_vel(enemy_id, vx)  # vyは指定しない（重力に任せる）

    # 3) ゴールに接近したらゴールのy座標を上に40上げてゴールの元の座標に敵を出す
    goal_pos = api.get_goal_pos()
    
    goal_dist = abs(px - goal_pos["x"])
    
    if goal_dist < 50 and not memory["goal_approached"]:  # プレイヤーから150ピクセル以内
        memory["goal_approached"] = True
        api.move_goal(0, -200)  # y座標を40上に移動
        api.spawn_enemy(x=goal_pos["x"], y=goal_pos["y"])

    # 4) 足場を上下往復運動させる
    for i in [0, 1]:  # 最初の2つの足場を制御
        pos = api.get_platform_pos(i)
        if pos and i in memory["platform_initial_y"]:
            initial_y = memory["platform_initial_y"][i]
            platform_range = memory["platform_range"]
            
            # 移動範囲を超えたら方向転換
            if pos["y"] < initial_y - platform_range:
                api.set_platform_velocity(i, 0, 1)  # 下に移動
            elif pos["y"] > initial_y + platform_range:
                api.set_platform_velocity(i, 0, -1)  # 上に移動
    
