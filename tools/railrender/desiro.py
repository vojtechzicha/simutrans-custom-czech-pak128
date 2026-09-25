"""Arriva vlaky class 642: Siemens Desiro Classic (DB VT 642) 2-car articulated
DMU, drawn from scratch with the pak128 box raycaster (render.py + railkit.py),
structured like lint.py.

Regenerate with `python tools/railrender/arriva.py 642`.

Real vehicle (Siemens datasheet "Dieselmechanischer Triebzug DESIRO VT 642",
Bestell-Nr. A19100-V800-B185-V3, side/plan drawing with dimensions; photos on
Commons "Class 642 of Arriva vlaky"):
  41 700 mm over couplers, 41 200 mm over the body noses (coupler 250 mm),
  2 830 mm wide, roof 3.60 m, AC units to 3 819 mm, B'(2)B', powered bogies
  (wheelbase 1 900) 4.60 m behind each nose, Jakobs bogie (2 650) in the middle,
  16 000 mm bogie pitch, wheels 770 mm; low floor 575 mm (60 %), high floor
  1 250 mm over the outer bogies; one double plug door per car side, 1 480 mm.
Model: the unit is 20 cu (10 + 10), M = 41.7/20 = 2.085 m per cu.
Car-local coordinates: m = metres behind that car's BODY NOSE (the drawing's
zero; the coupler face is 0.25 m ahead), z = model px (1 px = 0.375 m).
Car B is car A turned 180 degrees, so a car's left side always shows the
drawing's VT 642.5 side and its right side the VT 642.0 side.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS


PX = 0.375                    # metres per model px (height)
L_UNIT = 41.7
M = L_UNIT / 20.0             # metres per carunit along the track
OFF = 0.25                    # coupler face ahead of the body nose
J = 20.6                      # Jakobs bogie centre (body-nose metres) = half unit
BODY_END = 20.36              # car body ends 0.24 m short of the Jakobs centre
M_CAB = 3.32                  # GRP cab head glued to the aluminium body here
W = R.W_STD * 2.83 / 2.825    # body half width (cu)
CAPIN = 0.2                   # roof cap inset (cu)

# ------------------------------------------------------------------ heights (px)
Z_SKB = 0.75      # skirt bottom (0.28 m) in the low-floor part / under the cab
Z_BB = 2.4        # body bottom over the bogies (0.90 m)
Z_SK = 1.9        # top of the dark skirt = bottom of the body colour (0.71 m; the
                  # Arriva blue reaches ~0.85 m in photos, lowered so the body colour
                  # under the tall low-floor windows is 2 px)
Z_SILL = 2.95     # top of the DB light-grey sill band (drawn 1 px)
Z_HB0 = 5.2       # window band bottom, high-floor ends (1.95 m)
Z_LB0 = 4.0       # window band bottom, low-floor part (1.50 m; real 1.27 m, raised so
                  # the body colour under the windows reads - coordinator review)
Z_HW0 = 5.45      # passenger window bottom, high floor (2.04 m)
Z_LW0 = 4.15      # passenger window bottom, low floor (1.56 m)
Z_W1 = 8.1        # window top (3.04 m)
Z_B1 = 8.25       # window band top (3.09 m); body colour above it (>= 1 px)
ZS = 9.3          # side wall top (3.49 m)  - the upper band kept 1 px tall
ZR = 9.75         # roof crest (3.66 m)
Z_D0, Z_D1 = 1.47, 8.2          # door leaves: low floor 0.55 m to 3.07 m
Z_DW0, Z_DW1 = 3.6, 7.75        # door leaf windows

# ------------------------------------------------------------------ layout (body-nose metres)
WIN_HF = [(3.80, 5.14), (5.45, 6.80), (7.10, 8.44)]
WIN_HF4 = {"L": (8.76, 9.28), "R": (8.76, 9.85)}      # 642.5 side / 642.0 side
WIN_LF = [(12.31, 13.40), (13.70, 15.06), (15.36, 16.70), (17.00, 18.34), (18.64, 19.74)]
PILLAR_GROW = 0.05            # widen the ~0.3 m pillars a little (0.52 m per px)
BAND_HF = (M_CAB, 10.20)
BAND_LF = (11.99, 19.94)
DOOR = (10.33, 11.81)
BOGIE_C = 4.65                # powered bogie centre
CUT_F = (2.9, 6.1)            # body cut-out round the powered bogie
CUT_J = 18.5                  # cut-out start round the Jakobs bogie
AC = [(5.40, 8.20), (13.94, 16.84)]
EXHAUST = (5.00, 5.25)

# ------------------------------------------------------------------ colours
WS = (0x33, 0x42, 0x4F)       # windscreen / cab side window: plain, never lit
WS_HI = (0x58, 0x6E, 0x80)
WS_MID = (0x45, 0x58, 0x69)   # cab side window, lower part (lighter than the band)
BOGIE = Paint(0x2A2B2D)
BOGIE_HI = Paint(0x46494C)
HUB = Paint(0x6E7276)
BELLOWS = Paint(0x2C2E31, top=0x3A3C40)
WHITE = Paint(0xF2F4F5)


def livery(name):
    if name == "arrivamodra":
        body = Paint(0x16A3CB)
        anth = Paint(0x323940, top=0x3E454D)
        return dict(
            body=body, band=Paint(0x333F4A), hood=anth,
            roof=Paint(0x323940, top=0x4A5159), roofedge=Paint(0x16A3CB, top=0x1896BB),
            skirt=Paint(0x24272A), sill=None, plough=Paint(0xA8CE2C, top=0xB4D83A),
            recess=Paint(0x1E2124), cheek=body, numband=body,
            lampband=Paint(0x1C1F23), dest=Paint(0x1C1F23),
            door=Paint(0xB7BFC5), doorsplit=Paint(0x565D64),
            stripe=(Paint(0x8FD4EC), WHITE), logo=WHITE, logo_front=(0xF4, 0xF6, 0xF7),
            roofbox=Paint(0x565E66, top=0x69717A), exhaust=Paint(0x2A2D30, top=0x1C1E20),
            crystals=False)
    if name == "crystalvalley":
        c = livery("arrivamodra")
        c.update(stripe=None, logo=None, door=Paint(0xEEF2F4), doorsplit=Paint(0x7E8C96),
                 crystals=True)
        return c
    if name == "dbcervena":
        body = Paint(0xD8241C)
        grey = Paint(0xA4AAAE, top=0xAEB4B8)
        return dict(
            body=body, band=Paint(0x3A3F44), hood=grey,
            roof=grey, roofedge=Paint(0xA4AAAE, top=0xA0A6AA),
            skirt=Paint(0x3C4044), sill=Paint(0xD4D8D6), plough=Paint(0x3C4044),
            recess=Paint(0x2A2D30), cheek=body, numband=Paint(0xC4C8C6),
            lampband=Paint(0x1C1F23), dest=Paint(0x1C1F23),
            door=Paint(0xC4C9CB), doorsplit=Paint(0x50565C),
            stripe=None, logo=WHITE, logo_front=(0xF4, 0xF6, 0xF7),
            roofbox=Paint(0x8C9296, top=0x9AA0A4), exhaust=Paint(0x2A2D30, top=0x1C1E20),
            crystals=False)
    raise ValueError(name)


# ------------------------------------------------------------------ cab geometry
# front surface (body-nose metres) vs height (px), from the datasheet side view
_NOSE = [(0.70, 0.30), (1.25, 0.24), (1.90, 0.06), (2.44, 0.03), (2.46, 0.22), (3.29, 0.20),
         (3.31, 0.12), (4.80, 0.27), (5.33, 0.40), (6.67, 0.72), (8.00, 1.23),
         (8.90, 1.76), (9.33, 2.19), (9.75, 3.05)]
_NZ = [a for a, b in _NOSE]
_NM = [b for a, b in _NOSE]


def nose_m(z):
    return float(np.interp(z, _NZ, _NM))


def front_hw(z):
    """Cab front leans in towards the roof (rounded head-on outline)."""
    if z < 5.3:
        return W
    return W * (1 - 0.13 * min(1.0, (z - 5.3) / (ZR - 5.3)) ** 1.4)


def plan_hw(z, d):
    """Half width of the rounded nose d metres behind the local front surface."""
    if z < Z_SK:
        tab = [(0.0, 0.58), (0.15, 0.76), (0.35, 0.9), (0.7, 1.0)]
    else:
        tab = [(0.0, 0.80), (0.12, 0.89), (0.3, 0.95), (0.6, 1.0)]
    r = float(np.interp(d, [a for a, b in tab], [b for a, b in tab]))
    return r * front_hw(z)


# side livery lines of the cab (metres, from the datasheet + photos)
# front edge of the body-colour swoosh = rear edge of the windscreen / hood wrap
_SWF = [(1.45, 0.40), (2.0, 0.72), (2.5, 0.96), (3.0, 1.47), (3.2, 1.90), (3.35, 2.50), (3.50, 3.40)]
# rear edge of the swoosh = front edge of the dark cab-window region
_SWR = [(1.95, 1.19), (2.61, 1.80), (2.94, 2.34), (3.08, 2.87), (3.14, 3.40)]


def sw_front(zm):
    return float(np.interp(zm, [a for a, b in _SWF], [b for a, b in _SWF]))


def sw_rear(zm):
    return float(np.interp(zm, [a for a, b in _SWR], [b for a, b in _SWR]))


# ------------------------------------------------------------------ Crystal Valley wrap
# (car-local m, z px): cut-glass gems (flat top, crown, pointed pavilion);
# centre and half extents
CRYSTALS = [((1.85, 3.80), (1.15, 1.50)),     # lower cab side
            ((9.15, 4.70), (1.05, 2.70)),     # before the door
            ((13.25, 5.90), (0.95, 2.30)),    # behind the door
            ((16.45, 5.70), (1.10, 2.40)),    # low-floor window band
            ((19.35, 5.40), (0.62, 2.30))]    # at the joint
CR_WHITE = (0xF2, 0xFA, 0xFD)
CR_PALE = (0xA4, 0xDF, 0xF1)
CR_MID = (0x5C, 0xBE, 0xE0)


def crystal(m, z):
    for (cm, cz), (hm, hz) in CRYSTALS:
        a, b = (m - cm) / hm, (z - cz) / hz
        if b > 1.0 or b < -1.0:
            continue
        if b >= 0.3:                                   # crown, tapering to the table
            if abs(a) > 1.0 - 0.45 * (b - 0.3) / 0.7:
                continue
            return CR_WHITE if a < 0.1 else CR_PALE
        if abs(a) > (b + 1.0) / 1.3:                   # pavilion down to the point
            continue
        return CR_PALE if a < -0.05 else CR_MID
    return None


def cv_text(m, z):
    """'CRYSTAL VALLEY' lettering behind the cab: two white text lines, each a
    full px tall (thinner rows vanish in the ne/sw views)."""
    if 5.45 <= m <= 8.0 and 3.9 <= z <= 4.95:                    # CRYSTAL
        return CR_WHITE if int((m - 5.45) / 0.29) % 4 != 3 else None
    if 5.75 <= m <= 7.75 and 2.8 <= z < 3.9:                     # VALLEY
        return CR_WHITE if int((m - 5.60) / 0.29) % 4 != 1 else None
    return None


# ------------------------------------------------------------------ the model
class Car:
    """One half-unit. s_nose = unit metres of its body nose; dirn = +1 if its
    body-nose metres grow towards the unit rear (car A), -1 for car B."""

    def __init__(self, liv, owner, s_nose, dirn, lamp):
        self.C = livery(liv)
        self.owner, self.s_nose, self.dirn, self.lamp = owner, s_nose, dirn, lamp

    def m_of(self, u):
        return self.dirn * (u * M - self.s_nose)

    def u_of(self, m):
        return (self.s_nose + self.dirn * m) / M

    def box(self, m0, m1, v0, v1, z0, z1, mat):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat, self.owner)

    def carside(self, face):
        return "L" if ((face == "-v") == (self.dirn == 1)) else "R"

    # ---- materials
    def front(self, vl, z, top=False):
        """top=True: the +z face of a nose slab (no lamps / lettering there)."""
        C = self.C
        av = abs(vl)
        if z < 1.2:
            return C["plough"]
        if z < Z_SK:
            return C["skirt"]
        if z < 3.9:                                     # lower front 0.92-1.46 m
            if av < 0.56:
                return C["recess"]
            if C["sill"] is not None and z < Z_SILL:
                return C["sill"]
            return C["cheek"]
        if z < 4.2:
            return C["numband"]
        if z < 5.35:                                    # lamp band behind glass
            if self.lamp is not None and 0.46 <= av <= 0.66 and 4.4 <= z <= 5.1:
                return self.lamp
            if not top and C["logo_front"] is not None and av < 0.30 and 4.5 <= z <= 5.0:
                if int((vl + 0.30) / 0.1) % 3 != 2:
                    return C["logo_front"]
            return C["lampband"]
        if z < 5.95:                                    # destination display
            return C["dest"]
        if z < 8.8:
            if av > front_hw(z) - 0.06:
                return WS
            return WS_HI if z > 8.2 else WS
        if not top and self.lamp is R.HEAD and av < 0.1 and 9.0 <= z <= 9.5:
            return R.HEAD                               # top marker light
        return C["hood"]

    def cab_side(self, m, z):
        C = self.C
        zm = z * PX
        if z >= ZS:
            return C["hood"]
        if zm >= 1.45 and m < sw_front(zm):             # wrap of the black front
            if zm >= 3.02:
                return C["hood"]
            if zm >= 2.22:
                return WS_HI if zm > 3.0 else WS
            if zm >= 1.58:
                if self.lamp is not None and 4.4 <= z <= 5.1 and m < nose_m(z) + 0.14:
                    return self.lamp                    # lamp seen round the corner
                return C["lampband"]
        if z < Z_SK:
            if z < 1.2 and m < 0.9:
                return C["plough"]
            return C["skirt"]
        if C["sill"] is not None and z < Z_SILL:
            return C["sill"]
        if C["crystals"]:
            cr = crystal(m, z)
            if cr is not None:
                return cr
        if z >= Z_HB0 and m >= sw_rear(zm):              # dark cab-window region
            if Z_HW0 <= z <= 7.75 and sw_rear(zm) + 0.2 <= m <= 2.72:
                return WS_HI if z > 6.9 else WS_MID     # cab side window
            return C["band"]
        return C["body"]

    def side(self, m, z, cs):
        C = self.C
        if m < M_CAB:
            return self.cab_side(m, z)
        zm = z * PX
        if z >= ZS:
            return C["hood"] if m < M_CAB + 0.05 else C["roofedge"]
        st = C["stripe"]
        # upper band (body colour) with the top of the stripe
        if z >= Z_B1:
            if st is not None and 4.55 <= m < 5.6:
                return st[0] if m < 5.1 else st[1]
            if C["crystals"]:
                cr = crystal(m, z)
                if cr is not None:
                    return cr
            return C["body"]
        # door
        if DOOR[0] <= m <= DOOR[1] and Z_D0 <= z <= Z_D1:
            t = (m - DOOR[0]) / (DOOR[1] - DOOR[0])
            if 0.45 <= t <= 0.55:
                return C["doorsplit"]
            if Z_DW0 <= z <= Z_DW1 and (0.12 <= t <= 0.40 or 0.60 <= t <= 0.88):
                return R.GLASS_HI if z > Z_DW1 - 0.5 else R.GLASS
            if t < 0.06 or t > 0.94:
                return C["doorsplit"]                   # leaf edges / frame
            return C["door"]
        if C["crystals"]:
            cr = crystal(m, z)
            if cr is not None:
                return cr
        # window bands
        hf = BAND_HF[0] <= m <= BAND_HF[1] and z >= Z_HB0
        lf = BAND_LF[0] <= m <= BAND_LF[1] and z >= Z_LB0
        if hf or lf:
            wins = WIN_HF + [WIN_HF4[cs]] if hf else WIN_LF
            w0 = Z_HW0 if hf else Z_LW0
            if w0 <= z <= Z_W1:
                for (a, b) in wins:
                    if a + PILLAR_GROW <= m <= b - PILLAR_GROW:
                        return R.GLASS_HI if z > Z_W1 - 0.55 else R.GLASS
            return C["band"]
        if z < Z_SK:
            return C["skirt"]
        if C["sill"] is not None and z < Z_SILL:
            return C["sill"]
        if st is not None:
            s = m - 0.75 * (zm - 0.95)
            if 3.35 <= s < 4.1:
                return st[0]
            if 4.1 <= s < 4.7:
                return st[1]
        if C["logo"] is not None and 6.0 <= m <= 7.75 and 3.5 <= z <= 4.6:
            x = (m - 6.0) / 1.75
            if x < 0.16:                                 # the Arriva "a" emblem
                return C["logo"]
            if z >= 3.9 and int((x - 0.16) * 12) % 2 == 0:
                return C["logo"]                         # "arriva"
        if C["crystals"]:
            t = cv_text(m, z)
            if t is not None:
                return t
        return C["body"]

    def mat(self, f, u, v, z, d):
        m = self.m_of(u)
        vl = v * self.dirn
        if f == "+z":
            if m < M_CAB and z < ZR - 0.05:
                return self.front(vl, z, top=True)
            if z < ZS - 0.05:
                return self.C["skirt"] if z < Z_SK + 0.05 else self.C["body"]
            if m < M_CAB - 0.05:
                return self.C["hood"]
            if abs(v) > W - CAPIN - 0.12:
                return self.C["roofedge"]
            return self.C["roof"]
        if f in ("+v", "-v"):
            return self.side(m, z, self.carside(f))
        if m < M_CAB:
            return self.front(vl, z)
        # inner end at the joint
        if z >= Z_B1:
            return self.C["body"]
        if z >= Z_LB0:
            return self.C["band"]
        return self.C["skirt"] if z < Z_SK else self.C["body"]

    # ---- geometry
    def parts(self):
        P = []
        mat = self.mat
        # body over the bogies / low skirt between the cut-outs
        P.append(self.box(M_CAB, BODY_END, -W, W, Z_BB, ZS, mat))
        P.append(self.box(CUT_F[1], CUT_J, -W, W, Z_SKB, Z_BB + 0.01, mat))
        # roof cap
        P.append(self.box(M_CAB - 0.05, BODY_END - 0.03, -W + CAPIN, W - CAPIN, ZS, ZR, mat))
        # cab head: stacked slabs, rounded in plan
        zs = list(np.arange(Z_SKB, Z_SK, 0.34)) + [Z_SK] + list(np.arange(Z_SK + 0.3, 4.8, 0.36)) + \
            list(np.arange(4.8, ZR - 0.01, 0.27))
        zs = sorted(set(round(x, 3) for x in zs))
        dsteps = [0.0, 0.06, 0.12, 0.2, 0.3, 0.45, 0.6, 99.0]
        for i, z0 in enumerate(zs):
            z1 = zs[i + 1] if i + 1 < len(zs) else ZR
            zc = (z0 + z1) / 2
            mf = nose_m(zc)
            end = CUT_F[0] if z1 <= Z_BB + 0.01 else M_CAB
            if mf >= end:
                continue
            for k in range(len(dsteps) - 1):
                a, b = mf + dsteps[k], min(end, mf + dsteps[k + 1])
                if a >= b:
                    break
                hh = plan_hw(zc, (dsteps[k] + min(dsteps[k + 1], 3.0)) / 2)
                if z0 >= ZS - 0.01:
                    hh = min(hh, W - CAPIN)
                P.append(self.box(a, b, -hh, hh, z0, z1, mat))
        return P

    def roof_parts(self):
        C = self.C
        P = []
        for (a, b) in AC:
            P.append(self.box(a, b, -0.56, 0.56, ZR - 0.05, ZR + 0.7, lambda *x: C["roofbox"]))
        e0, e1 = EXHAUST
        vv = (-0.42, -0.22) if self.dirn == 1 else (0.22, 0.42)
        P.append(self.box(e0, e1, vv[0], vv[1], ZR - 0.05, ZR + 1.15, lambda *x: C["exhaust"]))
        return P

    def under_parts(self):
        # wheelsets: powered bogie 1.9 m wheelbase, Jakobs bogie 2.65 m
        axles = [BOGIE_C - 0.95, BOGIE_C + 0.95, J - 1.325]

        def bm(f, u, v, z, d):
            if f in ("+v", "-v"):
                m = self.m_of(u)
                if 0.45 < z < 1.25 and any(abs(m - a) < 0.2 for a in axles):
                    return HUB                          # axle box / wheel hub
                if 1.25 <= z < 1.8:
                    return BOGIE_HI                     # bogie frame
            return BOGIE
        return [self.box(BOGIE_C - 1.30, BOGIE_C + 1.30, -W + 0.12, W - 0.12, 0.0, Z_BB + 0.02, bm),
                # Jakobs bogie: each car draws its own half
                self.box(J - 1.55, J, -W + 0.12, W - 0.12, 0.0, Z_BB + 0.02, bm)]


def unit(liv):
    A = Car(liv, "A", OFF, +1, R.HEAD)
    B = Car(liv, "B", L_UNIT - OFF, -1, R.TAIL)
    parts = []
    for c in (A, B):
        parts += c.parts() + c.roof_parts() + c.under_parts()
    # bellows between the body ends (drawn with car A)
    ua, ub = A.u_of(BODY_END - 0.02), B.u_of(BODY_END - 0.02)
    parts.append(Part(min(ua, ub), max(ua, ub), -W + 0.1, W - 0.1, 1.7, ZS + 0.2,
                      lambda f, u, v, z, d: BELLOWS if f != "+z" else Paint(0x3A3C40), "A"))
    return parts, [], [("A", 0.0), ("B", 10.0)]


def rows_for(liv):
    parts, lines, cars = unit(liv)
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]


LIVERIES = ["arrivamodra", "crystalvalley", "dbcervena"]
