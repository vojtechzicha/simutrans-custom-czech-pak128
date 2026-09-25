"""DPMHK (Hradec Kralove) buses and trolleybuses rendered with the pak128 box
renderer (render.py, from the Prague/Brno SOR NS 12 work): one parametric model
for every body in the set.

Every Simutrans vehicle (section) is rendered separately. A single-section
vehicle is drawn at its real length on the native median lane footprint; an
articulated section of `l` carunits is drawn l * 4/3 m long with its body centre
(4 - l/2) carunits ahead of the tile centre, so the engine's spacing closes the
joints. Positions in the specs are REAL metres from the front (x); they are
mapped piecewise-linearly onto the drawn sections (u, drawn metres from the
front) so that the real joints land on the section boundaries.

usage: python tools/busrender/dpmhk.py [family ...]   regenerate the sheets
       python tools/busrender/dpmhk.py --preview DIR      also write zoomed previews
"""
import os, sys, math
import numpy as np
from PIL import Image
from render import Box, render, project, DIRS, HEAD, P

KCU = 4.0 / 3.0                 # render metres per carunit
W = 2.62                        # 2.55 m real; renders to the 11 px / 8 px widths of native buses
HW = W / 2
PER_CU = {d: P(np.array([HEAD[d][0], HEAD[d][1], 0.0])) * KCU for d in DIRS}

# ------------------------------------------------------------------ palette
GLASS = (0x4D, 0x4D, 0x4D)        # special: lit at night (doors, windscreen, rear window)
GLASS2 = (0x57, 0x65, 0x6F)       # special: lit at night (side-window glass)
HEADL = (0xFF, 0xFF, 0x53)
TAILL = (0xFF, 0x21, 0x1D)
BLACK = (0x1E, 0x1E, 0x20)
FRAME = (0x10, 0x10, 0x12)
AMBER = (0xF4, 0xA4, 0x1A)        # DPMHK destination displays: amber LED
STEP = (0xF0, 0xC8, 0x20)
TIRE = (0x1A, 0x1A, 0x1A)
HUB = (0x8C, 0x8C, 0x90)
ARCH = (0x0C, 0x0C, 0x0C)
POLE = (0x26, 0x26, 0x2A)
POLEBASE = (0x40, 0x40, 0x44)
RACK = (0x9A, 0x9E, 0xA4)         # silver pole-retriever rack (SOR NB trolleybuses)
SILVER = (0xB8, 0xBC, 0xC0)       # headlight clusters, grilles
HANDRAIL = (0xC8, 0xCC, 0xD0)     # the light vertical handrail stripes in the door leaves
BELLOWS = (0x8A, 0x8D, 0x92)
BELLOWS_D = (0x6A, 0x6D, 0x72)
BELLOWS_T = (0x9C, 0x9F, 0xA4)
TIP = (0xF4, 0xC8, 0x10)

RED = (0xD8, 0x28, 0x1E)          # DPMHK red, slightly orange
YEL = (0xF5, 0xC3, 0x00)          # DPMHK golden yellow
WHITE = (0xF6, 0xF6, 0xF6)
ROOFW = (0xEE, 0xEE, 0xEE)        # white roofs
ROOFS = (0xE2, 0xE4, 0xE6)        # light silver-grey roof fairing of the SOR NS
GREEN = (0x2E, 0xB0, 0x3A)        # "Zelena linka" green
GREENM = (0x1F, 0x6E, 0x48)       # EBN 11 green metallic
GREENL = (0x8C, 0xC8, 0x5A)       # EBN 11 light green graphic

SHADE = {"top": 1.0, "right": 0.93, "left": 0.93, "front": 0.87, "rear": 0.87}


def sh(c, f):
    k = SHADE.get(f, 1.0)
    return tuple(int(max(0, min(255, round(v * k)))) for v in c)


def inr(v, a, b):
    return a <= v < b


