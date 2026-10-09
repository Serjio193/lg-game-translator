// Isolated diagnostics only. Clone registration; forward original Prepare/Eval.
// Build against pinned TFLite 2.17 headers, and use only the pinned LG library.
#include "tensorflow/lite/core/c/common.h"
#include "conv_dispatch_symbols.h"
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <dlfcn.h>
#include <fstream>
#include <iomanip>
#include <pthread.h>

namespace {
using Clock = std::chrono::steady_clock;
struct Temporary {
    int index=-1, type=0, allocation=0;
    size_t bytes=0;
    void* first=nullptr;
    unsigned changes=0;
};
struct Row {
    TfLiteContext* context=nullptr;
    TfLiteNode* node=nullptr;
    int index=-1, input_tensor=-1, input_type=0, filter_type=0;
    unsigned prepare=0, eval=0, eigen=0, transpose=0;
    unsigned gemmlowp=0, ruy=0;
    double gemmlowp_ms=0, ruy_ms=0;
    unsigned gemmlowp_multi=0;
    uintptr_t kernel_run_offset=0;
    const char* kernel_name="unobserved";
    unsigned mallocs=0, callocs=0, reallocs=0, frees=0, creates=0;
    unsigned first_mallocs=0, last_mallocs=0, steady_min_mallocs=~0u, steady_max_mallocs=0;
    size_t first_bytes=0, last_bytes=0;
    size_t allocated_bytes=0;
    double eval_ms=0;
    uintptr_t eigen_caller=0;
    Temporary temporaries[8];
    int temporary_count=0;
};
Row rows[2048];
int used=0;
TfLiteRegistration original{}, diagnostic{};
thread_local Row* current=nullptr;
std::atomic<unsigned> all_creates{0};
void* runtime=nullptr;

void* lookup(const char* name) {
    if (!runtime) runtime=dlopen("/usr/lib/libtensorflow-lite.so",RTLD_NOW|RTLD_NOLOAD);
    void* result=runtime ? dlsym(runtime,name) : nullptr;
    if (!result) std::abort();
    return result;
}
uintptr_t offset(void* address) {
    Dl_info info{};
    return dladdr(address,&info) ? reinterpret_cast<uintptr_t>(address)-
        reinterpret_cast<uintptr_t>(info.dli_fbase) : 0;
}
Row& row(TfLiteContext* context,TfLiteNode* node) {
    for (int i=0;i<used;++i)
        if (rows[i].context==context && rows[i].node==node) return rows[i];
    if (used==2048) std::abort();
    auto& result=rows[used++];
    result.context=context;
    result.node=node;
    // Public graph inspection callbacks are delegate-only. Match model metadata
    // offline by the unique output tensor index instead of invoking those APIs.
    result.index=node->outputs->data[0];
    result.input_tensor=node->inputs->data[0];
    result.input_type=context->tensors[node->inputs->data[0]].type;
    result.filter_type=context->tensors[node->inputs->data[1]].type;
    return result;
}
void observe(Row& result) {
    auto* context=result.context;
    auto* node=result.node;
    int count=node->temporaries ? node->temporaries->size : 0;
    if (count>8) std::abort();
    result.temporary_count=count;
    for (int i=0;i<count;++i) {
        auto& temporary=result.temporaries[i];
        int index=node->temporaries->data[i];
        auto& tensor=context->tensors[index];
        if (temporary.index<0) {
            temporary.index=index;
            temporary.type=tensor.type;
            temporary.allocation=tensor.allocation_type;
            temporary.bytes=tensor.bytes;
            temporary.first=tensor.data.raw;
        } else if (temporary.first!=tensor.data.raw || temporary.bytes!=tensor.bytes ||
                   temporary.index!=index) ++temporary.changes;
    }
}
TfLiteStatus prepare(TfLiteContext* context,TfLiteNode* node) {
    auto& result=row(context,node);
    ++result.prepare;
    // Preparation counters are kept separate from Eval allocation counters.
    return original.prepare(context,node);
}
TfLiteStatus eval(TfLiteContext* context,TfLiteNode* node) {
    auto& result=row(context,node);
    observe(result);
    auto start=Clock::now();
    Row* previous=current;
    unsigned before_mallocs=result.mallocs;
    size_t before_bytes=result.allocated_bytes;
    current=&result;
    TfLiteStatus status=original.invoke(context,node);
    current=previous;
    result.eval_ms+=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    ++result.eval;
    result.last_mallocs=result.mallocs-before_mallocs;
    result.last_bytes=result.allocated_bytes-before_bytes;
    if (result.eval==1) {
        result.first_mallocs=result.last_mallocs;
        result.first_bytes=result.last_bytes;
    } else {
        if (result.last_mallocs<result.steady_min_mallocs) result.steady_min_mallocs=result.last_mallocs;
        if (result.last_mallocs>result.steady_max_mallocs) result.steady_max_mallocs=result.last_mallocs;
    }
    observe(result);
    return status;
}
struct Dump {
    ~Dump() {
        const char* path=std::getenv("GOCR_CONV_PROBE");
        if (!path) return;
        std::ofstream out(path);
        out<<"{\"registration_bytes\":"<<sizeof(TfLiteRegistration)
           <<",\"prepare_offset\":"<<offset(reinterpret_cast<void*>(original.prepare))
           <<",\"eval_offset\":"<<offset(reinterpret_cast<void*>(original.invoke))
           <<",\"pthread_create_total\":"<<all_creates<<",\"nodes\":[";
        for (int i=0;i<used;++i) {
            const auto& r=rows[i];
            if (i) out<<',';
            out<<"{\"context\":"<<reinterpret_cast<uintptr_t>(r.context)
               <<",\"output_tensor\":"<<r.index<<",\"input_tensor\":"<<r.input_tensor
               <<",\"input_type\":"<<r.input_type
               <<",\"filter_type\":"<<r.filter_type<<",\"prepare_calls\":"<<r.prepare
               <<",\"eval_calls\":"<<r.eval<<",\"eval_total_ms\":"<<r.eval_ms
               <<",\"eigen_calls\":"<<r.eigen<<",\"eigen_caller_offset\":"<<r.eigen_caller
               <<",\"transpose_calls\":"<<r.transpose<<",\"malloc_calls\":"<<r.mallocs
               <<",\"gemmlowp_dispatch_calls\":"<<r.gemmlowp<<",\"gemmlowp_total_ms\":"<<r.gemmlowp_ms
               <<",\"ruy_trmul_calls\":"<<r.ruy<<",\"ruy_total_ms\":"<<r.ruy_ms
               <<",\"gemmlowp_multi_calls\":"<<r.gemmlowp_multi
               <<",\"kernel_run_offset\":"<<r.kernel_run_offset
               <<",\"kernel_name\":"<<std::quoted(r.kernel_name)
               <<",\"calloc_calls\":"<<r.callocs<<",\"realloc_calls\":"<<r.reallocs
               <<",\"free_calls\":"<<r.frees<<",\"allocated_bytes\":"<<r.allocated_bytes
               <<",\"first_eval_mallocs\":"<<r.first_mallocs<<",\"first_eval_requested_bytes\":"<<r.first_bytes
               <<",\"last_eval_mallocs\":"<<r.last_mallocs<<",\"last_eval_requested_bytes\":"<<r.last_bytes
               <<",\"steady_min_mallocs\":"<<(r.eval>1 ? r.steady_min_mallocs : 0)
               <<",\"steady_max_mallocs\":"<<r.steady_max_mallocs
               <<",\"pthread_create_calls\":"<<r.creates<<",\"temporaries\":[";
            for (int j=0;j<r.temporary_count;++j) {
                if (j) out<<',';
                const auto& t=r.temporaries[j];
                out<<"{\"index\":"<<t.index<<",\"type\":"<<t.type
                   <<",\"allocation_type\":"<<t.allocation<<",\"bytes\":"<<t.bytes
                   <<",\"address\":"<<reinterpret_cast<uintptr_t>(t.first)
                   <<",\"address_or_size_changes\":"<<t.changes<<'}';
            }
            out<<"]}";
        }
        out<<"]}\n";
    }
} dump;
}

