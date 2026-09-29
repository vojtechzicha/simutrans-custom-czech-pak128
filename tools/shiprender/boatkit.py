"""Open river ferry boats for the pak128 box renderer (tools/busrender/render.py,
imported read-only): a parametric Boat (hull built from rake steps, deck on the
hull top, canopy with a valance on posts, railings, wheelhouse or helm console,
benches) textured per face, plus a few projected pixels (flag, mast, lamps).

Scale: the road-vehicle scale of render.py (1.5 px/m across, 4 px/m up; a 12 m
bus is 51 px long in the side views), so a boat reads at its true size next to
buses. Placement: hull centre at the waterline on the per-view origin fitted to
the native pak128.cs small ferries Ferry_yeu_128set and Veveri_ship_128set
(fitlane.py on src/*.png; both agree within 1-2 px), i.e. their right-hand
lane. The sheets use image_offset [0, 0]: rows extracted from pak128.cs ship
paks already sit where the game draws them (their .dat's -61,-91 crops a
250 px source cell to the 128 px tile).

Vehicle frame: s = 0 (stern, flag) .. L (bow, wheelhouse / helm),
t = -B/2 (port) .. +B/2 (starboard), z = height above the water.
"""
import os, sys, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "busrender"))
from render import Box, render, project, DIRS, HEAD, P  # noqa: E402

T = (231, 255, 255)
# hull centre at the waterline, per view (mean of the Ferry_yeu / Veveri fits)
ORIGINS = {"w": (71, 89), "nw": (75, 89), "n": (74, 104), "ne": (65, 108),
           "e": (52, 106), "se": (43, 86), "s": (53, 95), "sw": (60, 90)}

SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
ALLOWED = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}
GLASS = (0x4D, 0x4D, 0x4D)
GLASS2 = (0x57, 0x65, 0x6F)

NORMALS = {"top": None, "front": (1, 0), "rear": (-1, 0), "right": (0, 1), "left": (0, -1)}


def shade_of(view, face):
    if face == "top":
        return 1.0
    hx, hy = HEAD[view]
    a, b = NORMALS[face]            # in (heading, right) frame
    nx = a * hx + b * (-hy)
    ny = a * hy + b * hx
    k = (ny - nx + 1) / 2           # 1 = south-facing (lit), 0 = east-facing
    return 0.76 + 0.20 * max(0.0, min(1.0, k))


def mul(c, k):
    return tuple(int(max(0, min(255, round(v * k)))) for v in c)


# ------------------------------------------------------------------ helpers
def near(p, k, v, w=0.0):
    return p.near(k, v, w)


