#pragma once
#include "gocr_detector.h"
#include "tflite_runtime.h"
#include <vector>

namespace gocr {
void decode_head(TfLiteApi&,const void* tensor,int head,const GocrDetectorConfig&,
                 std::vector<GocrProposal>&);
}
