"""Alstom Coradia LINT 41 / LINT 27 DMUs of the Leo Express group, drawn from
scratch with the pak128 box raycaster (work/r/render.py + railkit.py).

  846  LINT 41, Leo Express Tenders (CZ), 2 cars 10 + 10 cu, livery bilooranzova
  648  LINT 41, Leo Express Slovensko (ex-BRB), 2 cars 10 + 10, modrostribrnazluta
  832  LINT 27, Leo Express Tenders (CZ), 1 car 13 cu, cabs at both ends, bilooranzova

Real body (research/multiple_units.md sections 2-3, photos research/photos/lint*):
  LINT 41 41.81 m over couplers (20.9 m per car to the Jakobs centre), LINT 27
  27.26 m; 2.75 m wide, 4.34 m high (roof equipment included).  B'2'B' / B'2'.
Model units: s = metres from the unit's front coupler face, u = s / M carunits
(M = 41.81/20 = 2.09 m/cu for LINT 41, 27.26/13 for LINT 27), v = lateral cu
(+v = right-hand side in the travel direction), z = model px (1 px = 0.375 m).
Everything along a car is given in car-local metres m from that car's cab nose
(car B of the LINT 41 is car A turned 180 deg).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS

PX = 0.375
W = R.W_STD * 2.75 / 2.825          # 0.896 cu half width
ZS = R.H_SIDE                       # 10.0 side wall top (3.75 m)
ZR = ZS + R.H_CAP                   # 10.8 roof top (4.05 m)
CAPIN = 0.2                         # roof cap inset (cu)

# heights (model px)
Z_BOT = 1.5          # body bottom in the low-floor part (0.56 m)
Z_BOT_BOG = 2.45     # body bottom over the bogies (bogie visible below)
Z_FLOOR = 1.65       # door leaves reach down to here (low floor 0.6 m)
Z_SKIRT = 3.3        # livery: top of the lower band (1.24 m)
Z_WIN0, Z_WIN1 = 4.9, 8.7     # passenger windows 1.84 - 3.26 m
Z_DOOR1 = 8.7        # door top = window top
Z_LAMP0, Z_LAMP1 = 3.8, 4.85

# ------------------------------------------------------------------ liveries
# The livery is only a colour table: geometry, door/window positions and the cab
# shape never depend on it.  livery(name) returns a dict with these keys
# (Paint = shaded per face like natives; plain tuples are used unshaded):
#   body       side wall between the lower band and the window-top line
#   shoulder   side wall above the window-top line + roof-cap sides
#   whiteline  thin line directly above the windows (None = no line)
#   skirt      lower band from the body bottom up to Z_SKIRT
#   roof       roof cap: side colour = shoulder, top = the roof centre
#   roofedge   outer strip of the roof top (the curved shoulder seen from above)
#   cabroof    roof top over the cab (CZ anthracite / BRB yellow cap)
#   swoosh     dark cab-side swoosh (curves from the roof down to the nose)
#   patch      side under the swoosh; frontcorner = the same patch where it
#              wraps round the lower front corners ("84" corner)
#   front      windscreen surround; lampband = front panel with the lamps;
#   lowfront   lower front around the coupler; anticlimb = anti-climber plate
#   door       door leaves; doorsplit = the centre joint of the double door
#   letters    big "leo" on the side next to the door (None = no lettering)
#   grille     louvre under the windows on the car's left side (None = none)
#   logo_front front wordmark colour, logo_dot its orange dots
#   ws, ws_hi  windscreen / cab side window (plain, never lit), lower / upper
WS = (0x46, 0x57, 0x66)          # windscreen / cab side window (never lit)
WS_HI = (0x6A, 0x7F, 0x92)
BLACK = Paint(0x1C1D1F)
BOGIE = Paint(0x2A2B2D)
BOGIE_HI = Paint(0x45484B)
UNDER = Paint(0x323437)
BELLOWS = Paint(0x2C2E31, top=0x3A3C40)
ROOFBOX = Paint(0x9EA2A5, top=0xB3B7BA)
ROOFBOX_DK = Paint(0x8A8E92, top=0x9DA1A4)
EXHAUST = Paint(0x4A4D51, top=0x2E3033)


def livery(name):
    if isinstance(name, dict):
        base = livery(name.get("base", "bilooranzova"))
        base.update({k: v for k, v in name.items() if k != "base"})
        return base
    if name == "bilooranzova":
        # Leo Express Tenders (CZ) 2019-: white, anthracite, orange
        anth = Paint(0x3B3E43)
        white = Paint(0xE9EBEC)
        return dict(
            body=white, shoulder=anth, whiteline=None, skirt=Paint(0x36393D),
            roof=Paint(0x3B3E43, top=0x8C8F93), roofedge=Paint(0x3B3E43, top=0x44474C),
            cabroof=Paint(0x3B3E43, top=0x44474C),
            swoosh=anth, patch=white, frontcorner=white, front=anth, lampband=anth,
            lowfront=anth, anticlimb=Paint(0xF07A22, top=0xF38A36),
            door=Paint(0xF07A22), doorsplit=Paint(0x2B2D30), letters=Paint(0xF07A22),
            grille=Paint(0x8E9295), logo_front=(0xF4, 0xF5, 0xF6), logo_dot=(0xF0, 0x7A, 0x22),
            ws=WS, ws_hi=WS_HI)
    if name == "modrostribrnazluta":
        # BRB (Bayerische Regiobahn) colours kept by Leo Express Slovensko
        blue = Paint(0x2B3F8E)
        silver = Paint(0xD8D5CC)
        return dict(
            body=silver, shoulder=blue, whiteline=Paint(0xF6F6F4), skirt=blue,
            roof=Paint(0x2B3F8E, top=0x8E939B), roofedge=Paint(0x2B3F8E, top=0x34489A),
            cabroof=Paint(0xE8D35C),
            swoosh=blue, patch=silver, frontcorner=silver, front=blue, lampband=silver,
            lowfront=blue, anticlimb=Paint(0x26377C, top=0x2E4290),
            door=Paint(0xE3C84A), doorsplit=Paint(0x3A3C40), letters=None,
            grille=None, logo_front=(0x3A, 0x3C, 0x40), logo_dot=(0xF0, 0x7A, 0x22),
            ws=WS, ws_hi=WS_HI)
    raise ValueError(name)


palette = livery


# ------------------------------------------------------------------ cab nose profile
def _bez(t, p0, p1, p2):
    return (1 - t) ** 2 * p0 + 2 * t * (1 - t) * p1 + t * t * p2


_RS = [(_bez(t, 2.20, 2.57, 3.15), _bez(t, 9.7, ZR, ZR)) for t in np.linspace(0, 1, 60)]


def nose_m(z):
    """Distance (m) of the cab front surface behind the coupler face at height z."""
    if z < 1.7:
        return 0.12                                   # orange anti-climber plate
    if z < 3.7:
        return 0.38 + (z - 1.7) * 0.015               # lower front, near vertical
    if z < 4.9:
        return 0.41 + (z - 3.7) / 1.2 * 0.17          # lamp band, slightly raked
    if z < 9.7:
        return 0.58 + (z - 4.9) / 4.8 * 1.62          # raked windscreen
    for (s, zz) in _RS:                               # rounded roof front
        if zz >= z:
            return s
    return 3.15


M_CAB = 3.2          # cab section length (m); the straight body starts here
M_SWOOSH = 3.3       # rear edge of the cab-side swoosh


def swoosh_z(m):
    """Lower edge of the dark cab swoosh on the side at car-local m."""
    return 4.35 + 0.95 * (min(m, M_SWOOSH) / M_SWOOSH) ** 2.2


def front_halfwidth(z):
    """The cab front leans in towards the roof (bullet-shaped head-on outline)."""
    if z < 4.9:
        return W
    return W - 0.13 * min(1.0, (z - 4.9) / 5.9)


# ------------------------------------------------------------------ layouts (car-local metres)
LINT41 = dict(
    length_m=41.81 / 2, cab_rear=False,
    windows=[(3.75, 5.30), (5.80, 7.35), (7.80, 8.75),
             (11.75, 13.30), (13.80, 15.35), (15.85, 17.40), (18.25, 19.95)],
    doors=[(9.80, 11.30)],
    # huge orange "leo" on the car's left side, from the door towards the joint
    letters={"L": [("l", 13.30, 13.75), ("e", 13.95, 15.40), ("o", 15.85, 17.40)]},
    grille={"L": (5.8, 7.3)},
    bogies=[4.40, 20.905],
    roofbox=[(4.2, 7.6)], exhaust=[8.3], ac=[(11.0, 15.0)],
)
LINT27 = dict(
    length_m=27.26, cab_rear=True,
    windows=[(3.90, 5.50), (5.95, 7.35), (7.75, 8.40),
             (10.70, 12.30), (12.80, 14.45), (14.95, 16.60),
             (18.85, 19.50), (19.90, 21.30), (21.75, 23.35)],
    doors=[(8.75, 10.25), (17.00, 18.50)],
    # right side (photo usti_lint27_2022): "o" next to the front door; the left
    # side is the 180-degree turn of it ("o" next to the rear door)
    letters={"R": [("o", 10.70, 12.30), ("e", 12.75, 14.30), ("l", 14.50, 14.95)],
             "L": [("l", 12.25, 12.70), ("e", 12.90, 14.45), ("o", 14.95, 16.60)]},
    grille={},
    bogies=[4.40, 27.26 - 4.40],
    roofbox=[(5.0, 8.4)], exhaust=[9.0], ac=[(16.0, 22.6)],
)


def letter_hit(ch, x, z):
    """Stroke mask of a big lowercase letter; x = 0..1 across it as READ."""
    if ch == "l":
        return 4.1 <= z <= 9.6
    z0, z1 = 4.1, 7.9
    if not (z0 <= z <= z1):
        return False
    y = (z - z0) / (z1 - z0)         # 0 bottom .. 1 top
    ring = x < 0.30 or x > 0.70 or y < 0.24 or y > 0.76
    if ch == "o":
        return ring
    if ch == "e":
        if 0.44 <= y <= 0.62:
            return True              # middle bar
        if x > 0.62 and 0.18 < y < 0.44:
            return False             # the open lower right of the "e"
        return ring
    return False


# ------------------------------------------------------------------ the model
class Car:
    """One car body. s_cab = unit metres of its cab nose; dirn = +1 if car-local
    m grows towards the unit rear (car A, LINT 27), -1 for car B (turned)."""

    def __init__(self, lay, liv, owner, s_cab, dirn, M, lamp_front, lamp_rear=None):
        self.lay, self.C, self.owner = lay, livery(liv), owner
        self.s_cab, self.dirn, self.M = s_cab, dirn, M
        self.lamp_front, self.lamp_rear = lamp_front, lamp_rear
        self.L = lay["length_m"]

    # coordinate helpers
    def m_of(self, u):
        return self.dirn * (u * self.M - self.s_cab)

    def u_of(self, m):
        return (self.s_cab + self.dirn * m) / self.M

    def box(self, m0, m1, v0, v1, z0, z1, mat):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat, self.owner)

    def carside(self, face):
        return "L" if ((face == "-v") == (self.dirn == 1)) else "R"

    def cab_local(self, m):
        """(distance from the nearer cab nose, which cab) - LINT 27 has two."""
        if self.lay["cab_rear"] and m > self.L / 2:
            return self.L - m, "rear"
        return m, "front"

    # ---- materials
    def side(self, m, z, cs):
        C, lay = self.C, self.lay
        if z >= ZS:
            return C["shoulder"]
        mc, _ = self.cab_local(m)
        # the LINT 27's rear half is the 180-degree turn of its front half
        mm = m
        if mc < M_SWOOSH + 0.6:
            if mc < M_SWOOSH and z > swoosh_z(mc):
                if 5.5 <= z <= 8.55 and nose_m(z) + 0.32 <= mc <= 3.05:
                    return C["ws_hi"] if z > 8.0 else C["ws"]   # cab side window
                return C["swoosh"]
            if z >= Z_WIN1:
                return C["whiteline"] if (C["whiteline"] and z < 9.55) else C["shoulder"]
            if z < Z_SKIRT:
                return C["skirt"]
            return C["patch"]
        # straight body
        if C["letters"] is not None:
            for (ch, a, b) in lay["letters"].get(cs, []):
                # on the car's right side screen-left is the car's rear end (larger
                # m): mirror the glyph so it reads left-to-right as seen there
                x = (mm - a) / (b - a)
                if a <= mm <= b and letter_hit(ch, 1 - x if cs == "R" else x, z):
                    return C["letters"]
        if z >= Z_WIN1:
            if C["whiteline"] is not None and z < 9.55:
                return C["whiteline"]
            return C["shoulder"]
        for (a, b) in lay["doors"]:
            if a <= mm <= b and z >= Z_FLOOR:
                t = (mm - a) / (b - a)
                if 0.20 <= t <= 0.80 and Z_WIN0 - 0.3 <= z <= Z_DOOR1 - 0.45:
                    return R.GLASS                          # the two leaf windows + split
                if 0.44 <= t <= 0.56:
                    return C["doorsplit"]
                return C["door"]
        if Z_WIN0 <= z <= Z_WIN1:
            for (a, b) in lay["windows"]:
                if a <= mm <= b:
                    return R.GLASS_HI if z > Z_WIN1 - 0.55 else R.GLASS
        g = lay["grille"].get(cs) if C["grille"] is not None else None
        if g and g[0] <= mm <= g[1] and 3.55 <= z <= 4.45:
            return C["grille"]
        if z < Z_SKIRT:
            return C["skirt"]
        return C["body"]

    def front(self, m, vl, z, which):
        """Cab front surface (vl = lateral as seen from the car's own frame)."""
        C = self.C
        lamp = self.lamp_front if which == "front" else self.lamp_rear
        av = abs(vl)
        if z < 1.7:
            return C["anticlimb"]
        hw = front_halfwidth(z)
        corner = av > hw - 0.24
        if z < 4.9:
            if corner and Z_SKIRT <= z < swoosh_z(0.3) + 0.2:
                return C["frontcorner"]                      # white corner patch "84"
            if z < 3.7:
                if av < 0.34 and z < 3.3:
                    return BLACK                              # covered coupler
                return C["lowfront"]
            if lamp is not None and 0.44 <= av <= 0.70 and Z_LAMP0 <= z <= Z_LAMP1:
                return lamp
            if 3.8 <= z <= 4.85:
                # "leo express" wordmark, orange dots in front of it (as seen from
                # the front the car's right-hand side +vl is on the viewer's left)
                if 0.16 <= vl <= 0.34:
                    return C["logo_dot"]
                if -0.30 <= vl < 0.12:
                    return C["logo_front"]
            return C["lampband"]
        if z < 9.7:
            if av < hw - 0.13 and 5.05 <= z <= 9.45:
                return C["ws_hi"] if z > 8.7 else C["ws"]
            return C["front"]
        if lamp is R.HEAD and av < 0.13 and z < 10.35:
            return R.HEAD                                    # top marker light
        return C["cabroof"]

    def mat(self, f, u, v, z, d):
        m = self.m_of(u)
        vl = v * self.dirn
        mc, which = self.cab_local(m)
        if f == "+z":
            if mc < M_CAB and z < ZR - 0.05:
                # tops of the stepped nose slabs: the sloped front surface
                return self.front(m, vl if which == "front" else -vl, z, which)
            if z < ZS - 0.05:
                return self.C["skirt"] if z < Z_SKIRT else self.C["body"]
            if mc < M_CAB - 0.1:
                return self.C["cabroof"]
            if abs(v) > W - CAPIN - 0.2:
                return self.C["roofedge"]     # the curved shoulder seen from above
            return self.C["roof"]
        if f in ("+v", "-v"):
            cs = self.carside(f)
            return self.side(m, z, cs)
        # u faces: cab fronts face away from the car body
        facing_front = (f == "-u") == (self.dirn == 1)       # faces the car's own cab end
        if (which == "front" and facing_front and mc < M_CAB) or \
           (which == "rear" and not facing_front and mc < M_CAB):
            return self.front(m, vl if which == "front" else -vl, z, which)
        # inner ends (joint) and slab steps facing the body
        if mc < M_CAB:
            return self.front(m, vl if which == "front" else -vl, z, which)
        return self.C["shoulder"] if z > Z_WIN1 else Paint(0x2C2E31)

    # ---- geometry
    def parts(self, joint_end=None):
        """joint_end: car-local m where the body ends at the joint (LINT 41)."""
        P = []
        mat = self.mat
        L = self.L
        ends = [("front", 0.0)] + ([("rear", L)] if self.lay["cab_rear"] else [])
        body_m0 = M_CAB
        body_m1 = L - M_CAB if self.lay["cab_rear"] else joint_end
        # bogie cut-outs (m ranges where the body bottom is raised)
        cuts = []
        for bc in self.lay["bogies"]:
            cuts.append((bc - 1.35, bc + 1.35))
        # main body above the cut-out line, full length between the cabs
        P.append(self.box(body_m0, body_m1, -W, W, Z_BOT_BOG, ZS, mat))
        # low skirt between the cut-outs
        edges = [body_m0] + [x for c in cuts for x in c] + [body_m1]
        edges = sorted(min(max(e, body_m0), body_m1) for e in edges)
        for i in range(0, len(edges) - 1):
            a, b = edges[i], edges[i + 1]
            mid = (a + b) / 2
            if any(c0 <= mid <= c1 for (c0, c1) in cuts) or b - a < 0.05:
                continue
            P.append(self.box(a, b, -W, W, Z_BOT, Z_BOT_BOG + 0.01, mat))
        # roof cap
        cap0 = M_CAB - 0.05
        cap1 = (L - M_CAB + 0.05) if self.lay["cab_rear"] else joint_end - 0.06
        P.append(self.box(cap0, cap1, -W + CAPIN, W - CAPIN, ZS, ZR, mat))
        # cab noses: stacked slabs with a rounded plan (corner steps)
        for (which, m_nose) in ends:
            sg = 1 if which == "front" else -1
            zs = list(np.arange(1.3, 4.9, 0.4)) + list(np.arange(4.9, ZR - 0.01, 0.3))
            for i, z0 in enumerate(zs):
                z1 = zs[i + 1] if i + 1 < len(zs) else ZR
                zc = (z0 + z1) / 2
                mf = nose_m(zc)
                if mf >= M_CAB:
                    continue
                hw = front_halfwidth(zc)
                if z0 >= ZS - 0.01:
                    hw = min(hw, W - CAPIN)
                steps = [(0.0, 0.18, 0.20), (0.18, 0.45, 0.07), (0.45, 99, 0.0)]
                for (d0, d1, cut) in steps:
                    a = mf + d0
                    b = min(M_CAB, mf + d1)
                    if a >= b:
                        continue
                    if cut == 0.0 and z1 > ZS + 0.01:
                        cut = 0.0
                    hh = hw - cut
                    if z0 >= ZS - 0.01:
                        hh = min(hh, W - CAPIN - cut * 0.5)
                    ma, mb = (m_nose + sg * a, m_nose + sg * b)
                    P.append(self.box(min(ma, mb), max(ma, mb), -hh, hh, z0, z1, mat))
            # anti-climber plate (wraps around the lower corners)
            for (a, b, cut) in ((0.12, 0.30, 0.16), (0.30, 1.4, 0.05)):
                ma, mb = m_nose + sg * a, m_nose + sg * b
                P.append(self.box(min(ma, mb), max(ma, mb), -(W - cut), W - cut, 0.8, 1.7,
                                  lambda f, u, v, z, d: self.C["anticlimb"]))
        return P

    def roof_parts(self):
        P = []
        lay = self.lay
        ends = [0.0] if not lay["cab_rear"] else [0.0]
        for (a, b) in lay["roofbox"]:
            P.append(self.box(a, b, -0.66, 0.66, ZR - 0.05, ZR + 0.85, lambda *x: ROOFBOX))
            P.append(self.box(a + 0.25, b - 0.25, -0.46, 0.46, ZR + 0.8, ZR + 1.1, lambda *x: ROOFBOX))
        for c in lay["exhaust"]:
            P.append(self.box(c - 0.22, c + 0.22, -0.30, 0.02, ZR - 0.05, ZR + 1.35, lambda *x: EXHAUST))
        for (a, b) in lay["ac"]:
            P.append(self.box(a, b, -0.56, 0.56, ZR - 0.05, ZR + 0.62, lambda *x: ROOFBOX_DK))
        return P

    def under_parts(self, bogie_owner_split=None):
        P = []
        for bc in self.lay["bogies"]:
            a, b = bc - 1.30, bc + 1.30
            if bogie_owner_split is not None and abs(bc - bogie_owner_split) < 0.01:
                b = bc                       # Jakobs bogie: each car draws its half
            P.append(self.box(a, b, -W + 0.12, W - 0.12, 0.0, Z_BOT_BOG + 0.02,
                              lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.1 < z < 1.8) else BOGIE))
        return P


