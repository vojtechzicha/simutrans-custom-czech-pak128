#!/usr/bin/env python3
"""Render the sprite sheets for the procedurally drawn supermarket industries.

Reads an ``industry.yaml`` (see CLAUDE.md, "Industries") and writes one PNG per
object into ``<set dir>/sprites/<sprite>.png``. Every object is a city
consumer with four layouts (rotations) and two seasons, laid out as::

    row  season * 4 + layout
    col  tile y * w + x inside that layout (w = the layout's x size)

Layout 0 has the shop front facing south (+y). When the map is rotated
clockwise Simutrans turns layout L into L - 1 (``gebaeude_t::rotate90``), so
layout L + 1 is layout L turned a quarter anticlockwise: the front faces east
in layout 1, north in 2 and west in 3.

The art is ray-cast from axis-aligned boxes and ellipsoids (halls, cars, lamps,
trees) standing on a textured ground plane, supersampled 3x3 and lit like
pak128: flat tops x1.0, south faces x0.835, east faces x0.61. Every sample is
assigned to the tile its surface stands on; since anything that can hide a
surface stands further south or east, Simutrans's back-to-front tile order
reassembles the building exactly. Signs are pixel-font bitmaps stamped onto
walls and roofs at screen resolution in world orientation, so they read left to
right in every layout. Shop glazing uses the lit-window special colours and
sign lettering the always-lit lamp colours, so both glow at night.

Needs numpy and Pillow.

Usage:
    python tools/gen_shops.py industry-city/supermarkety
    python tools/gen_shops.py industry-city/supermarkety --only lidl --preview previews/
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

TILE = 128
SS = 3                      # supersampling per axis
KEY = (231, 255, 255)       # makeobj transparent colour
LAYOUTS = 4
SEASONS = 2

# Simutrans special colours (makeobj image_t::rgbtab) plus the transparent key.
# A shaded pixel that lands on one by accident is nudged by one step; pixels
# painted with one on purpose (glass, lamps) are kept exact.
SPECIALS = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}
# lit at night (display_night_lights): window glass
GLASS = 0x57656F            # slate by day, warm yellow at night
GLASS_LIGHT = 0x7F9BF1      # pale blue by day, cool white at night
GLASS_DARK = 0x4D4D4D       # dark grey by day, yellow at night
# always lit: sign lettering and lamps
LAMP_YELLOW = 0xFFFF53
LAMP_RED = 0xFF211D
LAMP_GREEN = 0x01DD01
LAMP_WHITE = 0xE3E3FF       # near white by day, warm white at night
LAMP_BLUE = 0x0101FF

# pak128 lighting (as tools/gen_platforms.py): sun from the south, 60 degrees up
LIGHT = np.array([0.0, 0.5, 0.866])
AMB, DIF = 0.61, 0.45
F_TOP, F_EAST, F_SOUTH = 0, 1, 2
SHADE = {F_TOP: 1.0, F_EAST: AMB, F_SOUTH: AMB + DIF * 0.5}
TILE_W = 90.5               # tile side in world pixels
Z_W = 1 / 0.866             # screen height px -> world px

# pak128.CS temperate grass and snow ground (texture-climate.png statistics)
GRASS = (78, 136, 56)
GRASS_VAR = (15, 11, 5)
SNOW = (207, 207, 220)
SNOW_VAR = (4, 4, 5)

M = 1 / 24                  # one metre in tile units (a tile is 16 carunits of 1.5 m)
PXM = 3.27                  # one metre of height in screen px (90.5 px / 24 m * 0.866)


def hexrgb(v):
    if isinstance(v, (tuple, list, np.ndarray)):
        return tuple(int(c) for c in v[:3])
    if isinstance(v, str):
        v = int(v.lstrip("#"), 16)
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def rgb(t):
    return np.array(hexrgb(t) if isinstance(t, (int, str)) else t, float)


def hash2(ix, iy, seed=0):
    """Deterministic pseudo random in [0, 1) per integer cell."""
    with np.errstate(over="ignore"):
        h = (np.asarray(ix, np.int64) * 73856093) ^ (np.asarray(iy, np.int64) * 19349663) ^ np.int64(seed * 83492791)
        h = (h ^ (h >> 13)) * np.int64(1274126177)
        h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65536.0


def grid_lines(x, period, width):
    f = np.mod(x, period)
    return (f < width) | (f > period - 1e-4)


# --- pixel fonts ------------------------------------------------------------------------
# Bold 7-row font for shop signs (caps height 7, lowercase x-height 5) and a thin
# 5-row caps font for sub-labels. '#' = ink.

FONT7 = {
    "A": [".####.", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    "B": ["#####.", "##..##", "##..##", "#####.", "##..##", "##..##", "#####."],
    "C": [".####.", "##..##", "##....", "##....", "##....", "##..##", ".####."],
    "D": ["####..", "##.##.", "##..##", "##..##", "##..##", "##.##.", "####.."],
    "E": ["#####", "##...", "##...", "####.", "##...", "##...", "#####"],
    "G": [".####.", "##..##", "##....", "##.###", "##..##", "##..##", ".#####"],
    "H": ["##..##", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    "I": ["##", "##", "##", "##", "##", "##", "##"],
    "K": ["##..##", "##.##.", "####..", "###...", "####..", "##.##.", "##..##"],
    "L": ["##...", "##...", "##...", "##...", "##...", "##...", "#####"],
    "M": ["##...##", "###.###", "#######", "##.#.##", "##...##", "##...##", "##...##"],
    "N": ["##..##", "###.##", "######", "##.###", "##..##", "##..##", "##..##"],
    "O": [".####.", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    "P": ["#####.", "##..##", "##..##", "#####.", "##....", "##....", "##...."],
    "R": ["#####.", "##..##", "##..##", "#####.", "####..", "##.##.", "##..##"],
    "S": [".####.", "##..##", "##....", ".####.", "....##", "##..##", ".####."],
    "T": ["######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
    "U": ["##..##", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    "X": ["##..##", "##..##", ".####.", "..##..", ".####.", "##..##", "##..##"],
    "Y": ["##..##", "##..##", ".####.", "..##..", "..##..", "..##..", "..##.."],
    "Z": ["######", "....##", "...##.", "..##..", ".##...", "##....", "######"],
    "a": ["......", "......", ".####.", "....##", ".#####", "##..##", ".#####"],
    "b": ["##....", "##....", "#####.", "##..##", "##..##", "##..##", "#####."],
    "c": ["......", "......", ".####.", "##..##", "##....", "##..##", ".####."],
    "d": ["....##", "....##", ".#####", "##..##", "##..##", "##..##", ".#####"],
    "e": ["......", "......", ".####.", "##..##", "######", "##....", ".####."],
    "f": ["..###", ".##..", "####.", ".##..", ".##..", ".##..", ".##.."],
    "h": ["##....", "##....", "#####.", "##..##", "##..##", "##..##", "##..##"],
    "k": ["##....", "##....", "##..##", "##.##.", "####..", "##.##.", "##..##"],
    "l": ["##", "##", "##", "##", "##", "##", "##"],
    "m": [".......", ".......", "######.", "##.#.##", "##.#.##", "##.#.##", "##.#.##"],
    "n": ["......", "......", "#####.", "##..##", "##..##", "##..##", "##..##"],
    "o": ["......", "......", ".####.", "##..##", "##..##", "##..##", ".####."],
    "p": ["......", "......", "#####.", "##..##", "#####.", "##....", "##...."],
    "r": [".....", ".....", "##.##", "####.", "##...", "##...", "##..."],
    "s": ["......", "......", ".#####", "##....", ".####.", "....##", "#####."],
    "t": [".##..", ".##..", "#####", ".##..", ".##..", ".##..", "..###"],
    "u": ["......", "......", "##..##", "##..##", "##..##", "##..##", ".#####"],
    "x": ["......", "......", "##..##", ".####.", "..##..", ".####.", "##..##"],
    "y": ["......", "......", "##..##", "##..##", ".#####", "....##", "#####."],
    "z": ["......", "......", "######", "...##.", "..##..", ".##...", "######"],
    "ž": [".#..#.", "..##..", "######", "...##.", "..##..", ".##...", "######"],
    " ": ["..", "..", "..", "..", "..", "..", ".."],
    "&": [".###..", "##.##.", ".###..", ".##.#.", "##.###", "##.##.", ".##.##"],
}

FONT5 = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["#", "#", "#", "#", "#"],
    "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."],
    "P": ["##.", "#.#", "##.", "#..", "#.."],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "Z": ["###", "..#", ".#.", "#..", "###"],
    " ": [".", ".", ".", ".", "."],
    "&": [".#.", "#.#", ".#.", "#.#", ".##"],
}


def text_mask(text, font, spacing=1):
    """Boolean ink mask of a string set in one of the fonts."""
    glyphs = [np.array([[ch == "#" for ch in row] for row in font[c]], bool) for c in text]
    h = len(next(iter(font.values())))
    w = sum(g.shape[1] for g in glyphs) + spacing * (len(glyphs) - 1)
    out = np.zeros((h, max(w, 1)), bool)
    x = 0
    for g in glyphs:
        out[:, x:x + g.shape[1]] = g
        x += g.shape[1] + spacing
    return out


class Bitmap:
    """RGB bitmap with coverage, used for signs. Colour values that are
    Simutrans specials stay exact when stamped (lamps, glass)."""

    def __init__(self, w, h, fill=None):
        self.rgb = np.zeros((h, w, 3), np.int32)
        self.a = np.zeros((h, w), bool)
        if fill is not None:
            self.rgb[:] = hexrgb(fill)
            self.a[:] = True

    @property
    def w(self):
        return self.rgb.shape[1]

    @property
    def h(self):
        return self.rgb.shape[0]

    def rect(self, x0, y0, x1, y1, color):
        """Fill [x0, x1) x [y0, y1)."""
        x0, y0 = max(0, x0), max(0, y0)
        self.rgb[y0:y1, x0:x1] = hexrgb(color)
        self.a[y0:y1, x0:x1] = True
        return self

    def mask(self, m, x, y, color):
        h, w = m.shape
        sub = np.zeros((self.h, self.w), bool)
        ys, xs = np.nonzero(m)
        ys, xs = ys + y, xs + x
        ok = (ys >= 0) & (ys < self.h) & (xs >= 0) & (xs < self.w)
        sub[ys[ok], xs[ok]] = True
        self.rgb[sub] = hexrgb(color)
        self.a[sub] = True
        return self

    def text(self, s, font, color, x=None, y=None, spacing=1):
        m = text_mask(s, font, spacing)
        if x is None:
            x = (self.w - m.shape[1]) // 2
        if y is None:
            y = (self.h - m.shape[0]) // 2
        return self.mask(m, x, y, color)

    def disc(self, cx, cy, r, color):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        return self.mask_full((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= r * r, color)

    def mask_full(self, m, color):
        self.rgb[m] = hexrgb(color)
        self.a[m] = True
        return self

    def paste(self, other, x, y):
        ys, xs = np.nonzero(other.a)
        ty, tx = ys + y, xs + x
        ok = (ty >= 0) & (ty < self.h) & (tx >= 0) & (tx < self.w)
        self.rgb[ty[ok], tx[ok]] = other.rgb[ys[ok], xs[ok]]
        self.a[ty[ok], tx[ok]] = True
        return self


# --- scene --------------------------------------------------------------------------------

# local faces: 0 top, 1 +x, 2 -x, 3 +y (front in layout 0), 4 -y
L_TOP, L_PX, L_NX, L_PY, L_NY = range(5)
FACE_NORMAL = {L_PX: (1, 0), L_NX: (-1, 0), L_PY: (0, 1), L_NY: (0, -1)}
NORMAL_FACE = {v: k for k, v in FACE_NORMAL.items()}


@dataclass
class Sign:
    """A bitmap on one wall face of a box. `at` is the local along-wall
    coordinate of the bitmap centre, `top` the z of its top row."""
    bitmap: Bitmap
    at: float
    top: float


@dataclass
class Box:
    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float
    mat: object                 # material (callable) evaluated per sample
    signs: dict = field(default_factory=dict)   # local face -> [Sign]
    roof: object = None         # RoofLogo on the top face
    shape: str = "box"          # "box" | "ellipsoid"


@dataclass
class RoofLogo:
    """A bitmap painted flat on a roof, in world orientation so it reads left
    to right, scaled to cover `fill` of the roof's length or width."""
    bitmap: Bitmap
    fill: float


