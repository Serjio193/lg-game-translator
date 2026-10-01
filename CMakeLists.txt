cmake_minimum_required(VERSION 3.13)
project(lg_game_capture_probe C)

set(CMAKE_C_STANDARD 99)
add_executable(lg-game-capture-probe probe/main.c)
target_link_libraries(lg-game-capture-probe dl)
install(TARGETS lg-game-capture-probe RUNTIME DESTINATION bin)
