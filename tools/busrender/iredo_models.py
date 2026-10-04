"""Regional (IREDO, Královéhradecký kraj) buses as box models for the pak128
road projection, on the RegioJet coach pipeline (rj_vrender raycaster,
rj_busmodels.Coach helpers, rj_buses.calibration, rj_lane placement), so they
share the scale of the VZ-RegioJet and DPP Crossway PRO renders: lengths x
1.08, drawn width 3.1 m, true heights at 4.2 px/m, every livery band a whole
number of pixel rows counted from the body bottom Z0.

A bus is one body class (geometry, glazing, doors, ends) and one Livery
(paint and decals). The body asks the livery for the colour of every painted
pixel, so one livery paints every body and one body takes every livery.

Positions are REAL metres from the front (x). +v = right-hand (door) side,
-v = left (driver) side; on the right side screen-left is the rear, on the
left side screen-left is the front. Pixel rows k count up from Z0 (0.238 m
each): k = 0 is the lowest body row.

Pixel decals (Transdev figure, CDS lettering) are laid out in screen columns
(Coach.colidx), so they stay crisp in every view and read as seen in both
side views.
"""
import math

from rj_vrender import Box, Sh, PXZ
import rj_busmodels as C
from rj_busmodels import Coach, lerp, W2

# ------------------------------------------------------------------ palette
GLASS = C.GLASS                   # special 28, lit when loaded
GLASS_HI = C.GLASS_HI             # special 16
SCREEN = C.SCREEN                 # driver's glass, never lit
SCREEN_HI = C.SCREEN_HI
BLACK = C.BLACK
PILLAR = (0x26, 0x27, 0x29)
UNDER = C.UNDER
PLATE = C.PLATE
HEAD = C.HEAD
TAIL = C.TAIL
CHROME = C.CHROME
MIRROR = (0x22, 0x22, 0x24)
MARKER = (0xF0, 0x8A, 0x20)       # amber side marker lamps (plain colour)
GRILLE = (0x6A, 0x6C, 0x6E)
GRILLE_DK = (0x44, 0x46, 0x48)
GREY_LINE = (0xA8, 0xAA, 0xAC)    # Iveco front bar
SCREEN_L = (0x4C, 0x5A, 0x66)     # lighter driver's / windscreen glass (SOR), never lit
SCREEN_LHI = (0x68, 0x7A, 0x8A)
LED = (0xF0, 0xA0, 0x18)          # amber destination LEDs (plain colour)
KHK_PANEL = (0xE4, 0xE5, 0xE8)    # the KHK sticker panel over the rear window
KHK_RED = (0xD6, 0x22, 0x2A)
KHK_BLUE = (0x1E, 0x4F, 0xA0)


def inside(x, a, b):
    return a <= x < b


# ====================================================================== liveries
class Livery:
    """Plain white (BusLine KHK, KAD and every other plain white bus)."""
    slug = "bila"
    body = (0xF2, 0xF2, 0xF0)
    roof = (0xEE, 0xEE, 0xEB)
    ac = (0xEC, 0xEC, 0xE9)
    seam = (0xDA, 0xDB, 0xD9)
    bumper = None                 # colour of the lowest front/rear rows, None = body

    def side(self, bus, x, k, right):
        """decal colour at real x (from the front), row k; None = body paint."""
        return None

    def front(self, bus, v, k):
        return None

    def rear(self, bus, v, k):
        return None

    def ac_side(self):
        return Sh(tuple(c * 0.93 for c in self.ac))


class Transdev(Livery):
    """Transdev Čechy (ex-AUDIS BUS): white with the big red Transdev figure
    on each side just behind the front axle, small red mark on the front."""
    slug = "transdev"
    RED = (0xD8, 0x1E, 0x2C)
    # the figure as seen, top row first: hook stroke on the left, dot head
    # top right, the body/leg stroke running down to the right
    FIG = ["..##.#",
           ".#....",
           "#..##.",
           "#.##..",
           "#.#...",
           "#..#..",
           "#...#."]

    def side(self, bus, x, k, right):
        k_top = bus.R_BAND0 - 1                    # just under the glazing
        r = k_top - k
        if not 0 <= r < len(self.FIG):
            return None
        x0 = bus.axles[0] + bus.FIG_DX            # left edge as seen
        if right:
            # screen-left is the rear: start at the rear end of the figure
            xs = x0 + 1.25
            c = bus.colidx(x, xs, backwards=True)
        else:
            c = bus.colidx(x, x0)
        row = self.FIG[r]
        if 0 <= c < len(row) and row[c] == "#":
            return self.RED
        return None

    def front(self, bus, v, k):
        if k == 3 and 0.30 <= v < 0.55:
            return self.RED
        return None


