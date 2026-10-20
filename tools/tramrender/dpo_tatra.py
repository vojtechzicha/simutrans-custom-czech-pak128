"""DP Ostrava Tatra trams: TommPa9's / Lubak91's sheets patched to the cars as they run.

    python tools/tramrender/dpo_tatra.py [family ...] [--preview DIR]

Families: kt8d5r_n1, t3, t3sucs, t6a5 (default: all). The upstream sheets are
frozen in tools/tramrender/src/dpo/ and every shipped sheet is generated from
them here; change this script and regenerate, never edit the PNGs.
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tramkit as tk  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(HERE, "src", "dpo")
VEH = os.path.join(ROOT, "vehicle-tram", "dpo")

H = tk.hexrgb
BG = tk.BG
DIRS = tk.DIRS

# ------------------------------------------------------------------ colours
LIT = H("4D4D4D")            # special: passenger glass, lit at night when loaded
LIT_HI = H("57656F")         # special: lighter passenger glass
PLAIN = H("4D4D4E")          # the same glass one step off the special table
PLAIN_HI = H("57656E")
HEAD = H("FFFF53")           # special: headlight, always lit
TAIL = H("FF211D")           # special: tail light, always lit
INDICATOR = H("FF8442")      # orange lamp (plain)
REFLECTOR = H("C8201C")      # red reflector on the bumper (plain red, never lit)

# TommPa9's DPO blue-yellow palette
ROOF = H("295A84")
BLUE = H("4284C5")
WHITE = H("E6E6E6")
YELLOW = H("FFCE08")
FRAME = H("424242")
BELLOWS = H("313131")
BLACK = H("000000")
SCREEN = H("6B6B6C")         # plain windscreen grey of the KT8 front
LAMP_RIM = H("E6E6C5")
AC_TOP = H("F2F2F2")         # white roof A/C pod
AC_SIDE = H("C4C6C8")
AC_SIDE_DARK = H("A4A6A8")

# pantograph: the yellow single-arm of TommPa9's T6A5 sheet, the diamond of the KT8
PANTO_YELLOW = [H(h) for h in ("C5C500", "CECE00", "D6D600", "E6E600", "EFEF00")]
PIVOT = H("848484")


# ------------------------------------------------------------------ helpers
def load_src(name):
    return tk.load(os.path.join(SRC, name)).copy()


def cmask(t, cols):
    m = np.zeros(t.shape[:2], bool)
    for c in cols:
        m |= np.all(t == np.array(c), axis=2)
    return m


def boxmask(shape, box):
    """box = (x0, y0, x1, y1) inclusive."""
    m = np.zeros(shape[:2], bool)
    x0, y0, x1, y1 = box
    m[y0:y1 + 1, x0:x1 + 1] = True
    return m


def recolor(t, mapping, boxes=None):
    """Exact colour swaps, optionally only inside the given boxes."""
    region = np.ones(t.shape[:2], bool)
    if boxes is not None:
        region = np.zeros(t.shape[:2], bool)
        for b in boxes:
            region |= boxmask(t.shape, b)
    src = t.copy()
    for a, b in mapping.items():
        m = np.all(src == np.array(a), axis=2) & region
        t[m] = b


def plain_glass(t, boxes):
    """Cab glass: the lit specials one step off, identical by day, never lit."""
    recolor(t, {LIT: PLAIN, LIT_HI: PLAIN_HI}, boxes)


def put(t, pts, col):
    for x, y in pts:
        t[y, x] = col


def art(t, x0, y0, text, legend):
    tk.patch(t, text, legend, x0, y0)


def panto_mask(t, box, extra=(PIVOT, BLACK)):
    m = cmask(t, PANTO_YELLOW) & boxmask(t.shape, box)
    m |= cmask(t, extra) & boxmask(t.shape, box)
    return m


def erase(t, m, fill):
    """Remove the pixels in m: those on the body (below the local top edge of the
    sprite, interpolated where m covers the edge) become `fill`, the rest
    background."""
    body = ~np.all(t == np.array(BG), axis=2) & ~m
    W = t.shape[1]
    top = np.full(W, 10 ** 6)
    for x in range(W):
        ys = np.nonzero(body[:, x])[0]
        if len(ys):
            top[x] = ys.min()
    touched = sorted(set(np.nonzero(m)[1].tolist()))
    clean = [x for x in range(W) if x not in touched and top[x] < 10 ** 6]
    est = top.astype(float)
    for x in touched:
        covered = top[x] >= 10 ** 6 or (top[x] > 0 and m[top[x] - 1, x])
        if not covered:
            continue
        left = [c for c in clean if c < x and abs(c - x) <= 6]
        right = [c for c in clean if c > x and abs(c - x) <= 6]
        if left and right:
            xl, xr = left[-1], right[0]
            est[x] = top[xl] + (top[xr] - top[xl]) * (x - xl) / (xr - xl)
        elif left:
            est[x] = top[left[-1]]
        elif right:
            est[x] = top[right[0]]
    for y, x in zip(*np.nonzero(m)):
        t[y, x] = fill if y >= round(est[x]) else BG


def transplant(dst, src, m, dx, dy):
    for y, x in zip(*np.nonzero(m)):
        X, Y = x + dx, y + dy
        if 0 <= X < 128 and 0 <= Y < 128:
            dst[Y, X] = src[y, x]


def _inside(px, py, poly):
    """Point in convex polygon (any winding)."""
    sgn = 0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cr = (x1 - x0) * (py - y0) - (y1 - y0) * (px - x0)
        if abs(cr) < 1e-9:
            continue
        s = 1 if cr > 0 else -1
        if sgn == 0:
            sgn = s
        elif s != sgn:
            return False
    return True


def roof_pod(t, d, cx, cy, length=1.0, width=1.0, h=2, top=None, sides=None, protect=None):
    """A box on the roof: footprint centred on screen point (cx, cy) of the roof
    surface, `length` x `width` carunits, `h` px high; the top and the side faces
    that face the viewer are filled at pixel centres. Pantograph pixels stay."""
    top = top or AC_TOP
    sides = sides or (AC_SIDE, AC_SIDE_DARK)
    A = np.array(tk.PER_CU[d], float) * length / 2
    B = np.array(tk.PER_CU[DIRS[(DIRS.index(d) + 2) % 8]], float) * width / 2
    c = np.array([cx, cy], float)
    foot = [c + A + B, c + A - B, c - A - B, c - A + B]
    up = np.array([0.0, -h])
    faces = []
    for i in range(4):
        p0, p1 = foot[i], foot[(i + 1) % 4]
        mid = (p0 + p1) / 2 - c
        if mid[1] > 0.01:                       # faces the viewer (screen down)
            shade = sides[0] if mid[0] <= 0.01 else sides[1]
            faces.append(([p0, p1, p1 + up, p0 + up], shade))
    roof = [p + up for p in foot]
    src = t.copy()
    for y in range(max(0, int(cy) - 12), min(128, int(cy) + 12)):
        for x in range(max(0, int(cx) - 12), min(128, int(cx) + 12)):
            if protect is not None and protect(src[y, x]):
                continue
            px, py = x + 0.5, y + 0.5
            if _inside(px, py, roof):
                t[y, x] = top
            else:
                for poly, shade in faces:
                    if _inside(px, py, poly):
                        t[y, x] = shade
                        break


# ------------------------------------------------------------------ the single-arm pantograph
T6_PANTO_BOX = {0: (54, 69, 67, 81), 1: (57, 71, 70, 78), 2: (61, 69, 74, 81), 3: (52, 70, 63, 83),
                4: (50, 68, 65, 80), 5: (57, 73, 69, 84), 6: (62, 68, 77, 80), 7: (57, 70, 68, 83)}


def single_arm(dst, col, dx, dy):
    """Paste the raised yellow single-arm pantograph of the T6A5 front car (row 0
    of TommPa9's sheet) into tile dst of view col, moved by (dx, dy)."""
    t6 = tk.tile(load_src("t6a5_dpomodrozluta.png"), 0, col)
    m = panto_mask(t6, T6_PANTO_BOX[col])
    transplant(dst, t6, m, dx, dy)


# ------------------------------------------------------------------ KT8D5R.N1
KT8_DIAMOND_BOX = {0: (50, 67, 61, 79), 1: (58, 64, 68, 71), 2: (67, 68, 79, 80), 3: (62, 71, 73, 83),
                   4: (56, 74, 68, 85), 5: (58, 82, 68, 86), 6: (57, 74, 69, 85), 7: (47, 71, 58, 83)}
# where the T6A5 pantograph goes: the base on the diamond's base, about 1/3 back
KT8_PANTO_SHIFT = {0: (-4, -2), 1: (0, -5), 2: (4, -2), 3: (10, 0),
                   4: (8, 5), 5: (0, 2), 6: (-8, 5), 7: (-10, 0)}


# A/C pod: about 0.8 carunit behind the front of the roof, on the centre line
# (the pantograph base moved 1.8 carunits forward; nw/se by eye, foreshortened)
KT8_POD = {0: (48.8, 75.4), 1: (63.0, 68.0), 2: (78.2, 75.4), 3: (76.5, 82.5),
           4: (71.9, 87.9), 5: (63.0, 87.0), 6: (55.1, 87.9), 7: (43.5, 82.5)}

# cab glass of the front section (driver): windscreen and cab side window per view
KT8_CAB = {0: [(41, 74, 48, 86)], 2: [(78, 74, 87, 86)], 3: [(77, 80, 83, 93)], 4: [(68, 86, 78, 97)],
           6: [(48, 86, 58, 97)], 7: [(37, 80, 43, 93)]}

KT8_LEGEND = {"R": ROOF, "b": BLUE, "w": WHITE, "y": YELLOW, "g": LIT, "h": LIT_HI, "d": FRAME,
              "o": INDICATOR, "T": TAIL, "r": REFLECTOR, "k": BLACK}

# rear end of the rear section (row 2), seen straight on in nw: TommPa9 drew it as a
# copy of the front cab. The real Ostrava cars are one-way: a passenger rear window
# (LED display at its top), blue band, white panel with orange-over-red lamp
# clusters at the outer corners, yellow bumper with red reflectors, no headlights.
KT8_REAR_NW = """
gbRRRRRRRbg
ggbbbbbbbgg
ggbdddddbgg
ggbhgggh.gg
bgbgggggbgb
wbbgggggbbw
wwbgggggbww
owwbbbbbwwo
Twwwwwwwwwt
 yryyyyyry
"""


def kt8_rear_end(sh):
    t = tk.tile(sh, 2, 1)                                   # nw: the face
    art(t, 58, 83, KT8_REAR_NW.replace("t", "T").replace("h.", "hb"), KT8_LEGEND)
    t = tk.tile(sh, 2, 0)                                   # w: face at the lower right
    put(t, [(74, 94), (74, 95)], LIT)                        # no handrail in the window
    put(t, [(76, 96), (72, 98)], INDICATOR)
    put(t, [(76, 97), (72, 99)], TAIL)
    put(t, [(75, 98), (71, 100)], REFLECTOR)
    t = tk.tile(sh, 2, 2)                                   # n: face at the lower left
    put(t, [(53, 89), (53, 90), (54, 90), (55, 90), (56, 91)], LIT)
    put(t, [(53, 94), (53, 95)], LIT)
    put(t, [(51, 96), (55, 98)], INDICATOR)
    put(t, [(51, 97), (55, 99)], TAIL)
    put(t, [(52, 98), (56, 100)], REFLECTOR)


def kt8_blue():
    sh = load_src("kt8d5r_n1_dpomodrozluta.png")
    for col in range(8):
        t = tk.tile(sh, 0, col)
        m = panto_mask(t, KT8_DIAMOND_BOX[col])
        erase(t, m, ROOF)
        single_arm(t, col, *KT8_PANTO_SHIFT[col])
        plain_glass(t, KT8_CAB.get(col, []))
    for col, (cx, cy) in KT8_POD.items():                   # white A/C pod over the cab
        roof_pod(tk.tile(sh, 0, col), DIRS[col], cx, cy, protect=tk.is_panto if col in (0, 1, 2) else None)
    recolor(tk.tile(sh, 0, 5), {H("FFFF52"): HEAD})        # front headlights that never lit
    kt8_rear_end(sh)
    return sh


# ------------------------------------------------------------------ KT8D5R.N1 turquoise
# Zone map of the patched blue-yellow sheet, repainted in the DPO turquoise scheme
# of dpo_palette.py (photos of 1503, 1504, 1505): turquoise body down to the skirt,
# sunlit-tint roof, black window band (glass stays glass), one thin white line right
# under the band that follows the middle section's V-dip and runs under the
# windscreen across the front, black cab mask, black doors with dark glass.
import dpo_palette as pal  # noqa: E402

TQ_BODY = H("%06X" % pal.BODY)
TQ_ROOF = H("%06X" % pal.ROOF)
TQ_WHITE = H("%06X" % pal.WHITE)
TQ_MASK = H("%06X" % pal.MASK)
TQ_PILLAR = H("%06X" % pal.PILLAR)

GLASS = [LIT, LIT_HI, PLAIN, PLAIN_HI, SCREEN]
KEEP = [BLACK, BELLOWS, FRAME, HEAD, TAIL, INDICATOR, REFLECTOR, LAMP_RIM, PIVOT,
        AC_TOP, AC_SIDE, AC_SIDE_DARK] + PANTO_YELLOW
PAINT = [BLUE, WHITE, YELLOW]            # body paint of the blue-yellow scheme

# doors (right side: n, ne, e): column ranges; rows from the door's yellow
KT8_DOORS = {(0, 2): [(65, 68), (80, 82)], (0, 3): [(51, 56), (72, 76)], (0, 4): [(49, 52), (64, 66)],
             (1, 2): [(76, 79)], (1, 3): [(66, 71)], (1, 4): [(60, 63)],
             (2, 2): [(61, 63), (75, 78)], (2, 3): [(44, 48), (64, 69)], (2, 4): [(45, 47), (59, 62)]}
# columns through the front face (row 0) / rear face (row 2) in the end and diagonal views
KT8_FACES = {(0, 5): (58, 68), (0, 4): (70, 78), (0, 6): (49, 57),
             (2, 1): (58, 68), (2, 0): (70, 78), (2, 2): (49, 57)}


def _band(t, skip):
    """Per column the rows of the window band (top, bottom of the glass), the
    glass-free columns (pillars) interpolated from their neighbours."""
    g = cmask(t, GLASS)
    g[:, list(skip)] = False
    top, bot = {}, {}
    for x in range(128):
        ys = np.nonzero(g[:, x])[0]
        if len(ys):
            top[x], bot[x] = ys.min(), ys.max()
    have = sorted(top)
    out = {}
    for x in range(128):
        if x in top:
            out[x] = (top[x], bot[x])
            continue
        left = [c for c in have if x - 4 <= c < x]
        right = [c for c in have if x < c <= x + 4]
        if left and right:
            a, b = left[-1], right[0]
            f = (x - a) / (b - a)
            out[x] = (int(round(top[a] + (top[b] - top[a]) * f)), int(round(bot[a] + (bot[b] - bot[a]) * f)))
        elif left or right:
            c = left[-1] if left else right[0]
            out[x] = (top[c], bot[c])
    return out


def kt8_turq(blue):
    sh = blue.copy()
    for r in range(3):
        for c in range(8):
            t = tk.tile(sh, r, c)
            src = t.copy()
            doors = KT8_DOORS.get((r, c), [])
            door_cols = {x for a, b in doors for x in range(a, b + 1)}
            face = KT8_FACES.get((r, c))
            face_cols = set(range(face[0], face[1] + 1)) if face else set()
            band = _band(src, door_cols)
            paint = cmask(src, PAINT)
            roof = cmask(src, [ROOF])
            glass = cmask(src, GLASS)
            t[roof] = TQ_ROOF
            for x in range(128):
                col = paint[:, x]
                if not col.any():
                    continue
                ys = np.nonzero(col)[0]
                if x in door_cols:
                    yel = np.nonzero(np.all(src[:, x] == np.array(YELLOW), axis=1))[0]
                    d0, d1 = yel.min(), yel.max()
                    for y in ys:
                        t[y, x] = TQ_MASK if d0 <= y <= d1 else TQ_BODY
                    continue
                if x not in band:
                    for y in ys:
                        t[y, x] = TQ_BODY
                    continue
                b0, b1 = band[x]
                if x in face_cols:                  # the mask runs up to the roof
                    above = np.nonzero(~roof[:b0, x] & ~np.all(src[:b0, x] == np.array(BG), axis=1))[0]
                    b0 = above.min() if len(above) else b0
                for y in ys:
                    if b0 <= y <= b1:
                        t[y, x] = TQ_MASK if x in face_cols else TQ_PILLAR
                    elif y == b1 + 1:
                        t[y, x] = TQ_WHITE
                    else:
                        t[y, x] = TQ_BODY
            del glass
    # the faces seen straight on: front (se) and rear (nw) drawn out
    leg = {"K": TQ_MASK, "W": TQ_WHITE, "B": TQ_BODY, "m": SCREEN, "L": HEAD, "T": TAIL,
           "o": INDICATOR, "r": REFLECTOR, "g": LIT, "h": LIT_HI, "d": FRAME, "k": BLACK}
    t = tk.tile(sh, 0, 5)
    recolor(t, {TQ_ROOF: TQ_MASK}, [(58, 87, 68, 89)])
    art(t, 58, 88, KT8_TQ_FRONT_SE, leg)
    t = tk.tile(sh, 2, 1)
    art(t, 58, 80, KT8_TQ_REAR_NW, leg)
    return sh


# black mask from the roof edge to under the windscreen, white line straight
# across, turquoise apron with the headlights
KT8_TQ_FRONT_SE = """
KKKKKKKKKKK
KKKKKKKKKKK
mKKKKKKKKKm
mmKKKKKKKmm
mmKKKKKKKmm
mmKmmmmmKmm
KmKmmmmmKmK
KKKmmmmmKKK
KKKmmmmmKKK
WWWWWWWWWWW
BBLBBBBBLBB
 BBBBBBBBB
   BBkkkBB
"""
# rear: the black band runs round the passenger rear window
KT8_TQ_REAR_NW = """
KKKKKKKKKKK
KKKKKKKKKKK
KKKKKKKKKKK
gKKKKKKKKKg
ggKKKKKKKgg
ggKdddddKgg
ggKhggghKgg
KgKgggggKgK
KKKgggggKKK
KKKgggggKKK
oWWWWWWWWWo
TBBBBBBBBBT
 BrBBBBBrB
   BBkkkBB
"""


# ------------------------------------------------------------------ preview
def preview(entries, out, zoom=4):
    """Each sheet row at 1x (whole tiles) and `zoom`x (cropped to the drawing) on
    grass, entries one above another."""
    from PIL import Image, ImageDraw
    m = np.zeros((128, 128), bool)
    for _, sh in entries:
        for r in range(sh.shape[0] // 128):
            for c in range(8):
                m |= ~np.all(tk.tile(sh, r, c) == np.array(BG), axis=2)
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = max(0, xs.min() - 2), min(128, xs.max() + 3), max(0, ys.min() - 2), min(128, ys.max() + 3)
    strips = []
    for label, sh in entries:
        for r in range(sh.shape[0] // 128):
            tiles = [tk._on_grass(tk.tile(sh, r, c), r * 8 + c) for c in range(8)]
            one = Image.fromarray(np.concatenate(tiles, axis=1))
            crop = np.concatenate([np.pad(t[y0:y1, x0:x1], ((0, 0), (0, 1), (0, 0)), constant_values=250)
                                   for t in tiles], axis=1)
            big = Image.fromarray(crop).resize((crop.shape[1] * zoom, crop.shape[0] * zoom), Image.NEAREST)
            strips.append((f"{label}  row {r}", one, big))
    W = max(max(s[1].width, s[2].width) for s in strips)
    Ht = sum(14 + s[1].height + s[2].height + 8 for s in strips)
    img = Image.new("RGB", (W, Ht), (250, 250, 250))
    dr = ImageDraw.Draw(img)
    y = 0
    for lab, one, big in strips:
        dr.text((4, y + 1), lab + f"   (1x, then {zoom}x crop x{x0}-{x1} y{y0}-{y1}; views w nw n ne e se s sw)",
                fill=(0, 0, 0))
        y += 14
        img.paste(one, (0, y)); y += one.height
        img.paste(big, (0, y)); y += big.height + 8
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out)
    return out


def consist(sheet_path, lengths, out, rows=None):
    import subprocess
    cmd = [sys.executable, os.path.join(ROOT, "tools", "consist_preview.py"), sheet_path,
           ",".join(str(x) for x in lengths), out, "--zoom", "3"]
    if rows:
        cmd += ["--rows", ",".join(str(x) for x in rows)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    return out


# ------------------------------------------------------------------ families
def build_kt8():
    blue = kt8_blue()
    return {"dpomodrozluta": blue, "dpotyrkysova": kt8_turq(blue)}


# family -> (builder, base sheet for the before/after preview, consists to preview)
FAMILIES = {
    "kt8d5r_n1": (build_kt8, "kt8d5r_n1_dpomodrozluta.png", [((8, 5, 8), None)]),
}


def sheet_path(family, livery):
    return os.path.join(VEH, family, "sprites", livery + ".png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("families", nargs="*", help="default: all of " + ", ".join(FAMILIES))
    ap.add_argument("--preview", help="directory for before/after and consist previews")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    for fam in a.families or list(FAMILIES):
        build, base, consists = FAMILIES[fam]
        sheets = build()
        for livery, sh in sheets.items():
            path = sheet_path(fam, livery)
            if not a.no_write:
                tk.save(sh, path)
                print("wrote", os.path.relpath(path, ROOT))
            if a.preview:
                before = load_src(base)
                print("preview", preview([("before (upstream " + base + ")", before), (fam + " " + livery, sh)],
                                         os.path.join(a.preview, f"{fam}_{livery}.png")))
                if not a.no_write:
                    for k, (lengths, rows) in enumerate(consists):
                        out = os.path.join(a.preview, f"{fam}_{livery}_consist{k or ''}.png")
                        print("consist", consist(path, lengths, out, rows))


if __name__ == "__main__":
    main()
