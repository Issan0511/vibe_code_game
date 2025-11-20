import pygame
import json
import sys
import os

# 設定ファイルのパス
CONFIG_PATH = 'config/config.json'

# 色定義
COLOR_BG = (135, 206, 235)
COLOR_GROUND = (100, 200, 100)
COLOR_PLATFORM = (150, 75, 0)
COLOR_ENEMY = (255, 80, 80)
COLOR_GOAL = (255, 215, 0)
COLOR_SELECTED = (255, 255, 0)
COLOR_TEXT = (0, 0, 0)

# 定数
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
GRID_SIZE = 20

class LevelEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Vibe Code Game - Level Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)

        self.load_config()
        
        self.camera_x = 0
        self.scroll_speed = 10
        
        self.mode = "select" # select, platform, enemy, ground, goal
        self.selected_object = None
        self.drag_start = None
        self.dragging = False
        
        # 地面のY座標（固定）
        self.ground_y = self.config['screen']['height'] - self.config['ground']['y_offset']

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            print(f"Config file not found: {CONFIG_PATH}")
            sys.exit(1)

    def save_config(self):
        # データをソートして保存（見やすさのため）
        self.config['platforms'].sort(key=lambda x: x['world_x'])
        self.config['enemies'].sort(key=lambda x: x['world_x'])
        self.config['ground_segments'].sort(key=lambda x: x['start_x'])
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print("Level saved!")

    def world_to_screen(self, x, y):
        return x - self.camera_x, y

    def screen_to_world(self, x, y):
        return x + self.camera_x, y

    def snap_to_grid(self, val):
        return round(val / GRID_SIZE) * GRID_SIZE

    def run(self):
        running = True
        while running:
            self.handle_input()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # カメラ移動
        if keys[pygame.K_LEFT]:
            self.camera_x = max(0, self.camera_x - self.scroll_speed)
        if keys[pygame.K_RIGHT]:
            self.camera_x += self.scroll_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.save_config()
                elif event.key == pygame.K_1:
                    self.mode = "platform"
                    self.selected_object = None
                elif event.key == pygame.K_2:
                    self.mode = "enemy"
                    self.selected_object = None
                elif event.key == pygame.K_3:
                    self.mode = "ground"
                    self.selected_object = None
                elif event.key == pygame.K_4:
                    self.mode = "goal"
                    self.selected_object = None
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "select"
                    self.selected_object = None
                elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    self.delete_selected()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    self.handle_click(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.handle_release(event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    self.handle_drag(event.pos)

    def get_mouse_world_pos(self):
        mx, my = pygame.mouse.get_pos()
        return self.screen_to_world(mx, my)

    def handle_click(self, pos):
        wx, wy = self.screen_to_world(*pos)
        
        if self.mode == "select":
            self.select_object(wx, wy)
            if self.selected_object:
                self.dragging = True
                self.drag_start = (wx, wy)
                
        elif self.mode == "platform":
            # ドラッグ開始位置を記録
            self.drag_start = (self.snap_to_grid(wx), self.snap_to_grid(wy))
            self.dragging = True
            
        elif self.mode == "enemy":
            # 即座に追加
            new_enemy = {
                "world_x": self.snap_to_grid(wx),
                "move_range": 100,
                "speed": 2,
                "width": 40,
                "height": 40,
                "use_gravity": True
            }
            self.config['enemies'].append(new_enemy)
            self.selected_object = ('enemy', new_enemy)
            self.mode = "select" # 追加後は選択モードへ
            
        elif self.mode == "ground":
            self.drag_start = (self.snap_to_grid(wx), self.ground_y)
            self.dragging = True

        elif self.mode == "goal":
            # ゴール位置を更新
            self.config['goal']['world_x'] = self.snap_to_grid(wx)
            self.config['goal']['world_y'] = self.snap_to_grid(wy) - self.ground_y # 相対座標
            self.mode = "select"

    def handle_drag(self, pos):
        wx, wy = self.screen_to_world(*pos)
        
        if self.mode == "select" and self.selected_object:
            obj_type, obj = self.selected_object
            dx = wx - self.drag_start[0]
            dy = wy - self.drag_start[1]
            
            if obj_type == 'platform':
                obj['world_x'] += dx
                obj['y_offset'] -= dy # y_offsetは地面からの高さなので逆
            elif obj_type == 'enemy':
                obj['world_x'] += dx
                # enemyにはyがない（地面固定）が、空中の敵もいるかも？
                # 現状のconfig構造だとyがない場合もあるが、main.pyではGROUND_Y固定か？
                # config.jsonを見るとyはない。main.pyでGROUND_Yに配置している。
                # しかし、空中敵も作りたいかもしれない。
                # いったんxのみ移動
                pass
            elif obj_type == 'ground':
                obj['start_x'] += dx
                obj['end_x'] += dx
            elif obj_type == 'goal':
                self.config['goal']['world_x'] += dx
                self.config['goal']['world_y'] -= dy
            
            self.drag_start = (wx, wy)

    def handle_release(self, pos):
        wx, wy = self.screen_to_world(*pos)
        
        if self.mode == "platform" and self.dragging:
            start_x, start_y = self.drag_start
            end_x, end_y = self.snap_to_grid(wx), self.snap_to_grid(wy)
            
            # 矩形を正規化
            x = min(start_x, end_x)
            y = min(start_y, end_y)
            w = abs(end_x - start_x)
            h = abs(end_y - start_y)
            
            if w > 0: # 幅が必要
                # y_offsetに変換 (ground_y - y)
                # ただし、platformのyは上面。
                # configのy_offsetは ground_y - platform_top
                y_offset = self.ground_y - y
                
                new_plat = {
                    "world_x": x,
                    "y_offset": y_offset,
                    "width": w
                }
                self.config['platforms'].append(new_plat)
                self.selected_object = ('platform', new_plat)
                self.mode = "select"
                
        elif self.mode == "ground" and self.dragging:
            start_x, _ = self.drag_start
            end_x = self.snap_to_grid(wx)
            
            x1 = min(start_x, end_x)
            x2 = max(start_x, end_x)
            
            if x2 - x1 > 0:
                new_ground = {
                    "start_x": x1,
                    "end_x": x2
                }
                self.config['ground_segments'].append(new_ground)
                self.selected_object = ('ground', new_ground)
                self.mode = "select"
        
        self.dragging = False
        self.drag_start = None

    def select_object(self, wx, wy):
        # 当たり判定の優先順位: Enemy > Platform > Goal > Ground
        
        # Enemy
        for e in self.config['enemies']:
            # 簡易判定
            ex = e['world_x']
            ey = self.ground_y - e['height'] # 地面にいると仮定
            if ex - e['width']//2 <= wx <= ex + e['width']//2 and \
               ey <= wy <= ey + e['height']:
                self.selected_object = ('enemy', e)
                return

        # Platform
        for p in self.config['platforms']:
            px = p['world_x']
            py = self.ground_y - p['y_offset']
            pw = p['width']
            ph = 20 # 固定高さ
            if px <= wx <= px + pw and py <= wy <= py + ph:
                self.selected_object = ('platform', p)
                return

        # Goal
        g = self.config['goal']
        gx = g['world_x']
        gy = self.ground_y + g.get('world_y', 0)
        gw = g['width']
        gh = g['height']
        if gx <= wx <= gx + gw and gy - gh <= wy <= gy:
            self.selected_object = ('goal', g)
            return

        # Ground
        for gr in self.config['ground_segments']:
            if gr['start_x'] <= wx <= gr['end_x'] and \
               self.ground_y <= wy <= self.ground_y + 50: # 地面の下50pxまで判定
                self.selected_object = ('ground', gr)
                return
        
        self.selected_object = None

    def delete_selected(self):
        if not self.selected_object:
            return
            
        obj_type, obj = self.selected_object
        
        if obj_type == 'platform':
            self.config['platforms'].remove(obj)
        elif obj_type == 'enemy':
            self.config['enemies'].remove(obj)
        elif obj_type == 'ground':
            self.config['ground_segments'].remove(obj)
        
        self.selected_object = None

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        # グリッド
        start_col = int(self.camera_x // GRID_SIZE)
        end_col = int((self.camera_x + SCREEN_WIDTH) // GRID_SIZE) + 1
        for i in range(start_col, end_col):
            x = i * GRID_SIZE - self.camera_x
            pygame.draw.line(self.screen, (200, 200, 200), (x, 0), (x, SCREEN_HEIGHT))
        
        # 地面基準線
        gy_screen = self.ground_y
        pygame.draw.line(self.screen, (100, 100, 100), (0, gy_screen), (SCREEN_WIDTH, gy_screen))

        # Ground Segments
        for gr in self.config['ground_segments']:
            sx = gr['start_x'] - self.camera_x
            ex = gr['end_x'] - self.camera_x
            w = ex - sx
            if w > 0:
                rect = pygame.Rect(sx, gy_screen, w, SCREEN_HEIGHT - gy_screen)
                color = COLOR_SELECTED if self.selected_object and self.selected_object[1] == gr else COLOR_GROUND
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (0,0,0), rect, 2)

        # Platforms
        for p in self.config['platforms']:
            px = p['world_x'] - self.camera_x
            py = gy_screen - p['y_offset']
            pw = p['width']
            ph = 20
            rect = pygame.Rect(px, py, pw, ph)
            color = COLOR_SELECTED if self.selected_object and self.selected_object[1] == p else COLOR_PLATFORM
            pygame.draw.rect(self.screen, color, rect)

        # Enemies
        for e in self.config['enemies']:
            ex = e['world_x'] - self.camera_x
            ew = e['width']
            eh = e['height']
            ey = gy_screen - eh # 地面に配置
            rect = pygame.Rect(ex - ew//2, ey, ew, eh)
            color = COLOR_SELECTED if self.selected_object and self.selected_object[1] == e else COLOR_ENEMY
            pygame.draw.rect(self.screen, color, rect)

        # Goal
        g = self.config['goal']
        gx = g['world_x'] - self.camera_x
        gw = g['width']
        gh = g['height']
        gy = gy_screen + g.get('world_y', 0)
        rect = pygame.Rect(gx, gy - gh, gw, gh)
        color = COLOR_SELECTED if self.selected_object and self.selected_object[1] == g else COLOR_GOAL
        pygame.draw.rect(self.screen, color, rect)

        # ドラッグ中のプレビュー
        if self.dragging and self.drag_start:
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.screen_to_world(mx, my)
            sx, sy = self.drag_start
            
            if self.mode == "platform":
                x = min(sx, wx) - self.camera_x
                y = min(sy, wy)
                w = abs(wx - sx)
                h = abs(wy - sy)
                pygame.draw.rect(self.screen, (200, 200, 200), (x, y, w, h), 2)
                
            elif self.mode == "ground":
                x = min(sx, wx) - self.camera_x
                w = abs(wx - sx)
                pygame.draw.rect(self.screen, (100, 255, 100), (x, gy_screen, w, 50), 2)

        # UI
        self.draw_ui()

    def draw_ui(self):
        mode_text = f"Mode: {self.mode.upper()} (1:Plat, 2:Enemy, 3:Ground, 4:Goal, ESC:Select, DEL:Delete, Ctrl+S:Save)"
        surf = self.font.render(mode_text, True, COLOR_TEXT)
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 0, SCREEN_WIDTH, 30))
        self.screen.blit(surf, (10, 5))
        
        cam_text = f"Camera: {int(self.camera_x)}"
        surf2 = self.font.render(cam_text, True, COLOR_TEXT)
        self.screen.blit(surf2, (SCREEN_WIDTH - 150, 5))

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()
