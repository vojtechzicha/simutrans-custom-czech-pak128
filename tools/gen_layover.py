#!/usr/bin/env python3
"""Render the sprite sheets for the bus layover (odstavné stání) road stops.

Reads ``station-road/<set>/station.yaml`` and writes ``sprites/<sprite>.png``
for every object with a ``generate: {layover: 1|2|3}`` block. The stops are
fork objects (``layover=`` key, see the station.yaml): the engine parks buses
in the bays drawn here, at fixed bay centres in the map frame, so the bay
geometry below is shared with the engine and must not drift.

Geometry (tile units, measured on native pak128.cs art): the road asphalt
spans +-0.335 tile across the centre line (city_road, Road_030..090), lane
centres sit at +-0.135 and a bus is about 0.13 tile wide.

    layover=1  one side, two bays side by side, centres 0.275 and 0.415
               layouts 0 N-S bays east, 1 E-W bays north, 2 N-S bays west,
               3 E-W bays south (side(L-1) = rotate90(side(L)), as
               gebaeude_t::rotate90 turns a 4-layout building L -> L-1)
    layover=2  both sides, one bay outside each lane, centres +-0.40
               layouts 0 N-S, 1 E-W
    layover=3  dead end, two bays either side of the axis, centres +-0.25,
               the rest of the tile paved as a turning area
               layouts 0..3 = the road leaves the tile to the S, E, N, W
               (stock 4-layout terminal stop order)

Everything lies at ground level, so only back images are drawn; buses are
drawn over them. Sheet = the standard station sheet (see gen_platforms.py):
row 0 back images season 0, row 4 back images season 1 (snow), row 8 col 0
the build cursor and col 1 the 32x32 icon.

Usage:
    python tools/gen_layover.py station-road/odstavne-stani [--only SPRITE] [--preview DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_platforms as gp  # noqa: E402  (march, light, noise, special-colour guard)

TILE, SS, KEY = gp.TILE, gp.SS, gp.KEY

# --- bay geometry shared with the engine (map frame, tile units) ---------------
ROAD_EDGE = 0.335           # native asphalt half-width
LANE = 0.135                # native lane centre
BAYS = {
    1: (0.275, 0.415),      # one side
    2: (0.40,),             # both sides (mirrored)
    3: (0.25,),             # dead end (mirrored)
}
BUS_HALF = 0.065            # half the width of a native bus

# --- drawing ---------------------------------------------------------------------
KERB_W = 0.016              # kerb stone width
KERB_H = 1.5                # kerb height, screen px
LINE_W = 0.017              # painted line width (about 1 px)
OUTER = 0.5 - KERB_W        # pavement ends here, the kerb runs to the tile edge

ASPHALT = (88, 90, 92)      # pak128.cs city_road grey
CONCRETE = (158, 156, 150)  # bus bays: concrete slabs, as at Czech bus stops
JOINT = (130, 128, 122)
KERB = (182, 180, 174)
WHITE = (226, 226, 220)
YELLOW = (232, 196, 40)


def local(layover, layout, u, v):
    """Tile coords (u east, v south, 0..1) -> (a along the road, c across it).

    layover 1: c > 0 is the bay side. layover 3: a = 0 at the open end.
    """
    x, y = u - 0.5, v - 0.5
    if layover == 1:
        return {0: (v, x), 1: (u, -y), 2: (v, -x), 3: (u, y)}[layout]
    if layover == 2:
        return (v, x) if layout == 0 else (u, y)
    # dead end: the road leaves to S, E, N, W
    return {0: (1 - v, x), 1: (1 - u, y), 2: (v, x), 3: (u, y)}[layout]


# --- dead end outline ---------------------------------------------------------------
FLARE = 0.14                # the paved area widens from the road to the tile over this
CORNER_R = 0.24             # rounded corners at the closed end


def dead_end_half_width(a):
    """Half-width of the paved turning area at distance a from the open edge."""
    t = np.clip(a / FLARE, 0, 1)
    t = t * t * (3 - 2 * t)
    w = ROAD_EDGE + (0.5 - ROAD_EDGE) * t
    # rounded corners at the closed end (a = 1)
    d = np.clip(a - (1 - CORNER_R), 0, None)
    corner = (0.5 - CORNER_R) + np.sqrt(np.clip(CORNER_R ** 2 - d ** 2, 0, None))
    return np.where(a > 1 - CORNER_R, np.minimum(w, corner), w)


class Scene:
    """Heightfield for gp.march / gp.light: only the kerb stones stand up."""

    def __init__(self, layover, layout):
        self.layover, self.layout = layover, layout

    def ac(self, u, v):
        return u, v

    def paved(self, u, v):
        a, c = local(self.layover, self.layout, u, v)
        ac = np.abs(c)
        if self.layover == 1:
            return (c >= BAYS[1][0] - BUS_HALF - LINE_W) & (c < 0.5)
        if self.layover == 2:
            return (ac >= ROAD_EDGE - LINE_W) & (ac < 0.5)
        return ac < dead_end_half_width(a)

    def kerb(self, u, v):
        a, c = local(self.layover, self.layout, u, v)
        ac = np.abs(c)
        if self.layover == 1:
            return c >= OUTER
        if self.layover == 2:
            return ac >= OUTER
        w = dead_end_half_width(a)
        # kerb along the outline, except where the road continues (a ~ 0)
        rim = (ac >= w - KERB_W) & (ac < w)
        far = a >= 1 - KERB_W
        return (rim & (a > 0.02)) | (far & (ac < w))

    def height(self, u, v):
        inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
        h = np.where(self.paved(u, v), 0.0, gp.NEG)
        h = np.where(self.paved(u, v) & self.kerb(u, v), KERB_H, h)
        return np.where(inside, h, gp.NEG)


def dashed(a, on=0.07, off=0.055):
    return np.mod(a, on + off) < on


def albedo(layover, layout, u, v, z, n1, n2):
    """Surface colour of every sample (before lighting)."""
    a, c = local(layover, layout, u, v)
    ac = np.abs(c)
    noise = (n1[..., None] - 0.5) * 10
    col = np.broadcast_to(np.array(ASPHALT, float), a.shape + (3,)) + noise

    def paint(mask, rgb):
        nonlocal col
        col = np.where(mask[..., None], np.array(rgb, float) + noise * 0.6, col)

    if layover == 1:
        a_in, b_out = BAYS[1]
        lo = a_in - BUS_HALF - LINE_W               # lane edge of bay A
        bay = (c >= lo) & (c < OUTER)
        paint(bay, CONCRETE)
        paint(bay & ((np.mod(a, 0.125) < 0.012) | (np.abs(c - (a_in + b_out) / 2) < 0.006)), JOINT)
        paint((c >= lo) & (c < lo + LINE_W) & dashed(a), WHITE)          # lay-by edge, broken
        mid = (a_in + b_out) / 2
        paint((np.abs(c - mid) < LINE_W / 2) & dashed(a + 0.03, 0.04, 0.04), WHITE)  # bay divider
        paint((c >= OUTER - LINE_W * 1.6) & (c < OUTER - LINE_W * 0.6) & zigzag(a, c, OUTER - LINE_W * 1.1), YELLOW)
    elif layover == 2:
        bay = (ac >= ROAD_EDGE - LINE_W) & (ac < OUTER)
        paint(bay, CONCRETE)
        paint(bay & (np.mod(a, 0.125) < 0.012), JOINT)
        paint((ac >= ROAD_EDGE - LINE_W) & (ac < ROAD_EDGE) & dashed(a), WHITE)
        paint((ac >= OUTER - LINE_W * 1.6) & (ac < OUTER - LINE_W * 0.6) & zigzag(a, ac, OUTER - LINE_W * 1.1), YELLOW)
    else:
        b = BAYS[3][0]
        lo, hi = b - BUS_HALF - 0.03, b + BUS_HALF + 0.03
        a0, a1 = 0.10, 0.90
        bay = (ac >= lo) & (ac < hi) & (a >= a0) & (a < a1)
        paint(bay, CONCRETE)
        paint(bay & (np.mod(a, 0.125) < 0.012), JOINT)
        edge = bay & ((ac < lo + LINE_W) | (ac >= hi - LINE_W) | (a < a0 + LINE_W) | (a >= a1 - LINE_W))
        paint(edge, WHITE)
        # an arrow-free turning area: a white centre circle hint at the closed end
        r = np.hypot(c, a - 0.62)
        paint((np.abs(r - 0.09) < LINE_W / 2) & (ac < 0.09 + LINE_W), WHITE)

    kerb_top = Scene(layover, layout).kerb(u, v) & (z > KERB_H - 0.3)
    kerb_side = Scene(layover, layout).kerb(u, v) & (z <= KERB_H - 0.3)
    paint(kerb_top, KERB)
    paint(kerb_side, tuple(x * 0.92 for x in KERB))
    return col


def zigzag(a, c, centre, period=0.06, amp=None):
    """Yellow zigzag (V 12c) along the kerb of the stop area."""
    f = np.abs(np.mod(a / period, 1.0) - 0.5) * 2         # 0..1 triangle
    return np.abs(c - centre) < LINE_W * 0.5 + 0.004 * f


def render(layover, layout, snow):
    sc = Scene(layover, layout)
    hit, hz, hu, hv, wall = gp.march(sc)
    n1, n2, n3 = gp.pixel_noise(31 + layout), gp.pixel_noise(32 + layout), gp.pixel_noise(33 + layout)
    col = albedo(layover, layout, hu, hv, hz, n1, n2)
    if snow:
        flat = hit & (wall == 0)
        s = 246 + (n2 > 0.5) * 8 - (n1 < 0.08) * 10
        snowc = np.stack([s, s, s + 0.0], -1)
        # bays and the turning area get driven over: patchy, grey-ish snow
        mix = np.where(n3 < 0.35, 0.45, 0.85)[..., None]
        col = np.where(flat[..., None], col * (1 - mix) + snowc * mix, col)
    col = col * gp.light(sc, hu, hv, wall)[..., None]
    kk = hit.reshape(TILE, SS, TILE, SS)
    cnt = kk.sum(axis=(1, 3))
    mask = cnt * 2 >= SS * SS
    tot = (col * hit[..., None]).reshape(TILE, SS, TILE, SS, 3).sum(axis=(1, 3))
    out = np.where(cnt[..., None] > 0, tot / np.maximum(cnt, 1)[..., None], 0)
    return gp.to_image(out, mask)


LAYOUTS = {1: 4, 2: 2, 3: 4}


def draw_icon(tile):
    """32x32 toolbar button: bevelled grey square, the tile in miniature and a
    blue P sign (IP 11, parking) with a small bus."""
    icon = Image.new("RGB", (32, 32))
    d = ImageDraw.Draw(icon)
    for y in range(32):
        g = int(208 - y * 2.0)
        d.line([(0, y), (31, y)], fill=(g, g, g))
    d.line([(0, 0), (31, 0)], fill=(245, 245, 245))
    d.line([(0, 0), (0, 31)], fill=(245, 245, 245))
    d.line([(0, 31), (31, 31)], fill=(83, 83, 83))
    d.line([(31, 0), (31, 31)], fill=(83, 83, 83))
    arr = np.array(tile.convert("RGB"))
    m = ~np.all(arr == np.array(KEY), axis=-1)
    rgba = np.dstack([arr, m * 255]).astype(np.uint8)
    thumb = Image.fromarray(rgba, "RGBA").crop((0, 62, 128, 130)).resize((30, 16), Image.LANCZOS)
    t = np.array(thumb)
    t[..., 3] = np.where(t[..., 3] > 110, 255, 0)
    thumb = Image.fromarray(t, "RGBA")
    icon.paste(thumb, (1, 15), thumb)
    # IP 11 blue square with a white P
    d.rectangle([2, 2, 12, 12], fill=(30, 80, 170))
    d.line([(5, 4), (5, 10)], fill=(245, 245, 245))
    d.line([(6, 4), (8, 4)], fill=(245, 245, 245))
    d.line([(6, 7), (8, 7)], fill=(245, 245, 245))
    d.point([(9, 5), (9, 6)], fill=(245, 245, 245))
    # small bus, side view
    d.rectangle([15, 5, 28, 10], fill=(200, 40, 40))
    d.rectangle([16, 6, 27, 7], fill=(60, 70, 80))
    d.point([(17, 11), (18, 11), (25, 11), (26, 11)], fill=(30, 30, 30))
    return icon


def build_sheet(layover):
    sheet = Image.new("RGB", (TILE * 8, TILE * gp.SHEET_ROWS), KEY)
    for season in (0, 1):
        for layout in range(LAYOUTS[layover]):
            img = render(layover, layout, snow=season == 1)
            r, c = gp.sheet_cell("back", season, layout)
            sheet.paste(img, (c * TILE, r * TILE))
    cur = render(layover, 0, snow=False)
    sheet.paste(cur, (0, 8 * TILE))
    sheet.paste(draw_icon(cur), (TILE, 8 * TILE))
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
        gen = obj.get("generate") or {}
        if "layover" not in gen or (args.only and obj["sprite"] not in args.only):
            continue
        build_sheet(gen["layover"]).save(out_dir / f"{obj['sprite']}.png", optimize=True)
        print(f"wrote {out_dir / (obj['sprite'] + '.png')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
