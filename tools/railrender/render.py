"""Vectorised orthographic box raycaster in the pak128 projection.

World: X = east (screen down-right), Y = south (screen down-left), Z = up.
Units: X, Y in carunits (1/16 tile) -> 4 px x, 2 px y (straight track);
Z in screen pixels.  Diagonal (staircase) track comes out at 5.66 px/unit
horizontally and 2.83 px/unit vertically, exactly like Simutrans.
Vehicle-local: u = distance BEHIND the front (0 = front end), v = lateral
(+v = the vehicle's right-hand side), z = height in px above the rail.
anchor = screen position (tile px, continuous) of the local point (0, 0, 0).
"""
import math
import numpy as np

T = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
S2 = 1 / math.sqrt(2)
FWD = {"w": (-1, 0), "e": (1, 0), "n": (0, -1), "s": (0, 1),
       "ne": (S2, -S2), "sw": (-S2, S2), "nw": (-S2, -S2), "se": (S2, S2)}
VIEW = np.array([1.0, 1.0, 4.0])   # screen(VIEW) == (0, 0); viewer at +VIEW


def screen(X, Y, Z):
    return ((X - Y) * 4.0, (X + Y) * 2.0 - Z)


def frame(d):
    fx, fy = FWD[d]
    f = np.array([fx, fy, 0.0])
    r = np.array([-fy, fx, 0.0])
    return f, r


def back_vec(d):
    """screen px per unit of u (moving backwards along the vehicle)."""
    f, _ = frame(d)
    return screen(-f[0], -f[1], 0.0)


def local_to_screen(d, anchor, u, v, z):
    f, r = frame(d)
    W = -u * f + v * r
    sx, sy = screen(W[0], W[1], z)
    return sx + anchor[0], sy + anchor[1]


def face_normal_world(d, face):
    f, r = frame(d)
    ax, sg = face[1], (1 if face[0] == "+" else -1)
    if ax == "u":
        return -f * sg
    if ax == "v":
        return r * sg
    return np.array([0, 0, sg], float)


class Box:
    def __init__(self, u0, u1, v0, v1, z0, z1, mat, owner):
        self.lo = np.array([u0, v0, z0], float)
        self.hi = np.array([u1, v1, z1], float)
        self.mat = mat          # mat(face, u, v, z, d) -> RGB
        self.owner = owner


def render(boxes, d, anchor, size=128, lines=()):
    """Returns img (size,size,3) and owner map (size,size) of object str."""
    f, r = frame(d)
    dl = np.array([-(VIEW @ f), VIEW @ r, VIEW[2]])
    ys, xs = np.mgrid[0:size, 0:size]
    sx = xs + 0.5 - anchor[0]; sy = ys + 0.5 - anchor[1]
    X = (sx / 4.0 + sy / 2.0) / 2; Y = (sy / 2.0 - sx / 4.0) / 2
    o = [-(X * f[0] + Y * f[1]), X * r[0] + Y * r[1], np.zeros_like(X)]
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
            if dl[k] < 0:      # ta > tb everywhere
                hi_t, lo_t, fn = ta, tb, "-" + nm
            else:
                hi_t, lo_t, fn = tb, ta, "+" + nm
            m = hi_t < t1
            t1 = np.where(m, hi_t, t1); face = np.where(m, fn, face)
            t0 = np.maximum(t0, lo_t)
        hit = ok & (t0 <= t1) & (t1 > best_t)
        best_t = np.where(hit, t1, best_t)
        best_i = np.where(hit, bi, best_i)
        best_f = np.where(hit, face, best_f)
    img = np.zeros((size, size, 3), np.uint8); img[:, :] = T
    owner = np.full((size, size), "", dtype=object)
    for py, px in zip(*np.where(best_i >= 0)):
        b = boxes[best_i[py, px]]; t = best_t[py, px]
        q = (o[0][py, px] + t * dl[0], o[1][py, px] + t * dl[1], o[2][py, px] + t * dl[2])
        img[py, px] = b.mat(best_f[py, px], q[0], q[1], q[2], d)
        owner[py, px] = b.owner
    for ln in lines:
        p0, p1, col, own = ln[:4]
        thick = ln[4] if len(ln) > 4 else False
        a = np.array(p0, float); c = np.array(p1, float)
        sa = local_to_screen(d, anchor, *a); sc = local_to_screen(d, anchor, *c)
        ddx, ddy = abs(sc[0] - sa[0]), abs(sc[1] - sa[1])
        n = int(max(2, 3 * max(ddx, ddy) + 1))
        for i in range(n + 1):
            q = a + (c - a) * i / n
            qx, qy = local_to_screen(d, anchor, *q)
            px = int(math.floor(qx)); py = int(math.floor(qy))
            pts = [(px, py)]
            if thick:
                pts.append((px + 1, py) if ddy >= ddx else (px, py + 1))
            for (x, y) in pts:
                if 0 <= x < size and 0 <= y < size:
                    img[y, x] = col
                    owner[y, x] = own
    return img, owner