extern "C" TfLiteRegistration* registration() asm("_ZN6tflite3ops7builtin38Register_CONVOLUTION_MULTITHREADED_OPTEv");
extern "C" TfLiteRegistration* registration() {
    static bool initialized=false;
    if (!initialized) {
        using Get=TfLiteRegistration*(*)();
        original=*reinterpret_cast<Get>(lookup(
            "_ZN6tflite3ops7builtin38Register_CONVOLUTION_MULTITHREADED_OPTEv"))();
        diagnostic=original;
        diagnostic.prepare=prepare;
        diagnostic.invoke=eval;
        initialized=true;
    }
    return &diagnostic;
}
// Pinned system symbol, recovered from its PLT target at 0x3885d4. All seven
// parameters are pointers/references under ARM32 AAPCS; no arithmetic is replaced.
#define GEMM_SYMBOL "_ZN8gemmlowp17DispatchGemmShapeIaaNS_14BitDepthParamsINS_12OperandRangeILin127ELi127EEENS2_ILin128ELi127EEEEELNS_8MapOrderE1ELS6_0ELS6_0ENS_9VectorDupIKiLNS_11VectorShapeE0EEENS7_IS8_LS9_1EEESt5tupleIJNS_23OutputStageBiasAdditionINS_9VectorMapIS8_LS9_0EEEEENS_46OutputStageScaleInt32ByFixedPointAndExponentPCILS9_0EEENS_16OutputStageClampENS_31OutputStageSaturatingCastToInt8EEENS_11GemmContextEEEvPT8_RKNS_9MatrixMapIKT_XT2_EEERKNSP_ISR_XT3_EEEPNSP_IT0_XT4_EEERKT5_RKT6_RKT7_"
extern "C" void gemm(void*,const void*,const void*,void*,const void*,const void*,const void*) asm(GEMM_SYMBOL);
extern "C" void gemm(void* context,const void* lhs,const void* rhs,void* destination,
                     const void* lhs_offset,const void* rhs_offset,const void* stages) {
    using Gemm=void(*)(void*,const void*,const void*,void*,const void*,const void*,const void*);
    static auto next=reinterpret_cast<Gemm>(lookup(GEMM_SYMBOL));
    auto start=Clock::now();
    next(context,lhs,rhs,destination,lhs_offset,rhs_offset,stages);
    if (current) {
        ++current->gemmlowp;
        current->gemmlowp_ms+=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    }
}
extern "C" void trmul(void*,void*) asm("_ZN3ruy5TrMulEPNS_3CtxEPNS_11TrMulParamsE");
extern "C" void trmul(void* context,void* params) {
    static auto next=reinterpret_cast<void(*)(void*,void*)>(lookup(
        "_ZN3ruy5TrMulEPNS_3CtxEPNS_11TrMulParamsE"));
    auto start=Clock::now();
    next(context,params);
    if (current) {
        ++current->ruy;
        current->ruy_ms+=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
    }
}
using Multi=void(*)(void*,const void*,const void*,const void*,void*,const void*,const void*,const void*);
void multi_forward(Multi next,void* context,const void* kernel,const void* lhs,const void* rhs,
                   void* destination,const void* lhs_offset,const void* rhs_offset,const void* stages) {
    if (current) {
        ++current->gemmlowp_multi;
        // KernelBase ABI: Name(), Run(), destructors. Read the actual object
        // supplied by system DispatchGemmShape, never substitute its vtable.
        auto table=*reinterpret_cast<void* const* const*>(kernel);
        using Name=const char*(*)(const void*);
        current->kernel_name=reinterpret_cast<Name>(table[0])(kernel);
        current->kernel_run_offset=offset(table[1]);
    }
    next(context,kernel,lhs,rhs,destination,lhs_offset,rhs_offset,stages);
}
extern "C" void multi_col(void*,const void*,const void*,const void*,void*,const void*,const void*,const void*)
    asm(GOCR_GEMM_MULTI_COL);
