#include "labels.h"
#include <cstdint>
#include <fstream>
#include <iterator>
#include <map>
#include <stdexcept>
namespace gocr {
namespace {
uint64_t varint(const std::string& s,size_t& pos) {
    uint64_t value=0;
    for (int shift=0;shift<70;shift+=7) {
        if (pos>=s.size()) throw std::runtime_error("truncated protobuf");
        uint8_t byte=uint8_t(s[pos++]);
        if (shift==63 && byte>1) throw std::runtime_error("protobuf overflow");
        value|=uint64_t(byte&127)<<shift;
        if (byte<128) return value;
    }
    throw std::runtime_error("invalid protobuf varint");
}
struct Field { int number,wire; uint64_t integer=0; std::string bytes; };
Field field(const std::string& s,size_t& pos) {
    uint64_t tag=varint(s,pos);
    Field f{int(tag>>3),int(tag&7),0,{}};
    if (f.wire==0) f.integer=varint(s,pos);
    else {
        uint64_t n=f.wire==2 ? varint(s,pos) : (f.wire==1 ? 8 : (f.wire==5 ? 4 : 0));
        if ((f.wire!=1 && f.wire!=2 && f.wire!=5) || n>s.size()-pos)
            throw std::runtime_error("invalid protobuf field");
        f.bytes=s.substr(pos,size_t(n)); pos+=size_t(n);
    }
    return f;
}
}
std::vector<std::string> load_labels(const char* path) {
    std::ifstream file(path,std::ios::binary);
    if (!file) throw std::runtime_error("cannot open original label map");
    std::string data((std::istreambuf_iterator<char>(file)),{});
    std::map<int,std::string> labels;
    for (size_t pos=0;pos<data.size();) {
        auto entry=field(data,pos);
        if (entry.number!=1 || entry.wire!=2) continue;
        std::string label; int id=0;
        for (size_t k=0;k<entry.bytes.size();) {
            auto f=field(entry.bytes,k);
            if (f.number==1 && f.wire==2) label=f.bytes;
            if (f.number==2 && f.wire==0) id=int(f.integer);
        }
        labels[id]=label;
    }
    std::vector<std::string> result;
    for (const auto& item:labels) {
        if (item.first!=int(result.size())) throw std::runtime_error("label IDs not contiguous");
        result.push_back(item.second);
    }
    if (result.size()!=1292) throw std::runtime_error("original Google label count mismatch");
    return result;
}
}
