#!/usr/bin/env python3
import time
import threading
from dataclasses import dataclass

import numpy as np
import rclpy
from rclpy.node import Node

import mujoco
import mujoco.viewer


@dataclass
class SimFlags:
    paused: bool = False
    close_requested: bool = False


class MujocoSimNode(Node):
    def __init__(self):
        super().__init__("mujoco_sim_node")

        # --- params ---
        self.declare_parameter(
            "model_path", "/UniLuFP/ros_ws/src/mnt/pingu_description/mjcf/pingu.xml")
        self.declare_parameter("gui", True)
        # try to keep wall-clock sync
        self.declare_parameter("realtime", True)
        # used for headless timer; 0 => use m.opt.timestep
        self.declare_parameter("rate_hz", 0.0)

        self.model_path = self.get_parameter("model_path").value
        self.gui = bool(self.get_parameter("gui").value)
        self.realtime = bool(self.get_parameter("realtime").value)
        self.rate_hz = float(self.get_parameter("rate_hz").value)

        if not self.model_path:
            raise RuntimeError("ROS param 'model_path' is empty.")

        # --- mujoco ---
        self.m = mujoco.MjModel.from_xml_path(self.model_path)
        self.d = mujoco.MjData(self.m)

        # --- flags / thread-safety ---
        self.flags = SimFlags()
        self._lock = threading.Lock()

        # Register MuJoCo control callback (called inside mj_step)
        # mujoco.set_mjcb_control(self.mj_control_callback)

        # Headless stepping: timer-based
        self._timer = None
        if not self.gui:
            dt = self.m.opt.timestep
            period = (1.0 / self.rate_hz) if self.rate_hz > 0 else dt
            self._timer = self.create_timer(period, self.timer_step)

        self.get_logger().info(
            f"Loaded model: {self.model_path} | gui={self.gui} | dt={self.m.opt.timestep}"
        )

    # ---------- MuJoCo control callback ----------
    def mj_control_callback(self, model: mujoco.MjModel, data: mujoco.MjData):
        """
        This is the Low-level controller hook.
        Replace this with MPC/LQR etc.
        Must be fast and avoid heavy allocations.
        """
        # Example: zero control
        # data.ctrl[:] = 0.0

        # Example: simple PD for first actuator (only if exists)
        if model.nu > 0:
            data.ctrl[0] = 0.0

    # ---------- GUI callbacks ----------
    def key_callback(self, keycode: int):
        try:
            c = chr(keycode)
        except ValueError:
            return

        with self._lock:
            if c == " ":
                self.flags.paused = not self.flags.paused
            elif c == "Q":
                self.flags.close_requested = True
                self.get_logger().warn("Simulation canceled (Q pressed).")

    # ---------- stepping ----------
    def timer_step(self):
        # headless stepping
        with self._lock:
            if self.flags.close_requested:
                rclpy.shutdown()
                return
            paused = self.flags.paused

        if not paused:
            mujoco.mj_step(self.m, self.d)

    def run_viewer_loop(self):
        """
        GUI mode: viewer loop drives stepping, and we call spin_once inside.
        """
        with mujoco.viewer.launch_passive(self.m, self.d, key_callback=self.key_callback) as viewer:
            while rclpy.ok() and viewer.is_running():
                step_start = time.time()

                with self._lock:
                    if self.flags.close_requested:
                        break
                    paused = self.flags.paused

                if not paused:
                    mujoco.mj_step(self.m, self.d)

                # Optional: viewer option update (same as your example)
                with viewer.lock():
                    viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = int(
                        self.d.time % 2)

                viewer.sync()

                # Let ROS callbacks run (subscriptions/services/timers)
                rclpy.spin_once(self, timeout_sec=0.0)

                # crude realtime sync
                if self.realtime:
                    dt = self.m.opt.timestep
                    sleep_time = dt - (time.time() - step_start)
                    if sleep_time > 0:
                        time.sleep(sleep_time)

        self.get_logger().info("Viewer loop ended.")


def main(args=None):
    rclpy.init(args=args)

    node = MujocoSimNode()

    try:
        if node.gui:
            node.run_viewer_loop()
        else:
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
