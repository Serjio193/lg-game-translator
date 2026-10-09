#include "profiler.h"
#include <fstream>
#include <iomanip>
#include <algorithm>

namespace gocr {
void OpProfiler::reset() {
    std::lock_guard<std::mutex> lock(mutex);
    active.clear();
    totals.clear();
    invoke_ms=0;
    invoke_count=0;
}
void OpProfiler::invoked(double ms) {
    invoke_ms+=ms;
    ++invoke_count;
}
OpProfiler::OpProfiler(const char* file):path(file) {
    callbacks.data=this;
    callbacks.event=[](TelemetryCallbacks*,const char*,uint64_t) {};
    callbacks.op_event=[](TelemetryCallbacks*,const char*,int64_t,int64_t,uint64_t) {};
    callbacks.settings=[](TelemetryCallbacks*,const char*,const void*) {};
    callbacks.begin=begin;
    callbacks.end=end;
    callbacks.timed=timed;
}
uint32_t OpProfiler::begin(TelemetryCallbacks* callbacks,const char* name,int64_t node,int64_t subgraph) {
    auto& p=*static_cast<OpProfiler*>(callbacks->data);
    std::lock_guard<std::mutex> lock(p.mutex);
    uint32_t id=p.next++;
    p.active.emplace(id,Event{name ? name : "",node,subgraph,std::chrono::steady_clock::now()});
    return id;
}
void OpProfiler::end(TelemetryCallbacks* callbacks,uint32_t id) {
    auto& p=*static_cast<OpProfiler*>(callbacks->data);
    const auto now=std::chrono::steady_clock::now();
    std::lock_guard<std::mutex> lock(p.mutex);
    auto it=p.active.find(id);
    if (it==p.active.end()) return;
    auto& total=p.totals[{it->second.name,it->second.node,it->second.subgraph}];
    double ms=std::chrono::duration<double,std::milli>(now-it->second.start).count();
    total.ms+=ms;
    total.samples.push_back(ms);
    p.active.erase(it);
}
void OpProfiler::timed(TelemetryCallbacks* callbacks,const char* name,uint64_t us,int64_t node,int64_t subgraph) {
    auto& p=*static_cast<OpProfiler*>(callbacks->data);
    std::lock_guard<std::mutex> lock(p.mutex);
    auto& total=p.totals[{name ? name : "",node,subgraph}];
    total.ms+=double(us)/1000;
    total.samples.push_back(double(us)/1000);
}
OpProfiler::~OpProfiler() {
    std::ofstream file(path);
    file<<"{\"invoke_count\":"<<invoke_count<<",\"invoke_total_ms\":"<<invoke_ms
        <<",\"operators\":[";
    bool comma=false;
    for (auto& pair:totals) {
        if (comma) file<<',';
        auto& samples=pair.second.samples;
        std::sort(samples.begin(),samples.end());
        size_t mid=samples.size()/2;
        double median=samples.size()%2 ? samples[mid] : (samples[mid-1]+samples[mid])/2;
        file<<"{\"name\":"<<std::quoted(std::get<0>(pair.first))
            <<",\"node_index\":"<<std::get<1>(pair.first)
            <<",\"subgraph_index\":"<<std::get<2>(pair.first)
            <<",\"count\":"<<samples.size()<<",\"total_ms\":"<<pair.second.ms
            <<",\"median_ms\":"<<median
            <<",\"percent_invoke\":"<<(invoke_ms>0 ? pair.second.ms*100/invoke_ms : 0)<<'}';
        comma=true;
    }
    file<<"]}\n";
}
}
