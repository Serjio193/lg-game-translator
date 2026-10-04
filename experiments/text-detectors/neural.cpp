// PP-OCR preprocessing follows Tencent/ncnn examples/ppocrv5.cpp (BSD-3-Clause).
// Copyright 2025 Tencent. The connected-component postprocessor below is local.
#include "neural.h"

#include <algorithm>
#include <stdexcept>

NeuralDetector::NeuralDetector(const std::string& prefix, const std::string& backend)
{
    east = backend == "east";
    craft = backend == "craft";
    input_name = backend == "ppocr" || backend == "east" || craft ? "in0" : "input";
    output_name = backend == "ppocr" || backend == "east" || craft ? "out0" : "output";
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
    if (east)
        return detect_east(image);
    if (craft)
        return detect_craft(image);
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
    if (extractor.input(input_name.c_str(), padded) != 0
        || extractor.extract(output_name.c_str(), output) != 0
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

std::vector<Box> NeuralDetector::detect_craft(const Image& image)
{
    if (image.width > 320 || image.height > 192)
        throw std::runtime_error("CRAFT probe model is fixed at 320x192");
    ncnn::Mat padded;
    ncnn::Mat input = ncnn::Mat::from_pixels(image.rgb.data(), ncnn::Mat::PIXEL_RGB,
        image.width, image.height);
    ncnn::copy_make_border(input, padded, (192 - image.height) / 2,
        192 - image.height - (192 - image.height) / 2,
        (320 - image.width) / 2, 320 - image.width - (320 - image.width) / 2,
        ncnn::BORDER_CONSTANT, 0.f);
    const float means[] = {0.485f * 255, 0.456f * 255, 0.406f * 255};
    const float norms[] = {1 / (0.229f * 255), 1 / (0.224f * 255), 1 / (0.225f * 255)};
    padded.substract_mean_normalize(means, norms);
    auto extractor = network.create_extractor();
    ncnn::Mat output;
    if (extractor.input(input_name.c_str(), padded) != 0
        || extractor.extract(output_name.c_str(), output) != 0 || output.empty())
        throw std::runtime_error("Cannot extract CRAFT score output");
    if (output.dims != 3 || output.w != 2 || output.elemsize != sizeof(float))
        throw std::runtime_error("CRAFT output shape is " + std::to_string(output.w) + "x"
            + std::to_string(output.h) + "x" + std::to_string(output.c));
    const int map_width = output.c, map_height = output.h;
    std::vector<float> text(static_cast<size_t>(map_width) * map_height);
    std::vector<float> link(text.size());
    for (int x = 0; x < map_width; ++x) {
        const float* column = output.channel(x);
        for (int y = 0; y < map_height; ++y) {
            text[static_cast<size_t>(y) * map_width + x] = column[y * 2];
            link[static_cast<size_t>(y) * map_width + x] = column[y * 2 + 1];
        }
    }
    std::vector<uint8_t> mask(text.size(), 0);
    for (size_t i = 0; i < mask.size(); ++i)
        mask[i] = text[i] >= 0.4f || link[i] >= 0.4f;
    std::vector<Box> boxes;
    for (const Component& component : components(mask, map_width, map_height, text.data())) {
        if (component.area < 4 || component.box.score < 0.4f)
            continue;
        const Box& region = component.box;
        const float scale = static_cast<float>(image.width) / 320.f;
        int x = static_cast<int>(region.x * 2 * scale);
        int y = static_cast<int>((region.y * 2 - (192 - image.height) / 2) * scale);
        int right = static_cast<int>((region.x + region.width) * 2 * scale);
        int bottom = static_cast<int>((region.y + region.height) * 2 * scale);
        x = std::max(0, std::min(image.width, x));
        y = std::max(0, std::min(image.height, y));
        right = std::max(x, std::min(image.width, right));
        bottom = std::max(y, std::min(image.height, bottom));
        if (right <= x || bottom <= y) continue;
        Box box;
        box.x = x; box.y = y; box.width = right - x; box.height = bottom - y;
        box.score = component.box.score;
        boxes.push_back(box);
    }
    return boxes;
}

std::vector<Box> NeuralDetector::detect_east(const Image& image)
{
    const float scale = 512.f / std::max(image.width, image.height);
    const int width = std::max(32, static_cast<int>(image.width * scale) / 32 * 32);
    const int height = std::max(32, static_cast<int>(image.height * scale) / 32 * 32);
    ncnn::Mat resized = ncnn::Mat::from_pixels_resize(image.rgb.data(), ncnn::Mat::PIXEL_RGB,
        image.width, image.height, width, height);
    ncnn::Mat padded;
    ncnn::copy_make_border(resized, padded, 0, 512 - height, 0, 512 - width,
        ncnn::BORDER_CONSTANT, 0.f);
    auto extractor = network.create_extractor();
    ncnn::Mat output;
    if (extractor.input(input_name.c_str(), padded) != 0
        || extractor.extract(output_name.c_str(), output) != 0
        || output.empty() || output.c != 6 || output.elemsize != sizeof(float))
        throw std::runtime_error("Unexpected EAST score/geometry output");

    const float* scores = output.channel(0);
    const int map_width = output.w, map_height = output.h;
    std::vector<uint8_t> mask(static_cast<size_t>(map_width) * map_height, 0);
    const int valid_height = height / 4;
    for (int y = 0; y < valid_height; ++y)
        for (int x = 0; x < map_width; ++x)
            mask[static_cast<size_t>(y) * map_width + x] = scores[y * map_width + x] >= 0.8f;

    std::vector<Box> boxes;
    const float* top = output.channel(1);
    const float* right = output.channel(2);
    const float* bottom = output.channel(3);
    const float* left = output.channel(4);
    const float coordinate_scale = static_cast<float>(image.width) / width;
    for (const Component& component : components(mask, map_width, map_height, scores)) {
        if (component.area < 2 || component.box.score < 0.80f)
            continue;
        const Box& region = component.box;
        double cx = 0, cy = 0, t = 0, r = 0, b = 0, l = 0;
        int count = 0;
        for (int y = region.y; y < region.y + region.height; ++y)
            for (int x = region.x; x < region.x + region.width; ++x) {
                const int index = y * map_width + x;
                if (!mask[index]) continue;
                cx += x * 4.0 + 2.0; cy += y * 4.0 + 2.0;
                t += top[index]; r += right[index]; b += bottom[index]; l += left[index];
                ++count;
            }
        if (!count) continue;
        cx /= count; cy /= count; t /= count; r /= count; b /= count; l /= count;
        const int x1 = std::max(0, static_cast<int>((cx - l) * coordinate_scale));
        const int y1 = std::max(0, static_cast<int>((cy - t) * coordinate_scale));
        const int x2 = std::min(image.width, static_cast<int>((cx + r) * coordinate_scale));
        const int y2 = std::min(image.height, static_cast<int>((cy + b) * coordinate_scale));
        if (x2 <= x1 || y2 <= y1) continue;
        Box box;
        box.x = x1; box.y = y1; box.width = x2 - x1; box.height = y2 - y1;
        box.score = component.box.score;
        boxes.push_back(box);
    }
    return boxes;
}
