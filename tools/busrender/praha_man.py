"""MAN city buses (agent man, 2026-09-29), box-rendered in the projection of
the repo's DPP Streetway 12M / Crossway LE CITY 14,5M renders (1.386 m per
length unit, 4.15 px per metre of height), then shifted onto the median lane
footprint of native pak128.cs 12 m buses. Purely procedural: no source images.

Bodies (parametric, one class each):
  NewGen       MAN Lion's City 12 (2018 generation) "12C", NL 330 / NL 280:
               black one-piece face, grey corner fins, stepped roof fairing,
               engine-tower louvres in the last left window bay.
  Hybrid       NewGen + the EfficientHybrid roof module behind the A/C.
  IntercityLE  MAN Lion's Intercity LE 12 (LEU 330), doors 1-2-0.
  OldGen       MAN Lion's City, 2004-2019 generation, 12 m: NL 293 (Praha)
               and NL 283 (Brno).
  LionsCityL   OldGen stretched to the 14.7 m 3-axle Lion's City L (NL 323).

Liveries: "A" PID scheme A (pidsedocervena), "B" PID trikolora
(pidcervenomodrobila), "J" IDS JMK white-grey with the red roof edge (idsjmk).
The chosen shapes (user's picks from the variant round, 2026-09-29): 12C and
12C EfficientHybrid "v2 visible step", Lion's City L "v3", Intercity LE "v1";
the NL 293 / NL 283 use the measured old-gen defaults.

usage: python tools/busrender/praha_man.py [family ...] [--preview DIR]
"""
import sys, os, math
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

# ================================================================ iso renderer
# (the renderer of the DPP Streetway / Crossway LE CITY 14,5M renders)
# Tiny orthographic renderer for pak128 road-vehicle sprites.
# 
# World coordinates of a vehicle body (metres):
#   u = longitudinal, 0 at the front, growing rearwards
#   v = lateral, 0 at the vehicle's LEFT side, growing to the right
#   h = height above the road
# Screen projection (Simutrans pak128 isometric): one length unit (1/16 tile)
# along grid i = (4, 2) px, along grid j = (-4, 2) px; heights go straight up.

T = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
S2 = 1 / math.sqrt(2)
HEADING = {"n": (0, -1), "ne": (S2, -S2), "e": (1, 0), "se": (S2, S2),
           "s": (0, 1), "sw": (-S2, S2), "w": (-1, 0), "nw": (-S2, -S2)}


def proj(gi, gj):
    return np.array([4.0 * (gi - gj), 2.0 * (gi + gj)])


class View:
    def __init__(self, d, mpu, kh, origin):
        self.d = d
        hi, hj = HEADING[d]
        self.hd = (hi, hj)
        self.right = (-hj, hi)
        self.Au = proj(-hi, -hj) / mpu          # screen px per metre rearwards
        self.Av = proj(*self.right) / mpu       # per metre to the right
        self.Ah = np.array([0.0, -kh])          # per metre up
        self.O = np.array(origin, dtype=float)  # screen pos of (0,0,0)

    def S(self, u, v, h):
        return self.O + self.Au * u + self.Av * v + self.Ah * h

    def normal_visible(self, n_grid):
        return proj(*n_grid)[1] > 1e-6


class Box:
    """Axis-aligned box in vehicle coords with a texture callback per face.
    tex(face, a, b) -> RGB tuple or None (transparent). face in
    'top','left','right','front','rear'; (a, b) are world coords on the face:
    top: (u, v); left/right: (u, h); front/rear: (v, h)."""

    def __init__(self, u0, u1, v0, v1, h0, h1, tex, faces=None):
        self.u0, self.u1, self.v0, self.v1, self.h0, self.h1 = u0, u1, v0, v1, h0, h1
        self.tex = tex
        self.faces = faces  # optional subset of faces to draw

    def face_list(self, view):
        hi, hj = view.hd
        ri, rj = view.right
        out = []
        cand = {
            "top": ((0, 0), None),
            "left": ((-ri, -rj), None),
            "right": ((ri, rj), None),
            "front": ((hi, hj), None),
            "rear": ((-hi, -hj), None),
        }
        for f, (n, _) in cand.items():
            if self.faces is not None and f not in self.faces:
                continue
            if f == "top" or view.normal_visible(n):
                out.append(f)
        return out

    def face_geom(self, f):
        u0, u1, v0, v1, h0, h1 = self.u0, self.u1, self.v0, self.v1, self.h0, self.h1
        if f == "top":
            return (u0, v0, h1), (u1 - u0, 0, 0), (0, v1 - v0, 0), (u0, u1), (v0, v1)
        if f == "left":
            return (u0, v0, h0), (u1 - u0, 0, 0), (0, 0, h1 - h0), (u0, u1), (h0, h1)
        if f == "right":
            return (u0, v1, h0), (u1 - u0, 0, 0), (0, 0, h1 - h0), (u0, u1), (h0, h1)
        if f == "front":
            return (u0, v0, h0), (0, v1 - v0, 0), (0, 0, h1 - h0), (v0, v1), (h0, h1)
        if f == "rear":
            return (u1, v0, h0), (0, v1 - v0, 0), (0, 0, h1 - h0), (v0, v1), (h0, h1)


