"""Small helpers for editing existing pak128 tram sheets in place.

Two jobs, both on 1024 x (rows * 128) sheets with the (231, 255, 255) background:

* `roof_box`: put an extruded box (air-conditioning unit, equipment container)
  on a sprite's roof. The roof is found by its colour; a position along the car
  is a fraction of the roof's extent along the direction of travel in that view
  (0 = front end), the width a fraction of the roof's local width. The box is
  the roof footprint raised by `h` px: the visible sides keep the side colour,
  the top gets the top colour. Pantograph pixels are never painted over.
* `patch`: overlay small ASCII-art pixel patches (one character per pixel, a
  legend maps characters to colours, '.' = leave as is, ' ' = background).
* `preview`: full 128 px tiles at 1x and 3x (nearest) on a grass background,
  several sheets above one another for comparison.

Screen pixels per carunit of travel per view are those of tools/consist_preview.py.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "railrender"))
from railkit import safe  # noqa: E402  (special-colour guard shared with the rail renderers)

BG = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
S2 = 2 ** 0.5
PER_CU = {"w": (-4, -2), "e": (4, 2), "n": (4, -2), "s": (-4, 2),
          "ne": (4 * S2, 0), "sw": (-4 * S2, 0), "nw": (0, -2 * S2), "se": (0, 2 * S2)}


def hexrgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def load(path):
    return np.array(Image.open(path).convert("RGB"))


def save(arr, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    Image.fromarray(arr.astype(np.uint8)).save(path)


def tile(sheet, row, col):
    """View (not copy) of one 128 x 128 cell."""
    return sheet[row * 128:(row + 1) * 128, col * 128:(col + 1) * 128]


def is_panto(px):
    """Pantograph pixels: the yellow arms of the DPO sheets and the black pan head."""
    r, g, b = int(px[0]), int(px[1]), int(px[2])
    yellow = r > 150 and g > 150 and b < 40 and abs(r - g) < 40
    return yellow or (r, g, b) == (0, 0, 0)


def roof_box(t, d, roof_cols, f0, f1, width, h, top, side, edge=None, protect=is_panto):
    """Raise a box of height h px on the roof of tile t (view d), in place.

    roof_cols: list of RGB tuples that make up the roof's top face.
    f0..f1: fractions of the roof length from the front end.
    width: fraction of the local roof width the box covers (centred).
    edge: optional colour for the lowest visible side row (a dark gutter line).
    """
    roof = np.zeros(t.shape[:2], bool)
    for c in roof_cols:
        roof |= np.all(t == np.array(c), axis=2)
    ys, xs = np.nonzero(roof)
    if len(xs) == 0:
        return
    du = np.array(PER_CU[d], float); du /= np.linalg.norm(du)
    dv = np.array(PER_CU[DIRS[(DIRS.index(d) + 2) % 8]], float); dv /= np.linalg.norm(dv)
    s = xs * du[0] + ys * du[1]
    a = xs * dv[0] + ys * dv[1]
    smax, smin = s.max(), s.min()
    f = (smax - s) / max(1e-6, smax - smin)
    sel = (f >= f0) & (f <= f1)
    if not sel.any():
        return
    # local centre and half width per 1-px slice along the car
    keep = np.zeros_like(sel)
    sl = np.round(s).astype(int)
    for k in np.unique(sl[sel]):
        m = sel & (sl == k)
        lo, hi = a[m].min(), a[m].max()
        c, hw = (lo + hi) / 2, (hi - lo) / 2 + 0.5
        keep |= m & (np.abs(a - c) <= hw * width + 1e-6)
    fy, fx = ys[keep], xs[keep]
    top, side = safe(top), safe(side)
    edge = safe(edge) if edge is not None else side
    out = t.copy()
    # sides: the footprint swept upwards
    for k in range(0, h):
        for y, x in zip(fy - k, fx):
            if 0 <= y < 128 and not protect(t[y, x]):
                out[y, x] = edge if k == 0 else side
    # top face
    for y, x in zip(fy - h, fx):
        if 0 <= y < 128 and not protect(t[y, x]):
            out[y, x] = top
    t[:] = out


def patch(t, art, legend, x0, y0):
    """Overlay ASCII art onto tile t at (x0, y0); '.' keeps, ' ' clears to BG."""
    for j, line in enumerate(art.strip("\n").split("\n")):
        for i, ch in enumerate(line):
            if ch == ".":
                continue
            y, x = y0 + j, x0 + i
            if not (0 <= y < 128 and 0 <= x < 128):
                continue
            t[y, x] = BG if ch == " " else safe(legend[ch]) if legend[ch] not in KEEP_RAW else legend[ch]


KEEP_RAW = {(0x4D, 0x4D, 0x4D), (0x57, 0x65, 0x6F), (0xFF, 0xFF, 0x53), (0xFF, 0x21, 0x1D)}


def _grass(w, h, seed=1):
    rng = np.random.default_rng(seed)
    base = np.array([78, 136, 56], float)
    n = rng.random((h, w, 1))
    g = base + (n - 0.5) * np.array([24, 22, 10])
    return np.clip(g, 0, 255).astype(np.uint8)


def _on_grass(cell, seed):
    g = _grass(cell.shape[1], cell.shape[0], seed)
    m = np.all(cell == np.array(BG), axis=2)
    out = cell.copy()
    out[m] = g[m]
    return out


def preview(entries, out, rows=None, label_h=14):
    """entries: list of (label, sheet array). Each sheet row -> one strip at 1x
    (all 8 views) and one strip at 3x. rows: list of rows to show (default all)."""
    strips = []
    for label, sh in entries:
        rr = rows if rows is not None else range(sh.shape[0] // 128)
        for r in rr:
            row = np.concatenate([_on_grass(tile(sh, r, c), r * 8 + c) for c in range(8)], axis=1)
            one = Image.fromarray(row)
            three = one.resize((one.width * 3, one.height * 3), Image.NEAREST)
            strips.append((f"{label}  row {r}", one, three))
    W = max(s[2].width for s in strips)
    H = sum(label_h + s[1].height + s[2].height + 6 for s in strips)
    img = Image.new("RGB", (W, H), (250, 250, 250))
    dr = ImageDraw.Draw(img)
    y = 0
    for lab, one, three in strips:
        dr.text((4, y + 1), lab + "   (1x above, 3x below; views w nw n ne e se s sw)", fill=(0, 0, 0))
        y += label_h
        img.paste(one, (0, y)); y += one.height
        img.paste(three, (0, y)); y += three.height + 6
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out)
    return out
