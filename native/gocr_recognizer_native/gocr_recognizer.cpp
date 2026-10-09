#include "recognizer_internal.h"
#include "image_ops.h"
#include "labels.h"
#include "sha256.h"
#include "unicode.h"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <stdexcept>

using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t) {
    return std::chrono::duration<double,std::milli>(Clock::now()-t).count();
}
GocrRecognizer::GocrRecognizer(const char* library,const GocrRecognizerConfig& c):api(library),config(c) {}
GocrRecognizer::~GocrRecognizer() {
    if (interpreter) api.InterpreterDelete(interpreter);
    if (model) api.ModelDelete(model);
}
void GocrRecognizer::setup(const char* path,const char* label_path,int threads) {
    if (threads<1 || threads>4) throw std::runtime_error("threads must be 1..4");
    if (config.height!=32 || config.width!=168 || config.left_context!=16 ||
        config.useful_width!=136 || config.right_context!=16 || config.step!=4 || config.blank!=1292)
        throw std::runtime_error("unchanged recognizer window contract required");
    labels=gocr::load_labels(label_path);
    model=api.ModelCreateFromFile(path);
    if (!model) throw std::runtime_error("cannot open original recognizer");
    std::unique_ptr<void,void(*)(void*)> options(api.InterpreterOptionsCreate(),api.InterpreterOptionsDelete);
    if (!options) throw std::runtime_error("cannot allocate TFLite options");
    api.InterpreterOptionsSetNumThreads(options.get(),threads);
    interpreter=api.InterpreterCreate(model,options.get());
    if (!interpreter || api.InterpreterAllocateTensors(interpreter))
        throw std::runtime_error("cannot allocate recognizer interpreter");
    if (api.InterpreterGetInputTensorCount(interpreter)!=1)
        throw std::runtime_error("recognizer input count mismatch");
    void* input=api.InterpreterGetInputTensor(interpreter,0);
    if (api.TensorType(input)!=3 || api.TensorNumDims(input)!=4 ||
        api.TensorDim(input,0)!=1 || api.TensorDim(input,1)!=32 ||
        api.TensorDim(input,2)!=168 || api.TensorDim(input,3)!=1)
        throw std::runtime_error("recognizer input contract mismatch");
    for (int i=0;i<api.InterpreterGetOutputTensorCount(interpreter);++i) {
        const void* tensor=api.InterpreterGetOutputTensor(interpreter,i);
        if (api.TensorNumDims(tensor)==3 && api.TensorDim(tensor,2)==config.blank+1) logits=tensor;
    }
    if (!logits || api.TensorType(logits)!=3 || api.TensorDim(logits,0)!=1 ||
        api.TensorDim(logits,1)!=42 || api.TensorByteSize(logits)!=42*1293)
        throw std::runtime_error("recognizer logits contract mismatch");
}
GocrRecognition GocrRecognizer::recognize(const uint8_t* crop,int w,int h,int channels) {
    auto start=Clock::now();
    GocrRecognition result{};
    auto gray=gocr::normalize_line(crop,w,h,channels);
    result.normalized_width=gray.width;
    result.prepare_ms=elapsed(start);
    debug_windows.clear();
    bool debug=std::getenv("GOCR_RECOGNIZER_DEBUG_WINDOWS")!=nullptr;
    gocr::Sha256 hash;
    std::string decoded;
    int previous=-1;
    double margin_sum=0;
    for (int x=0;x<gray.width;x+=config.useful_width) {
        auto prep=Clock::now();
        auto* input=static_cast<uint8_t*>(api.TensorData(api.InterpreterGetInputTensor(interpreter,0)));
        if (!input) throw std::runtime_error("input tensor not allocated");
        gocr::make_window(gray,x,input);
        hash.update(input,32*168);
        if (debug) debug_windows.insert(debug_windows.end(),input,input+32*168);
        result.prepare_ms+=elapsed(prep);
        auto invoked=Clock::now();
        if (api.InterpreterInvoke(interpreter)) throw std::runtime_error("recognizer Invoke failed");
        result.invoke_ms+=elapsed(invoked);
        auto decode=Clock::now();
        const auto* data=static_cast<const uint8_t*>(api.TensorData(logits));
        if (!data) throw std::runtime_error("logits not allocated");
        int ids[42];
        int gaps=0;
        // Scalar positive affine dequantization leaves argmax unchanged. Work
        // directly on uint8 logits, exactly as the existing Python decoder.
        for (int t=0;t<42;++t) {
            int best=-1,second=-1,id=0;
            for (int j=0;j<1293;++j) {
                int value=data[t*1293+j];
                if (value>best) { second=best; best=value; id=j; }
                else if (value>second) second=value;
            }
            ids[t]=id; gaps+=best-second;
        }
        margin_sum+=double(gaps)/42;
        int keep=std::min(config.useful_width/config.step,(gray.width-x+config.step-1)/config.step);
        for (int i=config.left_context/config.step;i<config.left_context/config.step+keep;++i) {
            int id=ids[i];
            if (id!=previous && id!=config.blank) decoded+=labels.at(size_t(id));
            previous=id;
        }
        ++result.windows;
        result.decode_ms+=elapsed(decode);
    }
    auto decode=Clock::now();
    text=gocr::nfc_strip(decoded);
    result.text=text.c_str();
    result.margin=result.windows ? margin_sum/result.windows : 0;
    auto digest=hash.finish();
    std::memcpy(result.windows_sha256,digest.c_str(),65);
    result.decode_ms+=elapsed(decode);
    result.total_ms=elapsed(start);
    return result;
}
#define API extern "C" __attribute__((visibility("default")))
API int gocr_recognizer_abi() { return 1; }
API GocrRecognizer* gocr_recognizer_create(const char* model,const char* labels,const char* runtime,
    int threads,const GocrRecognizerConfig* cfg,char* error,size_t capacity) {
    try {
        if (!model || !labels || !runtime || !cfg) throw std::runtime_error("invalid recognizer arguments");
        auto rec=std::make_unique<GocrRecognizer>(runtime,*cfg);
        rec->setup(model,labels,threads);
        return rec.release();
    } catch (const std::exception& exc) {
        if (error && capacity) std::snprintf(error,capacity,"%s",exc.what());
        return nullptr;
    }
}
API void gocr_recognizer_destroy(GocrRecognizer* rec) { delete rec; }
API const char* gocr_recognizer_error(GocrRecognizer* rec) { return rec ? rec->error.c_str() : "null recognizer"; }
API int gocr_recognizer_recognize(GocrRecognizer* rec,const uint8_t* crop,size_t bytes,
    int w,int h,int channels,GocrRecognition* result) {
    if (!rec || !result) return -1;
    try {
        if (w<=0 || h<=0 || w>100000 || h>100000 || (channels!=1 && channels!=3) ||
            bytes!=size_t(w)*h*channels) throw std::runtime_error("invalid crop buffer");
        *result=rec->recognize(crop,w,h,channels);
        return 0;
    } catch (const std::exception& exc) { rec->error=exc.what(); return -1; }
}
API size_t gocr_recognizer_copy_windows(GocrRecognizer* rec,void* output,size_t capacity) {
    if (!rec) return 0;
    size_t size=rec->debug_windows.size();
    if (output && capacity>=size) std::memcpy(output,rec->debug_windows.data(),size);
    return size;
}
API int gocr_rectify_rgb(const uint8_t* rgb,size_t bytes,int w,int h,const double* quad,
    uint8_t* output,size_t capacity,int* ow,int* oh) {
    try {
        if (w<=0 || h<=0 || bytes!=size_t(w)*h*3 || !quad || !ow || !oh) return -1;
        auto crop=gocr::rectify(rgb,w,h,quad);
        *ow=crop.width; *oh=crop.height;
        if (output && capacity<crop.pixels.size()) return -1;
        if (output) std::memcpy(output,crop.pixels.data(),crop.pixels.size());
        return int(crop.pixels.size());
    } catch (...) { return -1; }
}