class Ctx:
    """Per-sample inputs handed to a material."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def rotate_box(b: Box, h: float) -> Box:
    """One engine rotation R: (x, y) -> (h - y, x) inside a footprint of height h."""
    signs = {}
    for f, lst in b.signs.items():
        nx, ny = FACE_NORMAL[f]
        nf = NORMAL_FACE[(-ny, nx)]
        # along-wall coordinate: x for +-y faces, y for +-x faces. Under R the
        # wall's along axis y -> new x, x -> new y (h - y for the new x).
        if f in (L_PX, L_NX):          # along y  -> new face is +-y, along new x = h - y
            signs[nf] = [Sign(s.bitmap, h - s.at, s.top) for s in lst]
        else:                           # along x  -> new face is +-x, along new y = x
            signs[nf] = [Sign(s.bitmap, s.at, s.top) for s in lst]
    return Box(h - b.y1, h - b.y0, b.x0, b.x1, b.z0, b.z1, b.mat, signs, b.roof, b.shape)


def world_boxes(boxes, dims, layout):
    """Boxes of the layout-0 scene placed for `layout` (world = R^(4-L) local)."""
    w, h = dims
    out = list(boxes)
    for _ in range((LAYOUTS - layout) % LAYOUTS):
        out = [rotate_box(b, h) for b in out]
        w, h = h, w
    return out, (w, h)


def to_local(u, v, dims, layout):
    """World coords of `layout` back to layout-0 local coords (apply R L times)."""
    w, h = dims
    x, y = u, v
    for _ in range(layout):
        x, y = h - y, x
        w, h = h, w
    return x, y


def normal_to_local(nx, ny, layout):
    for _ in range(layout):
        nx, ny = -ny, nx
    return nx, ny


# --- ray casting ------------------------------------------------------------------------------

class Render:
    """Ray-cast one layout of a scene into a supersampled canvas."""

    def __init__(self, boxes, dims, layout, ground):
        self.boxes, self.dims = world_boxes(boxes, dims, layout)
        self.local_dims = dims
        self.layout = layout
        self.ground = ground
        w, h = self.dims
        self.W = TILE // 2 * (w + h)
        self.H = TILE // 4 * (w + h) + TILE // 2
        self.ox = TILE // 2 * (h - 1)
        n_w, n_h = self.W * SS, self.H * SS
        jj, ii = np.mgrid[0:n_h, 0:n_w]
        sx = (ii + 0.5) / SS
        sy = (jj + 0.5) / SS
        X = (sx - self.ox - 64.0) / 64.0
        Y = (sy - 64.5) / 32.0
        self.a = (Y + X) / 2            # ground u of the ray
        self.b = (Y - X) / 2            # ground v of the ray
        self.sx, self.sy = sx, sy

    def cast(self):
        a, b = self.a, self.b
        w, h = self.dims
        on_ground = (a >= 0) & (a < w) & (b >= 0) & (b < h)
        best = np.where(on_ground, 0.0, -1e9)
        idx = np.where(on_ground, -1, -2).astype(np.int32)     # -1 ground, -2 nothing
        face = np.zeros(a.shape, np.int8)
        nrm = np.zeros(a.shape + (3,), np.float32)
        nrm[..., 2] = 1
        for k, bx in enumerate(self.boxes):
            # screen bounding box of the box -> sample window
            us = (bx.x0, bx.x1)
            vs = (bx.y0, bx.y1)
            xs = [64 * (u - v) + self.ox + 64 for u in us for v in vs]
            ys_lo = min(32 * (u + v) + 64.5 for u in us for v in vs) - bx.z1
            ys_hi = max(32 * (u + v) + 64.5 for u in us for v in vs) - bx.z0
            i0 = max(0, int(np.floor(min(xs) * SS)) - 1)
            i1 = min(a.shape[1], int(np.ceil(max(xs) * SS)) + 1)
            j0 = max(0, int(np.floor(ys_lo * SS)) - 1)
            j1 = min(a.shape[0], int(np.ceil(ys_hi * SS)) + 1)
            if i0 >= i1 or j0 >= j1:
                continue
            sa = a[j0:j1, i0:i1]
            sb = b[j0:j1, i0:i1]
            if bx.shape == "box":
                zu1 = 64 * (bx.x1 - sa)
                zv1 = 64 * (bx.y1 - sb)
                zhi = np.minimum(np.minimum(zu1, zv1), bx.z1)
                zlo = np.maximum(np.maximum(64 * (bx.x0 - sa), 64 * (bx.y0 - sb)), bx.z0)
                hit = (zlo <= zhi) & (zhi > best[j0:j1, i0:i1])
                if not hit.any():
                    continue
                f = np.where(zhi == bx.z1, F_TOP, np.where(zhi == zu1, F_EAST, F_SOUTH))
                n = np.zeros(sa.shape + (3,), np.float32)
                n[..., 2] = f == F_TOP
                n[..., 0] = f == F_EAST
                n[..., 1] = f == F_SOUTH
            else:
                # ellipsoid centre c, radii r (u, v in tiles, z in px): the ray is
                # (a + t/64, b + t/64, t); solve the quadratic in t
                cu, cv, cz = (bx.x0 + bx.x1) / 2, (bx.y0 + bx.y1) / 2, (bx.z0 + bx.z1) / 2
                ru, rv, rz = (bx.x1 - bx.x0) / 2, (bx.y1 - bx.y0) / 2, (bx.z1 - bx.z0) / 2
                du, dv = (sa - cu) / ru, (sb - cv) / rv
                ku, kv, kz = 1 / (64 * ru), 1 / (64 * rv), 1 / rz
                A = ku * ku + kv * kv + kz * kz
                B = 2 * (du * ku + dv * kv - cz * kz * kz)
                C = du * du + dv * dv + (cz * kz) ** 2 - 1
                disc = B * B - 4 * A * C
                ok = disc >= 0
                zhi = np.where(ok, (-B + np.sqrt(np.maximum(disc, 0))) / (2 * A), -1e9)
                zhi = np.minimum(zhi, bx.z1)
                hit = ok & (zhi >= max(bx.z0, 0)) & (zhi > best[j0:j1, i0:i1])
                if not hit.any():
                    continue
                pu = (sa + zhi / 64 - cu) / ru
                pv = (sb + zhi / 64 - cv) / rv
                pz = (zhi - cz) / rz
                n = np.stack([pu / (ru * TILE_W), pv / (rv * TILE_W), pz / (rz * Z_W)], -1)
                n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
                f = np.full(sa.shape, F_TOP, np.int8)
            win = (slice(j0, j1), slice(i0, i1))
            best[win] = np.where(hit, zhi, best[win])
            idx[win] = np.where(hit, k, idx[win])
            face[win] = np.where(hit, f, face[win])
            nrm[win] = np.where(hit[..., None], n, nrm[win])
        self.z = np.maximum(best, 0)
        self.idx, self.face, self.nrm = idx, face, nrm
        self.u = a + self.z / 64
        self.v = b + self.z / 64
        return self

    def shade(self, snow, seed=5):
        """Albedo x light per sample; returns rgb (float), special code (int, -1)."""
        n_h, n_w = self.idx.shape
        col = np.zeros((n_h, n_w, 3))
        spec = np.full((n_h, n_w), -1, np.int64)
        rng = np.random.default_rng(seed)
        n1 = rng.random((self.H, self.W)).repeat(SS, 0).repeat(SS, 1)
        n2 = rng.random((self.H, self.W)).repeat(SS, 0).repeat(SS, 1)
        lx, ly = to_local(self.u, self.v, self.dims, self.layout)
        # local face of every sample (walls only; tops stay top)
        lface = np.full(self.idx.shape, L_TOP, np.int8)
        for wf, (nu, nv) in ((F_EAST, (1, 0)), (F_SOUTH, (0, 1))):
            lnx, lny = normal_to_local(nu, nv, self.layout)
            lface[self.face == wf] = NORMAL_FACE[(lnx, lny)]
        light = AMB + DIF * np.clip(self.nrm @ LIGHT, 0, 1)
        light = np.where(self.face == F_EAST, SHADE[F_EAST], np.where(self.face == F_SOUTH, SHADE[F_SOUTH], light))

        groups = [(-1, self.ground)] + [(k, b.mat) for k, b in enumerate(self.boxes)]
        for k, mat in groups:
            sel = self.idx == k
            if not sel.any():
                continue
            box = self.boxes[k] if k >= 0 else None
            ctx = Ctx(x=lx[sel], y=ly[sel], z=self.z[sel], face=lface[sel], n1=n1[sel], n2=n2[sel],
                      snow=snow, box=box, nz=self.nrm[sel][:, 2])
            albedo, sp = mat(ctx)
            col[sel] = albedo
            if sp is not None:
                spec[sel] = sp
        col *= light[..., None]
        self.col, self.spec = col, spec
        return self

    def tiles(self):
        """Tile index (ty * w + tx) of every sample's surface, -1 for none."""
        w, h = self.dims
        eps = 1e-4
        u = np.where(self.face == F_EAST, self.u - eps, self.u)
        v = np.where(self.face == F_SOUTH, self.v - eps, self.v)
        tx = np.clip(np.floor(u), 0, w - 1).astype(int)
        ty = np.clip(np.floor(v), 0, h - 1).astype(int)
        t = ty * w + tx
        return np.where(self.idx == -2, -1, t)


