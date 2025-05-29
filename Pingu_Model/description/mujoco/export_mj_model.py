import mujoco
import os
import xml.etree.ElementTree as ET

def export_mj_model(input_urdf, output_mjcf):
    """
    Exports and modifies a MuJoCo MJCF model from a URDF file.
    Adds floor, lighting, floating base, and actuators.
    """
    # Convert URDF to MJCF
    model = mujoco.MjModel.from_xml_path(input_urdf)
    mujoco.mj_saveLastXML(output_mjcf, model)

    # Load MJCF XML for editing
    tree = ET.parse(output_mjcf)
    root = tree.getroot()

    # Rewrite mesh file paths
    asset = root.find("asset")
    if asset is not None:
        for mesh in asset.findall("mesh"):
            old_file = mesh.get("file")
            if old_file and (old_file.endswith(".STL") or old_file.endswith(".stl")):
                new_path = f"../urdf/{old_file}"
                mesh.set("file", new_path)

    # Remake body structure
    worldbody = root.find("worldbody")
    if worldbody is not None:
        # Add floor
        ET.SubElement(worldbody, "geom", {
            "name": "floor",
            "type": "plane",
            "pos": "0 0 0",
            "size": "5 5 0.1",
            "rgba": "0.8 0.9 0.8 1",
            "contype": "1",
            "conaffinity": "1"
        })

        # Add light
        ET.SubElement(worldbody, "light", {
            "name": "main_light",
            "pos": "0 0 3",
            "dir": "0 0 -1",
            "diffuse": "1 1 1",
            "specular": "0.3 0.3 0.3"
        })

    # #  Make base a floating link (freejoint)
    # first_body = worldbody.find("body")
    # if first_body is not None and first_body.find("freejoint") is None:
    #     ET.SubElement(first_body, "freejoint", {"name": "floating_base"})

    # Add actuator for a joint (example: "joint1")
    actuators = root.find("actuator")
    if actuators is None:
        actuators = ET.SubElement(root, "actuator")

    # ET.SubElement(actuators, "position", {
    #     "name": "act_joint1",
    #     "joint": "joint1",  # ← your actual joint name
    #     "ctrlrange": "-1 1",
    #     "kp": "100"
    # })

    # Save the modified MJCF
    tree.write(output_mjcf)
    print(f"Modified MJCF model saved to {output_mjcf}")


if __name__ == "__main__":
    current_path = __file__.replace("export_mj_model.py", "")
    
    input_urdf = os.path.join(current_path, "..", "urdf", "pingu.urdf")
    output_mjcf = os.path.join(current_path, "pingu.xml")

    export_mj_model(input_urdf, output_mjcf)
    print(f"Exported MJCF model to {output_mjcf}")