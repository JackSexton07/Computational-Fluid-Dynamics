#!/usr/bin/env python3
"""
Frontal area of a body from its STL, as seen by the oncoming flow (looking along x).

It projects every triangle onto the y-z plane, fills them in on a fine pixel grid,
and counts the filled pixels. Overlapping triangles (front and back of the car
land on the same spot) are only counted once, which is what frontal area means.
Anything below z = 0 (the tyre sections sunk into the ground) is ignored.

Usage:  python3 frontal_area.py constant/triSurface/corvette.stl [pixel_size_m]
Writes frontal_area.png so you can check the silhouette looks right.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw


def load_stl(path):
    data = open(path, "rb").read()
    # Binary STL: 80-byte header, triangle count, then 50 bytes per triangle
    if len(data) >= 84:
        n = int(np.frombuffer(data[80:84], dtype="<u4")[0])
        if len(data) == 84 + 50 * n:
            dt = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
            return np.frombuffer(data[84:], dtype=dt, count=n)["v"].astype(float)
    # Otherwise treat it as ASCII STL
    pts = [list(map(float, line.split()[1:4]))
           for line in data.decode(errors="ignore").splitlines()
           if line.strip().startswith("vertex")]
    return np.array(pts).reshape(-1, 3, 3)


path = sys.argv[1]
res = float(sys.argv[2]) if len(sys.argv) > 2 else 0.001   # 1 mm pixels

tris = load_stl(path)
y, z = tris[:, :, 1], tris[:, :, 2]
y0 = y.min()
z0 = max(z.min(), 0.0)                  # ground level; below it is outside the domain
W = int(np.ceil((y.max() - y0) / res)) + 2
H = int(np.ceil((z.max() - z0) / res)) + 2

img = Image.new("1", (W, H), 0)
draw = ImageDraw.Draw(img)
for t in tris:
    draw.polygon([((p[1] - y0) / res, (p[2] - z0) / res) for p in t], fill=1)

pixels = int(np.array(img, dtype=bool).sum())
area = pixels * res * res

print(f"Triangles read : {len(tris)}")
print(f"Width  (y)     : {y.max() - y0:.4f} m")
print(f"Height (z>0)   : {z.max() - z0:.4f} m")
print(f"Frontal area   : {area:.4f} m^2")
print(f"Cd rescale     : multiply any Cd computed with Aref = 1.95 by {1.95 / area:.4f}")

img.transpose(Image.FLIP_TOP_BOTTOM).save("frontal_area.png")
print("Silhouette written to frontal_area.png")
