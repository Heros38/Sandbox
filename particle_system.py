import pygame
import random
import math
import time
from config import *
from utils import *

class Particle:
    def __init__(self, type, x, y, color):
        self.type = type
        self.x = x
        self.y = y
        self.tx = float(x)
        self.ty = float(y)
        self.vx = 0
        self.vy = 1
        self.color = color

    def __repr__(self):
        return f"P(x:{self.x}, y:{self.y})"


grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
active_particles = set()
active_particles_copy = set()
particles_to_clear = set()
particles_to_draw = set()
chromatic_particles = set()


#grid_surface = pygame.Surface((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)).convert()
#grid_surface.fill(EMPTY_COLOR)


def initialize_grid():
    global grid, grid_surface
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    grid_surface = pygame.Surface((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)).convert()
    grid_surface.fill(EMPTY_COLOR)

def draw_grid(target_screen):
    for (x, y) in particles_to_clear:
        pygame.draw.rect(target_screen, EMPTY_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for p in particles_to_draw:
        pygame.draw.rect(target_screen, p.color, (p.x * CELL_SIZE, p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    target_screen.blit(target_screen, (0, 0))


def update_near_particles(x, y):
    uy = y-1
    if not (uy < 0 or uy >= GRID_HEIGHT):
        for ux in range(x - 1, x + 2):
            if ux < 0 or ux >= GRID_WIDTH:
                continue
            p = grid[uy][ux]
            if p is not None:
                if p not in active_particles and p.type in [SAND_ID, WATER_ID]:
                    active_particles_copy.add(p)
                    active_particles.add(p)
    for ux in [-1, 1]:
        if x + ux < GRID_WIDTH and x + ux > 0:
            p = grid[y][x + ux]
            if p is not None and p.type == WATER_ID:
                if p not in active_particles:
                    active_particles_copy.add(p)
                    active_particles.add(p)

def cycle_colors(CHROMATIC_PALETTE, palette_size):
    for p in chromatic_particles:
        speed_factor = 50
        spatial_factor = 2
        index = int(time.time() * speed_factor + p.x * spatial_factor + p.y * spatial_factor) % palette_size
        new_color = CHROMATIC_PALETTE[index]
        if p.color != new_color:
            p.color = new_color
            particles_to_draw.add(p)


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
                #p.color = (200, 50, 50)
                previous_x, previous_y = p.x, p.y

                V2 = p.vx**2 + p.vy**2
                if V2 > 0.0001:
                    V = math.sqrt(V2)
                    damping = 1 - FRICTION * V
                    p.vx *= damping
                    p.vy = GRAVITY + damping * p.vy
                else:
                    p.vy = GRAVITY

                moved = False
                target_tx = p.tx + p.vx
                target_ty = p.ty + p.vy

                int_target_x = round(target_tx)
                int_target_y = round(target_ty)

                if abs(int_target_x - p.x) <= 1 and abs(int_target_y - p.y) <= 1:
                    path = [(previous_x, previous_y), (int_target_x, int_target_y)]
                else:
                    path = get_line(previous_x, previous_y, int_target_x, int_target_y)
                
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

                    elif cell_content.type == WATER_ID and p.type == SAND_ID: # Sand encounters Water
                        final_x, final_y = nx, ny 
                        break

                    else: 
                        collision = True
                        break

                if (previous_x, previous_y) != (final_x, final_y):
                    grid[previous_y][previous_x] = None
                    p.x, p.y = final_x, final_y
                    grid[p.y][p.x] = None
                    
                    if cell_content is not None and p.type != WATER_ID and cell_content.type == WATER_ID:
                        water_particle = cell_content
                        water_particle.x = last_empty[0]
                        water_particle.y = last_empty[1]
                        water_particle.tx = water_particle.x
                        water_particle.ty = water_particle.y
                        grid[water_particle.y][water_particle.x] = water_particle
                        if water_particle not in active_particles:
                            active_particles_copy.add(water_particle)
                            active_particles.add(water_particle)
                        particles_to_draw.add(water_particle) 
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
                            if grid[p.y][nx] != None and grid[ny][p.x] != None:
                                if (grid[p.y][nx].type == STONE_ID and grid[ny][p.x].type == STONE_ID) or (grid[p.y][nx].type == CHROMATIC_ID and grid[ny][p.x].type == CHROMATIC_ID):
                                    continue
                            if grid[ny][nx] is None:
                                grid[previous_y][previous_x] = None
                                p.x, p.y = nx, ny
                                p.tx, p.ty = p.x, p.y
                                moved = True
                                break

                            elif p.type == SAND_ID and grid[ny][nx].type == WATER_ID:
                                water_particle = grid[ny][nx] 
                                grid[p.y][p.x] = None
                                grid[ny][nx] = None
                                grid[previous_y][previous_x] = water_particle
                                water_particle.x, water_particle.tx  = previous_x, previous_x
                                water_particle.y, water_particle.ty = previous_y, previous_y
                                p.x, p.y = nx, ny

                                p.tx, p.ty = float(p.x), float(p.y)
                                #p.vx *= 0.6 
                                #p.vy *= 0.6  
                                
                                if water_particle not in active_particles:
                                    active_particles_copy.add(water_particle)
                                    active_particles.add(water_particle)
                                particles_to_draw.add(water_particle)
                                moved = True
                                break

                
                if not moved and p.type == WATER_ID: #move randomly to the sides
                    for dx in random.sample([-4, -1, 1, 4], 4):
                        if dx < 0:
                            path = [p.x - i for i in range(1, abs(dx)+ 1)]
                        else:
                            path = [p.x + i for i in range(1, dx + 1)]
                        last_valid = (p.x, p.y)

                        for nx in path:
                            if not 0 <= nx < GRID_WIDTH:
                                break
                            if grid[p.y][nx] is None:
                                last_valid = (nx, p.y)
                            else:
                                break

                        if last_valid != (previous_x, previous_y):
                            grid[previous_y][previous_x] = None
                            p.x, p.y = last_valid
                            p.tx, p.ty = p.x, p.y
                            moved = True
                            break


                # Update grid
                grid[p.y][p.x] = p

                if moved:
                    update_near_particles(previous_x, previous_y)
                    particles_to_clear.add((previous_x, previous_y))
                    particles_to_draw.add(p)
                else:
                    #p.color = (50, 200, 50)
                    #particles_to_draw.add(p)
                    active_particles.discard(p)
                    p.vx = 0
                    p.vy = 1