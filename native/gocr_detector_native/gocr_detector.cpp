#include "gocr_detector.h"
#include "decode.h"
#include "preprocess.h"
#include "profiler.h"
#include "tflite_runtime.h"
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point start) {
    return std::chrono::duration<double,std::milli>(Clock::now()-start).count();
}

struct GocrDetector {
    gocr::TfLiteApi api;
    GocrDetectorConfig config;
    void* model=nullptr;
    void* interpreter=nullptr;
    void* delegate=nullptr;
    std::array<gocr::PyramidBranch,4> branches;
    std::array<const void*,11> heads{};
    std::vector<uint8_t> gray;
    std::vector<GocrProposal> proposals;
    std::vector<int32_t> membership;
    std::unique_ptr<gocr::OpProfiler> profiler;
    GocrDetectorStats stats{};
    std::string error;
    bool prepared=false, invoked=false;

    GocrDetector(const char* library,const GocrDetectorConfig& cfg):api(library),config(cfg) {}
    ~GocrDetector() {
        if (interpreter) api.InterpreterDelete(interpreter);
        if (delegate) api.XNNPackDelegateDelete(delegate);
        if (model) api.ModelDelete(model);
    }
    void setup(const char* path,int threads,bool xnnpack) {
        if (threads<1 || threads>4) throw std::runtime_error("threads must be 1..4");
        for (int i=0;i<11;++i)
            if (config.sources[i]<0 || config.sources[i]>=4 || config.strides[i]<=0 ||
                !std::isfinite(config.anchors[i]) || config.anchors[i]<=0)
                throw std::runtime_error("invalid detector launch config");
        if (!std::isfinite(config.confidence_threshold) || !std::isfinite(config.anchor_x) ||
            !std::isfinite(config.anchor_y)) throw std::runtime_error("invalid detector config");
        model=api.ModelCreateFromFile(path);
        if (!model) throw std::runtime_error("cannot open original Google model");
        std::unique_ptr<void,void(*)(void*)> options(api.InterpreterOptionsCreate(),api.InterpreterOptionsDelete);
        if (!options) throw std::runtime_error("cannot allocate TFLite options");
        api.InterpreterOptionsSetNumThreads(options.get(),threads);
        const char* profile_path=std::getenv("GOCR_DETECTOR_PROFILE");
        if (profile_path && *profile_path) {
            if (!api.InterpreterOptionsSetTelemetryProfiler || std::string(api.Version())!="2.17.0") {
                throw std::runtime_error("selected runtime lacks supported telemetry ABI");
            }
            profiler=std::make_unique<gocr::OpProfiler>(profile_path);
            api.InterpreterOptionsSetTelemetryProfiler(options.get(),&profiler->callbacks);
        }
        interpreter=api.InterpreterCreate(model,options.get());
        if (!interpreter) throw std::runtime_error("cannot create TFLite interpreter");
        if (api.InterpreterGetInputTensorCount(interpreter)!=4 ||
            api.InterpreterGetOutputTensorCount(interpreter)!=11)
            throw std::runtime_error("original Google input/output count mismatch");
        for (int i=0;i<4;++i) {
            branches[i].configure(config.limits[i]);
            int dims[4]={1,branches[i].tensor_height,branches[i].tensor_width,1};
            if (api.InterpreterResizeInputTensor(interpreter,i,dims,4))
                throw std::runtime_error("original input resize failed");
        }
        if (api.InterpreterAllocateTensors(interpreter))
            throw std::runtime_error("original tensor allocation failed");
        if (xnnpack) {
            if (!api.XNNPackDelegateCreate || !api.XNNPackDelegateOptionsDefault ||
                !api.XNNPackDelegateDelete || !api.InterpreterModifyGraphWithDelegate)
                throw std::runtime_error("XNNPACK API unavailable in selected runtime");
            // Exact options layout is TFLite 2.17. No FP16/quantization changes.
            if (std::string(api.Version())!="2.17.0")
                throw std::runtime_error("explicit XNNPACK ABI requires runtime 2.17.0");
            auto opts=api.XNNPackDelegateOptionsDefault();
            opts.num_threads=threads;
            delegate=api.XNNPackDelegateCreate(&opts);
            if (!delegate || api.InterpreterModifyGraphWithDelegate(interpreter,delegate))
                throw std::runtime_error("explicit XNNPACK delegate application failed");
        }
        for (int i=0;i<11;++i) {
            const void* tensor=api.InterpreterGetOutputTensor(interpreter,i);
            const char* name=api.TensorName(tensor);
            for (int head=0;head<11;++head) {
                std::string expected=head ? "Identity_"+std::to_string(head) : "Identity";
                if (name && expected==name) heads[head]=tensor;
            }
        }
        for (const void* head:heads)
            if (!head) throw std::runtime_error("missing original Google output head");
        proposals.reserve(2048);
    }
};

