#!/usr/bin/env python3
"""Siemens ER 20 "Hercules" (DB class 223) of Die Laenderbahn in the alex
scheme, hauling the Bavorsky expres Plzen - Domazlice - Schwandorf. Drawn from
scratch with the pak128 box raycaster (render.py + railkit.py).

    python tools/railrender/er20.py [--preview DIR]

writes vehicle-rail/die-landerbahn/223/sprites/alex.png.

Real body (Siemens data, the 223 066/068 side markings "19.28 m" and "10.36 m",
side-on photos of 223 068 at Domazlice and OeBB 2016 006, fronts of 223 070 in
Plzen and 223 065 "alexa"): 19.28 m over buffers, 2.87 m wide, 4.26 m high over
the cab roof domes, bogie centres 10.36 m, Bo'Bo'. Two cab modules of 4.0 m
with a raised, rounded roof dome over each cab; between them the lower machine
room with a big rounded roof shoulder, a flat roof and the cooler box towards
cab 2. Cab: vertical lower front with the lamps, windscreen raked back 0.64 m,
side window then the cab door behind it. Drawn at length 10 like the Vectron
(vectron.py) and pak128.cs's 19 m locomotives; u = cu behind the cab 1 buffer
face (1.928 m/cu), z = model px above the rail. Heights are the real ones x 1.18
(3.15 px/m), the same loco stylisation as vectron.py (roof ~2.5 px above a
coach roof, like the natives).

Livery "alex" (photos above + 223 063 Schwandorf 2024, 223 071/072/067): petrol
blue (cyan-teal in the sun, #0092BD cab top); a white band wraps each cab like a
"C" - down the cab side right behind the windscreen, over the sides of the cab
roof dome - and the whole rounded machine-room roof shoulder is white with a
silver roof top; blue cab dome tops and fronts. Along the side, bottom up: blue
sill, a light-grey band, a yellow-orange stripe (the stripes run from C band to
C band over doors and louvres), blue side panels with the vertical-slat louvres
and a big white "= alex" logo. Front: black windscreen with an amber
destination display, white "= alex" under it, lamps in black housings at the
lower corners plus a third lamp above the logo, black buffer beam and plough.
The research described the upper side as white with a blue lower body - the
side-on photos show blue panels with the white band only on the roof shoulder;
photos win. 223 072's "Griass di Allgaeu" advert is not drawn.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "die-landerbahn", "223")

import numpy as np  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
import style as S  # noqa: E402
from PIL import Image  # noqa: E402

L = 10.0
W = 0.92
M = 19.28 / L                  # metres per cu
HZ = 1.18 / 0.375              # model px per metre of height (loco stylisation)


def cu(m):
    return m / M


def zm(m):
    return m * HZ


ZB = zm(0.80)                  # body side bottom
Z_SILL = zm(1.13)              # top of the blue sill
Z_GREY = Z_SILL + 1.1          # light-grey band (>= 1 px)
Z_YEL = Z_GREY + 1.0           # yellow stripe, 1 px
Z_SIDE = zm(3.12)              # machine-room side wall top (white above)
Z_MROOF = zm(3.90)             # machine-room roof
Z_CABSIDE = zm(3.35)           # cab side wall top (= windscreen top)
Z_DOME = zm(4.26)              # cab roof dome top
Z_WS0 = zm(2.55)               # windscreen bottom
Z_FRONT_LOW = zm(1.25)         # front: black buffer-beam zone below this
U_NOSE = 0.26                  # lower front face
U_WST = cu(1.14)               # windscreen top
U_DOMEF = cu(2.07)             # dome front reaches full height
U_CAB = cu(4.0)                # cab module end
HW_TOP_DOME = 0.60             # half width of the dome's flat top
HW_TOP_MR = 0.64               # half width of the machine-room flat roof
C_BAND = cu(1.55)              # white C band on the cab side, from the nose
WIN = (cu(2.07), cu(3.02), zm(2.67), zm(3.28))     # cab side window
DOOR = (cu(3.06), cu(3.92), zm(1.02), zm(3.30))     # cab door
LOUVRES = [(U_CAB + 0.02, cu(4.0 + 2.1)), (cu(4.0 + 7.0), cu(4.0 + 9.7))]
SEAMS = [cu(4.0 + m) for m in (3.3, 4.45, 5.75, 11.28 - 1.6)]
BOGIES = (cu(9.64 - 5.18), cu(9.64 + 5.18))

# ------------------------------------------------------------------ colours
BLUE = 0x0A80AE
BLUE_TOP = 0x1596C2
WHITE = 0xE6E9EC
SILVER_TOP = 0xCDD2D8
GREY = 0xC8CCCE
YELLOW = 0xF2AA1C
BLACK = 0x1A1C1F
GLASS = 0x1E2830
GLASS_HI = 0x34434E
AMBER = 0xD8962C
BOGIE = Paint(0x26282A)
BOGIE_HI = Paint(0x3E4144)
UNDER = Paint(0x2E3033)
TANK = Paint(0x34373A)
COOLER = Paint(0xB9BEC4, top=0xC4C9CF)
FAN = 0x3A3E43
EXHAUST = Paint(0x3C3F43, top=0x24262A)


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ------------------------------------------------------------------ shape
def _ell(t):
    t = min(max(t, 0.0), 1.0)
    return 1.0 - np.sqrt(1.0 - t * t)


def nose_u(z):
    """Front surface of the cab 1 module at height z (cu behind the buffers)."""
    if z < Z_WS0:
        return U_NOSE
    if z < Z_CABSIDE:
        return U_NOSE + (U_WST - U_NOSE) * (z - Z_WS0) / (Z_CABSIDE - Z_WS0)
    return U_WST + (U_DOMEF - U_WST) * _ell((z - Z_CABSIDE) / (Z_DOME - Z_CABSIDE))


def hw_cab(z):
    if z <= Z_CABSIDE:
        return W
    return HW_TOP_DOME + (W - HW_TOP_DOME) * (1 - _ell((z - Z_CABSIDE) / (Z_DOME - Z_CABSIDE)))


def hw_mr(z):
    if z <= Z_SIDE:
        return W
    return HW_TOP_MR + (W - HW_TOP_MR) * (1 - _ell((z - Z_SIDE) / (Z_MROOF - Z_SIDE)))


# ------------------------------------------------------------------ paint
def side_colour(u, z, x, cab):
    """Body side at (u, z); x = cu from the LEFT end as seen; cab = in a cab module."""
    c = min(u, L - u)
    if z < Z_SILL:
        return BLUE
    if cab:
        if z > Z_CABSIDE - 0.05:
            return WHITE                                    # dome sides
        if c < C_BAND:
            return WHITE                                    # the "C" band
        if z > Z_CABSIDE - 1.0 and not (DOOR[0] <= c <= DOOR[1]):
            return S.GUTTER                                 # dark line under the dome (2026-09-26 style)
        if WIN[0] <= c <= WIN[1] and WIN[2] <= z <= WIN[3]:
            return GLASS_HI if z > WIN[3] - 0.8 else GLASS
        if DOOR[0] - 0.10 <= c <= DOOR[1] + 0.10 and zm(1.0) <= z <= DOOR[3] - 0.6:
            if c < DOOR[0] or c > DOOR[1]:
                return 0xC4CACF                             # grab rails either side
        if DOOR[0] <= c <= DOOR[1] and z <= DOOR[3]:
            if c - DOOR[0] < 0.12 or DOOR[1] - c < 0.12 or z > DOOR[3] - 0.35:
                return 0x06506E                             # door gaps / top edge
    else:
        if z > Z_SIDE - 0.02:
            return WHITE                                    # roof shoulder
        if z > Z_SIDE - 1.0:
            return S.GUTTER                                 # dark line under the shoulder (2026-09-26 style)
    if z < Z_GREY:
        col = GREY
    elif z < Z_YEL:
        col = YELLOW
    else:
        col = BLUE                                          # (no 1-px "= alex" logo, 2026-09-26 style)
    if not cab:
        for (a, b) in LOUVRES:
            if a <= u <= b and z >= Z_SILL + 0.3:
                # vertical slats: every other quarter-cu darker
                k = int(np.floor((u - a) / 0.25))
                return mix(rgb(col), (0, 0, 0), 0.30 if k % 2 == 0 else 0.16)
        for s in SEAMS:
            if abs(u - s) < 0.05 and z >= Z_YEL:
                return mix(rgb(col), (0, 0, 0), 0.22)
    return col


def front_colour(v, z, rear):
    """Cab front at lateral v (loco-right = +v) and height z."""
    av = abs(v)
    if z < Z_FRONT_LOW:
        return BLACK
    if z >= Z_CABSIDE:
        return BLUE                                         # dome front
    if av > 0.72:
        return WHITE                                        # rounded corners
    if z >= Z_WS0:
        vs = -v                                             # as seen from ahead
        if z > Z_CABSIDE - 1.0 and 0.05 < vs < 0.55:
            return AMBER if not rear else GLASS             # destination display
        return GLASS_HI if z > Z_CABSIDE - 0.9 else GLASS
    zl0, zl1 = zm(1.40), zm(1.72)
    if 0.40 <= av <= 0.70 and zl0 - 0.2 <= z <= zl1 + 0.2:
        if 0.45 <= av <= 0.66 and zl0 <= z <= zl1:
            return R.TAIL if rear else R.HEAD
        return BLACK                                        # lamp housings
    if av < 0.14 and zm(2.24) <= z <= Z_WS0:
        return R.HEAD if not rear else 0x2A2E33             # top lamp
    return BLUE


def paint(x):
    if isinstance(x, tuple) and len(x) == 3 and x in (R.HEAD, R.TAIL):
        return x
    if isinstance(x, int):
        return Paint(x)
    return Paint(x)


def body_mat(f, u, v, z, d):
    c = min(u, L - u)
    rear = u > L / 2
    cab = c < U_CAB - 1e-6
    if f in ("+v", "-v"):
        x = u if f == "-v" else L - u
        return paint(side_colour(u, z, x, cab))
    if f == "+z":
        if cab:
            if c < nose_u(z + 0.24) - 1e-4:
                return paint(front_colour(v, z, rear))     # nose / windscreen steps
            if z >= Z_DOME - 0.05:
                return Paint(BLUE, top=BLUE_TOP)
            if abs(v) > hw_cab(z + 0.24) - 1e-4:
                return Paint(WHITE, top=0xDADEE2)           # dome shoulder
            return Paint(BLUE, top=BLUE_TOP)
        if z >= Z_MROOF - 0.05:
            return Paint(WHITE, top=SILVER_TOP)
        return Paint(WHITE, top=0xDADEE2)
    # -u / +u faces: cab fronts, or the rear face of a dome over the machine room
    if cab and ((f == "-u" and not rear) or (f == "+u" and rear)):
        return paint(front_colour(v, z, rear))
    return Paint(WHITE)


def build(liv="alex"):
    parts, lines = [], []
    own = "V"
    # machine room: side wall + rounded roof shoulder in slabs
    parts.append(Part(U_CAB, L - U_CAB, -W, W, ZB, Z_SIDE, body_mat, own))
    for z0 in np.arange(Z_SIDE, Z_MROOF - 1e-6, 0.25):
        z1 = min(Z_MROOF, z0 + 0.25)
        hw = hw_mr(z1 - 0.01)
        parts.append(Part(U_CAB - 0.01, L - U_CAB + 0.01, -hw, hw, z0, z1, body_mat, own))
    # cab modules (both ends): stepped nose + dome
    for z0 in np.arange(ZB, Z_DOME - 1e-6, 0.25):
        z1 = min(Z_DOME, z0 + 0.25)
        zc = z1 - 0.01
        uf = nose_u(zc)
        hw = hw_cab(zc)
        parts.append(Part(uf, U_CAB, -hw, hw, z0, z1, body_mat, own))
        parts.append(Part(L - U_CAB, L - uf, -hw, hw, z0, z1, body_mat, own))
    # buffer beams, buffers, ploughs
    for (a, b) in ((0.10, U_NOSE + 0.01), (L - U_NOSE - 0.01, L - 0.10)):
        parts.append(Part(a, b, -W + 0.06, W - 0.06, 1.3, Z_FRONT_LOW, lambda *a: Paint(BLACK), own))
    for (a, b) in ((0.0, 0.12), (L - 0.12, L)):
        for vc in (-0.62, 0.62):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.5, 3.2, lambda *a: Paint(0x3A3D40), own))
    for (a, b) in ((0.14, 0.42), (L - 0.42, L - 0.14)):
        parts.append(Part(a, b, -0.72, 0.72, 0.25, 1.35, lambda *a: Paint(0x222427), own))
    # bogies, fuel tank
    for bc in BOGIES:
        parts.append(Part(bc - 0.95, bc + 0.95, -W + 0.10, W - 0.10, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.8) else BOGIE, own))
    parts.append(Part(BOGIES[0] + 1.0, BOGIES[1] - 1.0, -W + 0.18, W - 0.18, 0.7, ZB, lambda *a: TANK, own))
    parts.append(Part(U_NOSE, L - U_NOSE, -W + 0.25, W - 0.25, 1.4, ZB, lambda *a: UNDER, own))
    # roof: cooler box with two fans (towards cab 2), exhaust silencer
    def cooler(f, u, v, z, d):
        if f == "+z":
            for fc in (5.55, 6.45):
                if (u - fc) ** 2 / 0.30 ** 2 + v ** 2 / 0.42 ** 2 < 1.0:
                    return Paint(FAN)
            return COOLER
        return COOLER
    parts.append(Part(cu(4.0 + 5.9), cu(4.0 + 9.3), -0.58, 0.58, Z_MROOF, Z_MROOF + 1.1, cooler, own))
    parts.append(Part(cu(4.0 + 4.3), cu(4.0 + 5.1), -0.24, 0.24, Z_MROOF, Z_MROOF + 0.8, lambda *a: EXHAUST, own))
    parts.append(Part(cu(4.0 + 1.0), cu(4.0 + 3.2), -0.40, 0.40, Z_MROOF, Z_MROOF + 0.35,
                      lambda *a: Paint(0xAEB3B9, top=0xBBC0C6), own))
    return parts, lines


def rows_for(liv="alex"):
    parts, lines = build(liv)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]


LIVERIES = ["alex"]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for liv in (args or LIVERIES):
        rows = rows_for(liv)
        out = os.path.join(FAM, "sprites", f"{liv}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        R.save_rows(rows, out)
        S.polish(Image.open(out), **S.POLISH).save(out)
        if prev:
            R.preview(rows, os.path.join(prev, f"er20_{liv}.png"), z=4, labels=[liv])
        print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
