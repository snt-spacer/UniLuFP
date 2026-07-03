import os
import shutil

pingu_cubo_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu&cubo"
dest_vid_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu_web\static\videos"

os.makedirs(dest_vid_dir, exist_ok=True)

video_mappings = {
    # Stabilization / Impedance
    os.path.join(pingu_cubo_dir, "videos", "sim2real", "Stabilization 08 Ceiling 4-24-2026, 2.25.12pm GMT+2 - 4-24-2026, 2.25.37pm GMT+2.mp4"): "stabilization.mp4",
    os.path.join(pingu_cubo_dir, "videos", "impeadance_arm.mp4"): "impeadance_arm.mp4",
    os.path.join(pingu_cubo_dir, "videos", "impeadance_wall.mp4"): "impeadance_wall.mp4",
    
    # Dynamic Disturbance
    os.path.join(pingu_cubo_dir, "videos", "sim2real", "dynamic disturbance", "Ceiling 6-26-2026, 12.57.29pm GMT+2 - 6-26-2026, 12.58.49pm GMT+2.mp4"): "dynamic_disturbance.mp4",
    
    # Wall Docking
    os.path.join(pingu_cubo_dir, "videos", "sim2real", "walldocking", "Ceiling 6-26-2026, 10.13.50am GMT+2 - 6-26-2026, 10.14.20am GMT+2.mp4"): "docking_ceiling.mp4",
    os.path.join(pingu_cubo_dir, "videos", "sim2real", "walldocking", "Front 6-26-2026, 10.13.50am GMT+2 - 6-26-2026, 10.14.21am GMT+2.mp4"): "docking_front.mp4"
}

print("--- Copying Selected Videos ---")
for src, dest_name in video_mappings.items():
    dest_path = os.path.join(dest_vid_dir, dest_name)
    if os.path.exists(src):
        print(f"Copying video: {os.path.basename(src)} -> {dest_name}")
        try:
            shutil.copy2(src, dest_path)
        except Exception as e:
            print(f"  Error copying {dest_name}: {e}")
    else:
        print(f"Warning: Source video not found: {src}")

print("\nVideo copy complete!")
