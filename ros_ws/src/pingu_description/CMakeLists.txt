cmake_minimum_required(VERSION 3.8)
project(pingu_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

########### Find dependencies ###########
set(THIS_PACKAGE_INCLUDE_DEPENDS
  ament_cmake
)

foreach(THIS_PACKAGE_INCLUDE_DEPEND ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${THIS_PACKAGE_INCLUDE_DEPEND} REQUIRED)
endforeach()

install(
  DIRECTORY 
    launch 
    mesh
    rviz 
    urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
