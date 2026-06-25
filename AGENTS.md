# AGENTS.md — Hermes FreeCAD Integration

For AI coding assistants and Hermes agents working with this repo.

## What This Is

A single native, token-efficient 3D CAD tool for Hermes Agent. Registers via `tools.registry`, auto-discovered by Hermes's tool loader. Service-gated — only appears when `freecadcmd` is on PATH.

## File Structure

```
hermes-freecad/
├── tools/
│   └── freecad_tool.py     # freecad_exec — the tool
├── SKILL.md                # Hermes skill file (load with /skill freecad)
├── README.md               # User-facing install + usage
├── AGENTS.md               # This file
└── install.sh              # Automated install
```

## How the Tool Registers

`tools/freecad_tool.py` calls `registry.register()` at module level:

```python
from tools.registry import registry

registry.register(
    name="freecad_exec",
    toolset="freecad",
    schema=FREECAD_EXEC_SCHEMA,
    handler=lambda args, **kw: freecad_exec(code=args.get("code", ""), ...),
    check_fn=_freecad_available,
    emoji="🔧",
)
```

Hermes auto-discovers tools in `tools/*.py` by scanning for `registry.register()` calls. No manual import list needed.

## How It Works

1. Hermes calls `freecad_exec(code="...")` with FreeCAD Python code
2. The tool wraps user code in a marker-based template that collects document state after execution
3. Runs via subprocess: `freecadcmd /tmp/script.py`
4. Parses stdout — splits at `__FC_JSON_OUTPUT__` marker
5. Extracts balanced JSON (FreeCAD appends banner text after the JSON)
6. Returns compact result with `ok`, `o` (stdout), `doc` (document state), `e` (errors), `out_file` (export verification), `preview` (PNG render)

## Key Design Decisions

- **Single tool** — model writes Python, tool executes. No need for dozens of specialized tools.
- **Marker-based output parsing** — `__FC_JSON_OUTPUT__` separates user output from document state JSON
- **Balanced JSON extraction** — FreeCAD banner text trails after JSON; `_extract_json()` scans for balanced braces
- **Document cleanup** — `finally` block closes all documents after each call
- **Part.makeCompound()** — compound over sequential boolean fuses for performance
- **Preview via numpy-stl + Pillow** — no GUI/Xvfb dependency

## Adding to toolsets.py

The user must add the `freecad` toolset to `~/.hermes/hermes-agent/toolsets.py`:

```python
"freecad": {
    "description": "3D CAD modeling via FreeCAD headless — parametric modeling, STL/STEP/FCStd export",
    "tools": ["freecad_exec"],
    "includes": [],
},
```

The `install.sh` script handles this automatically.

## Design Principles

- **Token efficiency**: 310-token schema, compact JSON output, terse keys
- **Service gating**: `check_fn=_freecad_available` — zero schema cost when FreeCAD not installed
- **Single purpose**: One tool does one thing well (execute FreeCAD Python, return structured results)
- **Direct execution**: Tool runs code, returns results — no MCP server overhead
- **Privacy-safe**: No hardcoded paths, no personal data, no API keys

## Testing

```bash
# Test the tool imports and registers correctly
cd ~/.hermes/hermes-agent
python3 -c "
from tools.freecad_tool import freecad_exec, _freecad_available
print(f'FreeCAD available: {_freecad_available()}')
"

# If FreeCAD is installed, test end-to-end
python3 -c "
from tools.freecad_tool import freecad_exec
import json
r = freecad_exec(code='import FreeCAD,Part; d=FreeCAD.newDocument(\"T\"); Part.show(Part.makeBox(10,10,10),\"B\"); d.recompute()')
print(json.loads(r))
"
```