def downsample(r: Render):
    """Canvas pixels: colour, coverage, owner tile, special code."""
    H, W = r.H, r.W
    t = r.tiles()
    hitm = t >= 0
    kk = hitm.reshape(H, SS, W, SS)
    cnt = kk.sum(axis=(1, 3))
    mask = cnt * 2 >= SS * SS
    tot = (r.col * hitm[..., None]).reshape(H, SS, W, SS, 3).sum(axis=(1, 3))
    out = tot / np.maximum(cnt, 1)[..., None]
    # owner tile: the majority tile of the covered samples
    ntiles = r.dims[0] * r.dims[1]
    tb = t.reshape(H, SS, W, SS)
    votes = np.stack([(tb == k).sum(axis=(1, 3)) for k in range(ntiles)], -1)
    owner = votes.argmax(-1)
    # special colours: majority special of the pixel wins outright
    sp = r.spec.reshape(H, SS, W, SS)
    spec = np.full((H, W), -1, np.int64)
    for code in np.unique(r.spec[r.spec >= 0]):
        c = (sp == code).sum(axis=(1, 3))
        spec = np.where((c * 2 > cnt) & (cnt > 0), code, spec)
    return out, mask, owner, spec


def stamp_decals(r: Render, out, spec):
    """Signs on walls and logos on roofs, one bitmap pixel per screen pixel
    (walls) or per plan cell (roofs), sampled at each pixel's centre sample."""
    c = SS // 2
    idx = r.idx[c::SS, c::SS]
    face = r.face[c::SS, c::SS]
    u = r.u[c::SS, c::SS]
    v = r.v[c::SS, c::SS]
    z = r.z[c::SS, c::SS]
    for k, bx in enumerate(r.boxes):
        on = idx == k
        if not on.any():
            continue
        for lf, lst in bx.signs.items():
            nx, ny = FACE_NORMAL[lf]
            # sign faces are already in world orientation; only +x / +y faces are visible
            if (nx, ny) == (1, 0):
                wf = F_EAST
            elif (nx, ny) == (0, 1):
                wf = F_SOUTH
            else:
                continue
            sel = on & (face == wf)
            if not sel.any():
                continue
            for s in lst:
                bm = s.bitmap
                if wf == F_SOUTH:      # wall along u, text runs +u
                    col = np.floor((u - s.at) * 64 + bm.w / 2).astype(int)
                else:                  # wall along v, text runs -v
                    col = np.floor(-(v - s.at) * 64 + bm.w / 2).astype(int)
                row = np.floor(s.top - z).astype(int)
                ok = sel & (col >= 0) & (col < bm.w) & (row >= 0) & (row < bm.h)
                if not ok.any():
                    continue
                cc, rr = col[ok], row[ok]
                inked = bm.a[rr, cc]
                ys, xs = np.nonzero(ok)
                ys, xs = ys[inked], xs[inked]
                vals = bm.rgb[rr[inked], cc[inked]]
                code = (vals[:, 0] << 16) | (vals[:, 1] << 8) | vals[:, 2]
                special = np.isin(code, list(SPECIALS))
                shade = SHADE[wf]
                out[ys, xs] = np.where(special[:, None], vals, vals * shade)
                spec[ys, xs] = np.where(special, code, -1)
        if bx.roof is not None:
            sel = on & (face == F_TOP)
            if not sel.any():
                continue
            lg = bx.roof
            bm = lg.bitmap
            cu, cv = (bx.x0 + bx.x1) / 2, (bx.y0 + bx.y1) / 2
            lu, lv = bx.x1 - bx.x0, bx.y1 - bx.y0
            long_u = lu >= lv
            big, small = (lu, lv) if long_u else (lv, lu)
            px = lg.fill * min(big / bm.w, small / bm.h)
            if long_u:     # baseline along +u, letters up along -v
                col = np.floor((u - cu) / px + bm.w / 2).astype(int)
                row = np.floor((v - cv) / px + bm.h / 2).astype(int)
            else:          # baseline along -v, letters up along -u
                col = np.floor(-(v - cv) / px + bm.w / 2).astype(int)
                row = np.floor((u - cu) / px + bm.h / 2).astype(int)
            ok = sel & (col >= 0) & (col < bm.w) & (row >= 0) & (row < bm.h)
            if not ok.any():
                continue
            cc, rr = col[ok], row[ok]
            inked = bm.a[rr, cc]
            ys, xs = np.nonzero(ok)
            ys, xs = ys[inked], xs[inked]
            out[ys, xs] = bm.rgb[rr[inked], cc[inked]]
            spec[ys, xs] = -1
    return out, spec


def to_rgb_image(out, mask, spec):
    q = np.clip(np.rint(out), 0, 255).astype(np.int64)
    val = (q[..., 0] << 16) | (q[..., 1] << 8) | q[..., 2]
    # accidental specials are nudged one step; intended ones set exactly
    bad = np.isin(val, list(SPECIALS)) & mask & (spec < 0)
    q[..., 2] = np.where(bad, np.where(q[..., 2] > 0, q[..., 2] - 1, 1), q[..., 2])
    q = np.where((spec >= 0)[..., None], np.stack([(spec >> 16) & 255, (spec >> 8) & 255, spec & 255], -1), q)
    img = np.empty(out.shape, np.uint8)
    img[:] = KEY
    img[mask] = q[mask]
    return img


def render_layout(scene, layout, snow):
    """(canvas image, owner tile per pixel, coverage mask, world dims)."""
    r = Render(scene.boxes, scene.dims, layout, scene.ground).cast().shade(snow)
    out, mask, owner, spec = downsample(r)
    out, spec = stamp_decals(r, out, spec)
    return to_rgb_image(out, mask, spec), owner, mask, r


def split_tiles(img, owner, mask, r):
    """128x128 tile images of one layout, indexed ty * w + tx."""
    w, h = r.dims
    tiles = []
    for ty in range(h):
        for tx in range(w):
            k = ty * w + tx
            x0 = r.ox + 64 * (tx - ty)
            y0 = 32 * (tx + ty)
            cell = np.empty((TILE, TILE, 3), np.uint8)
            cell[:] = KEY
            sub_img = img[y0:y0 + TILE, x0:x0 + TILE]
            sub = (owner[y0:y0 + TILE, x0:x0 + TILE] == k) & mask[y0:y0 + TILE, x0:x0 + TILE]
            cell[sub] = sub_img[sub]
            tiles.append(cell)
    return tiles


class Scene:
    def __init__(self, dims, boxes, ground):
        self.dims = dims
        self.boxes = boxes
        self.ground = ground


def build_sheet(scene):
    ntiles = scene.dims[0] * scene.dims[1]
    sheet = np.empty((TILE * LAYOUTS * SEASONS, TILE * ntiles, 3), np.uint8)
    sheet[:] = KEY
    views = {}
    for season in range(SEASONS):
        for layout in range(LAYOUTS):
            img, owner, mask, r = render_layout(scene, layout, snow=season == 1)
            views[(season, layout)] = img
            for k, cell in enumerate(split_tiles(img, owner, mask, r)):
                row = season * LAYOUTS + layout
                sheet[row * TILE:(row + 1) * TILE, k * TILE:(k + 1) * TILE] = cell
    return Image.fromarray(sheet, "RGB"), views


# --- materials ----------------------------------------------------------------------------------
# A material maps a Ctx (per-sample local x, y, z, local face, noise n1/n2,
# snow flag, the box) to (albedo N x 3, special code N or None).

def noisy(base, n, var):
    v = np.array(var if isinstance(var, (tuple, list)) else (var,) * 3, float)
    return rgb(base) + (n[:, None] - 0.5) * v


def snow_col(ctx):
    return noisy(SNOW, ctx.n2, SNOW_VAR) + 18


def with_snow(ctx, col, cover=1.0):
    """Snow on the upward faces (tops, and the upper half of ellipsoids)."""
    if not ctx.snow:
        return col
    up = (ctx.face == L_TOP) & (ctx.nz > 0.55)
    if cover < 1:
        up &= ctx.n1 < cover
    return np.where(up[:, None], snow_col(ctx), col)


def solid(color, var=6, snow=1.0):
    def m(ctx):
        col = noisy(color, ctx.n1, var)
        return (with_snow(ctx, col, snow) if snow else col), None
    return m


def along(ctx):
    """Coordinate along a wall: x on the +-y faces, y on the +-x faces."""
    return np.where((ctx.face == L_PY) | (ctx.face == L_NY), ctx.x, ctx.y)


def roof_membrane(ctx, base=(168, 168, 164)):
    col = noisy(base, ctx.n1, 8)
    seam = grid_lines(ctx.x, 0.06, 0.006)
    return np.where(seam[:, None], col - 10, col)


class Facade:
    """Material for a building body: cladding with panel seams and a dark
    plinth, per local face a list of parts (a0, a1, z0, z1, painter) drawn over
    it, and a membrane roof on top."""

    def __init__(self, cladding, roof=(168, 168, 164), seams=0.05, plinth=(96, 96, 98)):
        self.cladding = cladding
        self.roof = roof
        self.seams = seams
        self.plinth = plinth
        self.parts = {f: [] for f in (L_PX, L_NX, L_PY, L_NY)}

    def add(self, faces, a0, a1, z0, z1, painter):
        for f in faces:
            self.parts[f].append((a0, a1, z0, z1, painter))
        return self

    def __call__(self, ctx):
        n = len(ctx.x)
        col = noisy(self.cladding, ctx.n1, 5)
        al = along(ctx)
        if self.seams:
            col = np.where(grid_lines(al, self.seams, 0.004)[:, None], col * 0.93, col)
        col = np.where((ctx.z < 1.2)[:, None], noisy(self.plinth, ctx.n1, 4), col)
        sp = np.full(n, -1)
        for f, parts in self.parts.items():
            on = ctx.face == f
            if not on.any():
                continue
            for a0, a1, z0, z1, painter in parts:
                sel = on & (al >= a0) & (al < a1) & (ctx.z >= z0) & (ctx.z < z1)
                if sel.any():
                    c, s = painter(ctx, sel, al, a0, a1, z0, z1)
                    col[sel] = c
                    if s is not None:
                        sp[sel] = s
        top = ctx.face == L_TOP
        if top.any():
            col = np.where(top[:, None], roof_membrane(ctx, self.roof), col)
            if ctx.snow:
                col = np.where(top[:, None], snow_col(ctx) - 4, col)
        return col, sp


def paint_band(color, var=4):
    def p(ctx, sel, al, a0, a1, z0, z1):
        return noisy(color, ctx.n1[sel], var), None
    return p


