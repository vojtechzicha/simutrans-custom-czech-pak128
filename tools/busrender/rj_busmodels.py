"""RegioJet coaches (Irizar i8 15M, Irizar PB 15.37, Setra S 531 DT) as box
models for the pak128 road projection (rj_vrender.py).

Scale (like native pak128.cs buses, which draw a 12 m bus ~13.5 m long and
~3.1 m wide at true height): lengths x SL = 1.08, drawn width 3.1 m, heights
true (4.2 px/m). Every livery band is a whole number of pixel rows (PXZ)
counted from the body bottom Z0, so each band covers exactly that many rows in
every view. Positions in the specs are REAL metres from the front (x); u (the
renderer's coordinate, 0 = rear) = L - x * SL.

Sides: +v = right-hand (door) side, -v = left (driver) side. On the right side
screen-left is the vehicle's rear, on the left side its front, so lettering is
laid out from the rear on the right side and from the front on the left side
(it reads left to right on both).
"""
import math
from rj_vrender import Box, Sh, PXZ, pxu, FWD, AX, AY
import rj_vrender as VR

SL = 1.08
W2 = 1.55

# ------------------------------------------------------------------ palette
YEL = (0xFF, 0xB6, 0x12)          # RegioJet yellow (as on the rail coaches)
YEL_ROOF = (0xFF, 0xC6, 0x30)     # roofs (tops are not shaded)
YEL_DK = (0xD8, 0x96, 0x00)       # panel seams, mirror arms
YEL_HATCH = (0xE6, 0xA4, 0x14)    # roof hatches
YEL_COVER = (0xE8, 0xA6, 0x10)    # Setra wheel covers
YEL_SEAM = (0xDE, 0x9A, 0x08)     # luggage-bay door seams
GLASS = (0x4D, 0x4D, 0x4D)        # special 28: lit at night when loaded
GLASS_HI = (0x57, 0x65, 0x6F)     # special 16: lit, lighter top row
SCREEN = (0x2A, 0x34, 0x3D)       # driver's glass, never lit
SCREEN_HI = (0x4F, 0x62, 0x72)
BLACK = (0x14, 0x14, 0x16)        # black trim / masks (not glass)
PILLAR = (0x1C, 0x1C, 0x1E)
UNDER = (0x1A, 0x1A, 0x1A)
TIRE = (0x1A, 0x1A, 0x1A)
ARCH = (0x0C, 0x0C, 0x0C)
HUB = (0x8C, 0x90, 0x95)
CHROME = (0xC4, 0xC8, 0xCC)
CHROME_LINE = (0xC8, 0xBE, 0xA4)  # Irizar side chrome line seen against yellow
SILVER = (0xB8, 0xBC, 0xC1)       # grey luggage doors (ex-DB i8), never a special grey
SILVER_DK = (0x98, 0x9C, 0xA1)
GRILLE = (0x3A, 0x3A, 0x3C)
RED = (0xE3, 0x34, 0x2F)          # "|| REGIO"
BLUE = (0x1F, 0x3A, 0x93)         # "JET"
WHITE = (0xF4, 0xF4, 0xF0)
PICTO = (0x8A, 0x5E, 0x08)        # dark outline pictograms on yellow
PLATE = (0xE8, 0xEA, 0xEC)
AMBER = (0xF0, 0xA0, 0x18)        # destination display LEDs (non-special)
HEAD = (0xFF, 0xFF, 0x53)         # special: headlight
TAIL = (0xFF, 0x21, 0x1D)         # special: tail light


def lerp(a, b, t):
    return a + (b - a) * t