extern "C" void multi_col(void* context,const void* kernel,const void* lhs,const void* rhs,
                          void* dst,const void* lo,const void* ro,const void* stages) {
    static auto next=reinterpret_cast<Multi>(lookup(GOCR_GEMM_MULTI_COL));
    multi_forward(next,context,kernel,lhs,rhs,dst,lo,ro,stages);
}
extern "C" void multi_row(void*,const void*,const void*,const void*,void*,const void*,const void*,const void*)
    asm(GOCR_GEMM_MULTI_ROW);
extern "C" void multi_row(void* context,const void* kernel,const void* lhs,const void* rhs,
                          void* dst,const void* lo,const void* ro,const void* stages) {
    static auto next=reinterpret_cast<Multi>(lookup(GOCR_GEMM_MULTI_ROW));
    multi_forward(next,context,kernel,lhs,rhs,dst,lo,ro,stages);
}
extern "C" void* eigen_pool(void*) asm("_ZN6tflite13eigen_support19GetThreadPoolDeviceEP13TfLiteContext");
extern "C" void* eigen_pool(void* context) {
    static auto next=reinterpret_cast<void*(*)(void*)>(lookup(
        "_ZN6tflite13eigen_support19GetThreadPoolDeviceEP13TfLiteContext"));
    if (current) {
        ++current->eigen;
        current->eigen_caller=offset(__builtin_return_address(0));
    }
    return next(context);
}
extern "C" void transpose(const TfLiteTensor*,TfLiteTensor*)
    asm("_ZN6tflite3ops7builtin4conv20TransposeFloatTensorEPK12TfLiteTensorPS3_");
