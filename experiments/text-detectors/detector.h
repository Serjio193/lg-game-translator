#pragma once

#include <cstdint>
#include <vector>

struct Image {
    int width = 0;
    int height = 0;
    std::vector<uint8_t> rgb;
};

struct Box {
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;
    float score = 0;
};

struct Component {
    Box box;
    int area = 0;
    double value_sum = 0;
};

Image read_image(const char* path);
Image resize_image(const Image& image, int max_edge);
std::vector<Component> components(const std::vector<uint8_t>& mask, int width,
    int height, const float* values = nullptr);
std::vector<Box> detect_contrast(const Image& image);
