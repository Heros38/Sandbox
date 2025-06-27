import pygame
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
import random
import math
import os


# ------------------------Settings-------------------------------
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
random_spawn = 0.75
SAND_ID = 1
WATER_ID = 2
STONE_ID = 3
current_material = SAND_ID # Start with sand
simulation_is_on = True

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Falling Sand Simulator")
clock = pygame.time.Clock()


material_names = ["sand", "water"]

# -------------------------------- UI --------------------------------

def set_sand_material():
    global current_material
    current_material = SAND_ID
    material_label.setText("Current: Sand")

def set_water_material():
    global current_material
    current_material = WATER_ID
    material_label.setText("Current: Water")

def set_stone_material():
    global current_material
    current_material = STONE_ID
    material_label.setText("Current: Stone")

def  toggle_simulation():
    global simulation_is_on
    simulation_is_on = not simulation_is_on
    if simulation_is_on:
        pause_button.setText("ON")
        pause_button.inactiveColour = (40, 167, 69)
        pause_button.hoverColour = (33, 136, 56)   
        pause_button.pressedColour = (30, 126, 52)  
    else:
        pause_button.setText("OFF")
        pause_button.inactiveColour = (220, 53, 69) 
        pause_button.hoverColour = (200, 48, 60)    
        pause_button.pressedColour = (180, 40, 50)  

sand_button = Button(
    screen,  
    850,  # X-coordinate of top left corner 
    200,  # Y-coordinate of top left corner 
    95,  # Width 
    50,  # Height 

    text="Sand",  
    font=pygame.font.SysFont("Arial", 24, bold=True), 
    margin=10,  
    textColour=(51, 51, 51), 
    inactiveColour=(255, 204, 0),  
    hoverColour=(224, 184, 0),  
    pressedColour=(192, 168, 0),  
    radius=10,  
    onClick=set_sand_material  
)

water_button = Button(
    screen,  
    955,  # X-coordinate of top left corner 
    200,  # Y-coordinate of top left corner
    95,  # Width
    50,  # Height

    text="Water",  
    font=pygame.font.SysFont("Arial", 24, bold=True), 
    margin=10, 
    textColour=(255, 255, 255), 
    inactiveColour=(0, 123, 255),  
    hoverColour=(0, 86, 179),  
    pressedColour=(0, 64, 133),  
    radius=10,  
    onClick=set_water_material  
)

stone_button = Button(
    screen,  
    1060,  # X-coordinate of top left corner 
    200,  # Y-coordinate of top left corner 
    95,  # Width 
    50,  # Height 

    text="Stone",  
    font=pygame.font.SysFont("Arial", 24, bold=True), 
    margin=10,  
    textColour=(255, 255, 255), 
    inactiveColour=(100, 100, 100), 
    hoverColour=(120, 120, 120), 
    pressedColour=(80, 80, 80),
    radius=10,  
    onClick=set_stone_material  
)

material_label = TextBox(
    screen, 
    940, 260, # X, Y 
    120, 30, # Width, Height 
    font=pygame.font.SysFont("Arial", 18),
    textColour=(255, 255, 255),
    borderThickness=0, 
    colour=(35, 38, 45), 
    radius=5, 
    maxInput=None 
)
material_label.setText(f"Current: Sand") 
material_label.disable() 

pause_button = Button(
    screen,  
    900,  # X-coordinate of top left corner
    320,  # Y-coordinate of top left corner 
    95,  # Width
    50,  # Height

    text="ON",  
    font=pygame.font.SysFont("Arial", 24, bold=True),
    margin=10,  
    textColour=(255, 255, 255), 
    inactiveColour=(40, 167, 69), 
    hoverColour=(33, 136, 56),  
    pressedColour=(30, 126, 52),  
    radius=10, 
    onClick=toggle_simulation 
)

brush_slider = Slider(
    screen, 
    900, 100, # X, Y position
    200, 30, # Width, Height
    min=0, max=6, step=1, 
    initial=spawn_radius,
    
    colour=(40, 44, 52),  
    barColour=(30, 144, 255), 
    handleColour=(173, 216, 230), 
)

