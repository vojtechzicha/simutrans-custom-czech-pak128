#!/usr/bin/env python3
"""Bombardier TRAXX F140 MS (class 186) of Railpool, leased to LINEAS and
chartered by Train Charter Services for European Sleeper ES 452/453 (Praha -
Usti n.L. - Decin - Dresden - Berlin - Amsterdam - Brussels; Czech carrier
Cityrail). Drawn from scratch with the pak128 box raycaster.

    python tools/railrender/traxx.py [--preview DIR]

writes vehicle-rail/european-sleeper/186/sprites/lineas.png.

Real body (TRAXX F140 MS data; side-on photo of 91 80 6186 291 at Brussels
27 Mar 2024, 186 291 at Praha hl.n. 26 Mar 2024 and Rotterdam 22 Jul 2024):
18.90 m over buffers, 2.98 m wide, roof ~3.8 m (4.28 m over the lowered
pantographs), bogie centres 10.44 m, Bo'Bo'. Flat-sided box body; each cab has
a near-vertical lower front with the lamps, a windscreen raked back ~0.9 m and
bevelled front corners; behind the windscreen a small side window, then the
cab door. A band of grilles runs along the top of the machine-room sides; two
pantographs, one near each end. Drawn at length 10 like the Vectron
(vectron.py); u = cu behind the cab 1 buffer face (1.89 m/cu), heights x 1.18
(3.15 px/m), the loco stylisation of vectron.py.

Livery "lineas" (186 291's "LINEAS / train charter / Decarbonizing Borderless
Performance" wrap, all photos above; its two ends differ):
  cab 1  navy-black, three teal stripes across the front and along the cab side
         (drawn as two 1 px stripes: three do not fit a 2.5 px band at 1x),
         fading out behind the cab door; white "LINEAS" on the side, a white
         "LINEAS" on the front between the stripes and the lamps.
  middle navy-black with blue mountain silhouettes, a light-blue arch bridge
         over pale water and the teal "DECARBONIZING BORDERLESS PERFORMANCE"
         boxes above it; white "train charter" near cab 2.
  cab 2  medium blue with lighter faceted triangles, a broad white diagonal
         stripe across the front.
Grey roof-edge grilles, dark grey roof and underframe.
Cab 1 leads (u = 0); photos show the same arrangement on the side seen, the
other side is assumed point-symmetric (graphics fixed to the cabs, lettering
reading left to right as seen).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "european-sleeper", "186")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
import style as S  # noqa: E402

L = 10.0
W = 0.92
M = 18.90 / L
HZ = 1.18 / 0.375


def cu(m):
    return m / M


def zm(m):
    return m * HZ


ZB = zm(0.89)                  # body side bottom
Z_SIDE = zm(3.30)              # side wall top (below the grille band)
Z_GRILLE = zm(3.62)            # grille band top
Z_ROOF = zm(3.78)              # roof top
Z_WS0 = zm(2.35)               # windscreen bottom
Z_WS1 = zm(3.40)               # windscreen top
Z_FRONT_LOW = zm(1.22)         # front: black buffer-beam zone below this
U_FRONT = cu(0.45)             # lower front face
U_WST = cu(1.34)               # windscreen top
U_CAB = cu(3.15)               # cab module end (cab roof, grille band start)
BEVEL = 0.16                   # front corner bevel (cu, lateral)
WIN = (cu(1.25), cu(1.80), zm(2.54), zm(3.15))
DOOR = (cu(1.90), cu(2.75), zm(0.95), zm(3.25))
BOGIES = (cu(9.45 - 5.22), cu(9.45 + 5.22))

# ------------------------------------------------------------------ colours
NAVY = 0x262A3A
NAVY_TOP = 0x323850
TEAL = 0x27B4C6
BLUE2 = 0x34479A
BLUE2_HI = 0x4B63AE
BLUE2_DK = 0x2A3A84
MOUNT = 0x3E5494
MOUNT_DK = 0x31437A
BRIDGE = 0xA6CAF2
WATER = 0x6F93C8
WHITE = 0xEEF1F4
GRILLE = 0x8C909B
ROOF = Paint(0x3C4049, top=0x4A4F59)
BLACK = 0x18191C
GLASS = 0x3A4755
GLASS_HI = 0x5A6B7C
BOGIE = Paint(0x26282A)
BOGIE_HI = Paint(0x3E4144)
UNDER = Paint(0x2C2E31)
PANTO_HEAD = (0x2A, 0x2A, 0x2C)


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def mix(a, b, t):
    a = rgb(a) if isinstance(a, int) else a
    b = rgb(b) if isinstance(b, int) else b
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# stripe rows (z) - each exactly 1 px so they stay crisp at 1x
STRIPES = ((zm(1.53), zm(1.53) + 1.0), (zm(2.17) - 0.35, zm(2.17) + 0.65))


def stripe(z):
    return any(a <= z < b for (a, b) in STRIPES)


def facets(u, z):
    """Lighter / darker triangles of the cab 2 wrap (c = cu from the rear end)."""
    c = L - u
    k = (int(np.floor(c / 0.45)) + int(np.floor(z / 2.2))) % 3
    tri = ((c / 0.45) % 1.0) > ((z / 2.2) % 1.0)
    if k == 0 and tri:
        return BLUE2_HI
    if k == 1 and not tri:
        return BLUE2_DK
    return BLUE2


def mountains(u, z):
    """Machine-room picture: mountains, the arch bridge over the water."""
    if cu(7.2) <= u <= cu(12.4):
        # water / bridge deck
        if zm(1.58) <= z < zm(1.58) + 1.0:
            return BRIDGE
        if zm(1.18) <= z < zm(1.58):
            return WATER if int(np.floor(u / 0.25)) % 3 else BRIDGE
        # the arch: a thin light line rising to the middle
        ua = (u - cu(7.45)) / (cu(12.2) - cu(7.45))
        if 0.0 <= ua <= 1.0:
            za = zm(1.58) + (zm(2.72) - zm(1.58)) * (1 - (2 * ua - 1) ** 2)
            if za - 0.5 <= z <= za + 0.5:
                return BRIDGE
    # mountain silhouettes (lighter blue) behind
    peaks = ((3.4, 8.2), (4.6, 9.0), (6.2, 8.7), (7.4, 8.0), (2.9, 7.2))
    for (pu, pz) in peaks:
        if z >= zm(1.2) and z <= pz - abs(u - pu) * 2.6:
            return MOUNT if (u < pu) else MOUNT_DK
    return None


def side_colour(u, z, side):
    """Body side (below the grille band); side = +1 for +v, -1 for -v."""
    c = min(u, L - u)
    cab1 = u < U_CAB
    cab2 = u > L - U_CAB
    if (cab1 or cab2):
        if WIN[0] <= c <= WIN[1] and WIN[2] <= z <= WIN[3]:
            return GLASS_HI if z > WIN[3] - 0.8 else GLASS
        if DOOR[0] <= c <= DOOR[1] and DOOR[2] <= z <= DOOR[3]:
            if c - DOOR[0] < 0.08 or DOOR[1] - c < 0.08 or z > DOOR[3] - 0.3:
                return 0x0E1016                              # door gaps
        if DOOR[0] - 0.12 <= c < DOOR[0] or DOOR[1] < c <= DOOR[1] + 0.12:
            if zm(1.1) <= z <= DOOR[3] - 0.5:
                return 0xB4BAC2                              # grab rails
    if cab2:
        return facets(u, z)
    # cab 1 teal stripes, running back past the door and fading out
    if stripe(z):
        if u < cu(5.0):
            return TEAL
        if u < cu(6.4):
            t = (u - cu(5.0)) / (cu(6.4) - cu(5.0))
            k = int(np.floor(u / 0.25))
            return mix(TEAL, NAVY, t) if (k % 2 == 0 or t < 0.4) else NAVY
    if cab1:
        return NAVY
    # (2026-09-26 style: no 1-px lettering; the LINEAS / train charter words are left out)
    # "DECARBONIZING BORDERLESS PERFORMANCE": teal boxes, white middle word
    if 7.6 <= z < 8.6 and cu(7.2) <= u <= cu(9.0):
        return TEAL                                         # DECARBONIZING
    if 6.6 <= z < 7.6 and cu(7.45) <= u <= cu(9.25):
        return WHITE if int(np.floor(u / 0.25)) % 4 else mix(WHITE, NAVY, 0.4)   # BORDERLESS
    if 5.8 <= z < 6.6 and cu(8.05) <= u <= cu(9.65):
        return TEAL                                         # PERFORMANCE
    m = mountains(u, z)
    if m is not None:
        return m
    return NAVY


def front_colour(v, z, rear):
    """Cab front; rear = the cab 2 end (blue, white diagonal)."""
    av = abs(v)
    vs = -v if not rear else v          # lateral as seen from ahead of that cab
    if z < Z_FRONT_LOW:
        return BLACK
    if z >= Z_WS1:
        return BLUE2 if rear else NAVY
    if z >= Z_WS0:
        if av < W - BEVEL - 0.02:
            return GLASS_HI if z > Z_WS1 - 0.9 else GLASS
        return BLUE2 if rear else NAVY
    zl0, zl1 = zm(1.33), zm(1.62)
    if 0.42 <= av <= 0.78 and zl0 - 0.25 <= z <= zl1 + 0.25:
        if 0.48 <= av <= 0.72 and zl0 <= z <= zl1:
            return R.TAIL if rear else R.HEAD
        return 0x2B2F36                                     # lamp frames
    if av < 0.13 and zm(2.18) <= z <= Z_WS0:
        return R.HEAD if not rear else 0x2B2F36             # top lamp
    if not rear:
        if stripe(z):
            return TEAL
        return NAVY
    # cab 2: broad white diagonal rising to the right as seen
    zc = Z_FRONT_LOW + (vs + 0.25) / 0.75 * (Z_WS0 - Z_FRONT_LOW)
    if abs(z - zc) < 1.0 and -0.35 <= vs <= 0.60:
        return WHITE
    return BLUE2


def body_mat(f, u, v, z, d):
    c = min(u, L - u)
    rear = u > L / 2
    in_cab = c < U_CAB - 1e-6
    side = 1 if f == "+v" else -1
    if f in ("+v", "-v"):
        if z >= Z_SIDE - 0.01 and z < Z_GRILLE:
            if in_cab:
                return Paint(BLUE2 if rear else NAVY)
            # grille band: two grey grille blocks (3.1-5.75 m, 11.9-15.6 m
            # from cab 1), dark frames between the grilles; smooth between
            x = u if side < 0 else u
            if cu(3.1) <= u <= cu(5.75) or cu(11.9) <= u <= cu(15.6):
                k = (u - cu(3.1)) / 0.55
                return Paint(0x30343C) if (k % 1.0) < 0.15 else Paint(GRILLE)
            return Paint(NAVY)
        if z >= Z_GRILLE:
            return Paint(BLUE2 if (in_cab and rear) else (NAVY if in_cab else S.GUTTER))
        col = side_colour(u, z, side)
        return col if isinstance(col, tuple) and col in (R.HEAD, R.TAIL) else Paint(col)
    if f == "+z":
        if in_cab and c < nose_u(z + 0.24) - 1e-4:
            col = front_colour(v, z, rear)
            return col if col in (R.HEAD, R.TAIL) else Paint(col)
        if in_cab:
            return Paint(BLUE2, top=0x4152A2) if rear else Paint(NAVY, top=NAVY_TOP)
        return ROOF
    if in_cab and ((f == "-u" and not rear) or (f == "+u" and rear)):
        col = front_colour(v, z, rear)
        return col if col in (R.HEAD, R.TAIL) else Paint(col)
    return ROOF


def nose_u(z):
    if z < Z_WS0:
        return U_FRONT + 0.05 * max(0.0, (z - zm(1.3)) / (Z_WS0 - zm(1.3)))
    if z < Z_WS1:
        return U_FRONT + 0.05 + (U_WST - U_FRONT - 0.05) * (z - Z_WS0) / (Z_WS1 - Z_WS0)
    return U_WST + 0.12 * (z - Z_WS1) / (Z_ROOF - Z_WS1)


def build(liv="lineas"):
    parts, lines = [], []
    own = "V"
    # machine room box: side wall, grille band (slightly inset), roof
    parts.append(Part(U_CAB, L - U_CAB, -W, W, ZB, Z_SIDE, body_mat, own))
    parts.append(Part(U_CAB, L - U_CAB, -W + 0.06, W - 0.06, Z_SIDE, Z_GRILLE, body_mat, own))
    parts.append(Part(U_CAB, L - U_CAB, -W + 0.14, W - 0.14, Z_GRILLE, Z_ROOF, body_mat, own))
    # cab modules: stepped nose with bevelled corners
    for z0 in np.arange(ZB, Z_ROOF - 1e-6, 0.25):
        z1 = min(Z_ROOF, z0 + 0.25)
        zc = z1 - 0.01
        uf = nose_u(zc)
        hw = W if zc < Z_GRILLE else W - 0.10
        # centre part reaches the full nose, the corners are bevelled back
        parts.append(Part(uf, U_CAB, -hw + BEVEL, hw - BEVEL, z0, z1, body_mat, own))
        parts.append(Part(L - U_CAB, L - uf, -hw + BEVEL, hw - BEVEL, z0, z1, body_mat, own))
        for s in (-1, 1):
            v0, v1 = (hw - BEVEL, hw) if s > 0 else (-hw, -hw + BEVEL)
            parts.append(Part(uf + 0.10, U_CAB, v0, v1, z0, z1, body_mat, own))
            parts.append(Part(L - U_CAB, L - uf - 0.10, v0, v1, z0, z1, body_mat, own))
    # buffer beams, buffers, ploughs
    for (a, b) in ((0.12, U_FRONT + 0.01), (L - U_FRONT - 0.01, L - 0.12)):
        parts.append(Part(a, b, -W + 0.08, W - 0.08, 1.4, Z_FRONT_LOW, lambda *a: Paint(BLACK), own))
    for (a, b) in ((0.0, 0.13), (L - 0.13, L)):
        for vc in (-0.62, 0.62):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.5, 3.2, lambda *a: Paint(0x3A3D40), own))
    for (a, b) in ((0.16, 0.46), (L - 0.46, L - 0.16)):
        parts.append(Part(a, b, -0.70, 0.70, 0.25, 1.45, lambda *a: Paint(0x222427), own))
    # bogies + transformer / equipment between them
    for bc in BOGIES:
        parts.append(Part(bc - 0.92, bc + 0.92, -W + 0.10, W - 0.10, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.9) else BOGIE, own))
    parts.append(Part(BOGIES[0] + 1.0, BOGIES[1] - 1.0, -W + 0.20, W - 0.20, 0.9, ZB, lambda *a: UNDER, own))
    parts.append(Part(U_FRONT, L - U_FRONT, -W + 0.26, W - 0.26, 1.5, ZB, lambda *a: UNDER, own))
    # roof equipment: main breaker / insulator box in the middle, pantograph
    # bases near each end; the rear-most pantograph raised
    parts.append(Part(4.1, 5.9, -0.42, 0.42, Z_ROOF, Z_ROOF + 0.55, lambda *a: Paint(0x50555E, top=0x5C626C), own))
    for (a, b) in ((1.9, 2.9), (7.1, 8.1)):
        parts.append(Part(a, b, -0.40, 0.40, Z_ROOF, Z_ROOF + 0.40, lambda *a: Paint(0x44484F, top=0x50555D), own))
    lines += R.pantograph(7.45, Z_ROOF + 0.40, own, fold=-1, reach=0.9, height=5.2,
                          col=S.PANTO_ARM, head=S.PANTO_HEAD, half_head=0.62, thick=False)
    return parts, lines


def rows_for(liv="lineas"):
    parts, lines = build(liv)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]


LIVERIES = ["lineas"]


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
            R.preview(rows, os.path.join(prev, f"traxx_{liv}.png"), z=4, labels=[liv])
        print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
