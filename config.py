import pygame
import utils

CELL_SIZE = 8
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 600
TOOLBAR_WIDTH = 400
SCREEN_WIDTH = WINDOW_WIDTH - TOOLBAR_WIDTH
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
FIRE_DIES_PROBABILITY = 0.03 # probability that the fire dies each frames, simulating a lifespan
FIRE_LIFESPAN = 20 # fire can't live more than this many frames
FIRE_LIFESPAN_VARIATION = 4 # FIRE_LIFESPAN gets +- FIRE_LIFESPAN_VARIATION for each fire particle
EMPTY_ID = 0
SAND_ID = 1
WATER_ID = 2
STONE_ID = 3
CHROMATIC_ID = 4
STEAM_ID = 5
FIRE_ID = 6
WOOD_ID = 7
BURNING_WOOD_ID = 8
SMOKE_ID = 9
ACID_ID = 10
current_material = SAND_ID  # Start with sand
simulation_is_on = True
frame_count = 0
MAX_SPREAD_DIST = 4 # water
BURNING_SPREAD_PROBABILITY = 0.01
BURNING_WOOD_LIFESPAN = 80
SPAWN_FIRE_PROBABILITY = 0.3 #probability of making a fire particle when burning wood
SPAWN_SMOKE_PROBABILITY_WOOD = SPAWN_FIRE_PROBABILITY + 0.3 #probability smoke appearing when wood burns or when fire dies
SPAWN_SMOKE_PROBABILITY_FIRE = 0.05
SMOKE_DISSIPATE_PROBABILITY = 0.06
ANNIVERSAIRE = True

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
    (240, 240, 240),
    (225, 225, 225),
    (210, 210, 210),
    (195, 195, 195)
]

FIRE_COLORS = [
    (255, 255, 102),
    (255, 204, 0),
    (255, 102, 0),
    (204, 51, 0) 
]

WOOD_COLORS = [
    (150, 95, 45), 
    (100, 60, 30), 
    (200, 140, 90) 
]

BURNING_WOOD_COLORS = [
    (70, 40, 20),
    (200, 80, 0),
    (255, 200, 100)
]

ACID_COLORS = [
    (153, 255, 0),
    (102, 204, 0),
    (51, 153, 0)
]

SMOKE_COLORS = [
    (150, 150, 150),
    (100, 100, 100),
    (70, 70, 70) 
]

EMPTY_COLOR = (0, 0, 0)
CHROMATIC_SPEED = 1
CHROMATIC_PALETTE = utils.generate_palette(CHROMATIC_COLORS)
palette_size = len(CHROMATIC_PALETTE)
