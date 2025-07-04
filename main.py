import pygame
import sys
import random
import os
import config
import ui_elements
import particle_system
import utils

pygame.init()
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
particle_system.initialize_grid()
pygame.display.set_caption("Sandbox")
clock = pygame.time.Clock()
ui_elements.init_ui(screen)

CHROMATIC_PALETTE = utils.generate_palette(config.CHROMATIC_COLORS)
palette_size = len(CHROMATIC_PALETTE)
# warm-up for jit functions
particle_system.apply_gravity(1.0, 1.0, 10.0, 10.0, 1.0)
utils.get_line(0, 0, 0, 0)
utils.get_shuffled_tab([1, 2])

if config.ANNIVERSAIRE:
    tab = utils.get_text_pixels_pygame("HAPPY", config.GRID_WIDTH, config.GRID_HEIGHT, 0.6)
    for (x, y) in tab:
        p = particle_system.Particle(config.CHROMATIC_ID, x, y, random.choice(config.CHROMATIC_COLORS))
        particle_system.grid[y][x] = p
        particle_system.chromatic_particles.add(p)
    tab = utils.get_text_pixels_pygame("BIRTHDAY", config.GRID_WIDTH, config.GRID_HEIGHT, 1.4)
    for (x, y) in tab:
        p = particle_system.Particle(config.CHROMATIC_ID, x, y, random.choice(config.CHROMATIC_COLORS))
        particle_system.grid[y][x] = p
        particle_system.chromatic_particles.add(p)

fps_font = pygame.font.SysFont("Arial", 24, bold=True)
def fps_counter():
    fps = str(int(clock.get_fps()))
    fps_t = fps_font.render(f'fps: {fps}', 1, pygame.Color("RED"))
    screen.blit(fps_t, (config.SCREEN_WIDTH + 10, 565))


def set_sand_material_callback():
    config.current_material = config.SAND_ID
    ui_elements.update_material_label_text(f"Current: Sand")


def set_water_material_callback():
    config.current_material = config.WATER_ID
    ui_elements.update_material_label_text(f"Current: Water")


def set_stone_material_callback():
    config.current_material = config.STONE_ID
    ui_elements.update_material_label_text(f"Current: Stone")


def set_chromatic_material_callback():
    config.current_material = config.CHROMATIC_ID
    ui_elements.update_material_label_text(f"Current: Chromatic")


def set_steam_material_callback():
    config.current_material = config.STEAM_ID
    ui_elements.update_material_label_text(f"Current: Steam")


def set_fire_material_callback():
    config.current_material = config.FIRE_ID
    ui_elements.update_material_label_text(f"Current: Fire")

def set_wood_material_callback():
    config.current_material = config.WOOD_ID
    ui_elements.update_material_label_text(f"Current: Wood")


def toggle_simulation_callback():
    config.simulation_is_on = not config.simulation_is_on
    if config.simulation_is_on:
        ui_elements.pause_button.setText("ON")
        ui_elements.pause_button.inactiveColour = (40, 167, 69)
        ui_elements.pause_button.hoverColour = (33, 136, 56)
        ui_elements.pause_button.pressedColour = (30, 126, 52)
    else:
        ui_elements.pause_button.setText("OFF")
        ui_elements.pause_button.inactiveColour = (220, 53, 69)
        ui_elements.pause_button.hoverColour = (200, 48, 60)
        ui_elements.pause_button.pressedColour = (180, 40, 50)


def clear_screen():
    particle_system.active_particles.clear()
    particle_system.particles_to_clear.clear()
    particle_system.particles_to_draw.clear()
    particle_system.chromatic_particles.clear()
    particle_system.active_steam_particles.clear()
    particle_system.fire_particles.clear()
    particle_system.burning_wood.clear()
    particle_system.initialize_grid()


def update_brush_size_from_slider_callback(value):
    config.spawn_radius = int(value)
    ui_elements.update_brush_label_text(f"Brush Size: {config.spawn_radius}")


ui_elements.sand_button.onClick = set_sand_material_callback
ui_elements.water_button.onClick = set_water_material_callback
ui_elements.stone_button.onClick = set_stone_material_callback
ui_elements.chromatic_button.onClick = set_chromatic_material_callback
ui_elements.steam_button.onClick = set_steam_material_callback
ui_elements.fire_button.onClick = set_fire_material_callback
ui_elements.wood_button.onClick = set_wood_material_callback
ui_elements.pause_button.onClick = toggle_simulation_callback
ui_elements.clear_button.onClick = clear_screen

