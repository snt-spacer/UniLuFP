
import casadi as ca
import numpy as np
import pinocchio as pin
from pinocchio import casadi as cpin


class DynamicsModel:
    """Dynamics model for the Pingu Air Floating Platform using CasADi and Pinocchio."""

    def __init__(self, urdf_path):
        """
        Initialize the Pinocchio model with the given URDF path.

        :param urdf_path: Path to the URDF file of the robot.
        """
        super().__init__(urdf_path)
        # TODO: Hardcode thruster configuration so far
        #       later this should be read from the URDF

        # disable gravity of pinocchio model
        self.cmodel.gravity.linear = ca.SX([0, -0.098, 0])
        self.cmodel.gravity.angular = ca.SX.zeros(3, 1)

        # Overwrite the number of inputs TODO
        num_thrusters = 8
        num_joints = self.nv - 6
        self.nu = num_thrusters + num_joints

        # Direction vectors for the thrusters
        direction = np.array([
            [0,  1, 0],                        # 1
            [0, -1, 0],                        # 2         <-2 1->
            [1, 0, 0],                        # 3     4 ^/       \^ 8
            [-1, 0, 0],                        # 4       |    <-r->|
            [0,  1, 0],                        # 5     3 v\       /v 7
            [0, -1, 0],                        # 6         <-6 5->
            [1, 0, 0],                        # 7                     x
            [-1, 0, 0]                         # 8                   y-|
        ])

        # Position vectors for the thrusters
        r = 0.23884271247461908
        position = np.array([
            [r, 0, 0],
            [r, 0, 0],
            [0, r, 0],
            [0, r, 0],
            [-r, 0, 0],
            [-r, 0, 0],
            [0, -r, 0],
            [0, -r, 0]
        ])

        # Calculate the torque for each thruster
        torque = np.cross(position, direction)

        # Stack the direction and torque vectors to form the thruster configuration matrix
        B = np.vstack((direction.T, torque.T))  # shape (6, 8)

        self.thruster_configuration = B

        # Set the control constraints
        self.lbu = np.zeros(self.nu)
        self.ubu = np.zeros(self.nu)
        self.lbu[:num_thrusters] = 0
        self.ubu[:num_thrusters] = 1
        self.lbu[num_thrusters:] = -10
        self.ubu[num_thrusters:] = 10

    def project_velocity(self, v):
        """
        Map the velocity input to the model's velocity space.
        """
        v_projected = ca.SX.zeros(self.nv, 1)
        v_projected[:6] = ca.vertcat(
            v[0], v[1], 0, 0, 0, v[5])  # vx, vy, 0, 0, 0, wz
        v_projected[6:] = v[6:]
        return v_projected

    def project_acceleration(self, a):
        """
        Map the acceleration input to the model's acceleration space.
        """
        a_projected = ca.SX.zeros(self.nv, 1)
        a_projected[:6] = ca.vertcat(a[0], a[1], 0, 0, 0, a[5])
        a_projected[6:] = a[6:]
        return a_projected

    def project_control(self, c_u):
        """
        Map the control input to the model's control space.
        """
        c_tau = ca.SX.zeros(self.nv, 1)
        # Apply thruster forces
        c_tau[:6] = self.thruster_configuration @ c_u[:8]
        c_tau[6:] = c_u[8:]
        return c_tau

    def forward_dynamics(self, q, v, u):
        # convert to generalized forces
        tau = self.project_control(u)

        # reduce the dof to 2D space
        a = cpin.aba(self.cmodel, self.cdata, q, v, tau)
        return self.project_acceleration(a)

    def integrate_dynamics(self, x, u, dt):
        q, v = x[:self.nq],  self.project_velocity(x[self.nq:])
        a = self.forward_dynamics(q, v, u)
        q_next = cpin.integrate(self.cmodel, q, v * dt + a * dt**2)
        v_next = v + a * dt
        return ca.vertcat(q_next, v_next)
