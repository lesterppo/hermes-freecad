#!/usr/bin/env python3
"""Decimate an STL via vertex clustering for self-contained HTML embedding.

Usage: python3 decimate_stl.py input.stl output.stl [voxel_mm]

Targets ~50K faces (good balance of detail vs file size).
Voxel size auto-computed; override with 3rd argument for finer/coarser output.
Uses only numpy-stl + stdlib — no trimesh/open3d needed.
"""
import sys, struct, os
import numpy as np
from stl import mesh

def decimate_stl(input_path, output_path, voxel_size=None, target_faces=50000):
    print(f"Loading {input_path}...")
    m = mesh.Mesh.from_file(input_path)
    orig_faces = len(m.vectors)
    print(f"  Original faces: {orig_faces:,}")

    verts = m.vectors.reshape(-1, 3)
    vmin = verts.min(axis=0)
    vmax = verts.max(axis=0)
    span = vmax - vmin
    
    if voxel_size is None:
        volume = span[0] * span[1] * span[2]
        voxel_size = max((volume / (target_faces * 3)) ** (1/3), span.max() / 200)
    print(f"  Voxel size: {voxel_size:.1f} mm (span: {span[0]:.0f} x {span[1]:.0f} x {span[2]:.0f})")

    grid_shape = np.ceil(span / voxel_size).astype(int) + 1
    grid_idx = np.floor((verts - vmin) / voxel_size).astype(int)
    np.clip(grid_idx, 0, grid_shape - 1, out=grid_idx)

    keys = (grid_idx[:,0].astype(np.int64) * (grid_shape[1]*grid_shape[2]) +
            grid_idx[:,1].astype(np.int64) * grid_shape[2] +
            grid_idx[:,2].astype(np.int64))
    
    unique_keys, inverse = np.unique(keys, return_inverse=True)
    print(f"  Unique voxels: {len(unique_keys):,}")

    new_verts = np.zeros((len(unique_keys), 3))
    np.add.at(new_verts, inverse, verts)
    counts = np.bincount(inverse)
    new_verts /= counts[:, np.newaxis]

    tri_indices = inverse.reshape(-1, 3)
    valid = ~((tri_indices[:,0] == tri_indices[:,1]) |
              (tri_indices[:,1] == tri_indices[:,2]) |
              (tri_indices[:,0] == tri_indices[:,2]))
    new_tris = tri_indices[valid]
    print(f"  Faces: {orig_faces:,} → {len(new_tris):,} ({100*len(new_tris)/orig_faces:.0f}%)")

    with open(output_path, 'wb') as f:
        f.write(b'\x00' * 80)
        f.write(struct.pack('<I', len(new_tris)))
        for tri in new_tris:
            v0, v1, v2 = new_verts[tri[0]], new_verts[tri[1]], new_verts[tri[2]]
            n = np.cross(v1 - v0, v2 - v0)
            normal = (n / np.linalg.norm(n)).astype(np.float32) if np.linalg.norm(n) > 1e-10 else np.array([0,0,1], dtype=np.float32)
            f.write(struct.pack('<3f', *normal))
            for v in [v0, v1, v2]:
                f.write(struct.pack('<3f', *v.astype(np.float32)))
            f.write(struct.pack('<H', 0))

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Output: {output_path} ({size_kb:.0f} KB)")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 decimate_stl.py input.stl output.stl [voxel_mm]")
        sys.exit(1)
    voxel = float(sys.argv[3]) if len(sys.argv) > 3 else None
    decimate_stl(sys.argv[1], sys.argv[2], voxel)
