#pragma once

#include "detector.h"
#include <net.h>
#include <string>

class NeuralDetector {
public:
    explicit NeuralDetector(const std::string& prefix);
    std::vector<Box> detect(const Image& image);
private:
    ncnn::Net network;
};
