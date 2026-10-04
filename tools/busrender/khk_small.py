"""Small buses, midibuses and vans of Kralovehradecky kraj (KHK): the IREDO
midibuses (VZ-IREDO-bus) and the town MHD minibuses of Jicin, Nova Paka and
Kostelec nad Orlici (VZ-MHDJicin-bus, VZ-MHDNovaPaka-bus, VZ-MHDKostelec-bus).

    python tools/busrender/khk_small.py [family ...] [--yaml] [--preview DIR]

Without --yaml only the sheets are written; with --yaml the family.yaml files
are (re)generated from FAMILIES too (review the diff).

Two methods, picked per type by which one reads better at pak scale:

* REPAINT (Dekstra LE 37, Rosero First, Dekstra LF 38, NovoCiti Life): the
  hand-drawn VTPsim midibus sheets already in the repo keep their silhouette
  (Daily bonnet under the big raked windscreen, rear-overhang door, roof pod)
  and shading; every light body pixel is recoloured by zone and multiplied by
  its own shade factor. The zones come from a box model fitted per view
  (geometry(), from the Prague PID repaints): face, u (0 front .. 1 rear),
  h (0 side top edge .. 1 skirt), lr (0 vehicle left .. 1 right), and the
  window-band bottom hb. Decals are pixel glyphs in screen columns, so they
  read left to right in both side views.
* RENDER (Stratos L 27, Sprinter 519, Mercus Sprinter, Iveco Daily 50C13,
  Renault Master): no hand-drawn base exists for these van-derived bodies, so
  they are box renders on the shipped small-bus renderer of praha_small.py
  (imported read-only; its Bus model subclassed with a livery object), at real
  length on the native lane like the Erduman Sprinter.

Every IREDO bus carries the kraj sticker: a light panel over the upper rear
window with a tiny red + blue chevron (town MHD vehicles outside IREDO do not).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import praha_small as PS                                  # noqa: E402  (read-only import)
from praha_small import Bus, mk, col, inr                 # noqa: E402
from render import render, DIRS                           # noqa: E402
from dpmhk import ORIGINS                                 # noqa: E402

T = (231, 255, 255)

# ------------------------------------------------------------------ palette
GLASS = (0x4D, 0x4D, 0x4D)         # special 28: lit at night
GLASS2 = (0x57, 0x65, 0x6F)        # special 16: lit at night (lighter glass)
HEADL = (0xFF, 0xFF, 0x53)
TAILL = (0xFF, 0x21, 0x1D)
AMBER = (0xF0, 0xA0, 0x18)         # destination LEDs (plain colour)
BLACK = (0x14, 0x14, 0x16)
FRAME = (0x16, 0x16, 0x18)
DARK = (0x2A, 0x2B, 0x2E)          # black plastic bumpers / trims
DGREY = (0x48, 0x4A, 0x4E)         # dark grey rubbing strips (Daily, Master)
SILVER = (0xB4, 0xB6, 0xBA)
PLATE = (0xE6, 0xE6, 0xE2)
KHK_PANEL = (0xE4, 0xE5, 0xE8)     # the KHK sticker panel over the rear window
KHK_RED = (0xD6, 0x22, 0x2A)
KHK_BLUE = (0x1E, 0x4F, 0xA0)

WHITE = (0xF2, 0xF2, 0xF0)
CDS_YELLOW = (0xF6, 0xC4, 0x00)
CDS_RED = (0xD8, 0x1E, 0x24)
CDS_INK = (0x1E, 0x2E, 0x6A)       # dark blue NACHOD
PT_YELLOW = (0xF7, 0xB2, 0x14)
PT_RED = (0xD6, 0x22, 0x1C)
TD_RED = (0xD8, 0x1E, 0x2C)        # Transdev red

# Dvur Kralove nad Labem MHD (KAD), the town photo wrap reduced to its colour
# fields; shared with the Crossway LE City 10,8M of the same town (see the
# DK_* docstring below and DvurKralove).
DK_PALETTE = {
    "white": (0xF2, 0xF2, 0xF0),       # base body, roof, A/C
    "green": (0x46, 0xAA, 0x3A),       # waist band, skirt, pillar panel, bonnet edge (~RAL 6018)
    "green_dk": (0x2E, 0x7E, 0x28),    # lettering band shadow / logo plate edge
    "logo": (0x3A, 0x3C, 0x40),        # dark-grey town logo plate
    "sky": (0x86, 0xAE, 0xD8),         # photo: sky over the square
    "facade": (0xD6, 0xB8, 0x86),      # photo: arcaded square, ochre / beige houses
    "facade2": (0xE8, 0xD8, 0xB4),     # photo: lighter house fronts
    "roofs": (0xA4, 0x4C, 0x34),       # photo: red roofs / town hall
    "bauble": (0x7A, 0x4E, 0x30),      # photo: blown-glass baubles, dark copper
    "bauble_hi": (0xC8, 0x9A, 0x48),   # photo: bauble gold highlights
    "lion": (0xB8, 0x82, 0x44),        # photo: Safari Park lions (tawny)
    "lion_dk": (0x6E, 0x4A, 0x28),     # photo: mane
}

SPECIAL = PS.SPECIAL
ALLOWED = PS.ALLOWED


def hx(c):
    return (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])


def unspecial(c):
    c = tuple(int(v) for v in c)
    if hx(c) in SPECIAL and hx(c) not in ALLOWED:
        c = (c[0], c[1], c[2] + 1 if c[2] < 255 else 254)
    return c


# ====================================================================== repaint
# box-model coordinates of a hand-drawn bus sprite (per view)
NONE, SIDE, ROOF, FRONT, REAR, EXCESS = 0, 1, 2, 3, 4, 5
VIS = {"ne": "R", "e": "R", "n": "R", "sw": "L", "w": "L", "s": "L", "se": None, "nw": None}
SLOPE = {"w": 0.5, "e": 0.5, "n": -0.5, "s": -0.5}


def geometry(tile, d, sp):
    """Per-pixel face / u / h / lr of a bus sprite tile from its box spec.

    ne / sw: dict(xf, xr, top, bot[, rooftop]) side face columns at the front /
    rear end, first side-face row, skirt row (pixels above rooftop are cut);
    w / n / e / s: dict(xf, xr, top, bot, W[, clip]) side face corners, the
    side's top edge y = top + slope (x - xf), W the width in across steps
    (roof pixels farther than W + clip are cut); nw / se: dict(x0, x1, rf, rr,
    e0, e1) roof rows front .. rear end, end-face rows top .. bottom."""
    m = ~np.all(tile == np.array(T), axis=2)
    face = np.zeros((128, 128), np.int8)
    u = np.full((128, 128), np.nan)
    h = np.full((128, 128), np.nan)
    lr = np.full((128, 128), np.nan)
    ys, xs = np.where(m)
    if d in ("ne", "sw"):
        xf, xr, top, bot = sp["xf"], sp["xr"], sp["top"], sp["bot"]
        lo, hi = min(xf, xr), max(xf, xr)
        rooftop = ys.min()
        for y, x in zip(ys, xs):
            if lo <= x <= hi:
                uu = (x - xf) / (xr - xf)
                if y >= top:
                    face[y, x] = SIDE; u[y, x] = uu; h[y, x] = (y - top) / max(1, bot - top)
                elif "rooftop" in sp and y < sp["rooftop"]:
                    face[y, x] = EXCESS
                else:
                    face[y, x] = ROOF; u[y, x] = uu
                    v = (top - y) / max(1, top - sp.get("rooftop", rooftop))
                    lr[y, x] = (1 - v) if VIS[d] == "R" else v
            else:
                front = (x - xf) * (xf - xr) > 0 or x == xf
                face[y, x] = FRONT if front else REAR
                h[y, x] = (y - top) / max(1, bot - top)
                lr[y, x] = 0.5
    elif d in SLOPE:
        s = SLOPE[d]
        wx, wy = (2.0 if s > 0 else -2.0), -1.0
        xf, xr, top, bot, W = sp["xf"], sp["xr"], sp["top"], sp["bot"], sp["W"]
        lo, hi = min(xf, xr), max(xf, xr)
        H = bot - top
        vis_end_x = xf if (xf - xr) * wx > 0 else xr
        vis_end = FRONT if vis_end_x == xf else REAR
        for y, x in zip(ys, xs):
            ytop = top + s * (x - xf)
            if lo <= x <= hi and y >= ytop - 0.01:
                face[y, x] = SIDE; u[y, x] = (x - xf) / (xr - xf); h[y, x] = (y - ytop) / H
                continue
            t = (y - top - s * (x - xf)) / (wy - s * wx)
            xe = x - t * wx
            if lo - 0.5 <= xe <= hi + 0.5 and t >= 0:
                if sp.get("clip") and t > W + sp["clip"]:
                    face[y, x] = EXCESS
                    continue
                face[y, x] = ROOF
                u[y, x] = min(1, max(0, (xe - xf) / (xr - xf)))
                v = min(1.0, t / W)
                lr[y, x] = (1 - v) if VIS[d] == "R" else v
                continue
            ta = (x - vis_end_x) / wx
            yt = top + s * (vis_end_x - xf) + ta * wy
            face[y, x] = vis_end
            h[y, x] = (y - yt) / H
            a = min(1.0, max(0.0, ta / W))
            lr[y, x] = (1 - a) if VIS[d] == "R" else a
    else:
        x0, x1, rf, rr, e0, e1 = sp["x0"], sp["x1"], sp["rf"], sp["rr"], sp["e0"], sp["e1"]
        end = FRONT if d == "se" else REAR
        for y, x in zip(ys, xs):
            a = (x - x0) / max(1, x1 - x0)
            if min(rf, rr) <= y <= max(rf, rr):
                face[y, x] = ROOF; u[y, x] = (y - rf) / (rr - rf)
            else:
                face[y, x] = end
                h[y, x] = (y - e0) / max(1, e1 - e0)
            lr[y, x] = (1 - a) if d == "se" else a
    return face, u, h, lr


def neutral(c, tol=14):
    return max(int(v) for v in c) - min(int(v) for v in c) <= tol


KEEP = {0xFF211D, 0xFFFF53, 0x4D4D4D, 0x57656F}


def white_paint(c, min_v=0xA8):
    """body paint of a white base sheet: light neutral pixels"""
    return neutral(c) and max(int(v) for v in c) >= min_v and hx(c) not in KEEP


def glassy(c):
    return hx(c) in (0x4D4D4D, 0x57656F, 0x6B6B6B, 0x9B9B9B) or (neutral(c, 20) and max(int(v) for v in c) < 0x60)


def band_bottom(tile, face, h):
    """median h of the lowest window-band pixel (first glass run from the top)"""
    vals = []
    for x in range(128):
        ys = sorted(y for y in range(128) if face[y, x] == SIDE)
        if len(ys) < 4:
            continue
        seen, last = False, None
        for y in ys:
            if glassy(tile[y, x]):
                seen, last = True, y
            elif seen and white_paint(tile[y, x]):
                break
        if last is not None:
            vals.append(h[last, x])
    return float(np.median(vals)) if vals else 0.5


class Px:
    """one body pixel of a repainted tile"""
    def __init__(self, **kw):
        self.__dict__.update(kw)

    @property
    def rk(self):
        """row below the window-band bottom (1 = first painted row)"""
        return int(round((self.h - self.hb) * self.H))

    @property
    def nrows(self):
        return int(round((1 - self.hb) * self.H))

    @property
    def kb(self):
        """row counted up from the skirt (0 = lowest row)"""
        return int(round((1 - self.h) * self.H))

    def seen(self):
        """screen column along the side, left to right as seen"""
        return (1 - self.u) * self.N if self.vis == "R" else self.u * self.N

    def glyph(self, rows, uc, r0):
        """pixel of a glyph (list of strings, top row first) centred at u = uc,
        its top row r0 rows below the band; read left to right in both sides"""
        c0 = ((1 - uc) * self.N if self.vis == "R" else uc * self.N) - len(rows[0]) / 2
        c = int(math.floor(self.seen() - c0 + 0.5))
        r = self.rk - r0
        if 0 <= r < len(rows) and 0 <= c < len(rows[0]):
            return rows[r][c]
        return None


class RLivery:
    """repaint livery: body colour of every light body pixel (None = keep)."""
    body = WHITE
    roof = None                    # None = body
    pod = None                     # roof A/C pod (grey pixels of the base roof)
    sticker = True                 # the KHK sticker on the rear window

    def paint(self, px):
        if px.face == ROOF:
            if px.pod and self.pod:
                return self.pod
            return self.roof or self.body
        if px.face == SIDE:
            return self.side(px) or self.body
        if px.face == FRONT:
            return self.front(px) or self.body
        if px.face == REAR:
            return self.rear(px) or self.body
        return None

    def side(self, px):
        return None

    def front(self, px):
        return None

    def rear(self, px):
        return None

    def glass(self, px):
        """colour for a side glass pixel (None = keep the glass)"""
        return None


class RBila(RLivery):
    """plain white (BusLine KHK, KAD, Transdev Cechy without the figure)."""
    body = None

    def paint(self, px):
        return None


class RTransdev(RLivery):
    """white with the big red Transdev figure on the lower side behind the
    front door, small red mark on the front."""
    # the figure as seen (as on the IREDO coaches, iredo_models.Transdev): hook
    # stroke on the left, dot head top right, body / leg running down right
    FIG = ["..##.#",
           ".#....",
           "#..##.",
           "#.##..",
           "#.#...",
           "#..#..",
           "#...#."]
    UC = 0.47

    def side(self, px):
        g = px.glyph(self.FIG, self.UC, 1)
        if g == "#":
            return TD_RED
        return None

    def front(self, px):
        if 0.62 <= px.h < 0.72 and 0.20 <= px.lr < 0.34:
            return TD_RED
        return None


class RCDS(RLivery):
    """CDS Nachod: all-over yellow, big red CDS + dark blue NACHOD between
    the axles under the windows, black front bumper."""
    body = CDS_YELLOW
    roof = (0xF8, 0xCC, 0x10)
    pod = (0xF8, 0xCC, 0x10)
    TXT = ["###.##..###",
           "#...#.#.#..",
           "#...#.#..##",
           "###.##..###"]
    UC = 0.56

    def side(self, px):
        g = px.glyph(self.TXT, self.UC, 1)
        if g == "#":
            return CDS_RED
        if px.rk == 5 and abs(px.seen() - ((1 - self.UC) * px.N if px.vis == "R" else self.UC * px.N)) < 4:
            return CDS_INK                         # NACHOD under the CDS, a dark blue dash
        return None

    def front(self, px):
        if px.h >= 0.80:
            return DARK
        return None

    def rear(self, px):
        if px.h >= 0.88:
            return DARK
        return None


class RPTransport(RLivery):
    """P-transport Broumov: yellow-orange, red line under the windows, red
    front lower corner and a red sweep rising towards the rear, red bumpers,
    red roof A/C pod."""
    body = PT_YELLOW
    roof = (0xF8, 0xBA, 0x22)
    pod = PT_RED

    def side(self, px):
        n = px.nrows
        k = px.kb
        u = px.u
        if px.rk == 1:
            return PT_RED                          # line under the windows
        if u < 0.22 and px.rk == 2:
            return PT_RED
        if u < 0.15 and px.rk >= 2:
            return PT_RED                          # front lower corner
        xs, xe = 0.12, 0.76
        if xs <= u < xe:
            t = (u - xs) / (xe - xs)
            if k < (n - 2) * 0.75 * t ** 1.3:
                return PT_RED
        if u >= 0.94 and k <= 1:
            return PT_RED
        if k == 0:
            return PT_RED                          # red skirt edge
        return None

    def front(self, px):
        if px.h >= 0.70:
            return PT_RED
        return None

    def rear(self, px):
        if px.h >= 0.80:
            return PT_RED
        return None


class RBiloCerna(RLivery):
    """Rosero First FCLEI of MHD Tyniste (Transdev Cechy, 2026): white with
    the black window band and black A-pillars, black lower bumpers and sills."""
    body = None

    def paint(self, px):
        if px.face == SIDE and px.kb == 0:
            return DARK
        if px.face == FRONT and px.h >= 0.80:
            return DARK
        if px.face == REAR and px.h >= 0.88:
            return DARK
        return None


class DvurKralove(RLivery):
    """Dvur Kralove nad Labem MHD (KAD), artist Jiri Holan's town wrap reduced
    to its colour fields (palette DK_PALETTE). Zone layout, reusable on any
    body (u = 0 front .. 1 rear, rows counted under the window band):

    * white body, roof and A/C;
    * green waist band: the first row under the windows, full length, and on
      the front a green edge along the bonnet under the windscreen;
    * green skirt: the lowest body row, full length, and the front / rear
      bumper rows;
    * photo panel between the two bands, from behind the front door to the
      rear end, in three fields front to rear: lions (tawny with dark mane
      blocks), the arcaded square (sky row, then ochre / beige houses with a
      red-roof row) and the blown-glass baubles (dark copper with gold
      highlights); the panel ahead of it, by the front door, stays white
      (KAD logo and town arms there are too small to draw);
    * one green vertical panel on a window pillar (Dekstra: just ahead of the
      rear door; Crossway: just behind the front door) with a dark-grey logo
      pixel;
    * rear: white over a black window, green band, a square-photo strip and
      a green bumper.
    """
    body = DK_PALETTE["white"]
    P0 = 0.30                    # photo panel start (u), behind the front door
    FIELDS = (0.50, 0.75)        # field boundaries: lions | square | baubles
    PILLAR = 0.66                # u of the green window pillar panel

    def photo(self, u, r, n, dither):
        P = DK_PALETTE
        f0, f1 = self.FIELDS
        if u < f0:                                  # lions
            return P["lion_dk"] if (r == 1 and dither) or (r >= n - 1 and not dither) else P["lion"]
        if u < f1:                                  # town square
            if r == 0:
                return P["sky"]
            if r == 1:
                return P["roofs"]
            return P["facade"] if dither else P["facade2"]
        return P["bauble_hi"] if dither and r % 2 else P["bauble"]   # baubles

    def side(self, px):
        P = DK_PALETTE
        n = px.nrows
        if px.rk < 1:
            return None                             # above the windows: white
        if px.rk == 1 or px.kb == 0:
            return P["green"]
        if px.u >= self.P0:
            r = px.rk - 2                           # 0 = first photo row
            d = (int(px.seen()) + px.rk) % 2 == 0
            return self.photo(px.u, r, n - 2, d)
        return None

    def glass(self, px):
        if abs(px.u - self.PILLAR) * px.N < 0.75:
            return DK_PALETTE["logo"] if px.rk == -2 else DK_PALETTE["green"]
        return None

    def front(self, px):
        P = DK_PALETTE
        if px.h >= 0.88:
            return P["green"]
        if 0.30 <= px.h < 0.42 and (px.lr < 0.25 or px.lr > 0.75):
            return P["green"]                       # green edge along the bonnet
        return None

    def rear(self, px):
        P = DK_PALETTE
        if px.h >= 0.90:
            return P["green"]
        if 0.50 <= px.h < 0.60:
            return P["green"]
        if 0.60 <= px.h < 0.90:
            return P["facade"] if int(px.x) % 2 else P["sky" if px.h < 0.70 else "facade2"]
        return None


def repaint(tiles, spec, liv, ref=0xEE, roof_k=1.05, ac=None, sticker=True, pods=True):
    """repaint a base row; ac = (u0, u1) draws a flat roof A/C box; pods: the
    grey roof pixels of the base are a roof pod (else only roof lines)"""
    out = []
    for c, d in enumerate(DIRS):
        t = tiles[c]
        face, u, h, lr = geometry(t, d, spec[d])
        hb = band_bottom(t, face, h) if d not in ("nw", "se") else 0.5
        sp = spec[d]
        H = sp.get("bot", 0) - sp.get("top", 0) if d not in ("nw", "se") else 1
        N = abs(sp.get("xr", 0) - sp.get("xf", 0)) if d not in ("nw", "se") else 1
        new = t.copy()
        for y in range(128):
            for x in range(128):
                f = face[y, x]
                if f == EXCESS:
                    new[y, x] = T
                    continue
                if f == NONE:
                    continue
                rgb = t[y, x]
                px = Px(d=d, face=f, u=u[y, x], h=h[y, x], lr=lr[y, x], hb=hb, H=H, N=N,
                        vis=VIS[d], rgb=rgb, x=x, y=y,
                        pod=(pods and f == ROOF and max(int(v) for v in rgb) < 0xEC))
                if f == SIDE and glassy(rgb) and px.h <= hb + 1e-6:
                    cg = liv.glass(px)
                    if cg is not None:
                        new[y, x] = cg
                    continue
                if not white_paint(rgb):
                    continue
                cc = liv.paint(px)
                if cc is None:
                    continue
                if f == ROOF and not px.pod:
                    k = roof_k * min(1.0, max(int(v) for v in rgb) / 0xEC)
                else:
                    k = max(int(v) for v in rgb) / ref
                new[y, x] = unspecial(tuple(min(255, max(0, round(v * k))) for v in cc))
        if ac:
            draw_ac(new, face, u, lr, ac, liv)
        if sticker:
            khk_sticker(new, t, face, lr)
        out.append(new)
    return out


def draw_ac(new, face, u, lr, urange, liv):
    """flat A/C box on the roof (top colour, darker near edge)"""
    top = liv.roof or liv.body or WHITE
    edge = tuple(int(v * 0.80) for v in top)
    box = set()
    for y in range(128):
        for x in range(128):
            if face[y, x] == ROOF and urange[0] <= u[y, x] <= urange[1] and 0.22 <= lr[y, x] <= 0.78:
                box.add((x, y))
    for (x, y) in box:
        new[y, x] = unspecial(top if (x, y + 1) in box else edge)


def khk_sticker(new, base, face, lr):
    """KHK sticker: the top row of the rear window becomes a light panel with a
    red + blue chevron at the vehicle's left"""
    cols = {}
    for y in range(128):
        for x in range(128):
            if face[y, x] == REAR and glassy(base[y, x]):
                cols.setdefault(x, []).append(y)
    if not cols:
        return
    xs = sorted(cols)
    if len(xs) < 3:
        return
    for x in xs:
        y0 = min(cols[x])
        new[y0, x] = KHK_PANEL
    # chevron on the vehicle-left end of the panel
    left = sorted(xs, key=lambda x: lr[min(cols[x]), x])
    a, b = left[1], left[2] if len(left) > 3 else left[1]
    new[min(cols[a]), a] = KHK_RED
    if b != a:
        new[min(cols[b]), b] = KHK_BLUE