def unit(kind, liv):
    """Parts + lines of a whole unit and its cars as (owner, u_front)."""
    parts, lines = [], []
    if kind == "lint41":
        M = 41.81 / 20.0
        J = 41.81 / 2
        A = Car(LINT41, liv, "A", 0.0, +1, M, R.HEAD)
        B = Car(LINT41, liv, "B", 41.81, -1, M, R.TAIL)
        jend = J - 0.30                  # car bodies end 0.3 m short of the joint
        for c in (A, B):
            parts += c.parts(joint_end=jend)
            parts += c.roof_parts()
            parts += c.under_parts(bogie_owner_split=J)
            # engine / gearbox block under the high floor behind the powered bogie
            parts.append(c.box(5.9, 7.6, -W + 0.22, W - 0.22, 0.9, Z_BOT_BOG,
                               lambda *x: UNDER))
        # bellows at the joint (one block, drawn by car A)
        parts.append(Part((J - 0.34) / M, (J + 0.34) / M, -W + 0.13, W - 0.13, Z_BOT_BOG - 0.2, ZS + 0.3,
                          lambda f, u, v, z, d: BELLOWS if f != "+z" else Paint(0x3A3C40), "A"))
        return parts, lines, [("A", 0.0), ("B", 10.0)]
    if kind == "lint27":
        M = 27.26 / 13.0
        Cc = Car(LINT27, liv, "C", 0.0, +1, M, R.HEAD, lamp_rear=R.TAIL)
        parts += Cc.parts()
        parts += Cc.roof_parts()
        parts += Cc.under_parts()
        parts.append(Cc.box(5.9, 8.0, -W + 0.22, W - 0.22, 0.9, Z_BOT_BOG, lambda *x: UNDER))
        return parts, lines, [("C", 0.0)]
    raise ValueError(kind)


build = unit


def rows_for(kind, liv):
    """8-direction tiles of every car: [[w..sw] car A, [w..sw] car B] (or one row)."""
    parts, lines, cars = build(kind, liv)
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]


def sheet(kind, liv, out):
    """Entry point: render unit `kind` ("lint41" | "lint27") in livery `liv`
    (a name from livery() or a dict of overrides, e.g. {"base": "bilooranzova",
    "body": Paint(0x1478C0), "letters": None, ...}) and save the 1024 x 128n sheet
    (one row per car, lead car first)."""
    rows = rows_for(kind, liv)
    R.save_rows(rows, out)
    return rows


if __name__ == "__main__":
    import leo
    leo.main()
