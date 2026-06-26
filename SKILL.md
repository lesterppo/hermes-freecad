---
name: freecad
description: Parametric 3D CAD via FreeCAD's Python API in headless mode.
version: 1.4.0
author: Peter + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cad, 3d-modeling, freecad, parametric-design, step, stl, openscad]
    category: software-development
    related_skills: [hermes-agent]
    config:
      tools.freecad.enabled:
        description: Enable the freecad_exec tool for 3D CAD modeling
        type: bool
        default: false
---

# FreeCAD Skill

Parametric 3D CAD modeling via FreeCAD's Python API. Hermes writes Python code that creates, modifies, and exports 3D models using FreeCAD's geometry kernel (OpenCASCADE). All execution happens in headless mode — no GUI needed.

## When to Use

- Creating 3D CAD models programmatically (boxes, cylinders, complex shapes)
- Boolean operations on solids (union, cut, intersect)
- Reading/writing CAD files: STEP, STL, IGES, OBJ, FCStd
- Converting between CAD formats
- Generating parametric designs with variables
- Querying geometry properties (volume, area, center of mass)
- Creating 2D sketches and extruding/padding them into 3D parts

## Prerequisites

Install FreeCAD:

```bash
# Ubuntu/Debian (if available in repos)
sudo apt install freecad

# Snap (requires sudo)
sudo snap install freecad

# AppImage — works without sudo, including WSL
# 1. Find latest version
curl -sL https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tag_name'])"
# 2. Download and extract
wget "https://github.com/FreeCAD/FreeCAD/releases/download/<version>/FreeCAD_<version>-Linux-x86_64-py311.AppImage"
chmod +x FreeCAD*.AppImage
./FreeCAD*.AppImage --appimage-extract
# Binary is at: ./squashfs-root/usr/bin/freecadcmd
```

For WSL-specific AppImage details, see `references/wsl-appimage-setup.md`.

Enable the FreeCAD toolset:

```bash
hermes tools enable freecad
# or: hermes config set tools.cli.enabled '["freecad"]'
hermes config set tools.freecad.enabled true
```

Start a new session.

## How to Run

Call `freecad_exec(code="...")` with FreeCAD Python code. The model writes Python using FreeCAD's API directly. Examples below.

### Quick Start: Create a Box

```
freecad_exec(code="""
import FreeCAD, Part, Mesh
doc = FreeCAD.newDocument("Test")
box = doc.addObject("Part::Box", "Box")
box.Length = 10
box.Width = 8
box.Height = 6
doc.recompute()
print(f"Box volume: {box.Shape.Volume:.2f} mm³")
doc.saveAs("/tmp/test_box.FCStd")
""", out_file="/tmp/test_box.FCStd")
```

### Export STL for 3D Printing

```
freecad_exec(code="""
import FreeCAD, Part
doc = FreeCAD.newDocument("Export")
# Create a sphere
sphere = Part.makeSphere(15)
obj = Part.show(sphere, "MySphere")
doc.recompute()
# Export
Mesh.export([obj], "/tmp/sphere.stl")
print("Exported sphere.stl")
""", out_file="/tmp/sphere.stl")
```

### Parametric Design with Variables

```
freecad_exec(code="""
import FreeCAD, Part, math

doc = FreeCAD.newDocument("Parametric")

# Parameters
bolt_diameter = 10.0
bolt_length = 50.0
head_diameter = 16.0
head_height = 8.0

# Bolt shaft
shaft = Part.makeCylinder(bolt_diameter/2, bolt_length)
shaft_obj = doc.addObject("Part::Feature", "Shaft")
shaft_obj.Shape = shaft

# Hex head (approximated as cylinder for simplicity)
head = Part.makeCylinder(head_diameter/2, head_height,
                         FreeCAD.Vector(0, 0, bolt_length))
head_obj = doc.addObject("Part::Feature", "Head")
head_obj.Shape = head

# Fuse
fuse = doc.addObject("Part::Fuse", "Bolt")
fuse.Base = shaft_obj
fuse.Tool = head_obj
doc.recompute()

print(f"Bolt volume: {fuse.Shape.Volume:.2f} mm³")
doc.saveAs("/tmp/bolt.FCStd")
""", out_file="/tmp/bolt.FCStd")
```

### Read and Analyze a CAD File

