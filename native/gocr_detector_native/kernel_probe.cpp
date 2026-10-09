// Diagnostic LD_PRELOAD only; forwards unchanged arguments to exported system kernels.
// Symbol ABIs verified against the pinned ARM32 system library, not a generic profiler.
#include <atomic>
#include <cstdlib>
#include <dlfcn.h>
#include <fstream>
#include <pthread.h>
#include <stdexcept>

namespace {
std::atomic<unsigned long> float_neon{0}, int_neon{0}, int_one_col{0}, execute{0}, created{0};
std::atomic<unsigned long> eigen_device{0};
void* symbol(const char* name) {
    static void* runtime=dlopen("/usr/lib/libtensorflow-lite.so",RTLD_NOW|RTLD_NOLOAD);
    void* address=runtime ? dlsym(runtime,name) : nullptr;
    if (!address) std::abort();
    return address;
}
struct Dump {
    ~Dump() {
        const char* path=std::getenv("GOCR_KERNEL_PROBE");
        if (!path) return;
        std::ofstream out(path);
        out<<"{\"ruy_float32_neon_calls\":"<<float_neon
           <<",\"ruy_int8_neon_calls\":"<<int_neon
           <<",\"ruy_int8_one_col_calls\":"<<int_one_col
           <<",\"ruy_threadpool_execute_calls\":"<<execute
           <<",\"eigen_threadpool_device_calls\":"<<eigen_device
           <<",\"pthread_create_calls\":"<<created<<"}\n";
    }
} dump;
}

extern "C" void* eigen_pool(void*) asm("_ZN6tflite13eigen_support19GetThreadPoolDeviceEP13TfLiteContext");
extern "C" void* eigen_pool(void* context) {
    static auto next=reinterpret_cast<void*(*)(void*)>(symbol(
        "_ZN6tflite13eigen_support19GetThreadPoolDeviceEP13TfLiteContext"));
    ++eigen_device;
    return next(context);
}

extern "C" void float_kernel(const void*) asm("_ZN3ruy17KernelFloat32NeonERKNS_17KernelParamsFloatILi8ELi4EEE");
extern "C" void float_kernel(const void* params) {
    static auto next=reinterpret_cast<void(*)(const void*)>(symbol(
        "_ZN3ruy17KernelFloat32NeonERKNS_17KernelParamsFloatILi8ELi4EEE"));
    ++float_neon;
    next(params);
}
extern "C" void int_kernel(const void*) asm("_ZN3ruy14Kernel8bitNeonERKNS_16KernelParams8bitILi4ELi2EEE");
extern "C" void int_kernel(const void* params) {
    static auto next=reinterpret_cast<void(*)(const void*)>(symbol(
        "_ZN3ruy14Kernel8bitNeonERKNS_16KernelParams8bitILi4ELi2EEE"));
    ++int_neon;
    next(params);
}
extern "C" void int_col(const void*) asm("_ZN3ruy18Kernel8bitNeon1ColERKNS_16KernelParams8bitILi4ELi2EEE");
extern "C" void int_col(const void* params) {
    static auto next=reinterpret_cast<void(*)(const void*)>(symbol(
        "_ZN3ruy18Kernel8bitNeon1ColERKNS_16KernelParams8bitILi4ELi2EEE"));
    ++int_one_col;
    next(params);
}
extern "C" void pool(void*,int,int,void*) asm("_ZN3ruy10ThreadPool11ExecuteImplEiiPNS_4TaskE");
extern "C" void pool(void* self,int threads,int tasks,void* task) {
    static auto next=reinterpret_cast<void(*)(void*,int,int,void*)>(symbol(
        "_ZN3ruy10ThreadPool11ExecuteImplEiiPNS_4TaskE"));
    ++execute;
    next(self,threads,tasks,task);
}
extern "C" int pthread_create(pthread_t* thread,const pthread_attr_t* attr,
                              void* (*start)(void*),void* arg) noexcept {
    using Create=int(*)(pthread_t*,const pthread_attr_t*,void*(*)(void*),void*);
    static auto next=reinterpret_cast<Create>(dlsym(RTLD_NEXT,"pthread_create"));
    if (!next) std::abort();
    ++created;
    return next(thread,attr,start,arg);
}
