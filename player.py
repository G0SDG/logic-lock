import pygame
from .sprite import Sprite
from .input import is_key_pressed
from .camera import camera

class Player(Sprite):
    """Player sprite with keyboard movement using delta-time and optional map collision.

    Usage:
      player = Player(image, x, y, speed=150)  # speed in pixels / second
      player.update(game_map, dt)  # pass dt (seconds) from the game loop
    """
    def __init__(self, image, x, y, speed=150):
        super().__init__(image, x, y)
        self.speed = float(speed)

    def update(self, game_map=None, dt=0.0):
        # Read input and build a direction vector
        dx = dy = 0.0
        if is_key_pressed(pygame.K_w) or is_key_pressed(pygame.K_UP):
            dy -= 1.0
        if is_key_pressed(pygame.K_s) or is_key_pressed(pygame.K_DOWN):
            dy += 1.0
        if is_key_pressed(pygame.K_a) or is_key_pressed(pygame.K_LEFT):
            dx -= 1.0
        if is_key_pressed(pygame.K_d) or is_key_pressed(pygame.K_RIGHT):
            dx += 1.0

        # Normalize direction
        mag = (dx*dx + dy*dy) ** 0.5
        if mag > 0:
            dx /= mag
            dy /= mag

        # Movement amount this frame (pixels)
        move = self.speed * float(dt)
        move_x = dx * move
        move_y = dy * move

        new_x = self.x + move_x
        new_y = self.y + move_y

        # debug logging removed

        if game_map is None:
            # Free move
            self.x = new_x
            self.y = new_y
        else:
            # Axis-separated movement for simpler collision response
            if self._can_move_to(new_x, self.y, game_map):
                self.x = new_x
            if self._can_move_to(self.x, new_y, game_map):
                self.y = new_y

        # Center the camera on the player (use float positions internally and optionally smooth)
        player_center_x = self.x + self.image.get_width() / 2
        player_center_y = self.y + self.image.get_height() / 2
        target_x = player_center_x - camera.width / 2
        target_y = player_center_y - camera.height / 2
        smooth = getattr(camera, 'smooth', 0.0)
        if smooth and 0.0 < smooth < 1.0:
            # lerp toward target to reduce jitter
            camera._x += (target_x - camera._x) * float(smooth)
            camera._y += (target_y - camera._y) * float(smooth)
        else:
            # immediate snap to target position
            camera._x = target_x
            camera._y = target_y

        # debug logging removed

    def _can_move_to(self, new_x, new_y, game_map):
        """Return True if the player's rectangle at (new_x,new_y) does not overlap any solid tiles."""
        left = new_x
        top = new_y
        right = new_x + self.image.get_width()
        bottom = new_y + self.image.get_height()
        ts = game_map.tile_size

        start_x = int(left // ts)
        end_x = int((right - 1) // ts)
        start_y = int(top // ts)
        end_y = int((bottom - 1) // ts)

        # Create a mask for the player image once for per-pixel checks
        try:
            player_mask = pygame.mask.from_surface(self.image)
        except Exception:
            player_mask = None

        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                # Out-of-bounds tiles are treated as non-solid here (change if necessary)
                if ty < 0 or tx < 0 or ty >= len(game_map.tiles) or tx >= len(game_map.tiles[0]):
                    continue
                tile_index = game_map.tiles[ty][tx]
                tk = game_map.tile_kinds[tile_index]
                if not tk.is_solid:
                    continue

                # If a mask exists for this tile image, perform per-pixel overlap test
                tile_mask = getattr(tk, 'mask', None)
                if tile_mask is not None and player_mask is not None:
                    image = tk.image
                    ts = game_map.tile_size
                    x_offset = (image.get_width() - ts) // 2
                    y_offset = max(0, image.get_height() - ts)
                    tile_x = int(tx * ts - x_offset)
                    tile_y = int(ty * ts - y_offset)
                    # compute offset of tile mask relative to player mask coordinate space
                    offset = (int(tile_x - left), int(tile_y - top))
                    if player_mask.overlap(tile_mask, offset) is not None:
                        return False
                else:
                    # fallback: entire tile square is solid
                    return False
        return True
