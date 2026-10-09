cmake_minimum_required(VERSION 3.16)
project(gocr_postprocess LANGUAGES CXX)
add_library(gocr_postprocess SHARED gocr_postprocess.cpp)
target_compile_features(gocr_postprocess PRIVATE cxx_std_17)
target_compile_options(gocr_postprocess PRIVATE -O2 -Wall -Wextra -Werror
    -fno-fast-math -ffp-contract=off)
set_target_properties(gocr_postprocess PROPERTIES CXX_VISIBILITY_PRESET hidden)
install(TARGETS gocr_postprocess LIBRARY DESTINATION lib)