```
freecad_exec(code="""
import FreeCAD, Part

doc = FreeCAD.open("/path/to/model.FCStd")
print(f"Document: {doc.Name}")
print(f"Objects: {len(doc.Objects)}")
for obj in doc.Objects:
    print(f"  {obj.Name} ({obj.TypeId}): {obj.Label}")
    if hasattr(obj, 'Shape') and obj.Shape:
        s = obj.Shape
        print(f"    Volume: {s.Volume:.2f}, Area: {s.Area:.2f}")
        print(f"    Center of Mass: {s.CenterOfMass}")
""")
```

## Quick Reference

### Core Modules

| Module | Import | Key Functions |
|--------|--------|--------------|
| FreeCAD | `import FreeCAD` | `newDocument(name)`, `open(path)`, `listDocuments()`, `getDocument(name)`, `closeDocument(name)` |
| Part | `import Part` | `makeBox(l,w,h)`, `makeSphere(r)`, `makeCylinder(r,h)`, `makeCone(r1,r2,h)`, `makeTorus(r1,r2)`, `show(shape, name)`, `read(path)`, `write(shape, path)` |
| Mesh | `import Mesh` | `export(objects, path)` for STL/OBJ, `createSphere()`, `read(path)` |

### Document Operations

```python
doc = FreeCAD.newDocument("Name")      # create
doc = FreeCAD.open("/path/file.FCStd")  # open
doc.save()                              # save
doc.saveAs("/path/file.FCStd")          # save as
doc.recompute()                         # recompute after changes
doc.exportObjects([obj], "/path.step")  # export to STEP/IGES
doc.addObject("Part::Box", "Name")      # add parametric object
doc.addObject("Part::Feature", "Name")  # add shape-based object
FreeCAD.closeDocument("Name")           # close
```

### Part Primitives (Part module)

```python
box = Part.makeBox(10, 8, 6)               # L x W x H
box = Part.makeBox(10, 8, 6, Vector(1,0,0)) # at position
sphere = Part.makeSphere(15)                 # radius
sphere = Part.makeSphere(15, Vector(0,0,0), 0, 90, 360)  # r, center, angle1, angle2, angle3
cyl = Part.makeCylinder(5, 20)              # radius, height
cyl = Part.makeCylinder(5, 20, Vector(), Vector(0,0,1))  # r, h, center, dir
cone = Part.makeCone(10, 5, 20)             # r1, r2, height
torus = Part.makeTorus(20, 5)               # major_r, minor_r
```

### Boolean Operations

```python
# Create shapes, add to doc, then:
union = doc.addObject("Part::Fuse", "Name")
union.Base = obj1
union.Tool = obj2

cut = doc.addObject("Part::Cut", "Name")
cut.Base = obj1
cut.Tool = obj2

intersect = doc.addObject("Part::Common", "Name")
intersect.Base = obj1
intersect.Tool = obj2
```

### Geometry Queries

```python
shape = obj.Shape         # Part::Shape
shape.Volume              # mm³
shape.Area                # mm²
shape.CenterOfMass        # Vector(x,y,z)
shape.BoundBox            # (xmin,ymin,zmin, xmax,ymax,zmax)
shape.isClosed()          # watertight?
shape.isValid()           # valid geometry?
shape.ShapeType           # 'Solid', 'Shell', 'Face', etc.
```

### Transforms & Placement

```python
FreeCAD.Vector(x, y, z)                 # 3D vector
FreeCAD.Placement(base, rotation)       # position + rotation
FreeCAD.Placement(Vector(10,0,0), Rotation(0,0,0))
FreeCAD.Rotation(yaw, pitch, roll)      # Euler angles in degrees
FreeCAD.Rotation(Vector(0,0,1), 45)     # axis + angle

obj.Placement.Base = Vector(5, 0, 0)    # move
obj.Placement.Rotation = Rotation(0,0,90)  # rotate
```

### Export Formats

```python
# STL (3D printing)
Mesh.export([obj], "/path/model.stl")

# STEP (CAD data exchange)
doc.exportObjects([obj], "/path/model.step")

# IGES
doc.exportObjects([obj], "/path/model.iges")

# OBJ (mesh)
Mesh.export([obj], "/path/model.obj")

# FreeCAD native
doc.saveAs("/path/model.FCStd")
```

### Sketcher (2D profile → 3D)

```python
import Sketcher
# Create a body and sketch
body = doc.addObject("PartDesign::Body", "Body")
sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
body.addObject(sketch)

# Add geometry to sketch (circles, lines, arcs)
geo_idx = sketch.addGeometry(Part.Circle(Vector(0,0,0), Vector(0,0,1), 10))
sketch.addConstraint(Sketcher.Constraint("Radius", geo_idx, 10.0))
sketch.addConstraint(Sketcher.Constraint("Coincident", geo_idx, 3, -1, 1))
doc.recompute()

# Pad (extrude) the sketch
pad = doc.addObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = 20.0
body.addObject(pad)
doc.recompute()
```

