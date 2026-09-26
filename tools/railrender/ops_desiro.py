#!/usr/bin/env python3
"""Siemens Desiro Classic (DB class 642) of Die Länderbahn (trilex) and DB Regio
Südost: the Desiro box model of desiro.py (geometry untouched, shared with the
Arriva family) with these operators' liveries.

    python tools/railrender/ops_desiro.py                  # every sheet
    python tools/railrender/ops_desiro.py dlb              # only die-landerbahn/642
    python tools/railrender/ops_desiro.py db               # only db-regio/642
    python tools/railrender/ops_desiro.py --preview DIR    # also 4x previews

Liveries (photos in the family.yaml comments):
  trilex     Die Länderbahn trilex white + orange (2020-23 redesign): white body,
             orange cantrail band that sweeps down in a "C" in front of the cab
             side window to the lower orange band, anthracite hood over a black
             front, orange doors, grey pinstripe + "≡ trilex" logo behind the cabs,
             orange "≡" on the front.
  dbregio    DB verkehrsrot of DB Regio Südost as desiro.py's "dbcervena", but the
             front carries the red DB logo box instead of white stickers.
             Written as dbcervena.png.
  vvo        DB Regio Südost VVO design (Dieselnetz refurbishment 2021-22): the
             same red with a white cantrail line above the window band, a white
             band at lamp height from the cab to the door (wrapping round the
             front corners), a white lower band, big white "VVO" on each car's
             right side and a DB logo in the band on its left side.

desiro.py's livery table and Car class are not modified: this module has its own
livery() and a Car subclass; liveries without a "scheme" key fall through to the
original drawing code.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import numpy as np  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
import desiro as D  # noqa: E402

PX = D.PX

# ------------------------------------------------------------------ trilex colours
# research de_at_operators.md A1 sprite bases, checked on 642 343 (Machnín 2023),
# 642 812 / 815 (Zittau) and 642 316 (Liberec)
T_WHITE = Paint(0xEEF0F0)
T_ORANGE = Paint(0xFF9224, top=0xF78C22)
T_PIN = Paint(0x9BA3A1)           # grey pinstripe, light enough to keep the side white
T_TEXT = Paint(0x3E4348)          # "trilex" wordmark
T_HOOD = Paint(0xB0B7BA, top=0xB8BFC2)   # silver-grey cab cap above the windscreen
T_BAND = Paint(0x66707A)          # window frames / pillars, lighter than the glass
T_BLACK = Paint(0x1C1F22)
T_SKIRT = Paint(0x46484A, top=0x3E4042)
T_ROOF = Paint(0xA3ABAF, top=0xA9B1B5)
T_SHOULDER = Paint(0x9AA2A6, top=0x9DA5A9)   # outer strip of the roof top (curved shoulder)

ORW = 0.42          # thickness (m, across the line) of the orange sweep behind the black front
# the sweep follows desiro.py's rear edge of the black front wrap (car-local m, height m),
# extended down to the skirt
SWEEP = [(0.35, 0.71)] + [(b, a) for (a, b) in D._SWF]
DIP = 0.30          # the cantrail band runs one row lower over the cab up to M_CAB + DIP
Z_OL1 = 2.95        # top of the lower orange band (bottom = Z_SK)
Z_P0, Z_P1 = 3.0, 3.95      # grey pinstripe row (the two real 13 cm lines share one row)
PIN_END = 9.55      # the pinstripes stop short of the door
LOGO = (3.75, 5.45)         # "≡ trilex" behind the cab (car-local m), one row above the pin
Z_LOGO = (4.05, 4.95)
T_BAND_HF0 = 3.62   # the grey window frame starts just before the first window (white
                    # between it and the cab side window)
CABWIN_FRAME = 0.08

# ------------------------------------------------------------------ DB / VVO colours
DB_RED = Paint(0xD8241C)
DB_LOGO = (0xE0, 0x22, 0x1A)      # DB logo box on the front
VVO_WHITE = Paint(0xE6E9E8, top=0xDDE0DF)
Z_VVO = (3.95, 4.90)              # white band at lamp height (1.48-1.84 m)
VVO_LETTERS = (4.70, 7.20)        # big "VVO" on the car's right side (car-local m)
VVO_DBBOX = (6.00, 6.50)          # DB logo in the band on the car's left side


def livery(name):
    if name == "trilex":
        return dict(
            scheme="trilex",
            body=T_WHITE, band=T_BAND, hood=T_HOOD,
            roof=T_ROOF, roofedge=T_ORANGE,
            skirt=T_SKIRT, sill=None, plough=Paint(0x3A3C3E), recess=T_BLACK,
            cheek=T_ORANGE, numband=Paint(0x2E3236), lampband=T_BLACK, dest=T_BLACK,
            door=T_ORANGE, doorsplit=Paint(0x34373B), shoulder=T_SHOULDER,
            stripe=None, logo=None, logo_front=None,
            roofbox=Paint(0x959DA1, top=0xA0A8AC), exhaust=Paint(0x2A2D30, top=0x1C1E20),
            crystals=False)
    if name == "dbregio":
        c = D.livery("dbcervena")
        c.update(scheme="db", numband=Paint(0x565B60), logo_front=None, db_front=True)
        return c
    if name == "vvo":
        c = livery("dbregio")
        c.update(scheme="vvo", sill=VVO_WHITE, white=VVO_WHITE,
                 roofedge=Paint(0xD8241C, top=0xC8251E), door=Paint(0xD2D6D8),
                 shoulder=Paint(0x9EA4A8, top=0x9EA4A8))
        return c
    return D.livery(name)


def sweep_dist(m, zm):
    """Distance (m) of a cab-side point behind the black front edge to that edge;
    points in front of it (m < edge) count as 0 (covered by the wrap or the corner)."""
    if m <= float(np.interp(zm, [b for a, b in SWEEP], [a for a, b in SWEEP])):
        return 0.0
    best = 9.0
    for (m0, z0), (m1, z1) in zip(SWEEP, SWEEP[1:]):
        dm, dz = m1 - m0, z1 - z0
        t = max(0.0, min(1.0, ((m - m0) * dm + (zm - z0) * dz) / (dm * dm + dz * dz)))
        best = min(best, ((m - m0 - t * dm) ** 2 + (zm - z0 - t * dz) ** 2) ** 0.5)
    return best


class Car(D.Car):
    """desiro.Car with the livery table of this module and the trilex / VVO paint."""

    def __init__(self, liv, owner, s_nose, dirn, lamp):
        self.C = livery(liv)
        self.owner, self.s_nose, self.dirn, self.lamp = owner, s_nose, dirn, lamp

    # ---------------------------------------------------------------- dispatch
    def mat(self, f, u, v, z, d):
        # the band colour ("roofedge") only on the ledge and the cap side: the outer
        # strip of the roof top stays roof grey, so the cantrail band is one row thick
        sh = self.C.get("shoulder")
        if sh is not None and f == "+z" and z >= D.ZR - 0.05 and self.m_of(u) >= D.M_CAB - 0.05                 and abs(v) > D.W - D.CAPIN - 0.12:
            return sh
        return D.Car.mat(self, f, u, v, z, d)

    def side(self, m, z, cs):
        sch = self.C.get("scheme")
        if sch == "trilex":
            return self.t_side(m, z, cs)
        if sch == "vvo":
            r = self.vvo_side(m, z, cs)
            if r is not None:
                return r
        return D.Car.side(self, m, z, cs)

    def front(self, vl, z, top=False):
        C = self.C
        av = abs(vl)
        sch = C.get("scheme")
        if sch == "trilex":
            return self.t_front(vl, z, top)
        if C.get("db_front") and av < 0.26 and 4.3 <= z <= 5.2:
            return DB_LOGO                              # red DB box between the lamps
        if sch == "vvo" and Z_VVO[0] <= z < Z_VVO[1] and av > D.front_hw(z) - 0.20:
            if not (self.lamp is not None and 0.46 <= av <= 0.66 and 4.4 <= z <= 5.1):
                return C["white"]                       # white band round the corners
        return D.Car.front(self, vl, z, top)

    # ---------------------------------------------------------------- trilex
    def t_side(self, m, z, cs):
        C = self.C
        zm = z * PX
        cab = m < D.M_CAB
        if z >= D.ZS:
            return C["hood"] if m < D.M_CAB + 0.05 else C["roofedge"]
        # black front wrap round the corner (windscreen, lamp glass), as desiro.py
        if cab and zm >= 1.45 and m < D.sw_front(zm):
            if zm >= 3.02:
                return C["hood"]
            if zm >= 2.22:
                return D.WS_HI if zm > 3.0 else D.WS
            if zm >= 1.58:
                if self.lamp is not None and 4.4 <= z <= 5.1 and m < D.nose_m(z) + 0.14:
                    return self.lamp
                return C["lampband"]
        if z < D.Z_SK:
            if z < 1.2 and m < 0.9:
                return C["plough"]
            return C["skirt"]
        # door (orange leaves, dark joint and edges, lit windows)
        if D.DOOR[0] <= m <= D.DOOR[1] and D.Z_D0 <= z <= D.Z_D1:
            t = (m - D.DOOR[0]) / (D.DOOR[1] - D.DOOR[0])
            if 0.45 <= t <= 0.55:
                return C["doorsplit"]
            if D.Z_DW0 <= z <= D.Z_DW1 and (0.12 <= t <= 0.40 or 0.60 <= t <= 0.88):
                return R.GLASS_HI if z > D.Z_DW1 - 0.5 else R.GLASS
            if t < 0.06 or t > 0.94:
                return C["doorsplit"]
            return C["door"]
        # cantrail band row: orange over the cab (stepping down), white along the body
        if z >= D.Z_B1:
            return T_ORANGE if m < D.M_CAB + DIP else T_WHITE
        if z < Z_OL1:
            return T_ORANGE                              # lower orange band
        # cab side window in its dark frame, white round it, the orange sweep in front
        if m < T_BAND_HF0 and z >= D.Z_HB0:
            sr = D.sw_rear(zm)
            if D.Z_HW0 <= z <= 7.75 and sr + 0.2 <= m <= 2.72:
                return D.WS_HI if z > 6.9 else D.WS_MID
            if 5.25 <= z <= 7.95 and sr + 0.2 - CABWIN_FRAME <= m <= 2.72 + CABWIN_FRAME:
                return C["band"]
        if cab and sweep_dist(m, zm) <= ORW:
            return T_ORANGE
        if m < T_BAND_HF0 and z >= D.Z_HB0:
            return T_WHITE
        # window bands (the high-floor frame starts at T_BAND_HF0)
        hf = T_BAND_HF0 <= m <= D.BAND_HF[1] and z >= D.Z_HB0
        lf = D.BAND_LF[0] <= m <= D.BAND_LF[1] and z >= D.Z_LB0
        if hf or lf:
            wins = D.WIN_HF + [D.WIN_HF4[cs]] if hf else D.WIN_LF
            w0 = D.Z_HW0 if hf else D.Z_LW0
            if w0 <= z <= D.Z_W1:
                for (a, b) in wins:
                    if a + D.PILLAR_GROW <= m <= b - D.PILLAR_GROW:
                        return R.GLASS_HI if z > D.Z_W1 - 0.55 else R.GLASS
            return C["band"]
        # grey pinstripe from the orange "C" to short of the door
        if Z_P0 <= z < Z_P1 and m <= PIN_END:
            return T_PIN
        # "≡ trilex" logo: orange mark first as read, dark wordmark after it
        if LOGO[0] <= m <= LOGO[1] and Z_LOGO[0] <= z <= Z_LOGO[1]:
            x = (m - LOGO[0]) / (LOGO[1] - LOGO[0])
            if cs == "R":
                x = 1 - x                                # reads left to right on both sides
            if x < 0.22:
                return T_ORANGE
            if x >= 0.36:
                return T_TEXT
        return T_WHITE

    def t_front(self, vl, z, top=False):
        C = self.C
        av = abs(vl)
        if z < 1.2:
            return C["plough"]
        if z < D.Z_SK:
            return C["skirt"]
        if z < 4.2:                                     # black lower nose + number band,
            if av >= 0.70:                               # orange corners (the sweep's ends)
                return T_ORANGE
            return C["recess"] if z < 3.9 else C["numband"]
        if z < 5.35:                                    # lamp glass
            if self.lamp is not None and 0.46 <= av <= 0.66 and 4.4 <= z <= 5.1:
                return self.lamp
            if av < 0.20 and 4.3 <= z <= 5.2:
                return (0xFF, 0x92, 0x24)               # orange "≡" mark
            return C["lampband"]
        if z < 5.95:
            return C["dest"]
        if z < 8.8:
            if av > D.front_hw(z) - 0.06:
                return D.WS
            return D.WS_HI if z > 8.2 else D.WS
        if not top and self.lamp is R.HEAD and av < 0.1 and 9.0 <= z <= 9.5:
            return R.HEAD
        return C["hood"]

    # ---------------------------------------------------------------- VVO
    def vvo_side(self, m, z, cs):
        """Only the VVO additions; None = draw as the DB livery."""
        C = self.C
        cab = m < D.M_CAB
        if z >= D.ZS:
            return None
        # white cantrail line directly above the window band (from the cab seam back)
        if z >= D.Z_B1 and m >= D.M_CAB + 0.05:
            return C["white"]
        in_door = D.DOOR[0] <= m <= D.DOOR[1]
        if in_door or m > D.BAND_HF[1]:
            return None
        if cab and m < D.nose_m(z) - 0.02:
            return None
        # white band at lamp height, from the front corner back to the door
        if Z_VVO[0] <= z < Z_VVO[1]:
            if cab and self.lamp is not None and 4.4 <= z <= 5.1 and m < D.nose_m(z) + 0.14:
                return self.lamp
            if cs == "L" and VVO_DBBOX[0] <= m <= VVO_DBBOX[1]:
                return DB_LOGO                          # DB logo box in the band
            return C["white"]
        # big white "VVO" between the two white bands on the car's right side
        if cs == "R" and D.Z_SILL <= z < Z_VVO[0] and VVO_LETTERS[0] <= m <= VVO_LETTERS[1]:
            x = 1 - (m - VVO_LETTERS[0]) / (VVO_LETTERS[1] - VVO_LETTERS[0])
            k = min(2, int(x * 3))
            lx = x * 3 - k                               # 0..1 across one letter as read
            y = (z - D.Z_SILL) / (Z_VVO[0] - D.Z_SILL)   # 0 bottom .. 1 top of this strip
            if k < 2:                                    # V: two strokes closing downwards
                c = 0.5 + (lx - 0.5)
                half = 0.12 + 0.30 * y
                if abs(abs(c - 0.5) - half) < 0.14:
                    return C["white"]
            elif lx < 0.26 or lx > 0.74:                 # O: its two sides
                return C["white"]
        return None


# ------------------------------------------------------------------ the unit
def unit(liv):
    A = Car(liv, "A", D.OFF, +1, R.HEAD)
    B = Car(liv, "B", D.L_UNIT - D.OFF, -1, R.TAIL)
    parts = []
    for c in (A, B):
        parts += c.parts() + c.roof_parts() + c.under_parts()
    ua, ub = A.u_of(D.BODY_END - 0.02), B.u_of(D.BODY_END - 0.02)
    parts.append(Part(min(ua, ub), max(ua, ub), -D.W + 0.1, D.W - 0.1, 1.7, D.ZS + 0.2,
                      lambda f, u, v, z, d: D.BELLOWS if f != "+z" else Paint(0x3A3C40), "A"))
    return parts, [], [("A", 0.0), ("B", 10.0)]


def rows_for(liv):
    parts, lines, cars = unit(liv)
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]


# family dir -> [(sheet name, livery)]
JOBS = {
    "dlb": ("die-landerbahn/642", [("trilex", "trilex")]),
    "db": ("db-regio/642", [("dbcervena", "dbregio"), ("vvo", "vvo")]),
}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for key in (args or list(JOBS)):
        fam, sheets = JOBS[key]
        for (sheet, liv) in sheets:
            rows = rows_for(liv)
            out = os.path.join(REPO, "vehicle-rail", *fam.split("/"), "sprites", f"{sheet}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"642_{key}_{sheet}.png"), z=4,
                          labels=["642 A", "642 B"])
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
