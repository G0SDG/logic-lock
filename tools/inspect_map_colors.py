"""Inspect an image map and print most common colors and suggest a palette file.

Usage: run from repository root: python tools/inspect_map_colors.py
"""
from collections import Counter
from pathlib import Path
import pygame

pygame.init()
img_path = Path('LogicLock/images/spam.png')
if not img_path.exists():
    print('Image not found:', img_path)
    raise SystemExit(1)

img = pygame.image.load(str(img_path))
px = [img.get_at((x,y))[:3] for y in range(img.get_height()) for x in range(img.get_width())]
cnt = Counter(px)
most = cnt.most_common(32)
print('Image size', img.get_width(), 'x', img.get_height())
print('\nTop colors (RGB) and counts:')
for i,(color,n) in enumerate(most,1):
    print(f"{i:2d}: {color} -> {n}")

# Suggest a palette file mapping the top colors to tile names (best guess)
from LogicLock.map import TileKind
# Load tile kinds to suggest names
kinds = [TileKind('dirt','images/dirt.png',False), TileKind('grass','images/grass.png',False), TileKind('water','images/water.png',False), TileKind('wood','images/wood.png',False)]

def nearest_tile_name(color):
    best = None; bd = None
    for tk in kinds:
        img = tk.image
        w,h = img.get_size()
        px = img.get_at((min(1,w-1), min(1,h-1)))[:3]
        d = (px[0]-color[0])**2 + (px[1]-color[1])**2 + (px[2]-color[2])**2
        if bd is None or d < bd:
            bd = d; best = tk.name
    return best

print('\nSuggested palette lines (R,G,B=tile_name). Save to a .palette file to use exact mapping:')
for color, n in most:
    print(f"{color[0]},{color[1]},{color[2]}={nearest_tile_name(color)}")

pygame.quit()
