#!/bin/bash
# install.sh — Hermes FreeCAD Integration installer
# Copies freecad_exec tool into Hermes Agent and configures the freecad toolset.
# Run from the repo root.

set -e

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_TOOLS="${HERMES_HOME}/hermes-agent/tools"
TOOLSETS_FILE="${HERMES_HOME}/hermes-agent/toolsets.py"

echo "Hermes FreeCAD Integration — Installer"
echo "====================================="
echo ""

# 1. Verify Hermes Agent is installed
if [ ! -d "$HERMES_TOOLS" ]; then
    echo "ERROR: Hermes Agent tools directory not found at $HERMES_TOOLS"
    echo "       Install Hermes Agent first:"
    echo "       curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    exit 1
fi
echo "✓ Hermes Agent found at $HERMES_TOOLS"

# 2. Check FreeCAD availability
echo ""
echo "Checking FreeCAD..."

HAS_FREECAD=0
if command -v freecadcmd &> /dev/null; then
    HAS_FREECAD=1
    echo "  ✓ freecadcmd: $(freecadcmd --version 2>&1 | head -1)"
elif command -v FreeCADCmd &> /dev/null; then
    HAS_FREECAD=1
    echo "  ✓ FreeCADCmd: found at $(which FreeCADCmd)"
elif python3 -c "import FreeCAD" 2>/dev/null; then
    HAS_FREECAD=1
    echo "  ✓ FreeCAD Python module: importable"
else
    echo "  ⚠ FreeCAD not found."
    echo "    Install: sudo apt install freecad"
    echo "    Or download AppImage from: https://www.freecad.org/downloads.php"
    echo "    The freecad_exec tool will be hidden until FreeCAD is installed (service-gated)."
fi

# 3. Check optional preview dependencies
echo ""
echo "Checking preview render dependencies..."
HAS_PREVIEW=0
if python3 -c "from stl import mesh; from PIL import Image" 2>/dev/null; then
    HAS_PREVIEW=1
    echo "  ✓ numpy-stl + Pillow: available (PNG previews enabled)"
else
    echo "  ⚠ numpy-stl + Pillow: not found"
    echo "    Install: pip install numpy-stl pillow"
    echo "    Or: uv pip install numpy-stl pillow"
    echo "    Enables render='/path/preview.png' for isometric PNG previews."
fi

# 4. Copy tool
echo ""
echo "Installing freecad_exec tool..."
if [ -f "tools/freecad_tool.py" ]; then
    cp "tools/freecad_tool.py" "$HERMES_TOOLS/freecad_tool.py"
    echo "  ✓ tools/freecad_tool.py → $HERMES_TOOLS/freecad_tool.py"
else
    echo "  ✗ tools/freecad_tool.py: not found in current directory"
    echo "    Make sure you're running from the hermes-freecad repo root."
    exit 1
fi

# 5. Add freecad toolset to toolsets.py
echo ""
echo "Configuring freecad toolset..."

if grep -q '"freecad"' "$TOOLSETS_FILE"; then
    echo "  ⚠ freecad toolset already exists in toolsets.py — skipping"
else
    # Insert after the medical toolset (or spotify, or before Scenario-specific)
    python3 -c "
import re
path = '$TOOLSETS_FILE'
with open(path) as f:
    content = f.read()

freecad_block = '''
    \"freecad\": {
        \"description\": \"3D CAD modeling via FreeCAD headless — parametric modeling, STL/STEP/FCStd export\",
        \"tools\": [\"freecad_exec\"],
        \"includes\": [],
    },

    # Scenario-specific toolsets
'''

# Try inserting after medical, spotify, or before Scenario-specific
for anchor in ['\"medical\"', '\"spotify\"']:
    if anchor in content:
        content = re.sub(
            r'(\\s*# Scenario-specific toolsets)',
            freecad_block,
            content,
            count=1
        )
        break
else:
    # Fallback: insert before the first comment mentioning 'Scenario'
    content = re.sub(
        r'(\\n\\n\\s*# Scenario)',
        freecad_block.strip() + r'\\n\\n\\1',
        content,
        count=1
    )

with open(path, 'w') as f:
    f.write(content)
print('added')
" 2>/dev/null
    
    if grep -q '"freecad"' "$TOOLSETS_FILE"; then
        echo "  ✓ freecad toolset added to toolsets.py"
    else
        echo "  ⚠ Could not auto-insert toolset. Add manually:"
        echo ""
        echo '  "freecad": {'
        echo '      "description": "3D CAD modeling via FreeCAD headless — parametric modeling, STL/STEP/FCStd export",'
        echo '      "tools": ["freecad_exec"],'
        echo '      "includes": [],'
        echo '  },'
        echo ""
        echo "  to the TOOLSETS dict in $TOOLSETS_FILE"
    fi
fi

# 6. Install the skill
echo ""
echo "Installing freecad skill..."
SKILL_DIR="$HERMES_HOME/skills/software-development/freecad"
mkdir -p "$SKILL_DIR"
if [ -f "SKILL.md" ]; then
    cp "SKILL.md" "$SKILL_DIR/SKILL.md"
    echo "  ✓ SKILL.md → $SKILL_DIR/SKILL.md"
else
    echo "  ⚠ SKILL.md not found — skipping skill install"
fi

# 7. Enable the toolset
echo ""
if command -v hermes &> /dev/null; then
    hermes tools enable freecad 2>/dev/null && echo "✓ freecad toolset enabled" || echo "⚠ Enable manually: hermes tools enable freecad"
else
    echo "⚠ hermes CLI not in PATH — enable manually: hermes tools enable freecad"
fi

# 8. Summary
echo ""
echo "====================================="
echo "Installation complete."
echo ""
[ $HAS_FREECAD -eq 1 ] && echo "  ✓ freecad_exec — ready to use"
[ $HAS_FREECAD -eq 0 ] && echo "  ✗ freecad_exec — install FreeCAD first (sudo apt install freecad)"
[ $HAS_PREVIEW -eq 1 ] && echo "  ✓ PNG preview renders — enabled"
[ $HAS_PREVIEW -eq 0 ] && echo "  ⚠ PNG preview renders — pip install numpy-stl pillow"
echo ""
echo "Next steps:"
echo "  1. Start a new Hermes session"
echo "  2. Load the skill: /skill freecad"
echo "  3. Test: freecad_exec(code='import FreeCAD,Part; d=FreeCAD.newDocument(\"Test\"); Part.show(Part.makeBox(5,5,5),\"B\"); d.recompute(); print(\"OK\")')"
echo ""
echo "The freecad_exec tool will appear in your tool list when FreeCAD is installed."
