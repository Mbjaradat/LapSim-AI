"""Minimal reader for the audited SPL legacy binary VTK triangle-strip meshes."""
import re
import struct


def read_mesh(path):
    data = path.read_bytes()
    if b'BINARY\nDATASET POLYDATA\n' not in data[:100]:
        raise ValueError('Expected binary legacy VTK POLYDATA')
    header = re.search(rb'POINTS (\d+) float\r?\n', data)
    count = int(header[1])
    end = header.end() + count * 12
    values = struct.unpack(f'>{count * 3}f', data[header.end():end])
    vertices = list(zip(values[::3], values[1::3], values[2::3]))
    strips = re.match(rb'\s*TRIANGLE_STRIPS (\d+) (\d+)\r?\n', data[end:])
    if strips is None:
        raise ValueError('Expected triangle strips')
    start = end + strips.end()
    indices = struct.unpack(f'>{int(strips[2])}i', data[start:start + int(strips[2]) * 4])
    faces = []
    cursor = 0
    for _ in range(int(strips[1])):
        size = indices[cursor]
        strip = indices[cursor + 1:cursor + 1 + size]
        if len(strip) != size or any(i < 0 or i >= count for i in strip):
            raise ValueError('Invalid strip indices')
        for i in range(size - 2):
            triangle = (strip[i+1], strip[i], strip[i+2]) if i % 2 else tuple(strip[i:i+3])
            if len(set(triangle)) == 3:
                faces.append(triangle)
        cursor += size + 1
    if cursor != len(indices):
        raise ValueError('Invalid strip length')
    return vertices, faces
