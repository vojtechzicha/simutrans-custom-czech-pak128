#!/usr/bin/env python3
"""Generate the VZ rail signal sheets (signal-rail/<set>/sprites/*.png).

Every object in ``signal.yaml`` with a ``generate:`` entry gets a sheet in the
layout of tools/sign_extract.py: 4 columns (images N, S, W, E) by one row per
state, plus a last row with the cursor (col 0) and the 32×32 toolbar icon
(col 1). The pak128.cs art these are built from lives in
``signal-rail/pak128cs-source/sprites`` (extracted with sign_extract.py).

``generate`` forms:
  {port: <pak128.cs name>}           copy the sheet 1:1
  {style: new|old|dwarf, function: main|autoblock|shunt|pre|choose|long|P}
                                      D1 signal: a pak128.cs base of that style
                                      plus the function's identification plate
  {lt: new|old|dwarf, head: choose|calling-on, letter: bool}
                                      LT as a light entry signal (vjezdové
                                      návěstidlo, like choose but without the
                                      direction indicator box; letter: white L
                                      on the red plate), 12 images: red (no
                                      train let in), green (route straight
                                      through the throat), yellow (a diverging
                                      route: two yellows, 40 km/h, on the
                                      AŽD 70 and SSSR heads; one on the dwarf)
  {d3: LT|P}                          drawn D3 objects (lichoběžníková tabulka,
                                      low Místo zastavení board, no lamp)
  {hradlo: automatic|manual, cabinet: bool, house: pair|all, hut: brick|prefab}
                                      block signal of a hradlo (block post): a
                                      main signal with the red plate and the
                                      red-and-white mast band (D1 čl. 67: every
                                      main signal for trains except AB).
                                      automatic: AŽD 70, optionally the relay
                                      cabinet at the foot. manual: SSSR, plus
                                      the block post hut outboard of the track,
                                      along it from the mast; house: pair draws the hut only in
                                      the N and W images, so a pair (one signal
                                      per direction) shows one hut

Function code (the plate under the head, real D1 plate colours): main none
(a two-lamp head, red and green only, on the red-white mast; the only D1 signal
without a plate), autoblock (the Block objects, is_autoblock) white on a white
mast (D1 čl. 69), in 12 images: red, green, yellow (one yellow lamp), shunt blue, presignal black, long red, choose red + direction indicator box on
top of the head (lit when the signal is clear), P red + white track-number
plate. The D1 LTs are light entry signals (see lt: below).

Usage:
    python tools/gen_signals.py signal-rail/signals [--only ID ...] [--preview DIR]
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "signal-rail" / "pak128cs-source" / "sprites"
TILE = 128
BG = (231, 255, 255)

# image_t::rgbtab specials: always lit (glow at night)
LAMP_RED, LAMP_GREEN, LAMP_YELLOW = (0xFF, 0x21, 0x1D), (0x01, 0xDD, 0x01), (0xFF, 0xFF, 0x53)
UNLIT = (70, 70, 60)
ICON_GREY = (156, 156, 156)
BLACK, WHITE, PALE = (18, 18, 18), (238, 240, 240), (226, 230, 232)
PLATES = {  # fill, rim
    "white": (PALE, (24, 24, 24)),
    "blue": ((36, 80, 196), PALE),
    "black": ((22, 22, 22), PALE),
    "red": ((198, 32, 32), PALE),
}
# which side of the mast the lamps face, per image direction (col 0..3)
LAMP_SIDE = [-1, 1, 1, -1]
FRONT = [True, False, True, False]

# style -> function -> (base object, plate, extra)
BASES = {
    "new": {
        "main": ("AZD70_Signal", None, None),
        "autoblock": ("AZD70_3aspect_permissive", "white", None),
        "shunt": ("AZD70_Signal_Shunting", "blue", None),
        "pre": ("AZD70_PreSignal", "black", None),
        "choose": ("AZD70_3aspect_choose", "red", "indicator"),
        "long": ("AZD70_LongSignal", "red", None),
        "P": ("AZD70_3aspect_absolute", "red", "number"),
    },
    "old": {
        "main": ("SSSR_Signal", None, None),
        "autoblock": ("SSSR_3aspect_permissive", "white", None),
        "shunt": ("SSSR_Signal_Shunting", "blue", None),
        "pre": ("SSSR_PreSignal", "black", None),
        "choose": ("SSSR_3aspect_choose", "red", "indicator"),
        "long": ("SSSR_LongSignal", "red", None),
        "P": ("SSSR_3aspect_absolute", "red", "number"),
    },
    "dwarf": {
        "main": ("SSSR_LongSignal_Dwarf", None, None),
        "autoblock": ("SSSR_LongSignal_Dwarf", "white", None),
        "shunt": ("SSSR_Signal_Shunting_Dwarf", "blue", None),
        "pre": ("SSSR_PreSignal_Station_Dwarf", "black", None),
        "choose": ("SSSR_LongSignal_Dwarf", "red", "indicator"),
        "long": ("SSSR_LongSignal_Dwarf", "red", None),
        "P": ("SSSR_LongSignal_Dwarf", "red", "number"),
    },
}
STATE_ROWS = {"pre": 3, "choose": 3, "autoblock": 3}  # everything else: red + green
# choose: red, green, yellow (sent to another platform / a diverging route; the
# two-yellow 40 km/h row of the base, or the green lamp recoloured on the dwarf)
# autoblock: red, green, yellow (výstraha: the block ends at a signal other than
# an autoblock, or has a switch in it; the single-yellow row of the permissive
# base, or the green lamp recoloured on the dwarf)
ICON_LABEL = {"main": "B", "autoblock": "AB", "shunt": "S", "pre": "PR", "choose": "C", "long": "L", "P": "P", "LT": "LT"}
ICON_CHIP = {"main": None, "autoblock": "white", "shunt": "blue", "pre": "black", "choose": "red", "long": "red", "P": "red"}

FONT = {  # 3×5
    "B": ["110", "101", "110", "101", "110"], "S": ["011", "100", "010", "001", "110"],
    "P": ["110", "101", "110", "100", "100"], "R": ["110", "101", "110", "101", "101"],
    "C": ["011", "100", "100", "100", "011"], "L": ["100", "100", "100", "100", "111"],
    "T": ["111", "010", "010", "010", "010"], "D": ["110", "101", "101", "101", "110"],
    "3": ["110", "001", "010", "001", "110"],
    "H": ["101", "101", "111", "101", "101"], "A": ["010", "101", "111", "101", "101"],
}


# ---------------------------------------------------------------- sheet I/O

def load_sheet(name: str) -> Image.Image:
    return Image.open(SOURCE / f"{name}.png").convert("RGB")


def tile(sheet: Image.Image, row: int, col: int) -> Image.Image:
    return sheet.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE))


def new_sheet(rows: int) -> Image.Image:
    return Image.new("RGB", (4 * TILE, (rows + 1) * TILE), BG)


def pixels(im: Image.Image) -> list[tuple[int, int]]:
    px = im.load()
    return [(x, y) for y in range(TILE) for x in range(TILE) if px[x, y] != BG]


# ---------------------------------------------------------------- geometry

class Anchor:
    """Where the plate goes in one image direction, measured on the red tile."""

    def __init__(self, im: Image.Image, col: int, dwarf: bool):
        pts = pixels(im)
        self.side = LAMP_SIDE[col]
        self.front = FRONT[col]
        self.y0 = min(y for _, y in pts)
        self.y1 = max(y for _, y in pts)
        ext = min if self.side < 0 else max
        if dwarf:
            rows = range(self.y0 + 4, self.y0 + 9)  # at the plate's height
            self.edge = ext(x for x, y in pts if y in rows)
            self.hb = self.y0 + 3
        else:
            per_row = {}
            for x, y in pts:
                if self.y1 - 28 <= y <= self.y1 - 8:
                    per_row.setdefault(y, []).append(x)
            self.edge = int(statistics.median(ext(xs) for xs in per_row.values()))
            px = im.load()
            self.hb = self.y0 + 12
            for y in range(self.y0 + 6, self.y1):
                beyond = range(self.edge - 10, self.edge) if self.side < 0 else range(self.edge + 1, self.edge + 11)
                if all(px[x, y] == BG for x in beyond):
                    self.hb = y - 1
                    break
        head = [x for x, y in pts if y <= self.y0 + 3]
        self.head_cx = round(sum(head) / len(head))

    def plate_box(self, dy: int = 0, h: int = 5) -> tuple[int, int, int, int]:
        y = self.hb + 2 + dy
        if self.front:
            x = self.edge - 4 if self.side < 0 else self.edge + 1
            return x, y, 4, h
        x = self.edge + self.side
        return x, y, 1, h


def draw_plate(im, box, kind):
    fill, rim = PLATES[kind]
    x0, y0, w, h = box
    px = im.load()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            border = w > 1 and (x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1))
            px[x, y] = rim if border else fill


def draw_number_plate(im, box):
    x0, y0, w, h = box
    px = im.load()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            px[x, y] = WHITE
    if w >= 4:  # a "1"
        for y in range(y0 + 1, y0 + h - 1):
            px[x0 + 2, y] = BLACK
        px[x0 + 1, y0 + 2] = BLACK


def draw_indicator(im, a: Anchor, lit: bool):
    px = im.load()
    w = 4 if a.front else 2
    x0 = a.head_cx - w // 2
    for y in range(a.y0 - 4, a.y0):
        for x in range(x0, x0 + w):
            px[x, y] = (20, 24, 26)
    col = LAMP_YELLOW if lit else UNLIT
    if a.front:
        px[x0 + 1, a.y0 - 3] = px[x0 + 2, a.y0 - 3] = px[x0 + 1, a.y0 - 2] = col
    else:
        lamp_x = x0 + (w - 1 if a.side > 0 else 0)
        px[lamp_x, a.y0 - 3] = px[lamp_x, a.y0 - 2] = col


def trapezoid(im, cx, ybot, number=True, reflect=False, wb=11, wt=7, h=7):
    """Lichoběžníková tabulka face-on: white, black rim, standing on its long side."""
    px = im.load()
    for i in range(h):
        y = ybot - i
        w = round(wb - (wb - wt) * i / (h - 1))
        x0 = cx - w // 2
        for x in range(x0, x0 + w):
            edge = i in (0, h - 1) or x in (x0, x0 + w - 1)
            px[x, y] = BLACK if edge else WHITE
    if number:
        for y in range(ybot - 5, ybot - 1):
            px[cx, y] = BLACK
        px[cx - 1, ybot - 4] = BLACK
    if reflect:
        for x, y in [(cx - wb // 2 + 1, ybot - 1), (cx + (wb - 1) // 2 - 1, ybot - 1),
                     (cx - wt // 2 + 1, ybot - h + 2), (cx + (wt - 1) // 2 - 1, ybot - h + 2)]:
            px[x, y] = (178, 180, 188)


# A flat board stands across the track, so it is drawn in the pak128 projection
# like pak128.cs's own boards (Minimum*): the N and W images show its painted
# face, S and E its grey back, and it slants 1 px down per 2 px across the
# screen in N/S (the board's plane runs east-west) and 1 px up in W/E.
BACK_FILL, BACK_RIM = (132, 134, 138), (92, 94, 98)
SLANT = [0.5, 0.5, -0.5, -0.5]


SS = 8  # supersampling for board outlines


def _mask(poly, col, cx, ybot):
    """Pixel-coverage mask (dict (x, y) -> bool) of a polygon given in board
    coordinates (u across from the centre, v up from the bottom edge)."""
    from PIL import ImageDraw
    k = SLANT[col]
    pts = [((cx + u + 0.5) * SS, (ybot + 1 - v + k * u) * SS) for u, v in poly]
    m = Image.new("L", (TILE * SS, TILE * SS), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    small = m.resize((TILE, TILE), Image.BOX)
    return {(x, y) for y in range(TILE) for x in range(TILE) if small.getpixel((x, y)) >= 128}


def board(im, col, cx, ybot, outer, inner, fill, rim, extras=()):
    """A flat board across the track. outer/inner are its outline and the
    outline of its painted field (rim = between them) in board coordinates;
    N/W images get fill/rim, S/E the grey back. extras: (u, v, colour) marks
    on the face (reflectors, a digit)."""
    px = im.load()
    out_m, in_m = _mask(outer, col, cx, ybot), _mask(inner, col, cx, ybot)
    for x, y in out_m:
        if FRONT[col]:
            px[x, y] = fill if (x, y) in in_m else rim
        else:
            px[x, y] = BACK_FILL if (x, y) in in_m else BACK_RIM
    if FRONT[col]:
        k = SLANT[col]
        for u, v, colour in extras:
            px[cx + round(u), ybot - round(v) + math.floor(k * u + 0.5)] = colour


def trapezoid_poly(wb, wt, h, inset=0.0):
    """Isosceles trapezoid on its longer base, shrunk by inset px."""
    slope = (wb - wt) / 2 / h            # side inset per unit height
    side = inset * math.hypot(1, slope)  # horizontal inset of the slanted side
    return [(-wb / 2 + side + inset * slope, inset), (wb / 2 - side - inset * slope, inset),
            (wt / 2 - side + inset * slope, h - inset), (-wt / 2 + side - inset * slope, h - inset)]


def lt_board(im, col, cx, ybot, number, wb=13, wt=9, h=7):
    """Lichoběžníková tabulka (D1 čl. 976, drawing Ž09-3): white isosceles
    trapezoid on its longer base, black rim, reflectors in the corners; the D1
    variant (čl. 1002) carries a black track number instead."""
    extras = []
    if number:
        extras = [(0, v, BLACK) for v in range(2, h - 1)] + [(-1, h - 3, BLACK)]
    else:
        r = (178, 180, 188)
        extras = [(-wb / 2 + 2, 1, r), (wb / 2 - 2, 1, r), (-wt / 2 + 1.5, h - 2, r), (wt / 2 - 1.5, h - 2, r)]
    board(im, col, cx, ybot, trapezoid_poly(wb, wt, h), trapezoid_poly(wb, wt, h, 1.0),
          WHITE, BLACK, extras)


# ---------------------------------------------------------------- D1

def gen_d1(style: str, function: str) -> Image.Image:
    base, plate, extra = BASES[style][function]
    src = load_sheet(base)
    src_rows = src.height // TILE - 1
    rows = STATE_ROWS.get(function, 2)
    recolour = function in ("choose", "autoblock") and src_rows < rows      # dwarf: no yellow row
    assert src_rows >= rows or recolour, f"{base} has {src_rows} state rows, need {rows}"
    dwarf = style == "dwarf"
    out = new_sheet(rows)
    for col in range(4):
        a = Anchor(tile(src, 0, col), col, dwarf)
        for row in range(rows):
            if recolour and row == 2:
                im = to_yellow(tile(src, 1, col))
            else:
                im = tile(src, row, col)
            if plate:
                draw_plate(im, a.plate_box(), plate)
            if extra == "number":
                draw_number_plate(im, a.plate_box(dy=6, h=6))
            if extra == "indicator":
                draw_indicator(im, a, lit=row >= 1)
            out.paste(im, (col * TILE, row * TILE))
    finish_skin(out, rows, src, src_rows, ICON_LABEL[function], ICON_CHIP.get(function))
    return out


# ---------------------------------------------------------------- LT (light)

# base per style and head; (red, green, yellow) state rows in that base.
# Yellow is the two-yellow 40 km/h aspect where the head has a lower yellow
# lamp (AŽD 70 5-lamp heads, the SSSR double head).
LT_BASES = {
    ("new", "choose"): ("AZD70_3aspect_choose", (0, 3, 2)),
    ("new", "calling-on"): ("AZD70_4aspect_choose", (0, 4, 3)),      # 5 lamps incl. the white calling-on lamp
    ("old", "choose"): ("SSSR_3aspect_choose", (0, 3, 2)),
    ("dwarf", "choose"): ("SSSR_LongSignal_Dwarf", (0, 1, None)),   # single yellow = the green lamp recoloured
}


def draw_letter_plate(im, box):
    """Solid red plate with a white L, the entry signal's letter (a rim would
    leave no room for the letter at this size)."""
    x0, y0, w, h = box
    px = im.load()
    red = PLATES["red"][0]
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            px[x, y] = red
    if w >= 4:
        for y in range(y0 + 1, y0 + h - 1):
            px[x0 + 1, y] = WHITE
        px[x0 + 2, y0 + h - 2] = WHITE


def to_yellow(im):
    px = im.load()
    for y in range(TILE):
        for x in range(TILE):
            if px[x, y] == LAMP_GREEN:
                px[x, y] = LAMP_YELLOW
    return im


def gen_lt(style: str, head: str, letter: bool) -> Image.Image:
    base, rows = LT_BASES[(style, head)]
    src = load_sheet(base)
    src_rows = src.height // TILE - 1
    dwarf = style == "dwarf"
    states = new_sheet(3)
    for col in range(4):
        a = Anchor(tile(src, 0, col), col, dwarf)
        for i, r in enumerate(rows):
            im = tile(src, r if r is not None else rows[1], col)
            if r is None:
                im = to_yellow(im)
            if letter:
                draw_letter_plate(im, a.plate_box(h=6))
            else:
                draw_plate(im, a.plate_box(), "red")
            states.paste(im, (col * TILE, i * TILE))
    finish_skin(states, 3, src, src_rows, "LT", "red")
    return states


# ---------------------------------------------------------------- D3

def foot(col: int) -> tuple[int, int]:
    """Mast foot of the AŽD 70 signals in this direction (x centre, y)."""
    im = tile(load_sheet("AZD70_OneWaySignal"), 0, col)
    pts = pixels(im)
    y1 = max(y for _, y in pts)
    xs = [x for x, y in pts if y >= y1 - 1]
    return round(sum(xs) / len(xs)), y1


def post(im, x, top, bot, band_top=None):
    """A 2 px steel post; band_top starts the oblique black-and-white band
    (označovací pás) of the lichoběžníková tabulka, right under its board."""
    px = im.load()
    for y in range(top, bot + 1):
        px[x, y] = (112, 118, 120)
        px[x + 1, y] = (70, 76, 78)
    for xx in range(x - 1, x + 3):
        px[xx, bot + 1] = (48, 48, 50)
    if band_top is not None:
        for y in range(band_top, band_top + 12):
            px[x, y] = BLACK if (y // 2) % 2 else WHITE
            px[x + 1, y] = BLACK if ((y + 1) // 2) % 2 else (200, 200, 200)


def misto_zastaveni(im, col, cx, ybot, w=9, h=6):
    """Návěst Místo zastavení (D1 čl. 988): white board on its long side with a
    red border."""
    outer = [(-w / 2, 0), (w / 2, 0), (w / 2, h), (-w / 2, h)]
    inner = [(-w / 2 + 1, 1), (w / 2 - 1, 1), (w / 2 - 1, h - 1), (-w / 2 + 1, h - 1)]
    board(im, col, cx, ybot, outer, inner, WHITE, (206, 30, 30))


def gen_d3(kind: str) -> Image.Image:
    rows = 1 if kind == "LT" else 2
    out = new_sheet(rows)
    for col in range(4):
        fx, fy = foot(col)
        x = fx - 1
        for row in range(rows):
            im = Image.new("RGB", (TILE, TILE), BG)
            if kind == "LT":
                post(im, x, fy - 32, fy, band_top=fy - 28)
                lt_board(im, col, x + 1, fy - 29, number=False)
            else:
                # a low sign, about half the LT's height, with no lamp: red and
                # green look the same (the train's behaviour shows the state)
                post(im, x, fy - 19, fy)
                misto_zastaveni(im, col, x + 1, fy - 17)
            out.paste(im, (col * TILE, row * TILE))
    base = load_sheet("AZD70_OneWaySignal")
    finish_skin(out, rows, base, base.height // TILE - 1, kind, None, d3=True, picture=kind)
    return out


# ---------------------------------------------------------------- hradlo

# tile coordinates: x east, y south (0..1 across the tile), z up in pixels;
# the tile diamond's top vertex (x = y = 0) is at (64, 64)
def iso(x, y, z=0.0):
    return 64 + (x - y) * 64, 64 + (x + y) * 32 - z


def to_tile(sx, sy):
    """Screen pixel of a ground point -> tile (x, y)."""
    a, b = (sx - 64) / 64, (sy - 64) / 32
    return (a + b) / 2, (b - a) / 2


def shade(c, f):
    return tuple(max(0, min(255, round(v * f))) for v in c)


def poly(im, pts, colour):
    from PIL import ImageDraw
    ImageDraw.Draw(im).polygon([(round(px), round(py)) for px, py in pts], fill=colour)


def box(im, x0, x1, y0, y1, z0, z1, colour):
    """Axis-aligned box with pak128 lighting: south face x0.835, east face
    x0.61, top x1.0."""
    poly(im, [iso(x0, y1, z0), iso(x1, y1, z0), iso(x1, y1, z1), iso(x0, y1, z1)], shade(colour, 0.835))
    poly(im, [iso(x1, y0, z0), iso(x1, y1, z0), iso(x1, y1, z1), iso(x1, y0, z1)], shade(colour, 0.61))
    poly(im, [iso(x0, y0, z1), iso(x1, y0, z1), iso(x1, y1, z1), iso(x0, y1, z1)], colour)


HUTS = {  # walls, roof, trim
    "brick": ((224, 208, 170), (160, 64, 44), (120, 44, 34)),     # plastered hut, red tiled roof
    "prefab": ((176, 180, 178), (84, 88, 90), (60, 62, 64)),      # grey prefabricated booth, flat roof
}
LIT_GLASS = (0x4D, 0x4D, 0x4D)   # special: dark by day, lit at night (the post is manned)

# hut footprint per image direction (outboard of the mast, clear of the track)
# (x0, x1, y0, y1); along the track from the mast so the hut never covers it
HUT_AT = {0: (0.80, 0.98, 0.30, 0.54), 1: (0.02, 0.20, 0.46, 0.70),
          2: (0.30, 0.54, 0.02, 0.20), 3: (0.46, 0.70, 0.80, 0.98)}


def hut(im, col, kind):
    walls, roof, trim = HUTS[kind]
    x0, x1, y0, y1 = HUT_AT[col]
    wall_h = 13
    box(im, x0, x1, y0, y1, 0, wall_h, walls)
    px = im.load()

    def dot(x, y, z, c):
        sx, sy = iso(x, y, z)
        px[round(sx), round(sy)] = c
    # windows on the south and east faces (lit specials), a door on the south
    for f in (0.3, 0.7):
        for dz in (7, 8, 9):
            dot(x0 + (x1 - x0) * f, y1, dz, LIT_GLASS)
            dot(x1, y0 + (y1 - y0) * f, dz, LIT_GLASS)
    for dz in range(1, 8):
        dot(x0 + (x1 - x0) * 0.5, y1, dz, shade(trim, 0.8))
    if kind == "prefab":
        box(im, x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, wall_h, wall_h + 2, roof)
        return
    # gabled roof, ridge along the longer side
    zr, e = wall_h + 7, 0.02
    if (x1 - x0) >= (y1 - y0):
        ym = (y0 + y1) / 2
        poly(im, [iso(x0 - e, y0 - e, wall_h), iso(x1 + e, y0 - e, wall_h), iso(x1 + e, ym, zr), iso(x0 - e, ym, zr)], shade(roof, 0.9))
        poly(im, [iso(x1, y0, wall_h), iso(x1, y1, wall_h), iso(x1, ym, zr)], shade(walls, 0.61))
        poly(im, [iso(x0 - e, y1 + e, wall_h), iso(x1 + e, y1 + e, wall_h), iso(x1 + e, ym, zr), iso(x0 - e, ym, zr)], roof)
    else:
        xm = (x0 + x1) / 2
        poly(im, [iso(x0 - e, y0 - e, wall_h), iso(xm, y0 - e, zr), iso(xm, y1 + e, zr), iso(x0 - e, y1 + e, wall_h)], shade(roof, 0.9))
        poly(im, [iso(x0, y1, wall_h), iso(x1, y1, wall_h), iso(xm, y1, zr)], shade(walls, 0.835))
        poly(im, [iso(x1 + e, y0 - e, wall_h), iso(xm, y0 - e, zr), iso(xm, y1 + e, zr), iso(x1 + e, y1 + e, wall_h)], shade(roof, 0.75))


def over(im, top):
    """Paste the non-background pixels of top onto im."""
    tp, ip = top.load(), im.load()
    for y in range(TILE):
        for x in range(TILE):
            if tp[x, y] != BG:
                ip[x, y] = tp[x, y]


# main signals with the red-white mast band: automatic = AŽD 70, manual = SSSR
BASE = {"automatic": "AZD70_3aspect_absolute", "manual": "SSSR_3aspect_absolute"}


def cabinet(im, col):
    """Relay cabinet at the mast foot, outboard (automatic hradlo)."""
    mx, my = to_tile(*foot(col))
    ox, oy = {0: (0.08, 0.06), 1: (-0.08, -0.06), 2: (0.06, -0.08), 3: (-0.06, 0.08)}[col]
    cx, cy = mx + ox, my + oy
    box(im, cx - 0.03, cx + 0.03, cy - 0.025, cy + 0.025, 0, 8, (150, 156, 150))


def gen_hradlo(kind: str, with_cabinet: bool, house: str, hut_kind: str) -> Image.Image:
    src = load_sheet(BASE[kind])
    src_rows = src.height // TILE - 1
    out = new_sheet(2)
    for col in range(4):
        a = Anchor(tile(src, 0, col), col, False)
        mx, my = to_tile(*foot(col))
        for row in range(2):
            sig = tile(src, row, col)
            draw_plate(sig, a.plate_box(), "red")
            extra = None
            if kind == "manual" and (house == "all" or col in (0, 2)):
                x0, x1, y0, y1 = HUT_AT[col]
                extra = (lambda im, c=col: hut(im, c, hut_kind), (x0 + x1) / 2 + (y0 + y1) / 2)
            elif kind == "automatic" and with_cabinet:
                extra = (lambda im, c=col: cabinet(im, c), 99 if col in (1, 3) else -1)
            if extra:
                draw, d = extra
                im = Image.new("RGB", (TILE, TILE), BG)
                if d > mx + my:             # in front of the mast
                    over(im, sig)
                    draw(im)
                else:
                    draw(im)
                    over(im, sig)
                sig = im
            out.paste(sig, (col * TILE, row * TILE))
    finish_skin(out, 2, src, src_rows, "AH" if kind == "automatic" else "HR", "red",
                picture=None if kind == "automatic" else "HR")
    return out


# ---------------------------------------------------------------- cursor / icon

def draw_text(px, x, y, s, colour):
    for ch in s:
        for dy, line in enumerate(FONT[ch]):
            for dx, bit in enumerate(line):
                if bit == "1":
                    px[x + dx, y + dy] = colour
        x += 4


def finish_skin(out, rows, src, src_rows, label, chip, d3=False, picture=None):
    """Cursor = the generated red image facing the viewer; icon = the base
    object's icon with its type label replaced by ours."""
    cursor = out.crop((0, 0, TILE, TILE))
    out.paste(cursor, (0, rows * TILE))
    icon = src.crop((TILE, src_rows * TILE, TILE + 32, src_rows * TILE + 32)).copy()
    px = icon.load()
    bgc = ICON_GREY
    x_from = 2 if picture else 17
    for y in range(3, 29):
        for x in range(x_from, 30):
            px[x, y] = bgc
    if picture == "LT":
        for y in range(14, 28):
            px[9, y] = (90, 96, 98)
        mini = Image.new("RGB", (TILE, TILE), BG)
        trapezoid(mini, 20, 20, number=False, wb=11, wt=7, h=7)
        for y in range(14, 21):
            for x in range(15, 26):
                if mini.getpixel((x, y)) != BG:
                    px[x - 11, y - 6] = mini.getpixel((x, y))
    elif picture == "P":
        for y in range(18, 28):
            px[9, y] = (90, 96, 98)
        for y in range(12, 18):
            for x in range(5, 14):
                px[x, y] = (206, 30, 30) if y in (12, 17) or x in (5, 13) else WHITE
    elif picture == "HR":
        for y in range(8, 28):
            px[6, y] = (90, 96, 98)
        for y in range(4, 11):
            for x in range(4, 9):
                px[x, y] = (22, 24, 26)
        px[6, 6] = LAMP_RED
        for y in range(12, 16):                   # red plate
            for x in range(4, 8):
                px[x, y] = (198, 32, 32)
        for y in range(20, 28):                   # hut
            for x in range(9, 20):
                px[x, y] = (224, 208, 170)
        for i in range(6):                        # roof
            for x in range(8 + i, 21 - i):
                px[x, 19 - i] = (160, 64, 44)
        px[12, 23] = px[16, 23] = LIT_GLASS
    if chip:
        fill, rim = PLATES[chip]
        for y in range(5, 11):
            for x in range(21, 26):
                px[x, y] = rim if x in (21, 25) or y in (5, 10) else fill
    text = ("D3 " + label) if d3 else label
    tw = 4 * len(text.replace(" ", "")) + 2 * text.count(" ")
    ty = 20 if picture else 14
    x = (31 - tw) if picture else 23 - (4 * len(label) - 1) // 2
    for part in text.split(" "):
        draw_text(px, x, ty, part, (16, 16, 208))
        x += 4 * len(part) + 2
    out.paste(icon, (TILE, rows * TILE))


