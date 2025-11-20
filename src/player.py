import pygame


class Player:
    def __init__(self, x_screen, ground_y, config):
        # Basic settings
        self.x_screen = x_screen  # Fixed x position on the screen (world coordinate is camera_x + x_screen)
        self.width = config['player']['width']
        self.height = config['player']['height']
        self.color = tuple(config['player']['color'])

        # Shoes
        shoe_conf = config['player']['shoe']
        self.shoe_width = shoe_conf['width']
        self.shoe_height = shoe_conf['height']
        self.shoe_color = tuple(shoe_conf['color'])

        # Load images
        self.images = []
        self.jump_image = None
        try:
            # Load walking animation (1.png to 8.png)
            for i in range(1, 9):
                img = pygame.image.load(f'assets/player/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(self.width * 1.2), int(self.height * 1.2)))
                self.images.append(img)
            
            # Load jump image
            self.jump_image = pygame.image.load('assets/player/jump.png').convert_alpha()
            self.jump_image = pygame.transform.scale(self.jump_image, (int(self.width * 1.2), int(self.height * 1.2)))
            
            self.use_image = True
        except Exception as e:
            print(f"Failed to load player images: {e}")
            self.use_image = False

        # Animation state
        self.animation_timer = 0
        self.current_frame_index = 0
        # Set animation so one loop = 40 frames -> 8 images => 5 frames per image
        self.ANIMATION_SPEED = 4

        # Physics parameters
        self.ground_y = ground_y
        self.config = config
        # Removed self.gravity to reference config['physics']['gravity'] directly
        self.jump_strength = -10      # 元の JUMP_STRENGTH と同じ
        self.max_jump_time = 15       # MAX_JUMP_TIME と同じ

        # State
        self.y = self.ground_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0
        self.facing_right = False  # Default facing left
        
        # Multiple jumps
        self.max_jumps = 1  # Default is 1 (single jump)
        self.jump_count = 0  # Current jump count

    # Input-related ---------------------------------
    def start_jump(self):
        if self.jump_count < self.max_jumps:
            self.vy = self.jump_strength
            self.is_jumping = True
            self.jump_held = True
            self.jump_time = 0
            self.jump_count += 1

    def release_jump(self):
        self.jump_held = False

    def reset(self):
        """Reset player state to initial values"""
        self.y = self.ground_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0

    # Physics update ---------------------------------
    def update(self):
        """Per-frame physics update.
        Gravity is read directly from `config` so runtime changes take effect.
        """
        gravity = self.config['physics']['gravity']

        # Variable jump (reduce gravity while the jump is held)
        if self.jump_held and self.is_jumping and self.jump_time < self.max_jump_time and self.vy < 0:
            self.vy += gravity * 0.3
            self.jump_time += 1
        else:
            self.vy += gravity

        self.y += self.vy
        
        # Ground collisions are handled in main.py (for ledge detection)

    def land_on(self, surface_y):
        """Call when landing on a platform or the ground"""
        self.y = surface_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0
        self.jump_count = 0  # 着地したらジャンプカウントをリセット

    # Bounce when stomping an enemy ------------------
    def stomp_enemy(self, jump_key_pressed: bool):
        if jump_key_pressed:
            # Jump key pressed -> big bounce
            self.vy = self.jump_strength * 1.3
            self.is_jumping = True
            self.jump_held = True
            self.jump_time = 0
        else:
            # No jump key -> small bounce
            self.vy = self.jump_strength * 0.4
            self.is_jumping = True
            self.jump_held = False
            self.jump_time = 0

    # Drawing & collision --------------------------
    def get_rect(self):
        return pygame.Rect(
            self.x_screen - self.width // 2,
            self.y,
            self.width,
            self.height,
        )

    def get_shoe_rect(self):
        return pygame.Rect(
            self.x_screen - self.shoe_width // 2,
            self.y + self.height - self.shoe_height,
            self.shoe_width,
            self.shoe_height,
        )

    def draw(self, surface, is_moving=False):
        if self.use_image and self.images:
            # Select image
            if self.is_jumping and self.jump_image:
                current_img = self.jump_image
            elif not is_moving:
                # Idle state: use 3.png (index 2)
                current_img = self.images[2]
            else:
                # Update animation only when moving
                self.animation_timer += 1
                if self.animation_timer >= self.ANIMATION_SPEED:
                    self.animation_timer = 0
                    self.current_frame_index = (self.current_frame_index + 1) % len(self.images)
                current_img = self.images[self.current_frame_index]

            # Draw image (centered, account for scaling)
            image_width = current_img.get_width()
            image_height = current_img.get_height()
            image_x = self.x_screen - image_width // 2
            image_y = self.y - (image_height - self.height)  # 足元を基準に
            
            # Flip based on facing direction
            if self.facing_right:
                surface.blit(current_img, (image_x, image_y))
            else:
                flipped_image = pygame.transform.flip(current_img, True, False)
                surface.blit(flipped_image, (image_x, image_y))                
        else:
            # Fallback: draw rectangles
            pygame.draw.rect(surface, self.color, self.get_rect())
            pygame.draw.rect(surface, self.shoe_color, self.get_shoe_rect())

    # リセット -----------------------------------
    def reset(self):
        self.y = self.ground_y - self.height
        self.vy = 0
        self.is_jumping = False
        self.jump_held = False
        self.jump_time = 0
        self.jump_count = 0
