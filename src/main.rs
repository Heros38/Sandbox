use ::rand::Rng;
use ::rand::seq::SliceRandom;
use ::rand::thread_rng;
use macroquad::prelude::*;
use crate::miniquad::conf::Platform;
use std::thread;
use std::time::{Instant, Duration};


const SAND_ID: usize = 1;
const SCREEN_WIDTH: usize = 1600;
const SCREEN_HEIGHT: usize = 800;
const CELL_SIZE: usize = 4;
const GRID_WIDTH: usize = SCREEN_WIDTH / CELL_SIZE;
const GRID_HEIGHT: usize = SCREEN_HEIGHT / CELL_SIZE;


const SAND_COLORS: [(u8, u8, u8); 4] = [
    (210, 180, 140),
    (194, 178, 128),
    (244, 213, 141),
    (178, 153, 110),
];

#[derive(Debug, Clone, Copy, PartialEq)]
struct Particle {
    type_id: usize,
    x: usize,
    y: usize,
    tx: f32,
    ty: f32,
    vx: f32,
    vy: f32,
    color: (u8, u8, u8),
    lifespan: usize,
}

fn create_particle(
    type_id: usize,
    x: usize,
    y: usize,
    vx: f32,
    vy: f32,
    color: (u8, u8, u8),
    lifespan: usize,
) -> Particle {
    Particle {
        type_id,
        x,
        y,
        tx: x as f32,
        ty: y as f32,
        vx,
        vy,
        color,
        lifespan,
    }
}