# ---------------------------------------------------------------- main

def build(obj: dict) -> Image.Image:
    g = obj["generate"]
    if "lt" in g:
        return gen_lt(g["lt"], g.get("head", "choose"), g.get("letter", False))
    if "port" in g:
        return load_sheet(g["port"])
    if "d3" in g:
        return gen_d3(g["d3"])
    if "hradlo" in g:
        return gen_hradlo(g["hradlo"], g.get("cabinet", False), g.get("house", "pair"), g.get("hut", "brick"))
    return gen_d1(g["style"], g["function"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir", type=Path)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--preview", type=Path, help="also write 3× previews of every sheet here")
    args = ap.parse_args()
    spec = yaml.safe_load((args.set_dir / "signal.yaml").read_text(encoding="utf-8"))
    out_dir = args.set_dir / "sprites"
    out_dir.mkdir(exist_ok=True)
    n = 0
    for obj in spec["objects"]:
        if "generate" not in obj or (args.only and obj["id"] not in args.only):
            continue
        sheet = build(obj)
        sheet.save(out_dir / f"{obj['sprite']}.png")
        if args.preview:
            args.preview.mkdir(parents=True, exist_ok=True)
            sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(args.preview / f"{obj['sprite']}.png")
        n += 1
    print(f"{n} sheets -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
