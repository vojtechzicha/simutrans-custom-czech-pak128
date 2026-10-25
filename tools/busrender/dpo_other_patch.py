"""Patches on frozen DP Ostrava sheets (tools/busrender/src/dpo/): the Unvi
Urbis DD, the Skoda 21Tr and the Temsa-bodied Skoda 36Tr.

Every patch works on the frozen sheet with a box frame fitted to its
silhouette (dpo_otherkit.Frame, per-view origin offsets found by a silhouette
fit); the frame gives each side-face pixel its position u (metres behind the
front) and height z, and aims the trolley poles at the wires of dpmhk.py.
"""
import math

import numpy as np

from render import Box, render, DIRS, HEAD, P
import dpo_otherkit as K
from dpo_otherkit import Frame, T, rgb, is_bg

# ------------------------------------------------------------------ frames
# fitted with a silhouette search (L, W, z0, zt; origin offset per view on a
# half-pixel grid) against the frozen sheets; the residual is wheels, mirrors
# and roof boxes
F_URBIS = Frame(12.0, 2.7, 0.2, 4.25, {
    "w": (0.0, -1.5), "nw": (0.0, 2.0), "n": (0.0, -0.5), "ne": (-0.5, -2.5),
    "e": (0.0, -1.5), "se": (0.0, 3.0), "s": (0.0, -0.5), "sw": (0.5, -1.5)})
F_21TR = Frame(11.0, 2.5, 0.0, 3.0, {
    "w": (-1.0, -2.0), "nw": (-0.5, -3.0), "n": (2.0, -3.0), "ne": (1.5, -2.0),
    "e": (1.0, -1.0), "se": (0.5, 0.0), "s": (-2.0, 0.0), "sw": (-2.5, -2.0)})
F_36TR = Frame(12.0, 2.7, 0.25, 3.5, {
    "w": (0.0, 1.0), "nw": (0.0, 0.5), "n": (0.0, 0.0), "ne": (-0.5, -1.0),
    "e": (0.0, -1.0), "se": (0.0, 1.0), "s": (0.0, 0.0), "sw": (-0.5, -1.0)})

RIGHT_VIEWS = ("n", "ne", "e")          # views that show the right (door) side
LEFT_VIEWS = ("s", "sw", "w")
FRONT_VIEWS = ("e", "se", "s")
REAR_VIEWS = ("w", "nw", "n")


def vals(t):
    return (t[..., 0].astype(np.int64) << 16) | (t[..., 1].astype(np.int64) << 8) | t[..., 2]


def side_masks(frame, d, margin=0.0):
    """{side: (u, z, mask)} for the sides visible in view d; mask = pixel
    centre on that side of the fitted box"""
    out = {}
    for side in ("left", "right"):
        r = frame.face_uz(d, side)
        if r is None:
            continue
        u, z = r
        m = (u >= margin) & (u <= frame.L - margin) & (z >= frame.z0) & (z <= frame.zt)
        out[side] = (u, z, m)
    return out


def recolour(tile, mask, mapping):
    out = tile.copy()
    v = vals(tile)
    for src, dst in mapping.items():
        out[mask & (v == src)] = dst
    return out


# ------------------------------------------------------------------ poles
def repole(tile, d, frame, u_base, z_base, half, cols, keep=None):
    t, _ = K.erase_poles(tile, keep=keep)
    return K.draw_poles(t, d, frame, u_base, z_base, half, **cols)


POLES_36TR = dict(pole_col=(0x22, 0x24, 0x26), base_col=(0x10, 0x10, 0x12), tip_col=(0x10, 0x10, 0x12))
POLES_21TR = dict(pole_col=(0xD8, 0xA8, 0x28), base_col=(0x1C, 0x1C, 0x1E), tip_col=(0x1C, 0x1C, 0x1E),
                  dark_frac=0.22, dark_col=(0x1C, 0x1C, 0x1E))


# ------------------------------------------------------------------ 36Tr
GLAZ_36 = {0x57656F, 0x4D4D4D, 0x1E1E1E}
LINE_36 = (0xC4, 0xCA, 0xCF)


