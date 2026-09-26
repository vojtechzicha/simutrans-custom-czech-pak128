"""RegioJet UK RegioPanters in the DUK green-yellow livery:
  650.2 = Skoda 15Ev, 2 cars (650 + 651), and
  640.2 = Skoda 20Ev, 3 cars (640 + 642 + 641).

Zone-map REPAINT of the CD RegioPanter art by TommPa9 (pak128_czr, the sheets
of vehicle-rail/ceske-drahy/650 and /640, livery najbrt2), so RegioJet's
RegioPanters have exactly the silhouette of the CD and Arriva ones in game
(RegioJet's 15Ev / 20Ev are "structurally identical" to CD's RegioPanters,
zeleznicni-magazin.cz 15 Jun 2026). The method follows regiopanter_idpk.py
(Arriva, IDPK livery; copied and adapted here, that file is not touched):

  * the cab cars are taken from the CD 650 sheet (rows 0 / 1): the 640's cab
    cars are pixel-identical in shape (only their palette differs), the
    middle car from the CD 640 sheet (row 1 = the middle car), its palette
    normalised to the 650 one first;
  * per view the side band is found column by column (white cant stripe h0,
    body h1..6, skirt edge h7, underframe h8); for the cab cars every column
    is mapped to u = distance behind the cab nose (side-view px, 72 = car)
    through the window/door centres of that view (idpk's calibrated anchors);
  * each band pixel is repainted from the DUK design: light-green cant,
    green body, continuous black window band (3 px over the high-floor ends,
    4 px over the low-floor part: the real band is taller there), yellow-
    orange stripe under the high-floor windows at the inner ends with a red /
    blue RegioJet logo on it, dark-grey skirt, silver doors, silver sweep and
    orange edge at the cab, white DUK logo under the first window. The
    source's glass (lit special 0x4D4D4D) and door glass are kept;
  * the cab fronts: black face (windscreen, destination display, lower
    panel with a white DUK logo), orange outline pillars, yellow skirt,
    0xFFFF53 headlights on the lead car, red tail lights on the rear car; the
    source's 0x6B6B6B / 0xC1B1D1 / 0xC2B2D2 specials are removed;
  * the grey roof and roof equipment of the source stay as drawn.

Colours (photos 12-15 Jun 2026, Usti n. L.: zdopravy.cz "Obrazem: RegioJet
vyjizdi s novymi vlaky v Usteckem kraji" gallery, zeleznicni-magazin.cz
641.264 on U3 15 Jun 2026 by L. Seidenglanz, Commons "Skoda 15 Ev pro
Regiojet" 4 Jun 2026): lime green body (sunlit #77BC28 / #63BB3B, vagonWEB
#00A508 is far too dark), black window band, silver-grey doors (vagonWEB
#7F868C), orange-yellow cab outline and side stripe (#F4A30C), silver sweep
(#C0C4CD), yellow skirt, dark-grey lower edge.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")
# Frozen copies of the TommPa9 ČD 650 / 640 sheets as they were when this repaint
# was tuned (the ČD families are being redrawn separately; the zone detection
# below depends on this exact source art).
SRC650 = os.path.join(HERE, "src", "cd650_najbrt2_tommpa9.png")
SRC640 = os.path.join(HERE, "src", "cd640_najbrt2_tommpa9.png")

T = (231, 255, 255)


def hx(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# ------------------------------------------------------------ source palette (CD 650)
C, G, B, F = hx(0x061843), hx(0x162450), hx(0x041335), hx(0x109AFA)
Q = hx(0x4D4D4D)                      # lit window glass (kept)
q, p, m = hx(0xFFC20E), hx(0xFFC106), hx(0xF0B500)
U, TT = hx(0x6C6C6C), hx(0x6B6B6B)    # windscreens / cab side windows
X = hx(0x7F7F7F)
WHITES = {hx(v) for v in (0xF3F7FA, 0xD3DCE3, 0xE6ECF1, 0xC0C9D2, 0xB0BAC3, 0x9EA7AF, 0x8D959C,
                          0xDCDCDC, 0x7C8389)}
BODY = {C, G, B, F, p, m}
BAND = BODY | {Q, q, U, TT}
HLIGHT = {hx(0xC2B2D2), hx(0xC1B1D1)}
TAILS = {hx(0xFF211D)}
LAMP_W = hx(0xE4E4FF)
ROOF_SET = {hx(v) for v in (0x515151, 0x787878, 0x333333, 0x373737, 0x3B3B3B, 0x414141, 0x454545,
                            0x464646, 0x4E4E4E)}
# CD 640 palette -> CD 650 classes (the 640 has lighter blues, navy doors,
# light-grey skirt edge); only used for the middle car
PAL640 = {hx(0x0061C4): C, hx(0x1275E4): C, hx(0x004D9D): B,
          hx(0x05153C): q, hx(0x102048): q, hx(0x04102F): q}

# ------------------------------------------------------------ DUK colours
GREEN = (0x6C, 0xBE, 0x2C)       # lime green body, lit side (photos #77BC28 / #63BB3B)
GREEN_LT = (0x9E, 0xDC, 0x52)    # light-green cant band (vagonWEB 48DC4F, lighter body top)
BLACK = (0x1A, 0x1D, 0x20)       # window band / black front face
ORANGE = (0xF4, 0xA3, 0x0C)      # cab outline, side stripe (#F4A30C)
YELLOW = (0xF6, 0xBC, 0x1A)      # front skirt
SILVER = (0xC4, 0xC9, 0xCF)      # cab sweep (#C0C4CD); not the special 0xC9C9C9
DOOR = (0x9C, 0xA3, 0xA9)        # silver-grey door leaves (vagonWEB 7F868C, lit)
SKIRT = (0x40, 0x45, 0x48)       # dark-grey lower edge (vagonWEB 313839, photo #434443)
WIN = (0x1C, 0x21, 0x27)         # windscreen / cab side window (plain, never lit)
WIN_HI = (0x33, 0x3D, 0x47)
WHITE = (0xEE, 0xF1, 0xF3)
RJ_RED = (0xE3, 0x34, 0x2F)
RJ_BLUE = (0x1F, 0x3A, 0x93)
HEAD = (0xFF, 0xFF, 0x53)
TAIL = (0xFF, 0x21, 0x1D)

SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
KEEP = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


def shade(c, k):
    c = tuple(int(max(0, min(255, round(v * k)))) for v in c)
    h = (c[0] << 16) | (c[1] << 8) | c[2]
    if h in SPECIAL and h not in KEEP:
        c = (c[0], c[1], c[2] + 1 if c[2] < 255 else c[2] - 1)
    return c


def kf(k):
    """view shade -> factor for flat livery colours."""
    return 1.0 if k >= 0.99 else (0.90 if k > 0.8 else 0.78)


# ------------------------------------------------------------ cab car layout
# u = side-view px behind the cab nose (source ne view: 72 px = 26.45 m)
FEAT_U = {
    "nose": 0.0, "cw": 3.0, "W1": 10.5, "W2": 15.5, "D1": 22.0, "W3": 27.5, "W4": 32.5,
    "W5": 37.5, "W6": 42.5, "D2": 48.0, "W7": 54.5, "W8": 59.5, "W9": 64.5, "W10": 69.5, "end": 72.0,
}
# silver sweep on the cab side: covers 1 <= u <= SWEEP[h] (h = rows below the cant)
SWEEP = {-1: 8, 0: 7, 1: 5, 2: 3, 3: 2, 4: 2, 5: 1, 6: 1}


def cab_design(u, h, high, flip=False):
    """DUK class of a cab-car band pixel: u behind the nose, h rows below the
    cant stripe, high = the nearest window is a high-floor one; flip = the
    inner end is on the screen-left (the stripe logo reads from the joint)."""
    if h >= 7:
        return "l"                       # green below the windows (see mid_design)
    if u < 0.75:
        return "o"                       # front edge: orange outline
    if u <= SWEEP.get(h, 0) + 0.25:
        return "s"
    if h == 0:
        return "G"
    if u < 6.5:
        # cab side behind the sweep: the black cab side window merges with
        # the first passenger window
        return "k" if 2 <= h <= 4 else "g"
    if u < 19.5:
        # cab-end section: high window + low window as one black area
        if u < 13.0:
            if 2 <= h <= 4:
                return "k"
            if h == 5 and 7.5 <= u <= 11.0:
                return "L"               # white DUK logo under the window
            return "g"
        return "k" if 4 <= h <= 6 else "g"
    xr = (u - 57.0) / 15.0
    return mid_design(h, high, stripe=(u > 57.0), x=(1.0 - xr) if flip else xr)


def mid_design(h, high, stripe, x):
    """low-floor part: band h4..6 (the glass rows); high-floor ends: band
    h2..4, stripe h5."""
    if h >= 7:
        # the source's windows reach down to the skirt-edge row; the real side
        # has ~0.4 m green under the windows above a dark-grey edge, so this
        # row is green and the dark underframe row below gives the edge
        return "l"
    if h == 0:
        return "G"
    if high:
        if 2 <= h <= 4:
            return "k"
        if h == 5 and stripe:
            return logo_on_stripe(x)
        return "g"
    return "k" if 4 <= h <= 6 else "g"


def logo_on_stripe(x):
    """1-px yellow stripe with the red '|| REGIO' + blue 'JET' in its middle
    (x = 0..1 along the stripe, as read left to right)."""
    if 0.30 <= x <= 0.36 or 0.40 <= x <= 0.56:
        return "R"
    if 0.60 <= x <= 0.70:
        return "J"
    return "y"


KCOL = {"G": GREEN_LT, "g": GREEN, "l": (0x5E, 0xA8, 0x26), "k": BLACK, "o": ORANGE, "s": SILVER, "y": ORANGE,
        "d": SKIRT, "L": WHITE, "R": RJ_RED, "J": RJ_BLUE}


# ------------------------------------------------------------ views (cab cars; idpk anchors)
DIAG_A = {  # cab at the RIGHT (u decreases with x) : row 1 col 0 geometry
    "end": 40, "W10": 41.5, "W9": 45, "W8": 48.5, "W7": 52, "D2": 56, "W6": 60, "W5": 64,
    "W4": 68, "W3": 72, "D1": 76, "W2": 80, "W1": 84, "cw": 88, "nose": 90}
DIAG_B = {  # cab at the LEFT : row 0 col 0 geometry
    "nose": 40, "cw": 42, "W1": 46, "W2": 50, "D1": 54, "W3": 58, "W4": 62, "W5": 66, "W6": 70,
    "D2": 74, "W7": 78, "W8": 81.5, "W9": 85, "W10": 88.5, "end": 91}
DIAG_C = {  # n/s views, cab at the RIGHT : row 0 col 2 geometry
    "end": 36.5, "W10": 38.5, "W9": 42, "W8": 45.5, "W7": 49, "D2": 53, "W6": 57, "W5": 61,
    "W4": 65, "W3": 69, "D1": 73, "W2": 77, "W1": 81, "cw": 85, "nose": 87}
DIAG_D = {  # n/s views, cab at the LEFT : row 0 col 6 geometry
    "nose": 57, "cw": 59, "W1": 63, "W2": 67, "D1": 71, "W3": 75, "W4": 79, "W5": 83, "W6": 87,
    "D2": 91, "W7": 95, "W8": 98.5, "W9": 102, "W10": 105.5, "end": 107}


def shift(a, dx):
    return {k: v + dx for k, v in a.items()}


VIEWS = {
    (1, 0): dict(kind="diag", k=1.00, x0=40, y0=73, s=+1, anc=DIAG_A, front="right"),
    (0, 4): dict(kind="diag", k=1.00, x0=20, y0=63, s=+1, anc=shift(DIAG_A, -20), front="right"),
    (0, 0): dict(kind="diag", k=1.00, x0=50, y0=78, s=+1, anc=DIAG_B, front="hidden"),
    (1, 4): dict(kind="diag", k=1.00, x0=30, y0=68, s=+1, anc=shift(DIAG_B, -20), front="hidden"),
    (0, 2): dict(kind="diag", k=0.76, x0=37, y0=98, s=-1, anc=DIAG_C, front="hidden"),
    (1, 6): dict(kind="diag", k=0.76, x0=57, y0=88, s=-1, anc=shift(DIAG_C, 20), front="hidden"),
    (0, 6): dict(kind="diag", k=0.76, x0=73, y0=80, s=-1, anc=DIAG_D, front="left"),
    (1, 2): dict(kind="diag", k=0.76, x0=53, y0=90, s=-1, anc=shift(DIAG_D, -20), front="left"),
    (0, 3): dict(kind="side", k=0.90, tip=82, dir=-1),
    (1, 7): dict(kind="side", k=0.90, tip=110, dir=-1),
    (0, 7): dict(kind="side", k=0.90, tip=38, dir=+1),
    (1, 3): dict(kind="side", k=0.90, tip=10, dir=+1),
    (0, 5): dict(kind="vert", k=0.86, front_y=84),
    (1, 1): dict(kind="vert", k=0.86, front_y=91),
    (0, 1): dict(kind="top", k=0.86, end_y=97),
    (1, 5): dict(kind="top", k=0.86, end_y=90),
}
# middle car (CD 640 row 1): diag / side views; the band is found automatically
MID_VIEWS = {0: dict(kind="diag", k=1.00, s=+1), 4: dict(kind="diag", k=1.00, s=+1),
             2: dict(kind="diag", k=0.76, s=-1), 6: dict(kind="diag", k=0.76, s=-1),
             3: dict(kind="side", k=0.90), 7: dict(kind="side", k=0.90),
             1: dict(kind="ends", k=0.86), 5: dict(kind="ends", k=0.86)}


def u_of_x(anc, x):
    pts = sorted((xv, FEAT_U[k]) for k, xv in anc.items())
    xs = [a for a, _ in pts]; us = [b for _, b in pts]
    if x <= xs[0]:
        return us[0] + (x - xs[0]) * (us[1] - us[0]) / (xs[1] - xs[0])
    if x >= xs[-1]:
        return us[-1] + (x - xs[-1]) * (us[-1] - us[-2]) / (xs[-1] - xs[-2])
    return float(np.interp(x, xs, us))


# ------------------------------------------------------------ band detection
def band_columns_anc(t, v):
    """[(x, h0)] of the side band (cab cars, diag views, idpk method)."""
    out = []
    xs = sorted(v["anc"].values())
    for x in range(int(np.floor(xs[0])) - 1, int(np.ceil(xs[-1])) + 2):
        g = v["y0"] + v["s"] * ((x - v["x0"]) // 2)
        for y in (g, g - 1, g + 1):
            if 0 <= y < 127 and tuple(t[y, x]) in WHITES and tuple(t[y + 1, x]) in BAND:
                out.append((x, y))
                break
    return out


def band_columns_auto(t, s):
    """[(x, h0)] of the side band found without anchors (middle car): the
    topmost white-over-band pixel per column, then only columns that follow
    the 2:1 staircase of their neighbours."""
    cand = {}
    for x in range(128):
        for y in range(0, 127):
            if tuple(t[y, x]) in WHITES and tuple(t[y + 1, x]) in BAND:
                cand[x] = y
                break
    xs = sorted(cand)
    if not xs:
        return []
    # fit y = a + s * x / 2 (robust: median of the intercepts)
    a = float(np.median([cand[x] - s * x / 2.0 for x in xs]))
    return [(x, cand[x]) for x in xs if abs(cand[x] - (a + s * x / 2.0)) <= 1.6]


# ------------------------------------------------------------ per column helpers
def column_info(t, x, h0):
    """(door, glass_rows) of a band column."""
    col = [tuple(t[h0 + h, x]) if 0 <= h0 + h < 128 else T for h in range(0, 9)]
    door = any(col[h] == q for h in range(2, 9)) and any(col[h] == q for h in range(6, 9))
    glass = [h for h in range(1, 7) if col[h] == Q]
    return door, glass


def high_map(t, cols):
    """x -> True if the nearest glass column has high-floor windows (glass up to h2..3)."""
    info = {x: column_info(t, x, h0) for x, h0 in cols}
    xs = [x for x, _ in cols]
    res = {}
    for x in xs:
        best = None
        for d in range(0, 5):
            for xx in (x - d, x + d):
                if xx in info and not info[xx][0] and info[xx][1]:
                    best = min(info[xx][1]) <= 3
                    break
            if best is not None:
                break
        res[x] = True if best is None else best
    return res, info


# ------------------------------------------------------------ painting
def paint_band(t, o, x, h0, cls_of_h, k, info_x):
    """repaint one band column; cls_of_h(h) -> DUK class."""
    door, _ = info_x
    kk = kf(k)
    for h in range(-1, 9):
        y = h0 + h
        if not (0 <= y < 128):
            continue
        src = tuple(t[y, x])
        if src == T:
            continue
        if h == -1:
            # roof edge above the cant stripe: the source's white cab hood top
            if src in WHITES:
                c = cls_of_h(-1)
                o[y, x] = shade(SILVER, kk) if c == "s" else shade(GREEN_LT, kk * 0.92)
            continue
        if h == 8:
            if src in WHITES or src == X:
                o[y, x] = shade(SKIRT, kk)
            elif src == q:
                o[y, x] = shade(DOOR, kk * 0.8)
            continue
        if src == Q:
            continue                           # glass stays lit
        if door and src == q:
            o[y, x] = shade(DOOR, kk)
            continue
        if src in (U, TT):
            o[y, x] = WIN
            continue
        if src in HLIGHT or src in TAILS or src == LAMP_W:
            continue                           # lamps: handled with the ends
        if src in BODY or src in WHITES or src == q or src == X:
            c = cls_of_h(h)
            if door and h >= 2 and c not in ("d",):
                o[y, x] = shade(DOOR, kk)
                continue
            o[y, x] = shade(KCOL[c], kk if c not in ("R", "J", "L") else 1.0)


def paint_leftovers(t, o, k, front_region=None, rear=False, lead=False):
    """everything the band pass did not reach: body blues -> green (end faces),
    whites -> light green, Najbrt yellow -> yellow skirt, windscreen specials."""
    kk = kf(k)
    for y in range(128):
        for x in range(128):
            src = tuple(t[y, x])
            if src == T or tuple(o[y, x]) != src:
                continue
            fr = front_region is not None and front_region(x, y)
            if fr:
                continue
            if src in (C, G, F):
                o[y, x] = shade(GREEN, kk * 0.82)
            elif src == B:
                o[y, x] = shade(GREEN, kk * 0.68)
            elif src in WHITES:
                o[y, x] = shade(GREEN_LT, kk * 0.88)
            elif src in (q, p, m):
                o[y, x] = shade(YELLOW, kk)
            elif src in (U, TT):
                o[y, x] = WIN
            elif src in HLIGHT:
                o[y, x] = HEAD if lead else TAIL
            elif src == X:
                # roof equipment (pantograph insulators) keeps its grey; the
                # skirt edge wrapping round the car ends becomes the dark edge
                if any(tuple(t[yy, x]) in ROOF_SET for yy in range(y + 1, min(128, y + 4))):
                    continue
                o[y, x] = shade(SKIRT, kk)


def paint_front(t, o, x, y, lead, kk, center=None):
    """one pixel of a cab front: black face, orange outline, yellow skirt."""
    src = tuple(t[y, x])
    if src == T:
        return
    if src in (U, TT, Q):
        o[y, x] = WIN
    elif src in (C, G, B, F):
        o[y, x] = BLACK                                  # black face
    elif src in WHITES or src == X:
        o[y, x] = shade(ORANGE, kk)                      # outline pillars / edges
    elif src in (q, p, m):
        o[y, x] = shade(YELLOW, kk)                      # skirt / anti-climber
    elif src in HLIGHT:
        o[y, x] = HEAD if lead else TAIL
    elif src in TAILS:
        o[y, x] = TAIL if not lead else shade(ORANGE, kk)
    elif src == LAMP_W:
        o[y, x] = (0xE4, 0xE4, 0xF0) if not lead else HEAD
    elif src in ROOF_SET and center is not None and center(x, y):
        o[y, x] = BLACK                                  # top of the black face


def paint_cab_tile(t, row, col):
    v = VIEWS[(row, col)]
    lead = (row == 0)
    o = t.copy()
    k = v["k"]
    kk = kf(k)
    bg = np.all(t == T, axis=2)
    front_region = None
    if v["kind"] == "diag":
        cols = band_columns_anc(t, v)
        hm, info = high_map(t, cols)
        for x, h0 in cols:
            u = u_of_x(v["anc"], x)
            ul = [u_of_x(v["anc"], x - 0.5), u_of_x(v["anc"], x + 0.5)]
            ua = min(ul)
            flip = v["anc"]["nose"] > v["anc"]["end"]          # cab right -> joint on the left
            paint_band(t, o, x, h0, lambda h, u=ua, fl=flip: cab_design(max(0.0, u), h, hm[x], fl),
                       k, info[x])
        nose = int(v["anc"]["nose"]); end = v["anc"]["end"]
        right = nose > end
        if v["front"] != "hidden":
            if right:
                front_region = lambda xx, yy: xx > nose
            else:
                front_region = lambda xx, yy: xx < nose
            for y in range(128):
                for x in range(128):
                    if front_region(x, y) and not bg[y, x]:
                        paint_front(t, o, x, y, lead, 0.86)
            # the black face runs up to the roof: the source's white rim along
            # the top of the front becomes black, only the side pillars stay
            # orange (a "U", photos) - skip the near pillar (2 columns next to
            # the nose) and the far edge column
            fx = sorted({x for x in range(128) for y in range(128) if front_region(x, y) and not bg[y, x]})
            if fx:
                inner = fx[2:-1] if right else fx[1:-2]
                for x in inner:
                    ys = [y for y in range(128) if not bg[y, x]]
                    for y in ys[:2]:
                        if tuple(t[y, x]) in WHITES:
                            o[y, x] = BLACK
            # nose column: the orange outline edge; the lowest px skirt
            ys = [y for y in range(128) if tuple(t[y, nose]) in (X,) or tuple(t[y, nose]) in WHITES]
            for y in ys[:-2]:
                o[y, nose] = shade(ORANGE, kk)
            for y in ys[-2:]:
                o[y, nose] = shade(SKIRT, kk)
        else:
            # the cab corner still shows on the far end: windscreen -> plain
            pass
    elif v["kind"] == "side":
        tip, dr = v["tip"], v["dir"]
        cols = [(x, 83) for x in range(128) if 1 <= (x - tip) * dr <= 72 and not bg[84, x]]
        hm, info = high_map(t, cols)
        for x, h0 in cols:
            u = (x - tip) * dr
            paint_band(t, o, x, h0, lambda h, u=u: cab_design(u, h, hm[x], dr < 0), k, info[x])
        # nose column (the cab front seen edge-on): orange outline, dark below
        for y in range(128):
            src = tuple(t[y, tip])
            if bg[y, tip]:
                continue
            if y <= 89:
                if src not in ROOF_SET:
                    o[y, tip] = shade(ORANGE, kk) if src not in (U, TT) else WIN
            else:
                paint_front(t, o, tip, y, lead, kk)
    elif v["kind"] == "vert":
        fy = v["front_y"]
        xs = [x for x in range(128) if not bg[fy + 4, x]]
        x0, x1 = min(xs), max(xs)
        cx = (x0 + x1) / 2.0

        def center(xx, yy):
            return abs(xx - cx) <= (x1 - x0) / 2.0 - 1.5
        front_region = lambda xx, yy: yy >= fy
        for y in range(fy, 128):
            for x in range(128):
                if bg[y, x]:
                    continue
                src = tuple(t[y, x])
                outer = (x <= x0 or x >= x1)
                if outer and (src in WHITES or src in (C, G, B, F)):
                    # the cab sides seen edge-on: silver sweep above, green below
                    o[y, x] = shade(SILVER, kk) if y < fy + 6 else shade(GREEN, kk * 0.9)
                    if src in HLIGHT:
                        o[y, x] = HEAD if lead else TAIL
                    continue
                if center(x, y) and y < fy + 5 and (src in WHITES or src == Q):
                    o[y, x] = BLACK                  # details inside the black face top
                    continue
                paint_front(t, o, x, y, lead, kk, center=center)
        # white DUK logo on the lower panel, orange line under it
        ly = [y for y in range(fy, 128) if tuple(t[y, int(cx)]) in (C, G, B, F)]
        if ly:
            yl = ly[len(ly) // 2]
            for x in (int(cx) - 1, int(cx), int(cx) + 1):
                o[yl, x] = WHITE
            yo = max(ly) + 1
            for x in range(x0 + 1, x1):
                if tuple(t[yo, x]) not in (T,) and center(x, yo):
                    o[yo, x] = shade(ORANGE, kk)
        # the side cant stripes seen from above along the car
        for y in range(0, fy):
            for x in (x0, x1):
                if tuple(t[y, x]) in WHITES:
                    o[y, x] = shade(GREEN_LT, kk)
    elif v["kind"] == "top":
        ey = v["end_y"]
        for y in range(0, 128):
            for x in range(128):
                if tuple(t[y, x]) in WHITES and y < ey:
                    o[y, x] = shade(GREEN_LT, kk)
    # the source's white cab hood above the band (rounded cab roof, the cab
    # corner in the views that hide the front) -> the silver sweep
    nx = None
    if v["kind"] == "diag":
        nx = v["anc"]["nose"]
    elif v["kind"] == "side":
        nx = v["tip"]
    if nx is not None:
        for y in range(128):
            for x in range(max(0, int(nx) - 7), min(128, int(nx) + 8)):
                src = tuple(t[y, x])
                if src in WHITES and tuple(o[y, x]) == src and not (front_region and front_region(x, y)):
                    o[y, x] = shade(SILVER, kk)
    paint_leftovers(t, o, k, front_region, lead=lead)
    # front lamps anywhere else (hidden-front views show a lamp at the corner)
    for hc in HLIGHT:
        mm = np.all(t == np.array(hc), axis=2)
        o[mm] = HEAD if lead else TAIL
    if lead:
        mm = np.all(t == np.array(TAIL), axis=2)
        o[mm] = shade(ORANGE, 0.86)
    mm = np.all(o == np.array(TT), axis=2)
    o[mm] = WIN
    return o


def paint_mid_tile(t, col):
    v = MID_VIEWS[col]
    o = t.copy()
    k = v["k"]
    bg = np.all(t == T, axis=2)
    if v["kind"] in ("diag", "side"):
        if v["kind"] == "diag":
            cols = band_columns_auto(t, v["s"])
        else:
            cols = [(x, 83) for x in range(128) if not bg[84, x] and tuple(t[83, x]) in WHITES]
        hm, info = high_map(t, cols)
        xs = [x for x, _ in cols]
        xa, xb = (min(xs), max(xs)) if xs else (0, 1)
        # the stripe logo reads left to right as seen: position along the
        # high-floor stretch it belongs to (left or right end of the car)
        for x, h0 in cols:
            frac = (x - xa) / max(1.0, xb - xa)
            if frac < 0.5:
                xl = frac / 0.26
            else:
                xl = (frac - 0.74) / 0.26
            paint_band(t, o, x, h0, lambda h, x=x, xl=xl: mid_design(h, hm[x], True, xl), k, info[x])
    paint_leftovers(t, o, k)
    return o


def load_rows():
    s650 = np.array(Image.open(SRC650).convert("RGB"))
    s640 = np.array(Image.open(SRC640).convert("RGB"))
    cab = [[s650[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)] for r in (0, 1)]
    mid = [s640[128:256, c * 128:(c + 1) * 128].copy() for c in range(8)]
    for tile in mid:
        for src, dst in PAL640.items():
            mm = np.all(tile == np.array(src), axis=2)
            tile[mm] = dst
    return cab, mid


def rows_650():
    cab, _ = load_rows()
    return [[paint_cab_tile(cab[r][c], r, c) for c in range(8)] for r in (0, 1)]


def rows_640():
    cab, mid = load_rows()
    front = [paint_cab_tile(cab[0][c], 0, c) for c in range(8)]
    middle = [paint_mid_tile(mid[c], c) for c in range(8)]
    rear = [paint_cab_tile(cab[1][c], 1, c) for c in range(8)]
    return [front, middle, rear]


JOBS = {
    "650_2": [("dukzelenozluta", rows_650, ["650", "651"])],
    "640_2": [("dukzelenozluta", rows_640, ["640", "642", "641"])],
}


def main():
    import railkit as R
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
