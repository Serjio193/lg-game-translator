// Exact float32 class-major argmax and existing greedy CTC token selection.
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

extern "C" int ppocr_class_major_ctc(const float* scores, int classes, int steps,
    int32_t* tokens, float* probabilities, int capacity)
{
    if (!scores || !tokens || !probabilities || classes < 2 || classes > 65536
        || steps < 1 || steps > 4096 || capacity < steps
        || static_cast<uint64_t>(classes) * steps > 64000000)
        return -1;
    // Preserve reference rejection of every NaN/Inf, including losing classes.
    uint32_t invalid = 0;
    const size_t elements = static_cast<size_t>(classes) * steps;
    for (size_t i = 0; i < elements; ++i) {
        uint32_t bits;
        std::memcpy(&bits, scores + i, sizeof(bits));
        invalid |= (bits & 0x7f800000u) == 0x7f800000u;
    }
    if (invalid) return -2;
    std::vector<float> best(scores, scores + steps);
    std::vector<int32_t> ids(static_cast<size_t>(steps), 0);
    for (int c = 1; c < classes; ++c) {
        const float* row = scores + static_cast<size_t>(c) * steps;
        for (int t = 0; t < steps; ++t) {
            // Strict greater preserves NumPy's first-index rule for ties.
            if (row[t] > best[t]) {
                best[t] = row[t];
                ids[t] = c;
            }
        }
    }
    int written = 0, previous = -1;
    for (int t = 0; t < steps; ++t) {
        const int token = ids[t];
        if (token && token != previous) {
            tokens[written] = token;
            probabilities[written] = best[t];
            ++written;
        }
        previous = token;
    }
    return written;
}
