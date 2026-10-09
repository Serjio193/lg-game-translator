/* Replay the current detector and PP-OCR crop path; no capture API is called. */
#define _POSIX_C_SOURCE 200809L
#include "text_detector.h"
#include "ppocr_dialogue.h"
#include "ppocr_pool.h"
#include "utils.h"
#include "log.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void string(const char* value)
{
    putchar('"');
    for (const unsigned char* p = (const unsigned char*)value; *p; ++p) {
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else if (*p < 32) printf("\\u%04x", *p);
        else putchar(*p);
    }
    putchar('"');
}

static void text(const char* tsv, char* result, size_t capacity)
{
    char copy[1024];
    size_t length = strnlen(tsv, sizeof(copy)-1);
    memcpy(copy, tsv, length); copy[length] = 0;
    size_t used = 0;
    char* saved = NULL;
    for (char* row = strtok_r(copy, "\n", &saved); row; row = strtok_r(NULL, "\n", &saved)) {
        if (strncmp(row, "5\t", 2)) continue;
        char* word = row;
        int count = 0;
        for (char* cursor = row; *cursor; ++cursor) {
            if (*cursor == '\t') { ++count; word = cursor+1; }
        }
        if (count != 11) continue;
        int size = snprintf(result+used, capacity-used, "%s%s", used ? " " : "", word);
        if (size < 0 || (size_t)size >= capacity-used) break;
        used += (size_t)size;
    }
}

int main(int argc, char** argv)
{
    if (argc != 3) return 2;
    int repeats = atoi(argv[2]);
    if (repeats < 1 || repeats > 20) return 2;
    FILE* file = fopen(argv[1], "rb");
    if (!file) return 1;
    char line[128];
    int width = 0, height = 0;
    if (!fgets(line, sizeof(line), file) || strcmp(line, "P6\n")
        || !fgets(line, sizeof(line), file) || sscanf(line, "%d %d", &width, &height) != 2
        || width != 1280 || height != 720
        || !fgets(line, sizeof(line), file) || strcmp(line, "255\n")) {
        fclose(file); return 1;
    }
    const size_t pixels = (size_t)width*height;
    unsigned char* rgb = malloc(pixels*3);
    unsigned char* gray = malloc(pixels);
    if (!rgb || !gray || fread(rgb, 3, pixels, file) != pixels) {
        fclose(file); free(rgb); free(gray); return 1;
    }
    fclose(file);
    log_init(); log_set_level(Warning);
    const char* root = "/media/developer/apps/usr/palm/applications/org.webosbrew.piccap/ppocr/";
    char path[512], param[512], model[512], dictionary[512];
    snprintf(path, sizeof(path), "%sPP_OCRv5_mobile_det", root);
    snprintf(param, sizeof(param), "%sPP_OCRv5_mobile_rec.ncnn.param", root);
    snprintf(model, sizeof(model), "%sPP_OCRv5_mobile_rec.ncnn.bin", root);
    snprintf(dictionary, sizeof(dictionary), "%sppocrv5_dict.txt", root);
    text_detector_t* detector = text_detector_create(path);
    ppocr_pool_t* pool = detector ? ppocr_pool_create(param, model, dictionary) : NULL;
    if (!pool) { text_detector_destroy(detector); free(rgb); free(gray); return 1; }
    printf("{\"mode\":\"CURRENT\",\"width\":1280,\"height\":720,\"samples\":[");
    bool success = true;
    for (int repeat = -1; repeat < repeats; ++repeat) {
        uint64_t start = getticks_us();
        for (size_t i = 0; i < pixels; ++i)
            gray[i] = (unsigned char)((77*rgb[i*3]+150*rgb[i*3+1]+29*rgb[i*3+2])>>8);
        uint64_t converted = getticks_us();
        text_region_t regions[PPOCR_BATCH_LIMIT];
        int count = text_detector_detect(detector, gray, width, height, regions, PPOCR_BATCH_LIMIT);
        if (count < 0) { success = false; break; }
        uint64_t detected = getticks_us();
        ppocr_result_t results[PPOCR_BATCH_LIMIT];
        bool skip[PPOCR_BATCH_LIMIT] = {0};
        ppocr_dialogue_run(detector, pool, gray, width, height, regions, count, skip, results);
        uint64_t finished = getticks_us();
        if (repeat < 0) continue;
        printf("%s{\"conversion_ms\":%.3f,\"detector_ms\":%.3f,"
            "\"recognizer_and_network_ms\":%.3f,\"ocr_ms\":%.3f,\"lines\":[",
            repeat ? "," : "", (converted-start)/1000.0, (detected-converted)/1000.0,
            (finished-detected)/1000.0, (finished-start)/1000.0);
        for (int i = 0; i < count; ++i) {
            char reading[1024] = {0}; text(results[i].tsv, reading, sizeof(reading));
            printf("%s{\"line_id\":\"%d\",\"text\":", i ? "," : "", i);
            string(reading);
            const text_region_t* r = &regions[i];
            printf(",\"source_quad\":[[%d,%d],[%d,%d],[%d,%d],[%d,%d]],\"status\":%d}",
                r->x,r->y,r->x+r->width,r->y,r->x+r->width,r->y+r->height,
                r->x,r->y+r->height,results[i].recognition);
        }
        printf("]}"); fflush(stdout);
    }
    printf("],\"complete\":%s}\n", success ? "true" : "false");
    ppocr_pool_destroy(pool); text_detector_destroy(detector); free(rgb); free(gray);
    return success ? 0 : 1;
}
