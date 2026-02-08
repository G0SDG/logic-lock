import pygame

class Camera:
    """A small camera object that keeps float positions for smooth movement but exposes
    integer `x`/`y` properties for legacy code that expects numeric positions."""
    def __init__(self):
        self._x = 0.0
        self._y = 0.0
        self.width = 0
        self.height = 0
        # smoothing factor in [0,1], 0 = immediate snap, higher = more smoothing
        self.smooth = 0.0

    @property
    def x(self):
        return int(self._x)

    @x.setter
    def x(self, value):
        try:
            self._x = float(value)
        except Exception:
            self._x = float(int(value))

    @property
    def y(self):
        return int(self._y)

    @y.setter
    def y(self, value):
        try:
            self._y = float(value)
        except Exception:
            self._y = float(int(value))

camera = Camera()


def create_screen(width, height, title):
    """Create the pygame display and set camera size fields."""
    pygame.display.set_caption(title)
    screen = pygame.display.set_mode((width, height))
    camera.width = width
    camera.height = height
    return screen
