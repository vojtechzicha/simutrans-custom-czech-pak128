"""ODIS (Moravskoslezský kraj) regional buses: render or repaint the sprite
sheets and write the family.yaml of every vehicle-bus/odis/<family>.

    python tools/busrender/odis.py [family ...] [--yaml] [--preview DIR]
                                   [--shape low|low1|raised|orig] [--out DIR]

Without --yaml only the sheets are written; with --yaml the family.yaml files
are (re)generated from FAMILIES too (review the diff). --shape picks the body
shape (iredo_models.SHAPES; default iredo_models.SHAPE); --out DIR writes
the sheets to DIR/<family>/ instead of the families' sprites/.

Package (user, 2026-10-20): agency ODIS -> VZ-ODIS-bus.pak holds the
regional buses only; every ODIS town with MHD has its own MHD<Town> pak
(odis_town.py and the older town drivers). As in VZ-IREDO and VZ-Praha there
is one object per type x livery, shared by every operator that runs it; the
operator appears only in the livery display name.

The kraj prescribes no body colour for its regional contracts. Each operator
keeps its own scheme and adds the kraj's "základní grafický prvek (kruh)"
over the rear axle on both sides (ODIS technical standards 2018, příloha 1:
1.5-2.3 m across), in colours matching the scheme:
  transdev          Transdev Morava: white, the big red Transdev figure, the
                    ring in salmon and reds
  bila              plain white (Z-Group bus, Transdev Slezsko's white buses):
                    the ring in greys with the red and blue kraj colours
  3csadbilozelena   3ČSAD white-green (Transdev Slezsko, ex ČSAD Havířov /
                    Karviná / Frýdek-Místek): the ring in greens
A Zlínský kraj bus seen on ODIS lines keeps its own scheme and gets no ring:
  bilazelenomodra   Z-Group bus's Kroměříž cars: white, a navy and a green hill
                    and the big Z-Group emblem in green and navy
The ring is open at the lower front quadrant and printed over the glass too
(drawn as a lighter tint there, so the window band still reads).

Methods, as in odis_town.py: the IREDO box models (iredo_models.py,
iredo_coachmodels.py) with the liveries below, registered under their own
keys so odis_town's town liveries stay untouched; hand-drawn sheets (repo
sheets, VTPsim's frozen ODIS sheets in src/odis/) repainted zone by zone with
the ring drawn on the fitted box.
"""
import os
import sys
import math
import textwrap

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import odis_town as T                                                   # noqa: E402
import iredo_models as M                                                # noqa: E402
import iredo_coachmodels as CM                                          # noqa: E402
from rj_vrender import Sh, Box                                          # noqa: E402
from rj_buses import row_for                                            # noqa: E402

K = T.K
WHITE = T.WHITE
CSAD_GREEN = T.CSAD_GREEN
LEDW, AMBER = T.LEDW, T.AMBER


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