fn update_particles(grid: &mut Vec<Vec<Option<Particle>>>, particles_to_clear: &mut Vec<(usize, usize)>, particles_to_draw: &mut Vec<(usize, usize, (u8, u8, u8))>) {
    particles_to_clear.clear();
    particles_to_draw.clear();
    for y in (0..GRID_HEIGHT).rev() {
        for x in 0..GRID_WIDTH {
            if let Some(current_cell_ref) = grid.get_mut(y).and_then(|row| row.get_mut(x)) {
                if let Some(mut p) = current_cell_ref.take(){
                    //println!("particle taken {x} {y}");
                    let previous_x: usize = x;
                    let previous_y: usize = y;
                    let mut final_y: usize = y;
                    let mut final_x: usize = x;
                    let mut moved = false;

                    if p.type_id == SAND_ID {
                        let target_y: usize = y + 1;
                        if target_y < GRID_HEIGHT {
                            if let Some(target_cell) = grid.get_mut(target_y).and_then(|row| row.get_mut(x)) {
                                if target_cell.is_none() {
                                    moved = true;
                                    final_y = target_y;
                                }
                            }
                        

                            if !moved {
                                let mut rng = thread_rng();
                                let mut diagonal_offsets: Vec<(isize, isize)> = vec![(-1, 1), (1, 1)];
                                if rng.gen_bool(0.5) {
                                    diagonal_offsets.reverse();
                                }

                                for (dx, dy) in diagonal_offsets {
                                    let target_y: usize = (y as isize + dy) as usize;
                                    let target_x: usize = (x as isize + dx) as usize;

                                    if target_y < GRID_HEIGHT && target_x < GRID_WIDTH {
                                        if target_x < GRID_WIDTH {
                                            if let Some(target_cell) = grid.get_mut(target_y).and_then(|row| row.get_mut(target_x)) {
                                                if target_cell.is_none() {
                                                    final_x = target_x;
                                                    final_y = target_y;
                                                    moved = true;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    p.x = final_x;
                    p.y = final_y;
                    grid[previous_y][previous_x] = None;
                    grid[final_y][final_x] = Some(p);
                    //println!("particle put back");
                    particles_to_clear.push((previous_x, previous_y));
                    particles_to_draw.push((final_x, final_y, p.color));

                }
            }
        }
    }
}

fn draw_screen(particles_to_clear: &Vec<(usize, usize)>, particles_to_draw: &Vec<(usize, usize, (u8, u8, u8))>) {
    //println!("particles to clear: {:?}", particles_to_clear);
    //println!("particles to draw: {:?}", particles_to_draw);
    for (x, y) in particles_to_clear {
        draw_rectangle((*x * CELL_SIZE) as f32, (*y * CELL_SIZE) as f32, CELL_SIZE as f32, CELL_SIZE as f32, BLACK)
    }
    for (x, y, (r, g, b)) in particles_to_draw {
        draw_rectangle((*x * CELL_SIZE) as f32, (*y * CELL_SIZE) as f32, CELL_SIZE as f32, CELL_SIZE as f32, Color::from_rgba(*r, *g, *b, 255))
    }
}

fn window_conf() -> Conf {
    Conf {
        window_title: "Sandbox".to_owned(),
        window_width: SCREEN_WIDTH as i32,   
        window_height: SCREEN_HEIGHT as i32, 
        high_dpi: true, 
        fullscreen: false,
        sample_count: 1, 
        window_resizable: true, 
        icon: None, 
        platform: Platform::default(), 
    }
}

fn handle_mouse_input(grid: &mut Vec<Vec<Option<Particle>>>, particles_to_draw: &mut Vec<(usize, usize, (u8, u8, u8))>){ 
    if is_mouse_button_down(MouseButton::Left) {
        let (mouse_x, mouse_y) = mouse_position();

        let grid_x = (mouse_x / CELL_SIZE as f32) as isize;
        let grid_y = (mouse_y / CELL_SIZE as f32) as isize;
        let radius = 10; 

        for dx in -radius..=radius {
            for dy in -radius..=radius {
                let target_grid_x = grid_x + dx;
                let target_grid_y = grid_y + dy;

                if target_grid_x >= 0 && target_grid_x < GRID_WIDTH as isize &&
                   target_grid_y >= 0 && target_grid_y < GRID_HEIGHT as isize {

                    let target_grid_x = target_grid_x as usize;
                    let target_grid_y = target_grid_y as usize;

                    if grid[target_grid_y][target_grid_x].is_none() {
                        let new_sand_particle = create_particle(
                            SAND_ID,
                            target_grid_x,
                            target_grid_y,
                            0.0, 
                            1.0, 
                            *SAND_COLORS.choose(&mut thread_rng()).unwrap(),
                            0,
                        );

                        grid[target_grid_y][target_grid_x] = Some(new_sand_particle);
                        particles_to_draw.push((target_grid_x, target_grid_y, new_sand_particle.color));
                    }
                }
            }
        }
    }
}
#[macroquad::main(window_conf)]
async fn main() {
    let mut grid: Vec<Vec<Option<Particle>>> = vec![vec![None; GRID_WIDTH as usize]; GRID_HEIGHT as usize];
    let mut particles_to_clear: Vec<(usize, usize)> = Vec::new();
    let mut particles_to_draw: Vec<(usize, usize, (u8, u8, u8))> = Vec::new();
    grid[5][3] = Some(create_particle(SAND_ID, 3, 5, 0.0, 1.0, *SAND_COLORS.choose(&mut thread_rng()).unwrap(), 0));
    grid[6][3] = Some(create_particle(SAND_ID, 3, 6, 0.0, 1.0, *SAND_COLORS.choose(&mut thread_rng()).unwrap(), 0));
    grid[7][3] = Some(create_particle(SAND_ID, 3, 7, 0.0, 1.0, *SAND_COLORS.choose(&mut thread_rng()).unwrap(), 0));
    grid[7][15] = Some(create_particle(SAND_ID, 15, 7, 0.0, 1.0, *SAND_COLORS.choose(&mut thread_rng()).unwrap(), 0));
    loop {
        let start_time = Instant::now();
        handle_mouse_input(&mut grid, &mut particles_to_draw);
        draw_screen(&particles_to_clear, &particles_to_draw);
        update_particles(&mut grid, &mut particles_to_clear, &mut particles_to_draw);
        next_frame().await;
        let end_time = Instant::now();
        let sleep_duration_ms = 1000.0 / 60.0 - end_time.duration_since(start_time).as_millis() as f32;

        if sleep_duration_ms > 0.0 {
            thread::sleep(Duration::from_millis(sleep_duration_ms as u64));
        }
        draw_fps();
    }
}