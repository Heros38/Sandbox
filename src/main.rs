use ::rand::Rng;
use ::rand::seq::SliceRandom;
use ::rand::thread_rng;
use macroquad::prelude::*;
use crate::miniquad::conf::Platform;
use std::{thread, vec};
use std::time::{Instant, Duration};


const SAND_ID: usize = 1;
const SCREEN_WIDTH: usize = 1600;
const SCREEN_HEIGHT: usize = 800;
const CELL_SIZE: usize = 5;
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

/* 
def get_line(x0: int, y0: int, x1: int, y1: int):
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
*/

fn get_line(mut x0:isize, mut y0:isize, x1:isize, y1:isize) -> Vec<(isize, isize)>{
    let mut points: Vec<(isize, isize)> = Vec::new();
    let dx: isize = (x1 - x0).abs();
    let dy: isize = -(y1 - y0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx + dy;

    loop{
        points.push((x0, y0));
        if x0 == x1 && y0 == y1{break}
        let e2 = 2 * &err;
        if e2 >= dy{
            err += &dy;
            x0 += sx;
        }
        if e2 <= dx{
            err += &dx;
            y0 += sy;
        }
    }
    return points
}


fn update_particles(grid: &mut Vec<Vec<Option<Particle>>>) {
    let mut rng = thread_rng();
    for y in (0..GRID_HEIGHT).rev() {
        let mut row_x_indices: Vec<usize> = (0..GRID_WIDTH).collect();
        row_x_indices.shuffle(&mut rng); 

        for x in row_x_indices {
            if let Some(mut p) = grid[y][x] {
                //if let Some(mut p) = current_cell_ref.take(){
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
                    //}
                if moved{
                    //let mut p = p;
                    p.x = final_x;
                    p.y = final_y;
                    grid[previous_y][previous_x] = None;
                    grid[final_y][final_x] = Some(p);
                }   

                }
            }
        }
    }
}

fn draw_screen(image: &mut Image, texture: &mut Texture2D, grid: &Vec<Vec<Option<Particle>>>) {
    //println!("particles to clear: {:?}", particles_to_clear);
    //println!("particles to draw: {:?}", particles_to_draw);
    for y in 0..GRID_HEIGHT{
        for x in 0..GRID_WIDTH {
            if let Some(current) = grid[y][x]{
                let (r, g, b) = current.color;
                image.set_pixel(x as u32, y as u32, Color::from_rgba(r, g, b, 255));
            } else{
                image.set_pixel(x as u32, y as u32, BLACK);
            }
        }
    }
    /*
    for (x, y) in particles_to_clear {
        image.set_pixel(*x as u32, *y as u32, BLACK);
        //draw_rectangle((*x * CELL_SIZE) as f32, (*y * CELL_SIZE) as f32, CELL_SIZE as f32, CELL_SIZE as f32, BLACK);
        //println!("particle cleared at {x} {y}");
    }
    for (x, y, (r, g, b)) in particles_to_draw {
        image.set_pixel(*x as u32, *y as u32, Color::from_rgba(*r, *g, *b, 255));
        //draw_rectangle((*x * CELL_SIZE) as f32, (*y * CELL_SIZE) as f32, CELL_SIZE as f32, CELL_SIZE as f32, Color::from_rgba(*r, *g, *b, 255))
    }
     */
    texture.update(image);
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

fn handle_mouse_input(grid: &mut Vec<Vec<Option<Particle>>>, previous_pos: &mut (isize, isize)){ 
    if is_mouse_button_down(MouseButton::Left) || is_mouse_button_down(MouseButton::Right){
        let (mouse_x, mouse_y) = mouse_position();
        let grid_x = (mouse_x / CELL_SIZE as f32) as isize;
        let grid_y = (mouse_y / CELL_SIZE as f32) as isize;
        let radius = 10; 
        if previous_pos.0 != -1{
            for (x, y) in get_line(previous_pos.0, previous_pos.1, grid_x, grid_y){
                if is_mouse_button_down(MouseButton::Left) {
                    for dx in -radius..=radius {
                        for dy in -radius..=radius {
                            let target_grid_x: isize = x + dx;
                            let target_grid_y: isize = y + dy;

                            if target_grid_x >= 0 && target_grid_x < GRID_WIDTH as isize &&
                            target_grid_y >= 0 && target_grid_y < GRID_HEIGHT as isize {

                                let target_grid_x: usize = target_grid_x as usize;
                                let target_grid_y: usize = target_grid_y as usize;

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
                                }
                            }
                        }
                    }
                }
                else if is_mouse_button_down(MouseButton::Right) {
                    for dx in -radius..=radius {
                        for dy in -radius..=radius {
                            let target_grid_x = x + dx;
                            let target_grid_y = y + dy;

                            if target_grid_x >= 0 && target_grid_x < GRID_WIDTH as isize &&
                            target_grid_y >= 0 && target_grid_y < GRID_HEIGHT as isize {

                                let target_grid_x = target_grid_x as usize;
                                let target_grid_y = target_grid_y as usize;

                                grid[target_grid_y][target_grid_x] = None;
                            }
                        }
                    }
                }
            }
        }
        *previous_pos = (grid_x, grid_y);
    } else {
        *previous_pos = (-1, -1)
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    let mut grid: Vec<Vec<Option<Particle>>> = vec![vec![None; GRID_WIDTH as usize]; GRID_HEIGHT as usize];
    let mut bytes: Vec<u8> = Vec::new();
    let mut previous_pos: (isize, isize) = (-1, -1);
    //set_fullscreen(true);
    bytes.resize(GRID_WIDTH * GRID_HEIGHT * 4, 0); 

    for i in (3..bytes.len()).step_by(4) {
        bytes[i] = 255;
    }
    let mut game_image = Image {bytes, width: GRID_WIDTH as u16, height: GRID_HEIGHT as u16};
    let mut game_texture = Texture2D::from_image(&game_image);
    game_texture.set_filter(FilterMode::Nearest);

    loop {
        let start_time = Instant::now();
        //let start_update_time = Instant::now();
        update_particles(&mut grid);
        //let end_update_time = Instant::now();
        //println!("update time: {}", end_update_time.duration_since(start_update_time).as_millis());
        
        handle_mouse_input(&mut grid, &mut previous_pos);
        
        //let start_draw_time = Instant::now();
        draw_screen(&mut game_image, &mut game_texture, &grid);
        draw_texture_ex(
            &game_texture, 
            0.0,
            0.0,
            WHITE, 
            DrawTextureParams {
                dest_size: Some(vec2(
                    GRID_WIDTH as f32 * CELL_SIZE as f32,
                    GRID_HEIGHT as f32 * CELL_SIZE as f32,
                )),
                ..Default::default()
            },
        );
        //let end_draw_time = Instant::now();
        //println!("draw time: {}", end_draw_time.duration_since(start_draw_time).as_millis());
        
        next_frame().await;
        let end_time: Instant = Instant::now();
        let sleep_duration_ms = 1000.0 / 60.0 - end_time.duration_since(start_time).as_millis() as f32;

        if sleep_duration_ms > 0.0 {
            thread::sleep(Duration::from_millis(sleep_duration_ms as u64));
        }
    }
}