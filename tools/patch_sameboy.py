#!/usr/bin/env python3
from pathlib import Path
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else "SameBoy")
path = root / "libretro" / "libretro.c"
src = path.read_text()


def replace_once(old, new, label):
    global src
    if old not in src:
        raise SystemExit(f"Patch anchor not found: {label}")
    src = src.replace(old, new, 1)


replace_once(
    '#include <Core/gb.h>\n',
    '#include <Core/gb.h>\n#include <Core/memory.h>\n',
    'memory include',
)

replace_once(
    '#define MAX_VIDEO_PIXELS (MAX_VIDEO_WIDTH * MAX_VIDEO_HEIGHT)\n',
    '''#define MAX_VIDEO_PIXELS (MAX_VIDEO_WIDTH * MAX_VIDEO_HEIGHT)

#define YELLOW_NATIVE_WIDTH 160
#define YELLOW_NATIVE_HEIGHT 144
#define YELLOW_VIEW_MARGIN_X 80
#define YELLOW_VIEW_MARGIN_Y 72
#define YELLOW_VIEW_WIDTH (YELLOW_NATIVE_WIDTH + YELLOW_VIEW_MARGIN_X * 2)
#define YELLOW_VIEW_HEIGHT (YELLOW_NATIVE_HEIGHT + YELLOW_VIEW_MARGIN_Y * 2)

#define YELLOW_W_FONT_LOADED 0xCFC3
#define YELLOW_W_IS_IN_BATTLE 0xD056
#define YELLOW_W_OVERWORLD_MAP 0xC6E8
#define YELLOW_W_OVERWORLD_MAP_END 0xCBFC
#define YELLOW_W_CURRENT_BLOCK_VIEW 0xD35E
#define YELLOW_W_Y_BLOCK_COORD 0xD362
#define YELLOW_W_X_BLOCK_COORD 0xD363
#define YELLOW_W_CUR_MAP 0xD35D
#define YELLOW_W_CUR_MAP_TILESET 0xD366
#define YELLOW_W_CUR_MAP_HEIGHT 0xD367
#define YELLOW_W_CUR_MAP_WIDTH 0xD368
#define YELLOW_W_MAP_VIEW_VRAM_POINTER 0xD525
#define YELLOW_W_TILESET_BANK 0xD52A
#define YELLOW_W_TILESET_BLOCKS_PTR 0xD52B
#define YELLOW_W_SPRITE_STATE_DATA1 0xC100
#define YELLOW_W_SPRITE_STATE_DATA2 0xC200
#define YELLOW_W_Y_COORD 0xD360
#define YELLOW_W_X_COORD 0xD361
#define YELLOW_W_NUM_SPRITES 0xD4E0
#define YELLOW_W_TOGGLEABLE_OBJECT_FLAGS 0xD5A5
#define YELLOW_W_TOGGLEABLE_OBJECT_LIST 0xD5CD

#define YELLOW_RUNNING_ENTRY_OFFSET 0x049D
#define YELLOW_RUNNING_ENTRY_SIZE 5
#define YELLOW_RUNNING_CAVE_OFFSET 0x3FEF
#define YELLOW_RUNNING_CAVE_SIZE 17
''',
    'yellow constants',
)

replace_once(
    '''static uint32_t *frame_buf = NULL;
static uint32_t *frame_buf_copy = NULL;
static uint32_t retained_frame_1[256 * 224];
''',
    '''static uint32_t *frame_buf = NULL;
static uint32_t *frame_buf_copy = NULL;

/* Pokemon Yellow expanded-overworld prototype. */
static bool pokemon_yellow_enhanced = false;
static uint32_t pokemon_yellow_frame[YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT];
static uint8_t pokemon_yellow_bg_color[YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT];
static uint8_t pokemon_yellow_bg_tile[YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT];
static uint8_t pokemon_yellow_bg_priority[YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT];
static uint8_t pokemon_yellow_object_pixel[YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT];
static bool pokemon_yellow_alignment_valid = false;
static uint8_t pokemon_yellow_alignment_map = 0;
static int pokemon_yellow_native_map_x = 0;
static int pokemon_yellow_native_map_y = 0;

static uint32_t retained_frame_1[256 * 224];
''',
    'yellow state',
)

replace_once(
    '    info->library_name     = "SameBoy";\n',
    '    info->library_name     = "Pokemon Yellow Expanded v0.3.3 Natural World";\n',
    'core name',
)

