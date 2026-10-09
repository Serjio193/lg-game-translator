#pragma once
#include <chrono>
#include <cstdint>
#include <map>
#include <mutex>
#include <string>
#include <tuple>
#include <vector>

namespace gocr {
struct TelemetryCallbacks {
    void* data;
    void (*event)(TelemetryCallbacks*,const char*,uint64_t);
    void (*op_event)(TelemetryCallbacks*,const char*,int64_t,int64_t,uint64_t);
    void (*settings)(TelemetryCallbacks*,const char*,const void*);
    uint32_t (*begin)(TelemetryCallbacks*,const char*,int64_t,int64_t);
    void (*end)(TelemetryCallbacks*,uint32_t);
    void (*timed)(TelemetryCallbacks*,const char*,uint64_t,int64_t,int64_t);
};
class OpProfiler {
public:
    explicit OpProfiler(const char* path);
    ~OpProfiler();
    void reset();
    void invoked(double ms);
    TelemetryCallbacks callbacks{};
private:
    struct Event {
        std::string name;
        int64_t node;
        int64_t subgraph;
        std::chrono::steady_clock::time_point start;
    };
    struct Total { double ms=0; std::vector<double> samples; };
    std::string path;
    std::mutex mutex;
    std::map<uint32_t,Event> active;
    std::map<std::tuple<std::string,int64_t,int64_t>,Total> totals;
    uint32_t next=1;
    double invoke_ms=0;
    uint64_t invoke_count=0;
    static uint32_t begin(TelemetryCallbacks*,const char*,int64_t,int64_t);
    static void end(TelemetryCallbacks*,uint32_t);
    static void timed(TelemetryCallbacks*,const char*,uint64_t,int64_t,int64_t);
};
}
