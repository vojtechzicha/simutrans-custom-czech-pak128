"""Small PID buses of the Prague non-DPP operators (VZ-Praha-bus), rendered
with the pak128 box renderer (render.py): BMC Neocity 8.5, BMC Procity 10.6 /
10.7, Erduman Mercedes-Benz Sprinter 519 CDI and TEMSA MD9 LE.

Every bus is drawn at its real length (4.24 px/m in the side views, like the
DPP SOR ICN 9.5 at 40 px and the 12 m SOR NB 12 at 51 px) on the lane origins
of dpmhk.py (a bare 12 m box on the median footprint of the native pak128.cs
12 m buses), so the bodies sit centred on the native lane. Positions in the
specs are real metres from the front (u); t < 0 is the vehicle's left, t > 0
its right (door) side. The models are purely procedural: no source images.

The chosen shapes (user's pick from the variant round, 2026-09-29): Neocity
"real proportions", Procity "window band from 1.3 m", TEMSA "taller and
wider", Sprinter "wider and taller for visibility".

usage: python tools/busrender/praha_small.py [family ...] [--preview DIR]
"""
import os, sys, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from render import Box, render, DIRS          # noqa: E402
from dpmhk import ORIGINS                     # noqa: E402  (read-only import of the lane origins)

T = (231, 255, 255)

# ------------------------------------------------------------------ palette
GLASS = (0x4D, 0x4D, 0x4D)        # special: lit at night
GLASS2 = (0x57, 0x65, 0x6F)       # special: lit at night (lighter glass)
HEADL = (0xFF, 0xFF, 0x53)
TAILL = (0xFF, 0x21, 0x1D)
AMBER = (0xF4, 0xA4, 0x1A)
BLACK = (0x10, 0x10, 0x12)
FRAME = (0x16, 0x16, 0x18)
TIRE = (0x1A, 0x1A, 0x1A)
HUB = (0x8C, 0x8C, 0x90)
ARCH = (0x0C, 0x0C, 0x0C)
STEP = (0xF0, 0xC8, 0x20)
SILVER = (0xB4, 0xB6, 0xBA)
MIRROR = (0x1E, 0x1E, 0x20)

# PID scheme A (as the DPP ICN 9.5 / Streetway sheets): (top, side)
GREY = ((0xD8, 0xDA, 0xDD), (0xC2, 0xC4, 0xC8))
RED = ((0xDA, 0x22, 0x2A), (0xCF, 0x20, 0x28))
RUB = (0x7D, 0x7F, 0x83)          # dark rubbing strip on the grey panels
ACPOD = ((0xE6, 0xE8, 0xEA), (0xCD, 0xCF, 0xD2))
LOUVRE = (0x3C, 0x3E, 0x42)
# PID trikolora (as the DPP SOR BN 12 / NB 12 sheets)
BLUE = ((0x26, 0x57, 0xAD), (0x1E, 0x48, 0x93))
WHITE = ((0xF0, 0xF0, 0xF0), (0xE9, 0xE9, 0xE9))
ROOFLT = (0xD6, 0xD9, 0xDC)
TRED = ((0xC8, 0x0B, 0x15), (0xC0, 0x0A, 0x13))

SH = {"top": 1.0, "right": 1.0, "left": 1.0, "front": 0.96, "rear": 0.96}


def col(pair, face):
    """colour of a (top, side) pair (or a single colour) on a face"""
    if isinstance(pair[0], int):
        pair = (pair, pair)
    if face == "top":
        return pair[0]
    c = pair[1]
    k = SH.get(face, 1.0)
    return tuple(int(round(v * k)) for v in c)


def inr(v, a, b):
    return a <= v < b


