# Included by the existing hyperion-webos build after unicapture is defined.
add_executable(gocr-current-benchmark benchmark_current.c
    ${PROJECT_SOURCE_DIR}/src/log.c ${PROJECT_SOURCE_DIR}/src/utils.c
    ${PROJECT_SOURCE_DIR}/src/socket_io.c)
target_include_directories(gocr-current-benchmark PRIVATE
    ${PROJECT_SOURCE_DIR}/unicapture ${PROJECT_SOURCE_DIR}/src ${PROJECT_BINARY_DIR})
target_link_libraries(gocr-current-benchmark unicapture fbs flatccrt pthread dl rt
    ${GTHREAD2_LDFLAGS} ${PMLOG_LDFLAGS})
add_executable(gocr-selected-frame-replay replay_selected_frame.c gocr_frame_transport.c)
