#!/usr/bin/env python3
"""Newag Impuls regional EMUs that reach Czech stations, drawn from scratch with
the pak128 box raycaster (render.py + railkit.py).

    python tools/railrender/impuls.py                  # every sheet
    python tools/railrender/impuls.py 45we 31webc      # only these families
    python tools/railrender/impuls.py --preview DIR    # also 4x previews

  45we   Koleje Dolnośląskie 45WE (Impuls 1, 5 sections), livery bilozluta
  31we   Koleje Dolnośląskie 31WE (Impuls 1, 4 sections), livery bilozluta
  31webc Koleje Śląskie 31WEbc (Impuls 2, 4 sections), livery bilomodra

The model is parametrised by a Spec (section count and lengths, joint and door
positions, windows, roof equipment, pantographs), a Nose (cab shape variant:
Impuls 1 or Impuls 2) and a Livery (a painter).  elf2.py reuses Unit with the
Pesa Elf 2 cab.

Coordinates.  The whole unit is modelled on one u axis (carunits behind the
A-end nose); every car row is rendered with its front on the Simutrans anchor,
so the joints meet in all views.  Positions along the unit are given in "unit
metres" x (0 = A-end nose, xend = E-end nose), measured on the vagonweb side
drawings (10 px = 1 m) of the classes and corrected by photos; x maps linearly
to u within each car (the car lengths are integer carunits, so the end cars
are 2.15 m/cu and the middle cars 2.0 m/cu, like the FLIRT of flirt.py).
z = model px above the rail (1 px = 0.375 m).

Sides.  The units are 180-degree symmetric; the painters describe the +v side
(right-hand side with the A end leading) and the -v side is its rotation:
the -v side at x looks like the +v side at xend - x.  That also keeps
lettering reading left to right on both sides.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
PX = 0.375


def zm(h):
    """metres above the rail -> model px"""
    return h / PX


def zmt(z):
    """model px -> metres"""
    return z * PX


class Spec:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# ---------------------------------------------------------------- common colours
WS = (0x2A, 0x34, 0x3D)          # windscreen / cab side glass (plain, never lit)
WS_HI = (0x4F, 0x62, 0x72)
DISP = (0x16, 0x17, 0x19)
AMBER = (0xF0, 0xA0, 0x18)
LAMP_OFF = (0x8A, 0x90, 0x96)    # unlit head lamp glass (rear end)
BOGIE = Paint(0x262729)
BOGIE_HI = Paint(0x3E4144)
UNDER = Paint(0x2C2E30)
COUPLER = Paint(0x3A3C3F)


def bars(r, z, rows):
    for (a, b, z0, z1) in rows:
        if a <= r <= b and z0 <= z <= z1:
            return True
    return False


# ---------------------------------------------------------------- cab shapes
class Nose:
    """Cab shape of one unit end.  front(z): metres of the front surface behind
    the end at height z (model px); corner(z) = (Rm, Rv, hw): plan-view corner
    rounding (Rm metres along the unit, Rv carunits inwards, hw = half width)."""
    CAB_M = 3.6
    PROF = []

    def __init__(self, W, ZS, ZR, ZCAP):
        self.W, self.ZS, self.ZR, self.ZCAP = W, ZS, ZR, ZCAP

    def front(self, z):
        zs = [p[0] for p in self.PROF]
        ms = [p[1] for p in self.PROF]
        return float(np.interp(z, zs, ms))

    def layers(self):
        L = [(0.8, 1.5), (1.5, 2.4), (2.4, 3.6), (3.6, 4.4)]
        z = 4.4
        while z < self.ZR - 1e-6:
            z1 = min(self.ZR, z + 0.4)
            L.append((z, z1))
            z = z1
        return L


class NoseImpuls1(Nose):
    """Impuls 1 (31WE/45WE): protruding lower front with the coupler mouth,
    lamp band raked back, windscreen raked ~40 deg, white cap
    (vagonweb profile 45WE-a + photos 45WE-028A / 31WE-022A)."""
    CAB_M = 3.7
    PROF = [(0.8, 0.45), (1.5, 0.37), (3.6, 0.35), (5.2, 0.70), (7.0, 1.27),
            (8.5, 1.75), (9.5, 2.13), (10.1, 2.43), (10.53, 2.80)]

    def corner(self, z):
        W = self.W
        if z < 1.5:
            return 0.55, 0.30, W - 0.06
        if z < 3.6:
            return 1.10, 0.40, W
        if z < 5.2:
            return 0.95, 0.34, W
        if z < self.ZS:
            return 0.80, 0.30, W
        return 0.90, 0.30, W - 0.12


class NoseImpuls2(Nose):
    """Impuls 2 (31WEbc): bulbous lower front, near-upright windscreen that
    rolls into the roof (vagonweb 31WEbc-a profile + photo 31WEbc-001)."""
    CAB_M = 3.5
    PROF = [(0.8, 0.67), (1.5, 0.57), (3.6, 0.55), (5.0, 0.67), (6.7, 1.03),
            (8.0, 1.35), (9.1, 1.80), (9.9, 2.30), (10.53, 3.10)]

    def corner(self, z):
        W = self.W
        if z < 1.5:
            return 0.60, 0.32, W - 0.06
        if z < 3.6:
            return 1.30, 0.46, W
        if z < 5.2:
            return 1.10, 0.40, W
        if z < self.ZS:
            return 0.95, 0.34, W
        return 1.00, 0.34, W - 0.12


# ---------------------------------------------------------------- unit model
class Unit:
    HALFJ = 0.14       # body end gap either side of a joint (cu)

    def __init__(self, S, liv, nose):
        self.S = S
        self.L = liv
        self.N = nose
        n = len(S.lengths)
        self.n = n
        self.LEN = list(S.lengths)
        self.U0 = [sum(S.lengths[:k]) for k in range(n)] + [sum(S.lengths)]
        self.UEND = float(self.U0[-1])
        self.X0 = [0.0] + list(S.joints) + [S.xend]
        self.XEND = S.xend
        self.parts = []
        self.lines = []
        self.build()

    # --- coordinates
    def car_of_u(self, u):
        for k in range(self.n - 1, -1, -1):
            if u >= self.U0[k] - 1e-6:
                return k
        return 0

    def car_of_x(self, x):
        for k in range(self.n - 1, -1, -1):
            if x >= self.X0[k] - 1e-6:
                return k
        return 0

    def xm(self, u):
        k = self.car_of_u(u)
        return self.X0[k] + (u - self.U0[k]) * (self.X0[k + 1] - self.X0[k]) / self.LEN[k]

    def um(self, x, k=None):
        if k is None:
            k = self.car_of_x(x)
        return self.U0[k] + (x - self.X0[k]) * self.LEN[k] / (self.X0[k + 1] - self.X0[k])

    def mpc(self, k):
        """metres per carunit in car k"""
        return (self.X0[k + 1] - self.X0[k]) / self.LEN[k]

    # --- materials
    def mat_for(self, k):
        S, N, L = self.S, self.N, self.L
        end = "A" if k == 0 else ("E" if k == self.n - 1 else None)
        ME = self.mpc(k)
        cab_u = N.CAB_M / ME

        def mat(f, u, v, z, d):
            x = self.xm(u)
            if end is not None:
                ul = u if end == "A" else self.UEND - u
                vl = v if end == "A" else -v
                fl = f
                if end == "E" and f in ("-u", "+u"):
                    fl = "-u" if f == "+u" else "+u"
                if ul < cab_u + 0.25:
                    uf = N.front(z) / ME
                    Rm = N.corner(z)[0] / ME
                    if f == "+z":
                        return L.nose(self, end, f, ul * ME, vl, z)
                    if fl == "-u":
                        return L.nose(self, end, fl, ul * ME, vl, z)
                    if f in ("+v", "-v") and ul - uf < Rm + 0.08:
                        return L.nose(self, end, f, ul * ME, vl, z)
            if f == "+z":
                return L.roof(self, x, v)
            if f in ("+v", "-v"):
                xp = x if f == "+v" else self.XEND - x
                return L.side(self, xp, z)
            return L.endface(self, z)
        return mat

    def box(self, x0, x1, v0, v1, z0, z1, mat, own, k=None):
        if k is None:
            k = self.car_of_x((x0 + x1) / 2)
        u0, u1 = self.um(x0, k), self.um(x1, k)
        self.parts.append(Part(min(u0, u1), max(u0, u1), v0, v1, z0, z1, mat, own))

    # --- geometry
    def build(self):
        S, N = self.S, self.N
        W = S.W
        n = self.n
        HJ = self.HALFJ
        for k in range(n):
            own = f"c{k}"
            mat = self.mat_for(k)
            ME = self.mpc(k)
            xa, xb = self.X0[k], self.X0[k + 1]
            # body extent (unit metres)
            b0 = xa + (N.CAB_M if k == 0 else HJ * ME)
            b1 = xb - (N.CAB_M if k == n - 1 else HJ * ME)
            # bottom line: raised over bogies
            cuts = []
            for bc in S.bogies:
                if xa - 2 <= bc <= xb + 2:
                    cuts.append((bc - S.bogie_cut, bc + S.bogie_cut))
            for J in S.joints:
                if xa - 2 <= J <= xb + 2:
                    cuts.append((J - S.bogie_cut, J + S.bogie_cut))
            edges = sorted(set([b0, b1] + [min(max(e, b0), b1) for c in cuts for e in c]))
            for i in range(len(edges) - 1):
                a, b = edges[i], edges[i + 1]
                if b - a < 0.02:
                    continue
                mid = (a + b) / 2
                zb = S.ZBOG if any(c0 <= mid <= c1 for (c0, c1) in cuts) else S.ZBOT
                self.box(a, b, -W, W, zb, S.ZS, mat, own, k)
            # roof cap (two steps)
            e = 0.04 * ME
            self.box(b0 - (0.1 if k == 0 else -e), b1 + (0.1 if k == n - 1 else -e),
                     -(W - S.CAP1), W - S.CAP1, S.ZS, S.ZCAP, mat, own, k)
            self.box(b0 - (0.1 if k == 0 else -e), b1 + (0.1 if k == n - 1 else -e),
                     -(W - S.CAP2), W - S.CAP2, S.ZCAP, S.ZR, mat, own, k)
            # underframe equipment between the bogies
            segs = [(b0, b1)]
            for (c0, c1) in cuts:
                nsegs = []
                for (a, b) in segs:
                    if c1 <= a or c0 >= b:
                        nsegs.append((a, b))
                        continue
                    if c0 > a:
                        nsegs.append((a, c0))
                    if c1 < b:
                        nsegs.append((c1, b))
                segs = nsegs
            for (a, b) in segs:
                if b - a > 1.0:
                    self.box(a + 0.3, b - 0.3, -W + 0.28, W - 0.28, 1.0, S.ZBOT + 0.05,
                             lambda *a_: UNDER, own, k)
        # cab noses
        self.build_nose(0, "A")
        self.build_nose(n - 1, "E")
        # joints: bellows + Jakobs bogie, owned by the car in front
        for j, J in enumerate(S.joints):
            own = f"c{j}"
            u = float(self.U0[j + 1])
            L = self.L
            self.parts.append(Part(u - HJ - 0.02, u + HJ + 0.02, -W + 0.10, W - 0.10,
                                   S.ZBOG + 0.3, S.ZR - 0.15,
                                   (lambda f, uu, v, z, d: L.bellows(f, uu, z)), own))
            self.parts += R.bogie(u, own, W=W, half=0.72, z1=2.2, col=BOGIE, frame=BOGIE_HI)
        # powered bogies under the cab cars
        for bc in S.bogies:
            k = self.car_of_x(bc)
            self.parts += R.bogie(self.um(bc, k), f"c{k}", W=W, half=0.74, z1=2.35,
                                  col=BOGIE, frame=BOGIE_HI)
        self.build_roof()

    def build_nose(self, k, end):
        S, N = self.S, self.N
        own = f"c{k}"
        mat = self.mat_for(k)
        ME = self.mpc(k)

        def add(m0, m1, v0, v1, z0, z1, mt=mat):
            # m = metres behind this end's nose
            if end == "A":
                x0, x1 = m0, m1
            else:
                x0, x1 = self.XEND - m1, self.XEND - m0
            self.box(x0, x1, v0, v1, z0, z1, mt, own, k)

        for (z0, z1) in N.layers():
            zc = (z0 + z1) / 2
            mf = N.front(zc)
            Rm, Rv, hw = N.corner(zc)
            if mf >= N.CAB_M:
                continue
            nstr = 6
            for i in range(nstr):
                a = mf + Rm * i / nstr
                b = mf + Rm * (i + 1) / nstr
                if a >= N.CAB_M:
                    break
                t = 1.0 - ((a + b) / 2 - mf) / Rm
                h = hw - Rv * (1.0 - np.sqrt(max(0.0, 1.0 - t * t)))
                add(a, min(b, N.CAB_M + 0.05), -h, h, z0, z1)
            if mf + Rm < N.CAB_M:
                add(mf + Rm, N.CAB_M + 0.05, -hw, hw, z0, z1)
        # coupler (the unit ends at the coupler face)
        add(0.0, N.front(2.6) + 0.1, -0.16, 0.16, 2.2, 3.1, lambda *a: COUPLER)
        # top lamp / camera pod on the cab roof (Impuls: small dark pod)
        if getattr(S, "roof_pod", True):
            m0 = N.front(N.ZR - 0.2) + 0.15
            add(m0, m0 + 0.55, -0.22, 0.22, N.ZR - 0.3, N.ZR + 0.35,
                lambda f, u, v, z, d, e=end: self.L.pod(e, f, z))

    def build_roof(self):
        S = self.S
        for (x0, x1, h, hw, kind) in S.roofboxes:
            L = self.L
            k = self.car_of_x((x0 + x1) / 2)
            self.box(x0, x1, -hw, hw, S.ZR - 0.05, S.ZR + zm(h),
                     (lambda f, u, v, z, d, kd=kind: L.roofbox(kd, f)), f"c{k}", k)
        zb = S.ZR + 0.35
        for (xb, raised, fold) in S.pantos:
            k = self.car_of_x(xb)
            own = f"c{k}"
            ub = self.um(xb, k)
            L = self.L
            self.box(xb - 0.9, xb + 0.9, -0.5, 0.5, S.ZR - 0.05, S.ZR + 0.35,
                     lambda f, u, v, z, d: L.roofbox("panto", f), own, k)
            if raised:
                self.lines += R.pantograph(ub, zb, own, fold=fold, reach=0.95, height=5.4,
                                           col=(0x70, 0x74, 0x78), head=(0x2A, 0x2A, 0x2C),
                                           half_head=0.62, thick=False)
            else:
                pc = (0x70, 0x74, 0x78)
                ue = ub + fold * 0.85
                self.lines += [((ub, 0.0, zb + 0.1), (ue, 0.0, zb + 0.45), pc, own, False),
                               ((ue, -0.5, zb + 0.45), (ue, 0.5, zb + 0.45), (0x2A, 0x2A, 0x2C), own, False)]

    # --- rendering
    def rows(self):
        out = []
        for k in range(self.n):
            lo, hi = self.U0[k] - 3.0, self.U0[k + 1] + 3.0
            parts = [p for p in self.parts if p.b[1] >= lo and p.b[0] <= hi]
            lines = [l for l in self.lines if lo <= l[0][0] <= hi]
            out.append([R.vehicle_tile(parts, lines, d, float(self.U0[k]), {f"c{k}"}) for d in DIRS])
        return out


# ---------------------------------------------------------------- painters
class Livery:
    """Base painter: subclasses set the colours and override the zones."""
    ROOF = Paint(0x76797C, top=0x84878A)
    ROOFBOX = Paint(0x55585C, top=0x63676B)
    ROOFBOX_HV = Paint(0x4A4C50, top=0x585B60)
    BELLOWS = Paint(0xA6AAAE, top=0xB0B4B8)
    BELLOWS_DK = Paint(0x868A8E, top=0x9A9EA2)

    def roofbox(self, kind, f):
        if kind == "hv":
            return self.ROOFBOX_HV
        return self.ROOFBOX

    def bellows(self, f, u, z):
        if f in ("+v", "-v") and int(u * 20) % 2 == 1:
            return self.BELLOWS_DK
        return self.BELLOWS

    def pod(self, end, f, z):
        return Paint(0x1E1F21)

    def endface(self, U, z):
        return self.BODY

    def roof(self, U, x, v):
        return self.ROOF

    # generic window / door helpers ------------------------------------
    def window(self, U, xp, z):
        S = U.S
        for (a, b) in S.windows:
            if a <= xp <= b and S.ZWF0 <= z <= S.ZWF1:
                if S.ZWG0 <= z <= S.ZWG1 and a + S.WF <= xp <= b - S.WF:
                    return R.GLASS_HI if z > S.ZWG1 - 0.45 else R.GLASS
                return self.WFRAME
        return None

    def door_at(self, U, xp, z):
        S = U.S
        for (a, b) in S.doors:
            if a - S.DF <= xp <= b + S.DF and S.ZD0 <= z <= S.ZD1 + S.DFT:
                return (a, b)
        return None


# ---- Koleje Dolnośląskie (Impuls 1)
class KDLivery(Livery):
    """White body, bright yellow lower body under a flowing black wave line,
    black-framed windows, black double doors, white nose with a black glazing
    mask, KD logo + red swoosh, grey roof.  Photos: 45WE-019A Lichkov 2018,
    45WE-021A, 45WE-028A (2017), 45WE-020E Wroclaw 2024, 31WE-022A Jelenia
    Gora 2025, 31WE-022D Lichkov, 31WE-023 Wroclaw 2020."""
    BODY = Paint(0xF0F0EE, top=0xF4F4F2)
    YELLOW = Paint(0xF5D00A)
    LINE = Paint(0x1E1E20)
    BLACK = Paint(0x1C1C1E)
    WFRAME = Paint(0x202022)
    DOOR = Paint(0x232426)
    RED = Paint(0xD2232B)
    CAP = Paint(0xECECEA, top=0xF2F2F0)
    CREST = Paint(0xF2C81A)

    def __init__(self, wave):
        self.wave_pts = wave          # [(x, h_m)] of the +v side yellow top

    def wave(self, xp):
        xs = [p[0] for p in self.wave_pts]
        hs = [p[1] for p in self.wave_pts]
        return float(np.interp(xp, xs, hs))

    # --- side
    def side(self, U, xp, z):
        S = U.S
        xe = min(xp, U.XEND - xp)
        if z > S.ZS - 0.02:
            return self.CAP if xe < S.cab_m else self.ROOF
        # cab zone
        if xe < S.cab_m:
            c = self.cab_side(U, xp, xe, z)
            if c is not None:
                return c
        dr = self.door_at(U, xp, z)
        if dr is not None:
            return self.door(U, xp, z, dr)
        w = self.window(U, xp, z)
        if w is not None:
            return w
        lg = self.logo(U, xp, xe, z)
        if lg is not None:
            return lg
        return self.base(xp, z)

    def base(self, xp, z):
        h = zmt(z)
        wv = self.wave(xp)
        if h < wv:
            return self.YELLOW
        if h < wv + 0.40:
            return self.LINE
        return self.BODY

    def door(self, U, xp, z, dr):
        S = U.S
        a, b = dr
        if z > S.ZD1:
            return self.base(xp, z)
        c = (a + b) / 2
        lw = (b - a) / 2
        # leaf windows (lit glass), one per leaf
        for (l0, l1) in ((a, c), (c, b)):
            if l0 + 0.20 <= xp <= l1 - 0.20 and S.ZDW0 <= z <= S.ZDW1:
                return R.GLASS_HI if z > S.ZDW1 - 0.4 else R.GLASS
        # white "2" class sign on the screen-left leaf (+v: larger x)
        if c + 0.25 <= xp <= b - 0.22 and zm(1.05) <= z <= zm(1.50):
            return self.BODY
        return self.DOOR

    def cab_side(self, U, xp, xe, z):
        S = U.S
        h = zmt(z)
        # black eyebrow: the glazing mask continues along the top of the cab side
        if z > S.ZS - 0.85 and xe < S.cab_m - 0.25:
            return self.BLACK
        # cab side window (plain glass), front edge raked like the windscreen
        fe = 2.05 + (h - 2.0) * 0.45
        if 2.0 <= h <= 3.2 and fe <= xe <= 3.35:
            if xe < fe + 0.1 or xe > 3.25 or h > 3.1 or h < 2.1:
                return self.BLACK
            return WS_HI if h > 2.85 else WS
        return None

    def logo(self, U, xp, xe, z):
        h = zmt(z)
        near_a = xp < U.XEND / 2
        if near_a:
            # KD + red swoosh behind the A cab (+v): reads K D swoosh towards the cab
            a, b = 3.75, 6.25
            if not (a <= xp <= b and 1.95 <= h <= 2.95):
                return None
            r = b - xp
            if bars(r, h, [(0.0, 0.2, 2.0, 2.9), (0.2, 0.62, 2.35, 2.55),
                           (0.42, 0.62, 2.55, 2.9), (0.42, 0.62, 2.0, 2.35),
                           (0.8, 1.0, 2.0, 2.9), (1.0, 1.25, 2.0, 2.18), (1.0, 1.25, 2.72, 2.9),
                           (1.2, 1.42, 2.1, 2.8)]):
                return self.BLACK
            # swoosh: arc bulging forward, from top-left to bottom-left
            if 1.6 <= r <= 2.45:
                t = (h - 2.0) / 0.9
                rc = 1.75 + 0.6 * np.sin(np.pi * min(max(t, 0), 1))
                if abs(r - rc) < 0.2 and 2.05 <= h <= 2.9:
                    return self.RED
            return None
        # E end of +v (= A end of -v): crest + DOLNY SLASK (2 lines)
        a, b = U.XEND - 6.3, U.XEND - 3.75
        if not (a <= xp <= b and 1.95 <= h <= 2.95):
            return None
        r = b - xp        # 0 at the cab end
        if r <= 0.55:
            if 2.0 <= h <= 2.85:
                if 0.18 <= r <= 0.38 and 2.25 <= h <= 2.65:
                    return self.BLACK       # eagle
                return self.CREST
            return None
        rr = r - 0.7
        if 0.0 <= rr <= 1.8:
            letter = int(rr / 0.3)
            if rr - letter * 0.3 < 0.22:
                if 2.5 <= h <= 2.9 and letter < 5:
                    return self.BLACK
                if 2.0 <= h <= 2.4 and letter < 5:
                    return self.BLACK
        return None

    # --- nose
    def nose(self, U, end, f, m, v, z):
        """m = metres behind this end's nose, v = lateral (local, cu)."""
        S, N = U.S, U.N
        av = abs(v)
        mf = N.front(z)
        dm = m - mf
        W = S.W
        # cab roof: white cap
        if f == "+z" and z >= S.ZS - 0.1:
            return self.CAP
        if z < 1.5:
            return self.BLACK if z < 1.0 else self.BODY
        if z < 3.6:
            # coupler mouth with the red coupler cover
            if av < 0.60 and dm < 0.45:
                if av < 0.26 and 1.9 <= z <= 3.2:
                    return self.RED
                return self.BLACK
            return self.BODY
        if z < 5.2:
            # lamp clusters at the outer corners
            if 0.56 <= av <= 0.88 and 4.0 <= z <= 5.1:
                if 0.62 <= av <= 0.80 and 4.2 <= z <= 4.85:
                    if end == "A":
                        return R.HEAD
                    return R.TAIL if av > 0.68 else LAMP_OFF
                return self.BLACK
            # front KD logo (reads K D swoosh as seen from ahead: K on +v)
            if 4.15 <= z <= 4.85 and av < 0.42 and dm < 0.4:
                if 0.16 <= v <= 0.34 or -0.08 <= v <= 0.08:
                    return self.BLACK
                if -0.40 <= v <= -0.20:
                    return self.RED
            return self.BODY
        if z < S.ZS:
            lim = 0.80 - 0.10 * (z - 5.2) / (S.ZS - 5.2)
            if av < lim:
                if z > S.ZS - 0.95:
                    if abs(z - (S.ZS - 0.5)) < 0.2 and av < lim - 0.25:
                        return AMBER
                    return DISP
                if av > lim - 0.09 or z < 5.5:
                    return self.BLACK
                return WS_HI if (z > 8.0 or (v > 0.3 and z > 6.8)) else WS
            if z > S.ZS - 0.85:
                return self.BLACK           # eyebrow round the corners
            return self.BODY
        return self.CAP

    def pod(self, end, f, z):
        if f == "-u" and end == "A" and z < 10.9:
            return R.HEAD
        return self.BLACK

    def roof(self, U, x, v):
        xe = min(x, U.XEND - x)
        if xe < U.S.cab_m:
            return self.CAP
        return self.ROOF


