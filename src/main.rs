use ::rand::Rng;
use ::rand::seq::SliceRandom;
use ::rand::thread_rng;
use macroquad::{prelude::*};
use crate::miniquad::conf::Platform;
use std::{thread, vec};
use std::time::{Instant, Duration};


const SAND_ID: usize = 1;
const WATER_ID: usize = 2;
const STONE_ID: usize = 3;
const _CHROMATIC_ID: usize = 4;
const _STEAM_ID: usize = 5;
const _FIRE_ID: usize = 6;
const _WOOD_ID: usize = 7;
const SCREEN_WIDTH: usize = 1600;
const SCREEN_HEIGHT: usize = 800;
const CELL_SIZE: usize = 2;
const GRID_WIDTH: usize = SCREEN_WIDTH / CELL_SIZE;
const GRID_HEIGHT: usize = SCREEN_HEIGHT / CELL_SIZE;
const GRAVITY: f32 = 0.2;
const FRICTION: f32 = 0.02;
const MAX_SPREAD_DIST: usize = 8;

const CHUNK_SIZE: usize = 40;
const CHUNKS_X: usize = GRID_WIDTH / CHUNK_SIZE;
const CHUNKS_Y: usize = GRID_HEIGHT / CHUNK_SIZE;


const SAND_COLORS: [(u8, u8, u8); 4] = [
    (210, 180, 140),
    (194, 178, 128),
    (244, 213, 141),
    (178, 153, 110),
];

const WATER_COLORS: [(u8, u8, u8); 3] = [
    (65, 105, 225),
    (0, 0, 128),
    (25, 25, 112)
];

const STONE_COLORS: [(u8, u8, u8); 4] = [
    (190, 200, 205),
    (140, 150, 155),
    (90, 100, 105),
    (50, 55, 60)
];
const _CHROMATIC_COLORS: [(u8, u8, u8); 7] = [
    (255, 0, 0),
    (255, 127, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 0, 255),
    (75, 0, 130),
    (148, 0, 211)
];

const _STEAM_COLORS: [(u8, u8, u8); 4] = [
    (240, 240, 240),
    (225, 225, 225),
    (210, 210, 210),
    (195, 195, 195)
];

const _FIRE_COLORS: [(u8, u8, u8); 4] = [
    (255, 255, 102),
    (255, 204, 0),
    (255, 102, 0),
    (204, 51, 0) 
];

const _WOOD_COLORS: [(u8, u8, u8); 3] = [
    (150, 95, 45), 
    (100, 60, 30), 
    (200, 140, 90) 
];

const _BURNING_WOOD_COLORS: [(u8, u8, u8); 3] = [
    (70, 40, 20),
    (200, 80, 0),
    (255, 200, 100)
];

const _ACID_COLORS: [(u8, u8, u8); 3] = [
    (153, 255, 0),
    (102, 204, 0),
    (51, 153, 0)
];

const _SMOKE_COLORS: [(u8, u8, u8); 3] = [
    (150, 150, 150),
    (100, 100, 100),
    (70, 70, 70) 
];


#[derive(Debug, PartialEq, Clone)]
struct Particle {
    type_id: usize,
    tx: f32,
    ty: f32,
    vx: f32,
    vy: f32,
    lifespan: usize,
}

fn create_particle(
    type_id: usize,
    tx: f32 ,
    ty: f32,
    vx: f32,
    vy: f32,
    lifespan: usize,
) -> Particle {
    Particle {
        type_id,
        tx,
        ty,
        vx,
        vy,
        lifespan,
    }
}

