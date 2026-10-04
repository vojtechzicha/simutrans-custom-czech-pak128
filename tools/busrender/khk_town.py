"""Town (MHD) buses of Královéhradecký kraj outside Hradec Králové: render or
repaint the sprite sheets and write the family.yaml files.

    python tools/busrender/khk_town.py [family ...] [--yaml] [--preview DIR]

Without --yaml only the sheets are written; with --yaml the family.yaml files
are (re)generated from FAMILIES too (review the diff). A family is named by
its folder (sor_ebn_9_5) or agency/folder (mhd-trutnov/sor_nbg_18).

Packages (user, 2026-10-04):
  IREDO (vehicle-bus/iredo/)  the town MHDs integrated in IREDO: Náchod, Rychnov
      nad Kněžnou, Vrchlabí; one object per type x livery, the operator only in
      the livery display name.
  MHDTrutnov (vehicle-bus/mhd-trutnov/)  Trutnov MHD (ARRIVA autobusy), own tariff.
  MHDSpindleruvMlyn (vehicle-bus/mhd-spindleruv-mlyn/)  Služby města Špindlerův Mlýn.

Three methods, picked per type by which reads more like the real bus:
  * SOR EBN 9,5 / 11,1: the parametric dpmhk.py body (imported, never edited, so
    the DPMHK sheets stay byte-identical) painted by the KVeh wrapper below, as
    praha.py does for the Prague liveries. The 2026 Rychnov cars get the current
    SOR e-bus face (black mask down to a white bumper), the 2018 Náchod and
    Vrchlabí cars the older "smile" face of dpmhk.py.
  * Iveco / Irisbus Crossway (Špindlerův Mlýn, the Trutnov Crossway PRO 13M): the
    IREDO box models of iredo_models.py with liveries defined here and
    registered into iredo_models.LIVERIES at import, so they match the IREDO
    Crossways; the subclasses here drop the kraj sticker from the rear window
    (town-ordered buses) and give Špindlerův Mlýn its green LED displays.
  * Bodies with no parametric model (Škoda Perun 26BB HE = Solaris Urbino 12 IV,
    SOR NBG 18, NB 12, BN 8,5, Scania Citywide LF): the upstream hand-drawn
    sheets already in the repo, repainted zone by zone with their shading kept
    (shade factor = pixel luminance / the zone's base luminance). Decals that
    need a position along the body (the Trutnov pixel mosaic and TRUTNOV logo)
    use a per-view box fitted to the sprite silhouette (fit_box), which gives
    every pixel its face and its fraction along the body. The source sheets are
    read at run time; regenerate after changing them.
"""
import os
import sys
import math

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import dpmhk as H                                                       # noqa: E402
from dpmhk import Veh, sh, inr, HW, PER_CU                              # noqa: E402
from render import render, Box, DIRS                                    # noqa: E402
import iredo_models as M                                                # noqa: E402
from rj_vrender import Sh                                               # noqa: E402
from rj_busmodels import W2                                             # noqa: E402
from rj_buses import row_for                                            # noqa: E402

T = (231, 255, 255)
BLACK, FRAME, GLASS, GLASS2 = H.BLACK, H.FRAME, H.GLASS, H.GLASS2
HEADL, TAILL, AMBER, SILVER = H.HEADL, H.TAILL, H.AMBER, H.SILVER
WHITE = (0xF6, 0xF6, 0xF6)


# ====================================================================== SOR EBN
# Livery keys of the KVeh wrapper:
#   cds   CDS Náchod: all-over yellow (roof and roof boxes too), black glazing
#         band from the roof edge down to the window line, red "CDS" + blue
#         "NÁCHOD" on the lowest band row in the rear half; older SOR face: black
#         mask, silver "smile", yellow bumper; black rear panel framed in white.
#   td    Transdev Čechy, Rychnov nad Kněžnou e-bus scheme (2026): white roof and
#         lower body, black from the roof edge down to the wheel-arch tops, white
#         "transdev" behind the front door and the town logo towards the rear on
#         the black, the dark-red Transdev figure on the white lower panel behind
#         the middle door; current SOR face: black mask down to a white bumper.
#   kad   KAD Vrchlabí (EBN 11,1 6H9 5510 since 10/2025): grass-green metallic
#         lower body, white roof and roof boxes, black glazing band with the white
#         KAD logo behind the middle door; older face with a white "smile" and a
#         green bumper.
KPAL = {
    "cds": dict(body=(0xF6, 0xC4, 0x00), roof=(0xF8, 0xCC, 0x10), bumper=(0xF6, 0xC4, 0x00)),
    "td": dict(body=WHITE, roof=(0xF2, 0xF2, 0xF2), bumper=WHITE),
    "kad": dict(body=(0x44, 0x9C, 0x2C), roof=(0xF2, 0xF2, 0xF2), bumper=(0x44, 0x9C, 0x2C)),
}
CDS_RED = (0xD8, 0x1E, 0x24)
CDS_BLUE = (0x1E, 0x3C, 0x96)
TD_RED = (0xB4, 0x14, 0x24)          # dark Transdev red (#C8102E in the shade of the sides)
LOGO_W = (0xF4, 0xF4, 0xF4)
# Transdev figure, 3 rows x 3 columns of 0.30 m cells as seen with the bus's
# front to the left: the arc on the left, the dot head top right, the leg stroke
TD_FIG = ["#..#",
          "#.#.",
          "#.#."]


