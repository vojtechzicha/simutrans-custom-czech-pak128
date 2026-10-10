#!/usr/bin/env python3
"""ČD Brejlovec (754, 750.7, 750): TommPa9's pak128.cs drawing with the 754's
own details redrawn, in every livery.

    python tools/railpaint/cd_brejlovec.py [754|750_7|750 ...] [--preview DIR]

The user chose variant B2 of the 2026-10-10 review: TommPa9's hand-drawn T 478
silhouette and shading (all eleven of his Brejlovec liveries share it, frozen in
src/tommpa9_brejlovec/, lifted 4 px to source coordinates), but not his coach-
like window dashes. handpaint.HandBase aligns the eleven sheets to get exact
face rows: side wall K 0-1 the shoulder under the roof, K 2-8 the wall, K 9 the
frame; end face K 0 the cab roof edge, K 1-4 the goggle frame round the two
windscreens, K 5-7 the nose, K 8+ lamps and buffer beam.

Redrawn on every livery (from the photos of 754 045, 754 062 and the 754 at
České Velenice): the two louvre panels behind cab 1, six portholes high on the
hood, a small louvre before cab 2, the radiator grille on the roof near cab 2,
raised one pixel above the roof line, and the goggle frame wrapping round the
cab corners. The 750.7 rebuild gets one wide windscreen in the frame.

Liveries (colours from cd_loco_livery.py; layouts by rule or from his own sheet
in that livery, every colour of it mapped to a zone):

  najbrt2       rules: light roof rim, sky, white stripe at lamp level, sapphire
                below it, white goggle frames, sapphire-grey roof.
  najbrt1_2     his CD_754_Brejlovec_(balkan): light grey cab ends and fronts,
                sky and sapphire trapezoids along the hood, dark grey shoulders,
                frame and lower front, blue goggle frames, grey roof.
  najbrt1       the same layout on a white body and roof, sapphire frame (754.068).
  cervenozluta  his CD_753: red body and roof, the broad yellow band at nose
                level, white goggle frames, dark grey lamp zone (754.044).
  modrokremova  rules: light blue, cream band, dark blue roof and frame (754.013).
  zelenosediva  his CD_750: dark green over a light grey band (750).
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, "src", "tommpa9_brejlovec")
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "railrender"))
from handpaint import (FACT, HandBase, T, even_slots, hexarr, load, lum, save, shade,  # noqa: E402
                       template_zones, unspecial)
import cd_loco_livery as CL  # noqa: E402

REFS = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".png"))
BASE = "CD_754_Brejlovec_(balkan)"

SKY, WHITE, SAPPHIRE, LGREY = CL.LOCO_SKY, CL.WHITE, CL.SAPPHIRE, CL.LGREY
RIM = (206, 214, 220)              # light strip along the top of the side (Najbrt 2)
ROOF_N2 = (62, 74, 98)             # sapphire-grey roof
ROOF_GREY = (98, 102, 106)
FRAME_DK = (40, 42, 46)
DGREY = (58, 61, 64)               # Najbrt 1.2 shoulders, frame, lower front
GRILLE = (34, 38, 46)              # roof radiator grille
GRILLE_HI = (70, 78, 92)
PORTHOLE = (24, 28, 34)
ZG_GREEN = (0, 78, 78)             # ČSD / ČD 750 dark teal green (his sheet)
ZG_GREY = (165, 167, 168)
BC_SKY = (54, 136, 206)            # 754.013 blue-cream: light blue body

GLASS = {0x6B6B6B}
LAMPS = {0xFFFF53, 0xFF0000, 0xFF7B00, 0xFF211D, 0xFFFF00, 0xC1B1D1}

# his colours, every view's shade of one paint, per template sheet
N12_MAP = {**{h: "sky" for h in (0x0063C5, 0x1073E6, 0x004A9C)},
           **{h: "navy" for h in (0x001942, 0x102152, 0x001031, 0x001029)},
           **{h: "cab" for h in (0xB5BDC5, 0xD6DEE6, 0x8C949C, 0xC5CED6, 0x9CA5AD, 0x7B848C)},
           **{h: "dgrey" for h in (0x313131, 0x3A3A3A, 0x292929, 0x424242)},
           **{h: "louvre" for h in (0x0052B5,)}}
CMAP = {
    "CD_754_Brejlovec_(balkan)": N12_MAP,
    "CD_753_Brejlovec": {**{h: "red_hi" for h in (0xB50000, 0x840000, 0xBD0000)},
                         **{h: "red" for h in (0x8C0000, 0xA50000, 0x730000, 0x940000)},
                         **{h: "yellow" for h in (0xFFDE10, 0xFFE631, 0xF7D600, 0xFFDE08, 0xFFE621, 0xEFCE00)},
                         **{h: "frame" for h in (0x525252, 0x636363, 0x4A4A4A)},
                         **{h: "white" for h in (0xE6E6E6, 0xD6D6D6, 0xEFEFEF)}},
    "CD_750_Brejlovec": {**{h: "green" for h in (0x003131, 0x002929, 0x003A3A, 0x004242, 0x004A4A)},
                         **{h: "grey" for h in (0x9C9C9C, 0xADADAD, 0xA5A5A5, 0x949494, 0xB5B5B5)},
                         **{h: "frame" for h in (0x3A3A3A, 0x4A4A4A, 0x313131)},
                         **{h: "white" for h in (0xF7F7F7, 0xEFEFEF, 0xFFFFFF)}},
}


class Livery:
    def __init__(self, zones, roof, frame, template=None, rules=None):
        self.zones, self.roof, self.frame = zones, roof, frame
        self.template, self.rules = template, rules


def n2_rules(face, k):
    if face == "S":
        return "rim" if k == 0 else "sky" if k <= 5 else "white" if k == 6 else "sapphire" if k <= 8 else "frame"
    return ("roof" if k == 0 else "white" if k <= 4 else "sky" if k <= 6 else "white" if k == 7 else "sapphire")


def bc_rules(face, k):
    if face == "S":
        return "sky" if k <= 4 else "cream" if k <= 7 else "blue"
    return ("roof" if k == 0 else "cream" if k <= 4 else "sky" if k <= 6 else "cream" if k == 7 else "blue")


def livery(name):
    if name == "najbrt2":
        return Livery({"rim": RIM, "sky": SKY, "white": WHITE, "sapphire": SAPPHIRE, "frame": FRAME_DK,
                       "roof": ROOF_N2}, ROOF_N2, WHITE, rules=n2_rules)
    if name == "najbrt1_2":
        return Livery({"sky": SKY, "navy": SAPPHIRE, "cab": LGREY, "dgrey": DGREY, "louvre": SKY},
                      ROOF_GREY, SKY, template=BASE)
    if name == "najbrt1":
        return Livery({"sky": SKY, "navy": SAPPHIRE, "cab": CL.N1_WHITE, "dgrey": CL.N1_WHITE,
                       "dgrey_low": SAPPHIRE, "louvre": SKY}, (212, 216, 218), SKY, template=BASE)
    if name == "cervenozluta":
        return Livery({"red_hi": shade(CL.RY_RED, 1.15), "red": CL.RY_RED, "yellow": CL.RY_YELLOW,
                       "frame": DGREY, "white": WHITE}, CL.RY_RED, WHITE, template="CD_753_Brejlovec")
    if name == "modrokremova":
        return Livery({"sky": BC_SKY, "cream": CL.BC_CREAM, "blue": CL.BC_BLUE, "roof": CL.BC_BLUE},
                      CL.BC_BLUE, CL.BC_CREAM, rules=bc_rules)
    if name == "zelenosediva":
        return Livery({"green": ZG_GREEN, "grey": ZG_GREY, "frame": DGREY, "white": WHITE},
                      ZG_GREEN, WHITE, template="CD_750_Brejlovec")
    raise ValueError(name)


JOBS = {
    "754": ["najbrt2", "najbrt1_2", "najbrt1", "cervenozluta", "modrokremova"],
    "750_7": ["najbrt2", "najbrt1_2"],
    "750": ["zelenosediva", "najbrt1_2"],
}

_hb = None


def base():
    global _hb
    if _hb is None:
        names = [BASE] + [n for n in REFS if n != BASE]
        _hb = HandBase([load(os.path.join(SRC, n + ".png")) for n in names], 0,
                       {3: 81, 7: 81}, {1: 81, 5: 88}, 10, 10, side_prof_x=range(50, 70), end_width=7)
    return _hb


def paint(fam, name):
    hb = base()
    L = livery(name)
    v = hexarr(hb.base)
    out = hb.base.copy()
    painted = np.zeros(hb.solid.shape, bool)
    zones = None
    if L.template:
        zones = template_zones(hb, load(os.path.join(SRC, L.template + ".png")), CMAP[L.template])
        if name == "najbrt1":
            # Najbrt 1: the grey shoulders become the white roof, the frame and
            # the lower front sapphire
            low = (zones == "dgrey") & (((hb.face == "S") & (hb.K >= 8)) | ((hb.face == "E") & (hb.K >= 8)))
            zones[low] = "dgrey_low"

    def zc(y, x):
        """the livery colour of a face pixel (albedo) or None."""
        if L.rules:
            return L.zones[L.rules(hb.face[y, x], hb.K[y, x])]
        z = zones[y, x]
        return L.zones.get(z) if z else None

    def put(y, x, c, face=None, flat=False):
        out[y, x] = c if flat else shade(c, hb.factor(y, x, face))
        painted[y, x] = True

    # ---------------------------------------------------------------- body
    for y, x in zip(*np.where(hb.solid)):
        f, hv = hb.face[y, x], v[y, x]
        if hv in GLASS or (hv in LAMPS and f != "S"):
            continue
        if f in ("S", "E"):
            c = zc(y, x)
            if c is not None:
                put(y, x, c)
        elif f == "R":
            # the roof keeps his light / dark structure in the livery's colour;
            # his black fan slots become plain roof (the grille replaces them)
            Lm = lum(hb.base[y, x])
            if Lm < 40:
                Lm = 66.0
            put(y, x, tuple(int(max(0, min(255, t * (0.75 + 0.25 * Lm / 66.0)))) for t in L.roof), flat=True)
    # ------------------------------------------------------------- details
    for c in (0, 2, 3, 4, 6, 7):
        cu = hb.column_u(c)
        cols = sorted(cu)
        X0 = c * 128
        # two louvre panels behind cab 1: horizontal slats in a darker frame
        lv = [x for x in cols if 0.13 <= cu[x] <= 0.31]
        if lv:
            mid = lv[len(lv) // 2]
            for x in lv:
                for y in np.where((hb.face[:, X0 + x] == "S") & (hb.K[:, X0 + x] >= 1) & (hb.K[:, X0 + x] <= 5))[0]:
                    zcol = zc(y, X0 + x)
                    if zcol is None:
                        continue
                    k = hb.K[y, X0 + x]
                    f = 0.78 if (x in (lv[0], lv[-1]) or x == mid) else (0.70 if k % 2 else 0.95)
                    put(y, X0 + x, tuple(int(t * f) for t in zcol))
        # six portholes high on the hood
        ph = [x for x in cols if 0.36 <= cu[x] <= 0.74]
        for x in even_slots(ph, 6):
            for y in np.where((hb.face[:, X0 + x] == "S") & np.isin(hb.K[:, X0 + x], (2, 3)))[0]:
                put(y, X0 + x, PORTHOLE, flat=True)
        # small louvre before cab 2
        for x in [x for x in cols if 0.80 <= cu[x] <= 0.85]:
            for y in np.where((hb.face[:, X0 + x] == "S") & np.isin(hb.K[:, X0 + x], (3, 4, 5)))[0]:
                zcol = zc(y, X0 + x)
                if zcol is not None:
                    put(y, X0 + x, tuple(int(t * 0.72) for t in zcol))
        # radiator grille on the roof near cab 2
        wide = c in (3, 7)
        for x in [x for x in cols if 0.58 <= cu[x] <= 0.86]:
            for y in np.where((hb.face[:, X0 + x] == "R") & (hb.K[:, X0 + x] >= -4) & (hb.K[:, X0 + x] <= -2))[0]:
                hi = (x % 2 == 0) if wide else ((x + hb.K[y, X0 + x]) % 2 == 0)
                put(y, X0 + x, GRILLE_HI if hi else GRILLE, flat=True)
    # the grille on the roof strip of the end views (rows toward cab 2)
    for c in (1, 5):
        X0 = c * 128
        ys = [y for y in range(128) if (hb.face[y, X0:X0 + 128] == "R").any()]
        y0, y1 = min(ys), max(ys)            # far end .. near end of the strip
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            u = (1 - t) if c == 5 else t     # se: near = front; nw: near = rear
            if 0.58 <= u <= 0.86:
                for x in range(X0 + 60, X0 + 67):
                    if hb.face[y, x] == "R":
                        put(y, x, GRILLE_HI if (y % 2 == 0) else GRILLE, flat=True)
    cooler_hump(hb, out, painted)
    wrap_goggles(hb, out, painted, L.frame)
    if fam == "750_7":
        wide_screen(hb, out, painted)
    return unspecial(out, painted)


# moving up across the roof from its near edge goes toward the front (w, s) or
# the rear (n, e) of the loco: u per roof row is about 1 / 32
ROOF_DU = {0: -1, 6: -1, 2: +1, 4: +1}


def cooler_hump(hb, out, painted, ua=0.58, ub=0.86):
    """the radiator stands one pixel proud of the roof: a grille-top row above
    the silhouette over its length."""
    for c in (0, 2, 3, 4, 6, 7):
        X0 = c * 128
        cu = hb.column_u(c)
        for x in range(128):
            col = np.where(hb.solid[:, X0 + x])[0]
            if not len(col) or x not in cu:
                continue
            ytop = col.min()
            if hb.face[ytop, X0 + x] != "R":
                continue
            h = hb.top[(c, x)] - ytop
            u = cu[x] + (0 if c in (3, 7) else ROOF_DU[c] * h / 32.0)
            if ua <= u <= ub:
                out[ytop - 1, X0 + x] = GRILLE_HI
                out[ytop, X0 + x] = GRILLE
                painted[ytop - 1, X0 + x] = painted[ytop, X0 + x] = True


def wrap_goggles(hb, out, painted, frame):
    """the goggle frame wraps round the cab corners: the side-face column at
    each cab end gets the frame colour in rows K 2-4."""
    v = hexarr(hb.base)
    for c in (0, 2, 3, 4, 6, 7):
        X0 = c * 128
        cu = hb.column_u(c)
        if not cu:
            continue
        for x in (min(cu, key=lambda q: cu[q]), max(cu, key=lambda q: cu[q])):
            for y in np.where((hb.face[:, X0 + x] == "S") & np.isin(hb.K[:, X0 + x], (2, 3, 4)))[0]:
                if v[y, X0 + x] not in GLASS:
                    out[y, X0 + x] = shade(frame, FACT["S"].get(c, 0.87))
                    painted[y, X0 + x] = True


def wide_screen(hb, out, painted):
    """750.7: one wide windscreen, the goggle pillar between the panes (end
    face rows K 2-3) becomes glass in every view that shows a cab front."""
    glass = hexarr(hb.base) == 0x6B6B6B
    for y, x in zip(*np.where((hb.face == "E") & (hb.K >= 2) & (hb.K <= 3))):
        if glass[y, x]:
            continue
        c = x // 128
        left = any(glass[y, x - d] for d in (1, 2) if (x - d) // 128 == c)
        right = any(glass[y, x + d] for d in (1, 2) if (x + d) // 128 == c)
        if left and right:
            out[y, x] = (0x6B, 0x6B, 0x6C)
            painted[y, x] = True


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for name in JOBS[fam]:
            a = paint(fam, name)
            path = os.path.join(FAM, fam, "sprites", f"{name}.png")
            save(a, path)
            print("wrote", os.path.relpath(path, REPO))
            if prev:
                g = a.astype(np.uint8).copy()
                g[np.all(g == T, axis=2)] = (104, 124, 76)
                Image.fromarray(g).resize((3072, 384), Image.NEAREST).save(os.path.join(prev, f"{fam}_{name}.png"))


if __name__ == "__main__":
    main()
