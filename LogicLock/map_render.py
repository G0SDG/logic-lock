import pygame
from .camera import camera
import time
import hashlib

# Set to False to disable expensive diagnostics
DEBUG = False

# Last draw stats (set each frame by draw_map)
last_draw_stats = {}

# Maximum allowed padding multiplier (in tile units) to prevent runaway huge surfaces
MAX_PADDING_MULTIPLIER = 4


def convert_tile_images(tile_kinds):
    for tk in tile_kinds:
        tk.convert_for_display()


def compute_extra_pixels(tile_kinds, tile_size):
    max_w = max((tk.image.get_width() for tk in tile_kinds))
    max_h = max((tk.image.get_height() for tk in tile_kinds))
    return max(0, max_w - tile_size), max(0, max_h - tile_size)


def create_chunks(tiles, tile_kinds, tile_size, chunk_size, extra_x, extra_y):
    if not tiles:
        return {}
    map_h = len(tiles)
    map_w = len(tiles[0]) if map_h else 0
    cs = chunk_size

    cols = (map_w + cs - 1) // cs
    rows = (map_h + cs - 1) // cs

    tree_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'tree'), None)
    ground_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'grass'), None)
    if ground_idx is None:
        ground_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'dirt'), None)

    tile = tile_size

    # Attempt to ensure the provided extra_x/extra_y are sufficient to contain all tile images inside a chunk.
    # If any image would be partially out-of-bounds, increase padding and retry (bounded iterations).
    extra_x_cur = int(extra_x)
    extra_y_cur = int(extra_y)
    max_iters = 4
    needed_extra_x = 0
    needed_extra_y = 0



    for it in range(max_iters):
        needed_extra_x = 0
        needed_extra_y = 0
        chunk_pixel_w = cs * tile + 2 * extra_x_cur
        chunk_pixel_h = cs * tile + 2 * extra_y_cur

        for cy in range(rows):
            for cx in range(cols):
                tx0 = cx * cs
                ty0 = cy * cs
                tx1 = min(map_w, (cx + 1) * cs)
                ty1 = min(map_h, (cy + 1) * cs)

                for ty in range(ty0, ty1):
                    row = tiles[ty]
                    for tx in range(tx0, tx1):
                        t = row[tx]
                        img = tile_kinds[t].image
                        x_offset = (img.get_width() - tile) // 2
                        y_offset = max(0, img.get_height() - tile)
                        local_x = extra_x_cur + (tx - tx0) * tile - x_offset
                        local_y = extra_y_cur + (ty - ty0) * tile - y_offset

                        if local_x < 0:
                            needed_extra_x = max(needed_extra_x, -local_x)
                        if local_y < 0:
                            needed_extra_y = max(needed_extra_y, -local_y)
                        if local_x + img.get_width() > chunk_pixel_w:
                            needed_extra_x = max(needed_extra_x, local_x + img.get_width() - chunk_pixel_w)
                        if local_y + img.get_height() > chunk_pixel_h:
                            needed_extra_y = max(needed_extra_y, local_y + img.get_height() - chunk_pixel_h)

        if needed_extra_x == 0 and needed_extra_y == 0:
            # current padding is sufficient
            break

        # Apply an upper bound to prevent runaway padding (prevents huge surfaces)
        max_pad = tile * MAX_PADDING_MULTIPLIER
        if extra_x_cur + needed_extra_x > max_pad:
            needed_extra_x = max(0, max_pad - extra_x_cur)
            print(f"Clamped extra_x to max allowed padding {max_pad}")
        if extra_y_cur + needed_extra_y > max_pad:
            needed_extra_y = max(0, max_pad - extra_y_cur)
            print(f"Clamped extra_y to max allowed padding {max_pad}")

        # Expand padding and retry
        extra_x_cur += int(needed_extra_x)
        extra_y_cur += int(needed_extra_y)
        print(f"Adjusted chunk padding, extra_x -> {extra_x_cur}, extra_y -> {extra_y_cur} (iteration {it+1})")

    if (needed_extra_x or needed_extra_y) and (it == max_iters - 1):
        print(f"Warning: chunk padding still insufficient after {max_iters} attempts (extra_x={extra_x_cur}, extra_y={extra_y_cur}).")

    # Now build the actual chunk surfaces using the (possibly adjusted) padding
    chunks = {}
    clipped = []
    for cy in range(rows):
        for cx in range(cols):
            chunk_pixel_w = cs * tile + 2 * extra_x_cur
            chunk_pixel_h = cs * tile + 2 * extra_y_cur
            surf = pygame.Surface((chunk_pixel_w, chunk_pixel_h), pygame.SRCALPHA)
            tx0 = cx * cs
            ty0 = cy * cs
            tx1 = min(map_w, (cx + 1) * cs)
            ty1 = min(map_h, (cy + 1) * cs)

            # Precomposite tree+ground surfaces
            composite_cache = {}
            for ty in range(ty0, ty1):
                row = tiles[ty]
                for tx in range(tx0, tx1):
                    t = row[tx]
                    img_key = t
                    if t == tree_idx and ground_idx is not None:
                        # Create composite image if not cached
                        img_key = (t, ground_idx)
                        if img_key not in composite_cache:
                            ground_img = tile_kinds[ground_idx].image
                            # Create surface tall enough for both ground and tree
                            ground_w, ground_h = ground_img.get_size()
                            tree_w, tree_h = tile_kinds[t].image.get_size()
                            comp_h = max(ground_h, tree_h)
                            composite = pygame.Surface((ground_w, comp_h), pygame.SRCALPHA)
                            composite.blit(ground_img, (0, comp_h - ground_h))  # Align ground to bottom
                            # Center tree horizontally, align to bottom
                            composite.blit(tile_kinds[t].image, 
                                         ((ground_w - tree_w) // 2, 
                                          comp_h - tree_h))
                            composite_cache[img_key] = composite
                        img = composite_cache[img_key]
                    else:
                        img = tile_kinds[t].image
                        if t not in composite_cache:
                            composite_cache[t] = img
                        img = composite_cache[t]
                    x_offset = (img.get_width() - tile) // 2
                    y_offset = max(0, img.get_height() - tile)
                    local_x = extra_x_cur + (tx - tx0) * tile - x_offset
                    local_y = extra_y_cur + (ty - ty0) * tile - y_offset

                    # Detect if this blit would be partially outside the chunk surface
                    iw, ih = img.get_width(), img.get_height()
                    out_left = local_x < 0
                    out_top = local_y < 0
                    out_right = (local_x + iw) > chunk_pixel_w
                    out_bottom = (local_y + ih) > chunk_pixel_h
                    if out_left or out_top or out_right or out_bottom:
                        clipped.append((cx, cy, tx, ty, iw, ih, int(local_x), int(local_y), chunk_pixel_w, chunk_pixel_h))

                    surf.blit(img, (int(local_x), int(local_y)))

            chunks[(cx, cy)] = surf

    if clipped:
        print(f"Warning: detected {len(clipped)} clipped tile(s) while building chunks")
        for ex in clipped[:6]:
            cx, cy, tx, ty, iw, ih, lx, ly, cw, ch = ex
            print(f"  chunk=({cx},{cy}) tile=({tx},{ty}) img={iw}x{ih} local=({lx},{ly}) chunk={cw}x{ch}")

    return chunks