def paint_glazing(mullion=0.07, frame=(150, 152, 156), door=None, transom=None):
    """Shop glazing: lit-window glass between aluminium mullions; the door
    [d0, d1) shows the lighter glass. Glass is a special colour, so it glows
    at night."""
    def p(ctx, sel, al, a0, a1, z0, z1):
        a = al[sel]
        z = ctx.z[sel]
        n = int(sel.sum())
        col = np.tile(rgb(GLASS), (n, 1))
        sp = np.full(n, GLASS)
        refl = (ctx.n2[sel] > 0.9) | (np.mod(a * 64 + z * 0.5, 9) < 1.0)
        col[refl] = rgb(GLASS_LIGHT)
        sp[refl] = GLASS_LIGHT
        fr = grid_lines(a - a0, mullion, 0.009) | (z < z0 + 0.8) | (z >= z1 - 0.8)
        if transom is not None:
            fr |= np.abs(z - transom) < 0.5
        if door is not None:
            d0, d1 = door
            ind = (a >= d0) & (a < d1)
            dfr = (np.abs(a - d0) < 0.008) | (np.abs(a - d1) < 0.008) | (np.abs(a - (d0 + d1) / 2) < 0.004) \
                | (z >= z1 - 0.8) | (z < z0 + 0.8)
            fr = np.where(ind, dfr, fr)
            dl = ind & ~fr
            col[dl] = rgb(GLASS_LIGHT)
            sp[dl] = GLASS_LIGHT
        col[fr] = rgb(frame)
        sp[fr] = -1
        return col, sp
    return p


def paint_door(color=(110, 112, 116), frame=(80, 80, 84)):
    """Opaque service or dock door with horizontal ribs."""
    def p(ctx, sel, al, a0, a1, z0, z1):
        a, z = al[sel], ctx.z[sel]
        col = noisy(color, ctx.n1[sel], 4)
        rib = np.mod(z - z0, 2.0) < 0.5
        col[rib] *= 0.9
        edge = (a - a0 < 0.006) | (a1 - a < 0.006) | (z1 - z < 0.7)
        col[edge] = rgb(frame)
        return col, None
    return p


def paint_windows(cladding, period=0.08, width=0.045):
    """A band of small office windows (dark glass, lit at night)."""
    def p(ctx, sel, al, a0, a1, z0, z1):
        a = al[sel]
        n = int(sel.sum())
        f = np.mod(a - a0, period)
        win = (f > (period - width) / 2) & (f < (period + width) / 2)
        col = noisy(cladding, ctx.n1[sel], 4)
        sp = np.full(n, -1)
        col[win] = rgb(GLASS_DARK)
        sp[win] = GLASS_DARK
        return col, sp
    return p


# ground ------------------------------------------------------------------------------------------

def grass_col(ctx):
    n = ctx.n1
    return rgb(GRASS) + np.stack([(n - 0.5) * 2 * GRASS_VAR[0], (ctx.n2 - 0.5) * 2 * GRASS_VAR[1],
                                  (n - 0.5) * 2 * GRASS_VAR[2]], -1)


def ground_snow(ctx):
    return rgb(SNOW) + (ctx.n2[:, None] - 0.5) * 2 * np.array(SNOW_VAR, float)


class Ground:
    """Ground plane: rectangular zones painted in order over grass, then line
    overlays. Zone kinds: asphalt, pavers, concrete, grass, gravel."""

    CODES = {"grass": 0, "asphalt": 1, "pavers": 2, "concrete": 3, "gravel": 4}

    def __init__(self):
        self.zones = []
        self.lines = []

    def zone(self, x0, x1, y0, y1, kind):
        self.zones.append((x0, x1, y0, y1, kind))
        return self

    def line(self, x0, x1, y0, y1, color=(206, 206, 200)):
        self.lines.append((x0, x1, y0, y1, color))
        return self

    def __call__(self, ctx):
        x, y = ctx.x, ctx.y
        col = grass_col(ctx)
        kind = np.zeros(len(x), np.int8)
        for x0, x1, y0, y1, k in self.zones:
            kind[(x >= x0) & (x < x1) & (y >= y0) & (y < y1)] = self.CODES[k]
        asp = kind == 1
        col[asp] = noisy((88, 88, 92), ctx.n1[asp], 10)
        pav = kind == 2
        if pav.any():
            pa = 0.03
            row = np.floor(y[pav] / pa).astype(int)
            j = grid_lines(x[pav] + (row % 2) * pa / 2, pa, 0.004) | grid_lines(y[pav], pa, 0.004)
            c = noisy((176, 172, 162), ctx.n1[pav], 8)
            c[j] = rgb((150, 146, 138))
            col[pav] = c
        con = kind == 3
        if con.any():
            c = noisy((162, 162, 158), ctx.n1[con], 7)
            j = grid_lines(x[con], 0.125, 0.004) | grid_lines(y[con], 0.125, 0.004)
            c[j] = rgb((128, 128, 124))
            col[con] = c
        grv = kind == 4
        if grv.any():
            g = 128 + (ctx.n1[grv] - 0.5) * 40
            col[grv] = np.stack([g + 6, g, g - 12], -1)
        paint = np.zeros(len(x), bool)
        for x0, x1, y0, y1, c in self.lines:
            sel = (x >= x0) & (x < x1) & (y >= y0) & (y < y1)
            col[sel] = rgb(c) + (ctx.n1[sel, None] - 0.5) * 6
            paint |= sel
        if ctx.snow:
            snowc = ground_snow(ctx)
            # grass and gravel under full cover; paved areas ploughed into
            # patches of wet surface between trodden snow, markings covered
            soft = (kind == 0) | (kind == 4)
            cell = hash2(np.floor(x / 0.05).astype(int), np.floor(y / 0.05).astype(int), 5)
            wet = ~soft & (cell < 0.45) & ~paint
            col = np.where(wet[:, None], col * 0.55 + snowc * 0.45,
                           np.where(soft[:, None], snowc, snowc * 0.9 + col * 0.1))
        return col, None


# --- props -------------------------------------------------------------------------------------------

CAR_COLOURS = [(226, 226, 222), (182, 186, 190), (112, 114, 118), (40, 40, 44), (44, 62, 112),
               (166, 32, 30), (70, 104, 168), (52, 92, 64), (196, 176, 136), (150, 150, 154)]


def car(x, y, along_y, seed):
    """A parked car centred at (x, y); along_y = its long axis runs along y."""
    L, W = 4.4 * M, 1.8 * M
    col = CAR_COLOURS[int(hash2(seed, 7, 3) * len(CAR_COLOURS))]
    hx, hy = (W / 2, L / 2) if along_y else (L / 2, W / 2)
    body = Box(x - hx, x + hx, y - hy, y + hy, 1.0, 4.3, solid(col, 6))
    under = Box(x - hx + 0.004, x + hx - 0.004, y - hy + 0.01, y + hy - 0.01, 0.0, 1.0, solid((34, 34, 36), 4, 0))
    if along_y:
        cab = Box(x - hx + 0.006, x + hx - 0.006, y - hy * 0.55, y + hy * 0.35, 4.3, 6.3, car_cabin(col))
    else:
        cab = Box(x - hx * 0.55, x + hx * 0.35, y - hy + 0.006, y + hy - 0.006, 4.3, 6.3, car_cabin(col))
    return [under, body, cab]


def car_cabin(col):
    def m(ctx):
        c = np.tile(rgb((58, 66, 78)), (len(ctx.x), 1)) + (ctx.n1[:, None] - 0.5) * 6
        c[ctx.face == L_TOP] = rgb(col)
        return with_snow(ctx, c), None
    return m


def lamp_post(x, y, h=20.0):
    s = 0.006
    return [Box(x - s, x + s, y - s, y + s, 0, h, solid((92, 96, 100), 4, 0)),
            Box(x - 0.018, x + 0.018, y - 0.009, y + 0.009, h - 1.2, h, lamp_head())]


def lamp_head():
    def m(ctx):
        n = len(ctx.x)
        col = np.tile(rgb((80, 84, 88)), (n, 1))
        sp = np.full(n, -1)
        side = ctx.face != L_TOP
        col[side] = rgb(LAMP_WHITE)
        sp[side] = LAMP_WHITE
        return with_snow(ctx, col), sp
    return m


def tree(x, y, r=0.08, h=20.0, seed=0):
    return [Box(x - 0.008, x + 0.008, y - 0.008, y + 0.008, 0, h * 0.45, solid((92, 70, 52), 6, 0)),
            Box(x - r, x + r, y - r, y + r, h * 0.35, h, foliage(seed), shape="ellipsoid")]


def bush(x, y, r=0.035, h=5.0, seed=0):
    return [Box(x - r, x + r, y - r * 0.8, y + r * 0.8, 0, h, foliage(seed + 1, dark=True), shape="ellipsoid")]


def foliage(seed, dark=False):
    base = (54, 100, 40) if not dark else (46, 86, 38)

    def m(ctx):
        n = ctx.n1
        col = rgb(base) + np.stack([(n - 0.5) * 30, (n - 0.5) * 40 + (ctx.n2 - 0.5) * 16, (n - 0.5) * 14], -1)
        col[ctx.n2 > 0.8] *= 0.82
        if ctx.snow:
            up = (ctx.nz > 0.35) & (ctx.n1 > 0.25)
            col = np.where(up[:, None], snow_col(ctx) - 6, col)
        return col, None
    return m


def cart_shelter(x0, x1, y0, y1, roof_col, h=8.0):
    """Trolley shelter: brand coloured roof on posts over rows of carts."""
    out = [Box(x0, x1, y0, y1, h - 0.8, h, solid(roof_col, 4))]
    for px in (x0 + 0.006, x1 - 0.006):
        out.append(Box(px - 0.004, px + 0.004, y1 - 0.012, y1 - 0.004, 0, h - 0.8, solid((120, 122, 126), 3, 0)))
    n = max(1, int((x1 - x0) / 0.045))
    for i in range(n):
        cx = x0 + (i + 0.5) * (x1 - x0) / n
        out.append(Box(cx - 0.013, cx + 0.013, y0 + 0.008, y1 - 0.014, 0.6, 3.6, cart_mat()))
    return out


def cart_mat():
    def m(ctx):
        col = noisy((168, 172, 176), ctx.n1, 16)
        col[(np.mod(ctx.z, 1.0) < 0.35) | (ctx.n2 > 0.7)] = rgb((120, 124, 128))
        return col, None
    return m


def truck_cab(col=(214, 214, 210)):
    def m(ctx):
        c = noisy(col, ctx.n1, 5)
        c[(ctx.z > 6.5) & (ctx.z < 9.5) & (ctx.face != L_TOP)] = rgb((58, 66, 78))
        return with_snow(ctx, c), None
    return m


def parapets(x0, x1, y0, y1, z, h=2.0, t=0.016, col=(196, 196, 192)):
    m = solid(col, 4)
    return [Box(x0, x1, y0, y0 + t, z, z + h, m), Box(x0, x1, y1 - t, y1, z, z + h, m),
            Box(x0, x0 + t, y0, y1, z, z + h, m), Box(x1 - t, x1, y0, y1, z, z + h, m)]


