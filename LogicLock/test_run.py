import pygame
from .camera import create_screen
from .map import Map, TileKind
from .player import Player
from .sprite import sprites, Sprite

pygame.init()
screen = create_screen(800, 600, "Test")

tile_kinds = [
    TileKind("dirt", "images/dirt.png", False),
    TileKind("grass", "images/grass.png", False),
    TileKind("water", "images/water.png", False),
    TileKind("wood", "images/wood.png", False),
]

try:
    game_map = Map("maps/start.map", tile_kinds, 32)
except Exception as e:
    print("Map load failed:", e)
    pygame.quit()
    raise

player = Player("images/player.jpg", 32 * 11, 32 * 7)
Sprite("images/box.png", 0 * 32, 0 * 32)

# Run a few update/draw cycles then exit
for i in range(3):
    player.update(game_map)
    screen.fill((30, 150, 50))
    game_map.draw(screen)
    for s in sprites:
        s.draw(screen)
    pygame.display.flip()

pygame.quit()
print('SMOKE TEST OK')
