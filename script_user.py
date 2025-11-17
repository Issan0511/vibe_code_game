# 来場者がいじるスクリプト

# 簡単なメモリ（状態を覚えておきたいとき用）
memory = {}

def on_init(state, api):
    """
    ゲーム起動時 または script_user リロード時に1回だけ呼ばれる。
    state: make_state() が作った dict
    api  : GameAPI のインスタンス
    """
    # ここに初期化処理を追加できる
    pass

def on_tick(state, api):
    """
    毎フレーム main から呼ばれる。
    state: make_state() が作った dict
    api  : GameAPI のインスタンス
    
    便利API使用例:
    # 定期的に敵を出現
    api.spawn_enemy_periodically(state, memory)
    
    # 敵の追跡とジャンプ
    api.enemy_chase_and_jump(state, memory)
    
    # ゴール接近時の処理
    api.goal_move_on_approach(state, memory)
    
    # 足場の往復運動
    api.platform_oscillate(memory)
    """
    # ここに毎フレームの処理を追加できる
    pass
    
