"""Arriva 650+651 RegioPanter in the IDPK "Plzenskykraj" livery.

Zone-map repaint of the CD 650 art by TommPa9 (pak128_czr 650_P2, the sheet the
repo's CeskeDrahy-650 family ships as najbrt1_2.png / najbrt2.png - both
liveries are pixel-identical in the source, so zones come from colour +
geometry, not from a livery diff).  Arriva's units ARE the ex-CD 650.009-017,
so both operators' RegioPanters share one silhouette in game.

Per view (8 directions x 2 cars) the script
  1. finds the side band column by column (white cant stripe h0, body h1..6,
     skirt edge h7, underframe h8) and maps every column to u = distance from
     the car's cab nose in side-view pixels (piecewise linear through the
     window/door centres of that view),
  2. repaints the band from a (u, h) livery design (white cab hood, blue body,
     green/white/yellow Plzensky kraj swooshes, yellow top bar on the 650,
     white lettering), keeping the source's glass (lit special 0x4D4D4D),
     door leaves and door glass,
  3. repaints the roof (fairings -> IDPK dark blue, roof skin -> light grey),
  4. repaints the cab front (blue cap + lower front, black windscreen, yellow
     anti-climber, 0xFFFF53 headlights on the 650; the source's 0x6B6B6B /
     0xC1B1D1 specials are removed),
and writes the sheet into the Arriva family.

Regenerate with `python tools/railrender/arriva.py 650` (also after any change
to the CD 650 source sheet).
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(REPO, "vehicle-rail", "ceske-drahy", "650", "sprites", "najbrt2.png")

T = (231, 255, 255)


def hx(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# ------------------------------------------------------------ source palette
C, G, B, F = hx(0x061843), hx(0x162450), hx(0x041335), hx(0x109AFA)
Q = hx(0x4D4D4D)                      # lit window glass (kept)
q, p, m = hx(0xFFC20E), hx(0xFFC106), hx(0xF0B500)
U, TT = hx(0x6C6C6C), hx(0x6B6B6B)    # windscreens / cab side windows
X = hx(0x7F7F7F)
WHITES = {hx(v) for v in (0xF3F7FA, 0xD3DCE3, 0xE6ECF1, 0xC0C9D2, 0xB0BAC3, 0x9EA7AF, 0x8D959C, 0xDCDCDC)}
BODY = {C, G, B, F, p, m}
BAND = BODY | {Q, q, U, TT}
ROOF_DARK = {hx(v) for v in (0x333333, 0x373737, 0x3B3B3B, 0x414141, 0x454545, 0x464646, 0x4E4E4E)}
ROOF_SKIN = hx(0x515151)
ROOF_TOP = hx(0x787878)
HLIGHT = {hx(0xC2B2D2), hx(0xC1B1D1)}

# ------------------------------------------------------------ IDPK colours
BLUE = (0x16, 0x5E, 0xBC)        # body, lit (w/e) side; photo median #0F55A5 sunlit
DOOR = (0xF6, 0xC8, 0x1C)        # bright yellow doors (#EEC81D photo)
YEL = (0xF8, 0xD2, 0x22)         # yellow swoosh / top bar
GRN = (0x34, 0xAC, 0x4A)         # green swoosh (#239656..#2FA04A photos, lifted for 1x)
SWH = (0xF2, 0xF5, 0xF8)         # white swoosh
LET = (0xE8, 0xEE, 0xF4)         # white lettering
SKIRT = (0x5E, 0x63, 0x6A)       # dark-grey skirt band (#5A5F66)
WIN = (0x1E, 0x24, 0x2C)         # cab side windows / windscreen (plain, never lit)
FAIR_TOP = (0x34, 0x4E, 0x92)    # roof fairings, top faces
FAIR = (0x1C, 0x2C, 0x5C)        # roof fairings, walls (#1A2951 photo)
ROOF = (0x88, 0x8E, 0x95)
ROOF_EDGE = (0xBC, 0xC2, 0xC8)   # white roof curve just above the cant stripe        # roof skin between fairings (white/grey roof)
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


# ------------------------------------------------------------ car layout
# u = side-view pixels behind the cab nose (source ne/sw views, 72 px = 26.45 m)
FEAT_U = {  # centres used as anchors
    "nose": 0.0, "cw": 3.0, "W1": 10.5, "W2": 15.5, "D1": 22.0, "W3": 27.5, "W4": 32.5,
    "W5": 37.5, "W6": 42.5, "D2": 48.0, "W7": 54.5, "W8": 59.5, "W9": 64.5, "W10": 69.5, "end": 72.0,
}

# ------------------------------------------------------------ livery design
# key per (u, h): 'W' hood white, 'g' green, 'y' yellow, 'w' white swoosh, 'L' lettering
HOOD = {1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2}      # hood covers u <= HOOD[h]


def design(car):
    d = {}
    for h, umax in HOOD.items():
        for u in range(0, umax + 1):
            d[(u, h)] = "W"

    def put(pts, k):
        for u, h in pts:
            d.setdefault((u, h), k)
            if d[(u, h)] != "W":
                d[(u, h)] = k

    # cab-end group: green + white pair rising from the hood foot towards W1,
    # green arcing on over W2 down to D1 (photos: 650 009 / 651 009 broadsides)
    put([(3, 6), (4, 6), (5, 5), (6, 5), (7, 4), (8, 4), (13, 3), (13, 2), (14, 2), (15, 2),
         (16, 2), (17, 2), (18, 3), (19, 3)], "g")
    put([(5, 6), (6, 6), (7, 5), (8, 5)], "w")
    # large white PLZENSKY KRAJ lettering under W1 (Arriva era, 650 016 / 651 014 photos)
    put([(9, 6), (10, 6), (11, 6), (12, 6)], "L")
    if car == "650":
        put([(u, 1) for u in range(8, 20)], "y")          # yellow top bar hood -> D1
    else:
        put([(u, 1) for u in range(11, 17)], "y")         # shorter yellow arc over W1/W2
    # D1 group: three '/' strokes in the strip above W3, green running down the D1/W3 gap
    put([(25, 6), (25, 5), (25, 4), (26, 3), (27, 2), (28, 1)], "g")
    put([(27, 3), (28, 2), (29, 1)], "w")
    put([(28, 3), (29, 2), (30, 1)], "y")
    # D2 group: '' strokes above W6, green down the W5/W6 gap
    put([(45, 1), (44, 2), (43, 3), (40, 4), (40, 5), (40, 6)], "g")
    put([(44, 1), (43, 2), (42, 3)], "w")
    put([(43, 1), (42, 2), (41, 3)], "y")
    # inner-end group: green over yellow rising under W10..W8, up the W7/W8 gap
    put([(70, 6), (69, 6), (68, 6), (67, 6), (66, 6), (65, 6), (64, 5), (63, 5), (62, 5),
         (61, 5), (60, 5), (59, 5), (58, 5), (57, 4), (57, 3), (57, 2), (56, 1), (55, 1)], "g")
    put([(63, 6), (62, 6), (61, 6), (60, 6), (59, 6), (58, 6)], "y")
    return d


LIV = {"650": design("650"), "651": design("651")}
PRIO = {"L": 5, "g": 4, "y": 4, "w": 3, "W": 2, None: 0}
KCOL = {"g": GRN, "y": YEL, "w": SWH, "L": LET}


# ------------------------------------------------------------ views
# kind, side shade k, car layout per view:
#   diag: x0, y0 = h0 of the stripe at column x0, s = +1 (y grows with x) / -1,
#         anchors {feature: x}, xr = (xmin, xmax) band columns incl. nose column
#   side: tip x, direction (+1 = cab at left, u grows with x)
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
    # (row, col): spec
    (1, 0): dict(kind="diag", k=1.00, x0=40, y0=73, s=+1, anc=DIAG_A, front="right", cap=(93, 95)),
    (0, 4): dict(kind="diag", k=1.00, x0=20, y0=63, s=+1, anc=shift(DIAG_A, -20), front="right", cap=(83, 85)),
    (0, 0): dict(kind="diag", k=1.00, x0=50, y0=78, s=+1, anc=DIAG_B, front="hidden"),
    (1, 4): dict(kind="diag", k=1.00, x0=30, y0=68, s=+1, anc=shift(DIAG_B, -20), front="hidden"),
    (0, 2): dict(kind="diag", k=0.76, x0=37, y0=98, s=-1, anc=DIAG_C, front="hidden"),
    (1, 6): dict(kind="diag", k=0.76, x0=57, y0=88, s=-1, anc=shift(DIAG_C, 20), front="hidden"),
    (0, 6): dict(kind="diag", k=0.76, x0=73, y0=80, s=-1, anc=DIAG_D, front="left", cap=(83, 85)),
    (1, 2): dict(kind="diag", k=0.76, x0=53, y0=90, s=-1, anc=shift(DIAG_D, -20), front="left", cap=(93, 95)),
    (0, 3): dict(kind="side", k=0.90, tip=82, dir=-1),
    (1, 7): dict(kind="side", k=0.90, tip=110, dir=-1),
    (0, 7): dict(kind="side", k=0.90, tip=38, dir=+1),
    (1, 3): dict(kind="side", k=0.90, tip=10, dir=+1),
    (0, 5): dict(kind="vert", k=0.86, front_y=84, cap=(84, 88)),
    (1, 1): dict(kind="vert", k=0.86, front_y=91, cap=(91, 95)),
    (0, 1): dict(kind="top", k=0.86, end_y=97),
    (1, 5): dict(kind="top", k=0.86, end_y=90),
}
CAR = {0: "650", 1: "651"}


def u_of_x(anc, x):
    pts = sorted((xv, FEAT_U[k]) for k, xv in anc.items())
    xs = [a for a, _ in pts]; us = [b for _, b in pts]
    if x <= xs[0]:
        return us[0] + (x - xs[0]) * (us[1] - us[0]) / (xs[1] - xs[0])
    if x >= xs[-1]:
        return us[-1] + (x - xs[-1]) * (us[-1] - us[-2]) / (xs[-1] - xs[-2])
    return float(np.interp(x, xs, us))


def u_span(anc, x):
    a, b = u_of_x(anc, x - 0.5), u_of_x(anc, x + 0.5)
    lo, hi = min(a, b), max(a, b)
    return [u for u in range(int(np.floor(lo + 0.5)), int(np.floor(hi + 0.5)) + 1) if lo - 0.5 < u <= hi + 0.5] or [int(round((a + b) / 2))]


def pick(car, us, h, diag=False):
    best, bp = None, 0
    for u in us:
        kk = LIV[car].get((u, h))
        if diag and kk in ("w", "L") and u < 14:
            kk = None                # too dense next to the hood in the 45-degree views
        if PRIO[kk] > bp:
            best, bp = kk, PRIO[kk]
    return best


def band_columns(t, v):
    """[(x, h0)] of the side band."""
    out = []
    anc = v["anc"]
    xs = sorted(anc.values())
    for x in range(int(np.floor(xs[0])) - 1, int(np.ceil(xs[-1])) + 2):
        g = v["y0"] + v["s"] * ((x - v["x0"]) // 2)
        found = None
        for y in (g, g - 1, g + 1):
            if 0 <= y < 127 and tuple(t[y, x]) in WHITES and tuple(t[y + 1, x]) in BAND:
                found = y
                break
        if found is None:
            continue
        out.append((x, found))
    return out


def paint_band_pixel(t, o, x, y, h, u_list, car, k, near_nose, diag=False):
    src = tuple(t[y, x])
    if src == Q:
        return
    if src == q and h >= 2:
        # door leaf (doors run h2..h8) or Najbrt stripe remnant
        col = [tuple(t[yy, x]) for yy in range(y - h + 7, y - h + 9)]
        if q in col:
            o[y, x] = shade(DOOR, 1.0 if k >= 0.99 else (0.96 if k > 0.8 else 0.88))
            return
    if src in (U, TT):
        o[y, x] = WIN
        return
    if h >= 7:
        if src == X or src in WHITES:
            o[y, x] = shade(SKIRT, 1.0 if k >= 0.99 else (0.95 if k > 0.8 else 0.86))
        return
    if src in BODY or src in WHITES or src == q or (src == X and near_nose):
        kk = pick(car, u_list, h, diag)
        if kk == "W":
            if src in WHITES:
                return                      # source hood white keeps its shading
            o[y, x] = hx(0xF3F7FA) if k >= 0.89 else hx(0xB0BAC3)
            if src == X:
                o[y, x] = hx(0x9EA7AF)
            return
        if kk in KCOL:
            o[y, x] = shade(KCOL[kk], 1.0 if k >= 0.99 else (0.94 if k > 0.8 else 0.80))
            return
        base = BLUE
        if src == B:
            base = shade(BLUE, 0.82)
        o[y, x] = shade(base, k)


def roof_pixel(t, o, x, y):
    src = tuple(t[y, x])
    if src == ROOF_SKIN:
        o[y, x] = ROOF
    elif src == ROOF_TOP:
        o[y, x] = FAIR_TOP
    elif src in ROOF_DARK:
        lum = src[0] / 0x46
        o[y, x] = shade(FAIR, 0.85 + 0.15 * lum)


def paint_tile(t, row, col):
    v = VIEWS[(row, col)]
    car = CAR[row]
    o = t.copy()
    k = v["k"]
    bg = np.all(t == T, axis=2)
    if v["kind"] == "diag":
        cols = band_columns(t, v)
        done = set()
        for x, h0 in cols:
            ul = u_span(v["anc"], x)
            un = u_of_x(v["anc"], x)
            for h in range(1, 9):
                y = h0 + h
                if y >= 128 or bg[y, x]:
                    continue
                paint_band_pixel(t, o, x, y, h, ul, car, k, un < 2.5, diag=True)
            # roof above the stripe (skip the stripe itself)
            for y in range(0, h0):
                if not bg[y, x]:
                    roof_pixel(t, o, x, y)
            if tuple(t[h0 - 1, x]) == ROOF_SKIN:
                o[h0 - 1, x] = ROOF_EDGE
            done.add(x)
    elif v["kind"] == "side":
        tip, dr = v["tip"], v["dir"]
        for x in range(128):
            u = (x - tip) * dr
            if u < 1 or u > 72:
                continue
            for h in range(1, 9):
                y = 83 + h
                if bg[y, x]:
                    continue
                paint_band_pixel(t, o, x, y, h, [u], car, k, u <= 1)
            for y in range(0, 83):
                if not bg[y, x]:
                    roof_pixel(t, o, x, y)
            if tuple(t[82, x]) == ROOF_SKIN:
                o[82, x] = ROOF_EDGE
    elif v["kind"] in ("vert", "top"):
        lim = v.get("front_y", v.get("end_y"))
        for x in range(128):
            for y in range(0, lim):
                if not bg[y, x]:
                    roof_pixel(t, o, x, y)
    if v["kind"] == "diag":
        # nose corner column: the white hood's rounded edge instead of Najbrt's grey line
        xn = int(v["anc"]["nose"])
        ys = [y for y in range(128) if tuple(t[y, xn]) == X]
        for y in ys[:-2]:
            o[y, xn] = hx(0x9EA7AF) if k > 0.9 else hx(0x8D959C)
        for y in ys[-2:]:
            o[y, xn] = shade(SKIRT, 1.0 if k > 0.9 else 0.86)
    paint_ends(t, o, row, col, v, car)
    return o


def paint_ends(t, o, row, col, v, car):
    """cab fronts / inner ends: explicit regions per view."""
    kf = 0.86
    reg = []
    inner = []
    kind = v["kind"]
    if kind == "diag":
        nose = int(v["anc"]["nose"]); end = v["anc"]["end"]
        if v["front"] == "right" or (v["front"] == "hidden" and nose > end):
            reg = [(x, y) for x in range(nose + 1, 128) for y in range(128)]
            inner = [(x, y) for x in range(0, int(np.floor(end))) for y in range(128)]
        else:
            reg = [(x, y) for x in range(0, nose) for y in range(128)]
            inner = [(x, y) for x in range(int(np.ceil(end)) + 1, 128) for y in range(128)]
        if v["front"] == "hidden":
            reg = []
    elif kind == "side":
        reg = [(v["tip"], y) for y in range(128)]
    elif kind == "vert":
        reg = [(x, y) for x in range(128) for y in range(v["front_y"], 128)]
    elif kind == "top":
        inner = [(x, y) for x in range(128) for y in range(v["end_y"], 128)]
    cap = v.get("cap", (-1, -1))
    for x, y in reg:
        src = tuple(t[y, x])
        if src == tuple(T):
            continue
        if src in (U, TT):
            o[y, x] = WIN
        elif src in (C, G, B, F):
            o[y, x] = shade(BLUE, kf)
        elif src == q:
            o[y, x] = DOOR
        elif (src in ROOF_DARK or src == ROOF_SKIN) and cap[0] <= y <= cap[1]:
            o[y, x] = shade(BLUE, kf * 0.92)          # blue cap above the windscreen
        elif y < cap[0]:
            roof_pixel(t, o, x, y)
    for x, y in inner:
        src = tuple(t[y, x])
        if src in (C, G, B, F):
            o[y, x] = shade(BLUE, 0.80)
    # headlights: 0xFFFF53 on the 650 (lead), plain white lamps on the 651
    for hc in HLIGHT:
        mm = np.all(t == np.array(hc), axis=2)
        o[mm] = HEAD if car == "650" else hx(0xE4E4FF)
    mm = np.all(o == np.array(TT), axis=2)
    o[mm] = WIN


def rows():
    """The IDPK sheet as rows of 8 tiles (row 0 = 650, row 1 = 651)."""
    src = np.array(Image.open(SRC).convert("RGB"))
    return [[paint_tile(src[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128], r, c) for c in range(8)]
            for r in (0, 1)]
