"""The DPO Iveco-Dekstra LE 37 and Rosero First FCLEI CNG, re-based on VTPsim's
Prague art (tools/busrender/src/dpo/vtpsim-stratos_le_37.png: his LE 37 body
cut to 7.7 m, with the Daily bonnet, door 1 behind the front wheel and a double
door in the rear overhang; the Prague Rosero sheet is the same drawing with a
single rear door and a roof A/C, so both DPO buses start from the LE 37 one).

The PID trikolora is repainted zone by zone in DPO turquoise (the pixel
colours of VTPsim's sheet are the zones: roof, side and end blues, white band,
red, glass and frames), then each bus gets its own details:

- Dekstra LE 37 (7304-7310): single door 1 behind the front wheel, left side
  driver's window + 3 big windows, IVECO grille on the bonnet with the white
  line under it, a light A/C box at the rear of the roof, silver wheels.
- Rosero First FCLEI CNG (7311-7312): doors 2-2 (the LE 37 layout), the 2021
  Daily front (white line on the bonnet, black bumper), a turquoise CNG fairing
  over the rear two thirds of the roof with the Webasto A/C box ahead of it,
  turquoise wheel rims.

Columns of the front and rear ends in the diagonal views and the window posts
are measured on the frozen sheet (it never changes).
"""
import numpy as np

from render import Box, render, DIRS, HEAD, P
import dpo_otherkit as K
from dpo_otherkit import T, rgb, is_bg

ROOF_BLUE = 0x285BB6
SIDE_BLUES = {0x275AB3, 0x2657AD}
REDS = {0xC00A13, 0xA90911}
WHITE = 0xE9E9E9
GLASS = 0x4D4D4D
DISPLAY = 0xF0A018
LAMP = 0xFFFF53
HUBS = {0x555555, 0x7B7B7B, 0x848484}
COWL = {0x191919, 0x292929, 0x000000, 0x080808, 0x161616, 0x212121}

# front-end / rear-end columns of the diagonal views (all of nw is the rear,
# all of se the front)
FRONT_COLS = {"e": range(50, 58), "s": range(50, 58), "se": range(0, 128)}
REAR_COLS = {"w": range(64, 74), "n": range(72, 80), "nw": range(0, 128)}
# the five left window posts (u = 1.41 .. 7.07 m) per view, and where the posts
# of the Dekstra's driver's window + three big windows go
POSTS_L = {"sw": [54, 60, 66, 72, 78], "w": [46, 50, 54, 58, 62], "s": [63, 67, 71, 75, 79]}
POSTS_DEKSTRA = {"sw": [54, 62, 70, 78], "w": [46, 51, 57, 62], "s": [63, 68, 74, 79]}
POST_COL = {"sw": 0x212121, "w": 0x292929, "s": 0x191919}


def vals(t):
    return (t[..., 0].astype(np.int64) << 16) | (t[..., 1].astype(np.int64) << 8) | t[..., 2]


def runs(col, pred):
    """[(start, end)] of consecutive rows where pred holds"""
    out, s = [], None
    for y in range(len(col) + 1):
        ok = y < len(col) and pred(col[y])
        if ok and s is None:
            s = y
        elif not ok and s is not None:
            out.append((s, y - 1)); s = None
    return out


def paint(tile, d, bus):
    """the trikolora zones in DPO turquoise"""
    out = tile.copy()
    v = vals(tile)
    out[v == ROOF_BLUE] = K.ROOF
    for c in SIDE_BLUES | REDS:
        out[v == c] = K.BODY
    fr = FRONT_COLS.get(d, ())
    rr = REAR_COLS.get(d, ())
    for x in range(128):
        col = v[:, x]
        white = lambda c: c == WHITE or (x in fr and c == 0x7B7B7B)
        for y0, y1 in runs(col, white):
            if x in fr:
                # the bonnet: VTPsim's white bonnet panel
                n = y1 - y0 + 1
                if bus == "dekstra":
                    for y in range(y0, y1 + 1):
                        out[y, x] = K.WLINE if y == y1 else K.BODY
                else:
                    for y in range(y0, y1 + 1):
                        out[y, x] = K.BODY
                # the windscreen above the cowl: plain glass
                for y in range(max(0, y0 - 9), y0):
                    if col[y] == GLASS:
                        out[y, x] = K.CAB
                if bus == "rosero":
                    # 2021 Daily: black bumper under the bonnet
                    y = y1 + 1
                    while y < 128 and (col[y] in REDS or col[y] in (0xF55F1B, 0x141414)):
                        out[y, x] = K.MASK
                        y += 1
            elif x in rr:
                # rear: all turquoise, the rear window one row deeper
                for y in range(y0, y1 + 1):
                    out[y, x] = K.BODY
                if y0 > 0 and col[y0 - 1] == GLASS:
                    out[y0, x] = K.GLASS
            else:
                # side: the white line under the glazing, turquoise below
                for y in range(y0, y1 + 1):
                    out[y, x] = K.WLINE if y == y0 else K.BODY
    return out