replace_once(
    '''    else {
        geom.base_width = GB_get_screen_width(&gameboy[0]);
        geom.base_height = GB_get_screen_height(&gameboy[0]);
        geom.aspect_ratio = (double)GB_get_screen_width(&gameboy[0]) / GB_get_screen_height(&gameboy[0]);
    }

    geom.max_width = MAX_VIDEO_WIDTH * emulated_devices;
    geom.max_height = MAX_VIDEO_HEIGHT * emulated_devices;
''',
    '''    else if (pokemon_yellow_enhanced) {
        geom.base_width = YELLOW_VIEW_WIDTH;
        geom.base_height = YELLOW_VIEW_HEIGHT;
        geom.aspect_ratio = (double)YELLOW_VIEW_WIDTH / YELLOW_VIEW_HEIGHT;
    }
    else {
        geom.base_width = GB_get_screen_width(&gameboy[0]);
        geom.base_height = GB_get_screen_height(&gameboy[0]);
        geom.aspect_ratio = (double)GB_get_screen_width(&gameboy[0]) / GB_get_screen_height(&gameboy[0]);
    }

    if (pokemon_yellow_enhanced && emulated_devices == 1) {
        geom.max_width = YELLOW_VIEW_WIDTH;
        geom.max_height = YELLOW_VIEW_HEIGHT;
    }
    else {
        geom.max_width = MAX_VIDEO_WIDTH * emulated_devices;
        geom.max_height = MAX_VIDEO_HEIGHT * emulated_devices;
    }
''',
    'AV geometry',
)

helper_anchor = '''void retro_run(void)
{
'''

