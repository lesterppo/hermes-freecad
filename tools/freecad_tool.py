#!/usr/bin/env python3
"""
FreeCAD integration — native, token-efficient CAD tool for Hermes.

FreeCAD is a parametric 3D CAD modeler with a complete Python API built on
OpenCASCADE, Coin3D, and Qt. The `freecad_exec` tool runs FreeCAD Python code
in headless mode (`freecadcmd`) and returns compact JSON output.

Output format:
- `o`: captured stdout (print() statements)
- `doc`: document state (object names, types, counts) after execution
- `e`: error messages from stderr
- `preview`: path to rendered PNG preview (when render param is set)
- `out_file`: export verification (size, path)
- `ok`: true/false for success
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, Optional


# ═══════════════════════════════════════════════════════════════════
# Dependency check
# ═══════════════════════════════════════════════════════════════════

def _freecad_available() -> bool:
    """Check if freecadcmd (headless) is available."""
    if shutil.which("freecadcmd") is not None:
        return True
    if shutil.which("FreeCADCmd") is not None:
        return True
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import FreeCAD"],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _find_freecad_cmd() -> Optional[str]:
    """Find the FreeCAD headless executable."""
    for cmd in ["freecadcmd", "FreeCADCmd"]:
        path = shutil.which(cmd)
        if path:
            return path
    return None


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _ok(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def _err(msg: str) -> str:
    return _ok({"ok": False, "e": msg})


def _indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line.strip() else line
                     for line in text.split("\n"))


def _format_size(size_bytes: int) -> str:
    size: float = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _extract_json(text: str) -> Optional[str]:
    """Extract the first balanced JSON object/array from a string.
    
    Handles trailing noise like FreeCAD banner text after the JSON payload.
    """
    if not text:
        return None
    opener = text[0]
    closer = {"{": "}", "[": "]"}.get(opener)
    if not closer:
        return None
    
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[:i + 1]
    return None


def _parse_stdout(stdout: str) -> tuple:
    """Parse stdout: split at marker, extract user output and doc state JSON."""
    marker = "__FC_JSON_OUTPUT__"
    if marker not in stdout:
        return stdout.strip(), {}
    
    before, after = stdout.split(marker, 1)
    user_output = before.strip()
    json_chunk = _extract_json(after.lstrip())
    if json_chunk:
        try:
            return user_output, json.loads(json_chunk)
        except json.JSONDecodeError:
            pass
    return user_output, {}


def _filter_stderr(stderr: str) -> str:
    """Extract only real errors from stderr (strip FreeCAD banner spam)."""
    if not stderr:
        return ""
    lines = [l for l in stderr.split("\n") if l.strip() and any(
        k in l.lower() for k in ("error", "traceback", "exception", "failed")
    )]
    return "\n".join(lines[:5])[:1000]


def _render_stl_preview(stl_path: str, png_path: str) -> bool:
    """Render an isometric PNG preview from an STL file.
    
    Uses numpy-stl + PIL for lightweight, headless rendering.
    Returns True on success, False if dependencies are missing.
    """
    try:
        from stl import mesh as stl_mesh
        from PIL import Image, ImageDraw
        import numpy as np
        import math
    except ImportError:
        return False
    
    try:
        m = stl_mesh.Mesh.from_file(stl_path)
        vertices = m.vectors.reshape(-1, 3)
        normals = m.normals

        # Isometric projection (120° between axes, 30° from horizontal)
        angle = math.radians(30)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        # Project to 2D
        x_2d = (vertices[:, 0] - vertices[:, 1]) * cos_a
        y_2d = (vertices[:, 0] + vertices[:, 1]) * sin_a - vertices[:, 2]
        
        # Normalize to image space
        x_2d -= x_2d.min()
        y_2d -= y_2d.min()
        
        # Face colors from normals (lighting simulation)
        light_dir = np.array([0.577, 0.577, 0.577])  # normalized isometric light
        face_brightness = np.abs(np.dot(normals, light_dir))
        face_brightness = 0.3 + 0.7 * face_brightness  # ambient + diffuse
        
        # Scale to image
        scale = 400 / max(x_2d.max(), y_2d.max(), 1)
        img_w = int(x_2d.max() * scale) + 60
        img_h = int(y_2d.max() * scale) + 60
        x_2d = (x_2d * scale + 30).astype(int)
        y_2d = (y_2d * scale + 30).astype(int)
        
        # Render faces sorted by depth (painter's algorithm)
        centroids_z = m.vectors.mean(axis=1)[:, 2]
        order = np.argsort(-centroids_z)  # back to front
        
        img = Image.new("RGBA", (img_w, img_h), (26, 26, 46, 255))
        draw = ImageDraw.Draw(img)
        
        for i in order:
            tri = [(x_2d[i*3 + j], y_2d[i*3 + j]) for j in range(3)]
            brightness = int(face_brightness[i] * 255)
            base_color = (255, 140, 0)
            r = int(base_color[0] * face_brightness[i])
            g = int(base_color[1] * face_brightness[i])
            b = int(base_color[2] * face_brightness[i])
            draw.polygon(tri, fill=(r, g, b, 255), outline=(r//2, g//2, b//2, 255))
        
        img.save(png_path)
        return True
    except Exception:
        return False


def _build_result(
    user_output: str, doc_state: dict, stderr: str, result_rc: int,
    out_file: Optional[str] = None, render: Optional[str] = None,
) -> str:
    """Build the final result dict and serialize to JSON."""
    if "error" in doc_state:
        return _err(f"FreeCAD script error: {doc_state['error']}")
    
    err_lines = _filter_stderr(stderr)
    
    # Non-zero exit with no docs = crash or compile error
    if result_rc != 0 and not doc_state.get("docs"):
        msg = err_lines or stderr[:500]
        return _err(f"FreeCAD error (exit {result_rc}): {msg}")
    
    # Stderr errors with no docs = syntax/compile error caught by FreeCAD
    if err_lines and not doc_state.get("docs"):
        return _err(f"FreeCAD script error: {err_lines}")
    
    result_dict: Dict[str, Any] = {"ok": True}
    if user_output:
        result_dict["o"] = user_output[:4000]
    if doc_state.get("docs"):
        result_dict["doc"] = doc_state["docs"]
    
    if err_lines:
        result_dict["e"] = err_lines
    
    if out_file:
        if os.path.exists(out_file):
            size = os.path.getsize(out_file)
            result_dict["out_file"] = {
                "path": out_file, "size": size, "size_human": _format_size(size),
            }
        else:
            result_dict["out_file"] = {"path": out_file, "created": False}
    
    if render:
        stl_path = out_file or render
        if os.path.exists(stl_path) and stl_path.endswith(".stl"):
            if _render_stl_preview(stl_path, render):
                result_dict["preview"] = render
    
    return _ok(result_dict)


# ═══════════════════════════════════════════════════════════════════
# Wrapper script template
# ═══════════════════════════════════════════════════════════════════

_WRAPPER_TEMPLATE = """\
import sys, json as _fc_json
_fc_exc = None
try:
{code}
    import FreeCAD
    _fc_docs = []
    for _fc_docname in FreeCAD.listDocuments():
        _fc_doc = FreeCAD.getDocument(_fc_docname)
        _fc_objects = []
        for _fc_obj in _fc_doc.Objects:
            _fc_objects.append({{
                "n": _fc_obj.Name,
                "t": _fc_obj.TypeId,
                "l": _fc_obj.Label,
            }})
        _fc_docs.append({{
            "name": _fc_doc.Name,
            "filename": _fc_doc.FileName if hasattr(_fc_doc, 'FileName') else "",
            "objects": _fc_objects,
            "n_objects": len(_fc_objects),
        }})
    print("__FC_JSON_OUTPUT__")
    print(_fc_json.dumps({{
        "docs": _fc_docs, "n_docs": len(_fc_docs),
    }}, separators=(",", ":")))
