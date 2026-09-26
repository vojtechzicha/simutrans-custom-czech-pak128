#!/usr/bin/env python3
"""ČD Škoda "Peršing / Eso" locomotives (162, 163, 362, 371), box models on the
calibrated rail renderer.

    python tools/railrender/cd_loco_e99.py [family ...] [--preview DIR]

The body is the 16.8 m Škoda 99E / E 499.3 family, taken from rj_locos.E99
(imported, never edited; RegioJet's 162 / 362.2 were fitted to native CD 363).
This file only swaps the paint, the roof equipment and the per-class side
openings:

  162 / 163 / 362  side A (+v): four portholes in the upper body; side B (-v):
                   the long dark louvre band between the doors (photos 162 039,
                   162 097, 362 062, 163 068).
  371              no portholes and no louvre band: five small square windows
                   high on both sides (photos 371 001 / 003 / 004 / 015).
  roof             two raised louvred resistor blocks mid-roof (not RegioJet's
                   lowered FNM box); an air-conditioned cab box over cab 1 on
                   162 and 362 (not 163); an extra AC switch box on 362.

Liveries (colours from cd_loco_livery.py, layouts from Commons photos):
  najbrt2        LOCO_SKY upper body, WHITE band over the lamps (rows 0-1 on sides
                 and fronts), SAPPHIRE sill / buffer beam, grey roof, white ČD
                 logo on the fronts and "ČD České dráhy" mid-side.
  najbrt1_2      LGREY cab ends and fronts, SKY window band on the fronts, on
                 each side a SAPPHIRE wedge behind every cab (slanting forward
                 toward the bottom) and SKY between the wedges; dark grey sill,
                 light grey roof (362 062, 362 092, 162 054).
  zelenozluta    163 ČD green with the yellow band over the lamps on sides and
                 fronts, yellow windscreen frames, black ČD logo (163 068).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
import rj_locos as RJ  # noqa: E402
from rj_locos import (E99, EndGlyphs, Glyphs, P_BLACK, P_BUF, P_YEL, WS, WS_HI,  # noqa: E402
                      PANTO_TOP, _uu, bogie, in_cols, in_vcols, on_col, prow, scr, vc)
import cd_loco_livery as CL  # noqa: E402
import style as ST  # noqa: E402


def pc(c):
    return Paint(c)


# loco-only colours (not in cd_loco_livery)
# the Najbrt 2 light blue on the locomotive bodies reads clearly lighter than
# RAL 5015 in every photo (162 039 / 097, 362 131, 371 003): about #3C94D6
LOCO_SKY = (60, 148, 214)
N2_ROOF = Paint((124, 130, 138), top=(132, 138, 146))       # weathered blue-grey roof
N12_ROOF = Paint((170, 175, 178), top=(160, 165, 168))      # light grey roof (362 062)
N12_SILL = Paint((58, 61, 64))                              # dark grey sill band
GY_ROOF = Paint((120, 124, 122), top=(112, 116, 114))
GY_SILL = Paint((34, 64, 42))
LOUVRE_DK = (Paint(0x2C3036), Paint(0x3A3F46))
PANTO_GREY = (0x40, 0x43, 0x46)
LOGO = {"w": Paint(CL.WHITE), "s": Paint(CL.SAPPHIRE), "k": Paint(0x1C1E20)}


class Liv:
    def __init__(self, name, roof, sill, beam, louvre=LOUVRE_DK, panto=PANTO_GREY):
        self.name, self.roof, self.sill, self.beam = name, roof, sill, beam
        self.louvre, self.panto = louvre, panto
        self.plough = "yellow"


STYLE_ROOF = Paint(ST.ROOF, top=ST.ROOF_TOP)                # 2026-09-26 style, all schemes
GREEN = (44, 110, 62)                                        # ČSD / ČD green (162 018)
CREAM = CL.BC_CREAM
LIV = {
    "najbrt2": Liv("najbrt2", STYLE_ROOF, pc(CL.SAPPHIRE), pc(CL.SAPPHIRE)),
    "najbrt1_2": Liv("najbrt1_2", STYLE_ROOF, N12_SILL, N12_SILL),
    "zelenozluta": Liv("zelenozluta", STYLE_ROOF, GY_SILL, P_BLACK),
    "zelenokremova": Liv("zelenokremova", STYLE_ROOF, pc((28, 60, 40)), P_BLACK),
    "modrokremova": Liv("modrokremova", STYLE_ROOF, pc((22, 44, 88)), P_BLACK),
    "cervenozluta": Liv("cervenozluta", STYLE_ROOF, pc((70, 72, 74)), P_BLACK),
}

# side lettering, 2 px high: ČD logo + "České dráhy" (white on N2, sapphire on N1.2)
SIDE_LOGO = {"H": ["cc.cc.ccc.cc.cc.cc", "cc.cc.c.c.cc.c..cc"],
             "D": ["cc.ccccc.cccc", "cc.cc.cc.cc.c"]}
FRONT_LOGO = ["ccc"]


class _NoGlyph:
    def at(self, *a, **k):
        return None


class CDE99(E99):
    def __init__(self, liv, unit):
        self.C = C = LIV[liv]
        self.liv, self.unit = liv, unit
        self.bigg = None
        self.smallg = {}
        lc = {"najbrt2": "w", "najbrt1_2": "s"}.get(liv, "k")
        cols = {"c": LOGO[lc]}
        zy = self.ZY
        # side logo mid-body just above the light band (N2 / GY), in the sky
        # middle panel on N1.2; on side A between the porthole pairs
        row = {"najbrt2": (2, 2)}.get(liv, (1, 1))
        self.logo = {f: Glyphs(3.2, zy, row, SIDE_LOGO["H"], SIDE_LOGO["D"], cols) for f in ("+v", "-v")}
        self.flogo = EndGlyphs(0.0, zy, 2, FRONT_LOGO, cols)
        # 2026-09-26 style: no 1-px side lettering (it reads as noise)
        self.logo = {f: _NoGlyph() for f in ("+v", "-v")}

    # --------------------------------------------------------- paint
    def zone(self, f, u, v, z, d, r, front):
        """plain livery colour at pixel row r above ZY (proportions from photos)."""
        liv, L = self.liv, self.L
        if liv == "najbrt2":
            # one thin white row at headlight level, sky blue above (362 158, 162 039)
            return pc(CL.WHITE) if r == 0 else pc(LOCO_SKY)
        if liv == "zelenozluta":
            return pc(CL.GY_YELLOW) if r <= 1 else pc((52, 112, 64))
        if liv == "zelenokremova":
            # 162 018: dark green body, cream band under the windows, cream screen frame
            if front and r >= 4:
                return pc(CREAM)
            return pc(CREAM) if r in (2, 3) else pc(GREEN)
        if liv == "modrokremova":
            # ES 499.1 as delivered: dark blue body, cream band at lamp level
            return pc(CREAM) if r in (1, 2) else pc((34, 78, 150))
        if liv == "cervenozluta":
            # 371 as delivered (1996): red upper body, yellow band, grey lower row
            if r == 0:
                return pc((150, 154, 156))
            return pc(CL.RY_YELLOW) if r in (1, 2) else pc((214, 74, 40))
        # najbrt1_2
        if front:
            return pc(CL.LGREY)          # light grey front, dark windscreens (362 030)
        # 362 030 / 092: the whole cab section up to the door is light grey, then a
        # sapphire wedge rises from the solebar behind it, sky blue beyond
        t = max(0.0, min(1.0, (z - self.ZY) / (self.ZS1 - self.ZY)))
        cu = min(u, L - u)
        if cu < 1.25:
            return pc(CL.LGREY)
        if cu < 1.25 + 1.1 * (1.0 - t):
            return pc(CL.SAPPHIRE)
        return pc(LOCO_SKY)

    def _side_base(self, f, u, v, z, d):
        C, L = self.C, self.L
        if z >= self.ZS1:
            return C.roof
        if z < self.ZY:
            return C.sill
        s = L - u if f == "+v" else u
        near = u < L / 2
        k = vc(d)
        r = prow(d, z, self.ZY)
        top = 5 if k == "D" else 6
        if r >= 4 and in_cols(d, u, v, z, *_uu(L, near, 0.30, 0.48)):
            return WS_HI if r == top else WS
        da, db = _uu(L, near, 0.58, 0.98)
        if da - 0.1 <= u <= db + 0.1:
            if on_col(d, u, v, z, da, v) or on_col(d, u, v, z, db, v):
                return P_BLACK
            if da <= u <= db and r >= 4 and in_cols(d, u, v, z, *_uu(L, near, 0.66, 0.90)):
                return WS
        if self.unit == "371":
            # five small square windows high on both sides
            if r >= top - (1 if k == "H" else 0):
                for wc in (1.75, 2.75, 4.0, 5.25, 6.25):
                    if abs(s - wc) < 0.3 and in_cols(d, u, v, z, L - wc - 0.12, L - wc + 0.12):
                        return WS
        elif f == "+v":
            if r >= top - (1 if k == "H" else 0):
                for p in self.PORTHOLES:
                    if abs(s - p) < 0.3 and in_cols(d, u, v, z, L - p - 0.11, L - p + 0.11):
                        return WS
        p = self.logo[f].at(f, u, v, z, d, L)
        if p is not None:
            return p
        return self.zone(f, u, v, z, d, r, False)

    def side(self, f, u, v, z, d):
        """2026-09-26 style: the Eso / Persing slab side is ribbed, and a dark
        louvre band runs high between the doors (not on the 371)."""
        base = self._side_base(f, u, v, z, d)
        if not (self.ZY <= z < self.ZS1):
            return base
        L = self.L
        s = L - u if f == "+v" else u
        r = prow(d, z, self.ZY)
        top = 5 if vc(d) == "D" else 6
        lb = 1.45 if self.liv == "najbrt1_2" else 1.25   # N1.2: band starts after the grey cab section
        if self.unit != "371" and r in (top - 1, top) and lb <= s <= L - lb \
                and not (f == "+v" and any(abs(s - p) < 0.3 for p in self.PORTHOLES)):
            x = math.floor(scr(d, u, v, z)[0])
            return Paint(0x23272B) if x % 2 else Paint(0x33383D)
        if 1.1 <= s <= L - 1.1 and r % 2 == 1 and r < top - 1 and isinstance(base, Paint):
            c = base.base
            return Paint(tuple(int(x * ST.RIB) for x in c))
        return base

    def uf(self, z):
        return 0.22                      # vertical front: the Eso is a slab box

    def front(self, f, u, v, z, d):
        C, liv = self.C, self.liv
        if z >= self.ZS1:
            return C.roof
        if z < self.ZY:
            return C.beam
        av = abs(v)
        sg = 1 if v > 0 else -1
        r = prow(d, z, self.ZY)
        if r >= 4:
            if in_vcols(d, u, v, z, 0.12 * sg, 0.78 * sg) and 0.08 <= av <= 0.82:
                return WS_HI if r == 5 else WS
            if liv == "zelenozluta" and av <= 0.86:
                return pc(CL.GY_YELLOW)                   # yellow window frames
        if r == 3 and av < 0.26:
            if in_vcols(d, u, v, z, -0.16, 0.16):
                return R.HEAD
            return P_BLACK
        if r == 0:
            if in_vcols(d, u, v, z, 0.50 * sg, 0.64 * sg):
                return R.HEAD
            if in_vcols(d, u, v, z, 0.70 * sg, 0.84 * sg):
                return Paint(0x9A1A14)
            if av < 0.30:
                return Paint(0xC8201E)                    # red number plate
        g = self.flogo.at(f, u, v, z, d)
        if g is not None:
            return g
        return self.zone(f, u, v, z, d, r, True)

    # --------------------------------------------------------- model
    def build(self):
        """2026-09-26 style: a slab box with sharp corners, a vertical front and a
        flat roof with a hard edge and a dark gutter (the Eso / Persing is not a
        rounded Laminatka), heavy roof equipment, light pantograph arms with a
        dark head bar."""
        L, W, C = self.L, self.W, self.C
        own = "V"
        parts, lines = [], []
        body = self.body_mat()
        uf = self.uf(0)
        zt = self.ZS1 + 0.3                     # side wall top
        zr = self.ZR - 0.4                      # roof plane
        parts.append(Part(uf, L - uf, -W, W, self.ZB, zt, body, own))
        gut = Paint(ST.GUTTER)
        parts.append(Part(uf + 0.05, L - uf - 0.05, -W + 0.06, W - 0.06, zt, zr,
                          lambda f, u, v, z, d: C.roof if f == "+z" else gut, own))

        def grille(f, u, v, z, d):
            if f == "+z":
                return Paint(0x40454A) if (u * 4.0) % 1.0 < 0.5 else Paint(0x5A6066)
            x = math.floor(scr(d, u, v, z)[0])
            return Paint(0x35393E) if x % 2 else Paint(0x50555A)
        for (a, b) in ((2.6, 3.9), (4.1, 5.4)):          # resistor / cooling blocks
            parts.append(Part(a, b, -0.78, 0.78, zr, zr + 1.6, grille, own))

        def ins(*a):
            return Paint(0x9AA0A6, top=0xB0B5BA)
        for a in (2.2, 5.55):                            # roof insulators
            parts.append(Part(a, a + 0.25, -0.25, 0.25, zr, zr + 1.0, ins, own))
        if self.unit in ("162", "362"):                  # cab air-conditioning box, cab 1
            parts.append(Part(0.60, 1.10, -0.46, 0.46, zr, zr + 0.6,
                              lambda *a: Paint(0x2A2D30, top=0x3A3E42), own))
        if self.unit == "362":                           # AC main switch
            parts.append(Part(3.92, 4.08, -0.20, 0.20, zr, zr + 1.2, ins, own))
        arm = ST.PANTO_ARM
        pp = Paint((arm[0] << 16) | (arm[1] << 8) | arm[2])
        parts.append(Part(1.2, 2.1, -0.40, 0.40, zr, zr + 0.3, lambda *a: pp, own))
        parts.append(Part(5.9, 6.8, -0.40, 0.40, zr, zr + 0.3, lambda *a: pp, own))
        zb = zr + 0.3
        h = PANTO_TOP - zb
        ub, uk, uh = 6.3, 6.9, 6.0
        lines += [((ub, 0.0, zb), (uk, 0.0, zb + h * 0.5), arm, own, False),
                  ((uk, 0.0, zb + h * 0.5), (uh, 0.0, PANTO_TOP), arm, own, False),
                  ((uh, -0.62, PANTO_TOP), (uh, 0.62, PANTO_TOP), ST.PANTO_HEAD, own, True)]
        for bc in (2.02, 5.98):
            parts += bogie(bc, 0.98, 0.76, W, self.ZB, own)
        parts.append(Part(3.05, 4.95, -W + 0.22, W - 0.22, 0.8, self.ZB, lambda *a: Paint(0x303336), own))
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(0.14, 0.24), -W + 0.05, W - 0.05, 1.9, self.ZY,
                              lambda *a: C.beam, own))
            parts.append(Part(*uu(0.08, 0.26), -0.82, 0.82, 0.4, 1.9, lambda *a: P_YEL, own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, 0.14), vcn - 0.13, vcn + 0.13, 2.4, 3.1,
                                  lambda *a: P_BUF, own))
        return parts, lines


def row(liv, unit):
    parts, lines = CDE99(liv, unit).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


def polish_sheet(path):
    """Apply the agreed post-process (style.POLISH) to a written sheet."""
    from PIL import Image
    im = Image.open(path)
    im.load()
    ST.polish(im, **ST.POLISH).save(path)


JOBS = {
    "162": ["najbrt2", "najbrt1_2", "zelenokremova"],
    "163": ["najbrt2", "najbrt1_2", "zelenozluta"],
    "362": ["najbrt2", "najbrt1_2", "modrokremova"],
    "371": ["najbrt2", "najbrt1_2", "cervenozluta"],
}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for liv in JOBS[fam]:
            rows = [row(liv, fam)]
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            polish_sheet(out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=[fam])
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
