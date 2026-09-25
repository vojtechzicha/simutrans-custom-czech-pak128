"""Arriva vlaky class 848 (Stadler GTW 2/6, 1st generation) drawn from scratch
with the pak128 box raycaster (render.py + railkit.py).

  848.2  ex DB Regio 646.2 (Zlinsky kraj)      livery arrivamodra
  848.4  ex Hessische Landesbahn (JMK, Plzen)  jihomoravskykraj, plzenskykraj
         (848.413 runs in arrivamodra too)

Unit = cab car A + short diesel-electric power module + cab car B
(2'Bo2', the end cars ride on the module).  38.66 m over couplers (Stadler
datasheets HLB / DB), 3.00 m wide, 3.85 m high.

Section split, measured on a telephoto broadside of an HLB unit
(commons: Unterwesterwaldbahn_bei_Girod_2020a.jpg) scaled by the datasheet
drawing's module length: end car 17.15 m coupler -> body end, bellows 0.30 m,
module body 3.76 m, bellows 0.30 m, end car 17.15 m.  That is 8.43 + 2.14 +
8.43 cu at 2.035 m/cu.  The family.yaml lengths are 8 + 3 + 8 (sum 19 = the
real 38.66 m); the owner split between the rows follows the real joints, so
the composed unit is exact whatever the nominal split.

Model units: s = metres from the unit's front coupler tip, u = s / MPC cu,
v = lateral cu (+v = right-hand side in the travel direction), z = model px
(1 px = 0.375 m).  End-car features are given in car-local metres m from that
car's coupler tip (car B is car A turned 180 deg).

Regenerate with `python tools/railrender/arriva.py 848`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS


# ------------------------------------------------------------------ dimensions
L_UNIT = 38.66
LENGTHS = [8, 3, 8]
MPC = L_UNIT / sum(LENGTHS)          # 2.035 m per carunit
PX = 0.375                           # m per model px (z)

W = R.W_STD * 3.00 / 2.825           # 0.977 cu half width
ZR = 3.85 / PX                       # 10.27 roof top
ZS = 3.20 / PX                       # 8.53 side wall top (roof curve starts)
ZC1 = 9.60                           # top of the first roof step
IN1, IN2 = 0.10, 0.38                # roof step insets

S_JA = 17.15                         # car A body end (joint) - also car B, car-local
S_BEL = 0.30                         # bellows length
S_M0 = S_JA + S_BEL                  # module body
S_M1 = L_UNIT - S_JA - S_BEL
M_CAB = 3.0                          # nose slabs end here, full body starts

# heights (model px)
Z_BOT = 1.05          # body side bottom, straight along the whole car (0.39 m);
                      # the cab bogie sits under it, only the wheels show
Z_FLOOR = 1.30        # door leaves reach down to the step (low floor 585 mm)
Z_WIN0 = 3.40         # passenger window bottom (1.28 m)
Z_WIN0_HI = 4.40      # HLB units: shorter windows over the bogie (1.65 m)
Z_WIN1 = 6.90         # window top (2.59 m)
Z_DOOR1 = 7.25        # door frame top
Z_LB0, Z_LB1 = 3.40, 4.50     # lamp band on the front
Z_PLOUGH = 1.40       # plough / skirt top

# car-local metres
WINDOWS = [(3.75, 5.18), (5.30, 6.75),
           (9.00, 10.43), (10.56, 11.99), (12.12, 13.55), (13.68, 15.11), (15.24, 16.67)]
PRE_DOOR = 6.9        # windows in front of this are over the high-floor bogie part
DOOR = (7.05, 8.60)
BOGIE_M = 4.30
CABWIN_REAR = 3.45

# ------------------------------------------------------------------ colours
WS = (0x2A, 0x34, 0x3D)            # windscreen / cab side window (never lit)
WS_HI = (0x4F, 0x62, 0x72)
AMBER = (0xF0, 0xA0, 0x18)         # LED destination display
DARK = Paint(0x2C2E31)
BELLOWS = Paint(0x2B2D30, top=0x3A3C40)
BOGIE = Paint(0x2A2B2D)
BOGIE_HI = Paint(0x45484B)
UNDER = Paint(0x303236)
PLOUGH = Paint(0x3A3D42, top=0x44474C)
YELLOW_EDGE = Paint(0xE6C92A)
COUPLER = Paint(0x26282B)
EXHAUST = Paint(0x5A5E63, top=0x2E3033)
WHITE = Paint(0xF0F2F4)


class Soft(Paint):
    """A paint whose side shading is softened (upper roof curve: it catches
    nearly as much light as the roof top)."""
    def __init__(self, base, soft=0.5):
        super().__init__(base)
        self.soft = soft

    def at(self, d, face):
        k = R.face_factor(d, face)
        if k is None:
            return R.safe(self.topc)
        k = 1.0 - (1.0 - k) * self.soft
        return R.safe(tuple(c * k for c in self.base))


def _mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def with_roof(C):
    """Roof curve gradient: side wall -> first roof step -> second step -> top."""
    r = C["roof"]
    C["roof_mid"] = Paint(r.base, top=_mix(r.base, r.topc, 0.45))
    C["roof_hi"] = Soft(_mix(r.base, r.topc, 0.55))
    return C


def livery(name):
    return with_roof(_livery(name))


def _livery(name):
    if name == "arrivamodra":
        # Arriva blue (848.2 Zlin + 848.413): cyan all over incl. the roof,
        # anthracite belt (front lamp band + panel round the cab side window),
        # one broad white slanted stripe per end car, silver doors
        blue = Paint(0x08ADDA, top=0x33BCE2)
        return dict(
            kind="arriva", hiwin=False,
            body=blue, roof=blue, roofbox=Paint(0x08ADDA, top=0x45C3E6),
            panel=Paint(0x535963), stripe=WHITE, pillar=Paint(0x45484C),
            door=Paint(0x8C939B), doorframe=Paint(0x5A6068), doorsplit=Paint(0x33373C),
            lampband=Paint(0x535963), hood=blue, visor=blue, lowfront=blue,
            grille=Paint(0x1492BA, top=0x1C9CC2), louvre=Paint(0x117FA2),
            modroof=Paint(0x16809F, top=0x2A8CAE), word=WHITE)
    if name == "jihomoravskykraj":
        # IDS JMK: coral-pink roof and cab hood, white band over the windows,
        # black body, white sill stripe, coral-red doors
        pink = Paint(0xEE6E8C, top=0xF27E99)
        return dict(
            kind="jmk", hiwin=True,
            body=Paint(0x2B3444), roof=pink, roofbox=Paint(0xE0607F, top=0xF6A0B4),
            band=Paint(0xE9EBEE), sill=Paint(0xE9EBEE), pillar=Paint(0x2B3444),
            door=Paint(0xE5405C), doorframe=Paint(0xD53753), doorsplit=Paint(0x8E2438),
            lampband=pink, hood=pink, visor=pink, lowfront=Paint(0x2B3444),
            grille=Paint(0xD85A79), louvre=Paint(0x7D848C),
            modroof=Paint(0xEE6E8C, top=0xF6A0B4), word=WHITE)
    if name == "plzenskykraj":
        # IDPK: blue body, white roof and cab hood (A-pillars), blue visor
        # over the windscreen, dark-grey skirt, yellow doors, swooshes
        blue = Paint(0x1562C2)
        white = Paint(0xE3E7EB, top=0xE8EBEE)
        return dict(
            kind="idpk", hiwin=True,
            body=blue, roof=white, roofbox=Paint(0xC9CED3, top=0xD6DADE),
            skirt=Paint(0x565B62), pillar=blue,
            door=Paint(0xF2C81E), doorframe=Paint(0xE0B616), doorsplit=Paint(0x6A5A1A),
            lampband=blue, hood=white, visor=blue, lowfront=blue,
            grille=Paint(0xA8AEB4, top=0xB4B9BE), louvre=Paint(0x0E4E9A),
            modroof=Paint(0xE3E7EB, top=0x8E949A), word=WHITE,
            sw_yel=Paint(0xF5CF1C), sw_grn=Paint(0x34B04A), sw_wht=Paint(0xF2F4F6))
    raise ValueError(name)


# ------------------------------------------------------------------ cab nose
def _bez(t, p0, p1, p2):
    return (1 - t) ** 2 * p0 + 2 * t * (1 - t) * p1 + t * t * p2


_RS = [(_bez(t, 1.65, 1.98, 2.95), _bez(t, 9.0, 10.15, ZR)) for t in np.linspace(0, 1, 60)]


def nose_m(z):
    """Car-local m of the cab front surface at height z (profile from the
    Stadler side drawing and photos: bumper most forward, windscreen raked
    about 30 deg, the roof curving into it)."""
    if z < Z_PLOUGH:
        return 0.80                                   # plough plate
    if z < Z_LB0:
        return 0.72 - (z - Z_PLOUGH) / (Z_LB0 - Z_PLOUGH) * 0.15    # bumper bulge
    if z < Z_LB1:
        return 0.57 + (z - Z_LB0) / (Z_LB1 - Z_LB0) * 0.08          # lamp band
    if z < 9.0:
        return 0.65 + (z - Z_LB1) / (9.0 - Z_LB1) * 1.00            # raked windscreen
    for (s, zz) in _RS:
        if zz >= z:
            return s
    return 2.95


def front_hw(z):
    """The front leans in a little towards the roof (head-on outline)."""
    hw = W if z < Z_LB1 else W - 0.10 * min(1.0, (z - Z_LB1) / 5.0)
    if z > ZC1:
        hw = min(hw, W - IN2)
    elif z > ZS:
        hw = min(hw, W - IN1)
    return hw


def cabwin(m, z):
    return 4.5 <= z <= 7.0 and nose_m(z) + 1.0 <= m <= CABWIN_REAR


def stripe_c(z):
    """Arriva white stripe centre (car-local m) at height z: slanted, the
    bottom nearer the nose; continues over the roof."""
    if z <= ZS:
        return 4.50 + 0.95 * (z - 1.3) / (ZS - 1.3)
    return 5.45 + 0.25 * (z - ZS) / (ZR - ZS)


def hood_edge(z):
    """Rear edge (car-local m) of the JMK pink / IDPK white cab hood on the side."""
    if z < 3.0:
        return nose_m(z) + 0.45
    if z < Z_WIN1:
        return 1.20 + (z - 3.0) / (Z_WIN1 - 3.0) * 1.2
    if z < 8.35:
        return 2.40 + (z - Z_WIN1) / (8.35 - Z_WIN1) * 0.80
    return 3.20 + (z - 8.35) / (ZR - 8.35) * 0.30


def swooshes(m, z, C):
    """IDPK curved swooshes above the windows (two groups per end car)."""
    for (m_lo, m_hi) in ((3.55, 6.20), (9.05, 11.10)):
        if not (m_lo - 0.3 <= m <= m_hi + 0.3 and Z_WIN1 - 0.2 <= z <= ZS + 0.9):
            continue
        t = max(0.0, min(1.0, (z - Z_WIN1) / (ZS - Z_WIN1)))   # 0 at window top .. 1 at cant
        span = m_hi - m_lo
        # arcs rising towards the cab (smaller m), concave
        for (off, w, key) in ((0.00, 0.26, "sw_yel"), (0.34, 0.40, "sw_grn"), (0.86, 0.24, "sw_wht")):
            c = m_hi - off - span * 0.62 * (t ** 0.8)
            if abs(m - c) <= w / 2:
                return C[key]
    return None


# ------------------------------------------------------------------ end car
class EndCar:
    """One end (cab) car. dirn = +1 for car A (m = s), -1 for car B."""

    def __init__(self, liv, owner, dirn, lamp):
        self.C = livery(liv)
        self.owner, self.dirn, self.lamp = owner, dirn, lamp

    def m_of(self, u):
        s = u * MPC
        return s if self.dirn == 1 else L_UNIT - s

    def u_of(self, m):
        s = m if self.dirn == 1 else L_UNIT - m
        return s / MPC

    def box(self, m0, m1, v0, v1, z0, z1, mat=None):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat or self.mat, self.owner)

    # ---- materials
    def win_bottom(self, m):
        return Z_WIN0_HI if (self.C["hiwin"] and m < PRE_DOOR) else Z_WIN0

    def front(self, m, vl, z):
        """Cab front surface; vl = lateral in the car's own frame."""
        C = self.C
        av = abs(vl)
        if z < Z_PLOUGH:
            return YELLOW_EDGE if z < 0.95 else PLOUGH
        hw = front_hw(z)
        if z < Z_LB0:
            if C["kind"] == "jmk":
                return C["sill"] if z >= 2.1 else C["body"]
            if C["kind"] == "idpk":
                if z < 2.5:
                    return C["skirt"]
                return C["hood"] if av > hw - 0.22 else C["lowfront"]
            return C["lowfront"]
        if z < Z_LB1:
            if 0.46 <= av <= 0.80 and 3.60 <= z <= 4.30:
                return self.lamp
            if C["kind"] == "idpk" and av > hw - 0.14:
                return C["hood"]
            if C["kind"] in ("jmk", "idpk") and av < 0.26 and 3.65 <= z <= 4.25:
                return C["word"]                       # "jmk" / "PLZENSKY KRAJ" logo
            return C["lampband"]
        if z < 9.35:
            if av < hw - 0.22 and 4.70 <= z <= 9.10:
                if 8.35 <= z <= 8.90 and av < 0.45:
                    return AMBER                       # LED destination display
                return WS_HI if z > 7.7 else WS
            return C["hood"]
        return C["visor"]

    def side(self, m, z, cs):
        C = self.C
        k = C["kind"]
        # rounded front corners belong to the front
        if m < nose_m(z) + 0.42:
            return self.front(m, W, z)
        if z > ZS:                                      # roof curve
            if k == "arriva" and abs(m - stripe_c(z)) <= 0.40:
                return C["stripe"]
            if 9.40 <= m <= 10.90 and z < ZC1:
                return C["grille"]                      # AC air intake on the roof curve
            return C["roof_hi"] if z > ZC1 else C["roof"]
        # cab side window (plain glass)
        if cabwin(m, z):
            return WS_HI if z > 6.5 else WS
        # doors: framed leaves from the floor up, tall leaf windows
        a, b = DOOR
        if a <= m <= b and Z_FLOOR <= z <= Z_DOOR1:
            t = (m - a) / (b - a)
            if t < 0.07 or t > 0.93 or z > Z_DOOR1 - 0.35:
                return C["doorframe"]
            if 0.47 <= t <= 0.53:
                return C["doorsplit"]
            if (0.15 <= t <= 0.41 or 0.59 <= t <= 0.85) and 2.9 <= z <= 6.6:
                return R.GLASS_HI if z > 6.15 else R.GLASS
            return C["door"]
        # passenger windows
        zb = self.win_bottom(m)
        if zb <= z <= Z_WIN1 and WINDOWS[0][0] <= m <= WINDOWS[-1][1]:
            for (wa, wb) in WINDOWS:
                if wa <= m <= wb:
                    return R.GLASS_HI if z > Z_WIN1 - 0.5 else R.GLASS
            if not (DOOR[0] - 0.3 <= m <= DOOR[1] + 0.3):
                return C["pillar"]
        # ---- livery
        if k == "arriva":
            if abs(m - stripe_c(z)) <= 0.40 and z >= Z_BOT:
                return C["stripe"]
            if m < 3.65 and Z_LB0 <= z <= 7.0:
                return C["panel"]                       # anthracite round the cab window
            if 11.9 <= m <= 13.9 and 1.95 <= z <= 2.85:
                x = (m - 11.9) / 2.0
                if x < 0.12 or int(x * 12) % 2 == 1:
                    return C["word"]                    # "arriva" wordmark (letter blocks)
            return C["body"]
        if k == "jmk":
            if m < hood_edge(z):
                return C["hood"]
            if z >= Z_WIN1 - 0.1:
                return C["band"]
            if 2.1 <= z < 3.05:
                return C["sill"]
            return C["body"]
        if k == "idpk":
            if m < hood_edge(z) - 0.9 and z >= 2.5:
                return C["hood"]                        # white band along the A-pillar
            sw = swooshes(m, z, C)
            if sw is not None:
                return sw
            if 3.75 <= m <= 5.0 and 2.65 <= z <= 3.2:
                return C["word"]                        # PLZENSKY KRAJ logo
            if z < 2.5:
                return C["skirt"]
            return C["body"]
        return C["body"]

    def top(self, m, vl, z):
        C = self.C
        if m < M_CAB and z < ZR - 0.05:
            if z < ZS or m < nose_m(z) + 0.42:
                return self.front(m, vl, z)             # tops of the nose slabs
        if z < ZS - 0.05:
            return self.side(m, z, "L")                 # steps of the lower body
        if C["kind"] == "arriva" and abs(m - stripe_c(z)) <= 0.40:
            return C["stripe"]
        if C["kind"] == "idpk" and m < 3.0:
            return C["visor"] if m < 2.2 else C["roof"]
        return C["roof_mid"] if z < ZR - 0.1 else C["roof"]

    def mat(self, f, u, v, z, d):
        m = self.m_of(u)
        vl = v * self.dirn
        if f == "+z":
            return self.top(m, vl, z)
        if f in ("+v", "-v"):
            return self.side(m, z, f)
        facing_cab = (f == "-u") == (self.dirn == 1)
        if m < M_CAB + 0.01 and facing_cab:
            return self.front(m, vl, z)
        if m < M_CAB + 0.01:
            return self.front(m, vl, z)                 # slab steps facing the body
        # inner end at the joint
        if z > ZS:
            return self.C["roof"]
        return DARK

    def roof_mat(self, f, u, v, z, d):
        return self.C["roofbox"]

    # ---- geometry
    def parts(self):
        P = []
        # main body (above the bogie cut-out) + low-floor skirt behind the bogie
        P.append(self.box(M_CAB, S_JA, -W, W, Z_BOT, ZS))
        # roof: two steps (large-radius roof curve)
        P.append(self.box(M_CAB - 0.05, S_JA - 0.04, -W + IN1, W - IN1, ZS, ZC1))
        P.append(self.box(M_CAB - 0.05, S_JA - 0.08, -W + IN2, W - IN2, ZC1, ZR))
        # cab nose: stacked slabs, rounded plan (corner steps)
        zs = list(np.arange(Z_PLOUGH, Z_LB1, 0.35)) + list(np.arange(Z_LB1, ZR - 0.01, 0.25))
        steps = [(0.0, 0.14, 0.34), (0.14, 0.34, 0.17), (0.34, 0.70, 0.06), (0.70, 99.0, 0.0)]
        for i, z0 in enumerate(zs):
            z1 = zs[i + 1] if i + 1 < len(zs) else ZR
            zc = (z0 + z1) / 2
            mf = nose_m(zc)
            if mf >= M_CAB:
                continue
            hw = front_hw(zc)
            for (d0, d1, cut) in steps:
                a, b = mf + d0, min(M_CAB, mf + d1)
                if a >= b:
                    continue
                P.append(self.box(a, b, -(hw - cut), hw - cut, z0, z1))
        # plough plate with the yellow lower edge (rounded front corners)
        for (a, b, cut) in ((0.80, 0.95, 0.30), (0.95, 1.25, 0.12), (1.25, 2.40, 0.04)):
            P.append(self.box(a, b, -(W - cut), W - cut, 0.50, Z_PLOUGH))
        # coupler
        P.append(self.box(0.05, 0.80, -0.20, 0.20, 1.85, 2.75, lambda *a: COUPLER))
        # cab bogie
        P.append(self.box(BOGIE_M - 1.35, BOGIE_M + 1.35, -W + 0.05, W - 0.05, 0.0, Z_BOT + 0.02,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 0.5 < z < 1.0) else BOGIE))
        # dark underframe line under the low floor
        # (a dark line under the body like the native stock; the low-floor body
        # sits 0.39 m above the rails with its shadow and underfloor boxes)
        P.append(self.box(M_CAB + 0.2, S_JA - 0.25, -W + 0.07, W - 0.07, 0.05, Z_BOT + 0.01, lambda *a: UNDER))
        # roof: cab air-conditioning cover + passenger AC unit
        P.append(self.box(3.30, 4.70, -0.52, 0.52, ZR - 0.05, ZR + 0.28, self.roof_mat))
        P.append(self.box(9.40, 11.20, -0.62, 0.62, ZR - 0.05, ZR + 0.38, self.roof_mat))
        return P