# ------------------------------------------------------------------ model
class Bus:
    def __init__(self, sp):
        self.sp = sp
        self.L = sp["L"]
        self.W = sp["W"]
        self.HW = self.W / 2
        for k in ("z0", "zr", "zw0", "zw1", "zb"):
            setattr(self, k, sp[k])
        self.WR = sp.get("wr", 0.48)
        self.ARCH = sp.get("arch", 0.05)
        self.liv = sp["livery"]

    # ---------------------------------------------------------- geometry
    def boxes(self):
        sp, L, HW = self.sp, self.L, self.HW
        s = lambda u: L - u
        bx = []
        hood = sp.get("hood")        # bonnet height; the windscreen above it rakes back in steps
        if hood:
            steps = sp["rake"]          # [(front u, top z), ...] above the bonnet
            bx.append(Box("body", 0.0, L, -HW, HW, self.z0, hood))
            zlo = hood
            for uf, zt in steps:
                bx.append(Box("body", 0.0, s(uf), -HW, HW, zlo, zt))
                zlo = zt
            self.front_u = lambda z: 0.0 if z < hood else next((uf for uf, zt in steps if z < zt), steps[-1][0])
        else:
            bx.append(Box("body", 0.0, L, -HW, HW, self.z0, self.zr))
            self.front_u = lambda z: 0.0
        for k, (a, b, h, hw, kind) in enumerate(sp.get("pods", [])):
            z1 = self.zr + h
            bx.append(Box("pod%d" % k, s(b), s(a), -hw, hw, self.zr, z1))
        for k, a in enumerate(sp["axles"]):
            r = self.WR + self.ARCH
            bx.append(Box("wheel%d" % k, s(a) - r, s(a) + r, -HW + 0.07, HW - 0.07, 0.0, self.WR * 2 + 0.1,
                          faces={"left", "right"}))
        if sp.get("mirrors", True):
            mu = sp.get("mirror_u", 0.0)
            mz = sp.get("mirror_z", (2.00, 2.60))
            for t0, t1 in ((-HW - 0.14, -HW + 0.02), (HW - 0.02, HW + 0.14)):
                bx.append(Box("mirror", s(mu) - 0.10, s(mu) + 0.22, t0, t1, mz[0], mz[1],
                              faces={"front", "right", "left", "top"}))
        return bx

    # ---------------------------------------------------------- textures
    def tex(self, p):
        u = self.L - p.s
        b = p.box
        f = p.face
        if b.startswith("wheel"):
            return self.tex_wheel(p, u)
        if b == "mirror":
            return MIRROR
        if b.startswith("pod"):
            return self.tex_pod(p, u, int(b[3:]))
        if f == "top":
            if p.z < self.zr - 0.01:                 # bonnet / scuttle of the van
                edge = 0.25 - u * 0.5
                return col(RED if p.t < edge else GREY, "top")
            return self.tex_roof(p, u)
        if f in ("left", "right"):
            return self.tex_side(p, u)
        if f == "front":
            if self.sp.get("hood") and p.z >= self.sp["hood"]:
                return self.tex_screen(p)
            return self.tex_front(p)
        return self.tex_rear(p)

    def ln(self, p, u, w=0.0):
        """pixel crosses the line u = const"""
        return p.near(0, self.L - u, w) if w else p.line(0, self.L - u)

    def tex_wheel(self, p, u):
        a = min(self.sp["axles"], key=lambda q: abs(q - u))
        d = math.hypot(u - a, p.z - self.WR)
        if abs(u - a) < 0.2 and abs(p.z - self.WR) < 0.2:
            return HUB
        if d < self.WR:
            return TIRE
        if d < self.WR + self.ARCH and p.z > 0.25:
            return ARCH
        return None

    # livery helpers -------------------------------------------------
    def in_band(self, u):
        return any(a <= u < b for a, b in self.liv.get("bands", []))

    def upper(self, u):
        """roof / cant colour pair at u"""
        L = self.liv
        if L["kind"] == "tri":
            return BLUE
        if self.in_band(u):
            return RED
        return GREY

    def tex_pod(self, p, u, k):
        a, b, h, hw, kind = self.sp["pods"][k]
        f = p.face
        if kind == "ac":
            if f == "top" and abs(p.t) < hw - 0.30 and a + 0.25 < u < b - 0.25:
                return (0x8A, 0x8E, 0x94)
            return col(ACPOD, f)
        if kind == "disp":                       # roof-mounted front destination display
            if f == "front" and inr(p.z, self.zr + 0.07, self.zr + h - 0.06) and abs(p.t) < hw - 0.10:
                return AMBER
            return col(GREY, f) if f != "front" else BLACK
        if kind == "tower":                      # raised engine tower / fairing, body colour
            return col(self.upper(u), f)
        return col(self.upper(u), f)

    def tex_roof(self, p, u):
        if self.liv["kind"] == "tri" and abs(p.t) < self.HW - 0.28:
            return ROOFLT                        # photos (1951, 308150): flat roof light grey, blue edge + pods
        return col(self.upper(u), "top")

    def door_at(self, u, right):
        for d0, d1 in (self.sp["doors"] if right else self.sp.get("ldoors", [])):
            if d0 <= u < d1:
                return d0, d1
        return None

    def tex_side(self, p, u):
        z, f = p.z, p.face
        right = f == "right"
        sp = self.sp
        for a in sp["axles"]:
            if abs(u - a) < self.WR + self.ARCH and math.hypot(u - a, z - self.WR) < self.WR + self.ARCH:
                return None
        if u < self.front_u(z) - 0.01:
            return None
        d = self.door_at(u, right)
        if d and z < self.zw1 + 0.05:
            return self.tex_door(p, u, d, right)
        eng = sp.get("engine")           # rear engine-bay panel (u0, u1, louvres on)
        if eng and eng[0] <= u < eng[1] and z >= self.zb - 0.05 and z < self.zw1 + 0.05:
            if self.liv["kind"] == "tri":
                return col(BLUE, f) if u > eng[1] - 0.25 else BLACK
            if int((z - self.zb) / 0.12) % 2 == 0 and eng[0] + 0.15 < u < eng[1] - 0.20:
                return LOUVRE
            return col(GREY, f)
        if z >= self.zb:
            if z < self.zw1 + 0.05 or (right and inr(u, *sp["sidedisp"]) and z < self.zw1 + 0.30):
                return self.glass_band(p, u, right)
            return self.cant(p, u)
        return self.lower(p, u, right)

    def tex_door(self, p, u, d, right):
        d0, d1 = d
        z = p.z
        if self.ln(p, d0 + 0.02) or self.ln(p, d1 - 0.02):
            return FRAME
        if d1 - d0 > 1.05 and self.ln(p, (d0 + d1) / 2):
            return FRAME
        if not right:                            # van cab door (Sprinter)
            if z < self.zw0 - 0.05:
                return col(self.lower_pair(u, right), p.face)
            return GLASS2 if z < self.zw1 - 0.05 else FRAME
        if p.rng(2)[0] < self.z0 + 0.14:
            return STEP
        if z >= self.zw1 - 0.08:
            return FRAME
        return GLASS

    def cant(self, p, u):
        f = p.face
        L = self.liv
        if L["kind"] == "tri":
            return col(BLUE, f)
        if p.z < L.get("zcant", self.zw1 + 0.12):
            return BLACK
        return col(self.upper(u), f)

    def glass_band(self, p, u, right):
        z = p.z
        sp = self.sp
        if right and inr(u, *sp["sidedisp"]) and inr(z, self.zw1 + 0.04, self.zw1 + 0.30):
            return AMBER
        if not (self.zw0 <= z < self.zw1):
            return FRAME
        a, b = sp.get("glass", (self.front_u(z) + 0.20, self.L - 0.25))
        if not (a <= u < b):
            return FRAME
        if self.ln(p, a + 0.05) or self.ln(p, b - 0.05):
            return FRAME
        drv = sp["drv"]
        if not right and inr(u, *drv):
            if self.ln(p, drv[1]):
                return FRAME
            return GLASS2
        stops = [a, b]
        if right:
            for d0, d1 in sp["doors"]:
                if a < d0 < b: stops.append(d0)
                if a < d1 < b: stops.append(d1)
        else:
            stops.append(drv[1])
            for d0, d1 in sp.get("ldoors", []):
                if a < d1 < b: stops.append(d1)
        stops = sorted(stops)
        pitch = sp.get("pitch", 1.45)
        for q0, q1 in zip(stops[:-1], stops[1:]):
            if q0 <= u < q1:
                n = max(1, int(round((q1 - q0) / pitch)))
                for k in range(1, n):
                    if self.ln(p, q0 + (q1 - q0) * k / n):
                        return FRAME
                if self.ln(p, q0 + 0.02) or self.ln(p, q1 - 0.02):
                    return FRAME
                break
        return GLASS

    def lower_pair(self, u, right):
        L = self.liv
        if L["kind"] == "tri":
            return WHITE
        blocks = L["blocks_r"] if right else L["blocks_l"]
        if any(a <= u < b for a, b in blocks):
            return RED
        return GREY

    def lower(self, p, u, right):
        f, z = p.face, p.z
        L = self.liv
        if L["kind"] == "tri":
            # white band under the windows, red lower body; blue down the rear pillar
            if z >= L["zred"]:
                return col(WHITE, f)
            return col(TRED, f)
        pair = self.lower_pair(u, right)
        rub = L.get("rub")
        if rub and pair is GREY and p.line(2, rub):
            return RUB
        return col(pair, f)

    # ---------------------------------------------------------- front/rear
    def tex_screen(self, p):
        """raked van windscreen (Sprinter)"""
        a = abs(p.t)
        if a > self.HW - 0.12:
            return col(GREY, "front")
        return GLASS

    def tex_front(self, p):
        t, z = p.t, p.z
        a = abs(t)
        HW = self.HW
        fr = self.sp["front"]
        L = self.liv
        tri = L["kind"] == "tri"
        left = t < 0
        if fr == "van":
            # Sprinter: grey bonnet, black grille, red diagonal on the vehicle's left
            if z < 0.36:
                return BLACK
            if a > HW - 0.36 and inr(z, 0.80, 1.00):
                return HEADL if a < HW - 0.10 else col(SILVER, "front")
            if a < 0.62 and inr(z, 0.50, 0.98):
                return BLACK                                   # grille + star
            edge = -0.05 + (z - 0.4) * 0.35                     # diagonal leans to the left going up
            if t < edge:
                return col(RED, "front")
            return col(GREY, "front")
        body_low = WHITE if tri else GREY
        if z < 0.30:
            return BLACK
        zl = self.sp.get("zlamp", (0.62, 0.86))
        if a > HW - 0.40 and inr(z, *zl):
            return HEADL if a < HW - 0.10 else col(SILVER, "front")
        zmask = self.sp.get("zmask", 1.10)                    # bottom of the black windscreen mask
        if z < zmask:
            if tri:
                return col(TRED, "front") if z < 0.62 else col(WHITE, "front")
            if left and z < self.sp.get("zred_front", 0.95) and t > -HW + 0.05 and t < -0.02:
                return col(RED, "front")
            return col(body_low, "front")
        if a > HW - 0.08 and fr != "neo":
            return col(body_low, "front") if z < self.zw1 else BLACK
        zs = self.sp.get("zscreen", (zmask + 0.06, 2.45))
        dz = self.sp.get("zdisp", (2.52, 2.78))
        if inr(z, *dz) and a < 0.95:
            return AMBER
        if inr(z, *zs) and a < HW - 0.14:
            return GLASS
        if z >= self.sp.get("zcap", 9.0):
            return col(BLUE if tri else GREY, "front")
        return BLACK

    def tex_rear(self, p):
        t, z = p.t, p.z
        a = abs(t)
        HW = self.HW
        rr = self.sp["rear"]
        L = self.liv
        tri = L["kind"] == "tri"
        left = t < 0
        if z < 0.30:
            return BLACK
        if rr == "van":
            if a > HW - 0.18 and inr(z, 0.75, 1.55):
                return TAILL
            if a < 0.04:
                return FRAME                                   # split of the rear doors
            if inr(z, 1.55, 2.35) and a < HW - 0.18:
                if inr(z, 2.05, 2.28) and inr(t, 0.20, 0.70):
                    return AMBER
                return GLASS
            if left and z < 1.55 and t > -HW + 0.18:
                return col(RED, "rear")
            return col(GREY, "rear")
        zt = self.sp.get("ztail", (0.70, 1.30))
        if a > HW - 0.24 and inr(z, *zt):
            return TAILL
        ztop = self.sp.get("zrear_black", 1.35)                # black upper rear (window / engine grille)
        if z >= ztop:
            if inr(z, 2.40, 2.62) and inr(t, 0.20, 0.75):
                return AMBER
            if a > HW - 0.10 and not tri:
                return col(GREY, "rear")
            if z >= self.zr - 0.12:
                return col(BLUE if tri else GREY, "rear")
            if self.sp.get("rear_glass") and inr(z, *self.sp["rear_glass"]) and a < HW - 0.30:
                return GLASS
            return BLACK
        if tri:
            return col(TRED, "rear") if z < 0.62 else col(WHITE, "rear")
        if left and t > -HW + 0.05 and t < -0.05:
            return col(RED, "rear")
        return col(GREY, "rear")


