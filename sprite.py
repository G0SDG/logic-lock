import os
import pygame
from .camera import camera

sprites = []
loaded = {}

def _resolve_image_path(image):
    if os.path.isabs(image):
        return image
    return os.path.join(os.path.dirname(__file__), image)

class Sprite:
    def __init__(self, image, x, y):
        img_path = _resolve_image_path(image)
        if img_path in loaded:
            self.image = loaded[img_path]
        else:
            self.image = pygame.image.load(img_path)
            loaded[img_path] = self.image
        self.x = x
        self.y = y
        sprites.append(self)

    def delete(self):
        sprites.remove(self)

    def draw(self, screen):
        screen.blit(self.image, (int(self.x - camera.x), int(self.y - camera.y)))