def hvac(x, y, sx=0.05, sy=0.035, z=0.0, h=4.0):
    def m(ctx):
        col = noisy((150, 152, 150), ctx.n1, 6)
        col[(ctx.face != L_TOP) & (np.mod(ctx.z, 1.2) < 0.4)] *= 0.8
        fan = (ctx.face == L_TOP) & ((ctx.x - x) ** 2 / sx ** 2 + (ctx.y - y) ** 2 / sy ** 2 < 0.12)
        col[fan] = rgb((70, 72, 74))
        return with_snow(ctx, col), None
    return [Box(x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2, z, z + h, m)]


def skylight(x0, x1, y0, y1, z):
    def m(ctx):
        col = np.tile(rgb((150, 170, 180)), (len(ctx.x), 1)) + (ctx.n1[:, None] - 0.5) * 12
        col[grid_lines(ctx.x, 0.035, 0.005)] = rgb((190, 192, 194))
        return with_snow(ctx, col), None
    return [Box(x0, x1, y0, y1, z, z + 1.0, m)]


# --- building models ---------------------------------------------------------------------------------
# One model per size class, shared by every brand of that class; the brand
# supplies colours, signs and the roof logo. Local layout-0 coordinates: the
# shop front faces +y (south), x runs west to east. Sign sizes are screen
# pixels: one tile along a wall is 64 px, heights are px of z.

def wall_signs(br, specs):
    """{local face: [Sign]} from (face, kind, w, h, at, top) tuples."""
    out = {}
    for face, kind, w, h, at, top in specs:
        out.setdefault(face, []).append(Sign(br.sign(kind, w, h), at, top))
    return out


def parking_row(g, x0, x1, y0, y1, bay, cars, seed):
    """Bays between x0 and x1 (lines along y) from y0 to y1; cars in some."""
    n = int(round((x1 - x0) / bay))
    bay = (x1 - x0) / n
    for k in range(n + 1):
        x = x0 + k * bay
        g.line(x - 0.0035, x + 0.0035, y0, y1)
    out = []
    for k in range(n):
        if hash2(k, seed, 11) < cars:
            cx = x0 + (k + 0.5) * bay + (hash2(k, seed, 12) - 0.5) * 0.01
            cy = (y0 + y1) / 2 + (hash2(k, seed, 13) - 0.5) * 0.02
            out += car(cx, cy, True, seed * 31 + k)
    return out


def pylon(br, x, y, w, h, sign_h):
    """Totem: a grey column carrying the brand panel (w px wide) on top."""
    s = w / 128
    col = Box(x - 0.012, x + 0.012, y - 0.012, y + 0.012, 0, h - sign_h, solid((120, 124, 128), 3, 0))
    panel = Box(x - s, x + s, y - 0.014, y + 0.014, h - sign_h, h, solid(plain(br.panel_bg), 3),
                wall_signs(br, [(L_PY, "pylon", w, sign_h, x, h), (L_NY, "pylon", w, sign_h, x, h)]))
    return [col, panel]


def truck(br, x0, y0, along_y, length=0.62):
    """The brand's delivery semi, cab towards +y (along_y) or +x, with the
    logo on both trailer sides."""
    W = 2.5 * M
    cab_l = 0.1
    sw = int(length * 64) - 6
    if along_y:
        signs = wall_signs(br, [(f, "truck", sw, 9, y0 + length / 2, 12.5) for f in (L_PX, L_NX)])
        return [Box(x0 + 0.01, x0 + W - 0.01, y0 + 0.02, y0 + length + cab_l, 0.0, 2.2, solid((36, 36, 38), 3, 0)),
                Box(x0, x0 + W, y0, y0 + length, 2.2, 13.5, br.truck_livery, signs),
                Box(x0 + 0.004, x0 + W - 0.004, y0 + length + 0.01, y0 + length + 0.01 + cab_l, 1.4, 11.0, truck_cab())]
    signs = wall_signs(br, [(f, "truck", sw, 9, x0 + length / 2, 12.5) for f in (L_PY, L_NY)])
    return [Box(x0 + 0.02, x0 + length + cab_l, y0 + 0.01, y0 + W - 0.01, 0.0, 2.2, solid((36, 36, 38), 3, 0)),
            Box(x0, x0 + length, y0, y0 + W, 2.2, 13.5, br.truck_livery, signs),
            Box(x0 + length + 0.01, x0 + length + 0.01 + cab_l, y0 + 0.004, y0 + W - 0.004, 1.4, 11.0, truck_cab())]


def store_scene(br):
    """1x1 convenience store: single storey pavilion with a glazed front,
    fascia board over the roofline, a small car park and a lawn."""
    g = Ground()
    g.zone(0.06, 0.94, 0.08, 0.74, "pavers")
    g.zone(0.36, 0.99, 0.76, 0.99, "asphalt")
    g.line(0.36, 0.99, 0.74, 0.76, (190, 190, 186))            # kerb
    B = parking_row(g, 0.38, 0.97, 0.78, 0.97, 0.118, 0.6, seed=br.seed)
    x0, x1, y0, y1, H = 0.16, 0.80, 0.14, 0.62, 14.0
    f = Facade(br.wall)
    f.add([L_PY], x0 + 0.02, x1 - 0.02, 1.2, 9.5, paint_glazing(0.075, door=(0.30, 0.42)))
    f.add([L_PX], 0.50, 0.60, 1.2, 9.5, paint_glazing(0.05))
    f.add([L_NY], 0.60, 0.70, 0.0, 8.5, paint_door())
    f.add([L_NX], 0.40, 0.52, 3.0, 8.5, paint_windows(br.wall, 0.12, 0.08))
    B.append(Box(x0, x1, y0, y1, 0, H, f,
                 wall_signs(br, [(L_NY, "back", 22, 8, 0.36, 12.5), (L_NX, "back", 18, 8, 0.26, 12.5)]),
                 roof=RoofLogo(br.roof("store"), 0.84)))
    B += parapets(x0, x1, y0, y1, H, h=1.6, col=br.coping)
    B += hvac(0.24, 0.20, 0.06, 0.04, z=H, h=3.0)
    # fascia board across the front, standing above the roofline
    B.append(Box(x0 - 0.006, x1 + 0.006, y1, y1 + 0.018, 9.5, 19.5, solid(plain(br.fascia), 3),
                 wall_signs(br, [(L_PY, "fascia", 42, 10, (x0 + x1) / 2, 19.5)])))
    # sign panel on the east wall
    B.append(Box(x1, x1 + 0.012, 0.17, 0.47, 7.0, 15.0, solid(plain(br.fascia), 3),
                 wall_signs(br, [(L_PX, "side", 19, 8, 0.32, 15.0)])))
    # canopy over the door
    B.append(Box(0.26, 0.46, y1 + 0.018, y1 + 0.075, 9.0, 9.8, solid(br.accent, 3)))
    # waste bin, bike stand, A-board
    B.append(Box(0.52, 0.545, y1 + 0.03, y1 + 0.055, 0, 3.4, solid((52, 74, 58), 4)))
    for k in range(3):
        bx = 0.60 + k * 0.03
        B.append(Box(bx, bx + 0.004, y1 + 0.03, y1 + 0.08, 0, 2.6, solid((150, 152, 156), 3, 0)))
    B.append(Box(0.22, 0.25, y1 + 0.06, y1 + 0.075, 0, 4.0, solid(plain(br.fascia), 3)))
    # lawn at the front-west corner with a tree and shrubs
    B += tree(0.13, 0.86, 0.085, 22.0, seed=br.seed)
    B += bush(0.25, 0.92, 0.04, 5.0, seed=br.seed)
    B += bush(0.05, 0.60, 0.035, 4.5, seed=br.seed + 1)
    return Scene((1, 1), B, g)


def market_scene(br):
    """1x2 discount supermarket: a long single storey hall with a glazed,
    canopied entrance at the front, the brand panel beside it, a car park of
    two rows in front and a delivery lane with the brand's lorry on the west."""
    g = Ground()
    g.zone(0.0, 0.14, 0.0, 1.16, "asphalt")                   # delivery lane
    g.zone(0.10, 0.99, 1.10, 1.30, "pavers")                  # pavement along the front
    g.zone(0.01, 0.99, 1.30, 1.99, "asphalt")                 # car park
    g.line(0.01, 0.99, 1.295, 1.305, (190, 190, 186))
    B = parking_row(g, 0.03, 0.97, 1.33, 1.53, 0.105, 0.55, seed=br.seed)
    B += parking_row(g, 0.03, 0.97, 1.77, 1.97, 0.105, 0.5, seed=br.seed + 5)
    g.line(0.03, 0.97, 1.648, 1.656, (196, 196, 190))          # aisle centre line
    x0, x1, y0, y1, H = 0.15, 0.95, 0.08, 1.10, 20.0
    f = Facade(br.wall)
    f.add([L_PY], x0 + 0.01, 0.60, 1.2, 12.0, paint_glazing(0.07, door=(0.30, 0.44), transom=9.0))
    f.add([L_PY], x0 + 0.01, 0.60, 12.6, H, paint_band(plain(br.fascia)))
    f.add([L_PX, L_NX, L_NY], 0.0, 2.0, H - 3.0, H, paint_band(br.accent))
    f.add([L_PX], 0.86, 1.06, 1.2, 10.0, paint_glazing(0.05))
    f.add([L_NX], 0.30, 0.44, 0.0, 10.0, paint_door())
    f.add([L_NX], 0.50, 0.64, 0.0, 10.0, paint_door())
    f.add([L_NY], 0.60, 0.70, 0.0, 8.5, paint_door())
    B.append(Box(x0, x1, y0, y1, 0, H, f,
                 wall_signs(br, [(L_PX, "side", 40, 11, 0.52, 16.0), (L_NY, "back", 40, 11, 0.50, 16.0),
                                 (L_NX, "side", 40, 11, 0.80, 16.0),
                                 (L_PY, "fascia", 28, 7, (x0 + 0.01 + 0.60) / 2, 19.8)]),
                 roof=RoofLogo(br.roof("market"), 0.78)))
    B += parapets(x0, x1, y0, y1, H, h=1.8, col=br.coping)
    B += hvac(0.35, 0.22, 0.09, 0.06, z=H, h=3.5)
    B += hvac(0.75, 0.22, 0.06, 0.05, z=H, h=3.0)
    # brand panel beside the entrance, rising above the roof
    B.append(Box(0.617, 0.961, y1, y1 + 0.02, 5.0, 26.0, solid(plain(br.panel_bg), 3),
                 wall_signs(br, [(L_PY, "panel", 22, 21, 0.789, 26.0)])))
    # canopy over the entrance on two columns
    B.append(Box(x0, 0.60, y1, y1 + 0.12, 12.0, 13.4, solid(br.accent, 3)))
    for cx in (x0 + 0.02, 0.58):
        B.append(Box(cx - 0.006, cx + 0.006, y1 + 0.10, y1 + 0.112, 0, 12.0, solid((150, 152, 156), 3, 0)))
    B += cart_shelter(0.66, 0.90, y1 + 0.06, y1 + 0.18, br.accent)
    # lamps on the car park edges, pylon at the entrance corner
    B += lamp_post(0.02, 1.65, 22.0)
    B += lamp_post(0.98, 1.65, 22.0)
    B += pylon(br, 0.925, 1.935, 9, 44.0, 32)
    # delivery lorry on the west lane, shrubs along the east edge
    B += truck(br, 0.02, 0.16, True, 0.62)
    B += bush(0.975, 0.30, 0.025, 4.0, seed=br.seed)
    B += bush(0.975, 0.70, 0.025, 4.0, seed=br.seed + 2)
    return Scene((1, 2), B, g)


