import os
import pygame


def load_palette_from_file(palette_path, tile_kinds):
    """Load a palette file mapping 'R,G,B=name_or_index' to tile indices.

    Returns a dict mapping (r,g,b) -> tile_index
    """
    palette = {}
    with open(palette_path, 'r') as pf:
        for line in pf:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            left, right = line.split('=', 1)
            parts = [int(x) for x in left.split(',')]
            color = (parts[0], parts[1], parts[2])
            try:
                idx = int(right)
            except ValueError:
                idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == right), None)
                if idx is None:
                    raise ValueError(f"Unknown tile name in palette: {right}")
            palette[color] = idx
    return palette


def find_palette_file_for_image(map_file):
    base = os.path.splitext(map_file)[0]
    candidates = [base + '.palette', os.path.join(os.path.dirname(__file__), 'maps', os.path.basename(base) + '.palette')]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def build_rep_palette(tile_kinds):
    """Sample a representative color from each TileKind image (top-left-ish pixel)."""
    colors = []
    for tk in tile_kinds:
        img = tk.image
        w, h = img.get_size()
        px = img.get_at((min(1, w - 1), min(1, h - 1)))
        colors.append((px[0], px[1], px[2]))
    return colors


def nearest_color_index(color, palette_colors):
    best = 0
    best_dist = None
    for i, c in enumerate(palette_colors):
        d = (c[0] - color[0]) ** 2 + (c[1] - color[1]) ** 2 + (c[2] - color[2]) ** 2
        if best_dist is None or d < best_dist:
            best_dist = d
            best = i
    return best


def image_to_tiles(map_file, tile_kinds, max_tiles=None, color_map=None):
    """Load an image file and convert each pixel to a tile index list-of-lists.

    Returns (tiles, (mw,mh)) where tiles is a 2D list.
    """
    surf = pygame.image.load(map_file)
    mw, mh = surf.get_size()

    if max_tiles is not None and (mw > max_tiles or mh > max_tiles):
        scale = min(max_tiles / mw, max_tiles / mh)
        new_w = max(1, int(mw * scale))
        new_h = max(1, int(mh * scale))
        try:
            surf = pygame.transform.smoothscale(surf, (new_w, new_h))
            print(f"Downscaled map image from {mw}x{mh} to {new_w}x{new_h} to limit tiles <= {max_tiles}")
        except Exception:
            surf = pygame.transform.scale(surf, (new_w, new_h))
        mw, mh = surf.get_size()

    # build color_map if provided as path
    palette = None
    if isinstance(color_map, str):
        palette = load_palette_from_file(color_map, tile_kinds)
    elif isinstance(color_map, dict):
        palette = {tuple(k): v for k, v in color_map.items()}

    rep_palette = None
    if palette is None:
        rep_palette = build_rep_palette(tile_kinds)

    tiles = []
    for y in range(mh):
        row = []
        for x in range(mw):
            c = surf.get_at((x, y))
            color = (c[0], c[1], c[2])
            if palette and color in palette:
                row.append(palette[color])
            else:
                if rep_palette is None:
                    rep_palette = build_rep_palette(tile_kinds)
                row.append(nearest_color_index(color, rep_palette))
        tiles.append(row)
    return tiles, (mw, mh)


def text_to_tiles(map_file):
    with open(map_file, 'r') as f:
        data = f.read()
    tiles = []
    for line in data.split('\n'):
        if not line:
            continue
        row = [int(ch) for ch in line]
        tiles.append(row)
    return tiles


def sparsify_trees(tiles, tile_kinds, tree_density, clustered=False):
    if tree_density is None or not (0.0 <= tree_density <= 1.0):
        return tiles
    import random

    tree_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'tree'), None)
    if tree_idx is None:
        return tiles

    grass_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'grass'), None)
    dirt_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'dirt'), None)
    replace_idx = grass_idx if grass_idx is not None else (dirt_idx if dirt_idx is not None else 0)

    h = len(tiles)
    w = len(tiles[0]) if h else 0
    for y in range(h):
        for x in range(w):
            if tiles[y][x] == tree_idx:
                if random.random() > tree_density:
                    tiles[y][x] = replace_idx

    if clustered:
        for y in range(h):
            for x in range(w):
                if tiles[y][x] != tree_idx:
                    neighbors = 0
                    for ny in range(max(0, y - 1), min(h, y + 2)):
                        for nx in range(max(0, x - 1), min(w, x + 2)):
                            if tiles[ny][nx] == tree_idx:
                                neighbors += 1
                    if neighbors > 0 and random.random() < 0.02:
                        tiles[y][x] = tree_idx
    return tiles


def scale_tree_images(tile_kinds, tile_size, tree_scale):
    if tree_scale is None:
        return
    for tk in tile_kinds:
        if tk.name == 'tree':
            img = tk.image
            w, h = img.get_size()
            desired_h = max(1, int(tile_size * tree_scale))
            if h != desired_h and h != 0:
                new_w = max(1, int(w * (desired_h / h)))
                try:
                    tk.image = pygame.transform.smoothscale(img, (new_w, desired_h))
                except Exception:
                    tk.image = pygame.transform.scale(img, (new_w, desired_h))
