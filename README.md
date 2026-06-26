# Hermes FreeCAD Integration

Native, token-efficient 3D CAD tool for [Hermes Agent](https://github.com/NousResearch/hermes-agent). A single service-gated tool `freecad_exec` that wraps FreeCAD's headless Python console — Hermes writes FreeCAD Python code, the tool executes it and returns compact JSON with document state, export verification, and optional PNG preview renders.

**310 token schema** (zero when FreeCAD not installed).

## Live Demos

| Demo | Description | Size |
|------|-------------|------|
| [Bowstring Warren Truss Bridge](demo/index.html) | 12m span, 197 components, 1:10 camber | Loads STL from CDN |
| [Bridge (offline)](demo/standalone.html) | Same bridge, self-contained — no network needed | 3.2 MB embedded |
| [Tower of Babel](examples/tower_of_babel/viewer.html) | 7-tier Mesopotamian ziggurat, 74 parts, spiral ramp | 144 KB embedded |

> Drag to rotate · Scroll to zoom · Right-drag to pan

## Projects

### Tower of Babel — Parametric Ziggurat
7-tier Mesopotamian ziggurat co-designed with Gemini Pro (session `c_72a72a8b188e50d9`). 320 × 370 × 296 mm, 74 parts compounded. Features: piecewise spiral ramp, corner landings, monumental arched gatehouse, summit temple with columns, dynamic buttresses. Fully parametric — tune base_width, height_decay, step_depth, ramp_width. Build script + STL in [`examples/tower_of_babel/`](examples/tower_of_babel/).

### Bowstring Warren Truss Bridge
12m span bowstring Warren truss bridge co-designed with Gemini Pro (session `c_6f8a3e44bc91ac84`). 197 components, cylindrical struts for parabolic chords, node spheres for manifold joints, 1:10 camber. Full-res STL at root (17.9 MB), decimated version (48K faces, 2.4 MB) in `demo/`.

## Self-Contained HTML Viewer

Build offline-capable 3D viewers that work on `file://` (no server, double-click to open):

1. **Decimate if needed:** `python3 scripts/decimate_stl.py input.stl output.stl [voxel_mm]`
2. **Fill template:** Replace `__STL_BASE64__` and camera/material placeholders in [`templates/standalone-viewer.html`](templates/standalone-viewer.html)
3. **Deliver:** Single HTML file, everything embedded — no external files, no network requests

Key details: `file://` blocks `fetch()` → use `atob()` → `Uint8Array` → `Blob` URL for STL loading. FreeCAD Z-up → Three.js Y-up via `rotateX(-PI/2)`. CDN: jsdelivr purged `examples/js/` — use `examples/jsm/` with importmap.

## Quick Install

```bash
git clone https://github.com/lesterppo/hermes-freecad.git /tmp/hermes-freecad
cd /tmp/hermes-freecad && bash install.sh

# Install FreeCAD
sudo apt install freecad        # Debian/Ubuntu
# OR: brew install --cask freecad  # macOS
# OR: download AppImage from https://www.freecad.org/downloads.php

# Enable and restart
hermes tools enable freecad
```

## Usage

Single tool: `freecad_exec(code="...")`

### Create a Box
```python
freecad_exec(code="""
import FreeCAD, Part
doc = FreeCAD.newDocument("Test")
box = Part.makeBox(10, 8, 6)
Part.show(box, "MyBox")
doc.recompute()
print(f"Volume: {box.Volume:.0f} mm³")
""")
```

### Parametric Design + Export
```python
freecad_exec(code="""
import FreeCAD, Part, Mesh
doc = FreeCAD.newDocument("Export")
sphere = Part.makeSphere(15)
Part.show(sphere, "Sphere")
doc.recompute()
Mesh.export([doc.Objects[0]], "/tmp/sphere.stl")
doc.saveAs("/tmp/sphere.FCStd")
""", out_file="/tmp/sphere.stl", render="/tmp/sphere_preview.png")
```

For the full SKILL.md with compound assembly patterns, oriented struts, boolean rules, FreeCAD 1.1.1 quirks, double-execution guard, and 7-round Gemini collaboration pattern, see [SKILL.md](SKILL.md).

## Token Efficiency

| Metric | Value |
|--------|-------|
| Tool schema | 1,240 chars (~310 tokens) |
| Service-gated | Zero tokens when FreeCAD not installed |
| Output | Compact JSON, short keys (`o`, `doc`, `e`, `ok`) |
| Toolset | NOT in `_HERMES_CORE_TOOLS` — off by default |

## Credits & Reference

| Component | Backend | Reference |
|-----------|---------|-----------|
| `freecad_exec` | FreeCAD headless (`freecadcmd`) | [FreeCAD](https://github.com/FreeCAD/FreeCAD) |
| Preview render | numpy-stl + Pillow | Lightweight isometric STL-to-PNG |
| STL decimation | Vertex clustering (numpy-stl) | `scripts/decimate_stl.py` |
| 3D viewer | Three.js (CDN, self-contained) | `templates/standalone-viewer.html` |

FreeCAD is built on [OpenCASCADE](https://dev.opencascade.org/) (geometry kernel), [Coin3D](https://github.com/coin3d/coin) (scene graph), and [Qt](https://www.qt.io/) (GUI). This integration uses only the Python API — no GUI dependencies.

## License

MIT — same as Hermes Agent.
