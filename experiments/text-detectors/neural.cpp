// PP-OCR preprocessing follows Tencent/ncnn examples/ppocrv5.cpp (BSD-3-Clause).
// Copyright 2025 Tencent. The connected-component postprocessor below is local.
#include "neural.h"

#include <algorithm>
#include <stdexcept>

NeuralDetector::NeuralDetector(const std::string& prefix)
{
    network.opt.num_threads = 1;
    network.opt.use_vulkan_compute = false;
    network.opt.use_fp16_packed = false;
    network.opt.use_fp16_storage = false;
    network.opt.use_fp16_arithmetic = false;
    if (network.load_param((prefix + ".param").c_str()) != 0
        || network.load_model((prefix + ".bin").c_str()) != 0)
        throw std::runtime_error("Cannot load detector model");
}

std::vector<Box> NeuralDetector::detect(const Image& image)
{
    const int w = image.width, h = image.height;
    ncnn::Mat input = ncnn::Mat::from_pixels(image.rgb.data(), ncnn::Mat::PIXEL_RGB2BGR, w, h);
    int wpad = (w + 31) / 32 * 32 - w;
    int hpad = (h + 31) / 32 * 32 - h;
    ncnn::Mat padded;
    ncnn::copy_make_border(input, padded, hpad / 2, hpad - hpad / 2,
        wpad / 2, wpad - wpad / 2, ncnn::BORDER_CONSTANT, 114.f);
    const float means[] = {0.485f * 255, 0.456f * 255, 0.406f * 255};
    const float norms[] = {1 / (0.229f * 255), 1 / (0.224f * 255), 1 / (0.225f * 255)};
    padded.substract_mean_normalize(means, norms);
    auto extractor = network.create_extractor();
    ncnn::Mat output;
    if (extractor.input("in0", padded) != 0 || extractor.extract("out0", output) != 0
        || output.empty() || output.c != 1 || output.elemsize != sizeof(float))
        throw std::runtime_error("Unexpected detector probability map");
    const float* probabilities = output.channel(0);
    std::vector<uint8_t> mask(static_cast<size_t>(output.w) * output.h);
    for (size_t i = 0; i < mask.size(); ++i)
        mask[i] = probabilities[i] >= 0.30f;
    std::vector<Box> result;
    float sx = static_cast<float>(padded.w) / output.w;
    float sy = static_cast<float>(padded.h) / output.h;
    for (const Component& component : components(mask, output.w, output.h, probabilities)) {
        const Box& b = component.box;
        if (component.area < 6 || b.score < 0.60f || b.width < b.height * 1.2f)
            continue;
        int margin = std::max(2, static_cast<int>(b.height * sy * 0.35f));
        int left = std::max(0, static_cast<int>(b.x * sx) - wpad / 2 - margin);
        int top = std::max(0, static_cast<int>(b.y * sy) - hpad / 2 - margin);
        int right = std::min(w, static_cast<int>((b.x + b.width) * sx) - wpad / 2 + margin);
        int bottom = std::min(h, static_cast<int>((b.y + b.height) * sy) - hpad / 2 + margin);
        if (right <= left || bottom <= top)
            continue;
        Box box;
        box.x = left; box.y = top; box.width = right - left; box.height = bottom - top;
        box.score = b.score;
        result.push_back(box);
    }
    return result;
}
