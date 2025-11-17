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
            with open('config.json', 'r', encoding='utf-8') as f:
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

