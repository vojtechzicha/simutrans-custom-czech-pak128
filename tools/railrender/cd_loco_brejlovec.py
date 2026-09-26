#!/usr/bin/env python3
"""ČD "Brejlovec" diesel locomotives (754, 750.7), box models on the calibrated
rail renderer.

    python tools/railrender/cd_loco_brejlovec.py [family ...] [--preview DIR]

Families (vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png):
  754    ČKD T 478.4 "Brejlovec" with the goggle cab (small windows in the cab
         roof curve over the split windscreen, big roof headlight): najbrt2,
         najbrt1_2, najbrt1, cervenozluta, modrokremova
  750_7  CZ LOKO rebuild of the 753 (2010-2017): same carbody and hood, new
         flat cab front with one wide white-framed windscreen, no goggles:
         najbrt2, najbrt1_2

Scale: 16.66 m over buffers drawn at length 8 like the native CD_754 (2.08 m per
carunit), bodies 2-3 px taller than coaches like the natives. Geometry and the
pixel-row helpers follow rj_locos.E99 (imported, not edited): every livery zone
is a whole number of pixel rows counted from ZY (sill top), so the diagonal
views never show half-pixel slivers. u = carunits behind the front buffer face,
v = lateral (+v = the loco's right), z = model px above the rail head.

Colours come from cd_loco_livery.py. Local additions (not shared): FRAME_GREY
(dark grey frame / lower front of the N1 schemes and the red-yellow), RED_DK. The N2 roof
stays sapphire (photos of 754.062 / 750.710: the rounded roof is dark blue,
unlike the grey equipment roof of the 362).
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
import rj_locos as K  # noqa: E402  (screen-row helpers, Glyphs, bogie)
import cd_loco_livery as C  # noqa: E402
from rj_locos import prow, in_cols, in_vcols, on_col, vc, scr, _uu, Glyphs, EndGlyphs  # noqa: E402

WS = K.WS
WS_HI = K.WS_HI
P_BLACK = K.P_BLACK
P_BUF = K.P_BUF

FRAME_GREY = (62, 66, 70)      # dark grey frame / lower front (N1, N1.2, red-yellow)
RED_DK = (150, 26, 22)
LOCO_SKY = C.LOCO_SKY
N12_ROOF = (170, 175, 178)    # as the E99 N1.2 roof
N12_SILL = (58, 61, 64)       # as the E99 N1.2 sill


def pnt(c, top=None):
    return Paint(c, top=top)


def lighten(c, f):
    return tuple(min(255, int(round(x * f))) for x in c)


class Liv:
    """Zone paints of one livery. zones_side(r, k) and zones_front(r) name the
    body zone of a pixel row; the model resolves names to paints."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def livery(name):
    sky, sap, white = pnt(LOCO_SKY), pnt(C.SAPPHIRE), pnt(C.WHITE)
    if name == "najbrt2":
        # sky body, white stripe at lamp level, sapphire below down to the
        # solebar, sapphire roof; white windscreen frames; white front logo
        return Liv(name=name, roof=pnt(C.SAPPHIRE, top=(84, 94, 112)), sill=sap,
                   upper=sky, lower=sap, band=white, frame=white, beam=pnt(C.FRAME),
                   lamp=sap, logo_side="b", logo_front="w", n1=False,
                   grille=(pnt(lighten(LOCO_SKY, 0.62)), pnt(lighten(LOCO_SKY, 0.80))))
    if name in ("najbrt1_2", "najbrt1"):
        grey = pnt(C.LGREY) if name == "najbrt1_2" else pnt(C.N1_WHITE)
        roofc = N12_ROOF if name == "najbrt1_2" else C.N1_WHITE
        return Liv(name=name, roof=pnt(roofc, top=lighten(roofc, 1.06)), sill=pnt(N12_SILL),
                   upper=grey, lower=grey, band=grey, frame=sky, beam=pnt(C.FRAME),
                   lamp=pnt(FRAME_GREY), logo_side="b", logo_front="b", n1=True,
                   grille=(pnt(lighten(C.SAPPHIRE, 0.62)), pnt(lighten(C.SAPPHIRE, 0.85))))
    if name == "cervenozluta":
        red = pnt(C.RY_RED)
        return Liv(name=name, roof=pnt(C.RY_RED, top=lighten(C.RY_RED, 1.05)), sill=pnt(FRAME_GREY),
                   upper=red, lower=red, band=pnt(C.RY_YELLOW), frame=white, beam=red,
                   lamp=pnt(FRAME_GREY), logo_side=None, logo_front=None, n1=False,
                   grille=(pnt(RED_DK), pnt(lighten(C.RY_RED, 0.85))))
    if name == "modrokremova":
        return Liv(name=name, roof=pnt(C.BC_BLUE, top=(84, 96, 122)), sill=pnt(C.BC_BLUE),
                   upper=sky, lower=sky, band=pnt(C.BC_CREAM), frame=sky, beam=pnt(C.BC_BLUE),
                   lamp=sky, logo_side="b", logo_front="b", n1=False,
                   grille=(pnt(lighten(LOCO_SKY, 0.62)), pnt(lighten(LOCO_SKY, 0.80))))
    raise ValueError(name)