class CDS(Livery):
    """CDS Náchod: all-over yellow, big red CDS and black NÁCHOD between the
    axles under the windows."""
    slug = "cds"
    body = (0xF6, 0xC4, 0x00)
    roof = (0xF8, 0xCC, 0x10)
    ac = (0xF8, 0xCC, 0x10)
    seam = (0xD8, 0xA8, 0x00)
    RED = (0xD8, 0x1E, 0x24)
    INK = (0x22, 0x22, 0x24)
    # 4-row bold caps, top row first
    TXT = ["###.##...##",
           "#...#.#.#..",
           "#...#.#...#",
           "###.##..##."]

    def side(self, bus, x, k, right):
        r = (bus.R_BAND0 - 2) - k
        if not 0 <= r < len(self.TXT):
            return None
        mid = (bus.axles[0] + bus.axles[1]) / 2
        n = len(self.TXT[0])
        half = n * bus.pw() / 2
        if right:
            c = bus.colidx(x, mid + half, backwards=True)
        else:
            c = bus.colidx(x, mid - half)
        if 0 <= c < n and self.TXT[r][c] == "#":
            return self.RED
        return None

    def front(self, bus, v, k):
        if k == 3 and -0.35 <= v < 0.35:
            return self.RED
        return None


class PTransport(Livery):
    """P-transport Broumov: golden yellow-orange, red skirt, a red sweep
    rising from the front lower corner over the front half, a second sweep
    between the axles, two red pinstripes under the windows, red bumpers,
    red roof A/C pod."""
    slug = "ptransport"
    body = (0xF7, 0xB2, 0x14)
    roof = (0xF8, 0xBA, 0x22)
    ac = (0xD6, 0x22, 0x1C)
    seam = (0xD8, 0x94, 0x08)
    RED = (0xD6, 0x22, 0x1C)
    bumper = (0xD6, 0x22, 0x1C)

    def side(self, bus, x, k, right):
        L = bus.real_len
        b0 = bus.R_BAND0
        if k == b0 - 1:
            return self.RED                         # band under the windows
        if x < 0.22 * L and k == b0 - 2:
            return self.RED                         # ... widening at the front
        if x < 1.1 and k <= b0 - 2:
            return self.RED                         # front lower corner
        xs, xe = 0.12 * L, 0.74 * L
        if xs <= x < xe:                            # the lower sweep
            t = (x - xs) / (xe - xs)
            if k < 3.4 * t ** 1.3:
                return self.RED
        if x >= L - 0.40 and k <= 1:
            return self.RED                         # rear bumper corner
        return None

    def front(self, bus, v, k):
        if k <= 2:
            return self.RED
        return None

    def rear(self, bus, v, k):
        if k <= 1:
            return self.RED
        if k == bus.R_BAND0 - 1:
            return self.RED                         # the band continues across the rear
        return None


class DvurKralove(Livery):
    """MHD Dvůr Králové nad Labem (KAD): white with a green waist band and
    skirt and the town photo wrap between them, reduced to its colour fields
    front to rear: lions, the arcaded square (sky, red roofs, facades), the
    blown-glass baubles. Same palette and zones as khk_small.DvurKralove on
    the Dekstra LF 38."""
    slug = "dvurkralove"
    GREEN = (0x46, 0xAA, 0x3A)
    P = {"sky": (0x86, 0xAE, 0xD8), "facade": (0xD6, 0xB8, 0x86), "facade2": (0xE8, 0xD8, 0xB4),
         "roofs": (0xA4, 0x4C, 0x34), "bauble": (0x7A, 0x4E, 0x30), "bauble_hi": (0xC8, 0x9A, 0x48),
         "lion": (0xB8, 0x82, 0x44), "lion_dk": (0x6E, 0x4A, 0x28)}
    bumper = (0x46, 0xAA, 0x3A)

    def side(self, bus, x, k, right):
        b0 = bus.R_BAND0
        if k == b0 - 1 or k == 0:
            return self.GREEN
        u = x / bus.real_len
        if u < 0.30 or not 1 <= k < b0 - 1:
            return None
        r = (b0 - 2) - k                      # 0 = first photo row under the band
        n = b0 - 2
        d = (bus.colidx(x, 0.0) + k) % 2 == 0
        P = self.P
        if u < 0.50:
            return P["lion_dk"] if (r == 1 and d) or (r >= n - 1 and not d) else P["lion"]
        if u < 0.75:
            if r == 0:
                return P["sky"]
            if r == 1:
                return P["roofs"]
            return P["facade"] if d else P["facade2"]
        return P["bauble_hi"] if d and r % 2 else P["bauble"]

    def front(self, bus, v, k):
        if k == 0 or (k == 4 and abs(v) > 0.95):
            return self.GREEN
        return None

    def rear(self, bus, v, k):
        if k == 0 or k == bus.R_BAND0 - 1:
            return self.GREEN
        if 1 <= k < bus.R_BAND0 - 1 and k >= 3:
            return self.P["facade"] if int(v * 4) % 2 else self.P["sky"]
        return None