def render(view, boxes, size=128, canvas=None, ss=None):
    """Render boxes in order (later boxes paint over earlier ones)."""
    img = np.zeros((size, size, 3), dtype=np.uint8) if canvas is None else canvas
    if canvas is None:
        img[:, :] = T
    ys, xs = np.mgrid[0:size, 0:size]
    px = xs + 0.5
    py = ys + 0.5
    for box in boxes:
        for f in box.face_list(view):
            p0, e1, e2, ra, rb = box.face_geom(f)
            s0 = view.S(*p0)
            s1 = view.Au * e1[0] + view.Av * e1[1] + view.Ah * e1[2]
            s2 = view.Au * e2[0] + view.Av * e2[1] + view.Ah * e2[2]
            det = s1[0] * s2[1] - s1[1] * s2[0]
            if abs(det) < 1e-6:
                continue  # edge-on
            dx = px - s0[0]
            dy = py - s0[1]
            a = (dx * s2[1] - dy * s2[0]) / det
            b = (s1[0] * dy - s1[1] * dx) / det
            inside = (a >= 0) & (a < 1) & (b >= 0) & (b < 1)
            # world size of one pixel along each face axis
            pa = abs(ra[1] - ra[0]) / max(abs(s1[0]), abs(s1[1]), 1e-9)
            pb = abs(rb[1] - rb[0]) / max(abs(s2[0]), abs(s2[1]), 1e-9)
            for y, x in zip(*np.where(inside)):
                wa = ra[0] + a[y, x] * (ra[1] - ra[0])
                wb = rb[0] + b[y, x] * (rb[1] - rb[0])
                c = box.tex(f, wa, wb, pa, pb)
                if c is not None:
                    img[y, x] = c
    return img


def bbox(tile):
    m = ~np.all(tile == np.array(T), axis=2)
    ys, xs = np.where(m)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


# ================================================================ lane placement

# Height-independent footprint metrics (X = body x-centre, C = lower-edge
# intercept along the road slope; vertical views: C = y-centre), median of core
# native pak128.cs 12 m vehicles. Natives agree on C within +-2 px.
MEDIAN = {"w": (57.2, 57.5), "nw": (73.0, 81.2), "n": (83.2, 139.0), "ne": (65.2, 105.5),
          "e": (45.2, 74.0), "se": (50.0, 83.0), "s": (65.5, 120.5), "sw": (64.5, 92.0)}
SLOPE = {"w": 0.5, "e": 0.5, "n": -0.5, "s": -0.5, "ne": 0.0, "sw": 0.0}


def metrics(tile, d):
    m = ~np.all(tile == np.array(T), axis=2)
    mo = ndimage.binary_opening(m, structure=np.ones((3, 3)))
    lab, n = ndimage.label(mo)
    sizes = ndimage.sum(mo, lab, range(1, n + 1))
    big = lab == (1 + int(np.argmax(sizes)))
    ys, xs = np.where(big)
    X = (xs.min() + xs.max()) / 2
    if d in SLOPE:
        cs = [np.where(big[:, x])[0].max() - SLOPE[d] * x
              for x in range(xs.min(), xs.max() + 1) if big[:, x].any()]
        C = float(np.median(cs))
    else:
        C = (ys.min() + ys.max()) / 2
    return X, C


def shift_for(tile, d, lat_thr=2, lon_thr=4):
    X, C = metrics(tile, d)
    mx, mc = MEDIAN[d]
    if d in ("nw", "se"):
        dx = int(round(mx - X)) if abs(mx - X) >= lat_thr else 0
        dy = int(round(mc - C)) if abs(mc - C) >= lon_thr else 0
        return dx, dy, X, C
    dx = int(round(mx - X)) if abs(mx - X) >= lon_thr else 0
    # C' = C + dy - slope*dx  ->  choose dy so that C' ~ mc
    need = mc - (C - SLOPE[d] * dx)
    dy = int(round(need)) if abs(need) >= lat_thr else 0
    return dx, dy, X, C


def shift_tile(tile, dx, dy):
    out = np.zeros_like(tile); out[:, :] = T
    m = ~np.all(tile == np.array(T), axis=2)
    ys, xs = np.where(m)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
    if not ok.all():
        raise ValueError(f"shift ({dx},{dy}) pushes pixels out of the tile")
    out[ny, nx] = tile[ys, xs]
    return out


def normalize_rows(rows, threshold=2, report=True, label=""):
    out = []
    for r, tiles in enumerate(rows):
        nt = []
        for c, d in enumerate(DIRS):
            dx, dy, X, C = shift_for(tiles[c], d, lat_thr=threshold)
            if report and (dx or dy):
                print(f"  {label} row{r} {d:2s}: X={X:.1f} C={C:.1f} (median {MEDIAN[d]}) -> shift ({dx:+d},{dy:+d})")
            nt.append(shift_tile(tiles[c], dx, dy) if (dx or dy) else tiles[c].copy())
        out.append(nt)
    return out

