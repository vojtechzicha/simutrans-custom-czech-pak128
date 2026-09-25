"""Leo Express Talgo VI ("Talgo S6") articulated coach set, loco-hauled.

Real set (vagonWEB, identical in every set seen), TG6 at the locomotive end:
  TG6 generator | TA6 Business 26 | TA6h Business 14+2 | TC6 bistro |
  7x TB6 Economy 36 | TB6R Economy 36 (network map) | TB6Z tail 20
Intermediate cars 13.14 m, TG6 ~12.2 m, TB6Z ~12.5 m, 2.942 m wide, 3.365 m
high (vs 4.05 m for a normal coach), single Rodal axles: one wheelset between
each pair of cars plus one near each outer end.

Model: the whole set in one u axis, every car length 6 (coordinator), car k
at u = 6k.  u = carunits behind the set front (TG6 outer buffers), v lateral
(+v = right-hand side in travel direction), z model px (1 px = 0.375 m).
The bellows + running-gear block at each joint belong to the car BEHIND it.

Sides (photos, Petrzalka / Praha, +v; vagonWEB drawings = -v side):
- doors sit at the REAR end of TA6/TB6 on both sides, at the FRONT (inner)
  end of TB6Z; TC6 and TB6R have no side doors.
- windows are at the same u on both sides; lettering and the TB6R map read
  left-to-right on each side (so they are u-mirrored between the sides).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import railkit as R
from railkit import Paint, Part, Lit
from render import DIRS

L = 6.0
W = 0.95            # 2.942 m wide vs 2.825 m (W_STD 0.92)
ZB = 1.15           # body bottom (~0.43 m)
ZSK = 2.30          # skirt band top (~0.86 m)
ZS = 8.32           # side top (~3.12 m)
ZR = 8.97           # roof top (3.365 m)
WZ0, WZ1 = 4.25, 6.45   # passenger window band (1.6 - 2.42 m)
JH = 0.15           # half gap between car bodies at a joint (bellows)

WHITE = Paint(0xF1F2EF)
ROOF = Paint(0xA9ADB0, top=0xBBBFC1)
SHOULDER = Paint(0x979CA0, top=0x9DA2A5)   # grey roof shoulder band (photos)
ROOFEQ = Paint(0x9A9FA2, top=0xA6ABAE)
SKIRT = Paint(0x2A2D2F)
BELLOWS = Paint(0x1C1D1F)
GEAR = Paint(0x1E2022)
GEAR_HI = Paint(0x3A3D40)
ORANGE = Paint(0xF06A0C)
ORANGE_DK = Paint(0xB84E08)
DOORGAP = Paint(0x8A4A1E)
GREEN = Paint(0x4BAF3A)
TEXT = Paint(0x2E3032)
DOT = Paint(0x3A3E42)          # map station dots
GRILLE = Paint(0xB2B7BA)
GRILLE_DK = Paint(0x979CA0)
PANEL = Paint(0xDCDEDC)        # service door / panel outline on the TG6
GATE = Paint(0x9CA2A6)         # grey gangway door in the end faces
ENDWIN = (0x2A, 0x34, 0x3D)    # end-face windows: plain dark (not lit)
ENDWIN_HI = (0x4F, 0x62, 0x72)
LAMP_OFF = Paint(0xD4D8D8)
BUFFER = Paint(0x1E2022)
SMALLWIN = (0x2A, 0x34, 0x3D)  # TG6 staff window: plain

# feature boxes in car-relative u (0..6 from the car's front), z
# windows: same u on both sides
# (drawing T6-01/02; each window trimmed 0.05 cu per side so the 0.4 m pillars
# still show as a pixel at 1x)
WIN4 = [(1.31, 1.85), (2.13, 2.66), (2.94, 3.42), (3.70, 4.23)]   # TA6/TB6/TC6
DOOR = (4.66, 5.22)                                            # TA6/TB6 rear door
WIN6 = [(1.15, 1.55), (1.73, 2.15), (2.50, 2.91), (3.25, 3.66), (4.01, 4.43), (4.76, 5.17)]  # TB6R (photo)
Z_WIN = [(1.74, 2.44), (2.64, 3.33), (3.53, 4.18)]             # TB6Z
Z_DOOR = (0.72, 1.26)                                          # TB6Z front door


def inbox(u, z, a, b, z0, z1):
    return a <= u <= b and z0 <= z <= z1


def window(u, z, a, b, z0=WZ0, z1=WZ1):
    """Passenger window with softened corners; returns colour or None."""
    if not inbox(u, z, a, b, z0, z1):
        return None
    return R.GLASS_HI if z > z1 - 0.7 else R.GLASS


def letters(x, x0, x1, pitch, dark):
    """Text as dark strokes with gaps: x in reading coordinate."""
    k = (x - x0) / pitch
    return (k - int(k)) < dark


class Car:
    def __init__(self, kind, k):
        self.kind = kind
        self.k = k
        self.u0 = k * L
        self.own = "c%d" % k


def grille(z, z0, z1):
    """Louvred grille: grey panel, darker top edge."""
    return GRILLE_DK if z > z1 - 0.45 else GRILLE


def big_logo(ur, z, s, x0):
    """Large "leo express" wordmark on the TG6. x0 = u where the logo starts
    as READ (screen-left): the larger-u end on +v, the smaller-u end on -v.
    Reading coordinate x grows to the screen-right. Dots + slash first, then
    the two text lines as bold bars ('l' ascender, 'p' descender)."""
    x = (x0 - ur) if s > 0 else (ur - x0)
    if x < 0:
        return None
    # three orange dots descending to the right, one pixel apart at 1x
    for (dx, dz) in ((0.10, 7.45), (0.32, 6.40), (0.54, 5.35)):
        if abs(x - dx) < 0.10 and abs(z - dz) < 0.50:
            return ORANGE
    # orange slash rising to the right below the dots
    if 0.02 <= x <= 0.50 and 3.0 <= z <= 4.5:
        if abs(z - (3.3 + (x - 0.02) * 2.2)) < 0.55:
            return ORANGE
    # "leo": x-height bar + the l ascender at its left end
    if 0.70 <= x <= 1.34 and (5.8 <= z <= 6.9 or (x <= 0.85 and z <= 7.9 and z >= 5.8)):
        return TEXT
    # "express": x-height bar + the p descender
    if 0.68 <= x <= 2.31 and 3.9 <= z <= 4.95:
        return TEXT
    if 1.05 <= x <= 1.18 and 3.0 <= z <= 3.9:
        return TEXT
    return None


def side_TG6(ur, z, s):
    """Generator car side. ur = u from car front (outer end), s = +1/-1 side.
    Text is drawn as one bold bar per line (letters alias to noise at 1x)."""
    if s > 0:
        # photo commons_TG6 (Petrzalka): outer end on the screen-right
        if inbox(ur, z, 5.05, 5.86, 3.4, 5.1):
            return GREEN                       # "Sun-fueled Innovation" pill
        c = big_logo(ur, z, s, 2.78)
        if c is not None:
            return c
        for (a, b, z0, z1) in ((0.60, 0.92, 6.1, 7.9), (2.85, 3.47, 6.0, 7.9), (3.63, 3.93, 6.0, 7.9)):
            if inbox(ur, z, a, b, z0, z1):
                return grille(z, z0, z1)
        if inbox(ur, z, 4.49, 4.90, 3.3, 7.9) and (ur < 4.57 or ur > 4.82 or z > 7.75):
            return PANEL
        return None
    # -v: vagonWEB T6-00 + zd photo: outer end on the screen-left
    if inbox(ur, z, 5.18, 5.84, 3.4, 5.1):
        return GREEN
    if inbox(ur, z, 5.00, 5.30, 6.5, 7.4):
        return SMALLWIN
    c = big_logo(ur, z, s, 0.98)
    if c is not None:
        return c
    for (a, b, z0, z1) in ((2.45, 2.80, 6.3, 7.9), (3.02, 3.57, 6.0, 7.9), (3.78, 4.22, 5.4, 7.9)):
        if inbox(ur, z, a, b, z0, z1):
            return grille(z, z0, z1)
    if inbox(ur, z, 4.45, 4.92, 3.3, 7.9) and (ur < 4.53 or ur > 4.84 or z > 7.75):
        return PANEL
    return None


def logo_small(ur, z, s, a, b, z0=3.3, z1=5.3):
    """Small LE logo: orange dots/slash left of two text bars (reads l->r)."""
    if not inbox(ur, z, a, b, z0, z1):
        return None
    x = (b - ur) if s > 0 else (ur - a)          # reading coordinate
    w = b - a
    zm = (z0 + z1) / 2
    if x < 0.24 * w:
        return ORANGE
    if x < 0.34 * w:
        return None
    if z > zm + 0.1:
        return TEXT if x < 0.62 * w else None      # "leo"
    if z < zm - 0.1:
        return TEXT                                # "express"
    return None


def side_seat(kind, ur, z, s):
    if kind in ("TA6", "TB6", "TC6"):
        for (a, b) in WIN4:
            c = window(ur, z, a, b)
            if c is not None:
                return c
    if kind in ("TA6", "TB6"):
        a, b = DOOR
        if inbox(ur, z, a, b, ZB, 8.05):
            if ur < a + 0.09 or ur > b - 0.09:
                return DOORGAP
            if inbox(ur, z, a + 0.16, b - 0.16, 5.3, 6.6):
                return R.GLASS
            return ORANGE
    if kind == "TB6":
        c = logo_small(ur, z, s, 0.25, 0.80, 3.9, 5.9)
        if c is not None:
            return c
    if kind == "TC6":
        # orange BISTRO lettering behind the last window (reads l->r)
        if inbox(ur, z, 4.55, 5.40, 4.75, 5.85):
            return ORANGE
    if kind == "TB6R":
        for (a, b) in WIN6:
            if inbox(ur, z, a, b, WZ0, WZ1):
                # the orange map line runs across the windows at mid height
                if 5.0 <= z <= 5.75 and x_ok_line(ur, s):
                    return ORANGE
                return R.GLASS_HI if z > WZ1 - 0.7 else R.GLASS
        c = tb6r_map(ur, z, s)
        if c is not None:
            return c
    if kind == "TB6Z":
        for (a, b) in Z_WIN:
            c = window(ur, z, a, b)
            if c is not None:
                return c
        a, b = Z_DOOR
        if inbox(ur, z, a, b, ZB, 8.05):
            if ur < a + 0.09 or ur > b - 0.09:
                return DOORGAP
            if inbox(ur, z, a + 0.16, b - 0.16, 5.3, 6.6):
                return R.GLASS
            # "family" cartoon (dark figure) on the lower door leaf
            if inbox(ur, z, a + 0.18, b - 0.18, 2.7, 3.9):
                return TEXT
            return ORANGE
        if s > 0:
            # two stacked louvred grilles near the rear end (photos, +v only)
            if inbox(ur, z, 4.78, 5.22, 5.7, 7.9):
                return grille(z, 5.7, 7.9)
            if inbox(ur, z, 4.78, 5.22, 3.1, 5.4):
                return grille(z, 3.1, 5.4)
    return None


# TB6R network map, in reading coordinate x (0 = left end as seen, 0..6)
def xr(ur, s):
    return (L - ur) if s > 0 else ur


def x_ok_line(ur, s):
    x = xr(ur, s)
    return 0.64 <= x <= 3.62


def tb6r_map(ur, z, s):
    x = xr(ur, s)
    # main line through the windows
    if 5.0 <= z <= 5.75 and 0.64 <= x <= 3.62:
        for sx in (0.66, 1.41, 2.16, 2.91, 3.60):
            if abs(x - sx) < 0.10:
                return DOT
        return ORANGE
    # fork: upper branch up to z 7.0, lower branch down to z 3.7
    if 3.60 <= x <= 3.86:
        t = (x - 3.60) / 0.26
        if abs(z - (5.4 + t * 1.6)) < 0.45 or abs(z - (5.4 - t * 1.7)) < 0.45:
            return ORANGE
    if 3.84 <= x <= 4.36 and (6.6 <= z <= 7.3):
        return DOT if x > 4.26 else ORANGE
    if 3.84 <= x <= 4.36 and (3.4 <= z <= 4.05):
        return DOT if x > 4.26 else ORANGE
    if 4.4 <= x <= 5.0 and 3.4 <= z <= 4.05:
        return ORANGE if int((x - 4.4) / 0.14) % 2 == 0 else None
    # big city names: Praha (above, left), Bratislava (below), Warszawa (above, right)
    if 1.20 <= x <= 1.75 and 6.75 <= z <= 7.45:
        return TEXT
    if 2.05 <= x <= 2.85 and 2.55 <= z <= 3.25:
        return TEXT
    if 4.40 <= x <= 5.15 and 6.75 <= z <= 7.45:
        return TEXT
    return None


def end_face(car, f, u, v, z, rear):
    """TG6 outer end (front) and TB6Z rear end: orange frame, white panel,
    grey gangway door, two windows, le.cz + green panel, orange apron."""
    av = abs(v)
    if av > W - 0.16 or z > ZR - 0.45:
        return ORANGE
    if z < 3.5:
        return ORANGE
    if av < 0.26 and z < 8.4:
        return GATE if av < 0.21 else Paint(0x6E7478)
    if 0.36 <= av <= 0.80 and 5.9 <= z <= 7.9:
        return ENDWIN_HI if z > 7.3 else ENDWIN
    # lamps (inner = red tail lights on the TB6Z, unlit on the TG6)
    if 4.3 <= z <= 5.0 and 0.40 <= av <= 0.80:
        if av < 0.60:
            return R.TAIL if rear else LAMP_OFF
        return LAMP_OFF
    # "le.cz" (viewer's left) and the green panel (viewer's right)
    left_side = (v < 0) if rear else (v > 0)
    if 5.05 <= z <= 5.65 and 0.34 <= av <= 0.80:
        return ORANGE if left_side else GREEN
    return WHITE


def build():
    order = ["TG6", "TA6", "TA6", "TC6", "TB6", "TB6", "TB6R", "TB6Z"]
    cars = [Car(kd, i) for i, kd in enumerate(order)]
    parts, lines = [], []
    for car in cars:
        u0, own, kind = car.u0, car.own, car.kind
        first = kind == "TG6"
        last = kind == "TB6Z"
        ub0 = u0 + (0.30 if first else JH)
        ub1 = u0 + L - (0.40 if last else JH)

        def body_mat(f, u, v, z, d, car=car, ub0=ub0, ub1=ub1):
            kind = car.kind
            ur = u - car.u0
            if f == "+z":
                return SHOULDER
            if f in ("+v", "-v"):
                s = 1 if f == "+v" else -1
                # orange frame wrap at the outer ends
                if kind == "TG6" and u - ub0 < 0.20:
                    return ORANGE
                if kind == "TB6Z" and ub1 - u < 0.20:
                    return ORANGE
                c = side_TG6(ur, z, s) if kind == "TG6" else side_seat(kind, ur, z, s)
                if c is not None:
                    return c
                if z < ZSK:
                    return SKIRT
                return WHITE
            if f == "-u" and kind == "TG6":
                return end_face(car, f, u, v, z, rear=False)
            if f == "+u" and kind == "TB6Z":
                return end_face(car, f, u, v, z, rear=True)
            return WHITE

        parts.append(Part(ub0, ub1, -W, W, ZB, ZS, body_mat, own))

        def roof_mat(f, u, v, z, d, car=car, ub0=ub0, ub1=ub1):
            if car.kind == "TG6" and u - ub0 < 0.12:
                return ORANGE
            if car.kind == "TB6Z" and ub1 - u < 0.12:
                return ORANGE
            return ROOF if f == "+z" else SHOULDER
        parts.append(Part(ub0 + 0.04, ub1 - 0.04, -W + 0.2, W - 0.2, ZS, ZR, roof_mat, own))

        # joint in front (bellows + single-axle running gear) belongs to this car
        if not first:
            parts.append(Part(u0 - JH, u0 + JH, -W + 0.14, W - 0.14, ZB + 0.3, ZS + 0.3,
                              lambda *a: BELLOWS, own))
            parts.append(Part(u0 - 0.32, u0 + 0.32, -W - 0.01, W + 0.01, 0.0, 2.9,
                              lambda f, u, v, z, d: GEAR_HI if (f in ("+v", "-v") and 1.4 < z < 2.0) else GEAR, own))
        # outer-end axles + buffers
        if first:
            ua = u0 + 1.70
            parts.append(Part(ua - 0.30, ua + 0.30, -W - 0.01, W + 0.01, 0.0, 2.7,
                              lambda f, u, v, z, d: GEAR_HI if (f in ("+v", "-v") and 1.4 < z < 2.0) else GEAR, own))
            for vc in (-0.62, 0.62):
                parts.append(Part(u0 + 0.04, ub0, vc - 0.17, vc + 0.17, 2.2, 3.2, lambda *a: BUFFER, own))
            parts.append(Part(u0 + 0.10, ub0, -0.14, 0.14, 2.1, 2.9, lambda *a: BUFFER, own))
        if last:
            ua = u0 + 4.35
            parts.append(Part(ua - 0.30, ua + 0.30, -W - 0.01, W + 0.01, 0.0, 2.7,
                              lambda f, u, v, z, d: GEAR_HI if (f in ("+v", "-v") and 1.4 < z < 2.0) else GEAR, own))
            for vc in (-0.62, 0.62):
                parts.append(Part(ub1, u0 + L - 0.10, vc - 0.17, vc + 0.17, 2.2, 3.2, lambda *a: BUFFER, own))
            parts.append(Part(ub1, u0 + L - 0.16, -0.14, 0.14, 2.1, 2.9, lambda *a: BUFFER, own))
        # roof equipment
        if first:
            parts.append(Part(u0 + 2.6, u0 + 4.3, -0.55, 0.55, ZR, ZR + 0.30, lambda *a: ROOFEQ, own))
            for ue in (3.0, 3.6):
                parts.append(Part(u0 + ue - 0.10, u0 + ue + 0.10, -0.12, 0.12, ZR, ZR + 0.85,
                                  lambda *a: Paint(0x3A3D40, top=0x2A2C2E), own))
        else:
            parts.append(Part(u0 + 4.3, u0 + 5.2, -0.50, 0.50, ZR, ZR + 0.28, lambda *a: ROOFEQ, own))
    return cars, parts, lines


ROWS = [("TG6", 0), ("TA6", 1), ("TC6", 3), ("TB6", 4), ("TB6R", 6), ("TB6Z", 7)]


def render_rows():
    cars, parts, lines = build()
    rows = []
    for kind, idx in ROWS:
        car = cars[idx]
        rows.append([R.vehicle_tile(parts, lines, d, car.u0, {car.own}) for d in DIRS])
    return rows


if __name__ == "__main__":
    import leo
    leo.main()
