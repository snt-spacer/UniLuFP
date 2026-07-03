import fitz  # PyMuPDF
import os
import shutil
import glob

# Paths
paper_fig_dir = r"C:\Users\ricard.marsal\Documents\GitHub\pingu_paper\fig"
pingu_cubo_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu&cubo"
main_paper_pdf = r"C:\Users\ricard.marsal\Documents\GitHub\pingu_paper\main.pdf"

dest_img_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu_web\static\images"
dest_pdf_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu_web\static\pdfs"
dest_vid_dir = r"C:\Users\ricard.marsal\Documents\2026\pingu_web\static\videos"

os.makedirs(dest_img_dir, exist_ok=True)
os.makedirs(dest_pdf_dir, exist_ok=True)
os.makedirs(dest_vid_dir, exist_ok=True)

# 1. Convert paper figures (PDFs) to PNGs and copy PNGs
print("--- Importing and Converting Paper Figures ---")
for root, dirs, files in os.walk(paper_fig_dir):
    for f in files:
        src_path = os.path.join(root, f)
        rel_path = os.path.relpath(src_path, paper_fig_dir)
        dest_path = os.path.join(dest_img_dir, rel_path)
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        if f.lower().endswith('.pdf'):
            dest_png = os.path.splitext(dest_path)[0] + '.png'
            print(f"Converting: {rel_path} -> .png")
            try:
                doc = fitz.open(src_path)
                page = doc[0]
                # High DPI resolution (300) for crisp web display
                pix = page.get_pixmap(dpi=300)
                pix.save(dest_png)
                doc.close()
            except Exception as e:
                print(f"  Error converting {f}: {e}")
        elif f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            print(f"Copying image: {rel_path}")
            shutil.copy2(src_path, dest_path)

# 2. Copy the main paper PDF
print("\n--- Copying Main Paper PDF ---")
if os.path.exists(main_paper_pdf):
    print("Copying main.pdf -> static/pdfs/paper.pdf")
    shutil.copy2(main_paper_pdf, os.path.join(dest_pdf_dir, "paper.pdf"))
else:
    print(f"Main paper PDF not found at {main_paper_pdf}")

# 3. Copy SVG assets from pingu&cubo
print("\n--- Copying SVGs from pingu&cubo ---")
svg_dest_dir = os.path.join(dest_img_dir, "svgs")
os.makedirs(svg_dest_dir, exist_ok=True)

svg_sources = [
    (os.path.join(pingu_cubo_dir, "svgs", "*.svg"), "svgs"),
    (os.path.join(pingu_cubo_dir, "paper_figures", "*.svg"), "paper_figures"),
    (os.path.join(pingu_cubo_dir, "drawings", "*.svg"), "drawings")
]

for pattern, folder_name in svg_sources:
    for svg_file in glob.glob(pattern):
        name = os.path.basename(svg_file)
        # Prefix with folder name to avoid collisions
        dest_name = f"{folder_name}_{name}"
        dest_svg_path = os.path.join(svg_dest_dir, dest_name)
        print(f"Copying SVG: {folder_name}/{name} -> svgs/{dest_name}")
        shutil.copy2(svg_file, dest_svg_path)

print("\nAsset import and conversion complete!")
