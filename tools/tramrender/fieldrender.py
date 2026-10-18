"""Implicit-surface raymarcher in the pak128 projection, for rounded vehicle bodies.

The box raycasters (tools/railrender/render.py, tools/busrender/rj_vrender.py)
only know axis-aligned boxes, so a rounded tram nose or roof shoulder comes out
as a stack of bricks. Here a solid is a scalar field (negative inside), so noses
rounded in plan, raked windscreens and curved roof shoulders are one expression
each, and the shading follows the true surface normal.

Projection and model coordinates are those of tools/railrender/render.py:
world X = east (screen down-right), Y = south (screen down-left), both in
carunits (4 px x, 2 px y on straight track); Z = up in screen px.
Model: u = carunits BEHIND the consist front, v = lateral carunits (+v = the
vehicle's right-hand side), z = height in px above the rail head.

Every pixel centre casts one orthographic ray (no anti-aliasing, so edges and
livery bands stay crisp pixel art). The ray is marched down from above the
model in fixed steps and refined by bisection; normals come from central
differences with z scaled by ZS px per carunit, so a radius means the same in
every direction.

Shading is that of the natives (tools/railrender/railkit.py face_factor):
south-facing sides full colour, south-east ~0.87, east ~0.72; faces turned up
blend into the paint's top colour; faces turned down darken. With flat=True
every side keeps its full colour in every view and the side-to-top blend is
cut into `top_steps` steps, which is how TommPa9 paints his trams (the DPO
Tango NF2 and Vario LF2 use one blue for every side and one for the roof).
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "railrender"))
from railkit import SPECIAL, KEEP  # noqa: E402

T = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
S2 = 1 / math.sqrt(2)
FWD = {"w": (-1, 0), "e": (1, 0), "n": (0, -1), "s": (0, 1),
       "ne": (S2, -S2), "sw": (-S2, S2), "nw": (-S2, -S2), "se": (S2, S2)}
ZS = 6.0          # model px per carunit vertically (4 px/m at 1.5 m per carunit)


def frame(d):
    fx, fy = FWD[d]
    return np.array([fx, fy]), np.array([-fy, fx])


def back_vec(d):
    """Screen px per carunit of u (moving backwards along the vehicle)."""
    f, _ = frame(d)
    return (-f[0] + f[1]) * 4.0, (-f[0] - f[1]) * 2.0


def to_screen(d, anchor, u, v, z):
    f, r = frame(d)
    X = -u * f[0] + v * r[0]
    Y = -u * f[1] + v * r[1]
    return (X - Y) * 4.0 + anchor[0], (X + Y) * 2.0 - z + anchor[1]


# ------------------------------------------------------------------ colours
def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def safe_arr(a):
    """Round to uint8 and nudge accidental special colours one blue step."""
    a = np.clip(np.round(a), 0, 255).astype(np.int64)
    hx = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    bad = np.isin(hx, [s for s in SPECIAL if s not in KEEP])
    a[..., 2] = np.where(bad, np.where(a[..., 2] < 255, a[..., 2] + 1, 254), a[..., 2])
    return a.astype(np.uint8)


class Paint:
    """A shaded colour. `top` is the colour of faces turned up (default base)."""
    def __init__(self, base, top=None):
        self.base = np.array(rgb(base) if isinstance(base, int) else base, float)
        t = base if top is None else top
        self.top = np.array(rgb(t) if isinstance(t, int) else t, float)


class Lit:
    """A colour drawn exactly as given (glass and lamp specials)."""
    def __init__(self, c):
        self.c = np.array(rgb(c) if isinstance(c, int) else c, float)


# ------------------------------------------------------------------ field helpers
def smax(a, b, k):
    """Smooth maximum (intersection with a fillet of size ~k)."""
    if k <= 0:
        return np.maximum(a, b)
    h = np.clip(0.5 - 0.5 * (b - a) / k, 0.0, 1.0)
    return a * h + b * (1 - h) + k * h * (1 - h)


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def round_rect(x, y, hx, hy, r):
    """2D rounded rectangle centred at 0 (half sizes hx, hy, corner radius r)."""
    qx = np.abs(x) - hx + r
    qy = np.abs(y) - hy + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


class Solid:
    """field(u, v, zs) -> array (< 0 inside; zs = z / ZS); zone(P) -> zone ids."""
    def __init__(self, field, zone, owner):
        self.field = field
        self.zone = zone
        self.owner = owner


# ------------------------------------------------------------------ render
def render(solids, lines, d, anchor, livery, size=128, zmax=48.0, step=0.04, flat=False, top_steps=2):
    """Render all solids in view d with consist-u 0 at `anchor` (screen px).

    lines: (p0, p1, colour, owner[, thick]) with p = (u, v, z), drawn 1 px wide
    and depth-tested against the solids.
    Returns (img uint8 [size, size, 3], owner array of str)."""
    f, r = frame(d)
    ys, xs = np.mgrid[0:size, 0:size]
    sx = xs + 0.5 - anchor[0]
    sy = ys + 0.5 - anchor[1]
    X0 = (sx / 4.0 + sy / 2.0) / 2.0
    Y0 = (sy / 2.0 - sx / 4.0) / 2.0
    u0 = -(X0 * f[0] + Y0 * f[1])
    v0 = X0 * r[0] + Y0 * r[1]
    du = -(f[0] + f[1])          # per unit t (X and Y both grow by t)
    dv = r[0] + r[1]

    def at(t):
        return u0 + t * du, v0 + t * dv, 4.0 * t

    def field_all(u, v, z):
        zs = z / ZS
        return np.min([s.field(u, v, zs) for s in solids], axis=0)

    # march from above (z = zmax) down to just below the rail
    t_hi = zmax / 4.0
    t_lo = -1.0 / 4.0
    dt = step / 4.0
    hit_t = np.full((size, size), -1e9)
    found = np.zeros((size, size), bool)
    prev_t = np.full((size, size), t_hi)
    t = t_hi
    while t > t_lo:
        t_next = t - dt
        live = ~found
        if not live.any():
            break
        u, v, z = at(t_next)
        val = field_all(u[live], v[live], np.full(live.sum(), z))
        inside = val < 0
        idx = np.where(live)
        hy, hx = idx[0][inside], idx[1][inside]
        if len(hy):
            # bisection between t (outside) and t_next (inside)
            a = np.full(len(hy), t)
            b = np.full(len(hy), t_next)
            for _ in range(10):
                m = 0.5 * (a + b)
                uu = u0[hy, hx] + m * du
                vv = v0[hy, hx] + m * dv
                fv = field_all(uu, vv, 4.0 * m)
                a = np.where(fv < 0, a, m)
                b = np.where(fv < 0, m, b)
            hit_t[hy, hx] = b
            found[hy, hx] = True
        t = t_next

    img = np.zeros((size, size, 3), np.uint8)
    img[:, :] = T
    owner = np.full((size, size), "", dtype=object)
    hy, hx = np.where(found)
    if len(hy):
        tt = hit_t[hy, hx]
        U = u0[hy, hx] + tt * du
        V = v0[hy, hx] + tt * dv
        Z = 4.0 * tt
        ZSc = Z / ZS
        vals = np.array([s.field(U, V, ZSc) for s in solids])
        which = np.argmin(vals, axis=0)
        cols = np.zeros((len(hy), 3))
        own = np.empty(len(hy), dtype=object)
        e = 0.01
        for si, s in enumerate(solids):
            m = which == si
            if not m.any():
                continue
            uu, vv, zz = U[m], V[m], ZSc[m]
            gu = s.field(uu + e, vv, zz) - s.field(uu - e, vv, zz)
            gv = s.field(uu, vv + e, zz) - s.field(uu, vv - e, zz)
            gz = s.field(uu, vv, zz + e) - s.field(uu, vv, zz - e)
            gn = np.sqrt(gu * gu + gv * gv + gz * gz) + 1e-12
            nu, nv, nz = gu / gn, gv / gn, gz / gn
            P = dict(u=uu, v=vv, z=zz * ZS, nu=nu, nv=nv, nz=nz, d=d)
            zones = s.zone(P)
            cols[m] = shade(livery, zones, P, d, flat, top_steps)
            own[m] = s.owner
        img[hy, hx] = safe_arr(cols)
        owner[hy, hx] = own

    for ln in lines:
        p0, p1, col, own = ln[:4]
        thick = ln[4] if len(ln) > 4 else False
        col = np.array(rgb(col) if isinstance(col, int) else col, np.uint8)
        a = np.array(p0, float)
        c = np.array(p1, float)
        sa = to_screen(d, anchor, *a)
        sc = to_screen(d, anchor, *c)
        ddx, ddy = abs(sc[0] - sa[0]), abs(sc[1] - sa[1])
        n = int(max(2, 3 * max(ddx, ddy) + 1))
        for i in range(n + 1):
            q = a + (c - a) * i / n
            qx, qy = to_screen(d, anchor, *q)
            px, py = int(math.floor(qx)), int(math.floor(qy))
            pts = [(px, py)]
            if thick:
                pts.append((px + 1, py) if ddy >= ddx else (px, py + 1))
            for (x, y) in pts:
                if 0 <= x < size and 0 <= y < size:
                    # visible unless a solid is nearer the viewer (larger t)
                    if found[y, x] and hit_t[y, x] > q[2] / 4.0 + 0.05:
                        continue
                    img[y, x] = col
                    owner[y, x] = own
    return img, owner


def shade(livery, zones, P, d, flat=False, top_steps=2):
    """Colour per hit from zone ids (array) and normals, native-style lighting."""
    f, r = frame(d)
    nu, nv, nz = P["nu"], P["nv"], P["nz"]
    # world horizontal normal
    nx = -nu * f[0] + nv * r[0]
    ny = -nu * f[1] + nv * r[1]
    h = np.hypot(nx, ny) + 1e-12
    hx, hy = nx / h, ny / h
    k_side = np.maximum(0.5, 1.0 - 0.28 * np.maximum(0.0, hx) ** 2 - 0.10 * np.maximum(0.0, -hy))
    # up-facing -> top colour; down-facing -> darker
    w_top = np.clip((nz - 0.42) / (0.88 - 0.42), 0.0, 1.0)
    if flat:
        k_side = np.ones_like(k_side)
        w_top = np.round(w_top * top_steps) / top_steps
    k_down = np.where(nz < -0.2, 0.72, 1.0)
    out = np.zeros((len(nz), 3))
    for zid in np.unique(zones):
        m = zones == zid
        p = livery[zid]
        if isinstance(p, Lit):
            out[m] = p.c
            continue
        if not isinstance(p, Paint):
            p = Paint(p)
        side = p.base[None, :] * (k_side[m] * k_down[m])[:, None]
        out[m] = side * (1 - w_top[m])[:, None] + p.top[None, :] * w_top[m][:, None]
    return out


def vehicle_tile(solids, lines, d, u_front, keep, anchor, livery, zmax=48.0, step=0.04, flat=False, top_steps=2):
    """Render the vehicle whose front is at consist-u `u_front` on the front
    anchor: only the solids and lines owned by `keep`, each section complete,
    like the native trams. (Cutting a section where its neighbour hides it in a
    straight consist would leave a notch in curves, where the neighbour turns
    away; the engine's draw order covers the hidden end of a complete section.)"""
    solids = [s for s in solids if s.owner in keep]
    lines = [ln for ln in lines if ln[3] in keep]
    bx, by = back_vec(d)
    a = (anchor[0] - u_front * bx, anchor[1] - u_front * by)
    img, owner = render(solids, lines, d, a, livery, zmax=zmax, step=step, flat=flat, top_steps=top_steps)
    mask = np.isin(owner, list(keep))
    out = img.copy()
    out[~mask] = T
    return out