class BusLineGreen(Livery):
    """BusLine (legacy): all-over medium green, white BusLine swoosh."""
    slug = "buslinezelena"
    body = (0x3C, 0xA6, 0x3E)
    roof = (0x44, 0xAE, 0x46)
    ac = (0x44, 0xAE, 0x46)
    seam = (0x2E, 0x88, 0x30)
    WHITE = (0xF2, 0xF2, 0xF0)

    def side(self, bus, x, k, right):
        # white swoosh: a 1-row stripe rising gently towards the rear over
        # the rear half, under the windows
        L = bus.real_len
        if x >= 0.50 * L:
            t = (x - 0.50 * L) / (0.45 * L)
            if t <= 1.0 and k == int(round(bus.R_BAND0 - 3 + 2 * t)):
                return self.WHITE
        return None


class BusLineLime(BusLineGreen):
    """BusLine / ex-OverLine (legacy): all-over yellow-green."""
    slug = "buslinezlutozelena"
    body = (0xC2, 0xD8, 0x2C)
    roof = (0xCA, 0xDE, 0x38)
    ac = (0xCA, 0xDE, 0x38)
    seam = (0xA0, 0xB4, 0x20)
    WHITE = (0x5E, 0x8E, 0x2A)     # dark green BusLine swoosh on lime


LIVERIES = {c.slug: c for c in (Livery, Transdev, CDS, PTransport, DvurKralove, BusLineGreen, BusLineLime)}


