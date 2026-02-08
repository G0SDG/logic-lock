import pygame
import sys
import os
import json
import menu  # Import the main menu module


def asset_path(rel_path):
    """Convert relative paths to absolute paths based on script location"""
    return os.path.join(os.path.dirname(__file__), rel_path)

# Prefer package-relative imports, but fall back to absolute imports when the module is run as a script
try:
    from .sprite import sprites, Sprite
    
    class StaticSprites:
        """Batched rendering for static sprites using single surface"""
        
        def __init__(self, image_path, positions, tile_size):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (tile_size, tile_size))
            
            min_x = min(x for x, y in positions)
            max_x = max(x for x, y in positions)
            min_y = min(y for x, y in positions)
            max_y = max(y for x, y in positions)
            width = (max_x - min_x + 1) * tile_size
            height = (max_y - min_y + 1) * tile_size
            
            self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect = pygame.Rect(min_x, min_y, width, height)
            
            for x, y in positions:
                x_offset = (x - min_x) * tile_size
                y_offset = (y - min_y) * tile_size
                self.surface.blit(self.image, (x_offset, y_offset))
                
        def draw(self, screen):
            # Get current viewport rect
            viewport = pygame.Rect(camera.x, camera.y, screen.get_width(), screen.get_height())
            if viewport.colliderect(self.rect):
                # Manual camera offset calculation
                screen.blit(self.surface, 
                           (self.rect.x - camera.x, self.rect.y - camera.y))

    from .player import Player
    from .input import keys_down
    from .map import Map, TileKind
    from .map_io import scale_tree_images, sparsify_trees
    from . import map_render
    from .camera import create_screen, camera
except Exception:
    import sys
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from LogicLock.sprite import sprites, Sprite
    
    class StaticSprites:
        """Batched rendering for static sprites using single surface"""
        
        def __init__(self, image_path, positions, tile_size):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (tile_size, tile_size))
            
            min_x = min(x for x, y in positions)
            max_x = max(x for x, y in positions)
            min_y = min(y for x, y in positions)
            max_y = max(y for x, y in positions)
            width = (max_x - min_x + 1) * tile_size
            height = (max_y - min_y + 1) * tile_size
            
            self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect = pygame.Rect(min_x, min_y, width, height)
            
            for x, y in positions:
                x_offset = (x - min_x) * tile_size
                y_offset = (y - min_y) * tile_size
                self.surface.blit(self.image, (x_offset, y_offset))
                
        def draw(self, screen):
            # Get current viewport rect
            viewport = pygame.Rect(camera.x, camera.y, screen.get_width(), screen.get_height())
            if viewport.colliderect(self.rect):
                # Manual camera offset calculation
                screen.blit(self.surface, 
                           (self.rect.x - camera.x, self.rect.y - camera.y))

    from LogicLock.player import Player
    from LogicLock.input import keys_down
    from LogicLock.map import Map, TileKind
    from LogicLock.map_io import scale_tree_images, sparsify_trees
    import LogicLock.map_render as map_render
    from LogicLock.camera import create_screen, camera
    # Hot-reloadable modules (remote server removed)
    import importlib, threading, time as _time, os as _os
    try:
        import menu as _menu_mod
    except Exception:
        import LogicLock.menu as _menu_mod

    HOT_MODULES = {'menu': _menu_mod}

    def start_hot_reload_watcher(modules, interval=1.0):
        mtimes = {}
        for name, mod in modules.items():
            try:
                mtimes[name] = _os.path.getmtime(mod.__file__)
            except Exception:
                mtimes[name] = None

        def _watch():
            while True:
                for name, mod in list(modules.items()):
                    try:
                        path = getattr(mod, '__file__', None)
                        if not path:
                            continue
                        mtime = _os.path.getmtime(path)
                        if mtimes.get(name) is None:
                            mtimes[name] = mtime
                        elif mtime != mtimes[name]:
                            print(f"[hotreload] detected change in {path}, reloading {name}")
                            try:
                                new_mod = importlib.reload(mod)
                                modules[name] = new_mod
                            except Exception as e:
                                print(f"[hotreload] reload failed for {name}: {e}")
                            mtimes[name] = mtime
                    except Exception as e:
                        print(f"[hotreload] watch error for {name}: {e}")
                _time.sleep(interval)

        t = threading.Thread(target=_watch, daemon=True)
        t.start()
        print(f"[hotreload] watcher started for: {', '.join(modules.keys())}")
        return t
    # start watcher automatically
    try:
        start_hot_reload_watcher(HOT_MODULES)
    except Exception:
        pass

    def reload_hot_modules():
        import importlib as _importlib
        for name, mod in list(HOT_MODULES.items()):
            try:
                new_mod = _importlib.reload(mod)
                HOT_MODULES[name] = new_mod
                print(f"[hotreload] manual reload: {name}")
            except Exception as e:
                print(f"[hotreload] manual reload failed for {name}: {e}")
    import pygame as _pygame_remote  # ensure pygame available for key mapping