def load_row(rel, row=0):
    im = np.array(Image.open(os.path.join(REPO, *rel.split("/"))).convert("RGB"))
    return [im[row * 128:(row + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)]


# base sheets (VTPsim art) and their box specs
LF38_BASE = "vehicle-bus/mhd-tabor/dekstra_lf_38_cng/sprites/comettbila.png"
FIRST_BASE = "vehicle-bus/praha/rosero_first/sprites/bila.png"
NOVO_BASE = "vehicle-bus/dpmp/novociti_life/sprites/bilocerna.png"
# Dekstra LF 38 CNG: rooftop / clip cut the raised CNG tank fairing off the roof
LF38_SPEC = {
    "ne": dict(xf=81, xr=50, top=93, bot=105, rooftop=89),
    "sw": dict(xf=48, xr=81, top=80, bot=92, rooftop=76),
    "w": dict(xf=41, xr=64, top=67, bot=78, W=5, clip=0.75),
    "e": dict(xf=50, xr=28, top=88, bot=99, W=4, clip=0.75),
    "n": dict(xf=103, xr=81, top=76, bot=87, W=4.5, clip=0.75),
    "s": dict(xf=58, xr=82, top=80, bot=91, W=4.5, clip=0.75),
    "nw": dict(x0=68, x1=78, rf=69, rr=82, e0=83, e1=94),
    "se": dict(x0=45, x1=55, rf=85, rr=70, e0=86, e1=96),
}
# Rosero First (the same VTPsim body, 2-1 doors, roof A/C pod kept)
FIRST_SPEC = {d: {k: v for k, v in s.items() if k not in ("rooftop", "clip")} for d, s in LF38_SPEC.items()}
NOVO_SPEC = {
    "ne": dict(xf=81, xr=50, top=93, bot=104),
    "sw": dict(xf=50, xr=81, top=82, bot=93),
    "w": dict(xf=41, xr=65, top=67, bot=78, W=4.5),
    "e": dict(xf=50, xr=27, top=87.5, bot=98.5, W=5),
    "n": dict(xf=97, xr=74, top=79, bot=90, W=4.5),
    "s": dict(xf=62, xr=86, top=80, bot=91, W=4.5),
    "nw": dict(x0=69, x1=79, rf=68, rr=83, e0=84, e1=95),
    "se": dict(x0=45, x1=55, rf=87, rr=72, e0=88, e1=100),
}

RLIVERIES = {"bila": RBila, "transdev": RTransdev, "cds": RCDS, "ptransport": RPTransport,
             "bilocerna": RBiloCerna, "dvurkralove": DvurKralove}


def repaint_job(base, spec, ac=None, sticker=True, pods=True):
    def run(color):
        liv = RLIVERIES[color]()
        return repaint(load_row(base), spec, liv, ac=ac, sticker=sticker, pods=pods)
    return run


# ====================================================================== render
class VLivery:
    """render livery: body colour pair (top, side), decals by (u, z, side)"""
    body = (WHITE, (0xEA, 0xEA, 0xE8))
    roof = None
    pod = None
    bumper = DARK
    sticker = False

    def side(self, bus, p, u, z, right):
        return None

    def front(self, bus, p, t, z):
        return None

    def rear(self, bus, p, t, z):
        return None


class VCDS(VLivery):
    """CDS Nachod Sprinter: all yellow, red CDS + blue NACHOD on the lower
    side behind the door, black bumpers, LED display."""
    body = (CDS_YELLOW, (0xF0, 0xBE, 0x00))
    roof = (0xF8, 0xCC, 0x10)
    sticker = True

    def side(self, bus, p, u, z, right):
        # CDS NACHOD between the axles under the windows, 2 lines of pixels
        a0, a1 = bus.sp["axles"]
        if a0 + 1.6 <= u < a1 - 0.3:
            if p.line(2, 1.05) or p.line(2, 0.95):
                q = int((u - a0 - 1.6) / 0.24)
                if q % 4 != 3 and (u < a0 + 2.6):
                    return CDS_RED
            if p.line(2, 0.80) and a0 + 2.7 <= u:
                return CDS_INK
        return None


class VPTransport(VLivery):
    """P-transport yellow-orange: red lower body rising towards the rear,
    two red lines under the windows, red bumpers."""
    body = (PT_YELLOW, (0xF2, 0xAC, 0x10))
    roof = (0xF8, 0xBA, 0x22)
    bumper = PT_RED
    sticker = True

    def side(self, bus, p, u, z, right):
        L = bus.L
        zr = 0.80
        if u > 0.55 * L:                               # sweep up to the windows at the rear
            t = (u - 0.55 * L) / (0.45 * L)
            zr = 0.80 + (bus.zw0 - 0.30 - 0.80) * min(1.0, t) ** 1.4
        if z < zr:
            return PT_RED
        if p.line(2, bus.zw0 - 0.14) or p.line(2, bus.zw0 - 0.32):
            return PT_RED
        return None

    def front(self, bus, p, t, z):
        return PT_RED if z < 0.62 else None

    def rear(self, bus, p, t, z):
        if z < 0.80 or p.line(2, 1.40) or p.line(2, 1.58):
            return PT_RED
        return None


class VSilverJicin(VLivery):
    """Fejfar Bus, MHD Jicin: silver metallic, dark grey Fejfar Bus script and
    the Jicin tower logo behind the front door, Jicin logo on the bonnet."""
    body = ((0xC8, 0xCA, 0xCE), (0xBC, 0xBE, 0xC2))
    roof = (0xC8, 0xCA, 0xCE)
    pod = ((0xE6, 0xE7, 0xE8), (0xD2, 0xD3, 0xD5))
    bumper = (0xA8, 0xAA, 0xAE)
    INK = (0x40, 0x42, 0x46)

    def side(self, bus, p, u, z, right):
        d1 = bus.sp["doors"][0][1]
        if d1 + 0.15 <= u < d1 + 1.35 and (p.line(2, 1.62) or p.line(2, 1.52)):
            return self.INK if int((u - d1) / 0.24) % 3 != 2 else None      # Fejfar Bus script
        if d1 + 1.55 <= u < d1 + 1.80 and 1.10 <= z < 1.70:
            return self.INK                                                  # Valdicka brana tower
        if d1 + 1.90 <= u < d1 + 2.70 and p.line(2, 1.48):
            return self.INK                                                  # JICIN
        return None


class VSilver(VLivery):
    """plain silver-grey (Iveco Daily of MHD Nova Paka), dark grey lower
    bumpers, sills and rubbing strips."""
    body = ((0xBE, 0xC0, 0xC4), (0xB2, 0xB4, 0xB8))
    roof = (0xC2, 0xC4, 0xC8)
    bumper = DGREY

    def side(self, bus, p, u, z, right):
        if z < 0.50:
            return DGREY
        return None


class VWhiteTransdev(VLivery):
    """plain white van (MHD Kostelec), black bumpers (the thin rubbing strip only
    stripes the diagonal views, so it is left out), small
    red Transdev circle on the cab doors."""
    bumper = DARK

    def side(self, bus, p, u, z, right):
        if inr(u, 0.95, 1.20) and inr(z, 1.10, 1.30):
            return TD_RED
        return None


class Van(Bus):
    """praha_small.Bus with a livery object: van-derived minibus bodies
    (bonnet + raked windscreen), with a van rear (two doors) or a bus rear
    (rear wall, window high up)."""

    def __init__(self, sp, liv):
        sp = dict(sp)
        sp.setdefault("livery", dict(kind="A", blocks_r=[], blocks_l=[], bands=[]))
        super().__init__(sp)
        self.lv = liv

    def pair(self):
        return self.lv.body

    def upper(self, u):
        return self.lv.roof or self.lv.body[0]

    def tex(self, p):
        u = self.L - p.s
        if p.face == "top" and p.box == "body" and p.z < self.zr - 0.01:
            return col(self.lv.body, "top")              # bonnet / scuttle
        return super().tex(p)

    def tex_roof(self, p, u):
        return col(self.lv.roof or self.lv.body, "top")

    def tex_pod(self, p, u, k):
        a, b, h, hw, kind = self.sp["pods"][k]
        f = p.face
        if kind == "ac":
            pc = self.lv.pod or self.lv.roof or self.lv.body
            if f == "top" and abs(p.t) < hw - 0.30 and a + 0.25 < u < b - 0.25:
                return tuple(int(v * 0.86) for v in col(pc, "top"))
            return col(pc, f)
        return super().tex_pod(p, u, k)

    def cant(self, p, u):
        return self.lower(p, u, p.face == "right")

    def lower_pair(self, u, right):
        return self.lv.body

    def lower(self, p, u, right):
        c = self.lv.side(self, p, u, p.z, right)
        if c is not None:
            return col(c, p.face) if not isinstance(c[0], int) else c
        if p.z < self.z0 + 0.14:
            return col(self.lv.bumper, p.face) if self.sp.get("sill") else col(self.lv.body, p.face)
        return col(self.lv.body, p.face)

    def tex_screen(self, p):
        a = abs(p.t)
        if a > self.HW - 0.12:
            return BLACK
        z = p.z
        top = self.sp.get("screen_top", self.sp["rake"][-1][1])
        if z >= top:
            return col(self.lv.body, "front")          # raised roof over the cab
        if z > top - 0.26 and self.sp.get("led_screen"):
            return AMBER if a < 0.85 and z < top - 0.06 else BLACK
        return GLASS

    def tex_front(self, p):
        t, z = p.t, p.z
        a = abs(t)
        HW = self.HW
        sp = self.sp
        d = self.lv.front(self, p, t, z)
        if d is not None:
            return col(d, "front") if not isinstance(d[0], int) else d
        if z < sp.get("zbump", 0.42):
            return col(self.lv.bumper, "front") if not isinstance(self.lv.bumper[0], int) else self.lv.bumper
        zl = sp.get("zlamp", (0.80, 1.00))
        if a > HW - 0.36 and inr(z, *zl):
            return HEADL if a < HW - 0.10 else col(SILVER, "front")
        gr = sp.get("grille", (0.62, 0.50, 0.98))
        if a < gr[0] and inr(z, gr[1], gr[2]):
            return BLACK
        return col(self.lv.body, "front")

    def tex_rear(self, p):
        t, z = p.t, p.z
        a = abs(t)
        HW = self.HW
        rr = self.sp["rear"]
        d = self.lv.rear(self, p, t, z)
        if z < 0.30:
            return BLACK
        if z < 0.46:
            return col(self.lv.bumper, "rear") if not isinstance(self.lv.bumper[0], int) else self.lv.bumper
        g0, g1 = self.sp.get("rear_glass", (1.55, 2.35))
        if rr == "van":
            if a > HW - 0.18 and inr(z, 0.75, 1.55):
                return TAILL
            if a < 0.04 and z < g1:
                return FRAME
        else:
            if a > HW - 0.16 and inr(z, 0.70, 1.45):
                return TAILL
        if inr(z, g0, g1) and a < HW - 0.18:
            if self.lv.sticker and z >= g1 - 0.22:
                if inr(t, -0.80, -0.55):
                    return KHK_RED if z >= g1 - 0.11 else KHK_BLUE
                return KHK_PANEL
            return GLASS
        if d is not None:
            return col(d, "rear") if not isinstance(d[0], int) else d
        return col(self.lv.body, "rear")


# Mercedes-Benz Sprinter 519 CDI minibus (CDS Nachod, 2018, 6H9 6326): the
# shipped Erduman Sprinter body (praha_small.SPRINTER, 7.36 m, drawn 2.30 m
# wide with a 2.82 m roof) as the high-roof van conversion: passenger door
# right behind the cab, roof A/C pod at the front, LED display behind the top
# of the windscreen (no roof display box), van rear doors.
SPRINTER_CDS = mk(PS.SPRINTER, doors=[(1.45, 2.35)],
                  pods=[(1.05, 2.45, 0.20, 0.80, "ac")], led_screen=True,
                  glass=(0.85, 7.10))
# Mercus Mercedes-Benz Sprinter (Fejfar Bus, MHD Jicin, 2019, 7H4 2992): the
# 2018 Sprinter (907) as a city minibus, doors 1-2: single door behind the
# cab, glazed double door in the rear overhang; roof A/C at the front; bus
# rear (rear wall with the window high up).
MERCUS = mk(PS.SPRINTER, L=7.40, doors=[(1.45, 2.30), (5.95, 7.05)],
            pods=[(0.95, 2.35, 0.22, 0.82, "ac")], rear="bus", rear_glass=(1.60, 2.40),
            glass=(0.85, 7.25), led_screen=False)
# SKD / Stratos Iveco L 27 (P-transport Broumov): high-floor midibus on the
# Iveco Daily 50C/65C, Daily cab front with the bonnet, high body with a
# straight roof, door behind the cab, bus rear with a big rear window; about
# 7.1 x 2.1 x 2.9 m, wheelbase 3.95 m. Drawn 2.30 m wide like the Sprinter.
STRATOS_L = dict(
    L=7.15, W=2.30, axles=[0.95, 4.90], wr=0.40, z0=0.40, zr=2.90, zw0=1.40, zw1=2.42, zb=1.32,
    hood=1.18, rake=[(0.40, 1.42), (0.58, 1.78), (0.82, 2.90)],
    doors=[(1.45, 2.35)], ldoors=[(0.82, 1.78)], drv=(0.82, 1.78), sidedisp=(9, 9),
    engine=None, glass=(0.88, 6.95), pitch=1.10,
    pods=[], mirror_u=0.85, mirror_z=(1.50, 1.95),
    front="van", rear="bus", rear_glass=(1.50, 2.45), led_screen=True,
    zlamp=(0.84, 1.04), grille=(0.70, 0.62, 1.00), zbump=0.52,
)
# Iveco Daily 50C13 minibus (L&Z Line, MHD Nova Paka, 2001, 9AT 4244): the
# 1999-2006 Daily van with the raised roof, one folding door behind the cab,
# van rear; about 7.0 x 2.0 x 2.75 m, wheelbase 3.95 m. Drawn 2.24 m wide.
DAILY = dict(
    L=7.00, W=2.24, axles=[0.95, 4.90], wr=0.38, z0=0.38, zr=2.75, zw0=1.38, zw1=2.30, zb=1.30,
    hood=1.15, rake=[(0.42, 1.40), (0.62, 1.80), (0.92, 2.42), (1.05, 2.75)],
    doors=[(1.50, 2.30)], ldoors=[(0.92, 1.80)], drv=(0.92, 1.80), sidedisp=(9, 9),
    engine=None, glass=(1.00, 6.80), pitch=1.20,
    pods=[], mirror_u=0.95, mirror_z=(1.45, 1.90),
    front="van", rear="van", rear_glass=(1.45, 2.25), grille=(0.80, 0.66, 0.92), zbump=0.50,
    screen_top=2.42,
    zlamp=(0.78, 0.98),
)
# Renault Master III L3H2 minibus (Transdev Cechy, MHD Kostelec n. O., 2017,
# 6H7 3995): 6.2 x 2.07 x 2.5 m, wheelbase 4.33 m, sliding door on the right
# behind the cab, van rear. Drawn 2.24 m wide with a 2.62 m roof.
MASTER = dict(
    L=6.20, W=2.24, axles=[0.90, 5.23], wr=0.38, z0=0.36, zr=2.62, zw0=1.32, zw1=2.22, zb=1.25,
    hood=1.10, rake=[(0.45, 1.38), (0.66, 1.78), (0.98, 2.40), (1.08, 2.62)],
    doors=[(1.55, 2.75)], ldoors=[(0.98, 1.78)], drv=(0.98, 1.78), sidedisp=(9, 9),
    engine=None, glass=(1.05, 6.00), pitch=1.15,
    pods=[], mirror_u=1.00, mirror_z=(1.40, 1.85),
    front="van", rear="van", rear_glass=(1.40, 2.15), grille=(0.62, 0.55, 1.00), zbump=0.55,
    screen_top=2.40,
    zlamp=(0.82, 1.02),
)


class VanSliding(Van):
    """Master: the sliding door is a body-coloured panel with a window."""

    def tex_door(self, p, u, d, right):
        if right:
            d0, d1 = d
            if self.ln(p, d0 + 0.02) or self.ln(p, d1 - 0.02):
                return FRAME
            if p.z >= self.zw0 and p.z < self.zw1 - 0.05:
                return GLASS
            return self.lower(p, u, right)
        return super().tex_door(p, u, d, right)


VLIVERIES = {"cds": VCDS, "ptransport": VPTransport, "stribrnajicin": VSilverJicin,
             "stribrna": VSilver, "bila": VWhiteTransdev}


def render_job(sp, cls=Van):
    def run(color):
        m = cls(sp, VLIVERIES[color]())
        tiles = []
        for d in DIRS:
            img, _ = render(d, m.boxes(), m.tex, m.L, np.array(ORIGINS[d]))
            tiles.append(img)
        return tiles
    return run


# ====================================================================== families
BASEF = {"waytype": "road", "freight": "Passagiere", "intro_month": 1,
         "retire_year": 2060, "retire_month": 12, "engine_type": "diesel"}
ORDER = ["cost", "payload", "speed", "weight", "runningcost", "fixed_cost", "intro_year",
         "intro_month", "retire_year", "retire_month", "waytype", "freight", "length",
         "engine_type", "power", "gear", "smoke"]


def fields(cost, payload, speed, weight, power, length, intro, run=None, fixed=None, gear=60,
           smoke="Diesel_small", **kw):
    f = dict(cost=cost, payload=payload, speed=speed, weight=weight,
             runningcost=run or round(cost / 16000), fixed_cost=fixed or round(cost / 2700),
             intro_year=intro, length=length, power=power, gear=gear, smoke=smoke)
    f.update(BASEF)
    f.update(kw)
    return {k: f[k] for k in ORDER if k in f}


LIVNAME = {
    "bila": ("white", "bílá"),
    "transdev": ("white with the red figure", "bílá s červenou postavou"),
    "cds": ("yellow", "žlutá"),
    "ptransport": ("yellow-red", "žluto-červená"),
    "bilocerna": ("white-black", "bílo-černá"),
    "dvurkralove": ("white-green, town photo wrap", "zeleno-bílá s fotografiemi města"),
    "stribrnajicin": ("silver, Jičín logo", "stříbrná s logem Jičína"),
    "stribrna": ("silver-grey", "stříbrošedá"),
}

AGENCY = {
    "IREDO": ("IREDO", "IREDO"),
    "MHDJicin": ("MHD Jičín", "MHD Jičín"),
    "MHDNovaPaka": ("MHD Nová Paka", "MHD Nová Paka"),
    "MHDKostelec": ("MHD Kostelec nad Orlicí", "MHD Kostelec nad Orlicí"),
}

MIDI = ("midibus", "midibus")
MINI = ("minibus", "minibus")

VTP = "VTPsim"
VZ = "vojtechzicha"

FAMILIES = {
    "vehicle-bus/iredo/dekstra_le_37": dict(
        agency="IREDO", type="Dekstra_LE_37", name="Dekstra LE 37 / SKD Stratos LE 37", role=MIDI,
        copyright=VTP, job=repaint_job(LF38_BASE, LF38_SPEC, ac=(0.70, 0.90), pods=False),
        liveries=[("bila", "BusLine KHK, KAD"), ("transdev", "Transdev Čechy"),
                  ("ptransport", "P-transport")],
        fields=fields(300000, 37, 90, 5, 132, 5, 2009),
        note="Iveco-Dekstra LE 37 (until 2016 SKD Stratos LE 37): low-entry midibus on the\n"
             "Iveco Daily 70C, about 7.7 x 2.2 x 2.9 m, doors 1-2 (door behind the front\n"
             "wheel, double door in the rear overhang), Iveco F1C 3.0 diesel 132 kW.\n"
             "KHK 2026: Transdev Čechy 14 (white + red figure), BusLine KHK 5 (white),\n"
             "KAD 1, P-transport 1 (yellow-red).\n"
             "Sprite: VTPsim's LE 37 art (the Tábor Dekstra LF 38 sheet, real length,\n"
             "32 px) with the CNG fairing cut off and a rear roof A/C box, repainted by\n"
             "zone (photos seznam-autobusu 409867, 441354, 411789, 393304). The front\n"
             "door stays double (1 px wider than the real single door)."),
    "vehicle-bus/iredo/rosero_first": dict(
        agency="IREDO", type="Rosero_First", name="Rošero First FCLLI / FCLEI", role=MIDI,
        copyright=VTP, job=repaint_job(FIRST_BASE, FIRST_SPEC),
        liveries=[("cds", "CDS Náchod"), ("ptransport", "P-transport"),
                  ("bila", "BusLine KHK, Transdev Čechy"),
                  ("bilocerna", "Transdev Čechy, MHD Týniště nad Orlicí")],
        fields=fields(290000, 33, 90, 5, 132, 5, 2009),
        note="Rošero-P First FCLLI / FSLLI / FCLEI: low-entry midibus on the Iveco Daily\n"
             "70C, about 7.7 x 2.2 x 2.9 m, door behind the front wheel and a door in the\n"
             "rear overhang, about 33 places, Iveco F1C 3.0 diesel 132 kW.\n"
             "KHK 2026: CDS Náchod 8 (yellow), P-transport 4 (yellow-red), Transdev Čechy\n"
             "3 (white) + FCLEI 9H0 1456 (MHD Týniště, white-black, 7/2026), BusLine KHK 1.\n"
             "Sprite: the Prague / Tábor Rošero First sheet (VTPsim's LE 37 art at the\n"
             "real length with the roof A/C pod), repainted by zone (photos\n"
             "seznam-autobusu 414338, 443235, 434375, 441989, 427851; vhdfoto 42822/3)."),
    "vehicle-bus/iredo/novociti_life": dict(
        agency="IREDO", type="NovoCiti_Life", name="Isuzu NovoCiti Life", role=MIDI,
        copyright=VTP, job=repaint_job(NOVO_BASE, NOVO_SPEC),
        liveries=[("bila", "BusLine KHK")],
        fields=fields(420000, 50, 90, 7, 140, 5, 2018),
        note="Isuzu NovoCiti Life (Class II), 7.9 m low-floor midibus, 7.9 x 2.3 x 3.0 m,\n"
             "doors 1-2, Isuzu 4HK1 5.2 l diesel 140 kW.\n"
             "KHK 2026: BusLine KHK 1 (8AX 3171, 2021, Hořice depot, white).\n"
             "Sprite: the DPMP NovoCiti Life sheet (VTPsim's Urbino 8 body shortened to\n"
             "7.9 m), white with the black glasshouse and front mask as on the BusLine\n"
             "car (photo seznam-autobusu 330687), plus the KHK rear sticker."),
    "vehicle-bus/iredo/sprinter_519": dict(
        agency="IREDO", type="Sprinter_519", name="Mercedes-Benz Sprinter 519 CDI", role=MINI,
        copyright=VZ, job=render_job(SPRINTER_CDS),
        liveries=[("cds", "CDS Náchod, MHD Náchod")],
        fields=fields(190000, 20, 90, 4, 140, 5, 2013, gear=64),
        note="Mercedes-Benz Sprinter 519 CDI high-roof minibus, about 7.4 x 2.0 x 2.8 m,\n"
             "wheelbase 4.325 m, door behind the cab, V6 3.0 diesel 140 kW.\n"
             "KHK 2026: CDS Náchod 1 (6H9 6326, 2018, MHD Náchod line 382; its sister\n"
             "6H9 6325 was sold in 2023), all yellow.\n"
             "Sprite: original box render (vojtechzicha), the praha_small.py Sprinter\n"
             "body as a van conversion (SPRINTER_CDS in tools/busrender/khk_small.py;\n"
             "photos seznam-autobusu 372179, 390545)."),
    "vehicle-bus/iredo/dekstra_lf_38": dict(
        agency="IREDO", type="Dekstra_LF_38", name="Dekstra LF 38", role=MIDI,
        copyright=VTP, job=repaint_job(LF38_BASE, LF38_SPEC, ac=(0.70, 0.90), pods=False, sticker=False),
        liveries=[("dvurkralove", "KAD")],
        fields=fields(310000, 40, 90, 5, 125, 5, 2019),
        note="Dekstra LF 38: low-floor midibus on the Iveco Daily 70C17, about 7.8 x 2.2 x\n"
             "2.9 m, doors 2-2, about 40 places, Iveco F1C 3.0 diesel 125 kW.\n"
             "KHK 2026: KAD 1 (7H5 9029, 2019 demonstrator, MHD Dvůr Králové nad Labem\n"
             "since 12/2020) in the town's white-green photo wrap.\n"
             "Sprite: VTPsim's LE 37 art (the Tábor Dekstra LF 38 sheet) with the CNG\n"
             "fairing cut off and a rear roof A/C box, repainted by zone; the photo\n"
             "collage is reduced to colour fields (photos seznam-autobusu 340433,\n"
             "283082; khk_mhd/dvur_kralove)."),
    "vehicle-bus/mhd-jicin/mercus_sprinter": dict(
        agency="MHDJicin", type="Mercus_Sprinter", name="Mercus Mercedes-Benz Sprinter", role=MINI,
        copyright=VZ, job=render_job(MERCUS),
        liveries=[("stribrnajicin", "Fejfar Bus")],
        fields=fields(230000, 34, 90, 4, 140, 5, 2019, gear=64),
        note="Mercus city minibus on the Mercedes-Benz Sprinter (907), about 7.4 x 2.0 x\n"
             "2.8 m, doors 1-2 (glazed double door in the rear overhang), 15+1 seats and\n"
             "19 standing, bus rear, roof A/C, 3.0 diesel ~140 kW.\n"
             "MHD Jičín 2026: Fejfar Bus 1 (7H4 2992, 2019), silver with the Fejfar Bus\n"
             "and Jičín \"svým občanům\" logos.\n"
             "Sprite: original box render (vojtechzicha), MERCUS in\n"
             "tools/busrender/khk_small.py (photos vhdfoto 3638, seznam-autobusu\n"
             "295755, 292354, 430011)."),
    "vehicle-bus/mhd-nova-paka/iveco_daily_50c13": dict(
        agency="MHDNovaPaka", type="Iveco_Daily_50C13", name="Iveco Daily 50C13", role=MINI,
        copyright=VZ, job=render_job(DAILY),
        liveries=[("stribrna", "L&Z Line")],
        fields=fields(150000, 19, 90, 3, 92, 5, 2001, gear=66),
        note="Iveco Daily 50C13 minibus (1999-2006 Daily, raised roof), about 7.0 x 2.0 x\n"
             "2.75 m, one folding door behind the cab, 2.8 l diesel 92 kW.\n"
             "MHD Nová Paka 2026: L&Z Line 1 (9AT 4244, 2001), plain silver-grey with dark\n"
             "grey bumpers and sills.\n"
             "Sprite: original box render (vojtechzicha), DAILY in\n"
             "tools/busrender/khk_small.py (photos vhdfoto 14678, seznam-autobusu 169195)."),
    "vehicle-bus/mhd-kostelec/renault_master": dict(
        agency="MHDKostelec", type="Renault_Master", name="Renault Master dCi 145", role=MINI,
        copyright=VZ, job=render_job(MASTER, VanSliding),
        liveries=[("bila", "Transdev Čechy")],
        fields=fields(140000, 16, 90, 3, 107, 5, 2014, gear=66),
        note="Renault Master III L3H2 minibus, about 6.2 x 2.07 x 2.5 m, wheelbase 4.33 m,\n"
             "sliding door behind the cab, dCi 145 diesel 107 kW.\n"
             "MHD Kostelec nad Orlicí 2026: Transdev Čechy 1 (6H7 3995, 2017), white with\n"
             "a small Transdev logo on the cab door.\n"
             "Sprite: original box render (vojtechzicha), MASTER in\n"
             "tools/busrender/khk_small.py (photos seznam-autobusu 370347, vhdfoto 41890)."),
}


# ====================================================================== output
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


def q(s):
    return '"' + s.replace('"', '\\"') + '"'


def write_yaml(fam, F):
    ag_en, ag_cs = AGENCY[F["agency"]]
    L = [f"agency: {F['agency']}",
         f"type: {q(F['type'])}",
         "# Sprites carry their own lane placement (body footprint on the median of",
         "# native pak128.cs 12 m buses), so no extra shift.",
         "image_offset: [0, 0]",
         "# Windows light up at night only while passengers are aboard.",
         "windows_lit_when_loaded: true",
         f"copyright: {F['copyright']}",
         "",
         "display:",
         f"  agency_en: {q(ag_en)}",
         f"  agency_cs: {q(ag_cs)}",
         f"  family_en: {q(F['name'])}",
         f"  family_cs: {q(F['name'])}",
         ""]
    L += ["# " + s if s else "#" for s in F["note"].split("\n")]
    L += ["# Generated by tools/busrender/khk_small.py --yaml.", "",
          "vehicles:",
          f"  - id: {q(F['type'])}",
          f"    display_id: {q(F['name'])}",
          f"    role_en: {q(F['role'][0])}",
          f"    role_cs: {q(F['role'][1])}",
          "    row: 0",
          "    prev: []",
          "    next: []",
          "    fields:"]
    for k, v in F["fields"].items():
        L.append(f"      {k}: {v}")
    L += ["", "liveries:"]
    for color, ops in F["liveries"]:
        en, cs = LIVNAME[color]
        if ops:
            en, cs = f"{en} · {ops}", f"{cs} · {ops}"
        L += [f"  - color: {color}", f"    name_en: {q(en)}", f"    name_cs: {q(cs)}"]
    path = os.path.join(REPO, *fam.split("/"), "family.yaml")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(path)


def main():
    args = sys.argv[1:]
    pv = None
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
        os.makedirs(pv, exist_ok=True)
    yaml = "--yaml" in args
    args = [a for a in args if a != "--yaml"]
    for fam, F in FAMILIES.items():
        name = fam.split("/")[-1]
        if args and name not in args:
            continue
        sd = os.path.join(REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        for color, _ in F["liveries"]:
            sheet = save_rows([F["job"](color)], os.path.join(sd, color + ".png"))
            if pv:
                preview(sheet, os.path.join(pv, f"{name}-{color}.png"))
            print(f"{fam}/sprites/{color}.png")
        if yaml:
            write_yaml(fam, F)


if __name__ == "__main__":
    main()