# ------------------------------------------------------------------ models
def mk(base, **kw):
    d = dict(base)
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            dd = dict(d[k]); dd.update(v); d[k] = dd
        else:
            d[k] = v
    return d


# BMC Neocity 8.5: 8.50 x 2.45 x 3.14 m, rear overhang 1.925 m; doors 1-2, the
# centre door just ahead of the rear axle; louvred engine tower at the rear
# corner (photos of 1915, 1917).
NEOCITY = dict(
    L=8.50, W=2.52, axles=[2.25, 6.575], z0=0.30, zr=2.98, zw0=1.22, zw1=2.44, zb=1.14,
    doors=[(0.40, 1.45), (3.95, 5.30)], drv=(0.30, 1.45), sidedisp=(1.55, 2.95),
    engine=(7.30, 8.50), glass=(0.20, 8.50), pitch=1.40,
    pods=[(3.10, 4.90, 0.20, 0.82, "ac")],
    front="neo", rear="neo", zmask=1.08, zlamp=(0.72, 0.92), zred_front=1.00, zscreen=(1.14, 2.44),
    zdisp=(2.52, 2.80), zrear_black=1.30, rear_glass=(1.80, 2.25),
    livery=dict(kind="A", blocks_r=[(1.45, 2.85), (5.30, 7.30)], blocks_l=[(1.45, 2.85), (5.30, 7.30)],
                bands=[(1.60, 2.80), (5.40, 7.20)], rub=0.62, zcant=2.60),
)
# the same body in the old PID tricolour (1949-1950, photos 302889 / 315331 on
# foto-busy): blue roof edge, rear corner pillars and raised rear roof
# fairing (from 3 m behind the front, housing the A/C), flat front roof light
# grey, black glazing band, white band over a
# red skirt about as tall as the white
NEOCITY_TRI = mk(NEOCITY, pods=[(3.00, 8.20, 0.20, 0.95, "tower")],
                 livery=dict(kind="tri", zred=0.72))
