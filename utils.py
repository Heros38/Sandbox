# import math
from numba import jit, types
import numpy as np
import pygame
import math


@jit(nopython=True, cache=True)
def get_line(x0: int, y0: int, x1: int, y1: int):
    points = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return points


def lerp_color(color1: tuple, color2: tuple, t: float):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = r1 + (r2 - r1) * t
    g = g1 + (g2 - g1) * t
    b = b1 + (b2 - b1) * t
    return (int(r), int(g), int(b))


def generate_palette(colors_table: list, steps=60):
    palette = []
    colors = colors_table + [colors_table[0]]
    for i in range(len(colors) - 1):
        for step in range(steps):
            t = step / steps
            new_color = lerp_color(colors[i], colors[i+1], t)
            palette.append(new_color)
    return palette


@jit(nopython=True, cache=True)
def get_shuffled_tab(tab: list):
    directions = np.array(tab, dtype=np.int32)
    np.random.shuffle(directions)
    return directions



def get_text_pixels_pygame(text:str, grid_width:int, grid_height:int, height_center:float):
    tempscreen = pygame.Surface((grid_width, grid_height))
    font = pygame.font.SysFont("Arial", 30, bold=True)
    tempscreen.fill((0, 0, 0))
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect()
    text_rect.center = (grid_width // 2, (grid_height * height_center) // 2)
    tempscreen.blit(text_surface, text_rect)

    tab = []
    #tab = [[0 for _ in range(grid_width)] for _ in range(grid_height)] 
    for y in range(grid_height):
        for x in range(grid_width):
            if tempscreen.get_at((x, y)) == (255, 255, 255):
                tab.append((x, y))
    return tab