def draw_map(screen, tiles, tile_kinds, tile_size, chunks, extra_px_x, extra_px_y, debug=False):
    if not tiles:
        return
    map_h = len(tiles)
    map_w = len(tiles[0]) if map_h else 0
    if map_w == 0 or map_h == 0:
        return

    left = int(camera.x)
    top = int(camera.y)
    right = int(camera.x + camera.width)
    bottom = int(camera.y + camera.height)

    extra_tiles_x = (extra_px_x + tile_size - 1) // tile_size
    extra_tiles_y = (extra_px_y + tile_size - 1) // tile_size

    start_x = max(0, left // tile_size - extra_tiles_x)
    end_x = min(map_w - 1, right // tile_size + extra_tiles_x)
    start_y = max(0, top // tile_size - extra_tiles_y)
    end_y = min(map_h - 1, bottom // tile_size + extra_tiles_y)

    #if chunks is None:
        # fallback (rare) to per-tile drawing
    #    for y in range(start_y, end_y + 1):
    #        row = tiles[y]
     #       for x in range(start_x, end_x + 1):
      #          t = row[x]
       #         img = tile_kinds[t].image
        #        x_offset = (img.get_width() - tile_size) // 2
         #       y_offset = max(0, img.get_height() - tile_size)
          #      x_loc = int(x * tile_size - camera.x - x_offset)
           #     y_loc = int(y * tile_size - camera.y - y_offset)
            #    screen.blit(img, (x_loc, y_loc))
      #  return

    cs = chunk_size = None
    # infer chunk size from chunk surface dimensions
    if chunks:
        first = next(iter(chunks.values()))
        chunk_pixel_w, chunk_pixel_h = first.get_size()
        cs = (chunk_pixel_w - 2 * extra_px_x) // tile_size if tile_size else 8
    else:
        cs = 8

    start_cx = start_x // cs
    end_cx = end_x // cs
    start_cy = start_y // cs
    end_cy = end_y // cs

    # Blit visible chunk surfaces and count how many we drew (for performance diagnostics)
    blit_count = 0
    start_ts = time.perf_counter()
    for cy in range(start_cy, end_cy + 1):
        for cx in range(start_cx, end_cx + 1):
            surf = chunks.get((cx, cy))
            if surf is None:
                continue
            blit_x = cx * cs * tile_size - extra_px_x - camera.x
            blit_y = cy * cs * tile_size - extra_px_y - camera.y
            screen.blit(surf, (int(blit_x), int(blit_y)))
            blit_count += 1
    end_ts = time.perf_counter()

    # Record draw stats
    global last_draw_stats
    last_draw_stats = {'draw_ms': (end_ts - start_ts) * 1000.0, 'chunk_blits': blit_count, 'visible_cx_range': (start_cx, end_cx), 'visible_cy_range': (start_cy, end_cy)}

    # Debug overlay: chunk borders and tile bounding boxes
    if debug:
        # draw chunk borders
        for (cx, cy), surf in chunks.items():
            cw, ch = surf.get_size()
            blit_x = cx * cs * tile_size - extra_px_x - camera.x
            blit_y = cy * cs * tile_size - extra_px_y - camera.y
            pygame.draw.rect(screen, (0, 0, 255), (int(blit_x), int(blit_y), int(cw), int(ch)), 1)

        # draw tile bounding boxes (red) for visible tiles
        tree_idx = next((i for i, tk in enumerate(tile_kinds) if tk.name == 'tree'), None)
        for y in range(start_y, end_y + 1):
            for x in range(start_x, end_x + 1):
                t = tiles[y][x]
                img = tile_kinds[t].image
                x_offset = (img.get_width() - tile_size) // 2
                y_offset = max(0, img.get_height() - tile_size)
                x_loc = int(x * tile_size - camera.x - x_offset)
                y_loc = int(y * tile_size - camera.y - y_offset)
                pygame.draw.rect(screen, (255, 0, 0), (x_loc, y_loc, img.get_width(), img.get_height()), 1)

