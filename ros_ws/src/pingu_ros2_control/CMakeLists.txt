cmake_minimum_required(VERSION 3.8)
project(pingu_ros2_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

########### Find dependencies ###########
set(THIS_PACKAGE_INCLUDE_DEPENDS
  ament_cmake
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)

foreach(THIS_PACKAGE_INCLUDE_DEPEND ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${THIS_PACKAGE_INCLUDE_DEPEND} REQUIRED)
endforeach()

########### Install ###########
install(
  DIRECTORY bringup/config bringup/launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
