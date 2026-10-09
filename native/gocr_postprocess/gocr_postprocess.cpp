#include "gocr_postprocess.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
using V = std::array<double, 2>;
struct Box {
    std::array<V, 4> q;
    V center;
    std::array<double, 4> bb;
    double w, h, angle, score;
    int pieces = 1, input = -1;
};
double dot(V a, V b) { return a[0]*b[0]+a[1]*b[1]; }
V sub(V a, V b) { return {a[0]-b[0], a[1]-b[1]}; }
V scale(V a, double d) { return {a[0]*d, a[1]*d}; }
double norm(V a) { return std::sqrt(dot(a,a)); }
V basis(const Box& b) {
    V u = sub(b.q[1],b.q[0]);
    double w = norm(u);
    return w < 1e-6 ? V{1,0} : scale(u,1/w);
}
V normal(V u) { return {-u[1],u[0]}; }
void bbox(Box& b) {
    b.bb = {b.q[0][0],b.q[0][1],b.q[0][0],b.q[0][1]};
    for (V p : b.q) {
        b.bb[0]=std::min(b.bb[0],p[0]); b.bb[1]=std::min(b.bb[1],p[1]);
        b.bb[2]=std::max(b.bb[2],p[0]); b.bb[3]=std::max(b.bb[3],p[1]);
    }
}
double angle_diff(double a, double b) {
    double d=std::fmod(std::abs((a-b)*(180.0/std::acos(-1.0))),180.0);
    return std::min(d,180.0-d);
}
double intersection(const Box& a, const Box& b) {
    return std::max(0.0,std::min(a.bb[2],b.bb[2])-std::max(a.bb[0],b.bb[0]))*
           std::max(0.0,std::min(a.bb[3],b.bb[3])-std::max(a.bb[1],b.bb[1]));
}
std::vector<Box> dedupe(std::vector<Box> boxes, const GocrPostprocessConfig& c) {
    std::stable_sort(boxes.begin(),boxes.end(),[](const Box& a,const Box& b) {
        return a.score>b.score;
    });
    std::vector<Box> keep;
    for (const Box& b : boxes) {
        bool duplicate=false;
        for (const Box& a : keep) {
            if (angle_diff(a.angle,b.angle)>c.max_angle_difference) continue;
            double inter=intersection(a,b);
            double aa=std::max(0.0,a.bb[2]-a.bb[0])*std::max(0.0,a.bb[3]-a.bb[1]);
            double ba=std::max(0.0,b.bb[2]-b.bb[0])*std::max(0.0,b.bb[3]-b.bb[1]);
            if (inter/std::max(aa+ba-inter,1e-9)>=c.duplicate_iou ||
                inter/std::min(std::max(aa,1e-9),std::max(ba,1e-9))>=c.duplicate_horizontal_overlap) {
                duplicate=true; break;
            }
        }
        if (!duplicate) keep.push_back(b);
    }
    return keep;
}
bool compatible(const Box& a,const Box& b,const GocrPostprocessConfig& c) {
    if (std::max(a.h,b.h)/std::max(std::min(a.h,b.h),1e-6)>c.max_height_ratio ||
        angle_diff(a.angle,b.angle)>c.max_angle_difference) return false;
    V ua=basis(a), ub=basis(b), u={ua[0]+ub[0],ua[1]+ub[1]};
    if (norm(u)<1e-6) u=ua;
    u=scale(u,1/std::max(norm(u),1e-6));
    V delta=sub(b.center,a.center);
    double along=std::abs(dot(delta,u)), across=std::abs(dot(delta,normal(u)));
    double typical=std::max(a.h,b.h), rel=across/std::max(typical,1e-6);
    double overlap=std::max(0.0,(a.h+b.h)/2-across)/std::max(std::min(a.h,b.h),1e-6);
    double required=rel<=c.optimal_centers_relative_distance ? c.min_overlap_optimal : c.min_overlap;
    if (rel>c.max_centers_relative_distance && overlap<required) return false;
    return along-(a.w+b.w)/2<=c.search_radius_factor*typical;
}
Box merge(const std::vector<Box>& comp) {
    V direction={0,0}, first=basis(comp.front());
    double sum=0, score=0;
    for (const Box& b : comp) {
        double weight=std::max(b.score,1e-6);
        V u=basis(b);
        if (dot(u,first)<0) u=scale(u,-1);
        direction[0]+=u[0]*weight; direction[1]+=u[1]*weight;
        sum+=weight; score+=b.score*weight;
    }
    direction=scale(direction,1/sum);
    direction=scale(direction,1/std::max(norm(direction),1e-6));
    V n=normal(direction);
    double lo=std::numeric_limits<double>::infinity(), hi=-lo, vlo=lo, vhi=hi;
    for (const Box& b : comp) for (V p : b.q) {
        double u=dot(p,direction), v=dot(p,n);
        lo=std::min(lo,u); hi=std::max(hi,u); vlo=std::min(vlo,v); vhi=std::max(vhi,v);
    }
    Box out{};
    std::array<V,4> uv={V{lo,vlo},V{hi,vlo},V{hi,vhi},V{lo,vhi}};
    for (int i=0;i<4;++i) {
        out.q[i]={direction[0]*uv[i][0]+n[0]*uv[i][1],direction[1]*uv[i][0]+n[1]*uv[i][1]};
        out.center[0]+=out.q[i][0]; out.center[1]+=out.q[i][1];
    }
    out.center=scale(out.center,0.25);
    out.w=norm(sub(out.q[1],out.q[0])); out.h=norm(sub(out.q[3],out.q[0]));
    out.angle=std::atan2(direction[1],direction[0]); out.score=score/sum;
    out.pieces=static_cast<int>(comp.size()); bbox(out);
    return out;
}
int find(std::vector<int>& p,int i) {
    while (p[i]!=i) { p[i]=p[p[i]]; i=p[i]; }
    return i;
}
double ms(Clock::time_point a,Clock::time_point b) {
    return std::chrono::duration<double,std::milli>(b-a).count();
}
}

