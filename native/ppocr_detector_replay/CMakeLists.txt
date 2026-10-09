cmake_minimum_required(VERSION 3.16)
project(ppocr_detector_replay LANGUAGES CXX)
set(PICCAP_UNICAPTURE "" CACHE PATH "Existing PicCap unicapture source directory")
set(NCNN_SOURCE "" CACHE PATH "Pinned ncnn source")
set(NCNN_BUILD "" CACHE PATH "Target ncnn build")
foreach(path "${PICCAP_UNICAPTURE}/text_detector.cpp" "${NCNN_SOURCE}/src/net.h"
             "${NCNN_BUILD}/src/libncnn.a")
    if(NOT EXISTS "${path}")
        message(FATAL_ERROR "Required existing source/build missing: ${path}")
    endif()
endforeach()
add_library(ppocr_detector_replay SHARED
    "${PICCAP_UNICAPTURE}/text_detector.cpp"
    "${PICCAP_UNICAPTURE}/text_regions.cpp"
    "${PICCAP_UNICAPTURE}/ocr_detector_core/neural.cpp"
    "${PICCAP_UNICAPTURE}/ocr_detector_core/image.cpp")
target_include_directories(ppocr_detector_replay PRIVATE
    "${PICCAP_UNICAPTURE}" "${NCNN_SOURCE}/src" "${NCNN_BUILD}/src")
target_compile_features(ppocr_detector_replay PRIVATE cxx_std_11)
target_compile_options(ppocr_detector_replay PRIVATE -Wall -Wextra -fno-fast-math)
target_link_libraries(ppocr_detector_replay PRIVATE "${NCNN_BUILD}/src/libncnn.a" pthread)
