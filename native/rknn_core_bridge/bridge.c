/* Keep reference tensor IO/inference intact; expose explicit context placement. */
#include BRIDGE_REFERENCE_SOURCE

int npu_set_core(model_t* model, int mask)
{
    if (!model || !model->context ||
        (mask != RKNN_NPU_CORE_0 && mask != RKNN_NPU_CORE_1 &&
         mask != RKNN_NPU_CORE_2 && mask != RKNN_NPU_CORE_0_1_2)) return -101;
    return rknn_set_core_mask(model->context, (rknn_core_mask)mask);
}