#[inline]
fn get_line(mut x0:isize, mut y0:isize, x1:isize, y1:isize, buffer: &mut Vec<(isize, isize)>){
    buffer.clear();
    let dx: isize = (x1 - x0).abs();
    let dy: isize = -(y1 - y0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx + dy;

    loop{
        buffer.push((x0, y0));
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
}

#[inline]
fn get_scanline(chunks: &Vec<Vec<bool>>, cy: usize, scanlines: &mut Vec<Vec<(usize, usize)>>, rng: &mut ::rand::prelude::ThreadRng){

    for y_local in (0..CHUNK_SIZE).rev(){
        let line: &mut Vec<(usize, usize)> = &mut scanlines[y_local];
        line.clear(); 
        for cx in 0..CHUNKS_X{
            if chunks[cy][cx] {    
                line.push((cx * CHUNK_SIZE, (cx+1) * CHUNK_SIZE));
            }
        }
        line.shuffle(rng);
    }
}


fn update_particles(chunks: &mut Vec<Vec<bool>>, image: &mut Image, grid: &mut Vec<Vec<Option<Particle>>>) {
    let mut rng: ::rand::prelude::ThreadRng = thread_rng();
    let image_data: &mut [[u8; 4]] = image.get_image_data_mut();
    let mut path_buffer: Vec<(isize, isize)> =  Vec::new();
    let mut scanlines_buffer: Vec<Vec<(usize, usize)>> = vec![vec![]; CHUNK_SIZE];

    for chunk_y in (0..CHUNKS_Y as usize).rev() { 
        get_scanline(chunks, chunk_y, &mut scanlines_buffer, &mut rng); // directly modify scanlines
        for cx in 0..CHUNKS_X {
            chunks[chunk_y][cx] = false;
        }

        for y_local in (0..CHUNK_SIZE).rev() {
            let y_global = chunk_y * CHUNK_SIZE + y_local;

            let lines: &Vec<(usize, usize)> = &scanlines_buffer[y_local]; 
            for chunk_line in lines {
                let mut row_x_indices: Vec<usize> = (chunk_line.0..chunk_line.1).collect();
                row_x_indices.shuffle(&mut rng);
                let chunk_x = chunk_line.0 / CHUNK_SIZE;

                for x_global in row_x_indices {
                    let x_local = x_global % CHUNK_SIZE;
                    if let Some(mut p) = grid[y_global][x_global].take() {
                        if p.type_id == SAND_ID || p.type_id == WATER_ID{
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

                            get_line(p.tx.round() as isize, p.ty.round() as isize, target_tx.round() as isize, target_ty.round() as isize, &mut path_buffer); // directly modify path

                            let mut collision: bool = false;

                            for &(nx, ny) in path_buffer.iter().skip(1){
                                if !(0 <= nx && nx < GRID_WIDTH as isize && 0 <= ny && ny < GRID_HEIGHT as isize){
                                    collision = true;
                                    break
                                }
                                if grid[ny as usize][nx as usize].is_none(){
                                    final_x = nx as usize;
                                    final_y = ny as usize;
                                } 
                                else if let Some(checked_cell) = &grid[ny as usize][nx as usize] {
                                    if p.type_id == SAND_ID && checked_cell.type_id == WATER_ID { 
                                        final_x = nx as usize;
                                        final_y = ny as usize;
                                    }
                                } 
                                
                                else{
                                    collision = true;
                                    break
                                }
                            }
                            if previous_x != final_x || previous_y != final_y{
                                moved = true;
                                if collision{
                                    p.tx = final_x as f32;
                                    p.ty = final_y as f32;
                                    p.vx = 0.0;
                                    p.vy = 0.0;

                                } else{
                                    if grid[final_y][final_x].is_none(){
                                        p.tx = target_tx;
                                        p.ty = target_ty;
                                    }
                                    else{ // swap between sand and water
                                        p.tx = target_tx;
                                        p.ty = target_ty;
                                        p.vx *= 0.6;
                                        p.vy *= 0.6;
                                        grid[previous_y][previous_x] = grid[final_y as usize][final_x as usize].take();
                                    }
                                }
                            }
                            
                            if p.type_id == SAND_ID{ // diagonals
                                if !moved {
                                    let mut diagonal_offsets: Vec<(isize, isize)> = vec![(-1, 1), (1, 1)];
                                    if rng.gen_bool(0.5) {
                                        diagonal_offsets.reverse();
                                    }

                                    for (dx, dy) in diagonal_offsets {
                                        let target_x = previous_x as isize + dx;
                                        let target_y = previous_y as isize + dy;

                                        if target_x >= 0 && target_x < GRID_WIDTH as isize &&
                                        target_y >= 0 && target_y < GRID_HEIGHT as isize {
                                            
                                            if grid[target_y as usize][target_x as usize].is_none() {
                                                final_x = target_x as usize;
                                                final_y = target_y as usize;
                                                p.tx = final_x as f32;
                                                p.ty = final_y as f32;
                                                moved = true;
                                                break;
                                            } else if let Some(checked_cell) = &grid[target_y as usize][target_x as usize] && checked_cell.type_id == WATER_ID{
                                                final_x = target_x as usize;
                                                final_y = target_y as usize;
                                                p.tx = final_x as f32;
                                                p.ty = final_y as f32;
                                                moved = true;
                                                grid[previous_y][previous_x] = grid[final_y as usize][final_x as usize].take();
                                                break;
                                            }
                                        }
                                    }
                                }
                            }
                            
                            if p.type_id == WATER_ID && !moved{ // water diags and spread
                                let mut diagonal_offsets: Vec<(isize, isize)> = vec![(-1, 1), (1, 1)];
                                if rng.gen_bool(0.5) {
                                    diagonal_offsets.reverse();
                                }

                                for (dx, dy) in diagonal_offsets {
                                    let target_x = previous_x as isize + dx;
                                    let target_y = previous_y as isize + dy;

                                    if target_x >= 0 && target_x < GRID_WIDTH as isize &&
                                    target_y >= 0 && target_y < GRID_HEIGHT as isize {
                                        
                                        if grid[target_y as usize][target_x as usize].is_none() {
                                            final_x = target_x as usize;
                                            final_y = target_y as usize;
                                            p.tx = final_x as f32;
                                            p.ty = final_y as f32;
                                            moved = true;
                                            break;
                                        }
                                    }
                                }
                                if !moved{
                                    let mut direction:isize = if rng.gen_bool(0.5) {1} else {-1};  
                                    for _ in 0..2{
                                        if moved {break}
                                        for dx in 1..MAX_SPREAD_DIST{
                                            let current_x:isize = previous_x as isize + dx as isize * direction;
                                            if current_x < GRID_WIDTH as isize && current_x >= 0 && grid[previous_y][current_x as usize].is_none(){ 
                                                final_x = current_x as usize;
                                                moved = true;
                                            }
                                        }
                                        direction *= -1;
                                    }
                                }
                            }
                            
                            if !moved {
                                p.vy *= 0.7;
                            } else {
                                chunks[chunk_y][chunk_x] = true;
                            }

                            let final_chunk_x = final_x / CHUNK_SIZE;
                            let final_chunk_y = final_y / CHUNK_SIZE;

                            grid[final_y][final_x] = Some(p);
                            if moved{
                                chunks[chunk_y][chunk_x] = true;
                                chunks[final_chunk_y][final_chunk_x] = true;
                                if y_local == 0{
                                    if chunk_y > 0 {chunks[chunk_y - 1][chunk_x] = true;}
                                }
                                if x_local == 0{
                                    if chunk_x > 0 {chunks[chunk_y][chunk_x - 1] = true;}
                                }
                                if x_local == CHUNK_SIZE - 1{
                                    if chunk_x < CHUNKS_X - 1 {chunks[chunk_y][chunk_x + 1] = true;}
                                }
                                let idx1 = previous_x + previous_y * GRID_WIDTH;
                                let idx2 = final_x + final_y * GRID_WIDTH;
                                let (first_idx, second_idx) = if idx1 < idx2 { (idx1, idx2) } else { (idx2, idx1) };

                                let (left_slice, right_slice_starting_at_second_idx) = image_data.split_at_mut(second_idx);

                                let pixel1 = &mut left_slice[first_idx]; 
                                let pixel2 = &mut right_slice_starting_at_second_idx[0]; 

                                std::mem::swap(pixel1, pixel2);
                            }
                        }
                        else{
                            grid[y_global][x_global] = Some(p);
                        }
                    }
                }
            }
        }
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

fn handle_mouse_input(chunks: &mut Vec<Vec<bool>>, previous_pos: &mut (isize, isize), image: &mut Image, current_particle_type: &usize, grid: &mut Vec<Vec<Option<Particle>>>){
    let image_data: &mut [[u8; 4]] = image.get_image_data_mut();
    let mut path_buffer: Vec<(isize, isize)> =  Vec::new();
    if is_mouse_button_down(MouseButton::Left) || is_mouse_button_down(MouseButton::Right){
        let (mouse_x, mouse_y) = mouse_position();
        let grid_x = (mouse_x / CELL_SIZE as f32) as isize;
        let grid_y = (mouse_y / CELL_SIZE as f32) as isize;
        let radius = 10;
        if previous_pos.0 != -1{
            get_line(previous_pos.0, previous_pos.1, grid_x, grid_y, &mut path_buffer);
            for (x, y) in path_buffer{
                if is_mouse_button_down(MouseButton::Left) {
                    for dx in -radius..=radius {
                        for dy in -radius..=radius {
                            let target_grid_x: isize = x + dx;
                            let target_grid_y: isize = y + dy;

                            if target_grid_x >= 0 && target_grid_x < GRID_WIDTH as isize &&
                               target_grid_y >= 0 && target_grid_y < GRID_HEIGHT as isize {

                                if grid[target_grid_y as usize][target_grid_x as usize].is_none() {
                                    if *current_particle_type == SAND_ID{
                                        let (r, g, b) = *SAND_COLORS.choose(&mut thread_rng()).unwrap();
                                        if let Some(pixel_slice) = image_data.get_mut(target_grid_x as usize + target_grid_y as usize * GRID_WIDTH) {
                                            *pixel_slice = [r, g, b, 255]; 
                                        }
                                        let new_particle = create_particle(
                                            SAND_ID,
                                            target_grid_x as f32,
                                            target_grid_y as f32,
                                            0.0,    
                                            1.0,
                                            0,
                                        );
                                        grid[target_grid_y as usize][target_grid_x as usize] = Some(new_particle);
                                    }
                                    else if *current_particle_type == WATER_ID{
                                        let (r, g, b) = *WATER_COLORS.choose(&mut thread_rng()).unwrap();
                                        if let Some(pixel_slice) = image_data.get_mut(target_grid_x as usize + target_grid_y as usize * GRID_WIDTH) {
                                            *pixel_slice = [r, g, b, 255]; 
                                        }
                                        let new_particle = create_particle(
                                            WATER_ID,
                                            target_grid_x as f32,
                                            target_grid_y as f32,
                                            0.0,    
                                            1.0,
                                            0,
                                        );
                                        grid[target_grid_y as usize][target_grid_x as usize] = Some(new_particle);
                                    } 
                                    else if *current_particle_type == STONE_ID{
                                        let (r, g, b) = *STONE_COLORS.choose(&mut thread_rng()).unwrap();
                                        if let Some(pixel_slice) = image_data.get_mut(target_grid_x as usize + target_grid_y as usize * GRID_WIDTH) {
                                            *pixel_slice = [r, g, b, 255]; 
                                        }
                                        let new_particle = create_particle(
                                            STONE_ID,
                                            target_grid_x as f32,
                                            target_grid_y as f32,
                                            0.0,    
                                            0.0,
                                            0,
                                        );
                                        grid[target_grid_y as usize][target_grid_x as usize] = Some(new_particle);
                                    }
                                    chunks[target_grid_y as usize / CHUNK_SIZE][target_grid_x as usize / CHUNK_SIZE] = true;
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
                                if grid[target_grid_y as usize][target_grid_x as usize] != None {
                                    if let Some(pixel_slice) = image_data.get_mut(target_grid_x as usize + target_grid_y as usize * GRID_WIDTH) {
                                        *pixel_slice = [0, 0, 0, 255]; 
                                    }
                                    grid[target_grid_y as usize][target_grid_x as usize] = None;
                                    chunks[target_grid_y as usize / CHUNK_SIZE][target_grid_x as usize / CHUNK_SIZE] = true;                                    
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

fn handle_keyboard_input(current_particle_type: &mut usize){
    if is_key_pressed(KeyCode::Key1){
        *current_particle_type = SAND_ID;
    }
    else if is_key_pressed(KeyCode::Key2){
        *current_particle_type = WATER_ID;
    }
    else if is_key_pressed(KeyCode::Key3){
        *current_particle_type = STONE_ID;
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    let mut grid: Vec<Vec<Option<Particle>>> = vec![vec![None; GRID_WIDTH as usize]; GRID_HEIGHT as usize];
    let mut bytes: Vec<u8> = Vec::new();
    let mut chunks: Vec<Vec<bool>> = vec![vec![false; CHUNKS_X]; CHUNKS_Y];
    let mut previous_pos: (isize, isize) = (-1, -1);
    let mut current_particle_type: usize = SAND_ID;
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
        update_particles(&mut chunks, &mut game_image, &mut grid);
        //let end_update_time = Instant::now();
        //println!("update time: {}", end_update_time.duration_since(start_update_time).as_millis());
        
        handle_mouse_input(&mut chunks, &mut previous_pos, &mut game_image, &current_particle_type, &mut grid);

        handle_keyboard_input(&mut current_particle_type);
        
        game_texture.update(&game_image);
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
                if chunks[chunk_y][chunk_x] {
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
        let end_time: Instant = Instant::now();
        let sleep_duration_ms = 1000.0 / 60.0 - end_time.duration_since(start_time).as_millis() as f32;

        if sleep_duration_ms > 0.0 {
            thread::sleep(Duration::from_millis(sleep_duration_ms as u64));
        }
        draw_fps();
        next_frame().await;
    }
}