MPU = 1.386
KH = 4.15


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def shade_key(view, face):
    if face == "top":
        return "top"
    hi, hj = view.hd
    ri, rj = view.right
    n = {"left": (-ri, -rj), "right": (ri, rj), "front": (hi, hj), "rear": (-hi, -hj)}[face]
    p = proj(*n)
    if abs(p[0]) < 1e-6:
        return "SE"
    return "S" if p[0] < 0 else "E"


def any_in(x, rngs):
    return any(a <= x < b for a, b in rngs)


_SW_ORIGIN = {"w": (36.0, 77.0), "nw": (68.0, 74.0), "n": (95.0, 87.0), "ne": (90.0, 102.0),
              "e": (69.0, 102.5), "se": (56.0, 103.0), "s": (51.0, 97.0), "sw": (42.0, 94.5)}


def centre(d):
    v = View(d, MPU, KH, _SW_ORIGIN[d])
    return v.S(6.0, 1.315, 0.0)


# ---------------------------------------------------------------- palettes
# PID scheme A: the DPP Streetway / Crossway render palette (same livery)
GREY = {"top": 0xD8D9DC, "S": 0xCFD0D3, "SE": 0xC5C6C9, "E": 0xBBBCBF}
GREY_SK = {"top": 0xB4B5B8, "S": 0xAAABAE, "SE": 0xA2A3A6, "E": 0x999A9D}
RED_A = {"top": 0xE8282E, "S": 0xDC232A, "SE": 0xD02026, "E": 0xC21C22}
RED_A_SK = {"top": 0xC01E24, "S": 0xB41B21, "SE": 0xAA191E, "E": 0x9E171C}
AC_A = {"top": 0xE9EAED, "S": 0xDDDEE1, "SE": 0xD2D3D6, "E": 0xC6C7CA}
# PID trikolora: the DPP SOR NB 12 trikolora sheet palette
BLUE = {"top": 0x2657AD, "S": 0x2352A2, "SE": 0x214D9A, "E": 0x1E4893}
RED_B = {"top": 0xD50B15, "S": 0xCC0B14, "SE": 0xC00A13, "E": 0xAC0911}
RED_B_SK = {"top": 0xA80912, "S": 0x9E0810, "SE": 0x95080F, "E": 0x88070E}
WHITE = {"top": 0xF4F4F4, "S": 0xEEEEEE, "SE": 0xE9E9E9, "E": 0xE0E0E0}
AC_B = {"top": 0x2C5FB6, "S": 0x2657AD, "SE": 0x2352A2, "E": 0x1E4893}

BLACK = 0x1B1B1C
FRAME = 0x0E0E0F
GLASS = 0x4D4D4D      # special: lit at night (loaded)
GLASS2 = 0x57656F     # special: lighter glass (door leaves, windscreen top row)
TYRE = 0x121212
HUB = 0x76777A
ARCH = 0x0A0A0B
AMBER = 0xF7A21B
LIME = 0x62D64A       # green LED displays (IDS JMK / BDS-BUS, as the repo's DPMB sheets)
# IDS JMK regional scheme (BDS-BUS): white, silver-grey lower body, red roof-edge line
RED_J = {"top": 0xED1C24, "S": 0xE21A22, "SE": 0xD4181F, "E": 0xC5161D}
GREY_J = {"top": 0x9A9A9C, "S": 0x8E8E90, "SE": 0x8A8A8C, "E": 0x7E7E80}
GREY_J_SK = {"top": 0x6E6E70, "S": 0x68686A, "SE": 0x646466, "E": 0x5E5E60}
ROOF_J = {"top": 0xECECEE, "S": 0xE2E2E4, "SE": 0xDADADC, "E": 0xD0D0D2}
AC_J = {"top": 0xF6F6F7, "S": 0xEDEDEF, "SE": 0xE2E2E5, "E": 0xD6D6D9}
HEAD = 0xFFFF53       # special: headlight
TAIL = 0xFF211D       # special: tail light
GRILLE = 0x5E5F62
SLAT = 0x6E7074       # louvre slats
HATCH = 0xE6E7EA
HATCH_B = 0x3A6CC0
SEAM = 0x9C9CA0
MIRROR = 0x161617
BUMPER = 0x2A2A2C


