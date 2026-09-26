#!/usr/bin/env python3
"""ÖBB class 4746 "Cityjet" (Siemens Desiro ML), 3-car EMU, drawn with the
pak128.cs calibrated box renderer (render.py / railkit.py).

    python tools/railrender/obb_cityjet.py [--preview DIR]

writes vehicle-rail/obb/4746/sprites/cityjet.png, row 0 = cab car A (leading,
headlights), row 1 = middle car, row 2 = cab car B (tail lights).

Real unit (research E5, vagonWEB drawing 4746-a scaled to 75.15 m): three cars
on two bogies each (Bo'2' + 2'2' + 2'Bo'), 24.7 + 25.8 + 24.7 m, 2.82 m wide;
each car has two double doors per side; the end cars have high-floor windows
over the bogies and a low-floor black window band between the doors; one
pantograph on car B next to the middle car (drawn raised).
Modelled on one u axis: car lengths 12 + 13 + 12 carunits (37 cu = 75.1 m),
car k's front at u = 0, 12, 25.  Car B is car A turned 180 degrees.

Livery Cityjet (photos 18.07.26 Tulln an der Donau 4746 113, 4746.054
Hausleiten 2020, 4746 013 Bahnhof Wolkersdorf 2017; vagonWEB 4746-a): white
upper body; the lower body red / orange / red in horizontal bands; windows in
black frames, the low-floor windows in one black band; dark doors with a light
centre seal; grey "cityjet" script and red ÖBB logos on the white. Front: huge
dark windscreen framed silver-grey with a red outline, light grey band with a
red ÖBB below it, red lower front with the lamp clusters, black coupler area.
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
W = R.W_STD * 2.82 / 2.825              # 0.918 cu
LENGTHS = [12, 13, 12]
U0 = [0, 12, 25]
UEND = 37.0
MLEN = [24.67, 25.80, 24.67]            # metres per car (coupler / joint to joint)
MPC = [m / l for m, l in zip(MLEN, LENGTHS)]
HALFJ = 0.16                            # body end gap either side of a joint (cu)


def zm(h):
    return h / PX


ZS = zm(3.75)                           # side wall top
ZR = zm(4.10)                           # roof top
Z_BOT = zm(0.46)                        # body bottom (skirt)
Z_BOG = zm(0.95)                        # body bottom over the bogies

# livery bands (m)
B_WHITE, B_RED1, B_OR, B_RED2 = 2.62, 2.42, 1.37, 0.95   # Hausleiten photo + drawing 4746-a

# high-floor windows, low-floor band, doors: metres from the car's A end
END = dict(
    high=[(4.30, 6.40), (19.20, 21.30), (21.50, 23.60)],
    band=(9.45, 16.10), panes=[(9.60, 11.40), (11.60, 13.80), (14.00, 15.95)],
    doors=[(7.20, 8.75), (16.85, 18.40)],
    cabwin=(1.85, 3.50),
    script=(9.60, 12.40), logos=[4.40],
    bogies=[4.30, 21.10],
)
MID = dict(
    high=[(1.00, 3.10), (3.30, 5.45), (20.35, 22.50), (22.70, 24.80)],
    band=(8.50, 17.30), panes=[(8.65, 10.75), (10.95, 13.05), (13.25, 15.10), (15.30, 17.15)],
    doors=[(6.25, 7.80), (18.00, 19.55)],
    cabwin=None, script=None, logos=[1.00, 23.95],
    bogies=[3.50, 22.30],
)
Z_HI0, Z_HI1 = 1.96, 3.11              # high-floor windows (m)
Z_BA0, Z_BA1 = 1.50, 2.65              # low-floor black band
Z_PA0, Z_PA1 = 1.62, 2.55              # its panes
Z_D0, Z_D1 = 0.69, 3.34                # doors
Z_DW0, Z_DW1 = 1.20, 3.10              # door windows

WHITE = Paint(0xF1F1F1)
RED = Paint(0xDE1E1A)
ORANGE = Paint(0xF06428)
BLACK = Paint(0x1C1D1F)
SKIRT = Paint(0x2A2C2E)
ROOF = Paint(0xE4E6E7, top=0xB2B6B9)          # white roof shoulder, light grey top
ROOFEQ = Paint(0x55595D, top=0x4A4E52)          # dark roof fairings (photos)
ROOFEQ2 = Paint(0x44484C, top=0x3A3E42)
GREYBAND = Paint(0xD6D8DA)
SILVER = Paint(0xC4C7CA)
DOOR = Paint(0x34373A)
SEAL = Paint(0xD4D6D8)
SCRIPT = Paint(0x9A9EA2)
LOGO = Paint(0xD8202A)
BOGIE = Paint(0x232426)
BOGIE_HI = Paint(0x3E4144)
UNDER = Paint(0x1E1F21)
BELLOWS = Paint(0x2C2E31, top=0x3A3C40)
WS = (0x26, 0x30, 0x3A)
WS_HI = (0x4A, 0x5C, 0x6C)
AMBER = (0xF0, 0xA0, 0x18)


# ---------------------------------------------------------------- nose
def nose_m(z_m):
    """front surface (m behind the coupler face) at height z_m (drawing 4746-a)."""
    if z_m < 0.92:
        return 0.30
    if z_m < 1.55:
        return 0.12                       # black bumper / coupler block
    if z_m < 2.30:
        return 0.30
    if z_m < 3.80:
        return 0.34 + (z_m - 2.30) / 1.50 * 0.96
    return 1.30 + (z_m - 3.80) / 0.30 * 1.00


M_CAB = 2.60                              # nose slabs end here (m)


def half_width(z_m, dm):
    r = 0.95 if z_m >= 2.3 else 0.45
    if dm >= r:
        return W
    t = 1.0 - dm / r
    return W - 0.42 * r * (1.0 - np.sqrt(max(0.0, 1.0 - t * t)))


def front(z_m, vl, lamp, top=False):
    av = abs(vl)
    if z_m < 0.92:
        return SKIRT
    if z_m < 1.55:
        return BLACK
    if z_m < 2.25:
        if not top and 1.78 <= z_m <= 2.10 and 0.50 <= av <= 0.82:
            return lamp
        if not top and 1.72 <= z_m <= 2.16 and 0.44 <= av <= 0.86:
            return BLACK                  # lamp cluster housing
        return RED
    if z_m < 2.58:
        if not top and 2.32 <= z_m <= 2.50 and -0.05 <= vl <= 0.38 and not (0.11 <= vl <= 0.15):
            return LOGO                   # ÖBB
        return GREYBAND
    if av > W - 0.10:
        return RED                        # red outline of the windscreen frame
    if z_m < 3.78:
        if top:
            return WS
        if av < W - 0.22:
            if 3.52 <= z_m <= 3.72 and av < 0.45:
                return AMBER if 3.58 <= z_m <= 3.66 else (0x1A, 0x1C, 0x1E)   # destination
            return WS_HI if (z_m > 3.2 and vl > 0.15) else WS
        return SILVER
    return SILVER


# ---------------------------------------------------------------- unit
class Unit:
    def __init__(self):
        self.parts = []
        self.lines = []
        self.build()

    @staticmethod
    def car_of(u):
        for k in (2, 1, 0):
            if u >= U0[k] - 1e-6:
                return k
        return 0

    @staticmethod
    def local_m(k, u):
        """metres from the car's A end (car A/M: its front; car B: its cab nose)."""
        if k == 2:
            return (UEND - u) * MPC[2]
        return (u - U0[k]) * MPC[k]

    @staticmethod
    def reads_up(k, face):
        """True if m grows to the screen-right on this face (for lettering)."""
        # -v: screen-right = larger u; +v: screen-right = smaller u
        grows_with_u = k != 2
        return grows_with_u == (face == "-v")

    def side(self, k, face, m, z):
        z_m = z * PX
        lay = MID if k == 1 else END
        if z >= ZS - 0.02:
            return ROOF
        # doors
        for (a, b) in lay["doors"]:
            if a <= m <= b and zm(Z_D0) <= z <= zm(Z_D1):
                c = (a + b) / 2
                if abs(m - c) < 0.08:
                    return SEAL
                if zm(Z_DW0) <= z <= zm(Z_DW1) and (a + 0.16 <= m <= c - 0.14 or c + 0.14 <= m <= b - 0.16):
                    return R.GLASS_HI if z_m > Z_DW1 - 0.25 else R.GLASS
                return DOOR
        # cab side window (plain)
        if lay["cabwin"] is not None:
            a, b = lay["cabwin"]
            b2 = b - (z_m - 2.30) * 0.9          # raked rear edge
            if a - (z_m - 2.3) * 0.5 <= m <= b2 and 2.30 <= z_m <= 3.34:
                if m > b2 - 0.15 or z_m < 2.40:
                    return BLACK
                return WS_HI if z_m > 3.10 else WS
        # high-floor windows
        for (a, b) in lay["high"]:
            if a <= m <= b and Z_HI0 <= z_m <= Z_HI1:
                if m - a < 0.12 or b - m < 0.12 or z_m < Z_HI0 + 0.10 or z_m > Z_HI1 - 0.10:
                    return BLACK
                return R.GLASS_HI if z_m > Z_HI1 - 0.30 else R.GLASS
        # low-floor band
        a, b = lay["band"]
        if a <= m <= b and Z_BA0 <= z_m <= Z_BA1:
            for (pa, pb) in lay["panes"]:
                if pa <= m <= pb and Z_PA0 <= z_m <= Z_PA1:
                    return R.GLASS_HI if z_m > Z_PA1 - 0.28 else R.GLASS
            return BLACK
        # lettering on the white
        up = self.reads_up(k, face)
        if lay["script"] is not None:
            sa, sb = lay["script"]
            if sa <= m <= sb and 2.86 <= z_m <= 3.46:
                xr = (m - sa) if up else (sb - m)
                if cityjet_script(xr, z_m - 2.88):
                    return SCRIPT
        for la in lay["logos"]:
            if la <= m <= la + 0.85 and 3.10 <= z_m <= 3.44:
                xr = (m - la) if up else (la + 0.85 - m)
                if CS.obb_logo(xr, z_m - 3.10, w=0.85, h=0.34):
                    return LOGO
        return band(z_m)

    def mat_for(self, k):
        lamp = R.HEAD if k == 0 else R.TAIL

        def mat(f, u, v, z, d):
            m = self.local_m(k, u)
            z_m = z * PX
            if k in (0, 2) and m < M_CAB + 0.05:
                # cab: faces pointing out of the unit are the front
                outward = (f == "-u") if k == 0 else (f == "+u")
                vl = v if k == 0 else -v
                if outward:
                    return front(z_m, vl, lamp)
                if f == "+z" and z < ZR - 0.05:
                    return front(z_m, vl, lamp, top=True)
                if f in ("+v", "-v"):
                    if z >= ZS - 0.02:
                        return front(z_m, vl, lamp, top=True) if m < nose_m(z_m) + 0.5 else ROOF
                    if m < nose_m(z_m) + 0.22:
                        if z_m >= 2.58:
                            return RED                   # red outline round the front
                        return front(z_m, vl, lamp, top=True)
                    return self.side(k, f, m, z)
            if f == "+z":
                return ROOF
            if f in ("+v", "-v"):
                return self.side(k, f, m, z)
            return band(z_m) if z_m < B_WHITE else WHITE
        return mat

    def add(self, k, m0, m1, v0, v1, z0, z1, mat):
        """box in car-local metres."""
        if k == 2:
            a, b = UEND - m1 / MPC[2], UEND - m0 / MPC[2]
        else:
            a, b = U0[k] + m0 / MPC[k], U0[k] + m1 / MPC[k]
        self.parts.append(Part(a, b, v0, v1, z0, z1, mat, f"c{k}"))

    def build(self):
        for k in range(3):
            mat = self.mat_for(k)
            L_m = MLEN[k]
            lay = MID if k == 1 else END
            j = HALFJ * MPC[k]
            m0 = j if k == 1 else M_CAB
            m1 = L_m - j
            if k in (0, 2):
                # nose slabs
                layers = [(Z_BOT, zm(0.92)), (zm(0.92), zm(1.55)), (zm(1.55), zm(2.30))]
                z = zm(2.30)
                while z < ZR - 1e-6:
                    layers.append((z, min(ZR, z + 0.45)))
                    z += 0.45
                for (z0, z1) in layers:
                    zc = (z0 + z1) / 2 * PX
                    nf = nose_m(zc)
                    if nf >= M_CAB:
                        continue
                    hwmax = W - 0.14 if z0 >= ZS - 0.01 else W
                    for (a, b) in ((0.0, 0.12), (0.12, 0.30), (0.30, 0.60), (0.60, M_CAB - nf)):
                        if b <= a:
                            continue
                        hw = min(hwmax, half_width(zc, (a + b) / 2))
                        if zc < 1.55 and zc >= 0.92:
                            hw = min(hw, W - 0.12)
                        self.add(k, nf + a, nf + b, -hw, hw, z0, z1, mat)
            # body: bogie zones raised, low middle
            bz = [(bc - 1.45, bc + 1.45) for bc in lay["bogies"]]
            edges = sorted(set([m0, m1] + [min(max(e, m0), m1) for c in bz for e in c]))
            for i in range(len(edges) - 1):
                a, b = edges[i], edges[i + 1]
                mid = (a + b) / 2
                zb = Z_BOG if any(c0 <= mid <= c1 for (c0, c1) in bz) else Z_BOT
                self.add(k, a, b, -W, W, zb, ZS, mat)
            self.add(k, m0, m1 - 0.05, -W + 0.14, W - 0.14, ZS, ZR, mat)
            # bogies + underfloor equipment
            for bc in lay["bogies"]:
                self.add(k, bc - 1.35, bc + 1.35, -W + 0.12, W - 0.12, 0.0, Z_BOG + 0.01,
                         lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.7) else BOGIE)
            if k in (0, 2):
                self.add(k, 0.02, 0.35, -0.20, 0.20, zm(0.95), zm(1.40), lambda *x: BLACK)   # coupler
        # joints: bellows owned by the car in front
        for jk, J in ((0, 12.0), (1, 25.0)):
            self.parts.append(Part(J - HALFJ - 0.03, J + HALFJ + 0.03, -W + 0.18, W - 0.18, zm(0.9), ZS + 0.2,
                                   lambda *x: BELLOWS, f"c{jk}"))
        self.build_roof()

    def build_roof(self):
        eq = lambda *x: ROOFEQ          # noqa: E731
        eq2 = lambda *x: ROOFEQ2        # noqa: E731
        zt = ZR - 0.05
        for k in (0, 2):
            self.add(k, 4.4, 6.0, -0.55, 0.55, zt, ZR + 0.45, eq)
            self.add(k, 6.2, 7.5, -0.50, 0.50, zt, ZR + 0.80, eq2)
            self.add(k, 8.6, 15.6, -0.62, 0.62, zt, ZR + 0.40, eq)
            self.add(k, 15.9, 18.6, -0.55, 0.55, zt, ZR + 0.55, eq)
            self.add(k, 19.0, 21.0, -0.45, 0.45, zt, ZR + 0.70, eq2)
        self.add(1, 9.6, 16.4, -0.62, 0.62, zt, ZR + 0.40, eq)
        # pantograph on car B next to the middle car, raised, knee towards the joint
        base_m = MLEN[2] - 3.4
        ub = UEND - base_m / MPC[2]
        self.add(2, base_m - 0.9, base_m + 0.9, -0.45, 0.45, zt, ZR + 0.35, lambda *x: Paint(0x55595E, top=0x6A6E72))
        self.lines += R.pantograph(ub, ZR + 0.35, "c2", fold=-1, reach=0.95, height=5.6,
                                   col=(0x70, 0x74, 0x78), head=(0x2A, 0x2A, 0x2C), half_head=0.62,
                                   thick=False)