# ====================================================================== body
class RegioBus(Coach):
    """Common two-axle regional bus. Subclasses set the specs:

    real_len, axles, DOORS = ((x0, x1, kind), ...) on the right side,
    kind 'le' (glazed to the floor, low entry) or 'hf' (high floor, glazing
    from the window line, painted lower panel); BAND = ((x0, x1, k0, k1), ...)
    glazing rows k0..k1-1 per stretch; R_TOP side-wall top row; ROOF_STEP
    (x, rows) a raised rear roof from x backwards; RUB a black rub-strip row
    (or None); AC (x0, x1) the roof A/C pod."""
    Z0 = 0.30
    wheel_r = 0.50
    arch_rows = 4
    R_BAND0 = 6                    # lowest glazing row (paint above it is the band)
    R_TOP = 12
    ROOF_STEP = None
    ROUND = 0.0                    # inset of the rounded corners / roof edges (m), 0 = boxy
    DOOR_RAISE = 0                 # rows the door glazing rises above the window band
    RUB = None
    AC = (2.4, 5.6)
    AC_H = 0.20
    FIG_DX = 0.55                  # Transdev figure: metres behind the front axle
    REAR_GLASS = (7, 10)           # rear window rows (k0, k1 inclusive)
    ENGINE_GRILLE = True
    KHK_STICKER = True             # the kraj sticker panel on the rear window (IREDO buses)

    def __init__(self, livery):
        self.lv = LIVERIES[livery]()
        super().__init__(livery)

    # ---------------------------------------------------------- helpers
    def paint(self, c):
        return Sh(c)

    def body_col(self, x, k, right):
        d = self.lv.side(self, x, k, right)
        if d is not None:
            return Sh(d)
        return Sh(self.lv.body)

    def top_row(self, x):
        """the side-wall top row at real x (raised rear roof)."""
        if self.ROOF_STEP and x >= self.ROOF_STEP[0]:
            return self.R_TOP + self.ROOF_STEP[1]
        return self.R_TOP

    def band_at(self, x):
        for x0, x1, k0, k1 in self.BAND:
            if x0 <= x < x1:
                return k0, k1
        return None

    GLASS_HI_ROWS = 1              # lighter (special 16) rows under the top frame
    HOPPER = False                 # top-hinged hopper windows: frame line in every other pane
    HATCHES = ()                   # roof hatch centres (real x)

    def glass(self, k, k1):
        if k == k1 - 1:
            return BLACK
        if k1 - 1 - self.GLASS_HI_ROWS <= k < k1 - 1:
            return GLASS_HI
        return GLASS

    def pane(self, x, right):
        """index of the window pane at x (counted from the front)."""
        return sum(1 for p in self.pillars(right) if p <= x)

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
        if k >= self.top_row(x):
            return Sh(self.lv.roof)
        band = self.band_at(x)
        if band and band[0] <= k < band[1]:
            b0, b1 = band
            if x < 0.14:
                return SCREEN                               # windscreen wrap
            if not right and x < 1.30:
                return SCREEN_HI if k == b1 - 1 else SCREEN  # driver's window
            if x >= L - 0.22:
                return self.body_col(x, k, right)           # rear corner post
            for p in self.pillars(right):
                if self.vline(x, p):
                    return PILLAR
            if self.HOPPER and k == b1 - 3 and self.pane(x, right) % 2 == 1:
                return BLACK
            return self.glass(k, b1)
        if x < 0.14 and k >= 4:
            return SCREEN
        if not right and x < 1.30 and band and k == band[0] - 1 and self.DRIVER_DIP:
            return SCREEN
        # decals first, then the body's own fittings on top
        d = self.lv.side(self, x, k, right)
        if d is not None:
            return Sh(d)
        if self.RUB is not None and k == self.RUB:
            return Sh(BLACK)
        if self.ENGINE_GRILLE and right and L - 1.20 <= x < L - 0.30 and 1 <= k <= 3:
            return Sh(GRILLE) if k % 2 else Sh(GRILLE_DK)
        if k == 1:
            for mx in self.markers():
                if self.vline(x, mx):
                    return MARKER
        if 1 <= k <= 3:
            for p in self.seams(right):
                if self.vline(x, p):
                    return Sh(self.lv.seam)
        return Sh(self.lv.body)

    DRIVER_DIP = False

    def markers(self):
        return (1.9, self.axles[0] + 1.6, self.axles[1] - 1.5, self.real_len - 0.45)

    def seams(self, right):
        return ()

    def door(self, x, k):
        for d0, d1, kind in self.DOORS:
            if not d0 <= x < d1:
                continue
            band = self.band_at(x) or (self.R_BAND0, self.R_TOP - 1)
            top = band[1] + self.DOOR_RAISE
            if k >= top:
                return None
            if k == top - 1 and self.DOOR_RAISE:
                return BLACK                               # door header
            if self.vline(x, d0) or (d1 - self.pw() <= x < d1):
                return BLACK
            if kind == "le":
                if k >= 1:
                    return self.glass(k, top) if k >= band[0] else GLASS
                return self.body_col(x, k, True)
            # high floor: glazing from the window line, painted panel below
            if k >= band[0] - 1:
                return self.glass(k, top)
            if k == 1:
                return SCREEN
            return self.body_col(x, k, True)
        return None

    # -------------------------------------------------------------- ends
    def front(self, v, z):
        k = self.row(z)
        av = abs(v)
        d = self.lv.front(self, v, k)
        return self.front_face(v, av, k, d)

    def front_face(self, v, av, k, d):
        raise NotImplementedError

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        g0, g1 = self.REAR_GLASS
        if g0 <= k <= g1 and av < W2 - 0.22 and not self.KHK_STICKER:
            return GLASS_HI if k == g1 else GLASS
        if g0 <= k <= g1 and av < W2 - 0.22:
            # the KHK sticker: a light panel over the upper rear window with
            # the red/blue chevron at the bus's left (viewer's right) and the
            # rear LED number on the other side
            if k >= g1 - 1:
                if k == g1 and 0.55 <= v < 0.95:
                    return KHK_RED
                if k == g1 - 1 and 0.55 <= v < 0.95:
                    return KHK_BLUE
                if -1.05 <= v < -0.65:
                    return LED if k == g1 else BLACK
                return KHK_PANEL
            return GLASS
        if k >= self.top_row(self.real_len - 0.1):
            return Sh(self.lv.roof)
        d = self.lv.rear(self, v, k)
        if d is not None:
            return Sh(d)
        if 1 <= k <= 3 and av > W2 - 0.22:
            return TAIL
        if k == 1 and av < 0.28:
            return PLATE
        if k == 0:
            if self.lv.bumper:
                return Sh(self.lv.bumper)
            return Sh(self.lv.seam) if av < 1.0 else Sh(self.lv.body)
        return Sh(self.lv.body)

    def roof(self, u, v):
        x = self.X(u)
        for h in self.HATCHES:
            if abs(x - h) < 0.32 and abs(v) < 0.34:
                return (0x5C, 0x5E, 0x62)
        return self.lv.roof

    STEP_FACE = 0.80               # the raised roof's front face, darker than the roof

    def mat_step(self, face, u, v, z):
        """the raised rear roof: its sides continue the side walls, its front
        face is a shaded roof-colour wall with a dark gutter at its foot."""
        if face == "+u":
            if self.row(z) == self.R_TOP:
                return Sh(PILLAR)
            return Sh(tuple(c * self.STEP_FACE for c in self.lv.roof))
        if face == "-u":
            return self.rear(v, z)
        return self.mat_body(face, u, v, z)

    def ac(self, face, u, v, z):
        if face == "+z":
            return self.lv.ac
        return self.lv.ac_side()

    # -------------------------------------------------------------- geometry
    def model(self):
        L = self.L
        U = self.U
        rl = self.real_len
        ztop = self.zr(self.R_TOP)
        B = self.mat_body
        roof_z = ztop + 0.08
        r = self.ROUND
        if r:
            # rounded body: the end caps and the roof slab are inset, so the
            # corners and the roof edges read as curved
            c = r * 0.8
            boxes = [
                Box(U(rl - c), U(c), -W2, W2, self.Z0, ztop, B),
                Box(U(c), U(0.0), -W2 + r, W2 - r, self.Z0, ztop - PXZ, B),
                Box(U(c), U(0.0), -W2 + 2 * r, W2 - 2 * r, ztop - PXZ, ztop, B),
                Box(U(rl), U(rl - c), -W2 + r, W2 - r, self.Z0, ztop - PXZ, B),
                Box(U(rl), U(rl - c), -W2 + 2 * r, W2 - 2 * r, ztop - PXZ, ztop, B),
                Box(U(rl - c - 0.10), U(c + 0.10), -W2 + r, W2 - r, ztop, roof_z, B),
                Box(U(rl - 0.5), U(0.5), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
            ]
        else:
            boxes = [
                Box(U(rl - 0.08), U(0.08), -W2, W2, self.Z0, ztop, B),
                Box(U(0.08), U(0.0), -W2 + 0.07, W2 - 0.07, self.Z0, ztop, B),
                Box(U(rl), U(rl - 0.08), -W2 + 0.07, W2 - 0.07, self.Z0, ztop, B),
                Box(U(rl - 0.10), U(0.10), -W2 + 0.03, W2 - 0.03, ztop, roof_z, B),
                Box(U(rl - 0.5), U(0.5), -W2 + 0.35, W2 - 0.35, 0.0, self.Z0, self.const(UNDER)),
            ]
        if self.ROOF_STEP:
            xs, n = self.ROOF_STEP
            zs = self.zr(self.R_TOP + n)
            ri = self.ROUND or 0.03
            boxes.append(Box(U(rl - (self.ROUND * 0.8 if self.ROUND else 0)), U(xs), -W2, W2, ztop, zs, self.mat_step))
            boxes.append(Box(U(rl - 0.10 - ri), U(xs + 0.10), -W2 + ri, W2 - ri, zs, zs + 0.08, B))
            roof_z = max(roof_z, zs)
        if self.AC:
            a0, a1 = self.AC
            boxes.append(Box(U(a1), U(a0), -0.95, 0.95, ztop + 0.08,
                             ztop + 0.08 + self.AC_H, self.ac))
        for a in self.axles:
            boxes.append(Box(U(a) - 0.5, U(a) + 0.5, -W2 + 0.07, W2 - 0.07, 0.0,
                             self.Z0 + 0.01, self.mat_tire))
        lines = []
        for s in (-1, 1):
            p0 = (L - 0.10, s * (W2 - 0.25), ztop - 0.12)
            p1 = (L + 0.30, s * (W2 + 0.12), ztop - 0.20)
            p2 = (L + 0.32, s * (W2 + 0.16), ztop - 0.85)
            lines += [(p0, p1, MIRROR), (p1, p2, MIRROR)]
        return L, boxes, lines


# ---------------------------------------------------------------------- Crossway
class CrosswayFace:
    """Iveco Crossway (2013+) front: deep windscreen with the destination
    display on top, body-coloured mask, grey IVECO bar, low headlights."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av < W2 - 0.30:
                return LED if av < 0.9 else BLACK
            return BLACK
        if k >= 5:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 4:
            return BLACK if av > W2 - 0.07 else Sh(d or self.lv.body)
        if d is not None:
            return Sh(d)
        if k == 3:
            return Sh(GREY_LINE) if av < 1.05 else Sh(self.lv.body)
        if k == 2:
            if av > W2 - 0.48:
                return HEAD
            return Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class CrosswayLELine(CrosswayFace, RegioBus):
    """Iveco Crossway LE LINE 12M (2013+ front): low-entry interurban, doors
    2-2-0 (double front door ahead of the front axle, double middle door
    between the axles), black glazing band 1.73-2.92 m, A/C over the front
    half of the roof."""
    real_len = 12.0
    axles = (2.65, 8.73)
    DOORS = ((0.32, 1.32, "le"), (5.10, 6.30, "le"))
    BAND = ((0.0, 12.0, 6, 11),)
    AC = (2.4, 5.9)
    FIG_DX = 0.55

    def pillars(self, right):
        if right:
            return (2.62, 4.05, 6.85, 8.15, 9.65, 11.0)
        return (2.62, 4.05, 5.55, 7.05, 8.55, 10.05)

    def seams(self, right):
        return (4.1, 9.9) if right else (1.5, 3.6, 5.5, 7.3, 9.9)


class CrosswayLELine108(CrosswayLELine):
    real_len = 10.8
    axles = (2.60, 7.70)
    DOORS = ((0.32, 1.32, "le"), (4.55, 5.75, "le"))
    BAND = ((0.0, 10.8, 6, 11),)
    AC = (2.3, 5.4)

    def pillars(self, right):
        if right:
            return (2.62, 4.0, 6.30, 7.70, 9.25)
        return (2.62, 4.05, 5.55, 7.05, 8.55, 9.95)


class CrosswayLELine145(CrosswayLELine):
    """14.5M: three axles (tag axle), middle door ahead of the rear bogie."""
    real_len = 14.5
    axles = (2.75, 10.10, 11.50)
    DOORS = ((0.32, 1.32, "le"), (6.40, 7.60, "le"))
    BAND = ((0.0, 14.5, 6, 11),)
    AC = (2.5, 6.4)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 8.10, 9.60, 11.1, 12.6, 13.6)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 10.1, 11.6, 13.1)

    def markers(self):
        return (1.9, 4.5, 7.5, 9.0, self.real_len - 0.45)


class CrosswayLine(CrosswayLELine):
    """Iveco Crossway LINE 12M: high floor, doors 1-1-0 (narrow front door,
    middle door between the axles), the window line one row higher, 'swoosh'
    dip behind the front door."""
    DOORS = ((0.30, 1.28, "hf"), (7.02, 7.97, "hf"))
    BAND = ((0.0, 12.0, 6, 11),)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 8.05, 9.65, 11.00)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 10.10)


class CrosswayLine13(CrosswayLine):
    real_len = 13.0
    axles = (2.65, 9.30, 10.65)
    DOORS = ((0.30, 1.28, "hf"), (6.60, 7.55, "hf"))
    BAND = ((0.0, 13.0, 6, 11),)
    AC = (2.5, 6.2)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 7.60, 9.10, 10.6, 12.0)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 10.1, 11.6)


class IrisbusFace:
    """Irisbus Crossway (2006-2013) front: windscreen with a body-coloured
    cap and the display behind it, a black band with the headlamps across
    the lower front, a chrome Irisbus bar under the windscreen."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            return Sh(self.lv.body) if av > W2 - 0.25 else (LED if av < 0.9 else BLACK)
        if k >= 5:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 4:
            return Sh(CHROME) if av < 0.55 else Sh(d or self.lv.body)
        if d is not None:
            return Sh(d)
        if k == 3:
            return Sh(self.lv.body)
        if k == 2:
            if av > W2 - 0.50:
                return HEAD
            return Sh(GRILLE_DK)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class IrisbusCrosswayLE(IrisbusFace, CrosswayLELine):
    """Irisbus Crossway LE 12M (2007-2013), the same body as the Iveco
    Crossway LE LINE with the Irisbus front."""


class IrisbusCrosswayLE108(IrisbusFace, CrosswayLELine108):
    """Irisbus Crossway LE 10,8M."""


class IrisbusCrossway(IrisbusFace, CrosswayLine):
    """Irisbus Crossway 12M (high floor, 2006-2013)."""


class IrisbusCrossway128(IrisbusCrossway):
    """Irisbus Crossway 12,8M: 12.8 m, two axles, one bay longer."""
    real_len = 12.8
    axles = (2.65, 9.10)
    DOORS = ((0.30, 1.28, "hf"), (7.30, 8.25, "hf"))
    BAND = ((0.0, 12.8, 6, 11),)
    AC = (2.5, 6.0)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 7.10, 8.35, 9.85, 11.35)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 10.10, 11.55)