def patch_36tr(rows):
    """light grey line under the glazing on both sides in every view; black
    poles aimed at the wire"""
    out = []
    for i, d in enumerate(DIRS):
        t = rows[0][i]
        sm = side_masks(F_36TR, d, margin=0.15)
        v = vals(t)
        new = t.copy()
        for side, (u, z, m) in sm.items():
            for x in range(128):
                for y in range(127):
                    if v[y, x] in GLAZ_36 and v[y + 1, x] == 0x00ADD6 and (m[y + 1, x] or m[y, x]):
                        new[y + 1, x] = LINE_36
        new = repole(new, d, F_36TR, 5.4, F_36TR.zt + 0.10, 0.30, POLES_36TR)
        out.append(new)
    return [out]


# ------------------------------------------------------------------ Skoda 21Tr
# TommPa9 shades every face in its own steps: (white, blue, door orange) of the
# sides and of the ends, per view
T21_SIDE = {"ne": (0xF7F7F7, 0x2994FF, 0xEFBD52), "sw": (0xF7F7F7, 0x2994FF, 0xEFBD52),
            "e": (0xE6E6E6, 0x218CFF, 0xEFB542), "w": (0xE6E6E6, 0x218CFF, 0xEFB542),
            "n": (0xDEDEDE, 0x0884FF, 0xEFB531), "s": (0xDEDEDE, 0x0884FF, 0xEFB531)}
T21_END = {"e": (0xDEDEDE, 0x0884FF), "w": (0xDEDEDE, 0x0884FF),
           "n": (0xE6E6E6, 0x218CFF), "s": (0xE6E6E6, 0x218CFF),
           "se": (0xF7F7F7, 0x2994FF), "nw": (0xF7F7F7, 0x2994FF)}
T21_ROOF = {0xC5C5C5, 0xFFFFFF, 0x848484, 0xFFFF00, 0x000000}
T21_GLASS = {0x4D4D4D, 0x57656F}
T21_ROOFC = (0xC5, 0xC5, 0xC5)


def t21_sides(tile, d):
    """blue cant rail (the top row of the side), blue line under the windows,
    orange stripe over the blue skirt"""
    if d not in T21_SIDE:
        return tile
    white, blue, orange = T21_SIDE[d]
    out = tile.copy()
    v = vals(tile)
    (_, zz, _), = side_masks(F_21TR, d).values()       # one side shows in a side view
    for x in range(128):
        for y in range(1, 127):
            if v[y, x] != white:
                continue
            up, dn = v[y - 1, x], v[y + 1, x]
            if up in T21_ROOF or is_bg(tile[y - 1, x]):
                out[y, x] = rgb(blue)
            elif up in T21_GLASS or up == blue:
                out[y, x] = rgb(blue)
            if dn == blue and zz[y, x] < 1.5:
                out[y, x] = rgb(orange)
    return out


BOX_U = (4.75, 10.45)                   # the roof container over the rear half
BOX_H = 0.30
BOX_TOP = (0xE2, 0xE3, 0xE4)
BOX_RIM = (0xFF, 0xFF, 0xFF)
BOX_SIDE = (0x8C, 0x8E, 0x90)
BOX_END = (0x80, 0x80, 0x82)


def t21_box(tile, d):
    """the silver roof container over the rear half, at its real length (the
    drawing had it 4 m long): the old outline is painted out to the roof grey
    and a box is rendered on the fitted frame"""
    f = F_21TR
    out = tile.copy()
    v = vals(tile)
    u, t = f.top_ut(d)
    roof = (u > -0.3) & (u < f.L + 0.3) & (np.abs(t) < f.W / 2 + 0.25)
    old = np.isin(v, [0xFFFFFF, 0x848484]) & roof
    out[old] = T21_ROOFC
    hw = f.W / 2 - 0.18
    box = Box("box", f.L - BOX_U[1], f.L - BOX_U[0], -hw, hw, f.zt, f.zt + BOX_H)
    body = Box("body", 0, f.L, -f.W / 2, f.W / 2, f.z0, f.zt)

    def tex(p):
        if p.box == "body":
            return (1, 2, 3)
        if p.face == "top":
            if p.line(1, hw - 0.01) or p.line(1, -hw + 0.01) or p.line(0, f.L - BOX_U[0] - 0.01) \
                    or p.line(0, f.L - BOX_U[1] + 0.01):
                return BOX_RIM
            return BOX_TOP
        if p.face in ("front", "rear"):
            return BOX_END
        return BOX_SIDE
    img, _ = render(d, [body, box], tex, f.L, f.origin(d))
    m = ~is_bg(img) & ~np.all(img == (1, 2, 3), axis=2)
    out[m] = img[m]
    # the old outline row standing above the roof edge
    stray = np.isin(v, [0xFFFFFF, 0x848484]) & ~roof & ~m
    out[stray] = T
    return out


