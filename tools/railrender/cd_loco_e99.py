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


LIV = {
    "najbrt2": Liv("najbrt2", N2_ROOF, pc(CL.SAPPHIRE), pc(CL.SAPPHIRE)),
    "najbrt1_2": Liv("najbrt1_2", N12_ROOF, N12_SILL, N12_SILL),
    "zelenozluta": Liv("zelenozluta", GY_ROOF, GY_SILL, P_BLACK),
}

# side lettering, 2 px high: ČD logo + "České dráhy" (white on N2, sapphire on N1.2)
SIDE_LOGO = {"H": ["cc.cc.ccc.cc.cc.cc", "cc.cc.c.c.cc.c..cc"],
             "D": ["cc.ccccc.cccc", "cc.cc.cc.cc.c"]}
FRONT_LOGO = ["ccc"]


class CDE99(E99):
    def __init__(self, liv, unit):
        self.C = C = LIV[liv]
        self.liv, self.unit = liv, unit
        self.bigg = None
        self.smallg = {}
        lc = {"najbrt2": "w", "najbrt1_2": "s", "zelenozluta": "k"}[liv]
        cols = {"c": LOGO[lc]}
        zy = self.ZY
        # side logo mid-body just above the light band (N2 / GY), in the sky
        # middle panel on N1.2; on side A between the porthole pairs
        row = {"najbrt2": (2, 2), "najbrt1_2": (1, 1), "zelenozluta": (1, 1)}[liv]
        self.logo = {f: Glyphs(3.2, zy, row, SIDE_LOGO["H"], SIDE_LOGO["D"], cols) for f in ("+v", "-v")}
        self.flogo = EndGlyphs(0.0, zy, 2, FRONT_LOGO, cols)

    # --------------------------------------------------------- paint
    def zone(self, f, u, v, z, d, r, front):
        """plain livery colour at pixel row r above ZY."""
        liv, L = self.liv, self.L
        if liv == "najbrt2":
            return pc(CL.WHITE) if r <= 1 else pc(LOCO_SKY)
        if liv == "zelenozluta":
            return pc(CL.GY_YELLOW) if r <= 2 else pc(CL.GY_GREEN)
        # najbrt1_2
        if front:
            return pc(LOCO_SKY) if r >= 3 else pc(CL.LGREY)
        t = max(0.0, min(1.0, (z - self.ZY) / (self.ZS1 - self.ZY)))
        cu = min(u, L - u)
        if cu < 0.48 + 0.20 * t:
            return pc(CL.LGREY)
        if cu < 0.98 + 0.18 * t:
            return pc(CL.SAPPHIRE)
        return pc(LOCO_SKY)

    def side(self, f, u, v, z, d):
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
        else:
            lv = (3, 4) if k == "D" else (4, 5)
            if lv[0] <= r <= lv[1] and 1.0 <= s <= 7.0:
                x = math.floor(scr(d, u, v, z)[0])
                return C.louvre[x % 2]
        p = self.logo[f].at(f, u, v, z, d, L)
        if p is not None:
            return p
        return self.zone(f, u, v, z, d, r, False)

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
        L, W, C = self.L, self.W, self.C
        own = "V"
        parts, lines = [], []
        body = self.body_mat()
        cham = 0.14
        for (z0, z1) in ((self.ZB, 6.4), (6.4, 8.0), (8.0, self.ZC)):
            uf = self.uf(z0 + 0.01)
            parts.append(Part(uf, L - uf, -W + cham, W - cham, z0, z1, body, own))
            parts.append(Part(uf + 0.12, L - uf - 0.12, -W, W, z0, z1, body, own))

        def roof(f, u, v, z, d):
            return C.roof
        parts.append(Part(0.52, L - 0.52, -W + 0.22, W - 0.22, self.ZC, 10.6, roof, own))
        parts.append(Part(0.74, L - 0.74, -W + 0.44, W - 0.44, 10.6, self.ZR, roof, own))

        # two raised louvred resistor blocks mid-roof
        def grille(f, u, v, z, d):
            if f == "+z":
                return Paint(0x464B50) if (u * 4.0) % 1.0 < 0.5 else Paint(0x70767C)
            if f in ("+v", "-v"):
                x = math.floor(scr(d, u, v, z)[0])
                return Paint(0x3C4146) if x % 2 else Paint(0x5E6368)
            return Paint(0x464B50)
        for (a, b) in ((2.75, 3.85), (4.05, 5.15)):
            parts.append(Part(a, b, -0.66, 0.66, self.ZR, self.ZR + 1.0, grille, own))
        if self.unit in ("162", "362"):          # cab air-conditioning box over cab 1
            parts.append(Part(0.90, 1.45, -0.46, 0.46, self.ZR, self.ZR + 0.6,
                              lambda *a: Paint(0x2A2D30, top=0x3A3E42), own))
        if self.unit == "362":                   # AC main switch / insulators
            parts.append(Part(2.30, 2.60, -0.20, 0.20, self.ZR, self.ZR + 0.7,
                              lambda *a: Paint(0x6A6F74, top=0x7A7F84), own))
        # single-arm pantographs: front lowered, rear raised
        pcol = C.panto
        pp = Paint((pcol[0] << 16) | (pcol[1] << 8) | pcol[2])
        parts.append(Part(1.55, 2.45, -0.40, 0.40, self.ZR, self.ZR + 0.30, lambda *a: pp, own))
        parts.append(Part(5.9, 6.5, -0.36, 0.36, self.ZR, self.ZR + 0.30, lambda *a: pp, own))
        zb = self.ZR + 0.30
        h = PANTO_TOP - zb
        ub, uk, uh = 6.25, 6.85, 5.9
        lines += [((ub, 0.0, zb), (uk, 0.0, zb + h * 0.5), pcol, own, False),
                  ((uk, 0.0, zb + h * 0.5), (uh, 0.0, PANTO_TOP), pcol, own, False),
                  ((uh, -0.62, PANTO_TOP), (uh, 0.62, PANTO_TOP), (0x2A, 0x2A, 0x2C), own, True)]
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


JOBS = {
    "162": ["najbrt2", "najbrt1_2"],
    "163": ["najbrt2", "zelenozluta"],
    "362": ["najbrt2", "najbrt1_2"],
    "371": ["najbrt2"],
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
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=[fam])
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