helper_replacement = r'''static bool pokemon_yellow_is_rom(const uint8_t *data, size_t size)
{
    static const char title[] = "POKEMON YELLOW";
    return data && size >= 0x150 &&
           memcmp(data + 0x134, title, sizeof(title) - 1) == 0;
}

static bool pokemon_yellow_apply_running_patch(GB_gameboy_t *gb)
{
    static const uint8_t original_entry[YELLOW_RUNNING_ENTRY_SIZE] = {
        0xFA, 0xFF, 0xD6, 0x3D, 0xC0,
    };
    static const uint8_t running_entry[YELLOW_RUNNING_ENTRY_SIZE] = {
        0xC3, 0xEF, 0x3F, 0x00, 0x00, /* jp $3FEF */
    };
    static const uint8_t empty_cave[YELLOW_RUNNING_CAVE_SIZE] = {0};
    static const uint8_t running_cave[YELLOW_RUNNING_CAVE_SIZE] = {
        0xFA, 0xFF, 0xD6,       /* ld a, [wWalkBikeSurfState] */
        0x3D,                   /* dec a */
        0xCA, 0xA2, 0x04,       /* jp z, $04A2 (original bike path) */
        0x3C,                   /* inc a */
        0xC0,                   /* ret nz (surfing) */
        0xF0, 0xB4,             /* ldh a, [hJoyHeld] */
        0xCB, 0x4F,             /* bit 1, a (B button) */
        0xC8,                   /* ret z */
        0xC3, 0xA2, 0x04,       /* jp $04A2 */
    };

    if (!gb->rom || gb->rom_size < YELLOW_RUNNING_CAVE_OFFSET + YELLOW_RUNNING_CAVE_SIZE) {
        return false;
    }
    if (memcmp(gb->rom + YELLOW_RUNNING_ENTRY_OFFSET,
               running_entry,
               YELLOW_RUNNING_ENTRY_SIZE) == 0 &&
        memcmp(gb->rom + YELLOW_RUNNING_CAVE_OFFSET,
               running_cave,
               YELLOW_RUNNING_CAVE_SIZE) == 0) {
        return true;
    }
    if (memcmp(gb->rom + YELLOW_RUNNING_ENTRY_OFFSET,
               original_entry,
               YELLOW_RUNNING_ENTRY_SIZE) != 0 ||
        memcmp(gb->rom + YELLOW_RUNNING_CAVE_OFFSET,
               empty_cave,
               YELLOW_RUNNING_CAVE_SIZE) != 0) {
        return false;
    }
    memcpy(gb->rom + YELLOW_RUNNING_CAVE_OFFSET,
           running_cave,
           YELLOW_RUNNING_CAVE_SIZE);
    memcpy(gb->rom + YELLOW_RUNNING_ENTRY_OFFSET,
           running_entry,
           YELLOW_RUNNING_ENTRY_SIZE);
    return true;
}

static bool pokemon_yellow_should_expand(void)
{
    if (!pokemon_yellow_enhanced || emulated_devices != 1) {
        return false;
    }

    GB_gameboy_t *gb = &gameboy[0];
    /* WRAM is intentionally randomized while the CGB boot ROM is running.
     * On some devices those random bytes can accidentally resemble valid map
     * pointers. Never enter the expanded renderer until the boot ROM has
     * handed control to Pokemon Yellow. */
    if (!gb->boot_rom_finished) {
        return false;
    }
    if (!(gb->io_registers[GB_IO_LCDC] & GB_LCDC_ENABLE)) {
        return false;
    }
    if (GB_safe_read_memory(gb, YELLOW_W_IS_IN_BATTLE) != 0) {
        return false;
    }
    const uint8_t map_pointer_high =
        GB_safe_read_memory(gb, YELLOW_W_MAP_VIEW_VRAM_POINTER + 1);
    if (map_pointer_high < 0x98 || map_pointer_high > 0x9B) {
        return false;
    }

    const uint16_t block_view =
        GB_safe_read_memory(gb, YELLOW_W_CURRENT_BLOCK_VIEW) |
        (GB_safe_read_memory(gb, YELLOW_W_CURRENT_BLOCK_VIEW + 1) << 8);
    const uint16_t blocks_ptr =
        GB_safe_read_memory(gb, YELLOW_W_TILESET_BLOCKS_PTR) |
        (GB_safe_read_memory(gb, YELLOW_W_TILESET_BLOCKS_PTR + 1) << 8);
    const uint8_t map_tileset =
        GB_safe_read_memory(gb, YELLOW_W_CUR_MAP_TILESET);
    const uint8_t map_height =
        GB_safe_read_memory(gb, YELLOW_W_CUR_MAP_HEIGHT);
    const uint8_t map_width =
        GB_safe_read_memory(gb, YELLOW_W_CUR_MAP_WIDTH);
    const bool outdoor_tileset =
        map_tileset == 0 ||  /* OVERWORLD */
        map_tileset == 3 ||  /* FOREST */
        map_tileset == 14 || /* SHIP_PORT */
        map_tileset == 23;   /* PLATEAU */
    return block_view >= YELLOW_W_OVERWORLD_MAP &&
           block_view < YELLOW_W_OVERWORLD_MAP_END &&
           blocks_ptr >= 0x4000 && blocks_ptr < 0x8000 &&
           outdoor_tileset &&
           map_height > 0 && map_height < 0x40 &&
           map_width > 0 && map_width < 0x40;
}

static uint16_t pokemon_yellow_read16(GB_gameboy_t *gb, uint16_t address)
{
    return GB_safe_read_memory(gb, address) |
           (GB_safe_read_memory(gb, address + 1) << 8);
}

static int pokemon_yellow_floor_div32(int value)
{
    int quotient = value / 32;
    if (value < 0 && value % 32) quotient--;
    return quotient;
}

static int pokemon_yellow_mod32(int value)
{
    int remainder = value % 32;
    if (remainder < 0) remainder += 32;
    return remainder;
}

/*
 * Read a background pixel from Pokemon Yellow's real map-block buffer.
 * Unlike the hardware BG map, this buffer includes the whole current map and
 * its connected-map border, so pixels outside the 160x144 LCD are not stale.
 */
static bool pokemon_yellow_map_pixel(int map_x, int map_y,
                                    uint32_t *rgb, uint8_t *raw_color,
                                    uint8_t *tile_id)
{
    GB_gameboy_t *gb = &gameboy[0];
    const int block_x = pokemon_yellow_floor_div32(map_x);
    const int block_y = pokemon_yellow_floor_div32(map_y);
    const int pixel_x = pokemon_yellow_mod32(map_x);
    const int pixel_y = pokemon_yellow_mod32(map_y);
    const unsigned stride =
        GB_safe_read_memory(gb, YELLOW_W_CUR_MAP_WIDTH) + 6;
    const unsigned rows =
        GB_safe_read_memory(gb, YELLOW_W_CUR_MAP_HEIGHT) + 6;

    if (block_x < 0 || block_x >= (int)stride ||
        block_y < 0 || block_y >= (int)rows) {
        return false;
    }
    const unsigned block_offset = block_y * stride + block_x;
    if (block_offset >= YELLOW_W_OVERWORLD_MAP_END - YELLOW_W_OVERWORLD_MAP) {
        return false;
    }
    const uint8_t block = GB_safe_read_memory(
        gb, YELLOW_W_OVERWORLD_MAP + block_offset);

    const uint8_t tile_in_block =
        (pixel_y >> 3) * 4 + (pixel_x >> 3);
    const uint8_t bank = GB_safe_read_memory(gb, YELLOW_W_TILESET_BANK);
    const uint16_t blocks_ptr =
        pokemon_yellow_read16(gb, YELLOW_W_TILESET_BLOCKS_PTR);
    const uint32_t bank_address =
        (uint32_t)blocks_ptr + (uint32_t)block * 16 + tile_in_block;
    if (bank_address < 0x4000 || bank_address >= 0x8000) return false;

    const size_t rom_offset =
        (size_t)bank * 0x4000 + (bank_address - 0x4000);
    if (!gb->rom || rom_offset >= gb->rom_size) return false;
    const uint8_t tile = gb->rom[rom_offset];
    if (tile_id) *tile_id = tile;

    const uint8_t lcdc = gb->io_registers[GB_IO_LCDC];
    uint16_t tile_address;
    if (lcdc & GB_LCDC_TILE_SEL) {
        tile_address = tile * 16;
    }
    else {
        tile_address = (int8_t)tile * 16 + 0x1000;
    }

    const unsigned tile_x = pixel_x & 7;
    const unsigned tile_y = pixel_y & 7;
    const uint8_t lo = gb->vram[tile_address + tile_y * 2];
    const uint8_t hi = gb->vram[tile_address + tile_y * 2 + 1];
    const unsigned bit = 7 - tile_x;
    const uint8_t color =
        ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
    const uint8_t palette_color =
        (gb->io_registers[GB_IO_BGP] >> (color * 2)) & 3;
    if (raw_color) *raw_color = color;
    if (rgb) *rgb = gb->background_palettes_rgb[palette_color];
    return true;
}

static void pokemon_yellow_find_native_alignment(int *native_x, int *native_y)
{
    GB_gameboy_t *gb = &gameboy[0];
    const uint16_t block_view =
        pokemon_yellow_read16(gb, YELLOW_W_CURRENT_BLOCK_VIEW);
    const int stride =
        GB_safe_read_memory(gb, YELLOW_W_CUR_MAP_WIDTH) + 6;
    const int block_offset = block_view - YELLOW_W_OVERWORLD_MAP;
    const int block_x = block_offset % stride;
    const int block_y = block_offset / stride;
    const int approximate_x =
        block_x * 32 +
        (GB_safe_read_memory(gb, YELLOW_W_X_BLOCK_COORD) & 1) * 16;
    const int approximate_y =
        block_y * 32 +
        (GB_safe_read_memory(gb, YELLOW_W_Y_BLOCK_COORD) & 1) * 16;
    const uint8_t map = GB_safe_read_memory(gb, YELLOW_W_CUR_MAP);

    unsigned best_score = ~0u;
    unsigned best_distance = ~0u;
    int best_x = approximate_x;
    int best_y = approximate_y;
    const bool reuse_alignment =
        pokemon_yellow_alignment_valid && pokemon_yellow_alignment_map == map;
    int reference_x = reuse_alignment
        ? pokemon_yellow_native_map_x : approximate_x;
    int reference_y = reuse_alignment
        ? pokemon_yellow_native_map_y : approximate_y;
    /* Never allow the image matcher to wander away from the game's real map
     * pointer. Repetitive ground tiles can otherwise produce an equally good
     * match one block away, then let the alignment drift farther every frame. */
    if (reference_x < approximate_x - 24) reference_x = approximate_x - 24;
    if (reference_x > approximate_x + 24) reference_x = approximate_x + 24;
    if (reference_y < approximate_y - 24) reference_y = approximate_y - 24;
    if (reference_y > approximate_y + 24) reference_y = approximate_y + 24;
    const int search_radius = reuse_alignment ? 6 : 24;

    /* Match the reconstructed map against sparse pixels in the real LCD frame.
     * This handles the game's 2-pixel walking scroll without assuming that the
     * map buffer and LCD scroll register update on the same emulated frame. */
    for (int adjust_y = -search_radius;
         adjust_y <= search_radius;
         adjust_y++) {
        for (int adjust_x = -search_radius;
             adjust_x <= search_radius;
             adjust_x++) {
            const int candidate_x = reference_x + adjust_x;
            const int candidate_y = reference_y + adjust_y;
            if (candidate_x < approximate_x - 24 ||
                candidate_x > approximate_x + 24 ||
                candidate_y < approximate_y - 24 ||
                candidate_y > approximate_y + 24) {
                continue;
            }
            unsigned score = 0;
            unsigned samples = 0;

            for (unsigned y = 4; y < YELLOW_NATIVE_HEIGHT; y += 16) {
                for (unsigned x = 4; x < YELLOW_NATIVE_WIDTH; x += 16) {
                    if (x >= 52 && x < 108 && y >= 44 && y < 104) continue;
                    uint32_t background;
                    if (!pokemon_yellow_map_pixel(candidate_x + (int)x,
                                                  candidate_y + (int)y,
                                                  &background, NULL, NULL)) {
                        continue;
                    }
                    samples++;
                    if (background != frame_buf[y * YELLOW_NATIVE_WIDTH + x]) {
                        score++;
                    }
                }
            }
            if (!samples) continue;

            const unsigned distance =
                abs(candidate_x - reference_x) + abs(candidate_y - reference_y);
            if (score < best_score ||
                (score == best_score && distance < best_distance)) {
                best_score = score;
                best_distance = distance;
                best_x = candidate_x;
                best_y = candidate_y;
            }
        }
    }

    pokemon_yellow_alignment_valid = true;
    pokemon_yellow_alignment_map = map;
    pokemon_yellow_native_map_x = best_x;
    pokemon_yellow_native_map_y = best_y;
    *native_x = best_x;
    *native_y = best_y;
}

static void pokemon_yellow_render_background(void)
{
    int native_x;
    int native_y;
    pokemon_yellow_find_native_alignment(&native_x, &native_y);
    const int output_map_x = native_x - YELLOW_VIEW_MARGIN_X;
    const int output_map_y = native_y - YELLOW_VIEW_MARGIN_Y;

    for (unsigned out_y = 0; out_y < YELLOW_VIEW_HEIGHT; out_y++) {
        for (unsigned out_x = 0; out_x < YELLOW_VIEW_WIDTH; out_x++) {
            const unsigned output_offset = out_y * YELLOW_VIEW_WIDTH + out_x;
            uint8_t color = 0;
            uint8_t tile = 0;
            pokemon_yellow_bg_priority[output_offset] = 0;
            if (pokemon_yellow_map_pixel(output_map_x + (int)out_x,
                                         output_map_y + (int)out_y,
                                         &pokemon_yellow_frame[output_offset],
                                         &color, &tile)) {
                pokemon_yellow_bg_color[output_offset] = color;
                pokemon_yellow_bg_tile[output_offset] = tile;
            }
            else {
                pokemon_yellow_bg_color[output_offset] = 0;
                pokemon_yellow_bg_tile[output_offset] = 0;
            }
        }
    }
}

static bool pokemon_yellow_object_is_hidden(unsigned sprite_index)
{
    GB_gameboy_t *gb = &gameboy[0];
    for (unsigned offset = 0; offset < 32; offset += 2) {
        const uint8_t listed_sprite = GB_safe_read_memory(
            gb, YELLOW_W_TOGGLEABLE_OBJECT_LIST + offset);
        if (listed_sprite == 0xFF) return false;
        const uint8_t flag_index = GB_safe_read_memory(
            gb, YELLOW_W_TOGGLEABLE_OBJECT_LIST + offset + 1);
        if (listed_sprite != sprite_index) continue;
        return (GB_safe_read_memory(
                    gb, YELLOW_W_TOGGLEABLE_OBJECT_FLAGS + (flag_index >> 3)) &
                (1u << (flag_index & 7))) != 0;
    }
    return false;
}

static int pokemon_yellow_unwrap_coordinate(uint8_t raw, int expected)
{
    int value = raw;
    while (value - expected > 128) value -= 256;
    while (expected - value > 128) value += 256;
    return value;
}

static void pokemon_yellow_draw_state_tile(int base_x, int base_y,
                                           uint8_t tile, bool x_flip,
                                           bool under_grass)
{
    GB_gameboy_t *gb = &gameboy[0];
    const uint16_t tile_address = (uint16_t)tile * 16;
    for (unsigned draw_y = 0; draw_y < 8; draw_y++) {
        const int out_y = base_y + (int)draw_y;
        if (out_y < 0 || out_y >= YELLOW_VIEW_HEIGHT) continue;
        const uint8_t lo = gb->vram[tile_address + draw_y * 2];
        const uint8_t hi = gb->vram[tile_address + draw_y * 2 + 1];
        for (unsigned draw_x = 0; draw_x < 8; draw_x++) {
            const int out_x = base_x + (int)draw_x;
            if (out_x < 0 || out_x >= YELLOW_VIEW_WIDTH) continue;
            const unsigned source_x = x_flip ? 7 - draw_x : draw_x;
            const unsigned bit = 7 - source_x;
            uint8_t color =
                ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
            if (color == 0) continue;
            const unsigned output_offset =
                out_y * YELLOW_VIEW_WIDTH + out_x;
            if (under_grass && pokemon_yellow_bg_color[output_offset] != 0) {
                continue;
            }
            color = (gb->io_registers[GB_IO_OBP0] >> (color * 2)) & 3;
            pokemon_yellow_frame[output_offset] =
                gb->object_palettes_rgb[color];
            pokemon_yellow_object_pixel[output_offset] = 1;
        }
    }
}

/*
 * OAM only contains objects inside the original LCD-sized camera.  Yellow's
 * sprite state tables retain every object on the current map, including its
 * map coordinate, facing direction, animation frame and loaded VRAM slot.
 * Reconstruct those 16x16 sprites so people remain visible in the expanded
 * area instead of popping in at the old 160x144 boundary.
 */
static void pokemon_yellow_render_map_objects(void)
{
    GB_gameboy_t *gb = &gameboy[0];
    unsigned count = GB_safe_read_memory(gb, YELLOW_W_NUM_SPRITES);
    if (count > 14) count = 14;
    const uint8_t player_y = GB_safe_read_memory(gb, YELLOW_W_Y_COORD);
    const uint8_t player_x = GB_safe_read_memory(gb, YELLOW_W_X_COORD);

    for (unsigned sprite_index = 1; sprite_index <= count; sprite_index++) {
        const uint16_t state1 =
            YELLOW_W_SPRITE_STATE_DATA1 + sprite_index * 16;
        const uint16_t state2 =
            YELLOW_W_SPRITE_STATE_DATA2 + sprite_index * 16;
        const uint8_t picture_id = GB_safe_read_memory(gb, state1);
        const uint8_t image_base = GB_safe_read_memory(gb, state2 + 0x0E);
        if (!picture_id || !image_base ||
            pokemon_yellow_object_is_hidden(sprite_index)) {
            continue;
        }

        const uint8_t map_y = GB_safe_read_memory(gb, state2 + 4);
        const uint8_t map_x = GB_safe_read_memory(gb, state2 + 5);
        const int expected_y = (int8_t)(map_y - player_y) * 16 - 4;
        const int expected_x = (int8_t)(map_x - player_x) * 16;
        const int screen_y = pokemon_yellow_unwrap_coordinate(
            GB_safe_read_memory(gb, state1 + 4), expected_y);
        const int screen_x = pokemon_yellow_unwrap_coordinate(
            GB_safe_read_memory(gb, state1 + 6), expected_x);
        const int output_y = screen_y + YELLOW_VIEW_MARGIN_Y;
        const int output_x = screen_x + YELLOW_VIEW_MARGIN_X;
        if (output_x <= -16 || output_x >= YELLOW_VIEW_WIDTH ||
            output_y <= -16 || output_y >= YELLOW_VIEW_HEIGHT) {
            continue;
        }

        uint8_t image_index = GB_safe_read_memory(gb, state1 + 2);
        if (image_index == 0xFF) {
            const uint8_t facing = GB_safe_read_memory(gb, state1 + 9) & 0x0C;
            const uint8_t animation = GB_safe_read_memory(gb, state1 + 8) & 3;
            image_index = (uint8_t)(((image_base - 1) << 4) |
                                    facing | animation);
        }

        const uint8_t image_slot = image_index >> 4;
        const bool still_sprite = image_slot >= 0x0A;
        const uint8_t base_tile = image_slot == 0x0B
            ? 0x7C : (uint8_t)(image_slot * 12);
        const uint8_t pose = still_sprite ? 0 : image_index & 0x0F;
        const uint8_t direction = pose & 0x0C;
        const uint8_t animation = pose & 3;
        const bool walking = !still_sprite && (animation & 1);
        const bool x_flip = direction == 0x0C ||
            ((direction == 0 || direction == 4) && animation == 3);
        const uint8_t facing_tile =
            direction == 4 ? 4 : (direction == 8 || direction == 0x0C ? 8 : 0);
        const bool grass_priority =
            (GB_safe_read_memory(gb, state2 + 7) & 0x80) != 0;

        for (unsigned tile_y = 0; tile_y < 2; tile_y++) {
            for (unsigned tile_x = 0; tile_x < 2; tile_x++) {
                const unsigned source_x = x_flip ? 1 - tile_x : tile_x;
                const uint8_t tile = (uint8_t)(base_tile + facing_tile +
                    tile_y * 2 + source_x + (walking ? 0x80 : 0));
                pokemon_yellow_draw_state_tile(
                    output_x + tile_x * 8,
                    output_y + tile_y * 8,
                    tile,
                    x_flip,
                    grass_priority && tile_y == 1);
            }
        }
    }
}

static uint8_t pokemon_yellow_clamp_color(int value)
{
    if (value < 0) return 0;
    if (value > 255) return 255;
    return value;
}

static uint8_t pokemon_yellow_mix_channel(int original, int target)
{
    return pokemon_yellow_clamp_color((original * 2 + target * 3) / 5);
}

static uint32_t pokemon_yellow_natural_color(uint32_t color,
                                             uint8_t tile,
                                             bool object_pixel)
{
    static const uint8_t earth[4][3] = {
        {30, 34, 30}, {105, 73, 43}, {195, 151, 83}, {247, 239, 207},
    };
    static const uint8_t green[4][3] = {
        {22, 49, 31}, {43, 105, 54}, {105, 184, 79}, {232, 242, 190},
    };
    static const uint8_t water[4][3] = {
        {17, 45, 73}, {28, 96, 145}, {75, 174, 211}, {218, 242, 236},
    };
    static const uint8_t character[4][3] = {
        {27, 31, 29}, {104, 65, 43}, {225, 169, 58}, {250, 235, 193},
    };
    const int red = (color >> 16) & 0xFF;
    const int source_green = (color >> 8) & 0xFF;
    const int blue = color & 0xFF;
    const int luminance = (red * 54 + source_green * 183 + blue * 19) >> 8;
    const unsigned shade = luminance < 64 ? 0 :
                           luminance < 150 ? 1 :
                           luminance < 225 ? 2 : 3;
    const uint8_t (*palette)[3] = earth;

    if (object_pixel) {
        palette = character;
    }
    else if (tile == 0x14) { /* water in every tileset that contains it */
        palette = water;
    }
    else if (tile == 0x3D || tile == 0x52) { /* trees and tall grass */
        palette = green;
    }

    return (pokemon_yellow_mix_channel(red, palette[shade][0]) << 16) |
           (pokemon_yellow_mix_channel(source_green, palette[shade][1]) << 8) |
           pokemon_yellow_mix_channel(blue, palette[shade][2]);
}

static void pokemon_yellow_apply_natural_colors(void)
{
    for (unsigned pixel = 0;
         pixel < YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT;
         pixel++) {
        pokemon_yellow_frame[pixel] =
            pokemon_yellow_natural_color(
                pokemon_yellow_frame[pixel],
                pokemon_yellow_bg_tile[pixel],
                pokemon_yellow_object_pixel[pixel] != 0);
    }
}

static void pokemon_yellow_render_sprites(void)
{
    GB_gameboy_t *gb = &gameboy[0];
    if (!(gb->io_registers[GB_IO_LCDC] & GB_LCDC_OBJ_EN)) {
        return;
    }

    const unsigned sprite_height =
        (gb->io_registers[GB_IO_LCDC] & GB_LCDC_OBJ_SIZE) ? 16 : 8;

    /* Draw high OAM indexes first so lower indexes retain priority. */
    for (int object_index = 39; object_index >= 0; object_index--) {
        const uint8_t *object = gb->oam + object_index * 4;
        if (object[0] == 0 || object[0] >= 160 || object[1] == 0) {
            continue;
        }

        const int base_y = (int)object[0] - 16 + YELLOW_VIEW_MARGIN_Y;
        const int base_x = (int)object[1] - 8 + YELLOW_VIEW_MARGIN_X;
        const uint8_t flags = object[3];

        for (unsigned draw_y = 0; draw_y < sprite_height; draw_y++) {
            const int out_y = base_y + (int)draw_y;
            if (out_y < 0 || out_y >= YELLOW_VIEW_HEIGHT) continue;

            unsigned source_y = draw_y;
            if (flags & 0x40) source_y = sprite_height - 1 - source_y;
            uint8_t tile = object[2];
            if (sprite_height == 16) {
                tile &= 0xFE;
                tile += source_y >> 3;
            }

            uint16_t tile_address = tile * 16 + (source_y & 7) * 2;
            if (gb->cgb_mode && (flags & 0x08)) tile_address += 0x2000;
            const uint8_t lo = gb->vram[tile_address];
            const uint8_t hi = gb->vram[tile_address + 1];

            for (unsigned draw_x = 0; draw_x < 8; draw_x++) {
                const int out_x = base_x + (int)draw_x;
                if (out_x < 0 || out_x >= YELLOW_VIEW_WIDTH) continue;

                const unsigned source_x =
                    (flags & 0x20) ? 7 - draw_x : draw_x;
                const unsigned bit = 7 - source_x;
                uint8_t color =
                    ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
                if (color == 0) continue;

                const unsigned output_offset =
                    out_y * YELLOW_VIEW_WIDTH + out_x;
                if ((gb->io_registers[GB_IO_LCDC] & GB_LCDC_BG_EN) &&
                    pokemon_yellow_bg_color[output_offset] != 0 &&
                    ((flags & 0x80) || pokemon_yellow_bg_priority[output_offset])) {
                    continue;
                }

                if (gb->cgb_mode) {
                    pokemon_yellow_frame[output_offset] =
                        gb->object_palettes_rgb[(flags & 7) * 4 + color];
                }
                else {
                    const unsigned palette = (flags & 0x10) ? 1 : 0;
                    color =
                        (gb->io_registers[GB_IO_OBP0 + palette] >> (color * 2)) & 3;
                    pokemon_yellow_frame[output_offset] =
                        gb->object_palettes_rgb[palette * 4 + color];
                }
                pokemon_yellow_object_pixel[output_offset] = 1;
            }
        }
    }
}

static void pokemon_yellow_video_refresh(void)
{
    memset(pokemon_yellow_frame, 0, sizeof(pokemon_yellow_frame));
    memset(pokemon_yellow_object_pixel, 0,
           sizeof(pokemon_yellow_object_pixel));

    const bool expanded = pokemon_yellow_should_expand();
    if (expanded) {
        pokemon_yellow_render_background();
        pokemon_yellow_render_map_objects();
        pokemon_yellow_render_sprites();
    }

    /* Keep the hardware-rendered native view pixel-perfect in the center. */
    for (unsigned y = 0; y < YELLOW_NATIVE_HEIGHT; y++) {
        memcpy(pokemon_yellow_frame +
                   (y + YELLOW_VIEW_MARGIN_Y) * YELLOW_VIEW_WIDTH +
                   YELLOW_VIEW_MARGIN_X,
               frame_buf + y * YELLOW_NATIVE_WIDTH,
               YELLOW_NATIVE_WIDTH * sizeof(uint32_t));
    }

    if (expanded) {
        pokemon_yellow_apply_natural_colors();
    }

    video_cb(pokemon_yellow_frame,
             YELLOW_VIEW_WIDTH,
             YELLOW_VIEW_HEIGHT,
             YELLOW_VIEW_WIDTH * sizeof(uint32_t));
}

void retro_run(void)
{
'''