class KVeh(Veh):
    def setup_livery(self):
        self.P = KPAL[self.liv]
        self.ROOF = self.P["roof"]
        self.TRIM = BLACK
        sp = self.sp
        self.newface = sp.get("newface", False)
        self.mid = self.doors[1]                       # middle door (drawn metres)
        self.rear_axle = self.axles[-1]

    # ---------------------------------------------------------- roof
    def tex_roof(self, p, u):
        if self.newface or self.face == "ebn":
            if u < 0.35:
                return BLACK if self.liv != "td" else self.ROOF
        return self.ROOF

    def tex_pod(self, p, u, k):
        f = p.face
        col = self.ROOF
        if f == "top" and abs(p.t) < 0.25 and self.pods[k][4] == "ac":
            return tuple(int(v * 0.62) for v in col)
        return col if f == "top" else sh(col, f)

    # ---------------------------------------------------------- sides
    def tex_side(self, p, u, U1):
        z, f = p.z, p.face
        right = f == "right"
        for a in self.axles:
            if abs(u - a) < 0.62 and z < 1.02 and math.hypot(u - a, z - self.WR) < 0.62:
                return None
        if u < 0.26 and z >= self.ZBAND0:
            return BLACK                               # black windscreen frame wrapping round
        if right:
            d = self.door_at(u)
            if d and z < self.ZWIN1 + 0.05:
                return self.tex_door(p, u, U1, d)
        if z >= self.ZBAND0:
            if z < self.ZWIN1 + 0.05 or (right and inr(u, *self.sidedisp) and z < self.ZWIN1 + 0.30):
                c = self.band_decal(p, u, right)
                return c if c else self.glass_band(p, u, U1, right)
            return self.cant(p, u)
        return self.lower(p, u, right)

    def cant(self, p, u):
        if self.liv == "td" or p.z < self.ZBAND1:
            return sh(BLACK, p.face)                   # Rychnov: black right up to the roof edge
        return sh(self.ROOF, p.face)

    def band_decal(self, p, u, right):
        """pixels painted over the glazing band (the low row only)"""
        z = p.z
        if not inr(z, self.ZWIN0, self.ZWIN0 + 0.25):
            return None
        L = self.U[-1]
        if self.liv == "cds":
            # "CDS" red then "NÁCHOD" blue, reading front to rear on both sides,
            # in the bay ahead of the rear axle
            a = self.rear_axle - 2.9
            if inr(u, a, a + 0.9):
                return CDS_RED
            if inr(u, a + 1.2, a + 2.6):
                return CDS_BLUE
        elif self.liv == "td":
            a = self.doors[0][1] + 0.35                # "transdev" behind the front door
            if inr(u, a, a + 1.1):
                return LOGO_W
            b = self.rear_axle - 0.2                   # Rychnov town logo over the rear axle
            if inr(u, b, b + 0.9) and int((u - b) / 0.30) % 2 == 0:
                return LOGO_W
        elif self.liv == "kad":
            a = self.mid[1] + 0.45                     # KAD behind the middle door
            if inr(u, a, a + 1.0):
                return LOGO_W
        return None

    def door_kick(self):
        return None

    def lower(self, p, u, right):
        z, f = p.z, p.face
        P = self.P
        if self.liv == "td":
            c = self.td_figure(p, u, right)
            if c:
                return c
        return sh(P["body"], f)

    def td_figure(self, p, u, right):
        """the Transdev figure on the white panel between the middle door and
        the rear arch, top row just under the black"""
        z = p.z
        r = int(math.floor((self.ZBAND0 - z) / 0.25 - 1e-6))
        if not 0 <= r < len(TD_FIG):
            return None
        x0 = (self.mid[1] + (self.rear_axle - 0.62)) / 2 - 0.45
        c = int(math.floor((u - x0) / 0.30))
        if right:
            c = len(TD_FIG[0]) - 1 - c                  # screen-left is the rear on the door side
        row = TD_FIG[r]
        if 0 <= c < len(row) and row[c] == "#":
            return sh(TD_RED, p.face)
        return None

    # ---------------------------------------------------------- ends
    def tex_front(self, p):
        t, z = p.t, p.z
        f = "front"
        a = abs(t)
        P = self.P
        if self.newface:
            # current SOR e-bus face (Rychnov 2026): white bumper with round
            # headlamps in the corners, black mask up to the windscreen
            if z < 0.32:
                return BLACK
            if z < 0.74:
                if a > HW - 0.42 and inr(z, 0.46, 0.64):
                    return HEADL if a < HW - 0.12 else sh(SILVER, f)
                return sh(P["bumper"], f)
            if a > HW - 0.10:
                return BLACK
            if inr(z, 0.90, 1.02) and (inr(t, -0.95, -0.45) or inr(t, 0.35, 0.90)):
                return sh(LOGO_W, f)                    # town logo / transdev on the mask
            if inr(z, 1.14, 2.46) and a < HW - 0.16:
                return GLASS
            if inr(z, 2.54, 2.82) and a < 0.98:
                return AMBER
            return BLACK
        # older SOR e-bus face (dpmhk "ebn")
        if z < 0.36:
            return BLACK
        if z < 0.80:
            if a > HW - 0.40 and inr(z, 0.50, 0.70):
                return HEADL if a < HW - 0.10 else sh(SILVER, f)
            return sh(P["bumper"], f)
        if z < 1.10:
            smile = SILVER if self.liv == "cds" else (0xF4, 0xF4, 0xF4)
            if a < 0.95 and abs(z - (0.82 + 0.26 * (a / 0.95) ** 2)) < 0.06:
                return smile
            return BLACK
        if a > HW - 0.10:
            return BLACK
        if inr(z, 1.14, 2.46) and a < HW - 0.16:
            return GLASS
        if inr(z, 2.54, 2.82) and a < 0.98:
            return AMBER
        if self.liv == "cds" and z >= 2.86:
            return sh(P["roof"], f)
        return BLACK

    def tex_rear(self, p):
        t, z = p.t, p.z
        f = "rear"
        a = abs(t)
        P = self.P
        if a > HW - 0.26 and inr(z, 0.55, 1.35):
            return TAILL
        if z < 0.42:
            return BLACK
        top = 1.30
        if z >= top:
            if self.liv == "cds" and (a > HW - 0.16 or inr(z, top, top + 0.12)):
                return sh(WHITE, f)                     # white frame round the black panel
            if z >= self.ZR - 0.20 and self.liv != "td":
                return sh(P["roof"], f)
            if inr(z, 2.42, 2.62) and inr(t, 0.30, 0.80):
                return AMBER
            if inr(z, 1.80, 2.62) and a < HW - 0.30:
                return GLASS
            return BLACK
        return sh(P["body"], f)


EBN95_M = H.MODELS["ebn95"]
EBN11_M = H.MODELS["ebn11"]
# Rychnov 2026 cars: same bodies, the current face, roof boxes over the front
# two thirds and the rear (photos 441351, 449827, vhdfoto 42828)
EBN95_N = H.mk(EBN95_M, newface=True)
EBN11_N = H.mk(EBN11_M, newface=True)


def build_ebn(sp, livery):
    m = KVeh(sp, livery)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        tiles = []
        for d in DIRS:
            o = np.array(H.origin_for(d))
            img, _ = render(d, m.boxes(i), m.tex_for(i), L, o)
            tiles.append(img)
        rows.append(tiles)
    return rows


# ====================================================================== Crossway
LEDG = (0x62, 0xD6, 0x4A)            # green LED displays (Špindlerův Mlýn), plain colour
ARRIVA_BLUE = (0x30, 0xBE, 0xEA)
SMSM_INK = (0x4A, 0x4C, 0x50)
SWIRL = [(0xE0, 0x3C, 0x1E), (0xF2, 0xA0, 0x1E), (0x2E, 0x9C, 0x3C), (0x1E, 0x5A, 0xB4)]
PICTO = (0x1E, 0x5A, 0xC8)