# ---- Koleje Śląskie (Impuls 2)
KS_BLUE = 0x1C9EE0


class KSLivery(Livery):
    """KS white / azure: azure nose, roof and a stripe along the sole bar,
    black window band, yellow doors framed in azure, KS ribbon (yellow, green,
    blue stripes) behind each cab.  Photo 31WEbc-001 (Katowice 2025, S71 working
    to Chalupki), vagonweb 31WEbc-a."""
    BODY = Paint(0xECEEEC, top=0xF2F4F2)
    BLUE = Paint(KS_BLUE, top=0x2AAAE8)
    BAND = Paint(0x17181A)
    WFRAME = Paint(0x17181A)
    DOOR = Paint(0xF2D00A)
    SKIRT = Paint(0x2E3134)
    BLACK = Paint(0x1A1B1D)
    MASK = Paint(0x1A1B1D)
    RIB = [Paint(0xF4C800), Paint(0x46B43C), Paint(0x1F7FD0)]
    ROOF = Paint(KS_BLUE, top=0x2AAAE8)
    ROOFBOX = Paint(0x7E8286, top=0x8E9296)
    BELLOWS = Paint(0x3A3D40, top=0x45484C)
    BELLOWS_DK = Paint(0x2C2E31, top=0x3A3D40)
    Z_TOPBAND = zm(3.35)
    Z_BAND0, Z_BAND1 = zm(1.50), zm(2.85)
    Z_STRIPE0, Z_STRIPE1 = zm(0.78), zm(1.12)

    def side(self, U, xp, z):
        S = U.S
        xe = min(xp, U.XEND - xp)
        if xe < S.cab_m + 0.1:
            c = self.cab_side(U, xp, xe, z)
            if c is not None:
                return c
        if z > self.Z_TOPBAND:
            return self.BLUE
        dr = self.door_at(U, xp, z)
        if dr is not None:
            return self.door(U, xp, z, dr)
        rb = self.ribbon(U, xp, xe, z)
        if rb is not None:
            return rb
        return self.base(U, xp, z, xe)

    BAND_START = 5.05      # the black window band starts behind the ribbon

    def base(self, U, xp, z, xe=99.0):
        if z > self.Z_TOPBAND:
            return self.BLUE
        if self.Z_BAND0 <= z <= self.Z_BAND1 and xe >= self.BAND_START:
            w = self.window(U, xp, z)
            return w if w is not None else self.BAND
        if self.Z_STRIPE0 <= z <= self.Z_STRIPE1:
            return self.BLUE
        if z < self.Z_STRIPE0:
            return self.SKIRT
        return self.BODY

    def door(self, U, xp, z, dr):
        S = U.S
        a, b = dr
        # azure frame round the door opening
        if xp < a or xp > b or z > S.ZD1:
            return self.BLUE
        c = (a + b) / 2
        for (l0, l1) in ((a, c), (c, b)):
            if l0 + 0.20 <= xp <= l1 - 0.20 and S.ZDW0 <= z <= S.ZDW1:
                return R.GLASS_HI if z > S.ZDW1 - 0.4 else R.GLASS
        if abs(xp - c) < 0.04:
            return Paint(0xB89E08)
        return self.DOOR

    def ribbon(self, U, xp, xe, z):
        h = zmt(z)
        a = self.RIB_X0
        if not (a - 0.2 <= xe <= a + 1.6 and 1.35 <= h <= 3.0):
            return None
        near_a = xp < U.XEND / 2
        # stripes lean back towards the rear (away from the cab) as they rise
        for i, col in enumerate(self.RIB):
            z0 = 1.45 + 0.22 * i
            if not (z0 <= h <= 2.95):
                continue
            c0 = a + i * 0.42 + (h - 1.45) * 0.30
            if c0 <= xe <= c0 + 0.30:
                return col
        return None

    RIB_X0 = 3.55

    def cab_side(self, U, xp, xe, z):
        S = U.S
        h = zmt(z)
        if z > self.Z_TOPBAND - 0.3 and xe < S.cab_m:
            return self.BLUE
        # the white body ends in a rounded front edge; blue ahead of it
        edge = self.white_edge(h)
        if xe < edge:
            # cab side window in the blue (plain glass)
            fe = 1.35 + (h - 2.0) * 0.35
            if 2.0 <= h <= 3.15 and fe <= xe <= 2.55:
                if xe > 2.45 or h > 3.05 or xe < fe + 0.08:
                    return self.MASK
                return WS_HI if h > 2.8 else WS
            if h < 0.78:
                return self.SKIRT
            return self.BLUE
        # separate cab door in the white (frame + small window)
        if 2.62 <= xe <= 3.40 and 0.75 <= h <= 3.05:
            if xe < 2.70 or xe > 3.32 or h > 2.97:
                return Paint(0x9FA3A6)
            if 2.2 <= h <= 2.85 and 2.80 <= xe <= 3.22:
                return WS
            return self.BODY
        if xe < S.cab_m:
            if self.Z_STRIPE0 <= z <= self.Z_STRIPE1:
                return self.BLUE
            if z < self.Z_STRIPE0:
                return self.SKIRT
            return self.BODY
        return None

    def white_edge(self, h):
        """front edge (m behind the nose) of the white body on the cab side."""
        return float(np.interp(h, [0.7, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4],
                               [3.4, 2.7, 2.15, 1.95, 2.05, 2.35, 2.55, 2.65]))

    # --- nose
    def nose(self, U, end, f, m, v, z):
        S, N = U.S, U.N
        av = abs(v)
        mf = N.front(z)
        dm = m - mf
        if f == "+z" and z >= S.ZS - 0.1:
            return self.BLUE
        if z < 1.0:
            return self.SKIRT
        if z < 3.8:
            # coupler recess
            if av < 0.48 and dm < 0.5 and 1.5 <= z:
                return self.BLACK
            return self.BLUE
        if z < 5.4:
            # lamp clusters, slanted black, at the lower corners of the mask
            if 0.40 <= av <= 0.86 and 4.0 <= z <= 5.3 and z > 4.0 + (av - 0.40) * 1.2:
                if 0.52 <= av <= 0.74 and 4.3 <= z <= 5.0:
                    if end == "A":
                        return R.HEAD
                    return R.TAIL if av > 0.64 else LAMP_OFF
                return self.MASK
            if av < 0.40 and z > 4.6:
                return self.MASK          # lower tip of the windscreen mask
            return self.BLUE
        if z < S.ZS - 0.1:
            lim = 0.80 - 0.06 * (z - 5.4) / (S.ZS - 5.4)
            if av < lim:
                if z > S.ZS - 1.15:
                    if abs(z - (S.ZS - 0.65)) < 0.2 and av < lim - 0.25:
                        return AMBER
                    return DISP
                if av > lim - 0.09 or z < 5.9:
                    return self.MASK
                return WS_HI if (z > 7.6 or (v > 0.3 and z > 6.6)) else WS
            return self.BLUE
        return self.BLUE

    def pod(self, end, f, z):
        if f == "-u" and end == "A" and z < 10.9:
            return R.HEAD
        return self.MASK

    def roof(self, U, x, v):
        return self.ROOF


