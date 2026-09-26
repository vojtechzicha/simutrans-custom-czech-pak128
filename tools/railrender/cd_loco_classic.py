#!/usr/bin/env python3
"""ČD 1216 Taurus (and the Taurus body the ÖBB / PKP generator taurus.py paints),
box model in the 2026-09-26 render style (style.py).

    python tools/railrender/cd_loco_classic.py [1216] [--preview DIR]

The 151 and 242 keep TommPa9's hand-drawn pak128.cs sheets (the user preferred
them to a render). One parametric body with rounded ends (the Taurus nose):

  - lower nose vertical, windscreen raked back from the headlights up, nose
    slabs chamfered at the corners so the cab reads round, not boxy;
  - a flat roof cap between the cabs whose side faces are the dark gutter
    (style.GUTTER), never a light rim;
  - livery zones on whole pixel rows (rj_locos.prow), measured on Commons photos;
  - no side lettering; pantographs light arm + dark 2 px head bar;
  - every sheet post-processed with style.polish(**style.POLISH).

u = carunits behind the front buffer, v lateral (+v right), z model px above rail.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
from rj_locos import P_BUF, P_YEL, PANTO_TOP, WS, WS_HI, bogie, in_cols, prow, scr, vc  # noqa: E402
import cd_loco_livery as CL  # noqa: E402
import style as S  # noqa: E402


def pc(c):
    return Paint(c)


ROOF = Paint(S.ROOF, top=S.ROOF_TOP)
GUT = Paint(S.GUTTER)
FRAME = Paint(CL.FRAME)
SILL_GREY = Paint((58, 61, 64))
LOUVRE = (Paint(0x23272B), Paint(0x33383D))
GRILLE_TOP = Paint(0x40454A, top=0x5A6066)
DOOR_LINE = Paint(0x1E2124)


class Classic:
    """One parametric rounded-end loco. Subclasses set the geometry constants
    and implement zone(face, u, v, z, d, r, cu, front) -> Paint."""
    L = 8.0
    W = 0.95
    ZB = 2.6          # body side bottom
    ZY = 3.6          # sill top: pixel rows count from here
    ZS = 10.0         # side wall top
    ZR = 11.0         # roof cap top
    UN = 0.30         # lower nose face
    UWT = 0.72        # windscreen top recedes to here
    ZW = 6.6          # rake starts above this height
    RC = 0.16         # nose corner chamfer
    UCAB = 1.35       # cab length (side windows / door)
    BOGIES = (2.05, 5.95)
    WB = 0.76
    PANTOS = ((1.55, 2.45), (5.55, 6.45))
    RAISED = 5.95     # base u of the raised pantograph (fold towards the front)
    ROOFBOX = ((2.7, 5.3, 0.62, 0.9),)    # (u0, u1, half width, height) on the roof

    def __init__(self, liv, reverse=False):
        self.liv, self.reverse = liv, reverse

    def nose_u(self, z):
        if z < self.ZW:
            return self.UN
        t = min(1.0, (z - self.ZW) / (self.ZS - self.ZW))
        return self.UN + (self.UWT - self.UN) * t

    # ------------------------------------------------------------ paint
    def side(self, f, u, v, z, d):
        L = self.L
        cu = min(u, L - u)
        r = prow(d, z, self.ZY)
        top = 5 if vc(d) == "D" else 6
        near = u < L / 2
        if z < self.ZY:
            return self.sill()
        # cab side window and door behind it
        a, b = (0.48, 0.86) if near else (L - 0.86, L - 0.48)
        if r >= top - 1 and in_cols(d, u, v, z, a, b):
            return WS_HI if r == top else WS
        a, b = (1.02, 1.30) if near else (L - 1.30, L - 1.02)
        if in_cols(d, u, v, z, a, a) or in_cols(d, u, v, z, b, b):
            return DOOR_LINE
        if r >= top - 1 and in_cols(d, u, v, z, a + 0.06, b - 0.06):
            return WS
        p = self.side_detail(f, u, v, z, d, r, top, cu)
        if p is not None:
            return p
        return self.zone(f, u, v, z, d, r, cu, False)

    def side_detail(self, f, u, v, z, d, r, top, cu):
        return None

    def louvre(self, d, u, v, z):
        x = int(np.floor(scr(d, u, v, z)[0]))
        return LOUVRE[x % 2]

    def front(self, f, u, v, z, d):
        rear = (f == "+u") != self.reverse
        if z < self.ZY:
            return self.beam()
        av = abs(v)
        r = prow(d, z, self.ZY)
        if z >= self.ZW - 0.1:
            if 0.10 <= av <= self.W - 0.16:
                return WS_HI if r == 6 else WS
            return self.frame_front(f, u, v, z, d, r)
        if r == 1 and 0.48 <= av <= 0.72:
            return R.TAIL if rear else R.HEAD
        if r == 2 and av < 0.12:
            return R.TAIL if rear else R.HEAD
        return self.zone(f, u, v, z, d, r, 0.0, True)

    def frame_front(self, f, u, v, z, d, r):
        return self.zone(f, u, v, z, d, r, 0.0, True)

    def sill(self):
        return FRAME

    def beam(self):
        return FRAME

    def body_mat(self):
        def m(f, u, v, z, d):
            if f == "+z":
                if z < self.ZS - 0.05:        # stepped nose tops = the sloped screen
                    return self.front("-u" if u < self.L / 2 else "+u", u, v, z, d)
                return ROOF
            if f in ("+v", "-v"):
                return self.side(f, u, v, z, d)
            return self.front(f, u, v, z, d)
        return m

    # ------------------------------------------------------------ model
    def build(self):
        L, W = self.L, self.W
        own = "V"
        parts, lines = [], []
        body = self.body_mat()
        parts.append(Part(self.UWT, L - self.UWT, -W, W, self.ZB, self.ZS, body, own))
        z0 = self.ZB
        while z0 < self.ZS - 1e-6:
            z1 = min(self.ZS, z0 + 0.5)
            uf = self.nose_u((z0 + z1) / 2)
            if uf < self.UWT:
                for (a, b) in ((uf + self.RC, self.UWT), (L - self.UWT, L - uf - self.RC)):
                    parts.append(Part(a, b, -W, W, z0, z1, body, own))
                for (a, b) in ((uf, self.UWT), (L - self.UWT, L - uf)):
                    parts.append(Part(a, b, -W + self.RC, W - self.RC, z0, z1, body, own))
            z0 = z1

        def cap(f, u, v, z, d):
            return ROOF if f == "+z" else GUT
        parts.append(Part(self.UWT + 0.05, L - self.UWT - 0.05, -W + 0.08, W - 0.08,
                          self.ZS, self.ZR, cap, own))
        for (a, b, hw, h) in self.ROOFBOX:
            parts.append(Part(a, b, -hw, hw, self.ZR, self.ZR + h, lambda *x: GRILLE_TOP, own))
        pp = Paint(S.PANTO_ARM)
        for (a, b) in self.PANTOS:
            parts.append(Part(a, b, -0.40, 0.40, self.ZR, self.ZR + 0.3, lambda *x: pp, own))
        zb = self.ZR + 0.3
        lines += R.pantograph(self.RAISED, zb, own, fold=+1, reach=0.6, height=PANTO_TOP - zb,
                              col=S.PANTO_ARM, head=S.PANTO_HEAD, half_head=0.62, thick=False)
        for bc in self.BOGIES:
            parts += bogie(bc, 0.98, self.WB, W, self.ZB, own)
        parts.append(Part(self.BOGIES[0] + 1.05, self.BOGIES[1] - 1.05, -W + 0.22, W - 0.22,
                          0.8, self.ZB, lambda *x: Paint(0x303336), own))
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(0.14, self.UN + 0.02), -W + 0.05, W - 0.05, 1.9, self.ZY,
                              lambda *x: self.beam(), own))
            parts.append(Part(*uu(0.08, 0.26), -0.82, 0.82, 0.4, 1.9, lambda *x: P_YEL, own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, 0.14), vcn - 0.13, vcn + 0.13, 2.4, 3.1,
                                  lambda *x: P_BUF, own))
        return parts, lines


# ------------------------------------------------------------------ Taurus
class Taurus(Classic):
    """Siemens Taurus ES64U2/U4 (19.28 m), drawn at length 10 like the native
    1216 / 1116: the rounded Taurus nose with its big raked screen.

    Livery-parametric so other operators' generators can import it:
        Taurus(table, reverse=False).build() / taurus_row(table, reverse=False)
    table (colour tuples, see TAURUS_CD):
        body   upper body side
        band   the stripe just above the lower band (same as body for none)
        low    lower band (rows 0..low_rows)
        low_rows  highest pixel row of the lower band (row 0 = first above the sill)
        cab    cab top / screen surround, swept back along the cab side
        nose   lower front face under the screen
        frame  solebar, buffer beam and the band under the nose
    reverse=True: the loco turned round (tail lights at the travel front), for
    the trailing loco of a push-pull pair."""
    L = 10.0
    W = 0.92
    ZS = 11.4
    ZR = 12.2
    UN = 0.34
    UWT = 1.05
    ZW = 6.2
    RC = 0.24
    UCAB = 1.6
    BOGIES = (2.55, 7.45)
    WB = 0.72
    PANTOS = ((1.9, 2.8), (7.2, 8.1))
    RAISED = 7.55
    ROOFBOX = ((3.4, 6.6, 0.55, 0.7),)

    def __init__(self, table, reverse=False):
        super().__init__("taurus", reverse)
        self.t = {k: (pc(v) if isinstance(v, tuple) else v) for k, v in table.items()}

    def sill(self):
        return self.t["frame"]

    def beam(self):
        return self.t["frame"]

    def side_detail(self, f, u, v, z, d, r, top, cu):
        if r >= 5 and cu < self.UCAB + 0.10 * (r - 5):
            return self.t["cab"]
        return None

    def frame_front(self, f, u, v, z, d, r):
        return self.t["cab"]

    def zone(self, f, u, v, z, d, r, cu, front):
        t = self.t
        if front:
            if r >= 4:
                return t["cab"]
            return t["nose"] if r >= 1 else t["frame"]
        if r <= t["low_rows"]:
            return t["low"]
        if r == t["low_rows"] + 1:
            return t["band"]
        return t["body"]


# ČD 1216 najbrt2 (1216.951-954, 902/903): sky-blue body, white lower band, dark
# grey frame; the cab top and screen surround sapphire, swept back along the side.
TAURUS_CD = {"body": CL.LOCO_SKY, "band": CL.LOCO_SKY, "low": CL.WHITE, "low_rows": 2,
             "cab": CL.SAPPHIRE, "nose": CL.WHITE, "frame": (70, 74, 78)}
# ČD railjet scheme (CD_railjet_1216, Lubak91): bright royal-blue body, a thin navy
# line over the white lower band, navy cab. Base colours chosen so the polished
# sheet matches the old one's brightness (ne side 0x2163DE / 0x192152 / white);
# style.polish pushes saturated blues much darker, hence the lighter bases.
TAURUS_CD_RJ = {"body": (90, 138, 240), "band": (58, 74, 148), "low": (255, 255, 255), "low_rows": 2,
                "cab": (58, 74, 148), "nose": (255, 255, 255), "frame": (70, 74, 78)}


def taurus_row(table, reverse=False):
    """8 rendered tiles (unpolished) of a Taurus in `table`; polish the saved sheet."""
    parts, lines = Taurus(table, reverse).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


TAURUS_LIV = {"najbrt2": TAURUS_CD, "railjet": TAURUS_CD_RJ}
JOBS = {
    "1216": [("najbrt2", [False]), ("railjet", [False, True])],
}


def rows_for(fam, liv, revs):
    rows = []
    for rev in revs:
        rows.append(taurus_row(TAURUS_LIV[liv], rev))
    return rows


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for liv, revs in JOBS[fam]:
            rows = rows_for(fam, liv, revs)
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            R.save_rows(rows, out)
            S.polish(Image.open(out), **S.POLISH).save(out)
            if prev:
                im = np.array(Image.open(out).convert("RGB"))
                pr = [[im[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] for c in range(8)]
                      for r in range(len(rows))]
                R.preview(pr, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=[f"{fam} {liv}"] * len(rows))
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
