#pragma once
#include <stddef.h>
#include <stdint.h>
#include "gocr_postprocess.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct GocrDetector GocrDetector;
/* Read via existing detector_config.py. Profile/head mappings are the unchanged
 * Python reference contract. No configuration inferred from proposals. */
typedef struct {
    int32_t limits[4], sources[11], strides[11];
    double anchors[11], confidence_threshold, anchor_x, anchor_y;
    GocrPostprocessConfig postprocess;
} GocrDetectorConfig;
typedef struct {
    double prepare_ms, invoke_ms, decode_ms, postprocess_ms, total_ms;
    GocrStats grouping;
    int32_t raw_pieces, raw_groups;
} GocrDetectorStats;
int gocr_detector_abi(void);
GocrDetector* gocr_detector_create(const char* model, const char* runtime,
    int threads, int xnnpack, const GocrDetectorConfig* config, char* error, size_t error_capacity);
void gocr_detector_destroy(GocrDetector*);
const char* gocr_detector_error(GocrDetector*);
const char* gocr_detector_version(GocrDetector*);
int gocr_detector_prepare(GocrDetector*, const uint8_t* rgb, size_t bytes);
int gocr_detector_invoke(GocrDetector*);
int gocr_detector_finish(GocrDetector*, GocrLine*, int capacity, GocrDetectorStats*);
int gocr_detector_detect(GocrDetector*, const uint8_t*, size_t, GocrLine*, int, GocrDetectorStats*);
/* Debug export only; hot path reads output tensor memory directly. */
size_t gocr_detector_copy_input(GocrDetector*, int ordinal, void*, size_t);
size_t gocr_detector_copy_output(GocrDetector*, int head, void*, size_t);
int gocr_detector_copy_proposals(GocrDetector*, GocrProposal*, int capacity);
#ifdef __cplusplus
}
#endif