# ---------------------------------------------------------------- unit specs
W_IMP = R.W_STD * 2.895 / 2.825     # 0.943 cu
H = dict(W=W_IMP, ZBOT=zm(0.60), ZBOG=zm(1.02), ZS=zm(3.55), ZCAP=zm(3.78), ZR=zm(3.95),
         CAP1=0.07, CAP2=0.24, bogie_cut=1.55,
         ZWF0=zm(1.70), ZWF1=zm(2.72), ZWG0=zm(1.80), ZWG1=zm(2.62), WF=0.10,
         ZD0=zm(0.62), ZD1=zm(2.98), ZDW0=zm(1.62), ZDW1=zm(2.70), DF=0.0, DFT=0.0,
         cab_m=3.6)

# end car windows behind the logo: 5 (photos 45WE-021A, 31WE-022D), door, 2
END_WIN = [(6.4, 7.6), (8.1, 9.6), (10.0, 11.5), (11.9, 13.4), (13.8, 15.2), (17.6, 19.1), (19.5, 20.7)]


def mirror(spans, xend):
    return sorted((round(xend - b, 2), round(xend - a, 2)) for (a, b) in spans)


def _wave45():
    """yellow top (m) along the +v side, vagonweb 45WE-a (window/door columns
    bridged), 0.5 m steps from the A nose."""
    h = [0.7, 0.7, 0.7, 0.7, 1.1, 1.29, 1.48, 1.66, 1.7, 1.7, 1.7, 1.6, 1.6, 1.44, 1.34, 1.24, 1.18, 1.1,
         1.02, 0.93, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 1.1, 1.1, 1.22, 1.32, 1.42, 1.52, 1.62,
         1.73, 1.84, 1.96, 2.03, 2.09, 2.16, 2.3, 2.35, 2.4, 2.44, 2.51, 2.57, 2.61, 2.64, 2.67, 2.7, 2.66,
         2.61, 2.56, 2.51, 2.46, 2.4, 2.34, 2.3, 2.16, 2.02, 1.88, 1.77, 1.63, 1.49, 1.36, 1.27, 1.18, 1.1,
         1.02, 1.0, 1.0, 1.0, 1.0, 1.06, 1.1, 1.18, 1.28, 1.38, 1.48, 1.6, 1.75, 2.0, 2.12, 2.25, 2.38, 2.5,
         2.6, 2.7, 2.7, 2.7, 2.7, 2.64, 2.54, 2.42, 2.3, 2.17, 2.05, 1.85, 1.6, 1.52, 1.4, 1.32, 1.22, 1.12,
         1.09, 1.02, 1.0, 1.0, 1.0, 1.0, 1.07, 1.15, 1.23, 1.3, 1.44, 1.58, 1.72, 1.83, 1.97, 2.11, 2.24,
         2.32, 2.38, 2.43, 2.49, 2.54, 2.59, 2.64, 2.69, 2.68, 2.65, 2.62, 2.6, 2.53, 2.47, 2.4, 2.38, 2.31,
         2.19, 2.12, 2.05, 2.0, 1.89, 1.78, 1.67, 1.56, 1.46, 1.36, 1.26, 1.17, 1.08, 1.0, 0.92, 0.9, 0.9,
         0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.98, 1.07, 1.15, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.7, 1.7, 1.7, 1.55,
         1.36, 1.18, 0.9, 0.7, 0.7, 0.7]
    return [(0.5 * i, v) for i, v in enumerate(h)]