replace_once(helper_anchor, helper_replacement, 'yellow renderer helpers')

replace_once(
    '''    else {
        video_cb(frame_buf,
                 GB_get_screen_width(&gameboy[0]),
                 GB_get_screen_height(&gameboy[0]),
                 GB_get_screen_width(&gameboy[0]) * sizeof(uint32_t));
    }
''',
    '''    else if (pokemon_yellow_enhanced && emulated_devices == 1 &&
             GB_get_screen_width(&gameboy[0]) == YELLOW_NATIVE_WIDTH &&
             GB_get_screen_height(&gameboy[0]) == YELLOW_NATIVE_HEIGHT) {
        pokemon_yellow_video_refresh();
    }
    else {
        video_cb(frame_buf,
                 GB_get_screen_width(&gameboy[0]),
                 GB_get_screen_height(&gameboy[0]),
                 GB_get_screen_width(&gameboy[0]) * sizeof(uint32_t));
    }
''',
    'single-screen video output',
)

replace_once(
    '''    if (info) {
        content_data = (const uint8_t *)info->data;
        content_size = info->size;
        content_type = check_rom_header(content_data, content_size);
    }

    check_variables();
''',
    '''    pokemon_yellow_enhanced = false;
    pokemon_yellow_alignment_valid = false;
    if (info) {
        content_data = (const uint8_t *)info->data;
        content_size = info->size;
        content_type = check_rom_header(content_data, content_size);
        pokemon_yellow_enhanced = pokemon_yellow_is_rom(content_data, content_size);
    }

    check_variables();
''',
    'Pokemon Yellow detection',
)

replace_once(
    '''    for (int i = 0; i < emulated_devices; i++) {
        init_for_current_model(i);
        GB_load_rom_from_buffer(&gameboy[i], content_data, content_size);
    }

    bool achievements = true;
''',
    '''    for (int i = 0; i < emulated_devices; i++) {
        init_for_current_model(i);
        GB_load_rom_from_buffer(&gameboy[i], content_data, content_size);
        if (pokemon_yellow_enhanced &&
            !pokemon_yellow_apply_running_patch(&gameboy[i])) {
            log_cb(RETRO_LOG_WARN,
                   "Pokemon Yellow running patch signature did not match; expanded view remains enabled.\\n");
        }
    }

    bool achievements = true;
''',
    'running runtime patch',
)

path.write_text(src)
print(f"Patched {path}")