class Bus:
    L = 12.0; W = 2.60; H = 2.95; SKIRT = 0.30; WR = 0.50
    axles = []
    doors_r = []
    posts_l = []; posts_r = []
    DTOP = 2.62
    reds = []                 # scheme A red columns (u ranges, both sides + roof)
    roof_parts = []           # dicts: kind, u0, u1, inset, h0, h1 (relative to H)
    hatches = []
    sidedisp = None           # right side display (u0, u1) at the window top
    mirrors = True

    def __init__(self, view, livery="A", variant=None):
        self.view = view
        self.liv = livery
        self.var = variant or {}

    def c(self, pal, face):
        return rgb(pal[shade_key(self.view, face)])

    @property
    def disp(self):
        return LIME if self.liv == "J" else AMBER

    # ------------------------------------------------ geometry hooks
    def band_bot(self, u, right): return 1.15
    def win_bot(self, u, right): return self.band_bot(u, right) + 0.10
    def win_top(self, u, right): return 2.62
    def band_top(self, u, right): return 2.78
    def glass_range(self, right): return (0.0, self.L)

    # ------------------------------------------------ livery hooks
    def is_red(self, u):
        return self.liv == "A" and any_in(u, self.reds)

    def lower_pal(self, u, h, right):
        if self.liv == "A":
            return RED_A if self.is_red(u) else GREY
        if self.liv == "J":
            return WHITE if h >= self.var.get("grey_top", 0.86) else GREY_J
        return WHITE if h >= self.white_bot(u) else RED_B

    def white_bot(self, u):
        bb = self.band_bot(u, True)
        return bb - self.var.get("white_frac", 0.40) * (bb - self.SKIRT)

    def skirt_pal(self, u, right):
        if self.liv == "A":
            return RED_A_SK if self.is_red(u) else GREY_SK
        if self.liv == "J":
            return GREY_J_SK
        return RED_B_SK

    def upper_pal(self, u, right):
        if self.liv == "A":
            return RED_A if self.is_red(u) else GREY
        if self.liv == "J":
            return RED_J
        return BLUE

    def roof_pal(self, u, v):
        if self.liv == "A":
            return RED_A if self.is_red(u) else GREY
        if self.liv == "J":
            return ROOF_J
        return BLUE

    # ------------------------------------------------ side
    def side(self, face, u, h, pu, ph):
        right = face == "right"
        for ax in self.axles:
            du = u - ax
            r2 = du * du + (h - self.WR) ** 2
            if r2 < self.WR ** 2:
                if abs(du) <= pu / 2 and abs(h - self.WR) <= ph / 2:
                    return rgb(HUB)
                return rgb(TYRE)
            if r2 < (self.WR + 0.09) ** 2 and h >= self.SKIRT:
                return rgb(ARCH)
        if h < self.SKIRT:
            return None
        if right:
            for d0, d1 in self.doors_r:
                if d0 <= u < d1 and h < self.DTOP:
                    edge = u - d0 < pu or d1 - u <= pu or h < self.SKIRT + ph or h >= self.DTOP - ph
                    if d1 - d0 > 0.9 and abs(u - (d0 + d1) / 2) <= pu / 2:
                        edge = True
                    return rgb(FRAME) if edge else rgb(GLASS2)
        if u < pu * 0.9:
            r = self.front_corner(face, u, h, pu, ph, right)
            if r is not None:
                return r
        if u > self.L - pu * 0.9:
            r = self.rear_corner(face, u, h, pu, ph, right)
            if r is not None:
                return r
        if h < self.SKIRT + ph:
            return self.c(self.skirt_pal(u, right), face)
        bb, wb, wt, bt = self.band_bot(u, right), self.win_bot(u, right), self.win_top(u, right), self.band_top(u, right)
        if h >= bt:
            return self.c(self.upper_pal(u, right), face)
        if h >= bb:
            r = self.band_extra(face, u, h, pu, ph, right)
            if r is not None:
                return r
            g0, g1 = self.glass_range(right)
            if g0 <= u < g1 and wb <= h < wt:
                for p in (self.posts_r if right else self.posts_l):
                    if abs(u - p) <= pu / 2:
                        return rgb(BLACK)
                if right and self.sidedisp and self.sidedisp[0] <= u < self.sidedisp[1] and h >= wt - ph:
                    return rgb(self.disp)
                return rgb(GLASS)
            return rgb(BLACK)
        r = self.lower_extra(face, u, h, pu, ph, right)
        if r is not None:
            return r
        return self.c(self.lower_pal(u, h, right), face)

    def band_extra(self, face, u, h, pu, ph, right): return None
    def lower_extra(self, face, u, h, pu, ph, right): return None
    def front_corner(self, face, u, h, pu, ph, right): return None
    def rear_corner(self, face, u, h, pu, ph, right): return None

    def top(self, face, u, v, pu, pv):
        for a0, a1 in self.hatches:
            if a0 <= u < a1 and 0.85 <= v < self.W - 0.85:
                return rgb(HATCH_B if self.liv == "B" else HATCH)
        r = self.roof_extra(u, v, pu, pv)
        if r is not None:
            return r
        return self.c(self.roof_pal(u, v), face)

    def roof_extra(self, u, v, pu, pv): return None

    def tex(self):
        def t(face, a, b, pa, pb):
            if face in ("left", "right"):
                return self.side(face, a, b, pa, pb)
            if face == "top":
                return self.top(face, a, b, pa, pb)
            if face == "front":
                return self.front(face, a, b, pa, pb)
            return self.rear(face, a, b, pa, pb)
        return t

    # ------------------------------------------------ roof parts
    def part_tex(self, p):
        kind = p["kind"]
        u0, u1 = p["u0"], p["u1"]
        hb = self.H + p["h0"]
        ht = self.H + p["h1"]

        def t(face, a, b, pa, pb):
            if face in ("top", "left", "right"):
                u = a
            else:
                u = u0 if face == "front" else u1 - 1e-6
            if kind == "fair":
                # roof-line fairing: body colour, PID red bands run over it
                if face == "top" and self.liv == "A" and u < self.var.get("cap", 0.0):
                    return rgb(BLACK)
                if face in ("left", "right", "rear") and b < hb + pb and u > u0 + 0.3:
                    # dark seam under the fairing edge: makes the roof-line step read
                    return self.c(RED_A_SK if self.is_red(u) else GREY_SK, face)
                return self.c(self.roof_pal(u, 1.0), face)
            if kind == "ac":
                if face == "top" and abs(b - self.W / 2) < 0.30 and u0 + 0.25 <= a < u1 - 0.25:
                    return rgb(GRILLE)
                if self.liv == "A":
                    return self.c(RED_A if self.is_red(u) else AC_A, face)
                return self.c(AC_J if self.liv == "J" else AC_B, face)
            if kind == "hybrid":
                # MAN EfficientHybrid roof module: light box, dark grilles
                if face == "front" and b >= ht - 2.2 * pb:
                    return rgb(GRILLE)
                if face == "top" and (u0 + 0.15 <= a < u0 + 0.55 or u1 - 0.55 <= a < u1 - 0.15) \
                        and abs(b - self.W / 2) < 0.55:
                    return rgb(GRILLE)
                return self.c(AC_A if self.liv == "A" else AC_B, face)
            return self.c(GREY, face)
        return t

    def boxes(self):
        out = []
        if self.mirrors:
            out += self.mirror_boxes()
        out.append(Box(0, self.L, 0, self.W, 0, self.H, self.tex()))
        for p in self.roof_parts:
            i = p.get("inset", 0.0)
            out.append(Box(p["u0"], p["u1"], i, self.W - i, self.H + p["h0"], self.H + p["h1"], self.part_tex(p)))
        return out

    def mirror_boxes(self):
        def t(face, a, b, pa, pb):
            return rgb(MIRROR)
        W = self.W
        return [Box(-0.30, -0.05, -0.10, 0.02, 1.95, 2.55, t),
                Box(-0.30, -0.05, W - 0.02, W + 0.10, 1.95, 2.55, t)]


