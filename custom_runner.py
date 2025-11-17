# custom_runner.py
import socket
import json
import sys
import random
import importlib

import script_user  # 来場者がいじるファイル

# ---- script_user から呼ばれる API（コマンドを貯めるだけ） ----
class RemoteAPI:
    def __init__(self):
        self.commands = []
        # config.json から元の値を読む（api.GameAPI と同じ発想）
        self.original_config = {}
        self._load_original_config()

    def _load_original_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
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
        # 必要なら state 側にも config を載せて同期する方が堅い
        # とりあえずは original_config ベースで返す簡易版
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


def main():
    host = "127.0.0.1"
    port = 50000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    f_r = sock.makefile("r")
    f_w = sock.makefile("w")

    api = RemoteAPI()
    did_init = False

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