_default_config = {
    'tile_size': 32,
    'player_speed': 150.0,
    'tree_scale': 4.0,
    'tree_density': 0.04,
    'clustered_trees': True,
    'chunk_size': 8,
    'max_tiles': 120,
    'clear_color': [30, 150, 50]
}

def load_config():
    pkg_dir = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(pkg_dir, '..'))
    cfg_path = os.path.join(repo_root, 'config.json')
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as fh:
                cfg = json.load(fh)
                merged = dict(_default_config)
                merged.update(cfg)
                print(f"Loaded configuration from {cfg_path}")
                return merged
        except Exception as e:
            print(f"Failed to load config {cfg_path}: {e}; using defaults")
    else:
        print(f"Config not found at {cfg_path}; using defaults")
    return dict(_default_config)

CONFIG = load_config()

def main():
    # Display the main menu (use hot-reloadable module)
    menu_action = HOT_MODULES['menu'].main_menu()

    # Support starting normally or via main-menu Load Game option
    if menu_action in ("start_game", "load_game"):
        do_load = (menu_action == "load_game")
        # Proceed to the game loop
        pygame.init()
        # create the screen via create_screen so camera.width/height are set
        screen = create_screen(800, 600, "Game")

        clock = pygame.time.Clock()

        camera.x = 0
        camera.y = 0
        camera.smooth = float(CONFIG.get('camera_smooth', 0.0))

        # Remote server removed — no streaming or remote key injection

        clear_color = tuple(CONFIG.get('clear_color', _default_config['clear_color']))
        running = True

        TILE_SIZE = int(CONFIG.get('tile_size', _default_config['tile_size']))
        tile_kinds = [
            TileKind("dirt", asset_path("images/dirt.png"), False),
            TileKind("grass", asset_path("images/grass.png"), False),
            TileKind("water", asset_path("images/water.png"), False),
            TileKind("tree", asset_path("images/tree.png"), True),
            TileKind("wood", asset_path("images/wood.png"), False)
        ]

        # Initialize the player
        player = Player(asset_path("images/player.jpg"), TILE_SIZE * 11, TILE_SIZE * 7,
                        speed=float(CONFIG.get('player_speed', _default_config['player_speed'])))

        # Center the camera on the player's initial position
        camera._x = player.x + player.image.get_width() / 2 - camera.width / 2
        camera._y = player.y + player.image.get_height() / 2 - camera.height / 2

        # debug logging removed

        map = Map(
            asset_path("images/spam.png"),
            tile_kinds,
            TILE_SIZE,
            tree_density=float(CONFIG.get('tree_density', _default_config['tree_density'])),
            clustered=bool(CONFIG.get('clustered_trees', _default_config['clustered_trees'])),
            tree_scale=float(CONFIG.get('tree_scale', _default_config['tree_scale'])),
            chunk_size=int(CONFIG.get('chunk_size', _default_config['chunk_size'])),
            max_tiles=int(CONFIG.get('max_tiles', _default_config['max_tiles']))
        )

        box_positions = [
            (0, 0), (7, 2), (1, 10),
            (12, -1), (14, 9), (13, 12),
            (20, 9), (22, -1), (24, 12),
            (2, 8), (15, 15), (17, 1),
            (1, 15)
        ]
        pixel_positions = [(x*TILE_SIZE, y*TILE_SIZE) for x, y in box_positions]
        box_sprites = StaticSprites(asset_path("images/box.png"), pixel_positions, TILE_SIZE)

        font = pygame.font.Font(None, 20)
        _overlay_msgs = []

        def add_msg(text):
            _overlay_msgs.append((text, pygame.time.get_ticks()))

        def draw_overlay(screen):
            now = pygame.time.get_ticks()
            y = 8
            for text, ts in _overlay_msgs[:]:
                if now - ts > 3000:
                    _overlay_msgs.remove((text, ts))
                    continue
                surf = font.render(text, True, (255, 255, 255))
                screen.blit(surf, (8, y))
                y += surf.get_height() + 2

        def save_config():
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            cfg_path = os.path.join(repo_root, 'config.json')
            try:
                with open(cfg_path, 'w', encoding='utf-8') as fh:
                    json.dump(CONFIG, fh, indent=2)
                add_msg(f"Config saved to {os.path.basename(cfg_path)}")
            except Exception as e:
                add_msg(f"Failed to save config: {e}")

        def save_game(path=None):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            save_path = path or os.path.join(repo_root, 'savegame.json')
            try:
                state = {
                    'version': 1,
                    'config': CONFIG,
                    'player': {'x': player.x, 'y': player.y, 'speed': player.speed},
                    'camera': {'_x': camera._x, '_y': camera._y},
                    'map': {
                        'tiles': map.tiles,
                        'tile_size': map.tile_size,
                        'tile_kinds': [tk.name for tk in map.tile_kinds],
                        'tree_density': map.tree_density,
                        'clustered': map.clustered,
                        'tree_scale': map.tree_scale,
                        'chunk_size': map.chunk_size,
                        'max_tiles': map.max_tiles
                    }
                }
                with open(save_path, 'w', encoding='utf-8') as fh:
                    json.dump(state, fh, indent=2)
                add_msg(f"Game saved to {os.path.basename(save_path)}")
            except Exception as e:
                add_msg(f"Failed to save game: {e}")

        def load_game(path=None):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            load_path = path or os.path.join(repo_root, 'savegame.json')
            if not os.path.exists(load_path):
                add_msg(f"Save not found: {os.path.basename(load_path)}")
                return
            try:
                with open(load_path, 'r', encoding='utf-8') as fh:
                    state = json.load(fh)

                # Restore config
                cfg = state.get('config')
                if isinstance(cfg, dict):
                    CONFIG.update(cfg)

                # Restore player
                p = state.get('player', {})
                try:
                    player.x = float(p.get('x', player.x))
                    player.y = float(p.get('y', player.y))
                    player.speed = float(p.get('speed', player.speed))
                except Exception:
                    pass

                # Restore camera
                cam = state.get('camera', {})
                try:
                    camera._x = float(cam.get('_x', camera._x))
                    camera._y = float(cam.get('_y', camera._y))
                except Exception:
                    pass

                # Restore map tiles and params
                m = state.get('map', {})
                saved_tiles = m.get('tiles')
                saved_tile_names = m.get('tile_kinds') or []

                if saved_tiles is not None:
                    # Remap saved tile indices to current tile_kinds order by name
                    name_to_index = {tk.name: idx for idx, tk in enumerate(tile_kinds)}
                    remap = {}
                    for i, name in enumerate(saved_tile_names):
                        remap[i] = name_to_index.get(name, i)

                    new_tiles = []
                    for row in saved_tiles:
                        new_row = [remap.get(int(v), int(v)) for v in row]
                        new_tiles.append(new_row)

                    new_map = Map.from_tiles(
                        new_tiles,
                        tile_kinds,
                        int(m.get('tile_size', TILE_SIZE)),
                        tree_density=m.get('tree_density'),
                        clustered=bool(m.get('clustered')),
                        max_tiles=int(m.get('max_tiles', map.max_tiles or _default_config['max_tiles'])),
                        tree_scale=m.get('tree_scale'),
                        chunk_size=int(m.get('chunk_size', map.chunk_size or _default_config['chunk_size']))
                    )
                    # Replace map reference in local scope
                    nonlocal_map_wrapper = globals()
                    # assign to local variable 'map' by mutating outer scope via closure trick
                    # (we simply update the existing map object's attributes where possible)
                    try:
                        # Swap attributes on existing map object to preserve references
                        map.tiles = new_map.tiles
                        map.tile_kinds = new_map.tile_kinds
                        map.tile_size = new_map.tile_size
                        map.tree_density = new_map.tree_density
                        map.clustered = new_map.clustered
                        map.max_tiles = new_map.max_tiles
                        map.tree_scale = new_map.tree_scale
                        map.chunk_size = new_map.chunk_size
                        map._chunks = None
                        map._images_converted = False
                    except Exception:
                        add_msg("Loaded map but failed to apply to current instance")

                add_msg(f"Game loaded from {os.path.basename(load_path)}")
            except Exception as e:
                add_msg(f"Failed to load game: {e}")

        def pause_menu():
            """Simple in-game pause menu. Navigable with arrows/W,S and Enter. ESC to resume."""
            menu_font = pygame.font.Font(None, 32)
            small_font = pygame.font.Font(None, 20)
            options = ["Resume", "Save", "Load", "Quit"]
            selected = 0
            # translucent overlay used on top of the live game render
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))

            while True:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            return
                        if ev.key in (pygame.K_UP, pygame.K_w):
                            selected = (selected - 1) % len(options)
                        elif ev.key in (pygame.K_DOWN, pygame.K_s):
                            selected = (selected + 1) % len(options)
                        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            choice = options[selected]
                            if choice == "Resume":
                                return
                            elif choice == "Save":
                                save_game()
                            elif choice == "Load":
                                load_game()
                                return
                            elif choice == "Quit":
                                pygame.quit()
                                sys.exit()

                # Render the last visible game frame so the world remains visible while paused
                try:
                    # draw map and sprites without updating game state
                    map.draw(screen)
                    for s in sprites:
                        s.draw(screen)
                    box_sprites.draw(screen)
                    draw_overlay(screen)
                    if SHOW_PERF:
                        draw_perf_hud(screen)
                except Exception:
                    # Fallback: clear screen if drawing fails
                    screen.fill((0, 0, 0))

                # Draw translucent overlay and menu UI on top
                screen.blit(overlay, (0, 0))
                title_surf = menu_font.render("PAUSED", True, (255, 255, 255))
                tx = (screen.get_width() - title_surf.get_width()) // 2
                ty = screen.get_height() // 4
                screen.blit(title_surf, (tx, ty))

                # Draw options
                oy = ty + 48
                for i, opt in enumerate(options):
                    color = (255, 220, 100) if i == selected else (220, 220, 220)
                    surf = small_font.render(opt, True, color)
                    sx = (screen.get_width() - surf.get_width()) // 2
                    screen.blit(surf, (sx, oy + i * 28))

                pygame.display.flip()
                clock.tick(60)

        def apply_tree_settings():
            scale_tree_images(map.tile_kinds, map.tile_size, float(CONFIG.get('tree_scale')))
            map._images_converted = False
            map._chunks = None
            add_msg(f"Applied tree_scale={CONFIG.get('tree_scale')}")


        
        SHOW_PERF = False

        def draw_perf_hud(screen):
            try:
                stats = map_render.last_draw_stats or {}
                lines = [
                    f"FPS: {clock.get_fps():.1f}",
                    f"Map draw: {stats.get('draw_ms', 0.0):.2f} ms",
                    f"Chunk blits: {stats.get('chunk_blits', 0)}"
                ]
                
                rendered = [font.render(ln, True, (255, 255, 255)) for ln in lines]
                w = max(s.get_width() for s in rendered)
                h = sum(s.get_height() + 2 for s in rendered)
                
                if rendered:
                    bg = pygame.Surface((w + 12, h + 8), pygame.SRCALPHA)
                    bg.fill((0, 0, 0, 160))
                    screen.blit(bg, (screen.get_width() - w - 16, 8))
                    y = 12
                    for s in rendered:
                        screen.blit(s, (screen.get_width() - w - 10, y))
                        y += s.get_height() + 2
            except Exception as e:
                print(f"PERF HUD ERROR: {e}")

        import time

        PERF_LOG = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'perf_slow.log')
        SLOW_FPS_THRESHOLD = 10.0
        SLOW_FRAMES_LIMIT = 30
        _slow_frame_count = 0
        _last_perf_log_time = 0.0
        # If the menu requested a load, apply it now (after player/map initialized)
        try:
            if do_load:
                load_game()
        except NameError:
            # do_load only exists when menu_action was start/load; ignore otherwise
            pass

        # Game Loop
        while running:
            frame_start = time.perf_counter()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    keys_down.add(event.key)
                    if event.key == pygame.K_F3:
                        map.toggle_debug()
                    elif event.key == pygame.K_F2:
                        try:
                            SHOW_PERF = not SHOW_PERF
                            add_msg(f"Perf HUD {'ON' if SHOW_PERF else 'OFF'}")
                        except Exception as e:
                            add_msg(f"Error toggling perf display: {str(e)}")
                            print(f"PERF TOGGLE ERROR: {e}")
                    elif event.key == pygame.K_F6:
                        try:
                            reload_hot_modules()
                            add_msg('Hot-reload complete')
                        except Exception as e:
                            add_msg(f'Reload failed: {e}')
                            print(f"HOTRELOAD ERROR: {e}")
                    elif event.key == pygame.K_F9:
                        save_game()
                    elif event.key == pygame.K_F10:
                        load_game()
                    elif event.key == pygame.K_ESCAPE:
                        pause_menu()
                    elif event.key == pygame.K_F5:
                        save_config()
                elif event.type == pygame.KEYUP:
                    keys_down.discard(event.key)
                elif event.type == pygame.ACTIVEEVENT and getattr(event, 'gain', 1) == 0:
                    keys_down.clear()

            # Remote server removed — no remote key integration

            dt = clock.tick_busy_loop(60)/1000.0 if hasattr(clock, 'tick_busy_loop') else clock.tick(60)/1000.0
            player.update(map, dt)

            screen.fill(clear_color)
            
            t0 = time.perf_counter()
            map.draw(screen)
            t1 = time.perf_counter()
            for s in sprites:
                s.draw(screen)
            box_sprites.draw(screen)
            t2 = time.perf_counter()

            draw_overlay(screen)
            if SHOW_PERF:
                draw_perf_hud(screen)

            # Remote server removed — no frame streaming

            pygame.display.flip()
            
            fps = clock.get_fps()
            if fps < SLOW_FPS_THRESHOLD:
                _slow_frame_count += 1
            else:
                _slow_frame_count = 0

            if _slow_frame_count >= SLOW_FRAMES_LIMIT and time.time() - _last_perf_log_time > 10.0:
                _last_perf_log_time = time.time()
                # ... (performance logging implementation)
                
            start_sleep = time.perf_counter()
            frame_end = time.perf_counter()

    elif menu_action == "settings":
        print("Settings menu not implemented yet.")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()