brush_size_label = TextBox(
    screen, 
    940, 140, # X, Y position
    110, 30, # Width, Height 
    font=pygame.font.SysFont("Arial", 18), 
    textColour=(255, 255, 255), 
    borderThickness=0, 
    colour=(35, 38, 45), 
    radius=5, 
    maxInput=None 
)
brush_size_label.setText(f"Brush Size: {spawn_radius}") 
brush_size_label.disable() 


# Colors
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


grid_surface = pygame.Surface(screen.get_size()).convert()
grid_surface.fill(EMPTY_COLOR) 

def draw_grid():
    for (x, y) in particles_to_clear:
        pygame.draw.rect(grid_surface, EMPTY_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for p in particles_to_draw:
        pygame.draw.rect(grid_surface, p.color, (p.x * CELL_SIZE, p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    screen.blit(grid_surface, (0, 0))


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

def update_particles():
    global grid, active_particles, active_particles_copy, particles_to_clear, particles_to_draw
    # new_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
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
                                if grid[p.y][nx].type == STONE_ID and grid[ny][p.x].type == STONE_ID:
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


def get_line(x0, y0, x1, y1):
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


# Main loop
prev_pos = None
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.USEREVENT:
            pass
    # Mouse actions
    mouse_buttons = pygame.mouse.get_pressed()
    if any(mouse_buttons):
        mx, my = pygame.mouse.get_pos()
        gx, gy = mx // CELL_SIZE, my // CELL_SIZE
        if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
            if prev_pos != None:
                for x, y in get_line(prev_pos[0], prev_pos[1], gx, gy):
                    if random_velocity:
                        vx = random.randint(-5, 5)
                        vy = random.randint(-5, 5)
                    if mouse_buttons[0]:  # Left click // Sand
                        if current_material == SAND_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                        if random_spawn >= random.random():
                                            if grid[ny][nx] is None:
                                                p = Particle(
                                                    SAND_ID, nx, ny, random.choice(SAND_COLORS))
                                                if random_velocity:
                                                    p.vx = vx
                                                    p.vy = vy
                                                grid[ny][nx] = p
                                                active_particles.add(p)
                                                particles_to_draw.add(p)
                        
                        elif current_material == WATER_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                        if random_spawn >= random.random():
                                            if grid[ny][nx] is None:
                                                p = Particle(
                                                    WATER_ID, nx, ny, random.choice(WATER_COLORS))
                                                if random_velocity:
                                                    p.vx = vx
                                                    p.vy = vy
                                                grid[ny][nx] = p
                                                active_particles.add(p)
                                                particles_to_draw.add(p)
                        
                        elif current_material == STONE_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                        if grid[ny][nx] is None:
                                            p = Particle(STONE_ID, nx, ny, random.choice(STONE_COLORS))
                                            grid[ny][nx] = p
                                            particles_to_draw.add(p)


                    elif mouse_buttons[2]:  # Right click // Air
                        for dx in range(-spawn_radius, spawn_radius+1):
                            for dy in range(-spawn_radius, spawn_radius+1):
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                    p = grid[ny][nx]
                                    if p is not None:
                                        active_particles.discard(p)
                                        grid[ny][nx] = None
                                        update_near_particles(nx, ny)
                                        particles_to_clear.add((nx, ny))
                                        particles_to_draw.discard(p)

        prev_pos = (gx, gy)
    else:
        pass
        prev_pos = None
    
    if simulation_is_on:
        update_particles()
    draw_grid()
    particles_to_clear.clear()
    particles_to_draw.clear()
    pygame.draw.rect(screen, (30, 30, 30), (WINDOW_WIDTH -
                     TOOLBAR_WIDTH, 0, TOOLBAR_WIDTH, WINDOW_HEIGHT))
    pygame_widgets.update(events)
    spawn_radius =  brush_slider.getValue()
    brush_size_label.setText(f"Brush Size: {spawn_radius}")
    pygame.display.flip()
    clock.tick(60)  

pygame.quit()
