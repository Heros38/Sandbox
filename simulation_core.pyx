# distutils: language = c

from cpython.set cimport PySet_Add, PySet_Contains, PySet_Discard
import random
from libc.math cimport sqrt, roundf
from utils import *

cdef class Particle:
    cdef public int type_id
    cdef public int x, y
    cdef public float tx, ty, vx, vy
    cdef public object color
    cdef public int lifespan

    def __init__(self, type_id: int, x: int, y: int, color):
        self.type_id = type_id
        self.x = x
        self.y = y
        self.tx = float(x)
        self.ty = float(y)
        self.vx = 0.0
        self.vy = 1.0
        self.color = color
        self.lifespan = 0

    def __repr__(self):
        return f"P(x:{self.x}, y:{self.y}, type:{self.type_id})"

cdef class SimulationSettings:
    # --- Constants (int) ---
    cdef public int CELL_SIZE
    cdef public int WINDOW_WIDTH
    cdef public int WINDOW_HEIGHT
    cdef public int TOOLBAR_WIDTH
    cdef public int GRID_HEIGHT # Derived, but set once
    cdef public int GRID_WIDTH  # Derived, but set once
    cdef public int FPS_LIMIT

    # --- Simulation Physics/Logic Constants (float or int) ---
    cdef public float GRAVITY
    cdef public float FRICTION
    cdef public float RANDOM_SPAWN_PROBABILITY
    cdef public float CONDENSE_PROBABILITY
    cdef public int STEAM_TO_WATER_RATIO
    cdef public float FIRE_DIES_PROBABILITY
    cdef public int FIRE_LIFESPAN
    cdef public int FIRE_LIFESPAN_VARIATION
    cdef public int MAX_SPREAD_DIST

    # --- Material IDs (int) ---
    cdef public int EMPTY_ID
    cdef public int SAND_ID
    cdef public int WATER_ID
    cdef public int STONE_ID
    cdef public int CHROMATIC_ID
    cdef public int STEAM_ID
    cdef public int FIRE_ID

    # colors
    cdef public list SAND_COLORS
    cdef public list WATER_COLORS
    cdef public list STONE_COLORS
    cdef public list FIRE_COLORS
    cdef public list STEAM_COLORS


    # --- Variables (that might change during runtime, though some might be constants for you) ---
    # Note: current_material, simulation_is_on, frame_count are likely managed in Python and
    # not needed directly in core Cython functions like update_near_particles.
    # If Cython *does* need to read/modify them, they'd be here.
    # For now, let's include some that might be relevant for other Cython functions:
    cdef public bint random_velocity # 'bint' is Cython's C boolean type
    cdef public int spawn_radius # Used if you make a spawn function in Cython
    # You could pass `current_material` to a Cython spawn function.
    # `frame_count` is often passed directly to functions that need it.

    # --- Constructor to populate the settings from Python ---
    def __init__(self,
                 cell_size: int, window_width: int, window_height: int, toolbar_width: int,
                 grid_height: int, grid_width: int, fps_limit: int,
                 gravity: float, friction: float, random_spawn_probability: float,
                 condense_probability: float, steam_to_water_ratio: int,
                 fire_dies_probability: float, fire_lifespan: int, fire_lifespan_variation: int,
                 max_spread_dist: int,
                 empty_id: int, sand_id: int, water_id: int, stone_id: int,
                 chromatic_id: int, steam_id: int, fire_id: int,
                 spawn_radius: int, random_velocity: bool): # Use bool for Python, Cython converts to bint

        self.CELL_SIZE = cell_size
        self.WINDOW_WIDTH = window_width
        self.WINDOW_HEIGHT = window_height
        self.TOOLBAR_WIDTH = toolbar_width
        self.GRID_HEIGHT = grid_height
        self.GRID_WIDTH = grid_width
        self.FPS_LIMIT = fps_limit

        self.GRAVITY = gravity
        self.FRICTION = friction
        self.RANDOM_SPAWN_PROBABILITY = random_spawn_probability
        self.CONDENSE_PROBABILITY = condense_probability
        self.STEAM_TO_WATER_RATIO = steam_to_water_ratio
        self.FIRE_DIES_PROBABILITY = fire_dies_probability
        self.FIRE_LIFESPAN = fire_lifespan
        self.FIRE_LIFESPAN_VARIATION = fire_lifespan_variation
        self.MAX_SPREAD_DIST = max_spread_dist

        self.EMPTY_ID = empty_id
        self.SAND_ID = sand_id
        self.WATER_ID = water_id
        self.STONE_ID = stone_id
        self.CHROMATIC_ID = chromatic_id
        self.STEAM_ID = steam_id
        self.FIRE_ID = fire_id

        self.SAND_COLORS = [
            (210, 180, 140),
            (194, 178, 128),
            (244, 213, 141),
            (178, 153, 110),
        ]
        self.WATER_COLORS = [
            (65, 105, 225),
            (0, 0, 128),
            (25, 25, 112)
        ]

        self.STONE_COLORS = [
            (190, 200, 205),
            (140, 150, 155),
            (90, 100, 105),
            (50, 55, 60)
        ]

        self.STEAM_COLORS = [
            (240, 240, 240),
            (225, 225, 225),
            (210, 210, 210),
            (195, 195, 195)
        ]

        self.FIRE_COLORS = [
            (255, 255, 102),  
            (255, 204, 0), 
            (255, 102, 0),  
            (204, 51, 0)  
        ]

        self.spawn_radius = spawn_radius
        self.random_velocity = random_velocity


