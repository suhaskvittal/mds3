cmake_minimum_required(VERSION 3.20.2)
project(MemSim VERSION 1.0)
if (CMAKE_BUILD_TYPE MATCHES "Release")
    set(COMPILE_OPTIONS
        -O3
        -fno-strict-aliasing
        -Wno-deprecated
        -Wno-unknown-warming-option
        -Wno-self-assign
        -Wno-unused-parameter
        -Wno-unused-but-set-variable
        -Wunused)
elseif (CMAKE_BUILD_TYPE MATCHES "Profile")
    set(COMPILE_OPTIONS
        -O1
        -fno-strict-aliasing
        -Wno-deprecated
        -Wno-unknown-warming-option
        -Wno-self-assign
        -Wno-unused-parameter
        -Wno-unused-but-set-variable
        -Wunused
        -g)
else()
    set(COMPILE_OPTIONS
        -g0
        -Wall)
endif()

set(CMAKE_CXX_STANDARD 17)

set(SIM_FILES
    src/mcache.cpp
    src/mcore.cpp
    src/memsys_dramsim3.cpp
    src/os.cpp
    src/sim.cpp
)

# memsim executable
add_executable(sim ${SIM_FILES})
target_compile_options(sim PRIVATE ${COMPILE_OPTIONS})
target_include_directories(sim PRIVATE "src")
target_compile_definitions(sim PRIVATE DRAMSIM3)

add_subdirectory(DRAMsim3)

find_package(ZLIB)
target_link_libraries(sim PRIVATE ZLIB::ZLIB dramsim3)