#define API extern "C" __attribute__((visibility("default")))
API int gocr_detector_abi() { return 1; }
API GocrDetector* gocr_detector_create(const char* model,const char* runtime,int threads,
    int xnnpack,const GocrDetectorConfig* config,char* error,size_t error_capacity) {
    try {
        if (!model || !runtime || !config || (xnnpack!=0 && xnnpack!=1))
            throw std::runtime_error("invalid detector creation arguments");
        auto detector=std::make_unique<GocrDetector>(runtime,*config);
        detector->setup(model,threads,xnnpack!=0);
        return detector.release();
    } catch (const std::exception& exc) {
        if (error && error_capacity) std::snprintf(error,error_capacity,"%s",exc.what());
        return nullptr;
    }
}
API void gocr_detector_destroy(GocrDetector* d) { delete d; }
API const char* gocr_detector_error(GocrDetector* d) {
    return d ? d->error.c_str() : "null detector";
}
API const char* gocr_detector_version(GocrDetector* d) {
    return d ? d->api.Version() : "";
}
API int gocr_detector_prepare(GocrDetector* d,const uint8_t* rgb,size_t bytes) {
    if (!d) return -1;
    try {
        d->prepared=false;
        d->invoked=false;
        if (!rgb || bytes!=1280*720*3) throw std::runtime_error("selected RGB frame contract mismatch");
        auto start=Clock::now();
        d->stats={};
        gocr::grayscale(rgb,d->gray);
        for (int i=0;i<4;++i) {
            void* tensor=d->api.InterpreterGetInputTensor(d->interpreter,i);
            const auto& b=d->branches[i];
            if (d->api.TensorType(tensor)!=3 ||
                d->api.TensorByteSize(tensor)!=size_t(b.tensor_width)*b.tensor_height)
                throw std::runtime_error("original uint8 input contract mismatch");
            auto* data=static_cast<uint8_t*>(d->api.TensorData(tensor));
            if (!data) throw std::runtime_error("input tensor not allocated");
            d->branches[i].fill(d->gray,data);
        }
        d->stats.prepare_ms=elapsed(start);
        d->prepared=true;
        return 0;
    } catch (const std::exception& exc) { d->error=exc.what(); return -1; }
}
API int gocr_detector_invoke(GocrDetector* d) {
    if (!d || !d->prepared) return -1;
    auto start=Clock::now();
    if (d->api.InterpreterInvoke(d->interpreter)) {
        d->error="original Google inference failed";
        d->invoked=false;
        return -1;
    }
    d->stats.invoke_ms=elapsed(start);
    d->invoked=true;
    return 0;
}
API int gocr_detector_finish(GocrDetector* d,GocrLine* output,int capacity,GocrDetectorStats* stats) {
    if (!d || !d->invoked || !stats) return -1;
    try {
        auto start=Clock::now();
        d->proposals.clear();
        for (int i=0;i<11;++i) {
            gocr::decode_head(d->api,d->heads[i],i,d->config,d->proposals);
            if (i==5) d->stats.raw_pieces=int32_t(d->proposals.size());
        }
        d->stats.raw_groups=int32_t(d->proposals.size())-d->stats.raw_pieces;
        d->stats.decode_ms=elapsed(start);
        d->membership.resize(d->proposals.size());
        start=Clock::now();
        int count=gocr_postprocess(d->proposals.data(),int(d->proposals.size()),&d->config.postprocess,
            output,capacity,d->membership.data(),&d->stats.grouping);
        if (count<0) throw std::runtime_error("native postprocess failed: "+std::to_string(count));
        d->stats.postprocess_ms=elapsed(start);
        d->stats.total_ms=d->stats.prepare_ms+d->stats.invoke_ms+d->stats.decode_ms+d->stats.postprocess_ms;
        *stats=d->stats;
        return count;
    } catch (const std::exception& exc) { d->error=exc.what(); return -1; }
}
API int gocr_detector_detect(GocrDetector* d,const uint8_t* rgb,size_t bytes,
    GocrLine* output,int capacity,GocrDetectorStats* stats) {
    if (gocr_detector_prepare(d,rgb,bytes) || gocr_detector_invoke(d)) return -1;
    return gocr_detector_finish(d,output,capacity,stats);
}
static size_t copy_tensor(GocrDetector* d,const void* tensor,void* output,size_t capacity) {
    if (!d || !tensor) return 0;
    size_t bytes=d->api.TensorByteSize(tensor);
    if (output && capacity>=bytes && d->api.TensorData(tensor))
        std::memcpy(output,d->api.TensorData(tensor),bytes);
    return bytes;
}
API size_t gocr_detector_copy_input(GocrDetector* d,int i,void* output,size_t capacity) {
    if (!d || i<0 || i>=4 || !d->prepared) return 0;
    return copy_tensor(d,d->api.InterpreterGetInputTensor(d->interpreter,i),output,capacity);
}
API size_t gocr_detector_copy_output(GocrDetector* d,int i,void* output,size_t capacity) {
    if (!d || i<0 || i>=11 || !d->invoked) return 0;
    return copy_tensor(d,d->heads[i],output,capacity);
}
API int gocr_detector_copy_proposals(GocrDetector* d,GocrProposal* output,int capacity) {
    if (!d) return -1;
    int count=int(d->proposals.size());
    if (output && capacity>=count) std::copy(d->proposals.begin(),d->proposals.end(),output);
    return count;
}
