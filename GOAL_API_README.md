# ゴール座標操作API ドキュメント

## 概要
ゴールの座標を動的に変更できる3つのAPIメソッドが追加されました。これにより、ゲーム実行中にゴールの位置を相対的または絶対的に変更できます。

## 追加されたAPIメソッド

### 1. `move_goal(dx, dy=0)`
ゴールの座標を**相対的に**移動します。

#### パラメータ
- `dx` (float/int): X軸方向の移動量
  - 正の値: 右に移動
  - 負の値: 左に移動
- `dy` (float/int, オプション): Y軸方向の移動量（デフォルト: 0）
  - 正の値: 下に移動
  - 負の値: 上に移動

#### 戻り値
- `True`: 成功
- `False`: ゴールが存在しない場合

#### 使用例
```python
# ゴールを右に100ユニット移動
api.move_goal(100)

# ゴールを左に50ユニット移動
api.move_goal(-50)

# ゴールを右に200、上に100ユニット移動
api.move_goal(200, -100)
```

---

### 2. `set_goal_position(x, y=None)`
ゴールの座標を**絶対位置**で設定します。

#### パラメータ
- `x` (float/int): ワールド座標でのX位置
- `y` (float/int, オプション): Y座標（Noneの場合は変更しない）

#### 戻り値
- `True`: 成功
- `False`: ゴールが存在しない場合

#### 使用例
```python
# ゴールをX=2000の位置に設定（Yは変更なし）
api.set_goal_position(2000)

# ゴールを座標(3000, 400)に設定
api.set_goal_position(3000, 400)
```

---

### 3. `get_goal_position()`
ゴールの現在の座標を取得します。

#### パラメータ
なし

#### 戻り値
- `(world_x, y)`: ゴールの座標をタプルで返す
- `None`: ゴールが存在しない場合

#### 使用例
```python
# 現在のゴール位置を取得
pos = api.get_goal_position()
if pos:
    goal_x, goal_y = pos
    print(f"ゴール位置: X={goal_x}, Y={goal_y}")
```

---

## 実用例

### 例1: プレイヤーが近づいたらゴールを遠ざける
```python
memory = {"goal_moved": False}

def on_tick(state, api):
    px = state["player"]["x"]
    goal_pos = api.get_goal_position()
    
    if goal_pos and not memory["goal_moved"]:
        goal_x, goal_y = goal_pos
        distance = abs(px - goal_x)
        
        # 200ユニット以内に近づいたら
        if distance < 200:
            api.move_goal(500)  # 右に500ユニット移動
            memory["goal_moved"] = True
```

### 例2: ゴールを周期的に移動させる
```python
memory = {"time": 0}

def on_tick(state, api):
    memory["time"] += 1
    
    # 5秒ごとにゴールを移動
    if memory["time"] % 300 == 0:  # 60fps * 5秒 = 300フレーム
        # ランダムな方向に移動
        dx = (api.rand() - 0.5) * 600  # -300 ~ 300の範囲
        api.move_goal(dx)
```

### 例3: ゴールを初期位置から遠くに配置
```python
def on_init(state, api):
    # 元の位置を取得
    original_pos = api.get_goal_position()
    if original_pos:
        original_x, original_y = original_pos
        # 元の位置から1000ユニット右に移動
        api.set_goal_position(original_x + 1000, original_y)
```

### 例4: 敵を全滅させたらゴールを近づける
```python
memory = {"goal_brought_close": False}

def on_tick(state, api):
    enemy_count = len(state["enemies"])
    
    # 敵が全滅したらゴールをプレイヤーの近くに移動
    if enemy_count == 0 and not memory["goal_brought_close"]:
        px = state["player"]["x"]
        py = state["player"]["y"]
        api.set_goal_position(px + 300, py)
        memory["goal_brought_close"] = True
```

---

## サンプルスクリプト

完全な動作例は `script_user_goal_example.py` を参照してください。このファイルを `script_user.py` にリネームすることで、ゴール移動機能を試すことができます。

---

## 注意事項

1. **座標系について**
   - X座標: ワールド座標（world_x）を使用
   - Y座標: 画面座標系（上が小さい値、下が大きい値）

2. **即座に反映される**
   - `move_goal`と`set_goal_position`は呼び出し直後に反映されます

3. **画面外への移動**
   - ゴールが画面外に移動しても問題ありませんが、プレイヤーが到達できない位置に置かないように注意してください

4. **エラーハンドリング**
   - すべてのメソッドは、ゴールが存在しない場合でも安全に動作します（例外を発生させません）

---

## 技術的な詳細

### 実装箇所
- **api.py**: `GameAPI`クラスに3つのメソッドを追加
- **main.py**: `state_ref`ディクショナリに`goal`参照を追加

### テスト
すべてのAPIメソッドは単体テストでテスト済みです。テストは以下を含みます：
- 相対移動の正確性
- 絶対位置設定の正確性
- 座標取得の正確性
- ゴールが存在しない場合のエラーハンドリング
