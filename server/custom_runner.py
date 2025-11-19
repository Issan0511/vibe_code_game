# custom_runner.py
import socket
import json
import sys
import random
import importlib
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from scripts import script_user  # 来場者がいじるファイル

# ---- script_user から呼ばれる API（コマンドを貯めるだけ） ----
class RemoteAPI:
    def __init__(self):
        self.commands = []
        # config.json から元の値を読む（api.GameAPI と同じ発想）
        self.original_config = {}
        self._load_original_config()

    def _load_original_config(self):
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                self.original_config = json.load(f)
        except Exception:
            self.original_config = {}

    def get_original_config(self, key):
        keys = key.split('.')
        v = self.original_config
        for k in keys:
            if isinstance(v, dict):
                v = v.get(k)
            else:
                return None
        return v

    # ---- 乱数 ----
    def rand(self):
        return random.random()

    # ---- パラメータ変更系 → コマンドに変換 ----
    def set_gravity(self, g):
        self.commands.append({
            "op": "set_param",
            "key": "gravity",
            "value": g,
        })

    def set_max_speed(self, v):
        self.commands.append({
            "op": "set_param",
            "key": "max_speed",
            "value": v,
        })

    def set_config(self, key, value):
        self.commands.append({
            "op": "set_config",
            "key": key,
            "value": value,
        })

    def get_config(self, key):
        # state から現在の config を取得する（動的変更を反映）
        if hasattr(self, '_current_state') and 'config' in self._current_state:
            keys = key.split('.')
            current = self._current_state['config']
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            return current
        # フォールバック: state が無い場合は original_config を返す
        return self.get_original_config(key)

    # ---- 敵関連 ----
    def set_enemy_vel(self, enemy_id, vx, vy=None):
        cmd = {
            "op": "set_enemy_vel",
            "id": enemy_id,
            "vx": vx,
        }
        if vy is not None:
            cmd["vy"] = vy
        self.commands.append(cmd)

    def enemy_jump(self, enemy_id):
        self.commands.append({
            "op": "enemy_jump",
            "id": enemy_id,
        })

    def spawn_enemy(self, x, y):
        self.commands.append({
            "op": "spawn_enemy",
            "x": x,
            "y": y,
        })

    def spawn_snake(self, x, y, width=60, height=20, speed=3, move_range=150):
        """重力を受けない蛇タイプの敵を生成"""
        self.commands.append({
            "op": "spawn_snake",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "speed": speed,
            "move_range": move_range,
        })

    def set_max_jumps(self, max_jumps):
        """プレイヤーの最大ジャンプ回数を設定（複数段ジャンプ）"""
        self.commands.append({
            "op": "set_max_jumps",
            "value": int(max_jumps),
        })

    # ---- 背景色 ----
    def set_bg_color(self, rgb):
        self.commands.append({
            "op": "set_bg_color",
            "color": list(rgb),
        })

    # ---- ゴール ----
    def move_goal(self, dx, dy=0):
        self.commands.append({
            "op": "move_goal",
            "dx": dx,
            "dy": dy,
        })

    def get_goal_pos(self):
        # state から取得（main.py で state に goal を載せている）
        if hasattr(self, '_current_state') and 'goal' in self._current_state:
            return self._current_state['goal']
        return None

    def set_goal_pos(self, x, y):
        self.commands.append({
            "op": "set_goal_pos",
            "x": x,
            "y": y,
        })

    # ---- 足場 ----
    def set_platform_velocity(self, platform_index, vx, vy):
        self.commands.append({
            "op": "set_platform_velocity",
            "index": platform_index,
            "vx": vx,
            "vy": vy,
        })

    def stop_platform(self, platform_index):
        self.commands.append({
            "op": "stop_platform",
            "index": platform_index,
        })

    def get_platform_pos(self, platform_index):
        # state から取得（main.py で state に platforms を載せている）
        if hasattr(self, '_current_state') and 'platforms' in self._current_state:
            platforms = self._current_state['platforms']
            if 0 <= platform_index < len(platforms):
                return platforms[platform_index]
        return None

    # ---- 高レベルAPI ----
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


def main():
    host = "127.0.0.1"
    port = 50000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    f_r = sock.makefile("r")
    f_w = sock.makefile("w")

    api = RemoteAPI()
    did_init = False

    # script_user をリロードして最新のコードを読み込む
    importlib.reload(script_user)

    while True:
        line = f_r.readline()
        if not line:
            break
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("type") != "tick":
            continue

        state = msg["state"]
        
        # API に現在の state を保持させる
        api._current_state = state

        # 初回だけ on_init を呼ぶ（あれば）
        if not did_init and hasattr(script_user, "on_init"):
            try:
                api.commands.clear()
                script_user.on_init(state, api)
                cmds_init = api.commands[:]
                api.commands.clear()
                if cmds_init:
                    out = json.dumps({"type": "commands", "commands": cmds_init})
                    f_w.write(out + "\n")
                    f_w.flush()
            except Exception as e:
                print("on_init error:", e, file=sys.stderr)
            did_init = True

        # 毎フレーム on_tick 呼び出し
        try:
            api.commands.clear()
            script_user.on_tick(state, api)
            cmds = api.commands[:]
            api.commands.clear()
        except Exception as e:
            print("on_tick error:", e, file=sys.stderr)
            cmds = []

        out = json.dumps({"type": "commands", "commands": cmds})
        f_w.write(out + "\n")
        f_w.flush()

if __name__ == "__main__":
    main()
