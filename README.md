# Hermes FreeCAD Integration

Native, token-efficient 3D CAD tool for [Hermes Agent](https://github.com/NousResearch/hermes-agent). A single service-gated tool `freecad_exec` that wraps FreeCAD's headless Python console — Hermes writes FreeCAD Python code, the tool executes it and returns compact JSON with document state, export verification, and optional PNG preview renders.

**310 token schema** (zero when FreeCAD not installed). Co-designed with Gemini Pro over 7 rounds (session `c_6f8a3e44bc91ac84`).

## Credits & Reference

| Component | Backend | Reference |
|-----------|---------|-----------|
| `freecad_exec` | FreeCAD headless (`freecadcmd`) | [FreeCAD](https://github.com/FreeCAD/FreeCAD) — open-source parametric 3D CAD |
| Preview render | numpy-stl + Pillow | Lightweight isometric STL-to-PNG (no GUI needed) |

FreeCAD is built on [OpenCASCADE](https://dev.opencascade.org/) (geometry kernel), [Coin3D](https://github.com/coin3d/coin) (scene graph), and [Qt](https://www.qt.io/) (GUI). This integration uses only the Python API — no GUI dependencies.

## Quick Install

```bash
# 1. Clone and install
git clone https://github.com/lesterppo/hermes-freecad.git /tmp/hermes-freecad
cd /tmp/hermes-freecad && bash install.sh

# 2. Install FreeCAD
sudo apt install freecad        # Debian/Ubuntu
# OR: brew install --cask freecad  # macOS
# OR: download AppImage from https://www.freecad.org/downloads.php

# 3. Enable and restart
hermes tools enable freecad
# Start a new Hermes session, then: /skill freecad
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

### Query Geometry
```python
freecad_exec(code="""
import FreeCAD, Part
doc = FreeCAD.open("/path/to/model.FCStd")
for obj in doc.Objects:
    if hasattr(obj, 'Shape') and obj.Shape:
        s = obj.Shape
        print(f"{obj.Name}: V={s.Volume:.0f}mm³ A={s.Area:.0f}mm²")
""")
```

### Complex Operations (Boolean, Transforms, Patterns)
```python
freecad_exec(code="""
import FreeCAD, Part

doc = FreeCAD.newDocument("Assembly")
# Create parts
base = Part.makeBox(100, 50, 10)
hole = Part.makeCylinder(5, 15, FreeCAD.Vector(25, 25, -2))

# Boolean cut
base_obj = doc.addObject("Part::Feature", "Base")
base_obj.Shape = base
hole_obj = doc.addObject("Part::Feature", "Hole")
hole_obj.Shape = hole

cut = doc.addObject("Part::Cut", "DrilledBase")
cut.Base = base_obj
cut.Tool = hole_obj
doc.recompute()

# Compound for efficient multi-body export
compound = Part.makeCompound([base_obj.Shape, cut.Shape])
final = doc.addObject("Part::Feature", "Assembly")
final.Shape = compound
doc.recompute()
print(f"Volume: {final.Shape.Volume:.0f} mm³")
""")
```

## Output Format

```json
{
  "ok": true,
  "o": "Volume: 1000 mm³",
  "doc": [{"name": "Test", "objects": [{"n": "Box", "t": "Part::Feature", "l": "Box"}], "n_objects": 1}],
  "out_file": {"path": "/tmp/sphere.stl", "size": 684, "size_human": "684 B"},
  "preview": "/tmp/sphere_preview.png"
}
```

## Token Efficiency

| Metric | Value |
|--------|-------|
| Tool schema | 1,240 chars (~310 tokens) |
| Service-gated | Zero tokens when FreeCAD not installed |
| Output | Compact JSON, short keys (`o`, `doc`, `e`, `ok`) |
| Toolset | NOT in `_HERMES_CORE_TOOLS` — off by default |

## Manual Toolset Setup

If the automated install doesn't work, add this to `~/.hermes/hermes-agent/toolsets.py`:

```python
# In the TOOLSETS dict, add after the "medical" entry:
"freecad": {
    "description": "3D CAD modeling via FreeCAD headless — parametric modeling, STL/STEP/FCStd export",
    "tools": ["freecad_exec"],
    "includes": [],
},
```

Then:
```bash
hermes tools enable freecad
# Start a new Hermes session
```

## Preview Render

Add `render="/tmp/preview.png"` to get a lightweight isometric PNG preview (requires `pip install numpy-stl pillow`). No GUI or Xvfb needed — pure Python STL-to-PNG renderer.

## Prerequisites

| Component | Requirement | Install |
|-----------|-------------|---------|
| `freecad_exec` | `freecadcmd` on PATH | `sudo apt install freecad` |
| Preview render | numpy-stl, pillow | `pip install numpy-stl pillow` |

## License

MIT — same as Hermes Agent.