def hyper_scene(br):
    """2x2 hypermarket: a large hall with a tall branded entrance block,
    glazed shop gallery and canopy along the front, a big car park, lamps,
    trolley shelters, a tall pylon and a lorry at the back docks."""
    g = Ground()
    g.zone(0.0, 2.0, 0.0, 0.15, "asphalt")                    # service road at the back
    g.zone(0.04, 1.96, 1.12, 1.34, "pavers")
    g.zone(0.01, 1.99, 1.34, 1.99, "asphalt")
    g.line(0.01, 1.99, 1.335, 1.345, (190, 190, 186))
    B = parking_row(g, 0.03, 0.91, 1.37, 1.57, 0.105, 0.6, seed=br.seed)
    B += parking_row(g, 1.09, 1.97, 1.37, 1.57, 0.105, 0.6, seed=br.seed + 1)
    B += parking_row(g, 0.03, 0.91, 1.77, 1.97, 0.105, 0.5, seed=br.seed + 2)
    B += parking_row(g, 1.09, 1.97, 1.77, 1.97, 0.105, 0.5, seed=br.seed + 3)
    g.line(0.03, 1.97, 1.668, 1.676, (196, 196, 190))
    for k in range(7):                                        # zebra from the entrance
        y = 1.36 + k * 0.09
        g.line(0.93, 1.07, y, y + 0.045, (214, 214, 208))
    x0, x1, y0, y1, H = 0.06, 1.94, 0.16, 1.14, 26.0
    e0, e1 = 0.62, 1.38
    f = Facade(br.wall)
    for a0, a1 in ((0.10, e0), (e1, 1.90)):
        f.add([L_PY], a0, a1, 1.2, 10.5, paint_glazing(0.08))
    f.add([L_PY], x0, x1, 17.5, H, paint_band(plain(br.fascia)))
    f.add([L_PX, L_NX, L_NY], 0.0, 2.0, H - 4.0, H, paint_band(br.accent))
    f.add([L_PX], 0.30, 0.60, 12.0, 17.0, paint_windows(br.wall, 0.06, 0.04))
    for k in range(4):
        a = 0.55 + k * 0.24
        f.add([L_NY], a, a + 0.14, 0.0, 12.0, paint_door())
    f.add([L_NX], 0.40, 0.52, 0.0, 9.0, paint_door())
    B.append(Box(x0, x1, y0, y1, 0, H, f,
                 wall_signs(br, [(L_PX, "side", 56, 14, 0.66, 21.0), (L_NY, "back", 56, 14, 1.0, 21.0),
                                 (L_NX, "side", 56, 14, 0.66, 21.0),
                                 (L_PY, "fascia", 34, 8, (x0 + e0) / 2, H - 0.3),
                                 (L_PY, "fascia", 34, 8, (e1 + x1) / 2, H - 0.3)]),
                 roof=RoofLogo(br.roof("hyper"), 0.66)))
    B += parapets(x0, x1, y0, y1, H, h=2.0, col=br.coping)
    for hx, hy in ((0.30, 0.34), (0.52, 0.34), (1.48, 0.32), (1.70, 0.32)):
        B += hvac(hx, hy, 0.09, 0.06, z=H, h=4.0)
    for sx in (0.16, 1.70):
        B += skylight(sx, sx + 0.12, 0.58, 0.98, H)
    # entrance block
    fe = Facade(br.entrance, seams=0.0)
    fe.add([L_PY], e0 + 0.05, e1 - 0.05, 1.2, 12.0, paint_glazing(0.07, door=(0.92, 1.08), transom=9.0))
    fe.add([L_PX, L_NX], y1 - 0.01, y1 + 0.13, 1.2, 12.0, paint_glazing(0.06))
    B.append(Box(e0, e1, y1 - 0.02, y1 + 0.12, 0, 34.0, fe,
                 wall_signs(br, [(L_PY, "entrance", 46, 17, 1.0, 32.5)])))
    B += parapets(e0, e1, y1 - 0.02, y1 + 0.12, 34.0, h=1.2, col=br.coping)
    # canopy along the gallery
    for a0, a1 in ((0.10, e0), (e1, 1.90)):
        B.append(Box(a0, a1, y1, y1 + 0.09, 11.0, 12.2, solid(br.accent, 3)))
    B += cart_shelter(0.30, 0.54, y1 + 0.10, y1 + 0.19, br.accent)
    B += cart_shelter(1.46, 1.70, y1 + 0.10, y1 + 0.19, br.accent)
    for lx in (0.50, 1.50):
        B += lamp_post(lx, 1.672, 26.0)
    B += lamp_post(0.02, 1.672, 26.0)
    B += lamp_post(1.98, 1.672, 26.0)
    B += pylon(br, 1.905, 1.935, 11, 54.0, 38)
    B += truck(br, 0.70, 0.02, False, 0.62)
    B += tree(0.03, 1.05, 0.05, 18.0, seed=br.seed)
    B += tree(1.97, 1.05, 0.05, 18.0, seed=br.seed + 1)
    return Scene((2, 2), B, g)


MODELS = {"store": store_scene, "market": market_scene, "hyper": hyper_scene}


# --- brands ----------------------------------------------------------------------------------------------
# Colours from the chains' logo files (hex) and photos of Czech stores. Sign
# lettering that is white, red or yellow in reality uses the always-lit lamp
# specials and white lightbox boards use LAMP_WHITE, so signs glow at night;
# roof logos get plain twins of those colours (roofs are not lit).