def glyph(bus, x, k, right, rows, k_top, x0, colours):
    """a pixel decal on a side, rows top first, columns as seen with the front
    on the left (left side) / right (door side); colours maps the cell chars."""
    r = k_top - k
    if not 0 <= r < len(rows):
        return None
    n = len(rows[0])
    c = bus.colidx(x, x0)
    if right:
        c = n - 1 - c                       # the door side reads mirrored: keep the text the same way round
    if 0 <= c < n:
        return colours.get(rows[r][c])
    return None


class SMSM(M.Livery):
    """Služby města Špindlerův Mlýn: plain white, the SMŠM logo (red-orange-
    green-blue swirl + dark grey SMŠM) behind the front door and under the
    windscreen, blue access pictograms at the front."""
    slug = "smsmbila"
    INK = SMSM_INK
    LOGO = ["ab.###",
            "dc...."]

    def side(self, bus, x, k, right):
        cols = {"a": SWIRL[0], "b": SWIRL[1], "c": SWIRL[2], "d": SWIRL[3], "#": self.INK}
        return glyph(bus, x, k, right, self.LOGO, bus.R_BAND0 - 1, 1.55, cols)

    def front(self, bus, v, k):
        if k == 4:
            if -0.10 <= v < 0.05:
                return SWIRL[0]
            if 0.05 <= v < 0.20:
                return SWIRL[2]
            if 0.20 <= v < 0.80:
                return self.INK
            if -0.95 <= v < -0.45:
                return PICTO
        return None


class SMSMRed(SMSM):
    """SMŠM 8H1 9232 (ex Slovak Lines): all-over signal red, the SMŠM logo
    with white lettering."""
    slug = "smsmcervena"
    body = (0xD2, 0x1A, 0x20)
    roof = (0xDA, 0x22, 0x26)
    ac = (0xDA, 0x22, 0x26)
    seam = (0xB0, 0x14, 0x1A)
    INK = (0xF4, 0xF4, 0xF4)


class ArrivaWhite(M.Livery):
    """ARRIVA autobusy, plain white with the small light-blue Arriva logo on
    the front and behind the front door."""
    slug = "arrivabila"

    def side(self, bus, x, k, right):
        return glyph(bus, x, k, right, ["###"], bus.R_BAND0 - 1, 1.70, {"#": ARRIVA_BLUE})

    def front(self, bus, v, k):
        if k == 4 and -0.80 <= v < -0.25:
            return ARRIVA_BLUE
        return None


for _c in (SMSM, SMSMRed, ArrivaWhite):
    M.LIVERIES[_c.slug] = _c


class TownRear:
    """rear window without the kraj sticker (the town orders these buses)."""
    REAR_LED = M.LED

    def rear(self, v, z):
        k = self.row(z)
        g0, g1 = self.REAR_GLASS
        if g0 <= k <= g1 and abs(v) < W2 - 0.22:
            if k == g1 and -1.05 <= v < -0.65:
                return self.REAR_LED
            return M.GLASS
        return M.RegioBus.rear(self, v, z)


class GreenLED(TownRear):
    REAR_LED = LEDG

    def front_face(self, v, av, k, d):
        c = super().front_face(v, av, k, d)
        return LEDG if c == M.LED else c


class SpLELine(GreenLED, M.CrosswayLELine):
    """Iveco Crossway LE LINE 12M of SMŠM."""


class SpIrisbusLE(GreenLED, M.IrisbusCrosswayLE):
    """Irisbus Crossway LE 12M of SMŠM."""


class TuCrosswayPro13(TownRear, M.CrosswayPro13):
    """Iveco Crossway PRO 13M, the Trutnov MHD reserve (6E7 6343)."""


# ====================================================================== repaints
FACE_ID = {"top": 1, "front": 2, "rear": 3, "right": 4, "left": 5}
FACE_NAME = {v: k for k, v in FACE_ID.items()}


def load_sheet(rel):
    return np.array(Image.open(os.path.join(REPO, *rel.split("/"))).convert("RGB"))