### Compound Assembly (Avoids Boolean Cascade)

For assemblies with many components (trusses, lattices, bridges), **never** use sequential
boolean fuses in a loop. OpenCASCADE chokes on 100+ sequential fuses. Instead, collect
all shapes in a list and use `Part.makeCompound()`:

```python
shapes = []
# Build all components, appending each to shapes[]
shapes.append(Part.makeBox(10, 10, 100))
shapes.append(Part.makeCylinder(5, 80))
# ... more shapes ...
compound = Part.makeCompound(shapes)
obj = doc.addObject("Part::Feature", "Assembly")
obj.Shape = compound
doc.recompute()
```

The mesh exporter handles overlapping compound geometry perfectly for STL export.
Compound is NOT a solid — `shape.ShapeType` returns `"Compound"`, which is expected.
For STEP export, `shape.exportStep(path)` works on compounds.

### Truss & Lattice Construction

The universal building block for any space frame: an oriented strut between two 3D points.

```python
def create_strut(p1, p2, thickness, use_cylinder=False):
    """Create an oriented strut between two 3D vectors."""
    direction = p2 - p1
    length = direction.Length
    direction.normalize()  # MANDATORY — prevents divide-by-zero
    rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), direction)
    
    if use_cylinder:
        shape = Part.makeCylinder(thickness / 2.0, length)
        shape.Placement = FreeCAD.Placement(p1, rotation)
    else:
        shape = Part.makeBox(thickness, thickness, length)
        shape.translate(FreeCAD.Vector(-thickness/2, -thickness/2, 0))
        shape.Placement = FreeCAD.Placement(p1, rotation)
    return shape
```

**When to use cylinders vs boxes:**
- **Cylinders** for curved/parabolic chords — prevents orientation twisting as the curve changes
- **Boxes** for straight chords and floor beams — visually crisp, structural look

**Node spheres** guarantee manifold geometry at joints by swallowing intersecting geometry:

```python
sphere_r = (chord_thickness / 2.0) * 1.12   # 1.1–1.15x, NOT 1.5x (too bulbous)
for pt in all_joint_points:
    s = Part.makeSphere(sphere_r)
    s.translate(pt)
    shapes.append(s)
```

For full truss examples, see `templates/bowstring_bridge.py`.

### Draft Workbench Utilities

```python
import Draft
# Array
array = Draft.makeArray(base_obj, FreeCAD.Vector(2,0,0),
                        FreeCAD.Vector(0,2,0), 5, 3)

# Fillet/chamfer on edges
edge_fillet = doc.addObject("Part::Fillet", "Fillet")
edge_fillet.Base = obj
edge_fillet.Edges = [(1, 2.0)]  # (edge_index, radius)
```

## Procedure

1. **Plan the model**: Decide what primitives and operations you need.
2. **Create document**: `doc = FreeCAD.newDocument("Name")`
3. **Build shapes in a list**: Append each Part solid to a `shapes[]` list.
   For assemblies with 10+ components, use `Part.makeCompound(shapes)` instead of
   sequential `doc.addObject()` + boolean fuses.
4. **Add to document**: `compound = Part.makeCompound(shapes); obj = doc.addObject("Part::Feature", "Name"); obj.Shape = compound`
5. **Recompute**: `doc.recompute()`
6. **Verify**: Query geometry properties — `Volume`, `Area`, `BoundBox`, `isClosed()`, `isValid()`
7. **Export**: `doc.saveAs()` or `Mesh.export()` or `shape.exportStep()`
8. **Clean up**: Documents auto-closed by the tool wrapper (no manual `closeDocument()` needed)

### Preview Rendering

The `render` parameter generates an isometric PNG preview from an STL export.
No GUI, no Xvfb — uses lightweight numpy-stl + PIL rendering.

```python
freecad_exec(code="""
import FreeCAD, Part, Mesh
doc = FreeCAD.newDocument("Preview")
Part.show(Part.makeSphere(15), "Sphere")
doc.recompute()
Mesh.export([doc.Objects[0]], "/tmp/sphere.stl")
""", out_file="/tmp/sphere.stl", render="/tmp/preview.png")
# Returns: {"preview": "/tmp/preview.png", ...}
```

Dependencies: `pip install numpy-stl pillow` (optional — skipped if missing).
For multi-color rendering with depth-sorted material groups, see `references/multicolor-stl-rendering.md`.

### Export with Mesh Quality Control

