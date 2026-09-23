#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "libretro.h"

static unsigned video_frames;
static unsigned last_width;
static unsigned last_height;

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
    (void)data;
    (void)pitch;
    video_frames++;
    last_width = width;
    last_height = height;
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
    (void)port;
    (void)device;
    (void)index;
    (void)id;
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s pokeyellow.gbc\n", argv[0]);
        return 2;
    }

    FILE *rom_file = fopen(argv[1], "rb");
    if (!rom_file) return 3;
    fseek(rom_file, 0, SEEK_END);
    long rom_size = ftell(rom_file);
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

    struct retro_game_info game = {
        .path = argv[1],
        .data = rom,
        .size = (size_t)rom_size,
        .meta = NULL,
    };
    if (!retro_load_game(&game)) {
        fprintf(stderr, "retro_load_game failed\n");
        return 5;
    }

    struct retro_system_av_info av;
    retro_get_system_av_info(&av);
    if (av.geometry.base_width != 256 || av.geometry.base_height != 224) {
        fprintf(stderr, "unexpected geometry: %ux%u\n",
                av.geometry.base_width, av.geometry.base_height);
        return 6;
    }

    for (unsigned frame = 0; frame < 180; frame++) retro_run();
    if (video_frames == 0 || last_width != 256 || last_height != 224) {
        fprintf(stderr, "unexpected video: frames=%u size=%ux%u\n",
                video_frames, last_width, last_height);
        return 7;
    }

    retro_unload_game();
    retro_deinit();
    free(rom);
    printf("PASS: %u frames at %ux%u\n", video_frames, last_width, last_height);
    return 0;
}
