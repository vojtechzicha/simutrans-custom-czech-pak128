#!/usr/bin/env python3
"""RegioJet locomotives in the render style agreed on 2026-09-26 (tools/railrender/
style.py, reference src/style_ref_362.png).

    python tools/railrender/regiojet.py 162 193 362_2 386_2 388_2 703 730 740

regiojet.py loads this module last, so its JOBS replace the rj_locos / rj_shunters
ones for these families. The models are the rj_locos / rj_shunters ones; the style
is applied here in RegioJet-only code paths, so the ČD generators that import those
modules keep their behaviour:
  - Škoda 99E (162, 362.2): the hard-edged slab box of the approved ČD 362 (sharp
    corners, vertical front, flat roof whose sides are the dark gutter), horizontal
    ribbing on the plain body, the lowered FNM resistor box kept. Side A keeps the
    huge REGIOJET letters (a bold shape at 1x); the 1-px "POOL" / small words go.
  - 362.2: RJEso362, the ČD 362 (cd_loco_e99) geometry and treatment one to one:
    heavy resistor blocks + insulators, the dark louvre band high under the gutter
    on side B (a large light panel on the 212 / 220 retros), ribbing on the plain
    body only; the retro zones, toned-down light roofs and painted pantographs.
  - TRAXX (386.2, 388.2) and Vectron (193): the first roof row above the yellow
    body (the TRAXX's grey shoulder, the Vectron's roof curve) is the dark gutter,
    no light rim.
  - Every pantograph: arms style.PANTO_ARM (painted ones keep the livery colour:
    362.212 yellow, 362.220 red, 162 red-brown), head bar style.PANTO_HEAD, 2 px.
  - Every sheet (shunters included): style.polish(**style.POLISH).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
import rj_locos as RJ  # noqa: E402
import rj_shunters as SH  # noqa: E402
import style as ST  # noqa: E402

GUT = Paint(ST.GUTTER, top=ST.GUTTER)
ROOF = Paint(ST.ROOF, top=ST.ROOF_TOP)


# ------------------------------------------------------------------ helpers
def restyle_lines(lines, z_min):
    """Pantograph lines above the roof: light arms, dark 2-px head bar (the one
    line running across the loco, i.e. along v only)."""
    out = []
    for ln in lines:
        a, b, col, own = ln[:4]
        thick = ln[4] if len(ln) > 4 else False
        if min(a[2], b[2]) < z_min:
            out.append((a, b, col, own, thick))
        elif abs(a[0] - b[0]) < 1e-6 and abs(a[2] - b[2]) < 1e-6 and abs(a[1] - b[1]) > 1e-6:
            out.append((a, b, ST.PANTO_HEAD, own, True))
        else:
            out.append((a, b, ST.PANTO_ARM, own, False))
    return out


def polish_row(tiles):
    return [np.array(ST.polish(Image.fromarray(t), **ST.POLISH)) for t in tiles]


def render(parts, lines):
    return polish_row([R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS])


def _dk(p, f):
    return Paint(tuple(int(round(x * f)) for x in p.base))


# ------------------------------------------------------------------ Škoda 99E
class RJEso(RJ.E99):
    """The RJ 99E on the approved ČD 362 slab box."""
    ZTOP = RJ.E99.ZS1 + 0.3       # top of the slab (roof-coloured band above ZS1)
    ZROOF = RJ.E99.ZR - 0.4       # flat roof plane

    def __init__(self, liv, unit="162"):
        super().__init__(liv, unit)
        self.smallg = {}                                  # 1-px words read as noise
        self.plain = {id(self.C.body), id(RJ.CSD_YELLOW), id(RJ.FNM_BLUE), id(RJ.FNM_SILVER)}

    def uf(self, z):
        return 0.22                                       # vertical front

    def side(self, f, u, v, z, d):
        p = super().side(f, u, v, z, d)
        if self.ZY <= z < self.ZS1 and id(p) in self.plain:
            L = self.L
            s = L - u if f == "+v" else u
            r = RJ.prow(d, z, self.ZY)
            top = 5 if RJ.vc(d) == "D" else 6
            if 1.1 <= s <= L - 1.1 and r % 2 == 1 and r < top - 1:
                return _dk(p, ST.RIB)                     # horizontal ribbing
        return p

    def build(self):
        L, W, C = self.L, self.W, self.C
        own = "V"
        parts, lines = [], []
        uf = self.uf(0)
        parts.append(Part(uf, L - uf, -W, W, self.ZB, self.ZTOP, self.body_mat(), own))
        # flat roof slab: its side faces are the dark gutter; the style roof grey,
        # except where the livery paints the roof light (362.212 cream, 362.220 silver)
        rb = C.roof.base
        roof = C.roof if 0.299 * rb[0] + 0.587 * rb[1] + 0.114 * rb[2] > 150 else ROOF
        parts.append(Part(uf + 0.05, L - uf - 0.05, -W + 0.06, W - 0.06, self.ZTOP, self.ZROOF,
                          lambda f, *a: roof if f == "+z" else GUT, own))
        zr = self.ZROOF

        def resistor(f, u, v, z, d):                      # lowered FNM resistor box
            if f == "+z":
                return Paint(0x2E3134) if (u * 4.0) % 1.0 < 0.5 else Paint(0x484C50)
            return Paint(0x3A3E42)
        parts.append(Part(2.95, 5.05, -0.60, 0.60, zr, zr + 0.6, resistor, own))
        parts.append(Part(0.95, 1.50, -0.42, 0.42, zr, zr + 0.55,
                          lambda *a: Paint(0x44484C, top=0x505458), own))
        # a livery with painted pantographs (362.212 yellow, 362.220 FNM red, the
        # 162's red-brown) keeps them; grey / black ones get the light style arm
        pc = C.panto
        acol = pc if max(pc) - min(pc) > 40 else ST.PANTO_ARM
        arm = Paint(acol)
        parts.append(Part(1.2, 2.3, -0.40, 0.40, zr, zr + 0.30, lambda *a: arm, own))
        parts.append(Part(6.0, 6.6, -0.36, 0.36, zr, zr + 0.30, lambda *a: arm, own))
        zb = zr + 0.30
        h = RJ.PANTO_TOP - zb
        ub, uk, uh = 6.35, 6.95, 6.0
        lines += [((ub, 0.0, zb), (uk, 0.0, zb + h * 0.5), acol, own, False),
                  ((uk, 0.0, zb + h * 0.5), (uh, 0.0, RJ.PANTO_TOP), acol, own, False),
                  ((uh, -0.62, RJ.PANTO_TOP), (uh, 0.62, RJ.PANTO_TOP), ST.PANTO_HEAD, own, True)]
        for bc in (2.02, 5.98):
            parts += RJ.bogie(bc, 0.98, 0.76, W, self.ZB, own)
        parts.append(Part(3.05, 4.95, -W + 0.22, W - 0.22, 0.8, self.ZB, lambda *a: Paint(0x303336), own))

        def plough_mat(f, u, v, z, d):
            if C.plough == "chevron":
                x, y = RJ.scr(d, u, v, z)
                return RJ.P_YEL if (math.floor(x) + math.floor(y)) % 3 else RJ.P_BLACK
            return RJ.P_YEL
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(0.14, 0.24), -W + 0.05, W - 0.05, 1.9, self.ZY, lambda *a: C.beam, own))
            parts.append(Part(*uu(0.08, 0.26), -0.82, 0.82, 0.4, 1.9, plough_mat, own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, 0.14), vcn - 0.13, vcn + 0.13, 2.4, 3.1,
                                  lambda *a: RJ.P_BUF, own))
        return parts, lines


def e99_row(liv, unit="162"):
    return render(*RJEso(liv, unit).build())


# ------------------------------------------------------------------ 362.2
# The 362.2 on the exact geometry and treatment of the approved ČD 362
# (cd_loco_e99.CDE99.build): slab box, flat roof with a dark gutter, heavy
# resistor blocks + insulators on the roof, the dark louvre band high under the
# gutter, ribbed plain sides. What differs on the real RJ locos (photos in the RJ
# research dossier, research/photos/362-2_retro):
#   side A (+v) portholes, side B (-v) the louvre band (as the 162);
#   the retro liveries' own zones, roofs and painted pantographs.
# Light retro roofs (212 cream, 220 silver) are toned down one step so they read
# as a roof under the style's dark gutter, not as a white plank.
ROOF_362 = {
    "csdmodrozluta": Paint((188, 182, 172), top=(196, 190, 180)),
    "fnmzelenosediva": Paint((172, 177, 181), top=(182, 187, 191)),
}
# louvre band: (rows below the top row in the square-on views, slat pair); 212 /
# 220 carry a big light panel over the blue / green upper body (photos 362 212 /
# 220), 213 / 219 a black / dark grey band as on the ČD 362
LOUVRE_362 = {
    "csdmodrozluta": (2, (Paint((182, 176, 167)), Paint((168, 162, 153)))),
    "fnmzelenosediva": (1, (Paint((176, 181, 186)), Paint((162, 167, 172)))),
    "zluta": (1, (Paint(0x23272B), Paint(0x33383D))),
    "zlutosediva": (1, (Paint(0x2A2D30), Paint(0x3A3E42))),
}


class RJEso362(RJ.E99):
    def __init__(self, liv, unit="362"):
        super().__init__(liv, unit)
        self.smallg = {}                                  # 1-px words read as noise

    def uf(self, z):
        return 0.22                                       # vertical front

    def zone(self, f, u, v, z, d, r):
        """plain livery colour at pixel row r (as rj_locos.E99.side's zones)."""
        C, L, liv = self.C, self.L, self.liv
        if liv == "csdmodrozluta":
            return RJ.CSD_YELLOW if r in (1, 2) else C.body
        if liv == "fnmzelenosediva":
            rl = self.fnm_row(min(u, L - u), 3)
            if r == rl:
                return RJ.FNM_BLUE
            return C.body if r > rl else RJ.FNM_SILVER
        if liv == "zlutosediva" and r == 0:
            return C.sill
        return C.body

    def side(self, f, u, v, z, d):
        C, L, liv = self.C, self.L, self.liv
        if z >= self.ZS1:
            return self.roof
        if z < self.ZY:
            return C.sill
        s = L - u if f == "+v" else u
        near = u < L / 2
        k = RJ.vc(d)
        r = RJ.prow(d, z, self.ZY)
        top = 5 if k == "D" else 6
        # cab side window, cab door with its window (both ends, both sides)
        if r >= 4 and RJ.in_cols(d, u, v, z, *RJ._uu(L, near, 0.30, 0.48)):
            return RJ.WS_HI if r == top else RJ.WS
        da, db = RJ._uu(L, near, 0.58, 0.98)
        if da - 0.1 <= u <= db + 0.1:
            if RJ.on_col(d, u, v, z, da, v) or RJ.on_col(d, u, v, z, db, v):
                return RJ.P_BLACK
            if da <= u <= db and r >= 4 and RJ.in_cols(d, u, v, z, *RJ._uu(L, near, 0.66, 0.90)):
                return RJ.WS
        if f == "+v":
            # side A: portholes high up, the big REGIOJET letters where the livery has them
            if r >= top - (1 if k == "H" else 0):
                for p in self.PORTHOLES:
                    if abs(s - p) < 0.3 and RJ.in_cols(d, u, v, z, L - p - 0.11, L - p + 0.11):
                        return RJ.WS
            if self.bigg is not None:
                p = self.bigg.at(f, u, v, z, d, L)
                if p is not None:
                    return p
        else:
            # side B: the louvre band high under the gutter, between the doors
            n, slats = LOUVRE_362[liv]
            if k == "D" and liv in ("csdmodrozluta", "fnmzelenosediva"):
                n -= 1                  # 5 diagonal rows: keep the zones below the panel
            if top - n <= r <= top and 1.25 <= s <= L - 1.25:
                x = math.floor(RJ.scr(d, u, v, z)[0])
                return slats[x % 2]
        base = self.zone(f, u, v, z, d, r)
        # horizontal ribbing on the plain body only: a livery band (the ČSD yellow,
        # the FNM blue line) stays clean, as the ČD 362's white stripe does
        if base in (C.body, RJ.FNM_SILVER) and 1.1 <= s <= L - 1.1 and r % 2 == 1 and r < top - 1:
            return _dk(base, ST.RIB)
        return base

    def build(self):
        L, W, C = self.L, self.W, self.C
        own = "V"
        parts, lines = [], []
        self.roof = ROOF_362.get(self.liv, ROOF)
        roofp = self.roof
        uf = self.uf(0)
        zt = self.ZS1 + 0.3                     # side wall top
        zr = self.ZR - 0.4                      # roof plane
        parts.append(Part(uf, L - uf, -W, W, self.ZB, zt, self.body_mat(), own))
        parts.append(Part(uf + 0.05, L - uf - 0.05, -W + 0.06, W - 0.06, zt, zr,
                          lambda f, *a: roofp if f == "+z" else GUT, own))

        def grille(f, u, v, z, d):
            if f == "+z":
                return Paint(0x40454A) if (u * 4.0) % 1.0 < 0.5 else Paint(0x5A6066)
            x = math.floor(RJ.scr(d, u, v, z)[0])
            return Paint(0x35393E) if x % 2 else Paint(0x50555A)
        # the FNM resistor block sits 340 mm lower than on the ČD locos
        for (a, b) in ((2.6, 3.9), (4.1, 5.4)):
            parts.append(Part(a, b, -0.78, 0.78, zr, zr + 1.2, grille, own))

        def ins(*a):
            return Paint(0x9AA0A6, top=0xB0B5BA)
        for a in (2.2, 5.55):                            # roof insulators
            parts.append(Part(a, a + 0.25, -0.25, 0.25, zr, zr + 1.0, ins, own))
        parts.append(Part(0.60, 1.10, -0.46, 0.46, zr, zr + 0.6,      # cab 1 air conditioning
                          lambda *a: Paint(0x2A2D30, top=0x3A3E42), own))
        parts.append(Part(3.92, 4.08, -0.20, 0.20, zr, zr + 1.2, ins, own))   # AC main switch
        # painted pantographs keep their colour (212 yellow, 220 red), grey ones
        # the light style arm; head bar always the dark style one
        pc = C.panto
        acol = pc if max(pc) - min(pc) > 40 else ST.PANTO_ARM
        arm = Paint(acol)
        parts.append(Part(1.2, 2.1, -0.40, 0.40, zr, zr + 0.3, lambda *a: arm, own))
        parts.append(Part(5.9, 6.8, -0.40, 0.40, zr, zr + 0.3, lambda *a: arm, own))
        zb = zr + 0.3
        h = RJ.PANTO_TOP - zb
        ub, uk, uh = 6.3, 6.9, 6.0
        lines += [((ub, 0.0, zb), (uk, 0.0, zb + h * 0.5), acol, own, False),
                  ((uk, 0.0, zb + h * 0.5), (uh, 0.0, RJ.PANTO_TOP), acol, own, False),
                  ((uh, -0.62, RJ.PANTO_TOP), (uh, 0.62, RJ.PANTO_TOP), ST.PANTO_HEAD, own, True)]
        for bc in (2.02, 5.98):
            parts += RJ.bogie(bc, 0.98, 0.76, W, self.ZB, own)
        parts.append(Part(3.05, 4.95, -W + 0.22, W - 0.22, 0.8, self.ZB, lambda *a: Paint(0x303336), own))

        def plough_mat(f, u, v, z, d):
            if C.plough == "chevron":
                x, y = RJ.scr(d, u, v, z)
                return RJ.P_YEL if (math.floor(x) + math.floor(y)) % 3 else RJ.P_BLACK
            return RJ.P_YEL
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(0.14, 0.24), -W + 0.05, W - 0.05, 1.9, self.ZY, lambda *a: C.beam, own))
            parts.append(Part(*uu(0.08, 0.26), -0.82, 0.82, 0.4, 1.9, plough_mat, own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, 0.14), vcn - 0.13, vcn + 0.13, 2.4, 3.1,
                                  lambda *a: RJ.P_BUF, own))
        return parts, lines

    def front(self, f, u, v, z, d):
        if z >= self.ZS1:
            return self.roof
        return super().front(f, u, v, z, d)

    def body_mat(self):
        base = super().body_mat()

        def mat(f, u, v, z, d):
            return self.roof if f == "+z" else base(f, u, v, z, d)
        return mat