# ====================================================================== the kraj ring
class Ring:
    """the kraj ring ("základní grafický prvek", the kraj design manual ch. 7.2
    and 8.1): up to three concentric bands of twelve 30-degree segments. As
    used on the buses the outer band is open at the lower front quadrant, the
    middle band runs from the lower rear over the top to the upper front and
    the inner band covers the upper half and a little of the lower front.
    Angles: 0 = towards the rear, 90 = up, +-180 = towards the front.
    OUTER: two tones alternating per segment (the white dividing lines read
    as a tone step at this scale), TOP: an accent segment at the top or None,
    MID / INNER: the middle and inner band colours."""
    def __init__(self, outer, top, mid, inner):
        self.outer, self.top, self.mid, self.inner = outer, top, mid, inner

    def at(self, dx, dz):
        """colour at (dx, dz) in radii from the centre (dx + towards the rear,
        dz + up); None = no ring"""
        r = math.hypot(dx, dz)
        ang = math.degrees(math.atan2(dz, dx))
        if 0.62 <= r <= 1.0:
            if ang < -90:                               # open at the lower front
                return None
            if self.top is not None and 60 <= ang < 90:
                return self.top
            return self.outer[int((ang + 180) // 30) % 2]
        if 0.37 <= r < 0.62:
            return self.mid if -60 <= ang < 120 else None
        if 0.15 <= r < 0.37:
            return self.inner if ang >= 0 or ang < -150 else None
        return None


# colours: the kraj's own (manual ch. 8.1: grey Cool Gray 6 / silver 877, red
# Pantone 485, blue Pantone 280) on Z-Group's white buses; Transdev Morava's
# peach and salmon wedges with the red top wedge, red middle and wine inner
# band (photos, white scaled to F0F0EE); the 3ČSAD greens
RING_KRAJ = Ring(((0xB0, 0xB1, 0xB3), (0x9C, 0x9E, 0xA2)), None, (0xC4, 0x24, 0x1F), (0x08, 0x46, 0x86))
RING_TD = Ring(((0xE8, 0xB4, 0x9C), (0xE0, 0x92, 0x7C)), (0xD8, 0x47, 0x3F),
               (0xD8, 0x47, 0x3F), (0x9C, 0x3B, 0x3B))
RING_GREEN = Ring(((0xA8, 0xDA, 0x88), (0x7C, 0xC4, 0x64)), None, CSAD_GREEN, (0x1C, 0x8A, 0x3C))
# geometry (Transdev Morava photos): 2.0-2.2 m across, centred 0.3-0.5 m
# behind the rear axle and about 1.4 m up, so its top is on the upper window
# band and its bottom at the body's lower edge behind the wheel arch
RX = 1.05                          # radius along the side (m)
RK = 4.4                           # radius in pixel rows (0.238 m each)
KC = 4.6                           # centre row over Z0 (1.4 m up)
XC = 0.40                          # centre behind the rear axle (m)
GLASS_TINT = 0.20                  # the ring on the glass: its colour mixed this far towards the glass
GLASS_DK = (0x4D, 0x4D, 0x4E)


def sill(bus, x):
    """the lowest glazing row at x (band_at includes the coach bodies' rising sills)"""
    band = bus.band_at(x)
    return band[0] if band else bus.R_BAND0


class KrajRing:
    """livery mixin: the ring over the rear axle; HUMP_BLACK paints the step
    under the raised rear windows of a SOR CN black (the 2018-19 Transdev
    Morava cars), so the window band reads as one stripe"""
    RING = RING_KRAJ
    HUMP_BLACK = False

    def ring(self, bus, x, k):
        return self.RING.at((x - bus.axles[-1] - XC) / RX, (k - KC) / RK)

    def hump(self, bus, x, k):
        if not self.HUMP_BLACK or not getattr(bus, "ROOF_STEP", None):
            return False
        return bus.BAND[0][2] <= k < sill(bus, x)

    def side(self, bus, x, k, right):
        c = self.ring(bus, x, k)
        if self.hump(bus, x, k):
            return M.BLACK if c is None else mix(c, GLASS_DK, GLASS_TINT)
        if c is not None and k < sill(bus, x):
            return c
        return super().side(bus, x, k, right)


class OdisTransdev(KrajRing, M.Transdev):
    """Transdev Morava: the IREDO Transdev scheme (white, the big red figure)
    with the ring in reds. The figure is placed as on the Transdev Morava
    photos: on the door side it ends 0.4 m ahead of the middle door, on the
    other side it starts 1 m behind the front axle (just past the arch)."""
    slug = "odis-transdev"
    RING = RING_TD
    HUMP_BLACK = True
    W = 1.25                       # the figure's length along the side (m)

    def figure(self, bus, x, k, right):
        """the figure placed for Transdev Morava; under 7 rows of lower panel
        (SOR CN, Crossway, ICN) the five-row FIG_S, under 5 the four-row FIG_XS"""
        top = sill(bus, x) - 1
        rows = top + 1 - bus.SKIRT
        fig = next(f for f in (self.FIG, self.FIG_S, self.FIG_XS) if rows >= len(f) or f is self.FIG_XS)
        r = top - k
        if not 0 <= r < len(fig):
            return None
        if right:
            xe = bus.DOORS[1][0] - 0.40
            c = bus.colidx(x, xe, backwards=True)
        else:
            c = bus.colidx(x, bus.axles[0] + 1.0)
        row = fig[r]
        return self.RED if 0 <= c < len(row) and row[c] == "#" else None

    def side(self, bus, x, k, right):
        c = self.ring(bus, x, k)
        if self.hump(bus, x, k):
            return M.BLACK if c is None else mix(c, GLASS_DK, GLASS_TINT)
        if c is not None and k < sill(bus, x):
            return c
        return self.figure(bus, x, k, right)


class OdisBila(KrajRing, M.Livery):
    """plain white with the ring in the kraj's own grey, red and blue (Z-Group bus)"""
    slug = "odis-bila"
    body = WHITE
    RING = RING_KRAJ


class OdisBilaZel(OdisBila):
    """white with the green ring (Transdev Slezsko Havířovsko, the ex-Bruntál
    Transdev Morava SOR CNG 12)"""
    slug = "odis-bilazel"
    RING = RING_GREEN


class OdisBilaCerv(OdisBila):
    """white with the salmon-red ring (Transdev Slezsko Hlučínsko)"""
    slug = "odis-bilacerv"
    RING = RING_TD


class OdisCsad(KrajRing, T.CsadWG):
    """3ČSAD white-green (Transdev Slezsko) with the green ring. The green
    skirt runs straight up to row CSAD_TOP (2 on the SOR CN, 3 on the taller
    Crossway LE CITY green) with the dark pinstripe over it; on bodies with
    CSAD_SWEEP it rises to the windows behind the front door."""
    slug = "odis-3csad"
    RING = RING_GREEN

    def side(self, bus, x, k, right):
        c = self.ring(bus, x, k)
        b0 = sill(bus, x)
        if c is not None and k < b0:
            return c
        top_g = getattr(bus, "CSAD_TOP", self.TOP)
        top = top_g
        if getattr(bus, "CSAD_SWEEP", False):
            d1 = bus.DOORS[0][1]
            if x < d1:
                top = b0 - 1
            elif x < d1 + 1.0:
                top = top_g + int(round((b0 - 1 - top_g) * (1 - (x - d1) / 1.0)))
        if k <= top:
            return CSAD_GREEN
        if k == top + 1 and top < b0 - 1:
            return self.PIN
        return None


class OdisCsadPod(OdisCsad):
    """3ČSAD white-green with the bright green CNG pod of Transdev Slezsko's
    two 2014 SOR CNG 12 (43-1101 / 43-1112, #223 / #222)"""
    slug = "odis-3csad-pod"
    ac = (0x5C, 0xC4, 0x3E)
    rear_ac = (0xEE, 0xEE, 0xEC)

    def ac_side(self):
        return Sh((0x46, 0xA8, 0x30))


BORS_YEL = (0xE6, 0x99, 0x28)
BORS_BLUE = (0x35, 0x51, 0x88)
RING_PALE = Ring(((0xDC, 0xE8, 0xF2), (0xB8, 0xD0, 0xE6)), None, (0x8C, 0xB4, 0xDC), (0x5E, 0x8A, 0xC4))


class OdisBors(KrajRing, M.Livery):
    """Z-Group's SOR CN 12 63-1401 (2016, ex BORS BUS Břeclav, at Kopřivnice since
    6/2025) in the BORS yellow-blue: royal blue skirt up to the rub strip,
    amber-yellow belt under the windows, a blue strip over them, yellow front
    mask over a blue bumper; the kraj ring added in 2025 looks pale blue on the
    only photo (unverified)"""
    slug = "odis-bors"
    body = BORS_YEL
    roof = (0xEE, 0xEE, 0xEA)
    ac = (0xEC, 0xEC, 0xE8)
    seam = (0xC8, 0x82, 0x20)
    bumper = BORS_BLUE
    RING = RING_PALE
    cant = True                    # the blue strip over the windows

    def side(self, bus, x, k, right):
        c = self.ring(bus, x, k)
        b0 = sill(bus, x)
        if c is not None and k < b0:
            return c
        if k <= 1:
            return BORS_BLUE
        if k == getattr(bus, "RUB", None):
            return None
        if k < b0:
            return BORS_YEL
        band = bus.band_at(x)
        if band and k >= band[1]:
            return BORS_BLUE                            # the strip over the windows
        return None

    def front(self, bus, v, k):
        return BORS_BLUE if k <= 1 else None

    def rear(self, bus, v, k):
        return BORS_BLUE if k <= 2 else None


ODIS_RED = (0xDC, 0x06, 0x12)      # the ODIS scheme's signal red (~RAL 3020)
ODIS_ROOF = (0xE6, 0x26, 0x2C)     # the same paint seen from above, lighter so the shape reads


class OdisRed(M.Livery):
    """the kraj's ODIS scheme (červeno-černá, every new contract from 12/2025):
    signal red body, roof and pods, black window band, the white folk-ornament
    line one row under the windows (dotted at this scale, broken by the doors),
    the big white ODIS logo on the lower side (between the front axle and the
    middle door on the door side, mid-length on the other), no ring; a black
    band under the windscreen"""
    slug = "odis-cervena"
    body = ODIS_RED
    roof = ODIS_ROOF
    ac = ODIS_ROOF
    seam = (0xB4, 0x04, 0x0E)
    LOGO = ["##.##.#.##",
            "##.##.#.##"]

    def side(self, bus, x, k, right):
        b0 = sill(bus, x)
        if k == b0 - 1:
            return WHITE if bus.colidx(x, 0.0) % 2 == 0 else None
        r = max(b0 - 3, bus.SKIRT + len(self.LOGO) - 1) - k     # on a low panel the logo moves up to the line
        if 0 <= r < len(self.LOGO):
            w = len(self.LOGO[0]) * bus.pw()
            xm = (bus.axles[0] + bus.DOORS[1][0]) / 2 if right else bus.real_len / 2
            a, b = xm - w / 2, xm + w / 2
            if a <= x < b:
                c = T.reading_col(bus, x, a, b, right)
                if 0 <= c < len(self.LOGO[r]) and self.LOGO[r][c] == "#":
                    return WHITE
        return None

    def front(self, bus, v, k):
        return M.BLACK if k == 4 else None

    def ac_side(self):
        return Sh(ODIS_RED)


ZG_GREEN = (0x4C, 0xB0, 0x5E)      # Z-Group green and navy (photos, white scaled to F2F2F0)
ZG_NAVY = (0x2E, 0x32, 0x6E)


class OdisZGroup(M.Livery):
    """Z-Group bus's own scheme (bílá se zeleno-modrou grafikou, the Zlínský
    kraj cars from 2021, no kraj ring): white, a navy and a green hill just
    behind the front axle, the big Z-Group emblem over the rear overhang
    (a green circle from the roof edge to the skirt, the navy tree in it over
    the glass, green and navy halves under the windows split by a white
    swoosh), a green swoosh and a navy panel at the lower right of the rear,
    the small green emblem on the front. The decals are one picture applied
    unmirrored, so in screen terms both sides look alike: navy hill left of
    the green, the emblem's green half left of the navy."""
    slug = "odis-zgroup"
    EX = 1.30                      # emblem: centre behind the rear axle and radius (m)
    EK, ER = 5.5, 6.0              # emblem centre row and radius in rows (row 0 to the cant)
    HILLS = (3.20, 5.10)           # the hills between the front arch and the middle door (m)

    def seen(self, bus, x, xc, right):
        """x - xc as seen: + towards screen right (the rear on the left side)"""
        return xc - x if right else x - xc

    def emblem(self, dx, dz):
        """the parts that are alike on both sides: the green circle and the
        navy tree (its stem and two arms rising apart); None = not in it"""
        r = math.hypot(dx, dz)
        if r > 1.0:
            return None
        if r >= 0.80:
            return ZG_GREEN
        if dz >= -0.08:
            ax = abs(dx)
            if ax < 0.10 or abs(ax - (0.15 + 0.45 * dz)) < 0.14:
                return ZG_NAVY
        return None

    def at(self, bus, x, k):
        xc = bus.axles[-1] + self.EX
        return (x - xc) / self.EX, (k + 0.5 - self.EK) / self.ER

    def ring(self, bus, x, k):
        """the emblem on the side glazing (Regio tints it towards the glass)"""
        return self.emblem(*self.at(bus, x, k))

    def hills(self, bus, x, k, right):
        a, b = self.HILLS
        if not a <= x < b:
            return None
        s = b - x if right else x - a
        h = (k + 0.5) / sill(bus, x)              # height on the lower side, 0..1
        g = 1 - ((s - 1.30) / 0.65) ** 2
        if g > 0 and h < 0.48 * math.sqrt(g):
            return ZG_GREEN
        top = 0.80 * math.sin(math.pi / 2 * min(s / 0.95, 1.0)) if s < 0.95 \
            else 0.80 - 1.25 * (s - 0.95)
        return ZG_NAVY if h < top else None

    def side(self, bus, x, k, right):
        dx, dz = self.at(bus, x, k)
        c = self.emblem(dx, dz)
        if c is not None:
            return c
        if math.hypot(dx, dz) < 0.80 and k < sill(bus, x):
            if right and x >= bus.real_len - 1.20 and 1 <= k <= 3:
                return None                         # the engine grille stays on top
            s = -dx if right else dx                # as seen
            cut = -0.05 + 0.15 * (dz + 0.5)
            if abs(s - cut) < 0.13:
                return WHITE                        # the white swoosh
            return ZG_GREEN if s < cut else ZG_NAVY
        return self.hills(bus, x, k, right)

    def front(self, bus, v, k):
        return ZG_GREEN if k == 4 and abs(v) < 0.18 else None

    def rear(self, bus, v, k):
        if k == 5 and -0.35 <= v < 0.40:
            return ZG_NAVY                          # Z-GROUP BUS
        # the swoosh: its left edge and the navy panel's edge rise to the right
        edge = {2: (0.0, 0.32), 3: (0.40, 0.56)}.get(k)
        if edge and edge[0] <= v < bus.W2 - 0.25:
            return ZG_GREEN if v < edge[1] else ZG_NAVY
        return None


for _lv in (OdisTransdev, OdisBila, OdisBilaZel, OdisBilaCerv, OdisCsad, OdisCsadPod, OdisBors, OdisRed,
            OdisZGroup):
    M.LIVERIES[_lv.slug] = _lv


class Regio:
    """body mixin for the ODIS regional buses: no IREDO sticker, the ring
    continued over the side glazing as a tint, white LED displays (the
    2016-2025 deliveries of all three operators). The low shape
    (iredo_models.SHAPES) applies to the bodies with a low(); the ODIS bodies
    add their roof boxes to it."""
    KHK_STICKER = False
    DISP = LEDW

    def side(self, u, z, right):
        c = super().side(u, z, right)
        if c is not M.GLASS and c is not M.GLASS_HI:
            return c
        x, k = self.X(u), self.row(z)
        if right and self.door(x, k) is not None:
            return c
        r = self.lv.ring(self, x, k) if hasattr(self.lv, "ring") else None
        return c if r is None else mix(r, GLASS_DK, GLASS_TINT)

    def front_face(self, v, av, k, d):
        c = super().front_face(v, av, k, d)
        return self.DISP if c == M.LED else c

    REAR_AC = None                 # (x0, x1, h): a second roof box, on the raised rear roof if any

    def model(self):
        L, boxes, lines = super().model()
        if self.REAR_AC:
            x0, x1, h = self.REAR_AC
            z0 = self.zr(self.top_row(x0)) + 0.08
            boxes.append(Box(self.U(x1), self.U(x0), -self.POD_W2, self.POD_W2, z0, z0 + h, self.rear_ac))
        return L, boxes, lines

    def rear_ac(self, face, u, v, z):
        """the second roof box: the livery's rear_ac colour (white A/C behind a
        coloured CNG pod), else the pod colour"""
        c = getattr(self.lv, "rear_ac", None)
        if c is None:
            return self.ac(face, u, v, z)
        return c if face == "+z" else Sh(tuple(x * 0.93 for x in c))


# ====================================================================== bodies
class OSorCN12(Regio, M.SorCN):
    """SOR CN 12 (2016-2018): the CN 12,3 model (same body at this scale),
    one long low A/C pod over the low front roof"""


class OSorCNG12(Regio, M.SorCNG):
    """SOR CNG 12 (2014-2019): the tank fairing over the front half (the
    tallest point, 0.4 m), the Webasto A/C box on the raised rear roof"""
    AC = (1.4, 6.0)
    AC_H = 0.40
    REAR_AC = (7.4, 10.4, 0.20)

    def low(self):
        return dict(super().low(), REAR_AC=(7.4, 10.4, 0.12))


class OSorCN105(Regio, M.SorCN105):
    """SOR CN 10,5 (2018-2019)"""


class OSorCNG105(Regio, M.SorCN105):
    """SOR CNG 10,5 (2015-2019): a 4 m tank fairing, the A/C on the rear roof"""
    AC = (1.4, 5.3)
    AC_H = 0.40
    REAR_AC = (6.6, 9.2, 0.20)
    HATCHES = (9.7,)

    def low(self):
        return dict(super().low(), REAR_AC=(6.6, 9.2, 0.12))


class OSorCN95(Regio, M.SorCN95):
    """SOR CN 9,5 (2018-2019): the big square A/C box over the rear half"""
    AC = None
    REAR_AC = (5.6, 8.3, 0.30)
    HATCHES = (3.2,)

    def low(self):
        return dict(super().low(), REAR_AC=(5.6, 8.3, 0.18))


class OSorC12(Regio, M.SorC105):
    """SOR C 12 (2018): high floor, level window line, doors 1-2 with the
    double middle door between the axles, A/C over the front middle"""
    real_len = 11.82
    axles = (2.60, 8.78)
    DOORS = ((0.30, 1.20, "hf"), (5.05, 6.25, "hf"))
    BAND = ((0.0, 11.82, 7, 12),)
    HATCHES = (3.6, 9.6)
    AC = (2.6, 5.0)

    def pillars(self, right):
        if right:
            return (2.40, 3.70, 6.30, 7.65, 9.00, 10.40)
        return (2.40, 3.75, 5.10, 6.45, 7.80, 9.20, 10.55)


class OCrosswayLELine(Regio, M.CrosswayLELine):
    """Iveco Crossway LE LINE 12M (2019-2020): single front door (1-2-0), the
    A/C from 3 to 7 m"""
    DOORS = ((0.32, 1.10, "le"), (5.10, 6.30, "le"))
    AC = (3.0, 7.0)


class OCrosswayLELineAmber(OCrosswayLELine):
    """the Crossway LE LINE 12M with amber BUSE displays (Z-Group's Kroměříž cars)"""
    DISP = M.LED


class OCrosswayLELineNP(OCrosswayLELine):
    """Iveco Crossway LE LINE 12M NP (CNG, 2020): the long flat CNG fairing
    over most of the roof"""
    AC = (2.4, 8.8)
    AC_H = 0.26


class OCrosswayLECity(Regio, M.CrosswayLELine):
    """Iveco Crossway LE CITY 12M NP (CNG, 2017-2019): wide double front door
    (2-2-0), the long flat CNG fairing; the 3ČSAD green taller and rising to
    the windows behind the front door"""
    AC = (2.4, 8.8)
    AC_H = 0.26
    CSAD_TOP = 3
    CSAD_SWEEP = True


class CrosswayFace2024:
    """Iveco Crossway 2024 facelift front: the windscreen over a black band,
    slim LED lamps at the corners under it, chrome IVECO letters on the
    body-coloured lower front"""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av < self.W2 - 0.30:
                return M.LED if av < 0.9 else M.BLACK
            return M.BLACK
        if k >= 5:
            if av > self.W2 - 0.07:
                return M.BLACK
            return M.SCREEN_HI if k == top - 2 else M.SCREEN
        if k == 4:
            return M.BLACK
        if k == 3:
            return M.HEAD if av > self.W2 - 0.42 else Sh(self.lv.body)
        if k == 2:
            return Sh(M.CHROME) if av < 0.62 else Sh(self.lv.body)
        if k == 1:
            return M.PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class OCrossway2025(Regio, CrosswayFace2024, M.CrosswayLELine):
    """Iveco Crossway LE LINE 12M NP CNG (2025, the facelift): single front
    door, the long low CNG pod from a quarter to two thirds of the length,
    the A/C over the front"""
    DOORS = ((0.32, 1.10, "le"), (5.10, 6.30, "le"))
    AC = (3.0, 8.0)
    AC_H = 0.28
    REAR_AC = (1.0, 2.8, 0.18)


class IcnFace2025:
    """SOR ICN (2025) front: the black mask round the windscreen down to a
    black band, LED lamps in black corner pods, body-coloured lower front
    with the SOR badge"""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av > self.W2 - 0.08:
                return M.BLACK
            return M.LED if av < 0.95 else M.BLACK
        if k >= 5:
            if av > self.W2 - 0.08:
                return M.BLACK
            return M.SCREEN_LHI if k >= top - 3 else M.SCREEN_L
        if k == 4:
            return M.BLACK
        if k in (2, 3) and av > self.W2 - 0.50:
            return M.HEAD if (k == 3 and av < self.W2 - 0.12) else M.BLACK
        if k == 2 and av < 0.12:
            return Sh(M.CHROME)
        if k == 1:
            return M.PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        if k == 0:
            return Sh(self.lv.bumper or self.lv.seam)
        return Sh(self.lv.body)


class OSorICNG105(Regio, IcnFace2025, CM.SorICN105):
    """SOR ICNG 10,5 (2026, Českotěšínsko II): the ICN 10,5 with the CNG pod over
    the front half and a low box behind the middle door"""
    AC = (1.4, 5.7)
    AC_H = 0.42
    REAR_AC = (7.6, 9.9, 0.20)
    HATCHES = ()

    def low(self):
        return dict(super().low(), AC_H=0.28, REAR_AC=(7.6, 9.9, 0.12))


class OSorICNG123(Regio, IcnFace2025, CM.SorICN):
    """SOR ICNG 12,3 (2025): the tall CNG pod over the front half, a low box
    behind it, the 2025 SOR face"""
    AC = (1.4, 6.4)
    AC_H = 0.42
    REAR_AC = (7.2, 10.6, 0.20)
    HATCHES = (11.2,)

    def low(self):
        return dict(super().low(), AC_H=0.28, REAR_AC=(7.2, 10.6, 0.12))


class OSetra(Regio, CM.SetraS415LE):
    """Setra S 415 LE business (2018): the glazing sill rising behind the rear
    axle leaves the black wedge that tells it apart, the A/C mid-roof"""


class OSorICNG12(Regio, CM.SorICN):
    """SOR ICNG 12 (the 2021 prototype): the ICN body with the CNG fairing
    over the front half and black bumpers"""
    AC = (1.4, 6.6)
    AC_H = 0.40
    REAR_AC = (7.4, 10.6, 0.22)
    HATCHES = (11.2,)

    def low(self):
        return dict(super().low(), AC_H=0.28, REAR_AC=(7.4, 10.6, 0.12))

    def __init__(self, livery):
        super().__init__(livery)
        self.lv.bumper = M.BLACK


# ====================================================================== repainted sheets
LIT = {(0x4D, 0x4D, 0x4D), (0x57, 0x65, 0x6F)}


def ring_decal(ring, axle, zc=1.40, base=None):
    """decals() for odis_town.repaint: the kraj ring on both side faces of a
    fitted hand-drawn sheet, centred at `axle` (fraction of the body from the
    front) and zc metres up; on the lit glass it becomes a tint. base: an
    earlier decals() to run first."""
    def draw(o, paint, geo, d, r):
        if base is not None:
            o = base(o, paint, geo, d, r)
        if d not in T.SIDE:
            return o
        o = o.copy()
        face, frac, z, L = geo["face"], geo["frac"], geo["z"], geo["L"]
        for y, x in zip(*np.where((face == 4) | (face == 5))):
            px = tuple(int(v) for v in o[y, x])
            if px == T.T:
                continue
            c = ring.at(((float(frac[y, x]) - axle) * L - XC) / RX, (float(z[y, x]) - zc) / (RK * 0.238))
            if c is None:
                continue
            if px in LIT:
                o[y, x] = mix(c, GLASS_DK, GLASS_TINT)
            elif paint[y, x]:
                o[y, x] = K.safe(c)
        return o
    return draw


def odis_red_decal(logo_r=(0.24, 0.44), logo_l=(0.40, 0.60), base=None):
    """decals(): the ODIS scheme's white ornament line (every other column of
    the first row under the window band) and the big white ODIS logo two rows
    lower, reading left to right on both sides"""
    def draw(o, paint, geo, d, r):
        if base is not None:
            o = base(o, paint, geo, d, r)
        if d not in T.SIDE:
            return o
        panel = T.lower_panel(o, paint, geo, d)
        o = o.copy()
        for x, (y, fc, f) in panel.items():
            if x % 2 == 0:
                T.put(o, paint, x, y, WHITE)
        for face, rng in ((4, logo_r), (5, logo_l)):
            cols = T.decal_columns(panel, face, *rng)
            for i, x in enumerate(cols):
                if i % 3 != 2:
                    y = panel[x][0]
                    T.put(o, paint, x, y + 2, WHITE)
                    T.put(o, paint, x, y + 3, WHITE)
        return o
    return draw


skirt_decal = T.skirt_decal
W_ZONES = {"white": ((0xEE, 0xEE, 0xEC), WHITE), "green": ((0xEE, 0xEE, 0xEC), WHITE)}
WG_ZONES = {"white": ((0xEE, 0xEE, 0xEC), WHITE), "green": (CSAD_GREEN, CSAD_GREEN)}
RED_ZONES = {"white": (ODIS_RED, ODIS_ROOF)}
WHITE_POD = T.WHITE_POD
RED_POD = (ODIS_RED, ODIS_ROOF)


def strip_marks(rows, Ls, zmin=0.95):
    """paint out VTPsim's stand-in for the kraj ring (a green or red hook over
    the rear axle, mostly on the glass): coloured side pixels above zmin
    metres take the nearest plain pixel left or right of them"""
    out = []
    for r, tiles in enumerate(rows):
        row = []
        for d, t in zip(T.DIRS, tiles):
            geo = T.fit(t, d, Ls[r])
            m = np.zeros((128, 128), bool)
            for y, x in zip(*np.where((geo["face"] == 4) | (geo["face"] == 5))):
                c = tuple(int(v) for v in t[y, x])
                if c == T.T or T.hexc(c) in T.H.SPECIAL or float(geo["z"][y, x]) < zmin:
                    continue
                if max(c) - min(c) > 0x50:
                    m[y, x] = True
            o = t.copy()
            for y, x in zip(*np.where(m)):
                for dx in range(1, 10):
                    hit = [xx for xx in (x - dx, x + dx)
                           if 0 <= xx < 128 and not m[y, xx] and not np.all(t[y, xx] == T.T)]
                    if hit:
                        o[y, x] = t[y, hit[0]]
                        break
            row.append(o)
        out.append(row)
    return out


def scania(name, Ls, zones, ring, axle, pods, display=LEDW):
    """a VTPsim Scania Citywide sheet (src/odis/) ported, its ring stand-in
    painted out, repainted, the ring and the CNG pods added"""
    def build():
        rows, _ = T.port_native(name, Ls[0], display, CSAD_GREEN)
        rows = strip_marks(rows, Ls)
        return T.repaint(rows, T.z_white_green, zones, Ls, ring_decal(ring, axle), pods, WHITE_POD)
    return build


def z_mdpo(c):
    """MDPO white-red (the Opava Urbanway 10,5M): the reds are the skirt"""
    if T.hexc(c) in T.H.SPECIAL:
        return None
    if T.neutral(c, 0xB0):
        return "white"
    r, g, b = c
    if r > 0xA0 and g < 0x30 and b < 0x40:
        return "green"
    return None


def man_lions_city_u():
    """MAN NÜ 313 Lion's City Ü CNG (the old generation): praha_man.OldGen
    with two doors, the rounded CNG fairing over the front 45 % and the A/C
    behind it, drawn plain white (its IDS JMK scheme with the grey and red
    taken out), then the kraj ring added on the fitted sheet"""
    import praha_man as PM

    class LionsCityU(PM.OldGen):
        doors_r = [(0.25, 1.50), (5.55, 6.85)]
        posts_r = [2.90, 4.25, 8.10, 9.65, 11.10]
        sidedisp = None
        ac = (6.40, 8.60)

        def __init__(self, view, livery="J", variant=None):
            super().__init__(view, livery, variant)
            self.roof_parts = [dict(kind="fair", u0=0.60, u1=5.40, inset=0.20, h0=0.0, h1=0.40),
                               dict(kind="ac", u0=6.40, u1=8.60, inset=0.30, h0=0.0, h1=0.20)]

    var = dict(grey_top=0.0, band_top=2.55)
    row = PM.build_row(LionsCityU, "J", var, label="lions_city_u")
    row = [np.array(t)[:, :, :3].copy() for t in row]

    def recol(c):
        h = T.hexc(c)
        if h == T.hexc(PM.rgb(PM.LIME)):
            return LEDW
        r, g, b = c
        if r > 0xB0 and g < 0x40 and b < 0x40:                 # the red roof-edge line
            return WHITE
        return None
    rows = [[K.recolour(t, recol) for t in row]]
    return T.repaint(rows, T.z_white, {"white": ((0xEE, 0xEE, 0xEC), WHITE)}, [[11.5, 12.0, 12.5]],
                     ring_decal(RING_KRAJ, 0.73))


# ====================================================================== families
f_ = T.f_
ODIS = ("ODIS", "ODIS", "ODIS")
BUS, MIDI = T.BUS, T.MIDI
TD = ("white with the red figure · Transdev Morava", "bílá s červenou postavou · Transdev Morava")
WG = ("3ČSAD white-green · Transdev Slezsko", "3ČSAD bílo-zelená · Transdev Slezsko")
WZ_TDS = ("white, green kraj ring · Transdev Slezsko", "bílá, zelený krajský kruh · Transdev Slezsko")
WZ_TDM = ("white, green kraj ring · Transdev Morava", "bílá, zelený krajský kruh · Transdev Morava")
WC = ("white, red kraj ring · Transdev Slezsko", "bílá, červený krajský kruh · Transdev Slezsko")
RED = ("ODIS red-black · Transdev Slezsko", "ODIS červeno-černá · Transdev Slezsko")
WGP = ("3ČSAD white-green, green CNG box · Transdev Slezsko",
       "3ČSAD bílo-zelená, zelený CNG box · Transdev Slezsko")
BORS = ("BORS yellow-blue · Z-Group bus", "BORS žluto-modrá · Z-Group bus")
ZG = ("white · Z-Group bus", "bílá · Z-Group bus")
ZGG = ("white with green-blue graphic · Z-Group bus", "bílá se zeleno-modrou grafikou · Z-Group bus")
RENDER = ("original box-model render (vojtechzicha): {cls} of tools/busrender/odis.py\n"
          "(on the {base} body of {mod}) with the livery of odis.py.")


def model(cls, liv):
    return lambda: [row_for(cls, liv)]


def rendered(cls):
    base = [b for b in cls.__mro__ if b.__module__ in ("iredo_models", "iredo_coachmodels")][0]
    return RENDER.format(cls=cls.__name__, base=base.__name__, mod=base.__module__ + ".py")


def one(vid, display, role, fields):
    return T.one(vid, display, role, fields)


def flow(text, width=78):
    return textwrap.fill(" ".join(text.split()), width)


def fam(folder, type_, name, vehicles, liveries, note, sprite, copyright="vojtechzicha", allow=()):
    return ("odis/" + folder, dict(agency=ODIS, type=type_, name=(name, name), copyright=copyright,
                                   vehicles=vehicles, liveries=liveries, note=flow(note),
                                   sprite=flow(sprite, 70), allow=allow))


WG_NOTE = ("3ČSAD white-green (Transdev Slezsko, the colours of ex ČSAD Havířov /"
           " Karviná / Frýdek-Místek; seznam-autobusu \"3ČSAD, bílo-zelená & logo dopravy"
           " Moravskoslezského kraje\"): white, black window band, green skirt with a dark"
           " pinstripe, green lower front and rear, the kraj ring in greens.")
WHITE_NOTE = ("seznam-autobusu \"bílá & logo dopravy Moravskoslezského kraje\": white, black"
              " window band, the kraj ring over the rear axle; Transdev Slezsko prints it"
              " green in Havířovsko and salmon-red in Hlučínsko.")
RED_NOTE = ("the kraj's ODIS scheme (\"schéma ODIS, červeno-černá\", every new contract from"
            " 12/2025): signal red with a black window band, the white folk-ornament line"
            " under the windows, the big white ODIS logo, no ring.")
ZG_NOTE = ("Z-Group bus (ex ČSAD Vsetín; Kopřivnice, Opava and Vítkov depots): white,"
           " black window band, the kraj ring in its own colours (grey, the red and blue"
           " inner bands), navy fleet numbers.")
ZGG_NOTE = ("Z-Group bus 6Z9 6492 (2020, depot Kroměříž, seen on ODIS line 670 in 9/2026; seznam-autobusu"
            " \"Z-Group bus, bílá se zeleno-modrou grafikou\" since 2/2021), doors 1-2-0, amber"
            " displays: Z-Group's own Zlínský kraj scheme, no kraj ring. White, black window"
            " band, a navy and a green hill just behind the front axle, the big Z-Group emblem"
            " over the rear overhang (green circle from the roof edge to the skirt, the navy"
            " tree on the glass, green and navy halves below), a green swoosh and a navy panel"
            " low on the rear (photos of 6Z9 6480 / 6491 / 6492 and 7Z6 4793, 2021-2024).")
TD_NOTE = ("Transdev Morava livery (seznam-autobusu: \"bílá & červené logo Transdev & logo\n"
           "dopravy Moravskoslezského kraje\"): white, black window band, the big red Transdev\n"
           "figure, the kraj ring in salmon and reds over the rear axle.")

FAMILIES = dict([
    # ------------------------------------------------------------ Transdev Morava
    fam("sor_cn_12", "SOR_CN_12", "SOR CN 12",
        one("SOR_CN_12", "CN 12", BUS,
            f_(620000, 90, 100, 11, 25, 127, 2016, 8, "diesel", 235, 54, smoke="Diesel_small")),
        [("transdev", *TD, model(OSorCN12, "odis-transdev")),
         ("borszlutomodra", *BORS, model(OSorCN12, "odis-bors"))],
        "SOR CN 12 low-entry interurban (2016-2018), doors 1-2. Transdev Morava 54:\n"
        "62-1001 to 1025 (Novojičínsko západ), 82-, 83-, 84-10xx (Krnovsko, Bruntálsko,\n"
        "Rýmařovsko). " + TD_NOTE + " The step under the raised rear"
        " windows is painted black, so the band reads as one stripe. Z-Group bus 1:"
        " 63-1401 (2016, ex BORS BUS Břeclav, Kopřivnice since 6/2025) in the BORS"
        " yellow-blue (blue skirt, amber belt, blue strip over the windows) with the"
        " kraj ring added in 2025, pale blue on the only photo (unverified).",
        rendered(OSorCN12)),
    fam("sor_cng_12", "SOR_CNG_12", "SOR CNG 12",
        one("SOR_CNG_12", "CNG 12", BUS,
            f_(650000, 90, 90, 12, 26, 132, 2014, 8, "diesel", 213, 54)),
        [("transdev", *TD, model(OSorCNG12, "odis-transdev")),
         ("3csadbilozelena", *WG, model(OSorCNG12, "odis-3csad")),
         ("bilazelenykruh", *WZ_TDM, model(OSorCNG12, "odis-bilazel")),
         ("bila", *ZG, model(OSorCNG12, "odis-bila")),
         ("3csadbilozelenazelenybox", *WGP, model(OSorCNG12, "odis-3csad-pod"))],
        "SOR CNG 12 low-entry interurban (CNG; engine_type diesel, no smoke), the tank\n"
        "fairing over the front half and the A/C box on the raised rear roof. Transdev\n"
        "Morava 24 (2018-2019): 62-1101 to 1109, 24-1101 to 1115 (Hlučínsko, 555). " + TD_NOTE +
        " Transdev Slezsko 82 (2014-2018; Havířov, Český Těšín, Karviná, Orlová,"
        " Frýdek-Místek): " + WG_NOTE + " Two 2014 cars, 43-1101 and 43-1112, have a"
        " bright green CNG pod (their own livery here)."
        " White with the green ring: Transdev Morava 24-1120 (2015, ex MHD Bruntál, the"
        " BRUNTÁL emblem removed). Z-Group bus 62 (Novojičínsko východ, Opavsko,"
        " Vítkovsko): " + ZG_NOTE,
        rendered(OSorCNG12)),
    fam("sor_cn_10_5", "SOR_CN_10_5", "SOR CN 10,5",
        one("SOR_CN_10_5", "CN 10,5", BUS,
            f_(560000, 78, 100, 10, 22, 114, 2018, 7, "diesel", 210, 54, smoke="Diesel_small")),
        [("transdev", *TD, model(OSorCN105, "odis-transdev"))],
        "SOR CN 10,5 (2018-2019), 10.75 m. Transdev Morava 35: 82-, 83-, 84-20xx\n"
        "(Bruntál areas), 64-2001 to 2003 (Bílovecko). " + TD_NOTE,
        rendered(OSorCN105)),
    fam("sor_cng_10_5", "SOR_CNG_10_5", "SOR CNG 10,5",
        one("SOR_CNG_10_5", "CNG 10,5", BUS,
            f_(590000, 78, 90, 10, 23, 120, 2015, 7, "diesel", 200, 54)),
        [("transdev", *TD, model(OSorCNG105, "odis-transdev")),
         ("3csadbilozelena", *WG, model(OSorCNG105, "odis-3csad")),
         ("bila", *ZG, model(OSorCNG105, "odis-bila"))],
        "SOR CNG 10,5 (CNG; engine_type diesel, no smoke). Transdev Morava 7 (2019):\n"
        "64-2101 to 2107 (Bílovecko). " + TD_NOTE + " Transdev Slezsko 19 (2016):"
        " 73-0021 to 0039 (Českotěšínsko), " + WG_NOTE + " Z-Group bus 11: " + ZG_NOTE,
        rendered(OSorCNG105)),
    fam("sor_cn_9_5", "SOR_CN_9_5", "SOR CN 9,5",
        one("SOR_CN_9_5", "CN 9,5", MIDI,
            f_(520000, 68, 90, 9, 21, 106, 2018, 7, "diesel", 180, 54, smoke="Diesel_small")),
        [("transdev", *TD, model(OSorCN95, "odis-transdev"))],
        "SOR CN 9,5 (2018-2019), 9.6 m, the big A/C box over the rear half. Transdev\n"
        "Morava 18: 62-3001 to 3014 (Novojičínsko západ), 64-3001 to 3004 (Bílovecko). " + TD_NOTE,
        rendered(OSorCN95)),
    fam("sor_c_12", "SOR_C_12", "SOR C 12",
        one("SOR_C_12", "C 12", BUS,
            f_(600000, 85, 100, 11, 24, 122, 2018, 8, "diesel", 235, 54, smoke="Diesel_small")),
        [("transdev", *TD, model(OSorC12, "odis-transdev"))],
        "SOR C 12 high-floor interurban (2018), 11.82 m, doors 1-2. Transdev Morava 13:\n"
        "82-1201, 1202, 83-1201 to 1206, 84-1201 to 1205 (Bruntál areas), on regional\n"
        "lines every day. " + TD_NOTE,
        rendered(OSorC12)),
    fam("crossway_le_line_12m", "Crossway_LE_Line_12M", "Iveco Crossway LE LINE 12M",
        one("Crossway_LE_Line_12M", "Crossway LE LINE 12M", BUS,
            f_(640000, 92, 100, 11, 26, 131, 2014, 8, "diesel", 243, 54, smoke="Diesel_small")),
        [("transdev", *TD, model(OCrosswayLELine, "odis-transdev")),
         ("bilazelenomodra", *ZGG, model(OCrosswayLELineAmber, "odis-zgroup"))],
        "Iveco Crossway LE LINE 12M (2013+ front), doors 2-2. Transdev Morava 23 (2019):\n"
        "64-0001 to 0004, 64-1001 to 1019 (Bílovecko). " + TD_NOTE + " " + ZGG_NOTE,
        rendered(OCrosswayLELine)),
    fam("sor_icng_12", "SOR_ICNG_12", "SOR ICNG 12",
        one("SOR_ICNG_12", "ICNG 12", BUS,
            f_(700000, 90, 90, 12, 28, 143, 2021, 8, "diesel", 235, 54)),
        [("transdev", *TD, model(OSorICNG12, "odis-transdev"))],
        "SOR ICNG 12 (CNG; engine_type diesel, no smoke): the 2021 prototype 24-1151,\n"
        "leased by Transdev Morava (Hlučínsko), black bumpers. " + TD_NOTE,
        rendered(OSorICNG12)),
    # ------------------------------------------------------------ Transdev Slezsko
    fam("crossway_le_line_12m_np", "Crossway_LE_Line_12M_NP", "Iveco Crossway LE LINE 12M NP",
        one("Crossway_LE_Line_12M_NP", "Crossway LE LINE 12M NP", BUS,
            f_(680000, 92, 90, 12, 27, 139, 2020, 8, "diesel", 243, 54)),
        [("bilazelenykruh", *WZ_TDS, model(OCrosswayLELineNP, "odis-bilazel")),
         ("bilacervenykruh", *WC, model(OCrosswayLELineNP, "odis-bilacerv"))],
        "Iveco Crossway LE LINE 12M NP (CNG, Natural Power; engine_type diesel, no smoke),"
        " single front door, the long flat CNG fairing. Transdev Slezsko 34 (2020):"
        " 42-1001 to 1023 (Havířovsko, green ring) and 24-1001 to 1011 (Hlučínsko, red"
        " ring); " + WHITE_NOTE,
        rendered(OCrosswayLELineNP)),
    fam("crossway_le_city_12m", "Crossway_LE_City_12M", "Iveco Crossway LE CITY 12M",
        one("Crossway_LE_City_12M", "Crossway LE CITY 12M", BUS,
            f_(660000, 100, 85, 12, 26, 135, 2017, 8, "diesel", 243, 54)),
        [("3csadbilozelena", *WG, model(OCrosswayLECity, "odis-3csad")),
         ("bila", *ZG, model(OCrosswayLECity, "odis-bila"))],
        "Iveco Crossway LE CITY 12M NP (CNG, Natural Power; engine_type diesel, no smoke;"
        " 2017-2019), doors 2-2-0, the long flat CNG fairing. Transdev Slezsko 56:"
        " 32-1001 to 1007, 33-1001 to 1026 (Frýdek-Místek), 51-1001 to 1014 (Orlovsko),"
        " 52-1001 to 1009 (Karvinsko). " + WG_NOTE + " On this body the green reaches"
        " two thirds of the lower side and rises to the windows behind the front door."
        " Z-Group bus 11 (2018): " + ZG_NOTE,
        rendered(OCrosswayLECity)),
    fam("sor_icng_12_3", "SOR_ICNG_12_3", "SOR ICNG 12,3",
        one("SOR_ICNG_12_3", "ICNG 12,3", BUS,
            f_(720000, 90, 90, 12, 29, 147, 2025, 8, "diesel", 235, 54, intro_month=10)),
        [("odiscervenocerna", *RED, model(OSorICNG123, "odis-cervena"))],
        "SOR ICNG 12,3 (CNG; engine_type diesel, no smoke), the 2025 SOR face, the tall"
        " CNG pod over the front half. Transdev Slezsko 26: 74-1101 to 1126"
        " (Jablunkovsko-Třinecko, from 12/2025). In " + RED_NOTE,
        rendered(OSorICNG123)),
    fam("sor_icng_10_5", "SOR_ICNG_10_5", "SOR ICNG 10,5",
        one("SOR_ICNG_10_5", "ICNG 10,5", BUS,
            f_(660000, 76, 90, 11, 26, 135, 2026, 7, "diesel", 220, 54, intro_month=12)),
        [("odiscervenocerna", *RED, model(OSorICNG105, "odis-cervena"))],
        "SOR ICNG 10,5 (CNG; engine_type diesel, no smoke), the 2025 SOR face, the CNG pod"
        " over the front half, doors 1-2-0. Transdev Slezsko, Českotěšínsko II from 13"
        " Dec 2026 (delivered 10/2026 with SOR ICNG 12,3 and Crossway LE LINE 12M NP"
        " (2025), about 38 buses in all). In " + RED_NOTE,
        rendered(OSorICNG105)),
    fam("crossway_le_line_12m_np_2025", "Crossway_LE_Line_12M_NP_2025",
        "Iveco Crossway LE LINE 12M NP (2025)",
        one("Crossway_LE_Line_12M_NP_2025", "Crossway LE LINE 12M NP (2025)", BUS,
            f_(700000, 92, 90, 12, 28, 143, 2025, 8, "diesel", 250, 54, intro_month=10)),
        [("odiscervenocerna", *RED, model(OCrossway2025, "odis-cervena"))],
        "Iveco Crossway LE LINE 12M NP CNG (CNG; engine_type diesel, no smoke) with the"
        " 2024 facelift face, the long low CNG pod. Transdev Slezsko 5: 74-1001 to 1005"
        " (Jablunkovsko-Třinecko, from 12/2025). In " + RED_NOTE,
        rendered(OCrossway2025)),
    fam("scania_citywide_le_12m_cng", "Citywide_LE_12M_CNG", "Scania Citywide LE 12M CNG",
        one("Citywide_LE_12M_CNG", "Citywide LE 12M CNG", BUS,
            f_(800000, 95, 85, 12, 30, 150, 2016, 8, "diesel", 206, 55)),
        [("3csadbilozelena", *WG,
          scania("CZ-ODIS-ScaniaCitywideLE128M_Suburban-Green", [[11.5, 12.0, 12.5]], WG_ZONES,
                 RING_GREEN, 0.78, [[(0.12, 0.55, 0.30, 1.0)]])),
         ("bila", *ZG,
          scania("CZ-ODIS-ScaniaCitywideLE128M_Suburban-Green", [[11.5, 12.0, 12.5]], W_ZONES,
                 RING_KRAJ, 0.78, [[(0.12, 0.55, 0.30, 1.0)]]))],
        "Scania Citywide LE 12M CNG (CNG; engine_type diesel, no smoke), the tall CNG"
        " fairing over the front half. Transdev Slezsko 4: 42-1201, 1202 (2016), 51-1201,"
        " 1202 (2018). " + WG_NOTE + " Z-Group bus 12 (2018): " + ZG_NOTE,
        "VTPsim's pak128.cs Citywide LE suburban (CZ-ODIS-ScaniaCitywideLE128M_"
        "Suburban-Green, frozen in tools/busrender/src/odis/) ported by"
        " odis_town.port_native, its ring stand-in painted out, the CNG fairing, the"
        " kraj ring and the white LED displays added by odis.py.",
        copyright="VTPsim"),
    fam("scania_citywide_suburban_le_15m_cng", "Citywide_Suburban_LE_15M_CNG",
        "Scania Citywide Suburban LE 15M CNG",
        one("Citywide_Suburban_LE_15M_CNG", "Citywide Suburban LE 15M CNG", BUS,
            f_(900000, 120, 90, 14, 34, 170, 2017, 10, "diesel", 250, 55)),
        [("3csadbilozelena", *WG,
          scania("CZ-ODIS-ScaniaCitywideLE15M_Suburban-Green", [[13.5, 14.5, 15.5]], WG_ZONES,
                 RING_GREEN, 0.88, [[(0.18, 0.55, 0.22, 0.95)]]))],
        "Scania Citywide Suburban LE 15M CNG (CNG; engine_type diesel, no smoke), three"
        " axles. Transdev Slezsko 10: 42-0007, 0008 (2017), 51-0001 to 0004, 52-0001 to"
        " 0004 (2018). " + WG_NOTE + " The ring sits on the rear panel behind the tandem.",
        "VTPsim's pak128.cs Citywide LE 15M suburban (CZ-ODIS-ScaniaCitywideLE15M_"
        "Suburban-Green, frozen in tools/busrender/src/odis/) ported by"
        " odis_town.port_native, its ring stand-in painted out, the CNG pods, the kraj"
        " ring and the white LED displays added by odis.py.",
        copyright="VTPsim"),
    fam("scania_citywide_le_15m_cng", "Citywide_LE_15M_CNG", "Scania Citywide LE 15M CNG",
        one("Citywide_LE_15M_CNG", "Citywide LE 15M CNG", BUS,
            f_(900000, 125, 85, 14, 34, 170, 2020, 10, "diesel", 250, 55)),
        [("bilazelenykruh", *WZ_TDS,
          scania("CZ-ODIS-ScaniaCitywideLE15M_Suburban-Green", [[13.5, 14.5, 15.5]], W_ZONES,
                 RING_GREEN, 0.88, [[(0.55, 0.92, 0.30, 1.0)]]))],
        "Scania Citywide LE 15M CNG (CNG; engine_type diesel, no smoke), three axles, the"
        " tank pod over the rear. Transdev Slezsko 6: 42-0001 to 0006 (2020,"
        " Havířovsko). " + WHITE_NOTE,
        "VTPsim's pak128.cs Citywide LE 15M (CZ-ODIS-ScaniaCitywideLE15M_Suburban-Green,"
        " frozen in tools/busrender/src/odis/) ported by odis_town.port_native,"
        " repainted white, the rear CNG pod, the kraj ring and the white LED displays"
        " added by odis.py.",
        copyright="VTPsim"),
    fam("scania_citywide_le_13_7m_cng", "Citywide_LE_13_7M_CNG", "Scania Citywide LE 13,7M CNG",
        one("Citywide_LE_13_7M_CNG", "Citywide LE 13,7M CNG", BUS,
            f_(860000, 110, 85, 13, 32, 165, 2020, 8, "diesel", 250, 55)),
        [("bilacervenykruh", *WC,
          scania("CZ-ODIS-ScaniaCitywideLE137M_White", [[12.5, 13.5, 14.0]], W_ZONES,
                 RING_TD, 0.80, [[(0.15, 0.55, 0.26, 0.95)]]))],
        "Scania Citywide LE 13,7M CNG (CNG; engine_type diesel, no smoke), tag axle,"
        " doors 1-2-1. Transdev Slezsko 6: 24-0001 to 0006 (2020, Hlučínsko). " + WHITE_NOTE +
        " The ring is printed mostly on the rear side windows.",
        "VTPsim's pak128.cs Citywide LE 13,7M (CZ-ODIS-ScaniaCitywideLE137M_White,"
        " frozen in tools/busrender/src/odis/) ported by odis_town.port_native, its ring"
        " stand-in painted out, the CNG pods, the kraj ring and the white LED displays"
        " added by odis.py.",
        copyright="VTPsim"),
    fam("scania_citywide_suburban_le_12_6m_cng", "Citywide_Suburban_LE_12_6M_CNG",
        "Scania Citywide Suburban LE 12,6M CNG",
        one("Citywide_Suburban_LE_12_6M_CNG", "Citywide Suburban LE 12,6M CNG", BUS,
            f_(820000, 95, 90, 12, 31, 155, 2019, 8, "diesel", 206, 55)),
        [("bila", *ZG,
          scania("CZ-ODIS-ScaniaCitywideLE128M_Suburban-Green", [[11.5, 12.0, 12.5]], W_ZONES,
                 RING_KRAJ, 0.78, [[(0.10, 0.28, 0.18, 0.90), (0.40, 0.72, 0.26, 0.95)]]))],
        "Scania Citywide Suburban LE 12,6M CNG (CNG; engine_type diesel, no smoke), the"
        " Suburban front, the A/C at the front and the CNG equipment further back."
        " Z-Group bus 6 (2019): " + ZG_NOTE,
        "VTPsim's pak128.cs Citywide LE suburban (CZ-ODIS-ScaniaCitywideLE128M_"
        "Suburban-Green, frozen in tools/busrender/src/odis/) ported by"
        " odis_town.port_native, its ring stand-in painted out, repainted white, the"
        " roof boxes, the kraj ring and the white LED displays added by odis.py.",
        copyright="VTPsim"),
    fam("setra_s_415_le_business", "Setra_S_415_LE_business", "Setra S 415 LE business",
        one("Setra_S_415_LE_business", "S 415 LE business", BUS,
            f_(680000, 90, 100, 11, 27, 139, 2014, 8, "diesel", 260, 54, smoke="Diesel_small")),
        [("bila", *ZG, model(OSetra, "odis-bila"))],
        "Setra S 415 LE business, doors 1-2-0. Z-Group bus 51 (2018, Kopřivnice:"
        " Novojičínsko východ, the Kopřivnice town trips of line 653). " + ZG_NOTE,
        rendered(OSetra)),
    fam("man_lions_city_u_cng", "Lions_City_U_CNG", "MAN Lion's City Ü CNG",
        one("Lions_City_U_CNG", "Lion's City Ü CNG", BUS,
            f_(760000, 92, 90, 12, 29, 155, 2020, 8, "diesel", 228, 55)),
        [("bila", *ZG, man_lions_city_u)],
        "MAN NÜ 313 Lion's City Ü CNG (CNG; engine_type diesel, no smoke), the old"
        " Lion's City body, two doors, the rounded CNG fairing over the front 45 % and"
        " the A/C behind it. Z-Group bus 5 (2020): " + ZG_NOTE,
        "original box-model render (vojtechzicha): praha_man.OldGen (the NL 283 body of"
        " tools/busrender/praha_man.py) with two doors and the CNG roof, white, the kraj"
        " ring added by odis.py."),
    fam("dekstra_le_37_cng", "Dekstra_LE_37_CNG", "Dekstra LE 37 L CNG",
        one("Dekstra_LE_37_CNG", "Dekstra LE 37 L CNG", MIDI,
            f_(420000, 45, 80, 6, 16, 85, 2018, 5, "diesel", 125, 50)),
        [("3csadbilozelena", *WG, lambda: T.repaint(
            T.load_rows("vehicle-bus/iredo/dekstra_le_37/sprites/bila.png"), T.z_white,
            {"white": ((0xEE, 0xEE, 0xEC), WHITE)}, [[7.0, 7.5, 8.0]],
            ring_decal(RING_GREEN, 0.68, base=skirt_decal(CSAD_GREEN, 1.0)),
            [[(0.30, 0.70, 0.22, 0.80)]], WHITE_POD, T.disp(LEDW)))],
        "Dekstra LE 37 L CNG (CNG; engine_type diesel, no smoke), the Iveco Daily based"
        " low-entry midibus with a low CNG box on the roof. Transdev Slezsko 7 (2018-2020):"
        " 33-4001 to 4003 (Frýdek-Místek), 52-3001 to 3004 (Karvinsko). " + WG_NOTE +
        " Here the lower third is green.",
        "VTPsim's Dekstra LE 37 (the IREDO white sheet, vehicle-bus/iredo/dekstra_le_37)"
        " repainted by odis_town.repaint, the green skirt, the CNG box and the kraj ring"
        " added by odis.py.",
        copyright="VTPsim"),
    fam("rosero_first_cng", "Rosero_First_CNG", "Rošero First FCLLI CNG",
        one("Rosero_First_CNG", "Rošero First FCLLI CNG", MIDI,
            f_(400000, 40, 80, 5, 15, 80, 2025, 5, "diesel", 125, 50, intro_month=10)),
        [("odiscervenocerna", *RED, lambda: T.repaint(
            T.load_rows("vehicle-bus/iredo/rosero_first/sprites/bila.png"), T.z_white,
            RED_ZONES, [[7.0, 7.5, 8.0]], odis_red_decal(), [[(0.30, 0.72, 0.24, 0.80)]],
            RED_POD, T.disp(LEDW)))],
        "ROŠERO-P First FCLLI CNG (CNG; engine_type diesel, no smoke) on the Iveco Daily."
        " Transdev Slezsko 2: 74-4001, 4002 (Jablunkovsko-Třinecko, from 12/2025). In " + RED_NOTE,
        "VTPsim's Rošero First (the IREDO white sheet, vehicle-bus/iredo/rosero_first)"
        " repainted red by odis_town.repaint, the ornament line, the ODIS logo and the"
        " CNG box added by odis.py.",
        copyright="VTPsim"),
    fam("urbanway_10_5m_cng", "Urbanway_10_5M_CNG", "Iveco Urbanway 10,5M CNG",
        one("Urbanway_10_5M_CNG", "Urbanway 10,5M CNG", BUS,
            f_(700000, 80, 80, 11, 27, 140, 2016, 7, "diesel", 213, 55)),
        [("3csadbilozelena", *WG, lambda: T.repaint(
            T.load_rows("vehicle-bus/mdpo/urbanway_10_5m/sprites/mdpobilocervena.png"), z_mdpo,
            WG_ZONES, [[10.0, 10.5, 11.0]], ring_decal(RING_GREEN, 0.78), None, None,
            lambda c: LEDW if T.hexc(c) in (0xF0A018, 0xF7A21B, 0x01DD01) else None))],
        "Iveco Urbanway 10,5M CNG (CNG; engine_type diesel, no smoke), city body, doors"
        " 2-2-0, ex Iveco demonstrator (2016). Transdev Slezsko 1: 73-0049"
        " (Českotěšínsko). " + WG_NOTE,
        "Lubak91's Urbanway 10,5M CNG (the MDPO sheet, vehicle-bus/mdpo/urbanway_10_5m)"
        " repainted by odis_town.repaint (its red skirt green), the kraj ring added by"
        " odis.py.",
        copyright="Lubak91"),
])


# ====================================================================== main
def option(argv, name):
    if name not in argv:
        return None, argv
    i = argv.index(name)
    return argv[i + 1], argv[:i] + argv[i + 2:]


def main(argv):
    pv, argv = option(argv, "--preview")
    if pv:
        os.makedirs(pv, exist_ok=True)
    shape, argv = option(argv, "--shape")
    if shape:
        M.SHAPE[0] = shape
    out, argv = option(argv, "--out")           # write the sheets there instead of sprites/
    do_yaml = "--yaml" in argv
    argv = [a for a in argv if a != "--yaml"]
    for key, f in FAMILIES.items():
        if argv and key not in argv and key.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, "vehicle-bus", *key.split("/"))
        sd = os.path.join(out, key.split("/")[-1]) if out else os.path.join(d, "sprites")
        os.makedirs(sd, exist_ok=True)
        for slug, _, _, fn in f["liveries"]:
            rows = fn()
            T.save_sheet(rows, os.path.join(sd, slug + ".png"), f.get("allow", ()))
            if pv:
                T.preview(rows, os.path.join(pv, f"{key.replace('/', '-')}-{slug}.png"))
            print(f"vehicle-bus/{key}/sprites/{slug}.png  rows={len(rows)}")
        if do_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(T.yaml_text(f, "odis.py"))


if __name__ == "__main__":
    main(sys.argv[1:])
