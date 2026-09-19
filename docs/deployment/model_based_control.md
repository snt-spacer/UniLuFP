# Model Based Control (MBC)

This doc id for [pingu_mbc](ros_ws/src/pingu_mbc).

## Structure

### Task

state(base_x, base_y, base_theta, joint1, joint2, ....)
->
Specific task
-> Objective function `y`

### Controller

Objective function `y`
->
commands(thruster)
