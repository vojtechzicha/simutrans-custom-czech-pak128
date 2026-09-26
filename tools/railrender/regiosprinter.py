"""GW Train Regio class 818 (Siemens/Duewag RegioSprinter, ex-DB class 654)
drawn from scratch with the pak128 box raycaster (render.py + railkit.py),
structure after db628.py / gtw.py.

  row 0  "818.0"  ex-Rurtalbahn cars (818 002-017): round side buffers and a
                  screw coupling on a dark buffer beam, grey roof AC housings
  row 1  "818.2"  ex-Vogtlandbahn cars (818 245-248): Scharfenberg coupler in a
                  grey bag, no side buffers, low turquoise-green bumper skirt,
                  amber panels under the lamps (in the lime band), white roof boxes

ONE Simutrans vehicle, cab at both ends (headlights at the front cab, tail
lights at the rear cab): 24.80 m over buffers -> length 12 cu
(M = 24.8 / 12 = 2.067 m per carunit).  The three articulated modules belong to
the same owner; the joints show as narrow dark bellows.

Real car (baureihe654.de technical data, de.wikipedia "RegioSprinter"): 23.98 m
over the body, 24.80 m with buffers (25.17 m with Scharfenberg couplers), end
modules 9.64 m, middle module 4.10 m (so 0.30 m joints), 2.97 m wide, roof
sheet 3.35 m (3.45 m with equipment), floor 0.53 m (low-floor part) / 1.13 m
(high-floor part over the engine), axle arrangement A'2'A' (one powered single
axle under each cab module, two single axles under the middle module), two
1.30 m double doors per side, one per end module.
Side layout (car-local metres from the module's lower front face), measured
with a 1-D perspective fit (joints + both ends; residuals < 1 px) on the
near-side-on Commons photos "RegioSprinter v Karlových Varech.jpg" (654 048,
VBG) and "GW Train RegioSprinter.jpg" (654 012, RTB); both agree within 0.1 m:
cab side window 0.45-1.72, "2" pictogram panel 2.1-2.9, window over the high
floor 3.0-4.8 (1.60-2.75 m high), double door 4.95-6.45, window 6.6-9.5
(1.10-2.80 m), body end 9.64; middle module one window 0.2-3.9.  Heights are
scaled so that the cant (2.95 m) and the roof crown match the 3.35 m roof.
The green / orange boundary meets the roof at m 4.35 (lime from m 3.45) and
runs down to 0.86 m under the cab window; big white GW TRAIN on m 1.6-4.75,
1.0-1.45 m.  Drawn with small liberties for 1x legibility: the windows and the
door are ~0.1 m narrower (one-pixel orange pillars) and window 1 starts at
3.18 so the lime crescent shows as a diagonal in front of it; the "2"
pictogram is left out (a stray white pixel at 1x).
Front (818_gwtr_3 / _4): windscreen 1.52-3.10 m with the lamps in its bottom
corners (RTB), green panel with logo 1.22-1.52 m, lime line 0.90-1.22 m,
orange below, dark buffer beam 0.30-0.55 m.

Model units: s = metres from the front buffer face, u = s / M; v = lateral cu
(+v = right-hand side in the travel direction); z = model px (1 px = 0.375 m).
Module-local m: metres from that end module's lower front face (module B is
module A turned 180 degrees).

Regenerate with `python tools/railrender/gwtr.py 818`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS

LIVERIES = ["oranzovozelena"]

# ------------------------------------------------------------------ dimensions
PX = 0.375                         # metres per model px (z)
L_CAR = 24.80                      # over buffers
M = L_CAR / 12.0                   # 2.067 m per carunit
BUF = 0.41                         # buffer length (body 23.98 m)
L_END = 9.64                       # end module body
L_MID = 4.10                       # middle module body
GAP = 0.30                         # joint
S_MID0 = BUF + L_END + GAP         # middle module body start, vehicle metres
W = R.W_STD * 2.97 / 2.825         # 0.967 cu half width
VM = 2.825 / 2 / R.W_STD           # lateral metres per cu (1.535)


def zp(metres):
    return metres / PX


Z_UF = zp(0.14)            # running gear / underframe bottom (visible dark band)
Z_SK = zp(0.30)            # orange skirt bottom under the cab (high-floor) part
Z_BOT = zp(0.40)           # body side bottom, low-floor part
Z_BOTMID = zp(0.46)        # middle module body bottom (running gear shows below)
ZC = zp(2.95)              # cant: side wall top
ZC1 = zp(3.17)             # first roof step
ZR = zp(3.35)              # roof crown
IN1, IN2 = 0.10, 0.44      # roof step insets (cu)

# car-local metres
M_CAB = 1.15               # nose slabs end here, the straight body starts
CABWIN = (0.45, 1.72)
# windows / door drawn ~0.1 m narrower than measured (3.0-4.8, 4.95-6.45,
# 6.6-9.5) so the orange pillars between them stay one pixel wide at 1x
WIN1 = (3.18, 4.62)        # window over the high floor
DOOR = (4.98, 6.42)
WIN2 = (6.78, 9.40)
SKIRT_END = 4.90           # the low orange skirt of the high-floor part ends here
WORD = (1.60, 4.75)        # big GW TRAIN
MID_WIN = (0.30, 3.80)     # middle-module window (module-local metres)

# heights (metres)
H_WIN1 = (1.60, 2.75)
H_WIN = (1.10, 2.80)
H_DOOR = (0.42, 2.88)
H_DOORGLASS = (1.12, 2.72)
H_CABWIN = (1.58, 2.86)
H_WORD = (1.10, 1.50)

# ------------------------------------------------------------------ colours
# GWTR shared palette (BRIEF): orange, dark green, lime, white, light-grey roof
ORANGE = Paint(0xE8641E)
GREEN = Paint(0x116B48)
LIME = Paint(0x52C040)
WHITE = Paint(0xF2F4F5)
ROOF = Paint(0xC3C7CA)
DOORGREEN = Paint(0x12473C)
DOORFRAME = Paint(0x1F2A28)
DOORSPLIT = Paint(0x161C1B)
WS = (0x2E, 0x3E, 0x4C)            # windscreen / cab side window (never lit)
WS_HI = (0x4E, 0x63, 0x75)         # upper part: sky reflection
DISPLAY = Paint(0x1E2124)          # destination display behind the windscreen top
BEAM = Paint(0x33363A)             # RTB buffer beam / skirt plate
BUFFER = Paint(0x1D1F21, top=0x2A2C2F)
HOOK = Paint(0x26282B)
TURQ = Paint(R.safe((0x10, 0xB0, 0x90)))     # VBG plastic bumper skirt
AMBER = Paint(0xFB9F18)            # VBG amber panels round the lamp level
BAG = Paint(0x9A9D98, top=0xA8ABA6)          # VBG coupler bag
UNDER = Paint(0x2E3033)
GEAR = Paint(0x2A2B2D)
GEAR_HI = Paint(0x45484B)
BELLOWS = Paint(0x2B2D30, top=0x3A3C40)
JOINT_END = Paint(0x3A3D40)
AC_RTB = Paint(0xA3A8AC, top=0xB6BABD)
AC_RTB_GRILLE = Paint(0x676C71)
AC_VBG = Paint(0xE6E8EA, top=0xF0F1F2)
AC_VBG_GRILLE = Paint(0xB9BDC1)
EXHAUST = Paint(0x3E4145, top=0x26282B)
FIN = Paint(0x26282B)


# ------------------------------------------------------------------ cab nose profile
def nose_m(z):
    """Car-local m of the cab front surface at model height z: vertical lower
    face, green panel slightly raked, windscreen raked ~20 deg, rounded roof
    front."""
    h = z * PX
    if h < 1.25:
        return 0.0 + max(0.0, h - 0.55) * 0.04
    if h < 1.52:
        return 0.03 + (h - 1.25) / 0.27 * 0.05
    if h < 3.10:
        return 0.08 + (h - 1.52) / 1.58 * 0.54
    t = min(1.0, (h - 3.10) / 0.25)
    return 0.62 + 0.45 * t ** 1.7


def front_hw(z):
    """Head-on outline: slight tumblehome above the windscreen bottom."""
    h = z * PX
    hw = W if h < 1.52 else W - 0.06 * min(1.0, (h - 1.52) / 1.43)
    if z > ZC1:
        hw = min(hw, W - IN2)
    elif z > ZC:
        hw = min(hw, W - IN1)
    return hw


# ------------------------------------------------------------------ livery curve
H_B0, H_TOP = 0.86, 3.00           # boundary height at the front / at the roof edge
M_OUT, P_OUT = 4.38, 4.6           # orange-side edge of the lime crescent meets the roof
H_I0, M_IN, P_IN = 1.21, 3.40, 3.9  # green-side edge


def edge_out(m):
    """Height (m) of the orange / lime boundary at car-local m."""
    return H_B0 + (H_TOP - H_B0) * (max(0.0, m) / M_OUT) ** P_OUT


def edge_in(m):
    """Height (m) of the lime / dark-green boundary at car-local m."""
    return H_I0 + (H_TOP - H_I0) * (max(0.0, m) / M_IN) ** P_IN


def zone(m, h):
    """Livery of the plain side wall (and roof side) at car-local m, height h."""
    if h < edge_out(m):
        return ORANGE
    if h < edge_in(m):
        return LIME
    return GREEN


def word_hit(x, zz):
    """GW TRAIN as two italic word blocks ("GW" ligature, "TRAIN"): x 0..1
    along it as read, zz 0..1 up.  At 1x it is a short white bar with one gap;
    letter gaps would only sprinkle single pixels."""
    x = x - 0.06 * (zz - 0.5)                      # italic slant
    return 0.0 <= x <= 0.25 or 0.32 <= x <= 1.0


# ------------------------------------------------------------------ end module
class EndModule:
    """One cab module. dirn = +1 for module A (front), -1 for module B."""

    def __init__(self, kind, owner, dirn, lamp):
        self.kind, self.owner, self.dirn, self.lamp = kind, owner, dirn, lamp

    def m_of(self, u):
        s = u * M
        return s - BUF if self.dirn == 1 else (L_CAR - BUF) - s

    def u_of(self, m):
        s = BUF + m if self.dirn == 1 else (L_CAR - BUF) - m
        return s / M

    def box(self, m0, m1, v0, v1, z0, z1, mat=None):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat or self.mat, self.owner)

    # ---- materials
    def front(self, m, vl, z):
        """Cab front surface; vl = lateral in the module's own frame."""
        h = z * PX
        av = abs(vl)
        vbg = self.kind == "vbg"
        if h < 0.55:
            return ORANGE if vbg else BEAM
        if h < 0.90:
            if vbg and h >= 0.68 and 0.40 <= av <= 0.84:
                return AMBER
            return ORANGE
        if h < 1.22:
            if vbg and 0.96 <= h <= 1.20 and 0.46 <= av <= 0.80:
                return self.lamp
            return LIME
        if h < 1.52:
            if 1.32 <= h <= 1.45 and av < 0.28:
                return WHITE                      # small GW TRAIN logo
            return GREEN
        hw = front_hw(z)
        if h < 3.10 and av < hw - 0.10 and 1.55 <= h <= 3.04:
            if not vbg and h <= 1.86 and 0.46 <= av <= hw - 0.11:
                return self.lamp                  # lamps behind the windscreen bottom
            if h >= 2.84:
                return DISPLAY
            return WS_HI if h > 2.55 else WS
        return GREEN

    def side(self, m, z, f):
        h = z * PX
        if m < nose_m(z) + 0.22:
            return self.front(m, W, z)            # rounded front corners
        if z > ZC:
            return zone(m, h)                     # roof side
        # cab side window: front edge along the windscreen, bottom rising aft
        if nose_m(z) + 0.40 <= m <= CABWIN[1]:
            hb = H_CABWIN[0] + 0.30 * max(0.0, (m - 1.15) / (CABWIN[1] - 1.15)) ** 2
            if hb <= h <= H_CABWIN[1]:
                return WS_HI if h > 2.62 else WS
        # double door: body-coloured frame, dark leaves, glass, green lower panels
        a, b = DOOR
        if a <= m <= b and H_DOOR[0] <= h <= H_DOOR[1]:
            t = (m - a) / (b - a)
            if t < 0.04 or t > 0.96 or h > H_DOOR[1] - 0.10:
                return DOORFRAME
            if 0.48 <= t <= 0.52:
                return DOORSPLIT
            if H_DOORGLASS[0] <= h <= H_DOORGLASS[1] and (0.10 <= t <= 0.44 or 0.56 <= t <= 0.90):
                return R.GLASS_HI if h > H_DOORGLASS[1] - 0.22 else R.GLASS
            if h < H_DOORGLASS[0]:
                return DOORGREEN
            return DOORFRAME
        # passenger windows
        if WIN1[0] <= m <= WIN1[1] and H_WIN1[0] <= h <= H_WIN1[1]:
            return R.GLASS_HI if h > H_WIN1[1] - 0.22 else R.GLASS
        if WIN2[0] <= m <= WIN2[1] and H_WIN[0] <= h <= H_WIN[1]:
            return R.GLASS_HI if h > H_WIN[1] - 0.22 else R.GLASS
        # big white GW TRAIN on the lower cab side, over the boundary
        if WORD[0] <= m <= WORD[1] and H_WORD[0] <= h <= H_WORD[1]:
            x = (m - WORD[0]) / (WORD[1] - WORD[0])
            if (f == "-v") != (self.dirn == 1):
                x = 1 - x                         # reads left to right on either side
            if word_hit(x, (h - H_WORD[0]) / (H_WORD[1] - H_WORD[0])):
                return WHITE
        return zone(m, h)

    def top(self, m, vl, z):
        h = z * PX
        if m < M_CAB and z < ZR - 0.05:
            if z < ZC or m < nose_m(z) + 0.22:
                return self.front(m, vl, z)       # tops of the nose slabs
        if z < ZR - 0.1:
            return zone(m, h)                     # skirt steps, roof ledge
        return ROOF

    def mat(self, f, u, v, z, d):
        m = self.m_of(u)
        vl = v * self.dirn
        if f == "+z":
            return self.top(m, vl, z)
        if f in ("+v", "-v"):
            return self.side(m, z, f)
        if m < M_CAB + 0.01:
            return self.front(m, vl, z)
        if z > ZC:
            return ROOF
        return JOINT_END                          # inner end at the joint

    # ---- geometry
    def parts(self):
        P = []
        # body, low orange skirt of the high-floor part, roof steps
        P.append(self.box(M_CAB, L_END, -W, W, Z_BOT, ZC))
        P.append(self.box(M_CAB, SKIRT_END, -W, W, Z_SK, Z_BOT + 0.01))
        P.append(self.box(M_CAB - 0.05, L_END - 0.04, -W + IN1, W - IN1, ZC, ZC1))
        P.append(self.box(M_CAB - 0.05, L_END - 0.08, -W + IN2, W - IN2, ZC1, ZR))
        # cab nose: stacked slabs, rounded plan (corner steps)
        zs = list(np.arange(Z_SK, zp(1.52), 0.4)) + list(np.arange(zp(1.52), ZR - 0.01, 0.3))
        steps = [(0.0, 0.10, 0.15), (0.10, 0.26, 0.05), (0.26, 99.0, 0.0)]
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
        # running gear: powered single axle under the cab module (behind the
        # skirt, wheels show below it) and the underframe of the low-floor part
        P.append(self.box(1.9, 3.3, -W + 0.16, W - 0.16, 0.0, Z_SK + 0.02,
                          lambda f, u, v, z, d: GEAR_HI if (f in ("+v", "-v") and z > Z_SK - 0.3) else GEAR))
        P.append(self.box(SKIRT_END, L_END - 0.25, -W + 0.10, W - 0.10, Z_UF, Z_BOT + 0.01,
                          lambda *a: UNDER))
        # front end equipment
        if self.kind == "rtb":
            P.append(self.box(-0.06, 0.20, -(W - 0.10), W - 0.10, zp(0.30), zp(0.55),
                              lambda *a: BEAM))
            for sg in (-1, 1):
                c = sg * 0.875 / VM
                P.append(self.box(-BUF, -0.05, c - 0.15, c + 0.15, zp(0.84), zp(1.28),
                                  lambda *a: BUFFER))
                P.append(self.box(-0.10, 0.02, c - 0.19, c + 0.19, zp(0.80), zp(1.32),
                                  lambda *a: BUFFER))      # buffer housings / plates
            P.append(self.box(-0.28, 0.0, -0.07, 0.07, zp(0.92), zp(1.12), lambda *a: HOOK))
        else:
            # low turquoise bumper skirt, rounded corners
            for (a, b, cut) in ((-0.30, -0.18, 0.26), (-0.18, 0.05, 0.10), (0.05, 0.30, 0.04)):
                P.append(self.box(a, b, -(W - cut), W - cut, zp(0.20), zp(0.56), lambda *x: TURQ))
            # Scharfenberg coupler under its grey bag
            P.append(self.box(-BUF, 0.0, -0.26, 0.26, zp(0.60), zp(1.30), lambda *a: BAG))
        return P

    def roof_parts(self):
        P = []
        vbg = self.kind == "vbg"
        body, grille = (AC_VBG, AC_VBG_GRILLE) if vbg else (AC_RTB, AC_RTB_GRILLE)

        def ac(f, u, v, z, d):
            if f in ("+v", "-v") and ZR + 0.25 < z < ZR + 0.75 and (self.m_of(u) * 1.4) % 1.0 < 0.5:
                return grille
            return body
        # passenger AC housing over the low-floor part
        P.append(self.box(5.5, 8.9, -0.62, 0.62, ZR - 0.05, ZR + 0.95, ac))
        # engine exhaust behind the cab, horn fin on the cab roof
        P.append(self.box(2.45, 2.85, -0.34, -0.06, ZR - 0.05, ZR + 0.85, lambda *a: EXHAUST))
        P.append(self.box(1.00, 1.30, 0.12, 0.26, ZR - 0.05, ZR + 0.70, lambda *a: FIN))
        if vbg:
            # white box on the cab roof (818 246 photo)
            P.append(self.box(1.35, 2.25, -0.40, 0.40, ZR - 0.05, ZR + 0.60, lambda *a: AC_VBG))
        return P


