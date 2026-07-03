import os
import shutil
import subprocess
import glob
import imageio_ffmpeg

# Paths
pingu_web_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu_web"
raw_vid_dir = os.path.join(pingu_web_dir, "raw_videos")
static_vid_dir = os.path.join(pingu_web_dir, "static", "videos")
pingu_cubo_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu&cubo"

os.makedirs(raw_vid_dir, exist_ok=True)
os.makedirs(static_vid_dir, exist_ok=True)

# 1. Pre-populate raw_videos folder if it is empty
raw_videos_present = glob.glob(os.path.join(raw_vid_dir, "*"))
if not raw_videos_present:
    print("--- Initializing raw_videos folder with source videos ---")
    source_mappings = {
        os.path.join(pingu_cubo_dir, "videos", "sim2real", "Stabilization 08 Ceiling 4-24-2026, 2.25.12pm GMT+2 - 4-24-2026, 2.25.37pm GMT+2.mp4"): "stabilization.mp4",
        os.path.join(pingu_cubo_dir, "videos", "impeadance_arm.mp4"): "impeadance_arm.mp4",
        os.path.join(pingu_cubo_dir, "videos", "impeadance_wall.mp4"): "impeadance_wall.mp4",
        os.path.join(pingu_cubo_dir, "videos", "sim2real", "dynamic disturbance", "Ceiling 6-26-2026, 12.57.29pm GMT+2 - 6-26-2026, 12.58.49pm GMT+2.mp4"): "dynamic_disturbance.mp4",
        os.path.join(pingu_cubo_dir, "videos", "sim2real", "walldocking", "Ceiling 6-26-2026, 10.13.50am GMT+2 - 6-26-2026, 10.14.20am GMT+2.mp4"): "docking_ceiling.mp4",
        os.path.join(pingu_cubo_dir, "videos", "sim2real", "walldocking", "Front 6-26-2026, 10.13.50am GMT+2 - 6-26-2026, 10.14.21am GMT+2.mp4"): "docking_front.mp4"
    }
    
    for src, name in source_mappings.items():
        if os.path.exists(src):
            dest = os.path.join(raw_vid_dir, name)
            print(f"Copying to raw_videos: {name}")
            shutil.copy2(src, dest)
        else:
            print(f"Warning: Source not found: {src}")
else:
    print("--- raw_videos folder already initialized ---")

# 2. Compress all videos from raw_videos to static/videos
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
print(f"Using FFmpeg binary at: {ffmpeg_exe}\n")

print("--- Starting Video Compression ---")
raw_files = glob.glob(os.path.join(raw_vid_dir, "*.mp4")) + glob.glob(os.path.join(raw_vid_dir, "*.MP4"))
raw_files = list(set(raw_files)) # De-duplicate

for src_path in raw_files:
    filename = os.path.basename(src_path)
    dest_path = os.path.join(static_vid_dir, filename.lower())
    
    # Calculate original size
    orig_size_mb = os.path.getsize(src_path) / (1024 * 1024)
    print(f"Processing: {filename} ({orig_size_mb:.2f} MB)")
    
    # Run FFmpeg compression: 
    # CRF 28 offers excellent compression with 1080p max height.
    # faststart allows web pages to play it progressively without downloading the whole file first.
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", src_path,
        "-vcodec", "libx264",
        "-crf", "28",
        "-preset", "fast",
        "-acodec", "aac",
        "-b:a", "128k",
        "-vf", "scale=-2:min(1080\\,ih)", # cap height at 1080p, preserve aspect ratio
        "-movflags", "+faststart",
        dest_path
    ]
    
    try:
        # Run conversion synchronously
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Calculate new size
        new_size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        savings = (1 - (new_size_mb / orig_size_mb)) * 100
        print(f"  Success: {filename} -> {os.path.basename(dest_path)}")
        print(f"  Original: {orig_size_mb:.2f} MB | Compressed: {new_size_mb:.2f} MB")
        print(f"  Savings: {savings:.1f}%\n")
    except subprocess.CalledProcessError as e:
        print(f"  Error compressing {filename}: {e}\n")

print("All video compressions complete!")
