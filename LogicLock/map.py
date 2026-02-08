import os
import pygame
from .camera import camera
from .tilekind import TileKind
from .map_io import image_to_tiles, text_to_tiles, find_palette_file_for_image, load_palette_from_file, sparsify_trees, scale_tree_images
from .map_render import convert_tile_images, compute_extra_pixels, create_chunks, draw_map


class Map:
    """Thin orchestrator that delegates IO and rendering to helper modules."""
    def __init__(self, map_file, tile_kinds, tile_size, color_map=None, tree_density=None, clustered=False, max_tiles=120, tree_scale=None, chunk_size=8):
        self.tile_kinds = tile_kinds
        self.tile_size = tile_size
        self.color_map = None
        self.tree_density = tree_density
        self.clustered = clustered
        self.max_tiles = max_tiles
        self.tree_scale = tree_scale
        self.chunk_size = int(chunk_size) if chunk_size and chunk_size > 0 else 8

        # Ensure required properties
        self._chunks = None
        self._images_converted = False
        self._extra_px_x = 0
        self._extra_px_y = 0

        # Resolve path relative to this module if a relative path was provided
        if not os.path.isabs(map_file):
            map_file = os.path.join(os.path.dirname(__file__), map_file)
        if not os.path.exists(map_file):
            raise FileNotFoundError(f"Map file not found: {map_file}")

        # If the map is an image, try to find a palette file nearby if none provided
        palette_path = None
        if isinstance(color_map, str):
            palette_path = color_map
        else:
            candidate = find_palette_file_for_image(map_file)
            if candidate:
                palette_path = candidate

        # Load tiles (image or text)
        lower = map_file.lower()
        if lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            self.tiles, (mw, mh) = image_to_tiles(map_file, tile_kinds, max_tiles=self.max_tiles, color_map=palette_path)
        else:
            self.tiles = text_to_tiles(map_file)

        # Optionally scale tree images before conversion
        if self.tree_scale is not None:
            scale_tree_images(self.tile_kinds, self.tile_size, self.tree_scale)

        # Optionally sparsify tree tiles
        if self.tree_density is not None and 0.0 <= self.tree_density <= 1.0:
            self.tiles = sparsify_trees(self.tiles, self.tile_kinds, self.tree_density, self.clustered)

    @classmethod
    def from_tiles(cls, tiles, tile_kinds, tile_size, tree_density=None, clustered=False, max_tiles=120, tree_scale=None, chunk_size=8):
        """Construct a Map directly from a tiles 2D-list (used when loading saved state)."""
        self = cls.__new__(cls)
        # assign basic fields
        self.tile_kinds = tile_kinds
        self.tile_size = tile_size
        self.color_map = None
        self.tree_density = tree_density
        self.clustered = clustered
        self.max_tiles = max_tiles
        self.tree_scale = tree_scale
        self.chunk_size = int(chunk_size) if chunk_size and chunk_size > 0 else 8

        # runtime-only caches
        self._chunks = None
        self._images_converted = False
        self._extra_px_x = 0
        self._extra_px_y = 0

        # set provided tiles
        self.tiles = tiles

        # Optionally scale tree images before conversion
        if self.tree_scale is not None:
            scale_tree_images(self.tile_kinds, self.tile_size, self.tree_scale)

        # Do not re-sparsify when constructing from saved tiles; keep provided tiles as-is.

        return self

    def draw(self, screen):
        # Ensure images have been converted for display and masks built
        if not self._images_converted:
            convert_tile_images(self.tile_kinds)
            self._images_converted = True

        # compute extra pixel margins used in chunking
        self._extra_px_x, self._extra_px_y = compute_extra_pixels(self.tile_kinds, self.tile_size)

        # Build chunk cache if needed
        if self._chunks is None:
            self._chunks = create_chunks(self.tiles, self.tile_kinds, self.tile_size, self.chunk_size, self._extra_px_x, self._extra_px_y)

        # Delegate the actual draw to rendering helper (pass debug flag)
        draw_map(screen, self.tiles, self.tile_kinds, self.tile_size, self._chunks, self._extra_px_x, self._extra_px_y, debug=getattr(self, '_debug', False))

    
    
    def toggle_debug(self):
        """Toggle debug overlay on/off and mark that a toggle occurred (for screenshot)."""
        self._debug = not getattr(self, '_debug', False)
        self._debug_just_toggled = True
        print(f"Map debug mode {'ON' if self._debug else 'OFF'}")
