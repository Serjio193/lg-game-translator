#include "gocr_detector.h"
#include <algorithm>
#include <cmath>
#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <sched.h>
#include <stdexcept>
#include <sys/resource.h>
#include <vector>

int main(int argc,char** argv) {
    try {
        if (argc!=8) throw std::runtime_error(
            "usage: gocr_detector_bench MODEL RUNTIME CONFIG FRAME.ppm THREADS XNNPACK ITERATIONS");
        GocrDetectorConfig config{};
        std::ifstream cfg(argv[3],std::ios::binary);
        char magic[8];
        cfg.read(magic,8);
        if (!cfg || std::string(magic,7)!="GDNCFG1") throw std::runtime_error("bad launch snapshot magic");
        cfg.read(reinterpret_cast<char*>(&config),sizeof(config));
        if (!cfg || cfg.peek()!=EOF) throw std::runtime_error("bad launch snapshot size");
        std::ifstream frame(argv[4],std::ios::binary);
        std::string format;
        int width,height,max_value;
        frame>>format>>width>>height>>max_value;
        if (!frame || format!="P6" || width!=1280 || height!=720 || max_value!=255)
            throw std::runtime_error("expected selected RGB PPM 1280x720");
        if (frame.get()!='\n') throw std::runtime_error("unsupported PPM header delimiter");
        std::vector<uint8_t> rgb(1280*720*3);
        frame.read(reinterpret_cast<char*>(rgb.data()),rgb.size());
        if (!frame) throw std::runtime_error("truncated frame pixels");
        const int threads=std::stoi(argv[5]),xnnpack=std::stoi(argv[6]),iterations=std::stoi(argv[7]);
        if (iterations<1 || iterations>1000) throw std::runtime_error("invalid iterations");
        char error[512]={};
        auto deleter=[](GocrDetector* p) { gocr_detector_destroy(p); };
        std::unique_ptr<GocrDetector,decltype(deleter)> detector(
            gocr_detector_create(argv[1],argv[2],threads,xnnpack,&config,error,sizeof(error)),deleter);
        if (!detector) throw std::runtime_error(error);
        auto* d=detector.get();
        if (gocr_detector_prepare(d,rgb.data(),rgb.size())) throw std::runtime_error(gocr_detector_error(d));
        for (int i=0;i<3;++i)
            if (gocr_detector_invoke(d)) throw std::runtime_error(gocr_detector_error(d));
        std::vector<double> samples;
        std::vector<GocrLine> lines(4096);
        GocrDetectorStats stats{};
        // Invoke-only loop: no decode/copy/preprocessing between samples.
        for (int i=0;i<iterations;++i) {
            auto start=std::chrono::steady_clock::now();
            if (gocr_detector_invoke(d))
                throw std::runtime_error(gocr_detector_error(d));
            samples.push_back(std::chrono::duration<double,std::milli>(
                std::chrono::steady_clock::now()-start).count());
        }
        int count=gocr_detector_finish(d,lines.data(),lines.size(),&stats);
        std::vector<double> sorted=samples;
        std::sort(sorted.begin(),sorted.end());
        double median=sorted.size()%2 ? sorted[sorted.size()/2] :
            (sorted[sorted.size()/2-1]+sorted[sorted.size()/2])/2;
        size_t p95=size_t(std::ceil(sorted.size()*.95))-1;
        struct rusage usage{};
        getrusage(RUSAGE_SELF,&usage);
        cpu_set_t cpus;
        CPU_ZERO(&cpus);
        if (sched_getaffinity(0,sizeof(cpus),&cpus)) throw std::runtime_error("cannot read affinity");
        std::cout<<"{\"runtime_version\":\""<<gocr_detector_version(d)<<"\",\"threads\":"<<threads
                 <<",\"explicit_xnnpack\":"<<(xnnpack ? "true" : "false")
                 <<",\"warmups\":3,\"iterations\":"<<iterations
                 <<",\"invoke_min_ms\":"<<sorted.front()<<",\"invoke_median_ms\":"<<median
                 <<",\"invoke_p95_ms\":"<<sorted[p95]<<",\"prepare_ms\":"<<stats.prepare_ms
                 <<",\"decode_ms\":"<<stats.decode_ms<<",\"postprocess_ms\":"<<stats.postprocess_ms
                 <<",\"raw_pieces\":"<<stats.raw_pieces<<",\"raw_groups\":"<<stats.raw_groups
                 <<",\"lines\":"<<count<<",\"max_rss_kib\":"<<usage.ru_maxrss
                 <<",\"affinity\":[";
        bool comma=false;
        for (int i=0;i<CPU_SETSIZE;++i) if (CPU_ISSET(i,&cpus)) {
            if (comma) std::cout<<',';
            std::cout<<i;
            comma=true;
        }
        std::cout<<"],\"samples_ms\":[";
        for (size_t i=0;i<samples.size();++i) {
            if (i) std::cout<<',';
            std::cout<<samples[i];
        }
        std::cout<<"]}\n";
        return 0;
    } catch (const std::exception& exc) {
        std::cerr<<exc.what()<<'\n';
        return 1;
    }
}