def _wave31():
    """as _wave45, vagonweb 31WE-v2-a."""
    h = [0.7, 0.7, 0.7, 0.7, 1.1, 1.29, 1.48, 1.66, 1.7, 1.7, 1.7, 1.6, 1.6, 1.44, 1.34, 1.24, 1.18, 1.1,
         1.02, 0.93, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 1.02, 1.06, 1.1, 1.22, 1.32, 1.42, 1.52, 1.62,
         1.73, 1.84, 1.96, 2.03, 2.09, 2.16, 2.3, 2.35, 2.4, 2.44, 2.51, 2.57, 2.61, 2.64, 2.67, 2.7, 2.7,
         2.7, 2.7, 2.7, 2.65, 2.56, 2.47, 2.4, 2.26, 2.12, 1.98, 1.86, 1.76, 1.66, 1.56, 1.44, 1.31, 1.17,
         1.03, 0.98, 0.95, 0.91, 0.9, 0.9, 0.9, 0.93, 0.96, 0.99, 1.08, 1.22, 1.36, 1.5, 1.6, 1.7, 1.8, 1.9,
         2.04, 2.18, 2.32, 2.42, 2.51, 2.59, 2.68, 2.7, 2.7, 2.7, 2.7, 2.69, 2.66, 2.62, 2.6, 2.55, 2.48,
         2.41, 2.39, 2.32, 2.2, 2.13, 2.07, 2.0, 1.77, 1.6, 1.6, 1.58, 1.48, 1.38, 1.28, 1.2, 1.09, 1.05,
         1.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.97, 1.05, 1.13, 1.2, 1.28, 1.38, 1.48, 1.6, 1.7, 1.7,
         1.7, 1.7, 1.59, 1.4, 1.21, 0.9, 0.7, 0.7, 0.7]
    return [(0.5 * i, v) for i, v in enumerate(h)]


