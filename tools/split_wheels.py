#!/usr/bin/env python3
"""
Split the wheels out of a single-shell car STL into their own named regions.

Downloaded car models are usually one welded surface, so the tyres and rims
can't be given their own boundary condition. This labels every triangle whose
centroid lies inside a wheel's cylinder (radius about the axle, between the
inner and outer tyre faces) and writes a multi-solid ASCII STL:

    solid body ... endsolid body
    solid wheel_FL ... endsolid wheel_FL
    ...

snappyHexMesh turns each solid into its own patch, named <surface>_<solid>
(e.g. corvette_wheel_FL), which can then take a rotatingWallVelocity condition.

Wheels are described in a JSON file, one entry per wheel:
    {"FL": {"x": 0.9965, "z": 0.317, "r_cut": 0.345, "y_in": 0.615, "y_out": 0.95, "side": 1}, ...}
x, z   axle centre (m); the axle is assumed parallel to y
r_cut  radius separating tyre from wheel arch (pick it in the gap between them)
y_in, y_out  |y| range of the wheel (inner tyre face to outer rim face)
side   +1 for the +y side of the car, -1 for the -y side
exclude (optional) list of boxes [x0, x1, |y|0, |y|1, z0, z1] that stay part of the
       body even if inside the wheel cylinder, e.g. suspension springs that intersect
       the tyre in a visual model and must not rotate

Usage:  python3 split_wheels.py car.stl wheels.json car_split.stl [preview.png]
"""
import json
import re
import sys

import numpy as np


def read_stl(path):
    text = open(path).read()
    v = np.array(re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text), float)
    return v.reshape(-1, 3, 3)


def write_stl(path, tris, labels, names):
    with open(path, "w") as f:
        for i, name in enumerate(names):
            f.write(f"solid {name}\n")
            for t in tris[labels == i]:
                n = np.cross(t[1] - t[0], t[2] - t[0])
                n /= np.linalg.norm(n) or 1.0
                f.write(f" facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n  outer loop\n")
                for p in t:
                    f.write(f"   vertex {p[0]:.7e} {p[1]:.7e} {p[2]:.7e}\n")
                f.write("  endloop\n endfacet\n")
            f.write(f"endsolid {name}\n")


def main():
    stl_in, wheels_json, stl_out = sys.argv[1:4]
    preview = sys.argv[4] if len(sys.argv) > 4 else None
    tris = read_stl(stl_in)
    wheels = json.load(open(wheels_json))
    c = tris.mean(axis=1)
    names = ["body"] + [f"wheel_{k}" for k in wheels]
    labels = np.zeros(len(tris), int)
    for i, (k, w) in enumerate(wheels.items(), start=1):
        sy = w["side"] * c[:, 1]
        inside = (np.hypot(c[:, 0] - w["x"], c[:, 2] - w["z"]) < w["r_cut"]) & (sy > w["y_in"]) & (sy < w["y_out"])
        for x0, x1, y0, y1, z0, z1 in w.get("exclude", []):
            inside &= ~((c[:, 0] > x0) & (c[:, 0] < x1) & (sy > y0) & (sy < y1) & (c[:, 2] > z0) & (c[:, 2] < z1))
        labels[inside] = i
    for i, name in enumerate(names):
        print(f"{name:10s} {np.sum(labels == i):7d} triangles")
    write_stl(stl_out, tris, labels, names)
    print(f"wrote {stl_out}")

    if preview:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(16, 4))
        for ax, side in zip(axes, (1, -1)):
            m = side * c[:, 1] > 0.3
            ax.scatter(c[m & (labels == 0), 0], c[m & (labels == 0), 2], s=0.1, c="0.7", label="body")
            wm = m & (labels > 0)
            ax.scatter(c[wm, 0], c[wm, 2], s=0.1, c=labels[wm], cmap="tab10", vmin=0, vmax=9)
            ax.set_aspect("equal")
            ax.set_title(f"{'+y (left)' if side > 0 else '-y (right)'} side: wheels in colour, body grey")
        fig.tight_layout()
        fig.savefig(preview, dpi=80)


if __name__ == "__main__":
    main()
