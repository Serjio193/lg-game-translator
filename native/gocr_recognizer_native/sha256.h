#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
namespace gocr {
class Sha256 {
public:
    void update(const void*,size_t);
    std::string finish() const;
private:
    void block(const uint8_t*);
    std::array<uint32_t,8> state{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
        0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    std::array<uint8_t,64> pending{};
    uint64_t length=0;
    size_t used=0;
};
}
