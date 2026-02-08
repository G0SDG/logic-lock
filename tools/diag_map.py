import pygame
from pathlib import Path
p = Path('LogicLock/maps/spam.png')
print('exists', p.exists(), 'path', p)
pygame.init()
img = pygame.image.load(str(p))
print('spam.png pixel size:', img.get_width(), 'x', img.get_height())
# Estimate tile count when tile_size=32
ts = 32
print('tiles (w x h):', img.get_width(), 'x', img.get_height(), 'total tiles:', img.get_width()*img.get_height())
print('estimated map pixel size:', img.get_width()*ts, 'x', img.get_height()*ts)
pygame.quit()