prev_pos = None
running = True
while running:
    if config.simulation_is_on:
        #print("--- Start of Frame ---")
        #print(f"fire_particles count before update_particles: {len(particle_system.fire_particles)}")
        particle_system.update_particles()
        #print(f"fire_particles count after update_particles: {len(particle_system.fire_particles)}")
        #print(f"fire_particles count before update_steam_particles: {len(particle_system.fire_particles)}")
        particle_system.update_steam_particles()
        #print(f"fire_particles count after update_steam_particles: {len(particle_system.fire_particles)}")
        #print(f"fire_particles count before update_fire_particles: {len(particle_system.fire_particles)}")
        particle_system.update_fire_particles()
        #print(f"fire_particles count AFTER update_fire_particles: {len(particle_system.fire_particles)}")
        #print(particle_system.fire_particles)
        particle_system.update_burning_wood()
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
        gx, gy = mx // config.CELL_SIZE, my // config.CELL_SIZE
        if 0 <= gx < config.GRID_WIDTH and 0 <= gy < config.GRID_HEIGHT:
            if prev_pos != None:
                for x, y in utils.get_line(prev_pos[0], prev_pos[1], gx, gy):
                    if config.random_velocity:
                        vx = random.randint(-5, 5)
                        vy = random.randint(-5, 5)
                    if mouse_buttons[0]:  # Left click // Sand
                        if config.current_material == config.SAND_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if config.RANDOM_SPAWN_PROBABILITY >= random.random():
                                            if particle_system.grid[ny][nx] is None:
                                                p = particle_system.Particle(config.SAND_ID, nx, ny, random.choice(config.SAND_COLORS))
                                                if config.random_velocity:
                                                    p.vx = vx
                                                    p.vy = vy
                                                particle_system.grid[ny][nx] = p
                                                particle_system.active_particles.add(p)
                                                particle_system.particles_to_draw.add(p)

                        elif config.current_material == config.WATER_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if config.RANDOM_SPAWN_PROBABILITY >= random.random():
                                            if particle_system.grid[ny][nx] is None:
                                                p = particle_system.Particle(config.WATER_ID, nx, ny, random.choice(config.WATER_COLORS))
                                                if config.random_velocity:
                                                    p.vx = vx
                                                    p.vy = vy
                                                particle_system.grid[ny][nx] = p
                                                particle_system.active_particles.add(p)
                                                particle_system.particles_to_draw.add(p)

                        elif config.current_material == config.STONE_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if particle_system.grid[ny][nx] is None:
                                            p = particle_system.Particle(config.STONE_ID, nx, ny, random.choice(config.STONE_COLORS))
                                            particle_system.grid[ny][nx] = p
                                            particle_system.particles_to_draw.add(p)

                        elif config.current_material == config.CHROMATIC_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if particle_system.grid[ny][nx] is None:
                                            p = particle_system.Particle(config.CHROMATIC_ID, nx, ny, random.choice(config.CHROMATIC_COLORS))
                                            particle_system.grid[ny][nx] = p
                                            particle_system.chromatic_particles.add(p)
                        
                        elif config.current_material == config.WOOD_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if particle_system.grid[ny][nx] is None:
                                            p = particle_system.Particle(config.WOOD_ID, nx, ny, random.choice(config.WOOD_COLORS))
                                            particle_system.grid[ny][nx] = p
                                            particle_system.particles_to_draw.add(p)

                        elif config.current_material == config.STEAM_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if config.RANDOM_SPAWN_PROBABILITY >= random.random():
                                            if particle_system.grid[ny][nx] is None:
                                                p = particle_system.Particle(config.STEAM_ID, nx, ny, random.choice(config.STEAM_COLORS))
                                                particle_system.grid[ny][nx] = p
                                                particle_system.active_steam_particles.add(p)
                                                particle_system.particles_to_draw.add(p)

                        elif config.current_material == config.FIRE_ID:
                            for dx in range(-spawn_radius, spawn_radius+1):
                                for dy in range(-spawn_radius, spawn_radius+1):
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                        if particle_system.grid[ny][nx] is None:
                                            p = particle_system.Particle(config.FIRE_ID, nx, ny, random.choice(config.FIRE_COLORS))
                                            p.lifespan = config.FIRE_LIFESPAN + random.randint(-config.FIRE_LIFESPAN_VARIATION, config.FIRE_LIFESPAN_VARIATION)
                                            particle_system.grid[ny][nx] = p
                                            particle_system.fire_particles.add(p)
                                            particle_system.particles_to_draw.add(p)

                    elif mouse_buttons[2]:  # Right click // Air
                        for dx in range(-spawn_radius, spawn_radius+1):
                            for dy in range(-spawn_radius, spawn_radius+1):
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < config.GRID_WIDTH and 0 <= ny < config.GRID_HEIGHT:
                                    p = particle_system.grid[ny][nx]
                                    if p is not None:
                                        particle_system.active_particles.discard(p)
                                        particle_system.grid[ny][nx] = None
                                        particle_system.update_near_particles(nx, ny)
                                        particle_system.particles_to_clear.add((nx, ny))
                                        particle_system.particles_to_draw.discard(p)
                                        particle_system.chromatic_particles.discard(p)
                                        particle_system.active_steam_particles.discard(p)
                                        particle_system.fire_particles.discard(p)
        prev_pos = (gx, gy)
    else:
        prev_pos = None 
    
    particle_system.draw_grid(screen)
    pygame.draw.rect(screen, (30, 30, 30), (config.WINDOW_WIDTH - config.TOOLBAR_WIDTH, 0, config.TOOLBAR_WIDTH, config.WINDOW_HEIGHT))
    ui_elements.pygame_widgets.update(events)
    particle_system.cycle_colors(CHROMATIC_PALETTE, palette_size)
    if ui_elements.brush_slider != None:
        spawn_radius = ui_elements.brush_slider.getValue()
        ui_elements.brush_size_label.setText(f"Brush Size: {spawn_radius}")
    fps_counter()
    pygame.display.flip()
    clock.tick(60)
    config.frame_count += 1
pygame.quit()
