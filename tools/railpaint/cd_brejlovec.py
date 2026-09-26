#!/usr/bin/env python3
"""ČD Brejlovec (754, 750.7, 750): TommPa9's pak128.cs drawing, repainted.

    python tools/railpaint/cd_brejlovec.py [754|750_7|750 ...] [--preview DIR]

The user found every box render of the Brejlovec unrecognisable, so the sheets
repaint TommPa9's hand-drawn T 478 / 75x body instead and keep its shape,
shading and details. All eleven of his Brejlovec liveries in pak128.cs share one
silhouette (frozen in src/tommpa9_brejlovec/, lifted 4 px to source
coordinates). Comparing them tells what each pixel is:

- FIX     identical in every livery: windows, goggles, lamps, black lines;
- FRAME   dark grey on the blue (balkan) sheet but not red on the 753: underframe;
- ROOF    dark grey on the blue sheet and red on the 753: the roof and its
          shoulders (the lowest two roof rows of a column are the shoulder);
- CAB     red on the 752 (red cab blocks on a blue hood): both cab blocks;
- wall    everything else: the body sides and the cab fronts.

Livery zones are painted by whole pixel rows counted from the top of the wall
in every column (r = 0 is the row just under the roof shoulder), so stripes
stay one pixel row thick in every view. Each colour is multiplied by the
original pixel's light (its red level on the 753, or its grey level on the
750 low band), so TommPa9's lighting and edge highlights survive.

The 750.7 gets its rebuilt fronts by repainting the end-face pixels: the white
goggle frame and split screen become one wide dark windscreen with a body-
coloured frame, as on the CZ LOKO rebuild.
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, "src", "tommpa9_brejlovec")
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
sys.path.insert(0, os.path.join(REPO, "tools", "railrender"))
import cd_loco_livery as CL  # noqa: E402

T = np.array([231, 255, 255])
REFS = ["CD_750_Brejlovec", "CD_750_Brejlovec_(balkan)", "CD_752_Brejlovec", "CD_753_Brejlovec",
        "CD_754_Brejlovec", "CD_754_Brejlovec_(balkan)", "CD_755_Brejlovec", "CD_Cargo_753_Brejlovec_",
        "CSD_T_478.1_Brejlovec", "CSD_T_478.2_Brejlovec", "CSD_T_478.3_Brejlovec"]
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
KEEP = {0xFFFF53, 0xFF211D}          # head / tail lights stay specials


def load(name):
    return np.array(Image.open(os.path.join(SRC, name + ".png")).convert("RGB")).astype(int)


def fam(c):
    r, g, b = [x / 255 for x in c]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l < 0.09:
        return "k"
    if s < 0.18 or (max(r, g, b) - min(r, g, b)) < 0.12:
        return "w" if l > 0.72 else ("g" if l > 0.36 else "d")
    h *= 360
    if h < 20 or h >= 330:
        return "r"
    if h < 70:
        return "y"
    if h < 170:
        return "t"
    return "b"


class Base:
    """Zones, row indices and light of the shared TommPa9 silhouette."""

    def __init__(self):
        R = {k: load(k) for k in REFS}
        self.R = R
        self.solid = ~np.all(R[REFS[0]] == T, axis=2)
        F = {k: np.vectorize(lambda a, b, c: fam((a, b, c)))(v[..., 0], v[..., 1], v[..., 2])
             for k, v in R.items()}
        b752, b753, bB = F["CD_752_Brejlovec"], F["CD_753_Brejlovec"], F["CD_754_Brejlovec_(balkan)"]
        same = np.all([np.all(R[k] == R[REFS[0]], axis=2) for k in REFS], axis=0)
        body = self.solid & ~same
        Z = np.full(self.solid.shape, "", object)
        Z[self.solid] = "FIX"
        Z[body] = "WALL"
        Z[body & (bB == "d") & (b753 == "r")] = "ROOF"
        Z[body & (bB == "d") & (b753 != "r")] = "FRAME"
        # lamps (the roof headlight): yellow on both the blue and the green sheet
        Z[body & (bB == "y") & (F["CD_750_Brejlovec"] == "y")] = "FIX"
        self.cab = body & (b752 == "r")
        # windscreen / cab-window glass: TommPa9's non-darkening grey 0x6B6B6B
        self.glass = self.solid & np.all(R["CD_754_Brejlovec_(balkan)"] == [0x6B, 0x6B, 0x6B], axis=2)
        near = np.zeros_like(self.glass)
        for dy in (-1, 0, 1):          # 8-neighbour: a closed frame, no checker
            for dx in (-1, 0, 1):
                near |= np.roll(np.roll(self.glass, dy, 0), dx, 1)
        self.surround = near & (Z == "WALL")
        self.view = np.tile(np.repeat(np.arange(8), 128), (Z.shape[0], 1))
        self.Z = Z
        # light: the 753's red level (top face bd = 1.0), else the 750's grey
        r753, g750 = R["CD_753_Brejlovec"], R["CD_750_Brejlovec"]
        fac = np.ones(Z.shape)
        red = b753 == "r"
        fac[red] = r753[..., 0][red] / 0xBD
        grey = ~red & (F["CD_750_Brejlovec"] == "g")
        fac[grey] = g750[..., 1][grey] / 0xAD
        self.fac = np.clip(fac, 0.55, 1.2)
        # row indices per column: r = wall row from the wall top, q = roof row
        # from the roof bottom (0, 1 = shoulder)
        H, W = Z.shape
        self.r = np.full(Z.shape, -1)
        self.q = np.full(Z.shape, -1)
        self.wallrows = np.zeros(Z.shape, int)
        for x in range(W):
            col = Z[:, x]
            roof = [y for y in range(H) if col[y] == "ROOF"]
            for i, y in enumerate(sorted(roof, reverse=True)):
                self.q[y, x] = i
            # the wall starts right under the roof (or at the first wall pixel
            # where a column has no roof) and runs down to the frame
            if roof:
                # end of the first roof run from the top (FIX roof details inside
                # the run belong to it); in the end views the column crosses the
                # roof, then the cab front, then more roof lower down
                y = min(roof)
                last = y
                while y < H and col[y] in ("ROOF", "FIX"):
                    if col[y] == "ROOF":
                        last = y
                    elif not any(col[yy] == "ROOF" for yy in range(y + 1, min(H, y + 3))):
                        break
                    y += 1
                top = last + 1
            else:
                walls = [y for y in range(H) if col[y] == "WALL"]
                if not walls:
                    continue
                top = min(walls)
            ys = []
            for y in range(top, H):
                if col[y] in ("WALL", "FIX"):
                    ys.append(y)
                else:
                    break
            # the wall height ends at the last paintable row (lamps and buffer
            # beam FIX pixels below it don't count)
            walls = [y for y in ys if col[y] == "WALL"]
            n = (max(walls) - top + 1) if walls else len(ys)
            for y in ys:
                self.r[y, x] = y - top
                self.wallrows[y, x] = n
            # wall-coloured specks inside the roof are roof details
            for y in range(0, top):
                if col[y] == "WALL":
                    self.r[y, x] = -1
        # u along the body, 0 = the tile's left end of the body, per view
        self.u = np.zeros(Z.shape)
        for c in range(8):
            xs = np.where(self.solid[:, c * 128:(c + 1) * 128].any(axis=0))[0]
            if len(xs):
                x0, x1 = xs.min(), xs.max()
                for x in range(x0, x1 + 1):
                    self.u[:, c * 128 + x] = (x - x0) / max(1, x1 - x0)



B = None


def base():
    global B
    if B is None:
        B = Base()
    return B


def shade(c, f):
    return tuple(int(max(0, min(255, round(v * f)))) for v in c)


def unspecial(a, painted):
    """nudge accidental special colours off the table, in painted pixels only
    (TommPa9's own pixels, e.g. his 0x6B6B6B glass, stay bit-exact)."""
    hx = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    bad = np.isin(hx, list(SPECIAL - KEEP)) & painted
    a[bad, 2] = np.where(a[bad, 2] < 255, a[bad, 2] + 1, 254)
    return a


# ------------------------------------------------------------------ liveries
SKY, WHITE, SAPPH, LGREY = CL.LOCO_SKY, CL.WHITE, CL.SAPPHIRE, CL.LGREY
ROOF_N2 = (60, 70, 92)          # dark sapphire-grey roof top (754.062, 754.045)
ROOF_GREY = (98, 102, 106)
FRAME = (46, 48, 51)
RED = (196, 32, 40)
YEL = (242, 194, 0)
CREAM = (232, 222, 188)
BC_BLUE = (28, 58, 118)
N1_WHITE = CL.N1_WHITE
BC_SKY = (54, 136, 206)       # 754.013 blue-cream: light-blue upper body


def n2_wall(r, n):
    """Najbrt 2 wall: sky, one white row at headlight level, sapphire below."""
    if r >= n - 2:
        return SAPPH
    if r == n - 3:
        return WHITE
    return SKY


def roof_n2(q):
    if q == 0:
        return SKY
    if q == 1:
        return WHITE
    return ROOF_N2


def trapezoid(u, r, n, cab2_right=True):
    """Najbrt 1 / 1.2 wedges rising toward cab 2: sapphire over sky."""
    t = u if cab2_right else 1 - u
    h = r / max(1, n - 1)              # 0 top .. 1 bottom
    edge = 0.30 + 0.45 * h             # the wedge leans toward cab 2
    if t > edge + 0.18:
        return SAPPH
    if t > edge:
        return SKY
    return None


def paint(liv, front=None):
    b = base()
    Z, cab, r, q, n, u, fac = b.Z, b.cab, b.r, b.q, b.wallrows, b.u, b.fac
    src = b.R["CD_754_Brejlovec_(balkan)"]
    out = src.copy()
    painted = np.zeros(Z.shape, bool)
    H, W = Z.shape
    for y in range(H):
        for x in range(W):
            z = Z[y, x]
            if z in ("", "FIX"):
                continue
            if z == "WALL" and r[y, x] < 0 and not b.surround[y, x]:
                z = "ROOF"
            c = None
            if z == "FRAME":
                c = FRAME
            elif z == "ROOF":
                qq = q[y, x] if b.view[y, x] not in (1, 5) else 9
                if liv in ("najbrt2", "najbrt1_2"):
                    c = roof_n2(qq) if liv == "najbrt2" else (
                        LGREY if cab[y, x] and qq <= 1 else (SKY if qq == 0 else ROOF_GREY))
                elif liv == "najbrt1":
                    c = N1_WHITE if qq <= 1 or cab[y, x] else (212, 216, 218)
                elif liv == "cervenozluta":
                    c = RED if qq <= 1 else ROOF_GREY
                elif liv == "modrokremova":
                    c = BC_SKY if qq == 0 else BC_BLUE
            else:  # WALL
                rr, nn = r[y, x], n[y, x]
                if rr < 0:
                    rr, nn = 0, 7
                if liv == "najbrt2":
                    c = n2_wall(rr, nn)
                elif liv in ("najbrt1_2", "najbrt1"):
                    body = LGREY if liv == "najbrt1_2" else N1_WHITE
                    if cab[y, x]:
                        c = body if rr < nn - 2 else (SAPPH if liv == "najbrt1" else (58, 61, 64))
                    else:
                        c = trapezoid(u[y, x] % 1.0, rr, nn) or (SKY if liv == "najbrt1_2" else body)
                        if rr >= nn - 1:
                            c = SAPPH if liv == "najbrt1" else (58, 61, 64)
                elif liv == "cervenozluta":
                    c = YEL if nn - 4 <= rr <= nn - 2 else RED
                elif liv == "modrokremova":
                    c = BC_BLUE if rr >= nn - 2 else (CREAM if rr >= nn - 5 else BC_SKY)
            if z == "WALL" and b.surround[y, x] and liv in ("najbrt2", "najbrt1_2", "najbrt1"):
                c = WHITE
            if c is not None:
                out[y, x] = shade(c, fac[y, x])
                painted[y, x] = True
    if front:
        front(out, b)
        painted &= ~np.all(out == [0x6B, 0x6B, 0x6B], axis=2)   # new glass = TommPa9's glass
    return unspecial(out, painted)



def front_7507(out, b):
    """750.7: the goggle pair becomes one wide windscreen: frame pixels that sit
    between two glass pixels of the same row (the centre pillar) turn to glass."""
    g = b.glass
    H, W = g.shape
    for y in range(H):
        xs = np.where(g[y])[0]
        for x0, x1 in zip(xs[:-1], xs[1:]):
            # only views that show a front; the ne / sw side views hold the
            # cab side windows, whose pillars stay
            if 1 < x1 - x0 <= 3 and x0 // 128 == x1 // 128 and x0 // 128 not in (3, 7):
                out[y, x0 + 1:x1] = (0x6B, 0x6B, 0x6B)


JOBS = {
    "754": ["najbrt2", "najbrt1_2", "najbrt1", "cervenozluta", "modrokremova"],
    "750_7": ["najbrt2", "najbrt1_2"],
    "750": ["zelenosediva", "najbrt1_2"],
}


def sheet(fam_, liv):
    if fam_ == "750" and liv == "zelenosediva":
        return base().R["CD_750_Brejlovec"].copy()      # TommPa9's own green-grey, unchanged
    return paint(liv, front_7507 if fam_ == "750_7" else None)


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for f in (args or list(JOBS)):
        for liv in JOBS[f]:
            a = sheet(f, liv).astype(np.uint8)
            out = os.path.join(FAM, f, "sprites", f"{liv}.png")
            Image.fromarray(a).save(out)
            print("wrote", os.path.relpath(out, REPO))
            if prev:
                g = a.copy()
                g[np.all(g == T, axis=2)] = (104, 124, 76)
                Image.fromarray(g).resize((2048, 256), Image.NEAREST).save(os.path.join(prev, f"{f}_{liv}.png"))


if __name__ == "__main__":
    main()
