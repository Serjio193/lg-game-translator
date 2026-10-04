#include <net.h>
#include "pgm.hpp"

#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::vector<std::string> load_dictionary(const char* path)
{
    std::ifstream input(path);
    if (!input)
        throw std::runtime_error("cannot open dictionary");
    std::vector<std::string> words;
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r')
            line.pop_back();
        words.push_back(line);
    }
    if (words.empty())
        throw std::runtime_error("empty dictionary");
    return words;
}

static std::string recognize(ncnn::Net& network, const GrayImage& image,
    const std::vector<std::string>& dictionary, int word_gap)
{
    const int resized_height = 48;
    const int resized_width = std::max(1, image.width * resized_height / image.height);
    ncnn::Mat input = ncnn::Mat::from_pixels_resize(image.pixels.data(),
        ncnn::Mat::PIXEL_GRAY2BGR, image.width, image.height,
        resized_width, resized_height);
    const float mean[3] = {127.5f, 127.5f, 127.5f};
    const float norm[3] = {1.f / 127.5f, 1.f / 127.5f, 1.f / 127.5f};
    input.substract_mean_normalize(mean, norm);

    ncnn::Extractor extractor = network.create_extractor();
    if (extractor.input("in0", input) != 0)
        throw std::runtime_error("recognizer input failed");
    ncnn::Mat output;
    if (extractor.extract("out0", output) != 0)
        throw std::runtime_error("recognizer inference failed");

    std::string text;
    int previous = 0;
    int blank_run = 0;
    for (int row = 0; row < output.h; ++row) {
        const float* scores = output.row(row);
        int best = 0;
        for (int column = 1; column < output.w; ++column) {
            if (scores[column] > scores[best])
                best = column;
        }
        if (best == 0) {
            ++blank_run;
        } else if (best != previous || previous == 0) {
            const size_t index = static_cast<size_t>(best - 1);
            if (index < dictionary.size()) {
                if (word_gap > 0 && !text.empty() && blank_run >= word_gap &&
                    text.back() != ' ')
                    text += ' ';
                text += dictionary[index];
            }
        }
        if (best > 0)
            blank_run = 0;
        previous = best;
    }
    return text;
}

int main(int argc, char** argv)
{
    if (argc != 6 && argc != 7) {
        std::cerr << "Usage: " << argv[0]
            << " model.param model.bin dictionary.txt crop.pgm iterations [word-gap]\n";
        return 2;
    }
    try {
        const int iterations = std::stoi(argv[5]);
        const int word_gap = argc == 7 ? std::stoi(argv[6]) : 0;
        if (iterations < 1 || iterations > 100)
            throw std::runtime_error("iterations must be 1..100");
        if (word_gap < 0 || word_gap > 20)
            throw std::runtime_error("word-gap must be 0..20");
        GrayImage image = load_pgm(argv[4]);
        std::vector<std::string> dictionary = load_dictionary(argv[3]);
        ncnn::Net network;
        network.opt.num_threads = 1;
        network.opt.use_vulkan_compute = false;
        if (network.load_param(argv[1]) != 0 || network.load_model(argv[2]) != 0)
            throw std::runtime_error("model load failed");

        std::string text = recognize(network, image, dictionary, word_gap);
        std::vector<double> timings;
        for (int i = 0; i < iterations; ++i) {
            const auto start = std::chrono::steady_clock::now();
            text = recognize(network, image, dictionary, word_gap);
            const auto end = std::chrono::steady_clock::now();
            timings.push_back(std::chrono::duration<double, std::milli>(end - start).count());
        }
        double total = 0;
        for (double elapsed : timings)
            total += elapsed;
        std::sort(timings.begin(), timings.end());
        std::cout << "crop=" << image.width << 'x' << image.height
            << " model_input=" << std::max(1, image.width * 48 / image.height) << "x48"
            << " iterations=" << iterations
            << " word_gap=" << word_gap
            << " mean_ms=" << total / timings.size()
            << " median_ms=" << timings[timings.size() / 2]
            << " text=" << text << '\n';
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