def band(z_m):
    if z_m >= B_WHITE:
        return WHITE
    if z_m >= B_RED1:
        return RED
    if z_m >= B_OR:
        return ORANGE
    if z_m >= B_RED2:
        return RED
    return SKIRT


def cityjet_script(xr, zr):
    """grey 'cityjet' script: letter strokes 2.8 m x 0.58 m, xr as read."""
    if not (0.0 <= xr <= 2.8 and 0.0 <= zr <= 0.58):
        return False
    if zr <= 0.32:
        return (xr % 0.40) < 0.26
    for (a, b) in ((0.45, 0.56), (0.86, 0.97), (1.90, 2.01), (2.52, 2.63)):
        if a <= xr <= b:
            return True
    return False


LABELS = ["4746-A", "4746-M", "4746-B"]


def render_unit():
    un = Unit()
    rows = []
    for k in range(3):
        lo, hi = U0[k] - 3.0, U0[k] + LENGTHS[k] + 3.0
        parts = [p for p in un.parts if p.b[1] >= lo and p.b[0] <= hi]
        lines = [l for l in un.lines if lo <= l[0][0] <= hi]
        rows.append([R.vehicle_tile(parts, lines, d, float(U0[k]), {f"c{k}"}) for d in DIRS])
    return rows


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        prev = args[args.index("--preview") + 1]
        os.makedirs(prev, exist_ok=True)
    rr = render_unit()
    out = os.path.join(REPO, "vehicle-rail", "obb", "4746", "sprites", "cityjet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    R.save_rows(rr, out)
    print("wrote", os.path.relpath(out, REPO))
    if prev:
        R.preview(rr, os.path.join(prev, "4746_cityjet.png"), z=4, labels=LABELS)


if __name__ == "__main__":
    main()
