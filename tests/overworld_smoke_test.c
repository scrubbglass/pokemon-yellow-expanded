#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libretro.h"

static unsigned current_frame;
static unsigned last_width;
static unsigned last_height;
static uint32_t last_video[256 * 224];

static void log_message(enum retro_log_level level, const char *format, ...)
{
    (void)level;
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
}

static bool environment(unsigned command, void *data)
{
    switch (command) {
        case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
            ((struct retro_log_callback *)data)->log = log_message;
            return true;
        case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        case RETRO_ENVIRONMENT_SET_SUPPORT_ACHIEVEMENTS:
        case RETRO_ENVIRONMENT_SET_SUBSYSTEM_INFO:
        case RETRO_ENVIRONMENT_SET_MEMORY_MAPS:
        case RETRO_ENVIRONMENT_SET_GEOMETRY:
        case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:
            return true;
        default:
            return false;
    }
}

static void video(const void *data, unsigned width, unsigned height, size_t pitch)
{
    last_width = width;
    last_height = height;
    if (!data || width > 256 || height > 224) return;
    for (unsigned y = 0; y < height; y++) {
        memcpy(last_video + y * 256,
               (const uint8_t *)data + y * pitch,
               width * sizeof(uint32_t));
    }
}

static size_t audio(const int16_t *data, size_t frames)
{
    (void)data;
    return frames;
}

static void input_poll(void) {}

static bool pulse(unsigned first, unsigned period, unsigned held)
{
    return current_frame >= first &&
           ((current_frame - first) % period) < held;
}

static int16_t input_state(unsigned port, unsigned device,
                           unsigned index, unsigned id)
{
    (void)port;
    (void)device;
    (void)index;

    uint16_t buttons = 0;
    /* Select opens the debug menu from the debug ROM's title screen. */
    if (current_frame >= 2200 && current_frame < 3000 &&
        pulse(2200, 45, 2)) {
        buttons |= 1 << RETRO_DEVICE_ID_JOYPAD_SELECT;
    }
    /* Pick the DEBUG entry, then confirm it. */
    if (current_frame >= 3100 && current_frame < 3102) {
        buttons |= 1 << RETRO_DEVICE_ID_JOYPAD_DOWN;
    }
    if (current_frame >= 3130 && current_frame < 3132) {
        buttons |= 1 << RETRO_DEVICE_ID_JOYPAD_A;
    }
    /* Decline nicknames for the debug party and advance any remaining prompts. */
    if (current_frame >= 3200 && current_frame < 4500 &&
        pulse(3200, 30, 2)) {
        buttons |= 1 << RETRO_DEVICE_ID_JOYPAD_B;
    }
    if (current_frame >= 4900 && current_frame < 5250) {
        buttons |= 1 << RETRO_DEVICE_ID_JOYPAD_RIGHT;
    }
    if (current_frame >= 5300 && current_frame < 5500) {
        buttons |= 1 << RETRO_DEVICE_ID_JOYPAD_UP;
    }
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) return buttons;
    return (buttons >> id) & 1;
}

static void write_ppm(const char *path)
{
    FILE *file = fopen(path, "wb");
    if (!file) return;
    fprintf(file, "P6\n%u %u\n255\n", last_width, last_height);
    for (unsigned y = 0; y < last_height; y++) {
        for (unsigned x = 0; x < last_width; x++) {
            const uint32_t pixel = last_video[y * 256 + x];
            const uint8_t rgb[3] = {
                (uint8_t)(pixel >> 16),
                (uint8_t)(pixel >> 8),
                (uint8_t)pixel,
            };
            fwrite(rgb, 1, sizeof(rgb), file);
        }
    }
    fclose(file);
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s pokeyellow_debug.gbc output.ppm\n", argv[0]);
        return 2;
    }

    FILE *rom_file = fopen(argv[1], "rb");
    if (!rom_file) return 3;
    fseek(rom_file, 0, SEEK_END);
    const long rom_size = ftell(rom_file);
    rewind(rom_file);
    uint8_t *rom = malloc((size_t)rom_size);
    if (!rom || fread(rom, 1, (size_t)rom_size, rom_file) != (size_t)rom_size) {
        return 4;
    }
    fclose(rom_file);

    retro_set_environment(environment);
    retro_set_video_refresh(video);
    retro_set_audio_sample_batch(audio);
    retro_set_input_poll(input_poll);
    retro_set_input_state(input_state);
    retro_init();

    const struct retro_game_info game = {
        .path = argv[1],
        .data = rom,
        .size = (size_t)rom_size,
        .meta = NULL,
    };
    if (!retro_load_game(&game)) return 5;

    uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    const size_t ram_size = retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM);
    fprintf(stderr, "system RAM: %zu bytes\n", ram_size);

    bool reached_overworld = false;
    for (current_frame = 0; current_frame < 5600; current_frame++) {
        retro_run();
        if (current_frame && current_frame % 300 == 0) {
            char snapshot_path[64];
            snprintf(snapshot_path, sizeof(snapshot_path),
                     "/tmp/pokemon-yellow-frame-%04u.ppm", current_frame);
            write_ppm(snapshot_path);
            if (ram && ram_size > 0x1526) {
                fprintf(stderr,
                        "frame %u: map=%02x view=%02x%02x vram=%02x%02x\n",
                        current_frame, ram[0x135d], ram[0x135f], ram[0x135e],
                        ram[0x1526], ram[0x1525]);
            }
        }
        if (ram && ram_size > 0x1526) {
            const uint16_t view = ram[0x135e] | (ram[0x135f] << 8);
            if (view >= 0xC6E8 && view < 0xCBFC &&
                ram[0x1525] == 0x00 && ram[0x1526] >= 0x98) {
                reached_overworld = true;
            }
        }
    }

    write_ppm(argv[2]);
    retro_unload_game();
    retro_deinit();
    free(rom);

    if (!reached_overworld || last_width != 256 || last_height != 224) {
        fprintf(stderr, "FAIL: overworld=%d size=%ux%u\n",
                reached_overworld, last_width, last_height);
        return 6;
    }
    printf("PASS: reached overworld at %ux%u\n", last_width, last_height);
    return 0;
}
