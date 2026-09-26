"""RegioJet depot shunters 703.602, 740.832 and 730.625 as box models.

Scale as the rest of the rail set: 26.4 m = 13 cu along the track, W_STD 0.92
cu = half of a 2.825 m body across it, 1 model px = 0.375 m up. Shunters are
drawn at real height x 1.08 (HX), a little taller like the native pak128.cs
locomotives. u = cu behind the front buffer face, v = cu to the right,
z = model px above the rail head.

  703  TS Martin T 212.1 (1976), 7.22 m, drawn at length 4. Narrow hood in
       front (leading), cab at the rear end, two axles under a deep frame with
       red/white warning chevrons on the buffer beams. Livery since the 2/2023
       overhaul: dark red with a white waist stripe, bluish-grey frame with a
       white "|| REGIOJET" on it (photo 703-602_2023_3q, Commons 2024).
  740  CKD T 448.0 (1984), 13.6 m, drawn at length 7. Full-height hoods (short
       hood leading, cab, long hood), Bo'Bo'. Never repainted: Vapenka Certovy
       schody white/teal green, green upper half, a green stripe in the white,
       white V on the hood ends, black frame, grey bogies and fuel tank, yellow
       handrails. Proportions from the vagonWEB 742 side drawing (same body):
       short hood 1.5 m, cab 2.1 m, long hood 8.7 m, hoods and cab 3.6 m high,
       roof 4.2 m.
  730  CKD T 457.0 (1989), 13.98 m, drawn at length 7. Low short hood
       (leading, 3.15 m), raised "tower" cab (4.22 m), long hood (3.45 m) with
       two radiator boxes at its outer end. KDS "Hrochostroj" purple/yellow
       with black stripes; for RegioJet Pool (3/2025) the HROCHOSTROJ lettering
       gave way to a yellow panel with the "|| REGIOJET POOL" logo. Layout
       measured on Commons "CZ Class 730 625-1 KDS obr.03" (side-on, 2021).

Headlights at both ends (locomotives), no lit-window specials (cab glass is
plain dark), no tail-light specials. Handrails are 1 px lines hidden behind
the body where the body is in front of them (lines_occluded).

    python tools/railrender/rj_shunters.py [--preview DIR]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")

import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS, back_vec, frame, local_to_screen, VIEW  # noqa: E402

PX = 0.375          # metres per model px
HX = 1.08           # locomotive height exaggeration (natives draw locos taller)
LAT = 2.825 / 2 / R.W_STD   # metres per lateral cu (1.5353)


def zm(h):
    """height above rail in metres -> model z."""
    return h / PX * HX


def vm(w):
    """half-width in metres -> lateral cu."""
    return w / LAT


WS = (0x2A, 0x34, 0x3D)       # cab glass (plain, never lit)
WS_HI = (0x4F, 0x62, 0x72)
BUFFER = Paint(0x2C2E30)
BUFFER_HEAD = Paint(0x9A9EA2)
OWN = "V"


# ------------------------------------------------------------------ geometry helpers
def box(u0, u1, v0, v1, z0, z1, mat):
    m = mat if callable(mat) else (lambda *a, _p=mat: _p)
    return Part(min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1), z0, z1, m, OWN)


def buffers(L, zc, parts, head=BUFFER_HEAD, depth=0.24):
    vc = vm(0.875)          # buffer centres 1.75 m apart
    for (a, b) in ((0.0, depth), (L - depth, L)):
        for s in (-1, 1):
            parts.append(box(a, b, s * vc - 0.13, s * vc + 0.13, zc - 0.45, zc + 0.45,
                             lambda f, u, v, z, d: head if f in ("-u", "+u") else BUFFER))


def axle_wheels(u, parts, r_m=0.5, W=0.80, col=Paint(0x242426)):
    """a wheelset seen from the side: a dark block one wheel diameter long."""
    r = r_m * 0.515
    parts.append(box(u - r, u + r, -W, W, 0.0, zm(2 * r_m) * 0.92, col))


def bogie(uc, parts, wb, frame_paint, wheel=Paint(0x222224), W=0.80, zt=None, r_m=0.5):
    """Bo bogie: side frame box over two wheelsets; wheels show below it."""
    zt = zt if zt is not None else zm(1.05)
    for a in (uc - wb / 2, uc + wb / 2):
        axle_wheels(a, parts, r_m, W - 0.04, wheel)
    parts.append(box(uc - wb / 2 - 0.30, uc + wb / 2 + 0.30, -W, W, zm(0.42), zt, frame_paint))


def visible_face(d, face):
    f, r = frame(d)
    ax, sg = face[1], (1 if face[0] == "+" else -1)
    n = (-f * sg) if ax == "u" else (r * sg)
    return n[0] + n[1] > 1e-6


def rail_lines(u0, u1, v, z0, z1, col, posts, mid=None):
    """side handrail: top rail (+ optional middle rail) and posts at u positions."""
    out = [((u0, v, z1), (u1, v, z1), col)]
    if mid is not None:
        out.append(((u0, v, mid), (u1, v, mid), col))
    for u in posts:
        out.append(((u, v, z0), (u, v, z1), col))
    return out


def posts_between(u0, u1, step):
    n = max(1, int(round((u1 - u0) / step)))
    return [u0 + (u1 - u0) * i / n for i in range(n + 1)]


def corner_steps(ub, ur, z0, z1, parts, body, edge, WF=0.92, depth=0.26, inset=0.10):
    """step ladders hanging below the frame at the four corners; the lowest
    tread is painted `edge` (yellow / warning colour)."""
    for (a, b) in ((ub, ub + depth), (ur - depth, ur)):
        for s in (-1, 1):
            v0, v1 = s * (WF - inset), s * WF
            parts.append(box(a, b, v0, v1, z0, z1,
                             lambda f, u, v, z, d, _z0=z0: edge if z < _z0 + 0.55 else body))


# ------------------------------------------------------------------ occluded lines
def _hits(q, dl, boxes, eps=1e-3):
    """does a ray from q towards the viewer hit any box? (q local, z scaled)"""
    q = q + dl * eps
    for lo, hi in boxes:
        t0, t1 = 0.0, 1e9
        ok = True
        for k in range(3):
            if abs(dl[k]) < 1e-12:
                if q[k] < lo[k] or q[k] > hi[k]:
                    ok = False
                    break
                continue
            ta = (lo[k] - q[k]) / dl[k]
            tb = (hi[k] - q[k]) / dl[k]
            if ta > tb:
                ta, tb = tb, ta
            t0 = max(t0, ta)
            t1 = min(t1, tb)
            if t0 > t1:
                ok = False
                break
        if ok and t1 > 0:
            return True
    return False


def tile(parts, lines, d, u_front=0.0):
    """R.vehicle_tile with depth-tested 1 px lines."""
    bx, by = back_vec(d)
    ax, ay = R.ANCHOR[d]
    a = (ax - u_front * bx, ay - u_front * by)
    img, owner = R.render_view(parts, [], d, a)
    k = R.KZ[d]
    f, r = frame(d)
    dl = np.array([-(VIEW @ f), VIEW @ r, VIEW[2]], float)
    dl = dl / np.linalg.norm(dl)
    boxes = [(np.array([p.b[0], p.b[2], p.b[4] * k]), np.array([p.b[1], p.b[3], p.b[5] * k]))
             for p in parts]
    for (p0, p1, col) in lines:
        col = R.safe(R.rgb(col)) if isinstance(col, int) else col
        A = np.array([p0[0], p0[1], p0[2] * k], float)
        B = np.array([p1[0], p1[1], p1[2] * k], float)
        sa = local_to_screen(d, a, *A)
        sb = local_to_screen(d, a, *B)
        n = int(max(2, 3 * max(abs(sb[0] - sa[0]), abs(sb[1] - sa[1])) + 1))
        for i in range(n + 1):
            q = A + (B - A) * i / n
            qx, qy = local_to_screen(d, a, *q)
            px, py = int(math.floor(qx)), int(math.floor(qy))
            if not (0 <= px < 128 and 0 <= py < 128):
                continue
            if _hits(q, dl, boxes):
                continue
            img[py, px] = col
    out = img.copy()
    return out


def lines_for_view(side_lines, d):
    """side_lines: list of (face, [lines]); keep the lines of faces seen in view d
    (both long sides in the end-on views nw/se, where neither faces the viewer)."""
    out = []
    for face, ls in side_lines:
        f, r = frame(d)
        if face in ("+v", "-v"):
            n = r * (1 if face == "+v" else -1)
            if n[0] + n[1] > -1e-6:
                out += ls
        else:
            if visible_face(d, face):
                out += ls
    return out


def render_row(model):
    parts, side_lines = model
    return [tile(parts, lines_for_view(side_lines, d), d) for d in DIRS]


# ------------------------------------------------------------------ 703.602
def build_703():
    L = 4.0
    C = dict(red=Paint(0xA23244, top=0xB4505F), white=Paint(0xF0F2F2), frame=Paint(0x56667E, top=0x4A5664),
             chev_r=Paint(0xC8262E), chev_w=Paint(0xF2F2F2), louvre=Paint(0x7C2635),
             roof=Paint(0x9A3042, top=0xB4505F), rail=0x2A2A2E, silver=Paint(0xB4B8BC, top=0xC4C8CA))
    UB, UF = 0.22, 0.42          # buffer beam face, hood front
    UH1 = 2.30                   # hood -> cab
    UC1 = 3.36                   # cab rear wall
    UR = L - UB                  # rear beam face
    ZFB, ZW = zm(0.70), zm(1.12)  # frame bottom, walkway
    ZHS, ZHT = zm(2.78), zm(2.94)  # hood side top, hood roof
    ZCS, ZCR = zm(3.12), zm(3.35)  # cab side top, cab roof crown
    ZST0, ZST1 = zm(1.84), zm(1.84) + 1.0   # white stripe (1 px)
    WF, WH, WC = 0.92, vm(0.90), vm(1.36)
    parts, side_lines = [], []

    def stripe(z):
        return ZST0 <= z < ZST1

    # frame (bluish grey) with the white RJ logo on its side
    def frame_mat(f, u, v, z, d):
        if f == "+z":
            return C["frame"]
        if f in ("+v", "-v"):
            # warning chevrons on the ends of the frame sides
            cu = min(u - UB, UR - u)
            if cu < 0.20:
                return C["chev_r"] if int((cu / 0.177 + z) / 2) % 2 == 0 else C["chev_w"]
            # "|| REGIOJET" on the frame, reading left to right as seen
            t = (u - 1.62) / 0.62
            if f == "+v":
                t = 1 - t
            if 0 <= t <= 1 and ZFB + 0.1 <= z <= ZFB + 1.1:
                if t < 0.14:
                    return C["chev_r"] if int(t * 30) % 2 == 0 else C["frame"]
                if t > 0.2:
                    return C["white"]
            return C["frame"]
        # end faces: red/white chevrons meeting in the middle (45 deg, 2 px bands)
        return C["chev_r"] if int((abs(v) / 0.177 + z) / 2) % 2 == 0 else C["chev_w"]
    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, frame_mat))
    # deep buffer beam plates below the frame at both ends
    for (a, b) in ((UB, UB + 0.16), (UR - 0.16, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.36), ZFB, frame_mat))
    buffers(L, zm(1.06), parts)
    for a in (1.20, 2.80):
        axle_wheels(a, parts, 0.5, 0.78)
    # hood
    def hood_mat(f, u, v, z, d):
        if f == "+z":
            return C["roof"]
        if stripe(z):
            return C["white"]
        if f in ("-u",):
            # front: top headlight, grille, two lower lamps at the corners
            if z > ZHS - 1.2 and abs(v) < 0.12:
                return R.HEAD
            if abs(v) < 0.26 and ZW + 0.8 < z < ZST0 - 0.2:
                return C["louvre"]
            if abs(v) > WH - 0.14 and ZW + 0.6 < z < ZW + 1.3:
                return R.HEAD
            return C["red"]
        # louvred doors: dark red slots in two rows
        uu = (u - UF) / (UH1 - UF)
        if 0.06 < uu < 0.96 and ((ZW + 0.6 < z < ZW + 1.4) or (ZST1 + 0.4 < z < ZST1 + 1.4)):
            if (uu * 7.0) % 1.0 < 0.55:
                return C["louvre"]
        return C["red"]
    parts.append(box(UF, UH1, -WH, WH, ZW, ZHS, hood_mat))
    parts.append(box(UF + 0.03, UH1, -WH + 0.05, WH - 0.05, ZHS, ZHT,
                     lambda f, u, v, z, d: C["roof"]))
    # cab (full width, at the rear)
    def cab_mat(f, u, v, z, d):
        if f == "+z":
            return C["roof"]
        if stripe(z):
            return C["white"]
        win = ZST1 + 0.5 <= z <= ZCS - 0.45
        if f in ("+v", "-v") and win:
            cu = u - UH1
            if 0.10 <= cu <= 0.26:              # door window (front of the cab side)
                return WS
            if 0.42 <= cu <= 0.98:              # big side window
                return WS_HI if z > ZCS - 1.2 else WS
        if f == "+u" and win:
            if 0.10 < abs(v) < WC - 0.10:       # two rear windows
                return WS_HI if z > ZCS - 1.2 else WS
        if f == "+u" and z > ZCS - 0.6 and abs(v) < 0.12:
            return R.HEAD
        if f == "+u" and abs(v) > WC - 0.14 and ZW + 0.5 < z < ZW + 1.2:
            return R.HEAD
        if f == "-u" and win and abs(v) > WH + 0.04:
            return WS
        return C["red"]
    parts.append(box(UH1, UC1, -WC, WC, ZW, ZCS, cab_mat))
    # rounded cab roof: two slabs, the lower one a little overhang
    parts.append(box(UH1 - 0.03, UC1 + 0.03, -WC - 0.02, WC + 0.02, ZCS, ZCS + 0.35,
                     lambda f, u, v, z, d: C["roof"]))
    parts.append(box(UH1 + 0.05, UC1 - 0.05, -WC + 0.18, WC - 0.18, ZCS + 0.35, ZCR,
                     lambda f, u, v, z, d: C["roof"]))
    # exhaust stack between hood and cab, horn
    parts.append(box(UH1 - 0.30, UH1 - 0.04, -0.22, 0.22, ZHT, ZHT + 1.1, C["silver"]))
    corner_steps(UB, UR, zm(0.30), ZFB, parts, C["frame"], Paint(0x8A9096))
    # front / rear end handholds
    fr = []
    for s in (-1, 1):
        fr.append(((UB + 0.05, s * 0.62, ZW), (UB + 0.05, s * 0.62, ZW + 2.8), C["rail"]))
    side_lines.append(("-u", fr))
    rr = []
    for s in (-1, 1):
        rr.append(((UR - 0.05, s * 0.70, ZW), (UR - 0.05, s * 0.70, ZW + 3.2), C["rail"]))
    side_lines.append(("+u", rr))
    return parts, side_lines


# ------------------------------------------------------------------ 740.832
def build_740():
    L = 7.0
    GREEN = Paint(0x3FAC94, top=0x3A9C87)
    C = dict(green=GREEN, white=Paint(0xE9EDEF, top=0xDCE1E3), roof=Paint(0xAEB3B6, top=0xB8BCBE),
             frame=Paint(0x2B2D31, top=0x3A3D42), bogie=Paint(0x6A7074), tank=Paint(0x767C80, top=0x858B8E),
             louvre=Paint(0x33917C), yellow=0xE6BE2E, plate=Paint(0xC2323A), cabroof=Paint(0x4E9E8A, top=0x9EA4A8),
             redlamp=Paint(0x8A1E22), step=Paint(0xE6BE2E))
    UB = 0.24                        # beam faces
    UR = L - UB
    US0, US1 = 0.31, 1.08            # short hood
    UC0, UC1 = 1.08, 2.16            # cab
    UL0, UL1 = 2.16, L - 0.31        # long hood
    ZFB, ZW = zm(0.90), zm(1.60)
    ZS = zm(1.60) + 6.0             # hood side top (3.6 m, rounded to whole bands)
    ZR1, ZR = zm(3.92), zm(4.20)
    WF, WH, WC = 0.92, 0.66, 0.90
    # side bands (bottom -> top): white, green stripe, white stripe, green
    Z1, Z2, Z3 = ZW + 2.0, ZW + 3.0, ZW + 4.0
    parts, side_lines = [], []

    def side_band(z):
        if z < Z1:
            return C["white"]
        if z < Z2:
            return C["green"]
        if z < Z3:
            return C["white"]
        return C["green"]

    def v_end(v, z):
        """white V on a green end: green inside the V, white elsewhere."""
        s = abs(v) / WH
        t = (z - ZW) / (ZS - ZW)
        if s < t - 0.30:
            return C["green"]
        if abs(s - t) < 0.30 and t > 0.85 and s > 0.9:
            return C["green"]
        return C["white"]

    def hood_mat(u0, u1, front):
        def m(f, u, v, z, d):
            if f == "+z":
                return C["roof"]
            if f in ("-u", "+u"):
                outer = (f == "-u" and front) or (f == "+u" and not front)
                if not outer:
                    return side_band(z)
                if abs(v) < 0.16 and ZS - 1.2 < z < ZS - 0.4:
                    return R.HEAD                   # top lamp box
                if 0.36 < abs(v) < 0.56:
                    if ZW + 1.1 < z < ZW + 1.8:
                        return R.HEAD               # lower white lamps
                    if ZW + 0.3 < z < ZW + 1.1:
                        return C["redlamp"]
                return v_end(v, z)
            # sides
            b = side_band(z)
            # white VCS chevron panel in the green on the long hood
            if not front and z >= Z3:
                uu = u - (u1 - 2.1)
                if 0 < uu < 1.0 and (z - Z3) < (1.0 - abs(uu - 0.5) * 2) * 2.6:
                    return C["white"]
            # louvre columns in the green upper band
            if z >= Z3 + 0.4 and z < ZS - 0.3:
                rel = (u - u0) / 0.36
                if (rel % 1.0) < 0.3 and u0 + 0.15 < u < u1 - 0.15:
                    return C["louvre"]
            return b
        return m
    parts.append(box(UB, UR, -WF, WF, ZFB, ZW,
                     lambda f, u, v, z, d: C["frame"]))
    # lower buffer beams with the yellow step boards
    for (a, b) in ((UB, UB + 0.10), (UR - 0.10, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.55), ZFB,
                         lambda f, u, v, z, d: C["step"] if z < zm(0.7) else C["frame"]))
    buffers(L, zm(1.06), parts)
    # bogies (grey) and the fuel tank between them
    for uc in (1.67, 5.33):
        bogie(uc, parts, 1.34, C["bogie"])
    parts.append(box(2.90, 4.10, -0.70, 0.70, zm(0.50), ZFB, C["tank"]))
    # hoods
    parts.append(box(US0, US1, -WH, WH, ZW, ZS, hood_mat(US0, US1, True)))
    parts.append(box(UL0, UL1, -WH, WH, ZW, ZS, hood_mat(UL0, UL1, False)))
    for (a, b) in ((US0, US1), (UL0, UL1)):
        # rounded roof edge (white like the top of the hood side), grey roof
        parts.append(box(a + 0.04, b - 0.04, -WH + 0.10, WH - 0.10, ZS, ZR1,
                         lambda f, u, v, z, d: C["roof"] if f == "+z" else C["white"]))
        parts.append(box(a + 0.10, b - 0.10, -WH + 0.26, WH - 0.26, ZR1, ZR, lambda f, u, v, z, d: C["roof"]))
    # long hood roof: radiator/fan box and exhaust
    parts.append(box(4.1, 5.8, -0.36, 0.36, ZR, ZR + 0.55, Paint(0x5E6468, top=0x4C5155)))
    parts.append(box(2.55, 2.75, -0.14, 0.14, ZR, ZR + 0.9, Paint(0x3A3C40, top=0x2A2C30)))

    # cab: green, full width, windows
    def cab_mat(f, u, v, z, d):
        if f == "+z":
            return C["cabroof"]
        win = ZW + 3.1 <= z <= ZS - 0.5
        if f in ("+v", "-v"):
            cu = u - UC0
            if win and (0.10 <= cu <= 0.30 or 0.44 <= cu <= 0.68 or 0.78 <= cu <= 0.98):
                return WS_HI if z > ZS - 1.2 else WS
            if 0.46 < cu < 0.90 and ZW + 2.0 <= z < ZW + 2.6:
                return C["plate"]               # red number plate
            return C["green"]
        if abs(v) > WH + 0.02 and win:
            return WS
        return C["green"]
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZS, cab_mat))
    parts.append(box(UC0 - 0.05, UC1 + 0.03, -WC - 0.02, WC + 0.02, ZS, ZS + 0.5,
                     lambda f, u, v, z, d: C["cabroof"]))
    parts.append(box(UC0 + 0.05, UC1 - 0.05, -WC + 0.2, WC - 0.2, ZS + 0.5, ZR - 0.1,
                     lambda f, u, v, z, d: C["cabroof"]))
    parts.append(box(UC0 + 0.30, UC0 + 0.40, -0.25, 0.25, ZR - 0.1, ZR + 0.6, Paint(0x3A3C40)))  # horns

    # yellow handrails along both walkways and round the ends
    corner_steps(UB, UR, zm(0.35), ZFB, parts, C["frame"], C["step"])
    Y = C["yellow"]
    zt = Z1 - 0.05
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        ls = rail_lines(UL0 + 0.12, UR - 0.04, vv, ZW, zt, Y, posts_between(UL0 + 0.12, UR - 0.04, 0.85))
        ls += rail_lines(UB + 0.04, US1 - 0.06, vv, ZW, zt, Y, posts_between(UB + 0.04, US1 - 0.06, 0.80))
        side_lines.append((face, ls))
    for face, uu in (("-u", UB + 0.04), ("+u", UR - 0.04)):
        ls = []
        for s in (-1, 1):
            ls.append(((uu, s * (WF - 0.03), zt), (uu, s * 0.74, zt), Y))
            ls.append(((uu, s * 0.74, ZW), (uu, s * 0.74, zt), Y))
        side_lines.append((face, ls))
    return parts, side_lines


# ------------------------------------------------------------------ 730.625
def build_730():
    L = 7.0
    C = dict(purple=Paint(0x9C78BC, top=0x9070AE), yellow=Paint(0xF2C948, top=0xF4D05A),
             black=Paint(0x1F1E23), under=Paint(0x34323A, top=0x3E3C46),
             louvre=Paint(0x7A5C98), rail=0x1C1C20, plate=Paint(0xC8323A),
             red=Paint(0xE3342F), blue=Paint(0x1F3A93), roofbox=Paint(0xE8C040, top=0xF0CC52))
    UB = 0.30
    UR = L - UB
    US0, US1 = 0.50, 1.28           # short hood
    UC0, UC1 = 1.28, 2.30           # cab
    UL0, UL1 = 2.30, L - 0.46       # long hood (an exhaust housing stands on its cab end)
    ZFB, ZW = zm(0.90), zm(1.60)
    ZSH = zm(3.15)                  # short hood top
    ZLH = zm(3.45)                  # long hood top
    ZCS, ZCR = zm(3.92), zm(4.22)   # cab side top, cab roof
    ZB0, ZB1 = zm(2.66), zm(2.66) + 1.0   # the black stripe round the whole loco
    WF, WH, WC = 0.92, 0.70, 0.80
    parts, side_lines = [], []

    def band(z, top):
        if z >= ZB1:
            return C["yellow"]
        if z >= ZB0:
            return C["black"]
        return C["purple"]

    # frame: purple sides, dark walkway, yellow edge on the lower beam plates
    def frame_mat(f, u, v, z, d):
        if f == "+z":
            return C["under"]
        return C["purple"]
    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, frame_mat))
    for (a, b) in ((UB, UB + 0.12), (UR - 0.12, UR)):
        parts.append(box(a, b, -WF + 0.06, WF - 0.06, zm(0.40), ZFB,
                         lambda f, u, v, z, d: C["yellow"] if z < zm(0.62) else C["purple"]))
    buffers(L, zm(1.06), parts, head=Paint(0x2A2A2E))
    for uc in (1.77, 5.30):
        bogie(uc, parts, 1.25, C["under"])
    parts.append(box(2.85, 4.25, -0.70, 0.70, zm(0.50), ZFB, C["under"]))

    def logo(u, z, side):
        """yellow panel with '|| REGIOJET POOL' on the long hood, reading left to right."""
        p0, p1 = UL0 + 1.15, UL0 + 2.85
        if not (p0 <= u <= p1 and ZW + 0.7 <= z <= ZB0 - 0.4):
            return None
        t = (u - p0) / (p1 - p0)
        if side > 0:
            t = 1 - t
        zz = z - (ZW + 0.7)
        if 0.05 < t < 0.95 and 0.5 < zz < 1.5:
            if t < 0.12:
                return C["red"] if int(t * 60) % 2 == 0 else C["yellow"]
            if t < 0.55:
                return C["red"]
            if t < 0.80:
                return C["blue"]
        return C["yellow"]

    def hood_mat(u0, u1, top, front):
        def m(f, u, v, z, d):
            if f == "+z":
                return C["yellow"]
            if f in ("-u", "+u"):
                outer = (f == "-u" and front) or (f == "+u" and not front)
                if outer:
                    if abs(v) < 0.30 and top - 1.3 < z < top - 0.4:
                        return R.HEAD               # twin headlights, top centre
                    if 0.34 < abs(v) < 0.58 and ZW + 1.0 < z < ZW + 2.0:
                        return R.HEAD               # lower lamps
                    if abs(v) < 0.22 and ZW + 0.0 < z < ZW + 1.4:
                        return C["black"]           # coupler plate
                return band(z, top)
            if f in ("+v", "-v") and not front:
                lg = logo(u, z, 1 if f == "+v" else -1)
                if lg is not None:
                    return lg
            b = band(z, top)
            if b is C["purple"] and z > ZW + 0.5:
                # louvre grilles at the outer ends of the hoods
                if (front and u > u1 - 0.30) or (not front and u < u0 + 0.35) or \
                   (not front and u > u1 - 0.75 and (u * 5.0) % 1.0 < 0.5):
                    return C["louvre"]
            return b
        return m
    parts.append(box(US0, US1, -WH, WH, ZW, ZSH, hood_mat(US0, US1, ZSH, True)))
    parts.append(box(UL0, UL1, -WH, WH, ZW, ZLH, hood_mat(UL0, UL1, ZLH, False)))
    # radiator boxes on the long hood roof near its outer end
    for (a, b) in ((UL1 - 0.62, UL1 - 0.10), (UL1 - 1.55, UL1 - 0.95)):
        parts.append(box(a, b, -0.52, 0.52, ZLH, ZLH + 0.7, C["roofbox"]))

    # purple exhaust housing between the cab and the long hood, up to the cab roof
    parts.append(box(UL0, UL0 + 0.44, -0.46, 0.46, ZLH, ZCR - 0.15, C["purple"]))

    # tower cab: yellow above the black stripe with the windows, purple roof
    ZWIN0 = ZB1 + 0.65
    ROOF730 = Paint(0x9C78BC, top=0xB294CE)

    def cab_mat(f, u, v, z, d):
        if f == "+z":
            return ROOF730
        cu = u - UC0
        if f in ("+v", "-v"):
            if ZWIN0 <= z <= ZCS - 0.30:
                if 0.08 <= cu <= 0.28 or 0.40 <= cu <= 0.62 or 0.72 <= cu <= 0.94:
                    return WS_HI if z > ZCS - 1.2 else WS
            if 0.42 < cu < 0.86 and ZB1 <= z < ZWIN0:
                return C["plate"]
            return band(z, ZCS)
        if f == "-u" and ZSH + 0.2 <= z <= ZCS - 0.3 and abs(v) < WC - 0.12:
            return WS_HI if z > ZCS - 1.2 else WS
        if f == "+u" and ZLH + 0.2 <= z <= ZCS - 0.3 and abs(v) < WC - 0.14:
            return WS
        return band(z, ZCS)
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZCS, cab_mat))
    parts.append(box(UC0 - 0.06, UC1 + 0.02, -WC + 0.02, WC - 0.02, ZCS, ZCS + 0.45,
                     lambda f, u, v, z, d: ROOF730))
    parts.append(box(UC0 + 0.10, UC1 - 0.08, -WC + 0.22, WC - 0.22, ZCS + 0.45, ZCR,
                     lambda f, u, v, z, d: ROOF730))
    parts.append(box(UC0 + 0.30, UC0 + 0.42, -0.16, 0.16, ZCR, ZCR + 0.6, C["purple"]))  # horn

    # black handrails along both walkways and at the ends
    corner_steps(UB, UR, zm(0.35), ZFB, parts, C["purple"], C["yellow"])
    K = C["rail"]
    zt = ZB0 + 0.05                 # top rail runs along the black stripe
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        ls = rail_lines(UL0 + 0.10, UR - 0.05, vv, ZW, zt, K, posts_between(UL0 + 0.10, UR - 0.05, 1.0))
        ls += rail_lines(UB + 0.05, US1 - 0.05, vv, ZW, zt, K, posts_between(UB + 0.05, US1 - 0.05, 0.75))
        side_lines.append((face, ls))
    for face, uu in (("-u", UB + 0.05), ("+u", UR - 0.05)):
        ls = []
        for s in (-1, 1):
            ls.append(((uu, s * (WF - 0.03), zt), (uu, s * 0.76, zt), K))
            ls.append(((uu, s * 0.76, ZW), (uu, s * 0.76, zt), K))
        side_lines.append((face, ls))
    return parts, side_lines


# ------------------------------------------------------------------ jobs
JOBS = {
    "703": [("cervenobila", lambda: [render_row(build_703())], ["703"])],
    "740": [("bilozelena", lambda: [render_row(build_740())], ["740"])],
    "730": [("fialovozluta", lambda: [render_row(build_730())], ["730"])],
}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for liv, make, labels in JOBS[fam]:
            rows = make()
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
