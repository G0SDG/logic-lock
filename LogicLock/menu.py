import pygame
import sys
import os


def _asset_path(name):
    return os.path.join(os.path.dirname(__file__), 'images', name)


def _load_image_if_exists(name):
    path = _asset_path(name)
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            try:
                return pygame.image.load(path)
            except Exception:
                return None
    return None


def _auto_assign_images():
    img_dir = os.path.join(os.path.dirname(__file__), 'images')
    if not os.path.isdir(img_dir):
        return None, None, [None, None, None]

    files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    if not files:
        return None, None, [None, None, None]

    def find_pref(keywords, exclude=None):
        for f in files:
            lf = f.lower()
            if exclude and f == exclude:
                continue
            for k in keywords:
                if k in lf:
                    return f
        return None

    bg = find_pref(['bg', 'background', 'menu'])
    if not bg:
        # choose largest file by bytes as background
        bg = max(files, key=lambda f: os.path.getsize(os.path.join(img_dir, f)))

    logo = find_pref(['logo', 'title'])
    if not logo:
        logo = next((f for f in files if f != bg), bg)

    start_img = find_pref(['start', 'play', 'go'])
    settings_img = find_pref(['setting', 'settings', 'option'])
    exit_img = find_pref(['exit', 'quit'])

    remaining = [f for f in files if f not in {bg, logo, start_img, settings_img, exit_img}]
    picks = []
    for pick in (start_img, settings_img, exit_img):
        if pick:
            picks.append(pick)
        else:
            picks.append(remaining.pop(0) if remaining else None)

    # debug: print chosen filenames
    try:
        print(f"[menu] auto_assign candidates: bg={bg}, logo={logo}, picks={picks}")
    except Exception:
        pass

    # load images (returns surfaces or None)
    bg_surf = _load_image_if_exists(bg) if bg else None
    logo_surf = _load_image_if_exists(logo) if logo else None
    option_surfaces = [
        _load_image_if_exists(picks[0]) if picks[0] else None,
        _load_image_if_exists(picks[1]) if picks[1] else None,
        _load_image_if_exists(picks[2]) if picks[2] else None,
    ]

    try:
        print(f"[menu] loaded surfaces: bg={bool(bg_surf)}, logo={bool(logo_surf)}, options={[bool(s) for s in option_surfaces]}")
    except Exception:
        pass

    return bg_surf, logo_surf, option_surfaces


