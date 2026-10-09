#include "sha256.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
namespace gocr {
namespace {
constexpr uint32_t k[64]={
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
uint32_t rotate(uint32_t x,int n) { return (x>>n)|(x<<(32-n)); }
}
void Sha256::block(const uint8_t* bytes) {
    uint32_t w[64];
    for (int i=0;i<16;++i)
        w[i]=(uint32_t(bytes[4*i])<<24)|(uint32_t(bytes[4*i+1])<<16)|
            (uint32_t(bytes[4*i+2])<<8)|bytes[4*i+3];
    for (int i=16;i<64;++i) {
        uint32_t a=w[i-15], b=w[i-2];
        w[i]=w[i-16]+(rotate(a,7)^rotate(a,18)^(a>>3))+w[i-7]+
            (rotate(b,17)^rotate(b,19)^(b>>10));
    }
    auto s=state;
    for (int i=0;i<64;++i) {
        uint32_t t=s[7]+(rotate(s[4],6)^rotate(s[4],11)^rotate(s[4],25))+
            ((s[4]&s[5])^(~s[4]&s[6]))+k[i]+w[i];
        uint32_t u=(rotate(s[0],2)^rotate(s[0],13)^rotate(s[0],22))+
            ((s[0]&s[1])^(s[0]&s[2])^(s[1]&s[2]));
        s={t+u,s[0],s[1],s[2],s[3]+t,s[4],s[5],s[6]};
    }
    for (int i=0;i<8;++i) state[i]+=s[i];
}
void Sha256::update(const void* data,size_t bytes) {
    const auto* input=static_cast<const uint8_t*>(data);
    length+=bytes;
    while (bytes) {
        size_t n=std::min(bytes,64-used);
        std::memcpy(pending.data()+used,input,n);
        used+=n; input+=n; bytes-=n;
        if (used==64) { block(pending.data()); used=0; }
    }
}
std::string Sha256::finish() const {
    Sha256 copy=*this;
    uint64_t bits=length*8;
    uint8_t end=128, zero=0;
    copy.update(&end,1);
    while (copy.used!=56) copy.update(&zero,1);
    uint8_t tail[8];
    for (int i=0;i<8;++i) tail[i]=uint8_t(bits>>(56-8*i));
    copy.update(tail,8);
    char result[65];
    for (int i=0;i<8;++i) std::snprintf(result+8*i,9,"%08x",copy.state[i]);
    return result;
}
}
