#!/usr/bin/env python3
"""Generate the VZ rail signal sheets (signal-rail/<set>/sprites/*.png).

Every object in ``signal.yaml`` with a ``generate:`` entry gets a sheet in the
layout of tools/sign_extract.py: 4 columns (images N, S, W, E) by one row per
state, plus a last row with the cursor (col 0) and the 32×32 toolbar icon
(col 1). The pak128.cs art these are built from lives in
``signal-rail/pak128cs-source/sprites`` (extracted with sign_extract.py).

``generate`` forms:
  {port: <pak128.cs name>}           copy the sheet 1:1
  {style: new|old|dwarf, function: block|shunt|pre|choose|long|P|LT}
                                      D1 signal: a pak128.cs base of that style
                                      plus the function's identification plate
  {d3: LT|P}                          drawn D3 objects (lichoběžníková tabulka,
                                      Místo zastavení board with a lamp)

Function code (the plate under the head, real D1 plate colours): block white,
shunt blue, presignal black, long red, choose red + direction indicator box on
top of the head (lit when the signal is clear), P red + white track-number
plate. LT replaces the head of the style's mast with a numbered
lichoběžníková tabulka.

Usage:
    python tools/gen_signals.py signal-rail/signals [--only ID ...] [--preview DIR]
"""

from __future__ import annotations

import argparse
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
        "block": ("AZD70_3aspect_permissive", "white", None),
        "shunt": ("AZD70_Signal_Shunting", "blue", None),
        "pre": ("AZD70_PreSignal", "black", None),
        "choose": ("AZD70_3aspect_choose", "red", "indicator"),
        "long": ("AZD70_LongSignal", "red", None),
        "P": ("AZD70_3aspect_absolute", "red", "number"),
        "LT": ("AZD70_OneWaySignal", None, "board"),
    },
    "old": {
        "block": ("SSSR_3aspect_permissive", "white", None),
        "shunt": ("SSSR_Signal_Shunting", "blue", None),
        "pre": ("SSSR_PreSignal", "black", None),
        "choose": ("SSSR_3aspect_choose", "red", "indicator"),
        "long": ("SSSR_LongSignal", "red", None),
        "P": ("SSSR_3aspect_absolute", "red", "number"),
        "LT": ("SSSR_Signal", None, "board"),
    },
    "dwarf": {
        "block": ("SSSR_LongSignal_Dwarf", "white", None),
        "shunt": ("SSSR_Signal_Shunting_Dwarf", "blue", None),
        "pre": ("SSSR_PreSignal_Station_Dwarf", "black", None),
        "choose": ("SSSR_LongSignal_Dwarf", "red", "indicator"),
        "long": ("SSSR_LongSignal_Dwarf", "red", None),
        "P": ("SSSR_LongSignal_Dwarf", "red", "number"),
        "LT": ("SSSR_LongSignal_Dwarf", None, "board"),
    },
}
STATE_ROWS = {"pre": 3, "LT": 1}  # everything else: red + green
ICON_LABEL = {"block": "B", "shunt": "S", "pre": "PR", "choose": "C", "long": "L", "P": "P", "LT": "LT"}
ICON_CHIP = {"block": "white", "shunt": "blue", "pre": "black", "choose": "red", "long": "red", "P": "red"}

