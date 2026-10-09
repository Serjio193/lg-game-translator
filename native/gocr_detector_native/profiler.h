#pragma once
#include <chrono>
#include <cstdint>
#include <map>
#include <mutex>
#include <string>

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
    TelemetryCallbacks callbacks{};
private:
    struct Event {
        std::string name;
        std::chrono::steady_clock::time_point start;
    };
    struct Total { uint64_t count=0; double ms=0; };
    std::string path;
    std::mutex mutex;
    std::map<uint32_t,Event> active;
    std::map<std::string,Total> totals;
    uint32_t next=1;
    static uint32_t begin(TelemetryCallbacks*,const char*,int64_t,int64_t);
    static void end(TelemetryCallbacks*,uint32_t);
    static void timed(TelemetryCallbacks*,const char*,uint64_t,int64_t,int64_t);
};
}
