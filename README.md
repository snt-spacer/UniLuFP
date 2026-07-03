# PINGU: Design, Characterization, and Validation of a Multi-Actuator Air-Bearing Spacecraft Emulator

[![Project Page](https://img.shields.io/badge/Project-Page-blue)](https://pingu-website.example.com)

PINGU is a reconfigurable planar micro-gravity platform designed to unify thruster, reaction-wheel, and robotic-arm actuation for research in orbital docking, stabilization, and manipulation. This repository contains the official project website and documentation.

## Overview

PINGU addresses the limitations of single-purpose testbeds by co-integrating:

- **8 Cold-Gas Thrusters** - RCS (Reaction Control System) for fine maneuvering
- **High-Torque Reaction Wheel** - Momentum-based attitude control (20cm metal-blended PLA disk)
- **Dual 2-DOF Robotic Arms** - LevionArms with 6-axis force/torque (F/T) wrist sensors
- **Air-Bearing Platform** - 40cm × 40cm × 65cm modular chassis with three 150mm porous-graphite air bearings

All actuators are exposed through a **unified ROS 2 actuator-abstraction layer**, enabling seamless swapping of classical optimal controllers (PID, LQR, MPC) and learned policies (PPO) on the same hardware—bridging the gap between classical optimal control and reinforcement learning.

## Key Capabilities

### Heterogeneous Actuation
Co-integrates planar RCS, reaction wheel, and dual robotic arms with F/T sensors on a single air-bearing chassis, enabling multi-modal control strategies.

### Unified ROS 2 Stack  
Hardware abstraction layer with command multiplexer allows model-based and learned policies to swap seamlessly without modification.

### Sim-to-Real Twin
GPU-accelerated digital twin in **Space Robotics Bench** (Isaac Lab) with extensive domain randomization over mass, inertia, and external forces.

## Experimental Validation

PINGU is validated across four benchmark tasks:

1. **Point-to-Pose Navigation** - Trajectory tracking with three actuator subsets
2. **Dynamic Disturbance Rejection** - Implicit rejection of arm-induced CoM shifts
3. **Reaction Wheel Momentum Stabilization** - Attitude stabilization under varying inertia
4. **Force-Controlled Docking** - Vision-guided approach with impedance-controlled contact damping

Results demonstrate effectiveness with both classical LQR baselines and sim-to-real PPO policies trained via domain randomization.

## Website Contents

This repository contains the official PINGU project website built with a modernized academic template.

### Sections

- **System & Mechanical Design** - Detailed breakdown of the four-layer modular chassis architecture
- **Actuator Characterization** - Thruster manifold coupling and reaction wheel envelope testing
- **Software Stack & Simulation** - Dual-workspace ROS 2 architecture and Space Robotics Bench integration
- **Experimental Tasks & Videos** - Interactive tabs with real hardware videos and performance metrics
- **BibTeX Citation** - Copy-to-clipboard citation for easy referencing

### Features

- Responsive design with mobile support
- Interactive tabbed experiments section
- Embedded videos and high-resolution figures
- SEO-optimized meta tags for academic indexing
- Copy-to-clipboard BibTeX citation
- Navigation dropdown for related projects

## Customization

Edit `index.html` to customize:

- Project title, authors, and affiliation
- Links (Paper PDF, ArXiv, GitHub, Models)
- Abstract and descriptions
- Videos, images, and figures
- Meta tags for SEO and social sharing
- Related projects in the navbar dropdown

### Key Customization Points

1. **Meta Tags** (lines 8-25) - Update title, description, keywords, and author
2. **Favicon** - Replace `static/images/simp_v4.png` with your own
3. **Hero Section** - Update publication info and links
4. **Content Sections** - Edit abstracts, descriptions, and captions
5. **Navigation** - Add more projects to the "Other Projects" dropdown

### Media Assets

Place media files in:
- `static/images/` - PNG/JPG images and diagrams
- `static/videos/` - MP4 videos (recommend compression with `compress_videos.py`)
- `static/pdfs/` - Paper PDF and supplementary materials
- `static/pdfs/paper.pdf` - Main paper file

## Build & Deploy

### Local Development

Run a local HTTP server:

```bash
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

### GitHub Pages

1. Push to `gh-pages` branch
2. Enable GitHub Pages in repository settings
3. Website will be live at `https://yourusername.github.io/pingu_web`

## Project Links

- 📄 **Paper** - `static/pdfs/paper.pdf`
- 🔬 **ArXiv** - [arxiv.org](https://arxiv.org/)
- 💻 **Code** - [GitHub repository](https://github.com/)
- 🤗 **Models** - [Hugging Face Hub](https://huggingface.co/)
- 🎮 **Simulation** - [Space Robotics Bench](https://andrejorsula.github.io/space_robotics_bench/)

## Related Projects

- **RoboRAN** - [GitHub](https://snt-spacer.github.io/RoboRAN-Website/)
- **Space Robotics Bench** - [Project Page](https://andrejorsula.github.io/space_robotics_bench/)

## Citation

```bibtex
@article{anonymous2026pingu,
  title={PINGU: Design, Characterization, and Validation of a Multi-Actuator Air-Bearing Spacecraft Emulator},
  author={Anonymous Authors},
  journal={Under Review},
  year={2026}
}
```

## Design Credits

This website is built using a modernized academic project page template inspired by [Nerfies](https://nerfies.github.io/), with design improvements for SEO, mobile responsiveness, and interactive components.

## License

This website is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).

## Contributors

PINGU is a collaborative effort between space robotics researchers. For more details, see the paper.

---

For questions or issues with the website, please open an issue or contact the authors.
