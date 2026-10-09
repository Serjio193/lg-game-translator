#include "profiler.h"
#include <stdexcept>

// Deterministic durations exercise node separation, reset, count, median and %.
int main(int argc,char** argv) {
    if (argc!=2) throw std::runtime_error("output path required");
    gocr::OpProfiler profiler(argv[1]);
    auto* callbacks=&profiler.callbacks;
    callbacks->timed(callbacks,"CONV_2D",999000,1,0);
    profiler.invoked(999);
    profiler.reset();
    callbacks->timed(callbacks,"CONV_2D",3000,1,0);
    callbacks->timed(callbacks,"CONV_2D",1000,1,0);
    callbacks->timed(callbacks,"CONV_2D",2000,1,0);
    callbacks->timed(callbacks,"CONV_2D",8000,2,0);
    callbacks->timed(callbacks,"CONV_2D",10000,2,0);
    callbacks->timed(callbacks,"ADD",1000,1,1);
    profiler.invoked(25);
    return 0;
}
