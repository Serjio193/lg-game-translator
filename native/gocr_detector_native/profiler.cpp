#include "profiler.h"
#include <fstream>
#include <iomanip>

namespace gocr {
OpProfiler::OpProfiler(const char* file):path(file) {
    callbacks.data=this;
    callbacks.event=[](TelemetryCallbacks*,const char*,uint64_t) {};
    callbacks.op_event=[](TelemetryCallbacks*,const char*,int64_t,int64_t,uint64_t) {};
    callbacks.settings=[](TelemetryCallbacks*,const char*,const void*) {};
    callbacks.begin=begin;
    callbacks.end=end;
    callbacks.timed=timed;
}
uint32_t OpProfiler::begin(TelemetryCallbacks* callbacks,const char* name,int64_t,int64_t) {
    auto& p=*static_cast<OpProfiler*>(callbacks->data);
    std::lock_guard<std::mutex> lock(p.mutex);
    uint32_t id=p.next++;
    p.active.emplace(id,Event{name ? name : "",std::chrono::steady_clock::now()});
    return id;
}
void OpProfiler::end(TelemetryCallbacks* callbacks,uint32_t id) {
    auto& p=*static_cast<OpProfiler*>(callbacks->data);
    const auto now=std::chrono::steady_clock::now();
    std::lock_guard<std::mutex> lock(p.mutex);
    auto it=p.active.find(id);
    if (it==p.active.end()) return;
    auto& total=p.totals[it->second.name];
    ++total.count;
    total.ms+=std::chrono::duration<double,std::milli>(now-it->second.start).count();
    p.active.erase(it);
}
void OpProfiler::timed(TelemetryCallbacks* callbacks,const char* name,uint64_t us,int64_t,int64_t) {
    auto& p=*static_cast<OpProfiler*>(callbacks->data);
    std::lock_guard<std::mutex> lock(p.mutex);
    auto& total=p.totals[name ? name : ""];
    ++total.count;
    total.ms+=double(us)/1000;
}
OpProfiler::~OpProfiler() {
    std::ofstream file(path);
    file<<"{\"operators\":[";
    bool comma=false;
    for (const auto& pair:totals) {
        if (comma) file<<',';
        file<<"{\"name\":"<<std::quoted(pair.first)<<",\"count\":"<<pair.second.count
            <<",\"total_ms\":"<<pair.second.ms<<'}';
        comma=true;
    }
    file<<"]}\n";
}
}
