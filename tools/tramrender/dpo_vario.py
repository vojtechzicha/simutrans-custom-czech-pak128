"""DP Ostrava Pragoimex Vario sheets (VarioLF, LF2, LF2+, LF3, LF3/2), every livery.

    python tools/tramrender/dpo_vario.py [family ...] [--out DIR] [--zones DIR]

Families: variolf, variolf2, variolf2_plus, variolf3, variolf3_s2. The sheets
go to vehicle-tram/dpo/<family>/sprites/<livery>.png (or to --out DIR as
<family>__<livery>.png); --zones DIR also writes a false-colour zone map per
family. Change this script and regenerate, never edit the PNGs; a second run
reproduces them byte for byte.

Art: TommPa9's blue-yellow drawings of the Pelikan-front Vario bodies, frozen
in src/dpo_vario/ exactly as they were in the repo before this script
(<family>_dpomodrozluta.png). They are patched here (doors, lamps) and every
livery is painted from one zone map of them, so all liveries share one
silhouette (the bodies were audited as correct; the drawing is kept):

* Zone map: per column of every view the window band (frames, glass, doors) is
  found between the paint above and the paint below it; the first paint row
  under it is the sill, the rows below are the lower body (counted from the sill
  and from the body bottom). On the side views that sill row is the white line
  TommPa9 drew on his own turquoise LF / LF2 sheets, to within a few pixels at
  the ends. The cab and rear faces are small per-view masks (P_FRONT,
  P_REARCAB, REAR, CABS) because windscreen, lamp row and display share a
  9-11 px face.
* Shared body: LF3 row 0 is LF2 row 0 (the Pelikan front module), LF3 row 2 is
  LF2 row 1; LF3/2 rows are LF3 except the left side and the rear cab; LF2+ is
  painted on the LF2 drawing (its own sheet was the LF2 turquoise recoloured).

Patches on the drawing (all liveries):
* The rear-corner door is single-leaf on the real cars (VarioLF rear door,
  the rear section of LF2 and LF3): TommPa9 drew it double; it is narrowed.
* LF3/2 (1651-1653) is bidirectional with the doors point-symmetric: on each
  side the section whose cab leads on that side has two doors, the middle one,
  the other end section one near the joint. The left-side views (w, s, sw) of
  the end sections are rebuilt from the right-side views of the opposite end
  section (A left = C right turned round, and the other way), aligned on the
  body; the roof (raised pantograph on A, folded one on C) stays its own.
* Lamps: FFFF53 headlights (2 + 2) on the front cab in se, e and s; FF211D
  tail lights at the rear (kept from TommPa9 on the one-way cars). This build
  has no bidirectional vehicles, so the LF3/2 always runs with row 0 leading:
  its row 2 cab is the trailing cab and shows tail lights, never headlights.
* Cab glass (windscreen, cab side window) in plain colours; passenger glass
  stays on the lit-at-night specials 4D4D4D / 57656F.

Liveries:
* dpomodrozluta: TommPa9's colours, plus the ochre half-disc that hangs in the
  trough of the white wave of every long section (LF2, LF3, LF3/2; photos of
  1401, 1601, 1652) and the small ochre swoosh in the blue wave at the rear of
  the single LF's left side (1352).
* dpotyrkysova (dpo_palette.py): turquoise body, light roof 44C1E4, a thin white
  line on the sill that steps with the sills and crosses the front under the
  windscreen, black window frames, doors as dark slots, black lamp mask with
  2 + 2 headlights; yellow pantograph as on the photos.
* stribrna (LF2+ 1411): silver-champagne upper body and roof, a wide copper
  band under the windows, grey-silver skirt, champagne front with a dark lamp
  panel, yellow pantograph.

Lengths: every section is drawn as long as its family.yaml length (LF2 / LF3
sections 8 + 5 + 8). The single VarioLF is drawn 10.8 carunits long, so its
length is 11: two coupled cars meet (check with tools/consist_preview.py on
the same row twice).
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dpo_palette as pal  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(HERE, "src", "dpo_vario")
DPO = os.path.join(ROOT, "vehicle-tram", "dpo")
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
W, NW, N, NE, E, SE, S, SW = range(8)

# ------------------------------------------------------------------ base palette
BG = 0xE7FFFF
ROOF = 0x295A84
BLUE = 0x4284C5
WHITE = 0xE6E6E6
BLUES = {BLUE, 0x528CC5, 0x639CCE, 0x6B9CCE, 0x84ADD6, 0x4A84C5, 0xADC5DE}
WHITES = {WHITE, 0xD6D6D6, 0xF7F7F7, 0xEFEFEF}
PAINT = BLUES | WHITES
GLASS, GLASS_HI = 0x4D4D4D, 0x57656F       # specials: lit at night when loaded
DOOR = 0xFFCE08
FRAME = 0x292929                          # window frames / pillars (side views)
FRAME_D = 0x313131                        # the same in the diagonal views
BLACK, BLACK2 = 0x000000, 0x101010
BAND = {FRAME, FRAME_D, GLASS, GLASS_HI, BLACK, BLACK2, DOOR}
PANTO = {0xC5C500, 0xCECE00, 0xD6D600, 0xE6E600, 0xEFEF00}
HEAD, TAIL = 0xFFFF53, 0xFF211D           # specials: always lit
OCHRE = 0xE8A317                          # blue-yellow half-discs / swoosh (photos ~E9A41A)

# ------------------------------------------------------------------ zones
# keep = drawn colour in every livery (frames, bellows, wheels, displays ...),
# upper = paint above the window band, sill / lower = the sill row and the
# paint below it, cab = cab glass, frontline / mask / lamp / frontbody = the cab
# face under the windscreen, rearbody = paint of a one-way rear end.
(Z_BG, Z_KEEP, Z_ROOF, Z_UP, Z_SILL, Z_LO, Z_DOOR, Z_GLASS, Z_PANTO,
 Z_CAB, Z_FLINE, Z_MASK, Z_LAMP, Z_FBODY, Z_TAIL, Z_RBODY) = range(16)
# false colours of the --zones maps, in the order above
ZDEBUG = [0xE7FFFF, 0x808080, 0x2040A0, 0x40C0FF, 0xFF00FF, 0x00C060, 0xFFC000, 0x303030,
          0xFFFF00, 0x8000FF, 0xFFFFFF, 0x000000, 0xFF8000, 0x00FFC0, 0xFF0000, 0x40A080]


# ------------------------------------------------------------------ io
def load(name):
    a = np.array(Image.open(os.path.join(SRC, name)).convert("RGB")).astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def to_rgb(h):
    return np.stack([(h >> 16) & 255, (h >> 8) & 255, h & 255], axis=-1).astype(np.uint8)


def save(h, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(to_rgb(h)).save(path)


def tile(sheet, r, c):
    return sheet[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128]


def isin(t, s):
    return np.isin(t, np.array(sorted(s), dtype=np.int64))


def art(t, x0, y0, rows, legend):
    """Overlay ASCII art on tile t: '.' keeps the pixel."""
    for j, line in enumerate(rows):
        for i, ch in enumerate(line):
            if ch != ".":
                t[y0 + j, x0 + i] = legend[ch]


BASE_LEGEND = {"y": DOOR, "g": GLASS, "G": GLASS_HI, "k": FRAME, "d": FRAME_D, "K": BLACK2,
               "#": BLACK, "b": BLUE, "w": WHITE, "R": ROOF}

BASES = {"lf": "variolf_dpomodrozluta.png", "lf2": "variolf2_dpomodrozluta.png",
         "lf3": "variolf3_dpomodrozluta.png", "lf32": "variolf3_s2_dpomodrozluta.png"}
FAMILIES = {
    "variolf": ("lf", ["dpomodrozluta", "dpotyrkysova"]),
    "variolf2": ("lf2", ["dpomodrozluta", "dpotyrkysova"]),
    "variolf2_plus": ("lf2", ["stribrna"]),
    "variolf3": ("lf3", ["dpomodrozluta", "dpotyrkysova"]),
    "variolf3_s2": ("lf32", ["dpomodrozluta", "dpotyrkysova"]),
}
# Row roles: front cab ("P" = Pelikan module, "LF" = the single car's), rear
# end, and which trough of the white wave gets the blue-yellow half-disc:
# (right side, left side) as a fraction of the section from its front end.
# Photos: on the front section it hangs between the doors on the right side and
# near the joint on the left side, on the others in the middle; the LF3/2 end
# sections are point-symmetric (C right = A left, C left = A right).
ROWS = {
    "lf": [dict(front="LF", rear="oneway", disc=None)],
    "lf2": [dict(front="P", disc=(0.5, 0.8)), dict(rear="oneway", disc=(0.45, 0.45))],
    "lf3": [dict(front="P", disc=(0.5, 0.8)), dict(disc=(0.5, 0.5)),
            dict(rear="oneway", disc=(0.45, 0.45))],
    "lf32": [dict(front="P", disc=(0.5, 0.8)), dict(disc=(0.5, 0.5)),
             dict(rear="cab", disc=(0.2, 0.5))],
}


# ------------------------------------------------------------------ geometry patches
# Rear-corner door made single-leaf. ne: a 6-column block from the door's rear
# edge (door 3 px, then the window bay widened over the freed columns). n / e:
# the door is 3 px wide there; its front column becomes the pillar in front of it.
SINGLE_NE = ["yyykgg",
             "ygykGG",
             "ygykgg",
             "ygykgg",
             "ygykgg",
             "ygywww",
             "ygywww",
             "ygybbb",
             "yyybbb",
             "yyybbb"]
# (base, row): {ne: (x0, y0) of the block, n / e: (front door column, rows)}
SINGLE_DOORS = {
    ("lf", 0): {NE: (23, 86), N: (49, range(95, 104)), E: (32, range(71, 82))},
    ("lf2", 1): {NE: (42, 88), N: (62, range(91, 102)), E: (46, range(80, 91))},
    ("lf3", 2): {NE: (42, 88), N: (62, range(91, 102)), E: (46, range(80, 91))},
}


def single_leaf_doors(sheet, base):
    for (b, r), spec in SINGLE_DOORS.items():
        if b != base:
            continue
        for v, (x, ys) in spec.items():
            t = tile(sheet, r, v)
            if v == NE:
                art(t, x, ys, SINGLE_NE, BASE_LEGEND)
            else:
                for y in ys:              # the front is to the right in n and e
                    t[y, x] = t[y, x + 1]


# LF3/2 left side: (target row, view) <- (source row, view, dx, dy). The A
# section's (row 0) left side is the C section's (row 2) right side turned
# round and the other way; dx, dy align the two bodies (window bands to the px).
LF32_LEFT = [((0, W), (2, E, 0, -1)), ((0, S), (2, N, -1, 0)), ((0, SW), (2, NE, 1, 1)),
             ((2, W), (0, E, 0, 0)), ((2, S), (0, N, 0, -1)), ((2, SW), (0, NE, 0, 0))]


def lf32_left_side(sheet):
    """Everything below the roof (and the pantograph) comes from the source view."""
    src = sheet.copy()
    roofish = {ROOF} | PANTO
    for (rt, vt), (rs, vs, dx, dy) in LF32_LEFT:
        t, s = tile(sheet, rt, vt), tile(src, rs, vs)
        t0 = t.copy()
        for x in range(128):
            xs = x - dx
            if not 0 <= xs < 128:
                continue
            yt = np.nonzero(isin(t0[:, x], roofish))[0]
            ys = np.nonzero(isin(s[:, xs], roofish))[0]
            if len(yt) == 0 or len(ys) == 0:
                continue
            for y in range(max(yt.max(), ys.max() + dy) + 1, 128):
                if 0 <= y - dy < 128:
                    t[y, x] = s[y - dy, xs]


def patched(base):
    sh = load(BASES[base])
    single_leaf_doors(sh, base)
    if base == "lf32":
        lf32_left_side(sh)
    return sh


# ------------------------------------------------------------------ face masks
# Cab faces, per view an ASCII mask laid over the drawing: C = glass becomes cab
# glass (the yellow route display inside stays), L = line under the windscreen,
# M = lamp mask, H = headlight, F = front paint, K = keep as drawn, . = as
# classified. The windscreen bottom frame becomes the line, TommPa9's lamp row
# the mask, his white line under it front paint (DPO turquoise photos 1318, 1320).
P_FRONT = {
    SE: (58, 87, ["KFFFFFFFFFK",
                  "KKKFFFFFKKK",
                  "KKKKKKKKKKK",
                  "KCCCCCCCCCK",
                  "KCCCCCCCCCK",
                  "KCCCCCCCCCK",
                  "KCCCCCCCCCK",
                  "KCCCCCCCCCK",
                  "LCCCCCCCCCL",
                  "FLLLLLLLLLF",
                  "FMHHMMMHHMF",
                  "FFFFFFFFFFF",
                  "FFFFKKKFFFF",
                  ".FFFFKFFFF."]),
    E: (69, 89, ["CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCLLLLL",
                 "...LHHMHM",
                 "...FFFKKF",
                 ".....KFF."]),
    S: (50, 89, ["CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "CCCCCCCCC",
                 "LLLLL..C.",
                 "MHMHHLL..",
                 "FKKFF....",
                 ".KKKF...."]),
}
# The single LF's cab sits 3 px further along x and 4 px higher in e and s.
LF_SHIFT = {SE: (0, 0), E: (-3, -4), S: (3, -4)}
# The same cab at the tail of the LF3/2 (row 2), seen in nw / w / n: TommPa9
# drew it as the front cab moved (nw: 7 px up; w: in place; n: 1 px right).
P_REARCAB = {
    NW: (58, 80, [s.replace("H", "M") for s in P_FRONT[SE][2]]),
    W: (69, 89, [s.replace("H", "M") for s in P_FRONT[E][2]]),
    N: (51, 89, [s.replace("H", "M") for s in P_FRONT[S][2]]),
}
P_REARCAB_TAILS = {NW: [(60, 90), (66, 90)], W: [(73, 98), (76, 98)], N: [(52, 98), (55, 98)]}

# Rear ends of the one-way cars, box (x0, y0, x1, y1): no line under the rear
# window (as TommPa9 drew his turquoise cars), route number kept.
REAR = {
    ("lf", 0): {NW: (56, 92, 72, 108), W: (85, 88, 96, 108), N: (30, 88, 43, 108)},
    ("lf2", 1): {NW: (56, 80, 72, 96), W: (72, 80, 84, 104), N: (44, 80, 56, 104)},
    ("lf3", 2): {NW: (56, 80, 72, 96), W: (72, 80, 84, 104), N: (44, 80, 56, 104)},
}
# Cab end of every row with a cab, per view: in front of the front door on the
# right side, of the first pillar behind the cab side window on the left. Its
# glass (windscreen, cab side window) becomes cab glass, and on the LF2+ the
# copper band stops there (photos of 1411: the cab module is champagne all
# round). LF3/2 left views were rebuilt from the other end section's right
# views, so they take those limits (shifted by the LF32_LEFT offsets).
P_CAB_RIGHT = {NE: (">=", 78, "x"), E: (">=", 68, "x"), N: (">=", 84, "x"), SE: (">=", 84, "y")}
CABS = {
    ("lf", 0): {NE: (">=", 77, "x"), E: (">=", 65, "x"), N: (">=", 82, "x"), SE: (">=", 84, "y"),
                W: ("<=", 45, "x"), SW: ("<=", 44, "x"), S: ("<=", 62, "x")},
    ("lf2", 0): {**P_CAB_RIGHT, W: ("<=", 43, "x"), SW: ("<=", 40, "x"), S: ("<=", 59, "x")},
    ("lf3", 0): {**P_CAB_RIGHT, W: ("<=", 43, "x"), SW: ("<=", 40, "x"), S: ("<=", 59, "x")},
    ("lf32", 0): {**P_CAB_RIGHT, W: ("<=", 42, "x"), SW: ("<=", 41, "x"), S: ("<=", 58, "x")},
    ("lf32", 2): {NW: (">=", 77, "y"), W: (">=", 68, "x"), S: (">=", 84, "x"), SW: (">=", 78, "x"),
                  NE: ("<=", 40, "x"), E: ("<=", 42, "x"), N: ("<=", 59, "x")},
}


# ------------------------------------------------------------------ zone map
def column_scan(t, Z, lv, dep):
    """Per column: the window band between paint above and paint below it.
    The first paint row under it is the sill (not under a door), the paint
    rows below it the lower body: lv = rows below the sill, dep = rows above
    the body bottom."""
    for x in range(128):
        col = t[:, x]
        y = 0
        while y < 128:
            if col[y] not in BAND:
                y += 1
                continue
            y0 = y
            while y < 128 and col[y] in BAND:
                y += 1
            if y >= 128 or y0 == 0 or col[y0 - 1] not in PAINT or col[y] not in PAINT:
                continue
            door_end = col[y - 1] == DOOR
            y1 = y
            while y < 128 and col[y] in PAINT:
                y += 1
            for yy in range(y1, y):
                if Z[yy, x] == Z_UP:
                    Z[yy, x] = Z_SILL if (yy == y1 and not door_end) else Z_LO
                    lv[yy, x] = yy - y1
                    dep[yy, x] = y - 1 - yy


def apply_mask(t, Z, x0, y0, rows):
    for j, line in enumerate(rows):
        for i, ch in enumerate(line):
            y, x = y0 + j, x0 + i
            px = t[y, x]
            if ch == "." or px == BG:
                continue
            if ch == "C":
                if px in (GLASS, GLASS_HI):
                    Z[y, x] = Z_CAB
                elif px == DOOR:
                    Z[y, x] = Z_KEEP
            elif ch == "F":
                Z[y, x] = Z_FBODY if px in PAINT else Z_KEEP
            else:
                Z[y, x] = {"L": Z_FLINE, "M": Z_MASK, "H": Z_LAMP, "K": Z_KEEP}[ch]


def classify(t, base, row, view):
    """Zone of every pixel of tile t of the patched drawing, plus the lower
    body levels (rows below the sill, rows above the bottom)."""
    Z = np.full(t.shape, Z_KEEP, np.int8)
    lv = np.full(t.shape, -1, np.int16)
    dep = np.full(t.shape, -1, np.int16)
    Z[t == BG] = Z_BG
    Z[t == ROOF] = Z_ROOF
    Z[isin(t, PAINT)] = Z_UP
    Z[isin(t, {GLASS, GLASS_HI})] = Z_GLASS
    Z[t == DOOR] = Z_DOOR
    Z[isin(t, PANTO)] = Z_PANTO
    Z[t == TAIL] = Z_TAIL
    role = ROWS[base][row]
    rear = REAR.get((base, row), {}).get(view)
    if rear:
        x0, y0, x1, y1 = rear
        sub = Z[y0:y1, x0:x1]
        sub[sub == Z_UP] = Z_RBODY
        sub[sub == Z_DOOR] = Z_KEEP
    column_scan(t, Z, lv, dep)
    Z[cab_end(base, row, view) & (Z == Z_GLASS)] = Z_CAB
    if role.get("front") and view in P_FRONT:
        x0, y0, rows = P_FRONT[view]
        dx, dy = LF_SHIFT[view] if role["front"] == "LF" else (0, 0)
        apply_mask(t, Z, x0 + dx, y0 + dy, rows)
    if role.get("rear") == "cab" and view in P_REARCAB:
        apply_mask(t, Z, *P_REARCAB[view])
        for x, y in P_REARCAB_TAILS[view]:
            Z[y, x] = Z_TAIL
    return Z, lv, dep


def cab_end(base, row, view):
    """Boolean mask of the cab end of this row in this view (see CABS)."""
    m = np.zeros((128, 128), bool)
    spec = CABS.get((base, row), {}).get(view)
    if spec is None:
        return m
    op, v, axis = spec
    idx = np.arange(128)
    sel = idx >= v if op == ">=" else idx <= v
    if axis == "x":
        m[:, sel] = True
    else:
        m[sel, :] = True
    return m


# ------------------------------------------------------------------ painting
def paint_turquoise(t, Z, lv, dep, ctx):
    o = t.copy()
    for z, c in ((Z_ROOF, pal.ROOF), (Z_UP, pal.BODY), (Z_LO, pal.BODY), (Z_FBODY, pal.BODY),
                 (Z_RBODY, pal.BODY), (Z_SILL, pal.WHITE), (Z_FLINE, pal.WHITE),
                 (Z_DOOR, TQ_DOOR), (Z_MASK, pal.MASK), (Z_LAMP, HEAD), (Z_TAIL, TAIL)):
        o[Z == z] = c
    cab_glass(o, t, Z)
    return o


def paint_silver(t, Z, lv, dep, ctx):
    o = t.copy()
    cab = cab_end(ctx["base"], ctx["row"], ctx["view"])
    lower = (Z == Z_LO) | (Z == Z_SILL)
    skirt = lower & (dep <= 1) & ~cab
    copper = lower & (dep > 1) & ~cab
    for z, c in ((Z_ROOF, LF2P_ROOF), (Z_UP, LF2P_BODY), (Z_LO, LF2P_BODY), (Z_SILL, LF2P_BODY),
                 (Z_FBODY, LF2P_BODY), (Z_RBODY, LF2P_BODY), (Z_FLINE, LF2P_BODY),
                 (Z_DOOR, LF2P_DOOR), (Z_MASK, LF2P_PANEL), (Z_LAMP, HEAD), (Z_TAIL, TAIL)):
        o[Z == z] = c
    o[copper] = LF2P_COPPER
    o[skirt] = LF2P_SKIRT
    cab_glass(o, t, Z)
    return o


def paint_blueyellow(t, Z, lv, dep, ctx):
    o = t.copy()
    o[Z == Z_LAMP] = HEAD
    o[Z == Z_TAIL] = TAIL
    cab_glass(o, t, Z)
    if ctx["disc"] is not None and ctx["view"] in (N, NE, E, W, S, SW):
        right = ctx["view"] in (N, NE, E)
        half_disc(o, t, Z, ctx["view"], ctx["disc"][0 if right else 1])
    if ctx["base"] == "lf" and ctx["view"] in SWOOSH:
        for x, y in SWOOSH[ctx["view"]]:
            if t[y, x] in BLUES:
                o[y, x] = OCHRE
    return o


def half_disc(o, t, Z, view, target):
    """Ochre half-disc hanging from the sill in a trough of the white wave (the
    columns whose lower body is white from the sill to the bottom). Of the
    troughs of the section, the one nearest `target` (fraction of the section
    length from its front end in the direction of travel) gets it: on the photos
    the disc sits in the rear half of the front section (both sides), in the
    middle of the middle section and of the one-way rear section, and on the
    LF3/2 the end sections are point-symmetric."""
    low = (Z == Z_LO) | (Z == Z_SILL)
    cols = np.nonzero(low.any(axis=0))[0]
    if len(cols) == 0:
        return
    xmin, xmax = cols.min(), cols.max()
    runs, cur = [], None
    for x in range(128):
        ys = np.nonzero(low[:, x])[0]
        ok = len(ys) >= 3 and all(t[y, x] in WHITES for y in ys)
        if ok and cur is not None and cur[1] == x - 1:
            cur[1] = x
        elif ok:
            cur = [x, x]
            runs.append(cur)
    runs = [r for r in runs if r[1] - r[0] >= 1]
    if not runs:
        return

    def frac(r):
        xc = (r[0] + r[1]) / 2.0
        f = (xc - xmin) / max(1, xmax - xmin)
        return 1 - f if view in (N, NE, E) else f   # front to the right in n, ne, e
    x0, x1 = min(runs, key=lambda r: (abs(frac(r) - target), r[0]))
    n = x1 - x0 + 1
    if n >= 5:                      # keep a white rim on both sides
        x0, x1 = x0 + 1, x1 - 1
        n -= 2
    c, hw = (x0 + x1) / 2.0, n / 2.0
    for x in range(x0, x1 + 1):
        ys = np.nonzero(low[:, x])[0]
        top, h = ys.min(), len(ys)
        dmax = max(1, min(3, h - 2))
        u = (x - c) / hw
        d = max(1, int(round(dmax * np.sqrt(max(0.0, 1 - u * u)))))
        for y in range(top, top + d):
            o[y, x] = OCHRE


# Small ochre swoosh in the blue wave at the rear of the single LF's left side
# (photo of 1352 from the left), rising towards the rear.
SWOOSH = {
    SW: [(84, 95), (85, 95), (86, 94), (87, 94), (88, 94), (89, 94), (90, 94),
         (91, 93), (92, 93), (93, 93), (94, 93)],
    S: [(87, 84), (88, 83), (89, 83), (90, 82)],
    W: [(70, 100), (71, 100), (72, 100), (73, 101), (74, 101), (75, 101), (76, 102),
        (77, 102), (78, 102), (79, 103)],
}


def cab_glass(o, t, Z):
    o[(Z == Z_CAB) & (t == GLASS)] = pal.CAB_GLASS
    o[(Z == Z_CAB) & (t == GLASS_HI)] = pal.CAB_GLASS_TOP


TQ_DOOR = 0x3A3F44                        # door leaves: dark slots
LF2P_BODY = 0xB1A187                      # silver-champagne (photos of 1411)
LF2P_ROOF = 0xBDAE95
LF2P_COPPER = 0x9C5824
LF2P_SKIRT = 0xA8A9A4
LF2P_DOOR = 0x4A453C
LF2P_PANEL = 0x3A3A3C
PAINTERS = {"dpomodrozluta": paint_blueyellow, "dpotyrkysova": paint_turquoise,
            "stribrna": paint_silver}


# ------------------------------------------------------------------ build
def build(family):
    base, liveries = FAMILIES[family]
    sh = patched(base)
    out = {lv: sh.copy() for lv in liveries}
    zones = np.zeros_like(sh)
    for r in range(sh.shape[0] // 128):
        role = ROWS[base][r]
        for v in range(8):
            t = tile(sh, r, v)
            Z, lvl, dep = classify(t, base, r, v)
            tile(zones, r, v)[:] = np.array(ZDEBUG, dtype=np.int64)[Z]
            ctx = dict(base=base, row=r, view=v, front=role.get("front"), rear=role.get("rear"),
                       disc=role.get("disc"))
            for lv in liveries:
                tile(out[lv], r, v)[:] = PAINTERS[lv](t, Z, lvl, dep, ctx)
    return out, zones


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("families", nargs="*", default=list(FAMILIES))
    ap.add_argument("--zones", help="write false-colour zone maps here")
    ap.add_argument("--out", help="write the sheets here instead of the repo")
    a = ap.parse_args()
    for fam in a.families:
        sheets, zones = build(fam)
        for lv, sh in sheets.items():
            path = (os.path.join(a.out, f"{fam}__{lv}.png") if a.out
                    else os.path.join(DPO, fam, "sprites", f"{lv}.png"))
            save(sh, path)
            print("wrote", os.path.relpath(path, ROOT) if not a.out else path)
        if a.zones:
            save(zones, os.path.join(a.zones, f"zones_{fam}.png"))


if __name__ == "__main__":
    main()
