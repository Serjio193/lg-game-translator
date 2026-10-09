cmake_minimum_required(VERSION 3.16)
project(gocr_recognizer_native LANGUAGES CXX)
add_subdirectory(../gocr_detector_native detector)
add_library(gocr_recognizer_native SHARED gocr_recognizer.cpp image_ops.cpp labels.cpp
    unicode.cpp sha256.cpp full_pipeline.cpp)
target_compile_features(gocr_recognizer_native PRIVATE cxx_std_17)
target_compile_options(gocr_recognizer_native PRIVATE -O2 -Wall -Wextra -Werror
    -fno-fast-math -ffp-contract=off)
target_include_directories(gocr_recognizer_native PUBLIC . ../gocr_detector_native ../gocr_postprocess)
target_link_libraries(gocr_recognizer_native PRIVATE gocr_detector_native dl pthread)
set_target_properties(gocr_recognizer_native PROPERTIES BUILD_RPATH "$ORIGIN;$ORIGIN/../gocr_detector_native" INSTALL_RPATH "$ORIGIN;$ORIGIN/../gocr_detector_native")
add_executable(gocr_recognizer_probe native_probe.cpp image_ops.cpp unicode.cpp sha256.cpp)
target_compile_features(gocr_recognizer_probe PRIVATE cxx_std_17)
target_compile_options(gocr_recognizer_probe PRIVATE -O2 -Wall -Wextra -Werror
    -fno-fast-math -ffp-contract=off)
install(TARGETS gocr_recognizer_native LIBRARY DESTINATION lib)