# BMC Procity 10.6: 10.59 x 2.55 x 3.08 m, doors 2-2-2, the rear one behind the
# rear axle; white A/C unit at the rear of the roof, raised fairing ahead of it
# (photos of 1951, 1954, 1955).
PROCITY = dict(
    L=10.59, W=2.62, axles=[2.55, 7.60], z0=0.30, zr=2.98, zw0=1.36, zw1=2.44, zb=1.30,
    doors=[(0.30, 1.55), (5.65, 6.90), (8.30, 9.50)], drv=(0.30, 1.50), sidedisp=(2.00, 3.60),
    engine=(9.70, 10.59), glass=(0.20, 10.59), pitch=1.45,
    pods=[(3.20, 8.30, 0.18, 0.95, "tower"), (8.30, 9.70, 0.24, 0.85, "ac")],
    front="pro", rear="pro", zmask=1.24, zlamp=(0.66, 0.86), zscreen=(1.30, 2.44), zdisp=(2.52, 2.80),
    zrear_black=1.35, zcap=2.88,
    livery=dict(kind="tri", zred=0.80),
)
# scheme A on the same body (1954, 1955): red columns around both axles, over
# the roof as bands; on the door side the front one runs from door 1 back
PROCITY_A = mk(PROCITY, livery=dict(
    kind="A", blocks_r=[(1.55, 3.30), (6.90, 8.30)], blocks_l=[(1.95, 3.65), (6.95, 8.35)],
    bands=[(1.90, 3.50), (6.95, 8.30)], rub=0.62, zcant=2.60))
