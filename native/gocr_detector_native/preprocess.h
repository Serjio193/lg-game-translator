#pragma once
#include <cstdint>
#include <vector>

namespace gocr {
struct Coefficients {
    int first;
    std::vector<int32_t> weights;
};
struct PyramidBranch {
    int content_width, content_height, tensor_width, tensor_height;
    std::vector<Coefficients> horizontal, vertical;
    std::vector<uint8_t> intermediate;
    void configure(int limit);
    void fill(const std::vector<uint8_t>& gray, uint8_t* tensor);
};
void grayscale(const uint8_t* rgb, std::vector<uint8_t>& gray);
}
