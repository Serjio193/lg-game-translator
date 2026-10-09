#pragma once
#include <cstddef>
#include <cstdint>

namespace gocr {
struct TelemetryCallbacks;
struct XnnOptions {
    int32_t num_threads;
    uint32_t flags;
    void* weights_cache;
    bool handle_variable_ops;
    const char* experimental_weight_cache_file_path;
};
// Minimal dynamically resolved TFLite 2.17 C API declarations. No C++ ABI used.
class TfLiteApi {
public:
    explicit TfLiteApi(const char* path);
    ~TfLiteApi();
    TfLiteApi(const TfLiteApi&)=delete;
    TfLiteApi& operator=(const TfLiteApi&)=delete;
    void* handle=nullptr;
    const char* (*Version)();
    void* (*ModelCreateFromFile)(const char*);
    void (*ModelDelete)(void*);
    void* (*InterpreterOptionsCreate)();
    void (*InterpreterOptionsSetNumThreads)(void*,int);
    void (*InterpreterOptionsDelete)(void*);
    void (*InterpreterOptionsSetTelemetryProfiler)(void*,TelemetryCallbacks*)=nullptr;
    void* (*InterpreterCreate)(const void*,const void*);
    void (*InterpreterDelete)(void*);
    int (*InterpreterResizeInputTensor)(void*,int,const int*,int);
    int (*InterpreterAllocateTensors)(void*);
    int (*InterpreterInvoke)(void*);
    int (*InterpreterGetInputTensorCount)(const void*);
    int (*InterpreterGetOutputTensorCount)(const void*);
    void* (*InterpreterGetInputTensor)(void*,int);
    const void* (*InterpreterGetOutputTensor)(const void*,int);
    int (*TensorType)(const void*);
    int (*TensorNumDims)(const void*);
    int (*TensorDim)(const void*,int);
    size_t (*TensorByteSize)(const void*);
    void* (*TensorData)(const void*);
    const char* (*TensorName)(const void*);
    int (*InterpreterModifyGraphWithDelegate)(void*,void*)=nullptr;
    XnnOptions (*XNNPackDelegateOptionsDefault)()=nullptr;
    void* (*XNNPackDelegateCreate)(const XnnOptions*)=nullptr;
    void (*XNNPackDelegateDelete)(void*)=nullptr;
};
}