def sheet_rows(sheet):
    return [[sheet[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)]
            for r in range(sheet.shape[0] // 128)]


def is_bg(t):
    return np.all(t == T, axis=2)


def _box_geo(d, L, zr, hw, z0=0.30):
    """render a bare box; per pixel the face id, s (m from the rear) and z"""
    def tex(p):
        return (FACE_ID[p.face], int(max(0, min(255, round(p.s * 16)))), int(max(0, min(255, round(p.z * 50)))))
    img, _ = render(d, [Box("b", 0, L, -hw, hw, z0, zr)], tex, L, np.array(H.origin_for(d), float))
    return img


def fit_box(tile, d, Ls):
    """fit a box (length, height, half width, whole-pixel shift) to the sprite
    silhouette of one view; returns the per-pixel geometry of the best fit:
    dict(face=int array, frac=fraction of the body from the front, z=metres)"""
    m = ~is_bg(tile)
    best = None
    for L in Ls:
        for zr in (2.9, 3.1, 3.3, 3.5):
            for hw in (1.20, 1.31, 1.45):
                g = _box_geo(d, L, zr, hw)
                b = ~is_bg(g)
                for dx in range(-6, 7):
                    for dy in range(-6, 7):
                        bb = np.roll(np.roll(b, dy, 0), dx, 1)
                        iou = (bb & m).sum() / max(1, (bb | m).sum())
                        if best is None or iou > best[0]:
                            best = (iou, L, g, dx, dy)
    iou, L, g, dx, dy = best
    g = np.roll(np.roll(g, dy, 0), dx, 1)
    face = np.where(is_bg(g), 0, g[:, :, 0]).astype(int)
    frac = (L - g[:, :, 1] / 16.0) / L
    return dict(face=face, frac=frac, z=g[:, :, 2] / 50.0, iou=iou)


def neutral(c, lo=0xC0):
    r, g, b = (int(v) for v in c)
    return max(r, g, b) - min(r, g, b) <= 12 and max(r, g, b) >= lo


def recolour(tile, rule):
    """apply rule(colour) -> new colour or None to every pixel (cached per colour)"""
    out = tile.copy()
    cache = {}
    flat = out.reshape(-1, 3)
    for i, c in enumerate(tuple(int(v) for v in px) for px in flat):
        if c == T:
            continue
        if c not in cache:
            cache[c] = rule(c)
        n = cache[c]
        if n is not None:
            flat[i] = n
    return out


def scaled(base, k):
    return tuple(int(max(0, min(255, round(v * k)))) for v in base)


def safe(c):
    """nudge a colour off the Simutrans special colours"""
    h = (c[0] << 16) | (c[1] << 8) | c[2]
    if h in H.SPECIAL:
        return (c[0], c[1], min(255, c[2] + 1) if c[2] < 255 else c[2] - 1)
    return c


# ---------------------------------------------------------------- Trutnov MHD
# Arriva light blue over the whole body, roof and roof fairings (the Arriva blue
# of the Přerov Crossway sheet), the black glazing band of the source art kept,
# a scattered mosaic of small vertical blocks (orange, magenta, yellow, dark
# and pale blue) straddling the lower edge of the band, denser towards the
# rear, and the white TRUTNOV MHD logo on the blue behind the front axle
# (photos seznam-autobusu 232403, 398768, 414852, 415210, 442882).
TU_BLUE = (0x30, 0xBE, 0xEA)
TU_WHITE = (0xF4, 0xF6, 0xF8)
MOSAIC = [(0xF3, 0x8B, 0x1F), (0xE0, 0x2E, 0x8C), (0xFF, 0xD2, 0x1E), (0x1E, 0x50, 0xA8),
          (0x9C, 0xE4, 0xFA)]
SLOPE = {"w": 0.5, "e": 0.5, "n": -0.5, "s": -0.5, "ne": 0.0, "sw": 0.0}


def _hash(*v):
    h = 2166136261
    for x in v:
        h = ((h ^ (int(x) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


def band_line(tile, paint, geo, d):
    """per screen column the y of the last band (dark) pixel above the painted
    lower body on a side face, kept only where it lies on the band's straight
    lower edge"""
    if d not in SLOPE:
        return {}
    side = (geo["face"] == 4) | (geo["face"] == 5)
    dark = (tile.max(axis=2) < 0x60) & ~is_bg(tile)
    found = {}
    for x in range(128):
        for y in range(127):
            if dark[y, x] and paint[y + 1, x] and (side[y + 1, x] or side[y, x]):
                found[x] = y
                break
    if not found:
        return {}
    k = SLOPE[d]
    cs = [round(y - k * x) for x, y in found.items()]
    mode = max(set(cs), key=cs.count)
    return {x: y for x, y in found.items() if abs(y - (mode + k * x)) <= 1.0}


def trutnov_decals(tile, paint, geo, d, mosaic=(0.45, 1.0), logo=None, seed=0):
    out = tile.copy()
    line = band_line(tile, paint, geo, d)
    frac = geo["frac"]
    for x, y in line.items():
        f = float(frac[y + 1, x])
        if mosaic and mosaic[0] <= f <= mosaic[1]:
            t = (f - mosaic[0]) / max(1e-6, mosaic[1] - mosaic[0])
            h = _hash(seed, x, DIRS.index(d))
            if (h % 1000) / 1000.0 < 0.28 + 0.62 * t:
                c = MOSAIC[(h >> 10) % len(MOSAIC)]
                ys = [y + 1]
                if (h >> 14) % 2:
                    ys.append(y)                       # the block reaches up into the band
                elif (h >> 15) % 3 == 0:
                    ys.append(y + 2)
                for yy in ys:
                    if 0 <= yy < 128 and (paint[yy, x] or yy == y):
                        out[yy, x] = c
        if logo and logo[0] <= f <= logo[1]:
            for yy, every in ((y + 2, 1), (y + 3, 2)):
                if yy < 128 and paint[yy, x] and (every == 1 or x % 2 == 0):
                    out[yy, x] = TU_WHITE
    return out


def blue_rule(paint_fn, base=TU_BLUE):
    """rule for recolour(): paint_fn(colour) -> shade factor (or None = keep)"""
    def rule(c):
        k = paint_fn(c)
        if k is None:
            return None
        return safe(scaled(base, k))
    return rule


def paint_mask(tile, paint_fn):
    m = np.zeros(tile.shape[:2], bool)
    cache = {}
    for y in range(128):
        for x in range(128):
            c = tuple(int(v) for v in tile[y, x])
            if c == T:
                continue
            if c not in cache:
                cache[c] = paint_fn(c) is not None
            m[y, x] = cache[c]
    return m


def trutnov_rows(src_rows, paint_fn, sections):
    """sections: per sprite row dict(L=[fit lengths], mosaic=(f0, f1) or None,
    logo=(f0, f1) or None)"""
    rows = []
    for r, (tiles, sec) in enumerate(zip(src_rows, sections)):
        out = []
        for d, t in zip(DIRS, tiles):
            paint = paint_mask(t, paint_fn)
            b = recolour(t, blue_rule(paint_fn))
            if d in SLOPE:
                geo = fit_box(t, d, sec["L"])
                b = trutnov_decals(b, paint, geo, d, sec.get("mosaic"), sec.get("logo"), seed=r)
            out.append(b)
        rows.append(out)
    return rows


# Škoda Perun 26BB HE (Solaris Urbino 12 IV body): TommPa9's Urbino 12 IV
# electric of the Tábor family (roof battery fairing), its COMETT white and the
# orange/black chequered patch on the ends turned Arriva blue
URBINO_SRC = "vehicle-bus/mhd-tabor/solaris_urbino_12_electric/sprites/comettbila.png"


def paint_urbino(c):
    h = (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])
    if h in (0xF55F1B, 0x141414):
        return 0.88                                    # the COMETT patch on front and rear
    if h == 0xC5C5C5:
        return None                                    # wheel hubs
    if neutral(c, 0xB0):
        return (int(c[0]) + int(c[1]) + int(c[2])) / 3 / 255.0
    return None


def rows_26bb():
    src = sheet_rows(load_sheet(URBINO_SRC))[:1]
    return trutnov_rows(src, paint_urbino, [dict(L=[11.5, 12.0, 12.5], mosaic=(0.45, 0.98), logo=(0.30, 0.40))])


# SOR NBG 18 / NB 12 / BN 8,5: VTPsim's pak128_czr SOR art (white body and roof,
# red lower body); white and red are the paint, the bellows greys stay
def paint_vtpsim(c):
    r, g, b = (int(v) for v in c)
    if r > 0x90 and g < 0x30 and b < 0x30:
        return min(1.0, r / 0xD5)                      # red (D50B15 = the lit side)
    if neutral(c, 0xC0):
        return (r + g + b) / 3 / 255.0
    return None


NBG18_SRC = "vehicle-bus/mhd-kladno/sor_nbg_18/sprites/kladnobilocervena.png"
NB12_SRC = "vehicle-bus/dpp/sor_nb_12/sprites/dppcervenobila.png"


def rows_nbg18():
    src = sheet_rows(load_sheet(NBG18_SRC))[:2]
    return trutnov_rows(src, paint_vtpsim, [
        dict(L=[10.5, 11.0, 11.5], mosaic=(0.55, 0.98), logo=(0.28, 0.38)),
        dict(L=[7.5, 8.0, 8.5], mosaic=(0.30, 0.98), logo=(0.06, 0.22))])


def rows_nb12():
    src = sheet_rows(load_sheet(NB12_SRC))[:1]
    return trutnov_rows(src, paint_vtpsim, [dict(L=[11.5, 12.0, 12.5], mosaic=(0.45, 0.98), logo=(0.30, 0.40))])


def is_red(c):
    r, g, b = (int(v) for v in c)
    return r > 0x90 and g < 0x40 and b < 0x40


def red_to_white_map(rows):
    """per red shade, the white of the same face: the light paint found
    straight above the red in the same screen column (majority vote)"""
    votes = {}
    for tiles in rows:
        for t in tiles:
            for x in range(128):
                for y in range(1, 128):
                    c = tuple(int(v) for v in t[y, x])
                    if not is_red(c):
                        continue
                    yy = y - 1
                    while yy >= 0 and is_red(tuple(int(v) for v in t[yy, x])):
                        yy -= 1
                    if yy >= 0:
                        a = tuple(int(v) for v in t[yy, x])
                        if neutral(a, 0xC8) and a != T:
                            votes.setdefault(c, {}).setdefault(a, 0)
                            votes[c][a] += 1
    out = {}
    for c, v in votes.items():
        out[c] = max(v.items(), key=lambda kv: kv[1])[0]
    # shades never seen under white: the closest voted red's white, scaled
    return out


def red_to_white(rows):
    m = red_to_white_map(rows)
    known = list(m.items())

    def rule(c):
        if not is_red(c):
            return None
        if c in m:
            return m[c]
        r0, w0 = min(known, key=lambda kv: abs(int(kv[0][0]) - int(c[0])))
        return safe(scaled(w0, c[0] / r0[0]))
    return [[recolour(t, rule) for t in tiles] for tiles in rows]


# SOR BN 8,5 (Trutnov 5E9 3012): plain white with the black SOR mask round the
# windscreen (photo 442526); the DPP BN 8,5 sheet (VTPsim's BN 9,5 shortened)
# with its red turned into the white of the same face
BN85_SRC = "vehicle-bus/dpp/sor_bn_8_5/sprites/dppcervenobila.png"


def rows_bn85():
    return red_to_white(sheet_rows(load_sheet(BN85_SRC))[:1])


# Iveco Crossway LE CITY 12M 1TI 2918: ex-Přerov, still in the plain Arriva
# blue (photo 449877): the Přerov sheet (Lubak91) with the white swoosh cut
# down to the short white Arriva wordmark and the green Přerov displays amber
LECITY_SRC = "vehicle-bus/mhd-prerov/crossway_le_city_12m/sprites/arrivamodra.png"


def rows_lecity():
    out = []
    for tiles in sheet_rows(load_sheet(LECITY_SRC))[:1]:
        row = []
        for t in tiles:
            t = t.copy()
            sw = np.all(t == (0xF6, 0xF6, 0xF6), axis=2)
            ys, xs = np.where(sw)
            if len(ys):
                order = np.argsort(ys)
                keep = set(order[len(order) // 2 - 1: len(order) // 2 + 1].tolist()) if len(order) > 2 else set()
                for i in range(len(ys)):
                    if i in keep:
                        continue
                    y, x = ys[i], xs[i]
                    for dx in (-1, 1, -2, 2):
                        if 0 <= x + dx < 128:
                            n = tuple(int(v) for v in t[y, x + dx])
                            if n != T and n[2] > n[0] + 0x40 and not sw[y, x + dx]:
                                t[y, x] = n
                                break
            t[np.all(t == (0x01, 0xDD, 0x01), axis=2)] = H.AMBER
            row.append(t)
        out.append(row)
    return out


# Scania Citywide LF 12M BEV (KAD EL3 84BE, Vrchlabí): black from the roof
# edge down to the wheel-arch tops, white skirt band, white roof and roof
# equipment; black front down to the headlamps over a white bumper (photos
# seznam-autobusu 402552, 415705). The Kladno Citywide LF sheet (Lubak91): its
# white belt under the windows turned black, the red band white, the light
# lower front black above the bumper.
CITYWIDE_SRC = "vehicle-bus/mhd-kladno/scania_citywide_lf_12m_cng/sprites/kladnobilocervena.png"
KAD_BLACK = (0x1C, 0x1C, 0x1E)


def rows_citywide_bev():
    src = sheet_rows(load_sheet(CITYWIDE_SRC))[:1]
    white = red_to_white_map(src)

    def blend(c):
        """red/white and red/black anti-aliasing pixels of the Kladno art: grey"""
        r, g, b = (int(v) for v in c)
        if is_red(c) or ((r << 16) | (g << 8) | b) in H.SPECIAL or r - max(g, b) <= 14:
            return None
        v = (r + g + b) // 3 + (0x10 if r > 0x90 else 0)
        return safe((min(255, v),) * 3)
    src = [[recolour(t, blend) for t in tiles] for tiles in src]
    rows = []
    for tiles in src:
        row = []
        for d, t in zip(DIRS, tiles):
            o = t.copy()
            dark = (t.max(axis=2) < 0x60) & ~is_bg(t)
            for x in range(128):
                for y in range(1, 127):
                    c = tuple(int(v) for v in t[y, x])
                    # the white belt: light pixel between the dark band and the red
                    if neutral(c, 0xC8) and dark[y - 1, x] and is_red(tuple(int(v) for v in t[y + 1, x])):
                        o[y, x] = sh(KAD_BLACK, "right")
            for y in range(128):
                for x in range(128):
                    c = tuple(int(v) for v in t[y, x])
                    if is_red(c):
                        o[y, x] = white.get(c, (0xE6, 0xE6, 0xE6))
            row.append(o)
        rows.append(row)
    # front: the light panel between the windscreen and the bumper turns black,
    # the lowest light row (the bumper) and the lamps stay
    for (tiles, srow) in zip(rows, src):
        for d, t, st in zip(DIRS, tiles, srow):
            geo = fit_box(st, d, [11.5, 12.0, 12.5])
            front = geo["face"] == 2
            front = front | np.roll(front, -1, 1)
            for x in range(128):
                ys = [y for y in range(128) if front[y, x] and tuple(t[y, x]) != T]
                if not ys:
                    continue
                def light(y):
                    c = tuple(int(v) for v in st[y, x])
                    return c != T and max(c) >= 0x80 and ((c[0] << 16) | (c[1] << 8) | c[2]) not in H.SPECIAL
                lights = [y for y in ys if light(y)]
                if not lights:
                    continue
                bottom = max(lights)
                seen_dark = False
                for y in ys:
                    c = tuple(int(v) for v in st[y, x])
                    if max(c) < 0x80:
                        seen_dark = True
                    elif seen_dark and light(y) and y < bottom:
                        t[y, x] = sh(KAD_BLACK, "front")
            # the white KAD logo on the black band behind the middle door
            if d in SLOPE:
                light = np.array([[neutral(tuple(int(v) for v in t[y, x]), 0xC8) and tuple(t[y, x]) != T
                                   for x in range(128)] for y in range(128)])
                for x, y in band_line(t, light, geo, d).items():
                    if 0.50 <= geo["frac"][y + 1, x] <= 0.60:
                        t[y - 1, x] = LOGO_W
    return rows


def save_sheet(rows, path, allow=()):
    """write a sheet; specials other than lit glass and lamps only where the
    source art already used them (allow)"""
    out = np.zeros((128 * len(rows), 1024, 3), dtype=np.uint8)
    out[:, :] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    flat = out.reshape(-1, 3).astype(np.int64)
    used = set(np.unique((flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]).tolist())
    bad = (used & H.SPECIAL) - H.ALLOWED - set(allow)
    if bad:
        raise SystemExit(f"{path}: unintended special colours {sorted(hex(b) for b in bad)}")
    Image.fromarray(out).save(path)
    return out


def source_specials(rel):
    a = load_sheet(rel).reshape(-1, 3).astype(np.int64)
    return set(np.unique((a[:, 0] << 16) | (a[:, 1] << 8) | a[:, 2]).tolist()) & H.SPECIAL


# ====================================================================== families
def f_(cost, payload, speed, weight, run, fixed, intro, length, engine, power, gear,
       intro_month=1, retire=2060, smoke=None):
    f = dict(cost=cost, payload=payload, speed=speed, weight=weight, runningcost=run,
             fixed_cost=fixed, intro_year=intro, intro_month=intro_month, retire_year=retire,
             retire_month=12, waytype="road", freight="Passagiere", length=length,
             engine_type=engine, power=power, gear=gear)
    if smoke:
        f["smoke"] = smoke
    return f


def ebn_rows(spec, liv):
    return lambda: build_ebn(spec, liv)


def rj_rows(cls, liv):
    return lambda: [row_for(cls, liv)]


IREDO = ("IREDO", "IREDO", "IREDO")
TRUTNOV = ("MHDTrutnov", "MHD Trutnov", "MHD Trutnov")
SPINDL = ("MHDSpindleruvMlyn", "MHD Špindlerův Mlýn", "MHD Špindlerův Mlýn")
EBUS = ("electric bus", "elektrobus")
EMIDI = ("electric midibus", "elektrický midibus")
BUS = ("bus", "autobus")
MIDI = ("midibus", "midibus")

RENDER_EBN = ("original box-model render (vojtechzicha): the SOR EBN body of\n"
              "tools/busrender/dpmhk.py painted by khk_town.KVeh.")
RENDER_CW = ("original box-model render (vojtechzicha): {cls} of\n"
             "tools/busrender/iredo_models.py with the livery of khk_town.py.")
TU_NAME = ("MHD Trutnov light blue", "MHD Trutnov světle modrá")
TD_NAME = ("white-black with the red figure · Transdev Čechy", "bílo-černá s červenou postavou · Transdev Čechy")

FAMILIES = {
    # ------------------------------------------------------------ IREDO
    "iredo/sor_ebn_9_5": dict(
        agency=IREDO, type="SOR_EBN_9_5", name=("SOR EBN 9,5", "SOR EBN 9,5"), copyright="vojtechzicha",
        vehicles=[dict(id="SOR_EBN_9_5", display="EBN 9,5", role=EMIDI,
                       fields=f_(650000, 60, 70, 10, 15, 80, 2018, 7, "battery", 120, 57, intro_month=10))],
        liveries=[("cds", "yellow · CDS Náchod", "žlutá · CDS Náchod", ebn_rows(EBN95_M, "cds")),
                  ("transdev", TD_NAME[0], TD_NAME[1], ebn_rows(EBN95_N, "td"))],
        note="SOR EBN 9,5 battery midibus, 9.5 m, doors 1-2-0, about 60 places.\n"
             "In 2026: CDS Náchod 6H9 8020 'Danny' and 6H9 8040 'Irena' (2018, MHD Náchod\n"
             "381 / 383): yellow, the older SOR face (photos seznam-autobusu 393906,\n"
             "265676); Transdev Čechy EL2 61FA (2025, MHD Rychnov n. Kn. since 3/2026):\n"
             "the Rychnov e-bus scheme, the current SOR face (photos 441351, 449827).",
        sprite=RENDER_EBN),
    "iredo/sor_ebn_11_1": dict(
        agency=IREDO, type="SOR_EBN_11_1", name=("SOR EBN 11,1", "SOR EBN 11,1"), copyright="vojtechzicha",
        vehicles=[dict(id="SOR_EBN_11_1", display="EBN 11,1", role=EBUS,
                       fields=f_(900000, 85, 80, 12, 20, 150, 2018, 8, "battery", 120, 57, intro_month=9))],
        liveries=[("transdev", TD_NAME[0], TD_NAME[1], ebn_rows(EBN11_N, "td")),
                  ("kadzelena", "green metallic · KAD", "zelená metalíza · KAD", ebn_rows(EBN11_M, "kad"))],
        note="SOR EBN 11,1 battery bus, 11.1 m, 3 doors, about 85 places, TAM 1052 120 kW.\n"
             "In 2026: Transdev Čechy EL2 60FA and EL2 62FA (2026, MHD Rychnov n. Kn.): the\n"
             "Rychnov e-bus scheme, the current SOR face (photos 441351, vhdfoto 42828);\n"
             "KAD 6H9 5510 (2018, MHD Vrchlabí 480): grass-green metallic, white roof, since\n"
             "10/2025 (photo 439058), the older face. Not the DPMHK EBN 11 paint\n"
             "(sorzelenametaliza: dark green nose and skirt, white side panels), so a\n"
             "livery of its own.",
        sprite=RENDER_EBN),
    "iredo/citywide_lf_12m_bev": dict(
        agency=IREDO, type="Citywide_LF_12M_BEV",
        name=("Scania Citywide LF 12M BEV", "Scania Citywide LF 12M BEV"), copyright="Lubak91",
        vehicles=[dict(id="Citywide_LF_12M_BEV", display="Citywide LF 12M BEV", role=EBUS,
                       fields=f_(1000000, 85, 80, 13, 20, 150, 2020, 8, "battery", 250, 55))],
        liveries=[("kadcernobila", "black-white · KAD", "černo-bílá · KAD", rows_citywide_bev)],
        allow=(0xC1B1D1, 0xE3E3FF),
        note="Scania Citywide LF 12M BEV, 12 m, doors 2-2-2 (2020, ex demonstrator).\n"
             "In 2026: KAD EL3 84BE (MHD Vrchlabí 480, since 7/2023): black from the roof\n"
             "edge to the wheel-arch tops, white skirt band and roof (photos 402552, 415705).",
        sprite="Lubak91's Citywide LF 12M body (the Kladno CNG sheet), repainted by\n"
               "khk_town.rows_citywide_bev: white belt black, red band white, the lower\n"
               "front black over a white bumper, white KAD logo on the band. The rear keeps\n"
               "the white of the source (no photo of the rear found)."),
    # ------------------------------------------------------------ Trutnov
    "mhd-trutnov/perun_26bb_he": dict(
        agency=TRUTNOV, type="Perun_26BB_HE", name=("Škoda Perun 26BB HE", "Škoda Perun 26BB HE"),
        copyright="TommPa9",
        vehicles=[dict(id="Perun_26BB_HE", display="26BB HE", role=EBUS,
                       fields=f_(1000000, 85, 80, 12, 20, 150, 2018, 8, "battery", 160, 54, intro_month=12,
                                 retire=2050))],
        liveries=[("trutnovmhd", TU_NAME[0], TU_NAME[1], rows_26bb)],
        note="Škoda Perun 26BB HE battery bus (Solaris Urbino 12 IV body), 12 m, 3 doors.\n"
             "Trutnov MHD (ARRIVA autobusy): 6E1 8260-8263, 4 cars, in service since 2/2019.",
        sprite="TommPa9's Solaris Urbino 12 IV electric (the Tábor sheet, roof battery\n"
               "fairing; it has the Urbino IV rear window line, which the smaller VTPsim\n"
               "Urbino III of the Třinec 26BB lacks), repainted by khk_town.rows_26bb: COMETT\n"
               "white and the chequered patch Arriva light blue, pixel mosaic and white\n"
               "TRUTNOV MHD logo (photos 232403, 414852)."),
    "mhd-trutnov/sor_nbg_18": dict(
        agency=TRUTNOV, type="SOR_NBG_18", name=("SOR NBG 18", "SOR NBG 18"), copyright="VTPsim",
        vehicles=[dict(id="SOR_NBG_18-A", display="SOR NBG 18", role=("front section", "přední díl"), row=0,
                       head=True, tail=False, next=["SOR_NBG_18-B"],
                       fields=dict(f_(540000, 90, 80, 9, 25, 128, 2018, 8, "diesel", None, None, retire=2050))),
                  dict(id="SOR_NBG_18-B", display="SOR NBG 18", role=("rear section", "zadní díl"), row=1,
                       head=False, tail=True, prev=["SOR_NBG_18-A"],
                       fields=f_(390000, 60, 80, 8, 11, 56, 2018, 8, "diesel", 213, 62, retire=2050))],
        liveries=[("trutnovmhd", TU_NAME[0], TU_NAME[1], rows_nbg18)],
        note="SOR NBG 18 (CNG), 18.75 m, 4 doors, pusher (Iveco Cursor 8 CNG 213 kW).\n"
             "Trutnov MHD: 6E1 3718-3720, 3 cars (2018). Fixed consist: front section A +\n"
             "powered rear section B. CNG: engine_type diesel (upstream convention), no smoke.",
        sprite="VTPsim's NB 18 body as repainted for the Kladno NBG 18 (CNG tank fairing),\n"
               "white and red turned Arriva light blue by khk_town.rows_nbg18, the black\n"
               "band under the windscreen kept, pixel mosaic on the rear half of the front\n"
               "section and on the rear section, TRUTNOV logo on both (photos 398768, 442882)."),
    "mhd-trutnov/sor_nb_12": dict(
        agency=TRUTNOV, type="SOR_NB_12", name=("SOR NB 12 City", "SOR NB 12 City"), copyright="VTPsim",
        vehicles=[dict(id="SOR_NB_12", display="NB 12", role=BUS,
                       fields=f_(604804, 88, 80, 11, 25, 128, 2009, 8, "diesel", 210, 54, intro_month=8,
                                 smoke="Diesel_small"))],
        liveries=[("trutnovmhd", TU_NAME[0], TU_NAME[1], rows_nb12)],
        note="SOR NB 12 City, 12.18 m, 4 doors. Trutnov MHD: 8T9 2189 (2013, ex MHD Třinec,\n"
             "in Trutnov since 11/2022, repainted in the Trutnov scheme; photo 415210).",
        sprite="VTPsim's NB 12 (the DPP city sheet), repainted by khk_town.rows_nb12."),
    "mhd-trutnov/crossway_le_city_12m": dict(
        agency=TRUTNOV, type="Crossway_LE_City_12M",
        name=("Iveco Crossway LE City 12M", "Iveco Crossway LE City 12M"), copyright="Lubak91",
        vehicles=[dict(id="Crossway_LE_City_12M", display="Crossway LE City 12M", role=BUS,
                       fields=f_(800000, 95, 80, 12, 26, 135, 2017, 8, "diesel", 243, 56, retire=2050,
                                 smoke="Diesel_small"))],
        liveries=[("arrivamodra", "Arriva light blue", "Arriva světle modrá", rows_lecity)],
        note="Iveco Crossway LE City 12M, 3 doors. Trutnov MHD reserve: 1TI 2918 (2017, ex\n"
             "MHD Přerov, in Trutnov since 3/2025), plain Arriva light blue without the\n"
             "Trutnov graphics (photo 449877).",
        sprite="the Přerov sheet (Lubak91's art), the white swoosh cut down to the short\n"
               "Arriva wordmark and the displays amber (khk_town.rows_lecity)."),
    "mhd-trutnov/sor_bn_8_5": dict(
        agency=TRUTNOV, type="SOR_BN_8_5", name=("SOR BN 8.5", "SOR BN 8,5"), copyright="VTPsim",
        vehicles=[dict(id="SOR_BN_8_5", display="BN 8,5", role=MIDI,
                       fields=f_(400000, 60, 90, 7, 21, 140, 2010, 8, "diesel", 137, 53, smoke="Diesel_small"))],
        liveries=[("bila", "white", "bílá", rows_bn85)],
        note="SOR BN 8,5 midibus. Trutnov MHD: 5E9 3012 (2017), line 7 since 2/2025, plain\n"
             "white with a small Arriva logo (photo 442526).",
        sprite="VTPsim's BN 9,5 shortened (the DPP BN 8,5 sheet), its red turned into the\n"
               "white of the same face (khk_town.rows_bn85)."),
    "mhd-trutnov/crossway_pro_13m": dict(
        agency=TRUTNOV, type="Crossway_Pro_13M", name=("Iveco Crossway PRO 13M", "Iveco Crossway PRO 13M"),
        copyright="vojtechzicha",
        vehicles=[dict(id="Crossway_Pro_13M", display="Crossway PRO 13M", role=BUS,
                       fields=f_(680000, 85, 100, 12, 27, 139, 2017, 9, "diesel", 265, 54,
                                 smoke="Diesel_small"))],
        liveries=[("arrivabila", "white", "bílá", rj_rows(TuCrosswayPro13, "arrivabila"))],
        note="Iveco Crossway PRO 13M, three axles. Trutnov MHD reserve since 2024: 6E7 6343\n"
             "(2015, ex Germany), white with the small light-blue Arriva logo (photo 418274).",
        sprite=RENDER_CW.format(cls="CrosswayPro13")),
    # ------------------------------------------------------------ Špindlerův Mlýn
    "mhd-spindleruv-mlyn/crossway_le_line_12m": dict(
        agency=SPINDL, type="Crossway_LE_Line_12M",
        name=("Iveco Crossway LE LINE 12M", "Iveco Crossway LE LINE 12M"), copyright="vojtechzicha",
        vehicles=[dict(id="Crossway_LE_Line_12M", display="Crossway LE LINE 12M", role=BUS,
                       fields=f_(640000, 92, 100, 11, 26, 131, 2014, 8, "diesel", 243, 54,
                                 smoke="Diesel_small"))],
        liveries=[("smsmbila", "white", "bílá", rj_rows(SpLELine, "smsmbila"))],
        note="Iveco Crossway LE LINE 12M. Služby města Špindlerův Mlýn: 6H5 8777 (2016) and\n"
             "7H1 6545 (2019), white with the SMŠM swirl logo, green LED displays (photos\n"
             "seznam-autobusu 411225, 449739).",
        sprite=RENDER_CW.format(cls="CrosswayLELine")),
    "mhd-spindleruv-mlyn/irisbus_crossway_le_12m": dict(
        agency=SPINDL, type="Irisbus_Crossway_LE_12M",
        name=("Irisbus Crossway LE 12M", "Irisbus Crossway LE 12M"), copyright="vojtechzicha",
        vehicles=[dict(id="Irisbus_Crossway_LE_12M", display="Crossway LE 12M", role=BUS,
                       fields=f_(600000, 92, 100, 11, 24, 122, 2007, 8, "diesel", 243, 54,
                                 smoke="Diesel_small"))],
        liveries=[("smsmcervena", "red", "červená", rj_rows(SpIrisbusLE, "smsmcervena")),
                  ("bila", "white", "bílá", rj_rows(SpIrisbusLE, "bila"))],
        note="Irisbus Crossway LE 12M. Služby města Špindlerův Mlýn: 8H1 9232 (2013, ex Slovak\n"
             "Lines, since 1/2023) all-over red with the SMŠM logo (photo 440624); 6B9 6628\n"
             "(2010, since 2/2026, skibus 696003) plain white (photo 422585). 6H7 9955 wears\n"
             "a Raiffeisenbank advert wrap: not drawn.",
        sprite=RENDER_CW.format(cls="IrisbusCrosswayLE")),
}


def yaml_text(f):
    ag, ag_en, ag_cs = f["agency"]
    L = [f"agency: {ag}",
         f'type: "{f["type"]}"',
         "# Sprites carry their own lane placement (body footprint on the median of",
         "# native pak128.cs 12 m buses), so no extra shift.",
         "image_offset: [0, 0]",
         "# Windows light up at night only while passengers are aboard.",
         "windows_lit_when_loaded: true",
         f"copyright: {f['copyright']}",
         "",
         "display:",
         f'  agency_en: "{ag_en}"',
         f'  agency_cs: "{ag_cs}"',
         f'  family_en: "{f["name"][0]}"',
         f'  family_cs: "{f["name"][1]}"',
         ""]
    L += ["# " + l for l in f["note"].split("\n")]
    L += [("# Sprite: " if i == 0 else "# ") + l for i, l in enumerate(f["sprite"].split("\n"))]
    L += ["# Regenerate with tools/busrender/khk_town.py (family.yaml: --yaml).", "", "vehicles:"]
    for i, v in enumerate(f["vehicles"]):
        if i:
            L.append("")
        L += [f'  - id: "{v["id"]}"',
              f'    display_id: "{v["display"]}"',
              f'    role_en: "{v["role"][0]}"',
              f'    role_cs: "{v["role"][1]}"',
              f'    row: {v.get("row", 0)}']
        for k in ("head", "tail"):
            if k in v:
                L.append(f"    {k}: {str(v[k]).lower()}")
        L.append("    prev: [" + ", ".join(f'"{p}"' for p in v.get("prev", [])) + "]")
        L.append("    next: [" + ", ".join(f'"{p}"' for p in v.get("next", [])) + "]")
        L.append("    fields:")
        for k, val in v["fields"].items():
            if val is not None:
                L.append(f"      {k}: {val}")
    L += ["", "liveries:"]
    for slug, en, cs, _ in f["liveries"]:
        L += [f"  - color: {slug}", f'    name_en: "{en}"', f'    name_cs: "{cs}"']
    return "\n".join(L) + "\n"


def preview(rows, path, z=4):
    a = np.concatenate([np.concatenate(t, axis=1) for t in rows], axis=0).copy()
    a[is_bg(a)] = (96, 104, 96)
    Image.fromarray(a).resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST).save(path)


def main(argv):
    pv = None
    if "--preview" in argv:
        i = argv.index("--preview")
        pv = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
        os.makedirs(pv, exist_ok=True)
    do_yaml = "--yaml" in argv
    argv = [a for a in argv if a != "--yaml"]
    for key, f in FAMILIES.items():
        if argv and key not in argv and key.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, "vehicle-bus", *key.split("/"))
        os.makedirs(os.path.join(d, "sprites"), exist_ok=True)
        for slug, _, _, fn in f["liveries"]:
            rows = fn()
            save_sheet(rows, os.path.join(d, "sprites", slug + ".png"), f.get("allow", ()))
            if pv:
                preview(rows, os.path.join(pv, f"{key.replace('/', '-')}-{slug}.png"))
            print(f"vehicle-bus/{key}/sprites/{slug}.png  rows={len(rows)}")
        if do_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(yaml_text(f))


if __name__ == "__main__":
    main(sys.argv[1:])
