#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libretro.h"

#define WIDTH 320
#define HEIGHT 288

static uint32_t frame[WIDTH * HEIGHT];
static unsigned frame_width;
static unsigned frame_height;
static uint16_t buttons;

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
            return true;
        case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:
            return true;
        default:
            return false;
    }
}

static void video(const void *data, unsigned width, unsigned height, size_t pitch)
{
    frame_width = width;
    frame_height = height;
    if (!data || width != WIDTH || height != HEIGHT) return;
    for (unsigned y = 0; y < HEIGHT; y++) {
        memcpy(frame + y * WIDTH,
               (const uint8_t *)data + y * pitch,
               WIDTH * sizeof(*frame));
    }
}

static size_t audio(const int16_t *data, size_t frames)
{
    (void)data;
    return frames;
}

static void input_poll(void) {}

static int16_t input_state(unsigned port, unsigned device,
                           unsigned index, unsigned id)
{
    (void)index;
    if (port != 0 || device != RETRO_DEVICE_JOYPAD) return 0;
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) return (int16_t)buttons;
    return id < 16 && (buttons & (1u << id));
}

static void run_frames(unsigned count, uint16_t held)
{
    buttons = held;
    for (unsigned i = 0; i < count; i++) retro_run();
    buttons = 0;
    retro_run();
}

static void tap(unsigned id)
{
    run_frames(3, (uint16_t)(1u << id));
    run_frames(5, 0);
}

static bool write_ppm(const char *path)
{
    FILE *output = fopen(path, "wb");
    if (!output) return false;
    fprintf(output, "P6\n%u %u\n255\n", frame_width, frame_height);
    for (unsigned y = 0; y < frame_height; y++) {
        for (unsigned x = 0; x < frame_width; x++) {
            const uint32_t color = frame[y * WIDTH + x];
            fputc((color >> 16) & 0xFF, output);
            fputc((color >> 8) & 0xFF, output);
            fputc(color & 0xFF, output);
        }
    }
    return fclose(output) == 0;
}

static bool expanded_border_has_map_pixels(void)
{
    unsigned non_black = 0;
    for (unsigned y = 0; y < HEIGHT; y++) {
        for (unsigned x = 0; x < WIDTH; x++) {
            const bool outside_native = x < 80 || x >= 240 ||
                                        y < 72 || y >= 216;
            if (outside_native && (frame[y * WIDTH + x] & 0xFFFFFF)) {
                non_black++;
            }
        }
    }
    return non_black > 1000;
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

    /* The pret debug build accepts Select at the title screen, then Down+A
     * chooses DEBUG and starts directly in Pallet Town. */
    run_frames(3000, (uint16_t)(1u << RETRO_DEVICE_ID_JOYPAD_SELECT));
    run_frames(120, 0);
    tap(RETRO_DEVICE_ID_JOYPAD_DOWN);
    tap(RETRO_DEVICE_ID_JOYPAD_A);
    run_frames(120, 0);
    for (unsigned prompt = 0; prompt < 8; prompt++) {
        run_frames(180, 0);
        tap(RETRO_DEVICE_ID_JOYPAD_DOWN);
        tap(RETRO_DEVICE_ID_JOYPAD_A);
    }
    for (unsigned dialogue = 0; dialogue < 30; dialogue++) {
        run_frames(60, 0);
        tap(RETRO_DEVICE_ID_JOYPAD_A);
    }
    run_frames(900, 0);

    if (frame_width != WIDTH || frame_height != HEIGHT) {
        fprintf(stderr, "unexpected video size: %ux%u\n",
                frame_width, frame_height);
        return 6;
    }
    if (!write_ppm(argv[2])) return 7;

    /* Menus and dialogue load Yellow's font. The expanded outdoor world must
     * remain rendered behind them instead of collapsing to the 160x144 LCD. */
    tap(RETRO_DEVICE_ID_JOYPAD_START);
    run_frames(30, 0);
    if (!expanded_border_has_map_pixels()) {
        fprintf(stderr, "expanded border vanished while font/menu was active\n");
        return 8;
    }
    tap(RETRO_DEVICE_ID_JOYPAD_B);

    retro_unload_game();
    retro_deinit();
    free(rom);
    printf("PASS: captured Pallet Town at %ux%u to %s\n",
           frame_width, frame_height, argv[2]);
    return 0;
}
