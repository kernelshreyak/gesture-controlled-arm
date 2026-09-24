# Model provenance

The Panda arm geometry and dynamics are derived from [pmh5050/panda_ign](https://github.com/pmh5050/panda_ign); see the adjacent `models/panda/UPSTREAM.md` and license.

The five-finger hand URDF and meshes come from [Tesollo's DG-5F ROS 2 repository](https://github.com/tesollodelto/dg5f_ros2), commit `9e9af1221cc82e4613a6f18210288f7782b53011`. They are distributed under the BSD 3-Clause license in `LICENSE`. The copied source is `dg5f_right.urdf` and `meshes/dg5f_right/`.

`model.sdf` combines the Panda arm with the DG-5F hand, replacing the Panda's two-finger gripper. It was generated with `scripts/build_panda_five_model.py`, which converts the Tesollo URDF through SDFormat and adds Gazebo position controllers. The adapter joint and controller gains are experiment-specific additions.
