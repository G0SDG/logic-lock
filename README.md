# LogicLock

A small pygame-based prototype. This repository contains the game code in the `LogicLock/` package and a set of helper scripts in `tools/`.

## Running the game

Recommended: run from the repository root so tools and config file resolve correctly.

- Run the game (module form):

  python -m LogicLock.main

- Quick smoke-run (tools):

  python tools/test_run.py

## Configuration

Project settings are read from `config.json` at the repository root. If it is missing the project uses built-in defaults. Settings you can change:

- `tile_size` (integer) — base tile pixel size (default: 32)
- `player_speed` (float) — player movement speed in pixels/second (default: 150.0)
- `tree_scale` (float) — tree sprite height relative to `tile_size` (default: 4.0)
- `tree_density` (float in 0.0-1.0) — probability a tree tile remains after sparsification (default: 0.04)
- `clustered_trees` (bool) — enable light clustering on sparsified trees (default: true)
- `chunk_size` (int) — number of tiles per chunk for pre-rendering (default: 8)
- `max_tiles` (int) — maximum number of tiles along the larger image dimension (maps exceeding this are downscaled) (default: 120)
- `clear_color` (list of 3 ints) — RGB background color used to clear the screen each frame (default: [30,150,50])

Edit `config.json` and restart the game to take effect.

## Tools

Scripts in `tools/` are convenience helpers for inspecting maps and assets. Examples:

- `python tools/inspect_map_colors.py` — list top colors in `images/spam.png` and suggest a `.palette`
- `python tools/fix_images.py` — repair images stored as ASCII byte lists (keeps backups in `LogicLock/images/bak/`)

## Runtime hotkeys

You can adjust some runtime parameters while the game is running — changes are reflected immediately and can be saved to `config.json` with the Save hotkey.

- F2 — Toggle performance HUD (FPS, map draw time, chunk blits, rebuilds)
- F3 — Toggle debug overlay (chunk borders and tile bounds)
- F5 — Save current configuration back to `config.json`
- F6 — Force chunk rebuild
- `+` / `=` — Increase player speed (by 10 px/s)
- `-` / `_` — Decrease player speed (by 10 px/s)
- `[` / `]` — Decrease / Increase `tree_scale` (by 0.25)
- `,` / `.` — Decrease / Increase `tree_density` (by 0.01)

Note: The engine clamps chunk padding to a safe maximum (4 * tile_size) to avoid creating excessively large surfaces; if clamping happens you'll see a console warning and a `Clipped tiles` entry in the HUD.
## Notes

- No files were deleted during reorganization; historical `.bak` files were copied into `LogicLock/backups/`.
- Add new runtime options to `config.json` and update `LogicLock/main.py` to wire them through where needed.