def spec_45we():
    xend = 90.8
    joints = [21.5, 37.45, 53.35, 69.25]
    doors = [(15.6, 17.3), (25.8, 27.5), (41.7, 43.4), (47.4, 49.1), (63.3, 65.0), (73.5, 75.2)]
    wa = END_WIN + [(22.4, 23.6), (24.1, 25.4), (27.8, 29.3), (29.7, 31.2), (31.6, 33.1), (33.5, 35.0),
                    (35.4, 36.6), (38.3, 39.5), (39.9, 41.4), (46.3, 47.1), (49.4, 50.9), (51.3, 52.5)]
    wins = wa + [w for w in mirror(END_WIN + [(22.4, 23.6), (24.1, 25.4), (27.8, 29.3), (29.7, 31.2),
                                              (31.6, 33.1), (33.5, 35.0), (35.4, 36.6)], xend)]
    roof = [(4.9, 6.7, 0.35, 0.55, "box"), (8.5, 12.0, 0.40, 0.66, "box"), (12.1, 16.3, 0.40, 0.66, "box"),
            (17.7, 19.8, 0.35, 0.55, "box"), (19.9, 21.2, 0.30, 0.45, "hv"),
            (27.8, 32.0, 0.40, 0.66, "box"), (35.3, 37.1, 0.30, 0.45, "hv"),
            (42.9, 47.1, 0.40, 0.66, "box"), (52.5, 53.1, 0.25, 0.40, "hv"),
            (58.8, 63.0, 0.40, 0.66, "box"), (64.4, 65.9, 0.30, 0.45, "hv"),
            (69.6, 70.9, 0.30, 0.45, "hv"), (71.0, 73.1, 0.35, 0.55, "box"),
            (74.5, 78.7, 0.40, 0.66, "box"), (78.8, 82.3, 0.40, 0.66, "box"), (84.1, 85.9, 0.35, 0.55, "box")]
    return Spec(name="45WE", lengths=[10, 8, 8, 8, 10], joints=joints, xend=xend, doors=doors,
                windows=sorted(wins), bogies=[5.5, xend - 5.5], roofboxes=roof,
                pantos=[(22.9, False, +1), (67.9, True, -1)], **H)


