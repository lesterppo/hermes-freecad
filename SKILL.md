---
name: freecad
description: Parametric 3D CAD via FreeCAD's Python API in headless mode.
version: 1.0.0
author: Peter + Gemini Pro (collaborative design, session c_6f8a3e44bc91ac84)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cad, 3d-modeling, freecad, parametric-design, step, stl]
    category: software-development
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

## Prerequisites

Install FreeCAD:

```bash
# Ubuntu/Debian
sudo apt install freecad

# macOS
brew install --cask freecad

# Or AppImage (Linux, headless-capable since v0.21)
wget https://github.com/FreeCAD/FreeCAD/releases/download/1.0/FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage
chmod +x FreeCAD*.AppImage
./FreeCAD*.AppImage --appimage-extract
./squashfs-root/usr/bin/freecadcmd  # headless console
```

Enable the toolset:

```bash
hermes tools enable freecad
```

Start a new session, then load this skill: `/skill freecad`

## Quick Reference

### Core Modules

| Module | Import | Key Functions |
|--------|--------|--------------|
| FreeCAD | `import FreeCAD` | `newDocument(name)`, `open(path)`, `listDocuments()`, `getDocument(name)` |
| Part | `import Part` | `makeBox(l,w,h)`, `makeSphere(r)`, `makeCylinder(r,h)`, `makeCone(r1,r2,h)`, `makeTorus(r1,r2)`, `show(shape, name)` |
| Mesh | `import Mesh` | `export(objects, path)` for STL/OBJ |

### Document Operations

```python
doc = FreeCAD.newDocument("Name")
doc.recompute()         # ALWAYS recompute after changes
doc.saveAs("/path.FCStd")
doc.exportObjects([obj], "/path.step")
Mesh.export([obj], "/path.stl")  # for 3D printing
```

### Part Primitives
```python
Part.makeBox(10, 8, 6)       # L × W × H
Part.makeSphere(15)           # radius
Part.makeCylinder(5, 20)      # radius, height
Part.makeCone(10, 5, 20)      # r1, r2, height
Part.makeTorus(20, 5)         # major_r, minor_r
```

### Boolean Operations
```python
doc.addObject("Part::Fuse", "Union")     # .Base + .Tool
doc.addObject("Part::Cut", "Difference")  # .Base - .Tool
doc.addObject("Part::Common", "Intersect") # .Base ∩ .Tool
```

### Geometry Queries
```python
shape.Volume       # mm³
shape.Area         # mm²
shape.CenterOfMass # Vector(x,y,z)
shape.BoundBox     # (xmin,ymin,zmin, xmax,ymax,zmax)
shape.isClosed()   # watertight?
shape.isValid()    # valid BRep?
```

### Transforms
```python
FreeCAD.Vector(x, y, z)
FreeCAD.Placement(base_vec, rotation)
FreeCAD.Rotation(FreeCAD.Vector(0,0,1), direction.normalize())
obj.Placement.Base = FreeCAD.Vector(5, 0, 0)  # move
obj.Placement.Rotation = FreeCAD.Rotation(0,0,90)  # rotate
```

## Procedure

1. Plan the model — decide primitives and operations
2. Create document: `doc = FreeCAD.newDocument("Name")`
3. Add primitives or shapes
4. Apply operations (booleans, transforms)
5. **Recompute**: `doc.recompute()`
6. Verify geometry properties
7. Export: `doc.saveAs()` / `Mesh.export()`

## Pitfalls

- **Must recompute**: Changes don't take effect until `doc.recompute()`
- **No GUI in headless**: `FreeCADGui` is unavailable. Use `FreeCAD` and `Part` modules
- **Boolean over coplanar faces fail**: Over-penetrate parts slightly, use node spheres at joints
- **Part vs PartDesign**: Use `Part` for direct BRep ops (simpler, more scriptable)
- **Units**: FreeCAD uses mm internally
- **Fillet may produce invalid geometry**: Always check `shape.isValid()` after fillets
- **Use `Part.makeCompound()` over sequential fuses**: Much faster, avoids cascade failure
- **FreeCAD runs scripts twice**: Use a file-marker guard or `if os.environ.get('_FC_RAN'): sys.exit(0)`
- **Vector rotation**: Always `.normalize()` direction vectors before `FreeCAD.Rotation()`
- **For image previews**: Install `numpy-stl` + `pillow` for lightweight PNG renders

## Verification

```bash
freecadcmd --version
python3 -c "import FreeCAD; print(FreeCAD.Version())"
hermes tools list | grep freecad
```
