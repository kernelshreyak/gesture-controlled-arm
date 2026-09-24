#!/usr/bin/env python3
"""Generate the combined Panda + Tesollo DG-5F Gazebo model from vendored sources."""

from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


PACKAGE = Path(__file__).resolve().parents[1] / 'ros2_ws/src/index_finger_experiment'
PANDA = PACKAGE / 'models/panda/model.sdf'
HAND = PACKAGE / 'models/panda_five/dg5f_right.urdf'
OUTPUT = PACKAGE / 'models/panda_five/model.sdf'

# Grasp assist is parked until the grab is fixed: with it on, the cube starts
# locked to the palm and relies on grasp_assist_node (launch grasp_assist:=true)
# to release it.
GRASP_ASSIST = False

sys.path.insert(0, str(PACKAGE))
from index_finger_experiment.arm_ik import READY  # noqa: E402


def add_friction(collision, mu='1.5'):
    surface = collision.find('surface')
    if surface is None:
        surface = ET.SubElement(collision, 'surface')
    friction = surface.find('friction')
    if friction is None:
        friction = ET.SubElement(surface, 'friction')
    for engine, first, second in (('ode', 'mu', 'mu2'), ('bullet', 'friction', 'friction2')):
        coefficients = ET.SubElement(friction, engine)
        ET.SubElement(coefficients, first).text = mu
        ET.SubElement(coefficients, second).text = mu
    contact = ET.SubElement(surface, 'contact')
    ET.SubElement(ET.SubElement(contact, 'ode'), 'min_depth').text = '0.001'


def main():
    panda_tree = ET.parse(PANDA)
    panda_root = panda_tree.getroot()
    panda_root.set('version', '1.12')
    model = panda_root.find('model')
    model.set('name', 'panda_five')

    for child in list(model):
        if child.tag == 'link' and child.get('name') in ('panda_leftfinger', 'panda_rightfinger'):
            model.remove(child)
        elif child.tag == 'joint' and child.get('name') in ('panda_finger_joint1', 'panda_finger_joint2'):
            model.remove(child)
        elif child.tag == 'plugin' and child.findtext('joint_name') in ('panda_finger_joint1', 'panda_finger_joint2'):
            model.remove(child)

    # Retain the Panda hand frame as the rigid arm attachment, but render the
    # more detailed five-finger hand in its place.
    panda_hand = next(link for link in model.findall('link') if link.get('name') == 'panda_hand')
    for child in list(panda_hand):
        if child.tag in ('visual', 'collision'):
            panda_hand.remove(child)

    for uri in model.iter('uri'):
        if uri.text and uri.text.startswith('meshes/'):
            uri.text = 'model://panda/' + uri.text

    converted = subprocess.run(['gz', 'sdf', '-p', str(HAND)], check=True,
                               capture_output=True, text=True)
    hand_model = ET.fromstring(converted.stdout).find('model')
    for child in hand_model:
        if child.tag not in ('link', 'joint'):
            continue
        if child.tag == 'link':
            # High friction lets the fingers hold the cube. Self-collision is
            # off by default, so adjacent finger links do not snag each other.
            for collision in child.findall('collision'):
                add_friction(collision)
        for uri in child.iter('uri'):
            uri.text = uri.text.replace('model://dg5f_description/meshes/dg5f_right/',
                                        'model://panda_five/meshes/dg5f_right/')
        model.append(child)

    # The converted hand's root link has no pose, which would leave it at the
    # Panda model origin; place it on the flange. A joint pose would only move
    # the joint frame, not the link.
    hand_root = next(link for link in model.findall('link') if link.get('name') == 'rl_dg_mount')
    hand_root.insert(0, ET.Element('pose', relative_to='panda_hand'))
    hand_root.find('pose').text = '0 0 0.03 0 0 0'

    mount = ET.SubElement(model, 'joint', name='panda_dg5f_mount', type='fixed')
    ET.SubElement(mount, 'parent').text = 'panda_hand'
    ET.SubElement(mount, 'child').text = 'rl_dg_mount'

    for finger in range(1, 6):
        for segment in range(1, 5):
            name = f'rj_dg_{finger}_{segment}'
            plugin = ET.SubElement(model, 'plugin',
                                   filename='gz-sim-joint-position-controller-system',
                                   name='gz::sim::systems::JointPositionController')
            for tag, value in (
                ('joint_name', name), ('topic', f'/panda_five/{name}/target'),
                # Velocity commands track the target without the overshoot that
                # torque control gave these light finger links; the gain is in
                # 1/s and cmd limits are joint speeds in rad/s.
                ('initial_position', '0'), ('use_velocity_commands', 'true'),
                ('p_gain', '12'), ('d_gain', '0'), ('cmd_max', '4'), ('cmd_min', '-4')):
                ET.SubElement(plugin, tag).text = value

    # Grasp assist: grasp_assist_node locks the cube to the palm while the fist
    # is closed around it. The joint starts attached, so the launch detaches it
    # while the world is still paused.
    if GRASP_ASSIST:
        assist = ET.SubElement(model, 'plugin', filename='gz-sim-detachable-joint-system',
                               name='gz::sim::systems::DetachableJoint')
        for tag, value in (('parent_link', 'rl_dg_mount'), ('child_model', 'cube'),
                           ('child_link', 'link'), ('attach_topic', '/cube/attach'),
                           ('detach_topic', '/cube/detach'), ('output_topic', '/cube/state'),
                           ('suppress_child_warning', 'true')):
            ET.SubElement(assist, tag).text = value

    # Velocity commands hold the arm on target despite the hand's weight (plain
    # torque control sagged 0.16-0.24 rad), and it starts in the raised pose.
    for plugin in model.findall('plugin'):
        joint = plugin.findtext('joint_name') or ''
        if joint.startswith('panda_joint'):
            index = int(joint[-1]) - 1
            for child in list(plugin):
                if child.tag not in ('joint_name', 'topic'):
                    plugin.remove(child)
            for tag, value in (('initial_position', f'{READY[index]:.4f}'),
                               ('use_velocity_commands', 'true'), ('p_gain', '6'),
                               ('d_gain', '0'), ('cmd_max', '2'), ('cmd_min', '-2')):
                ET.SubElement(plugin, tag).text = value

    ET.indent(panda_tree, space='  ')
    panda_tree.write(OUTPUT, encoding='unicode', xml_declaration=True)
    print(OUTPUT)


if __name__ == '__main__':
    main()
