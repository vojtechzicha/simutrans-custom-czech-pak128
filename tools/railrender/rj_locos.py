#!/usr/bin/env python3
"""RegioJet electric locomotives, box models on the calibrated rail renderer.

    python tools/railrender/rj_locos.py [family ...] [--preview DIR]

Families (vehicle-rail/regiojet/<family>/sprites/<livery>.png):
  386_2  Bombardier TRAXX F140 MS2e 386.201-204, RJ yellow
  388_2  TRAXX 3 F160 MS: 388.2 (yellow, yellow Pool) and 1388 (yellow Pool)
  193    Siemens Vectron MS in the RJ yellow wrap (ELL); geometry from vectron.py
  162    Skoda 99E ex-FNM, RJ yellow; the two long sides differ
  362_2  the same body rebuilt dual-system, one retro scheme per loco

Scale: the 19 m locos are drawn at length 10 like the native 1216 / ES64U2 and
the 16.8 m 99E at length 8 like CD 363; bodies are 2-3 px taller than coaches
like the natives (side top z 11.6, roof 12.4, as vectron.py). u = carunits
behind the front buffer face, v = lateral (+v = the loco's right), z = model
px above the rail head.

Pixel mapping: livery zones, lines, lettering and windows are placed in SCREEN
pixels, not resampled. Every horizontal zone is a whole number of pixel rows
counted from a base line (prow), so the sheared diagonal views (w/e/n/s) never
show a dotted half-pixel sliver; vertical lines (door edges) are the pixel
column of the edge (on_col); lettering is a bitmap with one pixel per bitmap
cell, drawn separately for the square-on views (ne/sw, 5.66 px per carunit)
and the diagonal views (4 px per carunit, H/D bitmaps).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")

import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS, T, frame  # noqa: E402

# ------------------------------------------------------------------ colours
YELLOW = 0xFFB612          # = rjcoach.YELLOW, so locos and coaches match
LEMON = 0xFFC70E           # 362.219: a touch more lemon than RJ yellow
RED = 0xE3342F             # logo bars + REGIO
BLUE = 0x1F3A93            # logo JET
SILVER = 0xA7AEB5          # TRAXX / Vectron cab ends
BLACK = 0x1C1E20
WS = (0x2A, 0x34, 0x3D)    # cab glass: plain colours, never the lit specials
WS_HI = (0x4F, 0x62, 0x72)

P_YEL = Paint(YELLOW, top=0xFFC83A)
P_LEMON = Paint(LEMON, top=0xFFD23A)
P_SIL = Paint(SILVER, top=0xB6BCC2)
P_SILL = Paint(0x3E4346)
P_BLACK = Paint(BLACK)
P_ANTH = Paint(0x2E3133)
P_BOGIE = Paint(0x262829)
P_BOGIE_HI = Paint(0x3C3F42)
P_RED = Paint(RED)
P_BLUE = Paint(BLUE)
P_RED_DK = Paint(0xA9221E)
P_BLUE_DK = Paint(0x152A6E)
P_BUF = Paint(0x3A3D40)
P_TX_ROOF = Paint(0x6E757B, top=0x737A80)
P_TX_SHOULDER = Paint(0x7A8187, top=0x737A80)
P_TX_LOUVRE = Paint(0x363B40)
LOGO_COLS = {"r": P_RED, "q": P_RED_DK, "b": P_BLUE, "c": P_BLUE_DK}

HVIEWS = ("ne", "sw")            # long sides seen square-on
DVIEWS = ("w", "e", "n", "s")    # long sides seen on the diagonal
PANTO_TOP = 18.05                # pantograph head height (as vectron.py)


# ------------------------------------------------------------------ screen maths
def _affine(d):
    """screen px of model point (u, v, z) for a vehicle drawn at u_front = 0."""
    f, r = frame(d)
    k = R.KZ[d]
    ax, ay = R.ANCHOR[d]
    # world W = -u f + v r ; screen = ((X - Y) 4, (X + Y) 2 - Z)
    eu = (-(f[0] - f[1]) * 4.0, -(f[0] + f[1]) * 2.0)
    ev = ((r[0] - r[1]) * 4.0, (r[0] + r[1]) * 2.0)
    return (ax, ay, eu, ev, k)


AFF = {d: _affine(d) for d in DIRS}


def scr(d, u, v, z):
    ax, ay, eu, ev, k = AFF[d]
    return (ax + u * eu[0] + v * ev[0], ay + u * eu[1] + v * ev[1] - z * k)


def vc(d):
    """view class: 'H' long side square-on, 'D' diagonal (and all end views)."""
    return "H" if d in HVIEWS else "D"


def prow(d, z, base):
    """pixel row index above the line z = base (0 = first row above it).
    Rows are exact in every view: each index occurs once per pixel column."""
    return math.floor((z - base) * R.KZ[d] + 1e-6)


def _cover(a, b, p):
    """1-D pixel coverage: is the pixel whose centre is p inside the span a..b?
    Spans narrower than one pixel still get the pixel holding their middle."""
    lo, hi = (a, b) if a <= b else (b, a)
    if lo <= p <= hi:
        return True
    if math.floor(hi - 0.5) < math.ceil(lo - 0.5):       # no pixel centre inside
        return math.floor(p) == math.floor((lo + hi) / 2)
    return False


def in_cols(d, u, v, z, ua, ub):
    """Pixel columns of a long side between u = ua and u = ub (at least one)."""
    return _cover(scr(d, ua, v, z)[0], scr(d, ub, v, z)[0], scr(d, u, v, z)[0])


def in_vcols(d, u, v, z, va, vb):
    """Pixel columns of an end face between v = va and v = vb (at least one)."""
    return _cover(scr(d, u, va, z)[0], scr(d, u, vb, z)[0], scr(d, u, v, z)[0])


def on_col(d, u, v, z, u2, v2):
    """Same screen pixel column as the vertical line through (u2, v2)."""
    return math.floor(scr(d, u, v, z)[0]) == math.floor(scr(d, u2, v2, z)[0])


class Glyphs:
    """Pixel bitmap on a long side, one bitmap cell = one screen pixel. H / D =
    bitmaps for the square-on / diagonal views (rows top first, '.' clear).
    s0 = left end as seen (reads left to right on both sides); the lowest
    bitmap row sits on pixel row rows[H|D] above the line z = base."""

    def __init__(self, s0, base, rows, H, D, cols=None):
        self.s0, self.base, self.rows = s0, base, rows
        self.bm = {"H": H, "D": D}
        self.cols = cols or LOGO_COLS

    def at(self, face, u, v, z, d, L):
        if d not in HVIEWS and d not in DVIEWS:
            return None
        k = vc(d)
        bm = self.bm[k]
        uo = (L - self.s0) if face == "+v" else self.s0
        c = math.floor(scr(d, u, v, z)[0]) - math.floor(scr(d, uo, v, z)[0])
        r = prow(d, z, self.base) - self.rows[0 if k == "H" else 1]
        n = len(bm)
        if r < 0 or r >= n or c < 0 or c >= len(bm[0]):
            return None
        return self.cols.get(bm[n - 1 - r][c])


class EndGlyphs:
    """Pixel bitmap on an end face centred at vcen (viewer's right positive),
    lowest row on pixel row `row` above the line z = base."""

    def __init__(self, vcen, base, row, bm, cols=None):
        self.vcen, self.base, self.row, self.bm = vcen, base, row, bm
        self.cols = cols or LOGO_COLS

    def at(self, face, u, v, z, d):
        sgn = -1 if face == "-u" else 1          # viewer's right: -v front, +v rear
        x = scr(d, u, v, z)[0]
        xc = scr(d, u, sgn * self.vcen, z)[0]
        xr = scr(d, u, sgn * (self.vcen + 1.0), z)[0]
        dirn = 1 if xr > xc else -1
        w = len(self.bm[0])
        c = (math.floor(x) - math.floor(xc)) * dirn + w // 2
        r = prow(d, z, self.base) - self.row
        n = len(self.bm)
        if r < 0 or r >= n or c < 0 or c >= w:
            return None
        return self.cols.get(self.bm[n - 1 - r][c])


# ------------------------------------------------------------------ RJ logo art
# "|| REGIOJET": two red slanted bars, REGIO red, JET blue. At 3-4 px letter
# height there is no room for letter gaps, so neighbouring letters alternate
# between two shades (r/q red, b/c blue) and still read as separate letters.
FONT = {
    3: {"R": ["XX.", "XX.", "X.X"], "R2": ["XX", "XX", "X."], "E": ["XX", "X.", "XX"],
        "G": ["XX", "X.", "XX"], "I": ["X", "X", "X"], "O": ["XXX", "X.X", "XXX"],
        "O2": ["XX", "XX", "XX"], "J": [".X", ".X", "XX"], "T": ["XXX", ".X.", ".X."],
        "T2": ["XX", "X.", "X."], "|": ["X.X", "X.X", "X.X"], "|D": ["X.X", "X.X", "X.X"]},
    4: {"R": ["XX.", "X.X", "XX.", "X.X"], "R2": ["XX", "XX", "X.", "X."],
        "E": ["XX", "X.", "XX", "XX"], "G": ["XXX", "X..", "X.X", "XXX"],
        "G2": ["XX", "X.", "X.", "XX"], "I": ["X", "X", "X", "X"],
        "O": ["XXX", "X.X", "X.X", "XXX"], "O2": ["XX", "XX", "XX", "XX"],
        "J": [".X", ".X", ".X", "XX"], "T": ["XXX", ".X.", ".X.", ".X."], "T2": ["XX", "X.", "X.", "X."],
        "|": ["X.X", "X.X", "X.X", "X.X"], "|D": ["X.X", "X.X", "X.X", "X.X"]},
    5: {"R": ["XX.", "X.X", "XX.", "X.X", "X.X"], "R2": ["XX", "XX", "XX", "X.", "X."],
        "E": ["XXX", "X..", "XX.", "X..", "XXX"], "E2": ["XX", "X.", "XX", "X.", "XX"],
        "G": ["XXX", "X..", "X.X", "X.X", "XXX"], "G2": ["XX", "X.", "X.", "XX", "XX"],
        "I": ["X", "X", "X", "X", "X"], "O": ["XXX", "X.X", "X.X", "X.X", "XXX"],
        "O2": ["XX", "XX", "XX", "XX", "XX"], "J": ["..X", "..X", "..X", "X.X", "XXX"],
        "J2": [".X", ".X", ".X", ".X", "XX"], "T": ["XXX", ".X.", ".X.", ".X.", ".X."],
        "T2": ["XX", "X.", "X.", "X.", "X."], "|": ["X.X", "X.X", "X.X", "X.X", "X.X"],
        "|D": [".X.X", ".X.X", "X.X.", "X.X.", "X.X."]},
}


def compose(n, glyphs, italic=False):
    """glyphs: list of (glyph name, colour char) -> bitmap rows (top first).
    italic: the bars lean right (upper half one pixel over); the letters stay
    upright, a sheared 3-5 px letter would no longer read."""
    rows = [""] * n
    for name, col in glyphs:
        g = ["."] * n if name == " " else FONT[n][name]
        if italic and name == "|":
            g = [("." + r if i < n // 2 else r + ".") for i, r in enumerate(g)]
        for i in range(n):
            rows[i] += g[i].replace("X", col)
    return rows


POOL_S = {"H": ["bb.b.b.b.", "b..b.b.bb"], "D": ["bbcbc.", "b.cbcb"]}   # small "POOL"
FRONT_LOGO = ["rrqrb"]                                                  # tiny nose logo


def rj_word(n, mode, pool=False):
    """'|| REGIOJET' (+ small 'POOL' on the baseline), n px high."""
    if mode == "H":
        g = [("|", "r"), (" ", "."), ("R", "r"), ("E", "q"), ("G", "r"), ("I", "q"), ("O", "r"),
             ("J", "b"), ("E", "c"), ("T", "b")]
    else:
        g = [("|D", "r"), (" ", "."), ("R2", "r"), ("E", "q"), ("G" if n < 4 else "G2", "r"),
             ("I", "q"), ("O2", "r"), ("J", "b"), ("E", "c"), ("T2", "b")]
    bm = compose(n, g, italic=(mode == "H"))
    if pool:
        pl = POOL_S[mode]
        bm = [r + "." + ("." * len(pl[0]) if i < n - 2 else pl[i - (n - 2)]) for i, r in enumerate(bm)]
    return bm


def big_word(mode):
    """5 px high '|| REGIOJET' filling side A of the 99E between the doors."""
    if mode == "H":
        g = [("|", "r"), (" ", "."), ("R", "r"), (" ", "."), ("E", "r"), (" ", "."), ("G", "r"),
             (" ", "."), ("I", "r"), (" ", "."), ("O", "r"), (" ", "."), ("J", "b"), (" ", "."),
             ("E", "b"), (" ", "."), ("T", "b")]
        return compose(5, g, italic=True)
    g = [("|D", "r"), (" ", "."), ("R2", "r"), ("E2", "q"), ("G2", "r"), ("I", "q"), ("O2", "r"),
         ("J2", "b"), ("E2", "c"), ("T2", "b")]
    return compose(5, g)


def small_word(mode, pool=False):
    """2 px high '|| REGIOJET' (side B of the 162, the 362.212 waist band)."""
    if mode == "H":
        rows = [".r.r.rqrqrbcb", "r.r..rqrqrbcb"]
        if pool:
            rows = [rows[0] + ".bcb", rows[1] + ".bcb"]
    else:
        rows = ["r.r.rqrqrbcb", "r.r.rqrqrbcb"]
        if pool:
            rows = [rows[0] + ".bc", rows[1] + ".bc"]
    return rows


def bogie(bc, half, wb, W, zb, own):
    """Bogie centred at u = bc: side frame (half length `half`) over two
    wheelsets at bc +- wb, with daylight between and outside the wheels."""
    def frame_mat(f, u, v, z, d):
        return P_BOGIE_HI if (f in ("+v", "-v") and 1.3 < z < 2.1) else P_BOGIE
    out = [Part(bc - half, bc + half, -W + 0.12, W - 0.12, 1.0, zb, frame_mat, own)]
    for a in (-wb, wb):
        out.append(Part(bc + a - 0.30, bc + a + 0.30, -W + 0.16, W - 0.16, 0.0, 1.8,
                        lambda *x: Paint(0x202224), own))
    return out


def _uu(L, near, a, b):
    """span (a, b) measured from the nearer end -> model u span."""
    return (a, b) if near else (L - b, L - a)


# ================================================================== TRAXX
class Traxx:
    """TRAXX F140 MS2e (386.2, gen 'ms2e') and TRAXX 3 (388.2 / 1388, gen 't3').
    18.9 m over buffers drawn at length 10 (1.89 m per carunit), vagonWEB
    386-a / 388-2-a for the positions. Side rows count from ZY (sill top):
    yellow rows 0-5 in the diagonal views, 0-6 square-on."""
    L = 10.0
    W = 0.96          # 2.977 m
    ZB = 3.0          # body side bottom (1.1 m)
    ZY = 4.1          # top of the anthracite sill band (1.5 m)
    ZS1 = 10.1        # top of the yellow (3.3 m) = ZY + 6 rows; grey shoulder above
    ZS = 11.6
    ZR = 12.4
    UB = 0.16         # buffer heads
    UN = 0.24         # lower nose face

    def __init__(self, gen, liv):
        self.gen, self.liv = gen, liv
        self.t3 = t3 = gen == "t3"
        self.ZN = 7.1                            # rake starts (top of nose row 2)
        self.UWT = 0.74 if t3 else 0.80         # front at the roof line
        self.redline = t3 and liv == "zluta"    # 388.2 yellow: red cab edge line
        pool = liv == "zlutapool"
        if t3:   # 388 logo 7.5 m long, letters half the side height
            self.logo = Glyphs(1.62, self.ZY, (2, 1), rj_word(4, "H", pool), rj_word(4, "D", pool))
        else:    # 386 logo 5.1 m, smaller
            self.logo = Glyphs(1.70, self.ZY, (3, 2), rj_word(3, "H"), rj_word(3, "D"))
        self.front_logo = EndGlyphs(0.30, self.ZY, 1, FRONT_LOGO)
        self.cab_roof = 1.28 if t3 else 1.85     # silver cab roof back to here

    # --------------------------------------------------------- shape
    def nose_u(self, z):
        if z < self.ZN:
            return self.UN
        t = min(1.0, (z - self.ZN) / (self.ZS - self.ZN))
        return self.UN + (self.UWT - self.UN) * t

    def silver_side(self, cu, z):
        """cab silver on the long side (cu = carunits from the nearer end)."""
        if z >= self.ZS1:
            return cu < self.cab_roof
        if self.t3:
            return z >= 5.4 and cu < self.nose_u(z) + 0.10 + (z - 5.4) * 0.05
        return z >= 4.8 and cu < self.nose_u(z) + 0.15

    # --------------------------------------------------------- paint
    def side(self, f, u, v, z, d):
        L = self.L
        cu = min(u, L - u)
        near = u < L / 2
        k = vc(d)
        r = prow(d, z, self.ZY)
        top = 5 if k == "D" else 6              # top yellow row
        if z < self.ZY:
            return P_SILL
        if z >= self.ZS1:
            # roof shoulder: grey, dark louvre grilles along the middle (row 0)
            s = L - u if f == "+v" else u
            if prow(d, z, self.ZS1) == 0 and 2.1 <= s <= 7.9 and (s - 2.1) % 1.45 < 1.25:
                return P_TX_LOUVRE
            return P_SIL if cu < self.cab_roof else P_TX_SHOULDER
        # cab side window (rows from ZY)
        w0 = (2 if self.t3 else 3)
        if w0 <= r <= top and in_cols(d, u, v, z, *_uu(L, near, 0.54, 0.76)):
            return WS_HI if r == top else WS
        if self.silver_side(cu, z):
            return P_SIL
        if self.redline and z >= 4.9 and self.silver_side(cu - 0.16, z):
            return P_RED
        # door: framed leaf from the sill to the top row
        da, db = _uu(L, near, 1.00, 1.42)
        if da - 0.1 <= u <= db + 0.1:
            if on_col(d, u, v, z, da, v) or on_col(d, u, v, z, db, v):
                return P_BLACK
            if da <= u <= db and r == top:
                return P_BLACK
        lp = self.logo.at(f, u, v, z, d, L)
        if lp is not None:
            return lp
        return P_YEL

    def front(self, f, u, v, z, d):
        """End face (rows from ZY): nose rows 0-2, black windscreen band above,
        silver A-pillars and cab roof edge."""
        W = self.W
        av = abs(v)
        sg = 1 if v > 0 else -1
        if z < self.ZY:
            return P_BLACK
        r = prow(d, z, self.ZY)
        if z >= self.ZS - 0.35:
            return P_SIL
        if self.t3:
            if av > W - 0.17 and r >= 1:
                return P_SIL
            mask = r >= 3 or (r == 2 and av < 0.55)
            if mask:
                if r >= 3 and av < W - 0.24:
                    if in_vcols(d, u, v, z, -0.03, 0.03):
                        return P_BLACK
                    return WS_HI if z > 10.4 else WS
                if r == 2 and av < 0.12:
                    return R.HEAD                     # central headlight
                return P_BLACK
            # corner headlight clusters (tall), red line along the nose bottom
            if 0.50 <= av <= 0.86 and r <= 1:
                if in_vcols(d, u, v, z, 0.62 * sg, 0.76 * sg):
                    return R.HEAD
                return P_BLACK
            if self.redline and r == 0:
                return P_RED
        else:
            if av > W - 0.15 and r >= 1:
                return P_SIL
            if r >= 3:
                if r >= 4 and av < W - 0.25:
                    if in_vcols(d, u, v, z, -0.03, 0.03):
                        return P_BLACK
                    return WS_HI if z > 10.4 else WS
                return P_BLACK
            if 0.50 <= av <= 0.86 and r == 0:
                if in_vcols(d, u, v, z, 0.62 * sg, 0.76 * sg):
                    return R.HEAD
                return P_BLACK
        g = self.front_logo.at(f, u, v, z, d)
        if g is not None:
            return g
        return P_YEL

    def body_mat(self):
        def mat(f, u, v, z, d):
            if f == "+z":
                if z < self.ZS - 0.05 and (u < 1.2 or u > self.L - 1.2) and z > self.ZN - 0.1:
                    # stepped windscreen slabs read as the sloped screen
                    return self.front("-u" if u < self.L / 2 else "+u", u, v, z, d)
                cu = min(u, self.L - u)
                return P_SIL if cu < self.cab_roof else P_TX_SHOULDER
            if f in ("+v", "-v"):
                return self.side(f, u, v, z, d)
            return self.front(f, u, v, z, d)
        return mat

    def roof_mat(self):
        def mat(f, u, v, z, d):
            cab = min(u, self.L - u) < self.cab_roof
            if f == "+z":
                return P_SIL if cab else P_TX_ROOF
            return P_SIL if cab else P_TX_SHOULDER
        return mat

    # --------------------------------------------------------- model
    def build(self):
        L, W = self.L, self.W
        own = "V"
        parts, lines = [], []
        body = self.body_mat()
        UWT = self.UWT
        parts.append(Part(UWT, L - UWT, -W, W, self.ZB, self.ZS1, body, own))
        parts.append(Part(UWT, L - UWT, -W + 0.06, W - 0.06, self.ZS1, self.ZS, body, own))
        for z0 in np.arange(self.ZB, self.ZS, 0.5):
            z1 = min(self.ZS, z0 + 0.5)
            uf = self.nose_u((z0 + z1) / 2)
            tp = 0.06 if z0 >= self.ZS1 - 1e-6 else (0.03 if z0 >= self.ZN else 0.0)
            parts.append(Part(uf, UWT, -W + tp, W - tp, z0, z1, body, own))
            parts.append(Part(L - UWT, L - uf, -W + tp, W - tp, z0, z1, body, own))
        parts.append(Part(UWT + 0.04, L - UWT - 0.04, -W + 0.26, W - 0.26, self.ZS, self.ZR,
                          self.roof_mat(), own))
        # roof equipment: main breaker / insulator deck between the pantographs
        parts.append(Part(3.7, 6.3, -0.40, 0.40, self.ZR, self.ZR + 0.5,
                          lambda *a: Paint(0x4E5459, top=0x5E656A), own))
        for (a, b) in ((1.9, 2.4), (7.6, 8.1)):
            parts.append(Part(a, b, -0.30, 0.30, self.ZR, self.ZR + 0.7,
                              lambda *a: Paint(0x7A2C24), own))          # insulators
        # pantographs: front one lowered (flat frame), rear one raised
        parts.append(Part(1.2, 2.6, -0.40, 0.40, self.ZR, self.ZR + 0.35,
                          lambda *a: Paint(0x3A3E42), own))
        parts.append(Part(7.9, 8.8, -0.40, 0.40, self.ZR, self.ZR + 0.40,
                          lambda *a: Paint(0x3A3E42), own))
        lines += R.pantograph(8.3, self.ZR + 0.40, own, fold=-1, reach=0.9,
                              height=PANTO_TOP - self.ZR - 0.40, col=(0x3C, 0x40, 0x44),
                              head=(0x22, 0x22, 0x24), half_head=0.62, thick=False)
        # underframe: bogies (pivots 10.44 m apart) + equipment between them
        for bc in (2.24, 7.76):                  # wheelbase 2.6 m
            parts += bogie(bc, 0.95, 0.69, W, self.ZB, own)
        parts.append(Part(3.3, 6.7, -W + 0.20, W - 0.20, 0.9, self.ZB, lambda *a: Paint(0x33373A), own))
        # buffer beams, yellow snowploughs, buffers
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(self.UB, self.UN + 0.02), -W + 0.05, W - 0.05, 1.9, self.ZY,
                              lambda *a: P_BLACK, own))
            parts.append(Part(*uu(0.05, 0.30), -0.80, 0.80, 0.35, 1.9, lambda *a: P_YEL, own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, self.UB), vcn - 0.13, vcn + 0.13, 2.4, 3.2,
                                  lambda *a: P_BUF, own))
        return parts, lines


def traxx_row(gen, liv):
    parts, lines = Traxx(gen, liv).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


# ================================================================== Skoda 99E
CSD_YELLOW = Paint(0xF2BA1E)
FNM_BLUE = Paint(0x243F8E)
FNM_SILVER = Paint(0xC5CACE)
DARK_MASK = Paint(0x3A3E44)


class E99Livery:
    def __init__(self, name, body, roof, sill, beam, panto, louvre, plough="yellow",
                 big=True, small=True, front_logo=True):
        self.name, self.body, self.roof, self.sill, self.beam = name, body, roof, sill, beam
        self.panto, self.louvre, self.plough = panto, louvre, plough
        self.big, self.small, self.front_logo = big, small, front_logo


def e99_livery(liv, unit):
    if liv == "zluta" and unit == "162":
        return E99Livery(liv, P_YEL, Paint(0x6C737A, top=0x7A8288), P_ANTH, P_BLACK,
                         (0x8A, 0x2A, 0x22), (Paint(0x6E5722), Paint(0x574419)))
    if liv == "zluta":          # 362.213, "RegioJet 2011" retro: black louvre band
        return E99Livery(liv, P_YEL, Paint(0x585E64, top=0x646A70), P_ANTH, P_BLACK,
                         (0x3A, 0x3D, 0x40), (Paint(0x2B2D30), Paint(0x3A3D41)))
    if liv == "csdmodrozluta":  # 362.212, CSD "unifikace 88" blue with the yellow band
        blue = Paint(0x2461E0)
        return E99Livery(liv, blue, Paint(0xDDD5CC, top=0xD3CCC3), blue, blue,
                         (0xE8, 0xC0, 0x1C), (Paint(0xD8D0C6), Paint(0xBDB6AD)),
                         big=False, small=False)
    if liv == "fnmzelenosediva":  # 362.220, FNM retro "E 630-09 RJ"
        return E99Livery(liv, Paint(0x3FAE3C), Paint(0xCDD2D5, top=0xC4C9CC), Paint(0x1F2F66),
                         Paint(0xD22A20), (0xC4, 0x30, 0x2A), (Paint(0xC9CED2), Paint(0xAEB3B8)),
                         plough="chevron", big=False, small=False)
    if liv == "zlutosediva":    # 362.219: lemon yellow, dark grey mask and lower band
        return E99Livery(liv, P_LEMON, Paint(0x50555A, top=0x5C6166), DARK_MASK, DARK_MASK,
                         (0x2E, 0x31, 0x34), (Paint(0x34383C), Paint(0x44484C)),
                         big=False, small=False, front_logo=False)
    raise ValueError(liv)


class E99:
    """Skoda 99E (FNM E.630 -> RJ 162 / 362.2). 16.8 m drawn at length 8 like
    the native CD 363 (2.1 m per carunit). Side A (+v; cab 1 on the right as
    seen) has four portholes and the big logo, side B (-v) the louvre band.
    Rows count from ZY (sill top): body rows 0-5 diagonal, 0-6 square-on;
    end faces: row 0 lamps, 1-2 waist, 3 twin headlights, 4-5 windscreens."""
    L = 8.0
    W = 0.95          # 2.94 m
    ZB = 2.6          # body side bottom
    ZY = 3.6          # sill band top (1.3 m)
    ZS1 = 9.6         # side wall top (3.35 m) = ZY + 6 rows
    ZC = 9.9          # cantrail top: roof chamfer steps above
    ZR = 11.3         # roof plane
    PORTHOLES = (1.48, 2.19, 5.48, 6.10)     # side A, as seen (vagonWEB 162-a)

    def __init__(self, liv, unit="162"):
        self.C = C = e99_livery(liv, unit)
        self.liv, self.unit = liv, unit
        zy = self.ZY
        self.bigg = Glyphs(1.06, zy, (0, 0), big_word("H"), big_word("D")) if C.big else None
        if liv == "csdmodrozluta":      # "REGIOJET POOL" on the waist band
            self.smallg = {"-v": Glyphs(2.3, zy, (1, 1), small_word("H", True), small_word("D", True)),
                           "+v": Glyphs(1.1, zy, (1, 1), small_word("H", True), small_word("D", True))}
        elif C.small:
            self.smallg = {"-v": Glyphs(1.3, zy, (1, 1), small_word("H"), small_word("D"))}
        else:
            self.smallg = {}
        self.front_logo = EndGlyphs(0.44, zy, 2, FRONT_LOGO) if C.front_logo else None

    def uf(self, z):
        """front face position (slight lean back above the headlights)."""
        return 0.22 if z < 6.4 else (0.26 if z < 8.0 else 0.30)

    # --------------------------------------------------------- paint
    @staticmethod
    def fnm_row(cu, mid):
        """FNM blue line row: mid-height along the body, dropping to row 1
        (just above the lamps) at the cab front corner."""
        t = min(1.0, max(0.0, (cu - 0.22) / (1.45 - 0.22)))
        return int(round(1 + (mid - 1) * t))

    def side(self, f, u, v, z, d):
        C, L, liv = self.C, self.L, self.liv
        if z >= self.ZS1:
            return C.roof
        if z < self.ZY:
            return C.sill
        cu = min(u, L - u)
        s = L - u if f == "+v" else u
        near = u < L / 2
        k = vc(d)
        r = prow(d, z, self.ZY)
        top = 5 if k == "D" else 6
        # cab side window, cab door with its window (both ends, both sides)
        if r >= 4 and in_cols(d, u, v, z, *_uu(L, near, 0.30, 0.48)):
            return WS_HI if r == top else WS
        da, db = _uu(L, near, 0.58, 0.98)
        if da - 0.1 <= u <= db + 0.1:
            if on_col(d, u, v, z, da, v) or on_col(d, u, v, z, db, v):
                return P_BLACK
            if da <= u <= db and r >= 4 and in_cols(d, u, v, z, *_uu(L, near, 0.66, 0.90)):
                return WS
        if f == "+v":
            # side A: portholes in the top row(s), over the lettering
            if r >= top - (1 if k == "H" else 0):
                for pc in self.PORTHOLES:
                    if abs(s - pc) < 0.3 and in_cols(d, u, v, z, L - pc - 0.11, L - pc + 0.11):
                        return WS
        else:
            # side B: louvre band between the doors, vertical slats
            lv = (4, top) if liv == "fnmzelenosediva" else ((3, 4) if k == "D" else (4, 5))
            if lv[0] <= r <= lv[1] and 1.0 <= s <= 7.0:
                x = math.floor(scr(d, u, v, z)[0])
                return C.louvre[x % 2]
        g = self.smallg.get(f)
        if g is not None:
            p = g.at(f, u, v, z, d, L)
            if p is not None:
                return p
        if self.bigg is not None and f == "+v":
            p = self.bigg.at(f, u, v, z, d, L)
            if p is not None:
                return p
        # plain zones
        if liv == "csdmodrozluta":
            return CSD_YELLOW if r in (1, 2) else C.body
        if liv == "fnmzelenosediva":
            rl = self.fnm_row(cu, 3)
            if r == rl:
                return FNM_BLUE
            return C.body if r > rl else FNM_SILVER
        if liv == "zlutosediva" and r == 0:
            return C.sill
        return C.body

    def front(self, f, u, v, z, d):
        C, liv = self.C, self.liv
        if z >= self.ZS1:
            return C.roof
        if z < self.ZY:
            return C.beam
        av = abs(v)
        sg = 1 if v > 0 else -1
        r = prow(d, z, self.ZY)
        if r >= 4:
            # windscreens: two panes and a centre post
            if liv == "csdmodrozluta":
                if in_vcols(d, u, v, z, 0.18 * sg, 0.70 * sg):
                    return WS_HI if r == 5 else WS
                if av <= 0.84:
                    return CSD_YELLOW                     # yellow frames
                return C.body
            if 0.08 <= av <= 0.82 and in_vcols(d, u, v, z, 0.10 * sg, 0.80 * sg):
                return WS_HI if r == 5 else WS
        if r == 3 and av < 0.26:
            # twin headlights in a dark box under the screens
            if in_vcols(d, u, v, z, -0.16, 0.16):
                return R.HEAD
            return P_BLACK
        if r == 0:
            # lamp row: white inner, red marker outer, number plate between
            if in_vcols(d, u, v, z, 0.50 * sg, 0.64 * sg):
                return R.HEAD
            if in_vcols(d, u, v, z, 0.70 * sg, 0.84 * sg):
                return Paint(0x9A1A14)
            if liv in ("csdmodrozluta", "zlutosediva") and av < 0.30:
                return Paint(0xC8201E)                       # red number plate
            if liv == "fnmzelenosediva" and av < 0.34:
                return Paint(0xE6E6DE)                       # "E 630-09 RJ" plate
        if self.front_logo is not None:
            g = self.front_logo.at(f, u, v, z, d)
            if g is not None:
                return g
        if liv == "csdmodrozluta":
            return CSD_YELLOW if r in (1, 2) else C.body
        if liv == "fnmzelenosediva":
            if r == 1:
                return FNM_BLUE
            return C.body if r > 1 else FNM_SILVER
        if liv == "zlutosediva":
            if r >= 3:
                return DARK_MASK
            if r == 0:
                return Paint(0xB4B9BD)
        return C.body

    def body_mat(self):
        def mat(f, u, v, z, d):
            if f == "+z":
                return self.C.roof
            if f in ("+v", "-v"):
                return self.side(f, u, v, z, d)
            return self.front(f, u, v, z, d)
        return mat

    # --------------------------------------------------------- model
    def build(self):
        L, W, C = self.L, self.W, self.C
        own = "V"
        parts, lines = [], []
        body = self.body_mat()
        cham = 0.14                              # plan-view corner chamfer
        for (z0, z1) in ((self.ZB, 6.4), (6.4, 8.0), (8.0, self.ZC)):
            uf = self.uf(z0 + 0.01)
            parts.append(Part(uf, L - uf, -W + cham, W - cham, z0, z1, body, own))
            parts.append(Part(uf + 0.12, L - uf - 0.12, -W, W, z0, z1, body, own))

        def roof(f, u, v, z, d):
            return C.roof
        parts.append(Part(0.52, L - 0.52, -W + 0.22, W - 0.22, self.ZC, 10.6, roof, own))
        parts.append(Part(0.74, L - 0.74, -W + 0.44, W - 0.44, 10.6, self.ZR, roof, own))

        # lowered resistor box mid-roof (louvred), cab air-con box over cab 1
        def resistor(f, u, v, z, d):
            if f == "+z":
                return Paint(0x2E3134) if (u * 4.0) % 1.0 < 0.5 else Paint(0x484C50)
            return Paint(0x3A3E42)
        parts.append(Part(2.95, 5.05, -0.60, 0.60, self.ZR, self.ZR + 0.6, resistor, own))
        parts.append(Part(0.95, 1.50, -0.42, 0.42, self.ZR, self.ZR + 0.55,
                          lambda *a: Paint(0x44484C, top=0x505458), own))
        # single-arm pantographs: front one lowered, rear one raised, knee outwards
        pc = C.panto
        pp = Paint((pc[0] << 16) | (pc[1] << 8) | pc[2])
        parts.append(Part(1.2, 2.3, -0.40, 0.40, self.ZR, self.ZR + 0.30, lambda *a: pp, own))
        parts.append(Part(6.0, 6.6, -0.36, 0.36, self.ZR, self.ZR + 0.30, lambda *a: pp, own))
        zb = self.ZR + 0.30
        h = PANTO_TOP - zb
        ub, uk, uh = 6.35, 6.95, 6.0
        lines += [((ub, 0.0, zb), (uk, 0.0, zb + h * 0.5), pc, own, False),
                  ((uk, 0.0, zb + h * 0.5), (uh, 0.0, PANTO_TOP), pc, own, False),
                  ((uh, -0.62, PANTO_TOP), (uh, 0.62, PANTO_TOP), (0x2A, 0x2A, 0x2C), own, True)]
        # underframe: bogies (pivots 8.3 m apart), central tank box
        for bc in (2.02, 5.98):                  # wheelbase 3.2 m
            parts += bogie(bc, 0.98, 0.76, W, self.ZB, own)
        parts.append(Part(3.05, 4.95, -W + 0.22, W - 0.22, 0.8, self.ZB, lambda *a: Paint(0x303336), own))

        # buffer beams, ploughs (FNM: yellow/black chevrons), buffers
        def plough_mat(f, u, v, z, d):
            if C.plough == "chevron":
                x, y = scr(d, u, v, z)
                return P_YEL if (math.floor(x) + math.floor(y)) % 3 else P_BLACK
            return P_YEL
        for sgn in (1, -1):
            def uu(a, b, sgn=sgn):
                return (a, b) if sgn > 0 else (L - b, L - a)
            parts.append(Part(*uu(0.14, 0.24), -W + 0.05, W - 0.05, 1.9, self.ZY,
                              lambda *a: C.beam, own))
            parts.append(Part(*uu(0.08, 0.26), -0.82, 0.82, 0.4, 1.9, plough_mat, own))
            for vcn in (-0.62, 0.62):
                parts.append(Part(*uu(0.0, 0.14), vcn - 0.13, vcn + 0.13, 2.4, 3.1,
                                  lambda *a: P_BUF, own))
        return parts, lines


def e99_row(liv, unit="162"):
    parts, lines = E99(liv, unit).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


# ================================================================== Vectron (RJ wrap)
ELL_S = {"H": ["kkk.gggg.k.", "kk..gggg..k", "kkk.gggg.k."],
         "D": ["kk.ggg.", "k..ggg.", "kk.ggg."]}
ELL_COLS = {"k": Paint(0x1E2022), "g": Paint(0x4A4E52)}


class VectronRJ:
    """Siemens Vectron MS 193.205/206/214/226/227 in the RegioJet yellow wrap.
    Geometry is vectron.py's (imported, not edited); only the paint changes:
    silver-grey upper cab front and cab roof, yellow lower front with the
    black grille stripes, dark grey lower side band, RJ and ELL logos.
    Side rows count from ZG (top of the grey band): yellow rows 0-7."""

    def __init__(self):
        import vectron as V
        self.V = V
        self.ZG = V.ZB + 1.0            # top of the grey lower band (1.35 m)
        self.logo = Glyphs(1.72, self.ZG, (3, 2), rj_word(4, "H"), rj_word(4, "D"))
        self.ell = Glyphs(7.25, self.ZG, (1, 1), ELL_S["H"], ELL_S["D"], ELL_COLS)

    def silver_side(self, cu, z):
        V = self.V
        if z < 5.4:
            return False
        return cu < min(1.02, V.nose_u(z) + 0.08 + (z - 5.4) * 0.07)

    def side(self, f, u, v, z, d):
        V = self.V
        L = V.L
        cu = min(u, L - u)
        if z < self.ZG:
            return Paint(0x55595C)
        if self.silver_side(cu, z):
            return P_SIL
        k = vc(d)
        r = prow(d, z, self.ZG)
        top = 7 if k == "D" else 8               # roof gutter row
        if r >= top:
            return Paint(0x3A3E42)
        near = u < L / 2
        da, db = _uu(L, near, 1.06, 1.46)
        if da - 0.1 <= u <= db + 0.1:
            if on_col(d, u, v, z, da, v) or on_col(d, u, v, z, db, v):
                return P_BLACK
            if da <= u <= db and (top - 4) <= r <= top - 2 and in_cols(d, u, v, z, *_uu(L, near, 1.14, 1.38)):
                return WS
        for g in (self.logo, self.ell):
            p = g.at(f, u, v, z, d, L)
            if p is not None:
                return p
        return P_YEL

    def front(self, f, u, v, z, d):
        """End face rows from ZG: 0-2 yellow panel (black stripes on 0 and 2,
        headlights on 1), 3 silver band, 4-6 windscreen, 7+ silver cab roof."""
        V = self.V
        W = V.W
        av = abs(v)
        if z < self.ZG:
            return Paint(0x4A4E52)
        r = prow(d, z, self.ZG)
        if r >= 7 or r == 3:
            return P_SIL
        if r >= 4:
            if av < W - 0.16:
                return WS_HI if r == 6 else WS
            return P_SIL
        sg = 1 if v > 0 else -1
        if av >= 0.64:
            # headlights in grey housings at the outer corners
            if r == 1 and in_vcols(d, u, v, z, 0.68 * sg, 0.82 * sg):
                return R.HEAD
            return Paint(0x8E959B)
        if 0.14 <= av and r in (0, 2):
            return P_BLACK
        return P_YEL

    def build(self):
        V = self.V
        orig = V.livery
        V.livery = lambda name: orig("railpool")
        try:
            parts, lines = V.build("railpool")
        finally:
            V.livery = orig
        L = V.L

        def body(f, u, v, z, d):
            if f == "+z" and z < V.ZS - 0.05:
                return self.front("-u" if u < L / 2 else "+u", u, v, z, d)
            if f == "+z":
                return P_SIL if min(u, L - u) < V.UCAB else P_TX_ROOF
            if f in ("+v", "-v"):
                return self.side(f, u, v, z, d)
            return self.front(f, u, v, z, d)

        def roof(f, u, v, z, d):
            cu = min(u, L - u)
            if cu < V.UCAB:
                return P_SIL
            if f == "+z":
                return P_TX_ROOF
            s = L - u if f == "+v" else u
            if f in ("+v", "-v") and (2.3 <= s <= 4.4 or 5.6 <= s <= 7.7) and prow(d, z, V.ZS) == 0:
                return P_TX_LOUVRE          # side grilles in the roof curve
            return P_TX_SHOULDER
        for p in parts:
            name = getattr(p.mat, "__name__", "")
            if name == "body_mat":
                p.mat = body
            elif name == "roof_mat":
                p.mat = roof
        # bogies with visible wheelsets instead of vectron.py's solid blocks
        parts = [p for p in parts if not (p.b[4] == 0.0 and abs(p.b[5] - V.ZB) < 1e-9
                                          and abs((p.b[1] - p.b[0]) - 2.5) < 1e-6)]
        for bc in (2.5, 7.5):                    # wheelbase 2.9 m
            parts += bogie(bc, 1.0, 0.76, V.W, V.ZB, "V")
        # grey snowploughs under the buffer beams
        for (a, b) in ((0.12, 0.40), (L - 0.40, L - 0.12)):
            parts.append(Part(a, b, -0.78, 0.78, 0.4, 1.6, lambda *a: Paint(0x9AA0A5), "V"))
        return parts, lines


def vectron_row():
    parts, lines = VectronRJ().build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


def row_for_spec(spec):
    """test helper: 'traxx:t3:zluta', 'e99:zluta:162', 'vec' -> one sprite row."""
    a = spec.split(":")
    if a[0] == "traxx":
        return traxx_row(a[1], a[2])
    if a[0] == "e99":
        return e99_row(a[1], a[2] if len(a) > 2 else "162")
    if a[0] == "vec":
        return vectron_row()
    raise ValueError(spec)


# ================================================================== jobs
def _empty_row():
    t = np.zeros((128, 128, 3), np.uint8)
    t[:, :] = T
    return [t.copy() for _ in range(8)]


# 362.2: one vehicle entry per loco, each restricted to its own scheme; rows are
# fixed indices (declaration order), so the earlier rows of a sheet stay empty
E362 = [("362.212", "csdmodrozluta"), ("362.220", "fnmzelenosediva"),
        ("362.213", "zluta"), ("362.219", "zlutosediva")]


def _rows_362(k):
    return [_empty_row() for _ in range(k)] + [e99_row(E362[k][1], "362")]


JOBS = {
    "386_2": [("zluta", lambda: [traxx_row("ms2e", "zluta")], ["386.2"])],
    "388_2": [("zluta", lambda: [traxx_row("t3", "zluta")], ["388.2"]),
              ("zlutapool", lambda: [traxx_row("t3", "zlutapool"), traxx_row("t3", "zlutapool")],
               ["388.2", "1388"])],
    "193": [("zluta", lambda: [vectron_row()], ["193"])],
    "162": [("zluta", lambda: [e99_row("zluta", "162")], ["162"])],
    "362_2": [(liv, (lambda k=k: _rows_362(k)), ["-"] * k + [vid]) for k, (vid, liv) in enumerate(E362)],
}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for liv, make, labels in JOBS[fam]:
            rows = make()
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