def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Main Menu")

    font = pygame.font.Font(None, 74)
    menu_options = ["Start Game", "Settings", "Exit"]
    selected_option = 0

    # Optional assets (place files in LogicLock/images/)
    bg = _load_image_if_exists('menu_bg.png')
    logo = _load_image_if_exists('menu_logo.png')
    option_images = [
        _load_image_if_exists('menu_start.png'),
        _load_image_if_exists('menu_settings.png'),
        _load_image_if_exists('menu_exit.png'),
    ]

    # If a dedicated bacmenu.png exists, prefer it as the background (override any menu_bg.png)
    bac = _load_image_if_exists('bacmenu.png')
    if bac:
        bg = bac
        try:
            print('[menu] overriding background with bacmenu.png')
        except Exception:
            pass

    # Explicit developer-named overrides (highest priority)
    # prefer 'play button.png' for Start, 'load button.png' for Settings, 'save button.png' for Exit
    play_btn = _load_image_if_exists('play button.png')
    load_btn = _load_image_if_exists('load button.png')
    save_btn = _load_image_if_exists('save button.png')
    # prefer 'logo.jpg' or 'logo.png' for the logo
    explicit_logo = _load_image_if_exists('logo.jpg') or _load_image_if_exists('logo.png')
    if explicit_logo:
        logo = explicit_logo
    if play_btn or load_btn or save_btn:
        option_images = [play_btn or option_images[0], load_btn or option_images[1], save_btn or option_images[2]]

    # If explicit menu_* assets are not present, prefer developer-named images
    explicit_exists = any(
        os.path.exists(_asset_path(n)) for n in ('menu_bg.png', 'menu_logo.png', 'menu_start.png', 'menu_settings.png', 'menu_exit.png')
    ) or any(option_images)

    if not explicit_exists:
        # Look for developer-specified names: logo, play, load, save
        img_dir = os.path.join(os.path.dirname(__file__), 'images')
        found = {k: None for k in ('logo', 'play', 'load', 'save')}
        if os.path.isdir(img_dir):
            for f in os.listdir(img_dir):
                lf = f.lower()
                for k in found:
                    if k in lf and found[k] is None:
                        found[k] = f

        # Map: `logo` -> logo; `play` -> start; `load` -> settings; `save` -> exit
        # also prefer explicit 'bacmenu.png' for background if present
        mapped_bg = found.get('logo') or found.get('play') or ('bacmenu.png' if os.path.exists(os.path.join(img_dir, 'bacmenu.png')) else None)
        mapped_logo = found.get('logo') or None
        mapped_start = found.get('play') or None
        mapped_settings = found.get('load') or None
        mapped_exit = found.get('save') or None

        if any(mapped_logo or mapped_start or mapped_settings or mapped_exit):
            print(f"[menu] found developer images: {found}")
            # load these surfaces (prefer explicit previously loaded surfaces)
            logo = logo or (_load_image_if_exists(mapped_logo) if mapped_logo else None)
            option_images = [
                option_images[0] or (_load_image_if_exists(mapped_start) if mapped_start else None),
                option_images[1] or (_load_image_if_exists(mapped_settings) if mapped_settings else None),
                option_images[2] or (_load_image_if_exists(mapped_exit) if mapped_exit else None),
            ]
            # choose a sensible background if none
            bg = bg or (_load_image_if_exists(mapped_bg) if mapped_bg else None)
            print(f"[menu] after mapping: bg={bool(bg)}, logo={bool(logo)}, options={[bool(o) for o in option_images]}")
        else:
            print('[menu] no explicit menu_* assets or developer-named images found — attempting auto-assign')
            bg_auto, logo_auto, options_auto = _auto_assign_images()
            # prefer explicit if present, otherwise use auto-assigned
            bg = bg or bg_auto
            logo = logo or logo_auto
            option_images = [oi or ao for oi, ao in zip(option_images, options_auto)]
            print(f"[menu] after auto-assign: bg={bool(bg)}, logo={bool(logo)}, options={[bool(o) for o in option_images]}")

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if menu_options[selected_option] == "Start Game":
                        return "start_game"
                    elif menu_options[selected_option] == "Settings":
                        return "settings"
                    elif menu_options[selected_option] == "Exit":
                        pygame.quit()
                        sys.exit()

        # Draw background (fallback to clear color)
        if bg:
            bg_scaled = pygame.transform.scale(bg, screen.get_size())
            screen.blit(bg_scaled, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Draw logo if available and scale everything to fit the visible area
        top_margin = 40
        bottom_margin = 40
        spacing = 18
        y_offset = top_margin

        # initial logo sizing (conservative caps)
        logo_display = None
        if logo:
            lw, lh = logo.get_size()
            max_logo_w = int(screen.get_width() * 0.5)
            max_logo_h = int(screen.get_height() * 0.2)
            initial_scale = min(1.0, max_logo_w / lw if lw else 1.0, max_logo_h / lh if lh else 1.0)
            logo_display = pygame.transform.rotozoom(logo, 0, initial_scale) if initial_scale != 1.0 else logo

        # initial option sizing
        opt_max_w = int(screen.get_width() * 0.5)
        opt_max_h = int(screen.get_height() * 0.09)
        scaled_options = []
        for img in option_images:
            if img:
                iw, ih = img.get_size()
                s = min(1.0, opt_max_w / iw if iw else 1.0, opt_max_h / ih if ih else 1.0)
                scaled_options.append(pygame.transform.rotozoom(img, 0, s) if s != 1.0 else img)
            else:
                scaled_options.append(None)

        # compute total required height
        def _height_of_logo(ld):
            return ld.get_height() if ld else 0

        def _height_of_opt(o):
            return o.get_height() if o else font.get_height()

        total_h = _height_of_logo(logo_display)
        if logo_display:
            total_h += spacing
        for opt in scaled_options:
            total_h += _height_of_opt(opt)
        total_h += spacing * (len(menu_options) - 1)

        available_h = screen.get_height() - top_margin - bottom_margin

        # if doesn't fit, scale everything down proportionally
        if total_h > available_h and total_h > 0:
            scale_down = available_h / total_h
            if logo_display:
                logo_display = pygame.transform.rotozoom(logo_display, 0, scale_down)
            for idx, opt in enumerate(scaled_options):
                if opt:
                    scaled_options[idx] = pygame.transform.rotozoom(opt, 0, scale_down)

            # recompute total_h after scaling
            total_h = _height_of_logo(logo_display)
            if logo_display:
                total_h += spacing
            for opt in scaled_options:
                total_h += _height_of_opt(opt)
            total_h += spacing * (len(menu_options) - 1)

        # center the block vertically in remaining area, then nudge it upward
        remaining_space = screen.get_height() - y_offset - bottom_margin
        start_y = y_offset + max(0, (remaining_space - total_h) // 2)
        # nudge up a bit so elements sit higher on the screen
        nudge_up = 60
        start_y = max(top_margin, start_y - nudge_up)

        # Draw translucent panel behind options for contrast
        panel_padding = 12
        panel_w = min(int(screen.get_width() * 0.9), screen.get_width() - 20)
        panel_x = int((screen.get_width() - panel_w) // 2)
        panel_y = start_y - panel_padding
        panel_h = total_h + panel_padding * 2
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 160))
        screen.blit(panel_surf, (panel_x, panel_y))

        # Draw the logo (centered)
        y = start_y
        if logo_display:
            lw2, lh2 = logo_display.get_size()
            logo_x = screen.get_width() // 2 - lw2 // 2
            screen.blit(logo_display, (logo_x, y))
            y += lh2 + spacing

        # Draw options centered horizontally
        for i, option in enumerate(menu_options):
            img = scaled_options[i]
            if img:
                # highlight selected subtly
                img_display = pygame.transform.rotozoom(img, 0, 1.04) if i == selected_option else img
                iw, ih = img_display.get_size()
                x = screen.get_width() // 2 - iw // 2
                screen.blit(img_display, (x, y))
                y += ih + spacing
            else:
                color = (255, 255, 255) if i == selected_option else (200, 200, 200)
                text = font.render(option, True, color)
                tx = screen.get_width() // 2 - text.get_width() // 2
                screen.blit(text, (tx, y))
                y += font.get_height() + spacing

        pygame.display.flip()
        clock.tick(30)


    # Import-time diagnostic: when module is imported (as `menu` or `LogicLock.menu`),
    # print which images would be chosen so main.py's import shows the mapping.
    try:
        if __name__ in ('menu', 'LogicLock.menu'):
            explicit_exists = any(
                os.path.exists(_asset_path(n)) for n in ('menu_bg.png', 'menu_logo.png', 'menu_start.png', 'menu_settings.png', 'menu_exit.png')
            )
            if not explicit_exists:
                print('[menu] import-time: no explicit menu_* assets — auto-assigning for diagnostic')
                _auto_assign_images()
            else:
                print('[menu] import-time: explicit menu_* assets detected')
    except Exception as _e:
        print(f'[menu] import-time diagnostic error: {_e}')