class IrisbusCrossway106(IrisbusCrossway):
    """Irisbus Crossway 10,6M."""
    real_len = 10.6
    axles = (2.55, 7.55)
    DOORS = ((0.30, 1.28, "hf"), (6.00, 6.95, "hf"))
    BAND = ((0.0, 10.6, 6, 11),)
    AC = (2.3, 5.3)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 7.05, 8.55, 9.75)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 9.85)


class CrosswayLECity12(CrosswayLELine):
    """Iveco Crossway LE CITY 12M: the LE body with three double doors
    (2-2-2, the rear one behind the rear axle)."""
    DOORS = ((0.32, 1.32, "le"), (5.10, 6.30, "le"), (9.80, 11.00, "le"))

    def pillars(self, right):
        if right:
            return (2.62, 4.05, 6.85, 8.15, 9.70)
        return (2.62, 4.05, 5.55, 7.05, 8.55, 10.05)


class CrosswayLECity108(CrosswayLELine108):
    """Iveco Crossway LE CITY 10,8M: two double doors (2-2-0)."""


class CrosswayPro13(CrosswayLine13):
    """Iveco Crossway PRO 13M: the LINE 13M body (tag axle) with the PRO's
    high window line; drawn as the LINE 13M with fixed windows."""


# ---------------------------------------------------------------------- SOR CN
class SorFace:
    """SOR CN / C front: a very deep flat windscreen in a black surround,
    the display behind its top edge, body-coloured lower front with the
    twin headlamps in black pods at the corners and the SOR badge."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av < W2 - 0.30:
                return LED if av < 0.9 else BLACK
            return BLACK
        if k >= 4:
            if av > W2 - 0.08:
                return BLACK
            return SCREEN_LHI if k >= top - 3 else SCREEN_L
        if k == 3:
            return BLACK if av > W2 - 0.08 else Sh(d or self.lv.body)
        if d is not None:
            return Sh(d)
        if k == 2:
            if av > W2 - 0.55:
                return HEAD if av > W2 - 0.45 else BLACK
            return Sh(CHROME) if av < 0.12 else Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class SorCN(SorFace, RegioBus):
    """SOR CN 12,3 (2020+): low-entry interurban. Doors 1-2-0 (single front
    door ahead of the front axle, double middle door just behind the half
    length). Behind the middle door the floor, the window line and the roof
    step up (the SOR 'hump'), drawn two rows high so it reads at pak128 scale
    like the VTPsim hand art; the middle door rises two rows above the window
    line into the step; rounded caps and roof edges; top-hinged hopper
    windows in every other pane; thin black rub strip at the arch tops.
    Approved variant R6 (comparison page, 2026-10-04). From the BusLine KHK
    #7036 left side and the AUDIS BUS 7H5 3048 rear photos."""
    real_len = 12.3
    axles = (2.55, 9.15)
    arch_rows = 3
    RUB = 3
    DOORS = ((0.30, 1.25, "le"), (5.95, 7.15, "le"))
    BAND = ((0.0, 7.15, 5, 11), (7.15, 12.3, 7, 13))
    ROOF_STEP = (6.6, 2)
    REAR_GLASS = (8, 12)
    ROUND = 0.32
    DOOR_RAISE = 2
    GLASS_HI_ROWS = 4
    HOPPER = True
    HATCHES = (6.0, 10.6)
    AC = (2.2, 5.6)
    FIG_DX = 0.50

    def pillars(self, right):
        if right:
            return (2.40, 3.55, 4.85, 7.15, 8.55, 9.95, 11.30)
        return (2.40, 3.70, 5.05, 6.45, 7.85, 9.30, 10.75)


