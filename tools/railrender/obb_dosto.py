#!/usr/bin/env python3
"""ÖBB double-deck push-pull stock (Bombardier Görlitz "Wiesel" family):
Bmpz-dl 26-33 double-deck coach and Bbfmpz 86-33 double-deck cab car, drawn
with the pak128.cs calibrated box renderer (render.py / railkit.py).

    python tools/railrender/obb_dosto.py [--preview DIR]

writes vehicle-rail/obb/dosto/sprites/<livery>.png, row 0 = 86-33 cab car,
row 1 = 26-33 coach, for the liveries
  cityshuttle  the original CityShuttle / "Wiesel" scheme: silver-grey car, red
               field over the left half AS SEEN ending in a steep "/" diagonal,
               white "CityShuttle" script on the red, the WIESEL weasel logo
               (or a red ÖBB) on the grey; light grey doors; cab front red
               with a dark grey windscreen band and a grey roof dome
               (photos I09 436 Bf Břeclav 86-33 210, 2017-09-14 Neulengbach
               86-33 013 + 26-33, Wiesel.jpg 26-33 070; vagonWEB Bmpz-dl-a,
               Bbfmpz-a/b)
  cityjet      the refurbished Cityjet scheme: white upper body with the upper
               deck windows in a continuous black band, red lower body with a
               lighter orange band, lower deck windows in a dark grey band,
               anthracite doors with a light centre seal and yellow step, grey
               "cityjet" script; cab front black from the dome to the
               windscreen bottom framed by a red outline, white band with a
               red ÖBB, red lower front (photos Dvoupatrový Cityjet ÖBB na
               nádraží Břeclav 2024, 20251026 Bf Marchegg 86-33 000, 86-33 112
               Wien Hbf 2019; vagonWEB Bmpz-dl-cj-a/b, Bbfmpz-cj-a/b)

Real cars: 26.8 m (coach) / 27.1 m (cab car) over buffers, 2.78 m wide,
4.63 m high; low-floor lower deck between the two double doors, single-level
end sections over the bogies with "intermediate" windows.  Both are drawn at
length 13 (pak128.cs coach convention).  Heights come from the vagonWEB
drawings (9.6 px/m vertically): roof edge 4.10 m, upper deck windows 3.23-3.96,
intermediate windows 1.88-2.71, lower deck windows 1.04-1.77, doors 0.42-2.6.

Coordinates as in obb_cityshuttle.py: s = metres from the car front (the cab
front of the 86-33), x = metres from the screen-left end AS SEEN (x = s on the
-v side, x = LM - s on the +v side); liveries are painted by x (point-symmetric
like the real cars), geometry by s.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import numpy as np                      # noqa: E402
import railkit as R                     # noqa: E402
from railkit import Paint, Part        # noqa: E402
from render import DIRS                 # noqa: E402
import obb_cityshuttle as CS            # noqa: E402  shared lettering + outlines

PX = 0.375
L = 13.0
W = R.W_STD * 2.78 / 2.825          # 0.905 cu


def zm(h):
    return h / PX


ZS = zm(4.10)                        # roof edge (side wall top) 10.93
ZLEAN = zm(3.02)                     # upper deck wall leans in above this
ZR = zm(4.63)                        # roof top 12.35
Z_END_BOT = zm(1.00)                 # body bottom over the bogies
Z_LOW_BOT = zm(0.42)                 # body bottom of the low-floor middle
Z_UP0, Z_UP1 = zm(3.23), zm(3.96)    # upper deck windows
Z_MID0, Z_MID1 = zm(1.88), zm(2.71)  # intermediate (end section) windows
Z_LO0, Z_LO1 = zm(1.04), zm(1.77)    # lower deck windows
Z_D0, Z_D1 = zm(0.42), zm(2.60)      # doors
Z_DW0, Z_DW1 = zm(1.05), zm(2.35)    # door windows

# layouts: metres from the car front (s)
COACH = dict(
    LM=26.8,
    upper=[(6.3, 7.65), (8.2, 9.55), (10.0, 11.4), (11.8, 13.15), (13.6, 14.9),
           (15.4, 16.8), (17.2, 18.6), (19.1, 20.5)],
    end_up=[(3.4, 4.5), (22.3, 23.4)],
    mid=[(1.8, 3.2), (3.4, 4.5), (22.3, 23.4)],
    lower=[(8.2, 9.55), (10.0, 11.4), (11.8, 13.15), (13.6, 14.9), (15.4, 16.8), (17.2, 18.6)],
    doors=[(6.0, 7.9), (18.9, 20.8)],
    low=(5.9, 20.9),                 # low-floor middle (body reaches down to 0.42 m)
    bogies=[3.3, 23.5],
    cab=False,
)
CAB = dict(
    LM=27.1,
    upper=[(6.6, 7.9), (8.5, 9.8), (10.3, 11.6), (12.1, 13.4), (13.9, 15.3),
           (15.7, 17.0), (17.5, 18.8), (19.4, 20.8)],
    end_up=[(22.6, 23.7)],
    mid=[(3.5, 4.5), (22.6, 23.7)],
    lower=[(8.5, 9.8), (10.3, 11.6), (12.1, 13.4), (13.9, 15.3), (15.7, 17.0), (17.5, 18.8)],
    doors=[(6.3, 8.2), (19.2, 21.1)],
    low=(6.2, 21.2),
    bogies=[3.4, 23.9],
    cab=True,
)

WS = (0x2A, 0x34, 0x3D)              # windscreen / cab side window: plain, never lit
WS_HI = (0x4F, 0x62, 0x72)
BOGIE = Paint(0x232426)
BOGIE_HI = Paint(0x3E4144)
UNDER = Paint(0x2A2C2E)
BUFFER = Paint(0x1E2022)
BELLOWS = Paint(0x2B2D2F)
WHITE = Paint(0xF4F4F4)
TAIL_OFF = (0x8A, 0x1E, 0x1A)


def livery(name):
    if name == "cityshuttle":
        return dict(
            name=name, grey=Paint(0xC6C8CA), red=Paint(0xD62420), red_dk=Paint(0xB81C1A),
            grey_dk=Paint(0xA6A9AC), roof=Paint(0xAEB2B6, top=0x9EA2A6),
            frame=Paint(0x3C3F42), door=Paint(0xF0F1F1), doorframe=(0x4A, 0x4D, 0x50),
            doorsplit=Paint(0x6A6D70), skirt=Paint(0x3A3C3E),
            front_band=Paint(0x4E5256), front_up=Paint(0xD62420), front_lo=Paint(0xD62420),
            beam=Paint(0x333537), dome=Paint(0xB4B8BC, top=0xA4A8AC))
    if name == "cityjet":
        return dict(
            name=name, white=Paint(0xF1F1F1), red=Paint(0xDC1E1A), orange=Paint(0xEE5A1E),
            orange2=Paint(0xF27538), black=Paint(0x1E2022), lowband=Paint(0x3E4246),
            roof=Paint(0xCACDCF, top=0xB4B8BA), frame=Paint(0x1E2022),
            door=Paint(0x3A3E42), doorframe=(0x1A, 0x1C, 0x1E), doorsplit=Paint(0xC8CCCE),
            step=Paint(0xE8C21A), skirt=Paint(0x2E3032), script=Paint(0x9A9EA2),
            logo=Paint(0xD8202A), mask=Paint(0x222426), outline=Paint(0xDC1E1A),
            beam=Paint(0x252729), dome=Paint(0x222426, top=0x2A2C2E))
    raise ValueError(name)


LIVERIES = ["cityshuttle", "cityjet"]


# ------------------------------------------------------------------ lettering
def wiesel_logo(xr, zr):
    """Dark blob with an orange weasel, 2.3 m x 1.2 m (xr, zr from its lower left
    as seen); returns a Paint or None."""
    if not (0.0 <= xr <= 2.3 and 0.0 <= zr <= 1.2):
        return None
    # ragged blob: trim the corners
    if (xr < 0.25 and zr > 0.8) or (xr > 2.05 and zr < 0.3) or (xr < 0.15 and zr < 0.2):
        return None
    # weasel: long body leaping to the right, head up at the right end
    if 0.35 <= xr <= 1.95 and 0.38 <= zr <= 0.68:
        return Paint(0xC86A2A)
    if 1.70 <= xr <= 2.05 and 0.62 <= zr <= 0.98:
        return Paint(0xC86A2A)
    if 1.30 <= xr <= 1.70 and 0.30 <= zr <= 0.42:
        return Paint(0xF0E6D8)          # white chest
    return Paint(0x3C3D40)


def wiesel_word(xr, zr):
    """'WIESEL' in grey capitals, 1.3 m x 0.30 m."""
    if not (0.0 <= xr <= 1.3 and 0.0 <= zr <= 0.30):
        return False
    return int(xr / 0.2167) % 1 == 0 and (xr % 0.2167) < 0.16


def cityjet_word(xr, zr):
    """grey outline 'cityjet' script: letter strokes 2.5 m x 0.55 m."""
    if not (0.0 <= xr <= 2.5 and 0.0 <= zr <= 0.55):
        return False
    if zr <= 0.30:
        return (xr % 0.36) < 0.24
    for (a, b) in ((0.40, 0.50), (0.78, 0.88), (1.70, 1.80), (2.25, 2.35)):   # i, t, j, t
        if a <= xr <= b:
            return True
    return False


# ------------------------------------------------------------------ cab nose
def nose_s(z_m):
    """front surface (m behind the buffer face) at height z_m (drawing Bbfmpz-a)."""
    if z_m < 1.25:
        return 0.40
    if z_m < 2.29:
        return 0.42
    if z_m < 3.85:
        return 0.42 + (z_m - 2.29) / 1.56 * 0.83
    t = min(1.0, (z_m - 3.85) / 0.78)
    return 1.25 + 0.75 * t * t


S_CAB = 2.10


def cab_half_width(z_m, ds):
    r = 0.80 if z_m >= 3.85 else (0.40 if z_m >= 2.29 else 0.25)
    if ds >= r:
        return W
    t = 1.0 - ds / r
    return W - 0.55 * r * (1.0 - np.sqrt(max(0.0, 1.0 - t * t)))


# ------------------------------------------------------------------ the car
class Car:
    def __init__(self, lay, liv, owner="C"):
        self.lay, self.C, self.owner = lay, livery(liv), owner
        self.LM = lay["LM"]
        self.M = self.LM / L
        self.cab = lay["cab"]

    def x_of(self, face, s):
        return s if face == "-v" else self.LM - s

    def body_bot(self, s):
        a, b = self.lay["low"]
        return Z_LOW_BOT if a <= s <= b else Z_END_BOT

    # ---- livery base colour at (x, z)
    def base(self, x, z, s):
        C = self.C
        z_m = z * PX
        if C["name"] == "cityshuttle":
            red = x < 11.7 + 3.6 * min(1.0, max(0.0, (z_m - 0.5) / 3.6))
            if z_m < 0.62:
                return C["red_dk"] if red else C["grey_dk"]
            return C["red"] if red else C["grey"]
        # cityjet: white upper, red / orange / light orange / red lower
        if z_m >= 2.29:
            return C["white"]
        if z_m >= 1.80:
            return C["red"]
        if z_m >= 1.46:
            return C["orange"]
        if z_m >= 1.04:
            return C["orange2"]
        if z_m >= 0.56:
            return C["red"]
        return C["skirt"]

    def is_red(self, x, z):
        z_m = z * PX
        return x < 11.7 + 3.6 * min(1.0, max(0.0, (z_m - 0.5) / 3.6))

    # ---- side paint
    def side(self, face, s, z):
        C, lay = self.C, self.lay
        x = self.x_of(face, s)
        z_m = z * PX
        cj = C["name"] == "cityjet"
        if z >= ZS - 0.02:
            return C["roof"]
        # doors (double leaf, centre seal)
        for (a, b) in lay["doors"]:
            if a <= s <= b and Z_D0 <= z <= Z_D1:
                c = (a + b) / 2
                if abs(s - c) < 0.09:
                    return C["doorsplit"]
                if Z_DW0 <= z <= Z_DW1 and (a + 0.22 <= s <= c - 0.24 or c + 0.24 <= s <= b - 0.22):
                    return R.GLASS_HI if z > Z_DW1 - 0.5 else R.GLASS
                if cj and z < Z_D0 + 0.35:
                    return C["step"]
                return C["door"]
        # cab zone: side cab window + cityjet mask
        if self.cab and s < S_CAB + 0.9:
            cp = self.cab_side(face, s, z)
            if cp is not None:
                return cp
        # upper deck windows
        if Z_UP0 <= z <= Z_UP1:
            for (a, b) in lay["upper"] + lay["end_up"]:
                if a <= s <= b:
                    if s - a < 0.10 or b - s < 0.10:
                        return C["frame"]
                    return R.GLASS_HI if z > Z_UP1 - 0.55 else R.GLASS
            if cj:
                ua, ub = lay["upper"][0][0] - 0.1, lay["upper"][-1][1] + 0.1
                if ua <= s <= ub and Z_UP0 - 0.2 <= z <= Z_UP1 + 0.25:
                    return C["black"]           # continuous black band
        if cj and Z_UP1 < z <= Z_UP1 + 0.25:
            ua, ub = lay["upper"][0][0] - 0.1, lay["upper"][-1][1] + 0.1
            if ua <= s <= ub:
                return C["black"]
        if cj and Z_UP0 - 0.25 <= z < Z_UP0:
            ua, ub = lay["upper"][0][0] - 0.1, lay["upper"][-1][1] + 0.1
            if ua <= s <= ub:
                return C["black"]
        # intermediate windows in the end sections
        if Z_MID0 <= z <= Z_MID1:
            for (a, b) in lay["mid"]:
                if a <= s <= b:
                    if s - a < 0.10 or b - s < 0.10:
                        return C["frame"]
                    return R.GLASS_HI if z > Z_MID1 - 0.55 else R.GLASS
        # lower deck windows
        la, lb = lay["lower"][0][0] - 0.1, lay["lower"][-1][1] + 0.1
        if Z_LO0 - (0.25 if cj else 0) <= z <= Z_LO1 + (0.25 if cj else 0) and la <= s <= lb:
            for (a, b) in lay["lower"]:
                if a <= s <= b and Z_LO0 <= z <= Z_LO1:
                    if s - a < 0.10 or b - s < 0.10:
                        return C["frame"] if not cj else C["lowband"]
                    return R.GLASS_HI if z > Z_LO1 - 0.5 else R.GLASS
            if cj:
                return C["lowband"]
        # lettering / logos (read left to right as seen)
        lg = self.letters(face, x, z_m, s)
        if lg is not None:
            return lg
        return self.base(x, z, s)

    def letters(self, face, x, z_m, s):
        C = self.C
        if C["name"] == "cityshuttle":
            red = self.is_red(x, z_m / PX)
            if red:
                sx = 1.9 if not (self.cab and face == "-v") else 2.0
                if CS.cityshuttle_script(x - sx, z_m - 1.30):
                    return WHITE
                return None
            # grey part: Wiesel logo on the coaches and the cab car's left side,
            # red ÖBB on the cab car's right side (drawings / Neulengbach photo)
            if self.cab and face == "+v":
                if CS.obb_logo(x - 15.6, z_m - 2.25, w=1.35, h=0.50):
                    return Paint(0xD62420)
                return None
            wl = wiesel_logo(x - 15.5, z_m - 1.90)
            if wl is not None:
                return wl
            if wiesel_word(x - 13.9, z_m - 2.0):
                return Paint(0x5A5C60)
            return None
        # cityjet: grey script between the decks, red ÖBB on the white near one end
        if 2.45 <= z_m <= 3.05 and cityjet_word(x - 10.4, z_m - 2.48):
            return C["script"]
        la = 3.9 if self.cab else 1.9          # metres from the car front (s)
        if la <= s <= la + 0.9 and 3.05 <= z_m <= 3.35:
            xr = (s - la) if face == "-v" else (la + 0.9 - s)
            if CS.obb_logo(xr, z_m - 3.05, w=0.9, h=0.30):
                return C["logo"]
        return None

    def cab_side(self, face, s, z):
        """cab section side paint near the nose; None = normal side paint."""
        C = self.C
        z_m = z * PX
        cj = C["name"] == "cityjet"
        ns = nose_s(z_m)
        if s < ns + 0.30:
            # the corner / front edge wraps the front colours
            if cj and 2.30 <= z_m < 4.40:
                return C["outline"]             # red line along the front edge
            return self.front(z_m, 0.0, top=True)
        if cj:
            # white cab side with the big dark driver's window (photo Marchegg,
            # drawing Bbfmpz-cj): plain glass, never lit
            if 0.95 <= s <= 2.60 and 2.40 <= z_m <= 3.40:
                return WS_HI if z_m > 3.20 else WS
            return None
        # classic: the dark grey windscreen band wraps round the cab side and
        # holds the driver's window (photos Neulengbach 86-33 013, Wien 86-33 112)
        if s < 2.65 and 2.30 <= z_m <= 3.22:
            if 1.65 <= s <= 2.55 and 2.40 <= z_m <= 3.12:
                return WS_HI if z_m > 2.95 else WS
            return C["front_band"]
        return None

    # ---- front
    def front(self, z_m, vl, top=False):
        """cab front paint; vl lateral (+ = car's right = viewer's left)."""
        C = self.C
        av = abs(vl)
        cj = C["name"] == "cityjet"
        if z_m >= 3.85:
            return C["dome"]
        if z_m < 1.25:
            return C["beam"]
        if cj:
            # black mask from the dome to below the windscreen, framed red
            if z_m >= 2.40:
                if not top and av < W - 0.14 and 2.55 <= z_m <= 3.55:
                    return WS_HI if z_m > 3.35 else WS
                if av > W - 0.08:
                    return C["outline"]
                return C["mask"]
            if z_m >= 2.30:
                return C["outline"]             # red line under the windscreen
            if z_m >= 1.88:
                if not top and 1.98 <= z_m <= 2.20 and -0.05 <= vl <= 0.40 and not (0.12 <= vl <= 0.16):
                    return C["logo"]            # red ÖBB on the white band
                return C["white"]
            if not top and 1.45 <= z_m <= 1.75 and 0.50 <= av <= 0.80:
                return R.HEAD
            if not top and 1.47 <= z_m <= 1.70 and 0.36 <= av < 0.48:
                return TAIL_OFF
            return self.base(99.0, z_m / PX, 0.0)   # the side bands run round the nose
        # classic
        if z_m >= 3.30:
            if not top and 3.50 <= z_m <= 3.72 and av < 0.10:
                return R.HEAD                   # top marker lamp
            if not top and 3.50 <= z_m <= 3.70 and 0.20 <= av <= 0.42:
                return Paint(0x7A1814)          # the two vents
            return C["front_up"]
        if z_m >= 2.30:
            if not top and av < W - 0.12 and 2.40 <= z_m <= 3.22:
                return WS_HI if z_m > 3.05 else WS
            return C["front_band"]
        if not top:
            if 1.52 <= z_m <= 1.76 and 0.46 <= av <= 0.80:
                return R.HEAD
            if 1.54 <= z_m <= 1.72 and 0.36 <= av < 0.44:
                return TAIL_OFF
            if 1.98 <= z_m <= 2.18 and -0.05 <= vl <= 0.40 and not (0.12 <= vl <= 0.16):
                return WHITE                     # ÖBB
        return C["front_lo"]

    # ---- material dispatcher
    def mat(self, f, u, v, z, d):
        s = u * self.M
        z_m = z * PX
        if self.cab and s < S_CAB + 0.05:
            if f == "-u":
                return self.front(z_m, v)
            if f == "+z" and z < ZR - 0.05:
                return self.front(z_m, v, top=True)
        if f == "+z":
            if z < ZS - 0.05:
                # tops of the leaning-wall steps: they read as the side wall
                return self.side("+v" if v > 0 else "-v", s, z - 0.01)
            return self.C["roof"]
        if f in ("+v", "-v"):
            if z >= ZS - 0.02:
                return self.C["roof"]
            return self.side(f, s, z)
        # coupled end face: gangway door
        if abs(v) < 0.40 and 2.8 < z < ZS - 0.8:
            return BELLOWS
        return self.base(99.0, z, s)          # end walls: grey (classic) / banded (cityjet)

    # ---- geometry
    def parts(self):
        P = []
        lay, M, own, mat = self.lay, self.M, self.owner, self.mat
        LM = self.LM
        s0 = 0.28                          # body ends (buffers / gangway in front)
        if self.cab:
            zs = [Z_END_BOT, zm(1.25)] + list(np.arange(zm(1.25) + 0.45, ZR, 0.42)) + [ZR]
            zs = sorted(set(round(z, 3) for z in zs))
            for i in range(len(zs) - 1):
                z0, z1 = zs[i], zs[i + 1]
                zc = (z0 + z1) / 2 * PX
                sf = nose_s(zc)
                if sf >= S_CAB:
                    continue
                for (a, b) in ((0.0, 0.10), (0.10, 0.25), (0.25, 0.50), (0.50, S_CAB - sf)):
                    if b <= a:
                        continue
                    hw = cab_half_width(zc, (a + b) / 2)
                    hw = min(hw, self.roof_hw(z0))
                    P.append(Part((sf + a) / M, (sf + b) / M, -hw, hw, z0, z1, mat, own))
            s0 = S_CAB
        # main body: end sections + low middle (per slab of the leaning profile)
        a_low, b_low = lay["low"]
        for (sa, sb, zb) in ((s0, a_low, Z_END_BOT), (a_low, b_low, Z_LOW_BOT), (b_low, LM - 0.28, Z_END_BOT)):
            P.append(Part(sa / M, sb / M, -W, W, zb, ZLEAN, mat, own))
        # upper deck wall (drawn vertical: the real lean of ~0.1 m is sub-pixel,
        # and its sliver of top face only produced stray 1-px lines in nw/se)
        P.append(Part(s0 / M, (LM - 0.28) / M, -W, W, ZLEAN, ZS, mat, own))
        # roof: three slabs of a rounded profile
        for (z0, z1) in ((ZS, zm(4.34)), (zm(4.34), zm(4.52)), (zm(4.52), ZR)):
            hw = self.roof_hw(z0)
            P.append(Part(s0 / M, (LM - 0.34) / M, -hw, hw, z0, z1, mat, own))
        # gangway + buffers at the coupled end(s)
        ends = [((LM - 0.28) / M, L - 0.02)]
        if not self.cab:
            ends.append((0.02, 0.28 / M))
        for (a, b) in ends:
            P.append(Part(a, b, -0.40, 0.40, zm(1.2), zm(3.3), lambda *x: BELLOWS, own))
            for vc in (-0.64, 0.64):
                P.append(Part(a, b, vc - 0.13, vc + 0.13, zm(0.88), zm(1.18), lambda *x: BUFFER, own))
        if self.cab:
            for vc in (-0.64, 0.64):
                P.append(Part(0.0, 0.40 / M, vc - 0.13, vc + 0.13, zm(0.88), zm(1.18), lambda *x: BUFFER, own))
            P.append(Part(0.05, 0.42 / M, -0.24, 0.24, zm(0.55), zm(1.25), lambda *x: BUFFER, own))
        # underframe: bogies + equipment under the end sections
        for bm in lay["bogies"]:
            bc = bm / M
            P.append(Part(bc - 0.75, bc + 0.75, -W + 0.12, W - 0.12, 0.0, Z_END_BOT + 0.01,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.7) else BOGIE,
                          own))
        # roof equipment: AC units over the end sections
        for (a, b) in ((1.0 if not self.cab else 2.6, 4.6), (22.0, 25.2)):
            P.append(Part(a / M, b / M, -0.40, 0.40, ZR - 0.05, ZR + 0.30,
                          lambda *x: Paint(0x9A9EA2, top=0x8C9094), own))
        return P

    @staticmethod
    def roof_hw(z0):
        if z0 < ZS - 0.01:
            return W
        if z0 < zm(4.34) - 0.01:
            return W - 0.14
        if z0 < zm(4.52) - 0.01:
            return W - 0.30
        return W - 0.50

    def lines(self, d):
        """1-px door outlines on the visible side."""
        C = self.C
        spans = [(a / self.M, b / self.M) for (a, b) in self.lay["doors"]]
        return CS.outline_lines(d, spans, W, Z_D0, Z_D1, C["doorframe"], self.owner)


KINDS = [(CAB, "86-33"), (COACH, "26-33")]


def rows(liv):
    out = []
    for lay, _ in KINDS:
        car = Car(lay, liv)
        P = car.parts()
        out.append([R.vehicle_tile(P, car.lines(d), d, 0.0, {"C"}) for d in DIRS])
    return out


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        prev = args[args.index("--preview") + 1]
        os.makedirs(prev, exist_ok=True)
    for liv in LIVERIES:
        rr = rows(liv)
        out = os.path.join(REPO, "vehicle-rail", "obb", "dosto", "sprites", f"{liv}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        R.save_rows(rr, out)
        print("wrote", os.path.relpath(out, REPO))
        if prev:
            R.preview(rr, os.path.join(prev, f"dosto_{liv}.png"), z=4, labels=[k for _, k in KINDS])


if __name__ == "__main__":
    main()
