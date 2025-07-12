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
const CELL_SIZE: usize = 2;
const GRID_WIDTH: usize = SCREEN_WIDTH / CELL_SIZE;
const GRID_HEIGHT: usize = SCREEN_HEIGHT / CELL_SIZE;
const GRAVITY: f32 = 0.2;
const FRICTION: f32 = 0.02;

const CHUNK_SIZE: usize = 40;
const CHUNKS_X: usize = GRID_WIDTH / CHUNK_SIZE;
const CHUNKS_Y: usize = GRID_HEIGHT / CHUNK_SIZE;


const SAND_COLORS: [(u8, u8, u8); 4] = [
    (210, 180, 140),
    (194, 178, 128),
    (244, 213, 141),
    (178, 153, 110),
];

#[derive(Clone)]
struct Chunk {
    particles: Vec<Vec<Option<Particle>>>,
    is_active: bool,
}

impl Chunk {
    fn new() -> Self {
        Chunk {
            particles: vec![vec![None; CHUNK_SIZE]; CHUNK_SIZE],
            is_active: false,
        }
    }
}

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
    is_sleeping: bool,
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
        is_sleeping: false
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
        let e2 = 2 * err;
        if e2 >= dy{
            err += dy;
            x0 += sx;
        }
        if e2 <= dx{
            err += dx;
            y0 += sy;
        }
    }
    return points
}


