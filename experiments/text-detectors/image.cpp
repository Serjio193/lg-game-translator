#include "detector.h"

#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <string>

static std::string token(std::istream& input)
{
    std::string result;
    while (input >> result) {
        if (result[0] != '#')
            return result;
        std::getline(input, result);
    }
    throw std::runtime_error("Incomplete PNM header");
}

Image read_image(const char* path)
{
    std::ifstream input(path, std::ios::binary);
    if (!input)
        throw std::runtime_error("Cannot open input image");
    std::string magic = token(input);
    Image image;
    image.width = std::stoi(token(input));
    image.height = std::stoi(token(input));
    int maximum = std::stoi(token(input));
    if ((magic != "P6" && magic != "P5") || maximum != 255 || image.width <= 0
        || image.height <= 0 || image.width > 4096 || image.height > 4096)
        throw std::runtime_error("Expected bounded P6/P5 image with maxval 255");
    char separator = input.get();
    if (separator == '\r' && input.peek() == '\n')
        input.get();
    size_t pixels = static_cast<size_t>(image.width) * image.height;
    size_t bytes = pixels * (magic == "P6" ? 3 : 1);
    std::vector<uint8_t> data(bytes);
    input.read(reinterpret_cast<char*>(data.data()), bytes);
    if (static_cast<size_t>(input.gcount()) != bytes)
        throw std::runtime_error("Truncated input pixels");
    image.rgb.resize(pixels * 3);
    if (magic == "P6") {
        image.rgb.swap(data);
    } else {
        for (size_t i = 0; i < pixels; ++i)
            image.rgb[i * 3] = image.rgb[i * 3 + 1] = image.rgb[i * 3 + 2] = data[i];
    }
    return image;
}

Image resize_image(const Image& image, int max_edge)
{
    int edge = std::max(image.width, image.height);
    if (edge <= max_edge)
        return image;
    Image result;
    result.width = std::max(1, image.width * max_edge / edge);
    result.height = std::max(1, image.height * max_edge / edge);
    result.rgb.resize(static_cast<size_t>(result.width) * result.height * 3);
    for (int y = 0; y < result.height; ++y) {
        double sy = (y + 0.5) * image.height / result.height - 0.5;
        int y0 = std::max(0, static_cast<int>(sy));
        int y1 = std::min(y0 + 1, image.height - 1);
        double fy = std::max(0.0, sy - y0);
        for (int x = 0; x < result.width; ++x) {
            double sx = (x + 0.5) * image.width / result.width - 0.5;
            int x0 = std::max(0, static_cast<int>(sx));
            int x1 = std::min(x0 + 1, image.width - 1);
            double fx = std::max(0.0, sx - x0);
            for (int c = 0; c < 3; ++c) {
                double top = image.rgb[(y0 * image.width + x0) * 3 + c] * (1 - fx)
                    + image.rgb[(y0 * image.width + x1) * 3 + c] * fx;
                double bottom = image.rgb[(y1 * image.width + x0) * 3 + c] * (1 - fx)
                    + image.rgb[(y1 * image.width + x1) * 3 + c] * fx;
                result.rgb[(y * result.width + x) * 3 + c] = top * (1 - fy) + bottom * fy;
            }
        }
    }
    return result;
}

std::vector<Component> components(const std::vector<uint8_t>& mask, int width,
    int height, const float* values)
{
    std::vector<uint8_t> seen(mask.size(), 0);
    std::vector<int> pending;
    std::vector<Component> result;
    for (int start = 0; start < width * height; ++start) {
        if (!mask[start] || seen[start])
            continue;
        Component item;
        int left = start % width, right = left;
        int top = start / width, bottom = top;
        pending.clear();
        pending.push_back(start);
        seen[start] = 1;
        while (!pending.empty()) {
            int index = pending.back();
            pending.pop_back();
            int x = index % width, y = index / width;
            left = std::min(left, x); right = std::max(right, x);
            top = std::min(top, y); bottom = std::max(bottom, y);
            ++item.area;
            item.value_sum += values ? values[index] : 1.0;
            int neighbors[4] = {x > 0 ? index - 1 : -1,
                x + 1 < width ? index + 1 : -1,
                y > 0 ? index - width : -1,
                y + 1 < height ? index + width : -1};
            for (int next : neighbors) {
                if (next >= 0 && mask[next] && !seen[next]) {
                    seen[next] = 1;
                    pending.push_back(next);
                }
            }
        }
        item.box.x = left; item.box.y = top;
        item.box.width = right - left + 1; item.box.height = bottom - top + 1;
        item.box.score = item.value_sum / item.area;
        result.push_back(item);
    }
    return result;
}