# ------------------------------------------------------------------ bodies
# x = real metres from the front.  doors on the right (kerb) side.
NS12 = dict(
    face="ns", rear="ns", real_len=12.0, joints=[], cu=[8],
    axles=[2.71, 8.64],
    doors=[(0.41, 1.75), (4.83, 6.16), (9.47, 10.80)],
    drv=(0.42, 1.75),
    z0=0.32, zr=3.00, zwin0=1.24, zwin1=2.40, zband0=1.15, zband1=2.67,
    cap=1.70, sidedisp=(3.05, 4.65), pods=[], mirrors=True,
)
NS18 = dict(
    face="ns", rear="ns", real_len=18.75, joints=[11.10], cu=[8, 6],
    axles=[2.70, 8.60, 15.35],
    doors=[(0.30, 1.60), (4.80, 6.10), (12.65, 13.95), (16.20, 17.50)],
    drv=(0.42, 1.75),
    z0=0.32, zr=3.00, zwin0=1.24, zwin1=2.40, zband0=1.15, zband1=2.67,
    cap=1.70, sidedisp=(3.20, 4.60), pods=[], mirrors=True,
)
# SOR NB 12 / TNB 12 (Skoda 30Tr): 4 doors, the last behind the rear axle
L1A_DIAG = dict(xw_top=2.05, wy=0.60, gap=0.30, k=1.5, xh_top=3.00)
NB12 = dict(
    face="nb", rear="nb", real_len=12.0, joints=[], cu=[8],
    axles=[2.75, 8.60],
    doors=[(0.30, 1.55), (4.15, 5.45), (6.70, 7.90), (9.25, 10.45)],
    drv=(0.35, 1.55),
    z0=0.24, zr=3.00, zwin0=1.22, zwin1=2.46, zband0=1.14, zband1=2.74,
    cap=0.0, sidedisp=(2.10, 3.60), pods=[], mirrors=True, diag=L1A_DIAG,
)
# SOR NB 18 / TNB 18 (Skoda 31Tr): long front section (~12.3 m, 3 doors), short
# pusher-style rear section (2 doors, the last behind the rear axle)
NB18 = dict(
    face="nb", rear="nb", real_len=18.75, joints=[12.30], cu=[9, 5],
    axles=[3.00, 10.55, 16.25],
    doors=[(0.30, 1.55), (4.60, 5.90), (7.60, 8.80), (13.10, 14.30), (16.95, 18.10)],
    drv=(0.35, 1.55),
    z0=0.24, zr=3.00, zwin0=1.22, zwin1=2.46, zband0=1.14, zband1=2.74,
    cap=0.0, sidedisp=(2.30, 3.80), pods=[], mirrors=True, diag=dict(L1A_DIAG, xw_top=2.30, xh_top=3.25),
)
# Iveco Urbanway 12M: 3 doors, the rear one behind the rear axle, then the black
# engine-bay panel
UW12 = dict(
    face="uw1", rear="uw", real_len=12.0, joints=[], cu=[8],
    axles=[2.70, 8.55],
    doors=[(0.32, 1.55), (5.00, 6.30), (9.28, 10.55)],
    drv=(0.35, 1.55),
    z0=0.24, zr=3.00, zwin0=1.20, zwin1=2.45, zband0=1.12, zband1=2.80,
    cap=0.0, sidedisp=(3.10, 4.70), pods=[], mirrors=True, diag=dict(L1A_DIAG, xw_top=1.95),
    engine=(10.62, 11.85),
)
# Iveco Urbanway 18M / Irisbus Citelis 18M: 4 doors (2 per section)
UW18 = dict(
    face="uw2", rear="uw", real_len=18.0, joints=[10.40], cu=[8, 6],
    axles=[2.70, 8.55, 14.85],
    doors=[(0.32, 1.55), (4.70, 6.00), (11.60, 12.90), (15.55, 16.80)],
    drv=(0.35, 1.55),
    z0=0.24, zr=3.00, zwin0=1.20, zwin1=2.45, zband0=1.12, zband1=2.80,
    cap=0.0, sidedisp=(3.10, 4.40), pods=[], mirrors=True, diag=dict(L1A_DIAG, xw_top=1.95),
    engine=(16.90, 17.85),
)
# SOR EBN 9.5 (401) and EBN 11 (403): older SOR e-bus face (black mask, "smile")
EBN95 = dict(
    face="ebn", rear="ns", real_len=9.5, joints=[], cu=[8],
    axles=[2.35, 7.05],
    doors=[(0.30, 1.50), (3.95, 5.20)],
    drv=(0.35, 1.50),
    z0=0.30, zr=2.95, zwin0=1.22, zwin1=2.40, zband0=1.12, zband1=2.62,
    cap=0.40, sidedisp=(2.00, 3.40), pods=[], mirrors=True, diag=dict(L1A_DIAG, xw_top=1.75, k=1.2),
)
EBN11 = dict(
    face="ebn", rear="ns", real_len=11.1, joints=[], cu=[8],
    axles=[2.55, 8.05],
    doors=[(0.30, 1.55), (4.45, 5.75), (8.85, 10.10)],
    drv=(0.35, 1.55),
    z0=0.30, zr=2.95, zwin0=1.22, zwin1=2.40, zband0=1.12, zband1=2.62,
    cap=0.40, sidedisp=(2.10, 3.60), pods=[], mirrors=True,
)


