# ゴール移動APIのサンプルスクリプト
# このファイルをscript_user.pyにリネームして使用してください

# 簡単なメモリ（状態を覚えておきたいとき用）
memory = {
    "goal_moved": False,
    "original_goal_pos": None,
}

def on_init(state, api):
    """
    ゲーム起動時 または script_user リロード時に1回だけ呼ばれる。
    state: make_state() が作った dict
    api  : GameAPI のインスタンス
    """
    # 元のゴール位置を保存
    memory["original_goal_pos"] = api.get_goal_position()
    print(f"初期ゴール位置: {memory['original_goal_pos']}")
    
    # 例1: ゲーム開始時にゴールを遠くに移動する
    # api.move_goal(500)  # 右に500ユニット移動
    # print(f"ゴールを移動しました: {api.get_goal_position()}")
    
    # 例2: ゴールを絶対位置に設定する
    # api.set_goal_position(2500)  # X=2500の位置に設定
    # print(f"ゴールを絶対位置に設定: {api.get_goal_position()}")

def on_tick(state, api):
    """
    毎フレーム main から呼ばれる。
    state: make_state() が作った dict
    api  : GameAPI のインスタンス
    """
    px = state["player"]["x"]
    goal_pos = api.get_goal_position()
    
    if goal_pos is None:
        return
    
    goal_x, goal_y = goal_pos
    
    # 例3: プレイヤーがゴールに近づいたら、ゴールを逃がす
    distance = abs(px - goal_x)
    if distance < 300 and not memory["goal_moved"]:
        print(f"プレイヤーが近づいた！ゴールを逃がします")
        api.move_goal(500)  # 右に500ユニット移動
        memory["goal_moved"] = True
        new_pos = api.get_goal_position()
        print(f"新しいゴール位置: {new_pos}")
    
    # プレイヤーが十分離れたらフラグをリセット
    if distance > 600:
        memory["goal_moved"] = False
    
    # 例4: 敵が全滅したらゴールをプレイヤーの近くに移動
    # enemy_count = len(state["enemies"])
    # if enemy_count == 0:
    #     # プレイヤーの300ユニット先に配置
    #     api.set_goal_position(px + 300, goal_y)
