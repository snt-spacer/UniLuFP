cmake_minimum_required(VERSION 3.8)
project(px4-simple)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)

# ----------------------- Cpp settings -----------------------
# include directories
include_directories(
  include
)
# add executables
# add_executable(px4_simple_node src/px4_simple_node.cpp)
# ament_target_dependencies(px4_simple_node
#   rclcpp
# )
# install(TARGETS
#   px4_simple_node
#   DESTINATION lib/${PROJECT_NAME}
# )

# ----------------------- Python settings -----------------------
ament_python_install_package(${PROJECT_NAME})

# # install Python executables
# install(PROGRAMS
#   scripts/px4_simple_node.py
#   DESTINATION lib/${PROJECT_NAME}
# )

# ----------------------- Install directories -----------------------
# install(DIRECTORY
#   launch
#   DESTINATION share/${PROJECT_NAME}/
# )

ament_package()