# ------------------------------------------------------------------ power module
class Module:
    def __init__(self, liv, owner="M"):
        self.C = livery(liv)
        self.owner = owner

    def box(self, s0, s1, v0, v1, z0, z1, mat=None):
        return Part(s0 / MPC, s1 / MPC, v0, v1, z0, z1, mat or self.mat, self.owner)

    def side(self, s, z, f):
        C = self.C
        k = C["kind"]
        # screen-right end on either side (the unit is 180-deg symmetric)
        if f == "-v":
            louv, upper, logo = (20.35, 21.05), (17.65, 20.10), (18.4, 19.7)
        else:
            louv, upper, logo = (17.61, 18.31), (18.56, 21.01), (18.96, 20.26)
        if z > ZS:
            if upper[0] <= s <= upper[1] and z < ZC1 and k != "idpk":
                return C["grille"]                     # cooler intakes on the roof curve
            return C["roof_hi"] if z > ZC1 else C["roof"]
        if k == "jmk":
            if z >= Z_WIN1 - 0.1:
                return C["band"]
            if 2.1 <= z < 3.05:
                return C["sill"]
        if louv[0] <= s <= louv[1] and 2.9 <= z <= 8.0:
            return C["louvre"]
        if k == "arriva" and logo[0] <= s <= logo[1] and 3.0 <= z <= 3.7:
            return C["word"]                           # Zlinsky kraj logo
        if k == "jmk" and logo[0] <= s <= logo[1] and 5.4 <= z <= 6.1:
            return C["word"]                           # Jihomoravsky kraj logo
        if k == "idpk" and z < 2.5:
            return C["skirt"]
        return C["body"]

    def mat(self, f, u, v, z, d):
        s = u * MPC
        C = self.C
        if f == "+z":
            if z > ZC1 and 17.75 <= s <= 20.2 and abs(v) < 0.62:
                return C["modroof"]                    # cooler grille on the roof
            if z > ZS - 0.05:
                return C["roof_mid"] if z < ZR - 0.1 else C["roof"]
            return self.side(s, z, "-v")
        if f in ("+v", "-v"):
            return self.side(s, z, f)
        return DARK

    def parts(self):
        P = []
        P.append(self.box(S_M0, S_M1, -W + 0.02, W - 0.02, 1.70, ZS))
        P.append(self.box(S_M0 + 0.03, S_M1 - 0.03, -W + IN1 + 0.02, W - IN1 - 0.02, ZS, ZC1))
        P.append(self.box(S_M0 + 0.06, S_M1 - 0.06, -W + IN2, W - IN2, ZC1, ZR))
        # bellows (both joints, drawn by the module)
        bel = lambda f, u, v, z, d: BELLOWS
        for (a, b) in ((S_JA - 0.02, S_M0 + 0.02), (S_M1 - 0.02, L_UNIT - S_JA + 0.02)):
            P.append(self.box(a, b, -W + 0.10, W - 0.10, 1.45, ZC1, bel))
        # powered bogie (wheelbase 2.0 m, 860 mm wheels)
        c = L_UNIT / 2
        P.append(self.box(c - 1.45, c + 1.45, -W + 0.06, W - 0.06, 0.0, 1.72,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.6) else BOGIE))
        # exhaust stack at the car-B end of the roof
        P.append(self.box(20.60, 20.90, 0.10, 0.40, ZR - 0.05, ZR + 0.50, lambda *a: EXHAUST))
        return P


# ------------------------------------------------------------------ the unit
def unit(liv):
    A = EndCar(liv, "A", +1, R.HEAD)
    B = EndCar(liv, "B", -1, R.TAIL)
    M = Module(liv)
    parts = A.parts() + M.parts() + B.parts()
    cars = [("A", 0.0), ("M", float(LENGTHS[0])), ("B", float(LENGTHS[0] + LENGTHS[1]))]
    return parts, [], cars


def rows_for(liv):
    parts, lines, cars = unit(liv)
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]


LIVERIES = ["arrivamodra", "jihomoravskykraj", "plzenskykraj"]