#define EXPORT __attribute__((visibility("default")))
extern "C" EXPORT int gocr_postprocess_abi(void) { return 1; }
extern "C" EXPORT int gocr_postprocess(const GocrProposal* input,int count,
    const GocrPostprocessConfig* config,GocrLine* output,int capacity,int32_t* membership,GocrStats* stats) {
    if (!config || !stats || count<0 || capacity<0 || (count && (!input || !membership)) ||
        (capacity && !output)) return -1;
    try {
        auto start=Clock::now(); const auto& c=*config;
        std::vector<Box> pieces, groups;
        for (int i=0;i<count;++i) {
            const auto& p=input[i]; Box b{};
            for (int k=0;k<8;++k) if (!std::isfinite(p.quad[k])) return -1;
            if (!std::isfinite(p.width) || !std::isfinite(p.height) ||
                !std::isfinite(p.angle) || !std::isfinite(p.score) ||
                !std::isfinite(p.center[0]) || !std::isfinite(p.center[1]) ||
                p.head<0 || p.head>10) return -1;
            for (int k=0;k<4;++k) b.q[k]={p.quad[k*2],p.quad[k*2+1]};
            b.center={p.center[0],p.center[1]}; b.w=p.width; b.h=p.height;
            b.angle=p.angle; b.score=p.score; b.input=i; bbox(b);
            (p.head<6 ? pieces : groups).push_back(b);
        }
        pieces=dedupe(pieces,c); auto deduped=Clock::now();
        int n=static_cast<int>(pieces.size()); std::vector<int> parent(n);
        std::iota(parent.begin(),parent.end(),0);
        for (int i=0;i<n;++i) for (int j=i+1;j<n;++j) if (compatible(pieces[i],pieces[j],c)) {
            int a=find(parent,i),b=find(parent,j); if (a!=b) parent[b]=a;
        }
        std::vector<int> roots, member(count,-1); std::vector<std::vector<Box>> components;
        for (int i=0;i<n;++i) {
            int root=find(parent,i); auto it=std::find(roots.begin(),roots.end(),root);
            int index=static_cast<int>(it-roots.begin());
            if (it==roots.end()) { roots.push_back(root); components.emplace_back(); }
            components[index].push_back(pieces[i]); member[pieces[i].input]=index;
        }
        auto connected=Clock::now(); std::vector<Box> lines;
        for (const auto& comp : components) lines.push_back(merge(comp));
        auto fitted=Clock::now(); groups=dedupe(groups,c);
        std::stable_sort(groups.begin(),groups.end(),[](const Box& a,const Box& b) { return a.w*a.h<b.w*b.h; });
        for (const Box& g : groups) {
            V gu=basis(g),gn=normal(gu); std::vector<int> selected; std::vector<double> heights;
            std::vector<Box> comp;
            for (size_t i=0;i<lines.size();++i) {
                const Box& line=lines[i];
                if (angle_diff(g.angle,line.angle)>c.max_angle_difference) continue;
                V delta=sub(line.center,g.center);
                if (std::abs(dot(delta,gu))<=g.w/2+line.w/2 && std::abs(dot(delta,gn))<=g.h*c.group_across_factor) {
                    selected.push_back(static_cast<int>(i)); heights.push_back(line.h); comp.push_back(line);
                }
            }
            if (selected.size()<2) continue;
            std::sort(heights.begin(),heights.end()); size_t m=heights.size()/2;
            double typical=heights.size()%2 ? heights[m] : (heights[m-1]+heights[m])/2;
            if (g.h>c.max_height_ratio*typical) continue;
            Box merged=merge(comp); std::vector<Box> kept;
            for (size_t i=0;i<lines.size();++i)
                if (std::find(selected.begin(),selected.end(),static_cast<int>(i))==selected.end()) kept.push_back(lines[i]);
            kept.push_back(merged); lines=std::move(kept);
        }
        lines=dedupe(lines,c); auto finished=Clock::now();
        if (static_cast<int>(lines.size())>capacity) return -2;
        for (size_t i=0;i<lines.size();++i) {
            const Box& b=lines[i]; GocrLine out{};
            for (int k=0;k<4;++k) { out.quad[k*2]=b.q[k][0]; out.quad[k*2+1]=b.q[k][1]; }
            out.center[0]=b.center[0]; out.center[1]=b.center[1]; out.width=b.w; out.height=b.h;
            out.angle=b.angle; out.score=b.score; out.piece_count=b.pieces; output[i]=out;
        }
        std::copy(member.begin(),member.end(),membership);
        *stats={ms(start,deduped),ms(deduped,connected),ms(connected,fitted),ms(fitted,finished),
                ms(start,finished),n,static_cast<int32_t>(components.size()),int64_t(n)*(n-1)/2};
        return static_cast<int>(lines.size());
    } catch (...) { return -3; }
}