def spec_31we():
    xend = 74.9
    joints = [21.5, 37.45, 53.35]
    doors = [(15.6, 17.3), (25.8, 27.5), (31.5, 33.2), (41.7, 43.4), (47.4, 49.1), (57.6, 59.3)]
    wa = END_WIN + [(22.4, 23.6), (24.1, 25.4), (27.9, 29.3), (29.7, 31.2), (33.5, 35.0), (35.4, 36.6)]
    wins = wa + mirror(wa, xend)
    roof = [(4.9, 6.7, 0.35, 0.55, "box"), (8.0, 13.8, 0.40, 0.66, "box"), (14.0, 16.5, 0.40, 0.55, "box"),
            (17.1, 20.2, 0.35, 0.55, "box"), (20.7, 21.2, 0.30, 0.45, "hv"),
            (25.1, 26.4, 0.35, 0.45, "hv"), (27.8, 32.0, 0.40, 0.66, "box"), (35.3, 36.8, 0.35, 0.55, "box"),
            (38.1, 39.6, 0.35, 0.55, "box"), (42.9, 47.1, 0.40, 0.66, "box"), (48.5, 49.8, 0.35, 0.45, "hv"),
            (53.8, 54.2, 0.30, 0.45, "hv"), (54.7, 57.8, 0.35, 0.55, "box"), (58.4, 60.9, 0.40, 0.55, "box"),
            (61.1, 66.9, 0.40, 0.66, "box"), (68.2, 70.0, 0.35, 0.55, "box")]
    return Spec(name="31WE", lengths=[10, 8, 8, 10], joints=joints, xend=xend, doors=doors,
                windows=sorted(wins), bogies=[5.5, xend - 5.5], roofboxes=roof,
                pantos=[(22.9, False, +1), (52.0, True, -1)], **H)


