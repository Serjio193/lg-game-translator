#include "detector.h"

#include <algorithm>
#include <cmath>

static std::vector<Box> find_letters(const std::vector<uint8_t>& mask, int w, int h)
{
    std::vector<Box> letters;
    for (const Component& component : components(mask, w, h)) {
        const Box& b = component.box;
        float fill = static_cast<float>(component.area) / (b.width * b.height);
        if (b.height >= 5 && b.height <= h / 6 && b.width >= 2
            && b.width <= b.height * 1.5 && component.area >= 6
            && fill >= 0.10 && fill <= 0.90)
            letters.push_back(b);
    }
    return letters;
}

static std::vector<Box> group_letters(std::vector<Box> letters)
{
    // Group geometrically compatible connected components into horizontal words.
    std::sort(letters.begin(), letters.end(), [](const Box& a, const Box& b) {
        return a.x < b.x;
    });
    std::vector<Box> result;
    std::vector<uint8_t> used(letters.size(), 0);
    for (size_t i = 0; i < letters.size(); ++i) {
        if (used[i])
            continue;
        Box group = letters[i];
        used[i] = 1;
        int count = 1;
        int glyph_height = group.height;
        for (size_t j = i + 1; j < letters.size(); ++j) {
            const Box& b = letters[j];
            int gap = b.x - (group.x + group.width);
            if (gap > glyph_height * 2)
                break;
            int center_delta = std::abs((b.y * 2 + b.height) - (group.y * 2 + group.height));
            if (used[j] || gap < -2 || b.height < glyph_height * 0.5
                || b.height > glyph_height * 1.8 || center_delta > glyph_height)
                continue;
            int bottom = std::max(group.y + group.height, b.y + b.height);
            group.y = std::min(group.y, b.y);
            group.height = bottom - group.y;
            group.width = b.x + b.width - group.x;
            used[j] = 1;
            ++count;
        }
        if (count >= 3 && group.width >= group.height * 1.5) {
            group.score = std::min(1.0f, count / 10.0f);
            result.push_back(group);
        }
    }
    return result;
}

std::vector<Box> detect_contrast(const Image& image)
{
    const int w = image.width, h = image.height;
    std::vector<uint8_t> gray(static_cast<size_t>(w) * h);
    std::vector<uint32_t> integral(static_cast<size_t>(w + 1) * (h + 1), 0);
    for (int y = 0; y < h; ++y) {
        uint32_t row = 0;
        for (int x = 0; x < w; ++x) {
            const uint8_t* pixel = &image.rgb[(y * w + x) * 3];
            uint8_t value = (77 * pixel[0] + 150 * pixel[1] + 29 * pixel[2]) >> 8;
            gray[y * w + x] = value;
            row += value;
            integral[(y + 1) * (w + 1) + x + 1] = integral[y * (w + 1) + x + 1] + row;
        }
    }
    std::vector<Box> result;
    for (int polarity : {-1, 1}) {
        std::vector<uint8_t> mask(gray.size(), 0);
        for (int y = 0; y < h; ++y) {
            int top = std::max(0, y - 8), bottom = std::min(h, y + 9);
            for (int x = 0; x < w; ++x) {
                int left = std::max(0, x - 8), right = std::min(w, x + 9);
                uint32_t sum = integral[bottom * (w + 1) + right]
                    - integral[top * (w + 1) + right]
                    - integral[bottom * (w + 1) + left]
                    + integral[top * (w + 1) + left];
                int mean = sum / ((right - left) * (bottom - top));
                mask[y * w + x] = (static_cast<int>(gray[y * w + x]) - mean) * polarity > 18;
            }
        }
        auto boxes = group_letters(find_letters(mask, w, h));
        result.insert(result.end(), boxes.begin(), boxes.end());
    }
    return result;
}
