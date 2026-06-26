# Bridge Demo

Two self-contained HTML pages demonstrating the Bowstring Warren Truss Bridge — an AI-generated 3D parametric model built by Hermes Agent × Gemini Pro over 7 collaborative rounds.

## Open

| File | Loads STL | Best for |
|------|-----------|----------|
| [`index.html`](index.html) | Auto-loads from GitHub CDN | Quick view, one-click, no setup |
| [`standalone.html`](standalone.html) | Self-contained (STL embedded) | Offline, double-click from desktop, no network |
| [`manual.html`](manual.html) | Auto-loads on http://, file picker on file:// | Offline use with local full-res STL |

Just open either file in any browser. No server required.

## index.html — Auto-Loader

**One-click:** opens and the bridge appears. 4-tab interface with 3D viewer, specs, design process, and file listing. Tries three STL sources automatically:
1. Same folder (`WarrenBridge_v3.stl`)
2. GitHub CDN (`raw.githubusercontent.com/lesterppo/hermes-freecad/main/WarrenBridge_v3.stl`)
3. Local server fallback

## manual.html — Manual Loader

**Two modes:**
- **http://** — loads STL automatically from same-directory URL
- **file://** (double-click from desktop) — shows "Choose STL File" button. Select `WarrenBridge_v3.stl` from the same folder and it loads instantly via async blob URL (smooth, non-blocking)

Focused 3D viewer with orbit controls, view presets, wireframe toggle, auto-rotate, keyboard shortcuts. FPS counter and triangle count HUD.

## Controls (both viewers)

| Action | Input |
|--------|-------|
| Rotate | 🖱 Left-drag |
| Zoom | 🖱 Scroll wheel |
| Pan | 🖱 Right-drag |
| Top view | Press `T` |
| Front view | Press `F` |
| Side view | Press `S` |
| Default view | Press `D` |
| Close-up | Press `C` |
| Wireframe | Press `W` |
| Auto-rotate | Press `R` |
| Reset | `Escape` |

## Technical Notes

- **Z-up → Y-up:** The STL is exported from FreeCAD (Z-up coordinate system). Both viewers apply `geometry.rotateX(-Math.PI/2)` to convert to Three.js Y-up.
- **file:// performance:** `manual.html` uses blob URL → `STLLoader.load()` (async, non-blocking) instead of `loader.parse()` (synchronous, freezes page for ~3s on 376K triangles).
- **index.html:** Single file with embedded CSS, no external stylesheets. Only external dependency is Three.js from jsDelivr CDN.

## Privacy

No tracking, no analytics, no external dependencies except Three.js CDN and the STL file from this repo. All rendering happens locally in your browser.
