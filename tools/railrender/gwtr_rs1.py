"""GW Train Regio 841.2 (Stadler Regio-Shuttle RS1) liveries.

Zone-map repaint of the CeskeDrahy 841.2 sheets (pak128.CS CD_840 body by
Lubak91, repainted per livery in vehicle-rail/ceske-drahy/841_2/sprites/), so
both operators' RS1s share one silhouette in game. The six CD sheets have the
same silhouette; pixels that are identical in all six are Lubak91's fixed
detail (glass, windscreens, lamps, bogies, underframe) and are kept, every
other pixel is repainted here from a livery design in car coordinates.

Per view the script
  1. maps every body pixel to a face and car coordinates: the pure views
     directly (side ne/sw: u along the car, k rows below the cantrail; ends
     nw/se: v across the end, k rows below the cab cap), the diagonal views
     (w/n/e/s) through the side map they are a sheared copy of (fitted on the
     six CD sheets) and the end face measured from the lamps and windscreen;
  2. recovers the CD painter's per-pixel shading from the six sheets and their
     known albedos, and keeps it as relative detail (window pillars, the
     highlight under the cantrail, frame shadows) on top of the face levels of
     the rendered GWTR stock (side 1.0 w/e, 0.86 ne/sw, 0.72 n/s);
  3. paints the side (u, k), end (v, k) and roof designs of the liveries,
     keeps the lit window glass (0x4D4D4D) apart from vinyl on the windows, the
     plain windscreens and the source's headlights (front) / tail lights (rear).

u = 0 at the front nose, 1 at the rear nose (the car's front is the headlight
end: e / se / s views). k = 0 is the cantrail row, windows k 3..7, k 10 the
lowest body row, k 11 the skirt under the cabs.

Liveries: plzenskykraj (IDPK blue, white cab "C", yellow doors, swoosh),
ideska (Jihocesky kraj dark green with bright-green bars, since 12/2025) and
oranzovozelena (GWTR orange with green cab ends, as the RegioSprinter).

Regenerate with `python tools/railrender/gwtr.py 841_2 [--preview DIR]`.
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC_DIR = os.path.join(REPO, "vehicle-rail", "ceske-drahy", "841_2", "sprites")
# svetlesheda (plain light grey) is the base: its fixed pixels are kept
SOURCES = ["svetlesheda", "pardubickykraj", "najbrt2", "dukzelenobila", "hzlkremovacervena", "pidsedocervena"]

LIVERIES = ["plzenskykraj", "ideska", "oranzovozelena"]

T = (231, 255, 255)


def hx(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def hexarr(a):
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
GLASS, HEAD, TAIL = 0x4D4D4D, 0xFFFF53, 0xFF211D
KEEP = {GLASS, 0x57656F, HEAD, TAIL}

# ------------------------------------------------------------------ geometry
# Faces
NONE, SIDE, END, ROOF = 0, 1, 2, 3
# pure side views: col -> (x of the front nose, direction of u along +x)
SIDE_TOP = 82                      # cantrail row (k = 0) in the ne / sw views
SIDE_LEN = 66.5                    # nose to nose, px
PURE_SIDE = {3: (82.5, -1), 7: (37.5, +1)}
# pure end views: col -> (end, cap row = k 0, roof rows (front y, rear y))
PURE_END = {5: ("front", 88, (87.5, 55.5)), 1: ("rear", 91, (90.5, 58.5))}
# diagonal views: side map (source side col, s, bx, by, slope): the pixel
# (x, y) is the side-view pixel (round(s*x + bx), round(y - slope*x + by));
# fitted on the six CD sheets (trimmed feature distance, all 8 views).
DIAG_SIDE = {0: (7, 1.41, -17, 30, 0.5), 2: (3, 1.38, -40, -33, -0.5),
             4: (3, 1.42, -17, 30, 0.5), 6: (7, 1.40, -42, -33, -0.5)}
# end face of the diagonal views (from the lamps and the windscreen): which end,
# columns x0..x1, the corner column next to the visible side, x of the first
# lamp (maps to pure-end x 59, the second lamp to 67, 1.6 px per px) and the
# cap row cap(x) = c0 + sign * floor((x - xl) / 2).
DIAG_END = {4: ("front", 71, 76, 70, 71, 85, -1), 0: ("rear", 87, 92, 86, 87, 93, -1),
            2: ("rear", 35, 40, 41, 35, 91, +1), 6: ("front", 51, 56, 57, 51, 83, +1)}

# face brightness of the rendered GWTR stock (railkit: 845 / 818)
SIDE_LEVEL = {0: 1.0, 4: 1.0, 3: 0.86, 7: 0.86, 2: 0.72, 6: 0.72}
END_LEVEL = {0: 0.72, 4: 0.72, 1: 0.86, 5: 0.86, 2: 1.0, 6: 1.0}


def _cap(spec, x):
    xl, c0, sg = spec[4:]
    return c0 + sg * ((x - xl) // 2)


def geometry(mask):
    """Per-pixel face, u (0 front .. 1 rear), k (row) and v (0..1 across the
    end, pure end-view x 58..68) for the 128 x 1024 sheet row."""
    face = np.zeros((128, 1024), int)
    U = np.full((128, 1024), np.nan)
    K = np.full((128, 1024), -99, int)
    V = np.full((128, 1024), np.nan)
    for col in range(8):
        sl = slice(col * 128, (col + 1) * 128)
        m = mask[:, sl]
        f, u, k, v = face[:, sl], U[:, sl], K[:, sl], V[:, sl]
        ys, xs = np.where(m)
        for y, x in zip(ys, xs):
            if col in PURE_SIDE:
                xn, dr = PURE_SIDE[col]
                u[y, x] = (x - xn) * dr / SIDE_LEN
                k[y, x] = y - SIDE_TOP
                f[y, x] = ROOF if y < SIDE_TOP else SIDE
            elif col in PURE_END:
                end, cap, (yf, yr) = PURE_END[col]
                if y < cap:
                    f[y, x] = ROOF
                    u[y, x] = (y - yf) / (yr - yf)
                    k[y, x] = y - cap
                else:
                    f[y, x] = END
                    k[y, x] = y - cap
                    v[y, x] = (x - 58) / 10.0
                    u[y, x] = 0.0 if end == "front" else 1.0
            else:
                es = DIAG_END[col]
                if es[1] <= x <= es[2]:
                    cap = _cap(es, x)
                    xp = 59 + (x - es[4]) * 1.6
                    k[y, x] = y - cap
                    v[y, x] = min(1.0, max(0.0, (xp - 58) / 10.0))
                    u[y, x] = 0.0 if es[0] == "front" else 1.0
                    f[y, x] = END if y >= cap else ROOF
                    continue
                src, s, bx, by, slope = DIAG_SIDE[col]
                sy = int(round(y - slope * x + by))
                kk = sy - SIDE_TOP
                # a roof-top pixel lies across the roof from the near roof
                # edge: project it back along the car's cross direction
                xa = x + (kk + 1) * (1 if slope > 0 else -1) if kk < -1 else x
                sx = int(round(s * xa + bx))
                xn, dr = PURE_SIDE[src]
                u[y, x] = min(1.0, max(0.0, (sx - xn) * dr / SIDE_LEN))
                k[y, x] = kk
                f[y, x] = ROOF if kk < 0 else SIDE
    return face, U, K, V


# ------------------------------------------------------------------ sources
_CACHE = {}

# Unshaded albedos the CD painter used per source sheet (its livery table): a
# source pixel is albedo * shade, so every sheet that shows a pixel unclipped
# gives an estimate of Lubak91's shading there.
_LG, _YEL, _WHITE = (210, 214, 217), (238, 196, 24), (240, 241, 243)
CD_ALBEDO = {
    "svetlesheda": [_LG, (78, 80, 84), _YEL],
    "pardubickykraj": [(33, 58, 128), (228, 64, 46), (236, 238, 241), (230, 190, 0), _YEL,
                       (210, 40, 40), (60, 90, 170)],
    "najbrt2": [(214, 220, 224), (38, 120, 192), (30, 52, 94), (206, 211, 209), (38, 66, 138), _YEL,
                _WHITE, (64, 100, 170)],
    "dukzelenobila": [(92, 178, 74), (220, 224, 226), _WHITE],
    "hzlkremovacervena": [(232, 224, 196), (184, 36, 60)],
    "pidsedocervena": [(205, 209, 213), (216, 64, 58), (92, 96, 100), _YEL, _WHITE],
}


def sources():
    if not _CACHE:
        refs = np.stack([np.array(Image.open(os.path.join(SRC_DIR, n + ".png")).convert("RGB"))[:128, :1024]
                         for n in SOURCES]).astype(int)
        bg = np.all(refs[0] == np.array(T), axis=-1)
        fixed = np.all(refs == refs[0:1], axis=(0, 3)) & ~bg
        face, U, K, V = geometry(~bg)
        _CACHE.update(refs=refs, bg=bg, fixed=fixed, face=face, U=U, K=K, V=V)
        _CACHE["detail"] = _detail(refs, bg, fixed, face, K)
        pk = refs[SOURCES.index("pardubickykraj")].astype(float)
        # doors: the Pardubice sheet has yellow door leaves; roof boxes: its
        # A/C boxes are white on a navy roof
        # (the CD door zone runs up to the cantrail; the leaves end at the
        # window tops, k 2)
        _CACHE["door"] = ((pk[..., 0] > 150) & (pk[..., 1] > 110) & (pk[..., 2] < 90)
                          & ~fixed & (face == SIDE) & (K >= 2))
        lum = 0.299 * pk[..., 0] + 0.587 * pk[..., 1] + 0.114 * pk[..., 2]
        _CACHE["box"] = (lum > 150) & (pk.max(-1) - pk.min(-1) < 40) & ~fixed & (face == ROOF)
        _CACHE["roofd"] = _roof_detail(refs, bg, face)
    return _CACHE


def _estimate(c, pal):
    """Best shade factor of colours c [...,3] over the albedos pal (nan where no
    albedo explains the colour within tolerance or the colour is clipped)."""
    c = c.astype(float)
    best = np.full(c.shape[:-1], np.nan)
    berr = np.full(c.shape[:-1], 1e9)
    clipped = (c.max(axis=-1) >= 253)
    for a in pal:
        a = np.array(a, float)
        f = (c * a).sum(-1) / (a * a).sum()
        err = np.abs(c - f[..., None] * a).max(-1)
        ok = (err <= np.maximum(3.0, 0.035 * c.max(-1))) & (f > 0.3) & (f < 1.7) & ~clipped & (err < berr)
        best[ok] = f[ok]
        berr[ok] = err[ok]
    return best


def _detail(refs, bg, fixed, face, K):
    """Relative shading of every repainted side / end pixel: the CD shade
    factor (median over the source sheets) divided by the median of its row
    (view, face, k). Lubak91's per-row levels differ from view to view (they
    would band a plain body colour), his pillars, frames and seams do not."""
    est = np.stack([_estimate(refs[i], CD_ALBEDO[n]) for i, n in enumerate(SOURCES)])
    fac = _nanmed(est)
    det = np.ones((128, 1024))
    for col in range(8):
        sl = slice(col * 128, (col + 1) * 128)
        for fc in (SIDE, END):
            m = (face[:, sl] == fc) & ~fixed[:, sl] & ~bg[:, sl] & ~np.isnan(fac[:, sl])
            if not m.any():
                continue
            fmed = np.median(fac[:, sl][m])
            for k in np.unique(K[:, sl][m]):
                mk = m & (K[:, sl] == k)
                med = np.median(fac[:, sl][mk]) if mk.sum() >= 4 else fmed
                d = det[:, sl]
                d[mk] = np.clip(fac[:, sl][mk] / med, 0.6, 1.3)
    return det


def _nanmed(est):
    out = np.full(est.shape[1:], np.nan)
    n = (~np.isnan(est)).sum(0)
    s = np.sort(np.where(np.isnan(est), np.inf, est), axis=0)
    for c in range(1, est.shape[0] + 1):
        m = n == c
        if not m.any():
            continue
        lo = s[(c - 1) // 2][m]
        hi = s[c // 2][m]
        out[m] = (lo + hi) / 2
    return out


def _roof_detail(refs, bg, face):
    """Roof shading: the najbrt2 roof is sapphire recoloured by Lubak91's roof
    luminance (never clipped), so lum / lum(sapphire) is the roof relief."""
    n2 = refs[SOURCES.index("najbrt2")].astype(float)
    lum = 0.299 * n2[..., 0] + 0.587 * n2[..., 1] + 0.114 * n2[..., 2]
    sap = 0.299 * 30 + 0.587 * 52 + 0.114 * 94
    d = np.clip(lum / sap, 0.5, 1.6)
    d[bg] = 1.0
    return d


# ------------------------------------------------------------------ lettering
# bold caps, 5 rows (top first); '#' = letter
_GLYPHS = {
    "A": [".##.", "#..#", "####", "#..#", "#..#"],
    "D": ["###.", "#..#", "#..#", "#..#", "###."],
    "E": ["###", "#..", "##.", "#..", "###"],
    "G": [".###", "#...", "#.##", "#..#", ".###"],
    "I": ["#", "#", "#", "#", "#"],
    "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#..#", "#.#.", "##..", "#.#.", "#..#"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "P": ["###.", "#..#", "###.", "#...", "#..."],
    "R": ["###.", "#..#", "###.", "#.#.", "#..#"],
    "S": [".###", "#...", ".##.", "...#", "###."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "Z": ["####", "...#", "..#.", ".#..", "####"],
}


def word_bitmap(text):
    cols = []
    for i, ch in enumerate(text):
        if ch == " ":
            cols += [[0] * 5]
            continue
        g = _GLYPHS[ch]
        for c in range(len(g[0])):
            cols.append([1 if g[r][c] == "#" else 0 for r in range(5)])
        if i + 1 < len(text):
            cols.append([0] * 5)
    return np.array(cols, float).T          # 5 x n


WORDS = {w: word_bitmap(w) for w in ("GW TRAIN", "IDESKA", "PLZENSKY KRAJ")}


def word_hit(word, t, zz, ft, fz, thr=0.42):
    """White / not for a pixel at t (0..1 along the word as read) and zz (0..1
    up) with a pixel footprint ft x fz (fractions of the word): coverage of
    the bitmap over the footprint, so the 1x sprite keeps the letter rhythm."""
    bm = WORDS[word]
    rows, cols = bm.shape
    x0, x1 = (t - ft / 2) * cols, (t + ft / 2) * cols
    y0, y1 = (1 - zz - fz / 2) * rows, (1 - zz + fz / 2) * rows
    c0, c1 = max(0, int(np.floor(x0))), min(cols, int(np.ceil(x1)))
    r0, r1 = max(0, int(np.floor(y0))), min(rows, int(np.ceil(y1)))
    if c0 >= c1 or r0 >= r1:
        return False
    tot = cov = 0.0
    for r in range(r0, r1):
        wy = min(y1, r + 1) - max(y0, r)
        for c in range(c0, c1):
            wgt = wy * (min(x1, c + 1) - max(x0, c))
            tot += wgt
            cov += wgt * bm[r, c]
    return tot > 0 and cov / tot >= thr


def lettering(c, word, u0, u1, k0, k1, thr=0.42):
    """True if pixel c is lettering of `word` placed over u0..u1 (along the
    car) and rows k0..k1 of the side; reads left to right as seen (the right
    side of the car has its front on the right, the left side on the left)."""
    u, k = c["u"], c["k"]
    if not (u0 - 0.01 <= u <= u1 + 0.01 and k0 <= k <= k1):
        return False
    t = (u1 - u) / (u1 - u0) if c["side"] == "R" else (u - u0) / (u1 - u0)
    zz = (k1 + 0.5 - k) / (k1 - k0 + 1)
    ft = c["du"] / (u1 - u0)
    return word_hit(word, t, zz, ft, 1.0 / (k1 - k0 + 1), thr)


# ------------------------------------------------------------------ car layout
# u along the car at the pure side view's pixel centres
NOSE = 0.035                          # rounded cab front seen from the side
WIN_FRONT = (0.105, 0.226)            # big window of the front end section
WIN_MID = (0.33, 0.677)               # window row of the low-floor middle
WIN_REAR = (0.782, 0.902)             # big window of the rear end section
WINDOWS = (WIN_FRONT, WIN_MID, WIN_REAR)


def in_window(c):
    return 3 <= c["k"] <= 7 and any(a <= c["u"] <= b for a, b in WINDOWS)


# ------------------------------------------------------------------ liveries
BLACK = (0x1C, 0x1E, 0x21)            # printed / framed window band
COUPLER = (0x34, 0x36, 0x3A)          # coupler, buffers and hoses of the lower front
UNDERFRAME = (0x5A, 0x5E, 0x64)       # underframe edge (at source luminance 160)

# IDPK, Plzensky kraj (colours of regiopanter_idpk.py, Arriva 650)
PK_BLUE = (0x16, 0x5E, 0xBC)
PK_DOOR = (0xF6, 0xC8, 0x1C)
PK_YEL = (0xF8, 0xD2, 0x22)
PK_GRN = (0x34, 0xAC, 0x4A)
PK_SWH = (0xF2, 0xF5, 0xF8)
PK_LET = (0xE8, 0xEE, 0xF4)
PK_WHITE = (0xEC, 0xEF, 0xF2)         # white cab "C" and roof
PK_SKIRT = (0x46, 0x4A, 0x52)         # charcoal skirt band (#2E2A2E in photos, lifted for 1x)
PK_BOX = (0xB8, 0xBE, 0xC4)           # light-grey roof A/C boxes

# IDESKA, Jihocesky kraj
ID_DARK = (0x1E, 0x6B, 0x5C)          # teal body (photo #306B66..#44817C overcast; darker for contrast)
ID_BRIGHT = (0x3D, 0xA0, 0x34)
ID_YEL = (0xE8, 0xC8, 0x00)
ID_WHITE = (0xF2, 0xF4, 0xF5)

# GWTR orange with green cab ends
GW_ORANGE = (0xE8, 0x64, 0x1E)
GW_GREEN = (0x11, 0x6B, 0x48)
GW_LIME = (0x52, 0xC0, 0x40)
GW_WHITE = (0xF2, 0xF4, 0xF5)
GW_ROOF = (0xC3, 0xC7, 0xCA)
GW_AC = (0xE2, 0xE6, 0xE8)


def _lower_front(c, col):
    """Rows k 10..11 of the end face: the source's dark coupler, buffers and
    hoses stay dark, the buffer-beam corners take the livery colour."""
    if c["srclum"] < 70:
        return ("dim", COUPLER)
    return col


def plzenskykraj(c):
    f, k, w = c["face"], c["k"], c["w"]
    if f == ROOF:
        if c["fixed"]:
            return None
        return PK_BOX if c["box"] else PK_WHITE
    if f == END:
        if c["fixed"]:
            return None
        if k >= 12:
            return PK_YEL                                  # yellow strip under the buffer beam
        if k >= 10:
            return _lower_front(c, PK_BLUE)
        if k <= 6 and (c["v"] <= 0.05 or c["v"] >= 0.95):
            return PK_WHITE                                # white hood round the windscreen sides
        return PK_BLUE                                     # thin blue cap edge, blue face under the windscreen
    if c["fixed"]:
        if c["skirt"]:
            return PK_SKIRT                                # skirt under the cab
        if c["wscreen_side"]:
            return PK_WHITE                                # the hood hides the windscreen's side
        if not c["glass"]:
            return None
    swoosh = _pk_swoosh(c)
    if c["glass"]:
        return ("flat", swoosh) if swoosh else None
    if c["door"]:
        return PK_DOOR
    if k >= 10:
        return PK_SKIRT
    if _pk_hood(k, w):
        return PK_WHITE                                    # the white hood of the cab end
    if swoosh:
        return swoosh
    if lettering(c, "PLZENSKY KRAJ", 0.112, 0.222, 9, 9) or lettering(c, "PLZENSKY KRAJ", 0.778, 0.888, 9, 9):
        return PK_LET
    return PK_BLUE


def _pk_hood(k, w):
    """White hood of the IDPK cab ends on the side (841 268): over the cab
    window to behind it at the top, in front of it (about 1.1 m) down to a
    quarter of the body height, the lower edge sweeping down to the nose."""
    if k <= 1:
        return w < 0.095
    if k <= 7:
        return w < 0.046
    if k == 8:
        return w < 0.03
    if k == 9:
        return w < 0.02
    return False


def _pk_swoosh(c):
    """Plzensky kraj swoosh: green, white and yellow arcs rising across the
    end-section windows towards the doors, strokes on the middle windows next
    to each door (photos of 841 268 / 841 263)."""
    k, d = c["k"], c["w"]
    rear = c["u"] > 0.5
    if 0.08 <= d <= 0.235 and 2 <= k <= 8:
        kg = 8.3 - (d - 0.08) / 0.155 * 6.3           # green arc
        if abs(k - kg) < 0.55:
            return PK_GRN
        if abs(k - (kg - 1.3)) < 0.5 and d > 0.12:
            return PK_SWH
        if abs(k - (kg - 2.5)) < 0.5 and d > 0.15 and not c["glass"]:
            return PK_YEL                              # (keeps most of the glass lit)
    if 0.325 <= d <= 0.37 and 3 <= k <= 7:
        kg = 7 - (d - 0.325) / 0.045 * 4.5
        if abs(k - kg) < 0.55:
            return PK_GRN
        if abs(k - (kg - 1.2)) < 0.5 and not c["glass"]:
            return PK_YEL if rear else PK_SWH
    return None


def ideska(c):
    """End A (low green band from the nose) is the front, end B (green hook
    under the roofline) the rear, as on 841 277."""
    f, u, k, w = c["face"], c["u"], c["k"], c["w"]
    front = u < 0.5
    if f == ROOF:
        if c["fixed"]:
            return None
        if c["box"]:
            return ID_BRIGHT                               # bright-green tops of the roof boxes
        if k == -1 and (0.665 <= u <= 0.685 or 0.905 <= u <= 0.925):
            return ID_BRIGHT                               # bars turning up into the roofline
        return ID_DARK
    if f == END:
        if c["fixed"]:
            return None
        if k >= 12:
            return ID_YEL
        if k >= 10:
            return _lower_front(c, ID_DARK)
        return ID_DARK
    if c["fixed"]:
        if c["skirt"]:
            return ID_BRIGHT if (front and w < NOSE) else ID_DARK
        if not c["glass"]:
            return None
    if c["glass"]:
        # printed on the glass: the road "E" at the cab end of both end
        # windows, the white bar across the middle windows
        e = (WIN_FRONT[0] - 0.005 <= u <= WIN_FRONT[0] + 0.028) or (WIN_REAR[1] - 0.028 <= u <= WIN_REAR[1] + 0.005)
        if e and k in (4, 6):
            return ("flat", ID_WHITE)
        if e and k == 5:
            return ("flat", ID_BRIGHT)
        if k == 5 and 0.39 <= u <= 0.63:
            return ("flat", ID_WHITE)
        return None
    if c["door"]:
        return ID_BRIGHT
    if in_window(c):
        return ("dim", BLACK)
    # front end section: low band from the nose, sweeping down round it
    if front and ((9 <= k <= 10 and u <= 0.098) or (k == 11 and u < NOSE)):
        return ID_BRIGHT
    # rear end section: hook under the roofline next to the cab
    if not front and ((1 <= k <= 2 and 0.875 <= u <= 0.915) or (k == 0 and 0.905 <= u <= 0.925)):
        return ID_BRIGHT
    # middle: lower bar with a rounded downturn at the front door, upper bar
    # turning up into the roofline at the rear door
    if (k == 9 and 0.325 <= u <= 0.585) or (k == 10 and 0.318 <= u <= 0.336):
        return ID_BRIGHT
    if (k == 1 and 0.455 <= u <= 0.675) or (k == 0 and 0.665 <= u <= 0.685):
        return ID_BRIGHT
    if lettering(c, "IDESKA", 0.118, 0.222, 8, 9) or lettering(c, "IDESKA", 0.778, 0.882, 8, 9):
        return ID_WHITE
    return ID_DARK


def _gw_boundary(k):
    """Green cab / orange body boundary on the side (distance from the nose)
    at row k: from behind the cab window at the roof down to the nose at the
    front's lime line (k 8)."""
    if k >= 8:
        return 0.0
    return 0.118 * (1.0 - max(k, 0) / 8.0) ** 0.6