FONT = {  # 3×5
    "B": ["110", "101", "110", "101", "110"], "S": ["011", "100", "010", "001", "110"],
    "P": ["110", "101", "110", "100", "100"], "R": ["110", "101", "110", "101", "101"],
    "C": ["011", "100", "100", "100", "011"], "L": ["100", "100", "100", "100", "111"],
    "T": ["111", "010", "010", "010", "010"], "D": ["110", "101", "101", "101", "110"],
    "3": ["110", "001", "010", "001", "110"],
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


def slab(im, cx, ybot, h=7, w=2):
    """A board seen edge-on."""
    px = im.load()
    for y in range(ybot - h + 1, ybot + 1):
        px[cx, y] = (200, 202, 204)
        if w > 1:
            px[cx + 1, y] = (90, 92, 96)


def erase_above(im, y):
    px = im.load()
    for yy in range(0, y + 1):
        for x in range(TILE):
            px[x, yy] = BG


def is_band(p):
    r, g, b = p
    return (r > 150 and g < 130) or min(p) > 160 or (b > 150 and r < 130)


# ---------------------------------------------------------------- D1

def gen_d1(style: str, function: str) -> Image.Image:
    base, plate, extra = BASES[style][function]
    src = load_sheet(base)
    src_rows = src.height // TILE - 1
    rows = STATE_ROWS.get(function, 2)
    assert src_rows >= rows, f"{base} has {src_rows} state rows, need {rows}"
    dwarf = style == "dwarf"
    out = new_sheet(rows)
    for col in range(4):
        a = Anchor(tile(src, 0, col), col, dwarf)
        for row in range(rows):
            im = tile(src, row, col)
            if extra == "board":
                im = lt_from(im, a, dwarf)
            else:
                draw_plate(im, a.plate_box(), plate)
                if extra == "number":
                    draw_number_plate(im, a.plate_box(dy=6, h=6))
                if extra == "indicator":
                    draw_indicator(im, a, lit=row == 1)
            out.paste(im, (col * TILE, row * TILE))
    finish_skin(out, rows, src, src_rows, ICON_LABEL[function], ICON_CHIP.get(function),
                picture="LT" if function == "LT" else None)
    return out


def lt_from(im, a: Anchor, dwarf: bool):
    px = im.load()
    if dwarf:
        cut = a.y0 + 9
        erase_above(im, cut)
        row = [x for x in range(TILE) if px[x, cut + 2] != BG]
        cx = round(sum(row) / len(row))
        if a.front:
            trapezoid(im, cx, cut + 1, wb=9, wt=5, h=6)
        else:
            slab(im, cx, cut + 1, h=6)
        return im
    # mast: black-and-white band, head replaced by the board
    if a.front:
        cols = [a.edge, a.edge - a.side]
        for y in range(a.hb + 1, a.y1 - 8):
            for x in cols:
                if px[x, y] != BG and is_band(px[x, y]):
                    px[x, y] = BLACK if (y // 2) % 2 else WHITE
    erase_above(im, a.hb)
    lo, hi = sorted((a.edge, a.edge - 4 * a.side))
    row = [x for x in range(lo, hi + 1) if px[x, a.hb + 3] != BG]
    cx = round(sum(row) / len(row)) if row else a.edge
    if a.front:
        trapezoid(im, cx, a.hb + 1)
    else:
        slab(im, cx, a.hb + 1)
    return im


# ---------------------------------------------------------------- D3

def foot(col: int) -> tuple[int, int]:
    """Mast foot of the AŽD 70 signals in this direction (x centre, y)."""
    im = tile(load_sheet("AZD70_OneWaySignal"), 0, col)
    pts = pixels(im)
    y1 = max(y for _, y in pts)
    xs = [x for x, y in pts if y >= y1 - 1]
    return round(sum(xs) / len(xs)), y1


def post(im, x, top, bot, band):
    px = im.load()
    for y in range(top, bot + 1):
        px[x, y] = (112, 118, 120)
        px[x + 1, y] = (70, 76, 78)
    for xx in range(x - 1, x + 3):
        px[xx, bot + 1] = (48, 48, 50)
    if band:
        for y in range(top + 10, top + 24):
            px[x, y] = BLACK if (y // 2) % 2 else WHITE
            px[x + 1, y] = BLACK if ((y + 1) // 2) % 2 else (200, 200, 200)


def misto_zastaveni(im, cx, ytop, front, w=9, h=6):
    """Návěst Místo zastavení: white board on its long side with a red border."""
    px = im.load()
    if not front:
        for y in range(ytop, ytop + h):
            px[cx, y] = (206, 30, 30)
            px[cx + 1, y] = (150, 26, 26)
        return
    x0 = cx - w // 2
    for y in range(ytop, ytop + h):
        for x in range(x0, x0 + w):
            border = y in (ytop, ytop + h - 1) or x in (x0, x0 + w - 1)
            px[x, y] = (206, 30, 30) if border else WHITE


def lamp(im, cx, ytop, colour, front, side):
    px = im.load()
    w = 3 if front else 2
    x0 = cx - 1 if front else cx
    for y in range(ytop, ytop + 4):
        for x in range(x0, x0 + w):
            px[x, y] = (22, 24, 26)
    lx = cx if front else (x0 + 1 if side > 0 else x0)
    px[lx, ytop + 1] = px[lx, ytop + 2] = colour


def gen_d3(kind: str) -> Image.Image:
    rows = 1 if kind == "LT" else 2
    out = new_sheet(rows)
    for col in range(4):
        fx, fy = foot(col)
        x = fx - 1
        for row in range(rows):
            im = Image.new("RGB", (TILE, TILE), BG)
            if kind == "LT":
                post(im, x, fy - 30, fy, band=True)
                if FRONT[col]:
                    trapezoid(im, x + 1, fy - 29, number=False, reflect=True, wb=13, wt=8, h=8)
                else:
                    slab(im, x, fy - 29, h=8)
            else:
                post(im, x, fy - 26, fy, band=False)
                misto_zastaveni(im, x + 1 if FRONT[col] else x, fy - 30, FRONT[col])
                lamp(im, x + 1 if FRONT[col] else x, fy - 35, LAMP_RED if row == 0 else LAMP_GREEN,
                     FRONT[col], LAMP_SIDE[col])
            out.paste(im, (col * TILE, row * TILE))
    base = load_sheet("AZD70_OneWaySignal")
    finish_skin(out, rows, base, base.height // TILE - 1, kind, None, d3=True, picture=kind)
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
        for y in range(16, 28):
            px[9, y] = (90, 96, 98)
        for y in range(10, 16):
            for x in range(5, 14):
                px[x, y] = (206, 30, 30) if y in (10, 15) or x in (5, 13) else WHITE
        for y in range(4, 9):
            for x in range(8, 11):
                px[x, y] = (22, 24, 26)
        px[9, 6] = LAMP_RED
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
    if "port" in g:
        return load_sheet(g["port"])
    if "d3" in g:
        return gen_d3(g["d3"])
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