# side logo "ČD" (rounded box letters), 2 rows; front logo 1 row
LOGO_S = {"H": [".bbbb.", "b.bb.b", ".bbbb."], "D": [".bbb.", "b.b.b", ".bbb."]}
LOGO_F = ["cc.cc", "cc.cc"]


class Brejlovec:
    """ČKD T 478.3/4 carbody: 16.66 m, 3.08 m wide, Bo'Bo', two cabs, a long
    hood between them with a row of round portholes in the upper side, the
    cooling-air louvre block next to cab 2 and a raised louvred cooler on the
    roof. Rows count from ZY (sill top): body rows 0-5 diagonal, 0-6
    square-on; end faces rows 0 lamps, 1 stripe, 2-3 nose, 4-5 windscreen."""
    L = 8.0
    W = 0.97
    ZB = 2.5          # body side bottom (solebar)
    ZY = 3.6          # solebar top
    ZS1 = 9.6         # side wall top
    ZR1 = 10.4        # roof step 1
    ZR = 11.0         # roof plane
    PORTHOLES = (2.0, 2.52, 3.04, 3.56, 4.08, 4.60)   # from cab 1 end
    GRILLE = (5.02, 6.30)                              # louvre block before cab 2

    def __init__(self, liv, variant="754"):
        self.C = livery(liv)
        self.liv, self.variant = liv, variant
        self.g754 = variant == "754"
        cols = {"b": pnt(C.SAPPHIRE), "w": pnt(C.WHITE), "c": pnt(C.WHITE)}
        self.logo = (Glyphs(3.3, self.ZY, (2, 2), LOGO_S["H"], LOGO_S["D"], cols)
                     if self.C.logo_side else None)
        fc = pnt(C.WHITE) if self.C.logo_front == "w" else pnt(C.SAPPHIRE)
        self.flogo = (EndGlyphs(0.0, self.ZY, 2, LOGO_F, {"c": fc})
                      if self.C.logo_front else None)

    # --------------------------------------------------------- zones
    def zone_side(self, r, k):
        """body zone of pixel row r above ZY in view class k."""
        if self.liv == "najbrt2":
            lo = 0                                 # sapphire row 0 (+ the solebar)
            if r <= lo:
                return "lower"
            return "band" if r == lo + 1 else "upper"
        if self.liv == "cervenozluta":
            ya, yb = (1, 3) if k == "H" else (1, 2)
            return "band" if ya <= r <= yb else "upper"
        if self.liv == "modrokremova":
            ya, yb = (1, 3) if k == "H" else (1, 2)
            return "band" if ya <= r <= yb else "upper"
        return "upper"

    def n1_side(self, f, u, z, r, k):
        """Najbrt 1 / 1.2 trapezoids: grey at the cab-1 end, then a sky wedge
        and a sapphire wedge rising toward cab 2 (boundaries lean back)."""
        L = self.L
        s = u                                   # physical position from cab 1
        h = r / 6.0
        b1 = 1.62 + 0.9 * h                     # grey -> sky
        b2 = 2.10 + 1.6 * h                     # sky -> sapphire
        if s < b1:
            return self.C.upper
        if s < b2:
            return pnt(LOCO_SKY)
        return pnt(C.SAPPHIRE)

    # --------------------------------------------------------- paint
    def side(self, f, u, v, z, d):
        Cl, L = self.C, self.L
        if z >= self.ZS1:
            return Cl.roof
        if z < self.ZY:
            return Cl.sill
        near = u < L / 2
        k = vc(d)
        r = prow(d, z, self.ZY)
        top = 5 if k == "D" else 6
        s = L - u if f == "+v" else u            # as seen, left end = 0
        # cab: side window, door with window (both ends)
        if r >= 4 and in_cols(d, u, v, z, *_uu(L, near, 0.46, 0.86)):
            return WS_HI if r == top else WS
        da, db = _uu(L, near, 0.98, 1.40)
        if da - 0.1 <= u <= db + 0.1:
            if on_col(d, u, v, z, da, v) or on_col(d, u, v, z, db, v):
                return P_BLACK if not Cl.n1 else pnt(FRAME_GREY)
            if da <= u <= db and r >= 4 and in_cols(d, u, v, z, *_uu(L, near, 1.06, 1.32)):
                return WS
        # hood: louvre block next to cab 2 (physical u), portholes
        ga, gb = self.GRILLE
        if ga <= u <= gb and 1 <= r <= top - 1:
            x = math.floor(scr(d, u, v, z)[0])
            if on_col(d, u, v, z, (ga + gb) / 2, v):
                return Cl.grille[0]
            return Cl.grille[x % 2]
        pr = (4,) if k == "D" else (5,)
        if r in pr:
            for pc in self.PORTHOLES:
                if in_cols(d, u, v, z, pc - 0.12, pc + 0.12):
                    return WS
        if self.logo is not None and not Cl.n1:
            p = self.logo.at(f, u, v, z, d, L)
            if p is not None:
                return p
        if Cl.n1:
            return self.n1_side(f, u, z, r, k)
        return getattr(Cl, self.zone_side(r, k))

    def front(self, f, u, v, z, d):
        Cl = self.C
        if z >= self.ZS1:
            return self.front_roof(f, u, v, z, d)
        if z < self.ZY:
            return Cl.beam
        av = abs(v)
        sg = 1 if v > 0 else -1
        r = prow(d, z, self.ZY)
        if r >= 4:
            if self.g754:
                # split windscreen: two panes, centre pillar, frame round them
                if 0.07 <= av <= 0.78 and in_vcols(d, u, v, z, 0.09 * sg, 0.76 * sg):
                    return WS_HI if r == 5 else WS
                if av <= 0.88:
                    return Cl.frame
            else:
                # 750.7: one wide windscreen in a broad frame
                if av <= 0.74 and in_vcols(d, u, v, z, -0.72, 0.72):
                    return WS_HI if r == 5 else WS
                if av <= 0.88:
                    return Cl.frame
        if r == 0:
            # lamps: white inner pair, red marker outer; number plate
            if in_vcols(d, u, v, z, 0.46 * sg, 0.60 * sg):
                return R.HEAD
            if in_vcols(d, u, v, z, 0.68 * sg, 0.82 * sg):
                return pnt((0x9A, 0x1A, 0x14))
            if av < 0.28:
                return pnt((0xC8, 0x20, 0x1E))          # red number plate
            return Cl.lamp
        if self.flogo is not None and r in (2, 3):
            g = self.flogo.at(f, u, v, z, d)
            if g is not None:
                return g
        if Cl.n1:
            return Cl.upper
        if self.liv == "najbrt2":
            return Cl.band if r == 1 else Cl.upper
        if self.liv in ("cervenozluta", "modrokremova"):
            return Cl.band if r in (1, 2) else Cl.upper
        return Cl.upper

    def front_roof(self, f, u, v, z, d):
        """cab roof curve over the windscreen: goggles (754), roof colour."""
        Cl = self.C
        if self.g754 and z < self.ZR1 and f in ("-u", "+u"):
            av = abs(v)
            sg = 1 if v > 0 else -1
            if 0.30 <= av <= 0.62 and in_vcols(d, u, v, z, 0.32 * sg, 0.60 * sg):
                return WS
        if not self.g754 and z < self.ZR1 and f in ("-u", "+u") and abs(v) <= 0.80:
            return Cl.frame                    # 750.7: the broad windscreen frame
        return Cl.roof

    def body_mat(self):
        def mat(f, u, v, z, d):
            if f == "+z":
                return self.C.roof
            if f in ("+v", "-v"):
                return self.side(f, u, v, z, d)
            return self.front(f, u, v, z, d)
        return mat

    def uf(self, z):
        """front face position by height: the Brejlovec nose leans back from
        the lamp row and the windscreen is raked; 750.7 is flatter."""
        if self.g754:
            return 0.22 if z < 5.2 else (0.27 if z < 7.4 else 0.34)
        return 0.22 if z < 5.2 else (0.25 if z < 7.4 else 0.29)

    # --------------------------------------------------------- model
    def build(self):
        L, W, Cl = self.L, self.W, self.C
        own = "V"
        parts, lines = [], []
        body = self.body_mat()
        cham = 0.14
        for (z0, z1) in ((self.ZB, 5.2), (5.2, 7.4), (7.4, self.ZS1)):
            uf = self.uf(z0 + 0.01)
            parts.append(Part(uf, L - uf, -W + cham, W - cham, z0, z1, body, own))
            parts.append(Part(uf + 0.12, L - uf - 0.12, -W, W, z0, z1, body, own))
        # roof: rounded in two steps; the cab roof curve recedes further
        rc = 0.50 if self.g754 else 0.40
        parts.append(Part(rc, L - rc, -W + 0.18, W - 0.18, self.ZS1, self.ZR1, body, own))
        parts.append(Part(rc + 0.34, L - rc - 0.34, -W + 0.44, W - 0.44, self.ZR1, self.ZR,
                          lambda *a: Cl.roof, own))

        # raised louvred cooler on the hood roof, exhaust + fan boxes
        def cooler(f, u, v, z, d):
            dk = Paint(0x2E3134) if Cl.name != "najbrt1" else Paint(0x6E7275)
            li = Paint(0x484C50) if Cl.name != "najbrt1" else Paint(0x9A9EA1)
            if f == "+z":
                return dk if (u * 5.0) % 1.0 < 0.5 else li
            return Cl.roof
        parts.append(Part(2.05, 4.75, -0.66, 0.66, self.ZR, self.ZR + 0.55, cooler, own))
        parts.append(Part(5.10, 5.55, -0.30, 0.30, self.ZR, self.ZR + 0.45,
                          lambda *a: Paint(0x303336, top=0x3A3D40), own))
        # roof headlight over each cab
        for sgn in (1, -1):
            ua, ub = (0.60, 0.80) if sgn > 0 else (L - 0.80, L - 0.60)
            fac = "-u" if sgn > 0 else "+u"

            def lamp(f, u, v, z, d, fac=fac):
                return R.HEAD if f == fac else Paint(0x3A3D40, top=0x4A4D50)
            parts.append(Part(ua, ub, -0.16, 0.16, self.ZR1 - 0.1, self.ZR1 + 0.55, lamp, own))
        # underframe: bogies (pivots 8.9 m apart), fuel tank + air reservoirs
        for bc in (1.86, 6.14):
            parts += K.bogie(bc, 0.98, 0.76, W, self.ZB, own)
        parts.append(Part(3.02, 4.98, -W + 0.22, W - 0.22, 0.8, self.ZB,
                          lambda *a: Paint(0x303336), own))
        # buffer beams, yellow ploughs, buffers
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(0.14, 0.24), -W + 0.05, W - 0.05, 1.9, self.ZY,
                              lambda *a: Cl.beam, own))
            parts.append(Part(*uu(0.08, 0.26), -0.82, 0.82, 0.4, 1.9,
                              lambda *a: Paint(C.PLOUGH), own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, 0.14), vcn - 0.13, vcn + 0.13, 2.4, 3.1,
                                  lambda *a: P_BUF, own))
        return parts, lines


def row(liv, variant):
    parts, lines = Brejlovec(liv, variant).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


JOBS = {
    "754": [(liv, "754") for liv in ("najbrt2", "najbrt1_2", "najbrt1", "cervenozluta", "modrokremova")],
    "750_7": [(liv, "750.7") for liv in ("najbrt2", "najbrt1_2")],
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
        rows_all, labels = [], []
        for liv, variant in JOBS[fam]:
            rows = [row(liv, variant)]
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            rows_all += rows
            labels.append(liv)
            print("wrote", os.path.relpath(out, REPO))
        if prev:
            R.preview(rows_all, os.path.join(prev, f"{fam}.png"), z=4, labels=labels)


if __name__ == "__main__":
    main()
