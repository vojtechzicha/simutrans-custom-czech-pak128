#!/usr/bin/env python3
"""DB class 612 "RegioSwinger" (Adtranz / Bombardier, 1998-2003): tilting 2-car
diesel multiple unit of DB Regio, drawn from scratch with the pak128 box
raycaster (render.py + railkit.py), structure after desiro.py / db628.py.

    python tools/railrender/db612.py [--preview DIR]

writes vehicle-rail/db-regio/612/sprites/dbcervena.png.

  row 0  "612"   car A (612 0xx), cab at its FRONT end, headlights, leads
  row 1  "612.5" car B (612 5xx), cab at its REAR end, tail lights
  each car 25.875 m over couplers -> length 13 cu (M = 51.75 / 26 = 1.99 m/cu)

Real vehicle (de.wikipedia DB-Baureihe 612 (1998); photos of 612 977 at Cheb
2022, 612 980 at Burgkunstadt 2024 and aerial views, 612 553 / 078 / 144, Tillig /
Commons): 51 750 mm over couplers, 2 852 mm wide, 4 124 mm high over the roof
units, floor 1 290 mm (high floor, steps), 2'B' + B'2', wheels 890 mm, bogie
wheelbase 2 450 mm, 2 x 563 kW, 160 km/h, tilting body (8 degrees) with the
sides leaning in above the waist and a narrow roof; GRP cab front; two
single-leaf plug doors per car side, one behind the first two windows at the cab
end and one at the inner end next to the short-coupled joint.
Side layout (car-local metres from the car's own coupler face) measured on the
near-broadside 612 at Cheb (Aug 2022) by the perspective of the constant body
height (screen scale along the car ~ (apparent height)^2) and on 612 980:
windows 1.25 m wide, 2.30-3.15 m high; car A 7 saloon windows (pitch 1.90), car B
6 windows (pitch 1.86) + the wide multi-purpose window by its inner door.
Heights: body side bottom 0.90 m, light-grey band to 1.28 m, white cantrail line
3.38-3.64 m, roof 3.94 m, cooling unit behind the cab to 4.12 m.

Model units: s = unit metres from car A's front coupler face, u = s / M,
v = lateral cu (+v = right-hand side in the travel direction), z = model px
(1 px = 0.375 m). Car B is car A turned 180 degrees.
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

PX = 0.375
L_CAR = 25.875
L_UNIT = 2 * L_CAR
M = L_UNIT / 26.0                    # metres per carunit
W = R.W_STD * 2.852 / 2.825          # 0.929 cu half width at the waist
TAPER = 0.075                        # the side leans in by this much (cu) up to the cantrail
CAPIN = 0.30                         # narrow roof of the tilting profile


def zp(metres):
    return metres / PX


# ------------------------------------------------------------------ heights (px)
Z_BOT = 2.4          # body side bottom (0.90 m)
Z_GREY = 3.4         # top of the light-grey band (1.28 m)
Z_WAIST = 5.8        # the side starts leaning in above here (2.18 m)
Z_G0, Z_G1 = 6.1, 8.45       # passenger window glass (2.29 - 3.17 m)
Z_WHITE = 9.0        # white cantrail line from here to the side wall top
ZS = 9.7             # side wall top (3.64 m)
ZR = 10.5            # roof (3.94 m)
Z_D0, Z_D1 = 1.6, 9.0        # door leaves: from the step (0.60 m) to the white line
Z_DW0, Z_DW1 = 5.7, 8.3      # door windows
Z_CW0, Z_CW1 = 6.0, 8.95     # cab side window

# ------------------------------------------------------------------ layout (car-local m)
M_CAB = 3.35                 # GRP cab head -> steel body
BODY_END = 25.52             # inner body end (bellows to the joint at 25.875)
CABWIN_END = 2.95
FRONT_WINS = [(3.55, 4.75), (5.15, 6.35)]
DOORS = [(6.85, 7.80), (24.20, 25.15)]
LAYOUT = {
    "A": dict(wins=[(8.40 + k * 1.90, 9.65 + k * 1.90) for k in range(7)],
              regio=(17.55, 19.25), bike=None),
    "B": dict(wins=[(9.15 + k * 1.86, 10.40 + k * 1.86) for k in range(6)] + [(21.85, 23.10)],
              regio=(11.70, 13.40), bike=(22.00, 22.85)),
}
BOGIES = [4.90, 22.70]
COOLER = (3.60, 7.40)        # radiator / fan unit on the roof behind the cab

# ------------------------------------------------------------------ colours
RED = Paint(0xD8241C)
GREY = Paint(0xD4D8D6, top=0xC8CCCA)        # DB lichtgrau lower band
WHITE = Paint(0xE9ECEB)
ROOF = Paint(0x62686C, top=0x6A7074)
ROOF_RED = Paint(0xD8241C, top=0xB82019)    # shoulder seen from above
MASK = Paint(0x2C3136, top=0x3A4046)        # black-grey front mask
MASK_TOP = Paint(0x60666B, top=0x6C7277)    # dark grey roof front above the mask
DOOR = Paint(0xD0D4D6)
DOOR_EDGE = Paint(0x4A4F54)
LAMP_HOUSING = Paint(0x3A3E42)
LAMP_OFF = (0x6A, 0x6E, 0x72)
BLACK = Paint(0x1C1E20)
SKIRT = Paint(0x3A3E42, top=0x33363A)
PLOUGH = Paint(0x46494D)
BOGIE = Paint(0x2A2B2D)
BOGIE_HI = Paint(0x4A4D50)
HUB = Paint(0x6E7276)
UNDER = Paint(0x3C4044)
UNDER_HI = Paint(0x5A5E62)
BELLOWS = Paint(0x2B2D30, top=0x3A3C40)
COOLER_C = Paint(0x4A4F54, top=0x565C62)
FAN = Paint(0x2E3236, top=0x2E3236)
DB_LOGO = (0xE0, 0x22, 0x1A)
WS = (0x2E, 0x3E, 0x4C)
WS_HI = (0x5A, 0x72, 0x87)


# ------------------------------------------------------------------ cab geometry
# front surface (m behind the coupler face) vs height (px), from photos
_NOSE = [(0.8, 0.62), (1.6, 0.50), (2.4, 0.45), (3.4, 0.45), (5.6, 0.60),
         (8.9, 1.55), (9.5, 1.98), (10.0, 2.50), (10.3, 2.95), (10.5, 3.35)]


def nose_m(z):
    return float(np.interp(z, [a for a, b in _NOSE], [b for a, b in _NOSE]))


def side_hw(z):
    """Half width of the body side: vertical to the waist, then leaning in."""
    if z <= Z_WAIST:
        return W
    return W - TAPER * min(1.0, (z - Z_WAIST) / (ZS - Z_WAIST))


def front_hw(z):
    """The cab front narrows towards the roof more than the body side."""
    if z <= Z_WAIST:
        return W
    return side_hw(z) - 0.10 * min(1.0, (z - Z_WAIST) / (ZR - Z_WAIST)) ** 1.3


def plan_hw(z, d):
    """Half width of the rounded nose d metres behind the local front surface."""
    tab = [(0.0, 0.80), (0.12, 0.88), (0.30, 0.95), (0.60, 1.0)]
    r = float(np.interp(d, [a for a, b in tab], [b for a, b in tab]))
    return r * front_hw(z)


# ------------------------------------------------------------------ the model
class Car:
    """One car. s_cab = unit metres of its coupler face; dirn = +1 if car-local m
    grows towards the unit rear (car A), -1 for car B (turned)."""

    def __init__(self, key, owner, s_cab, dirn, lamp):
        self.key, self.owner, self.s_cab, self.dirn, self.lamp = key, owner, s_cab, dirn, lamp
        self.lay = LAYOUT[key]

    def m_of(self, u):
        return self.dirn * (u * M - self.s_cab)

    def u_of(self, m):
        return (self.s_cab + self.dirn * m) / M

    def box(self, m0, m1, v0, v1, z0, z1, mat, owner=None):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat, owner or self.owner)

    def carside(self, face):
        """'R' / 'L' = the car's own right / left side (cab = front)."""
        return "R" if ((face == "+v") == (self.dirn == 1)) else "L"

    # ---- materials
    def side(self, m, z, cs):
        lay = self.lay
        if z >= ZS:
            return RED                                  # red shoulder up to the roof
        if m < M_CAB:
            return self.cab_side(m, z)
        # doors: light-grey single leaves with a dark edge and a narrow lit window
        for (a, b) in DOORS:
            if a <= m <= b and Z_D0 <= z <= Z_D1:
                t = (m - a) / (b - a)
                if t < 0.10 or t > 0.90 or z > Z_D1 - 0.3:
                    return DOOR_EDGE
                if Z_DW0 <= z <= Z_DW1 and 0.28 <= t <= 0.72:
                    return R.GLASS_HI if z > Z_DW1 - 0.5 else R.GLASS
                return DOOR
        # white cantrail line (the old yellow side displays are gone: 612 977 at Cheb)
        if z >= Z_WHITE:
            return WHITE
        # windows
        if Z_G0 <= z <= Z_G1:
            for (a, b) in FRONT_WINS + lay["wins"]:
                if a <= m <= b:
                    return R.GLASS_HI if z > Z_G1 - 0.55 else R.GLASS
        if z < Z_GREY:
            return GREY
        # white lettering: "REGIO DB" below the windows, bike pictogram on car B
        a, b = lay["regio"]
        if a <= m <= b and 4.6 <= z <= 5.3:
            x = (m - a) / (b - a)
            if cs == "R":
                x = 1 - x                                # reads left to right
            if x < 0.68 and int(x * 9) % 2 == 0 or x > 0.78:
                return WHITE
        if lay["bike"] is not None:
            a, b = lay["bike"]
            if a <= m <= b and 3.9 <= z <= 5.0:
                x = (m - a) / (b - a)
                if x < 0.3 or x > 0.7 or z > 4.7:
                    return WHITE
        return RED

    def cab_side(self, m, z):
        nm = nose_m(z)
        if z < Z_BOT:
            return PLOUGH if z < 1.6 else SKIRT
        if z < Z_GREY:
            return GREY
        # the black front mask wraps just round the corner
        if 5.6 <= z and m < nm + 0.25:
            return MASK if z < 9.3 else MASK_TOP
        # lamp housing seen round the corner
        if 4.1 <= z <= 5.0 and m < nm + 0.18:
            if self.lamp is R.TAIL:
                return R.TAIL
            return LAMP_HOUSING
        # big cab side window with a slanted front edge along the windscreen
        if Z_CW0 <= z <= Z_CW1 and nm + 0.55 <= m <= CABWIN_END:
            return WS_HI if z > Z_CW1 - 0.9 else WS
        return RED

    def front(self, vl, z, top=False):
        av = abs(vl)
        hw = front_hw(z)
        if z < 1.6:
            return PLOUGH
        if z < Z_BOT:
            return SKIRT
        if z < 3.9 and av < 0.52:
            return BLACK                                 # coupler recess
        if z < Z_GREY:
            return GREY
        if z < 5.6:
            # two oval lamp housings: headlight inside, tail light outside
            # (lamps drawn a little larger than real so they read at 1x)
            if 4.05 <= z <= 5.05 and 0.32 <= av <= 0.82:
                if 0.36 <= av <= 0.57:
                    return R.HEAD if self.lamp is R.HEAD else LAMP_OFF
                if 0.59 <= av <= 0.80:
                    return R.TAIL if self.lamp is R.TAIL else LAMP_OFF
                return LAMP_HOUSING
            if av < 0.22 and 4.2 <= z <= 5.1:            # DB logo: red box, white rim
                return DB_LOGO if (av < 0.13 and 4.4 <= z <= 4.9) else (0xF2, 0xF4, 0xF4)
            return RED
        if z < 8.9:
            if self.lamp is R.HEAD and av < 0.12 and 5.6 <= z <= 6.15:
                return R.HEAD                            # upper headlight under the windscreen
            if av < hw - 0.12 and 6.1 <= z <= 8.7:
                return WS_HI if z > 7.9 else WS
            return MASK
        if av < 0.22 and z < 9.9:
            return BLACK                                 # camera / marker box on top
        return MASK if z < 9.3 else MASK_TOP

    def mat(self, f, u, v, z, d):
        m = self.m_of(u)
        vl = v * self.dirn
        if f == "+z":
            if m < M_CAB and z < ZR - 0.05:
                if z >= ZS - 0.05:
                    return MASK_TOP if m < nose_m(z) + 0.6 else RED
                return self.front(vl, z, top=True)
            if z < ZS - 0.05:
                # tops of the leaning-in wall steps (seen in the nw/se views): plain
                # body colour, so the long edges read as a clean red line
                if m >= M_CAB and z >= Z_WHITE:
                    return WHITE
                return GREY if z < Z_GREY else RED
            if z < ZR - 0.05:
                return ROOF_RED                          # ledge outside the narrow roof
            if m < M_CAB + 0.2:
                return MASK_TOP
            return ROOF
        if f in ("+v", "-v"):
            return self.side(m, z, self.carside(f))
        facing_cab = (f == "-u") == (self.dirn == 1)
        if m < M_CAB and facing_cab:
            return self.front(vl, z)
        if m < M_CAB:
            return self.front(vl, z)
        # inner end at the joint
        if z >= ZS:
            return RED
        return GREY if z < Z_GREY else RED

    # ---- geometry
    def parts(self):
        P = []
        mat = self.mat
        # body: vertical lower wall, then leaning-in slabs up to the cantrail
        P.append(self.box(M_CAB, BODY_END, -W, W, Z_BOT, Z_WAIST + 0.01, mat))
        zs = list(np.arange(Z_WAIST, ZS - 0.01, 0.5)) + [ZS]
        for i in range(len(zs) - 1):
            z0, z1 = zs[i], zs[i + 1]
            hw = side_hw((z0 + z1) / 2)
            P.append(self.box(M_CAB, BODY_END, -hw, hw, z0, z1 + 0.01, mat))
        # narrow roof cap
        P.append(self.box(M_CAB - 0.05, BODY_END - 0.05, -W + CAPIN, W - CAPIN, ZS, ZR, mat))
        # door leaves reach below the body (step wells)
        for (a, b) in DOORS:
            P.append(self.box(a, b, -W, -W + 0.12, Z_D0, Z_BOT + 0.01, mat))
            P.append(self.box(a, b, W - 0.12, W, Z_D0, Z_BOT + 0.01, mat))
        # cab head: stacked slabs, rounded in plan
        zs = list(np.arange(0.9, Z_GREY, 0.5)) + [Z_GREY] + list(np.arange(Z_GREY + 0.4, 5.6, 0.44)) + \
            list(np.arange(5.6, ZR - 0.01, 0.3))
        zs = sorted(set(round(x, 3) for x in zs))
        dsteps = [0.0, 0.06, 0.12, 0.2, 0.3, 0.45, 0.6, 99.0]
        for i, z0 in enumerate(zs):
            z1 = zs[i + 1] if i + 1 < len(zs) else ZR
            zc = (z0 + z1) / 2
            mf = nose_m(zc)
            end = M_CAB
            if z1 <= Z_BOT + 0.01:
                end = BOGIES[0] - 1.75                   # valance ends before the bogie
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
        P = []
        a, b = COOLER

        def cool(f, u, v, z, d):
            if f == "+z":
                mm = self.m_of(u)
                if abs(v) < 0.42 and (mm - a) % 1.25 > 0.35:
                    return FAN                           # fan openings
            return COOLER_C
        P.append(self.box(a, b, -0.66, 0.66, ZR - 0.05, zp(4.12), cool))
        for c in (10.5, 16.0, 21.5):                     # small antennas / vents
            P.append(self.box(c - 0.2, c + 0.2, -0.15, 0.15, ZR - 0.05, ZR + 0.45, lambda *x: BLACK))
        return P

    def under_parts(self):
        P = []
        for bc in BOGIES:
            axles = [bc - 1.225, bc + 1.225]

            def bm(f, u, v, z, d, axles=axles):
                if f in ("+v", "-v"):
                    mm = self.m_of(u)
                    if 0.5 < z < 1.5 and any(abs(mm - x) < 0.22 for x in axles):
                        return HUB
                    if 1.5 <= z < 2.1:
                        return BOGIE_HI
                return BOGIE
            P.append(self.box(bc - 1.65, bc + 1.65, -W + 0.12, W - 0.12, 0.0, Z_BOT + 0.02, bm))
        # engine, gearbox, tanks between the bogies
        P.append(self.box(BOGIES[0] + 1.9, BOGIES[1] - 1.9, -W + 0.24, W - 0.24, 0.8, Z_BOT,
                          lambda f, u, v, z, d: UNDER_HI if (f in ("+v", "-v") and z > 1.9) else UNDER))
        return P


def unit():
    A = Car("A", "A", 0.0, +1, R.HEAD)
    B = Car("B", "B", L_UNIT, -1, R.TAIL)
    parts = []
    for c in (A, B):
        parts += c.parts() + c.roof_parts() + c.under_parts()
    # bellows between the body ends (drawn by car A)
    ua, ub = A.u_of(BODY_END - 0.03), B.u_of(BODY_END - 0.03)
    parts.append(Part(min(ua, ub), max(ua, ub), -W + 0.14, W - 0.14, Z_BOT, ZS + 0.3,
                      lambda f, u, v, z, d: BELLOWS if f != "+z" else Paint(0x3A3C40), "A"))
    return parts, [], [("A", 0.0), ("B", 13.0)]


def rows_for():
    parts, lines, cars = unit()
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        os.makedirs(prev, exist_ok=True)
    rows = rows_for()
    out = os.path.join(REPO, "vehicle-rail", "db-regio", "612", "sprites", "dbcervena.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    R.save_rows(rows, out)
    if prev:
        R.preview(rows, os.path.join(prev, "612_dbcervena.png"), z=4, labels=["612", "612.5"])
    print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
