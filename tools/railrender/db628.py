"""Arriva vlaky class 845 + 945 (ex-DB 628.2 + 928.2, Duewag / Waggon Union /
LHB / MBB 1986-89, modernised at Pars nova Sumperk), drawn from scratch with
the pak128 box raycaster (render.py + railkit.py), structure after lint.py.

  row 0  "845"  motor car, cab at its FRONT (outer) end, headlights, leads
  row 1  "945"  driving trailer, cab at its REAR (outer) end, tail lights
  each car 22.7 m over buffers -> length 11 cu (M = 22.7/11 = 2.064 m/cu)

Real body (DB 628.2 technical data, nahverkehr-franken.de/rbahn/628-techdat;
photos of the Arriva units on Commons "CZ Class 845 of
Arriva vlaky", "DB Class 628.2"): 22,700 mm over buffers per car, body 21,940
mm, 2,850 mm wide, side wall top ~3.72 m, roof ~4.05 m, floor 1,210 mm, bogie
pivots 15,100 mm, bogie wheelbase 1,900 mm, wheels 770 mm.
Side layout (metres from the car's cab buffer face, measured on the broadside
945.205 at Kacice, 12/2019, 66 px/m, cross-checked on 845.104 / 845.301 /
945.107 / 845.317): cab side window 0.95-1.72, single-leaf cab door 1.90-2.82
(both sides), vestibule window 3.75-4.90, 8 saloon windows from 6.70 at a
1.72 m pitch (1.20 m wide), inner end: a single-leaf door 20.55-21.45 on the
car's own LEFT side only (the unit is 180-degree symmetric, so the doors
alternate between the sides of the unit), a narrow toilet window on the right.
Window band 1.98-3.17 m, glass 2.02-3.08 m.

Model units: s = unit metres from the 845's front buffer face, u = s / M,
v = lateral cu (+v = right-hand side in the travel direction), z = model px
(1 px = 0.375 m).  Car-local m = metres from that car's own cab buffer face
(the 945 is the 845 turned 180 degrees).

Regenerate with `python tools/railrender/arriva.py 845`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS

LIVERIES = ["arrivamodra", "tyrkysovokremova", "dbcervena"]

PX = 0.375                          # metres per model px (z)
L_CAR = 22.7                        # metres over buffers per car
M = L_CAR / 11.0                    # metres per carunit
W = R.W_STD * 2.85 / 2.825          # 0.928 cu half width
CAPIN = 0.2


def zp(metres):
    return metres / PX


# heights (model px)
Z_BOT = zp(0.78)          # body side bottom (sole bar)
Z_DOORBOT = zp(0.58)      # door leaves (with the step well) reach down to here
Z_B0, Z_B1 = zp(1.98), zp(3.17)     # window band
Z_G0, Z_G1 = zp(1.99), zp(3.12)     # passenger window glass
Z_DT = zp(3.30)           # door top
Z_DW0, Z_DW1 = zp(2.05), zp(3.02)   # door window
ZS = zp(3.72)             # side wall top
ZR = 10.8                 # roof crown (4.05 m)
Z_MASK0 = zp(1.90)        # front: dark mask from here up
Z_WS0, Z_WS1 = zp(2.20), zp(3.40)   # windscreen
Z_LAMP0, Z_LAMP1 = zp(1.40), zp(1.86)   # lamps drawn a bit taller (visibility)
Z_LOW = zp(1.36)          # DB: top of the light-grey lower band

# layout (car-local metres from the cab buffer face)
FRONT_M = 0.47            # lower cab front
M_CAB = 1.85              # the straight body starts here
BODY_END = 22.32          # inner end of the body (joint plane at 22.7)
CABWIN = (0.98, 1.72)
CABDOOR = (1.90, 2.82)
VESTWIN = (3.75, 4.90)
WINDOWS = [(6.70 + k * 1.72, 7.90 + k * 1.72) for k in range(8)]
INNERDOOR = (20.55, 21.45)          # car's own LEFT side only
TOILETWIN = (20.45, 21.05)          # car's own RIGHT side
BOGIES = (3.85, 18.95)

WS = (0x2E, 0x3E, 0x4C)             # windscreen / cab side window (never lit)
WS_HI = (0x5A, 0x72, 0x87)          # upper part: sky reflection
BLACK = Paint(0x1D1F21)
BOGIE = Paint(0x2A2B2D)
BOGIE_HI = Paint(0x4A4D50)
UNDER = Paint(0x35383B)
BELLOWS = Paint(0x2B2D30, top=0x3A3C40)
AC = Paint(0xC2C6C9, top=0xD3D6D8)
AC_GRILLE = Paint(0x5E6368)
EXHAUST = Paint(0x3E4145, top=0x2A2C2F)


# ------------------------------------------------------------------ liveries
def livery(name):
    """Colour table + flags of a livery; geometry never depends on it."""
    if name == "arrivamodra":
        # Arriva Blue (2019-): sky blue body, individual windows on blue
        # pillars, anthracite panel round the window behind the cab door, cab
        # door and front mask, slanted white + pale-blue stripe behind the cab door,
        # lime skirt edge, white "arriva"; light-grey roof with AC boxes
        blue = Paint(0x2DA5D8)
        anth = Paint(0x3A4046)
        return dict(
            name=name, body=blue, band=Paint(0x464D54), door=anth, doorframe=anth,
            innerdoor=anth, word_z=(1.30, 1.66),
            roofside=blue, roof=Paint(0x2DA5D8, top=0xB0B6BB),
            mask=Paint(0x464C54), masktop=Paint(0x464C54, top=0x52585F),
            lowfront=blue, logo=(0xF3, 0xF5, 0xF6), letters=Paint(0xF2F4F5),
            stripe=Paint(0xF1F3F4), stripe2=Paint(0x90D0EC),
            beam=BLACK, skirt=Paint(0x3A3D40), skirtedge=Paint(0xC9DB3E),
            ac=True, lowband=None)
    if name == "tyrkysovokremova":
        # "Limetka" 2012-2019: turquoise body, lime cab + cab door, cream sweep
        # from the roof behind the cab down round the door, black mask, lime
        # lower front with a black wordmark, individually framed windows
        tq = Paint(0x14A7B8)
        lime = Paint(0xC7DA3B)
        return dict(
            name=name, body=tq, band=None, door=lime, doorframe=lime,
            innerdoor=tq, innerframe=Paint(0x0B5E68), word_z=(1.36, 1.72),
            cream=Paint(0xEEE8CF), lime=lime,
            roofside=tq, roof=Paint(0x14A7B8, top=0x8E9499),
            mask=Paint(0x2E3236), masktop=Paint(0x3A3E42, top=0x6C7175),
            lowfront=lime, logo=(0x1E, 0x20, 0x22), letters=Paint(0xF2F4F5),
            beam=BLACK, skirt=Paint(0x26282B), skirtedge=Paint(0xC7DA3B),
            ac=False, lowband=None)
    if name == "dbcervena":
        # DB Regio Verkehrsrot: red body, light-grey lower band, doors and roof
        # shoulder, grey front mask, dark-grey skirt; Arriva sticker mid-car
        red = Paint(0xD9272D)
        grey = Paint(0xCCD0CC)
        return dict(
            name=name, body=red, band=None, door=grey, doorframe=grey,
            innerdoor=grey, word_z=(1.50, 1.84),
            roofside=grey, roof=Paint(0xCCD0CC, top=0xA3A8AB),
            mask=Paint(0x6F7478), masktop=Paint(0x6F7478, top=0x80858A),
            lowfront=red, logo=(0xF4, 0xF4, 0xF4), letters=Paint(0xF2F4F5),
            beam=Paint(0x303336), skirt=Paint(0x4C5054), skirtedge=Paint(0x4C5054),
            ac=False, lowband=grey)
    raise ValueError(name)


# ------------------------------------------------------------------ cab nose profile
def nose_m(z):
    """Car-local m of the cab front surface at model height z."""
    zm = z * PX
    if zm < 1.90:
        return FRONT_M + max(0.0, zm - 0.78) * 0.06
    if zm < 3.40:
        return FRONT_M + 0.067 + (zm - 1.90) / 1.50 * 0.30
    if zm < 3.72:
        return FRONT_M + 0.367 + (zm - 3.40) / 0.32 * 0.18
    t = min(1.0, (zm - 3.72) / 0.33)
    return FRONT_M + 0.547 + 0.75 * t ** 1.6


def front_halfwidth(z):
    """Slight tumblehome of the cab front above the windscreen bottom."""
    if z < Z_WS0:
        return W
    return W - 0.07 * min(1.0, (z - Z_WS0) / (ZS - Z_WS0))


def word_hit(x, zz):
    """Lowercase wordmark as letter blocks: x 0..1 along it, zz 0..1 up."""
    k = int(x * 11)
    return x < 0.10 or k % 2 == 1 or zz > 0.62


# ------------------------------------------------------------------ the model
class Car:
    """One car. s_cab = unit metres of its cab buffer face; dirn = +1 if its
    car-local m grows towards the unit rear (845), -1 for the turned 945."""

    def __init__(self, liv, owner, s_cab, dirn, motor, lamp):
        self.C = livery(liv)
        self.owner, self.s_cab, self.dirn = owner, s_cab, dirn
        self.motor, self.lamp = motor, lamp

    def m_of(self, u):
        return self.dirn * (u * M - self.s_cab)

    def u_of(self, m):
        return (self.s_cab + self.dirn * m) / M

    def box(self, m0, m1, v0, v1, z0, z1, mat, owner=None):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat, owner or self.owner)

    def own_side(self, face):
        """'R' / 'L' = the car's own right / left side (cab = front)."""
        return "R" if ((face == "+v") == (self.dirn == 1)) else "L"

    # ---- materials
    def zone(self, m, z, cs):
        """Livery paint of the plain side wall (no openings)."""
        C = self.C
        zm = z * PX
        t = (zm - 0.78) / (3.72 - 0.78)
        nm = C["name"]
        if nm == "arrivamodra":
            # slanted stripe pair, top leaning back; pale blue on the cab side
            wa, wb = 4.14 + t * 1.01, 5.00 + t * 0.92
            pa = 3.38 + t * 1.17
            if wa <= m <= wb:
                return C["stripe"]
            if pa <= m < wa:
                return C["stripe2"]
            # anthracite panel only round the vestibule window, between the cab
            # door and the stripe; the saloon windows sit on blue pillars
            if Z_B0 <= z <= Z_B1 and CABDOOR[1] - 0.05 <= m < pa:
                return C["band"]
            return C["body"]
        if nm == "tyrkysovokremova":
            if m < CABDOOR[0]:
                # cab side: lime, cream wedge under the cab window
                zl = 0.95 + (m - FRONT_M) / (CABDOOR[0] - FRONT_M) * 1.05
                return C["lime"] if zm > zl else C["cream"]
            sweep = CABDOOR[1] + 0.22 + 1.35 * max(0.0, t) ** 2
            if m <= sweep or (z > Z_DT and m < CABDOOR[1]):
                return C["cream"]
            return C["body"]
        if nm == "dbcervena":
            if z <= Z_LOW:
                return C["lowband"]
            return C["body"]
        raise ValueError(nm)

    def side(self, m, z, cs):
        C = self.C
        if z >= ZS - 0.02:
            return C["roofside"]
        # doors (cab door both sides, inner door on the car's own left)
        doors = [(CABDOOR, C["door"], None)]
        if cs == "L":
            doors.append((INNERDOOR, C["innerdoor"], C.get("innerframe")))
        for ((a, b), leaf, frame) in doors:
            if a <= m <= b and z <= Z_DT:
                if a + 0.18 <= m <= b - 0.18 and Z_DW0 <= z <= Z_DW1:
                    return R.GLASS_HI if z > Z_DW1 - 0.5 else R.GLASS
                if frame is not None and (m < a + 0.2 or m > b - 0.2 or z > Z_DT - 0.35):
                    return frame                    # body-coloured leaf: dark gaps
                return leaf
        # driver's side window (plain dark, never lit)
        if CABWIN[0] <= m <= CABWIN[1] and zp(2.05) <= z <= zp(3.05):
            return WS_HI if z > zp(2.85) else WS
        # passenger windows
        wins = [VESTWIN] + WINDOWS + ([TOILETWIN] if cs == "R" else [])
        if Z_G0 <= z <= Z_G1:
            for (a, b) in wins:
                if a <= m <= b:
                    return R.GLASS_HI if z > Z_G1 - 0.55 else R.GLASS
        # side wordmark (white), mid-car below the windows
        wa, wb = 9.75, 12.05
        w0, w1 = zp(C["word_z"][0]), zp(C["word_z"][1])
        if wa <= m <= wb and w0 <= z <= w1:
            x = (m - wa) / (wb - wa)
            if cs == "R":
                x = 1 - x          # reads left to right on either side
            zz = (z - w0) / (w1 - w0)
            if word_hit(x, zz):
                return C["letters"]
        return self.zone(m, z, cs)

    def front(self, m, vl, z):
        """Cab front (vl = lateral in the car's own frame)."""
        C = self.C
        av = abs(vl)
        hw = front_halfwidth(z)
        if z < Z_MASK0:
            if C["lowband"] is not None and z <= Z_LOW:
                return C["lowband"]
            if Z_LAMP0 <= z <= Z_LAMP1 and 0.33 <= av <= 0.74:
                outer = av > 0.535
                if self.lamp is R.HEAD:
                    return R.HEAD
                if self.lamp is R.TAIL:
                    return R.TAIL if outer else (0x5A, 0x5E, 0x62)
            if zp(1.55) <= z <= zp(1.76) and av < 0.27:
                return C["logo"]
            return C["lowfront"]
        if av < hw - 0.10 and Z_WS0 <= z <= Z_WS1:
            return WS_HI if z > zp(3.12) else WS
        if self.lamp is R.HEAD and av < 0.085 and zp(1.98) <= z <= zp(2.14):
            return R.HEAD                                  # upper headlight
        return C["mask"]

    def mat(self, f, u, v, z, d):
        C = self.C
        m = self.m_of(u)
        vl = v * self.dirn
        if f == "+z":
            if m < M_CAB and z < ZR - 0.05:
                if z >= ZS - 0.05:
                    # rounded roof front: mask on the lower half, roof above
                    return C["masktop"] if z < ZS + 0.35 else C["roof"]
                return self.front(m, vl, z)        # tops of the raked-front slabs
            if z < ZS - 0.05:
                return self.zone(m, z, "R")
            if z < ZS + 0.05:
                return C["roofside"]          # ledge outside the roof cap (shoulder)
            return C["roof"]
        if f in ("+v", "-v"):
            return self.side(m, z, self.own_side(f))
        facing_cab = (f == "-u") == (self.dirn == 1)
        if m < M_CAB and facing_cab:
            if z >= ZS - 0.02:
                return C["masktop"]
            return self.front(m, vl, z)
        if m < M_CAB:
            return self.front(m, vl, z)
        return C["roofside"] if z > ZS else C["body"]

    # ---- geometry
    def parts(self):
        P = []
        mat = self.mat
        P.append(self.box(M_CAB, BODY_END, -W, W, Z_BOT, ZS, mat))
        P.append(self.box(M_CAB - 0.05, BODY_END - 0.06, -W + CAPIN, W - CAPIN, ZS, ZR, mat))
        # door leaves reach below the sole bar (step wells)
        for (a, b) in [CABDOOR]:
            P.append(self.box(a, b, -W, -W + 0.12, Z_DOORBOT, Z_BOT + 0.01, mat))
            P.append(self.box(a, b, W - 0.12, W, Z_DOORBOT, Z_BOT + 0.01, mat))
        a, b = INNERDOOR
        # own left side: -v for the 845 (dirn +1), +v for the 945
        if self.dirn == 1:
            P.append(self.box(a, b, -W, -W + 0.12, Z_DOORBOT, Z_BOT + 0.01, mat))
        else:
            P.append(self.box(a, b, W - 0.12, W, Z_DOORBOT, Z_BOT + 0.01, mat))
        # cab nose: stacked slabs, small rounded corners
        zs = list(np.arange(Z_BOT, Z_MASK0, 0.5)) + list(np.arange(Z_MASK0, ZR - 0.01, 0.3))
        for i, z0 in enumerate(zs):
            z1 = zs[i + 1] if i + 1 < len(zs) else ZR
            zc = (z0 + z1) / 2
            mf = nose_m(zc)
            if mf >= M_CAB:
                continue
            hw = front_halfwidth(zc)
            if z0 >= ZS - 0.01:
                hw = min(hw, W - CAPIN)
            for (d0, d1, cut) in ((0.0, 0.10, 0.12), (0.10, 0.24, 0.04), (0.24, 99, 0.0)):
                a0 = mf + d0
                b0 = min(M_CAB, mf + d1)
                if a0 >= b0:
                    continue
                P.append(self.box(a0, b0, -(hw - cut), hw - cut, z0, z1, mat))
        # buffer beam, buffers, skirt with its edge
        C = self.C
        P.append(self.box(0.24, 0.62, -(W - 0.06), W - 0.06, zp(0.86), zp(1.34),
                          lambda *a: C["beam"]))
        for sg in (-1, 1):
            P.append(self.box(0.0, 0.26, sg * 0.30, sg * 0.54, zp(0.90), zp(1.24),
                              lambda *a: BLACK))
        P.append(self.box(0.34, 0.95, -(W - 0.22), W - 0.22, zp(0.66), zp(0.86),
                          lambda *a: C["skirt"]))
        # the lime anti-climber / skirt edge: one full pixel row (visibility)
        P.append(self.box(0.30, 0.95, -(W - 0.24), W - 0.24, zp(0.28), zp(0.66),
                          lambda *a: C["skirtedge"]))
        return P

    def roof_parts(self):
        P = []
        if self.C["ac"]:
            # cab AC box above the cab + saloon AC box (845.1xx photos 2026)
            P.append(self.box(1.35, 2.95, -0.60, 0.60, ZR - 0.35, ZR + 0.72,
                              lambda f, u, v, z, d: AC_GRILLE if (f in ("-u", "+u") and z > ZR + 0.1) else AC))
            sal = (17.4, 20.4) if self.motor else (4.3, 7.3)
            P.append(self.box(sal[0], sal[1], -0.66, 0.66, ZR - 0.05, ZR + 1.15,
                              lambda f, u, v, z, d: AC_GRILLE if (f in ("+v", "-v") and ZR + 0.3 < z < ZR + 0.9
                                                                  and (self.m_of(u) - sal[0]) % 1.0 < 0.55) else AC))
        if self.motor:
            # engine exhaust above the vestibule (845.317 photo)
            P.append(self.box(4.55, 5.25, -0.34, 0.08, ZR - 0.05, ZR + 0.95, lambda *a: EXHAUST))
        return P

    def under_parts(self):
        P = []
        for bc in BOGIES:
            P.append(self.box(bc - 1.40, bc + 1.40, -W + 0.12, W - 0.12, 0.0, Z_BOT + 0.02,
                              lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.6) else BOGIE))
        if self.motor:
            # engine / transmission / tanks between the bogies
            P.append(self.box(6.4, 16.8, -W + 0.20, W - 0.20, 0.75, Z_BOT, lambda *a: UNDER))
        else:
            P.append(self.box(7.6, 14.6, -W + 0.28, W - 0.28, 1.00, Z_BOT, lambda *a: UNDER))
        return P


def unit(liv):
    """Parts, lines and the cars as (owner, u_front) of one 845 + 945 unit."""
    A = Car(liv, "A", 0.0, +1, True, R.HEAD)
    B = Car(liv, "B", 2 * L_CAR, -1, False, R.TAIL)
    parts = []
    for c in (A, B):
        parts += c.parts() + c.roof_parts() + c.under_parts()
    # wide bellows gangway at the joint (drawn by the 845)
    parts.append(Part(BODY_END / M - 0.02, (2 * L_CAR - BODY_END) / M + 0.02,
                      -W + 0.10, W - 0.10, Z_BOT + 0.35, ZS - 0.15,
                      lambda f, u, v, z, d: BELLOWS if f != "+z" else Paint(0x3A3C40), "A"))
    return parts, [], [("A", 0.0), ("B", 11.0)]


def rows_for(liv):
    parts, lines, cars = unit(liv)
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]

