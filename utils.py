#import math

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

def lerp_color(color1, color2, t):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = r1 + (r2 - r1) * t
    g = g1 + (g2 - g1) * t
    b = b1 + (b2 - b1) * t
    return (int(r), int(g), int(b))

def generate_palette(colors_table, steps=60):
    palette = []
    colors = colors_table + [colors_table[0]]
    for i in range(len(colors) - 1):
        for step in range(steps):
            t = step / steps
            new_color = lerp_color(colors[i], colors[i+1], t)
            palette.append(new_color)
    return palette