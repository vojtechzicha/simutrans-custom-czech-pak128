"""KŽC UIC-Y compartment coaches (VEB Waggonbau Bautzen, ČSD 1965-85) in the
historic ČSD dark green: B (B256/249 type), BDs (2nd class + luggage room),
RBDs "RychBar" (BDs with a bar compartment) and A (1st class).

24.5 m over buffers -> length 12 (like the pak128.cs Y coach CD_B249, 2.04 m
per cu). Window / door positions from the KŽC side drawings
(kzc.cz/image/B_272-6.png, BDs_328-2, RBDs_422-2, A_092-0; 75.6 px/m, x from
the left buffer face), heights from the same drawings (rail at y 330).
The luggage room / bar is at the same physical end on both sides.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import railkit as R
from railkit import Paint, Part
from render import DIRS

L = 12.0
LM = 24.5
M = LM / L
W = R.W_STD
PXM = 75.6            # drawing px per metre


def zm(h):
    return h / 0.375


def dm(x):
    """drawing x -> metres from the car's front buffer face"""
    return x / PXM


ZB = zm(0.95)          # body bottom (black sill / solebar)
Z_SILL = zm(1.20)      # green starts
Z_GREEN = zm(3.50)     # green ends at the gutter (natives: side colour up to ~z 9.5)
ZS = R.H_SIDE          # 10.0 wall top
ZR = ZS + R.H_CAP
WIN_Z = (zm(2.22), zm(2.95))

GREEN = Paint(0x486845)
ROOF = Paint(0xA8AAA4, top=0xB2B4AE)
ROOF_SIDE = Paint(0x9C9E99)
ROOF_MID = Paint(0x9EA09B, top=0xA4A6A0)
ROOF_EDGE = Paint(0x979994, top=0x979994)
SILL = Paint(0x262826)
DOOR_LINE = Paint(0x22301F)
YELLOW = Paint(0xE8C818)
RED = Paint(0xC0262C)
UNDER = Paint(0x2E302E)
BOGIE = Paint(0x262727)
BOGIE_HI = Paint(0x3A3C3B)
GANG = Paint(0x2B2D2B)
FROST = Paint(0x8E968E)
FRAME = Paint(0xA9AEA8)

B_WIN = [(234, 313), (379, 458), (523, 602), (667, 746), (812, 891),
         (962, 1041), (1107, 1186), (1251, 1330), (1395, 1474), (1540, 1619)]
A_WIN = [(234, 313), (398, 477), (560, 639), (722, 801), (884, 963),
         (1052, 1131), (1214, 1293), (1376, 1455), (1540, 1619)]
SMALL = [(139, 183), (1670, 1714)]          # vestibule / WC windows
DOORS = [(35, 116), (1737, 1818)]          # end doors (leaf incl. frame)
DOOR_WIN = [(70, 87), (1766, 1783)]

KINDS = {
    "B": dict(win=B_WIN + SMALL, lug=None, stripe=None, text=None, cls="2"),
    "BDs": dict(win=B_WIN[5:] + SMALL + [(799, 843)], lug=(528, 659), service=[(256, 265), (273, 305), (313, 322)],
                stripe=None, text=None, cls="2"),
    "RBDs": dict(win=B_WIN[5:] + SMALL + [(799, 843)], lug=(528, 659), service=[(256, 265), (273, 305), (313, 322)],
                 stripe=(RED, 117, 919), text=(388, 470), cls="2"),
    "A": dict(win=A_WIN + SMALL, lug=None, stripe=(YELLOW, 117, 1736), text=None, cls="1"),
}
LABELS = ["B", "BDs", "RBDs", "A"]


