"""DP Ostrava sheets derived from existing art (CANDIDATES, under review).

    python tools/busrender/dpo_derived.py [family ...] [--variant A|B] [--preview DIR]

Families (folder names):
  solarisurbino12_s4_electric   vehicle-bus/dpo/: Solaris Urbino 12 IV electric
      (DPO 5008-5031, 2022). TommPa9's DPO Urbino 12 IV sheet with the long
      roof battery fairing added. Variant A: the plain fairing. Variant B: the
      fairing with the black front part of its sides (the glazing band of the
      DPO e-bus scheme sweeps up into it over the front door), the white "ooo"
      e-mark near the rear and the OppCharge contact rails on the front roof.
  sor_tnb_12                    vehicle-trolleybus/dpo/: SOR TNB 12 prototype
      (DPO 3912, 2009/2011). VTPsim's SOR NB 12 body (the white Praha sheet)
      moved onto the footprint of the DPO 26Tr sheet, given the white roof
      container of the traction equipment with the poles of the 26Tr sheet
      (pixel for pixel, so they stay on the wire), the front roof A/C unit of
      the bus removed. Variant A: the whole roof blue (seznam-autobusu: "bílá s
      modrou střechou"). Variant B: only the cant rail and the front cap blue,
      the roof white (what the side photos show from the ground).

Shapes added to the hand-drawn sheets are boxes rendered with render.py in a
frame fitted per view to the sprite silhouette (fit()), so they sit on the
roof of the drawing in every view. The source sheets are read at run time;
regenerate after changing them. Without --variant each family's chosen
variant (VARIANT) is written to its sprites/ folder; --preview writes every
variant and the reference sheets to DIR instead and leaves sprites/ alone.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import dpmhk as H                                                       # noqa: E402
from render import render, Box, DIRS                                    # noqa: E402
import rj_lane                                                          # noqa: E402
from rj_buscommon import SPECIAL                                        # noqa: E402

T = (231, 255, 255)
MARK = (1, 2, 3)                      # body pixels of a render (occluder only)

URBINO_SRC = "vehicle-bus/dpo/solarisurbino12_s4/sprites/dpotyrkysova.png"
TR26_SRC = "vehicle-trolleybus/dpo/26trsolaris/sprites/dpotyrkysova.png"
NB12_SRC = "vehicle-bus/praha/sor_nb_12/sprites/bila.png"

# the chosen variant per family (what goes into sprites/)
VARIANT = {"solarisurbino12_s4_electric": "B", "sor_tnb_12": "A"}
OUT = {"solarisurbino12_s4_electric": "vehicle-bus/dpo/solarisurbino12_s4_electric/sprites/dpotyrkysova.png",
       "sor_tnb_12": "vehicle-trolleybus/dpo/sor_tnb_12/sprites/bilamodrastrecha.png"}


# ------------------------------------------------------------------ helpers
def load_tiles(rel, row=0):
    im = np.array(Image.open(os.path.join(REPO, *rel.split("/"))).convert("RGB"))
    return [im[row * 128:(row + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)]


def is_bg(t):
    return np.all(t == T, axis=2)


def safe(c):
    c = tuple(int(max(0, min(255, round(v)))) for v in c)
    h = (c[0] << 16) | (c[1] << 8) | c[2]
    if h in SPECIAL:
        c = (c[0], c[1], c[2] + 1 if c[2] < 255 else c[2] - 1)
    return c


def shift(tile, dx, dy):
    out = np.zeros_like(tile); out[:, :] = T
    ys, xs = np.where(~is_bg(tile))
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
    assert ok.all(), "shift pushes pixels out of the tile"
    out[ny, nx] = tile[ys, xs]
    return out


class Fit:
    """a box (length L, roof height zr, half width hw) fitted to one view of a
    sprite, with the whole-pixel offset (dx, dy) of the drawing"""

    def __init__(self, d, L, zr, hw, dx, dy, iou):
        self.d, self.L, self.zr, self.hw, self.dx, self.dy, self.iou = d, L, zr, hw, dx, dy, iou

    def origin(self):
        o = H.origin_for(self.d)
        return np.array((o[0] + self.dx, o[1] + self.dy), float)

    def draw(self, extra, tex):
        """render extra boxes on the fitted body; returns (image, mask of the
        extra pixels); the body only hides what lies behind it"""
        boxes = [Box("body", 0, self.L, -self.hw, self.hw, 0.30, self.zr)] + list(extra)

        def tx(p):
            return MARK if p.box == "body" else tex(p)
        img, _ = render(self.d, boxes, tx, self.L, self.origin())
        m = ~is_bg(img) & ~np.all(img == MARK, axis=2)
        return img, m

    def faces(self):
        """per pixel the face name of the bare body box ('' = none) and s / L"""
        face = np.full((128, 128), "", dtype=object)
        frac = np.zeros((128, 128))
        zz = np.zeros((128, 128))
        ids = {"top": 1, "front": 2, "rear": 3, "right": 4, "left": 5}
        names = {v: k for k, v in ids.items()}

        def tx(p):
            return (ids[p.face], int(max(0, min(255, p.s / self.L * 250))), int(max(0, min(255, p.z * 50))))
        img, _ = render(self.d, [Box("body", 0, self.L, -self.hw, self.hw, 0.30, self.zr)], tx,
                        self.L, self.origin())
        bg = is_bg(img)
        for y, x in zip(*np.where(~bg)):
            face[y, x] = names[int(img[y, x, 0])]
            frac[y, x] = img[y, x, 1] / 250.0
            zz[y, x] = img[y, x, 2] / 50.0
        return face, frac, zz


_FITS = {}
LS = (11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0)
ZRS = (3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4)
HWS = (1.1, 1.3, 1.5, 1.7)


def fit(tile, d, Ls=LS, zrs=ZRS, hws=HWS, rng=14):
    """best box by silhouette IoU. The hand-drawn sheets are not in true
    proportion in every view (TommPa9's nw/se views are drawn long and tall),
    so length and height are fitted per view, over wide ranges."""
    key = (tile.tobytes(), d)
    if key not in _FITS:
        _FITS[key] = _fit(tile, d, Ls, zrs, hws, rng)
    return _FITS[key]


def _fit(tile, d, Ls, zrs, hws, rng):
    m = ~is_bg(tile)
    ys, xs = np.where(m)
    y0, y1, x0, x1 = max(0, ys.min() - 4), min(128, ys.max() + 5), max(0, xs.min() - 4), min(128, xs.max() + 5)
    mc = m[y0:y1, x0:x1]
    best = None
    for L in Ls:
        for zr in zrs:
            for hw in hws:
                img, _ = render(d, [Box("b", 0, L, -hw, hw, 0.30, zr)], lambda p: (0, 0, 0), L,
                                np.array(H.origin_for(d), float))
                b = ~is_bg(img)
                for dx in range(-rng, rng + 1):
                    for dy in range(-rng, rng + 1):
                        bb = np.roll(np.roll(b, dy, 0), dx, 1)[y0:y1, x0:x1]
                        iou = (bb & mc).sum() / max(1, (bb | mc).sum())
                        if best is None or iou > best[-1]:
                            best = (L, zr, hw, dx, dy, iou)
    return Fit(d, *best)


def paste(tile, img, mask):
    out = tile.copy()
    out[mask] = img[mask]
    return out


# ------------------------------------------------- Urbino 12 IV electric
U_BODY = (0x00, 0xAD, 0xD6)            # TommPa9's DPO turquoise (sides, roof rim)
U_ROOF = (0x00, 0x7B, 0x94)            # roof
U_END = (0x00, 0x96, 0xBA)             # fairing ends, a step darker than the sides
U_TOP = (0x00, 0x8E, 0xAB)             # fairing top, between roof and sides
U_STEP = (0x00, 0x5E, 0x72)            # dark step line at the foot of the fairing
U_BLACK = (0x00, 0x00, 0x00)
U_WHITE = (0xE6, 0xE6, 0xE6)
U_RAIL = (0x84, 0x84, 0x84)
U_RAIL_HI = (0xC5, 0xC5, 0xC5)

FAIR_H = 0.45                          # 0.45 m = 1.8 px
FAIR_IN = 0.25                         # inset from the body sides


def urbino_tile(tile, d, variant):
    f = fit(tile, d)
    L, zr, hw = f.L, f.zr, f.hw
    s0, s1 = 1.0, L - 0.6               # rear end ~1 m ahead of the tail, front at the dome
    z1 = zr + FAIR_H
    boxes = [Box("fair", s0, s1, -hw + FAIR_IN, hw - FAIR_IN, zr, z1)]
    if variant == "B":
        # OppCharge contact rails: four longitudinal bars above the front axle
        for t in (-0.55, -0.2, 0.2, 0.55):
            boxes.append(Box("rail", L - 3.4, L - 2.2, t - 0.07, t + 0.07, z1, z1 + 0.22))

    def tex(p):
        if p.box == "rail":
            return U_RAIL_HI if p.face == "top" else U_RAIL
        if p.face == "top":
            return U_TOP
        if p.face in ("front", "rear"):
            return U_END
        # side walls
        if p.z < zr + 0.12:
            return U_STEP
        if variant == "B":
            if p.s > L - 3.6 + (p.z - zr) * 1.5:        # black front part, slanting back
                return U_BLACK
            for sm in (1.9, 2.5, 3.1):                   # "ooo" e-mark
                if p.line(0, sm) and p.z > zr + 0.15:
                    return U_WHITE
        return U_BODY
    img, m = f.draw(boxes, tex)
    return paste(tile, img, m), f


def build_urbino(variant):
    tiles = load_tiles(URBINO_SRC)
    out, fits = [], []
    for d, t in zip(DIRS, tiles):
        o, f = urbino_tile(t, d, variant)
        out.append(o); fits.append(f)
    return [out], fits


# ---------------------------------------------------------- SOR TNB 12
TNB_BLUE = (0x28, 0x8C, 0xD2)          # DPO light blue of 3912's roof / cant rail
NB_WHITE = (0xFF, 0xFF, 0xFF)
BOX_W = {"top": (0xF6, 0xF6, 0xF6), "right": (0xEC, 0xEC, 0xEA), "left": (0xEC, 0xEC, 0xEA),
         "front": (0xDE, 0xDE, 0xDC), "rear": (0xDE, 0xDE, 0xDC)}
BOX_STEP = (0xBC, 0xBC, 0xBA)
LOUVRE = (0x9A, 0x9A, 0x98)
LOUVRE_LO = (0x6E, 0x6E, 0x6C)


# about 3.8 m towards the rear, in whole steps along the lane direction of each
# view (w/e/n/s 2:1, ne/sw horizontal, nw/se vertical)
POLE_BACK = {"w": (12, 6), "nw": (0, 8), "n": (-12, 6), "ne": (-16, 0),
             "e": (-12, -6), "se": (0, -8), "s": (12, -6), "sw": (16, 0)}


def footprint_shift(src, ref, d):
    """whole-pixel shift that puts src's body (X, C) on ref's"""
    X, C = rj_lane.metrics(src, d)
    Xr, Cr = rj_lane.metrics(ref, d)
    if d in ("nw", "se"):
        return int(round(Xr - X)), int(round(Cr - C))
    dx = int(round(Xr - X))
    k = rj_lane.SLOPE[d]
    dy = int(round(Cr - (C - k * dx)))
    return dx, dy


def pole_pixels(tr26, urb):
    """the 26Tr poles: where the 26Tr sheet differs from the bare Urbino IV it
    was drawn on, and is not background; single retouched pixels elsewhere on
    the body are dropped (only connected groups of 4+ pixels are poles)"""
    from scipy import ndimage
    m = np.any(tr26 != urb, axis=2) & ~is_bg(tr26)
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    return np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 4])


def lum(c):
    return (int(c[0]) + int(c[1]) + int(c[2])) / 3.0


def tnb_tile(nb, tr26, urb, d, variant):
    dx, dy = footprint_shift(nb, tr26, d)
    t = shift(nb, dx, dy)
    f = fit(t, d)
    L, zr, hw = f.L, f.zr, f.hw
    face, frac, zz = f.faces()
    out = t.copy()

    # 1. remove the bus's front roof A/C unit: whatever stands above the roof
    #    over the front 2.6 m, outside the fitted body
    bodyless = ~is_bg(t) & (face == "")
    _, ac = f.draw([Box("ac", L - 2.6, L - 0.2, -hw, hw, zr - 0.05, zr + 0.9)], lambda p: (9, 9, 9))
    out[bodyless & ac] = T
    # ... and its grey on the roof itself becomes roof white
    top = face == "top"
    for y, x in zip(*np.where(top & (frac > 1 - 2.6 / L))):
        c = out[y, x]
        if max(c) - min(c) < 12 and lum(c) > 0xB0:
            out[y, x] = NB_WHITE

    # 2. livery: blue on white pixels of the roof / cant rail / front cap
    def blue(c):
        k = lum(c) / 255.0
        return safe(tuple(v * min(1.0, k / 0.97) for v in TNB_BLUE))
    side = (face == "right") | (face == "left")
    cant = side & (zz > zr - 0.28)
    cap = (face == "front") & (zz > zr - 0.32)
    paint = cant | cap | (top if variant == "A" else np.zeros_like(top))
    if variant == "B":
        # B: the roof white, only its outer edge blue (1 px rim on the top face)
        rim = top & ~(np.roll(top, 1, 0) & np.roll(top, -1, 0) & np.roll(top, 1, 1) & np.roll(top, -1, 1))
        paint |= rim
    for y, x in zip(*np.where(paint & ~is_bg(out))):
        c = out[y, x]
        if max(c) - min(c) < 14 and lum(c) > 0xB0:
            out[y, x] = blue(c)

    # 3. the roof container of the traction equipment (rounded white cover)
    #    with the lower louvred resistor box ahead of it
    s0, s1 = L * 0.22, L * 0.62
    zt = zr + 0.5
    boxes = [Box("cont", s0, s1, -hw + 0.18, hw - 0.18, zr, zt - 0.15),
             Box("cont", s0 + 0.35, s1 - 0.35, -hw + 0.32, hw - 0.32, zt - 0.15, zt),
             Box("louv", s1, s1 + 1.1, -hw + 0.45, hw - 0.45, zr, zr + 0.3)]

    def tex(p):
        if p.box == "louv":
            if p.face == "top":
                return LOUVRE
            return LOUVRE_LO
        if p.face != "top" and p.z < zr + 0.1:
            return BOX_STEP
        return BOX_W[p.face]
    img, m = f.draw(boxes, tex)
    out = paste(out, img, m)

    # 4. the 26Tr poles, pixel for pixel, moved back along the lane (so the
    #    heads stay on the wire) from the 26Tr's mounting to the rear end of
    #    the TNB's roof container
    pm = pole_pixels(tr26, urb)
    poles = np.zeros_like(tr26); poles[:] = T
    poles[pm] = tr26[pm]
    poles = shift(poles, *POLE_BACK[d])
    pm = ~is_bg(poles)
    out[pm] = poles[pm]
    return out, f, (dx, dy)


def build_tnb(variant):
    nb = load_tiles(NB12_SRC)
    tr = load_tiles(TR26_SRC)
    ur = load_tiles(URBINO_SRC)
    out, fits, shifts = [], [], []
    for i, d in enumerate(DIRS):
        o, f, s = tnb_tile(nb[i], tr[i], ur[i], d, variant)
        out.append(o); fits.append(f); shifts.append(s)
    return [out], fits, shifts


# ------------------------------------------------------------------ output
def sheet(rows):
    a = np.zeros((128 * len(rows), 1024, 3), np.uint8); a[:] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    return a


def check_specials(a, label):
    flat = a.reshape(-1, 3).astype(np.int64)
    vals = set(np.unique((flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]).tolist())
    bad = (vals & SPECIAL) - {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}
    if bad:
        print(f"WARNING {label}: special colours {[hex(b) for b in sorted(bad)]}")


GRASS = (92, 132, 60)


def on_grass(a):
    g = a.copy()
    g[is_bg(a)] = GRASS
    return g


def preview(sheets, path, scale):
    """stack labelled sheets (name, array of one row) on grass at scale"""
    rows = [on_grass(a[:128]) for _, a in sheets]
    s = np.concatenate(rows, axis=0)
    im = Image.fromarray(s).resize((s.shape[1] * scale, s.shape[0] * scale), Image.NEAREST)
    im.save(path)


def build(fam, variant):
    if fam == "solarisurbino12_s4_electric":
        rows, fits = build_urbino(variant)
        info = [f"{f.d}: L={f.L} zr={f.zr} hw={f.hw} off=({f.dx},{f.dy}) iou={f.iou:.2f}" for f in fits]
    else:
        rows, fits, shifts = build_tnb(variant)
        info = [f"{f.d}: body shift {s} L={f.L} zr={f.zr} hw={f.hw} off=({f.dx},{f.dy}) iou={f.iou:.2f}"
                for f, s in zip(fits, shifts)]
    a = sheet(rows)
    check_specials(a, f"{fam} {variant}")
    return a, info


REF = {"solarisurbino12_s4_electric": [("Urbino 12 IV (diesel, DPO)", URBINO_SRC)],
       "sor_tnb_12": [("SOR NB 12 white (Praha)", NB12_SRC), ("26Tr (DPO)", TR26_SRC)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("families", nargs="*")
    ap.add_argument("--variant")
    ap.add_argument("--preview")
    a = ap.parse_args()
    fams = a.families or list(OUT)
    for fam in fams:
        if a.preview:
            os.makedirs(a.preview, exist_ok=True)
            items = [(n, np.array(Image.open(os.path.join(REPO, p)).convert("RGB"))) for n, p in REF[fam]]
            for v in ("A", "B"):
                arr, info = build(fam, v)
                print(f"{fam} variant {v}:\n  " + "\n  ".join(info))
                Image.fromarray(arr).save(os.path.join(a.preview, f"{fam}_{v}.png"))
                items.append((v, arr))
            for sc in (1, 3):
                preview(items, os.path.join(a.preview, f"{fam}_compare_{sc}x.png"), sc)
            continue
        v = a.variant or VARIANT[fam]
        arr, info = build(fam, v)
        print(f"{fam} variant {v}:\n  " + "\n  ".join(info))
        path = os.path.join(REPO, *OUT[fam].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(arr).save(path)
        print("wrote", OUT[fam])


if __name__ == "__main__":
    main()
