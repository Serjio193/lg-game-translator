#include "recognizer_internal.h"
#include "image_ops.h"
#include "sha256.h"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <stdexcept>

struct GocrFull {
    GocrDetector* detector;
    GocrRecognizer* recognizer;
    std::vector<GocrLine> detections;
    std::vector<std::string> texts;
    std::string error;
    GocrFull(GocrDetector* d,GocrRecognizer* r):detector(d),recognizer(r),detections(4096) {}
};
using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t) {
    return std::chrono::duration<double,std::milli>(Clock::now()-t).count();
}
static std::pair<double,double> origin(const GocrLine& l) {
    double x=l.quad[0],y=l.quad[1];
    for (int k=1;k<4;++k) { x=std::min(x,l.quad[2*k]); y=std::min(y,l.quad[2*k+1]); }
    return {y,x};
}
#define API extern "C" __attribute__((visibility("default")))
API GocrFull* gocr_full_create(GocrDetector* d,GocrRecognizer* r) {
    try { return d && r ? new GocrFull(d,r) : nullptr; } catch (...) { return nullptr; }
}
API void gocr_full_destroy(GocrFull* full) { delete full; }
API const char* gocr_full_error(GocrFull* f) { return f ? f->error.c_str() : "null full worker"; }
API int gocr_full_ocr(GocrFull* f,const uint8_t* rgb,size_t bytes,
    GocrRecognizedLine* output,int capacity,GocrFullStats* stats) {
    if (!f || !output || capacity<0 || !stats) return -1;
    try {
        auto start=Clock::now();
        *stats={};
        int count=gocr_detector_detect(f->detector,rgb,bytes,f->detections.data(),
            int(f->detections.size()),&stats->detector);
        if (count<0) throw std::runtime_error(gocr_detector_error(f->detector));
        if (count>capacity) throw std::runtime_error("full output capacity exceeded");
        std::stable_sort(f->detections.begin(),f->detections.begin()+count,
            [](const GocrLine& a,const GocrLine& b){return origin(a)<origin(b);});
        f->texts.clear(); f->texts.reserve(size_t(count));
        int accepted=0;
        for (int i=0;i<count;++i) {
            const auto& source=f->detections[i];
            double x2=source.quad[0],y2=source.quad[1];
            for (int k=1;k<4;++k) { x2=std::max(x2,source.quad[2*k]); y2=std::max(y2,source.quad[2*k+1]); }
            auto top=origin(source);
            if (x2<=0 || y2<=0 || top.second>=1280 || top.first>=720) continue;
            auto t=Clock::now();
            auto crop=gocr::rectify(rgb,1280,720,source.quad);
            GocrRecognizedLine result{};
            result.source=source; result.line_id=i;
            result.crop_width=crop.width; result.crop_height=crop.height;
            result.rectify_ms=elapsed(t); stats->rectify_ms+=result.rectify_ms;
            // Same diagnostic fingerprint header as image_contract.py.
            std::string header="RGB:"+std::to_string(crop.width)+":"+std::to_string(crop.height)+":";
            gocr::Sha256 hash; hash.update(header.data(),header.size());
            hash.update(crop.pixels.data(),crop.pixels.size());
            auto digest=hash.finish(); std::memcpy(result.crop_sha256,digest.c_str(),65);
            result.recognition=f->recognizer->recognize(crop.pixels.data(),crop.width,crop.height,3);
            f->texts.emplace_back(result.recognition.text);
            stats->recognizer_ms+=result.recognition.total_ms;
            output[accepted++]=result;
        }
        for (int i=0;i<accepted;++i) output[i].recognition.text=f->texts[size_t(i)].c_str();
        stats->total_ms=elapsed(start);
        return accepted;
    } catch (const std::exception& exc) { f->error=exc.what(); return -1; }
}
