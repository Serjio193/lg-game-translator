#include "unicode.h"
#include <algorithm>
#include <cstdint>
#include <iterator>
#include <stdexcept>
#include <vector>
#include "unicode_tables.h"

namespace gocr {
namespace {
uint32_t ccc(uint32_t cp) {
    auto it=std::lower_bound(std::begin(combining),std::end(combining),cp,
        [](const Combining& a,uint32_t b){return a.cp<b;});
    return it!=std::end(combining) && it->cp==cp ? it->value : 0;
}
void decompose(uint32_t cp,std::vector<uint32_t>& out) {
    if (cp>=0xac00 && cp<0xac00+11172) {
        uint32_t s=cp-0xac00;
        out.push_back(0x1100+s/588); out.push_back(0x1161+(s%588)/28);
        if (s%28) out.push_back(0x11a7+s%28);
        return;
    }
    auto it=std::lower_bound(std::begin(decompositions),std::end(decompositions),cp,
        [](const Decomposition& a,uint32_t b){return a.cp<b;});
    if (it==std::end(decompositions) || it->cp!=cp) out.push_back(cp);
    else { decompose(it->a,out); if (it->b) decompose(it->b,out); }
}
uint32_t compose(uint32_t a,uint32_t b) {
    if (a>=0x1100 && a<0x1113 && b>=0x1161 && b<0x1176)
        return 0xac00+((a-0x1100)*21+b-0x1161)*28;
    if (a>=0xac00 && a<0xac00+11172 && (a-0xac00)%28==0 && b>0x11a7 && b<0x11c3)
        return a+b-0x11a7;
    auto key=std::make_pair(a,b);
    auto it=std::lower_bound(std::begin(compositions),std::end(compositions),key,
        [](const Composition& x,const std::pair<uint32_t,uint32_t>& y){
            return std::make_pair(x.a,x.b)<y;
        });
    return it!=std::end(compositions) && it->a==a && it->b==b ? it->cp : 0;
}
void append_utf8(uint32_t cp,std::string& out) {
    if (cp<128) out+=char(cp);
    else if (cp<2048) { out+=char(0xc0|(cp>>6)); out+=char(0x80|(cp&63)); }
    else if (cp<65536) {
        out+=char(0xe0|(cp>>12)); out+=char(0x80|((cp>>6)&63)); out+=char(0x80|(cp&63));
    } else {
        out+=char(0xf0|(cp>>18)); out+=char(0x80|((cp>>12)&63));
        out+=char(0x80|((cp>>6)&63)); out+=char(0x80|(cp&63));
    }
}
}
std::string nfc_strip(const std::string& input) {
    std::vector<uint32_t> chars;
    for (size_t i=0;i<input.size();) {
        uint8_t first=uint8_t(input[i++]);
        int n=first<128 ? 0 : (first<224 ? 1 : (first<240 ? 2 : 3));
        uint32_t cp=first & (n ? ((1<<(6-n))-1) : 127);
        if (i+n>input.size()) throw std::runtime_error("truncated label UTF-8");
        for (int k=0;k<n;++k) {
            uint8_t b=uint8_t(input[i++]);
            if ((b&0xc0)!=0x80) throw std::runtime_error("invalid label UTF-8");
            cp=(cp<<6)|(b&63);
        }
        if (cp>0x10ffff || (cp>=0xd800 && cp<=0xdfff))
            throw std::runtime_error("invalid Unicode scalar");
        decompose(cp,chars);
    }
    for (size_t i=1;i<chars.size();++i) {
        size_t k=i;
        while (k && ccc(chars[k]) && ccc(chars[k-1])>ccc(chars[k])) {
            std::swap(chars[k],chars[k-1]); --k;
        }
    }
    std::vector<uint32_t> result;
    size_t starter=0;
    uint32_t previous=0;
    for (uint32_t cp:chars) {
        uint32_t cc=ccc(cp);
        uint32_t joined=result.empty() ? 0 : compose(result[starter],cp);
        if (joined && (previous<cc || previous==0)) result[starter]=joined;
        else {
            if (!cc) starter=result.size();
            result.push_back(cp); previous=cc;
        }
    }
    auto space=[](uint32_t cp){return std::binary_search(std::begin(whitespace),std::end(whitespace),cp);};
    size_t begin=0,end=result.size();
    while (begin<end && space(result[begin])) ++begin;
    while (end>begin && space(result[end-1])) --end;
    std::string out;
    for (size_t i=begin;i<end;++i) append_utf8(result[i],out);
    return out;
}
}
