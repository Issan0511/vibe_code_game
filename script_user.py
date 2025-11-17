# 来場者がいじるスクリプト

# 簡単なメモリ（状態を覚えておきたいとき用）
memory = {
    "last_spawn_time": 0,
    "enemy_jump_cooldown": {},  # 敵ごとのジャンプクールダウン
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
        dy = py - enemy["y"]
        dist = abs(dx) or 1.0
        
        # 敵が近い場合はジャンプの判定
        if abs(dx) < 150:  # プレイヤーから150ピクセル以内
            # クールダウン管理
            if enemy_id not in memory["enemy_jump_cooldown"]:
                memory["enemy_jump_cooldown"][enemy_id] = 0
            
            # クールダウンが終わっていれば、一定確率でジャンプ
            if now - memory["enemy_jump_cooldown"][enemy_id] > 500:  # 500ms のクールダウン
                if api.rand() < 0.3:  # 30%の確率でジャンプ
                    api.enemy_jump(enemy_id)
                    memory["enemy_jump_cooldown"][enemy_id] = now
        
        # 追跡処理
        speed = 2.0
        vx = speed * (dx / dist) if abs(dx) > 5 else 0  # 近すぎる場合は停止
        api.set_enemy_vel(enemy_id, vx)  # vyは指定しない（重力に任せる）