def oranzovozelena(c):
    f, k, w = c["face"], c["k"], c["w"]
    if f == ROOF:
        if c["fixed"]:
            return None
        if c["box"]:
            return GW_AC
        if w < 0.07:
            return GW_GREEN                                # green cab dome
        if w < 0.095 and k >= -2:
            return GW_LIME                                 # crescent reaching the roof edge
        return GW_ROOF
    if f == END:
        if c["fixed"]:
            return None
        if k >= 12:
            return GW_ORANGE
        if k >= 10:
            return _lower_front(c, GW_ORANGE)
        if k == 9:
            return GW_LIME                                 # lime line just below the lamps
        return GW_GREEN
    if c["fixed"]:
        if c["skirt"]:
            return GW_ORANGE
        if not c["glass"]:
            return None
    if c["glass"]:
        return None
    if c["door"]:
        return GW_GREEN
    if k >= 8 and (lettering(c, "GW TRAIN", 0.07, 0.225, 8, 9, thr=0.3)
                   or lettering(c, "GW TRAIN", 0.775, 0.93, 8, 9, thr=0.3)):
        return GW_WHITE                                    # big white wordmark on the lower cab side
    b = _gw_boundary(k)
    if k <= 8 and w < b:
        return GW_GREEN
    if k <= 8 and w < b + 0.03:
        return GW_LIME
    if in_window(c):
        return ("dim", BLACK)
    return GW_ORANGE


