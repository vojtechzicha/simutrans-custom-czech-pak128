#!/usr/bin/env python3
"""Preview a multi-vehicle consist exactly as Simutrans places it.

Simutrans anchors every vehicle at its FRONT and puts the next vehicle's anchor
`length` carunits (16 per tile) behind it (see convoi_t: `dist = driven - vlen`).
A sprite drawn like a native 8-carunit section (body centred in the tile) has
its body centre 4 carunits behind the anchor, so vehicles whose `length` is not
8 must have their body
shifted along the direction of travel by (4 - length/2) carunits, or a mixed
consist shows gaps / overlaps at the joints (e.g. 12 + 6 centred sections leave
a 3-carunit gap). This tool composites the sheet rows with the engine's spacing
for all 8 directions so such errors are visible before going in-game.

Usage:
    python tools/consist_preview.py <sheet.png> <len0,len1,...> <out.png> [--rows r0,r1,...] [--zoom 4]

`len*` are the family.yaml `length` values in consist order (lead vehicle first);
`--rows` picks the sprite row of each vehicle (default 0, 1, 2, ...). Use the
same row twice for vehicles that share a row (e.g. reverse:true rear motors are
not modelled; preview those separately).
"""
import argparse
import numpy as np
from PIL import Image, ImageDraw

T = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
# screen pixels per carunit of forward travel (pak128: 64 px x / 32 px y per tile
# along a straight direction; diagonal steps are scaled by the diagonal multiplier)
S2 = 2 ** 0.5
PER_CU = {"w": (-4, -2), "e": (4, 2), "n": (4, -2), "s": (-4, 2),
          "ne": (4 * S2, 0), "sw": (-4 * S2, 0), "nw": (0, -2 * S2), "se": (0, 2 * S2)}
BG = (96, 104, 96)


def load_row(path, row):
    im = np.array(Image.open(path).convert("RGB"))
    return [im[row * 128:(row + 1) * 128, c * 128:(c + 1) * 128] for c in range(8)]


def compose(rows, lengths, d, size=320):
    canvas = np.zeros((size, size, 3), np.uint8); canvas[:, :] = BG
    vx, vy = PER_CU[d]
    placed = []
    back = 0
    for i, tiles in enumerate(rows):
        placed.append((i, 96 - back * vx, 96 - back * vy))
        back += lengths[i]
    # painter's order like the engine: farther up the screen first
    for i, ox, oy in sorted(placed, key=lambda p: (p[2], p[1])):
        t = rows[i][DIRS.index(d)]
        ys, xs = np.where(~np.all(t == np.array(T), axis=2))
        X = xs + int(round(ox)); Y = ys + int(round(oy))
        ok = (X >= 0) & (X < size) & (Y >= 0) & (Y < size)
        canvas[Y[ok], X[ok]] = t[ys[ok], xs[ok]]
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("lengths"); ap.add_argument("out")
    ap.add_argument("--rows"); ap.add_argument("--zoom", type=int, default=4)
    a = ap.parse_args()
    lengths = [int(x) for x in a.lengths.split(",")]
    rows_idx = [int(x) for x in a.rows.split(",")] if a.rows else list(range(len(lengths)))
    rows = [load_row(a.sheet, r) for r in rows_idx]
    tiles = []
    for d in DIRS:
        c = compose(rows, lengths, d)
        ys, xs = np.where(np.any(c != np.array(BG), axis=2))
        c = c[max(0, ys.min() - 3):ys.max() + 4, max(0, xs.min() - 3):xs.max() + 4]
        tiles.append((d, Image.fromarray(c).resize((c.shape[1] * a.zoom, c.shape[0] * a.zoom), Image.NEAREST)))
    halves = [tiles[:4], tiles[4:]]
    W = max(sum(t.width + 8 for _, t in h) for h in halves)
    H = sum(max(t.height for _, t in h) + 18 for h in halves)
    img = Image.new("RGB", (W, H), (255, 255, 255)); dr = ImageDraw.Draw(img)
    y = 0
    for h in halves:
        x = 0
        for d, t in h:
            dr.text((x + 2, y + 2), d, fill=(0, 0, 0)); img.paste(t, (x, y + 16)); x += t.width + 8
        y += max(t.height for _, t in h) + 18
    img.save(a.out)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