def coach(kind, u0=0.0, owner="C"):
    K = KINDS[kind]
    parts = []

    def xm(u):
        return (u - u0) * M          # metres from the front buffer face

    def side(f, u, v, z, d):
        m = xm(u)
        x = m * PXM
        if z < Z_SILL:
            # black sill with the yellow data lettering in the middle
            if 11.0 <= m <= 13.0 and zm(1.12) <= z <= zm(1.22):
                return YELLOW
            return SILL
        # end doors: framed leaves reaching the sill, door window
        for (a, b), (wa, wb) in zip(DOORS, DOOR_WIN):
            if a <= x <= b and z <= zm(3.15):
                if x - a < 15 or b - x < 15 or z > zm(3.08):
                    return DOOR_LINE
                if wa - 8 <= x <= wb + 8 and zm(2.20) <= z <= zm(2.92):
                    return R.GLASS
                return GREEN
        if K["lug"] is not None:
            a, b = K["lug"]
            if a <= x <= b and z <= zm(3.15):
                mid = (a + b) / 2
                if x - a < 8 or b - x < 8 or abs(x - mid) < 5 or z > zm(3.08):
                    return DOOR_LINE
                if zm(2.20) <= z <= zm(2.92) and (550 <= x <= 569 or 618 <= x <= 637):
                    return FROST
                return GREEN
            for (sa, sb) in K["service"]:
                if sa <= x <= sb and WIN_Z[0] <= z <= WIN_Z[1]:
                    return R.GLASS_HI if z > WIN_Z[1] - 0.5 else R.GLASS
        for (a, b) in K["win"]:
            if a - 3 <= x <= b + 3 and WIN_Z[0] - 0.85 <= z <= WIN_Z[1]:
                if z < WIN_Z[0]:
                    return FRAME              # aluminium window frame / sill
                # daylight reflections: the lighter lit special on most of the pane
                return R.GLASS if z < WIN_Z[0] + 0.7 else R.GLASS_HI
        if K["stripe"] is not None:
            p, a, b = K["stripe"]
            if a <= x <= b and zm(3.22) <= z <= zm(3.50):
                return p
        if K["text"] is not None:
            a, b = K["text"]
            if a <= x <= b and zm(2.45) <= z <= zm(2.72):
                return YELLOW                 # "RychBar" script
        if z >= Z_GREEN:
            return ROOF_SIDE
        return GREEN

    def end(f, u, v, z, d):
        if abs(v) < 0.40 and ZB < z < Z_GREEN - 0.3:
            return GANG
        if z >= Z_GREEN:
            return ROOF_SIDE
        if z < Z_SILL:
            return SILL
        return GREEN

    def body_mat(f, u, v, z, d):
        if f == "+z":
            return ROOF_EDGE
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        return end(f, u, v, z, d)

    ub0, ub1 = u0 + 0.12, u0 + L - 0.12
    parts.append(Part(ub0, ub1, -W, W, ZB, ZS, body_mat, owner))
    # rounded roof: two caps, lighter towards the ridge
    parts.append(Part(ub0 + 0.04, ub1 - 0.04, -W + 0.2, W - 0.2, ZS, ZS + 0.45,
                      lambda *a: ROOF_MID, owner))
    parts.append(Part(ub0 + 0.08, ub1 - 0.08, -W + 0.46, W - 0.46, ZS + 0.45, ZR, lambda *a: ROOF, owner))
    # gangways + buffers
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        parts.append(Part(a, b, -0.40, 0.40, 2.8, ZS - 1.2, lambda *a: GANG, owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *a: Paint(0x1E2022), owner))
    # entrance steps under the end doors (yellow step edges)
    for (a, b) in DOORS:
        ua, ub = u0 + dm(a + 8) / M, u0 + dm(b - 8) / M

        def step(f, u, v, z, d):
            if f in ("+v", "-v") and abs(z - zm(0.55)) < 0.3:
                return YELLOW
            return Paint(0x2A2B2A)
        parts.append(Part(ua, ub, -W + 0.04, W - 0.04, zm(0.45), ZB, step, owner))
    # underframe equipment + bogies (Görlitz V, centres 3.87 / 20.70 m)
    parts.append(Part(u0 + 9.0 / M, u0 + 15.4 / M, -W + 0.28, W - 0.28, zm(0.45), ZB,
                      lambda *a: UNDER, owner))
    for bm in (3.87, 20.70):
        bc = u0 + bm / M
        parts.append(Part(bc - 1.65 / M, bc + 1.65 / M, -W + 0.12, W - 0.12, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.1 < z < 2.0) else BOGIE,
                          owner))
    return parts


def rows():
    out = []
    for k in LABELS:
        parts = coach(k)
        out.append([R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS])
    return out