# ================================================================ new generation
class NewGen(Bus):
    """MAN Lion's City 12 (2018+), '12C' in PID use: NL 330 diesel and NL 280 /
    NL 330 EfficientHybrid.  12.185 x 2.55 m, wheelbase 6.005 m (overhangs
    2.78 / 3.40 m), doors 2-2-2.  Black one-piece face with the display, grey
    corner fins front and rear, a roof-line fairing over the front 60 % of
    the roof (the 'step' in side view) with the A/C unit at its rear end, and
    the engine-air louvres in the last window bay on the left (engine tower)."""
    L = 12.18; W = 2.60; H = 2.95; SKIRT = 0.30; WR = 0.50
    axles = [2.78, 8.78]
    doors_r = [(0.28, 1.55), (5.95, 7.20), (9.72, 10.92)]
    DTOP = 2.60
    posts_r = [3.05, 4.55, 8.45, 11.35]
    posts_l = [1.55, 3.05, 4.55, 6.05, 7.55, 9.05, 10.45]
    reds = [(1.55, 3.65), (7.25, 9.70)]
    sidedisp = (2.10, 3.30)
    hatches = [(10.20, 10.75)]
    louvre = (10.60, 11.95)          # engine tower louvres, left side, window band
    fair = (0.25, 7.20)

    def __init__(self, view, livery="A", variant=None):
        super().__init__(view, livery, variant)
        v = self.var
        fh = v.get("fair_h", 0.17)
        f0, f1 = self.fair
        self.roof_parts = [dict(kind="fair", u0=f0, u1=f1, inset=v.get("fair_inset", 0.10), h0=0.0, h1=fh),
                           dict(kind="ac", u0=f1 - 2.40, u1=f1 - 0.25, inset=0.45, h0=fh, h1=fh + v.get("ac_h", 0.10))]
        self.roof_parts += self.extra_parts()

    def extra_parts(self): return []

    def band_bot(self, u, right): return self.var.get("band_bot", 1.25)
    def win_bot(self, u, right): return self.band_bot(u, right) + 0.08
    def win_top(self, u, right): return 2.60
    def band_top(self, u, right): return 2.74

    def band_extra(self, face, u, h, pu, ph, right):
        if not right and self.louvre[0] <= u < self.louvre[1] and self.win_bot(u, right) <= h < self.win_top(u, right):
            k = int((h - self.win_bot(u, right)) / ph)
            return rgb(SLAT) if k % 2 == 1 else rgb(BLACK)
        return None

    def lower_extra(self, face, u, h, pu, ph, right):
        if self.liv == "A" and not self.is_red(u) and 0.72 <= h < 0.72 + ph:
            if (not right and any_in(u, [(4.6, 5.3), (9.9, 10.6)])) or (right and any_in(u, [(4.6, 5.3), (11.0, 11.7)])):
                return self.c(RED_A, face)             # red "pid" lettering
        return None

    def front_corner(self, face, u, h, pu, ph, right):
        # grey fin wraps the front corner, full height
        if h >= self.SKIRT + ph:
            return self.c(GREY, face) if self.liv == "A" else self.c(WHITE, face)
        return None

    def rear_corner(self, face, u, h, pu, ph, right):
        if h >= self.SKIRT + ph:
            return self.c(GREY, face) if self.liv == "A" else self.c(WHITE, face)
        return None

    def roof_extra(self, u, v, pu, pv):
        if u < pu * 0.9:
            return rgb(BLACK)                          # black face runs over the front edge
        return None

    def front(self, face, v, h, pv, ph):
        W = self.W
        left = v < W * 0.5            # v = 0 is the vehicle's left
        if h < self.SKIRT:
            return None
        if h < self.SKIRT + ph:
            return rgb(BUMPER)
        edge = v < pv * 0.9 or v > W - pv * 0.9
        fb = self.var.get("face_bot", 0.98)
        if h < fb:
            # lower front: grey, black grille between LED headlights, red on the left
            hl0 = self.var.get("hl_h", 0.62)
            if hl0 <= h < hl0 + ph and (v < pv or v > W - pv):
                return rgb(HEAD)
            if 0.45 <= h < 0.85 and 0.55 <= v < W - 0.55:
                if self.liv == "A" and h >= 0.85 - ph and v < W * 0.52:
                    return self.c(RED_A, face)
                return rgb(BLACK)
            if self.liv == "A" and v < 0.95 and h < 0.62:
                return self.c(RED_A, face)
            return self.c(GREY, face)
        # black face with the one-piece windscreen and the display
        if edge:
            return self.c(GREY, face) if self.liv == "A" else self.c(WHITE, face)
        dh = self.var.get("disp_h", 2.55)
        if dh <= h < dh + ph and 0.30 <= v < W - 0.30:
            return rgb(self.disp)
        if 1.12 <= h < dh - 0.10:
            if h >= dh - 0.10 - ph:
                return rgb(GLASS2)
            return rgb(GLASS)
        return rgb(BLACK)

    def rear(self, face, v, h, pv, ph):
        W = self.W
        if h < self.SKIRT:
            return None
        if h < self.SKIRT + ph:
            return rgb(BUMPER)
        edge = v < pv * 0.9 or v > W - pv * 0.9
        if edge:
            if 0.70 <= h < 1.30:
                return rgb(TAIL)
            return self.c(GREY, face)
        if h >= 1.62:
            if h >= self.H - ph:
                return self.c(GREY, face)
            if 2.42 <= h < 2.42 + ph and 1.15 <= v < 1.75:
                return rgb(self.disp)                      # rear route number
            if 1.62 + ph <= h < 2.35:
                return rgb(GLASS)
            return rgb(BLACK)
        if self.liv == "A" and 0.35 <= v < 1.35:
            return self.c(RED_A, face)
        return self.c(GREY, face)


