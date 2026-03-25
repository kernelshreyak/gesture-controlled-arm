import math

import pybullet as p
import pybullet_data


class SimpleHandSim:
    def __init__(self, use_gui=True, motor_force=6.0, max_velocity=10.0):
        self.use_gui = use_gui
        self.motor_force = motor_force
        self.max_velocity = max_velocity
        self.client_id = None
        self.body_id = None
        self.joint_map = {}

    def connect(self):
        mode = p.GUI if self.use_gui else p.DIRECT
        self.client_id = p.connect(mode)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        p.loadURDF("plane.urdf")

    def close(self):
        if self.client_id is not None:
            p.disconnect(self.client_id)
        self.client_id = None

    def build(self):
        # Base arm segments
        base_half = [0.05, 0.05, 0.15]
        forearm_half = [0.045, 0.045, 0.12]
        palm_half = [0.06, 0.02, 0.03]

        base_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=base_half)
        base_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=base_half, rgbaColor=[0.6, 0.6, 0.6, 1])

        forearm_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=forearm_half)
        forearm_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=forearm_half, rgbaColor=[0.5, 0.5, 0.5, 1])

        palm_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=palm_half)
        palm_vis = p.createVisualShape(p.GEOM_BOX, halfExtents=palm_half, rgbaColor=[0.8, 0.6, 0.4, 1])

        link_masses = []
        link_collision = []
        link_visual = []
        link_positions = []
        link_orientations = []
        link_inertial_pos = []
        link_inertial_orn = []
        link_parent = []
        link_joint_types = []
        link_joint_axis = []

        # Forearm link
        link_masses.append(0.5)
        link_collision.append(forearm_col)
        link_visual.append(forearm_vis)
        link_positions.append([0, 0, base_half[2] + forearm_half[2]])
        link_orientations.append([0, 0, 0, 1])
        link_inertial_pos.append([0, 0, 0])
        link_inertial_orn.append([0, 0, 0, 1])
        link_parent.append(0)
        link_joint_types.append(p.JOINT_FIXED)
        link_joint_axis.append([0, 0, 1])

        # Palm link
        link_masses.append(0.2)
        link_collision.append(palm_col)
        link_visual.append(palm_vis)
        link_positions.append([0, 0, forearm_half[2] + palm_half[2]])
        link_orientations.append([0, 0, 0, 1])
        link_inertial_pos.append([0, 0, 0])
        link_inertial_orn.append([0, 0, 0, 1])
        link_parent.append(1)
        link_joint_types.append(p.JOINT_FIXED)
        link_joint_axis.append([0, 0, 1])

        palm_link_index = 2

        def add_finger(name, base_offset, segment_lengths, color):
            parent = palm_link_index
            for seg_idx, length in enumerate(segment_lengths):
                half = [0.008, 0.008, length / 2.0]
                col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half)
                vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=color)

                link_masses.append(0.02)
                link_collision.append(col)
                link_visual.append(vis)
                if seg_idx == 0:
                    link_positions.append([base_offset[0], base_offset[1], palm_half[2] + length / 2.0])
                else:
                    link_positions.append([0, 0, segment_lengths[seg_idx - 1] / 2.0 + length / 2.0])
                link_orientations.append([0, 0, 0, 1])
                link_inertial_pos.append([0, 0, 0])
                link_inertial_orn.append([0, 0, 0, 1])
                link_parent.append(parent)
                link_joint_types.append(p.JOINT_REVOLUTE)
                link_joint_axis.append([1, 0, 0])

                joint_name = f"{name}_{seg_idx}"
                self.joint_map[joint_name] = len(link_masses) - 1
                parent = len(link_masses) - 1

        add_finger("thumb", [-0.035, -0.02, 0], [0.03, 0.025, 0.02], [0.7, 0.5, 0.4, 1])
        add_finger("index", [-0.02, 0.03, 0], [0.035, 0.03, 0.025], [0.8, 0.6, 0.5, 1])
        add_finger("middle", [0.0, 0.035, 0], [0.04, 0.035, 0.03], [0.8, 0.6, 0.5, 1])
        add_finger("ring", [0.02, 0.03, 0], [0.037, 0.032, 0.027], [0.8, 0.6, 0.5, 1])
        add_finger("pinky", [0.035, 0.02, 0], [0.03, 0.025, 0.02], [0.8, 0.6, 0.5, 1])

        self.body_id = p.createMultiBody(
            baseMass=1.0,
            baseCollisionShapeIndex=base_col,
            baseVisualShapeIndex=base_vis,
            basePosition=[0, 0, 0.2],
            baseOrientation=[0, 0, 0, 1],
            linkMasses=link_masses,
            linkCollisionShapeIndices=link_collision,
            linkVisualShapeIndices=link_visual,
            linkPositions=link_positions,
            linkOrientations=link_orientations,
            linkInertialFramePositions=link_inertial_pos,
            linkInertialFrameOrientations=link_inertial_orn,
            linkParentIndices=link_parent,
            linkJointTypes=link_joint_types,
            linkJointAxis=link_joint_axis,
        )

        for joint_index in range(p.getNumJoints(self.body_id)):
            p.setJointMotorControl2(
                self.body_id,
                joint_index,
                controlMode=p.POSITION_CONTROL,
                targetPosition=0,
                force=self.motor_force,
                maxVelocity=self.max_velocity,
            )

    def set_finger_targets(self, finger_targets):
        for name, angles in finger_targets.items():
            for i, angle in enumerate(angles):
                joint_name = f"{name}_{i}"
                joint_idx = self.joint_map.get(joint_name)
                if joint_idx is None:
                    continue
                p.setJointMotorControl2(
                    self.body_id,
                    joint_idx,
                    controlMode=p.POSITION_CONTROL,
                    targetPosition=angle,
                    force=self.motor_force,
                    maxVelocity=self.max_velocity,
                )

    def step(self, dt=1.0 / 240.0):
        p.setTimeStep(dt)
        p.stepSimulation()
