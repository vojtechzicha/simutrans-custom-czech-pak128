"""ČKD class 708 ("malé lego") two-axle diesel shunter, MBM rail 708.014-6,
drawn with the pak128 box raycaster of the worktree (tools/railrender).

Real: ČKD 1995-97, Bo, LIAZ M 1.2 C 300 kW, electric transmission, 80 km/h,
34 t, 9.45 m over buffers. Hood unit with a long hood (radiator end leading),
a tall cab and a short hood; massive grey frame with walkways and railings.
Proportions from photos: "Lokomotiva 708.006-2, Svitavská pobřežní dráha 01"
(Commons, near side view), zdopravy.cz Aug 2026 photo of 708.014-6 + Blm at
Bruntál - Malá Morávka (the livery: orange-red cab, hood ends and hood tops,
blue hood side panels, light grey frame, black/yellow striped buffer beams,
blue number plate; the ČD 708 scheme).

Drawn at length 5 (M = 1.89 m/cu, like pak128.cs draws its 19 m locos at 10).
s = metres behind the front buffer face; u = s / M; v lateral cu; z model px.
"""
import os
import sys

RR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RR)

import numpy as np          # noqa: E402
import railkit as R         # noqa: E402
from railkit import Paint, Part   # noqa: E402
from render import DIRS, frame    # noqa: E402
import style as S                 # noqa: E402

PX = 0.375
LOB = 9.45
L = 5
M = LOB / L


def zm(h):
    return h / PX


def u(s):
    return s / M


# plan (m) and heights (m)
S_BEAM0, S_BEAM1 = 0.42, LOB - 0.42        # buffer beam faces
S_HOOD0, S_HOOD1 = 0.62, 4.95              # long hood (front face .. cab)
S_ORANGE = 1.15                            # orange radiator section of the hood side
S_CAB0, S_CAB1 = 4.95, 7.45
S_SHORT0, S_SHORT1 = 7.45, 8.60
Z_FRAME0, Z_FRAME1 = 0.30, 1.35
Z_HOOD = 3.05
Z_CAB = 4.12
Z_WIN0, Z_WIN1 = 3.05, 3.90
WF = R.W_STD * 3.10 / 2.825 / 2 * 2       # frame half width (cu) for 3.1 m
WF = R.W_STD * 3.10 / 2.825
WH = R.W_STD * 2.05 / 2.825                # hood half width
WC = R.W_STD * 2.90 / 2.825                # cab half width

ORANGE = Paint(0xE2482C, top=0xE85A3C)
BLUE = Paint(0x2F5FA8, top=0x3A6CB6)
GREY = Paint(0xA3A5A7, top=0xB2B4B5)
GREY_DK = Paint(0x86888A)
DARK = Paint(0x2A2B2D)
WHEEL = Paint(0x2E2F31)
GRILLE = Paint(0xC9CBCB)
LOUVRE = Paint(0x244C8A)                   # louvres on the blue panels
PLATE = Paint(0x2A56A6)
YELLOW = Paint(0xF0C414)
BLACK = Paint(0x1C1C1E)
WS = (0x3E4A54)
WS_HI = (0x5A6874)
RAIL = (0xA4A7A9)                         # railings: light but not white, so they stay quiet


def lamp_face(v, z, front):
    """lamp pair at each lower corner of an end face: headlight over tail lamp."""
    av = abs(v)
    if 0.36 <= av <= 0.58:
        if 5.40 <= z <= 6.50:
            return R.HEAD if front else (0xE8, 0xE8, 0xE0)
        if 4.30 <= z < 5.40:
            return (0x8A, 0x1A, 0x16) if front else R.TAIL
    return None


def hood_front(f, uu, v, z, d):
    """front face of the long hood: grille, lamps, number plate."""
    lf = lamp_face(v, z, True)
    if lf is not None:
        return lf
    if abs(v) < 0.30 and zm(2.1) <= z <= zm(2.4):
        return PLATE
    if -0.20 <= v <= 0.34 and zm(2.45) <= z <= zm(2.95):
        return GRILLE
    return ORANGE


