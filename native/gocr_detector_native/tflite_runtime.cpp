#include "tflite_runtime.h"
#include <dlfcn.h>
#include <stdexcept>
#include <string>

namespace gocr {
TfLiteApi::TfLiteApi(const char* path) {
    handle=dlopen(path,RTLD_NOW|RTLD_LOCAL);
    if (!handle) throw std::runtime_error(dlerror());
    try {
#define LOAD(name) name=reinterpret_cast<decltype(name)>(dlsym(handle,"TfLite" #name)); \
    if (!name) throw std::runtime_error("missing TfLite" #name)
        LOAD(Version);
        LOAD(ModelCreateFromFile);
        LOAD(ModelDelete);
        LOAD(InterpreterOptionsCreate);
        LOAD(InterpreterOptionsSetNumThreads);
        LOAD(InterpreterOptionsDelete);
        LOAD(InterpreterCreate);
        LOAD(InterpreterDelete);
        LOAD(InterpreterResizeInputTensor);
        LOAD(InterpreterAllocateTensors);
        LOAD(InterpreterInvoke);
        LOAD(InterpreterGetInputTensorCount);
        LOAD(InterpreterGetOutputTensorCount);
        LOAD(InterpreterGetInputTensor);
        LOAD(InterpreterGetOutputTensor);
        LOAD(TensorType);
        LOAD(TensorNumDims);
        LOAD(TensorDim);
        LOAD(TensorByteSize);
        LOAD(TensorData);
        LOAD(TensorName);
#undef LOAD
#define OPTIONAL(name) name=reinterpret_cast<decltype(name)>(dlsym(handle,"TfLite" #name))
        OPTIONAL(InterpreterModifyGraphWithDelegate);
        OPTIONAL(InterpreterOptionsSetTelemetryProfiler);
        OPTIONAL(XNNPackDelegateOptionsDefault);
        OPTIONAL(XNNPackDelegateCreate);
        OPTIONAL(XNNPackDelegateDelete);
#undef OPTIONAL
    } catch (...) {
        dlclose(handle);
        handle=nullptr;
        throw;
    }
}
TfLiteApi::~TfLiteApi() {
    if (handle) dlclose(handle);
}
}
