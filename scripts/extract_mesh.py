"""
Extract 3D mesh geometry (vertices and triangle faces) from glTF binary buffer
so Plotly can render the authentic 3D heart with true clinical pressure heatmap.
"""
import json
import struct
import numpy as np
import os
import plotly.graph_objects as go

def extract_mesh_from_gltf(gltf_path: str, bin_path: str, output_npz: str):
    with open(gltf_path, 'r', encoding='utf-8') as f:
        gltf = json.load(f)

    with open(bin_path, 'rb') as f:
        bin_data = f.read()

    # Accessor 0: Positions
    acc_pos = gltf['accessors'][0]
    bv_pos = gltf['bufferViews'][acc_pos['bufferView']]
    pos_offset = bv_pos.get('byteOffset', 0) + acc_pos.get('byteOffset', 0)
    pos_count = acc_pos['count']

    # Float32 unpack (3 floats per vertex)
    vertices = np.frombuffer(bin_data, dtype=np.float32, count=pos_count * 3, offset=pos_offset)
    vertices = vertices.reshape((pos_count, 3))

    # Accessor 6: Indices (triangles)
    acc_idx = gltf['accessors'][6]
    bv_idx = gltf['bufferViews'][acc_idx['bufferView']]
    idx_offset = bv_idx.get('byteOffset', 0) + acc_idx.get('byteOffset', 0)
    idx_count = acc_idx['count']

    indices = np.frombuffer(bin_data, dtype=np.uint32, count=idx_count, offset=idx_offset)
    indices = indices.reshape((-1, 3))

    # Save to compressed NPZ
    np.savez_compressed(output_npz, vertices=vertices, indices=indices)
    print(f"Extracted {len(vertices)} vertices and {len(indices)} triangular faces!")
    print(f"Saved to {output_npz}")

    return vertices, indices

if __name__ == "__main__":
    gltf_p = os.path.join(os.path.dirname(__file__), "..", "assets", "heart_3d", "scene.gltf")
    bin_p = os.path.join(os.path.dirname(__file__), "..", "assets", "heart_3d", "scene.bin")
    out_npz = os.path.join(os.path.dirname(__file__), "..", "assets", "heart_3d", "heart_mesh.npz")
    v, idx = extract_mesh_from_gltf(os.path.abspath(gltf_p), os.path.abspath(bin_p), os.path.abspath(out_npz))