class SorCN105(SorCN):
    real_len = 10.6
    axles = (2.55, 7.85)
    DOORS = ((0.30, 1.25, "le"), (5.05, 6.25, "le"))
    BAND = ((0.0, 6.25, 5, 11), (6.25, 10.6, 7, 13))
    ROOF_STEP = (5.7, 2)
    HATCHES = (5.0, 9.1)
    AC = (2.0, 4.9)

    def pillars(self, right):
        if right:
            return (2.40, 3.70, 6.25, 7.65, 9.10)
        return (2.40, 3.75, 5.10, 6.50, 7.90, 9.30)


class SorCN95(SorCN):
    real_len = 9.5
    axles = (2.50, 6.95)
    DOORS = ((0.30, 1.25, "le"), (4.35, 5.55, "le"))
    BAND = ((0.0, 5.55, 5, 11), (5.55, 9.5, 7, 13))
    ROOF_STEP = (5.0, 2)
    HATCHES = (4.4, 8.1)
    AC = (2.0, 4.5)
    FIG_DX = 0.40

    def pillars(self, right):
        if right:
            return (2.40, 3.40, 5.55, 6.95, 8.30)
        return (2.40, 3.75, 5.10, 6.50, 7.95)


class SorCN85(SorCN):
    real_len = 8.5
    axles = (2.30, 6.20)
    DOORS = ((0.30, 1.25, "le"), (3.85, 5.05, "le"))
    BAND = ((0.0, 5.05, 5, 11), (5.05, 8.5, 7, 13))
    ROOF_STEP = (4.5, 2)
    HATCHES = (3.9, 7.3)
    AC = (1.8, 4.1)
    FIG_DX = 0.35

    def pillars(self, right):
        if right:
            return (2.30, 3.30, 5.05, 6.40, 7.60)
        return (2.30, 3.65, 5.00, 6.35, 7.60)