class Coach:
    """Common geometry/texture helpers. Subclasses set the specs and draw."""
    real_len = 15.0
    skibox = 0.0                  # real depth of a rear luggage box
    Z0 = 0.30
    axles = (3.0, 10.4, 11.8)
    wheel_r = 0.52
    arch_rows = 4
    hub_color = HUB
    hub_r = 0.18
    arch_extra = 0.10

    def __init__(self, livery):
        self.liv = livery
        self.Lb = self.real_len * SL                  # drawn body length
        self.Lk = self.skibox * SL                    # drawn skibox depth
        self.L = self.Lb + self.Lk                    # u = 0 .. L (skibox at the rear)

    # ---------------------------------------------------------- coordinates
    def U(self, x):
        return self.L - x * SL

    def X(self, u):
        return (self.L - u) / SL

    def zr(self, k):
        """z of the bottom of pixel row k (row 0 = the lowest body row)."""
        return self.Z0 + k * PXZ

    def row(self, z):
        return int(math.floor((z - self.Z0) / PXZ + 1e-6))

    def pw(self):
        """real metres along the body per screen column (current view)."""
        return pxu() / SL

    def colidx(self, x, x0, backwards=False):
        """column index of real position x counted from x0 (towards the rear,
        or towards the front if backwards)."""
        d = (x0 - x) if backwards else (x - x0)
        return int(math.floor(d / self.pw() + 1e-6))

    def vline(self, x, xl):
        """1-px vertical line at real position xl (exactly one column)."""
        return xl <= x < xl + self.pw()

    # ---------------------------------------------------------- wheels
    def wheel(self, u, z):
        """wheel arch colour at (u, z) on a side face, or None."""
        top = self.zr(self.arch_rows)
        if z >= top:
            return None
        R = self.wheel_r
        for a in self.axles:
            au = self.U(a)
            du = u - au
            if abs(du) < R + self.arch_extra:
                r = math.hypot(du, z - R)
                if r < self.hub_r:
                    return self.hub(z)
                if r < R:
                    return TIRE
                return ARCH
        return None

    def hub(self, z):
        return self.hub_color

    # ---------------------------------------------------------- materials
    def mat_body(self, face, u, v, z):
        if face == "+v":
            return self.side(u, z, right=True)
        if face == "-v":
            return self.side(u, z, right=False)
        if face == "+u":
            return self.front(v, z)
        if face == "-u":
            return self.rear(v, z)
        if face == "+z":
            return self.roof(u, v)
        return UNDER

    def mat_tire(self, face, u, v, z):
        if face in ("+v", "-v"):
            w = self.wheel(u, z)
            return w if w is not None and w != ARCH else TIRE
        return TIRE

    @staticmethod
    def const(c):
        return lambda face, u, v, z: c

    def pv(self):
        """lateral metres per screen column on a front/rear face (current view)."""
        fx, fy = FWD[VR.VIEW_D]
        rx, ry = -fy, fx
        per = abs(AX * (rx - ry))
        return 1.0 / per if per > 1e-6 else 1e9