cdef (float, float, int, int, float, float) apply_gravity_cython(
    float vx, float vy, float tx, float ty, SimulationSettings settings
):
    cdef float V2 = vx*vx + vy*vy # Use vx*vx for C-style power
    cdef float V, damping, target_tx, target_ty
    cdef int int_target_x, int_target_y

    if V2 > 0.0001: # Small epsilon to avoid division by zero or near-zero velocity issues
        V = sqrt(V2) # Use C's sqrt
        damping = 1.0 - settings.FRICTION * V # Use settings.FRICTION
        vx *= damping
        vy = settings.GRAVITY + damping * vy
    else:
        vy = settings.GRAVITY # If velocity is negligible, just apply gravity

    target_tx = tx + vx
    target_ty = ty + vy

    int_target_x = <int>roundf(target_tx) # Use C's roundf and cast to int
    int_target_y = <int>roundf(target_ty)

    return target_tx, target_ty, int_target_x, int_target_y, vx, vy



cdef int _find_furthest_spread_x(int original_x, int current_y, int dx_direction,
                                 list grid, SimulationSettings settings): # Pass settings here
    cdef int furthest_x = original_x
    cdef int dist, check_x
    for dist in range(1, settings.MAX_SPREAD_DIST + 1): # Use settings.MAX_SPREAD_DIST
        check_x = original_x + (dx_direction * dist)

        if check_x < 0 or check_x >= settings.GRID_WIDTH: # Use settings.GRID_WIDTH
            break

        if grid[current_y][check_x] is None:
            furthest_x = check_x
        else:
            break  # Blocked

    return furthest_x

