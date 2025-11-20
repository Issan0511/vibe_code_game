# 来場者がいじるスクリプト（デフォルト版）

memory = {}

def on_init(state, api):
    # ---- 初期化: 利用可能な足場インデックスを検出 ----
    # プラットフォームが存在するインデックスを探して memory に保存する
    # 最大チェック数は16（通常この範囲に収まる想定）
    available = []
    for i in range(16):
        pos = api.get_platform_pos(i)
        if pos is not None:
            available.append(i)

    memory['platform_indices'] = available

    # ---- 初期化: 各足場の移動方向を決める ----
    # 上下移動にするために vy を交互に -1 / +1 にして位相差を作る
    speeds = []
    for idx in range(len(available)):
        if idx % 2 == 0:
            speeds.append((0, -1))  # 上向きに移動開始
        else:
            speeds.append((0, 1))   # 下向きに移動開始
    memory['platform_speeds'] = speeds

    # ---- 初期化: プレイヤーが足場上にいる状態とバウンスタイマー管理 ----
    # on_platform: プラットフォームごとにプレイヤーが上にいるかを保持
    # bounce_end_time: バウンスが終わる時刻（ms）を保持
    on_platform = {}
    bounce_end_time = {}
    cur_time = state['world']['time_ms']
    for idx in available:
        on_platform[idx] = False
        bounce_end_time[idx] = 0
    memory['on_platform'] = on_platform
    memory['bounce_end_time'] = bounce_end_time


def on_tick(state, api):
    # ---- 足場検出が未完了なら再検出 ----
    # 実行時に動的に足場が追加される場合に備えて、見つかっていなければ再検索する
    if 'platform_indices' not in memory or not memory['platform_indices']:
        available = []
        for i in range(32):
            pos = api.get_platform_pos(i)
            if pos is not None:
                available.append(i)
        memory['platform_indices'] = available
        speeds = []
        for idx in range(len(available)):
            if idx % 2 == 0:
                speeds.append((0, -1))
            else:
                speeds.append((0, 1))
        memory['platform_speeds'] = speeds

        # 初期化されていない状態を整える
        on_platform = {}
        bounce_end_time = {}
        cur_time = state['world']['time_ms']
        for idx in available:
            on_platform[idx] = False
            bounce_end_time[idx] = 0
        memory['on_platform'] = on_platform
        memory['bounce_end_time'] = bounce_end_time

    # ---- 足場の上にジャンプ（着地）したら足場を跳ねさせる処理 ----
    # プレイヤーが『足場の上にいる』状態を判定して、着地（未着地->着地）時に跳ねる
    # 判定のしきい値: 横方向 64px、縦方向 16px
    player = state.get('player', {})
    px = player.get('x', 0.0)
    py = player.get('y', 0.0)
    cur_time = state['world']['time_ms']

    horiz_threshold = 64    # px: 横方向の判定幅（ピクセル）
    vert_threshold = 16     # px: 縦方向の判定幅（ピクセル）
    bounce_duration_ms = 400  # ms: バウンス持続時間
    bounce_vy = -8.0  # 上向き速度（負の値が上）

    # 準備: メモリ参照
    platform_indices = memory.get('platform_indices', [])
    platform_speeds = memory.get('platform_speeds', [])
    on_platform = memory.get('on_platform', {})
    bounce_end_time = memory.get('bounce_end_time', {})

    # 判定とバウンストリガー
    for idx in platform_indices:
        pos = api.get_platform_pos(idx)
        if pos is None:
            # プラットフォームが消えた場合はフラグをリセット
            on_platform[idx] = False
            bounce_end_time[idx] = 0
            continue

        dx = px - pos['x']
        dy = py - pos['y']
        # 横方向と縦方向の距離の絶対値で「上にいるか」を判定
        near_horiz = (dx >= -horiz_threshold and dx <= horiz_threshold)
        near_vert = (dy >= -vert_threshold and dy <= vert_threshold)
        is_on_top = near_horiz and near_vert

        previously_on = on_platform.get(idx, False)

        # 着地を検出（前回は上にいなかったが今回上にいる）
        if not previously_on and is_on_top:
            # 着地が発生したらバウンスを開始
            end_time = cur_time + bounce_duration_ms
            bounce_end_time[idx] = end_time
            on_platform[idx] = True
            # プラットフォームを上方向に跳ねさせる
            api.set_platform_velocity(idx, vx=0, vy=bounce_vy)
        else:
            # 状態更新: 上にいるフラグは現在の判定に合わせる（着地直後は True のまま）
            on_platform[idx] = is_on_top

        # バウンス期間が終了したらフラグをクリアして停止させる
        if bounce_end_time.get(idx, 0) and cur_time >= bounce_end_time.get(idx, 0):
            # バウンス終了
            bounce_end_time[idx] = 0
            # 移動を止める（次の処理で往復運動に含めるため）
            api.stop_platform(idx)
            # フラグは現在の接触判定に合わせる（着地から離れていれば False）
            on_platform[idx] = is_on_top

    # メモリに戻す
    memory['on_platform'] = on_platform
    memory['bounce_end_time'] = bounce_end_time

    # ---- 全ての非バウンス足場を上下に往復運動させる ----
    # バウンス中の足場はここに含めず、動きを優先させない
    non_bouncing_indices = []
    non_bouncing_speeds = []
    for pos_i, idx in enumerate(platform_indices):
        # バウンス中かどうか確認
        if bounce_end_time.get(idx, 0) and cur_time < bounce_end_time.get(idx, 0):
            # バウンス中なので往復運動に含めない
            continue
        non_bouncing_indices.append(idx)
        # platform_speeds 配列は platform_indices と対応している前提
        if pos_i < len(platform_speeds):
            non_bouncing_speeds.append(platform_speeds[pos_i])
        else:
            non_bouncing_speeds.append((0, -1))

    # move_range=80 は往復幅（ピクセル）
    if non_bouncing_indices:
        api.platform_oscillate(memory,
                               platform_indices=non_bouncing_indices,
                               speeds=non_bouncing_speeds,
                               move_range=80)

    # ---- 既存のデフォルト処理（そのまま残す） ----
    # 既存サンプルではここに他の処理が入りますが、今回は足場の移動とバウンスのみ変更しました
    pass
