import os
import pygame

class TileKind:
    """Represents a tile type with its image and properties.

    Fields:
      name: string
      image: pygame.Surface
      is_solid: bool
      mask: pygame.Mask or None (set after conversion to display format)
    """
    def __init__(self, name, image, is_solid):
        image_path = image if os.path.isabs(image) else os.path.join(os.path.dirname(__file__), image)
        self.name = name
        self.image = pygame.image.load(image_path)
        self.is_solid = is_solid
        self.mask = None

    def convert_for_display(self):
        """Convert the surface to display format and build a mask for pixel-perfect collisions."""
        try:
            self.image = self.image.convert_alpha()
        except Exception:
            self.image = self.image.convert()
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def __repr__(self):
        return f"TileKind(name={self.name!r}, size={self.image.get_size()}, solid={self.is_solid})"
