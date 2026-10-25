cmake_minimum_required(VERSION 3.22)
project(glshim CXX)

set(OPTION_ASTC_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../astc-codec ${CMAKE_CURRENT_BINARY_DIR}/astc-codec)

add_library(glshim SHARED glshim.cpp)
target_compile_features(glshim PRIVATE cxx_std_17)
target_compile_options(glshim PRIVATE -fno-exceptions -fno-rtti -O2)
target_include_directories(glshim PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../astc-codec/include)
target_link_libraries(glshim log android dl astc-codec)
