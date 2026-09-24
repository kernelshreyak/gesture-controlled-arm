# Panda model provenance

The model and meshes in this directory come from [`pmh5050/panda_ign`](https://github.com/pmh5050/panda_ign), commit `30aa6374677da97067658f397952e88ee27fceb3`. That repository is a fork of Andrej Orsula's Panda Gazebo description and declares a BSD license; see `LICENSE` here.

The upstream SDF geometry, kinematics, meshes, and inertia data are retained. This experiment adds one left-finger contact sensor, a joint-state publisher, and Gazebo-native position controllers. The upstream authors caution that dynamic parameters are estimates, so the force signal is experimental rather than calibrated hardware force.
