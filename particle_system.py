import pygame
import random
import math
import time
from config import *
from utils import *
from numba import jit


class Particle:
    __slots__ = ('type', 'x', 'y', 'tx', 'ty', 'vx', 'vy', 'color', 'lifespan')

    def __init__(self, type, x, y, color):
        self.type = type
        self.x = x
        self.y = y
        self.tx = float(x)
        self.ty = float(y)
        self.vx = 0.0
        self.vy = 1.0
        self.color = color
        self.lifespan = 0

    def __repr__(self):
        return f"P(x:{self.x}, y:{self.y})"


grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
active_particles = set()
active_particles_copy = set()
particles_to_clear = set()
particles_to_draw = set()
chromatic_particles = set()
active_smoke_particles = set()
fire_particles = set()
burning_wood = set()
acid_particles = set()


def initialize_grid():
    global grid, grid_surface
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    grid_surface = pygame.Surface(
        (GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)).convert()
    grid_surface.fill(EMPTY_COLOR)


def draw_grid(target_screen):
    global grid_surface
    for (x, y) in particles_to_clear:
        pygame.draw.rect(grid_surface, EMPTY_COLOR,
                         (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for p in particles_to_draw:
        pygame.draw.rect(grid_surface, p.color, (p.x * CELL_SIZE,
                         p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    target_screen.blit(grid_surface, (0, 0))
    particles_to_clear.clear()
    particles_to_draw.clear()


def update_near_particles(x: int, y: int):
    ny = y - 1
    if 0 <= ny < GRID_HEIGHT:
        for dx in [-1, 0, 1]:  # normal falling blocks
            nx = x + dx
            if 0 <= nx < GRID_WIDTH:
                p = grid[ny][nx]
                if p is not None:
                    if p.type in (SAND_ID, WATER_ID, ACID_ID):
                        if p not in active_particles:
                            active_particles.add(p)
                            active_particles_copy.add(p)
                        if p.type == ACID_ID:
                            acid_particles.add(p)
    for dx in [-1, 1]:  # water because it can spread sideways (also steam)
        nx = x + dx
        if 0 <= nx < GRID_WIDTH:
            p = grid[y][nx]
            if p is not None:
                if p.type in (WATER_ID, ACID_ID):
                    if p not in active_particles:
                        active_particles.add(p)
                        active_particles_copy.add(p)
                    if p.type == ACID_ID:
                        acid_particles.add(p)
                elif p.type == STEAM_ID or p.type == SMOKE_ID:
                    active_smoke_particles.add(p)
    ny = y + 1
    if 0 <= ny < GRID_HEIGHT:
        for dx in [-1, 0, 1]:  # elements that go upwards like steam
            nx = x + dx
            if 0 <= nx < GRID_WIDTH:
                p = grid[ny][nx]
                if p is not None:
                    if p.type == STEAM_ID or p.type == SMOKE_ID:
                        active_smoke_particles.add(p)


@jit(nopython=True, cache=True, fastmath=True)
def calculate_color_index(current_time: float, p_x: int, p_y: int, speed_factor: int, spatial_factor: int, palette_size: int):
    return int(current_time * speed_factor + p_x * spatial_factor + p_y * spatial_factor) % palette_size

def cycle_colors(CHROMATIC_PALETTE: list, palette_size: int):
    current_time = time.time()
    for p in chromatic_particles:
        speed_factor = 50
        spatial_factor = 2
        
        index = calculate_color_index(current_time, p.x, p.y, speed_factor, spatial_factor, palette_size)
        
        new_color = CHROMATIC_PALETTE[index]
        if p.color != new_color:
            p.color = new_color
            particles_to_draw.add(p)


@jit(nopython=True, cache=True, fastmath=True)
def apply_gravity(vx: float, vy: float, tx: float, ty: float, gravity: float):
    V2 = vx**2 + vy**2
    if V2 > 0.0001:
        V = math.sqrt(V2)
        damping = 1 - FRICTION * V
        vx *= damping
        vy = gravity + damping * vy
    else:
        vy = gravity
    target_tx = tx + vx
    target_ty = ty + vy
    return target_tx, target_ty, round(target_tx), round(target_ty), vx, vy

def update_acid_particles():
    acid_particles_copy = acid_particles.copy()
    for p in acid_particles_copy:
        previous_x, previous_y = p.x, p.y
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = p.x + dx, p.y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                target_cell = grid[ny][nx]
                if target_cell != None and target_cell.type != ACID_ID:
                    grid[previous_y][previous_x] = None
                    grid[ny][nx] = None
                    active_particles.discard(p)
                    acid_particles.discard(p)
                    particles_to_draw.discard(p)
                    active_particles.discard(target_cell)
                    fire_particles.discard(target_cell)
                    burning_wood.discard(target_cell)
                    active_smoke_particles.discard(target_cell)
                    chromatic_particles.discard(target_cell)
                    particles_to_draw.discard(target_cell)
                    particles_to_clear.add((previous_x, previous_y))
                    particles_to_clear.add((nx, ny))
                    update_near_particles(nx, ny)
                    update_near_particles(previous_x, previous_y)
                    break

def update_fire_particles():
    fire_particles_copy = fire_particles.copy()
    for p in fire_particles_copy:
        p.lifespan -= 1
        previous_x, previous_y = p.x, p.y
        if random.random() <= FIRE_DIES_PROBABILITY or p.lifespan == 0:
            grid[previous_y][previous_x] = None
            fire_particles.discard(p)
            particles_to_draw.discard(p)
            if random.random() <= SPAWN_SMOKE_PROBABILITY_FIRE: #spawns smoke
                smoke = Particle(SMOKE_ID, previous_x, previous_y, random.choice(SMOKE_COLORS))
                active_smoke_particles.add(smoke)
                grid[previous_y][previous_x] = smoke
                particles_to_draw.add(smoke)
            else:
                particles_to_clear.add((previous_x, previous_y))
        else:
            ny = previous_y - 1
            if ny >= 0:
                for dx in random.sample([-1, 0, 1], 3):
                    nx = previous_x + dx
                    if 0 <= nx < GRID_WIDTH:
                        target_cell = grid[ny][nx]
                        if target_cell == None:  # fire just moves
                            p.x = nx
                            p.y = ny
                            p.tx, p.ty = p.x, p.y
                            grid[ny][nx] = p
                            grid[previous_y][previous_x] = None
                            particles_to_clear.add((previous_x, previous_y))
                            particles_to_draw.add(p)
                            break
                        # fire encounters water -> create steam
                        elif target_cell.type == WATER_ID:
                            water_particle = grid[ny][nx]
                            grid[ny][nx] = None
                            grid[previous_y][previous_x] = None
                            active_particles.discard(water_particle)
                            fire_particles.discard(p)
                            particles_to_clear.add((previous_x, previous_y))
                            particles_to_clear.add((nx, ny))
                            steam1 = Particle(STEAM_ID, nx, ny, random.choice(STEAM_COLORS))
                            steam2 = Particle(STEAM_ID, previous_x, previous_y, random.choice(STEAM_COLORS))
                            grid[ny][nx] = steam1
                            grid[previous_y][previous_x] = steam2
                            active_smoke_particles.add(steam1)
                            active_smoke_particles.add(steam2)
                            particles_to_draw.add(steam1)
                            particles_to_draw.add(steam2)
                            particles_to_draw.discard(p)
                            break
                        # fire encounters wood, making burning wood
                        elif target_cell.type == WOOD_ID:
                            grid[ny][nx] = None
                            grid[previous_y][previous_x] = None
                            fire_particles.discard(p)
                            particles_to_draw.discard(p)
                            particles_to_clear.add((previous_x, previous_y))
                            burning_wood_particle = Particle(BURNING_WOOD_ID, nx, ny, random.choice(BURNING_WOOD_COLORS))
                            burning_wood_particle.lifespan = BURNING_WOOD_LIFESPAN
                            grid[ny][nx] = burning_wood_particle
                            particles_to_draw.add(burning_wood_particle)
                            burning_wood.add(burning_wood_particle)
                            break

def update_burning_wood():
    burning_wood_copy = burning_wood.copy()
    for p in burning_wood_copy:
        previous_x, previous_y = p.x, p.y
        burnt = False
        p.lifespan -= 1

        for dy in range(-1, 2):
                ny = previous_y + dy
                if 0 <= ny < GRID_HEIGHT:
                    for dx in range(-1, 2):
                        nx = previous_x + dx
                        if 0 <= nx < GRID_WIDTH:
                            checked_cell = grid[ny][nx]
                            if checked_cell != None and checked_cell.type == WATER_ID:
                                grid[ny][nx] = None
                                grid[previous_y][previous_x] = None
                                burning_wood.discard(p)
                                active_particles.discard(checked_cell)
                                steam_particle = Particle(STEAM_ID, nx, ny, random.choice(STEAM_COLORS))
                                wood_particle = Particle(WOOD_ID, previous_x, previous_y, random.choice(WOOD_COLORS))
                                grid[previous_y][previous_x] = wood_particle
                                grid[ny][nx] = steam_particle
                                active_smoke_particles.add(steam_particle)
                                particles_to_draw.add(steam_particle)
                                particles_to_draw.add(wood_particle)
                                continue


        if p.lifespan == 0:
            grid[p.y][previous_x] = None
            burning_wood.discard(p)
            particles_to_clear.add((previous_x, previous_y))
            r = random.random()
            if r <= SPAWN_FIRE_PROBABILITY: #spawns fire particle
                fire_particle = Particle(FIRE_ID, previous_x, previous_y, random.choice(FIRE_COLORS))
                p.lifespan = FIRE_LIFESPAN + random.randint(-FIRE_LIFESPAN_VARIATION, FIRE_LIFESPAN_VARIATION)
                grid[previous_y][previous_x] = fire_particle
                fire_particles.add(fire_particle)
            elif r <= SPAWN_SMOKE_PROBABILITY_WOOD:
                smoke = Particle(SMOKE_ID, previous_x, previous_y, random.choice(SMOKE_COLORS))
                active_smoke_particles.add(smoke)
                grid[previous_y][previous_x] = smoke
                particles_to_draw.add(smoke)
            burnt = True
        
        if random.random() <= BURNING_SPREAD_PROBABILITY or burnt: #burn other wood particle around
            update_near_particles(previous_x, previous_y)
            for dy in range(-1, 2):
                ny = previous_y + dy
                if 0 <= ny < GRID_HEIGHT:
                    for dx in range(-1, 2):
                        nx = previous_x + dx
                        if 0 <= nx < GRID_WIDTH:
                            checked_cell = grid[ny][nx]
                            if checked_cell != None and checked_cell.type == WOOD_ID:
                                grid[ny][nx] = None
                                burning_wood_particle = Particle(BURNING_WOOD_ID, nx, ny, random.choice(BURNING_WOOD_COLORS))
                                burning_wood_particle.lifespan = BURNING_WOOD_LIFESPAN
                                grid[ny][nx] = burning_wood_particle
                                particles_to_draw.add(burning_wood_particle)
                                burning_wood.add(burning_wood_particle)

def update_smoke_particles():
    active_smoke_particles_copy = active_smoke_particles.copy()
    for p in active_smoke_particles_copy:
        previous_x, previous_y = p.x, p.y
        moved = False
        top = False
        ny = previous_y - 1
        if ny >= 0:
            cell_above = grid[ny][previous_x]
            for dx in random.sample([-1, 0, 1], 3):
                nx = previous_x + dx
                if 0 <= nx < GRID_WIDTH:
                    cell_adjacent = grid[previous_y][nx]
                    target_cell = grid[ny][nx]
                    if target_cell == None:
                        if cell_above == None or cell_adjacent == None or (cell_above.type not in [CHROMATIC_ID, STONE_ID, WOOD_ID] and cell_adjacent.type not in [CHROMATIC_ID, STONE_ID, WOOD_ID]):
                            p.x = nx
                            p.y = ny
                            p.tx, p.ty = p.x, p.y
                            moved = True
                            break
                    elif target_cell.type == FIRE_ID:
                        if cell_above == None or cell_adjacent == None or (cell_above.type not in [CHROMATIC_ID, STONE_ID, WOOD_ID] and cell_adjacent.type not in [CHROMATIC_ID, STONE_ID, WOOD_ID]):
                            p.x = nx
                            p.y = ny
                            p.tx, p.ty = p.x, p.y
                            moved = True
                            grid[ny][nx] = None
                            fire_particles.discard(target_cell)
                            break

        if not moved:
            top = True
            if ny >= 0:
                for dx in range(-1, 0, 1):
                    nx = previous_x + dx
                    if grid[ny][nx] == None or grid[ny][nx].type not in [STONE_ID, CHROMATIC_ID, WOOD_ID]:
                        top = False
                        break
        
        
        if top:
            r = random.random()
            if p.type == STEAM_ID:
                if r <= CONDENSE_PROBABILITY:  # steam condenses into water
                    
                    grid[previous_y][previous_x] = None
                    water_particle = Particle(
                        WATER_ID, previous_x, previous_y, random.choice(WATER_COLORS))
                    grid[previous_y][previous_x] = water_particle
                    particles_to_draw.add(water_particle)
                    active_particles.add(water_particle)
                    active_smoke_particles.discard(p)
                    continue
                elif r <= STEAM_TO_WATER_RATIO * CONDENSE_PROBABILITY:  # the steam dissapear
                    grid[previous_y][previous_x] = None
                    particles_to_clear.add((previous_x, previous_y))
                    active_smoke_particles.discard(p)
                    update_near_particles(previous_x, previous_y)
                    continue
            elif p.type == SMOKE_ID:
                if r <= SMOKE_DISSIPATE_PROBABILITY:
                    grid[previous_y][previous_x] = None
                    active_smoke_particles.discard(p)
                    particles_to_clear.add((previous_x, previous_y))
                    update_near_particles(previous_x, previous_y)
                    continue
            
        if not moved:
            for dx in random.sample([-1, 1], 2):
                nx = previous_x + dx
                if 0 <= nx < GRID_WIDTH:
                    if grid[previous_y][nx] == None:
                        p.x = nx
                        p.tx = p.x
                        moved = True
                        break
        if moved:
            particles_to_clear.add((previous_x, previous_y))
            grid[previous_y][previous_x] = None
            particles_to_draw.add(p)
            grid[p.y][p.x] = p
            active_smoke_particles.add(p)
            update_near_particles(previous_x, previous_y)
        elif not top:
            active_smoke_particles.discard(p)


def _find_furthest_spread_x(original_x, current_y, dx_direction, grid, GRID_WIDTH, MAX_SPREAD_DIST):
    furthest_x = original_x
    for dist in range(1, MAX_SPREAD_DIST + 1):
        check_x = original_x + (dx_direction * dist)

        if check_x < 0 or check_x >= GRID_WIDTH:
            break

        if grid[current_y][check_x] is None:
            furthest_x = check_x
        else:
            break  # Blocked

    return furthest_x


def update_particles():
    global grid, active_particles, active_particles_copy, particles_to_clear, particles_to_draw
    active_particles_copy = active_particles.copy()
    while active_particles_copy:
        buckets = [[] for _ in range(GRID_HEIGHT)]
        for p in active_particles_copy:
            buckets[p.y].append(p)
        active_particles_copy = set()
        for y in range(GRID_HEIGHT - 1, -1, -1):
            for p in buckets[y]:
                previous_x, previous_y = p.x, p.y

                target_tx, target_ty, int_target_x, int_target_y, p.vx, p.vy = apply_gravity(
                    float(p.vx), float(p.vy), float(p.tx), float(p.ty), GRAVITY)

                moved = False
                if abs(int_target_x - previous_x) <= 1 and abs(int_target_y - previous_y) <= 1:
                    path = [(previous_x, previous_y),
                            (int_target_x, int_target_y)]
                else:
                    path = get_line(previous_x, previous_y,
                                    int_target_x, int_target_y)

                last_empty = (previous_x, previous_y)
                final_x, final_y = previous_x, previous_y
                collision = False

                for nx, ny in path[1:]:
                    if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                        collision = True
                        break
                    cell_content = grid[ny][nx]

                    if cell_content is None:
                        final_x, final_y = nx, ny
                        last_empty = (nx, ny)
                        continue
                    elif cell_content.type == FIRE_ID:
                        final_x, final_y = nx, ny
                        last_empty = (nx, ny)
                        fire_particles.discard(cell_content)
                        grid[ny][nx] = None
                        particles_to_clear.add((nx, ny))
                        continue

                    # swap between two particles
                    elif (cell_content.type == WATER_ID and p.type == SAND_ID) or cell_content.type == STEAM_ID or cell_content.type == SMOKE_ID:
                        final_x, final_y = nx, ny
                        break

                    else:
                        collision = True
                        break

                if (previous_x, previous_y) != (final_x, final_y):
                    grid[previous_y][previous_x] = None
                    p.x, p.y = final_x, final_y
                    grid[final_y][final_x] = None

                    if cell_content is not None and ((p.type == SAND_ID and cell_content.type == WATER_ID) or cell_content.type == STEAM_ID or cell_content.type == SMOKE_ID):
                        cell_content.x = last_empty[0]
                        cell_content.y = last_empty[1]
                        cell_content.tx = cell_content.x
                        cell_content.ty = cell_content.y
                        grid[cell_content.y][cell_content.x] = cell_content
                        if cell_content.type == WATER_ID and cell_content not in active_particles:
                            active_particles_copy.add(cell_content)
                            active_particles.add(cell_content)
                        elif cell_content.type == STEAM_ID or cell_content.type == SMOKE_ID:
                            active_smoke_particles.add(cell_content)
                        particles_to_draw.add(cell_content)
                        p.vx *= 0.6
                        p.vy *= 0.6

                    if collision:
                        p.tx, p.ty = p.x, p.y
                        p.vx *= 0.5
                        p.vy *= 0.5
                    else:
                        p.tx = target_tx
                        p.ty = target_ty
                    moved = True

                if not moved:
                    # diagonals
                    for dx in random.sample([-1, 1], 2):
                        nx = p.x + dx
                        ny = p.y + 1
                        if 0 <= nx < GRID_WIDTH and ny < GRID_HEIGHT:
                            cell_content = grid[ny][nx]
                            cell_adjacent = grid[p.y][nx]
                            cell_under = grid[ny][p.x]
                            if (cell_adjacent != None and cell_under != None):
                                if cell_adjacent.type in [STONE_ID, CHROMATIC_ID, WOOD_ID] and cell_under.type in [STONE_ID, CHROMATIC_ID, WOOD_ID]:
                                    continue
                            if cell_content is None:
                                grid[previous_y][previous_x] = None
                                p.x, p.y = nx, ny
                                p.tx, p.ty = p.x, p.y
                                moved = True
                                break
                            elif cell_content.type == FIRE_ID:
                                grid[previous_y][previous_x] = None
                                grid[ny][nx] = None
                                p.x, p.y = nx, ny
                                p.tx, p.ty = nx, ny
                                moved = True
                                fire_particles.discard(cell_content)
                                break

                            elif (p.type == SAND_ID and cell_content.type == WATER_ID) or cell_content.type == STEAM_ID or cell_content.type == SMOKE_ID:
                                grid[previous_y][previous_x] = None
                                grid[ny][nx] = None
                                grid[previous_y][previous_x] = cell_content
                                cell_content.x, cell_content.tx = previous_x, previous_x
                                cell_content.y, cell_content.ty = previous_y, previous_y
                                p.x, p.y = nx, ny

                                p.tx, p.ty = nx, ny
                                # p.vx *= 0.6
                                # p.vy *= 0.6

                                if cell_content not in active_particles and (cell_content.type != STEAM_ID and cell_content.type != SMOKE_ID):
                                    active_particles_copy.add(cell_content)
                                    active_particles.add(cell_content)
                                particles_to_draw.add(cell_content)
                                moved = True
                                break

                if not moved and (p.type == WATER_ID or p.type == ACID_ID):

                    direction1 = 1
                    direction2 = -1
                    if random.choice([True, False]):
                        direction1 = -1
                        direction2 = 1

                    final_new_x = previous_x

                    calculated_new_x = _find_furthest_spread_x(
                        previous_x, previous_y, direction1, grid, GRID_WIDTH, MAX_SPREAD_DIST)
                    if calculated_new_x != previous_x:
                        final_new_x = calculated_new_x
                        grid[previous_y][previous_x] = None
                        p.x = final_new_x
                        p.y = previous_y
                        p.tx = p.x
                        p.ty = p.y
                        moved = True
                    else:
                        calculated_new_x = _find_furthest_spread_x(
                            previous_x, previous_y, direction2, grid, GRID_WIDTH, MAX_SPREAD_DIST)
                        if calculated_new_x != previous_x:
                            final_new_x = calculated_new_x
                            grid[previous_y][previous_x] = None
                            p.x = final_new_x
                            p.y = previous_y
                            p.tx = p.x
                            p.ty = p.y
                            moved = True                     

                        
                # Update grid
                grid[p.y][p.x] = p

                if moved:
                    update_near_particles(previous_x, previous_y)
                    particles_to_clear.add((previous_x, previous_y))
                    particles_to_draw.add(p)
                else:
                    active_particles.discard(p)
                    p.vx = 0
                    p.vy = 1
