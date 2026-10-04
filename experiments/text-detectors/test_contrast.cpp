#include "detector.h"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <stdexcept>

static void pixel(Image& image, int x, int y)
{
    size_t i = (y * image.width + x) * 3;
    image.rgb[i] = image.rgb[i + 1] = image.rgb[i + 2] = 255;
}

int main()
{
    Image image;
    image.width = 320; image.height = 240;
    image.rgb.resize(320 * 240 * 3, 0);
    assert(detect_contrast(image).empty());
    for (int letter = 0; letter < 6; ++letter) {
        int left = 40 + letter * 14;
        for (int y = 60; y < 76; ++y) {
            for (int x = left; x < left + 10; ++x) {
                if (x < left + 2 || x >= left + 8 || (y >= 66 && y < 69))
                    pixel(image, x, y);
            }
        }
    }
    auto boxes = detect_contrast(image);
    bool found = false;
    for (const Box& b : boxes)
        found = found || (b.x <= 42 && b.y <= 62 && b.x + b.width >= 118
            && b.y + b.height >= 74);
    assert(found);
    Image reduced = resize_image(image, 160);
    assert(reduced.width == 160 && reduced.height == 120);

    const char* path = "/tmp/lg-detector-input-test.pgm";
    {
        std::ofstream file(path, std::ios::binary);
        file << "P5\n# comment\n2 1\n255\n";
        char values[] = {0, static_cast<char>(255)};
        file.write(values, 2);
    }
    auto loaded = read_image(path);
    assert(loaded.width == 2 && loaded.height == 1 && loaded.rgb.size() == 6);
    assert(loaded.rgb[0] == 0 && loaded.rgb[3] == 255);
    {
        std::ofstream file(path);
        file << "P6\n1280 720\n255\nshort";
    }
    bool rejected = false;
    try { read_image(path); } catch (const std::runtime_error&) { rejected = true; }
    assert(rejected);
    std::remove(path);
    std::puts("PASS: blank, glyph group, resize, PGM, truncated input");
}
