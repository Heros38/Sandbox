import pygame

CELL_SIZE = 8
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
TOOLBAR_WIDTH = 400
GRID_HEIGHT = WINDOW_HEIGHT // CELL_SIZE
GRID_WIDTH = (WINDOW_WIDTH - TOOLBAR_WIDTH) // CELL_SIZE

GRAVITY = 0.2
FRICTION = 0.02
spawn_radius = 0
random_velocity = False
RANDOM_SPAWN_PROBABILITY = 0.75
SAND_ID = 1
WATER_ID = 2
STONE_ID = 3
current_material = SAND_ID # Start with sand
simulation_is_on = True

SAND_COLORS = [
    (210, 180, 140),
    (194, 178, 128),
    (244, 213, 141),
    (178, 153, 110),
]
WATER_COLORS = [
    (65, 105, 225),   
    (0, 0, 128),     
    (25, 25, 112)
]

STONE_COLORS = [
    (190, 200, 205),  
    (140, 150, 155),  
    (90, 100, 105),  
    (50, 55, 60)      
]

EMPTY_COLOR = (0, 0, 0)