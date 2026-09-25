"""Tiny orthographic box renderer in the pak128 dimetric projection, for
pixel-exact livery placement on simple vehicle bodies.

World: x = east (screen down-right), y = south (screen down-left), z = up.
Screen: X = 2A (x - y), Y = A (x + y) - B z   (A = 1.5 px/m, B = 4 px/m, i.e.
a 12 m bus is 51 px long in the horizontal views, 36 px along x in the
diagonal views and 25.5 rows in the vertical views, like native pak128 buses).

Vehicle frame: s = 0 (rear) .. L (front), t = -W/2 (left) .. +W/2 (right),
z = height above the road.

Pixels are ray-cast at their centre; every box face stores its texture
coordinates at the centre and at the four edge midpoints so that textures
can draw 1-px lines exactly once (see Px.line).
"""
import math
import numpy as np

A, B = 1.5, 4.0
R2 = math.sqrt(0.5)
HEAD = {"w": (-1, 0), "nw": (-R2, -R2), "n": (0, -1), "ne": (R2, -R2),
        "e": (1, 0), "se": (R2, R2), "s": (0, 1), "sw": (-R2, R2)}
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
CAM = np.array([1.0, 1.0, 2 * A / B])          # towards the viewer


def P(v):
    return np.array([2 * A * (v[0] - v[1]), A * (v[0] + v[1]) - B * v[2]])


class Box:
    def __init__(self, name, s0, s1, t0, t1, z0, z1, faces=None):
        self.name = name
        self.lo = (s0, t0, z0)
        self.hi = (s1, t1, z1)
        self.faces = faces  # None = all


class Px:
    """Texture-coordinate bundle for one pixel of one face."""
    __slots__ = ("face", "box", "c", "h", "v", "view")

    def __init__(self, face, box, c, h, v, view):
        self.face, self.box, self.c, self.h, self.v, self.view = face, box, c, h, v, view

    @property
    def s(self): return self.c[0]

    @property
    def t(self): return self.c[1]

    @property
    def z(self): return self.c[2]

    def rng(self, k):
        """range of coordinate k over the pixel, along the midline where it varies most"""
        h0, h1 = sorted((self.h[0][k], self.h[1][k]))
        v0, v1 = sorted((self.v[0][k], self.v[1][k]))
        return (h0, h1) if (h1 - h0) >= (v1 - v0) else (v0, v1)

    def line(self, k, p):
        lo, hi = self.rng(k)
        return lo <= p < hi

    def near(self, k, p, w):
        """pixel within w of p (w in coordinate units) or crossing p"""
        lo, hi = self.rng(k)
        return (lo - w) <= p < (hi + w)


FACES = {  # name: (fixed axis, which bound, free axes, normal in (h, r, z) frame)
    "top": (2, 1, (0, 1), (0, 0, 1)),
    "front": (0, 1, (1, 2), (1, 0, 0)),
    "rear": (0, 0, (1, 2), (-1, 0, 0)),
    "right": (1, 1, (0, 2), (0, 1, 0)),
    "left": (1, 0, (0, 2), (0, -1, 0)),
}


def render(view, boxes, tex, L, origin, size=128):
    """Return an (size,size,3) uint8 image (None pixels = transparent key)."""
    hx, hy = HEAD[view]
    h3 = np.array([hx, hy, 0.0]); r3 = np.array([-hy, hx, 0.0]); z3 = np.array([0, 0, 1.0])
    axes = [h3, r3, z3]
    Pax = [P(a) for a in axes]
    O = np.array(origin, float)
    Lc = L / 2.0

    def world(c):  # vehicle coords (s,t,z) -> world vector
        return (c[0] - Lc) * h3 + c[1] * r3 + c[2] * z3

    ys, xs = np.mgrid[0:size, 0:size].astype(float)
    samples = {"c": (xs + .5, ys + .5), "l": (xs, ys + .5), "r": (xs + 1, ys + .5),
               "t": (xs + .5, ys), "b": (xs + .5, ys + 1)}
    cands = []  # (depth array, mask, face, box, coords dict)
    for box in boxes:
        for fname, (fix, bound, free, nrm) in FACES.items():
            if box.faces is not None and fname not in box.faces:
                continue
            n = sum(nrm[i] * axes[i] for i in range(3))
            if n @ CAM <= 1e-9:
                continue
            fv = (box.lo, box.hi)[bound][fix]
            a, b = free
            M = np.array([Pax[a], Pax[b]]).T
            if abs(np.linalg.det(M)) < 1e-9:
                continue
            Mi = np.linalg.inv(M)
            base = O - Lc * Pax[0] + fv * Pax[fix]
            co = {}
            for k, (sx, sy) in samples.items():
                dx, dy = sx - base[0], sy - base[1]
                arr = [None, None, None]
                arr[fix] = np.full_like(dx, fv)
                arr[a] = Mi[0, 0] * dx + Mi[0, 1] * dy
                arr[b] = Mi[1, 0] * dx + Mi[1, 1] * dy
                co[k] = arr
            cs = co["c"]
            eps = 1e-9
            mask = ((cs[a] >= box.lo[a] - eps) & (cs[a] <= box.hi[a] + eps) &
                    (cs[b] >= box.lo[b] - eps) & (cs[b] <= box.hi[b] + eps))
            depth = ((cs[0] - Lc) * (h3 @ CAM) + cs[1] * (r3 @ CAM) + cs[2] * (z3 @ CAM))
            cands.append((depth, mask, fname, box, co))
    out = np.zeros((size, size, 3), np.uint8); out[:] = (231, 255, 255)
    zbuf = np.full((size, size), -1e18)
    for depth, mask, fname, box, co in cands:
        yy, xx = np.where(mask & (depth > zbuf))
        for y, x in zip(yy, xx):
            c = tuple(float(co["c"][i][y, x]) for i in range(3))
            hs = (tuple(float(co["l"][i][y, x]) for i in range(3)), tuple(float(co["r"][i][y, x]) for i in range(3)))
            vs = (tuple(float(co["t"][i][y, x]) for i in range(3)), tuple(float(co["b"][i][y, x]) for i in range(3)))
            col = tex(Px(fname, box.name, c, hs, vs, view))
            if col is None:
                continue
            if depth[y, x] > zbuf[y, x]:
                zbuf[y, x] = depth[y, x]
                out[y, x] = col
    return out, zbuf


def project(view, L, origin, s, t, z):
    hx, hy = HEAD[view]
    h3 = np.array([hx, hy, 0.0]); r3 = np.array([-hy, hx, 0.0])
    w = (s - L / 2) * h3 + t * r3 + np.array([0, 0, z])
    return np.array(origin, float) + P(w)