def spec_31webc():
    xend = 75.9
    joints = [21.65, 37.95, 54.25]
    doors = [(9.4, 11.1), (15.9, 17.6), (25.7, 27.4), (32.2, 33.9),
             (42.0, 43.7), (48.5, 50.2), (58.3, 60.0), (64.8, 66.5)]
    wa = [(5.2, 5.7), (6.2, 7.3), (7.9, 9.1), (11.6, 12.7), (13.3, 13.8), (14.5, 15.4), (18.0, 19.1),
          (19.7, 20.8), (22.6, 23.7), (24.3, 25.4), (27.9, 29.0), (29.6, 30.1), (30.8, 31.7),
          (34.3, 35.4), (36.0, 37.1)]
    wins = wa + mirror(wa, xend)
    roof = [(4.0, 5.7, 0.30, 0.55, "box"), (8.9, 11.7, 0.30, 0.62, "box"), (11.9, 16.1, 0.30, 0.66, "box"),
            (16.5, 18.6, 0.30, 0.55, "box"), (19.5, 20.8, 0.30, 0.45, "box"), (25.2, 26.1, 0.25, 0.40, "hv"),
            (28.1, 32.3, 0.30, 0.66, "box"), (33.4, 35.5, 0.30, 0.55, "box"), (35.8, 37.3, 0.30, 0.50, "box"),
            (38.6, 40.1, 0.30, 0.50, "box"), (40.4, 42.5, 0.30, 0.55, "box"), (43.6, 47.8, 0.30, 0.66, "box"),
            (49.8, 50.7, 0.25, 0.40, "hv"), (55.1, 56.4, 0.30, 0.45, "box"), (57.3, 59.4, 0.30, 0.55, "box"),
            (59.8, 64.0, 0.30, 0.66, "box"), (64.2, 67.0, 0.30, 0.62, "box"), (70.2, 71.9, 0.30, 0.55, "box")]
    h = dict(H)
    h.update(ZWF0=zm(1.62), ZWF1=zm(2.76), ZWG0=zm(1.66), ZWG1=zm(2.72), WF=0.0,
             ZDW0=zm(1.55), ZDW1=zm(2.70), DF=0.12, DFT=0.30, cab_m=3.5)
    return Spec(name="31WEbc", lengths=[10, 8, 8, 10], joints=joints, xend=xend, doors=doors,
                windows=sorted(wins), bogies=[5.2, xend - 5.2], roofboxes=roof,
                pantos=[(23.3, False, +1), (52.6, True, -1)], **h)


