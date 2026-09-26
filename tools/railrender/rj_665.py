"""RegioJet class 665 "Sirius" (CRRC Zhuzhou, built for Leo Express, three units
leased by RegioJet from 9/2024 for R23 Kolin - Melnik - Usti n. L.).

6-section articulated EMU on Jacobs bogies, Bo'2'2'2'2'2'Bo': powered bogies
under both cab sections, Jacobs bogies at the five joints. 111.2 m over
couplers = head sections 22.0 m + four intermediate sections 16.8 m
(cs.wikipedia "Elektricka jednotka 665"), 2.86 m wide, 4.3 m high, 5 single-
leaf 1 m doors per side (sections 1, 2, 3, 5, 6), pointed aerodynamic nose.

Scale 26.4 m = 13 cu: head sections 22.0 m -> 11 cu (2.0 m/cu), intermediate
16.8 m -> 8 cu (2.1 m/cu); 54 cu in all. Section k's front at
u = 0, 11, 19, 27, 35, 43; joints (Jacobs bogie centres) at 11, 19, 27, 35, 43.

Positions are taken straight from the vagonWEB drawing (research/photos/665,
vagonweb_665_full-unit_composited_10px-per-m.png, 10 px = 1 m, relax section
on the left = section 1 = our lead section, business section with the raised
pantograph = section 6 = our trailing section): drawing x (px) is mapped onto
u per section (ud()), heights (drawing rows, rail at row 57.5) are scaled by
4.02 / 3.77 so the roof crown sits at the renderer's standard 4.02 m.

Livery "antracitovozluta" (RegioJet sticker livery, 665.001 from 9 Nov 2024,
665.002 11/2024, 665.003 from 10 Apr 2025; photos 665 001 Kolin 26 Nov 2024,
665 002 Strekov 6 Aug 2025, vagonWEB 665-rj-1..6-a):
  - anthracite / blue-grey body (photos #3D4653, highlights #585F6B), roof the
    same with lighter shoulders,
  - darker window band with the windows in it,
  - RJ-yellow stripe along the bottom of the window band over the whole unit,
    rising at each cab section into a double vertical bar up to the roof
    edge, and a yellow arc sweeping from the front bar over the oval cab side
    window ("eye") down to the headlight,
  - yellow door leaves with a narrow door window,
  - white lettering above the windows ("|| REGIOJET", class words) as dashes,
  - black raked windscreen, oval headlights on the nose bulb, white
    "|| REGIOJET" on the bulb, orange-red nose skirt.
Passenger + door glass = lit specials; windscreen and eye window plain dark.
Headlights on section 1, tail lights on section 6.

Regenerate with `python tools/railrender/rj_665.py [--preview DIR]`.
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")

import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402

LIVERIES = ["antracitovozluta"]
LABELS = ["665-1", "665-2", "665-3", "665-4", "665-5", "665-6"]

LENGTHS = [11, 8, 8, 8, 8, 11]
U0 = [0, 11, 19, 27, 35, 43]
UEND = 54.0
JOINTS = [11.0, 19.0, 27.0, 35.0, 43.0]
PX = 0.375
W = R.W_STD * 2.86 / 2.825       # 0.931
HALFJ = 0.13                     # body end gap either side of a joint

# drawing x (px) of the section boundaries: nose tip, joints, nose tip
J_D = [1.0, 214.5, 382.5, 550.5, 718.5, 886.5, 1100.0]
HS = 4.02 / 3.77                 # drawing height -> model height


def zm(h):
    return h / PX


def hrow(row):
    """drawing row -> metres above rail (scaled)."""
    return (57.5 - row) / 10.0 * HS


def ud(x):
    """drawing x -> consist u."""
    for k in range(6):
        if x <= J_D[k + 1] or k == 5:
            return U0[k] + (x - J_D[k]) / (J_D[k + 1] - J_D[k]) * LENGTHS[k]


def xd(u):
    """consist u -> drawing x."""
    for k in range(6):
        if u <= U0[k] + LENGTHS[k] or k == 5:
            return J_D[k] + (u - U0[k]) / LENGTHS[k] * (J_D[k + 1] - J_D[k])


def sec_of(u):
    for k in range(5, -1, -1):
        if u >= U0[k] - 1e-6:
            return k
    return 0


DU_PX = 11.0 / 213.5             # u per drawing px on a head section

# ------------------------------------------------------------------ heights
ZBOT = zm(0.55)                  # body bottom (low floor)
ZBOG = zm(0.95)                  # body bottom over the powered bogie
ZST0, ZST1 = zm(1.12), zm(1.52)  # yellow stripe (1 full px)
ZB0, ZB1 = zm(1.52), zm(2.64)    # window band
ZG0, ZG1 = zm(1.60), zm(2.56)    # passenger glass
ZL0, ZL1 = zm(2.80), zm(3.10)    # white lettering above the windows
ZS = zm(3.20)                    # side wall top
ZC = zm(3.66)                    # roof shoulder step
ZR = zm(4.02)                    # roof crown (10.72)
ZD1 = zm(2.93)                   # door top
ZDW0, ZDW1 = zm(1.62), zm(2.60)  # door window

# ------------------------------------------------------------------ layout (drawing px)
WINDOWS = [(44, 55), (62, 73), (80, 91), (98, 109), (116, 127), (155, 166), (173, 184),
           (227, 238), (245, 256), (263, 274), (281, 292), (299, 310), (341, 352), (359, 370),
           (395, 406), (413, 424), (431, 442), (449, 460), (467, 478), (509, 520), (527, 538),
           (563, 574), (581, 592), (599, 610), (617, 628), (641, 652), (659, 670), (677, 688),
           (695, 706),
           (731, 742), (749, 760), (791, 802), (809, 820), (827, 838), (845, 856), (863, 874),
           (917, 928), (935, 946), (974, 985), (992, 1003), (1010, 1021), (1028, 1039), (1046, 1057)]
DOORS = [(138, 148), (325, 335), (493, 503), (767, 777), (953, 963)]
LETTERS = [(45, 69), (88, 107), (260, 288), (428, 456), (656, 684), (824, 852), (911, 929),
           (996, 1025), (1032, 1056)]
BAND_LOGOS = [(191, 209), (893, 911)]          # small white "|| REGIOJET" on the band
ROOFBOX = [(108, 154), (284, 314), (452, 482), (628, 658), (820, 850), (988, 1018)]
PANTO_X = 906                                   # pantograph base, section 6 (raised)

# cab-section features by dn = drawing px behind the nose tip
BAR_F = (28.0, 32.0)             # front vertical bar (slightly widened: 1 px each
BAR_R = (36.0, 40.0)             # + 1 px gap in the side views)
BAND_START = 42.0
EYE_BACK = 26.5
# yellow arc centre line (dn, h metres): from the top of the front bar forward
# and down over the eye to the headlight (drawing rows 27..41)
ARC = [(30.0, hrow(26.6)), (26.0, hrow(28.3)), (22.0, hrow(29.4)), (19.0, hrow(30.8)),
       (17.0, hrow(32.0)), (15.5, hrow(33.3)), (13.5, hrow(35.0)), (12.0, hrow(36.6)),
       (10.5, hrow(38.5)), (9.2, hrow(40.6))]
ARC_HW = 0.20                    # arc half thickness (m): >= 1 px in every view

# ------------------------------------------------------------------ colours
BODY = Paint(0x545C68)
BODY_HI = Paint(0x5A626E)
BODY_DK = Paint(0x3E454F)
ROOF = Paint(0x545C68, top=0x5E6570)
ROOF_SH = Paint(0x5C6470, top=0x6C737E)       # lighter shoulder (sky reflection)
BAND = Paint(0x22262B)
YELLOW = Paint(0xFFB612)
YEL_DK = Paint(0xD99A0C)
WHITE = Paint(0xE6EAED)
ORANGE = Paint(0xE8581E)
WS = (0x22, 0x29, 0x30)
WS_HI = (0x3E, 0x4C, 0x58)
EYE = (0x1E, 0x23, 0x28)
BELLOWS = Paint(0x26282B)
BELLOWS_DK = Paint(0x1B1C1E)
BOGIE = Paint(0x232426)
BOGIE_HI = Paint(0x3C3F42)
UNDER = Paint(0x1C1D1F)
ROOFEQ = Paint(0x474E57, top=0x565D66)
PANTO_BASE = Paint(0x55595E, top=0x6E7378)


# ------------------------------------------------------------------ nose geometry
# nose front (dn, drawing px behind the tip) vs height h (m), from the drawing
NOSE = [(0.70, 14.0), (0.80, 3.0), (0.92, 1.0), (1.01, 0.0), (1.86, 0.0), (2.40, 3.0),
        (2.93, 8.0), (3.46, 13.0), (3.78, 18.0), (4.02, 22.0)]


def nose_dn(h):
    hs = [p[0] for p in NOSE]; ds = [p[1] for p in NOSE]
    return float(np.interp(h, hs, ds))


def corner(h):
    """plan-view rounding: (Ru along u, Rv lateral, max half width)."""
    if h < 1.9:
        return 0.95, 0.42, W - 0.02          # rounded nose bulb
    if h < 3.2:
        return 0.80, 0.34, W
    return 0.55, 0.26, W - 0.10


def half_width(h, du):
    Ru, Rv, hw = corner(h)
    if du >= Ru:
        return hw
    t = 1.0 - du / Ru
    return hw - Rv * (1.0 - np.sqrt(max(0.0, 1.0 - t * t)))


UN = 1.9     # nose slabs end here (u behind the tip)


def arc_dist(dn, h):
    """distance (m) from (dn, h) to the arc centre line."""
    p = np.array([dn * 0.1, h])
    best = 9.0
    for (a, b) in zip(ARC[:-1], ARC[1:]):
        A = np.array([a[0] * 0.1, a[1]]); B = np.array([b[0] * 0.1, b[1]])
        AB = B - A
        t = max(0.0, min(1.0, float((p - A) @ AB / (AB @ AB))))
        best = min(best, float(np.linalg.norm(p - (A + t * AB))))
    return best


def arc_dn(h):
    """dn of the arc centre line at height h (the arc is monotonic)."""
    hs = [p[1] for p in ARC][::-1]; ds = [p[0] for p in ARC][::-1]
    return float(np.interp(h, hs, ds))


def dashes(x, a, b):
    """white lettering as bold dashes with 1-px-ish gaps (reads as text at 1x)."""
    t = (x - a) / (b - a)
    return int(t * 7.0) % 3 != 2


# ------------------------------------------------------------------ model
class Unit:
    def __init__(self, liv):
        self.liv = liv
        self.parts = []
        self.lines = []
        self.build()

    # ---- side paint
    def side(self, u, z, face):
        """paint of a side-wall point; u consist, z model px."""
        h = z * PX
        k = sec_of(u)
        x = xd(u)
        if z >= ZS - 0.02:
            return ROOF_SH
        # doors
        for (a, b) in DOORS:
            if a <= x <= b and z <= ZD1:
                c = (a + b) / 2
                if abs(x - c) <= 2.6 and ZDW0 <= z <= ZDW1:
                    return R.GLASS_HI if z > ZDW1 - 0.5 else R.GLASS
                if x - a < 1.2 or b - x < 1.2 or z > ZD1 - 0.3:
                    return YEL_DK
                return YELLOW
        if k in (0, 5):
            dn = (x - 1.0) if k == 0 else (1100.0 - x)
            p = self.cab_side(k, dn, h, z)
            if p is not None:
                return p
        # window band + glass
        if ZB0 <= z <= ZB1:
            for (a, b) in WINDOWS:
                if a + 0.6 <= x <= b - 0.6 and ZG0 <= z <= ZG1:
                    return R.GLASS_HI if z > ZG1 - 0.55 else R.GLASS
            for (a, b) in BAND_LOGOS:
                if a <= x <= b and zm(1.85) <= z <= zm(2.25) and dashes(x, a, b):
                    return WHITE
            return BAND
        if ZST0 <= z < ZST1:
            return YELLOW
        if ZL0 <= z <= ZL1:
            for (a, b) in LETTERS:
                if a <= x <= b and dashes(x, a, b):
                    return WHITE
        if z > ZB1 + 0.6:
            return BODY_HI
        return BODY

    def cab_side(self, k, dn, h, z):
        """cab-section paint in front of the window band (None = go on)."""
        if dn >= BAND_START:
            return None
        if BAR_F[0] <= dn < BAR_F[1] or BAR_R[0] <= dn < BAR_R[1]:
            if ZST0 <= z < ZS - 0.02:
                return YELLOW
        if BAR_R[1] <= dn < BAND_START:
            if ZST0 <= z < ZST1:
                return YELLOW
            return BODY
        if dn < BAR_F[0] + 0.5:
            if arc_dist(dn, h) <= ARC_HW:
                return YELLOW
            # oval cab side window under the arc
            if 1.95 <= h <= 2.95 and arc_dn(h) + 1.9 <= dn <= EYE_BACK:
                return EYE
        return BODY

    # ---- nose paint (front face, rounded corners, sloped tops)
    def nose(self, k, ul, v, z, face):
        h = z * PX
        dn = ul / DU_PX
        rear = (k == 5)
        vl = v if k == 0 else -v              # lateral in the section's own frame
        av = abs(v)
        du = ul - nose_dn(h) * DU_PX
        Ru, Rv, hw = corner(h)
        # side-ish surfaces of the cab: livery elements
        near_side = av > half_width(h, max(0.0, du)) - 0.16
        if h < 0.70:
            return BODY_DK
        if h < 1.01:
            return BODY_DK
        if h < 1.90:
            if 1.58 <= h <= 1.88 and 0.40 <= av <= 0.72 and du < 0.55:
                return R.TAIL if rear else R.HEAD
            if near_side and du > 0.25:
                return self.cab_side(k, dn, h, z) or BODY
            # white "|| REGIOJET" on the bulb, viewer's right = section's -v
            if 1.14 <= h <= 1.42 and -0.66 <= vl <= -0.12 and du < 0.45:
                return WHITE if int((-vl - 0.12) * 16) % 3 != 2 else BODY
            return BODY
        if h < 3.42 or (near_side and z < ZS - 0.02 and du > 0.18):
            if near_side and du > 0.18:
                return self.cab_side(k, dn, h, z) or BODY
            if near_side and du > 0.18:
                return self.cab_side(k, dn, h, z) or BODY
            lim = hw - 0.20
            if av < lim:
                return WS_HI if (h > 2.95 or (vl > 0.25 and h > 2.5)) else WS
            return BODY_HI
        return ROOF if face != "+z" else ROOF

    # ---- materials
    def mat_for(self, k):
        def mat(f, u, v, z, d):
            if k in (0, 5):
                ul = u if k == 0 else UEND - u
                fl = f
                if k == 5 and f in ("-u", "+u"):
                    fl = "-u" if f == "+u" else "+u"
                if f == "+z":
                    if ul < UN + 0.05 and z < ZR - 0.05:
                        return self.nose(k, ul, v, z, f)
                    if z < ZS + 0.05:
                        return ROOF_SH
                    return ROOF
                if fl == "-u" and ul < UN + 0.05:
                    return self.nose(k, ul, v, z, fl)
                if f in ("+v", "-v"):
                    if ul < UN + 0.05:
                        return self.nose(k, ul, v, z, f)
                    return self.side(u, z, f)
                return BODY_DK                    # joint end face
            if f == "+z":
                return ROOF_SH if z < ZS + 0.05 else ROOF
            if f in ("+v", "-v"):
                return self.side(u, z, f)
            return BODY_DK
        return mat

    def add(self, u0, u1, v0, v1, z0, z1, mat, own):
        self.parts.append(Part(u0, u1, v0, v1, z0, z1, mat, own))

    def add_end(self, k, ul0, ul1, v0, v1, z0, z1, mat, own):
        if k == 0:
            self.add(ul0, ul1, v0, v1, z0, z1, mat, own)
        else:
            self.add(UEND - ul1, UEND - ul0, v0, v1, z0, z1, mat, own)

    def build(self):
        for k in range(6):
            own = f"c{k}"
            mat = self.mat_for(k)
            if k in (0, 5):
                self.build_end(k, mat, own)
            else:
                u0, u1 = U0[k] + HALFJ, U0[k] + LENGTHS[k] - HALFJ
                self.add(u0, u1, -W, W, ZBOT, ZS, mat, own)
                self.add(u0 + 0.03, u1 - 0.03, -W + 0.10, W - 0.10, ZS, ZC, mat, own)
                self.add(u0 + 0.06, u1 - 0.06, -W + 0.32, W - 0.32, ZC, ZR, mat, own)
                self.add(U0[k] + 1.0, U0[k] + LENGTHS[k] - 1.0, -W + 0.28, W - 0.28, 1.1, ZBOT,
                         lambda *a: UNDER, own)
        # joints: bellows + Jacobs bogie, owned by the section in front
        for j, J in enumerate(JOINTS):
            own = f"c{j}"
            self.add(J - HALFJ - 0.02, J + HALFJ + 0.02, -W + 0.12, W - 0.12, ZBOT + 0.3, ZS + 0.25,
                     lambda f, u, v, z, d: BELLOWS if (f == "+z" or int(u * 24) % 2 == 0) else BELLOWS_DK,
                     own)
            self.parts += R.bogie(J, own, W=W, half=0.80, z1=2.0, col=BOGIE, frame=BOGIE_HI)
        # powered end bogies (drawing x 30..64 / 1038..1071)
        for (k, x) in ((0, 47.0), (5, 1054.5)):
            self.parts += R.bogie(ud(x), f"c{k}", W=W, half=0.85, z1=2.35, col=BOGIE, frame=BOGIE_HI)
        self.build_roof()

    def build_end(self, k, mat, own):
        layers = [(zm(0.70), zm(1.01)), (zm(1.01), zm(1.45)), (zm(1.45), zm(1.90))]
        z = zm(1.90)
        while z < ZR - 1e-6:
            z1 = min(ZR, z + 0.45)
            layers.append((z, z1))
            z = z1
        for (z0, z1) in layers:
            zc = (z0 + z1) / 2
            h = zc * PX
            uf = nose_dn(h) * DU_PX
            Ru, Rv, hw = corner(h)
            if z0 >= ZS - 0.01:
                hw = min(hw, W - 0.10 if z0 < ZC else W - 0.32)
            n = 6
            for i in range(n):
                a = uf + Ru * i / n
                b = uf + Ru * (i + 1) / n
                if a >= UN:
                    break
                b = min(b, UN)
                hwi = min(hw, half_width(h, (a + b) / 2 - uf))
                self.add_end(k, a, b, -hwi, hwi, z0, z1, mat, own)
            b = uf + Ru
            if b < UN:
                self.add_end(k, b, UN, -hw, hw, z0, z1, mat, own)
        # main body (higher bottom over the powered bogie)
        ub = 66.0 * DU_PX                  # behind the powered bogie (drawing x 30..64)
        self.add_end(k, UN, ub, -W, W, ZBOG, ZS, mat, own)
        self.add_end(k, ub, LENGTHS[k] - HALFJ, -W, W, ZBOT, ZS, mat, own)
        self.add_end(k, UN, LENGTHS[k] - HALFJ - 0.03, -W + 0.10, W - 0.10, ZS, ZC, mat, own)
        self.add_end(k, UN, LENGTHS[k] - HALFJ - 0.06, -W + 0.32, W - 0.32, ZC, ZR, mat, own)
        # orange-red skirt under the nose bulb (drawing x 14..30, rows 51.5..55.5;
        # photos: it shows below the bulb from the front, so it starts a little
        # further forward and is a touch taller for visibility)
        self.add_end(k, 7.0 * DU_PX, 30.0 * DU_PX, -(W - 0.26), W - 0.26, zm(0.16), zm(0.69),
                     lambda f, u, v, z, d: ORANGE, own)
        # underbody shadow behind the powered bogie
        self.add_end(k, ub, LENGTHS[k] - 1.0, -W + 0.28, W - 0.28, 1.1, ZBOT, lambda *a: UNDER, own)

    def build_roof(self):
        for (a, b) in ROOFBOX:
            ua, ub = ud(a), ud(b)
            k = sec_of((ua + ub) / 2)
            self.add(ua, ub, -0.62, 0.62, ZR - 0.05, ZR + 0.85, lambda *x: ROOFEQ, f"c{k}")
        # pantograph on section 6 near its front joint, raised, knee trailing
        ub = ud(PANTO_X)
        self.add(ub - 0.45, ub + 0.55, -0.45, 0.45, ZR - 0.05, ZR + 0.45, lambda *x: PANTO_BASE, "c5")
        self.lines += R.pantograph(ub, ZR + 0.45, "c5", fold=+1, reach=0.95, height=5.6,
                                   col=(0x70, 0x74, 0x78), head=(0x2A, 0x2A, 0x2C), half_head=0.62,
                                   thick=False)


def rows_for(liv):
    un = Unit(liv)
    rows = []
    for k in range(6):
        lo, hi = U0[k] - 3.0, U0[k] + LENGTHS[k] + 3.0
        parts = [p for p in un.parts if p.b[1] >= lo and p.b[0] <= hi]
        lines = [l for l in un.lines if lo <= l[0][0] <= hi]
        rows.append([R.vehicle_tile(parts, lines, d, float(U0[k]), {f"c{k}"}) for d in DIRS])
    return rows


JOBS = {"665": [(c, (lambda c=c: rows_for(c)), LABELS) for c in LIVERIES]}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        os.makedirs(prev, exist_ok=True)
    for fam, jobs in JOBS.items():
        for liv, make, labels in jobs:
            rows = make()
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