except Exception as _fc_e:
    print("__FC_JSON_OUTPUT__")
    print(_fc_json.dumps({{"error": str(_fc_e)}}))
finally:
    # Close all documents to prevent leaks in long-running FreeCAD processes.
    # Each invocation gets a fresh process, but future persistent-mode backends
    # (e.g. FreeCAD running as a server) would accumulate documents otherwise.
    import FreeCAD as _fc_app
    for _fc_docname in list(_fc_app.listDocuments()):
        try:
            _fc_app.closeDocument(_fc_docname)
        except Exception:
            pass
"""


def _build_wrapped_script(code: str) -> str:
    """Wrap user code in the marker-based wrapper template."""
    indented_code = _indent(code, 4)
    script = _WRAPPER_TEMPLATE.replace("{code}", indented_code)
    script = script.replace("{{", "{").replace("}}", "}")
    return script


# ═══════════════════════════════════════════════════════════════════
# Tool: freecad_exec
# ═══════════════════════════════════════════════════════════════════

def freecad_exec(
    code: str,
    out_file: Optional[str] = None,
    render: Optional[str] = None,
    timeout: int = 120,
) -> str:
    """Execute FreeCAD Python code in headless mode. Returns compact JSON.

    code:      FreeCAD Python commands using FreeCAD's API.
    out_file:  Expected output file path. Tool verifies creation and reports size.
    render:    Path for a PNG preview render (e.g. '/tmp/preview.png').
               Requires the script to export an STL file first.
               Uses lightweight numpy-stl + PIL rendering (no GUI needed).
    timeout:   Max execution seconds (default 120, max 600).
    """
    try:
        if timeout > 600:
            timeout = 600
        if timeout < 1:
            timeout = 120

        fc_cmd = _find_freecad_cmd()
        executable = fc_cmd if fc_cmd else sys.executable
        return _run(executable, code, out_file, render, timeout)

    except subprocess.TimeoutExpired:
        return _err(f"FreeCAD execution timed out ({timeout}s). Simplify code.")
    except Exception as e:
        return _err(f"FreeCAD error: {e}")


def _run(
    executable: str, code: str, out_file: Optional[str],
    render: Optional[str], timeout: int,
) -> str:
    """Run the wrapped script via executable, parse output, return result."""
    wrapped = _build_wrapped_script(code)
    
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(wrapped)
        script_path = f.name
    
    try:
        result = subprocess.run(
            [executable, script_path],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "LC_ALL": "C.UTF-8"},
        )
        
        user_output, doc_state = _parse_stdout(result.stdout)
        return _build_result(
            user_output, doc_state, result.stderr.strip(), result.returncode,
            out_file=out_file, render=render,
        )
    finally:
        os.unlink(script_path)


# ═══════════════════════════════════════════════════════════════════
# Schema (token-efficient)
# ═══════════════════════════════════════════════════════════════════

FREECAD_EXEC_SCHEMA = {
    "name": "freecad_exec",
    "description": (
        "Execute FreeCAD Python code in headless mode. "
        "Model writes Python using FreeCAD's API — create/modify 3D objects, "
        "run booleans, export STL/STEP/FCStd, query geometry, etc. "
        "Key modules: FreeCAD, Part, Mesh, Sketcher, Draft, PartDesign. "
        "Common: doc=FreeCAD.newDocument(); box=doc.addObject('Part::Box','Box'); "
        "doc.recompute(); Part.show(shape); doc.saveAs('/path/file.FCStd'). "
        "Returns compact JSON: output, doc state, errors."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "FreeCAD Python code. Uses FreeCAD API: "
                    "FreeCAD.newDocument/createDocument, doc.addObject(type,name), "
                    "doc.recompute(), Part.makeBox/Sphere/Cylinder/Cone/Torus, "
                    "Part.show(shape), doc.saveAs(path), doc.exportObjects([objs],path), "
                    "Mesh.export(obj, 'file.stl'), obj.Shape.Volume/Area/CenterOfMass, "
                    "FreeCAD.Vector(x,y,z), FreeCAD.Placement(base,rot), "
                    "FreeCAD.Rotation(yaw,pitch,roll). Print() goes to output 'o' field."
                ),
            },
            "out_file": {
                "type": "string",
                "description": (
                    "Expected output file path (e.g., '/tmp/model.stl'). "
                    "Tool checks if file was created and reports size. "
                    "For high-quality STL, use Mesh.export(obj, path, "
                    "tolerance=0.01, angularDeflection=0.1) in your code."
                ),
            },
            "render": {
                "type": "string",
                "description": (
                    "Path to save a PNG preview render (e.g., '/tmp/preview.png'). "
                    "Script must export an STL first via Mesh.export(). "
                    "Uses lightweight isometric renderer — no GUI needed. "
                    "Requires: pip install numpy-stl pillow"
                ),
            },
            "timeout": {
                "type": "integer",
                "description": "Max execution seconds (default 120, max 600).",
                "default": 120,
            },
        },
        "required": ["code"],
    },
}


# ═══════════════════════════════════════════════════════════════════
# Registry
# ═══════════════════════════════════════════════════════════════════

from tools.registry import registry

registry.register(
    name="freecad_exec",
    toolset="freecad",
    schema=FREECAD_EXEC_SCHEMA,
    handler=lambda args, **kw: freecad_exec(
        code=args.get("code", ""),
        out_file=args.get("out_file"),
        render=args.get("render"),
        timeout=args.get("timeout", 120),
    ),
    check_fn=_freecad_available,
    emoji="🔧",
)