def front_details(src, tile, d, bus):
    """se: the IVECO grille (Dekstra) or the white line on the bonnet and the
    lamps in the black bumper (Rosero); zones read on the source drawing src"""
    if d != "se":
        return tile
    out = tile.copy()
    v = vals(src)
    xs = [x for x in range(128) if (v[:, x] != 0xE7FFFF).any()]
    x0, x1 = min(xs), max(xs)
    cx = (x0 + x1) / 2
    for x in range(x0, x1 + 1):
        col = v[:, x]
        wr = runs(col, lambda c: c == WHITE or c == 0x7B7B7B)
        if not wr:
            continue
        y0, y1 = wr[-1]
        if bus == "dekstra" and abs(x - cx) <= 2 and y1 > y0:
            out[y0, x] = (0x1A, 0x1C, 0x1E)               # IVECO grille
        if bus == "rosero":
            if abs(x - cx) <= 2:
                out[y0, x] = K.WLINE                        # the white line on the bonnet
            if abs(x - cx) >= (x1 - x0) / 2 - 1:
                out[y1, x] = K.HEADL                        # lamps at the bonnet corners
                for y in range(y1 + 1, 128):
                    if v[y, x] == LAMP:
                        out[y, x] = K.MASK
    return out


def driver_window(tile, d):
    """the cab window on the left side: plain glass ahead of the first post"""
    if d not in POSTS_L:
        return tile
    out = tile.copy()
    v = vals(tile)
    first = POSTS_L[d][0]
    span = {"sw": range(48, first), "w": range(43, first), "s": range(58, first)}[d]
    for x in span:
        for y in range(128):
            if v[y, x] == GLASS:
                out[y, x] = K.CAB
    return out


def band_rows(v, x, post):
    """rows of the side glazing in column x (glass, the transom and post
    colours under the black frame row)"""
    gl = {GLASS, 0x424242, 0x3A3A3A, 0x292929, post}
    ys = [y for y in range(128) if v[y, x] in gl]
    if not ys:
        return []
    # the longest run
    best, cur = [], []
    for y in range(ys[0], ys[-1] + 2):
        if y < 128 and v[y, x] in gl:
            cur.append(y)
        else:
            if len(cur) > len(best):
                best = cur
            cur = []
    return best


def relayout_left(tile, d):
    """Dekstra: driver's window and three big windows on the left (the LE 37
    has four equal ones)"""
    if d not in POSTS_DEKSTRA:
        return tile
    out = tile.copy()
    v = vals(tile)
    post = POST_COL[d]
    old, new = POSTS_L[d], POSTS_DEKSTRA[d]
    for x in old:
        if x in new:
            continue
        # a glass column next to the post, with its rows aligned on the band top
        ref = x + 1 if (x + 1) not in old else x - 1
        rb, xb = band_rows(v, ref, post), band_rows(v, x, post)
        if not rb or not xb:
            continue
        for k, y in enumerate(xb):
            if k < len(rb):
                out[y, x] = tile[rb[k], ref]
    v2 = vals(out)
    for x in new:
        if x in old:
            continue
        for y in band_rows(v2, x, post):
            out[y, x] = rgb(post)
    return out


