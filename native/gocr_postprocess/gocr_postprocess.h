#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* ABI v1: double preserves the Python reference's float64 geometry.
 * Quads are supplied verbatim after tensor decode, never reconstructed. */
typedef struct {
    double quad[8], center[2], width, height, angle, score;
    int32_t head;
} GocrProposal;
typedef struct {
    double max_height_ratio, search_radius_factor, max_angle_difference;
    double max_centers_relative_distance, optimal_centers_relative_distance;
    double min_overlap, min_overlap_optimal, duplicate_horizontal_overlap;
    /* Existing clean-room literals, supplied by Python, not new Google knobs. */
    double duplicate_iou, group_across_factor;
} GocrPostprocessConfig;
typedef struct {
    double quad[8], center[2], width, height, angle, score;
    int32_t piece_count;
} GocrLine;
typedef struct {
    double dedupe_ms, pairwise_ms, fit_ms, refine_ms, total_ms;
    int32_t deduped_count, component_count;
    int64_t pair_tests;
} GocrStats;
int gocr_postprocess_abi(void);
/* membership[input index] = component ordinal; -1 for suppressed/group heads.
 * Return final count, or a negative error; output is untouched on error. */
int gocr_postprocess(const GocrProposal*, int, const GocrPostprocessConfig*,
                     GocrLine*, int, int32_t*, GocrStats*);
#ifdef __cplusplus
}
#endif
