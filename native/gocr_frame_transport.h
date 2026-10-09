#pragma once
#include <stdbool.h>
#include <stdint.h>

bool gocr_selected_frame_enabled(void);
int gocr_submit_selected_rgb(const uint8_t* rgb, int width, int height,
    uint64_t sequence, uint64_t captured_ms);