extern "C" void transpose(const TfLiteTensor* source,TfLiteTensor* destination) {
    static auto next=reinterpret_cast<void(*)(const TfLiteTensor*,TfLiteTensor*)>(lookup(
        "_ZN6tflite3ops7builtin4conv20TransposeFloatTensorEPK12TfLiteTensorPS3_"));
    if (current) ++current->transpose;
    next(source,destination);
}
// glibc forwarding avoids recursive dlsym/malloc bootstrapping. Main Eval thread only.
extern "C" void* __libc_malloc(size_t);
extern "C" void* __libc_calloc(size_t,size_t);
extern "C" void* __libc_realloc(void*,size_t);
extern "C" void __libc_free(void*);
extern "C" void* malloc(size_t size) noexcept {
    if (current) { ++current->mallocs; current->allocated_bytes+=size; }
    return __libc_malloc(size);
}
extern "C" void* calloc(size_t count,size_t size) noexcept {
    if (current) { ++current->callocs; current->allocated_bytes+=count*size; }
    return __libc_calloc(count,size);
}
extern "C" void* realloc(void* pointer,size_t size) noexcept {
    if (current) { ++current->reallocs; current->allocated_bytes+=size; }
    return __libc_realloc(pointer,size);
}
extern "C" void free(void* pointer) noexcept {
    if (current) ++current->frees;
    __libc_free(pointer);
}
extern "C" int pthread_create(pthread_t* thread,const pthread_attr_t* attr,
                              void* (*start)(void*),void* argument) noexcept {
    using Create=int(*)(pthread_t*,const pthread_attr_t*,void*(*)(void*),void*);
    static auto next=reinterpret_cast<Create>(dlsym(RTLD_NEXT,"pthread_create"));
    if (!next) std::abort();
    ++all_creates;
    if (current) ++current->creates;
    return next(thread,attr,start,argument);
}