DESIGNS = {"plzenskykraj": plzenskykraj, "ideska": ideska, "oranzovozelena": oranzovozelena}

# mild row profile of the side wall (Lubak91's own row levels are normalised
# away): the curved top under the cantrail catches light, the bottom less
SIDE_PROFILE = {0: 1.02, 1: 1.06, 10: 0.94, 11: 0.9}


# ------------------------------------------------------------------ painter
def _safe(col):
    col = tuple(int(max(0, min(255, round(v)))) for v in col)
    h = (col[0] << 16) | (col[1] << 8) | col[2]
    if h in SPECIAL and h not in KEEP:
        col = (col[0], col[1], col[2] + 1 if col[2] < 255 else col[2] - 1)
    return col


def paint_row(liv):
    """128 x 1024 sheet row of one livery."""
    C = sources()
    design = DESIGNS[liv]
    src = C["refs"][0]
    face, U, K, V = C["face"], C["U"], C["K"], C["V"]
    out = src.astype(np.uint8).copy()
    vals = hexarr(src)
    lum = 0.299 * src[..., 0] + 0.587 * src[..., 1] + 0.114 * src[..., 2]
    ys, xs = np.where(~C["bg"])
    for y, X in zip(ys, xs):
        col, x = X // 128, X % 128
        fc = face[y, X]
        if fc == NONE:
            continue
        u = float(U[y, X])
        side_col = col if col in PURE_SIDE else DIAG_SIDE.get(col, (None,))[0]
        c = dict(col=col, x=x, y=y, face=fc, u=u, w=min(u, 1 - u), k=int(K[y, X]), v=float(V[y, X]),
                 side="R" if side_col == 3 else ("L" if side_col == 7 else None),
                 du=(1.0 if col in PURE_SIDE else 1.41) / SIDE_LEN,
                 fixed=bool(C["fixed"][y, X]), glass=vals[y, X] == GLASS, door=bool(C["door"][y, X]),
                 box=bool(C["box"][y, X]), srclum=float(lum[y, X]), skirt=False)
        # Lubak91 lets the windscreen show round the nose in the side-facing
        # views (the cab side windows sit further back, w >= 0.045, k >= 2)
        c["wscreen_side"] = (vals[y, X] == 0x6B6B6C and fc in (SIDE, ROOF)
                             and (c["w"] < 0.035 or (c["k"] < 2 and c["w"] < 0.046)))
        det = float(C["detail"][y, X])
        if c["fixed"]:
            s = src[y, X]
            if lum[y, X] >= 240 and s.max() - s.min() < 12:
                # white edge highlights drawn identically in every CD sheet
                # (roof edge of the nw / se views, nose corners): the livery
                # colour, lit
                c["fixed"], det = False, 1.3
            elif fc == SIDE and c["k"] >= 11 and lum[y, X] > 115 and s[2] - s[0] >= 8:
                # the light blue-grey skirt / underframe edge of the upstream
                # Najbrt art: the livery's skirt under the cabs, dark
                # underframe grey elsewhere
                if c["w"] >= 0.1:
                    out[y, X] = _safe(tuple(v * lum[y, X] / 160.0 for v in UNDERFRAME))
                    continue
                c["skirt"] = True
        r = design(c)
        if r is None:
            continue
        mode, colr = r if isinstance(r[0], str) else ("shade", r)
        if mode == "flat":
            f = 1.0
        elif fc == ROOF:
            f = float(C["roofd"][y, X]) * (det if det > 1.0 else 1.0)
        else:
            f = SIDE_LEVEL[col] * SIDE_PROFILE.get(c["k"], 1.0) if fc == SIDE else END_LEVEL[col]
            if mode == "shade":
                f *= det
        out[y, X] = _safe(tuple(v * f for v in colr))
    # no special colours other than the lit glass and the lamps
    v = hexarr(out)
    for h in set(np.unique(v).tolist()) & (SPECIAL - KEEP):
        out[v == h] = _safe(hx(h))
    return out


def rows_for(liv):
    """The sheet of one livery: 1 row (the railcar) of 8 tiles."""
    a = paint_row(liv)
    return [[a[:, c * 128:(c + 1) * 128] for c in range(8)]]
