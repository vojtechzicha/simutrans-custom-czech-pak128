#!/usr/bin/env python3
"""Render the sprite sheets for procedurally drawn rail platforms and crossings.

Reads a ``station.yaml`` (see CLAUDE.md, "Stations") and writes one PNG per
object into ``<station dir>/sprites/<sprite>.png``. Every object in this
generator is a 16-layout through stop (Simutrans picks the layout from the
track direction, the free platform ends and the side facing the neighbouring
platform), so each sheet holds::

    row 0-1  back image,  season 0, layouts 0-7 / 8-15
    row 2-3  front image, season 0
    row 4-5  back image,  season 1 (snow)
    row 6-7  front image, season 1
    row 8    col 0 = build cursor, col 1 = 32x32 toolbar icon (top-left)

Layout bits (bauer/hausbauer.cc): 1 = east-west track, 2 = no neighbour at the
south/east end (ramp there), 4 = no neighbour at the north/west end, 8 =
platform on the near (east/south) side of the track instead of the far side.
Near-side platforms go to the front image so they are drawn over the train
standing on the tile; everything at ground level stays in the back image.

The art is ray-marched from a small heightfield scene per tile: tile-local
``a`` runs along the track (0 = north/west end), ``c`` across it (0 = far tile
edge, 0.5 = track axis, 1 = near edge); heights are screen pixels. Lighting
follows pak128: sun from the south at 60 degrees, so south faces are bright
and east faces dark. Needs numpy and Pillow.

Usage:
    python tools/gen_platforms.py station-rail/uzke-nastupiste
    python tools/gen_platforms.py station-rail/uzke-nastupiste --preview out.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

TILE = 128
SS = 3                      # supersampling per axis
KEY = (231, 255, 255)       # makeobj transparent colour
NEG = -1e9                  # "no surface" height

# pak128 lighting: sun from the south, 60 degrees up. Flat tops come out at
# factor 1.0, south faces 0.835, east faces 0.61 (matches the 140/102 greys of
# the pak128.cs asphalt platforms' concrete sides).
LIGHT = np.array([0.0, 0.5, 0.866])
AMB, DIF = 0.61, 0.45
TILE_W = 90.5               # tile side in world pixels (for slope normals)
Z_W = 1 / 0.866             # screen height px -> world px

# --- geometry (tile units) ---------------------------------------------------
EDGE = 0.115                # platform edge from the track axis (pak128.cs asphalt: 0.113)
PLAT_W = 0.17               # platform width (pak128.cs full-width asphalt: 0.387)
PLAT_H = 3.0                # platform height, screen px (pak128.cs asphalt: 4)
BAND = (0.365, 0.635)       # crossing band along the track, as on pak128.cs's
                            # Asfaltove_nastupiste_se_sluzebnim_prejezdem, so the two line up
DIP = 0.1                   # ramp length down into the crossing
END_GAP = 0.04              # a free platform end stops this far from the tile edge
END_RAMP = 0.12
TRACK_ZONE = 0.14           # crossing panels cover the track this far from the axis

# Rail pixels of the pak128.cs tracks at screen row 96, measured on
# rail_track_*: they sit half a pixel below the geometric axis, so the rails
# redrawn over crossing panels are placed in screen space to match exactly.
#   N-S: pixel x + 2*(y-96) in {58,59} and {70,71}; E-W: x - 2*(y-96) in {56,57}, {68,69}
RAILS = {0: ((58, 59), (70, 71)), 1: ((56, 57), (68, 69))}
FLANGEWAYS = {0: (60, 69), 1: (58, 67)}
RAIL_RGB = (123, 82, 49)
FLANGE_RGB = (58, 54, 50)

# Ballast palette sampled from the pak128.cs track sprites.
BALLAST = np.array([(123, 107, 99), (115, 99, 90), (132, 115, 115), (140, 123, 115),
                    (99, 90, 82), (123, 115, 107), (132, 123, 115), (107, 95, 86)], float)

# Simutrans special colours (image_t::rgbtab) plus the transparent key: a pixel
# that lands on one of these by accident is nudged by one step.
SPECIALS = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}

# material classes of a hit
M_NONE, M_FILL, M_BAND, M_TOP, M_WALL = 0, 1, 2, 3, 4


def ramp(x, x0, x1):
    return np.clip((x - x0) / (x1 - x0), 0, 1)


def hash2(ix, iy, seed=0):
    """Deterministic pseudo random in [0, 1) per integer cell."""
    h = (np.asarray(ix, np.int64) * 73856093) ^ (np.asarray(iy, np.int64) * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65536.0


def grid_lines(x, period, width):
    f = np.mod(x, period)
    return (f < width) | (f > period - 1e-4)


def rgb(t):
    return np.array(t, float)


def pixel_noise(seed):
    """Per output pixel random field at supersampled resolution, so textures
    stay crisp instead of being averaged away by the supersampling."""
    n = np.random.default_rng(seed).random((TILE, TILE))
    return n.repeat(SS, 0).repeat(SS, 1)


# --- surface styles -----------------------------------------------------------

class Style:
    """Albedo of a platform top (by along-track a and distance cr from the
    platform's track edge), its side walls, and the crossing band."""
    edge = 0.035

    def top(self, a, cr, n1, n2):
        raise NotImplementedError

    def side(self, a, z, n1, back):
        raise NotImplementedError


class Slabs(Style):
    """Large weathered concrete slabs with lighter edge stones (Světlá nad Sázavou)."""
    slab = 0.1

    def top(self, a, cr, n1, n2):
        across = (PLAT_W - self.edge) / 2
        ia = np.floor(a / self.slab).astype(int)
        ic = np.where(cr < self.edge, -1, np.floor((cr - self.edge) / across)).astype(int)
        r = hash2(ia, ic, 3)
        out = rgb((174, 167, 152)) + (r[..., None] - 0.5) * rgb((26, 24, 20)) + (n1[..., None] - 0.5) * 12
        stain = (n2 > 0.96)
        out = np.where(stain[..., None], out - 18, out)
        edge = cr < self.edge
        out = np.where(edge[..., None], rgb((196, 193, 184)) + (n1[..., None] - 0.5) * 8, out)
        joint = grid_lines(a, self.slab, 0.006) | (np.abs(cr - self.edge) < 0.004) \
            | (np.abs(cr - self.edge - across) < 0.004)
        return np.where(joint[..., None], rgb((126, 120, 108)), out)

    def side(self, a, z, n1, back):
        return rgb((184, 180, 170)) + (n1[..., None] - 0.5) * 8


class Pavers(Style):
    """Light interlocking pavers, Tischer edge, white tactile guidance strip (Nezamyslice)."""
    edge = 0.03

    def top(self, a, cr, n1, n2):
        out = rgb((180, 179, 174)) + (n1[..., None] - 0.5) * 9
        pa, pc = 0.032, 0.03
        row = np.floor(cr / pc).astype(int)
        joints = grid_lines(a + (row % 2) * pa / 2, pa, 0.004) | grid_lines(cr, pc, 0.004)
        out = np.where(joints[..., None], rgb((163, 162, 157)), out)
        edge = cr < self.edge
        out = np.where(edge[..., None], rgb((200, 199, 194)) + (n1[..., None] - 0.5) * 6, out)
        out = np.where((grid_lines(a, 0.1, 0.005) & edge)[..., None], rgb((158, 157, 152)), out)
        strip = np.abs(cr - PLAT_W * 0.55) < 0.012      # guidance strip along the middle
        rib = grid_lines(cr, 0.011, 0.004)
        out = np.where(strip[..., None], np.where(rib[..., None], rgb((202, 202, 196)), rgb((226, 226, 220))), out)
        return out

    def side(self, a, z, n1, back):
        return rgb((190, 189, 184)) + (n1[..., None] - 0.5) * 6


class Sudop(Style):
    """Old low platform: Sudop L-shaped concrete edge blocks on legs, gravel surface."""
    edge = 0.04

    def gravel(self, n1, n2, base=138):
        g = base + (n1 - 0.5) * 38 + (n2 > 0.92) * 20 - (n2 < 0.07) * 26
        return np.stack([g + 9, g + 1, g - 13], -1)

    def top(self, a, cr, n1, n2):
        out = self.gravel(n1, n2)
        edge = cr < self.edge
        out = np.where(edge[..., None], rgb((172, 172, 166)) + (n1[..., None] - 0.5) * 8, out)
        return np.where((grid_lines(a, 0.1, 0.005) & edge)[..., None], rgb((98, 96, 92)), out)

    def side(self, a, z, n1, back):
        blk = rgb((174, 174, 168)) + (n1[..., None] - 0.5) * 8
        leg = grid_lines(a + 0.013, 0.05, 0.026)
        face = np.where(((z < 1.4) & ~leg)[..., None], rgb((70, 66, 60)), blk)
        return np.where(back[..., None], self.gravel(n1, n1, 124), face)


STYLES = {"deska": Slabs(), "dlazba": Pavers(), "sudop": Sudop()}


# --- crossing band materials ---------------------------------------------------

def track_zone(c):
    return np.abs(c - 0.5) < TRACK_ZONE


def band_concrete(a, c, n1, n2):
    out = rgb((170, 168, 160)) + (n1[..., None] - 0.5) * 9
    out = np.where(track_zone(c)[..., None], rgb((160, 158, 150)) + (n1[..., None] - 0.5) * 9, out)
    joint = grid_lines(c, 0.07, 0.005) | grid_lines(a - BAND[0], (BAND[1] - BAND[0]) / 2, 0.005)
    return np.where(joint[..., None], rgb((118, 116, 110)), out)


def band_rubber(a, c, n1, n2):
    out = rgb((180, 179, 174)) + (n1[..., None] - 0.5) * 9       # paver path
    rub = rgb((62, 62, 64)) + (n1[..., None] - 0.5) * 7
    rub = np.where(grid_lines(a - BAND[0], (BAND[1] - BAND[0]) / 3, 0.006)[..., None], rgb((40, 40, 42)), rub)
    return np.where(track_zone(c)[..., None], rub, out)


def band_wood(a, c, n1, n2):
    out = STYLES["sudop"].gravel(n1, n2, 132)                     # gravel path
    pk = hash2(np.floor((a - BAND[0]) / 0.032).astype(int), 0, 9)
    wood = np.stack([118 + pk * 22, 88 + pk * 16, 58 + pk * 10], -1) + (n1[..., None] - 0.5) * 12
    wood = np.where(grid_lines(a - BAND[0], 0.032, 0.005)[..., None], rgb((62, 48, 36)), wood)
    return np.where(track_zone(c)[..., None], wood, out)


BANDS = {"beton": band_concrete, "pryz": band_rubber, "drevo": band_wood}


# --- scene -------------------------------------------------------------------------

class Scene:
    """One tile: optional half-island platform, ballast fill, crossing band."""

    def __init__(self, layout, style=None, band=None, platform=True, parts="all"):
        self.orient = layout & 1
        self.end_a1 = bool(layout & 2)
        self.end_a0 = bool(layout & 4)
        self.near = bool(layout & 8)
        self.style = STYLES[style] if style else None
        self.band = BANDS[band] if band else None
        self.platform = platform and style is not None
        self.parts = parts      # "all" | "ground" | "platform"

    def ac(self, u, v):
        return (v, u) if self.orient == 0 else (u, v)

    def crel(self, c):
        """Distance from the platform's track-side edge, 0 .. PLAT_W."""
        return (c - (0.5 + EDGE)) if self.near else ((0.5 - EDGE) - c)

    def in_plat_c(self, c):
        cr = self.crel(c)
        return (cr >= 0) & (cr < PLAT_W)

    def in_band(self, a):
        if self.band is None:
            return np.zeros(np.shape(a), bool)
        return (a >= BAND[0]) & (a <= BAND[1])

    def profile(self, a):
        """Platform height factor along the track; negative = no platform."""
        p = np.ones_like(a)
        if self.end_a0:
            p = np.where(a < END_GAP, -1.0, np.minimum(p, ramp(a, END_GAP, END_GAP + END_RAMP)))
        if self.end_a1:
            p = np.where(a > 1 - END_GAP, -1.0, np.minimum(p, ramp(1 - a, END_GAP, END_GAP + END_RAMP)))
        if self.band is not None:
            b0, b1 = BAND
            d = np.where(a < b0, ramp(b0 - a, 0, DIP), np.where(a > b1, ramp(a - b1, 0, DIP), 0.0))
            # past the band on a free end there is no platform left
            if self.end_a0:
                d = np.where(a < b0, -1.0, d)
            if self.end_a1:
                d = np.where(a > b1, -1.0, d)
            p = np.where((p < 0) | (d < 0), -1.0, np.minimum(p, d))
        return p

    def height(self, a, c):
        h = np.full(np.shape(a), NEG)
        if self.parts in ("all", "ground"):
            h = np.where(self.in_band(a), 0.0, h)
        if self.platform and self.parts in ("all", "platform"):
            p = self.profile(a)
            # where the platform has dipped to the ground the crossing band
            # (ground layer) takes over
            ph = np.where(p <= 1e-3, NEG, PLAT_H * p)
            h = np.where(self.in_plat_c(c), np.maximum(h, ph), h)
        return h


def march(scene, dz=0.2):
    """Ray-march every supersample; returns hit mask, hit height, u, v, wall kind
    (0 top, 1 east face, 2 south face)."""
    n = TILE * SS
    j, i = np.mgrid[0:n, 0:n]
    sx = (i + 0.5) / SS
    sy = (j + 0.5) / SS
    X = (sx - 64.0) / 64.0
    hit = np.zeros((n, n), bool)
    hz = np.zeros((n, n))
    hu = np.zeros((n, n))
    hv = np.zeros((n, n))
    wall = np.zeros((n, n), np.int8)
    pv = None
    z = PLAT_H + 0.5
    while z >= -dz:
        Yz = (sy - 64.5 + z) / 32.0
        u = (Yz + X) / 2
        v = (Yz - X) / 2
        inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
        a, c = scene.ac(u, v)
        h = np.where(inside, scene.height(a, c), NEG)
        new = (~hit) & inside & (h >= z)
        if new.any():
            hit |= new
            hz[new], hu[new], hv[new] = z, u[new], v[new]
            if pv is not None:
                is_wall = new & (h - z > dz * 1.5 + 0.05)
                if is_wall.any():
                    qa, qc = scene.ac(u, pv)
                    east = is_wall & (scene.height(qa, qc) >= z)
                    wall[east] = 1
                    wall[is_wall & ~east] = 2
        pv = v
        z -= dz
    return hit, hz, hu, hv, wall


def light(scene, u, v, wall, eps=1e-3):
    a, c = scene.ac(u, v)
    h0 = scene.height(a, c)
    a1, c1 = scene.ac(u + eps, v)
    a2, c2 = scene.ac(u, v + eps)
    dhdu = np.clip(scene.height(a1, c1) - h0, -50, 50) * Z_W / (eps * TILE_W)
    dhdv = np.clip(scene.height(a2, c2) - h0, -50, 50) * Z_W / (eps * TILE_W)
    nrm = np.stack([-dhdu, -dhdv, np.ones_like(dhdu)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    lit = AMB + DIF * np.clip(nrm @ LIGHT, 0, 1)
    lit = np.where(wall == 1, AMB, lit)
    return np.where(wall == 2, AMB + DIF * 0.5, lit)


def shade(scene, snow, seed):
    hit, hz, hu, hv, wall = march(scene)
    a, c = scene.ac(hu, hv)
    n1, n2, n3 = pixel_noise(seed), pixel_noise(seed + 1), pixel_noise(seed + 2)

    band = scene.in_band(a) & (hz <= 0.05)
    plat = hit & scene.in_plat_c(c) & (hz > 0.05) if scene.platform else np.zeros_like(hit)
    cls = np.where(hit, M_FILL, M_NONE)
    cls = np.where(hit & band, M_BAND, cls)
    cls = np.where(plat & (wall == 0), M_TOP, cls)
    cls = np.where(plat & (wall != 0), M_WALL, cls)
    cls = np.where(hit & ~band & ~plat & (wall != 0), M_WALL, cls)

    idx = (n3 * len(BALLAST)).astype(int) % len(BALLAST)
    col = BALLAST[idx].copy()
    if scene.platform:
        st = scene.style
        crl = scene.crel(c)
        col = np.where((cls == M_TOP)[..., None], st.top(a, crl, n1, n2), col)
        back = np.abs(crl - PLAT_W) < 0.02          # the wall away from the track
        col = np.where((cls == M_WALL)[..., None], st.side(a, hz, n1, back), col)
    if scene.band is not None:
        col = np.where((cls == M_BAND)[..., None], scene.band(a, c, n1, n2), col)
    if snow:
        flat_top = np.isin(cls, (M_FILL, M_BAND, M_TOP))
        s = 247 + (n2 > 0.5) * 8 - (n1 < 0.08) * 10
        snowc = np.stack([s, s, s + 0.0], -1)
        # crossings are kept clear: panels show through a thin, patchy snow cover
        cleared = (cls == M_BAND) & (n3 < 0.6)
        col = np.where((flat_top & ~cleared)[..., None], snowc,
                       np.where(cleared[..., None], col * 0.55 + snowc * 0.45, col))

    col = col * light(scene, hu, hv, wall)[..., None]

    # downsample: coverage by majority, colour by mean of covered samples
    kk = hit.reshape(TILE, SS, TILE, SS)
    cnt = kk.sum(axis=(1, 3))
    mask = cnt * 2 >= SS * SS
    tot = (col * hit[..., None]).reshape(TILE, SS, TILE, SS, 3).sum(axis=(1, 3))
    out = np.where(cnt[..., None] > 0, tot / np.maximum(cnt, 1)[..., None], 0)
    band_px = (cls == M_BAND).reshape(TILE, SS, TILE, SS).sum(axis=(1, 3)) * 2 >= SS * SS
    return out, mask, band_px


def draw_rails(out, band_px, orient):
    jj, ii = np.mgrid[0:TILE, 0:TILE]
    k = ii + 2 * (jj - 96) if orient == 0 else ii - 2 * (jj - 96)
    for x in FLANGEWAYS[orient]:
        out = np.where(((k == x) & band_px)[..., None], rgb(FLANGE_RGB), out)
    for pair in RAILS[orient]:
        on = np.isin(k, pair) & band_px
        out = np.where(on[..., None], rgb(RAIL_RGB), out)
    return out


def to_image(out, mask):
    q = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    img = np.empty((TILE, TILE, 3), np.uint8)
    img[:] = KEY
    img[mask] = q[mask]
    flat = img.reshape(-1, 3)
    val = (flat[:, 0].astype(np.int32) << 16) | (flat[:, 1].astype(np.int32) << 8) | flat[:, 2]
    bad = np.isin(val, list(SPECIALS)) & mask.reshape(-1)
    flat[bad, 2] = np.where(flat[bad, 2] > 0, flat[bad, 2] - 1, 1)
    return Image.fromarray(img, "RGB")


def render_layer(layout, style, band, platform, parts, snow):
    sc = Scene(layout, style, band, platform, parts)
    out, mask, band_px = shade(sc, snow, seed=17 + layout)
    if band is not None:
        out = draw_rails(out, band_px, sc.orient)
    return to_image(out, mask), bool(mask.any())


def render_tile(layout, style, band, platform, snow):
    """(back, front) images for one layout; front is None when empty."""
    near = bool(layout & 8) and platform and style is not None
    if near:
        back, _ = render_layer(layout, style, band, platform, "ground", snow)
        front, _ = render_layer(layout, style, band, platform, "platform", snow)
        return back, front
    back, _ = render_layer(layout, style, band, platform, "all", snow)
    return back, None


# --- icon / cursor -------------------------------------------------------------------

def track_image(orient):
    """A plain pak128-like track tile (ballast, sleepers, rails), only used as
    the backdrop of the toolbar icon."""
    img = np.zeros((TILE, TILE, 3))
    mask = np.zeros((TILE, TILE), bool)
    jj, ii = np.mgrid[0:TILE, 0:TILE]
    X = (ii + 0.5 - 64.0) / 64.0
    Y = (jj + 0.5 - 64.5) / 32.0
    u, v = (Y + X) / 2, (Y - X) / 2
    a, c = (v, u) if orient == 0 else (u, v)
    inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    bed = inside & (np.abs(c - 0.5) < 0.19)
    n = np.random.default_rng(3).random((TILE, TILE))
    img[bed] = BALLAST[(n[bed] * len(BALLAST)).astype(int) % len(BALLAST)]
    sleeper = bed & (np.abs(c - 0.5) < 0.086) & grid_lines(a, 1 / 16, 0.022)
    img[sleeper] = (196, 192, 190)
    mask |= bed
    k = ii + 2 * (jj - 96) if orient == 0 else ii - 2 * (jj - 96)
    for pair in RAILS[orient]:
        img[np.isin(k, pair) & bed] = RAIL_RGB
    return img, mask


def over(dst, dmask, img):
    arr = np.array(img.convert("RGB")).astype(float)
    m = ~np.all(arr == np.array(KEY, float), axis=-1)
    dst[m] = arr[m]
    return dst, dmask | m


def tile_closeup(style, band, platform):
    """One N-S track tile with the platform on its near side (layout 8),
    cropped around the track and platform."""
    back, front = render_tile(8, style, band, platform, snow=False)
    t, m = track_image(0)
    t, m = over(t, m, back)
    if front is not None:
        t, m = over(t, m, front)
    rgba = np.dstack([np.clip(t, 0, 255), m * 255.0]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA").crop((22, 74, 114, 129))


def draw_icon(closeup):
    """32x32 toolbar button in the pak128.cs style: bevelled grey square, a
    close-up of the platform by its track and a small passenger pictogram."""
    icon = Image.new("RGB", (32, 32))
    d = ImageDraw.Draw(icon)
    for y in range(32):
        g = int(208 - y * 2.0)
        d.line([(0, y), (31, y)], fill=(g, g, g))
    d.line([(0, 0), (31, 0)], fill=(245, 245, 245))
    d.line([(0, 0), (0, 31)], fill=(245, 245, 245))
    d.line([(1, 1), (30, 1)], fill=(224, 224, 224))
    d.line([(1, 1), (1, 30)], fill=(224, 224, 224))
    d.line([(0, 31), (31, 31)], fill=(83, 83, 83))
    d.line([(31, 0), (31, 31)], fill=(83, 83, 83))
    d.line([(1, 30), (30, 30)], fill=(108, 108, 108))
    d.line([(30, 1), (30, 30)], fill=(108, 108, 108))
    tile = closeup.resize((30, 18), Image.LANCZOS)
    arr = np.array(tile)
    arr[..., 3] = np.where(arr[..., 3] > 100, 255, 0)
    tile = Image.fromarray(arr, "RGBA")
    icon.paste(tile, (1, 12), tile)
    # passenger pictogram (two small figures), as on the pak128.cs stop icons
    for x0, body in ((4, (112, 104, 196)), (8, (212, 112, 44))):
        d.point([(x0 + 1, 3), (x0 + 2, 3)], fill=(236, 196, 156))
        d.rectangle([x0 + 1, 4, x0 + 2, 4], fill=(222, 182, 142))
        d.rectangle([x0, 5, x0 + 3, 8], fill=body)
        d.line([(x0 + 1, 9), (x0 + 1, 11)], fill=(44, 44, 56))
        d.line([(x0 + 2, 9), (x0 + 2, 11)], fill=(44, 44, 56))
    return icon


# --- sheets --------------------------------------------------------------------------

SHEET_ROWS = 9


def sheet_cell(kind, season, layout):
    """(row, col) of a layer image in the standard sheet."""
    row = (0 if kind == "back" else 2) + season * 4 + layout // 8
    return row, layout % 8


def build_sheet(gen):
    style = gen.get("style")
    band = gen.get("crossing")
    platform = gen.get("platform", True)
    sheet = Image.new("RGB", (TILE * 8, TILE * SHEET_ROWS), KEY)
    for season in (0, 1):
        for layout in range(16):
            back, front = render_tile(layout, style, band, platform, snow=season == 1)
            r, c = sheet_cell("back", season, layout)
            sheet.paste(back, (c * TILE, r * TILE))
            if front is not None:
                r, c = sheet_cell("front", season, layout)
                sheet.paste(front, (c * TILE, r * TILE))
    # build cursor: the plain far-side tile (layout 0); the icon shows the
    # near side so the platform sits in front of its track
    cur, _ = render_tile(0, style, band, platform, snow=False)
    sheet.paste(cur, (0, 8 * TILE))
    sheet.paste(draw_icon(tile_closeup(style, band, platform)), (TILE, 8 * TILE))
    return sheet


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("station_dir", type=Path)
    ap.add_argument("--only", action="append", help="render only these sprite names")
    args = ap.parse_args()
    spec = yaml.safe_load((args.station_dir / "station.yaml").read_text(encoding="utf-8"))
    out_dir = args.station_dir / "sprites"
    out_dir.mkdir(exist_ok=True)
    for obj in spec["objects"]:
        name = obj["sprite"]
        if args.only and name not in args.only:
            continue
        gen = obj.get("generate")
        if not gen:
            continue
        sheet = build_sheet(gen)
        sheet.save(out_dir / f"{name}.png", optimize=True)
        print(f"wrote {out_dir / (name + '.png')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
