/* Isolated timing/preallocation experiment around the unchanged existing bridge. */
#define _POSIX_C_SOURCE 200809L
#include "rknn_api.h"
#include <string.h>
#include <time.h>

static _Thread_local double timings[6];

static double milliseconds(void)
{
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (double)now.tv_sec * 1000.0 + now.tv_nsec / 1000000.0;
}

static int timed_inputs(rknn_context context, uint32_t count, rknn_input* inputs)
{
    double start = milliseconds();
    int code = rknn_inputs_set(context, count, inputs);
    timings[0] += milliseconds() - start;
    return code;
}

static int timed_run(rknn_context context, rknn_run_extend* extension)
{
    double start = milliseconds();
    int code = rknn_run(context, extension);
    timings[1] += milliseconds() - start;
    return code;
}

static int timed_get(void* opaque, uint32_t count, rknn_output* outputs,
    rknn_output_extend* extension);

static int timed_release(rknn_context context, uint32_t count, rknn_output* outputs)
{
    double start = milliseconds();
    int code = rknn_outputs_release(context, count, outputs);
    timings[4] += milliseconds() - start;
    return code;
}

static void* timed_copy(void* destination, const void* source, size_t size)
{
    /* Preallocated outputs already reside in the reference result buffers. */
    if (destination == source) return destination;
    double start = milliseconds();
    void* result = memcpy(destination, source, size);
    timings[3] += milliseconds() - start;
    return result;
}

#define rknn_inputs_set timed_inputs
#define rknn_run timed_run
#define rknn_outputs_get(context, count, outputs, extension) timed_get(model, count, outputs, extension)
#define rknn_outputs_release timed_release
#define memcpy timed_copy
#define npu_run reference_npu_run
#include BRIDGE_REFERENCE_SOURCE
#undef rknn_inputs_set
#undef rknn_run
#undef rknn_outputs_get
#undef rknn_outputs_release
#undef memcpy
#undef npu_run

static int timed_get(void* opaque, uint32_t count, rknn_output* outputs,
    rknn_output_extend* extension)
{
    model_t* model = opaque;
#ifdef OUTPUT_PREALLOC
    for (unsigned i = 0; i < count; ++i) {
        outputs[i].is_prealloc = 1;
        outputs[i].buf = model->results[i];
        outputs[i].size = model->outputs[i].n_elems * sizeof(float);
    }
#endif
    double start = milliseconds();
    int code = rknn_outputs_get(model->context, count, outputs, extension);
    timings[2] += milliseconds() - start;
    return code;
}

int npu_run(model_t* model, float** values)
{
    memset(timings, 0, sizeof(timings));
    double start = milliseconds();
    int code = reference_npu_run(model, values);
    timings[5] = milliseconds() - start;
    return code;
}

double npu_profile_ms(int stage)
{
    return stage >= 0 && stage < 6 ? timings[stage] : -1;
}