class Hybrid(NewGen):
    """Lion's City 12 EfficientHybrid: the same body with the MAN hybrid roof
    module (ultracapacitor box) behind the A/C fairing, over the rear axle."""
    def extra_parts(self):
        v = self.var
        return [dict(kind="hybrid", u0=v.get("hy_u0", 7.45), u1=v.get("hy_u1", 9.55), inset=v.get("hy_inset", 0.45),
                     h0=0.0, h1=v.get("hy_h", 0.35))]


class IntercityLE(NewGen):
    """MAN Lion's Intercity LE 12 (LEU 330, 2020+): 12.28 x 2.55 x ~3.1 m,
    wheelbase 6.09 m, doors 1-2-0 (single-leaf front door, double door ahead
    of the rear axle; seznam-autobusu.cz 8431-8434),
    low-entry front with a deeper black band, raised rear with higher glass,
    engine louvres low in the rear corner (both sides), roof fairing + A/C."""
    L = 12.28; H = 2.98
    axles = [2.70, 8.79]
    doors_r = [(0.30, 1.20), (6.55, 7.75)]
    posts_r = [3.20, 4.90, 9.55, 10.90]
    posts_l = [1.60, 3.20, 4.90, 6.55, 8.10, 9.55, 10.90]
    reds = [(1.45, 3.60), (7.75, 9.55)]
    sidedisp = (2.05, 3.25)
    hatches = [(10.30, 10.85)]
    louvre = (99, 99)
    fair = (0.25, 6.60)

    def band_bot(self, u, right):
        return 0.98 if u < 1.95 else self.var.get("band_bot", 1.36)

    def win_bot(self, u, right):
        return self.band_bot(u, right) + 0.08

    def lower_extra(self, face, u, h, pu, ph, right):
        if 11.05 <= u < 11.95 and 0.55 <= h < 1.25:
            return rgb(BLACK) if int((h - 0.55) / ph) % 2 == 0 else self.c(GREY, face)   # louvres
        if self.liv == "A" and not self.is_red(u) and 0.72 <= h < 0.72 + ph and any_in(u, [(4.6, 5.3), (10.0, 10.6)]):
            return self.c(RED_A, face)
        return None


