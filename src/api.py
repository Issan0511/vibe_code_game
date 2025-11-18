# 安全API（コマンド相当）
import random
import json

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

class GameAPI:
    def __init__(self, main_ref):
        # main.py のグローバルか、Game クラスのインスタンスなどをぶら下げる
        self.m = main_ref
        # config.jsonから初期値を保持
        self.original_config = {}
        self._load_original_config()

    def _load_original_config(self):
        """config.json から元の値を読み込む"""
        try:
            with open('../config/config.json', 'r', encoding='utf-8') as f:
                self.original_config = json.load(f)
        except:
            pass

    def get_original_config(self, key):
        """元のconfig値を取得（ネストキー対応）"""
        keys = key.split('.')
        value = self.original_config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value

    # ---- 乱数 ----
    def rand(self):
        return random.random()

    # ---- パラメータ変更 ----
    def set_gravity(self, g):
        self.m["GRAVITY"] = clamp(g, -5.0, 5.0)

    def set_max_speed(self, v):
        self.m["MAX_SPEED"] = clamp(v, 0.5, 30.0)

    # ---- 敵関連 ----
    def set_enemy_vel(self, enemy_id, vx, vy=None):
        MAX_V = 15.0
        if vy is not None:
            speed2 = vx*vx + vy*vy
            if speed2 > MAX_V*MAX_V:
                s = (MAX_V / (speed2 ** 0.5))
                vx *= s
                vy *= s
        else:
            # vyが指定されていない場合はvxのみクランプ
            if abs(vx) > MAX_V:
                vx = MAX_V if vx > 0 else -MAX_V
        
        for e in self.m["enemies"]:
            if e.id == enemy_id:
                e.use_api_control = True
                e.vx = vx
                # vyが指定されている場合のみ上書き（重力を無視する場合）
                if vy is not None:
                    e.vy = vy
                break

    def enemy_jump(self, enemy_id):
        """敵にジャンプさせる"""
        jump_strength = -15  # プレイヤーと同じ値
        for e in self.m["enemies"]:
            if e.id == enemy_id:
                # 敵が地面に接しているかどうかを確認
                if e.y >= self.m.get("GROUND_Y", 0):
                    e.vy = jump_strength
                break

    def spawn_enemy(self, x, y):
        from main import Enemy  # 循環 import 回避するなら工夫
        if len(self.m["enemies"]) >= 300:
            return
        self.m["enemies"].append(
            Enemy(world_x=x, y=y, move_range=100, speed=2)
        )

    # ---- 背景色など ----
    def set_bg_color(self, rgb):
        r, g, b = rgb
        self.m["bg_color"] = (int(clamp(r,0,255)),
                              int(clamp(g,0,255)),
                              int(clamp(b,0,255)))

    # ---- config上書き ----
    def set_config(self, key, value):
        """
        configの値を上書きする
        例: api.set_config("physics.gravity", 1.5)
        例: api.set_config("player.x", 300)
        """
        keys = key.split('.')
        config = self.m.get("config")
        if config is None:
            return False
        
        # ネストされたキーをたどる
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 最後のキーに値を設定
        current[keys[-1]] = value
        return True
    
    def get_config(self, key):
        """
        configの値を取得する
        例: api.get_config("physics.gravity")
        """
        keys = key.split('.')
        config = self.m.get("config")
        if config is None:
            return None
        
        current = config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current

    # ---- ゴール関連 ----
    def move_goal(self, dx, dy=0):
        """
        ゴールの座標を相対的に変更する
        例: api.move_goal(100, -50)  # x方向に+100、y方向に-50移動
        """
        goal = self.m.get("goal")
        if goal:
            goal.world_x += dx
            goal.y += dy

    def get_goal_pos(self):
        """
        ゴールの座標を取得する
        戻り値: {"x": world_x, "y": y} または None
        """
        goal = self.m.get("goal")
        if goal:
            return {"x": goal.world_x, "y": goal.y}
        return None

    def set_goal_pos(self, x, y):
        """
        ゴールの座標を絶対的に設定する
        例: api.set_goal_pos(1600, 520)
        """
        goal = self.m.get("goal")
        if goal:
            goal.world_x = x
            goal.y = y

    # ---- 足場関連 ----
    def set_platform_velocity(self, platform_index, vx, vy):
        """
        足場の移動速度を設定する
        platform_index: 足場のインデックス（0から始まる）
        vx: x方向の速度（正で右、負で左）
        vy: y方向の速度（正で下、負で上）
        例: api.set_platform_velocity(0, 2, 0)  # 最初の足場を右に移動
        例: api.set_platform_velocity(1, 0, -1) # 2番目の足場を上に移動
        """
        platforms = self.m.get("platforms")
        if platforms and 0 <= platform_index < len(platforms):
            platforms[platform_index].set_velocity(vx, vy)

    def stop_platform(self, platform_index):
        """
        足場の移動を停止する
        platform_index: 足場のインデックス（0から始まる）
        """
        platforms = self.m.get("platforms")
        if platforms and 0 <= platform_index < len(platforms):
            platforms[platform_index].stop()

    def get_platform_pos(self, platform_index):
        """
        足場の座標を取得する
        戻り値: {"x": world_x, "y": y} または None
        """
        platforms = self.m.get("platforms")
        if platforms and 0 <= platform_index < len(platforms):
            platform = platforms[platform_index]
            return {"x": platform.world_x, "y": platform.y}
        return None

    # ---- 便利機能 ----
    def spawn_enemy_periodically(self, state, memory, interval_ms=1000, spawn_chance=0.5, offset_x=400):
        """
        定期的にプレイヤーの先に敵を出現させる
        
        引数:
            state: ゲーム状態
            memory: メモリdict（"last_spawn_time"キーを使用）
            interval_ms: 出現間隔（ミリ秒）
            spawn_chance: 出現確率（0.0〜1.0）
            offset_x: プレイヤーからのx方向のオフセット
        """
        if "last_spawn_time" not in memory:
            memory["last_spawn_time"] = 0
        
        now = state["world"]["time_ms"]
        px = state["player"]["x"]
        py = state["player"]["y"]
        
        if now - memory["last_spawn_time"] > interval_ms:
            memory["last_spawn_time"] = now
            if self.rand() < spawn_chance:
                self.spawn_enemy(x=px + offset_x, y=py)

    def enemy_chase_and_jump(self, state, memory, chase_distance=150, jump_chance=0.01, jump_cooldown_ms=500):
        """
        全敵をプレイヤー追尾させ、近い場合はランダムでジャンプ
        
        引数:
            state: ゲーム状態
            memory: メモリdict（"enemy_jump_cooldown"キーを使用）
            chase_distance: ジャンプ判定する距離
            jump_chance: ジャンプ確率（0.0〜1.0）
            jump_cooldown_ms: ジャンプのクールダウン（ミリ秒）
        """
        if "enemy_jump_cooldown" not in memory:
            memory["enemy_jump_cooldown"] = {}
        
        now = state["world"]["time_ms"]
        px = state["player"]["x"]
        
        for enemy in state["enemies"]:
            enemy_id = enemy["id"]
            dx = px - enemy["x"]
            
            # 敵が近い場合はジャンプの判定
            if abs(dx) < chase_distance:
                # クールダウン管理
                if enemy_id not in memory["enemy_jump_cooldown"]:
                    memory["enemy_jump_cooldown"][enemy_id] = 0
                
                # クールダウンが終わっていれば、一定確率でジャンプ
                if now - memory["enemy_jump_cooldown"][enemy_id] > jump_cooldown_ms:
                    if self.rand() < jump_chance:
                        self.enemy_jump(enemy_id)
                        memory["enemy_jump_cooldown"][enemy_id] = now

    def goal_move_on_approach(self, state, memory, approach_distance=50, move_dy=-200, spawn_enemy_at_goal=True):
        """
        ゴールに接近したらゴールを移動し、元の位置に敵を出現させる（1回のみ）
        
        引数:
            state: ゲーム状態
            memory: メモリdict（"goal_approached"キーを使用）
            approach_distance: 接近と判定する距離
            move_dy: ゴールを移動させるy方向の距離
            spawn_enemy_at_goal: ゴールの元の位置に敵を出現させるか
        """
        if "goal_approached" not in memory:
            memory["goal_approached"] = False
        
        px = state["player"]["x"]
        goal_pos = self.get_goal_pos()
        
        if goal_pos:
            goal_dist = abs(px - goal_pos["x"])
            
            if goal_dist < approach_distance and not memory["goal_approached"]:
                memory["goal_approached"] = True
                if spawn_enemy_at_goal:
                    self.spawn_enemy(x=goal_pos["x"], y=goal_pos["y"])
                self.move_goal(0, move_dy)

    def platform_oscillate(self, memory, platform_indices=[0, 1], speeds=[(0, -1), (0, 1)], move_range=80):
        """
        足場を往復運動させる（上下・左右・斜め対応）
        
        引数:
            memory: メモリdict（"platform_initial_pos"、"platform_speeds"、"platform_range"キーを使用）
            platform_indices: 制御する足場のインデックスリスト
            speeds: 各足場の初期速度タプルのリスト [(vx1, vy1), (vx2, vy2), ...]
                   vx: 正で右、負で左 / vy: 正で下、負で上
            move_range: 移動範囲（ピクセル）
        """
        if "platform_initial_pos" not in memory:
            memory["platform_initial_pos"] = {}
        if "platform_speeds" not in memory:
            memory["platform_speeds"] = {}
        if "platform_range" not in memory:
            memory["platform_range"] = move_range
        
        for idx, platform_index in enumerate(platform_indices):
            pos = self.get_platform_pos(platform_index)
            if pos:
                # 初期座標と速度を記録（初回のみ）
                if platform_index not in memory["platform_initial_pos"]:
                    memory["platform_initial_pos"][platform_index] = {"x": pos["x"], "y": pos["y"]}
                    # 初回に速度を設定
                    if idx < len(speeds):
                        vx, vy = speeds[idx]
                        memory["platform_speeds"][platform_index] = {"vx": vx, "vy": vy}
                        self.set_platform_velocity(platform_index, vx, vy)
                
                initial_pos = memory["platform_initial_pos"][platform_index]
                current_speed = memory["platform_speeds"][platform_index]
                platform_range = memory["platform_range"]
                
                # 移動範囲を超えたら方向転換
                new_vx = current_speed["vx"]
                new_vy = current_speed["vy"]
                
                # Y方向のチェック
                if pos["y"] < initial_pos["y"] - platform_range and current_speed["vy"] < 0:
                    new_vy = -current_speed["vy"]  # 下に反転
                elif pos["y"] > initial_pos["y"] + platform_range and current_speed["vy"] > 0:
                    new_vy = -current_speed["vy"]  # 上に反転
                
                # X方向のチェック
                if pos["x"] < initial_pos["x"] - platform_range and current_speed["vx"] < 0:
                    new_vx = -current_speed["vx"]  # 右に反転
                elif pos["x"] > initial_pos["x"] + platform_range and current_speed["vx"] > 0:
                    new_vx = -current_speed["vx"]  # 左に反転
                
                # 速度が変わった場合のみ更新
                if new_vx != current_speed["vx"] or new_vy != current_speed["vy"]:
                    memory["platform_speeds"][platform_index] = {"vx": new_vx, "vy": new_vy}
                    self.set_platform_velocity(platform_index, new_vx, new_vy)