For high-quality STL, control tessellation in your code:
```python
# Coarse (small file)
Mesh.export([obj], "/tmp/model.stl", 1.0)  # positional tolerance=1.0
# Fine (large file)  
Mesh.export([obj], "/tmp/model.stl", 0.01)  # positional tolerance=0.01
```
Default FreeCAD tessellation is fairly coarse — specify tolerance for 3D-printing quality.
**FreeCAD 1.1.1 note:** `angularDeflection` keyword is rejected — use positional tolerance only.

### Self-Contained HTML Viewer (embedded STL)

For desktop deliverables that work offline on `file://` (no server needed):

1. **If STL < 500 KB:** embed it directly as base64 in the viewer HTML.
2. **If STL > 500 KB:** decimate first with `scripts/decimate_stl.py`, then embed.

Decimation uses vertex clustering (numpy-stl only, no external deps):
```bash
python3 scripts/decimate_stl.py input.stl output.stl [voxel_mm]
# Auto-targets ~50K faces. Override voxel size for finer/coarser output.
```

Then inject the base64 STL into `templates/standalone-viewer.html` — replace
`__STL_BASE64__` and all `__CAPITAL__` placeholders with model-specific values.

Key implementation details:
- `file://` blocks `fetch()` → MUST use `atob()` → `Uint8Array` → `Blob` → `URL.createObjectURL()` → `STLLoader.load()`.
- FreeCAD Z-up → Three.js Y-up: `geometry.rotateX(-Math.PI / 2)`.
- CDN: jsdelivr purged `examples/js/` — use `examples/jsm/` with importmap (see template).
- Camera presets: adjust `__CAM_*__`, `__FRONT_*__`, `__TOP_*__`, `__SIDE_*__` for your model's bounding box.

For the full workflow and CDN path rationale, see `references/standalone-project-page.md`.

## Pitfalls

- **Must recompute**: Most changes don't take effect until `doc.recompute()`. Forgot this = empty results.
- **Double execution**: FreeCAD runs Python scripts twice (once as `exec()`, once as macro). Guard with a file marker at script start. Use a PID-based marker to avoid stale guards from crashed runs blocking subsequent executions:
  ```python
  import os, sys
  MARKER = f"/tmp/_fc_guard_{os.getpid()}"
  if os.path.exists(MARKER): sys.exit(0)
  open(MARKER, "w").close()
  ```
  Without this guard, the second pass re-executes on a stale document and crashes. Fixed-path markers (e.g. `/tmp/_fc_guard`) survive crashed runs and silently kill the next invocation — always use PID.<br/>
  **Note:** FreeCAD 1.1.1 may only execute once in some modes. The guard is harmless either way — it won't trigger on single-pass execution.

- **`__name__` is NOT `'__main__'`**: FreeCAD's `exec()` sets `__name__` to the filename (e.g. `'build_tower'`), not `'__main__'`. Code guarded by `if __name__ == '__main__':` will NEVER execute. Call your entry function at module level instead:
  ```python
  # WRONG — never runs in FreeCAD
  if __name__ == '__main__':
      build_model()

  # RIGHT — runs in FreeCAD
  build_model()
  ```

- **`Mesh.export()` keyword changes in 1.1.1**: `angularDeflection` is not a valid keyword argument in FreeCAD 1.1.1. Use the bare form or positional `tolerance` only:
  ```python
  # Works in 1.1.1
  Mesh.export([obj], "/path/model.stl")
  Mesh.export([obj], "/path/model.stl", 0.01)  # positional tolerance

  # Fails in 1.1.1 with: 'angularDeflection' is an invalid keyword argument
  Mesh.export([obj], "/path/model.stl", tolerance=0.01, angularDeflection=0.1)
  ```
- **`Wire.close()` does not exist**: Polygons from `Part.makePolygon()` must be closed by repeating the first vertex as the last point. Use `Part.Face(Part.Wire(wire.Edges))` to create a face from the closed wire.
- **`Part.Face` extrude axis determines solid vs shell**: When extruding a face into a solid, the extrusion vector must be perpendicular to the face plane. Extruding along a wrong axis (e.g., `face.extrude(Vector(0,0,-1))` on an XY-plane face) creates a 1mm-thick hollow shell instead of a solid block. Draw 2D profiles on the plane perpendicular to the desired extrusion direction. Example: for a ramp wedge spanning Y, draw the profile on XZ plane, then `face.extrude(Vector(0, width, 0))`.
- **Duplicate geometry from overlapping loops**: When generating end-posts and diagonals in the same loop, ensure conditions are mutually exclusive. Example: at `i==0`, both the end-post and the first diagonal can fire, creating two identical struts in the same position. Use `if i==0:` for end-post then `if i>0:` for diagonals — never leave both conditions reachable at the same index.
- **Fillet produces invalid BRep**: `Part::Fillet` often creates invalid geometry on complex shapes. Always validate after fillet:
  ```python
  doc.recompute()
  if fillet.Shape.isValid():
      final = fillet
  # else: fall back to unfilleted shape
  ```