def unit(fam):
    if fam == "45we":
        S = spec_45we()
        return Unit(S, KDLivery(_wave45()), NoseImpuls1(S.W, S.ZS, S.ZR, S.ZCAP))
    if fam == "31we":
        S = spec_31we()
        return Unit(S, KDLivery(_wave31()), NoseImpuls1(S.W, S.ZS, S.ZR, S.ZCAP))
    if fam == "31webc":
        S = spec_31webc()
        return Unit(S, KSLivery(), NoseImpuls2(S.W, S.ZS, S.ZR, S.ZCAP))
    raise KeyError(fam)


FAMILIES = {
    "45we": ("koleje-dolnoslaskie", "bilozluta", ["45WE-A", "45WE-B", "45WE-C", "45WE-D", "45WE-E"]),
    "31we": ("koleje-dolnoslaskie", "bilozluta", ["31WE-A", "31WE-B", "31WE-C", "31WE-D"]),
    "31webc": ("koleje-slaskie", "bilomodra", ["31WEbc-A", "31WEbc-B", "31WEbc-C", "31WEbc-D"]),
}


def run(families, make, argv):
    """Regenerate sheets: families = {fam: (agency dir, livery, labels)}."""
    args = list(argv)
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(families)):
        agency, liv, labels = families[fam]
        rows = make(fam).rows()
        out = os.path.join(REPO, "vehicle-rail", agency, fam, "sprites", f"{liv}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        R.save_rows(rows, out)
        if prev:
            R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
        print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    run(FAMILIES, unit, sys.argv[1:])