fn update_particles(chunks: &mut Vec<Vec<Chunk>>, image: &mut Image) {
    let mut rng = thread_rng();
    let image_data: &mut [[u8; 4]] = image.get_image_data_mut();

    

    for chunk_y in (0..CHUNKS_Y as usize).rev() { 
        for chunk_x in 0..CHUNKS_X as usize { 
            if let Some(chunk) = chunks.get_mut(chunk_y).and_then(|row| row.get_mut(chunk_x)) {
                if chunk.is_active {
                    let mut still_active = false;
                    for y_local in (0..CHUNK_SIZE).rev() {
                        let mut row_x_indices: Vec<usize> = (0..CHUNK_SIZE).collect();
                        row_x_indices.shuffle(&mut rng);

                        for x_local in row_x_indices {
                            let x_global = chunk_x * CHUNK_SIZE + x_local;
                            let y_global = chunk_y * CHUNK_SIZE + y_local;

                            if let Some(mut p) = chunks[chunk_y][chunk_x].particles[y_local][x_local].take() {
                                if p.is_sleeping {
                                    chunks[chunk_y][chunk_x].particles[y_local][x_local] = Some(p);
                                    continue;
                                }

                                let previous_x: usize = x_global;
                                let previous_y: usize = y_global;
                                let mut final_x: usize = x_global;
                                let mut final_y: usize = y_global;
                                let mut moved = false;

                                let v2: f32 = p.vx*p.vx + p.vy*p.vy;
                                if v2 > 0.0001{
                                    let v: f32 = v2.sqrt();
                                    let damping: f32 = 1.0 - FRICTION * v;
                                    p.vx *= damping;
                                    p.vy = GRAVITY + damping * p.vy
                                } else{
                                    p.vy = GRAVITY
                                }
                                let target_tx = p.tx + p.vx;
                                let target_ty = p.ty + p.vy;

                                let path = get_line(p.tx.round() as isize, p.ty.round() as isize, target_tx.round() as isize, target_ty.round() as isize);

                                let mut collision: bool = false;

                                for (nx, ny) in path.clone().into_iter().skip(1){
                                    if !(0 <= nx && nx < GRID_WIDTH as isize && 0 <= ny && ny < GRID_HEIGHT as isize){
                                        collision = true;
                                        break
                                    }
                                    let target_chunk_x = (nx as usize) / CHUNK_SIZE;
                                    let target_chunk_y = (ny as usize) / CHUNK_SIZE;
                                    let target_local_x = (nx as usize) % CHUNK_SIZE;
                                    let target_local_y = (ny as usize) % CHUNK_SIZE;

                                    if chunks[target_chunk_y][target_chunk_x].particles[target_local_y][target_local_x].is_none(){
                                        final_x = nx as usize;
                                        final_y = ny as usize;
                                    } else{
                                        collision = true;
                                        break
                                    }
                                }
                                if previous_x != final_x || previous_y != final_y{
                                    moved = true;
                                    if collision{
                                        p.tx = final_x as f32;
                                        p.ty = final_y as f32;
                                        p.vx *= 0.5;

                                    } else{
                                        p.tx = target_tx;
                                        p.ty = target_ty;
                                    }
                                }
                                
                                p.x = final_x;
                                p.y = final_y;

                                if p.type_id == SAND_ID{
                                    if !moved {
                                        let mut diagonal_offsets: Vec<(isize, isize)> = vec![(-1, 1), (1, 1)];
                                        if rng.gen_bool(0.5) {
                                            diagonal_offsets.reverse();
                                        }

                                        for (dx, dy) in diagonal_offsets {
                                            let target_x_diag_global = p.x as isize + dx;
                                            let target_y_diag_global = p.y as isize + dy;

                                            if target_x_diag_global >= 0 && target_x_diag_global < GRID_WIDTH as isize &&
                                            target_y_diag_global >= 0 && target_y_diag_global < GRID_HEIGHT as isize {
                                                
                                                let target_chunk_x = target_x_diag_global as usize / CHUNK_SIZE;
                                                let target_chunk_y = target_y_diag_global as usize / CHUNK_SIZE;
                                                let target_local_x = target_x_diag_global as usize % CHUNK_SIZE;
                                                let target_local_y = target_y_diag_global as usize % CHUNK_SIZE;
                                                
                                                if chunks[target_chunk_y][target_chunk_x].particles[target_local_y][target_local_x].is_none() {
                                                    p.x = target_x_diag_global as usize;
                                                    p.y = target_y_diag_global as usize;
                                                    p.tx = p.x as f32;
                                                    p.ty = p.y as f32;
                                                    moved = true;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                }
                                final_x = p.x;
                                final_y = p.y;
                                if let Some(pixel_slice) = image_data.get_mut(previous_x + previous_y * GRID_WIDTH) {
                                    *pixel_slice = [0, 0, 0, 255]; 
                                }
                                if let Some(pixel_slice) = image_data.get_mut(final_x + final_y * GRID_WIDTH) {
                                    let (r, g, b) = p.color;
                                    *pixel_slice = [r, g, b, 255]; 
                                }
                                

                                if !moved {
                                    p.vy *= 0.7;
                                    if p.vy.abs() < 0.1 {
                                    p.is_sleeping = true;
                                    }
                                } else {
                                    p.is_sleeping = false;
                                    still_active = true;
                                }

                                let final_chunk_x = p.x / CHUNK_SIZE;
                                let final_chunk_y = p.y / CHUNK_SIZE;
                                let final_local_x = p.x % CHUNK_SIZE;
                                let final_local_y = p.y % CHUNK_SIZE;

                                chunks[final_chunk_y][final_chunk_x].particles[final_local_y][final_local_x] = Some(p);

                                if moved {
                                    for dx in -1..=1 {
                                        for dy in -1..=1 {
                                            let nx = final_chunk_x as isize + dx;
                                            let ny = final_chunk_y as isize + dy;
                                            if let Some(chunk) = chunks.get_mut(ny as usize).and_then(|row| row.get_mut(nx as usize)) {
                                                chunk.is_active = true;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    chunks[chunk_y][chunk_x].is_active = still_active;

                }
            }
        }
    }
}


fn _draw_screen(image: &mut Image, texture: &mut Texture2D, chunks: &Vec<Vec<Chunk>>) {
    let image_data: &mut [[u8; 4]] = image.get_image_data_mut();

    for cx in 0..CHUNKS_X {
        for cy in 0..CHUNKS_Y {
            let chunk = &chunks[cy][cx];
            if chunk.is_active{
                for lx in 0..CHUNK_SIZE {
                    for ly in 0..CHUNK_SIZE {
                        let gx = cx * CHUNK_SIZE + lx;
                        let gy = cy * CHUNK_SIZE + ly;
                        let pixel_index = gy * GRID_WIDTH + gx;

                        if let Some(pixel_slice) = image_data.get_mut(pixel_index) {
                            if let Some(current_particle) = chunk.particles[ly][lx] {
                                let (r, g, b) = current_particle.color;
                                *pixel_slice = [r, g, b, 255]; 
                            } else {
                                *pixel_slice = [0, 0, 0, 255]; 
                            }
                        }
                    }
                }
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

fn handle_mouse_input(chunks: &mut Vec<Vec<Chunk>>, previous_pos: &mut (isize, isize), image: &mut Image){
    let image_data: &mut [[u8; 4]] = image.get_image_data_mut();
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
                                let chunk_x = target_grid_x as usize / CHUNK_SIZE;
                                let chunk_y = target_grid_y as usize / CHUNK_SIZE;
                                let local_x = target_grid_x as usize % CHUNK_SIZE;
                                let local_y = target_grid_y as usize % CHUNK_SIZE;

                                if chunks[chunk_y][chunk_x].particles[local_y][local_x].is_none() {
                                    let color = *SAND_COLORS.choose(&mut thread_rng()).unwrap();
                                    if let Some(pixel_slice) = image_data.get_mut(target_grid_x as usize + target_grid_y as usize * GRID_WIDTH) {
                                        let (r, g, b) = color;
                                        *pixel_slice = [r, g, b, 255]; 
                                    }
                                    let new_sand_particle = create_particle(
                                        SAND_ID,
                                        target_grid_x as usize,
                                        target_grid_y as usize,
                                        0.0,    
                                        1.0,
                                        color,
                                        0,
                                    );
                                    chunks[chunk_y][chunk_x].particles[local_y][local_x] = Some(new_sand_particle);
                                    chunks[chunk_y][chunk_x].is_active = true;
                                    
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
                                let chunk_x = target_grid_x as usize / CHUNK_SIZE;
                                let chunk_y: usize = target_grid_y as usize / CHUNK_SIZE;
                                let local_x = target_grid_x as usize % CHUNK_SIZE;
                                let local_y = target_grid_y as usize % CHUNK_SIZE;
                                if chunks[chunk_y][chunk_x].particles[local_y][local_x].is_some() {
                                    if let Some(pixel_slice) = image_data.get_mut(target_grid_x as usize + target_grid_y as usize * GRID_WIDTH) {
                                        *pixel_slice = [0, 0, 0, 255]; 
                                    }
                                    chunks[chunk_y][chunk_x].particles[local_y][local_x] = None;
                                    chunks[chunk_y][chunk_x].is_active = true;                                    
                                }
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
    //let mut grid: Vec<Vec<Option<Particle>>> = vec![vec![None; GRID_WIDTH as usize]; GRID_HEIGHT as usize];
    let mut bytes: Vec<u8> = Vec::new();
    let mut chunks: Vec<Vec<Chunk>> = vec![vec![Chunk::new(); CHUNKS_X]; CHUNKS_Y];
    let mut previous_pos: (isize, isize) = (-1, -1);
    //set_fullscreen(true);
    bytes.resize(GRID_WIDTH * GRID_HEIGHT * 4, 0); 

    for i in (3..bytes.len()).step_by(4) {
        bytes[i] = 255;
    }
    let mut game_image = Image {bytes, width: GRID_WIDTH as u16, height: GRID_HEIGHT as u16};
    let game_texture: Texture2D = Texture2D::from_image(&game_image);
    game_texture.set_filter(FilterMode::Nearest);

    loop {
        let start_time = Instant::now();    
        //let start_update_time = Instant::now();
        update_particles(&mut chunks, &mut game_image);
        //let end_update_time = Instant::now();
        //println!("update time: {}", end_update_time.duration_since(start_update_time).as_millis());
        
        handle_mouse_input(&mut chunks, &mut previous_pos, &mut game_image);
        
        //let start_draw_time = Instant::now();
        game_texture.update(&game_image);
        //draw_screen(&mut game_image, &mut game_texture, &chunks);
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
        for chunk_y in (0..CHUNKS_Y as usize).rev() { 
            for chunk_x in 0..CHUNKS_X as usize { 
                if let Some(chunk) = chunks.get_mut(chunk_y).and_then(|row| row.get_mut(chunk_x)) {
                    if chunk.is_active {
                        draw_rectangle_lines(
                            (chunk_x * CHUNK_SIZE * CELL_SIZE) as f32,
                            (chunk_y * CHUNK_SIZE * CELL_SIZE) as f32,
                            (CHUNK_SIZE * CELL_SIZE) as f32,
                            (CHUNK_SIZE * CELL_SIZE) as f32,
                            2.0,
                            RED,
                        )
                    }   
                }
            }
        }
        //let end_draw_time = Instant::now();
        //println!("draw time: {}", end_draw_time.duration_since(start_draw_time).as_millis());
        let end_time: Instant = Instant::now();
        let sleep_duration_ms = 1000.0 / 60.0 - end_time.duration_since(start_time).as_millis() as f32;

        if sleep_duration_ms > 0.0 {
            thread::sleep(Duration::from_millis(sleep_duration_ms as u64));
        }
        draw_fps();
        next_frame().await;
    }
}