# TEMSA MD9 LE (Skoda D'City 9 LE): 9.536 x 2.40 x 3.132 m, wheelbase 4.60 m;
# single front door ahead of the front axle, double centre door ahead of the
# rear axle; raised roof fairing over the rear 2/3. Drawn 2.58 m wide with a
# 3.12 m roof and a tall windscreen (the variant the user picked).
TEMSA = dict(
    L=9.54, W=2.58, axles=[2.55, 7.15], z0=0.30, zr=3.12, zw0=1.20, zw1=2.60, zb=1.12,
    doors=[(0.95, 2.00), (5.15, 6.40)], drv=(0.25, 1.95), sidedisp=(2.10, 3.40),
    engine=(8.30, 9.54), glass=(0.15, 9.54), pitch=1.30,
    pods=[(3.60, 8.60, 0.14, 0.95, "tower")],
    front="temsa", rear="temsa", zmask=1.05, zlamp=(0.62, 0.84), zscreen=(1.08, 2.62), zdisp=(2.68, 2.96),
    zrear_black=1.40, rear_glass=(1.85, 2.45),
    livery=dict(kind="A", blocks_r=[(2.00, 3.65), (6.40, 7.70)], blocks_l=[(1.95, 3.65), (6.55, 7.75)],
                bands=[(2.00, 3.60), (6.50, 7.70)], rub=0.62, zcant=2.76),
)
# Erduman Mercedes-Benz Sprinter 519 CDI (Seyyah low-floor city body): 7.36 x
# 2.02 m, wheelbase 4.325 m; bonnet, raked windscreen, roof-mounted front
# display box and rear A/C; folding door behind the front axle on the right,
# driver's door on the left. Drawn 2.30 m wide with a 2.82 m roof so it reads
# at 1x (the variant the user picked); still clearly smaller than a midibus.
SPRINTER = dict(
    L=7.36, W=2.30, axles=[1.00, 5.325], wr=0.40, z0=0.36, zr=2.82, zw0=1.30, zw1=2.35, zb=1.25,
    hood=1.15, rake=[(0.45, 1.45), (0.62, 1.75), (0.80, 2.82)],
    doors=[(1.55, 2.60)], ldoors=[(0.80, 1.75)], drv=(0.80, 1.75), sidedisp=(9, 9),
    engine=None, glass=(0.85, 7.10), pitch=1.10,
    pods=[(0.80, 1.10, 0.34, 1.02, "disp"), (5.20, 6.80, 0.20, 0.70, "ac")],
    mirror_u=0.85, mirror_z=(1.45, 1.90),
    front="van", rear="van",
    livery=dict(kind="A", blocks_r=[(2.60, 3.60)], blocks_l=[(3.20, 4.80)],
                bands=[(3.20, 4.60)], rub=None, zcant=2.40),
)