cpdef void update_fire_particles(
    list grid,
    set fire_particles,
    set active_particles, # Needed for discarding water_particle
    set active_steam_particles,
    set particles_to_clear,
    set particles_to_draw,
    SimulationSettings settings # Pass settings object
):
    cdef Particle p, water_particle, steam1, steam2
    cdef int previous_x, previous_y, ny, nx, dx
    cdef float r # For random.random()
    cdef list dx_sample # For random.sample
    cdef Particle cell_content # <--- MOVE IT HERE (or even higher)

    # Iterate over a copy to allow modification of original set
    cdef set fire_particles_copy = fire_particles.copy()

    for p in fire_particles_copy:
        p.lifespan -= 1
        previous_x, previous_y = p.x, p.y

        r = random.random() # Python random call
        if r <= settings.FIRE_DIES_PROBABILITY or p.lifespan == 0:
            if 0 <= previous_y < settings.GRID_HEIGHT and 0 <= previous_x < settings.GRID_WIDTH:
                if grid[previous_y][previous_x] is p: # Only clear if it's still this particle
                    grid[previous_y][previous_x] = None
                PySet_Discard(fire_particles, p)
                PySet_Add(particles_to_clear, (previous_x, previous_y))
                PySet_Discard(particles_to_draw, p) # Discard if it was marked for draw
        else:
            ny = previous_y - 1
            if ny >= 0: # Check if row above exists
                dx_sample = random.sample([-1, 0, 1], 3) # Python random call
                for dx in dx_sample:
                    nx = previous_x + dx
                    if 0 <= nx < settings.GRID_WIDTH:
                        # Now cell_content is declared at the top of the function
                        cell_content = grid[ny][nx] # Assignment only, not declaration

                        if cell_content is None:  # fire just moves
                            # Update particle's position
                            p.x = nx
                            p.y = ny
                            p.tx, p.ty = float(p.x), float(p.y) # Update target floats
                            # Update grid
                            grid[ny][nx] = p
                            grid[previous_y][previous_x] = None
                            PySet_Add(particles_to_clear, (previous_x, previous_y))
                            PySet_Add(particles_to_draw, p)
                            break # Moved, so break from dx loop
                        # fire encounters water -> create steam
                        elif cell_content.type_id == settings.WATER_ID: # Use settings.WATER_ID
                            water_particle = cell_content # Store reference to water particle
                            # Clear both fire and water positions
                            grid[ny][nx] = None
                            grid[previous_y][previous_x] = None
                            # Remove from respective active sets
                            PySet_Discard(active_particles, water_particle)
                            PySet_Discard(fire_particles, p)
                            # Mark for clearing on screen
                            PySet_Add(particles_to_clear, (previous_x, previous_y))
                            PySet_Add(particles_to_clear, (nx, ny))
                            # Create new steam particles
                            steam1 = Particle(settings.STEAM_ID, nx, ny, random.choice(settings.STEAM_COLORS)) # Use settings.STEAM_ID & colors
                            steam2 = Particle(settings.STEAM_ID, previous_x, previous_y, random.choice(settings.STEAM_COLORS))
                            # Place steam particles in grid
                            grid[ny][nx] = steam1
                            grid[previous_y][previous_x] = steam2
                            # Add to active steam set
                            PySet_Add(active_steam_particles, steam1)
                            PySet_Add(active_steam_particles, steam2)
                            # Mark for drawing
                            PySet_Add(particles_to_draw, steam1)
                            PySet_Add(particles_to_draw, steam2)
                            # Discard original fire and water from draw set if they were there
                            PySet_Discard(particles_to_draw, p)
                            PySet_Discard(particles_to_draw, water_particle)
                            break # Handled interaction, break from dx loop

