#ifndef LG_TEXT_RECOGNITION_PGM_HPP
#define LG_TEXT_RECOGNITION_PGM_HPP

#include <string>
#include <vector>

struct GrayImage {
    int width;
    int height;
    std::vector<unsigned char> pixels;
};

GrayImage load_pgm(const char* path);
std::string trim_line_endings(std::string text);

#endif