- **Boolean overlap**: When fusing reinforcements (gussets, ribs), the tool shape must VOLUMETRICALLY overlap the base — edge-touching produces zero overlap and fails silently. Verify with `base.common(tool).Volume > 0` before fusing.
- **`ImportGui` unavailable headless**: In headless mode, `ImportGui.export()` does not exist. Use `shape.exportStep(path)` for STEP or `Mesh.export([obj], path)` for STL.
- **Not installed**: FreeCAD is ~2GB installed. If not on system, the `freecad_exec` tool won't appear (service-gated).
- **AppImage on WSL**: Download the AppImage, extract with `--appimage-extract`, find binary at `squashfs-root/usr/bin/freecadcmd`. See `references/wsl-appimage-setup.md`.
- **stdout may be captured**: `print()` output can be interleaved with FreeCAD's progress bars. For debugging, log to a temp file and print only the final summary.
- **No GUI in headless**: `FreeCADGui` is unavailable. All operations use `FreeCAD` and `Part` modules only.
- **Part vs PartDesign**: Use `Part` module for direct BRep operations (simpler, more scriptable). Use `PartDesign` only when you need feature-based parametric history.
- **Large models**: Models with 1000+ objects may timeout. Increase `timeout` param or simplify design.
- **Units**: FreeCAD uses mm internally. Scale accordingly.
- **Export path**: Always specify absolute paths. Use `out_file` param so the tool confirms file creation.
- **Shape access**: For parametric objects, access geometry via `.Shape`. Ensure they've been computed first.
- **Boolean order matters**: `Part::Cut` with wrong Base/Tool assignment = wrong result. Base is cut FROM, Tool is the cutting tool.

## Verification

```bash
# Check FreeCAD is installed
freecadcmd --version
# or: python3 -c "import FreeCAD; print(FreeCAD.Version())"

# Test with a simple script
freecadcmd -c "import FreeCAD,Part; doc=FreeCAD.newDocument(); Part.show(Part.makeBox(10,10,10)); doc.recompute(); print(f'Volume: {Part.ActivePart.Shape.Volume}')"

# Verify tool is registered
hermes tools list | grep freecad
```

## Reference Files

- `references/wsl-appimage-setup.md` — AppImage download/extract on WSL without sudo
- `references/tool-audit.md` — Bugs found, fixes applied, test results
- `references/gemini-bridge-collaboration.md` — 7-round Gemini Pro collaborative bridge design session, with reusable patterns (compound assembly, oriented struts, Warren truss node math)
- `references/gemini-cad-collaboration.md` — Reusable 7-round pattern for collaborating with Gemini Pro on CAD projects: brainstorm → refine → build plan → review → source code upload → fix → sign-off. Includes FreeCAD API command patterns and proven bug categories.
- `references/standalone-project-page.md` — How to deliver CAD projects as self-contained HTML files with auto-loading 3D viewer, tabbed interface, and GitHub CDN fallback. Includes file:// vs http:// STL loading strategy and size thresholds for base64 embedding.
- `references/stl-decimation.md` — Vertex-clustering STL decimation for large models (>5MB) before base64 HTML embedding. numpy-stl, no external deps.
- `references/multicolor-stl-rendering.md` — Multi-color material-group GIF rendering with depth-sorted painter's algorithm
- `references/tower-of-babel-case-study.md` — 7-round Gemini Pro ziggurat build: piecewise spiral ramps, corner landings, single-boolean arched gatehouse, parametric safety assertions. 74 parts, print-ready.
- `templates/parametric_bracket.py` — Verified template: L-bracket with holes, gusset, fillets, STL/STEP/FCStd export
- `templates/bowstring_bridge.py` — Full Bowstring Warren Truss bridge template (197 components, 12m span)
- `templates/stl-viewer.html` — Reusable self-contained 3D viewer template. Copy next to any STL, edit CONFIG, deploy.
- `scripts/install.sh` — One-command install for other Hermes agents
- GitHub: https://github.com/lesterppo/hermes-freecad — standalone privacy-safe repo with tool + skill + installer