cpdef void update_steam_particles(
    list grid,
    set active_steam_particles,
    set active_particles, # Needed for adding water particle
    set fire_particles, # Needed for discarding fire
    set particles_to_clear,
    set particles_to_draw,
    SimulationSettings settings # Pass settings object
):
    cdef Particle p, cell_above, cell_adjacent, target_cell, water_particle
    cdef int previous_x, previous_y, ny, nx, dx
    cdef bint moved, top
    cdef float r # For random.random()
    cdef list dx_sample # For random.sample
    # Declare target_cell, cell_above, cell_adjacent at the top too:
    # (These were already mostly at the top, just ensure they are before any executable line)

    # Iterate over a copy to allow modification of original set
    cdef set active_steam_particles_copy = active_steam_particles.copy()

    for p in active_steam_particles_copy:
        previous_x, previous_y = p.x, p.y
        moved = False
        top = False # Assume not at top initially

        ny = previous_y - 1
        if ny >= 0: # Check if row above exists
            # Ensure these declarations are outside the inner loops if they are used across different dx iterations
            # and only assigned within. 
            # cell_above and cell_adjacent are often re-evaluated based on dx,
            # so it's fine to assign them inside the loop, just *declare* them at the top.
            cell_above = grid[ny][previous_x] # Get cell directly above (previous_x is fixed for this part)
            dx_sample = random.sample([-1, 0, 1], 3) # Python random call
            for dx in dx_sample:
                nx = previous_x + dx
                if 0 <= nx < settings.GRID_WIDTH: # Use settings.GRID_WIDTH
                    target_cell = grid[ny][nx] # Assignment
                    cell_adjacent = grid[previous_y][nx] # Assignment # Cell to the side at current y

                    if target_cell is None:
                        # Check for blocking by solid particles (STONE/CHROMATIC)
                        if (cell_above is None or cell_above.type_id not in [settings.CHROMATIC_ID, settings.STONE_ID]) and \
                           (cell_adjacent is None or cell_adjacent.type_id not in [settings.CHROMATIC_ID, settings.STONE_ID]):
                            p.x = nx
                            p.y = ny
                            p.tx, p.ty = float(p.x), float(p.y)
                            moved = True
                            break # Moved, break from dx loop
                    elif target_cell.type_id == settings.FIRE_ID: # Use settings.FIRE_ID
                        # Check for blocking by solid particles (STONE/CHROMATIC)
                        if (cell_above is None or cell_above.type_id not in [settings.CHROMATIC_ID, settings.STONE_ID]) and \
                           (cell_adjacent is None or cell_adjacent.type_id not in [settings.CHROMATIC_ID, settings.STONE_ID]):
                            p.x = nx
                            p.y = ny
                            p.tx, p.ty = float(p.x), float(p.y)
                            moved = True
                            # Remove fire particle
                            grid[ny][nx] = None # Clear fire's spot
                            PySet_Discard(fire_particles, target_cell) # Remove from fire set
                            PySet_Add(particles_to_clear, (nx,ny)) # Mark fire's old spot for clear
                            break # Moved, break from dx loop

        if not moved: # If steam couldn't move up/diagonally
            top = True # Assume it's at the top of its movement
            # Check if there's any non-solid space directly above or diagonally above
            # Original loop range(-1, 0, 1) is only for dx = -1. Should be range(-1, 2) for -1, 0, 1.
            # Re-evaluating original logic for 'top' condition:
            # It seems 'top' is true if all 3 cells above (-1,0,1 dx) are solid or off-grid,
            # or if it's already at y=0.
            if ny < 0: # If it's already at the very top of the grid (y=0)
                top = True
            else: # Check cells directly above or diagonally above
                for dx in [-1, 0, 1]: # Check all 3 positions above
                    nx = previous_x + dx
                    if 0 <= nx < settings.GRID_WIDTH:
                        cell_content = grid[ny][nx]
                        if cell_content is None or cell_content.type_id not in [settings.STONE_ID, settings.CHROMATIC_ID]:
                            top = False # Found a non-solid spot above, so not truly "at top"
                            break
                    # If nx is out of bounds, it's also considered a "solid" boundary for steam movement
                    # so 'top' remains true if all valid cells above are solid.

        if top:
            r = random.random() # Python random call
            if r <= settings.CONDENSE_PROBABILITY:  # steam condenses into water
                if 0 <= previous_y < settings.GRID_HEIGHT and 0 <= previous_x < settings.GRID_WIDTH:
                    # Only clear if it's still this particle
                    if grid[previous_y][previous_x] is p:
                        grid[previous_y][previous_x] = None
                    PySet_Discard(active_steam_particles, p)
                    water_particle = Particle(
                        settings.WATER_ID, previous_x, previous_y, random.choice(settings.WATER_COLORS))
                    grid[previous_y][previous_x] = water_particle
                    PySet_Add(particles_to_draw, water_particle)
                    PySet_Add(active_particles, water_particle) # Add to general active particles
                    continue # Particle handled, move to next steam particle

            elif r <= settings.STEAM_TO_WATER_RATIO * settings.CONDENSE_PROBABILITY:  # the steam disappears
                if 0 <= previous_y < settings.GRID_HEIGHT and 0 <= previous_x < settings.GRID_WIDTH:
                    if grid[previous_y][previous_x] is p:
                        grid[previous_y][previous_x] = None
                    PySet_Add(particles_to_clear, (previous_x, previous_y))
                    PySet_Discard(active_steam_particles, p)
                    # Call update_near_particles_cython for the empty spot left behind
                    update_near_particles_cython(previous_x, previous_y, grid, active_particles, set(), active_steam_particles, settings)
                    continue # Particle handled, move to next steam particle

        elif not moved: # If not at top AND not moved upwards, try horizontal spread
            dx_sample = random.sample([-1, 1], 2) # Python random call
            for dx in dx_sample:
                nx = previous_x + dx
                if 0 <= nx < settings.GRID_WIDTH:
                    if grid[previous_y][nx] is None:
                        p.x = nx
                        p.tx = float(p.x)
                        moved = True
                        break # Moved horizontally, break from dx loop

        if moved:
            # Only clear old position if it actually moved
            if 0 <= previous_y < settings.GRID_HEIGHT and 0 <= previous_x < settings.GRID_WIDTH:
                if grid[previous_y][previous_x] is p: # Only clear if it was this particle
                    grid[previous_y][previous_x] = None
            PySet_Add(particles_to_clear, (previous_x, previous_y))
            PySet_Add(particles_to_draw, p)
            grid[p.y][p.x] = p # Place particle in new position
            PySet_Add(active_steam_particles, p) # Ensure it's still in the active set
            # Call update_near_particles_cython for the empty spot left behind
            update_near_particles_cython(previous_x, previous_y, grid, active_particles, set(), active_steam_particles, settings)
        elif not top: # If it didn't move and isn't at the top (meaning it's settled for now)
            PySet_Discard(active_steam_particles, p)