# ------------------------------------------------------------------ Unvi Urbis DD
# lower deck of the box render (rows of the ne view: glass 1.34-2.09 m, the
# top glass row in the lighter special, a light line 1.09-1.34 m)
U_GLASS_TOP = (1.84, 2.09)
U_GLASS = (1.34, 2.09)
U_LINE = (1.09, 1.34)
U_BODY = (0x00, 0xAD, 0xD6)
U_LIGHT = (0xC4, 0xCA, 0xCF)
U_POST = (0x1E, 0x1E, 0x1E)
U_WHITE = (0xF2, 0xF2, 0xF2)
U_REAR_AXLE = 9.0
# door 2 one metre further back than drawn (5.4-6.6 m): just ahead of the rear
# axle with one window between it and the wheel, as on 7991/7992
U_DOOR2 = (6.45, 7.55)
U_RIGHT = dict(span=(5.00, 11.75), posts=[5.45], glass=[(5.00, 6.25), (7.75, 8.95)],
               grille=(9.15, 11.62))
U_LEFT = dict(span=(8.45, 11.75), posts=[], glass=[], grille=(8.72, 11.62))
PX_PER_M = {"ne": 4.243, "sw": 4.243, "e": 3.0, "w": 3.0, "n": 3.0, "s": 3.0}


def urbis_lower(tile, d):
    """re-render the rear half of the lower deck: door 2 moved back, the
    windowless rear with the white grille graphic (both sides), the light
    line under the glazing"""
    f = F_URBIS
    side = "right" if d in RIGHT_VIEWS else ("left" if d in LEFT_VIEWS else None)
    if side is None:
        return tile
    spec = U_RIGHT if side == "right" else U_LEFT
    body = Box("body", 0, f.L, -f.W / 2, f.W / 2, f.z0, f.zt)
    ppm = PX_PER_M[d]

    def tex(p):
        if p.face != side:
            return None
        u, z = f.L - p.s, p.z
        a, b = spec["span"]
        if not (a <= u < b) or z >= U_GLASS[1]:
            return None
        if abs(u - U_REAR_AXLE) < 0.72 and z < 1.12:
            return None                                   # wheel and arch stay as drawn
        d0, d1 = U_DOOR2
        if side == "right" and (p.line(0, f.L - d0 - 0.02) or p.line(0, f.L - d1 + 0.02)):
            return U_LIGHT                                # door frame, drawn exactly once
        if side == "right" and d0 <= u < d1:
            if p.line(0, f.L - (d0 + d1) / 2):
                return U_POST
            if z < f.z0 + 0.14:
                return U_POST
            return K.GLASS
        if U_GLASS[0] <= z:
            g0, g1 = spec["grille"]
            if g0 <= u < g1:
                col = int(math.floor(u * ppm))
                row = int(math.floor((z - U_GLASS[0]) / 0.25))
                return U_WHITE if (col + row) % 2 == 0 else U_BODY
            for q0, q1 in spec["glass"]:
                if q0 <= u < q1:
                    if any(p.line(0, f.L - c) for c in spec["posts"]):
                        return U_POST
                    return K.GLASS2 if z >= U_GLASS_TOP[0] else K.GLASS
            return U_BODY
        if U_LINE[0] <= z:
            return U_LIGHT
        return U_BODY

    img, _ = render(d, [body], lambda p: tex(p) or (1, 2, 3), f.L, f.origin(d))
    m = ~is_bg(img) & ~np.all(img == (1, 2, 3), axis=2)
    out = tile.copy()
    out[m] = img[m]
    return out