# family dir -> {livery colour: model spec}
FAMILIES = {
    "vehicle-bus/praha/bmc_neocity_8_5": {"pidsedocervena": NEOCITY, "pidcervenomodrobila": NEOCITY_TRI},
    "vehicle-bus/praha/bmc_procity_10_6": {"pidcervenomodrobila": PROCITY, "pidsedocervena": PROCITY_A},
    "vehicle-bus/praha/temsa_md9_le": {"pidsedocervena": TEMSA},
    "vehicle-bus/praha/sprinter_519_erduman": {"pidsedocervena": SPRINTER},
}

SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
ALLOWED = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


def build(sp):
    m = Bus(sp)
    tiles = []
    for d in DIRS:
        img, _ = render(d, m.boxes(), m.tex, m.L, np.array(ORIGINS[d]))
        tiles.append(img)
    return tiles


def save_rows(rows, path):
    out = np.zeros((128 * len(rows), 1024, 3), dtype=np.uint8)
    out[:, :] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    flat = out.reshape(-1, 3).astype(np.int64)
    used = set(np.unique((flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]).tolist())
    bad = (used & SPECIAL) - ALLOWED
    if bad:
        raise SystemExit(f"{path}: unintended special colours {sorted(hex(b) for b in bad)}")
    Image.fromarray(out).save(path)
    return out


def preview(sheet, path, z=4):
    a = sheet.copy()
    a[np.all(a == T, axis=2)] = (96, 104, 96)
    Image.fromarray(a).resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST).save(path)


def main():
    args = sys.argv[1:]
    pv = None
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
        os.makedirs(pv, exist_ok=True)
    for fam, livs in FAMILIES.items():
        name = fam.split("/")[-1]
        if args and name not in args:
            continue
        sd = os.path.join(REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        for color, sp in livs.items():
            sheet = save_rows([build(sp)], os.path.join(sd, color + ".png"))
            if pv:
                preview(sheet, os.path.join(pv, f"{name}-{color}.png"))
            print(f"{fam}/sprites/{color}.png")


if __name__ == "__main__":
    main()
