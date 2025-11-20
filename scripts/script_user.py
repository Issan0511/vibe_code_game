# 来場者がいじるスクリプト（デフォルト版）
# このファイルを編集してゲームをカスタマイズしてください！

memory = {}  # ゲームの状態を記憶する辞書（待機時間、タイマーなど）

def on_init(state, api):
    """
    ゲーム開始時（ゲーム起動時・リロード時）に1回だけ実行されます。
    ここで設定を変更してからゲームを起動してください。
    """
    # ---------- ゲームの物理演算 ----------
    # api.update_config を使ってゲームの設定を変更します。
    api.update_config({
        
        # ---------- プレイヤー設定 ----------
        "player": {
            "x": 200,          # プレイヤーの初期位置（画面左端からの距離）
            "scale": 1,
        },
        
        # ---------- 物理演算 ----------
        "physics": {
            "gravity": 0.8,           # 重力（高いほど落下が速くなる）
            "jump_strength": -10,     # ジャンプ力（負の値で上方向に作用）
            "acceleration": 0.333,    # 加速度（高いほど素早く加速）
            "deceleration": 0.2,      # 減速度（高いほど素早く減速）
            "max_speed": 5.33,        # 最大速度
            "bg_scroll_speed": 5      # 背景スクロール速度
        },
        
        # ---------- 地面設定 ----------
        "ground": {
            "y_offset": 80,           # 画面下部から地面までの距離
        },
        
        # ---------- ゴール（クリア条件） ----------
        "goal": {
            "world_x": 3000,  # ゴールの世界座標 X
            "world_y": 0,     # ゴールの世界座標 Y（相対）
            "width": 60,      # ゴールの幅
            "height": 80,     # ゴールの高さ
        },
        
        # ---------- 敵設定 ----------
        "enemies": [
            # 敵 1: 高い位置にいる敵
            {
            "world_x": 385,        # 敵の世界座標 X
            "move_range": 80,      # 敵が左右に動く幅
            "speed": 2,            # 敵の移動速度
            "width": 40,           # 敵の幅
            "height": 40,          # 敵の高さ
            "scale": 1,            # 表示スケール
            "use_gravity": False,  # 重力を使うか（False = 空中に浮く）
            "y_offset": 127        # 地面からの高さ
            },
            # 敵 2: 中間の高さにいる敵
            {
            "world_x": 1065,
            "move_range": 60,
            "speed": 1.5,
            "width": 40,
            "height": 40,
            "scale": 1,
            "use_gravity": False
            # y_offset がない場合は 0（地面上）
            },
            # 敵 3: 低い位置にいる敵
            {
            "world_x": 1941,
            "move_range": 100,
            "speed": 2,
            "width": 40,
            "height": 40,
            "scale": 1,
            "use_gravity": False,
            "y_offset": 112
            }
        ],
        
        # ---------- 足場（ジャンプ用の足場） ----------
        "platforms": [
            # 足場 1: 最初の足場
            {"world_x": 300, "y_offset": 100, "width": 150},
            # 足場 2
            {"world_x": 698, "y_offset": 110, "width": 160},
            # 足場 3
            {"world_x": 1300, "y_offset": 120, "width": 150},
            # 足場 4
            {"world_x": 2098, "y_offset": 84, "width": 120},
            # 足場 5
            {"world_x": 2289, "y_offset": 148, "width": 120},
            # 足場 6
            {"world_x": 2484, "y_offset": 87, "width": 140},
            # 足場 7: ゴール付近の足場
            {"world_x": 2720, "y_offset": 40, "width": 160}
        ],
        
        # ---------- 崖（地面がないエリア） ----------

        # 崖の間は地面がないので落ちるとゲームオーバー
        "cliffs": [
            # 崖 1
            {"start_x": 590, "end_x": 905},
            # 崖 2
            {"start_x": 1237, "end_x": 1653},
            # 崖 3: 最後の大きな崖
            {"start_x": 2041, "end_x": 2919}
        ]

    })
  
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

    # ---- プレイヤーのジャンプ検出と敵の挙動切替 ----
    # プレイヤーの上下移動を見て「ジャンプした瞬間」を検出し、
    # それに応じて近くの敵を逃げさせる／普段は敵がジャンプして接近するようにする。

    px = state["player"]["x"]
    py = state["player"]["y"]
    now = state["world"]["time_ms"]

    # ---- 定期的に敵を出現させる処理 ----
    # 1秒ごとに50%の確率でプレイヤーの前方に敵を出現させる
    # interval_ms: ミリ秒（1000ms = 1秒）
    # spawn_chance: 出現確率（0.0〜1.0）
    api.spawn_enemy_periodically(state, memory, interval_ms=1000, spawn_chance=0.5, offset_x=400)

    # 前回のプレイヤーY座標を取得（初回は現在値を保存してジャンプ検出しない）
    prev_py = memory.get("prev_player_y")
    if prev_py is None:
        memory["prev_player_y"] = py
        prev_py = py

    # 上方向への速い移動をジャンプ開始とみなす
    # 1.5 はピクセル/frame の閾値（小さい値で感度高め）。
    jump_threshold = 1.5  # px/frame（この値より上に動いたらジャンプと判定）
    is_player_jumping_now = (prev_py - py) > jump_threshold

    # 次回の比較のため現在のyを保存
    memory["prev_player_y"] = py

    # 敵関連のパラメータ
    flee_distance = 220          # プレイヤーがジャンプした時に逃げ出す範囲（ピクセル）
    flee_speed = 3.5             # 逃げるときの水平速度（敵に与えるvxの大きさ）
    approach_max_speed = 3.0     # プレイヤー不在時（ジャンプしてないとき）に敵が近づく最大速度
    approach_jump_distance = 150 # プレイヤーに近づくためにジャンプする距離の閾値（ピクセル）
    approach_jump_cooldown = 800 # 敵が連続でジャンプしないためのクールダウン（ms）
    flee_jump_cooldown = 400     # 逃げるジャンプのクールダウン（ms）

    # 初期化：ジャンプの最終時刻を敵ごとに管理する辞書
    if "last_approach_jump" not in memory:
        memory["last_approach_jump"] = {}
    if "last_flee_jump" not in memory:
        memory["last_flee_jump"] = {}

    # 敵ごとの振る舞いを決定
    for enemy in state.get("enemies", []):
        enemy_id = enemy.get("id")
        ex = enemy.get("x")
        ey = enemy.get("y")

        # プレイヤーに対する相対距離（x軸）を計算
        dx = ex - px
        # 距離ゼロ除算回避
        dist = abs(dx) or 1.0

        # ---- プレイヤーがジャンプした直後の処理（敵は逃げる） ----
        if is_player_jumping_now:
            # 近い敵だけ逃げる
            if dist < flee_distance:
                # プレイヤーから遠ざかる方向に速度をセット
                # dx>0 のとき敵は右にいるので左（負のvx）に動かす -> -(dx/dist)
                sign = 1.0 if dx >= 0 else -1.0
                # signは +1 なら敵は右側、逃げる方向は右へ、-1 は左へ
                vx = flee_speed * sign
                # 敵の水平速度を直接設定して逃がす
                api.set_enemy_vel(enemy_id, vx)

                # 逃げる際に一度ジャンプさせて離脱を助ける（地面にいる場合のみ効果あり）
                last_flee = memory["last_flee_jump"].get(enemy_id, -999999)
                if now - last_flee > flee_jump_cooldown:
                    api.enemy_jump(enemy_id)
                    memory["last_flee_jump"][enemy_id] = now
            else:
                # 遠くの敵は通常動作（特に制御しない）
                pass

        # ---- プレイヤーがジャンプしていない通常時の処理（敵が接近してジャンプ） ----
        else:
            # プレイヤーに向かって移動させる
            # dx = ex - px, 移動方向はプレイヤー方向 -> vx = - (dx/dist) * speed
            vx = - (dx / dist) * approach_max_speed
            api.set_enemy_vel(enemy_id, vx)

            # 近づいたらジャンプしてさらに接近する（ジャンプはクールダウン付き）
            last_ap_jump = memory["last_approach_jump"].get(enemy_id, -999999)
            if dist < approach_jump_distance and (now - last_ap_jump) > approach_jump_cooldown:
                # 30% の確率でジャンプして近づく（確率でバラつきを出す）
                if api.rand() < 0.3:
                    api.enemy_jump(enemy_id)
                    memory["last_approach_jump"][enemy_id] = now

    # （補足）プレイヤーがジャンプ中の間ずっと逃げさせたい場合は、
    # ジャンプ継続を検出するロジックに変更する必要があります。
    # ここでは「ジャンプした瞬間」をトリガーとして処理しています。
