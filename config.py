import pygame
import utils

CELL_SIZE = 5
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
TOOLBAR_WIDTH = 400
GRID_HEIGHT = WINDOW_HEIGHT // CELL_SIZE
GRID_WIDTH = (WINDOW_WIDTH - TOOLBAR_WIDTH) // CELL_SIZE
FPS_LIMIT = 60

GRAVITY = 0.2
FRICTION = 0.02
spawn_radius = 0
random_velocity = False
RANDOM_SPAWN_PROBABILITY = 0.75
CONDENSE_PROBABILITY = 0.01 # probability that the steam turns into water when at the top of the screen
STEAM_TO_WATER_RATIO = 2 # how many steam particle is needed to make one water particle on average
EMPTY_ID = 0
SAND_ID = 1
WATER_ID = 2
STONE_ID = 3
CHROMATIC_ID = 4
STEAM_ID = 5
current_material = SAND_ID  # Start with sand
simulation_is_on = True
frame_count = 0
MAX_SPREAD_DIST = 4

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
CHROMATIC_COLORS = [
    (255, 0, 0),
    (255, 127, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 0, 255),
    (75, 0, 130),
    (148, 0, 211)
]

STEAM_COLORS = [
    (240, 240, 240),  # Almost White
    (225, 225, 225),  # Very Light Gray
    (210, 210, 210),  # Subtle Gray
    (195, 195, 195)   # Faint Shadow Gray
]

EMPTY_COLOR = (0, 0, 0)
CHROMATIC_SPEED = 1
CHROMATIC_PALETTE = utils.generate_palette(CHROMATIC_COLORS)
palette_size = len(CHROMATIC_PALETTE)
