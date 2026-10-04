#include "detector.h"

#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <stdexcept>
#include <string>
#include <time.h>

static int number(const char* text, int minimum, int maximum)
{
    char* end = nullptr;
    errno = 0;
    long value = std::strtol(text, &end, 10);
    if (errno || !end || *end || value < minimum || value > maximum)
        throw std::runtime_error("Invalid integer argument");
    return static_cast<int>(value);
}

static double seconds(const timespec& value)
{
    return value.tv_sec + value.tv_nsec / 1e9;
}

int main(int argc, char** argv)
{
    try {
        if (argc != 9) {
            std::fprintf(stderr, "Usage: %s before.pgm after.pgm x y width height iterations\n", argv[0]);
            return 2;
        }
        Image before = read_image(argv[1]);
        Image after = read_image(argv[2]);
        if (before.width != after.width || before.height != after.height)
            throw std::runtime_error("Frame dimensions differ");
        const int x = number(argv[3], 0, before.width - 1);
        const int y = number(argv[4], 0, before.height - 1);
        const int width = number(argv[5], 1, before.width - x);
        const int height = number(argv[6], 1, before.height - y);
        const int iterations = number(argv[7], 1, 10000);
        const int threshold = number(argv[8], 0, 255);
        const size_t count = static_cast<size_t>(width) * height;
        size_t changed = 0;
        uint64_t difference = 0;
        timespec wall_start{}, wall_end{};
        clock_gettime(CLOCK_MONOTONIC, &wall_start);
        clock_t cpu_start = std::clock();
        for (int iteration = 0; iteration < iterations; ++iteration) {
            changed = 0;
            difference = 0;
            for (int row = 0; row < height; ++row) {
                size_t offset = (static_cast<size_t>(y + row) * before.width + x) * 3;
                for (int col = 0; col < width; ++col) {
                    size_t pixel = offset + static_cast<size_t>(col) * 3;
                    int delta = std::abs(static_cast<int>(before.rgb[pixel])
                        - static_cast<int>(after.rgb[pixel]));
                    difference += static_cast<unsigned>(delta);
                    changed += delta > threshold;
                }
            }
        }
        clock_t cpu_end = std::clock();
        clock_gettime(CLOCK_MONOTONIC, &wall_end);
        double wall_ms = (seconds(wall_end) - seconds(wall_start)) * 1000 / iterations;
        double cpu_ms = 1000.0 * (cpu_end - cpu_start) / CLOCKS_PER_SEC / iterations;
        std::printf("{\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,"
            "\"threshold\":%d,\"changed_percent\":%.4f,\"mean_abs_delta\":%.4f,"
            "\"wall_ms\":%.4f,\"cpu_ms\":%.4f,\"iterations\":%d}\n",
            x, y, width, height, threshold, 100.0 * changed / count,
            static_cast<double>(difference) / count, wall_ms, cpu_ms, iterations);
        return 0;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "frame diff error: %s\n", error.what());
        return 1;
    }
}
