import mujoco 
import os

def export_mj_model(input_urdf, output_mjcf):
    """
    Exports a MuJoCo model from a URDF file.

    Args:
        input_urdf (str): Path to the input URDF file.
        output_mjcf (str): Path to save the output MJCF file.
    """
    # Load the URDF model
    model = mujoco.MjModel.from_xml_path(input_urdf)

    # Recompile

    # Export the model to MJCF format
    mujoco.mj_saveLastXML(output_mjcf, model)

if __name__ == "__main__":
    current_path = __file__.replace("export_mj_model.py", "")
    
    input_urdf = os.path.join(current_path, "..", "urdf", "pingu.urdf")
    output_mjcf = os.path.join(current_path, "pingu.xml")

    export_mj_model(input_urdf, output_mjcf)
    print(f"Exported MJCF model to {output_mjcf}")