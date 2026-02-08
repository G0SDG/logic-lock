import pygame

# Keeps track of what key is down (event-driven fallback)
keys_down = set()

def is_key_pressed(key):
    """Return True if the key is currently pressed.

    Prefer to use the real-time keyboard state (pygame.key.get_pressed()) so
    missed KEYUP events or focus loss do not leave keys logically stuck.
    Fall back to the event-driven `keys_down` set for compatibility.
    """
    try:
        pressed = pygame.key.get_pressed()
        return bool(pressed[key]) or (key in keys_down)
    except Exception:
        return key in keys_down
