#!/usr/bin/env python3
"""ÖBB CityShuttle push-pull stock ("Schlieren" type): Bmpz-l 21-73 coach and
Bmpz-s 80-73 cab car, in the CityShuttle livery, drawn with the pak128.cs
calibrated box renderer (render.py / railkit.py).

    python tools/railrender/obb_cityshuttle.py [--preview DIR]

writes vehicle-rail/obb/cityshuttle/sprites/cityshuttle.png
(row 0 = 80-73 cab car, row 1 = 21-73 coach).

Real cars (vagonWEB side drawings Bmpz-l-2173-0-2019-a/b and
Bmpz-s-8073-2019-a/b, 10 px = 1 m): 26.40 m over buffers, 2.825 m wide,
single-leaf plug doors near both ends, ten 1.3 m windows with a top vent,
bogie centres 4.0 m from the ends. The cab car carries the flat cab with a
two-pane windscreen in a dark band, a big round lamp on the roof edge, a bike
window and the driver's side window behind the cab (no cab door, drawings a/b).

The CityShuttle livery (ÖBB 1990s, also worn by the older "Wiesel" double-deck
cars, see obb_dosto.py): silver-grey car, a red field covering the car from the
roof edge to the sill over its left half AS SEEN from either side, ending in a
steep "/" diagonal; white "ÖBB" and "CityShuttle" script on the red. So the
pattern is point-symmetric: a cab car shows red at the cab end on its left-hand
side (-v) and at the far end on its right-hand side (+v) (drawings a/b, photos
ÖBB 80-73 Feldbach, ÖBB 1116 jižní zastávka České Budějovice (01)).

Coordinates: u = carunits behind the car front (0 = cab front / coupler face),
s = metres from the car front (s = u * M), x = metres from the screen-left end
of the side AS SEEN (x = s on the -v side, x = 26.4 - s on the +v side).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import numpy as np                     # noqa: E402
import railkit as R                    # noqa: E402
from railkit import Paint, Part       # noqa: E402
from render import DIRS                # noqa: E402

PX = 0.375                 # metres per model px (z)


def zm(h):
    """height above rail (m) -> model z."""
    return h / PX


# ------------------------------------------------------------------ ÖBB colours
RED = Paint(0xD62420, top=0xD02A24)
RED_DK = Paint(0xB81C1A)               # sill line / cab door outline on the red
GREY = Paint(0xC6C8CA)                 # CityShuttle silver-grey body
GREY_DK = Paint(0xA9ACAF)              # sill line on the grey
ROOF = Paint(0xB0B4B8, top=0xA2A6AA)
ROOF_EDGE = Paint(0xB8BCC0, top=0xA8ACB0)
DOOR = Paint(0xF2F3F3)                 # light grey door leaves (on red and grey)
DOOR_EDGE = Paint(0x55585C)            # door gap / seal: frames the leaf
FRAME = Paint(0x3C3F42)                # window rubber frame
WHITE = Paint(0xF2F2F2)
UNDER = Paint(0x2A2C2E)
BOGIE = Paint(0x232426)
BOGIE_HI = Paint(0x3E4144)
BUFFER = Paint(0x1E2022)
BELLOWS = Paint(0x2B2D2F)
BEAM = Paint(0x303234)
WS = (0x2A, 0x34, 0x3D)                # windscreen / cab window (plain, never lit)
WS_HI = (0x4F, 0x62, 0x72)
TAIL_OFF = (0x8A, 0x1E, 0x1A)          # unlit tail lamp on a leading cab


# ------------------------------------------------------------------ lettering
def cityshuttle_script(xr, z_m):
    """White "CityShuttle" script, xr = metres from the start of the word as READ,
    z_m = metres above rail relative to its baseline (0 .. ~0.8).  A bold x-height
    band broken between the words, plus the ascenders (C, S, t, t, l, h) so it
    reads as a word at 1x."""
    if not (0.0 <= xr <= 3.6 and 0.0 <= z_m <= 0.80):
        return False
    # x-height band: "City" and "Shuttle" with a gap after "City"
    if z_m <= 0.38:
        if 1.12 <= xr <= 1.30:
            return False
        if 0.20 <= xr <= 0.30 and z_m > 0.12:
            return False                 # open "C"
        return True
    # ascenders
    for (a, b) in ((0.0, 0.26), (1.32, 1.66), (2.30, 2.40), (2.62, 2.72), (3.00, 3.10), (1.70, 1.80)):
        if a <= xr <= b:
            return True
    return False


def obb_logo(xr, z_m, w=0.80, h=0.34):
    """Small "ÖBB" wordmark as a solid pill with a notch between Ö and BB
    (at 1x it is 2-3 px): xr, z_m relative to its lower-left corner."""
    if not (0.0 <= xr <= w and 0.0 <= z_m <= h):
        return False
    return not (0.30 * w <= xr <= 0.38 * w)


# ------------------------------------------------------------------ crisp outlines
def visible_sides(d):
    """side faces that face the viewer in view d ('+v' / '-v'); nw/se see them edge-on."""
    from render import frame
    f, r = frame(d)
    k = r[0] + r[1]
    if k > 0.1:
        return {"+v"}
    if k < -0.1:
        return {"-v"}
    return set()


def outline_lines(d, spans, W, z0, z1, col, owner, top=True, sides=None):
    """1-px screen lines framing door leaves on the visible side(s): spans are
    (u_a, u_b) in carunits.  Lines are drawn after the raycast, so they give an
    exact 1-px frame in every view instead of a sub-pixel band."""
    out = []
    vis = visible_sides(d) if sides is None else sides & visible_sides(d)
    for sd in vis:
        v = (W + 0.004) * (1 if sd == "+v" else -1)
        for (a, b) in spans:
            out.append(((a, v, z0), (a, v, z1), col, owner))
            out.append(((b, v, z0), (b, v, z1), col, owner))
            if top:
                out.append(((a, v, z1), (b, v, z1), col, owner))
    return out


# ------------------------------------------------------------------ car layout
L = 13.0                   # carunits
LM = 26.40                 # metres over buffers
M = LM / L
W = R.W_STD                # 2.825 m
ZS = R.H_SIDE              # 10.0 roof edge (3.75 m)
ZR = ZS + R.H_CAP          # 10.8 roof top
ZB = zm(0.80)              # body bottom (sill) 2.13
Z_SILL = zm(0.95)          # darker sill line up to here
Z_WIN0, Z_WIN1 = zm(2.00), zm(3.22)     # windows 5.33 .. 8.59
Z_VENT = zm(2.78)                        # top vent split line
Z_DOOR0, Z_DOOR1 = zm(0.62), zm(3.42)   # door leaf (reaches the step)
Z_DW0, Z_DW1 = zm(2.02), zm(3.20)       # door window

WIN_COACH = [(3.2 + 2.07 * i, 4.5 + 2.07 * i) for i in range(10)]    # 3.2 .. 23.2
WC_COACH = (0.9, 1.4)                     # small frosted WC window at one end
DOORS_COACH = [(1.64, 2.68), (23.72, 24.76)]
# cab car (s from the cab front): cab door, bike window, door, 8 windows, door, WC
CAB_WIN = (1.80, 2.50)                    # driver's side window (no cab door: drawings 8073-a/b)
WIN_CAB = [(4.30, 5.55, "bike")] + [(7.3 + 2.07 * i, 8.6 + 2.07 * i, "w") for i in range(8)]
DOORS_CAB = [(5.88, 6.92), (23.72, 24.76)]
WC_CAB = (24.85, 25.40)
BOGIES = [4.0, 22.4]


def wedge_x(z_m):
    """x (as seen) where the red field ends at height z_m: steep '/' diagonal,
    12.2 m at the sill, 14.5 m at the roof edge (drawings + ČB photo)."""
    t = min(1.0, max(0.0, (z_m - 0.87) / (3.75 - 0.87)))
    return 12.2 + 2.3 * t


def x_of(face, s):
    """metres from the screen-left end as seen on this face."""
    return s if face == "-v" else LM - s


# ------------------------------------------------------------------ materials
def coach_side(face, s, z, cab=False):
    """Side paint.  s = metres from the car front, z = model px."""
    x = x_of(face, s)
    z_m = z * PX
    red = x < wedge_x(z_m)
    base = RED if red else GREY
    if z >= ZS - 0.02:
        return base
    # doors (geometry follows s; white leaves on red and grey)
    doors = DOORS_CAB if cab else DOORS_COACH
    for (a, b) in doors:
        if a <= s <= b and Z_DOOR0 <= z <= Z_DOOR1:
            if Z_DW0 <= z <= Z_DW1 and a + 0.24 <= s <= b - 0.24:
                return R.GLASS_HI if z > Z_DW1 - 0.5 else R.GLASS
            return DOOR
    if cab:
        a, b = CAB_WIN
        if a <= s <= b and zm(2.10) <= z <= zm(3.05):
            return WS_HI if z > zm(2.88) else WS           # driver's window: not lit
        wins = WIN_CAB
        a, b = WC_CAB
        if a <= s <= b and zm(2.35) <= z <= zm(3.0):
            return Paint(0x8E969C)                          # frosted WC
    else:
        wins = [(a, b, "w") for (a, b) in WIN_COACH]
        a, b = WC_COACH
        if a <= x_of(face, s) <= b and zm(2.35) <= z <= zm(3.0):
            return Paint(0x8E969C)
    for (a, b, k) in wins:
        if a <= s <= b and Z_WIN0 <= z <= Z_WIN1:
            if s - a < 0.08 or b - s < 0.08:
                return FRAME
            return R.GLASS_HI if z > Z_VENT else R.GLASS
    # lettering on the red (reads left to right as seen)
    if red:
        if cab:
            lx0, ly0 = 3.35, 2.20                             # ÖBB behind the cab door
            sx0, sy0 = 1.60, 1.08                              # CityShuttle under the cab
            if face == "+v":
                lx0, sx0 = 1.0, 3.0                            # the far end on this side
        else:
            lx0, ly0 = 0.70, 1.92
            sx0, sy0 = 3.00, 1.08
        if obb_logo(x - lx0, z_m - ly0):
            return WHITE
        if cityshuttle_script(x - sx0, z_m - sy0):
            return WHITE
    if z < Z_SILL:
        return RED_DK if red else GREY_DK
    return base


def end_face(face, s, v, z):
    """Coach end (gangway end): body colour with the dark gangway door."""
    if abs(v) < 0.40 and z < ZS - 0.6 and z > ZB + 0.2:
        return BELLOWS
    return GREY


# ------------------------------------------------------------------ cab nose
# nose profile: s (m from coupler face) of the front surface vs height (m)
def nose_s(z_m):
    if z_m < 1.25:
        return 0.34                  # buffer beam face
    if z_m < 2.10:
        return 0.36                  # lower front with the lamps
    if z_m < 3.32:
        return 0.38 + (z_m - 2.10) / 1.22 * 0.24    # raked windscreen band
    if z_m < 3.75:
        return 0.62 + (z_m - 3.32) / 0.43 * 0.18
    return 0.80 + (z_m - 3.75) / 0.30 * 0.55        # roof dome


S_CAB = 1.40                       # nose slabs end here (m); straight body behind


def cab_front(z_m, vl, top=False):
    """Front face paint.  vl = lateral cu with + = the car's right (viewer's left).
    top: a sloped or corner surface seen from above / the side (no lamps)."""
    av = abs(vl)
    if top:
        if z_m >= 3.75:
            return ROOF_EDGE
        if z_m < 1.25:
            return BEAM
        if 2.12 <= z_m < 3.30:
            return Paint(0x4C5054)
        return RED
    if z_m >= 3.75:
        return ROOF_EDGE
    if z_m < 1.25:
        return BEAM
    if z_m < 2.12:
        if 1.42 <= z_m <= 1.80 and 0.54 <= av <= 0.78:
            return R.HEAD                 # round headlights, outer
        if 1.45 <= z_m <= 1.72 and 0.36 <= av < 0.50:
            return TAIL_OFF               # tail lamps (off while leading)
        if 1.84 <= z_m <= 2.08 and av < 0.30:
            return WHITE if not (0.06 <= vl <= 0.10) else RED   # ÖBB
        return RED
    if z_m < 3.30:
        if av < 0.80 and 2.24 <= z_m <= 3.20 and not av < 0.05:
            return WS_HI if z_m > 3.02 else WS
        return Paint(0x4C5054)            # dark grey windscreen band
    if 3.40 <= z_m <= 3.68 and av < 0.15:
        return R.HEAD                     # big round lamp on the roof edge
    if 3.44 <= z_m <= 3.62 and 0.22 <= av <= 0.32:
        return TAIL_OFF
    return RED


def cab_half_width(z_m, ds):
    """plan rounding of the cab corners; ds = m behind the local nose face."""
    if z_m >= 3.75:
        r = 0.9
    elif z_m >= 2.1:
        r = 0.35
    else:
        r = 0.22
    if ds >= r:
        return W
    t = 1.0 - ds / r
    return W - (r / M) * 0.9 * (1.0 - np.sqrt(max(0.0, 1.0 - t * t)))


def build(kind, owner="C"):
    """Parts + lines of one car ('coach' or 'cab'), front at u = 0."""
    cab = kind == "cab"
    parts, lines = [], []

    def mat(f, u, v, z, d):
        s = u * M
        z_m = z * PX
        if cab and s < S_CAB + 0.05:
            if f == "-u":
                return cab_front(z_m, v)
            if f == "+z" and z < ZR - 0.05:
                return cab_front(z_m, v, top=True)       # sloped nose surface
            if f in ("+v", "-v"):
                if z >= ZS - 0.02:
                    return ROOF_EDGE
                if s < nose_s(z_m) + 0.25:
                    return cab_front(z_m, v, top=True)
                return coach_side(f, s, z, cab=True)
        if f == "+z":
            return ROOF
        if f in ("+v", "-v"):
            if z >= ZS - 0.02:
                return ROOF_EDGE
            return coach_side(f, s, z, cab=cab)
        return end_face(f, s, v, z)

    u0, u1 = 0.14, L - 0.14
    if cab:
        # stacked nose slabs (buffer beam .. roof dome), plan-rounded corners
        zs = [ZB, zm(1.25)] + list(np.arange(zm(1.25) + 0.5, ZR + 1e-6, 0.4))
        zs = sorted(set([round(z, 3) for z in zs] + [round(ZR, 3)]))
        for i in range(len(zs) - 1):
            z0, z1 = zs[i], zs[i + 1]
            zc = (z0 + z1) / 2 * PX
            sf = nose_s(zc)
            if sf >= S_CAB:
                continue
            steps = [(0.0, 0.10), (0.10, 0.22), (0.22, 0.45), (0.45, S_CAB - sf)]
            for (a, b) in steps:
                if b <= a:
                    continue
                hw = cab_half_width(zc, (a + b) / 2)
                if z0 >= ZS - 0.01:
                    hw = min(hw, W - 0.2)
                parts.append(Part((sf + a) / M, (sf + b) / M, -hw, hw, z0, z1, mat, owner))
        u0 = S_CAB / M
    parts.append(Part(u0, u1, -W, W, ZB, ZS, mat, owner))
    parts.append(Part(u0 + (0.0 if cab else 0.05), u1 - 0.05, -W + 0.2, W - 0.2, ZS, ZR, mat, owner))
    # gangway + buffers at the coupled end(s)
    ends = [(u1, L - 0.02)] if cab else [(0.02, u0), (u1, L - 0.02)]
    for (a, b) in ends:
        parts.append(Part(a, b, -0.40, 0.40, 2.6, ZS - 0.8, lambda *x: BELLOWS, owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *x: BUFFER, owner))
    if cab:
        for vc in (-0.64, 0.64):
            parts.append(Part(0.0, 0.34 / M, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *x: BUFFER, owner))
        # coupler / hoses block under the beam
        parts.append(Part(0.05, 0.40 / M, -0.22, 0.22, 1.2, ZB + 0.3, lambda *x: BUFFER, owner))
    # door leaves and steps continue below the sill (painted by the side material)
    for (a, b) in (DOORS_CAB if cab else DOORS_COACH):
        parts.append(Part(a / M, b / M, -W + 0.02, W - 0.02, Z_DOOR0, ZB + 0.01, mat, owner))
    # underframe equipment + bogies
    parts.append(Part(6.0 / M, (LM - 6.0) / M, -W + 0.25, W - 0.25, 0.9, ZB, lambda *x: UNDER, owner))
    for bm in BOGIES:
        bc = bm / M
        parts.append(Part(bc - 0.72, bc + 0.72, -W + 0.12, W - 0.12, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.0 < z < 1.7) else BOGIE,
                          owner))
    # roof: vents / AC box
    for (a, b) in ((5.0, 6.2), (20.2, 21.4)):
        parts.append(Part(a / M, b / M, -0.34, 0.34, ZR - 0.05, ZR + 0.35, lambda *x: Paint(0x86898D, top=0x7C8084), owner))
    return parts, lines


KINDS = [("cab", "80-73"), ("coach", "21-73")]


def door_frames(d, kind, owner="C"):
    doors = DOORS_CAB if kind == "cab" else DOORS_COACH
    return outline_lines(d, [(a / M, b / M) for (a, b) in doors], W, Z_DOOR0, Z_DOOR1,
                         (0x3A, 0x3C, 0x3F), owner)


def rows():
    out = []
    for kind, _ in KINDS:
        parts, lines = build(kind)
        out.append([R.vehicle_tile(parts, lines + door_frames(d, kind), d, 0.0, {"C"}) for d in DIRS])
    return out


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        prev = args[args.index("--preview") + 1]
        os.makedirs(prev, exist_ok=True)
    rr = rows()
    out = os.path.join(REPO, "vehicle-rail", "obb", "cityshuttle", "sprites", "cityshuttle.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    R.save_rows(rr, out)
    print("wrote", os.path.relpath(out, REPO))
    if prev:
        R.preview(rr, os.path.join(prev, "cityshuttle.png"), z=4, labels=[k for _, k in KINDS])


if __name__ == "__main__":
    main()