# ------------------------------------------------------------------ middle module
class MidModule:
    def __init__(self, kind, owner):
        self.kind, self.owner = kind, owner

    def box(self, a, b, v0, v1, z0, z1, mat=None):
        """a, b in module-local metres (from the front joint side)."""
        return Part((S_MID0 + a) / M, (S_MID0 + b) / M, v0, v1, z0, z1, mat or self.mat, self.owner)

    def side(self, a, z):
        h = z * PX
        if z > ZC:
            return ORANGE
        if MID_WIN[0] <= a <= MID_WIN[1] and H_WIN[0] <= h <= H_WIN[1]:
            if abs(a - (MID_WIN[0] + MID_WIN[1]) / 2) < 0.04:
                return DOORFRAME                  # thin mullion
            return R.GLASS_HI if h > H_WIN[1] - 0.22 else R.GLASS
        return ORANGE

    def mat(self, f, u, v, z, d):
        a = u * M - S_MID0
        if f == "+z":
            return ROOF if z > ZR - 0.1 else ORANGE
        if f in ("+v", "-v"):
            return self.side(a, z)
        return JOINT_END

    def parts(self):
        P = []
        P.append(self.box(0.0, L_MID, -W, W, Z_BOTMID, ZC))
        P.append(self.box(0.03, L_MID - 0.03, -W + IN1, W - IN1, ZC, ZC1))
        P.append(self.box(0.06, L_MID - 0.06, -W + IN2, W - IN2, ZC1, ZR))
        # two single-axle running gears near the ends, underframe between
        gear = lambda f, u, v, z, d: GEAR_HI if (f in ("+v", "-v") and 0.5 < z < 0.9) else GEAR
        for c in (0.70, L_MID - 0.70):
            P.append(self.box(c - 0.55, c + 0.55, -W + 0.18, W - 0.18, 0.0, Z_BOTMID + 0.02, gear))
        P.append(self.box(1.25, L_MID - 1.25, -W + 0.20, W - 0.20, zp(0.22), Z_BOTMID + 0.02,
                          lambda *x: UNDER))
        # roof AC housing
        body = AC_VBG if self.kind == "vbg" else AC_RTB
        P.append(self.box(0.75, 3.35, -0.58, 0.58, ZR - 0.05, ZR + 0.80, lambda *x: body))
        # bellows at both joints (drawn by the middle module, same owner)
        bel = lambda f, u, v, z, d: BELLOWS
        for (a, b) in ((-GAP - 0.03, 0.03), (L_MID - 0.03, L_MID + GAP + 0.03)):
            P.append(self.box(a, b, -W + 0.10, W - 0.10, zp(0.55), ZC1, bel))
        return P


# ------------------------------------------------------------------ the car
def car(kind):
    """Parts and lines of one RegioSprinter; kind 'rtb' (818.0) or 'vbg' (818.2)."""
    A = EndModule(kind, "A", +1, R.HEAD)
    B = EndModule(kind, "A", -1, R.TAIL)
    Mm = MidModule(kind, "A")
    parts = A.parts() + A.roof_parts() + Mm.parts() + B.parts() + B.roof_parts()
    return parts, []


def row(kind):
    parts, lines = car(kind)
    return [R.vehicle_tile(parts, lines, d, 0.0, {"A"}) for d in DIRS]


def rows_for(liv):
    """[818.0 ex-RTB row, 818.2 ex-VBG row] in livery `liv`."""
    if liv not in LIVERIES:
        raise ValueError(liv)
    return [row("rtb"), row("vbg")]