class Brand:
    """Colours and sign art of one chain. `lockup(mw, mh, kind)` returns the
    logo (wordmark plus marks) as a transparent bitmap no larger than mw x mh;
    signs put it on a board, the roof logo on a panel."""

    SUB_KINDS = ("entrance", "side", "roof")

    def __init__(self, key, wordmark, fascia, ink, wall=(214, 214, 210), accent=None, entrance=None,
                 panel_bg=None, coping=(196, 196, 192), trailer=(236, 236, 232), roof_bg=None, roof_ink=None,
                 sub=None, sub_ink=None, emblem=None, lockup=None, board=None, pylon=None, stack=None,
                 truck_ink=None, truck_band=False, seed=1):
        self.key = key
        self.wordmark = wordmark
        self.fascia = fascia
        self.ink = ink
        self.wall = wall
        self.accent = accent or plain(fascia)
        self.entrance = entrance or plain(fascia)
        self.panel_bg = panel_bg or fascia
        self.coping = coping
        self.trailer = trailer
        self.roof_bg = roof_bg or plain(fascia)
        self.roof_ink = roof_ink or plain(ink)
        self.sub = sub
        self.sub_ink = sub_ink or ink
        self.emblem = emblem
        self.custom_lockup = lockup
        self.custom_board = board
        self.custom_pylon = pylon
        self.stack = stack or wordmark.upper()
        self.truck_ink = truck_ink
        self.truck_band = truck_band
        self.seed = seed
        self.truck_livery = trailer_material(self)

    # logo -------------------------------------------------------------------
    def lockup(self, mw, mh, kind):
        if self.custom_lockup:
            return self.custom_lockup(self, mw, mh, kind)
        return default_lockup(self, mw, mh, kind)

    # signs ------------------------------------------------------------------
    def sign(self, kind, w, h):
        if kind == "pylon":
            return (self.custom_pylon or default_pylon)(self, w, h)
        if kind == "panel":
            return self.panel(w, h)
        if kind == "truck":
            return self.truck_sign(w, h)
        bm = Bitmap(w, h, self.fascia)
        if self.custom_board:
            self.custom_board(self, bm, kind)
        lk = self.lockup(w - 2, h - (0 if h <= 10 else 2), kind)
        if lk is not None:
            bm.paste(lk, (w - lk.w) // 2, (h - lk.h + 1) // 2)
        return bm

    def truck_sign(self, w, h):
        """Trailer side: the logo on the trailer colour (or on the fascia band
        with truck_band); lorries are not lit, so every colour is plain."""
        if self.truck_band:
            bm = Bitmap(w, h, self.fascia)
            if self.custom_board:
                self.custom_board(self, bm, "truck")
        else:
            bm = Bitmap(w, h, self.trailer)
        lk = self.lockup(w - 2, h - 1, "truck")
        if lk is not None:
            if self.truck_ink is not None:
                lk.rgb[lk.a] = hexrgb(self.truck_ink)
            bm.paste(lk, (w - lk.w) // 2, (h - lk.h + 1) // 2)
        for y in range(bm.h):
            for x in range(bm.w):
                bm.rgb[y, x] = plain(tuple(bm.rgb[y, x]))
        return bm

    def panel(self, w, h):
        """Brand panel beside a supermarket entrance: the emblem, or the logo."""
        bm = Bitmap(w, h, self.panel_bg)
        if self.emblem is not None:
            s = min(w, h)
            em = self.emblem(s)
            bm.paste(em, (w - em.w) // 2, (h - em.h) // 2)
            return bm
        if self.custom_board:
            self.custom_board(self, bm, "panel")
        lk = self.lockup(w - 2, h - 2, "panel")
        if lk is not None:
            bm.paste(lk, (w - lk.w) // 2, (h - lk.h) // 2)
        return bm

    def roof(self, kind):
        """Roof logo: the lockup on a panel with a margin (plain colours)."""
        lk = self.lockup(200, 40, "roof")
        pad = 3
        bm = Bitmap(lk.w + 2 * pad, lk.h + 2 * pad, plain(self.roof_bg))
        if self.custom_board:
            self.custom_board(self, bm, "roof")
        bm.paste(lk, pad, pad)
        return bm


def plain(c):
    """A special colour's plain twin, for surfaces that must not glow."""
    v = hexrgb(c)
    if (v[0] << 16 | v[1] << 8 | v[2]) in SPECIALS:
        return (v[0], v[1], v[2] - 1 if v[2] > 0 else 1)
    return v


def font_for(text, mw, mh, fonts=None):
    """(mask, font) of `text` in the largest font that fits, or (None, None)."""
    for font in fonts or (FONT7, FONT5):
        t = text if all(c in font for c in text) else text.upper()
        if len(font["A"]) > mh or not all(c in font for c in t):
            continue
        m = text_mask(t, font)
        if m.shape[1] <= mw:
            return m, font
    return None, None


def default_lockup(br, mw, mh, kind):
    """Emblem (if it fits) + wordmark, with the sub-label underneath on the
    kinds that have room for it."""
    em = br.emblem(min(mh, 11)) if br.emblem else None
    em_w = em.w + 2 if em is not None else 0
    word, font = font_for(br.wordmark, mw - em_w, mh)
    if word is None and em is not None:
        word, font = font_for(br.wordmark, mw, mh)
        em, em_w = None, 0
    if word is None:
        return br.emblem(min(mw, mh)) if br.emblem else None
    sub = None
    if br.sub and kind in Brand.SUB_KINDS:
        sub, _ = font_for(br.sub.upper(), mw, 5, (FONT5,))
        if sub is not None and word.shape[0] + 1 + sub.shape[0] > mh:
            sub = None
    tw = max(word.shape[1] + em_w, sub.shape[1] if sub is not None else 0)
    th = max(word.shape[0] + ((sub.shape[0] + 1) if sub is not None else 0), em.h if em is not None else 0)
    bm = Bitmap(tw, th)
    x = (tw - word.shape[1] - em_w) // 2
    if em is not None:
        bm.paste(em, x, (word.shape[0] - em.h) // 2 if em.h <= word.shape[0] else 0)
        x += em_w
    bm.mask(word, x, 0, br.ink if kind != "roof" else br.roof_ink)
    if sub is not None:
        bm.mask(sub, (tw - sub.shape[1]) // 2, word.shape[0] + 1, br.sub_ink if kind != "roof" else plain(br.sub_ink))
    return bm


def default_pylon(br, w, h):
    """Totem panel: emblem at the top, then the name in stacked capitals."""
    bm = Bitmap(w, h, br.panel_bg)
    y = 1
    if br.emblem is not None:
        em = br.emblem(w - 2 if w > 8 else w)
        bm.paste(em, (w - em.w) // 2, y)
        y += em.h + 2
    letters = [c for c in br.stack if c in FONT5]
    if letters and y + 6 * len(letters) - 1 <= h - 1:
        y += (h - 1 - y - (6 * len(letters) - 1)) // 2
        for ch in letters:
            m = text_mask(ch, FONT5)
            bm.mask(m, (w - m.shape[1]) // 2, y, br.ink)
            y += 6
    return bm


def trailer_material(br):
    """Delivery trailer: the brand's trailer colour with a darker skirt."""
    base = plain(br.trailer)

    def m(ctx):
        col = noisy(base, ctx.n1, 3)
        col[(ctx.face != L_TOP) & (ctx.z < 3.2)] *= 0.8
        return with_snow(ctx, col), None
    return m


# emblems -------------------------------------------------------------------------------------------------

def zabka_basket(s):
    """Žabka: a basket of 2 x 4 coloured tiles under a black handle."""
    w = max(7, s)
    h = max(6, round(w * 0.8))
    bm = Bitmap(w, h)
    tiles = [0xE31B1D, 0xCBD300, 0xF8B000, 0x009EE0, 0x009EE0, 0xF8B000, 0xE31B1D, 0xCBD300]
    top = h // 3
    tw = w / 4
    th = (h - top) / 2
    for i, c in enumerate(tiles):
        cx, cy = i % 4, i // 4
        x0, x1 = round(cx * tw), round((cx + 1) * tw)
        y0, y1 = top + round(cy * th), top + round((cy + 1) * th)
        bm.rect(x0, y0, x1, y1, c)
    # handle: an arc from the top corners
    yy, xx = np.mgrid[0:h, 0:w]
    r = w * 0.36
    d = np.hypot(xx + 0.5 - w / 2, (yy + 0.5 - top) * 1.3)
    bm.mask_full((d >= r - 0.9) & (d <= r + 0.4) & (yy < top), (30, 32, 34))
    return bm


def lidl_logo(s):
    """Lidl: blue square, yellow disc in a red ring, blue LIDL, red i-dot."""
    s = max(7, s)
    bm = Bitmap(s, s, 0x0050AA)
    c = s / 2
    r = s * 0.46
    bm.disc(c, c, r, LAMP_RED)
    bm.disc(c, c, r - (1.0 if s >= 9 else 0.7), LAMP_YELLOW)
    if s >= 15:
        font = FONT7 if s >= 30 else FONT5
        m = text_mask("LIDL", font)
        x = (s - m.shape[1]) // 2
        y = (s - m.shape[0]) // 2
        bm.mask(m, x, y, 0x0050AA)
        # the i: its dot is red
        iw = len(font["I"][0])
        ix = x + len(font["L"][0]) + 1
        bm.rect(ix, y, ix + iw, y + (2 if font is FONT7 else 1), LAMP_RED)
    else:
        bm.rect(round(s * 0.22), round(c - 1), round(s * 0.78), round(c + 1), 0x0050AA)
    return bm


def kaufland_logo(s):
    """Kaufland: a red frame round a red K of two squares and two triangles."""
    s = max(7, s)
    bm = Bitmap(s, s, LAMP_WHITE)
    red = LAMP_RED
    bm.rect(0, 0, s, 1, red).rect(0, s - 1, s, s, red).rect(0, 0, 1, s, red).rect(s - 1, 0, s, s, red)
    yy, xx = np.mgrid[0:s, 0:s]
    fx = (xx + 0.5) / s
    fy = (yy + 0.5) / s
    left = (fx > 0.2) & (fx < 0.47) & (fy > 0.2) & (fy < 0.8)
    upper = (fx > 0.5) & (fy > 0.2) & (fy < 0.5) & (fx - 0.5 < (0.5 - fy) * 1.0 + 0.02) & (fx < 0.8)
    lower = (fx > 0.5) & (fy > 0.5) & (fy < 0.8) & (fx - 0.5 < (fy - 0.5) * 1.0 + 0.02) & (fx < 0.8)
    bm.mask_full(left | upper | lower, red)
    return bm


def penny_logo(s):
    """Penny: red square, white PENNY, yellow full stop."""
    s = max(7, s)
    bm = Bitmap(s, s, 0xCD1316)
    word, _ = font_for("PENNY", s - 3, s - 2, (FONT7, FONT5))
    if word is None:
        word = text_mask("P", FONT5)
    x = (s - word.shape[1] - 2) // 2
    y = (s - word.shape[0]) // 2
    bm.mask(word, x, y, LAMP_WHITE)
    bm.rect(x + word.shape[1] + 1, y + word.shape[0] - 1, x + word.shape[1] + 2, y + word.shape[0], LAMP_YELLOW)
    return bm


def globus_globe(s):
    """Globus: a green globe grid."""
    s = max(7, s)
    bm = Bitmap(s, s)
    yy, xx = np.mgrid[0:s, 0:s]
    c = s / 2
    r = s / 2 - 0.3
    d = np.hypot(xx + 0.5 - c, yy + 0.5 - c)
    inside = d <= r
    bm.mask_full(inside, LAMP_WHITE)
    grid = (d >= r - 1.0) & inside
    grid |= inside & (np.abs(yy + 0.5 - c) < 0.5)
    grid |= inside & (np.abs(xx + 0.5 - c) < 0.5)
    ex = np.abs(xx + 0.5 - c) / max(r * 0.55, 1)
    grid |= inside & (np.abs(np.hypot(ex, (yy + 0.5 - c) / r) - 1) < 1.2 / s)
    bm.mask_full(grid, 0x00AC4F)
    return bm


def albert_leaves(w=5):
    """Albert: three leaves above the 'ert' (blue upright, green, yellow)."""
    bm = Bitmap(w, 2)
    bm.rect(0, 1, 2, 2, 0xF8DC00)         # flat yellow oval, left
    bm.rect(1, 0, 3, 1, 0x88AB32)         # green, middle
    bm.rect(3, 0, 4, 2, 0x007ABC)         # blue upright, right
    return bm


# lockups ---------------------------------------------------------------------------------------------------

def tesco_lockup(br, mw, mh, kind):
    """Red TESCO over a row of slanted blue dashes; 'expres' etc. beside or below."""
    red = br.ink if kind != "roof" else plain(br.ink)
    blue = 0x00539F
    for font, dash_h in ((FONT7, 1), (FONT5, 1)):
        word = text_mask("TESCO", font)
        if word.shape[0] + 1 + dash_h > mh or word.shape[1] > mw:
            continue
        sub = None
        if br.sub and kind in ("roof", "side", "entrance", "fascia"):
            sub, _ = font_for(br.sub.upper(), mw, 5, (FONT5,))
        side_by_side = sub is not None and word.shape[1] + 3 + sub.shape[1] <= mw
        below = sub is not None and not side_by_side and word.shape[0] + 3 + sub.shape[0] <= mh
        tw = word.shape[1] + (sub.shape[1] + 3 if side_by_side else 0)
        th = word.shape[0] + 2 + (sub.shape[0] + 1 if below else 0)
        bm = Bitmap(max(tw, sub.shape[1] if below else 0), th)
        bm.mask(word, 0, 0, red)
        # dashes: short slanted strokes under the word
        n = 6
        y = word.shape[0] + 1
        for k in range(n):
            x0 = round(k * word.shape[1] / n)
            bm.rect(x0, y, x0 + max(2, word.shape[1] // n - 1), y + 1, blue)
        if side_by_side:
            bm.mask(sub, word.shape[1] + 3, word.shape[0] - sub.shape[0], blue)
        elif below:
            bm.mask(sub, (bm.w - sub.shape[1]) // 2, y + 2, blue)
        return bm
    return None


def albert_lockup(br, mw, mh, kind):
    """Blue lowercase albert with the three leaves over 'ert'; on hypermarkets
    a yellow band and a blue band with white HYPERMARKET underneath."""
    blue = 0x007ABC
    word, font = font_for("albert", mw, mh)
    if word is None:
        return None
    ink = br.roof_ink if kind == "roof" else br.ink
    hyper = br.sub and kind in ("entrance", "side", "roof")
    sub = text_mask(br.sub.upper(), FONT5) if hyper else None
    if sub is not None and (word.shape[0] + 1 + 9 > mh or sub.shape[1] + 2 > mw):
        sub = None
    tw = max(word.shape[1], sub.shape[1] + 4 if sub is not None else 0)
    th = word.shape[0] + (10 if sub is not None else 0)
    bm = Bitmap(tw, th)
    x = (tw - word.shape[1]) // 2
    bm.mask(word, x, 0, ink)
    if font is FONT7:
        # leaves over "er" (the x-height leaves rows 0-1 free there)
        lv = albert_leaves()
        ex = x + sum(len(FONT7[c][0]) + 1 for c in "alb")
        bm.paste(lv, ex + 2, 0)
    if sub is not None:
        y = word.shape[0] + 1
        bm.rect(0, y, tw, y + 2, 0xF8DC00)
        bm.rect(0, y + 2, tw, y + 9, blue)
        bm.mask(sub, (tw - sub.shape[1]) // 2, y + 3, LAMP_WHITE if kind != "roof" else (250, 250, 250))
    return bm


def penny_lockup(br, mw, mh, kind):
    word, font = font_for("PENNY", mw - 3, mh)
    if word is None:
        return None
    bm = Bitmap(word.shape[1] + 3, word.shape[0])
    white = LAMP_WHITE if kind != "roof" else (250, 250, 250)
    bm.mask(word, 0, 0, white)
    d = 2 if font is FONT7 else 1
    bm.rect(word.shape[1] + 1, word.shape[0] - d, word.shape[1] + 1 + d, word.shape[0],
            LAMP_YELLOW if kind != "roof" else 0xFFD400)
    return bm


def norma_board(br, bm, kind):
    """Norma: the red band edged with orange and yellow stripes."""
    if bm.h < 7:
        return
    yellow = 0xFFCC33
    orange = 0xFF6600
    bm.rect(0, 0, bm.w, 1, yellow).rect(0, 1, bm.w, 2, orange)
    bm.rect(0, bm.h - 2, bm.w, bm.h - 1, orange).rect(0, bm.h - 1, bm.w, bm.h, yellow)


def globus_lockup(br, mw, mh, kind):
    """Orange GLOBUS with the green globe before it."""
    em_s = min(mh, 9)
    em = globus_globe(em_s) if mw > 40 + em_s else None
    word, font = font_for("GLOBUS", mw - (em.w + 2 if em else 0), mh)
    if word is None:
        return globus_globe(min(mw, mh))
    orange = br.roof_ink if kind == "roof" else 0xF58220
    tw = word.shape[1] + (em.w + 2 if em else 0)
    th = max(word.shape[0], em.h if em else 0)
    bm = Bitmap(tw, th)
    x = 0
    if em:
        bm.paste(em, 0, (th - em.h) // 2)
        x = em.w + 2
    bm.mask(word, x, (th - word.shape[0]) // 2, orange)
    return bm


def zabka_lockup(br, mw, mh, kind):
    em = zabka_basket(min(mh, 9))
    word, font = font_for("žabka", mw - em.w - 2, mh)
    if word is None:
        return zabka_basket(min(mw, mh))
    white = LAMP_WHITE if kind != "roof" else (250, 250, 250)
    th = max(word.shape[0], em.h)
    bm = Bitmap(em.w + 2 + word.shape[1], th)
    bm.paste(em, 0, th - em.h)
    bm.mask(word, em.w + 2, th - word.shape[0], white)
    return bm


def lidl_lockup(br, mw, mh, kind):
    """Lidl signs are the square logo itself."""
    return lidl_logo(min(mw, mh))


def kaufland_lockup(br, mw, mh, kind):
    """The K emblem, then red 'Kaufland' when there is room (else capitals)."""
    em = kaufland_logo(min(mh, 11))
    word, font = font_for("Kaufland", mw - em.w - 2, mh)
    if word is None:
        return kaufland_logo(min(mw, mh))
    red = br.ink if kind != "roof" else plain(br.ink)
    th = max(word.shape[0], em.h)
    bm = Bitmap(em.w + 2 + word.shape[1], th)
    bm.paste(em, 0, (th - em.h) // 2)
    bm.mask(word, em.w + 2, (th - word.shape[0]) // 2, red)
    return bm


ANTHRACITE = (52, 55, 58)
CHARCOAL = (52, 63, 64)

BRANDS = {
    # small stores (1x1)
    "zabka": Brand("zabka", "žabka", CHARCOAL, LAMP_WHITE, wall=(206, 206, 202), accent=CHARCOAL,
                   lockup=zabka_lockup, seed=11),
    "tesco_expres": Brand("tesco_expres", "TESCO", LAMP_WHITE, LAMP_RED, wall=(222, 222, 218), accent=(0, 83, 159),
                          roof_bg=(246, 246, 244), sub="expres", lockup=tesco_lockup, seed=12),
    "albert": Brand("albert", "albert", LAMP_WHITE, 0x007ABC, wall=(222, 222, 218), accent=(0, 122, 188),
                    roof_bg=(0, 122, 188), roof_ink=(250, 250, 250), lockup=albert_lockup, seed=13),
    "coop": Brand("coop", "coop", ANTHRACITE, 0xEA5D00, wall=(232, 230, 224), accent=(234, 93, 0),
                  roof_bg=(234, 93, 0), roof_ink=(250, 250, 250), seed=14),
    # supermarkets (1x2)
    "lidl": Brand("lidl", "LIDL", (0, 80, 170), LAMP_YELLOW, wall=(226, 226, 222), accent=(0, 80, 170),
                  panel_bg=(0, 80, 170), trailer=(236, 236, 232), roof_bg=(0, 80, 170), lockup=lidl_lockup,
                  emblem=lidl_logo, seed=21),
    "penny": Brand("penny", "PENNY", (205, 19, 22), LAMP_WHITE, wall=(44, 44, 46), accent=(205, 19, 22),
                   coping=(70, 70, 72), trailer=(205, 19, 22), roof_bg=(205, 19, 22), roof_ink=(250, 250, 250),
                   lockup=penny_lockup, emblem=penny_logo, seed=22),
    "billa": Brand("billa", "BILLA", ANTHRACITE, LAMP_YELLOW, wall=(232, 232, 228), accent=ANTHRACITE,
                   trailer=(250, 214, 0), roof_bg=ANTHRACITE, roof_ink=(255, 213, 0), truck_ink=ANTHRACITE,
                   seed=23),
    "norma": Brand("norma", "NORMA", (214, 15, 25), LAMP_WHITE, wall=(222, 222, 218), accent=(214, 15, 25),
                   trailer=(236, 236, 232), roof_bg=(214, 15, 25), roof_ink=(250, 250, 250), board=norma_board,
                   truck_band=True, seed=24),
    "tesco": Brand("tesco", "TESCO", LAMP_WHITE, LAMP_RED, wall=(222, 222, 218), accent=(0, 83, 159),
                   panel_bg=LAMP_WHITE, roof_bg=(246, 246, 244), lockup=tesco_lockup, seed=25),
    # hypermarkets (2x2)
    "kaufland": Brand("kaufland", "Kaufland", LAMP_WHITE, LAMP_RED, wall=(214, 214, 212), accent=(225, 9, 21),
                      entrance=(225, 9, 21), panel_bg=LAMP_WHITE, trailer=(236, 236, 232), roof_bg=(246, 246, 244),
                      lockup=kaufland_lockup, emblem=kaufland_logo, stack="", seed=31),
    "globus": Brand("globus", "GLOBUS", LAMP_WHITE, 0xF58220, wall=(226, 226, 222), accent=(0, 172, 79),
                    entrance=(245, 130, 32), panel_bg=LAMP_WHITE, trailer=(236, 236, 232), roof_bg=(245, 130, 32),
                    roof_ink=(250, 250, 250), lockup=globus_lockup, emblem=globus_globe, seed=32),
    "albert_hyper": Brand("albert_hyper", "albert", LAMP_WHITE, 0x007ABC, wall=(236, 214, 70), accent=(0, 122, 188),
                          entrance=(0, 122, 188), panel_bg=LAMP_WHITE, sub="hypermarket", sub_ink=LAMP_WHITE,
                          trailer=(236, 236, 232), roof_bg=(0, 122, 188), roof_ink=(250, 250, 250),
                          lockup=albert_lockup, stack="ALBERT", seed=33),
    "tesco_hyper": Brand("tesco_hyper", "TESCO", LAMP_WHITE, LAMP_RED, wall=(214, 214, 212), accent=(0, 83, 159),
                         entrance=(0, 83, 159), panel_bg=LAMP_WHITE, roof_bg=(246, 246, 244), lockup=tesco_lockup,
                         seed=34),
    "makro": Brand("makro", "makro", (1, 37, 112), LAMP_YELLOW, wall=(24, 54, 120), accent=(252, 236, 25),
                   entrance=(1, 37, 112), coping=(40, 64, 124), trailer=(1, 37, 112), roof_bg=(1, 37, 112),
                   roof_ink=(252, 236, 25), seed=35),
}


# --- sheets and preview -----------------------------------------------------------------------------------

def preview(views, scene, path):
    """Every layout and season placed on a grass apron, as the game shows it."""
    pads = []
    for season in range(SEASONS):
        row = []
        for layout in range(LAYOUTS):
            img = views[(season, layout)]
            h, w = img.shape[:2]
            bg = np.empty((h + 16, w + 16, 3), np.uint8)
            bg[:] = (70, 110, 50) if season == 0 else (200, 200, 212)
            sub = bg[8:8 + h, 8:8 + w]
            m = ~np.all(img == KEY, -1)
            sub[m] = img[m]
            row.append(bg)
        hh = max(r.shape[0] for r in row)
        row = [np.pad(r, ((0, hh - r.shape[0]), (0, 4), (0, 0)), constant_values=40) for r in row]
        pads.append(np.concatenate(row, 1))
    ww = max(p.shape[1] for p in pads)
    pads = [np.pad(p, ((0, 4), (0, ww - p.shape[1]), (0, 0)), constant_values=40) for p in pads]
    out = Image.fromarray(np.concatenate(pads, 0), "RGB")
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("set_dir", type=Path)
    ap.add_argument("--only", action="append", help="render only these sprite names")
    ap.add_argument("--preview", type=Path, help="also write a preview PNG per sprite into this directory")
    args = ap.parse_args()
    spec = yaml.safe_load((args.set_dir / "industry.yaml").read_text(encoding="utf-8"))
    out_dir = args.set_dir / "sprites"
    out_dir.mkdir(exist_ok=True)
    for obj in spec["objects"]:
        name = obj["sprite"]
        if args.only and name not in args.only:
            continue
        gen = obj.get("generate")
        if not gen:
            continue
        brand = BRANDS[gen["brand"]]
        scene = MODELS[gen["model"]](brand)
        if tuple(scene.dims) != tuple(obj["dims"]):
            raise SystemExit(f"{name}: model {gen['model']} is {scene.dims}, yaml says {obj['dims']}")
        sheet, views = build_sheet(scene)
        sheet.save(out_dir / f"{name}.png", optimize=True)
        print(f"wrote {out_dir / (name + '.png')}")
        if args.preview:
            args.preview.mkdir(parents=True, exist_ok=True)
            preview(views, scene, args.preview / f"{name}.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
