import pygame
import pygame_gui
import random
import math


# Settings
CELL_SIZE = 5
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
TOOLBAR_WIDTH = 400
GRID_HEIGHT = WINDOW_HEIGHT // CELL_SIZE
GRID_WIDTH = (WINDOW_WIDTH - TOOLBAR_WIDTH) // CELL_SIZE

GRAVITY = 0.2
FRICTION = 0.02
spawn_radius = 1
random_velocity = False
random_spawn = 1

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Falling Sand Simulator")
clock = pygame.time.Clock()
manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))


brush_slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((820, 100), (200, 30)),
    start_value=spawn_radius,
    value_range=(0, 15),
    manager=manager
)
brush_label = pygame_gui.elements.UILabel(
    relative_rect=pygame.Rect((820, 140), (200, 30)),
    text=f"Brush Size: {spawn_radius}",
    manager=manager
)


# Colors
SAND_COLORS = [
    (210, 180, 140),
    (194, 178, 128),
    (244, 213, 141),
    (178, 153, 110),
]
EMPTY_COLOR = (0, 0, 0)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.tx = float(x)
        self.ty = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
    
    def __repr__(self):
        return f"P(x:{self.x}, y:{self.y})"

grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
active_particles = set()
active_particles_copy = set()
particles_to_clear = set()
particles_to_draw = set()

def draw_grid():
    for (x, y) in particles_to_clear:
        pygame.draw.rect(screen, EMPTY_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    for p in particles_to_draw:
        pygame.draw.rect(screen, p.color, (p.x * CELL_SIZE, p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    particles_to_clear.clear()
    particles_to_draw.clear()
    

def update_near_particles(x, y):
    for uy in range(y - 1, y):
        if uy < 0 or uy >= GRID_HEIGHT:
            continue
        for ux in range(x - 1, x + 2):
            if ux < 0 or ux >= GRID_WIDTH:
                continue
            p = grid[uy][ux]
            if p is not None:
                if p not in active_particles:
                    active_particles_copy.add(p)
                    active_particles.add(p)
                



def update_particles():
    global grid, active_particles, active_particles_copy, particles_to_clear, particles_to_draw
    #new_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for x, y in particles_to_clear:
        grid[y][x] = None
    #particles_to_clear.clear()
    active_particles_copy = active_particles.copy()

    while active_particles_copy:
        buckets = [[] for _ in range(GRID_HEIGHT)]
        for p in active_particles_copy:
            buckets[p.y].append(p)
        active_particles_copy = set()
        for y in range(GRID_HEIGHT - 1, -1, -1):
            for p in buckets[y]:
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
                    path = [(p.x, p.y), (int_target_x, int_target_y)]
                else:
                    path = get_line(p.x, p.y, int_target_x, int_target_y)
                last_valid = (p.x, p.y)
                collision = False

                for nx, ny in path[1:]:
                    if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                        collision = True
                        break
                    if grid[ny][nx] is None:
                        last_valid = (nx, ny)
                    else:
                        collision = True
                        break

                if last_valid != (p.x, p.y):
                    grid[p.y][p.x] = None
                    p.x, p.y = last_valid
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
                        if 0 <= nx < GRID_WIDTH and ny < GRID_HEIGHT and grid[ny][nx] is None:
                            grid[p.y][p.x] = None
                            p.x, p.y = nx, ny
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
    time_delta = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED and event.ui_element == brush_slider:
                spawn_radius = int(event.value)
                brush_label.set_text(f"Brush Size: {spawn_radius}")
        manager.process_events(event)
    manager.update(time_delta)
    # Mouse actions
    mouse_buttons = pygame.mouse.get_pressed()
    if any(mouse_buttons):
        mx, my = pygame.mouse.get_pos()
        gx, gy = mx // CELL_SIZE, my // CELL_SIZE
        
        if prev_pos != None:
            for x, y in get_line(prev_pos[0], prev_pos[1], gx, gy):
                if random_velocity:
                    vx = random.randint(-5, 5)
                    vy = random.randint(-5, 5)
                if mouse_buttons[0]: # Left click // Sand
                    for dx in range(-spawn_radius, spawn_radius+1):
                        for dy in range(-spawn_radius, spawn_radius+1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:                            
                                if random_spawn >= random.random(): 
                                    if grid[ny][nx] is None:
                                        p = Particle(nx, ny, random.choice(SAND_COLORS))
                                        if random_velocity:
                                            p.vx = vx
                                            p.vy = vy
                                        grid[ny][nx] = p
                                        active_particles.add(p)
                                        particles_to_draw.add(p)
                            
                elif mouse_buttons[2]: # Right click // Air
                    for dx in range(-spawn_radius, spawn_radius+1):
                        for dy in range(-spawn_radius, spawn_radius+1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                if random_spawn >= random.random():
                                    p = grid[ny][nx]
                                    if p is not None:   
                                        active_particles.discard(p) 
                                        grid[ny][nx] = None
                                        update_near_particles(nx, ny)
                                        particles_to_clear.add((nx, ny))
                                        particles_to_draw.discard(p)
        
        prev_pos = (gx, gy)  
    else:
        prev_pos = None          

    update_particles()
    #screen.fill(EMPTY_COLOR)
    pygame.draw.rect(screen, (30, 30, 30), (WINDOW_WIDTH - TOOLBAR_WIDTH, 0, TOOLBAR_WIDTH, WINDOW_HEIGHT))
    draw_grid()
    manager.draw_ui(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()