#include <tesseract/capi.h>
#include "pgm.hpp"

#include <chrono>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::string recognize(TessBaseAPI* api, const GrayImage& image)
{
    TessBaseAPIClear(api);
    TessBaseAPISetImage(api, image.pixels.data(), image.width, image.height, 1,
        image.width);
    TessBaseAPISetSourceResolution(api, 300);
    char* result = TessBaseAPIGetUTF8Text(api);
    if (!result)
        throw std::runtime_error("Tesseract returned no text buffer");
    std::string text(result);
    TessDeleteText(result);
    return trim_line_endings(text);
}

int main(int argc, char** argv)
{
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0]
            << " tessdata-dir iterations crop1.pgm [crop2.pgm ...]\n";
        return 2;
    }
    try {
        const int iterations = std::stoi(argv[2]);
        if (iterations < 1 || iterations > 100)
            throw std::runtime_error("iterations must be 1..100");
        std::vector<GrayImage> images;
        std::vector<std::string> names;
        for (int i = 3; i < argc; ++i) {
            images.push_back(load_pgm(argv[i]));
            std::string path(argv[i]);
            size_t slash = path.find_last_of('/');
            names.push_back(slash == std::string::npos ? path : path.substr(slash + 1));
        }
        TessBaseAPI* api = TessBaseAPICreate();
        if (!api)
            throw std::runtime_error("TessBaseAPICreate failed");
        const auto init_start = std::chrono::steady_clock::now();
        int initialized = TessBaseAPIInit3(api, argv[1], "eng");
        const auto init_end = std::chrono::steady_clock::now();
        if (initialized != 0) {
            TessBaseAPIDelete(api);
            throw std::runtime_error("Tesseract initialization failed");
        }
        TessBaseAPISetPageSegMode(api, tesseract::PSM_SINGLE_LINE);
        const double init_ms = std::chrono::duration<double, std::milli>(init_end - init_start).count();
        for (size_t index = 0; index < images.size(); ++index) {
            const GrayImage& image = images[index];
            std::string text = recognize(api, image);
            std::vector<double> timings;
            for (int i = 0; i < iterations; ++i) {
                const auto start = std::chrono::steady_clock::now();
                text = recognize(api, image);
                const auto end = std::chrono::steady_clock::now();
                timings.push_back(std::chrono::duration<double, std::milli>(end - start).count());
            }
            double total = 0;
            for (double elapsed : timings)
                total += elapsed;
            std::cout << "crop=" << names[index] << ' ' << image.width << 'x' << image.height
                << " iterations=" << iterations
                << " init_ms=" << init_ms
                << " mean_ms=" << total / timings.size()
                << " text=" << text << '\n';
        }
        TessBaseAPIEnd(api);
        TessBaseAPIDelete(api);
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