# ================================================================ old generation
class OldGen(Bus):
    """MAN Lion's City, 2004-2019 generation (A21/A26 platform).
    NL 293 / NL 283: 11.98 x 2.50 x 2.88 m, wheelbase 6.12 m (overhangs 2.61 /
    3.26 m), doors 2-2-2 (front overhang, middle, behind the rear axle).
    Large windscreen with the display behind it, black A-pillars, light mask
    with the black grille strip and corner headlights; engine grille low in
    the right rear corner."""
    L = 11.98; W = 2.55; H = 2.88; SKIRT = 0.30; WR = 0.50
    axles = [2.61, 8.73]
    doors_r = [(0.25, 1.50), (5.55, 6.85), (9.35, 10.60)]
    DTOP = 2.55
    posts_r = [2.90, 4.25, 8.10, 11.25]
    posts_l = [1.40, 2.90, 4.25, 5.60, 6.95, 8.30, 9.65, 10.95]
    reds = [(1.50, 3.70), (7.20, 9.60)]
    sidedisp = (1.95, 3.10)
    hatches = [(1.30, 1.85), (6.30, 6.85)]
    ac = (8.30, 10.90)
    engine_r = (10.95, 11.80)

    def __init__(self, view, livery="B", variant=None):
        super().__init__(view, livery, variant)
        a0, a1 = self.ac
        self.roof_parts = [dict(kind="ac", u0=a0, u1=a1, inset=0.30, h0=0.0, h1=self.var.get("ac_h", 0.22))]

    def band_bot(self, u, right): return self.var.get("band_bot", 1.28)
    def win_bot(self, u, right): return self.band_bot(u, right) + 0.08
    def win_top(self, u, right): return 2.55
    def band_top(self, u, right):
        # IDS JMK: the red roof-edge line is at least one full pixel
        return self.var.get("band_top", 2.60 if self.liv == "J" else 2.70)

    def lower_extra(self, face, u, h, pu, ph, right):
        e0, e1 = self.engine_r
        if right and e0 <= u < e1 and 0.55 <= h < 1.10:
            return rgb(GRILLE) if int((h - 0.55) / ph) % 2 == 0 else rgb(BLACK)
        if self.liv == "A" and not self.is_red(u) and 0.72 <= h < 0.72 + ph and any_in(u, self.logos()):
            return self.c(RED_A, face)
        return None

    def logos(self):
        return [(4.4, 5.1), (10.0, 10.7)]

    def front_corner(self, face, u, h, pu, ph, right):
        # the A-pillar: blue on the trikolora (1578), black on scheme A (9915)
        if h >= self.band_bot(u, right):
            return self.c(BLUE, face) if self.liv == "B" else rgb(BLACK)
        return None

    def front(self, face, v, h, pv, ph):
        W = self.W
        if h < self.SKIRT:
            return None
        if h < self.SKIRT + ph:
            return self.c({"B": RED_B_SK, "J": GREY_J_SK}.get(self.liv, GREY_SK), face)
        edge = v < pv * 0.9 or v > W - pv * 0.9
        mb = self.var.get("mask_top", 1.12)
        if h < mb:
            hl0 = 0.60
            if hl0 <= h < hl0 + ph and (v < pv or v > W - pv):
                return rgb(HEAD)
            if 0.52 <= h < 0.52 + ph and 0.60 <= v < W - 0.60:
                return rgb(BLACK)                      # grille strip
            if self.liv == "B":
                # white mask, red bumper and corners (a red 'U')
                if h < 0.52 or (edge and h < 0.85):
                    return self.c(RED_B, face)
                return self.c(WHITE, face)
            if self.liv == "J":
                # white mask, silver-grey bumper
                return self.c(GREY_J if h < 0.50 else WHITE, face)
            if v < 1.15 and h < 0.85:
                return self.c(RED_A, face)             # red block, vehicle's left
            return self.c(GREY, face)
        if h >= self.H - ph:
            return self.c({"B": BLUE, "J": RED_J}.get(self.liv, GREY), face)
        if edge:
            return self.c(BLUE, face) if self.liv == "B" else rgb(BLACK)
        if 2.52 <= h < 2.52 + ph and 0.30 <= v < W - 0.30:
            return rgb(self.disp)
        if mb + ph <= h < 2.45:
            if h >= 2.45 - ph:
                return rgb(GLASS2)
            return rgb(GLASS)
        return rgb(BLACK)

    def rear(self, face, v, h, pv, ph):
        W = self.W
        if h < self.SKIRT:
            return None
        if h < self.SKIRT + ph:
            return rgb(BUMPER)
        edge = v < pv * 0.9 or v > W - pv * 0.9
        if h >= self.H - ph:
            return self.c({"B": BLUE, "J": RED_J}.get(self.liv, GREY), face)
        if h >= 1.72:
            if 2.40 <= h < 2.40 + ph and 1.10 <= v < 1.70:
                return rgb(self.disp)
            if not edge and 1.72 + ph <= h < 2.60:
                return rgb(GLASS)
            return rgb(BLACK)
        if edge and 0.72 <= h < 1.22:
            return rgb(TAIL)
        if self.liv == "B":
            return self.c(WHITE if h >= 1.05 else RED_B, face)
        if self.liv == "J":
            return self.c(WHITE if h >= 0.86 else GREY_J, face)
        if 0.60 <= v < 1.50:
            return self.c(RED_A, face)
        return self.c(GREY, face)


