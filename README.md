# Gesture-Controlled Bionic Arm

A repository for building a real-time, camera-driven bionic arm system. The goal is to simulate a functional bionic arm in **Webots** first, then move to a physical build later. Control is driven by **MediaPipe** hand pose detection from live video input, with emphasis on **precise finger motion** and intuitive mapping from human hand gestures to a robotic arm.

## Vision
- Real-time hand pose tracking from a camera feed
- High-fidelity finger motion capture and mapping
- Simulated bionic arm in Webots (initial milestone)
- Path to a physical bionic arm prototype
- Optional expansion to ROS 2 + Gazebo for broader robotics workflows

## Planned Stack
- **Hand pose detection**: MediaPipe
- **Simulation**: Webots (initially)
- **Robotics middleware (later)**: ROS 2
- **Advanced simulation (later)**: Gazebo
- **3D models**: Existing CAD assets or basic custom models for learning

## High-Level Architecture (planned)
1. **Camera Input**: Real-time video capture
2. **Hand Pose Inference**: MediaPipe hand landmark detection
3. **Gesture/Hand Mapping**: Convert landmarks to arm & finger joint targets
4. **Simulation/Control**: Drive Webots arm model with joint targets
5. **Physical Prototype**: Replace simulation backend with real actuators

## Models
- MediaPipe Tasks models live in `models/`
- See `models/README.md` for required files and placement

## Milestones (tentative)
1. Setup MediaPipe hand tracking with stable landmark output
2. Build or import a simple arm + hand model in Webots
3. Map finger landmarks to simulated joint angles
4. Add calibration layer for scale and hand size
5. Prototype a full arm motion mapping (wrist + elbow + shoulder)
6. Explore ROS 2 and Gazebo integration
7. Begin hardware planning for a physical model

## Repo Status
This repo is an early-stage scaffold. Expect rapid iteration and structural changes as the simulation and mapping pipeline solidify.

## Contributing
Contributions and ideas are welcome. If you want to help, open an issue with your proposal or start a draft PR.

## License
TBD
