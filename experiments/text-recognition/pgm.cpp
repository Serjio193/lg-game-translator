#include "pgm.hpp"

#include <fstream>
#include <stdexcept>

static std::string next_token(std::istream& input)
{
    std::string value;
    while (input >> value) {
        if (value[0] != '#')
            return value;
        std::getline(input, value);
    }
    throw std::runtime_error("truncated PGM header");
}

GrayImage load_pgm(const char* path)
{
    std::ifstream input(path, std::ios::binary);
    if (!input || next_token(input) != "P5")
        throw std::runtime_error("expected binary P5 PGM");
    GrayImage image;
    image.width = std::stoi(next_token(input));
    image.height = std::stoi(next_token(input));
    if (std::stoi(next_token(input)) != 255 || image.width <= 0 || image.height <= 0 ||
        image.width > 4096 || image.height > 2048)
        throw std::runtime_error("invalid PGM dimensions or depth");
    char separator = static_cast<char>(input.get());
    if (separator == '\r' && input.peek() == '\n')
        input.get();
    image.pixels.resize(static_cast<size_t>(image.width) * image.height);
    input.read(reinterpret_cast<char*>(image.pixels.data()), image.pixels.size());
    if (static_cast<size_t>(input.gcount()) != image.pixels.size())
        throw std::runtime_error("truncated PGM pixels");
    return image;
}

std::string trim_line_endings(std::string text)
{
    while (!text.empty() && (text.back() == '\n' || text.back() == '\r'))
        text.pop_back();
    return text;
}
