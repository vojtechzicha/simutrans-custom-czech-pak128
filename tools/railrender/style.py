"""Render style for rendered locomotives, agreed with the user on 2026-09-26.

The box renders lost against the hand-drawn pak128.cs art (TommPa9, Lubak91): a
ČD 362 "Eso" read as a rounded "Laminatka". Four rounds of variants, picked
visually by the user, gave the rules below. tools/railrender/src/style_ref_362.png
is the approved result (ČD 362 in Najbrt 2); compare new renders against it.

Model rules (in the generator, not here):
- Shape before paint. Take the class's signature shape from photos: a boxy
  class (Eso, Peršing, Bastard) gets a slab box with sharp corners, a vertical
  front and a flat roof with a hard edge. Chamfered corners, a stepped roof and
  a leaning front read as a rounded body (Laminatka) and are only for those.
- Where roof meets body, draw a dark gutter (GUTTER), never a light rim: a light
  rim reads as a rounded roof.
- Livery zones in the proportions of the photos (Najbrt 2: the white stripe is
  one row, the sky blue fills the rest). Measure, do not guess.
- Horizontal ribbing (every other plain body row x RIB) where the real body is
  ribbed; the dark louvre band where the real loco has it; heavy roof equipment.
- No 1-px side lettering: it reads as noise. Keep only marks that read as a shape.
- Roof ROOF / ROOF_TOP. Pantographs: arms PANTO_ARM, 1 px; head bar PANTO_HEAD,
  2 px thick.

Post-process: apply polish(img, **POLISH) to every rendered sheet (outline,
face edges, more saturated colours). Special colours are left bit-exact.
"""
import colorsys
import numpy as np
from PIL import Image

from railkit import SPECIAL  # noqa: E402  (special colours stay bit-exact)

T = np.array([231, 255, 255])


def _hex(a):
    return (a[..., 0].astype(int) << 16) | (a[..., 1].astype(int) << 8) | a[..., 2].astype(int)


def _lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def polish(img, outline=0.0, edges=0.0, edge_step=28, punch=0.0, ground=0.0, ground_rows=2):
    a = np.array(img.convert("RGB")).astype(float)
    solid = ~np.all(a == T, axis=2)
    special = np.isin(_hex(a.astype(int)), list(SPECIAL))
    free = solid & ~special
    out = a.copy()
    if punch:
        flat = out[free] / 255.0
        res = []
        for r, g, b in flat:
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            s = min(1.0, s * (1 + punch))
            l = l - punch * 0.25 * (l - l * l) * 2      # deepen mids, keep extremes
            res.append(colorsys.hls_to_rgb(h, max(0, min(1, l)), s))
        out[free] = np.array(res) * 255.0
    L = _lum(out)
    fac = np.ones(L.shape)
    if edges:
        for dy, dx in ((-1, 0), (0, -1), (1, 0), (0, 1)):
            nb = np.roll(np.roll(L, dy, 0), dx, 1)
            nb_solid = np.roll(np.roll(solid, dy, 0), dx, 1)
            step = (nb - L) > edge_step          # this pixel is the darker side
            fac = np.where(free & nb_solid & step, np.minimum(fac, 1 - edges), fac)
    if outline:
        edge = np.zeros(solid.shape, bool)
        for dy, dx in ((-1, 0), (0, -1), (1, 0), (0, 1)):
            edge |= ~np.roll(np.roll(solid, dy, 0), dx, 1)
        fac = np.where(free & edge, np.minimum(fac, 1 - outline), fac)
    if ground:
        # lowest `ground_rows` solid pixels of every column in every tile
        below = np.zeros(solid.shape, int)
        cnt = np.zeros(solid.shape[1], int)
        for y in range(solid.shape[0] - 1, -1, -1):
            cnt = np.where(solid[y], cnt + 1, 0)
            below[y] = cnt
        fac = np.where(free & (below >= 1) & (below <= ground_rows), np.minimum(fac, 1 - ground), fac)
    out = out * fac[..., None]
    out = np.clip(np.round(out), 0, 255).astype(np.uint8)
    # keep specials and transparency bit-exact; nudge accidental specials off the table
    out[~free] = a[~free].astype(np.uint8)
    hx = _hex(out.astype(int))
    acc = free & np.isin(hx, list(SPECIAL))
    out[acc, 2] = np.where(out[acc, 2] < 255, out[acc, 2] + 1, 254)
    return Image.fromarray(out)


GUTTER = (0x34, 0x38, 0x3C)
ROOF = (96, 100, 106)
ROOF_TOP = (104, 108, 114)
PANTO_ARM = (190, 194, 198)
PANTO_HEAD = (0x3A, 0x3D, 0x40)
RIB = 0.9
POLISH = dict(outline=0.32, edges=0.22, punch=0.35)
