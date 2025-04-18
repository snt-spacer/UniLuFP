# Minimum CMake version required
cmake_minimum_required(VERSION 3.16)

# Project name and version
project(test_motor_connection VERSION 1.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add source files
add_executable(test_motor_connection 
  src/test_can.cpp
)

# Include directories
target_include_directories(test_motor_connection PRIVATE 
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Link libraries
# target_link_libraries(test_motor_connection PRIVATE some_library)