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

def update_brush_size_from_slider_callback(value):
    config.spawn_radius = int(value) 
    ui_elements.update_brush_label_text(f"Brush Size: {config.spawn_radius}")


ui_elements.sand_button.onClick = set_sand_material_callback
ui_elements.water_button.onClick = set_water_material_callback
ui_elements.stone_button.onClick = set_stone_material_callback
ui_elements.chromatic_button.onClick = set_chromatic_material_callback
ui_elements.pause_button.onClick = toggle_simulation_callback


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
                                                p = particle_system.Particle(
                                                    config.SAND_ID, nx, ny, random.choice(config.SAND_COLORS))
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
                                                p = particle_system.Particle(   
                                                    config.WATER_ID, nx, ny, random.choice(config.WATER_COLORS))
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

        prev_pos = (gx, gy)
    else:
        prev_pos = None
    
    if config.simulation_is_on:
        particle_system.update_particles()
    particle_system.draw_grid(screen)
    particle_system.particles_to_clear.clear()
    particle_system.particles_to_draw.clear()
    pygame.draw.rect(screen, (30, 30, 30), (config.WINDOW_WIDTH -
                    config.TOOLBAR_WIDTH, 0, config.TOOLBAR_WIDTH, config.WINDOW_HEIGHT))
    ui_elements.pygame_widgets.update(events)
    if config.frame_count % 2 == 0:
        particle_system.cycle_colors(CHROMATIC_PALETTE, palette_size) 
    if ui_elements.brush_slider != None:
        spawn_radius =  ui_elements.brush_slider.getValue()
        ui_elements.brush_size_label.setText(f"Brush Size: {spawn_radius}")
    pygame.display.flip()
    clock.tick(60)  
    config.frame_count += 1
pygame.quit()