class SorCNG(SorCN):
    """SOR CNG 12,3: the CN 12,3 with the CNG tank fairing over the front
    (low) roof instead of the A/C pod."""
    AC = (0.9, 6.3)
    AC_H = 0.34
    HATCHES = (10.6,)


class SorC105(SorCN):
    """SOR C 10,5 (high floor, 2005-2015): the SOR face on a single-level
    body, flat roof, doors 1-1-0 (narrow front door, single middle door
    between the axles), the window line high all along, hopper windows."""
    real_len = 10.5
    axles = (2.50, 7.65)
    RUB = 3
    R_TOP = 13
    DOORS = ((0.30, 1.20, "hf"), (4.70, 5.55, "hf"))
    BAND = ((0.0, 10.5, 7, 12),)
    ROOF_STEP = None
    REAR_GLASS = (8, 11)
    DOOR_RAISE = 0
    HATCHES = (3.6, 7.8)
    AC = None

    def pillars(self, right):
        if right:
            return (2.40, 3.55, 5.60, 7.00, 8.40, 9.60)
        return (2.40, 3.75, 5.10, 6.45, 7.80, 9.20)


class SorC95(SorC105):
    real_len = 9.5
    axles = (2.45, 6.90)
    DOORS = ((0.30, 1.20, "hf"), (4.20, 5.05, "hf"))
    BAND = ((0.0, 9.5, 7, 12),)
    HATCHES = (3.4, 7.0)

    def pillars(self, right):
        if right:
            return (2.40, 3.40, 5.10, 6.45, 7.95)
        return (2.40, 3.75, 5.10, 6.45, 7.90)


