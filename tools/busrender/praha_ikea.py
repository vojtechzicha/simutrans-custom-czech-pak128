"""The IKEA line's bus (VZ-Praha): the Conecto LF II in the IKEA forest wrap.

    python tools/busrender/praha_ikea.py [--preview DIR]

Line IKEA 2 (103116), Černý Most - IKEA Černý Most, free shuttle for IKEA
customers. In autumn 2026 a single bus runs it every day (seznam-autobusu
duty log, 15 Sep - 5 Nov 2026): ARRIVA STŘEDNÍ ČECHY 9501, 4SF 7497,
Mercedes-Benz Conecto LF II (2017, doors 2-2-2, ex-demonstrator, then MHD
Hořovice in the red-white town scheme), since 12/2024 in "CVR IKEA, bílá s
grafikou švédské tajgy" (seznam-autobusu photos 413770, 415105, 417104):

- front and roof white, the black windscreen band, a small IKEA logo on the
  front panel on the vehicle's right of the star;
- both sides wrapped up to the roof edge, windows included, with a dark
  Swedish forest: dark and light grey trunks, green moss over the lower body;
- the blue-yellow IKEA box in the window band, on the door side between the
  front axle and the middle door, on the off side just behind the driver;
- "Nästa stopp Sverige!" in white over the rear windows of the door side
  (too small to letter at this scale, left out);
- the front door is clear glass; the middle and rear doors are wrapped.
- The rear is on no photo; it is kept white (unverified).

The base is VTPsim's white Conecto LF sheet (vehicle-bus/mhd-kolin/
conecto_lf), the same body and door layout. Only the side faces of the fitted
box change (odis_town.fit): window glass keeps the lit-at-night specials,
special 28 for the dark forest and special 16 for the light trunks, so the
bus still lights up only while loaded; the cant and lower body take plain
colours. Trunks stand at fixed metres along the body, one pixel column each.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import odis_town as T                                                   # noqa: E402
from render import DIRS                                                 # noqa: E402

SRC = "vehicle-bus/mhd-kolin/conecto_lf/sprites/bila.png"
OUT = "vehicle-bus/praha/conecto_lf/sprites/ikea.png"
LS = [11.5, 12.0, 12.5]
BODY = 12.0                     # m; trunk and logo positions are along this

GLASS = (0x4D, 0x4D, 0x4D)      # special 28: window glass, dark forest
GLASS_HI = (0x57, 0x65, 0x6F)   # special 16: lighter glass, the light trunks
CANT = (0x2C, 0x30, 0x2E)       # the wrap's dark top above the windows
CANT_TRUNK = (0x6C, 0x75, 0x74)
MOSS = (0x5A, 0x68, 0x32)       # moss over the lower body
MOSS_HI = (0x93, 0x9F, 0x5C)
MOSS_TOP = (0x76, 0x80, 0x58)   # first row under the windows, grey-green
GAP = (0x2B, 0x2F, 0x24)        # dark gaps between the moss mounds
IKEA_BLUE = (0x00, 0x58, 0xA3)
IKEA_YELLOW = (0xFF, 0xDA, 0x1A)

Z_CANT = 2.45                   # above: the band over the windows
Z_SILL = 1.20                   # below: the lower body
# trunk positions, m from the front (irregular, 0.8-1.3 m apart)
TRUNKS = np.cumsum([1.5, 0.9, 1.2, 0.8, 1.1, 1.3, 0.9, 1.0, 0.8, 1.2, 0.9, 1.1])
# per side face: (wrap starts at frac, logo frac range)
RIGHT, LEFT = 4, 5
SIDES = {RIGHT: dict(start=0.12, logo=(0.38, 0.47)),       # behind the clear front door
         LEFT: dict(start=0.04, logo=(0.09, 0.17))}        # behind the driver's window
FRONT = 2


def rgb(t, y, x):
    return tuple(int(v) for v in t[y, x])


def is_glass(c):
    return c in (GLASS, (0x4E, 0x4E, 0x4E), (0x44, 0x44, 0x44), (0x39, 0x39, 0x39))


def is_frame(c):
    return max(c) < 0x34 and max(c) - min(c) < 8


def is_white(c):
    return min(c) >= 0xC8 and max(c) - min(c) <= 14


def mpp(d):
    """metres of body per screen pixel along the body in view d"""
    sx, sy = T.STEP[d]
    return 1.5 / max(abs(sx), abs(sy))


def side_columns(face, geo, m):
    """per screen column of one side face: (u metres from the front, rows)"""
    cols = {}
    sel = (geo["face"] == face) & m
    for x in range(128):
        ys = np.where(sel[:, x])[0]
        if len(ys):
            cols[x] = (float(np.median(geo["frac"][ys, x])) * BODY, ys)
    return cols


def wrap_side(o, t, geo, d, face):
    m = ~T.is_bg(t)
    cols = side_columns(face, geo, m)
    if not cols:
        return
    half = mpp(d) / 2
    start = SIDES[face]["start"] * BODY
    lo, hi = (f * BODY for f in SIDES[face]["logo"])
    logo_cols = []
    for x, (u, ys) in cols.items():
        if u < start:
            continue
        trunk = bool(np.min(np.abs(TRUNKS - u)) < half)
        glass_rows = []
        for y in ys:
            c = rgb(t, y, x)
            z = float(geo["z"][y, x])
            if z > Z_CANT:
                if is_frame(c) or is_white(c):
                    o[y, x] = CANT_TRUNK if trunk else CANT
            elif z > Z_SILL:
                if c == GLASS:
                    o[y, x] = GLASS_HI if trunk else GLASS
                    glass_rows.append(y)
                elif is_white(c):
                    o[y, x] = CANT_TRUNK if trunk else CANT
            else:
                if is_white(c) or c == GLASS:     # door glass too; frames and wheels stay
                    top = z > Z_SILL - 0.30
                    if trunk:
                        o[y, x] = GAP
                    elif top:
                        o[y, x] = MOSS_TOP
                    else:
                        o[y, x] = MOSS_HI if (int(u * 4) * 7 + y) % 5 == 0 else MOSS
        if lo <= u < hi and glass_rows:
            logo_cols.append((x, glass_rows))
    if d in ("nw", "se") or not logo_cols:
        return
    # the IKEA box over the lowest three glass rows: blue frame, yellow inside
    logo_cols.sort()
    n = len(logo_cols)
    for i, (x, rows) in enumerate(logo_cols):
        rows = sorted(rows)[-3:]
        for j, y in enumerate(rows):
            inner = 0 < i < n - 1 and j == 1 or n <= 3 and i == n // 2 and j == 1
            o[y, x] = IKEA_YELLOW if inner else IKEA_BLUE


def front_logo(o, t, geo, d):
    """a blue-yellow pair on the front panel, on the vehicle's right of centre"""
    m = ~T.is_bg(t)
    fr = (geo["face"] == FRONT) & m
    if fr.sum() < 12:
        return
    xs = np.where(fr.any(axis=0))[0]
    if len(xs) < 5:
        return
    rx = np.where(((geo["face"] == RIGHT) & m).any(axis=0))[0]
    lx = np.where(((geo["face"] == LEFT) & m).any(axis=0))[0]
    if len(rx):
        right_low = rx.mean() < xs.mean()          # the right side shows on that side
    elif len(lx):
        right_low = not (lx.mean() < xs.mean())
    else:
        right_low = True                           # head-on (se): its right is screen-left
    w = len(xs)
    xa = xs[0] + w // 4 if right_low else xs[-1] - w // 4
    xb = xa + 1 if right_low else xa - 1
    whites = [y for y in np.where(fr[:, xa])[0] if is_white(rgb(t, y, xa))]
    if not whites:
        return
    y = whites[len(whites) // 2]
    o[y, xa] = IKEA_BLUE
    if fr[y, xb] and is_white(rgb(t, y, xb)):
        o[y, xb] = IKEA_YELLOW


def rows():
    src = T.load_rows(SRC)
    out = []
    for tiles in src:
        row = []
        for d, t in zip(DIRS, tiles):
            geo = T.fit(t, d, LS)
            o = t.copy()
            for face in (RIGHT, LEFT):
                wrap_side(o, t, geo, d, face)
            front_logo(o, t, geo, d)
            row.append(o)
        out.append(row)
    return out


def main(argv):
    out = rows()
    path = os.path.join(REPO, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    T.save_sheet(out, path)
    print(OUT)
    if "--preview" in argv:
        d = argv[argv.index("--preview") + 1]
        os.makedirs(d, exist_ok=True)
        T.preview(out, os.path.join(d, "praha-conecto_lf-ikea.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