def mk(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


# ------------------------------------------------------------------ vehicle
class Veh:
    def __init__(self, sp, livery):
        self.sp = sp
        self.liv = livery
        self.cu = sp["cu"]
        self.single = len(self.cu) == 1
        if self.single:
            self.U = [0.0, sp["real_len"]]
        else:
            self.U = [0.0]
            for c in self.cu:
                self.U.append(self.U[-1] + c * KCU)
        self.Rk = [0.0] + list(sp["joints"]) + [sp["real_len"]]
        for k in ("z0", "zr", "zwin0", "zwin1", "zband0", "zband1"):
            setattr(self, k.upper(), sp[k])
        M = self.M
        self.axles = [M(a) for a in sp["axles"]]
        self.doors = [(M(a), M(b)) for a, b in sp["doors"]]
        self.drv = (M(sp["drv"][0]), M(sp["drv"][1]))
        self.sidedisp = (M(sp["sidedisp"][0]), M(sp["sidedisp"][1]))
        self.cap = M(sp["cap"]) if sp["cap"] else 0.0
        self.pods = [(M(a), M(b), h, hw, kind) for a, b, h, hw, kind in sp["pods"]]
        self.joints = self.U[1:-1]
        self.BW = 1.00
        self.WR = 0.50
        self.face = sp["face"]
        self.rearstyle = sp["rear"]
        self.poles = sp.get("poles")          # (x base, half spacing)
        self.rack = sp.get("rack")            # (x0, x1, height) silver retriever rack
        self.setup_livery()

    # real metres from front -> drawn metres from front
    def M(self, x):
        for i in range(len(self.Rk) - 1):
            if x <= self.Rk[i + 1] or i == len(self.Rk) - 2:
                r0, r1 = self.Rk[i], self.Rk[i + 1]
                return self.U[i] + (x - r0) / (r1 - r0) * (self.U[i + 1] - self.U[i])

    def sec_len(self, i):
        return self.U[i + 1] - self.U[i]

    def front_arch(self):
        return self.axles[0] - 0.62

    # ------------------------------------------------------------ livery setup
    def setup_livery(self):
        L = self.liv
        sp = self.sp
        self.ROOF = ROOFW
        self.TRIM = RED
        if L == "L2":
            # new 2026 design: red front part, vertical yellow stripe, white behind
            x0, x1 = sp["stripe"]
            self.stripe = (self.M(x0), self.M(x1))
            self.logo = tuple(self.M(v) for v in sp["logo"])
        if L in ("L1b", "L2", "zl"):
            self.ROOF = ROOFS if L == "L1b" else ROOFW
        if L == "green":
            self.TRIM = GREENM

    def lower_zy(self):
        """top of the red area under the yellow band (L1a)"""
        f = self.sp.get("yfrac", 0.34)
        return self.ZBAND0 - f * (self.ZBAND0 - self.Z0)

    # ------------------------------------------------------------ geometry
    def boxes(self, i, body_only=False):
        """boxes of section i in its own frame s = 0 (rear) .. L (front)"""
        L = self.sec_len(i)
        U0, U1 = self.U[i], self.U[i + 1]
        s_of = lambda u: U1 - u
        hb = self.BW / 2
        front_b = hb if i > 0 else 0.0
        rear_b = hb if i < len(self.cu) - 1 else 0.0
        bx = [Box("body%d" % i, rear_b, L - front_b, -HW, HW, self.Z0, self.ZR)]
        if body_only:
            return bx
        if front_b:
            bx.append(Box("bell_f", L - front_b, L, -HW + 0.06, HW - 0.06, self.Z0 + 0.04, self.ZR - 0.04))
        if rear_b:
            bx.append(Box("bell_r", 0.0, rear_b, -HW + 0.06, HW - 0.06, self.Z0 + 0.04, self.ZR - 0.04))
        for k, (a, b, h, hw, kind) in enumerate(self.pods):
            a2, b2 = max(a, U0 + (hb if i > 0 else 0)), min(b, U1 - (hb if i < len(self.cu) - 1 else 0))
            if b2 > a2 + 0.05:
                bx.append(Box("pod%d" % k, s_of(b2), s_of(a2), -hw, hw, self.ZR, self.ZR + h))
        if self.rack:
            a, b = self.M(self.rack[0]), self.M(self.rack[1])
            a, b = max(a, U0), min(b, U1)
            if b > a:
                zt = self.ZR + self.rack[2]
                for sg in (-1, 1):
                    t0 = sg * (HW - 0.34)
                    bx.append(Box("rail", s_of(b), s_of(a), min(t0, t0 + sg * 0.16), max(t0, t0 + sg * 0.16),
                                  zt - 0.14, zt))
                bx.append(Box("rail", s_of(b), s_of(b) + 0.22, -HW + 0.34, HW - 0.34, zt - 0.14, zt))
        if self.poles:
            pb = self.M(self.poles[0])
            if U0 <= pb < U1:
                top = self.roof_top(pb)
                bx.append(Box("polebase", s_of(pb) - 0.50, s_of(pb) + 0.50, -0.55, 0.55, top, top + 0.16))
        for k, a in enumerate(self.axles):
            if U0 <= a < U1:
                bx.append(Box("wheel%d" % k, s_of(a) - 0.62, s_of(a) + 0.62, -HW + 0.07, HW - 0.07, 0.0, 1.12,
                              faces={"left", "right"}))
        if i == 0 and self.sp["mirrors"]:
            for t0, t1 in ((-HW - 0.12, -HW + 0.02), (HW - 0.02, HW + 0.12)):
                bx.append(Box("mirror", L - 0.10, L + 0.22, t0, t1, 2.05, 2.65,
                              faces={"front", "right", "left", "top"}))
        return bx

    def roof_top(self, u):
        top = self.ZR
        for a, b, h, hw, kind in self.pods:
            if a <= u <= b:
                top = max(top, self.ZR + h)
        return top

    # ------------------------------------------------------------ textures
    def tex_for(self, i):
        U1 = self.U[i + 1]
        last = len(self.cu) - 1

        def tex(p):
            u = U1 - p.s
            self.curU1 = U1
            b = p.box
            if b.startswith("wheel"):
                return self.tex_wheel(p, u)
            if b.startswith("bell"):
                return self.tex_bellows(p, u)
            if b == "polebase":
                return sh(POLEBASE, p.face)
            if b == "rail":
                return sh(RACK, p.face)
            if b == "mirror":
                return sh(FRAME, p.face)
            if b.startswith("pod"):
                return self.tex_pod(p, u, int(b[3:]))
            f = p.face
            if f == "top":
                return self.tex_roof(p, u)
            if f in ("left", "right"):
                return self.tex_side(p, u, U1)
            if f == "front":
                return self.tex_front(p) if i == 0 else sh(BELLOWS_D, f)
            return self.tex_rear(p) if i == last else sh(BELLOWS_D, f)
        return tex

    def ln(self, p, U1, u, w=0.0):
        """pixel crosses the line u = const (u in drawn metres from the front)"""
        return p.near(0, U1 - u, w) if w else p.line(0, U1 - u)

    def tex_wheel(self, p, u):
        a = min(self.axles, key=lambda q: abs(q - u))
        d = math.hypot(u - a, p.z - self.WR)
        if abs(u - a) < 0.2 and abs(p.z - self.WR) < 0.2:
            return sh(HUB, p.face)
        if d < self.WR:
            return TIRE
        if d < 0.62 and p.z > 0.25:
            return ARCH
        return None

    def tex_bellows(self, p, u):
        f = p.face
        if f == "top":
            return BELLOWS_T
        if f in ("front", "rear"):
            return sh(BELLOWS_D, f)
        j = min(self.joints, key=lambda q: abs(q - u))
        k = (u - j) / 0.25
        if abs(k - round(k)) < 0.18 and abs(u - j) > 0.05:
            return sh(BELLOWS_D, f)
        if p.z < self.Z0 + 0.18:
            return sh(BELLOWS_D, f)
        return sh(BELLOWS, f)

    # ---------------- paint zones (livery) -----------------------------
    def upper_col(self, u):
        """roof / roof-fairing colour at u"""
        if self.liv == "L2":
            a, b = self.stripe
            if u < a:
                return RED
            if u < b:
                return YEL
            return ROOFW
        return self.ROOF

    def tex_pod(self, p, u, k):
        f = p.face
        kind = self.pods[k][4]
        if kind == "ac":
            col = (0xD8, 0xDA, 0xDC)
            if f == "top" and (abs(p.t) < 0.25):
                return (0x8A, 0x8E, 0x94)           # condenser grille
            return sh(col, f)
        if kind == "dark":
            return sh((0x50, 0x52, 0x56), f)
        col = self.upper_col(u)
        if self.face == "ns" and u < self.cap:
            return sh(BLACK, f)
        return col if f == "top" else sh(col, f)

    def tex_roof(self, p, u):
        t = p.t
        if self.face == "ns":
            if u < self.cap:
                if abs(t) > HW - 0.30:
                    return self.TRIM
                return BLACK
            return self.upper_col(u)
        if self.face == "ebn":
            if u < 0.35:
                return BLACK
        return self.upper_col(u)

    def door_at(self, u):
        for d0, d1 in self.doors:
            if d0 <= u < d1:
                return d0, d1
        return None

    def tex_side(self, p, u, U1):
        z, f = p.z, p.face
        right = f == "right"
        for a in self.axles:
            if abs(u - a) < 0.62 and z < 1.02 and math.hypot(u - a, z - self.WR) < 0.62:
                return None
        if self.face in ("ns", "ebn"):
            # front corner "wing" (red outline strip up the A-pillar) and along the cap edge
            if u < 0.26 and z >= 0.45:
                return self.TRIM
            if u < self.cap and z >= self.ZBAND1 + 0.17:
                return self.TRIM
        if right:
            d = self.door_at(u)
            if d and z < self.ZWIN1 + 0.05:
                return self.tex_door(p, u, U1, d)
        if z >= self.ZBAND0:
            if z < self.ZWIN1 + 0.05 or (right and inr(u, *self.sidedisp) and z < self.ZWIN1 + 0.30):
                c = self.glass_band(p, u, U1, right)
                return c
            return self.cant(p, u)
        return self.lower(p, u, right)

    def tex_door(self, p, u, U1, d):
        d0, d1 = d
        z = p.z
        if self.ln(p, U1, d0 + 0.02) or self.ln(p, U1, d1 - 0.02):
            return FRAME
        if self.ln(p, U1, (d0 + d1) / 2):
            return HANDRAIL if (z > 0.60 and self.face in ("ns", "ebn")) else FRAME
        if p.rng(2)[0] < self.Z0 + 0.14:
            return STEP
        if z >= self.ZWIN1 - 0.08:
            return FRAME
        kick = self.door_kick()
        if kick and z < self.Z0 + 0.42:
            return sh(kick, p.face)
        return GLASS

    def door_kick(self):
        if self.liv in ("L1b", "L2"):
            return RED
        return None

    def cant(self, p, u):
        """side between the window band and the roof edge"""
        f = p.face
        if self.face in ("ns", "ebn"):
            if u < self.cap:
                return BLACK
            if self.liv == "zl" and p.z >= self.ZWIN1 + 0.05 and p.z < self.ZBAND1:
                return sh(GREEN, f)                  # Zelena linka: green strip over the windows
            if p.z < self.ZBAND1:
                return sh(BLACK, f)
            return sh(self.upper_col(u), f)
        if p.z < self.ZBAND1:
            return sh(BLACK, f)
        return sh(self.upper_col(u), f)

    def glass_band(self, p, u, U1, right):
        z = p.z
        if right and inr(u, *self.sidedisp) and inr(z, self.ZWIN1 + 0.04, self.ZWIN1 + 0.30):
            return AMBER
        if self.liv == "L2":
            c = self.logo_px(p, u, right)
            if c:
                return c
        eng = self.sp.get("engine")
        if eng and self.M(eng[0]) <= u < self.M(eng[1]):
            return sh(BLACK, p.face)
        if not (self.ZWIN0 <= z < self.ZWIN1):
            return FRAME
        if self.liv == "zl" and u > self.drv[1] + 0.2:
            # Zelena linka: green band with tree silhouettes over the lower glass
            tree = (u * 1.7) % 1.0 < 0.30
            if p.line(2, self.ZWIN0 + 0.08) or z < self.ZWIN0 + 0.08 or (tree and p.line(2, self.ZWIN0 + 0.33)):
                return sh(GREEN, p.face)
        for i in range(len(self.cu)):
            U0s, U1s = self.U[i], self.U[i + 1]
            if U0s <= u < U1s:
                a = U0s + (self.BW / 2 if i > 0 else 0.25)
                b = U1s - (self.BW / 2 if i < len(self.cu) - 1 else 0.25)
                break
        if not (a + 0.08 <= u < b - 0.08):
            return FRAME
        if self.ln(p, U1, a + 0.10) or self.ln(p, U1, b - 0.10):
            return FRAME
        if not right and inr(u, *self.drv):
            if self.ln(p, U1, self.drv[1]):
                return FRAME
            return GLASS2
        stops = [a, b]
        if right:
            for d0, d1 in self.doors:
                if a < d0 < b: stops.append(d0)
                if a < d1 < b: stops.append(d1)
        else:
            stops.append(self.drv[1])
        stops = sorted(stops)
        for q0, q1 in zip(stops[:-1], stops[1:]):
            if q0 <= u < q1:
                n = max(1, int(round((q1 - q0) / 1.45)))
                for k in range(1, n):
                    if self.ln(p, U1, q0 + (q1 - q0) * k / n):
                        return FRAME
                if self.ln(p, U1, q0 + 0.02) or self.ln(p, U1, q1 - 0.02):
                    return FRAME
                break
        return GLASS2

    def logo_px(self, p, u, right):
        """crowned G on the window band ahead of the yellow stripe (L2): a yellow
        crown (bar + three dots) over a big white G; a second, yellow G overlaps it
        on the door side"""
        a, b = self.logo
        z = p.z
        if not (a <= u < b):
            return None
        w = b - a
        # G occupies the lower 2/3 of the band, crown the top third
        gz0, gz1 = self.ZWIN0 + 0.05, self.ZWIN0 + 0.72
        cz0, cz1 = gz1 + 0.08, gz1 + 0.34
        fx = (u - a) / w            # 0 at the front edge of the logo
        if not right:
            fx = 1 - fx             # mirror so the G reads the same way on both sides
        if inr(z, cz0, cz1):
            if z < cz0 + 0.12:
                return YEL
            if any(abs(fx - q) < 0.13 for q in (0.2, 0.5, 0.8)):
                return YEL
            return None
        if inr(z, gz0, gz1):
            fz = (z - gz0) / (gz1 - gz0)
            ring = (fx < 0.28) or (fz < 0.24) or (fz > 0.76)
            bar = fz < 0.55 and fx > 0.72
            tongue = inr(fz, 0.40, 0.58) and fx > 0.45
            if ring and not (fz > 0.62 and fx > 0.72) or bar or tongue:
                return (0xFA, 0xFA, 0xFA)
            return None
        return None

    # lower body (below the window band)
    def lower(self, p, u, right):
        L = self.liv
        f = p.face
        z = p.z
        if L == "L1a":
            return sh(self.lower_l1a(p, u, right), f)
        if L == "zl":
            return sh(self.lower_l1a(p, u, right, band=1), f)
        if L in ("L1b", "L2"):
            return sh(self.lower_ns(p, u, right), f)
        if L == "green":
            return sh(self.lower_green(p, u, right), f)
        return sh(WHITE, f)

    def lower_l1a(self, p, u, right, band=2):
        """classic white-front scheme: yellow band (2 px) over red; at the front
        corner of the left side a white panel, then swept-back yellow and red
        diagonals (bottom further forward); on the door side red between the
        front door and the band's slanted leading edge"""
        dg = self.sp["diag"]
        z = p.z
        zb = self.ZBAND0
        k = dg["k"]
        back = k * (zb - z)                                  # diagonals lean back with height
        if right:
            if u < self.doors[0][0] + 0.02:
                return WHITE
            if u < self.M(dg["xh_top"] - back):
                return RED
        else:
            xw = self.M(dg["xw_top"] - back)
            if u < xw:
                return WHITE
            if u < self.M(dg["xw_top"] + dg["wy"] - back):
                return YEL
            if u < self.M(dg["xw_top"] + dg["wy"] + dg["gap"] - back):
                return RED
        eng = self.sp.get("engine")
        if eng and self.M(eng[0]) <= u < self.M(eng[1]) and z > self.Z0 + 0.26:
            return BLACK
        # pixel centres sit 0.25 m apart in z on every side face, so a band of
        # n * 0.25 m under the window band is exactly n pixel rows in every view
        if z >= zb - 0.25 * band:
            return YEL
        return RED

    def lower_ns(self, p, u, right):
        """SOR NS black-front scheme: black ahead of the front wheel arch with a red
        skirt strip, the yellow line sweeping down in front of the arch; behind the
        arch a thin yellow line over red (L1b). L2 keeps the front part the same but
        without the yellow line; vertical yellow stripe, white behind it."""
        z = p.z
        L = self.liv
        fa = self.front_arch()
        xb = fa - 0.10                                    # black / red boundary
        zl = self.ZBAND0 - 0.25                           # yellow pinstripe (exactly 1 px row)
        zs = self.Z0 + 0.26                               # top of the red skirt strip
        U1 = self.curU1
        if L == "L2":
            a, b = self.stripe
            if inr(u, a, b):
                return YEL
            if u >= b:
                return WHITE
        thin = L in ("L1b", "zl")
        if u < xb:
            if z < zs:
                return RED
            if thin and (p.line(0, U1 - (xb - 0.07)) or (u > xb - 0.07)) and z < self.ZBAND0:
                return YEL
            return BLACK
        if thin and z >= zl:
            return YEL
        return RED

    def lower_green(self, p, u, right):
        """SOR demonstrator paint of the EBN 11: green nose and skirt, light-green
        belt line, white side panels"""
        z = p.z
        if u < self.front_arch() - 0.10 or z < self.Z0 + 0.25:
            return GREENM
        if z >= self.ZBAND0 - 0.25:
            return GREENL
        return (0xEE, 0xF2, 0xEE)

    # ---------------- front / rear faces ---------------------------------
    def tex_front(self, p):
        t, z = p.t, p.z
        f = "front"
        a = abs(t)
        face = self.face
        L = self.liv
        if face == "ns":
            if z < 0.44:
                return BLACK
            if z < 1.08:
                if a > HW - 0.40:                        # silver headlight clusters
                    if inr(z, 0.62, 0.88) and a < HW - 0.10:
                        return HEADL
                    return sh(SILVER, f)
                if z > 0.98:                               # silver band over the chin
                    return sh(SILVER, f)
                chin = RED if L == "L2" else YEL
                if L == "L2" and a < 0.20 and inr(z, 0.56, 0.90):
                    return YEL if z > 0.80 else (0xFA, 0xFA, 0xFA)   # crowned G
                return sh(chin, f)
            if a > HW - 0.10:
                return self.TRIM
            if inr(z, 1.14, 2.42) and a < HW - 0.16:
                return GLASS
            if inr(z, 2.52, 2.82) and a < 0.98:
                return AMBER
            return BLACK
        if face == "nb":
            # SOR NB (Skoda 30Tr/31Tr): white mask, red bumper, black windscreen
            if z < 0.34:
                return BLACK
            if a > HW - 0.36 and inr(z, 0.58, 0.82):     # headlights on the white/red line
                return HEADL if a < HW - 0.10 else sh(SILVER, f)
            if z < 0.70:
                return sh(RED, f)
            if z < 1.12:
                return sh(WHITE, f)
            if a > HW - 0.08:
                return sh(WHITE, f)
            if inr(z, 2.36, 2.62) and a < 1.00:
                return AMBER
            if inr(z, 1.16, 2.70) and a < HW - 0.12:
                return GLASS
            return sh(WHITE, f)
        if face == "uw1":
            # Iveco Urbanway (2013 face): white nose with a silver grille band,
            # red bumper sweeping up at the corners
            if z < 0.32:
                return BLACK
            up = 0.62 + (0.30 if a > HW - 0.45 else 0.0)
            if a > HW - 0.44 and inr(z, 0.66, 0.86):
                return HEADL if a < HW - 0.12 else sh(SILVER, f)
            if z < up:
                return sh(RED, f)
            if z < 1.14:
                if inr(z, 0.92, 1.06) and a < 0.80:
                    return sh(SILVER, f)
                return sh(WHITE, f)
            if a > HW - 0.08:
                return sh(WHITE, f)
            if inr(z, 2.40, 2.66) and a < 1.00:
                return AMBER
            if inr(z, 1.16, 2.72) and a < HW - 0.12:
                return GLASS
            return sh(WHITE, f)
        if face == "uw2":
            # Iveco Urbanway 2024 face: black windscreen surround, white band with
            # slim headlights and the IVECO letters, red bumper
            if z < 0.32:
                return BLACK
            if z < 0.66:
                return sh(RED, f)
            if z < 1.00:
                if a > HW - 0.50 and inr(z, 0.70, 0.84):
                    return HEADL if a < HW - 0.12 else sh(SILVER, f)
                if inr(z, 0.78, 0.90) and a < 0.60:
                    return sh((0x60, 0x62, 0x66), f)       # IVECO letters
                return sh(WHITE, f)
            if a > HW - 0.08 and z < 2.72:
                return sh(WHITE, f)
            if inr(z, 2.40, 2.66) and a < 1.00:
                return AMBER
            if inr(z, 1.22, 2.72) and a < HW - 0.12:
                return GLASS
            if z < 1.22:
                return BLACK
            return sh(WHITE, f)
        if face == "ebn":
            if z < 0.36:
                return BLACK
            if z < 0.80:
                if a > HW - 0.40 and inr(z, 0.50, 0.70):
                    return HEADL if a < HW - 0.10 else sh(SILVER, f)
                return sh(RED if L != "green" else GREENM, f)
            if z < 1.10:
                if L == "zl" and a < 0.95 and z < 0.80 + 0.30 * (a / 0.95) ** 2 + 0.06 and z > 0.80 + 0.30 * (a / 0.95) ** 2 - 0.06:
                    return GREEN
                if L == "green" and a < 0.95 and abs(z - (0.82 + 0.26 * (a / 0.95) ** 2)) < 0.06:
                    return (0xF4, 0xF4, 0xF4)
                return BLACK
            if a > HW - 0.10:
                return self.TRIM
            if inr(z, 1.14, 2.46) and a < HW - 0.16:
                return GLASS
            if inr(z, 2.54, 2.82) and a < 0.98:
                return AMBER
            return BLACK
        return sh(WHITE, f)

    def tex_rear(self, p):
        t, z = p.t, p.z
        f = "rear"
        a = abs(t)
        st = self.rearstyle
        L = self.liv
        if st == "ns":
            if a > HW - 0.26 and inr(z, 0.55, 1.35):
                return TAILL
            if z < 0.45:
                return BLACK
            if z >= self.ZBAND0 + 0.20:
                if inr(z, 2.42, 2.62) and inr(t, 0.30, 0.80):
                    return AMBER
                if inr(z, 1.75, 2.62) and a < HW - 0.30:
                    return GLASS
                if a > HW - 0.22 and z > 2.70:
                    return TAILL
                return BLACK
            if L == "L2":
                return sh(WHITE, f)
            if L == "green":
                return sh(GREENM, f)
            # yellow engine lid between the light clusters, red bumper below
            if z < 0.62:
                return sh(RED, f)
            if a > HW - 0.30:
                return sh(SILVER, f)
            return sh(YEL, f)
        if st in ("nb", "uw"):
            if z < 0.30:
                return BLACK
            if a > HW - 0.26 and inr(z, 0.70, 1.30):
                return TAILL
            if z < 0.64:
                return sh(RED, f)
            ztop = 1.36 if st == "nb" else 1.30
            if z < ztop:
                return sh(YEL, f)
            if st == "nb" and z < 1.74:
                # white louvred panel
                if a < HW - 0.25 and int((z - 1.36) / 0.09) % 2 == 1:
                    return sh((0xC8, 0xCA, 0xCC), f)
                return sh(WHITE, f)
            if inr(z, 2.36, 2.58) and inr(t, 0.25, 0.80):
                return AMBER
            zg0 = 1.78 if st == "nb" else 1.55
            if inr(z, zg0, 2.62) and a < HW - 0.22:
                return GLASS
            return sh(WHITE, f)
        return sh(WHITE, f)


# ------------------------------------------------------------------ poles
WIRES = {
    "w": ("c", 0.5, [{28, 29}, {32}]),
    "e": ("c", 0.5, [{50, 51}, {54}]),
    "n": ("c", -0.5, [{114}, {117, 118}]),
    "s": ("c", -0.5, [{92}, {95, 96}]),
    "ne": ("y", None, [{77}, {79}]),
    "sw": ("y", None, [{66}, {68}]),
    "se": ("x", None, [{51}, {54}]),
    "nw": ("x", None, [{73}, {76}]),
}
POLE_LEN = 6.3


def on_wire(view, x, y, k):
    kind, slope, sets = WIRES[view]
    if kind == "c":
        return int(round(y - slope * x)) in sets[k]
    if kind == "y":
        return y in sets[k]
    return x in sets[k]


def bresenham(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
    return pts


def pole_tips(view, L, origin, bs, bz, bt):
    best = {}
    bases = []
    for pi, tb in enumerate((-bt, bt)):
        bases.append(project(view, L, origin, bs, tb, bz))
        for zt in np.arange(4.6, 8.6, 0.05):
            for tt in np.arange(-1.6, 1.61, 0.05):
                run2 = POLE_LEN ** 2 - (zt - bz) ** 2 - (tt - tb) ** 2
                if run2 <= 0:
                    continue
                st = bs - math.sqrt(run2)
                tip = project(view, L, origin, st, tt, zt)
                x, y = int(math.floor(tip[0])), int(math.floor(tip[1]))
                for k in (0, 1):
                    if on_wire(view, x, y, k):
                        cost = 0.3 * abs(zt - 6.0) + 0.8 * abs(tt - tb * 1.7)
                        key = (pi, k)
                        if key not in best or cost < best[key][0]:
                            best[key] = (cost, x, y)
    opts = []
    for k0 in (0, 1):
        a, b = best.get((0, k0)), best.get((1, 1 - k0))
        if a and b:
            opts.append((a[0] + b[0], a, b))
    if not opts:
        return [(bases[0], None), (bases[1], None)]
    _, a, b = min(opts)
    return [(bases[0], (0, 0, a[1], a[2], 0)), (bases[1], (0, 0, b[1], b[2], 0))]


def draw_poles(img, view, L, origin, bs, bz, bt, tipcol):
    for base, tip in pole_tips(view, L, origin, bs, bz, bt):
        if tip is None:
            print("  no wire for pole in", view)
            continue
        bx, by = int(math.floor(base[0])), int(math.floor(base[1]))
        for x, y in bresenham(bx, by, tip[2], tip[3]):
            if 0 <= x < 128 and 0 <= y < 128:
                img[y, x] = POLE
        img[tip[3], tip[2]] = tipcol


# ------------------------------------------------------------------ placement
# Tile-centre origin per view: a bare 12 m x 2.62 m body box (z 0.32-3.0 m)
# rendered at (64, 96) and shifted by whole pixels so its footprint (x centre and
# lower-edge intercept along the road slope) matches the median of native
# pak128.cs 12 m buses and trolleybuses (normalize.py of the MHD import work) -
# the same origins as the Prague/Brno SOR NS 12 / NS 18 renders.
ORIGINS = {"w": (58.0, 85.0), "nw": (74.0, 89.0), "n": (84.0, 96.0), "ne": (66.0, 106.0),
           "e": (46.0, 96.0), "se": (50.0, 90.0), "s": (66.0, 86.0), "sw": (65.0, 92.0)}


def origin_for(d):
    return ORIGINS[d]


def build(sp, livery, verbose=False):
    m = Veh(sp, livery)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        tiles = []
        for d in DIRS:
            o = np.array(origin_for(d))
            if not m.single:
                o = o + (4 - l / 2.0) * PER_CU[d]
            img, zb = render(d, m.boxes(i), m.tex_for(i), L, o)
            if m.poles:
                pb = m.M(m.poles[0])
                if m.U[i] <= pb < m.U[i + 1]:
                    s = m.U[i + 1] - pb
                    draw_poles(img, d, L, o, s, m.roof_top(pb) + 0.16, m.poles[1], TIP)
            tiles.append(img)
        rows.append(tiles)
        if verbose:
            print("section", i, "len", l, "->", round(L, 2), "m drawn")
    return rows


# ------------------------------------------------------------------ the set
MODELS = {
    # SOR NS 12 diesel (111-116)
    "ns12": mk(NS12, pods=[(1.80, 3.60, 0.22, 0.80, "ac")]),
    # SOR NS 12 electric (404-423): full-length roof fairing over the batteries
    "ns12e": mk(NS12, pods=[(1.70, 11.75, 0.26, 1.10, "fair")]),
    # SOR NS 18 diesel (237-240)
    "ns18": mk(NS18, pods=[(1.80, 3.60, 0.22, 0.80, "ac"), (12.2, 13.8, 0.20, 0.75, "ac")]),
    # Skoda 32Tr SOR (NS 12 body, traction battery), 2026 design
    "32tr": mk(NS12, pods=[(1.80, 6.60, 0.24, 0.95, "fair"), (8.70, 9.50, 0.14, 0.60, "fair")],
               poles=(7.10, 0.30), stripe=(7.20, 7.95), logo=(6.25, 7.10)),
    # Skoda 33Tr SOR (NS 18 body, traction battery), 2026 design; poles on the
    # front section above the middle door
    "33tr": mk(NS18, pods=[(1.80, 5.40, 0.24, 0.95, "fair"), (12.0, 14.5, 0.20, 0.85, "fair")],
               poles=(6.20, 0.30), stripe=(7.20, 7.95), logo=(6.25, 7.10)),
    # Skoda 30Tr SOR (SOR TNB 12 body): equipment fairing over the front 2/3 of
    # the roof, pole base near the rear axle, silver retriever rack behind it
    "30tr": mk(NB12, pods=[(1.60, 7.80, 0.30, 1.05, "fair")], poles=(8.40, 0.30),
               rack=(8.10, 11.70, 0.34)),
    # 30Tr battery cars (29-38): a battery box on the rear roof
    "30trb": mk(NB12, pods=[(1.60, 7.80, 0.30, 1.05, "fair"), (9.60, 11.40, 0.18, 0.55, "dark")],
                poles=(8.40, 0.30), rack=(8.10, 11.70, 0.34)),
    # 30TrDG (17, 18): diesel generator set in a second roof box at the rear
    "30trdg": mk(NB12, pods=[(1.60, 7.80, 0.30, 1.05, "fair"), (9.40, 11.60, 0.26, 0.90, "fair")],
                 poles=(8.40, 0.30), rack=(8.10, 9.30, 0.34)),
    # Skoda 31Tr SOR (SOR TNB 18 body): AC at the front, equipment fairing ahead
    # of the joint, poles on the rear section with the retriever rack behind them
    "31tr": mk(NB18, pods=[(0.45, 1.75, 0.22, 0.80, "ac"), (8.60, 11.80, 0.30, 1.05, "fair"),
                           (12.90, 14.20, 0.30, 1.05, "fair")],
               poles=(14.00, 0.30), rack=(13.80, 17.60, 0.34)),
    "uw12": mk(UW12, pods=[(2.20, 4.60, 0.24, 0.85, "ac")]),
    "uw12h": mk(UW12, face="uw2", pods=[(1.40, 3.80, 0.26, 0.95, "fair"), (6.80, 8.60, 0.24, 0.85, "ac")]),
    "uw18h": mk(UW18, pods=[(1.40, 3.80, 0.26, 0.95, "fair"), (6.40, 8.20, 0.24, 0.85, "ac"),
                            (11.80, 13.40, 0.24, 0.85, "ac")]),
    "cit18": mk(UW18, face="uw1", pods=[(2.00, 4.20, 0.24, 0.85, "ac"), (11.80, 13.40, 0.24, 0.85, "ac")]),
    "ebn95": mk(EBN95, pods=[(1.00, 3.60, 0.28, 0.95, "fair"), (5.40, 8.60, 0.28, 0.95, "fair")]),
    "ebn11": mk(EBN11, pods=[(1.20, 3.60, 0.30, 0.95, "fair"), (4.20, 6.60, 0.30, 0.95, "fair"),
                             (7.20, 9.60, 0.30, 0.95, "fair")]),
}

# ------------------------------------------------------------------ output
T = (231, 255, 255)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simutrans special colours (image_t::rgbtab); only the lit-window glass and the
# head/tail lights may appear in these sheets.
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
ALLOWED = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


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
    """all rows side by side, background greyed, scaled z times"""
    a = sheet.copy()
    a[np.all(a == T, axis=2)] = (96, 104, 96)
    Image.fromarray(a).resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST).save(path)


L1 = "dpmhkcervenozlutobila"
L2 = "dpmhkcervenozlutobilasvisla"

# family dir -> {livery colour: [(model, livery key), ...] in sprite-row order}
FAMILIES = {
    "vehicle-trolleybus/dpmhk/30tr": {L1: [("30tr", "L1a"), ("30trb", "L1a"), ("30trdg", "L1a")]},
    "vehicle-trolleybus/dpmhk/31tr": {L1: [("31tr", "L1a")]},
    "vehicle-trolleybus/dpmhk/32tr": {L2: [("32tr", "L2")]},
    "vehicle-trolleybus/dpmhk/33tr": {L2: [("33tr", "L2")]},
    "vehicle-bus/dpmhk/sor_ns_12": {L1: [("ns12", "L1b")]},
    "vehicle-bus/dpmhk/sor_ns_12_electric": {L1: [("ns12e", "L1b")]},
    "vehicle-bus/dpmhk/sor_ns_18": {L1: [("ns18", "L1b")]},
    "vehicle-bus/dpmhk/urbanway_12m": {L1: [("uw12", "L1a"), ("uw12h", "L1a")]},
    "vehicle-bus/dpmhk/urbanway_18m_hybrid": {L1: [("uw18h", "L1a")]},
    "vehicle-bus/dpmhk/citelis_18m": {L1: [("cit18", "L1a")]},
    "vehicle-bus/dpmhk/sor_ebn_9_5": {"dpmhkzelenalinka": [("ebn95", "zl")]},
    "vehicle-bus/dpmhk/sor_ebn_11": {"sorzelenametaliza": [("ebn11", "green")]},
}


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
        for color, parts in livs.items():
            rows = []
            for model, liv in parts:
                rows += build(MODELS[model], liv)       # an articulated model adds a row per section
            sheet = save_rows(rows, os.path.join(sd, color + ".png"))
            if pv:
                preview(sheet, os.path.join(pv, f"{name}-{color}.png"))
            print(f"{fam}/sprites/{color}.png  rows={len(rows)}")


if __name__ == "__main__":
    main()