class Boat:
    """Parametric open ferry: hull (stacked boxes for the rake), deck, canopy on
    posts, railings, a wheelhouse or helm console, benches; details drawn as
    textures (1-px lines exact via Px.line) and a few projected pixels."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    # -- geometry
    def boxes(self):
        L, B, s = self.L, self.B, self
        bx = []
        # hull: rake steps (z0, z1, s_from_stern, s_from_bow, inset of width)
        for i, (z0, z1, a, b, w) in enumerate(self.hull):
            bx.append(Box(f"hull{i}", a, L - b, -B / 2 + w, B / 2 - w, z0, z1))
        # railings / posts: thin slabs on the four sides (both faces of each slab
        # exist, so the far railing shows through the open sides too)
        c0, c1 = self.can_s
        z0, z1 = self.deck, self.can_z[0]
        e = 0.02
        rs0, rs1 = self.rail_s
        tw = B / 2 - self.rail_in
        bx.append(Box("railR", rs0, rs1, tw - e, tw, z0, z1))
        bx.append(Box("railL", rs0, rs1, -tw, -tw + e, z0, z1))
        bx.append(Box("railS", rs0, rs0 + e, -tw, tw, z0, z1))
        bx.append(Box("railB", rs1 - e, rs1, -tw, tw, z0, z1))
        # canopy: top + valance skirt
        cz0, cz1 = self.can_z
        bx.append(Box("canopy", c0, c1, -B / 2 - self.can_over, B / 2 + self.can_over, cz0, cz1))
        for i, bb in enumerate(self.benches):
            bx.append(Box(f"bench{i}", *bb))
        if self.cabin:
            a, b, t0, t1, zt = self.cabin
            bx.append(Box("cabin", a, b, t0, t1, self.deck, zt))
        if self.console:
            a, b, t0, t1, zt = self.console
            bx.append(Box("console", a, b, t0, t1, self.deck, zt))
        return bx

    # -- texture
    def tex(self, p):
        n = p.box
        s, t, z = p.c
        col = None
        if n.startswith("hull"):
            col = self.tex_hull(p)
        elif n == "deck":
            col = self.DECK
        elif n.startswith("rail"):
            col = self.tex_rail(p)
        elif n == "canopy":
            col = self.tex_canopy(p)
        elif n.startswith("bench"):
            col = self.BENCH if p.face == "top" else mul(self.BENCH, 0.8)
        elif n == "cabin":
            col = self.tex_cabin(p)
        elif n == "console":
            col = self.tex_console(p)
        if col is None:
            return None
        if col in (GLASS, GLASS2):
            return col
        return mul(col, shade_of(p.view, p.face))

    def tex_hull(self, p):
        s, t, z = p.c
        top = self.hull[-1][1]
        if p.face == "top":
            a, b = self.hull[-1][2], self.L - self.hull[-1][3]
            g = self.gw
            if z < top - 0.01 or abs(t) > self.B / 2 - g or s < a + g or s > b - g:
                return self.GUNWALE
            return self.DECK
        if self.gw_side > 0 and z > top - self.gw_side:
            return self.GUNWALE
        if self.hull_low is not None and z < self.hull_low[0]:
            return self.hull_low[1]
        if p.face in ("right", "left") and self.letters(p):
            return self.LETTER
        return self.HULL

    def letters(self, p):
        s, t, z = p.c
        for (a, b, zc) in self.names:
            if a <= s <= b and p.near(2, zc, 0.0):
                # dashed lettering: skip every third drawn metre step
                return int((s - a) / 0.26) % 3 != 2
        return False

    def tex_rail(self, p):
        s, t, z = p.c
        if p.face == "top":
            return None
        along = 0 if p.box in ("railR", "railL") else 1
        pos = s if along == 0 else t
        posts = self.posts if along == 0 else self.end_posts
        for q in posts:
            if p.line(along, q):
                return self.POST
        zr = z - self.deck
        for r in self.rails:
            if p.line(2, self.deck + r):
                if along == 0 and any(a <= s <= b for a, b in self.gates):
                    continue
                return self.RAIL
        return None

    def tex_canopy(self, p):
        s, t, z = p.c
        if p.face == "top":
            if self.can_edge and (p.line(1, self.B / 2 + self.can_over - 0.01) or
                                  p.line(1, -self.B / 2 - self.can_over + 0.01)):
                return self.CAN_EDGE_TOP
            return self.CANOPY
        # valance skirt
        if self.scallop and p.line(2, self.can_z[0] + 0.01):
            k = s if p.face in ("right", "left") else t
            return self.VALANCE if int(k / 0.27) % 2 == 0 else None
        return self.VALANCE

    def tex_cabin(self, p):
        s, t, z = p.c
        if p.face == "top":
            return self.CAB_ROOF
        zr = z - self.deck
        w0, w1 = self.win_z
        if zr >= w1:
            return self.CREAM
        k = s if p.face in ("right", "left") else t
        a, b = (self.cabin[0], self.cabin[1]) if p.face in ("right", "left") else (self.cabin[2], self.cabin[3])
        # lifebuoys on the cabin sides
        for (bs, bz, faces) in self.buoys:
            if p.face in faces and p.near(0 if p.face in ("right", "left") else 1, bs, 0.12) and p.near(2, self.deck + bz, 0.12):
                ang = (int((k - bs + 0.3) / 0.2) + int((z - self.deck - bz + 0.3) / 0.2)) % 2
                return self.BUOY_A if ang else self.BUOY_B
        if w0 <= zr < w1:
            # windows between mahogany frames
            if p.line(0 if p.face in ("right", "left") else 1, (a + b) / 2) or k - a < 0.14 or b - k < 0.14:
                return self.FRAME
            if zr > w1 - 0.1 or zr < w0 + 0.08:
                return self.FRAME
            return GLASS
        # lower varnished boards, a frame line under the windows
        if p.line(2, self.deck + w0 - 0.05):
            return self.FRAME
        return self.WOOD

    def tex_console(self, p):
        s, t, z = p.c
        if p.face == "top":
            return self.CONSOLE_TOP
        if p.face in ("right", "left") and self.console_text(p):
            return self.CONSOLE_TEXT
        return self.CONSOLE

    def console_text(self, p):
        s, t, z = p.c
        a, b = self.console[0], self.console[1]
        zc = self.deck + self.console_text_z
        return a + 0.15 <= s <= b - 0.1 and p.near(2, zc, 0.0) and int((s - a) / 0.24) % 3 != 2

    # -- projected details (flag, masts, lamps)
    def extras(self, img, view, o):
        def put(s, t, z, c):
            x, y = project(view, self.L, o, s, t, z)
            x, y = int(math.floor(x)), int(math.floor(y))
            if 0 <= x < 128 and 0 <= y < 128:
                img[y, x] = c
        # flag staff at the stern and the Czech flag (white over red, blue hoist)
        fs, fz = self.flag
        steps = int((fz - self.deck) / 0.18)
        for i in range(steps + 1):
            put(fs, 0.0, self.deck + i * 0.18, self.STAFF)
        hx, hy = HEAD[view]
        # the flag streams aft (towards -s)
        for i, dz in enumerate((0.0, 0.25)):
            for j, ds in enumerate((0.15, 0.4, 0.65)):
                if j == 0:
                    c = self.FLAG_B
                else:
                    c = self.FLAG_W if i == 0 else self.FLAG_R
                put(fs - ds, 0.0, fz - dz, c)
        for (ms, mt, z0, z1, top) in self.masts:
            n = max(1, int((z1 - z0) / 0.2))
            for i in range(n):
                put(ms, mt, z0 + i * (z1 - z0) / n, self.STAFF)
            put(ms, mt, z1, top)
        for (ls, lt, lz, c) in self.lamps:
            put(ls, lt, lz, c)


def check(arr, label):
    flat = arr.reshape(-1, 3).astype(np.int64)
    used = set(np.unique((flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]).tolist())
    bad = (used & SPECIAL) - ALLOWED
    return bad


def fix_specials(img):
    """nudge any accidental special colour by one in blue"""
    flat = img.reshape(-1, 3)
    v = (flat[:, 0].astype(np.int64) << 16) | (flat[:, 1].astype(np.int64) << 8) | flat[:, 2]
    for sp in SPECIAL - ALLOWED:
        m = v == sp
        if m.any():
            flat[m, 2] = np.where(flat[m, 2] > 0, flat[m, 2] - 1, 1)
    return img


def build_row(boat):
    tiles = []
    for d in DIRS:
        o = np.array(ORIGINS[d], float)
        img, _ = render(d, boat.boxes(), boat.tex, boat.L, o)
        boat.extras(img, d, o)
        tiles.append(fix_specials(img))
    return tiles


def save_sheet(rows, path):
    out = np.zeros((128 * len(rows), 1024, 3), np.uint8)
    out[:] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    bad = check(out, path)
    if bad:
        raise SystemExit(f"{path}: special colours {sorted(hex(b) for b in bad)}")
    Image.fromarray(out).save(path)
    return out
