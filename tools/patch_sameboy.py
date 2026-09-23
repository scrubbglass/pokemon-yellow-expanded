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
#define YELLOW_VIEW_MARGIN 16
#define YELLOW_VIEW_WIDTH (YELLOW_NATIVE_WIDTH + YELLOW_VIEW_MARGIN * 2)
#define YELLOW_VIEW_HEIGHT (YELLOW_NATIVE_HEIGHT + YELLOW_VIEW_MARGIN * 2)

#define YELLOW_W_FONT_LOADED 0xCFC3
#define YELLOW_W_IS_IN_BATTLE 0xD056
#define YELLOW_W_MAP_VIEW_VRAM_POINTER 0xD525

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
static uint8_t pokemon_yellow_bg_priority[YELLOW_VIEW_WIDTH * YELLOW_VIEW_HEIGHT];

static uint32_t retained_frame_1[256 * 224];
''',
    'yellow state',
)

replace_once(
    '    info->library_name     = "SameBoy";\n',
    '    info->library_name     = "Pokemon Yellow Expanded v0.1 Running View";\n',
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
    if (!(gb->io_registers[GB_IO_LCDC] & GB_LCDC_ENABLE)) {
        return false;
    }
    if (GB_safe_read_memory(gb, YELLOW_W_IS_IN_BATTLE) != 0) {
        return false;
    }
    if (GB_safe_read_memory(gb, YELLOW_W_FONT_LOADED) & 1) {
        return false;
    }

    const uint8_t map_pointer_high =
        GB_safe_read_memory(gb, YELLOW_W_MAP_VIEW_VRAM_POINTER + 1);
    return map_pointer_high >= 0x98 && map_pointer_high <= 0x9B;
}

static void pokemon_yellow_render_background(void)
{
    GB_gameboy_t *gb = &gameboy[0];
    const uint8_t lcdc = gb->io_registers[GB_IO_LCDC];
    const uint8_t scx = gb->io_registers[GB_IO_SCX];
    const uint8_t scy = gb->io_registers[GB_IO_SCY];
    const uint16_t map = (lcdc & GB_LCDC_BG_MAP) ? 0x1C00 : 0x1800;

    for (unsigned out_y = 0; out_y < YELLOW_VIEW_HEIGHT; out_y++) {
        const uint8_t world_y = (uint8_t)(scy + (int)out_y - YELLOW_VIEW_MARGIN);
        for (unsigned out_x = 0; out_x < YELLOW_VIEW_WIDTH; out_x++) {
            const uint8_t world_x = (uint8_t)(scx + (int)out_x - YELLOW_VIEW_MARGIN);
            const unsigned tile_map_offset =
                map + (world_y >> 3) * 32 + (world_x >> 3);
            const uint8_t tile = gb->vram[tile_map_offset];
            const uint8_t attributes = gb->cgb_mode
                ? gb->vram[0x2000 + tile_map_offset] : 0;

            uint16_t tile_address;
            if (lcdc & GB_LCDC_TILE_SEL) {
                tile_address = tile * 16;
            }
            else {
                tile_address = (int8_t)tile * 16 + 0x1000;
            }
            if (attributes & 0x08) {
                tile_address += 0x2000;
            }

            unsigned tile_x = world_x & 7;
            unsigned tile_y = world_y & 7;
            if (attributes & 0x20) tile_x ^= 7;
            if (attributes & 0x40) tile_y ^= 7;

            const uint8_t lo = gb->vram[tile_address + tile_y * 2];
            const uint8_t hi = gb->vram[tile_address + tile_y * 2 + 1];
            const unsigned bit = 7 - tile_x;
            uint8_t color = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
            const unsigned output_offset = out_y * YELLOW_VIEW_WIDTH + out_x;

            pokemon_yellow_bg_color[output_offset] = color;
            pokemon_yellow_bg_priority[output_offset] =
                (attributes & 0x80) != 0;

            if (gb->cgb_mode) {
                pokemon_yellow_frame[output_offset] =
                    gb->background_palettes_rgb[(attributes & 7) * 4 + color];
            }
            else {
                color = (gb->io_registers[GB_IO_BGP] >> (color * 2)) & 3;
                pokemon_yellow_frame[output_offset] =
                    gb->background_palettes_rgb[color];
            }
        }
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

        const int base_y = (int)object[0] - 16 + YELLOW_VIEW_MARGIN;
        const int base_x = (int)object[1] - 8 + YELLOW_VIEW_MARGIN;
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
            }
        }
    }
}

static void pokemon_yellow_video_refresh(void)
{
    memset(pokemon_yellow_frame, 0, sizeof(pokemon_yellow_frame));

    if (pokemon_yellow_should_expand()) {
        pokemon_yellow_render_background();
        pokemon_yellow_render_sprites();
    }

    /* Keep the hardware-rendered native view pixel-perfect in the center. */
    for (unsigned y = 0; y < YELLOW_NATIVE_HEIGHT; y++) {
        memcpy(pokemon_yellow_frame +
                   (y + YELLOW_VIEW_MARGIN) * YELLOW_VIEW_WIDTH +
                   YELLOW_VIEW_MARGIN,
               frame_buf + y * YELLOW_NATIVE_WIDTH,
               YELLOW_NATIVE_WIDTH * sizeof(uint32_t));
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
