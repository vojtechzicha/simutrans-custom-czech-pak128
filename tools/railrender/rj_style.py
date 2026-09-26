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
    return [RJ._empty_row() for _ in range(k)] + [e99_row(RJ.E362[k][1], "362")]


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