def build():
    parts, own = [], "L"

    def P(s0, s1, v0, v1, z0, z1, mat):
        parts.append(Part(u(s0), u(s1), v0, v1, z0, z1, mat, own))

    # ---- frame (grey), walkway top, buffer beams with black/yellow chevrons
    def frame_mat(f, uu, v, z, d):
        if f in ("-u", "+u"):
            # diagonal black/yellow stripes on the beam faces
            k = int(np.floor((v * 2.2 + z * 0.35)))
            return YELLOW if k % 2 == 0 else BLACK
        if f == "+z":
            return GREY
        if z < zm(0.55):
            return GREY_DK
        return GREY
    P(S_BEAM0, S_BEAM1, -WF, WF, zm(Z_FRAME0), zm(Z_FRAME1), frame_mat)
    # wheels (Bo), under the frame and showing below it
    for wc in (2.75, 6.70):
        P(wc - 0.50, wc + 0.50, -WF + 0.20, WF - 0.20, 0.0, zm(0.62), lambda *a: WHEEL)
    # buffers + coupler
    for (a, b) in ((0.0, S_BEAM0), (S_BEAM1, LOB)):
        for vc in (-0.60, 0.60):
            P(a, b, vc - 0.13, vc + 0.13, zm(0.93), zm(1.20), lambda *a: BLACK)

    # ---- long hood
    def hood_mat(f, uu, v, z, d):
        s = uu * M
        if f == "-u" and s < S_HOOD0 + 0.05:
            return hood_front(f, uu, v, z, d)
        if f == "+z":
            return ORANGE if s < S_ORANGE else BLUE
        if f in ("+v", "-v"):
            if s < S_ORANGE:
                return ORANGE
            # louvre columns on the blue panels
            if zm(1.9) <= z <= zm(2.8) and int((s - S_ORANGE) / 0.55) % 2 == 1:
                return LOUVRE
            return BLUE
        return BLUE
    P(S_HOOD0, S_HOOD1, -WH, WH, zm(Z_FRAME1), zm(Z_HOOD), hood_mat)
    # orange rim along the hood top edge (the hood roof frame)
    P(S_HOOD0, S_ORANGE + 0.3, -WH, WH, zm(Z_HOOD), zm(Z_HOOD) + 0.35, lambda *a: ORANGE)

    # ---- cab
    def cab_mat(f, uu, v, z, d):
        s = uu * M
        if f == "+z":
            return ORANGE
        if f in ("-u", "+u"):
            # front (towards the long hood) and rear windows
            if zm(Z_WIN0) <= z <= zm(Z_WIN1) and abs(v) < WC - 0.12 and abs(v) > 0.05:
                return WS_HI if z > zm(Z_WIN1) - 0.5 else WS
            return ORANGE
        # sides: door (rear half) with window, side window (front half)
        if S_CAB0 + 0.25 <= s <= S_CAB0 + 1.05 and zm(Z_WIN0) <= z <= zm(Z_WIN1):
            return WS_HI if z > zm(Z_WIN1) - 0.5 else WS
        if S_CAB0 + 1.35 <= s <= S_CAB0 + 2.20:
            if zm(Z_WIN0) <= z <= zm(Z_WIN1) and S_CAB0 + 1.45 <= s <= S_CAB0 + 2.10:
                return WS_HI if z > zm(Z_WIN1) - 0.5 else WS
            if s < S_CAB0 + 1.43 or s > S_CAB0 + 2.12:
                return Paint(0xA8341F)          # door frame
        if zm(Z_FRAME1) + 0.2 <= z <= zm(Z_FRAME1) + 1.0 and s < S_CAB0 + 1.2:
            return Paint(0xA8341F)              # vent grille under the side window
        return ORANGE
    P(S_CAB0, S_CAB1, -WC, WC, zm(Z_FRAME1), zm(Z_CAB), cab_mat)
    # roof with a slight overhang
    P(S_CAB0 - 0.12, S_CAB1 + 0.10, -WC - 0.05, WC + 0.05, zm(Z_CAB) - 0.4, zm(Z_CAB) + 0.2,
      lambda f, uu, v, z, d: ORANGE if f == "+z" else Paint(S.GUTTER))   # dark roof gutter (2026-09-26 style)
    # exhaust stack at the cab front corner (left side of the loco)
    P(S_CAB0 - 0.28, S_CAB0 - 0.08, -WH + 0.05, -WH + 0.28, zm(Z_HOOD), zm(4.55),
      lambda f, uu, v, z, d: Paint(0x2E2B2A, top=0x141414))

    # ---- short hood
    def short_mat(f, uu, v, z, d):
        s = uu * M
        if f == "+u" and s > S_SHORT1 - 0.05:
            lf = lamp_face(v, z, False)
            if lf is not None:
                return lf
            return ORANGE
        if f == "+z":
            return BLUE
        if f in ("+v", "-v"):
            if zm(1.9) <= z <= zm(2.6) and S_SHORT0 + 0.3 <= s <= S_SHORT1 - 0.3:
                return LOUVRE
            return BLUE
        return BLUE
    P(S_SHORT0, S_SHORT1, -WH, WH, zm(Z_FRAME1), zm(2.95), short_mat)
    return parts


def railings(d):
    """walkway railings on the side facing the viewer (lines are drawn on top of
    everything, so the far-side railings are left out)."""
    f, r = frame(d)
    view = np.array([1.0, 1.0])
    sides = []
    if r[0] * view[0] + r[1] * view[1] > 0.05:
        sides.append(+1)
    if -(r[0] * view[0] + r[1] * view[1]) > 0.05:
        sides.append(-1)
    own = "L"
    z0, z1 = zm(Z_FRAME1), zm(Z_FRAME1 + 1.0)
    L = []
    vv = WF - 0.10
    for sg in sides:
        v = sg * vv
        for (a, b) in ((S_HOOD0 + 0.25, S_HOOD1 - 0.25), (S_SHORT0 + 0.15, S_SHORT1 - 0.10)):
            L.append(((u(a), v, z1), (u(b), v, z1), RAIL, own))
            for s in np.linspace(a, b, max(2, int((b - a) / 1.3) + 1)):
                L.append(((u(s), v, z0), (u(s), v, z1), RAIL, own))
    return L


def render_rows():
    parts = build()
    return [[R.vehicle_tile(parts, railings(d), d, 0.0, {"L"}) for d in DIRS]]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    rows = render_rows()
    R.save_rows(rows, os.path.join(out, "l708.png"))
    R.preview(rows, os.path.join(out, "l708_prev.png"), z=5, labels=["708"])
    print("wrote l708")
