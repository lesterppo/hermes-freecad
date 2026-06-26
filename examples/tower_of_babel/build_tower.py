#!/usr/bin/env freecadcmd
"""
Tower of Babel — Parametric Mesopotamian Ziggurat
7 tiers, spiral ramp, buttresses, grand staircase, summit temple.
Built with Gemini Pro (session c_72a72a8b188e50d9, Rounds 1-3).
"""
import os, sys

# === DOUBLE-EXECUTION GUARD ===
# FreeCAD runs scripts twice: once as exec(), once as macro.
# Without this guard, the second pass re-executes on a stale document and crashes.
# Use a unique marker per run to avoid stale guards from previous runs.
import time
MARKER = f"/tmp/_fc_tower_babel_{os.getpid()}"
if os.path.exists(MARKER):
    sys.exit(0)
open(MARKER, "w").close()

import math
import FreeCAD
import Part
from FreeCAD import Vector, Placement, Rotation

OUTPUT_DIR = "/tmp/tower_of_babel"

def build_tower_of_babel():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # =========================================================================
    # PARAMETRIC VARIABLES (Locked from R2)
    # =========================================================================
    base_width = 300.0
    base_height = 50.0
    height_decay = 0.90
    step_depth = 16.0
    ramp_width = 12.0
    num_tiers = 7
    
    buttress_width = 15.0
    buttress_depth = 10.0
    staircase_width = 60.0
    staircase_projection = 60.0
    
    temple_width = 84.0
    temple_height = 35.0
    column_radius = 3.0

    # === PARAMETRIC SAFETY ASSERTIONS ===
    assert step_depth >= ramp_width, "Ramp width cannot exceed step depth."
    assert base_width - (num_tiers * 2 * step_depth) > 0, "Too many tiers for this base width/step depth."

    assembly_parts = []
    
    # Trackers for the loop
    tiers_data = []  # Will store dicts of {W, H, Z_base}
    current_z = 0.0
    current_w = base_width
    current_h = base_height

    # =========================================================================
    # 1. BUILD TIERS
    # =========================================================================
    print("Building 7 structural tiers...")
    for i in range(num_tiers):
        tier_info = {'W': current_w, 'H': current_h, 'Z': current_z}
        tiers_data.append(tier_info)
        
        tier_box = Part.makeBox(current_w, current_w, current_h)
        # Center the tier exactly at (0,0,Z)
        tier_box.translate(Vector(-current_w/2, -current_w/2, current_z))
        assembly_parts.append(tier_box)
        
        print(f"  Tier {i+1}: W={current_w:.1f} H={current_h:.1f} Z={current_z:.1f}")
        
        # Prepare next tier dimensions
        current_z += current_h
        current_w -= (2 * step_depth)
        current_h *= height_decay

    # =========================================================================
    # 2. SPIRAL RAMPS & LANDING PADS (Tiers 1 to 6)
    # =========================================================================
    print("Generating piecewise spiral ramps and corners...")
    # Ramps sit ON tier i-1 and lean AGAINST tier i
    for i in range(1, num_tiers):
        W_i = tiers_data[i]['W']
        H_i = tiers_data[i]['H']
        Z_base = tiers_data[i]['Z']
        
        for face_index in range(4):
            # Face 0=South, 1=West, 2=North, 3=East
            Z_start = Z_base + face_index * (H_i / 4.0)
            Z_end = Z_base + (face_index + 1) * (H_i / 4.0)
            
            # --- RAMP WEDGE (Profile on South Face) ---
            if Z_start > Z_base:
                # Trapezoid profile
                pts = [
                    Vector(W_i/2, -W_i/2, Z_base),     # Bottom East
                    Vector(-W_i/2, -W_i/2, Z_base),    # Bottom West
                    Vector(-W_i/2, -W_i/2, Z_end),     # Top West
                    Vector(W_i/2, -W_i/2, Z_start),    # Top East
                    Vector(W_i/2, -W_i/2, Z_base)      # Close
                ]
            else:
                # Triangle profile (Starts at ground level)
                pts = [
                    Vector(W_i/2, -W_i/2, Z_base),     # Bottom East
                    Vector(-W_i/2, -W_i/2, Z_base),    # Bottom West
                    Vector(-W_i/2, -W_i/2, Z_end),     # Top West
                    Vector(W_i/2, -W_i/2, Z_base)      # Close
                ]
            
            # Create the 2D face and extrude it OUTWARD (Negative Y)
            wire = Part.makePolygon(pts)
            face = Part.Face(wire)
            ramp_segment = face.extrude(Vector(0, -ramp_width, 0))
            
            # Rotate segment to the correct architectural face
            # Negative 90 degrees per face_index wraps the ramp clockwise
            rot_placement = Placement(Vector(0,0,0), Rotation(Vector(0,0,1), -90 * face_index))
            ramp_segment.Placement = rot_placement
            assembly_parts.append(ramp_segment)
            
            # --- CORNER LANDING PAD ---
            # Solid block at the end of the current ramp face, squaring off the corner
            pad_height = Z_end - Z_base
            pad = Part.makeBox(ramp_width, ramp_width, pad_height)
            
            # Position at South-West corner of the current tier's wall
            pad_base = Placement(
                Vector(-W_i/2 - ramp_width, -W_i/2 - ramp_width, Z_base),
                Rotation()
            )
            # Rotate pad to the correct corner
            pad.Placement = rot_placement.multiply(pad_base)
            assembly_parts.append(pad)

    # =========================================================================
    # 3. BUTTRESSES (Tier 0 Fortifications)
    # =========================================================================
    print("Constructing base buttresses...")
    W_0 = tiers_data[0]['W']
    H_0 = tiers_data[0]['H']
    
    # 4 faces (S, W, N, E)
    angles = [0, -90, -180, -270]
    for face_idx in range(4):
        # Dynamic buttress positions based on base width
        p_outer = W_0 / 2.0 - buttress_width  # Aligns to the outer corners
        p_inner = p_outer / 3.0                # Spaces the inner buttresses evenly
        # South face gets 2 to leave room for stair; others get 4 evenly spaced
        positions = [-p_outer, p_outer] if face_idx == 0 else [-p_outer, -p_inner, p_inner, p_outer]
        
        for x_pos in positions:
            buttress = Part.makeBox(buttress_width, buttress_depth, H_0)
            
            # Place on South Face projecting outward
            base_plm = Placement(
                Vector(x_pos - buttress_width/2, -W_0/2 - buttress_depth, 0),
                Rotation()
            )
            rot_plm = Placement(Vector(0,0,0), Rotation(Vector(0,0,1), angles[face_idx]))
            
            buttress.Placement = rot_plm.multiply(base_plm)
            assembly_parts.append(buttress)

    # =========================================================================
    # 4. GRAND STAIRCASE
    # =========================================================================
    print("Carving grand staircase...")
    # Wedge profile drawn in the YZ plane (at X=0), looking West
    stair_pts = [
        Vector(0, -W_0/2 - staircase_projection, 0),  # Ground, furthest South
        Vector(0, -W_0/2, 0),                          # Wall base
        Vector(0, -W_0/2, H_0),                        # Wall top
        Vector(0, -W_0/2 - staircase_projection, 0)    # Close
    ]
    stair_wire = Part.makePolygon(stair_pts)
    stair_face = Part.Face(stair_wire)
    staircase = stair_face.extrude(Vector(staircase_width, 0, 0))  # Extrude East (+X)
    
    # Shift West to perfectly center on the South face
    staircase.translate(Vector(-staircase_width/2, 0, 0))
    assembly_parts.append(staircase)

    # =========================================================================
    # 4b. MONUMENTAL GATEHOUSE (single boolean cut for archway)
    # =========================================================================
    print("Forging the Monumental Gatehouse...")
    
    # Dimensions
    gate_w = 100.0   # Wider than the 60mm staircase
    gate_d = 40.0    # Depth of the structure
    gate_h = 60.0    # Height
    
    # Calculate Y-position so it straddles the very bottom of the staircase
    gate_y_start = -W_0/2 - staircase_projection
    
    # 1. Main Gatehouse Block
    gate_body = Part.makeBox(gate_w, gate_d, gate_h)
    gate_body.translate(Vector(-gate_w/2, gate_y_start, 0))
    
    # 2. Archway Parameters (The tunnel)
    arch_w = 40.0         # Opening width
    arch_h = 35.0         # Height to the springline
    arch_radius = arch_w / 2.0
    
    # 3. Create the Arch Negative (Box + Cylinder compound)
    # The box handles the rectangular bottom of the tunnel
    arch_box = Part.makeBox(arch_w, gate_d + 10, arch_h)
    arch_box.translate(Vector(-arch_w/2, gate_y_start - 5, 0))
    
    # The cylinder handles the curved top
    # Rotated -90 degrees on X axis to punch through along Y
    arch_cyl = Part.makeCylinder(arch_radius, gate_d + 10)
    arch_cyl.Placement = Placement(
        Vector(0, gate_y_start - 5, arch_h),
        Rotation(Vector(1, 0, 0), -90)
    )
    
    # 4. Execute the Boolean Cut
    arch_negative = Part.makeCompound([arch_box, arch_cyl])
    gate_final = gate_body.cut(arch_negative)
    
    # Append the finished boolean shape to our master assembly
    assembly_parts.append(gate_final)

    # =========================================================================
    # 5. SUMMIT TEMPLE
    # =========================================================================
    print("Erecting summit temple...")
    Z_temple = current_z  # The height accumulated after 7 tiers
    
    # Main Cella
    temple = Part.makeBox(temple_width, temple_width, temple_height)
    temple.translate(Vector(-temple_width/2, -temple_width/2, Z_temple))
    assembly_parts.append(temple)
    
    # Entrance Columns
    col1 = Part.makeCylinder(column_radius, temple_height)
    col1.translate(Vector(-10, -temple_width/2, Z_temple))
    assembly_parts.append(col1)
    
    col2 = Part.makeCylinder(column_radius, temple_height)
    col2.translate(Vector(10, -temple_width/2, Z_temple))
    assembly_parts.append(col2)

    # =========================================================================
    # 6. COMPOUND & EXPORT
    # =========================================================================
    print(f"\nCompounding {len(assembly_parts)} parts into single architectural mesh...")
    master_tower = Part.makeCompound(assembly_parts)
    
    # Create FreeCAD Headless Document
    doc = FreeCAD.newDocument("TowerOfBabel")
    obj = doc.addObject("Part::Feature", "Tower")
    obj.Shape = master_tower
    
    # Export FCStd
    fcstd_path = os.path.join(OUTPUT_DIR, "TowerOfBabel.FCStd")
    doc.saveAs(fcstd_path)
    print(f"Saved native FreeCAD file: {fcstd_path}")
    
    # Export STL (high quality)
    stl_path = os.path.join(OUTPUT_DIR, "TowerOfBabel.stl")
    import Mesh
    Mesh.export([obj], stl_path)
    print(f"Exported production STL: {stl_path}")
    
    # Metrics
    bbox = master_tower.BoundBox
    print("\n=== FINAL BUILD STATS ===")
    print(f"Total Parts:         {len(assembly_parts)}")
    print(f"Tower Bounding Box:  X: {bbox.XLength:.1f}mm  Y: {bbox.YLength:.1f}mm  Z: {bbox.ZLength:.1f}mm")
    print(f"Volume:              {master_tower.Volume:.1f} mm^3")
    print(f"Surface Area:        {master_tower.Area:.1f} mm^2")
    
    # Validate
    print(f"\nGeometry Valid:      {master_tower.isValid()}")
    print(f"Geometry Closed:     {master_tower.isClosed()}")

# Execute immediately — FreeCAD's exec() sets __name__ to the filename, not '__main__'
build_tower_of_babel()
print("\nArchitecture complete. Exiting.")
