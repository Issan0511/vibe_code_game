# GameAPI リファレンス

`script_user.py` で使用できる GameAPI のメソッド一覧です。

## 目次

- [基本機能](#基本機能)
- [乱数](#乱数)
- [物理パラメータ](#物理パラメータ)
- [設定管理](#設定管理)
- [敵の制御](#敵の制御)
- [ゴールの制御](#ゴールの制御)
- [足場の制御](#足場の制御)
- [視覚効果](#視覚効果)
- [便利機能（高レベルAPI）](#便利機能高レベルapi)

---

## 基本機能

### `api.rand()`

0.0 から 1.0 の間のランダムな浮動小数点数を返します。

**戻り値:**
- `float`: 0.0 ≤ 値 < 1.0

**使用例:**
```python
# 50%の確率で処理を実行
if api.rand() < 0.5:
    print("当たり！")

# 1%の確率で敵をジャンプさせる
if api.rand() < 0.01:
    api.enemy_jump(enemy_id)
```

---

## 乱数

### `api.rand()`

詳細は[基本機能](#基本機能)を参照してください。

---

## 物理パラメータ

### `api.set_gravity(g)`

重力加速度を設定します。

**引数:**
- `g` (float): 重力値（-5.0 〜 5.0）
  - 正の値: 下向きの重力
  - 負の値: 上向きの重力

**使用例:**
```python
# 通常の重力
api.set_gravity(1.0)

# 弱い重力（月面のような感じ）
api.set_gravity(0.3)

# 逆重力
api.set_gravity(-1.0)
```

### `api.set_max_speed(v)`

プレイヤーの最大移動速度を設定します。

**引数:**
- `v` (float): 最大速度（0.5 〜 30.0）

**使用例:**
```python
# 通常の速度
api.set_max_speed(8.0)

# 高速移動
api.set_max_speed(20.0)

# スローモーション
api.set_max_speed(2.0)
```

---

## 設定管理

### `api.set_config(key, value)`

ゲームの設定値を動的に変更します。

**引数:**
- `key` (str): 設定のキー（ドット記法でネスト可能）
- `value`: 設定する値

**戻り値:**
- `bool`: 成功時は `True`、失敗時は `False`

**使用例:**
```python
# 物理設定を変更
api.set_config("physics.gravity", 1.5)
api.set_config("physics.acceleration", 1.2)
api.set_config("physics.max_speed", 10.0)

# プレイヤーの位置を変更
api.set_config("player.x", 300)
api.set_config("player.y", 400)
```

### `api.get_config(key)`

現在の設定値を取得します。

**引数:**
- `key` (str): 設定のキー（ドット記法でネスト可能）

**戻り値:**
- 設定値、存在しない場合は `None`

**使用例:**
```python
current_gravity = api.get_config("physics.gravity")
print(f"現在の重力: {current_gravity}")
```

### `api.get_original_config(key)`

`config.json` から読み込んだ元の設定値を取得します。

**引数:**
- `key` (str): 設定のキー（ドット記法でネスト可能）

**戻り値:**
- 元の設定値、存在しない場合は `None`

**使用例:**
```python
# 元の値を取得して2倍にする
original_speed = api.get_original_config("physics.max_speed")
if original_speed is not None:
    api.set_config("physics.max_speed", original_speed * 2)
```

---

## 敵の制御

### `api.spawn_enemy(x, y)`

指定した座標に敵を出現させます。

**引数:**
- `x` (float): ワールド座標でのx位置
- `y` (float): y座標

**制限:**
- 敵の最大数は300まで

**使用例:**
```python
# プレイヤーの右側に敵を出現
px = state["player"]["x"]
py = state["player"]["y"]
api.spawn_enemy(x=px + 400, y=py)

# ゴールの位置に敵を出現
goal_pos = api.get_goal_pos()
if goal_pos:
    api.spawn_enemy(x=goal_pos["x"], y=goal_pos["y"])
```

### `api.set_enemy_vel(enemy_id, vx, vy=None)`

敵の速度を直接設定します。

**引数:**
- `enemy_id` (int): 敵のID
- `vx` (float): x方向の速度（正で右、負で左）
- `vy` (float, optional): y方向の速度（正で下、負で上）
  - 省略すると重力に任せる（vyを変更しない）

**制限:**
- 速度の最大値は 15.0

**使用例:**
```python
# 敵をプレイヤーに向かって移動させる
for enemy in state["enemies"]:
    enemy_id = enemy["id"]
    dx = state["player"]["x"] - enemy["x"]
    distance = abs(dx) or 1.0
    
    # 正規化して速度を設定
    vx = 3.0 * (dx / distance)
    api.set_enemy_vel(enemy_id, vx)  # vyは省略して重力に任せる

# 敵を特定方向に飛ばす
api.set_enemy_vel(enemy_id, vx=5.0, vy=-10.0)
```

### `api.enemy_jump(enemy_id)`

敵をジャンプさせます。

**引数:**
- `enemy_id` (int): 敵のID

**注意:**
- 敵が地面に接している時のみジャンプします

**使用例:**
```python
# プレイヤーが近づいたら敵をジャンプさせる
for enemy in state["enemies"]:
    enemy_id = enemy["id"]
    dx = abs(state["player"]["x"] - enemy["x"])
    
    if dx < 100:  # 100ピクセル以内なら
        api.enemy_jump(enemy_id)
```

---

## ゴールの制御

### `api.get_goal_pos()`

ゴールの現在位置を取得します。

**戻り値:**
- `dict`: `{"x": world_x, "y": y}` または `None`

**使用例:**
```python
goal_pos = api.get_goal_pos()
if goal_pos:
    print(f"ゴール位置: x={goal_pos['x']}, y={goal_pos['y']}")
    
    # プレイヤーとゴールの距離を計算
    px = state["player"]["x"]
    distance = abs(px - goal_pos["x"])
```

### `api.move_goal(dx, dy=0)`

ゴールを相対的に移動させます。

**引数:**
- `dx` (float): x方向の移動量
- `dy` (float): y方向の移動量（デフォルト: 0）

**使用例:**
```python
# ゴールを右に100、上に50移動
api.move_goal(100, -50)

# ゴールを上に200移動（逃げる演出）
api.move_goal(0, -200)
```

### `api.set_goal_pos(x, y)`

ゴールを絶対座標で設定します。

**引数:**
- `x` (float): ワールド座標でのx位置
- `y` (float): y座標

**使用例:**
```python
# ゴールを特定位置に配置
api.set_goal_pos(1600, 520)
```

---

## 足場の制御

### `api.get_platform_pos(platform_index)`

足場の現在位置を取得します。

**引数:**
- `platform_index` (int): 足場のインデックス（0から始まる）

**戻り値:**
- `dict`: `{"x": world_x, "y": y}` または `None`

**使用例:**
```python
# 最初の足場の位置を取得
pos = api.get_platform_pos(0)
if pos:
    print(f"足場0の位置: x={pos['x']}, y={pos['y']}")
```

### `api.set_platform_velocity(platform_index, vx, vy)`

足場の移動速度を設定します。

**引数:**
- `platform_index` (int): 足場のインデックス（0から始まる）
- `vx` (float): x方向の速度（正で右、負で左）
- `vy` (float): y方向の速度（正で下、負で上）

**使用例:**
```python
# 足場を右に移動
api.set_platform_velocity(0, vx=2, vy=0)

# 足場を上に移動
api.set_platform_velocity(1, vx=0, vy=-1)

# 足場を斜めに移動
api.set_platform_velocity(2, vx=1, vy=-1)
```

### `api.stop_platform(platform_index)`

足場の移動を停止します。

**引数:**
- `platform_index` (int): 足場のインデックス（0から始まる）

**使用例:**
```python
# 最初の足場を停止
api.stop_platform(0)
```

---

## 視覚効果

### `api.set_bg_color(rgb)`

背景色を変更します。

**引数:**
- `rgb` (tuple): RGB値のタプル `(r, g, b)`
  - 各値は 0 〜 255

**使用例:**
```python
# 青い背景
api.set_bg_color((100, 150, 200))

# 赤い背景
api.set_bg_color((200, 50, 50))

# 暗い背景
api.set_bg_color((30, 30, 30))

# 時間経過で背景色を変える
time_sec = state["world"]["time_ms"] / 1000.0
r = int(128 + 127 * math.sin(time_sec))
api.set_bg_color((r, 100, 150))
```

---

## 便利機能（高レベルAPI）

これらは複雑な処理を簡単に実装できる高レベルAPIです。

### `api.spawn_enemy_periodically(state, memory, ...)`

定期的にプレイヤーの前方に敵を出現させます。

**引数:**
- `state` (dict): ゲーム状態（必須）
- `memory` (dict): メモリ辞書（必須、`"last_spawn_time"` キーを使用）
- `interval_ms` (int): 出現間隔（ミリ秒、デフォルト: 1000）
- `spawn_chance` (float): 出現確率（0.0〜1.0、デフォルト: 0.5）
- `offset_x` (float): プレイヤーからのx方向オフセット（デフォルト: 400）

**使用例:**
```python
# 基本的な使い方（1秒ごとに50%の確率で敵を出現）
api.spawn_enemy_periodically(state, memory)

# カスタマイズ: 2秒ごとに80%の確率で、プレイヤーの300ピクセル先に出現
api.spawn_enemy_periodically(
    state, memory,
    interval_ms=2000,
    spawn_chance=0.8,
    offset_x=300
)

# 高頻度で出現させる
api.spawn_enemy_periodically(state, memory, interval_ms=500, spawn_chance=1.0)
```

### `api.enemy_chase_and_jump(state, memory, ...)`

全ての敵がプレイヤーを追跡し、近づいたらランダムでジャンプします。

**引数:**
- `state` (dict): ゲーム状態（必須）
- `memory` (dict): メモリ辞書（必須、`"enemy_jump_cooldown"` キーを使用）
- `chase_distance` (float): ジャンプ判定する距離（デフォルト: 150）
- `jump_chance` (float): ジャンプ確率（0.0〜1.0、デフォルト: 0.01）
- `jump_cooldown_ms` (int): ジャンプのクールダウン（ミリ秒、デフォルト: 500）

**使用例:**
```python
# 基本的な使い方
api.enemy_chase_and_jump(state, memory)

# カスタマイズ: 200ピクセル以内で5%の確率でジャンプ、1秒のクールダウン
api.enemy_chase_and_jump(
    state, memory,
    chase_distance=200,
    jump_chance=0.05,
    jump_cooldown_ms=1000
)

# より攻撃的な敵（高確率、短クールダウン）
api.enemy_chase_and_jump(
    state, memory,
    chase_distance=200,
    jump_chance=0.1,
    jump_cooldown_ms=300
)
```

### `api.goal_move_on_approach(state, memory, ...)`

プレイヤーがゴールに接近したら、ゴールを移動させて元の位置に敵を出現させます（1回のみ実行）。

**引数:**
- `state` (dict): ゲーム状態（必須）
- `memory` (dict): メモリ辞書（必須、`"goal_approached"` キーを使用）
- `approach_distance` (float): 接近と判定する距離（デフォルト: 50）
- `move_dy` (float): ゴールを移動させるy方向の距離（デフォルト: -200）
- `spawn_enemy_at_goal` (bool): ゴールの元の位置に敵を出現させるか（デフォルト: True）

**使用例:**
```python
# 基本的な使い方（50ピクセル以内で発動、ゴールを200上に移動）
api.goal_move_on_approach(state, memory)

# カスタマイズ: 100ピクセル以内で発動、ゴールを300上に移動、敵は出現させない
api.goal_move_on_approach(
    state, memory,
    approach_distance=100,
    move_dy=-300,
    spawn_enemy_at_goal=False
)

# ゴールを下に移動させる（落とし穴風）
api.goal_move_on_approach(
    state, memory,
    move_dy=200
)
```

### `api.platform_oscillate(memory, ...)`

足場を往復運動させます（上下・左右・斜め対応）。

**引数:**
- `memory` (dict): メモリ辞書（必須、`"platform_initial_pos"`, `"platform_speeds"`, `"platform_range"` キーを使用）
- `platform_indices` (list): 制御する足場のインデックスリスト（デフォルト: [0, 1]）
- `speeds` (list): 各足場の初期速度タプルのリスト `[(vx1, vy1), (vx2, vy2), ...]`
  - vx: 正で右方向、負で左方向
  - vy: 正で下方向、負で上方向
  - デフォルト: `[(0, -1), (0, 1)]`（上下のみ）
- `move_range` (int): 移動範囲（ピクセル、デフォルト: 80)

**使用例:**
```python
# 基本的な使い方（足場0と1を上下に80ピクセルの範囲で往復）
api.platform_oscillate(memory)

# カスタマイズ: 3つの足場を制御、移動範囲を100ピクセルに
api.platform_oscillate(
    memory,
    platform_indices=[0, 1, 2],
    speeds=[(0, -1), (0, 1), (0, -2)],  # 3番目は2倍速
    move_range=100
)

# 足場を横方向にも動かす（左右往復）
api.platform_oscillate(
    memory,
    platform_indices=[0],
    speeds=[(2, 0)],  # 左右のみ往復
    move_range=120
)

# 斜め方向に往復
api.platform_oscillate(
    memory,
    platform_indices=[1],
    speeds=[(1, -1)],  # 右斜め上と左斜め下を往復
    move_range=100
)
```

---

## 完全な使用例

以下は `script_user.py` での完全な使用例です。

```python
# 来場者がいじるスクリプト

# 簡単なメモリ（状態を覚えておきたいとき用）
memory = {}

def on_init(state, api):
    """
    ゲーム起動時 または script_user リロード時に1回だけ呼ばれる。
    """
    # プレイヤーの速さを2倍に
    original_max_speed = api.get_original_config("physics.max_speed")
    if original_max_speed:
        api.set_config("physics.max_speed", original_max_speed * 2)
    
    # 背景色を青系に
    api.set_bg_color((100, 150, 200))
    
    # 重力を弱くする
    api.set_gravity(0.5)

def on_tick(state, api):
    """
    毎フレーム main から呼ばれる。
    """
    # 便利APIを組み合わせて使用
    api.spawn_enemy_periodically(state, memory, interval_ms=1500, spawn_chance=0.7)
    api.enemy_chase_and_jump(state, memory, chase_distance=200, jump_chance=0.05)
    api.goal_move_on_approach(state, memory, approach_distance=80)
    api.platform_oscillate(memory, move_range=100)
    
    # 時間経過で背景色を変化
    import math
    time_sec = state["world"]["time_ms"] / 1000.0
    r = int(100 + 50 * math.sin(time_sec * 0.5))
    g = int(150 + 50 * math.cos(time_sec * 0.3))
    api.set_bg_color((r, g, 200))
```

---

## Tips

### メモリの管理

便利機能を使う場合、`memory` 辞書を適切に初期化する必要があります。

```python
# 必要なキーを事前に初期化（オプション）
memory = {
    "last_spawn_time": 0,
    "enemy_jump_cooldown": {},
    "goal_approached": False,
    "platform_initial_pos": {},
    "platform_speeds": {},
    "platform_range": 80,
}
```

ただし、便利APIは自動的に必要なキーを初期化するため、空の辞書 `memory = {}` でも動作します。

### 状態の取得

`state` 辞書から様々な情報を取得できます:

```python
# プレイヤー情報
px = state["player"]["x"]
py = state["player"]["y"]

# 経過時間（ミリ秒）
time_ms = state["world"]["time_ms"]

# 全ての敵
for enemy in state["enemies"]:
    enemy_id = enemy["id"]
    ex = enemy["x"]
    ey = enemy["y"]
    # ...
```


---

## 制限事項

- 敵の最大数: 300体
- 重力の範囲: -5.0 〜 5.0
- 最大速度の範囲: 0.5 〜 30.0
- 敵の速度の最大値: 15.0
- RGB値の範囲: 0 〜 255

---

以上が GameAPI の全リファレンスです。自由に組み合わせて、面白いゲーム体験を作ってください！
