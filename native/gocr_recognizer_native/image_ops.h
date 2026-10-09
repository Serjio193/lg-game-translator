#pragma once
#include <cstdint>
#include <vector>
namespace gocr {
struct ImageBuffer {
    int width=0, height=0, channels=0;
    std::vector<uint8_t> pixels;
};
int round_even(double value);
ImageBuffer rectify(const uint8_t* rgb,int width,int height,const double quad[8]);
ImageBuffer normalize_line(const uint8_t* pixels,int width,int height,int channels);
void make_window(const ImageBuffer&,int x,uint8_t* output);
}
