cmake_minimum_required(VERSION 3.13)
project(lg_text_recognition_bench CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror")

if(NOT NCNN_ROOT)
    message(FATAL_ERROR "Set NCNN_ROOT to a configured ncnn build directory")
endif()
if(NOT NCNN_SOURCE)
    message(FATAL_ERROR "Set NCNN_SOURCE to the ncnn source checkout")
endif()
add_executable(lg-ppocrv5-rec-bench recognize.cpp pgm.cpp)
target_include_directories(lg-ppocrv5-rec-bench PRIVATE
    "${NCNN_ROOT}/src" "${NCNN_SOURCE}/src")
target_link_libraries(lg-ppocrv5-rec-bench
    "${NCNN_ROOT}/src/libncnn.a" dl pthread)

if(TESSERACT_SOURCE AND TESSERACT_LIBRARY AND LEPTONICA_LIBRARY)
    set(GENERIC_MAJOR_VERSION 5)
    set(GENERIC_MINOR_VERSION 4)
    set(GENERIC_MICRO_VERSION 1)
    set(PACKAGE_VERSION 5.4.1)
    set(TESSERACT_GENERATED_INCLUDE "${CMAKE_CURRENT_BINARY_DIR}/generated")
    file(MAKE_DIRECTORY "${TESSERACT_GENERATED_INCLUDE}/tesseract")
    configure_file(
        "${TESSERACT_SOURCE}/include/tesseract/version.h.in"
        "${TESSERACT_GENERATED_INCLUDE}/tesseract/version.h" @ONLY)
    add_executable(lg-tesseract-api-bench tesseract_api.cpp pgm.cpp)
    target_include_directories(lg-tesseract-api-bench PRIVATE
        "${TESSERACT_SOURCE}/include" "${TESSERACT_GENERATED_INCLUDE}")
    target_link_libraries(lg-tesseract-api-bench
        "${TESSERACT_LIBRARY}" "${LEPTONICA_LIBRARY}" dl pthread)
    target_link_options(lg-tesseract-api-bench PRIVATE "-Wl,--allow-shlib-undefined")
endif()
