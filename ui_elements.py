import pygame
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from config import *

brush_slider = None
brush_size_label = None
sand_button = None
water_button = None
stone_button = None
material_display_label = None
pause_button = None

def update_brush_label_text(text):
    if brush_size_label: # Ensure the widget is initialized before trying to use it
        brush_size_label.setText(text)
        brush_size_label.update() # Force TextBox to re-render its internal surface

def update_material_label_text(text):
    if material_display_label: # Ensure the widget is initialized
        material_display_label.setText(text)
        material_display_label.update()

def init_ui(target_screen):
    global brush_slider, brush_size_label, sand_button, water_button, stone_button, material_label, pause_button
    sand_button = Button(
        target_screen,  
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
    )

    water_button = Button(
        target_screen,  
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
    )

    stone_button = Button(
        target_screen,  
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
    )

    material_label = TextBox(
        target_screen, 
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
        target_screen,  
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
    )

    brush_slider = Slider(
        target_screen, 
        900, 100, # X, Y position
        200, 30, # Width, Height
        min=0, max=6, step=1, 
        initial=spawn_radius,
        
        colour=(40, 44, 52),  
        barColour=(30, 144, 255), 
        handleColour=(173, 216, 230), 
    )

    brush_size_label = TextBox(
        target_screen, 
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