# Bridge Demo

Self-contained HTML page demonstrating the Bowstring Warren Truss Bridge — an AI-generated 3D parametric model built by Hermes Agent × Gemini Pro.

## Open

Just open `index.html` in any browser. The 3D viewer loads automatically from GitHub CDN — no server, no file picker, no setup.

## What's included

| Tab | Content |
|-----|---------|
| 🎥 3D Viewer | Interactive Three.js model — orbit, zoom, pan, wireframe, auto-rotate, 5 view presets |
| 📐 Specs | Dimensions, component breakdown with proportional bar charts |
| 🔄 Process | 7-round Gemini Pro collaboration timeline, bugs found, design decisions |
| 📦 Files | Deliverable listing with sizes |

## How the STL loads

The HTML tries three sources automatically:
1. `WarrenBridge_v3.stl` in the same folder
2. GitHub raw CDN: `raw.githubusercontent.com/lesterppo/hermes-freecad/main/WarrenBridge_v3.stl`
3. Local server fallback

No file picker needed — the first successful source loads the model.

## Controls

| Action | Input |
|--------|-------|
| Rotate | Left-drag |
| Zoom | Scroll |
| Pan | Right-drag |
| Top/Front/Side | Press T / F / S |
| Wireframe | Press W |
| Auto-rotate | Press R |

## Privacy

No tracking, no analytics, no external dependencies except Three.js CDN and the STL file from this repo. All rendering happens locally in your browser.
