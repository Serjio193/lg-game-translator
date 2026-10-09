#include "image_ops.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <stdexcept>

namespace gocr {
int round_even(double value) {
    double base=std::floor(value), fraction=value-base;
    if (fraction>0.5 || (fraction==0.5 && std::fmod(base,2.0)!=0)) ++base;
    if (!std::isfinite(base) || base<0 || base>100000)
        throw std::runtime_error("invalid image dimension");
    return int(base);
}
namespace {
double cubic(double a,double b,double c,double d,double t) {
    double p1=b, p2=-a+c, p3=2*(a-b)+c-d, p4=-a+b-c+d;
    return p1+t*(p2+t*(p3+t*p4));
}
uint8_t sample(const uint8_t* rgb,int width,int height,double sx,double sy,int channel) {
    if (sx<0 || sx>=width || sy<0 || sy>=height) return 255;
    sx-=0.5; sy-=0.5;
    int x=int(std::floor(sx)), y=int(std::floor(sy));
    double dx=sx-x, dy=sy-y;
    --x; --y;
    double rows[4];
    for (int row=0;row<4;++row) {
        if (row && (y+row<0 || y+row>=height)) {
            rows[row]=rows[row-1];
            continue;
        }
        int yy=std::clamp(y+row,0,height-1);
        double values[4];
        for (int k=0;k<4;++k)
            values[k]=rgb[(size_t(yy)*width+std::clamp(x+k,0,width-1))*3+channel];
        rows[row]=cubic(values[0],values[1],values[2],values[3],dx);
    }
    return uint8_t(std::clamp(cubic(rows[0],rows[1],rows[2],rows[3],dy),0.0,255.0));
}
struct Coeff { int first; std::vector<int32_t> weights; };
double sinc(double x) {
    if (x==0) return 1;
    x*=3.14159265358979323846;
    return std::sin(x)/x;
}
std::vector<Coeff> coefficients(int input,int output) {
    double scale=double(input)/output, filter_scale=std::max(scale,1.0);
    double inverse=1.0/filter_scale;
    double support=3*filter_scale;
    std::vector<Coeff> result;
    for (int i=0;i<output;++i) {
        double center=(i+0.5)*scale;
        int first=std::max(0,int(center-support+0.5));
        int end=std::min(input,int(center+support+0.5));
        std::vector<double> weights;
        double sum=0;
        for (int k=first;k<end;++k) {
            double x=(k-center+0.5)*inverse;
            double weight=(-3<=x && x<3) ? sinc(x)*sinc(x/3) : 0;
            weights.push_back(weight); sum+=weight;
        }
        Coeff c{first,{}};
        for (double weight:weights) {
            double value=(sum ? weight/sum : weight)*(1<<22);
            c.weights.push_back(int32_t(value+(value<0 ? -0.5 : 0.5)));
        }
        result.push_back(std::move(c));
    }
    return result;
}
uint8_t rounded(int64_t value) { return uint8_t(std::clamp<int64_t>(value>>22,0,255)); }
}
ImageBuffer rectify(const uint8_t* rgb,int width,int height,const double q[8]) {
    if (!rgb || width<=0 || height<=0) throw std::runtime_error("invalid source image");
    for (int i=0;i<8;++i)
        if (!std::isfinite(q[i])) throw std::runtime_error("nonfinite quad");
    // Keep reference norm arithmetic and Python ties-to-even dimension rounding.
    double ux=q[2]-q[0], uy=q[3]-q[1], vx=q[6]-q[0], vy=q[7]-q[1];
    double w=std::sqrt(ux*ux+uy*uy), h=std::sqrt(vx*vx+vy*vy);
    if (w<1 || h<1) throw std::runtime_error("degenerate Google line quad");
    ImageBuffer out{std::max(1,round_even(w)),std::max(1,round_even(h)),3,{}};
    if (size_t(out.width)*out.height>1280*720*4)
        throw std::runtime_error("rectified crop exceeds resource bound");
    out.pixels.resize(size_t(out.width)*out.height*3);
    double as=1.0/out.width, at=1.0/out.height;
    double a[8]={q[0],ux*as,vx*at,(q[4]-q[6]-q[2]+q[0])*as*at,
                 q[1],uy*as,vy*at,(q[5]-q[7]-q[3]+q[1])*as*at};
    for (int y=0;y<out.height;++y) {
        for (int x=0;x<out.width;++x) {
            double xx=x+0.5, yy=y+0.5;
            double sx=a[0]+a[1]*xx+a[2]*yy+a[3]*xx*yy;
            double sy=a[4]+a[5]*xx+a[6]*yy+a[7]*xx*yy;
            for (int c=0;c<3;++c)
                out.pixels[(size_t(y)*out.width+x)*3+c]=sample(rgb,width,height,sx,sy,c);
        }
    }
    return out;
}
ImageBuffer normalize_line(const uint8_t* pixels,int width,int height,int channels) {
    if (!pixels || width<=0 || height<=0 || (channels!=1 && channels!=3))
        throw std::runtime_error("invalid recognizer crop");
    int normalized=std::max(1,round_even(double(width)*32/height));
    ImageBuffer gray{width,height,1,{}};
    gray.pixels.resize(size_t(width)*height);
    if (channels==1) std::memcpy(gray.pixels.data(),pixels,gray.pixels.size());
    else for (size_t i=0;i<gray.pixels.size();++i) {
        const uint8_t* p=pixels+3*i;
        gray.pixels[i]=uint8_t((p[0]*19595+p[1]*38470+p[2]*7471+32768)>>16);
    }
    ImageBuffer intermediate{normalized,height,1,{}};
    if (normalized==width) intermediate.pixels=gray.pixels;
    else {
        auto coeff=coefficients(width,normalized);
        intermediate.pixels.resize(size_t(normalized)*height);
        for (int y=0;y<height;++y) for (int x=0;x<normalized;++x) {
            int64_t value=1<<21;
            const auto& c=coeff[x];
            for (size_t k=0;k<c.weights.size();++k)
                value+=int64_t(gray.pixels[size_t(y)*width+c.first+k])*c.weights[k];
            intermediate.pixels[size_t(y)*normalized+x]=rounded(value);
        }
    }
    ImageBuffer out{normalized,32,1,{}};
    if (height==32) out.pixels=std::move(intermediate.pixels);
    else {
        auto coeff=coefficients(height,32);
        out.pixels.resize(size_t(normalized)*32);
        for (int y=0;y<32;++y) for (int x=0;x<normalized;++x) {
            int64_t value=1<<21;
            const auto& c=coeff[y];
            for (size_t k=0;k<c.weights.size();++k)
                value+=int64_t(intermediate.pixels[size_t(c.first+k)*normalized+x])*c.weights[k];
            out.pixels[size_t(y)*normalized+x]=rounded(value);
        }
    }
    return out;
}
void make_window(const ImageBuffer& gray,int x,uint8_t* output) {
    for (int y=0;y<32;++y) for (int k=0;k<168;++k) {
        int padded=x+k, source=padded-16;
        output[y*168+k]=padded>=gray.width+32 ? 0 :
            (source<0 || source>=gray.width ? 255 : gray.pixels[size_t(y)*gray.width+source]);
    }
}
}
