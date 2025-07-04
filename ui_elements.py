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
chromatic_button = None
steam_button = None
fire_button = None
wood_button = None
material_display_label = None
pause_button = None
clear_button = None


def update_brush_label_text(text):
    if brush_size_label:
        brush_size_label.setText(text)


def update_material_label_text(text):
    if material_display_label:
        material_display_label.setText(text)


def init_ui(target_screen):
    global brush_slider, brush_size_label, sand_button, water_button, stone_button, chromatic_button, steam_button, fire_button, wood_button, material_display_label, pause_button, clear_button
    sand_button = Button(
        target_screen,
        SCREEN_WIDTH + 50,  # X-coordinate of top left corner
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
        SCREEN_WIDTH + 155,  # X-coordinate of top left corner
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
        SCREEN_WIDTH + 260,  # X-coordinate of top left corner
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

    wood_button = Button(
        target_screen,
        SCREEN_WIDTH + 260,  # X-coordinate of top left corner
        260,  # Y-coordinate of top left corner
        95,  # Width
        50,  # Height

        text="Wood",
        font=pygame.font.SysFont("Arial", 24, bold=True),
        margin=10,
        textColour=(255, 255, 255),
        inactiveColour=(150, 95, 45),
        hoverColour=(120, 80, 50),
        pressedColour=(70, 40, 15),
        radius=10,
    )

    chromatic_button = Button(
        target_screen,
        SCREEN_WIDTH + 155,  # X-coordinate
        320,  # Y-coordinate
        95,   # Width
        50,   # Height
        text="Chromatic",
        font=pygame.font.SysFont("Arial", 24, bold=True),
        margin=10,
        textColour=(255, 255, 255),
        inactiveColour=(148, 0, 211),
        hoverColour=(120, 0, 180),
        pressedColour=(100, 0, 150),
        radius=10,
    )

    steam_button = Button(
        target_screen,
        SCREEN_WIDTH + 50,  # X-coordinate
        260,  # Y-coordinate
        95,   # Width
        50,   # Height
        text="Steam",
        font=pygame.font.SysFont("Arial", 24, bold=True),
        margin=10,
        textColour=(255, 255, 255),
        inactiveColour=(210, 215, 220),
        hoverColour=(180, 185, 190),
        pressedColour=(150, 155, 160),
        radius=10,
    )

    fire_button = Button(
        target_screen,
        SCREEN_WIDTH + 155,  # X-coordinate
        260,  # Y-coordinate
        95,   # Width
        50,   # Height
        text="Fire",
        font=pygame.font.SysFont("Arial", 24, bold=True),
        margin=10,
        textColour=(255, 255, 255),
        inactiveColour=(255, 153, 0),
        hoverColour=(204, 102, 0),
        pressedColour=(153, 51, 0),
        radius=10,
    )

    material_display_label = TextBox(
        target_screen,
        SCREEN_WIDTH + 100, 380,  # X, Y
        200, 30,  # Width, Height
        font=pygame.font.SysFont("Arial", 18),
        textColour=(255, 255, 255),
        borderThickness=0,
        colour=(35, 38, 45),
        radius=5,
        maxInput=None
    )
    material_display_label.setText(f"Current: Sand")
    material_display_label.disable()

    pause_button = Button(
        target_screen,
        SCREEN_WIDTH + 100,  # X-coordinate of top left corner
        420,  # Y-coordinate of top left corner
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

    clear_button = Button(
        target_screen,
        SCREEN_WIDTH + 205,  # X-coordinate of top left corner
        420,  # Y-coordinate of top left corner
        95,  # Width
        50,  # Height

        text="Clear",
        font=pygame.font.SysFont("Arial", 24, bold=True),
        margin=10,
        textColour=(255, 255, 255),
        inactiveColour=(220, 53, 69),
        hoverColour=(200, 48, 60),
        pressedColour=(180, 40, 50),
        radius=10,
    )

    brush_slider = Slider(
        target_screen,
        SCREEN_WIDTH + 100, 100,  # X, Y position
        200, 30,  # Width, Height
        min=0, max=6, step=1,
        initial=spawn_radius,

        colour=(40, 44, 52),
        barColour=(30, 144, 255),
        handleColour=(173, 216, 230),
    )

    brush_size_label = TextBox(
        target_screen,
        SCREEN_WIDTH + 140, 140,  # X, Y position
        110, 30,  # Width, Height
        font=pygame.font.SysFont("Arial", 18),
        textColour=(255, 255, 255),
        borderThickness=0,
        colour=(35, 38, 45),
        radius=5,
        maxInput=None
    )
    brush_size_label.setText(f"Brush Size: {spawn_radius}")
    brush_size_label.disable()
