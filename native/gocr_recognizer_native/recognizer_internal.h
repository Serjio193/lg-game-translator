#pragma once
#include "gocr_recognizer.h"
#include "tflite_runtime.h"
#include <string>
#include <vector>
struct GocrRecognizer {
    gocr::TfLiteApi api;
    GocrRecognizerConfig config;
    void* model=nullptr;
    void* interpreter=nullptr;
    const void* logits=nullptr;
    std::vector<std::string> labels;
    std::vector<uint8_t> debug_windows;
    std::string text, error;
    GocrRecognizer(const char*,const GocrRecognizerConfig&);
    ~GocrRecognizer();
    void setup(const char*,const char*,int);
    GocrRecognition recognize(const uint8_t*,int,int,int);
};
