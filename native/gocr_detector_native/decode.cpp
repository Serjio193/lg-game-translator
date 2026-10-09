#include "decode.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace gocr {
void decode_head(TfLiteApi& api,const void* tensor,int head,const GocrDetectorConfig& cfg,
                 std::vector<GocrProposal>& output) {
    if (api.TensorType(tensor)!=1 || api.TensorNumDims(tensor)!=4 ||
        api.TensorDim(tensor,0)!=1 || api.TensorDim(tensor,3)!=7)
        throw std::runtime_error("original detector head contract mismatch");
    const int rows=api.TensorDim(tensor,1), cols=api.TensorDim(tensor,2);
    const auto* data=static_cast<const float*>(api.TensorData(tensor));
    if (!data || api.TensorByteSize(tensor)!=size_t(rows)*cols*7*sizeof(float))
        throw std::runtime_error("invalid detector output storage");
    const double threshold=std::clamp(cfg.confidence_threshold,1e-6,1-1e-6);
    const double cutoff=std::log(threshold/(1-threshold));
    const double sx=double(cfg.limits[cfg.sources[head]])/1280;
    const double sy=sx;
    const double stride=cfg.strides[head], anchor=cfg.anchors[head];
    for (int y=0;y<rows;++y) {
        for (int x=0;x<cols;++x) {
            const float* v=data+(y*cols+x)*7;
            // NumPy compares float32 grid with scalar cast to its dtype.
            if (!(v[0]>=float(cutoff))) continue;
            GocrProposal p{};
            p.center[0]=(x+cfg.anchor_x+double(v[1]))*stride/sx;
            p.center[1]=(y+cfg.anchor_y+double(v[2]))*stride/sy;
            p.width=anchor*std::exp(std::clamp(double(v[3]),-8.0,8.0))/sx;
            p.height=anchor*std::exp(std::clamp(double(v[4]),-8.0,8.0))/sy;
            p.angle=std::atan2(double(v[6]),double(v[5]));
            const double c=std::cos(p.angle),s=std::sin(p.angle);
            const double xs[4]={-p.width/2,p.width/2,p.width/2,-p.width/2};
            const double ys[4]={-p.height/2,-p.height/2,p.height/2,p.height/2};
            for (int k=0;k<4;++k) {
                p.quad[k*2]=p.center[0]+xs[k]*c-ys[k]*s;
                p.quad[k*2+1]=p.center[1]+xs[k]*s+ys[k]*c;
            }
            if (v[0]>=0) {
                p.score=1/(1+std::exp(-double(v[0])));
            } else {
                double z=std::exp(double(v[0]));
                p.score=z/(1+z);
            }
            p.head=head;
            output.push_back(p);
        }
    }
}
}
