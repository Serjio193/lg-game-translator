#include "detector.h"
#include "neural.h"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <thread>

using Clock = std::chrono::steady_clock;

static double cpu_ms()
{
    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) != 0)
        throw std::runtime_error("getrusage failed");
    return (usage.ru_utime.tv_sec + usage.ru_stime.tv_sec) * 1000.0
        + (usage.ru_utime.tv_usec + usage.ru_stime.tv_usec) / 1000.0;
}

static int argument(const char* text, int low, int high)
{
    std::string value(text);
    size_t end = 0;
    int number = std::stoi(value, &end);
    if (end != value.size() || number < low || number > high)
        throw std::runtime_error("Argument out of bounds");
    return number;
}

int main(int argc, char** argv)
{
    try {
        if (argc != 7) {
            std::fprintf(stderr, "Usage: %s contrast|ppocr image.ppm max_edge iterations period_ms model_prefix\n", argv[0]);
            return 2;
        }
        std::string backend(argv[1]);
        if (backend != "contrast" && backend != "ppocr")
            throw std::runtime_error("Unknown backend");
        int edge = argument(argv[3], 160, 1280);
        int iterations = argument(argv[4], 1, 100);
        int period_ms = argument(argv[5], 0, 10000);
        Image source = read_image(argv[2]);
        std::unique_ptr<NeuralDetector> neural;
        if (backend == "ppocr")
            neural.reset(new NeuralDetector(argv[6]));
        auto detect = [&](const Image& image) {
            return neural ? neural->detect(image) : detect_contrast(image);
        };
        // Model load and one warmup are separate from steady-state detection timings.
        detect(resize_image(source, edge));
        double wall_sum = 0, cpu_sum = 0, wall_min = 1e20, wall_max = 0;
        std::vector<Box> boxes;
        auto run_start = Clock::now();
        double run_cpu = cpu_ms();
        for (int i = 0; i < iterations; ++i) {
            auto started = Clock::now();
            double cpu_start = cpu_ms();
            Image input = resize_image(source, edge);
            boxes = detect(input);
            double elapsed = std::chrono::duration<double, std::milli>(Clock::now() - started).count();
            double cpu = cpu_ms() - cpu_start;
            wall_sum += elapsed; cpu_sum += cpu;
            wall_min = std::min(wall_min, elapsed); wall_max = std::max(wall_max, elapsed);
            if (i == iterations - 1) {
                for (Box& b : boxes) {
                    int left = b.x * source.width / input.width;
                    int top = b.y * source.height / input.height;
                    int right = std::min(source.width,
                        ((b.x + b.width) * source.width + input.width - 1) / input.width);
                    int bottom = std::min(source.height,
                        ((b.y + b.height) * source.height + input.height - 1) / input.height);
                    b.x = left; b.y = top; b.width = right - left; b.height = bottom - top;
                }
            }
            std::this_thread::sleep_until(started + std::chrono::milliseconds(period_ms));
        }
        double run_ms = std::chrono::duration<double, std::milli>(Clock::now() - run_start).count();
        rusage usage{};
        getrusage(RUSAGE_SELF, &usage);
        std::printf("{\"backend\":\"%s\",\"source_width\":%d,\"source_height\":%d,"
            "\"max_edge\":%d,\"iterations\":%d,\"period_ms\":%d,\"threads\":1,"
            "\"mean_wall_ms\":%.3f,\"min_wall_ms\":%.3f,\"max_wall_ms\":%.3f,"
            "\"mean_cpu_ms\":%.3f,\"run_ms\":%.3f,\"one_core_cpu_percent\":%.3f,"
            "\"max_rss_kb\":%ld,\"boxes\":[",
            backend.c_str(), source.width, source.height, edge, iterations, period_ms,
            wall_sum / iterations, wall_min, wall_max, cpu_sum / iterations, run_ms,
            (cpu_ms() - run_cpu) * 100.0 / run_ms, usage.ru_maxrss);
        for (size_t i = 0; i < boxes.size(); ++i) {
            const Box& b = boxes[i];
            std::printf("%s{\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,\"score\":%.3f}",
                i ? "," : "", b.x, b.y, b.width, b.height, b.score);
        }
        std::puts("]}");
        return 0;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "%s\n", error.what());
        return 1;
    }
}