cpdef void update_near_particles_cython(
    int x, int y,
    list grid,
    set active_particles,
    set active_particles_copy,
    set active_steam_particles,
    SimulationSettings settings # Pass the settings object here!
):
    cdef int ny, nx, dx
    cdef Particle p
    cdef list row_at_ny

    ny = y - 1
    # Use attributes from the settings object
    if 0 <= ny < settings.GRID_HEIGHT:
        row_at_ny = grid[ny]
        for dx in [-1, 0, 1]:
            nx = x + dx
            if 0 <= nx < settings.GRID_WIDTH:
                p = row_at_ny[nx]
                if p is not None:
                    # Use material IDs from settings
                    if p.type_id == settings.SAND_ID or p.type_id == settings.WATER_ID:
                        if not PySet_Contains(active_particles, p):
                            PySet_Add(active_particles, p)
                            PySet_Add(active_particles_copy, p)

    for dx in [-1, 1]:
        nx = x + dx
        if 0 <= nx < settings.GRID_WIDTH:
            p = grid[y][nx]
            if p is not None:
                if p.type_id == settings.WATER_ID:
                    if not PySet_Contains(active_particles, p):
                        PySet_Add(active_particles, p)
                        PySet_Add(active_particles_copy, p)
                elif p.type_id == settings.STEAM_ID:
                    PySet_Add(active_steam_particles, p)

    ny = y + 1
    if 0 <= ny < settings.GRID_HEIGHT:
        row_at_ny = grid[ny]
        for dx in [-1, 0, 1]:
            nx = x + dx
            if 0 <= nx < settings.GRID_WIDTH:
                p = row_at_ny[nx]
                if p is not None:
                    if p.type_id == settings.STEAM_ID:
                        PySet_Add(active_steam_particles, p)