def e362_row(liv):
    return render(*RJEso362(liv).build())


# ------------------------------------------------------------------ TRAXX / Vectron
def _gutter_roof(parts, zs, roof_names=("roof_mat", "mat")):
    """Wrap the roof part(s) starting at the body top so their first pixel row
    above the body, on the long sides, is the dark gutter."""
    for p in parts:
        if abs(p.b[4] - zs) < 1e-6 and p.b[5] > zs:
            m = p.mat

            def mat(f, u, v, z, d, m=m):
                if f in ("+v", "-v") and RJ.prow(d, z, zs) == 0:
                    return GUT
                return m(f, u, v, z, d)
            p.mat = mat
    return parts


def traxx_row(gen, liv):
    t = RJ.Traxx(gen, liv)
    parts, lines = t.build()
    parts = _gutter_roof(parts, t.ZS1)      # the grey roof shoulder starts at the body top
    return render(parts, restyle_lines(lines, t.ZR))


def vectron_row():
    v = RJ.VectronRJ()
    parts, lines = v.build()
    V = v.V
    parts = _gutter_roof(parts, V.ZS)
    return render(parts, restyle_lines(lines, V.ZR))


# ------------------------------------------------------------------ shunters
def shunter_rows(fam):
    out = []
    for liv, make, labels in SH.JOBS[fam]:
        out.append((liv, (lambda make=make: [polish_row(r) for r in make()]), labels))
    return out


# ================================================================== jobs
def _rows_362(k):
    return [RJ._empty_row() for _ in range(k)] + [e362_row(RJ.E362[k][1])]


JOBS = {
    "386_2": [("zluta", lambda: [traxx_row("ms2e", "zluta")], ["386.2"])],
    "388_2": [("zluta", lambda: [traxx_row("t3", "zluta")], ["388.2"]),
              ("zlutapool", lambda: [traxx_row("t3", "zlutapool"), traxx_row("t3", "zlutapool")],
               ["388.2", "1388"])],
    "193": [("zluta", lambda: [vectron_row()], ["193"])],
    "162": [("zluta", lambda: [e99_row("zluta", "162")], ["162"])],
    "362_2": [(liv, (lambda k=k: _rows_362(k)), ["-"] * k + [vid]) for k, (vid, liv) in enumerate(RJ.E362)],
}
for _fam in SH.JOBS:
    JOBS[_fam] = shunter_rows(_fam)