# ====================================================================== i8
class IrizarI8(Coach):
    """Irizar i8 15M (Scania K450 EB 6x2*4 NI / Volvo B11R), 14.98 x 2.55 x 3.98 m.

    Positions from the #271 / #315 left profiles and #291 / #321 right 3/4
    views (perspective-corrected): front axle 3.05 m, drive 10.5, tag 11.9;
    front door behind the front corner, a narrow middle door just ahead of
    the drive axle (right side); big first side window whose lower edge sweeps
    down towards the front; window band 2.48-3.58 m; roof cap raised over the
    front 4 m."""
    real_len = 14.98
    Z0 = 0.30
    axles = (3.05, 10.50, 11.90)
    # rows from Z0: 0-5 lockers, 6-8 logo zone, 9-13 window band, 14 top
    R_BAND0, R_BAND1 = 9, 14          # band = rows 9..13
    R_TOP = 15                        # side wall top = zr(15) = 3.87 m
    ROOF = 3.98
    BIG_R = ((0.85, 1.36), (4.20, 2.44))   # right side big window lower edge (x, z)
    BIG_L = ((0.75, 1.50), (3.70, 2.44))   # left side
    BAND_R = (4.40, 14.62)
    BAND_L = (3.95, 14.62)
    PILLARS = (5.80, 7.00, 9.25, 11.46, 12.75)
    DOOR_F = (0.95, 1.95)
    DOOR_M = (8.95, 9.71)
    PICTO_X = (5.00, 0.50, 6)         # first, spacing, count
    LOGO_R = (10.30, 12.60)           # (front end, rear end) real x
    LOGO_L = (10.40, 12.70)
    GRILLE_X = (13.84, 14.60)
    FUN = (1.90, 3.30)                # Fun&Relax sticker on the big window
    R_CHROME = 6                      # thin chrome line at 1.7 m (row 6)
    SEAMS_L = (4.45, 7.00, 8.95, 9.71, 12.75)
    SEAMS_R = (4.45, 7.00, 12.75)

    def __init__(self, livery):
        super().__init__(livery)
        self.lockers = livery == "zlutostribrna"
        if self.lockers:
            self.LOGO_R = (11.40, 13.70)
            self.LOGO_L = (11.50, 13.80)

    # ---------------------------------------------------------- sides
    def big_edge(self, x, right):
        (x0, z0), (x1, z1) = self.BIG_R if right else self.BIG_L
        t = min(1.0, max(0.0, (x - x0) / (x1 - x0)))
        return lerp(z0, z1, t)

    def side(self, u, z, right):
        x = self.X(u)
        k = self.row(z)
        band0, band1 = self.zr(self.R_BAND0), self.zr(self.R_BAND1)
        w = self.wheel(u, z)
        if w is not None:
            return w
        # --- glazing ---------------------------------------------------
        bx0, bx1 = self.BAND_R if right else self.BAND_L
        big_x1 = (self.BIG_R if right else self.BIG_L)[1][0]
        if band0 <= z < band1:
            top = k == self.R_BAND1 - 1
            if x < 0.30:
                return SCREEN                                      # windscreen wrap
            if x < big_x1:
                if not right and x < 1.70:
                    return SCREEN_HI if top else SCREEN            # driver's window
                if self.fun(x, k):
                    return self.fun(x, k)
                return GLASS_HI if top else GLASS
            if x < bx0:
                return PILLAR                                      # pillar after the big window
            if x < bx1:
                for p in self.PILLARS:
                    if self.vline(x, p):
                        return PILLAR
                return GLASS_HI if top else GLASS
            return Sh(YEL)
        if z >= band1:
            return Sh(YEL)
        # below the band: big window sweep, doors
        if x < big_x1 and z >= self.big_edge(x, right) and z >= self.zr(4):
            if x < 0.30:
                return SCREEN
            if not right and x < 1.70:
                return SCREEN
            return GLASS
        if x < 0.30 and z >= self.zr(4):
            return SCREEN
        if right:
            d = self.door(x, z)
            if d is not None:
                return d
        # --- engine grille at the rear corner --------------------------
        g0, g1 = self.GRILLE_X
        if g0 <= x < g1 and 1 <= k <= 4:
            return GRILLE if k % 2 == 1 else Sh(SILVER_DK if self.lockers else YEL_DK)
        # --- Irizar chrome line along the locker tops -------------------
        if k == self.R_CHROME and x < self.real_len - 0.25:
            (ex0, ez0), (ex1, ez1) = self.BIG_R if right else self.BIG_L
            zc = self.zr(k)
            start = ex0 + (zc - ez0) / (ez1 - ez0) * (ex1 - ex0)
            if x >= start and not (self.GRILLE_X[0] <= x < self.GRILLE_X[1]):
                return Sh(CHROME_LINE)
        # --- luggage-bay door seams ------------------------------------
        if k < self.R_CHROME:
            for p in (self.SEAMS_R if right else self.SEAMS_L):
                if self.vline(x, p):
                    grey = self.lockers and x >= 6.48 and not (9.30 <= x < 12.60 and k >= 4)
                    return Sh(SILVER_DK if grey else YEL_SEAM)
        # --- lettering zone rows 7-8 -----------------------------------
        if k in (7, 8):
            c = self.logo(x, k, right)
            if c is not None:
                return c
            c = self.pictos(x, k)
            if c is not None:
                return c
        # --- lockers ---------------------------------------------------
        if self.lockers and k <= 5 and x >= 6.48:
            if 9.30 <= x < 12.60 and k >= 4:
                return Sh(YEL)                 # yellow strip over the axles
            return Sh(SILVER)
        return Sh(YEL)

    def door(self, x, z):
        """right-side doors: framed leaves from the floor up to the glass."""
        for (d0, d1), glass_z in ((self.DOOR_F, None), (self.DOOR_M, self.zr(5))):
            if d0 <= x < d1:
                edge = self.vline(x, d0) or (d1 - self.pw() <= x < d1)
                if glass_z is None:
                    top = self.big_edge(x, True)
                    if edge and z < top:
                        return BLACK
                    return None
                if z >= glass_z:
                    return BLACK if edge else GLASS
                if edge:
                    return BLACK
                if self.lockers and x >= 6.48:
                    return Sh(SILVER)
                return Sh(YEL)
        return None

    def fun(self, x, k):
        """Fun&Relax sticker: white word with a red '&' on the big window
        (not on the ex-DB batch)."""
        a, b = self.FUN
        if k == 12 and a <= x < b and not self.lockers:
            mid = (a + b) / 2
            if self.vline(x, mid):
                return RED
            return WHITE
        return None

    def logo(self, x, k, right):
        front, rear = self.LOGO_R if right else self.LOGO_L
        if not (front <= x < rear):
            return None
        # reading start: the rear end on the right side, the front end on the left
        c = self.colidx(x, rear, backwards=True) if right else self.colidx(x, front)
        n = max(6, int(round((rear - front) / self.pw())))
        if c in (0, 1):
            return RED                          # the two slanted bars, 2 rows tall
        if k != 7 or c == 2:
            return None
        rest = n - 3
        return RED if c - 3 < round(rest * 0.55) else BLUE

    def pictos(self, x, k):
        x0, dx, n = self.PICTO_X
        if self.lockers:
            # ex-DB batch: four white pictograms, 2 rows tall
            for i in range(4):
                if self.vline(x, 4.30 + i * 0.95):
                    return WHITE
            return None
        if k != 7:
            return None
        for i in range(n):
            if self.vline(x, x0 + i * dx):
                return PICTO
        return None

    # ---------------------------------------------------------- ends
    def front(self, v, z):
        av = abs(v)
        k = self.row(z)
        if z >= self.zr(self.R_TOP) or k >= 14:
            return Sh(YEL)                       # roof cap
        if k >= 5:
            if av > W2 - 0.06:
                return BLACK
            return SCREEN_HI if k == 13 else SCREEN
        if k == 4:
            return BLACK                         # black band with the "Irizar" badge
        if k == 3:
            # chrome V converging under the badge
            return Sh(CHROME) if av < 0.55 else Sh(YEL)
        if k == 2:
            if av > W2 - 0.55:
                return HEAD                      # LED headlight strips
            return Sh(CHROME) if 0.55 <= av < 0.9 else Sh(YEL)
        if k == 1:
            return PLATE if av < 0.26 else Sh(YEL)
        return Sh(YEL)

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        if 10 <= k <= 13 and av < W2 - 0.30:
            return GLASS_HI if k == 13 else GLASS
        if 2 <= k <= 6 and av > W2 - 0.26:
            return TAIL
        if k in (6, 7) and av < 0.75:
            return GRILLE if k == 7 or av < 0.45 else Sh(YEL)   # the chevron vents
        if k == 1:
            return PLATE if av < 0.26 else GRILLE if av > W2 - 0.5 else Sh(YEL)
        return Sh(YEL)

    HATCHES = (4.6, 10.6)

    def roof(self, u, v):
        x = self.X(u)
        for h in self.HATCHES:
            if h <= x < h + 0.75 and abs(v) < 0.40:
                return YEL_HATCH                 # roof escape hatches
        return YEL_ROOF

    # ---------------------------------------------------------- geometry
    def model(self):
        L = self.L
        ztop = self.zr(self.R_TOP)
        B = self.mat_body
        U = self.U
        boxes = [
            Box(U(14.90), U(0.10), -W2, W2, self.Z0, ztop, B),
            Box(U(0.10), U(0.0), -W2 + 0.07, W2 - 0.07, self.Z0, ztop, B),       # front face
            Box(U(14.98), U(14.90), -W2 + 0.07, W2 - 0.07, self.Z0, ztop, B),    # rear face
            Box(U(14.70), U(0.30), -W2 + 0.16, W2 - 0.16, ztop, self.ROOF, B),   # roof
            Box(U(14.3), U(0.8), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
        ]
        for a in self.axles:
            boxes.append(Box(U(a) - 0.5, U(a) + 0.5, -W2 + 0.07, W2 - 0.07, 0.0, self.Z0 + 0.01, self.mat_tire))
        return L, boxes, self.mirrors(3.62, 2.65)

    def mirrors(self, z_arm, z_head, col=YEL_DK):
        """rabbit-ear mirrors: arm forward and out from the roof cap, head hanging down."""
        L = self.L
        lines = []
        for s in (-1, 1):
            p0 = (L - 0.25, s * (W2 - 0.20), z_arm + 0.15)
            p1 = (L + 0.40, s * (W2 + 0.18), z_arm)
            p2 = (L + 0.45, s * (W2 + 0.22), z_head)
            lines.append((p0, p1, col))
            lines.append((p1, p2, col))
        return lines


# ====================================================================== PB
class IrizarPB(IrizarI8):
    """Irizar PB 15.37 (Scania K-series 6x2*4 / Volvo), 15.0 x 2.55 x 3.70 m.

    Lower and rounder than the i8: window band 2.43-3.36 m, big curved
    windscreen under a body-coloured 'eyebrow', straight band, rounded roof."""
    real_len = 15.0
    Z0 = 0.30
    axles = (3.00, 10.35, 11.75)
    # rows: 0-4 lockers, 5-8 logo zone, 9-12 band, 13 top
    R_BAND0, R_BAND1 = 9, 13
    R_TOP = 14                        # zr(14) = 3.63 m
    ROOF = 3.70
    BIG_R = ((0.90, 1.30), (3.85, 2.44))
    BIG_L = ((0.80, 1.45), (3.70, 2.44))
    BAND_R = (4.05, 14.55)
    BAND_L = (3.90, 14.55)
    PILLARS = (5.55, 7.20, 8.85, 10.50, 12.15, 13.60)
    DOOR_F = (0.95, 1.90)
    DOOR_M = (8.80, 9.55)
    PICTO_X = (4.80, 0.50, 6)
    LOGO_R = (10.40, 12.70)
    LOGO_L = (10.40, 12.70)
    GRILLE_X = (13.95, 14.65)
    FUN = (1.90, 3.20)
    R_CHROME = 5                      # chrome line at 1.58 m
    SEAMS_L = (4.30, 6.40, 8.70, 12.60)
    SEAMS_R = (4.30, 6.40, 12.60)

    def __init__(self, livery):
        Coach.__init__(self, livery)
        self.lockers = False

    def fun(self, x, k):
        a, b = self.FUN
        if k == 11 and a <= x < b:
            return RED if self.vline(x, (a + b) / 2) else WHITE
        return None

    def front(self, v, z):
        """big curved windscreen 1.0-3.15 m under a tall yellow 'eyebrow' cap
        (#228, #242), headlight clusters low at the corners, black grille."""
        av = abs(v)
        k = self.row(z)
        if k >= 12:
            return Sh(YEL)                       # eyebrow roof cap
        if k >= 3:
            if av > W2 - 0.08:
                return BLACK
            return SCREEN_HI if k == 11 else SCREEN
        if k == 2:
            if av > W2 - 0.50:
                return HEAD
            return BLACK if av < 0.80 else Sh(YEL)    # grille with the Irizar badge
        if k == 1:
            return PLATE if av < 0.26 else Sh(YEL)
        return Sh(YEL)

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        if 10 <= k <= 12 and av < W2 - 0.35:
            return GLASS_HI if k == 12 else GLASS
        if 2 <= k <= 5 and av > W2 - 0.26:
            return TAIL
        if k in (6, 7) and av < 0.70:
            return GRILLE if k == 7 else Sh(YEL)
        if k == 1:
            return PLATE if av < 0.26 else Sh(YEL)
        return Sh(YEL)

    def model(self):
        L = self.L
        ztop = self.zr(self.R_TOP)
        B = self.mat_body
        U = self.U
        boxes = [
            Box(U(14.90), U(0.12), -W2, W2, self.Z0, ztop, B),
            Box(U(0.12), U(0.0), -W2 + 0.09, W2 - 0.09, self.Z0, ztop, B),
            Box(U(15.0), U(14.90), -W2 + 0.09, W2 - 0.09, self.Z0, ztop, B),
            Box(U(14.75), U(0.25), -W2 + 0.22, W2 - 0.22, ztop, self.ROOF, B),
            Box(U(14.3), U(0.8), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
        ]
        for a in self.axles:
            boxes.append(Box(U(a) - 0.5, U(a) + 0.5, -W2 + 0.07, W2 - 0.07, 0.0, self.Z0 + 0.01, self.mat_tire))
        return L, boxes, self.mirrors(3.42, 2.30)


# ====================================================================== Setra
class SetraS531DT(Coach):
    """Setra S 531 DT, 14.0 m (+ rear skibox) x 2.55 x 4.00 m, double-decker.

    From the #340 left profile (perspective-corrected): front axle 2.69 m,
    drive 9.52, tag 10.87. Left side: all-black front 2.37 m, yellow arrow
    panel between the decks 2.37-8.62 m (pointed rear end, white pictograms),
    lower-deck glazing to 7.72 m then a diagonal black sweep up to the upper
    band at 9.88 m, grey 'SETRA' line under the glazing and along the sweep,
    full-length upper band with a silver roof-edge trim, big red '|| REGIOJET'
    between the decks at 10.43-12.73 m, yellow wheel covers."""
    real_len = 14.0
    skibox = 0.62
    Z0 = 0.28
    axles = (2.69, 9.52, 10.87)
    hub_r = 0.16
    # rows from Z0: 0-3 lower body, 4 grey line, 5-7 lower glass, 8-10 arrow
    # panel, 11-14 upper band, 15 silver trim  -> side top zr(16) = 4.09 m
    R_TOP = 16
    FRONT_BLACK = 2.37
    ARROW = (2.37, 8.62)
    LOWER_END = 7.72
    SWEEP_TOP = 9.88
    UPPER = (0.30, 13.62)
    TRIM = (1.25, 13.00)
    UP_PILLARS = (1.40, 3.50, 5.30, 7.10, 8.90, 10.10, 11.40)
    LOW_PILLARS = (3.50, 5.50)
    PICTOS = (3.70, 4.70, 5.70, 6.65, 7.55)
    LOGO = (10.43, 12.73)
    VENT = (12.70, 13.55)
    FUN = (1.36, 2.30)
    DOOR_F = (0.40, 1.40)
    DOOR_M = (7.95, 8.90)
    SEAMS = (3.47, 4.85, 6.25, 7.60, 11.50, 12.65)

    def hub(self, z):
        return YEL_COVER                          # yellow wheel covers (in the arch shade)

    def sweep_x(self, z):
        """x where the black ends (lower glazing + diagonal sweep) at height z."""
        z0 = self.zr(5); z1 = self.zr(11)
        if z < z0:
            return self.LOWER_END
        t = min(1.0, (z - z0) / (z1 - z0))
        return lerp(self.LOWER_END, self.SWEEP_TOP, t)

    def side(self, u, z, right):
        x = self.X(u)
        k = self.row(z)
        if x > self.real_len:                     # skibox side
            return Sh(YEL)
        w = self.wheel(u, z)
        if w is not None:
            return w
        if right:
            d = self.door(x, z, k)
            if d is not None:
                return d
        # rear corner
        if x >= self.UPPER[1]:
            if 6 <= k <= 7 and self.VENT[0] <= x < self.VENT[1]:
                return GRILLE
            return Sh(YEL)
        if k >= 16:
            return Sh(YEL)
        if k == 15:                               # silver roof-edge trim
            if self.TRIM[0] <= x < self.TRIM[1]:
                return Sh(CHROME)
            return BLACK if x < self.TRIM[0] else Sh(YEL)
        if k >= 11:                               # upper deck band
            if x < self.UPPER[0]:
                return SCREEN
            for p in self.UP_PILLARS:
                if self.vline(x, p):
                    return PILLAR
            return GLASS_HI if k == 14 else GLASS
        sx = self.sweep_x(self.zr(k) + 0.5 * PXZ)
        # arrow panel between the decks
        if 8 <= k <= 10:
            a0, a1 = self.ARROW
            # front end slanted, rear end pointed
            front_end = a0 + (10 - k) * 0.09 if not right else a0 + (10 - k) * 0.09
            rear_end = a1 - (0.0 if k == 9 else 0.25)
            if front_end <= x < rear_end:
                if k == 9:
                    for p in self.PICTOS:
                        if self.vline(x, p):
                            return WHITE
                return Sh(YEL)
            if x < sx:
                if k == 9 and self.FUN[0] <= x < self.FUN[1]:
                    return RED if self.vline(x, (self.FUN[0] + self.FUN[1]) / 2) else WHITE
                return BLACK
        # black region: lower glazing + sweep
        if 5 <= k <= 10 and x < sx:
            if k <= 7:
                if x < 0.45:
                    return SCREEN
                if not right and x < 1.36:
                    return SCREEN                 # driver's side window
                if x > sx - 0.35:
                    return BLACK
                for p in self.LOW_PILLARS:
                    if self.vline(x, p):
                        return PILLAR
                return GLASS
            return BLACK
        # grey line under the black (and along the sweep)
        if k == 4 and x < self.LOWER_END + 0.2:
            return Sh(CHROME) if x >= 1.36 else BLACK
        if 5 <= k <= 10 and sx <= x < sx + max(self.pw(), 0.20) and k < 11:
            return Sh(CHROME)
        # big logo between the decks, rear half
        if k in (8, 9, 10):
            c = self.logo(x, k, right)
            if c is not None:
                return c
        if 6 <= k <= 7 and self.VENT[0] <= x < self.VENT[1]:
            return GRILLE
        if k <= 3:
            for p in self.SEAMS:
                if self.vline(x, p):
                    return Sh(YEL_SEAM)
        return Sh(YEL)

    def door(self, x, z, k):
        for (d0, d1), top in ((self.DOOR_F, 10), (self.DOOR_M, 9)):
            if d0 <= x < d1:
                edge = self.vline(x, d0) or (d1 - self.pw() <= x < d1)
                if k > top:
                    return None
                if edge:
                    return BLACK
                if k >= 1:
                    return GLASS
                return Sh(YEL)
        return None

    def logo(self, x, k, right):
        front, rear = self.LOGO
        if not (front <= x < rear):
            return None
        c = self.colidx(x, rear, backwards=True) if right else self.colidx(x, front)
        n = max(6, int(round((rear - front) / self.pw())))
        if c in (0, 1):
            return RED if k >= 8 else None
        if k == 8 or c == 2:
            return None
        rest = n - 3
        return RED if c - 3 < round(rest * 0.55) else BLUE

    def front(self, v, z):
        av = abs(v)
        k = self.row(z)
        if k >= 15:
            return BLACK
        if k >= 11:
            if av > W2 - 0.10:
                return BLACK
            return GLASS_HI if k == 14 else GLASS         # upper deck: passenger glass
        if k == 10:
            return AMBER if (av < 0.85 and int((v + 2) / 0.24) % 3) else BLACK
        if k >= 4:
            if av > W2 - 0.08:
                return BLACK
            return SCREEN_HI if k == 9 else SCREEN
        if k == 3:
            return BLACK
        if k == 2:
            if av > W2 - 0.50:
                return HEAD
            return Sh(CHROME) if int((v + 2) / 0.22) % 2 else BLACK     # 'SETRA' letters
        if k == 1:
            return PLATE if av < 0.26 else Sh(YEL)
        return Sh(YEL)

    def rear(self, v, z):
        """rear face of the body (above/beside the skibox)."""
        av = abs(v)
        k = self.row(z)
        if 12 <= k <= 14 and av < W2 - 0.35:
            if k == 12 and av < 0.45:
                return Sh(CHROME)                        # SETRA badge
            return GLASS_HI if k == 14 else GLASS
        if 3 <= k <= 6 and av > W2 - 0.30:
            return TAIL
        if k == 10 and av < 0.55:
            return RED
        return Sh(YEL)

    def ski(self, face, u, v, z):
        if face == "-u":
            av = abs(v)
            k = self.row(z)
            if 2 <= k <= 3 and av > W2 - 0.26 - 0.30:
                return TAIL
            if k == 1 and av < 0.26:
                return PLATE
            return Sh(YEL)
        if face == "+z":
            return YEL_ROOF
        return Sh(YEL)

    def roof(self, u, v):
        x = self.X(u)
        if x < 0.55:
            return BLACK
        if abs(v) > W2 - 0.10 and self.TRIM[0] <= x < self.TRIM[1]:
            return CHROME
        return YEL_ROOF

    def model(self):
        L = self.L
        ztop = self.zr(self.R_TOP)
        B = self.mat_body
        U = self.U
        boxes = [
            Box(U(13.92), U(0.10), -W2, W2, self.Z0, ztop, B),
            Box(U(0.10), U(0.0), -W2 + 0.08, W2 - 0.08, self.Z0, ztop, B),
            Box(U(14.0), U(13.92), -W2 + 0.08, W2 - 0.08, self.Z0, ztop, B),
            Box(0.0, U(14.0), -W2 + 0.26, W2 - 0.26, self.zr(1), self.zr(10), self.ski),   # skibox
            Box(U(13.5), U(0.8), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
        ]
        for a in self.axles:
            boxes.append(Box(U(a) - 0.5, U(a) + 0.5, -W2 + 0.07, W2 - 0.07, 0.0, self.Z0 + 0.01, self.mat_tire))
        lines = []
        for s in (-1, 1):
            p0 = (L - 0.15, s * (W2 - 0.15), 2.95)
            p1 = (L + 0.45, s * (W2 + 0.20), 2.85)
            p2 = (L + 0.50, s * (W2 + 0.24), 2.15)
            lines += [(p0, p1, YEL_DK), (p1, p2, YEL_DK)]
        return L, boxes, lines


MODELS = {"irizar_i8": IrizarI8, "irizar_pb": IrizarPB, "setra_s531dt": SetraS531DT}