class SorLC12(SorC105):
    """SOR LC 12 / LC 10,5 (long-distance, high floor): the C body with
    fixed windows (no hoppers), luggage lockers between the axles, doors
    1-1-0 with the middle door between the axles, roof A/C."""
    real_len = 12.0
    axles = (2.65, 8.60)
    R_TOP = 13
    DOORS = ((0.30, 1.20, "hf"), (5.70, 6.55, "hf"))
    BAND = ((0.0, 12.0, 7, 12),)
    HOPPER = False
    HATCHES = (3.8, 9.2)
    AC = (2.6, 5.4)

    def pillars(self, right):
        if right:
            return (2.40, 4.05, 6.60, 8.20, 9.80, 11.2)
        return (2.40, 4.05, 5.70, 7.35, 9.00, 10.65)

    def seams(self, right):
        return (3.4, 4.8, 7.4) if right else (3.4, 4.8, 6.2, 7.4)


class SorLC105(SorLC12):
    real_len = 10.5
    axles = (2.50, 7.65)
    DOORS = ((0.30, 1.20, "hf"), (4.70, 5.55, "hf"))
    BAND = ((0.0, 10.5, 7, 12),)
    HATCHES = (3.6, 7.8)
    AC = (2.4, 4.6)

    def pillars(self, right):
        if right:
            return (2.40, 3.55, 5.60, 7.00, 8.40, 9.60)
        return (2.40, 3.75, 5.10, 6.45, 7.80, 9.20)
