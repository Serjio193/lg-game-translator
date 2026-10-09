#include "preprocess.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <stdexcept>

namespace gocr {
namespace {
// Pillow 10.3 reference: normalized separable bilinear, 22-bit coefficients,
// rounding after each pass. This is not a generic four-neighbor resize.
std::vector<Coefficients> coefficients(int input, int output) {
    const double scale=double(input)/output;
    const double support=std::max(scale,1.0);
    const double inverse=1.0/support;
    std::vector<Coefficients> result;
    for (int out=0;out<output;++out) {
        const double center=(out+0.5)*scale;
        const int first=std::max(0,int(center-support+0.5));
        const int end=std::min(input,int(center+support+0.5));
        std::vector<double> weights;
        double sum=0;
        for (int i=first;i<end;++i) {
            double x=std::abs((i-center+0.5)*inverse);
            double weight=x<1 ? 1-x : 0;
            weights.push_back(weight);
            sum+=weight;
        }
        Coefficients c{first,{}};
        for (double weight:weights)
            c.weights.push_back(int32_t(0.5+(sum ? weight/sum : weight)*(1<<22)));
        result.push_back(std::move(c));
    }
    return result;
}
uint8_t rounded(int64_t value) {
    return uint8_t(std::clamp<int64_t>(value>>22,0,255));
}
}

void grayscale(const uint8_t* rgb,std::vector<uint8_t>& gray) {
    gray.resize(1280*720);
    for (size_t i=0;i<gray.size();++i) {
        const uint8_t* p=rgb+3*i;
        gray[i]=uint8_t((p[0]*19595+p[1]*38470+p[2]*7471+32768)>>16);
    }
}

void PyramidBranch::configure(int limit) {
    if (limit!=1280 && limit!=640 && limit!=160)
        throw std::runtime_error("unsupported unchanged 1280x720 profile");
    content_width=limit;
    // 720*limit/1280 is exact for the three supported profile dimensions.
    content_height=720*limit/1280;
    tensor_width=(content_width+31)/32*32;
    tensor_height=(content_height+31)/32*32;
    if (content_width==1280 && content_height==720) {
        horizontal.clear();
        vertical.clear();
        intermediate.clear();
        return;
    }
    horizontal=coefficients(1280,content_width);
    vertical=coefficients(720,content_height);
    intermediate.resize(size_t(content_width)*720);
}

void PyramidBranch::fill(const std::vector<uint8_t>& gray,uint8_t* tensor) {
    std::memset(tensor,255,size_t(tensor_width)*tensor_height);
    if (content_width==1280 && content_height==720) {
        for (int y=0;y<720;++y)
            std::memcpy(tensor+y*tensor_width,gray.data()+y*1280,1280);
        return;
    }
    for (int y=0;y<720;++y) {
        for (int x=0;x<content_width;++x) {
            const auto& c=horizontal[x];
            int64_t value=1<<21;
            for (size_t k=0;k<c.weights.size();++k)
                value+=int64_t(gray[y*1280+c.first+k])*c.weights[k];
            intermediate[y*content_width+x]=rounded(value);
        }
    }
    for (int y=0;y<content_height;++y) {
        const auto& c=vertical[y];
        for (int x=0;x<content_width;++x) {
            int64_t value=1<<21;
            for (size_t k=0;k<c.weights.size();++k)
                value+=int64_t(intermediate[(c.first+k)*content_width+x])*c.weights[k];
            tensor[y*tensor_width+x]=rounded(value);
        }
    }
}
}
