"""Shared helpers for the DP Ostrava buses and trolleybuses outside the Solaris
family (dpo_other.py): palette, lane placement, fitted body frames, pole
redrawing, special-colour checks and previews.

Nothing here changes the behaviour of the modules it imports from
(render.py, dpmhk.py, dpo_lane.py, tools/tramrender/dpo_palette.py).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "tramrender"))

from render import P, HEAD, DIRS, project                  # noqa: E402
from dpmhk import ORIGINS, pole_tips, bresenham            # noqa: E402
import dpo_lane                                            # noqa: E402
import dpo_palette as DP                                   # noqa: E402

T = (231, 255, 255)
TA = np.array(T)
SRC = os.path.join(HERE, "src", "dpo")


def rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def hexv(c):
    return (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])


# ------------------------------------------------------------------ palette
# DPO turquoise (owner's decision 2026-10-18 / 2026-10-20): flat body colour on
# every side, the light sunlit roof 44C1E4 on every top surface.
BODY = rgb(DP.BODY)
ROOF = rgb(DP.ROOF)
WLINE = rgb(DP.WHITE)
MASK = rgb(DP.MASK)
CAB = rgb(DP.CAB_GLASS)            # plain windscreen / driver's window glass
CAB_TOP = rgb(DP.CAB_GLASS_TOP)
GLASS = (0x4D, 0x4D, 0x4D)         # special: passenger glass, lit at night when loaded
GLASS2 = (0x57, 0x65, 0x6F)        # special: lighter passenger glass
HEADL = (0xFF, 0xFF, 0x53)         # special: always lit
TAILL = (0xFF, 0x21, 0x1D)         # special: always lit
LIT = {hexv(GLASS), hexv(GLASS2)}

SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
ALLOWED = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


# ------------------------------------------------------------------ sheets
def load(path):
    a = np.array(Image.open(path).convert("RGB"))
    return [[a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)]
            for r in range(a.shape[0] // 128)]


def sheet(rows):
    out = np.zeros((128 * len(rows), 1024, 3), dtype=np.uint8)
    out[:, :] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    return out


def specials(arr):
    flat = arr.reshape(-1, 3).astype(np.int64)
    used = set(np.unique((flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]).tolist())
    return used & SPECIAL


def save(rows, path):
    out = sheet(rows)
    bad = specials(out) - ALLOWED
    if bad:
        raise SystemExit(f"{path}: unintended special colours {sorted(hex(b) for b in bad)}")
    Image.fromarray(out).save(path)
    return out


def is_bg(t):
    return np.all(t == TA, axis=-1)


# ------------------------------------------------------------------ lane
def lane(rows, lead=0):
    """move every view along the road the way dpo_lane.py does (front where a
    native 12 m bus has its front), so the committed sheet is a fixed point of
    dpo_lane.py; returns the shifted rows and the (dx, dy) per view"""
    a = sheet(rows)
    L = dpo_lane.drawn_length(a, lead)
    shifts = []
    out = [list(r) for r in rows]
    for i, d in enumerate(DIRS):
        dx, dy = dpo_lane.view_shift(rows[lead][i], d, L)
        shifts.append((dx, dy))
        if (dx, dy) != (0, 0):
            for r in range(len(rows)):
                out[r][i] = dpo_lane.shift_tile(rows[r][i], dx, dy)
    return out, shifts


# ------------------------------------------------------------------ frames
class Frame:
    """a box body fitted to a sheet (fitbox: silhouette fit per view): length L,
    width W, body bottom z0 and roof zt; origin = dpmhk lane origin + offset"""

    def __init__(self, L, W, z0, zt, off):
        self.L, self.W, self.z0, self.zt, self.off = L, W, z0, zt, dict(off)

    def origin(self, d, extra=(0, 0)):
        o = ORIGINS[d]
        dx, dy = self.off[d]
        return np.array((o[0] + dx + extra[0], o[1] + dy + extra[1]), float)

    def xy(self, d, u, t, z, extra=(0, 0)):
        """screen position of the point u metres behind the front, t to the right"""
        return project(d, self.L, self.origin(d, extra), self.L - u, t, z)

    def face_uz(self, d, side, extra=(0, 0)):
        """(u, z) of every pixel centre on the plane of the left / right side
        (u metres behind the front); NaN where the side faces away"""
        hx, hy = HEAD[d]
        h3 = np.array([hx, hy, 0.0]); r3 = np.array([-hy, hx, 0.0])
        sg = 1 if side == "right" else -1
        if sg * (r3 @ np.array([1.0, 1.0, 0.0])) <= 1e-9:
            return None
        ph, pz = P(h3), P(np.array([0, 0, 1.0]))
        base = self.origin(d, extra) + P(sg * self.W / 2 * r3) - self.L / 2 * ph
        M = np.linalg.inv(np.array([ph, pz]).T)
        ys, xs = np.mgrid[0:128, 0:128] + 0.5
        dx, dy = xs - base[0], ys - base[1]
        s = M[0, 0] * dx + M[0, 1] * dy
        z = M[1, 0] * dx + M[1, 1] * dy
        return self.L - s, z

    def face_tz(self, d, end, extra=(0, 0)):
        """(t, z) of every pixel centre on the plane of the front / rear end
        (t > 0 = the vehicle's right); None where that end faces away"""
        hx, hy = HEAD[d]
        h3 = np.array([hx, hy, 0.0]); r3 = np.array([-hy, hx, 0.0])
        sg = 1 if end == "front" else -1
        if sg * (h3 @ np.array([1.0, 1.0, 0.0])) <= 1e-9:
            return None
        pr, pz = P(r3), P(np.array([0, 0, 1.0]))
        base = self.origin(d, extra) + sg * self.L / 2 * P(h3)
        M = np.linalg.inv(np.array([pr, pz]).T)
        ys, xs = np.mgrid[0:128, 0:128] + 0.5
        dx, dy = xs - base[0], ys - base[1]
        return M[0, 0] * dx + M[0, 1] * dy, M[1, 0] * dx + M[1, 1] * dy

    def top_ut(self, d, z=None, extra=(0, 0)):
        """(u, t) of every pixel centre on the roof plane z (default zt)"""
        z = self.zt if z is None else z
        hx, hy = HEAD[d]
        h3 = np.array([hx, hy, 0.0]); r3 = np.array([-hy, hx, 0.0])
        ph, pr = P(h3), P(r3)
        base = self.origin(d, extra) + P(np.array([0, 0, z])) - self.L / 2 * ph
        M = np.linalg.inv(np.array([ph, pr]).T)
        ys, xs = np.mgrid[0:128, 0:128] + 0.5
        dx, dy = xs - base[0], ys - base[1]
        s = M[0, 0] * dx + M[0, 1] * dy
        return self.L - s, M[1, 0] * dx + M[1, 1] * dy


# ------------------------------------------------------------------ poles
POLE_COLS = {0xFFFF00, 0x000000}


def erase_poles(tile, cols=POLE_COLS, keep=None):
    """remove the old trolley poles: the connected runs of pole colours that
    contain yellow; pixels over the body take the colour of their row
    neighbours, the rest become transparent. Returns (tile, removed mask)."""
    v = (tile[..., 0].astype(np.int64) << 16) | (tile[..., 1].astype(np.int64) << 8) | tile[..., 2]
    pc = np.isin(v, list(cols))
    lab, n = ndimage.label(pc, structure=np.ones((3, 3)))
    pole = np.zeros_like(pc)
    for k in range(1, n + 1):
        m = lab == k
        if (v[m] == 0xFFFF00).any():
            pole |= m
    if keep is not None:
        pole &= ~keep
    out = tile.copy()
    out[pole] = T
    # the body: the drawing without its thin protrusions (poles in the air,
    # mirrors); poles lying over the roof stay inside it
    body = ndimage.binary_opening(~is_bg(tile), structure=np.ones((3, 3)))
    for y, x in zip(*np.where(pole)):
        if not body[y, x]:
            continue
        best = None
        for dist in (1, 2, 3):
            cand = [tuple(out[y, xx]) for xx in (x - dist, x + dist)
                    if 0 <= xx < 128 and not pole[y, xx] and not is_bg(out[y, xx])]
            if cand:
                best = max(set(cand), key=cand.count)
                break
        if best is None:
            cand = [tuple(out[yy, x]) for yy in (y - 1, y + 1) if 0 <= yy < 128 and not pole[yy, x]
                    and not is_bg(out[yy, x])]
            best = cand[0] if cand else None
        if best is not None:
            out[y, x] = best
    # loose bits of the old poles left in the air (pole heads in other colours)
    lab, n = ndimage.label(~is_bg(out), structure=np.ones((3, 3)))
    if n > 1:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        main = 1 + int(np.argmax(sizes))
        loose = (lab != main) & (lab > 0)
        out[loose] = T
        pole |= loose
    return out, pole


def draw_poles(tile, d, frame, u_base, z_base, half, pole_col, base_col, tip_col, dark_frac=0.0,
               dark_col=None, extra=(0, 0)):
    """two trolley poles from (u_base, +-half, z_base) aimed at the wires of
    dpmhk.WIRES (6.3 m poles, like dpmhk.py); the lower dark_frac of each pole in
    dark_col (spring base), the tip pixel in tip_col"""
    o = frame.origin(d, extra)
    res = pole_tips(d, frame.L, o, frame.L - u_base, z_base, half)
    out = tile.copy()
    for base, tip in res:
        if tip is None:
            raise SystemExit(f"no wire for a pole in view {d}")
        bx, by = int(math.floor(base[0])), int(math.floor(base[1]))
        pts = bresenham(bx, by, tip[2], tip[3])
        n = len(pts)
        for k, (x, y) in enumerate(pts):
            if 0 <= x < 128 and 0 <= y < 128:
                c = pole_col
                if dark_col is not None and k < dark_frac * n:
                    c = dark_col
                out[y, x] = c
        if 0 <= by < 128 and 0 <= bx < 128:
            out[by, bx] = base_col
        out[tip[3], tip[2]] = tip_col
    return out


# ------------------------------------------------------------------ previews
GRASS = (86, 112, 70)


def strip(rows_list, labels, z):
    """rows of 8 views (each a list of tiles) as one image on grass, cropped
    per column to the union of all rows, scaled z times, with labels"""
    crops = []
    for c in range(8):
        xs, ys = [], []
        for rows in rows_list:
            m = ~is_bg(rows[c])
            yy, xx = np.where(m)
            if len(xx):
                xs += [xx.min(), xx.max()]; ys += [yy.min(), yy.max()]
        crops.append((max(min(xs) - 2, 0), min(max(xs) + 3, 128), max(min(ys) - 2, 0), min(max(ys) + 3, 128)))
    lab_w = 120 if z > 1 else 90
    cw = [(c[1] - c[0]) * z + 4 for c in crops]
    rh = max(c[3] - c[2] for c in crops) * z + 6
    img = Image.new("RGB", (sum(cw) + lab_w, rh * len(rows_list) + 2), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for i, (rows, lab) in enumerate(zip(rows_list, labels)):
        x = lab_w
        dr.text((3, i * rh + 3), lab, fill=(0, 0, 0))
        for c in range(8):
            x0, x1, y0, y1 = crops[c]
            t = rows[c][y0:y1, x0:x1].copy()
            t[is_bg(t)] = GRASS
            img.paste(Image.fromarray(t).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST), (x, i * rh + 3))
            x += cw[c]
    return img


def preview(path, rows_list, labels):
    """1x and 3x strips stacked"""
    a = strip(rows_list, labels, 1)
    b = strip(rows_list, labels, 3)
    out = Image.new("RGB", (max(a.width, b.width), a.height + b.height + 8), (255, 255, 255))
    out.paste(a, (0, 0)); out.paste(b, (0, a.height + 8))
    out.save(path)
