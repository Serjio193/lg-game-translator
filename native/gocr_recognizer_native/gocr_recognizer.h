#pragma once
#include <stddef.h>
#include <stdint.h>
#include "gocr_detector.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct GocrRecognizer GocrRecognizer;
typedef struct GocrFull GocrFull;
typedef struct {
    int32_t height, width, left_context, useful_width, right_context, step, blank;
} GocrRecognizerConfig;
typedef struct {
    double prepare_ms, invoke_ms, decode_ms, total_ms, margin;
    int32_t windows, normalized_width;
    char windows_sha256[65];
    const char* text;
} GocrRecognition;
typedef struct {
    GocrLine source;
    int32_t line_id, crop_width, crop_height;
    double rectify_ms;
    char crop_sha256[65];
    GocrRecognition recognition;
} GocrRecognizedLine;
typedef struct {
    GocrDetectorStats detector;
    double rectify_ms, recognizer_ms, total_ms;
} GocrFullStats;
int gocr_recognizer_abi(void);
GocrRecognizer* gocr_recognizer_create(const char* model,const char* labels,const char* runtime,
    int threads,const GocrRecognizerConfig*,char* error,size_t);
void gocr_recognizer_destroy(GocrRecognizer*);
const char* gocr_recognizer_error(GocrRecognizer*);
int gocr_recognizer_recognize(GocrRecognizer*,const uint8_t*,size_t,int,int,int,GocrRecognition*);
/* Debug exports do not run inference or affect normal execution. */
size_t gocr_recognizer_copy_windows(GocrRecognizer*,void*,size_t);
int gocr_rectify_rgb(const uint8_t*,size_t,int,int,const double*,uint8_t*,size_t,int*,int*);
GocrFull* gocr_full_create(GocrDetector*,GocrRecognizer*);
void gocr_full_destroy(GocrFull*);
const char* gocr_full_error(GocrFull*);
int gocr_full_ocr(GocrFull*,const uint8_t*,size_t,GocrRecognizedLine*,int,GocrFullStats*);
#ifdef __cplusplus
}
#endif