def urbis_mirrors(tile, d):
    """the mirrors hang at lower-deck level. In the side views the far
    mirror, seen past the front, stood a deck higher on screen than the near
    one and read as an upper-deck mirror: only the near one is kept there"""
    from scipy import ndimage
    f = F_URBIS
    body, _ = render(d, [Box("body", 0, f.L, -f.W / 2, f.W / 2, f.z0, f.zt)], lambda p: (1, 2, 3),
                     f.L, f.origin(d))
    v = vals(tile)
    cand = (v == 0x141618) & is_bg(body)
    out = tile.copy()
    near = {"ne": 1, "sw": -1}.get(d)
    corners = {sg: f.xy(d, 0.0, sg * f.W / 2, 0.0) for sg in (-1, 1)}
    lab, n = ndimage.label(cand, structure=np.ones((3, 3)))
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        cx, cy = xs.mean() + 0.5, ys.mean() + 0.5
        sg = near if near else min(corners, key=lambda s: abs(corners[s][0] - cx))
        z = (corners[sg][1] - cy) / 4.0
        if z > 2.9:
            out[lab == k] = T
    return out


def urbis_roof(tile, d):
    """painted parts of the glass roof (frame, ribs, the caps) in the light
    DPO roof colour; the glass stays"""
    f = F_URBIS
    u, t = f.top_ut(d)
    top = (u > -0.05) & (u < f.L + 0.05) & (np.abs(t) < f.W / 2 + 0.05)
    return recolour(tile, top, {0x0096BA: K.ROOF, 0x009CC2: K.ROOF})


def patch_urbis(rows):
    out = []
    for i, d in enumerate(DIRS):
        t = rows[0][i]
        t = urbis_lower(t, d)
        t = urbis_mirrors(t, d)
        t = urbis_roof(t, d)
        out.append(t)
    return [out]


def patch_21tr(rows):
    out = []
    for i, d in enumerate(DIRS):
        t = rows[0][i]
        t, _ = K.erase_poles(t)
        t = t21_sides(t, d)
        t = t21_ends(t, d)
        t = t21_box(t, d)
        t = K.draw_poles(t, d, F_21TR, BOX_U[0] + 0.35, F_21TR.zt + BOX_H + 0.12, 0.30, **POLES_21TR)
        out.append(t)
    return [out]


def t21_ends(tile, d):
    """front: plain windscreen without the blue centre post, headlights moved up
    into the white band, orange stripe over the blue bumper; rear: orange stripe
    over the blue bumper"""
    if d not in T21_END:
        return tile
    white, blue = T21_END[d]
    out = tile.copy()
    v = vals(tile)
    front = d in FRONT_VIEWS
    r = F_21TR.face_tz(d, "front" if front else "rear")
    tt, zz = r
    glass = {}
    for x in range(128):
        ys = [y for y in range(128) if v[y, x] in T21_GLASS and abs(tt[y, x]) < F_21TR.W / 2 + 0.3
              and -0.5 < zz[y, x] < F_21TR.zt + 0.5]
        if ys:
            glass[x] = (min(ys), max(ys))
    if not glass:
        return out
    gx = sorted(glass)
    for x in range(gx[0], gx[-1] + 1):
        col = v[:, x]
        if x not in glass:
            # a window post between two panes: the panes of the nearer column,
            # moved by the slope of the face
            n = min(gx, key=lambda q: (abs(q - x), q))
            sl = int(round((x - n) * {"e": 0.5, "w": 0.5, "n": -0.5, "s": -0.5}.get(d, 0)))
            g0, g1 = glass[n][0] + sl, glass[n][1] + sl
        else:
            g0, g1 = glass[x]
        if front:
            for y in range(g0, g1 + 1):
                if col[y] in T21_GLASS or col[y] == blue:
                    out[y, x] = K.CAB
        # the white band under the window, down to the blue bumper
        k = g1 + 1
        band = []
        while k < 128 and col[k] not in (blue, 0xFFFF53) and not is_bg(tile[k, x]):
            band.append(k); k += 1
        if not band or k >= 128 or is_bg(tile[k, x]):
            continue
        corner = abs(tt[band[-1], x]) > F_21TR.W / 2 - 0.42
        for y in band[:-1]:
            if col[y] != 0xFF211D:
                out[y, x] = rgb(white)
        if front and corner and len(band) >= 2:
            out[band[-2], x] = K.HEADL
        if col[band[-1]] != 0xFF211D:
            out[band[-1], x] = rgb(T21_SIDE.get(d, (0, 0, 0xEFBD52))[2])
        y = k
        while front and y < 128 and v[y, x] in (blue, 0xFFFF53):
            if v[y, x] == 0xFFFF53:
                out[y, x] = rgb(blue)
            y += 1
    return out