def narrow_door1(tile, d):
    """Dekstra: door 1 is a single leaf (ne: the LE 37 double door at x 69-75
    becomes a window at 69-71 and a single door at 72-75)"""
    if d != "ne":
        return tile
    out = tile.copy()
    for x in (69, 70, 71):
        out[93:106, x] = tile[93:106, 66]
    return out


def rims(tile, d):
    """Rosero: turquoise wheel rims"""
    out = tile.copy()
    v = vals(tile)
    ys, xs = np.where(~is_bg(tile))
    ylo = ys.max() - 4
    for y, x in zip(*np.where(np.isin(v, list(HUBS)))):
        if y >= ylo:
            out[y, x] = (0x00, 0x96, 0xBA)
    return out


# ------------------------------------------------------------------ roof items
def roof_frame(tile, d):
    """(centre, L, W) of the roof top drawn in this view: the roof colour region
    is the top face of a box, so its extent along the projected length and width
    axes gives the drawn length and width"""
    m = np.all(tile == np.array(K.ROOF), axis=-1)
    ys, xs = np.where(m)
    pts = np.c_[xs + 0.5, ys + 0.5]
    hx, hy = HEAD[d]
    ph = P(np.array([hx, hy, 0.0])); pr = P(np.array([-hy, hx, 0.0]))
    M = np.linalg.inv(np.array([ph, pr]).T)
    ab = (M @ pts.T).T
    a0, a1 = ab[:, 0].min(), ab[:, 0].max()
    b0, b1 = ab[:, 1].min(), ab[:, 1].max()
    # one pixel of slack: centres sit half a pixel inside the edges
    pa = 1.0 / max(np.hypot(*ph), 1e-6)
    pb = 1.0 / max(np.hypot(*pr), 1e-6)
    L = a1 - a0 + pa
    W = b1 - b0 + pb
    ca, cb = (a0 + a1) / 2, (b0 + b1) / 2
    centre = ca * ph + cb * pr
    return centre, L, W


def roof_items(tile, d, items, zt=2.9):
    """render boxes standing on the drawn roof: items = [(u0, u1 as fractions of
    the roof length from the front, half width as a fraction, height m, top,
    side, end)]"""
    centre, L, W = roof_frame(tile, d)
    origin = centre + np.array([0.0, 4.0 * zt])
    boxes, cols = [], {}
    body = Box("body", 0, L, -W / 2, W / 2, zt - 0.5, zt)
    for k, (f0, f1, fw, h, top, side, end) in enumerate(items):
        name = "item%d" % k
        boxes.append(Box(name, L * (1 - f1), L * (1 - f0), -fw * W / 2, fw * W / 2, zt, zt + h))
        cols[name] = (top, side, end)

    def tex(p):
        if p.box == "body":
            return (1, 2, 3)
        top, side, end = cols[p.box]
        if p.face == "top":
            return top
        if p.face in ("front", "rear"):
            return end
        return side
    img, _ = render(d, [body] + boxes, tex, L, origin)
    m = ~is_bg(img) & ~np.all(img == (1, 2, 3), axis=2)
    out = tile.copy()
    out[m] = img[m]
    return out


AC_TOP = (0xDA, 0xDC, 0xDE)
AC_SIDE = (0xB4, 0xB8, 0xBC)
DEKSTRA_ROOF = [(0.76, 0.94, 0.55, 0.20, AC_TOP, AC_SIDE, AC_SIDE)]
ROSERO_ROOF = [(0.40, 0.98, 0.72, 0.30, K.ROOF, K.BODY, K.BODY),
               (0.20, 0.40, 0.62, 0.22, K.ROOF, K.BODY, K.BODY)]


def rebase(rows, bus):
    out = []
    for i, d in enumerate(DIRS):
        t = rows[0][i]
        if bus == "dekstra":
            t = narrow_door1(t, d)
            t = relayout_left(t, d)
        src = t
        t = paint(t, d, bus)
        t = front_details(src, t, d, bus)
        t = driver_window(t, d)
        if bus == "rosero":
            t = rims(t, d)
        t = roof_items(t, d, DEKSTRA_ROOF if bus == "dekstra" else ROSERO_ROOF)
        out.append(t)
    return [out]


def dekstra(rows):
    return rebase(rows, "dekstra")


def rosero(rows):
    return rebase(rows, "rosero")
