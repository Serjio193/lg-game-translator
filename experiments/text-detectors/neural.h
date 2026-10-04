#pragma once

#include "detector.h"
#include <net.h>
#include <string>

class NeuralDetector {
public:
    NeuralDetector(const std::string& prefix, const std::string& backend);
    std::vector<Box> detect(const Image& image);
    std::vector<Box> detect_east(const Image& image);
    std::vector<Box> detect_craft(const Image& image);
private:
    ncnn::Net network;
    std::string input_name;
    std::string output_name;
    bool east = false;
    bool craft = false;
};
