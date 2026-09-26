"""KŽC Bix / RBix "Bixovna": lightweight 4-axle trailers (Vagónka Tatra
Studénka 1958-69, ČSD Balm -> Bix 020) in the ČSD cream-red scheme.

18.5 m over buffers -> length 9 (2.06 m per cu, the pak128.cs coach scale).
Positions from the KŽC side drawings kzc.cz/image/Bix_020.208-2.png and
RBix_020.687-7.png (1338 px = 18.5 m, 72.3 px/m; rail at y 318): rounded
ends with a sloping roof, two inboard doors reaching the steps, 12 windows
per side incl. the large end windows. RBix: red line under the roof edge and
the yellow "BAROVÝ VŮZ" lettering (photos kzc.cz RBix 687 / Commons Rudná).
There is no pak128.CS or installed art of a Bix; this is rendered with the
railrender conventions of ric.py (railkit anchors), colours matched to the
pak128.CS Balm-d that runs in the same trains.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS

L = 9.0
LM = 18.5
M = LM / L
W = 0.92 * 2.90 / 2.825
PXM = 1338 / 18.5


def zm(h):
    return h / 0.375


def xm_(x):
    return x / PXM


ZB = zm(0.75)          # body bottom at the bogies
ZSK = zm(0.60)         # skirt bottom between the bogies
Z_RED = zm(1.87)       # red / cream boundary
ZW = zm(3.34)          # wall top (cream up to the roof)
Z1 = ZW + 0.55
Z2 = zm(3.80)
WIN_Z = (zm(2.09), zm(2.96))

CREAM = Paint(0xEFE9C2)
RED = Paint(0xB8262E)
ROOF = Paint(0xA9A9A6, top=0xB3B3B0)
ROOF_MID = Paint(0xA0A09D, top=0xA6A6A3)
ROOF_EDGE = Paint(0x979794, top=0x979794)
DOOR_LINE = Paint(0x3A1A1C)
DOOR_LINE_C = Paint(0x6E6A58)
YELLOW = Paint(0xE8C020)
STEP = Paint(0x262626)
GANG = Paint(0x2B2B2B)
BOGIE = Paint(0x262727)
BOGIE_HI = Paint(0x3A3C3B)
UNDER = Paint(0x2E2E2E)
TEXT = Paint(0xD89A18)

WINS = [(40, 90), (107, 141), (173, 240), (279, 346), (470, 537), (579, 646),
        (691, 758), (800, 867), (991, 1058), (1097, 1164), (1196, 1230), (1247, 1297)]
DOORS = [(383, 445), (895, 957)]
DOOR_WIN = [(395, 429), (908, 942)]
BOGIES_M = (2.97, 15.53)
LABELS = ["Bix", "RBix"]


def end_half(du):
    """half width of the rounded end at distance du (cu) from the body end."""
    if du >= 0.36:
        return W
    t = du / 0.36
    return W * (0.72 + 0.28 * np.sqrt(max(0.0, 1 - (1 - t) ** 2)))


def coach(kind, u0=0.0, owner="C"):
    bar = kind == "RBix"
    parts = []
    # body ends (real 0.46 m inside the buffer faces; drawn 0.3 m so coupled
    # cars do not show a 2 px gap at 1x)
    ub0, ub1 = u0 + 0.30 / M, u0 + L - 0.30 / M

    def xpx(u):
        return (u - u0) * M * PXM

    def side(f, u, v, z, d):
        x = xpx(u)
        for (a, b), (wa, wb) in zip(DOORS, DOOR_WIN):
            if a <= x <= b and z <= zm(3.14):
                if x - a < 7 or b - x < 7 or z > zm(3.07):
                    return DOOR_LINE if z < Z_RED else DOOR_LINE_C
                if wa - 3 <= x <= wb + 3 and WIN_Z[0] <= z <= WIN_Z[1]:
                    return R.GLASS_HI if z > WIN_Z[1] - 0.8 else R.GLASS
                if z < zm(1.30):
                    # step well with yellow step edges
                    if abs(z - zm(0.75)) < 0.28 or abs(z - zm(1.10)) < 0.28:
                        return YELLOW
                    return STEP
                return RED if z < Z_RED else CREAM
        for (a, b) in WINS:
            if a <= x <= b and WIN_Z[0] <= z <= WIN_Z[1]:
                return R.GLASS_HI if z > WIN_Z[1] - 0.8 else R.GLASS
        if bar:
            if z >= ZW - 0.95:
                return RED                     # red line under the roof edge
            if 600 <= x <= 720 and ZW - 1.95 <= z < ZW - 1.0:
                return TEXT                    # "BAROVÝ VŮZ"
        if z < ZB + 0.01 and (x < 480 or x > 860):
            return RED
        return RED if z < Z_RED else CREAM

    def end(f, u, v, z, d):
        av = abs(v)
        if z >= Z_RED:
            if bar and z >= ZW - 0.95:
                return RED
            if WIN_Z[0] <= z <= WIN_Z[1] + 0.3:
                if av < 0.22:
                    return R.GLASS                 # gangway door window
                if 0.34 < av < W - 0.14:
                    return R.GLASS_HI if z > WIN_Z[1] - 0.5 else R.GLASS
            if av < 0.28 and z < WIN_Z[1] + 0.7:
                return DOOR_LINE_C if av > 0.20 else CREAM
            return CREAM
        if av < 0.28:
            return DOOR_LINE if av > 0.20 else RED
        return RED

    def body_mat(f, u, v, z, d):
        if f == "+z":
            return ROOF_EDGE
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        return end(f, u, v, z, d)

    # body: full-width centre + stepped rounded ends
    n = 6
    ue = 0.36
    parts.append(Part(ub0 + ue, ub1 - ue, -W, W, ZB, ZW, body_mat, owner))
    for i in range(n):
        a = ue * i / n
        b = ue * (i + 1) / n
        hw = end_half((a + b) / 2)
        parts.append(Part(ub0 + a, ub0 + b, -hw, hw, ZB, ZW, body_mat, owner))
        parts.append(Part(ub1 - b, ub1 - a, -hw, hw, ZB, ZW, body_mat, owner))
    # skirt between the bogies (equipment boxes behind it)
    parts.append(Part(u0 + xm_(480) / M, u0 + xm_(860) / M, -W, W, ZSK, ZB + 0.2, body_mat, owner))
    # roof: two caps, the upper one shorter -> the roof slopes down at the ends
    parts.append(Part(ub0 + 0.12, ub1 - 0.12, -W + 0.2, W - 0.2, ZW, Z1, lambda *a: ROOF_MID, owner))
    parts.append(Part(ub0 + 0.55, ub1 - 0.55, -W + 0.46, W - 0.46, Z1, Z2, lambda *a: ROOF, owner))
    # roof vents
    for xv in (215, 400, 600, 800, 1000, 1180):
        uc = u0 + xm_(xv) / M
        parts.append(Part(uc - 0.10, uc + 0.10, -0.22, 0.22, Z2, Z2 + 0.35,
                          lambda *a: Paint(0x8E8E8B, top=0x9A9A97), owner))
    # buffers + coupler (the end door is drawn on the end wall; no bellows)
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        parts.append(Part(a, b, -0.12, 0.12, 2.3, 3.0, lambda *a: Paint(0x1E2022), owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *a: Paint(0x1E2022), owner))
    # bogies
    for bm in BOGIES_M:
        bc = u0 + bm / M
        parts.append(Part(bc - 1.55 / M, bc + 1.55 / M, -W + 0.14, W - 0.14, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.8) else BOGIE,
                          owner))
    return parts


def rows():
    out = []
    for k in LABELS:
        parts = coach(k)
        out.append([R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS])
    return out
