"""Vectorised orthographic box raycaster in the pak128 road projection.

Same projection and conventions as the DP Ostrava bus renderer (t39/render.py,
copied here as render.py): 1 carunit (1.5 m) = 4 px along a straight road,
4.2 px per metre vertically.

World: X = east (screen down-right), Y = south (screen down-left), Z = up.
Vehicle-local: u = along the length (0 = rear end, L = front end),
v = lateral (+v = the vehicle's right-hand side), z = up (metres).

Differences to render.py:
- numpy slab intersection for all pixels at once (fast);
- mat(face, u, v, z) may return an RGB tuple (used as is) or a Sh(rgb)
  paint, which is shaded per face like native pak128.cs vehicles (south-facing
  side 1.0, south-east 0.93, east 0.86; tops keep their colour);
- 3D polylines are depth tested against the boxes (a mirror behind the body
  is hidden);
- the module global VIEW_D holds the direction being rendered, so textures can
  size 1-px vertical lines per view (pxu()).
"""
import math
import numpy as np

AX, AY, HZ = 2.6667, 1.3333, 4.2
T = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
S2 = 1 / math.sqrt(2)
FWD = {"w": (-1, 0), "e": (1, 0), "n": (0, -1), "s": (0, 1),
       "ne": (S2, -S2), "sw": (-S2, S2), "nw": (-S2, -S2), "se": (S2, S2)}
VIEW = np.array([1.0, 1.0, 2 * AY / HZ])
PXZ = 1.0 / HZ
VIEW_D = "w"

SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
KEEP = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


def safe(c):
    c = tuple(int(max(0, min(255, round(x)))) for x in c)
    h = (c[0] << 16) | (c[1] << 8) | c[2]
    if h in SPECIAL and h not in KEEP:
        c = (c[0], c[1], c[2] + 1 if c[2] < 255 else c[2] - 1)
    return c


class Sh:
    """A paint colour, shaded per face."""
    __slots__ = ("c",)

    def __init__(self, c):
        self.c = c


def pxu(d=None):
    """Metres along the vehicle per screen pixel column in view d (side faces)."""
    d = d or VIEW_D
    fx, fy = FWD[d]
    per_m = abs(AX * (fx - fy))
    if per_m < 1e-6:          # nw/se: the length runs vertically on screen
        per_m = abs(AY * (fx + fy))
    return 1.0 / per_m


def frame(d):
    fx, fy = FWD[d]
    return np.array([fx, fy, 0.0]), np.array([-fy, fx, 0.0])


def face_factor(d, face, end_k=0.95):
    if face in ("+z", "-z"):
        return None
    f, r = frame(d)
    n = {"+u": f, "-u": -f, "+v": r, "-v": -r}[face]
    k = 1.0 - 0.14 * max(0.0, n[0]) ** 2
    if face in ("+u", "-u"):
        k *= end_k
    return k


class Box:
    def __init__(self, u0, u1, v0, v1, z0, z1, mat):
        self.lo = np.array([u0, v0, z0], float)
        self.hi = np.array([u1, v1, z1], float)
        self.mat = mat


def screen(P):
    X, Y, Z = P
    return (X * AX - Y * AX, (X + Y) * AY - Z * HZ)


def render(boxes, L, d, lines=(), size=128, center=(64.0, 64.0)):
    """Render the vehicle (length L, centred on the tile origin) for view d.
    lines: ((u,v,z), (u,v,z), rgb) polylines, depth tested."""
    global VIEW_D
    VIEW_D = d
    f, r = frame(d)
    up = np.array([0, 0, 1.0])
    dl = np.array([VIEW @ f, VIEW @ r, VIEW @ up])
    ys, xs = np.mgrid[0:size, 0:size].astype(float)
    sx = xs + 0.5 - center[0]; sy = ys + 0.5 - center[1]
    X = (sx / AX + sy / AY) / 2; Y = (sy / AY - sx / AX) / 2
    o = [X * f[0] + Y * f[1] + L / 2, X * r[0] + Y * r[1], np.zeros_like(X)]
    best_t = np.full((size, size), -1e18)
    best_i = np.full((size, size), -1, int)
    best_f = np.full((size, size), "", dtype=object)
    for bi, b in enumerate(boxes):
        t0 = np.full((size, size), -1e18); t1 = np.full((size, size), 1e18)
        face = np.full((size, size), "", dtype=object)
        ok = np.ones((size, size), bool)
        for k, nm in enumerate("uvz"):
            if abs(dl[k]) < 1e-12:
                ok &= (o[k] >= b.lo[k]) & (o[k] <= b.hi[k])
                continue
            ta = (b.lo[k] - o[k]) / dl[k]; tb = (b.hi[k] - o[k]) / dl[k]
            if dl[k] < 0:
                hi_t, lo_t, fn = ta, tb, "-" + nm
            else:
                hi_t, lo_t, fn = tb, ta, "+" + nm
            m = hi_t < t1
            t1 = np.where(m, hi_t, t1); face = np.where(m, fn, face)
            t0 = np.maximum(t0, lo_t)
        hit = ok & (t0 <= t1) & (t1 > best_t + 1e-9)
        best_t = np.where(hit, t1, best_t)
        best_i = np.where(hit, bi, best_i)
        best_f = np.where(hit, face, best_f)
    img = np.zeros((size, size, 3), np.uint8); img[:, :] = T
    for py, px in zip(*np.where(best_i >= 0)):
        b = boxes[best_i[py, px]]; t = best_t[py, px]; fc = best_f[py, px]
        q = (o[0][py, px] + t * dl[0], o[1][py, px] + t * dl[1], o[2][py, px] + t * dl[2])
        c = b.mat(fc, q[0], q[1], q[2])
        if c is None:
            continue
        if isinstance(c, Sh):
            k = face_factor(d, fc)
            c = c.c if k is None else tuple(x * k for x in c.c)
        img[py, px] = safe(c)
    # depth-tested polylines
    for ln in lines:
        p0, p1, col = ln[:3]
        a = np.array(p0, float); c1 = np.array(p1, float)
        W0 = (a[0] - L / 2) * f + a[1] * r + a[2] * up
        W1 = (c1[0] - L / 2) * f + c1[1] * r + c1[2] * up
        s0 = np.array(screen(W0)); s1 = np.array(screen(W1))
        n = int(max(2, 3 * np.abs(s1 - s0).max() + 1))
        for i in range(n + 1):
            W = W0 + (W1 - W0) * i / n
            sxy = screen(W)
            px = int(math.floor(sxy[0] + center[0])); py = int(math.floor(sxy[1] + center[1]))
            if 0 <= px < size and 0 <= py < size:
                tq = (W @ VIEW) / (VIEW @ VIEW)     # depth of the point along VIEW
                tb = best_t[py, px]
                if best_i[py, px] < 0 or tq >= _box_depth(tb, py, px, o, dl, f, r, L) - 1e-6:
                    img[py, px] = safe(col)
    return img


def _box_depth(t, py, px, o, dl, f, r, L):
    """World point of the box hit, projected onto VIEW (same measure as lines)."""
    q = np.array([o[0][py, px] + t * dl[0], o[1][py, px] + t * dl[1], o[2][py, px] + t * dl[2]])
    W = (q[0] - L / 2) * f + q[1] * r + q[2] * np.array([0, 0, 1.0])
    return (W @ VIEW) / (VIEW @ VIEW)
