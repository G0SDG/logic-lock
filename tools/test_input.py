"""
Quick input test script for LogicLock input handling.
Run from the workspace root (so it can import LogicLock):
  python tools/test_input.py

What it does:
- Initializes a small pygame window
- Simulates a KEYDOWN for the RIGHT arrow, pumps events and prints
- Simulates a KEYUP for the RIGHT arrow and prints
- Shows whether the project's input.is_key_pressed sees the key as pressed

If this script prints `True` after KEYDOWN and `False` after KEYUP, input handling is working.
"""

import sys, os
import pygame
from LogicLock.input import is_key_pressed, keys_down

pygame.init()
screen = pygame.display.set_mode((240,80))
clock = pygame.time.Clock()

keys_down.clear()
print('initial pressed RIGHT:', is_key_pressed(pygame.K_RIGHT))

# simulate KEYDOWN
evt = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT})
pygame.event.post(evt)
for i in range(3):
    for e in pygame.event.get():
        if e.type == pygame.KEYDOWN:
            keys_down.add(e.key)
        elif e.type == pygame.KEYUP:
            keys_down.discard(e.key)
    print(f'after KEYDOWN loop {i}, is pressed:', is_key_pressed(pygame.K_RIGHT))
    clock.tick(30)

# simulate KEYUP
evt_up = pygame.event.Event(pygame.KEYUP, {'key': pygame.K_RIGHT})
pygame.event.post(evt_up)
for i in range(3):
    for e in pygame.event.get():
        if e.type == pygame.KEYDOWN:
            keys_down.add(e.key)
        elif e.type == pygame.KEYUP:
            keys_down.discard(e.key)
    print(f'after KEYUP loop {i}, is pressed:', is_key_pressed(pygame.K_RIGHT))
    clock.tick(30)

pygame.quit()
print('done')