# Test motor connection

This is a minimal package to test t-motor connection. This package is ignored by `colcon build` command.

## Build

To build the package using CMake, follow these steps:

Create a build directory:

```bash
cmake -S . -B build # If build directory has not been made
cd build
cmake --build .
```

## Virtual CAN test

```bash
sudo modprobe vcan
sudo ip link add dev can0 type vcan
sudo ip link set can0 txqueuelen 1000
sudo ip link set up can0
```
