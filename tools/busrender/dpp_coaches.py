"""DPP Prague non-city buses rendered as box models: the Iveco Crossway PRO
10.8M / 12M driving-school buses and the Mercedes-Benz Tourismo 15 RHD /
Tourismo RHD charter coaches.

usage: python tools/busrender/dpp_coaches.py [family ...]   regenerate the sheets
       python tools/busrender/dpp_coaches.py --preview DIR      also write zoomed previews

Families (vehicle-bus/dpp/<family>/sprites/<livery>.png):
  crossway_pro_10_8m  bila
  crossway_pro_12m    bila
  tourismo_15_rhd     bila
  tourismo_rhd        dppcervena

Rendered with the RegioJet coach pipeline, whose modules are only imported
(rj_vrender.py raycaster, rj_busmodels.Coach helpers, rj_buses.calibration and
rj_lane placement), so the coaches share the long-coach scale of the
VZ-RegioJet coaches: lengths x 1.08, drawn width 3.1 m, true heights at 4.2
px/m, every livery band a whole number of pixel rows counted from the body
bottom Z0, and the body footprint on the median lane of native 12 m buses.
Nothing is read from disk: the models are fully procedural.

Positions in the specs are REAL metres from the front (x). +v = right-hand
(door) side, -v = left (driver) side; on the right side screen-left is the
rear, on the left side screen-left is the front.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import numpy as np
from rj_vrender import Box, render, DIRS, Sh, PXZ
import rj_busmodels as C
from rj_busmodels import Coach, lerp, W2
from rj_buscommon import save_rows, preview
from rj_buses import calibration
from rj_lane import shift_tile

# ------------------------------------------------------------------ palette
WHITE = (0xF2, 0xF2, 0xF0)        # body white (#F2F2F0, as the brief's 'bila')
WHITE_ROOF = (0xEE, 0xEE, 0xEB)   # roof tops (unshaded) a shade darker than the sides
WHITE_SEAM = (0xDA, 0xDB, 0xD9)   # panel / locker seams on white
GREY_LINE = (0xA8, 0xAA, 0xAC)    # the Crossway's front chrome-grey bar
GLASS = C.GLASS                   # special 28, lit when loaded
GLASS_HI = C.GLASS_HI             # special 16
SCREEN = C.SCREEN                 # driver's glass, never lit
SCREEN_HI = C.SCREEN_HI
BLACK = C.BLACK
PILLAR = (0x26, 0x27, 0x29)
UNDER = C.UNDER
GRILLE = (0x6A, 0x6C, 0x6E)
GRILLE_DK = (0x44, 0x46, 0x48)
PLATE = C.PLATE
HEAD = C.HEAD
TAIL = C.TAIL
MARKER = (0xF0, 0x8A, 0x20)       # amber side marker lamps (plain colour)
DPP_RED = (0xD7, 0x1A, 0x21)      # DPP logo red
L_BLUE = (0x1E, 0x4F, 0xB4)       # driving-school 'L' plates
CHROME = C.CHROME
MIRROR = (0x22, 0x22, 0x24)

# Tourismo RHD (2025) DPP red with the gold Prague skyline
TR_RED = (0xD2, 0x1E, 0x24)
TR_RED_ROOF = (0xDC, 0x2A, 0x2E)
TR_RED_SEAM = (0xA8, 0x16, 0x1B)
GOLD = (0xD9, 0xAE, 0x4A)


def inside(x, a, b):
    return a <= x < b


# ====================================================================== Crossway
class CrosswayPro(Coach):
    """Iveco Crossway PRO (high-floor interurban, 2013+ front), 2 doors 1-1-0.

    Heights from the DPP photos (#6AZ 6097 side-on, 5AZ 5534 rear-left):
    body bottom 0.32 m, glazing band 1.75-2.94 m with a one-row dip towards
    the front door ('CROSSWAY' swoosh), white roof rim, A/C pod over the
    front half of the roof. Front: windscreen from 1.51 m, white mask with the
    grey IVECO bar and low headlights; rear: big rear window, tall corner tail
    lamps, engine grille at the right rear corner."""
    Z0 = 0.32
    wheel_r = 0.52
    arch_rows = 4
    R_BAND0, R_BAND1 = 6, 11          # band rows 6..10 (1.75-2.94 m)
    R_TOP = 12                        # side wall top zr(12) = 3.18 m
    ROOF = 3.26
    AC_TOP = 3.46
    DOOR_F = (0.30, 1.28)
    SWOOSH = (1.28, 2.55)             # band dips one row from the door back to here
    L_PLATE_X = 3.30                  # side L plate / DPP logo positions (right side)
    LOGO_X = 4.05


    def glass(self, k):
        """band glazing: black frame row on top, lighter reflection row below."""
        if k == self.R_BAND1 - 1:
            return BLACK
        if k == self.R_BAND1 - 2:
            return GLASS_HI
        return GLASS

    # -------------------------------------------------------------- sides
    def side(self, u, z, right):
        x = self.X(u)
        k = self.row(z)
        L = self.real_len
        w = self.wheel(u, z)
        if w is not None:
            return w
        if right:
            d = self.door(x, k)
            if d is not None:
                return d
        if k >= self.R_BAND1:
            return Sh(WHITE)
        # --- glazing band ------------------------------------------------
        b0 = self.R_BAND0
        if right and k == b0 - 1 and self.SWOOSH[0] <= x < lerp(*self.SWOOSH, 0.55):
            return BLACK             # the swoosh: one row lower behind the front door
        if b0 <= k < self.R_BAND1:
            top = k == self.R_BAND1 - 1
            if x < 0.14:
                return SCREEN                               # windscreen wrap
            if not right and x < 1.35:
                return SCREEN_HI if top else SCREEN         # driver's window
            if x >= L - 0.22:
                return Sh(WHITE)                            # rear corner post
            for p in self.pillars(right):
                if self.vline(x, p):
                    return PILLAR
            return self.glass(k)
        if not right and x < 1.35 and k == b0 - 1:
            return SCREEN
        if x < 0.14 and k >= 5:
            return SCREEN
        # --- rear engine grilles -----------------------------------------
        if right and L - 1.25 <= x < L - 0.25 and 1 <= k <= 4:
            return Sh(GRILLE) if k % 2 else Sh(GRILLE_DK)
        if not right and L - 0.95 <= x < L - 0.55 and k == 5:
            return Sh(GRILLE)
        # --- small real features ------------------------------------------
        if k == 1:
            for mx in self.markers():
                if self.vline(x, mx):
                    return MARKER
        if right and k in (4, 5):
            if self.vline(x, self.L_PLATE_X):
                return L_BLUE
            if self.vline(x, self.LOGO_X) and k == 4:
                return DPP_RED
        if not right and k in (4, 5):
            if self.vline(x, L - self.L_PLATE_X - 1.0):
                return L_BLUE
            if self.vline(x, L - self.LOGO_X - 1.0) and k == 4:
                return DPP_RED
        if 1 <= k <= 3:
            for p in self.seams(right):
                if self.vline(x, p):
                    return Sh(WHITE_SEAM)
        return Sh(WHITE)

    def markers(self):
        return (1.9, self.axles[0] + 1.6, self.axles[1] - 1.5, self.real_len - 0.45)

    def door(self, x, k):
        # front door: glazing down to 1.51 m, white panel, low black window
        d0, d1 = self.DOOR_F
        if d0 <= x < d1:
            if k >= self.R_BAND1:
                return None
            edge = self.vline(x, d0) or (d1 - self.pw() <= x < d1)
            if edge:
                return BLACK
            if k >= 5:
                return self.glass(k)
            if 1 <= k <= 2:
                return SCREEN
            return Sh(WHITE)
        d0, d1 = self.DOOR_M
        if d0 <= x < d1:
            if k >= self.R_BAND1:
                return None
            edge = self.vline(x, d0) or (d1 - self.pw() <= x < d1)
            if edge:
                return BLACK
            if k >= 4:
                return self.glass(k)
            return Sh(WHITE)
        return None

    # -------------------------------------------------------------- ends
    def front(self, v, z):
        av = abs(v)
        k = self.row(z)
        if k >= self.R_BAND1:
            return Sh(WHITE)
        if k >= 5:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == self.R_BAND1 - 1 else SCREEN
        if k == 4:
            if -0.62 <= v < -0.30:
                return L_BLUE                              # L plate, driver's side
            if -0.22 <= v < 0.02:
                return DPP_RED                             # DPP logo
            return Sh(WHITE)
        if k == 3:
            return Sh(GREY_LINE) if av < 1.05 else Sh(WHITE)
        if k == 2:
            if av > W2 - 0.48:
                return HEAD
            return Sh(WHITE)
        if k == 1:
            return PLATE if av < 0.28 else Sh(WHITE)
        return Sh(WHITE)

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        if 7 <= k <= 10 and av < W2 - 0.22:
            return GLASS_HI if k == 10 else GLASS
        if 0 <= k <= 3 and av > W2 - 0.20:
            return TAIL
        if k in (4, 5) and av < 0.20:
            return L_BLUE                                  # big L plate
        if k == 1 and av < 0.28:
            return PLATE
        if k == 0 and av < 0.9:
            return Sh(WHITE_SEAM)
        return Sh(WHITE)

    def roof(self, u, v):
        return WHITE_ROOF

    def ac(self, face, u, v, z):
        if face == "+z":
            return (0xEC, 0xEC, 0xE9)
        return Sh((0xDA, 0xDA, 0xD7))

    # -------------------------------------------------------------- geometry
    def model(self):
        L = self.L
        U = self.U
        rl = self.real_len
        ztop = self.zr(self.R_TOP)
        B = self.mat_body
        boxes = [
            Box(U(rl - 0.08), U(0.08), -W2, W2, self.Z0, ztop, B),
            Box(U(0.08), U(0.0), -W2 + 0.07, W2 - 0.07, self.Z0, ztop, B),
            Box(U(rl), U(rl - 0.08), -W2 + 0.07, W2 - 0.07, self.Z0, ztop, B),
            Box(U(rl - 0.10), U(0.10), -W2 + 0.03, W2 - 0.03, ztop, self.ROOF, B),
            Box(U(self.AC[1]), U(self.AC[0]), -0.95, 0.95, self.ROOF, self.AC_TOP, self.ac),
            Box(U(rl - 0.5), U(0.5), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
        ]
        for a in self.axles:
            boxes.append(Box(U(a) - 0.5, U(a) + 0.5, -W2 + 0.07, W2 - 0.07, 0.0, self.Z0 + 0.01, self.mat_tire))
        # mirrors: arms from above the windscreen, heads hanging at the corners
        lines = []
        for s in (-1, 1):
            p0 = (L - 0.10, s * (W2 - 0.25), 3.02)
            p1 = (L + 0.30, s * (W2 + 0.12), 2.95)
            p2 = (L + 0.32, s * (W2 + 0.16), 2.30)
            lines += [(p0, p1, MIRROR), (p1, p2, MIRROR)]
        return L, boxes, lines


class CrosswayPro108(CrosswayPro):
    """10.8M: 10.795 m, wheelbase 5.10 m (front overhang 2.55 m)."""
    real_len = 10.795
    axles = (2.55, 7.65)
    DOOR_M = (6.02, 6.97)
    AC = (2.35, 5.35)

    def pillars(self, right):
        if right:
            return (2.62, 4.30, 7.05, 8.75)
        return (2.62, 4.30, 6.00, 7.70, 9.30)

    def seams(self, right):
        return (4.3, 5.9, 8.9) if right else (1.5, 3.4, 5.1, 8.9)


class CrosswayPro12(CrosswayPro):
    """12M: 12.0 m, wheelbase 6.08 m (front overhang 2.60 m)."""
    real_len = 12.0
    axles = (2.60, 8.68)
    DOOR_M = (7.02, 7.97)
    AC = (2.50, 5.70)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 8.05, 9.65, 11.00)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 10.10)

    def seams(self, right):
        return (4.1, 5.8, 9.9) if right else (1.5, 3.6, 5.5, 7.3, 9.9)


# ====================================================================== Tourismo
class Tourismo(Coach):
    """Mercedes-Benz Tourismo RHD coaches (common helpers)."""
    Z0 = 0.30
    wheel_r = 0.52
    arch_rows = 4
    R_BAND0, R_BAND1 = 8, 14          # band rows 8..13 (2.20-3.63 m), row 13 = black top
    R_TOP = 14                        # side top zr(14) = 3.63 m
    ROOF = 3.72
    ROOF_INSET = 0.18
    DOOR_F = (0.32, 1.28)
    glass = CrosswayPro.glass

    # colours by livery ------------------------------------------------
    def body(self):
        return {"bila": WHITE, "dppcervena": TR_RED}[self.liv]

    def roofc(self):
        return {"bila": WHITE_ROOF, "dppcervena": TR_RED_ROOF}[self.liv]

    def seamc(self):
        return {"bila": WHITE_SEAM, "dppcervena": TR_RED_SEAM}[self.liv]

    def band_bottom(self, x, right):
        """z of the glazing band's lower edge at x (subclasses add sweeps)."""
        return self.zr(self.R_BAND0)

    def side(self, u, z, right):
        x = self.X(u)
        k = self.row(z)
        L = self.real_len
        w = self.wheel(u, z)
        if w is not None:
            return w
        if right:
            d = self.door(x, k)
            if d is not None:
                return d
        body = Sh(self.body())
        if k >= self.R_BAND1:
            return self.over_band(x, k, right)
        zb = self.band_bottom(x, right)
        zc = self.zr(k) + 0.5 * PXZ
        if zc >= zb and k < self.R_BAND1:
            top = k == self.R_BAND1 - 1
            if x < 0.16:
                return SCREEN
            if not right and x < 1.45:
                return SCREEN_HI if top else SCREEN
            rc = self.rear_corner(k)
            if x >= L - rc:
                return body
            for p in self.pillars(right):
                if self.vline(x, p):
                    return PILLAR
            return self.glass(k)
        if x < 0.16 and k >= 4:
            return SCREEN
        c = self.decor(x, k, right)
        if c is not None:
            return c
        if k == 1:
            for mx in self.markers():
                if self.vline(x, mx):
                    return MARKER
        if 0 <= k <= 5:
            for p in self.seams(right):
                if self.vline(x, p):
                    return Sh(self.seamc())
        return body

    def over_band(self, x, k, right):
        return Sh(self.body())

    def rear_corner(self, k):
        """depth of the body-coloured rear corner (the band ends rounded)."""
        top = self.R_BAND1 - 1
        return 0.30 if k < top else 0.55

    def markers(self):
        return (2.0, self.axles[0] + 1.7, self.axles[1] - 1.4, self.real_len - 0.5)

    def door(self, x, k):
        d0, d1 = self.DOOR_F
        if d0 <= x < d1:
            if k >= self.R_BAND1:
                return None
            edge = self.vline(x, d0) or (d1 - self.pw() <= x < d1)
            if edge:
                return BLACK
            if k >= 3:
                return self.glass(k)
            return Sh(self.body())
        d0, d1 = self.DOOR_M
        if d0 <= x < d1:
            if k >= self.R_BAND1:
                return None
            zb = self.row(self.band_bottom((d0 + d1) / 2, True))
            edge = self.vline(x, d0) or (d1 - self.pw() <= x < d1)
            if edge and k >= 1:
                return Sh(self.seamc()) if k < zb else BLACK
            if k >= zb:
                return self.glass(k)
            return None
        return None

    # -------------------------------------------------------------- ends
    def front(self, v, z):
        av = abs(v)
        k = self.row(z)
        body = Sh(self.body())
        if k >= self.R_BAND1:
            return body
        if k == self.R_BAND1 - 1:
            return BLACK                                   # black cap over the windscreen
        if k >= 4:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k in (self.R_BAND1 - 2, 9) else SCREEN
        if k == 3:
            return self.front_mid(v)
        if k == 2:
            if av > W2 - 0.52:
                return HEAD
            return Sh(CHROME) if av < 0.62 else body
        if k == 1:
            return PLATE if av < 0.28 else body
        return body

    def front_mid(self, v):
        av = abs(v)
        if av < 0.62:
            return Sh(CHROME) if av > 0.10 else BLACK         # grille with the star
        return Sh(self.body())

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        body = Sh(self.body())
        if k == 13 and av < W2 - 0.10:
            return BLACK
        if 10 <= k <= 12 and av < W2 - 0.25:
            return GLASS_HI if k == 12 else GLASS
        if 2 <= k <= 5 and av > W2 - 0.22:
            return TAIL
        if 2 <= k <= 5 and 0.55 <= av < W2 - 0.35:
            return Sh(GRILLE) if k % 2 == 0 else Sh(GRILLE_DK)  # engine louvres
        if k == 1 and av < 0.28:
            return PLATE
        return self.rear_decor(v, k) or body

    def rear_decor(self, v, k):
        return None

    def roof(self, u, v):
        return self.roofc()

    def ac(self, face, u, v, z):
        if face == "+z":
            return self.roofc()
        return Sh(self.seamc() if self.liv != "bila" else (0xDA, 0xDA, 0xD7))

    def model(self):
        L = self.L
        U = self.U
        rl = self.real_len
        ztop = self.zr(self.R_TOP)
        B = self.mat_body
        boxes = [
            Box(U(rl - 0.08), U(0.10), -W2, W2, self.Z0, ztop, B),
            Box(U(0.10), U(0.0), -W2 + 0.08, W2 - 0.08, self.Z0, ztop, B),
            Box(U(rl), U(rl - 0.08), -W2 + 0.08, W2 - 0.08, self.Z0, ztop, B),
            Box(U(rl - 0.30), U(0.35), -W2 + self.ROOF_INSET, W2 - self.ROOF_INSET, ztop, self.ROOF, B),
            Box(U(self.AC[1]), U(self.AC[0]), -0.85, 0.85, self.ROOF, self.ROOF + 0.14, self.ac),
            Box(U(rl - 0.5), U(0.7), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
        ]
        for a in self.axles:
            boxes.append(Box(U(a) - 0.5, U(a) + 0.5, -W2 + 0.07, W2 - 0.07, 0.0, self.Z0 + 0.01, self.mat_tire))
        return L, boxes, self.mirrors(3.45, 2.55, self.mirror_col())

    def mirror_col(self):
        return MIRROR

    mirrors = C.IrizarI8.mirrors


class Tourismo15(Tourismo):
    """Tourismo 15 RHD (2nd generation, 2014): 13.99 x 2.55 x 3.68 m, 3 axles
    (tag axle), front door + middle door; DPP #4AJ 7335: white with the large
    red DPP emblem over the rear quarter of both sides."""
    real_len = 13.99
    axles = (2.62, 9.10, 10.45)
    DOOR_M = (6.10, 6.95)
    AC = (6.0, 10.0)

    def pillars(self, right):
        if right:
            return (1.75, 3.55, 5.40, 7.40, 9.30, 11.30)
        return (3.55, 5.40, 7.40, 9.30, 11.30)

    def seams(self, right):
        return (3.4, 5.2, 7.8, 11.4) if right else (3.4, 5.2, 7.2, 11.4)

    def band_bottom(self, x, right):
        z = self.zr(self.R_BAND0)
        if x < 1.75 and right:
            return self.zr(3)          # the front door window reaches low
        return z

    def emblem(self, x, k, right):
        """The red DPP emblem over the rear quarter of both sides (photos of
        #4AJ 7335): from the rear corner a wide swash falling from under the
        glazing to the bottom, then a tall oval ring with a narrow white hole,
        ending just behind the tag axle. s = metres from the rear end."""
        if k < 0 or k > self.R_BAND0 - 1:
            return None
        sr = self.real_len - x
        h = self.zr(k) + 0.5 * PXZ
        # oval ring
        e_out = ((sr - 2.55) / 0.80) ** 2 + ((h - 1.30) / 0.98) ** 2
        e_in = ((sr - 2.55) / 0.30) ** 2 + ((h - 1.30) / 0.52) ** 2
        if e_out < 1.0 and e_in >= 1.0:
            return DPP_RED
        # swash from the top rear down towards the front bottom
        sc = 0.15 + (2.15 - h) * (1.35 / 1.75)
        if 0.35 <= h < 2.15 and abs(sr - sc) < 0.42 and sr > 0.05:
            return DPP_RED
        return None

    def decor(self, x, k, right):
        e = self.emblem(x, k, right)
        if e is not None:
            return e
        # small 'Dopravní podnik' logo mid-side (red mark)
        lx = 4.4 if right else 3.8
        if k == self.R_BAND0 - 1 and self.vline(x, lx):
            return DPP_RED
        return None

    def rear_decor(self, v, k):
        if k == 8 and -0.95 <= v < -0.70:
            return DPP_RED                # rear DPP logo, left of the text
        if k == 8 and -0.60 <= v < 0.55:
            return Sh(WHITE_SEAM)         # the text as a light grey line
        return None


class TourismoNew(Tourismo):
    """Tourismo RHD (M/2, 2024 facelift), DPP #8002 II (2025): 12.14 x 2.55 x
    3.71 m, 2 axles; front door + middle door ahead of the rear axle. The
    glazing band's lower edge sweeps down towards the front door."""
    real_len = 12.14
    axles = (2.66, 8.74)
    DOOR_M = (7.05, 7.90)
    AC = (1.2, 3.6)

    def pillars(self, right):
        if right:
            return (1.60, 3.55, 5.40, 8.00, 10.00)
        return (3.55, 5.40, 7.30, 9.20, 10.90)

    def seams(self, right):
        return (3.2, 5.3, 9.6) if right else (3.2, 5.3, 7.4, 9.6)

    def band_bottom(self, x, right):
        z = self.zr(self.R_BAND0)
        x0, x1 = 1.40, 4.40        # sweep from the door back to here
        if x < x0:
            return self.zr(5 if right else 6)
        if x < x1:
            t = (x - x0) / (x1 - x0)
            zs = self.zr(5 if right else 6)
            return lerp(zs, z, t * t * (3 - 2 * t))
        return z

    def decor(self, x, k, right):
        L = self.real_len
        if self.liv == "dppcervena":
            # gold skyline line: runs mid-height from the rear towards the
            # middle, rising into the Prague skyline peaks near the rear
            if right:
                seg = (4.0, L - 0.6)
            else:
                seg = (0.6 + 1.0, L - 4.0)
            if inside(x, *seg):
                base = 3
                if k == base:
                    return GOLD
                # skyline peaks (Hradčany / towers) near the rear
                peaks = (L - 3.3, L - 2.9, L - 2.3) if right else (3.2, 3.6, 4.2)
                for i, p in enumerate(peaks):
                    if self.vline(x, p) and base < k <= base + (2 if i != 1 else 3):
                        return GOLD
            # 'Praha' gold script at the rear upper lockers
            px = (L - 3.9, L - 2.6) if right else (1.5, 2.8)
            if k == 6 and inside(x, *px):
                return GOLD
            # white 'dpp' logo mid-side
            lx = (4.5, 5.3) if right else (5.0, 5.8)
            if k in (5, 6) and inside(x, *lx):
                return (0xF6, 0xF6, 0xF4)
            return None
        return None

    def front(self, v, z):
        k = self.row(z)
        if self.liv == "dppcervena" and k == 3 and 0.75 <= v < 1.15:
            return (0xF6, 0xF6, 0xF4)              # white dpp logo on the front
        return super().front(v, z)

    def rear_decor(self, v, k):
        if self.liv == "dppcervena" and k == 8 and -0.45 <= v < 0.45:
            return (0xF6, 0xF6, 0xF4)              # white dpp logo on the rear
        return None

    def mirror_col(self):
        return TR_RED_SEAM if self.liv == "dppcervena" else MIRROR


# ====================================================================== jobs
def row_for(cls, livery):
    m = cls(livery)
    L, boxes, lines = m.model()
    cal = calibration(m)
    return [shift_tile(render(boxes, L, d, lines), *cal[d]) for d in DIRS]


FAMDIR = os.path.join(REPO, "vehicle-bus", "dpp")
JOBS = {
    "crossway_pro_10_8m": [("bila", CrosswayPro108)],
    "crossway_pro_12m": [("bila", CrosswayPro12)],
    "tourismo_15_rhd": [("bila", Tourismo15)],
    "tourismo_rhd": [("dppcervena", TourismoNew)],
}


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    for fam in (argv or list(JOBS)):
        for livery, cls in JOBS[fam]:
            rows = [row_for(cls, livery)]
            dst = os.path.join(FAMDIR, fam, "sprites", f"{livery}.png")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            save_rows(rows, dst)
            print("wrote", os.path.relpath(dst, REPO))
            if prev:
                os.makedirs(prev, exist_ok=True)
                preview(rows, os.path.join(prev, f"{fam}_{livery}.png"), z=5)


if __name__ == "__main__":
    main(sys.argv[1:])