cpdef void update_particles_cython(
    list grid, # grid: list of lists of Particle or None
    set active_particles, # main active particles, updated across frames
    set particles_to_clear, # positions to clear on screen
    set particles_to_draw, # particles to draw on screen
    set fire_particles, # specific set for fire particles
    set active_steam_particles, # specific set for active steam particles
    SimulationSettings settings, # your settings object
    object get_line_func    
):
    # Declare all local variables with cdef types for efficiency
    cdef int y, dx, ny, nx
    cdef Particle p, cell_content, cell_adjacent, cell_under
    cdef int previous_x, previous_y
    cdef float target_tx, target_ty, p_vx, p_vy
    cdef int int_target_x, int_target_y
    cdef bint moved # Flag for whether the particle moved in this wave
    cdef bint collision # Flag for path collision
    cdef list path # List of (int, int) tuples
    cdef tuple last_empty # (int, int)
    cdef int final_x, final_y
    cdef int current_x, current_y, direction1, direction2, calculated_new_x
    cdef int wave_count = 0

    # current_active_particles_to_process: Particles to consider moving in *this* wave.
    # next_active_particles_to_process: Particles that *did* move, *were affected*, or *need further processing* in the *next* wave.
    cdef list[list] buckets

    # Initialize the first wave with a copy of the main active_particles set.
    # This ensures "every particle should only move once per frame" in terms of its initial state.
    active_particles_copy = active_particles.copy()

    # Outer loop for "waves" of updates within a single frame.
    # Continues as long as particles are moving or being activated.
    while len(active_particles_copy) > 0:
        # Efficient bucket creation using Cython-typed lists
        # Each sublist holds particles at that specific Y-coordinate.
        buckets = [[] for _ in range(settings.GRID_HEIGHT)]
        for p in active_particles_copy:
            buckets[p.y].append(p)
        active_particles_copy = set()
        """
        # Populate buckets for the current wave from current_active_particles_to_process
        for p in current_active_particles_to_process:
            # CRITICAL: Validate particle before adding to bucket
            if p is None:
                PySet_Discard(active_particles, None) # Clean up if None somehow got in
                continue
            if not (0 <= p.x < settings.GRID_WIDTH and 0 <= p.y < settings.GRID_HEIGHT):
                # print(f"DEBUG: Particle {p.type_id} at ({p.x}, {p.y}) out of bounds during bucketing.")
                # Remove from all relevant sets if it's invalid
                PySet_Discard(active_particles, p)
                PySet_Discard(fire_particles, p)
                PySet_Discard(active_steam_particles, p)
                PySet_Add(particles_to_clear, (p.x,p.y)) # Mark its potentially invalid spot for clearing
                continue # Skip this particle
            buckets[p.y].append(p)
        """
        # Process particles from bottom to top (Y-axis) for correct fall behavior
        for y in range(settings.GRID_HEIGHT - 1, -1, -1):
            for p in buckets[y]:
                previous_x, previous_y = p.x, p.y

                target_tx, target_ty, int_target_x, int_target_y, p.vx, p.vy = apply_gravity_cython(
                    float(p.vx), float(p.vy), float(p.tx), float(p.ty), settings)

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
                    if not (0 <= nx < settings.GRID_WIDTH and 0 <= ny < settings.GRID_HEIGHT):
                        collision = True
                        break
                    cell_content = grid[ny][nx]

                    if cell_content is None:
                        final_x, final_y = nx, ny
                        last_empty = (nx, ny)
                        continue
                    elif cell_content.type_id == settings.FIRE_ID:
                        final_x, final_y = nx, ny
                        last_empty = (nx, ny)
                        PySet_Discard(fire_particles, cell_content)
                        grid[ny][nx] = None
                        PySet_Add(particles_to_clear, (nx, ny))
                        continue

                    # swap between two particles
                    elif (cell_content.type_id == settings.WATER_ID and p.type_id == settings.SAND_ID) or cell_content.type_id == settings.STEAM_ID:
                        final_x, final_y = nx, ny
                        break

                    else:
                        collision = True
                        break

                # --- Apply Movement / Handle Collision Response ---
                if (previous_x, previous_y) != (final_x, final_y):
                    grid[previous_y][previous_x] = None
                    p.x, p.y = final_x, final_y
                    grid[final_y][final_x] = None

                    if cell_content is not None and ((p.type_id == settings.SAND_ID and cell_content.type_id == settings.WATER_ID) or cell_content.type_id == settings.STEAM_ID):
                        cell_content.x = last_empty[0]
                        cell_content.y = last_empty[1]
                        cell_content.tx = cell_content.x
                        cell_content.ty = cell_content.y
                        grid[cell_content.y][cell_content.x] = cell_content
                        if cell_content.type_id == settings.WATER_ID and cell_content not in active_particles:
                            PySet_Add(active_particles_copy, cell_content)
                            PySet_Add(active_particles, cell_content)
                        elif cell_content.type_id == settings.STEAM_ID:
                            PySet_Add(active_steam_particles, cell_content)
                        PySet_Add(particles_to_draw, cell_content)
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
                        if 0 <= nx < settings.GRID_WIDTH and ny < settings.GRID_HEIGHT:
                            cell_content = grid[ny][nx]
                            cell_adjacent = grid[p.y][nx]
                            cell_under = grid[ny][p.x]
                            if (cell_adjacent != None and cell_under != None):
                                if cell_adjacent.type_id in [settings.STONE_ID, settings.CHROMATIC_ID] and cell_under.type_id in [settings.STONE_ID, settings.CHROMATIC_ID]:
                                    continue
                            if cell_content is None:
                                grid[previous_y][previous_x] = None
                                p.x, p.y = nx, ny
                                p.tx, p.ty = p.x, p.y
                                moved = True
                                break
                            elif cell_content.type_id == settings.FIRE_ID:
                                grid[previous_y][previous_x] = None
                                grid[ny][nx] = None
                                p.x, p.y = nx, ny
                                p.tx, p.ty = nx, ny
                                moved = True
                                PySet_Discard(fire_particles, cell_content)

                            elif (p.type_id == settings.SAND_ID and cell_content.type_id == settings.WATER_ID) or cell_content.type_id == settings.STEAM_ID:
                                grid[previous_y][previous_x] = None
                                grid[ny][nx] = None
                                grid[previous_y][previous_x] = cell_content
                                cell_content.x, cell_content.tx = previous_x, previous_x
                                cell_content.y, cell_content.ty = previous_y, previous_y
                                p.x, p.y = nx, ny

                                p.tx, p.ty = nx, ny
                                # p.vx *= 0.6
                                # p.vy *= 0.6

                                if cell_content not in active_particles and cell_content.type_id != settings.STEAM_ID:
                                    PySet_Add(active_particles_copy, cell_content)
                                    PySet_Add(active_particles, cell_content)
                                PySet_Add(particles_to_draw, cell_content)
                                moved = True
                                break

                if not moved and p.type_id == settings.WATER_ID:
                    current_x = p.x
                    current_y = p.y

                    direction1 = 1
                    direction2 = -1
                    if random.choice([True, False]):
                        direction1 = -1
                        direction2 = 1

                    final_new_x = current_x
                    moved_in_this_step = False

                    calculated_new_x = _find_furthest_spread_x(
                        current_x, current_y, direction1, grid, settings)
                    if calculated_new_x != current_x:
                        final_new_x = calculated_new_x
                        moved_in_this_step = True
                    else:
                        calculated_new_x = _find_furthest_spread_x(
                            current_x, current_y, direction2, grid, settings)
                        if calculated_new_x != current_x:
                            final_new_x = calculated_new_x
                            moved_in_this_step = True

                    if moved_in_this_step:
                        grid[previous_y][previous_x] = None

                        p.x = final_new_x
                        p.y = current_y
                        p.tx = p.x
                        p.ty = p.y
                        moved = True


                # --- Final Particle Update / Activation / Deactivation ---
                if moved:
                    update_near_particles_cython(previous_x, previous_y, grid, active_particles, active_particles_copy, active_steam_particles, settings)
                    grid[p.y][p.x] = p
                    PySet_Add(particles_to_draw, p)
                    PySet_Add(particles_to_clear, (previous_x, previous_y))
                    # Ensure it's in the main active set and added to the next wave's set
                    if not PySet_Contains(active_particles, p):
                        PySet_Add(active_particles, p)
                        PySet_Add(active_particles_copy, p) # Keep active for next wave
                else: # Particle did NOT move in any way in this processing step
                    # If it's a "settling" particle type (Sand/Water) and fully blocked, deactivate it
                    p.vy = 1
                    p.vx = 0
                    PySet_Discard(active_particles, p)