class LionsCityL(OldGen):
    """MAN Lion's City L (NL 323), 14.70 x 2.55 x 2.88 m, 3 axles: front,
    drive axle 6.925 m behind it, tag axle 1.40 m further (overhangs 2.61 /
    3.77 m); doors 2-2-2 (front overhang, middle, behind the tag axle).
    Arriva City 9288-9295 (photos 9288, 9292, 9293, 9294, 9295): scheme A
    has three red columns per side (front arch, ahead of the tandem, around
    the tag axle); the A/C sits at the rear of the roof."""
    L = 14.70
    axles = [2.61, 9.53, 10.93]
    doors_r = [(0.25, 1.50), (6.10, 7.40), (11.85, 13.10)]
    posts_r = [2.95, 4.55, 8.60, 10.20, 13.85]
    posts_l = [1.40, 2.95, 4.50, 6.05, 7.60, 9.15, 10.70, 12.25, 13.75]
    reds = [(1.50, 3.85), (7.40, 8.90), (10.25, 11.70)]
    hatches = [(1.30, 1.85), (6.60, 7.15)]
    ac = (9.90, 12.70)
    engine_r = (13.45, 14.45)

    def logos(self):
        return [(4.4, 5.1), (12.2, 12.9)]


def stretched(cls, length):
    """the same body drawn `length` m long (all positions scaled)"""
    k = length / cls.L
    sc = lambda rr: [(a * k, b * k) for a, b in rr]
    attrs = dict(L=length, axles=[a * k for a in cls.axles], doors_r=sc(cls.doors_r), reds=sc(cls.reds),
                 posts_r=[a * k for a in cls.posts_r], posts_l=[a * k for a in cls.posts_l],
                 hatches=sc(cls.hatches))
    for n in ("ac", "engine_r", "louvre", "fair", "sidedisp"):
        v = getattr(cls, n, None)
        if v:
            attrs[n] = (v[0] * k, v[1] * k)
    if hasattr(cls, "logos"):
        base_logos = cls.logos
        attrs["logos"] = lambda self: [(a * k, b * k) for a, b in base_logos(self)]
    return type(cls.__name__ + "_%d" % round(length * 100), (cls,), attrs)


MODELS = {"c12": NewGen, "hybrid": Hybrid, "ile": IntercityLE, "nl293": OldGen, "l": LionsCityL}


def build_tile(cls, d, livery, variant):
    L, W = cls.L, cls.W
    c = centre(d)
    v0 = View(d, MPU, KH, (0, 0))
    o = c - v0.Au * (L / 2) - v0.Av * (W / 2)
    view = View(d, MPU, KH, tuple(o))
    bus = cls(view, livery, variant)
    return render(view, bus.boxes())


def build_row(cls, livery, variant=None, norm=True, label=""):
    row = [build_tile(cls, d, livery, variant) for d in DIRS]
    if norm:
        row = normalize_rows([row], threshold=2, report=False, label=label)[0]
    return row


# ================================================================ output
V12 = dict(fair_h=0.28, fair_inset=0.0, ac_h=0.14, face_bot=0.88)      # user's pick: 12C v2
VL = dict(band_bot=1.20, white_frac=0.47, ac_h=0.32)                    # user's pick: L v3
FAMILIES = {
    # family dir (repo-relative): [(livery slug, class, livery code, variant)]
    "vehicle-bus/praha/lions_city_12c": [("pidsedocervena", NewGen, "A", V12)],
    "vehicle-bus/praha/lions_city_12c_hybrid": [("pidsedocervena", Hybrid, "A", V12)],
    "vehicle-bus/praha/lions_city_l": [("pidcervenomodrobila", LionsCityL, "B", VL),
                                       ("pidsedocervena", LionsCityL, "A", VL)],
    "vehicle-bus/praha/lions_intercity_le_12": [("pidsedocervena", IntercityLE, "A", None)],
    "vehicle-bus/praha/lions_city_nl293": [("pidcervenomodrobila", OldGen, "B", None)],
    "vehicle-bus/brno/lions_city_nl283": [("idsjmk", OldGen, "J", None)],
}


def save_rows(rows, path):
    out = np.zeros((128 * len(rows), 1024, 3), dtype=np.uint8)
    out[:, :] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    Image.fromarray(out).save(path)
    return out


def preview(sheet, path, z=4, bg=(96, 104, 96)):
    a = sheet.copy()
    a[np.all(a == np.array(T), axis=2)] = bg
    im = Image.fromarray(a)
    im.resize((im.width * z, im.height * z), Image.NEAREST).save(path)


def main():
    args = sys.argv[1:]
    pv = None
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
        os.makedirs(pv, exist_ok=True)
    for fam, livs in FAMILIES.items():
        name = fam.split("/")[-1]
        if args and name not in args:
            continue
        sd = os.path.join(REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        for color, cls, liv, var in livs:
            sheet = save_rows([build_row(cls, liv, var)], os.path.join(sd, color + ".png"))
            if pv:
                preview(sheet, os.path.join(pv, f"{name}-{color}.png"))
            print(f"{fam}/sprites/{color}.png")


if __name__ == "__main__":
    main()
