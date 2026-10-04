#!/usr/bin/env python3
"""ÖBB railjet coaches (vehicle-rail/obb/railjet), CZR art turned for both ways round.

    python tools/railrender/obb_railjet.py [--preview DIR]

writes vehicle-rail/obb/railjet/sprites/railjet.png.

The art is the CZR ÖBB railjet (Lubak91, CZR-vehicles-rail-pass-OeBB.pak), frozen in
src/czr_obb_railjet.png in the pak's object order (Bmpvz, 3x Bmpz, ARbmpz, Ampz,
Afmpz; pak-extracted, so 4 px low and lifted here). CZR drew the Afmpz with its cab
leading and gave its "RailjetReverse" set the very same sprites, so in CZR the
direct set ends in a cab car facing the coaches and the reversed set's cars are
not turned round. Here every car exists both ways round:

  rows 0-4  the set with the locomotive at the Bmpvz end leading: the cars as
            drawn, the Afmpz turned (cab at the tail)
  rows 5-9  the same set travelling the other way (Afmpz leading): every car
            turned, the Afmpz as drawn (cab leading)

A car turned round is its opposite-direction tile (column c + 4): the screen faces
it shows are the same, only its ends swap. That tile sits where the engine puts a
length-13 car travelling the other way, so it is moved onto the bounding box of the
car's own tile in that column (checked on the CZR ČD railjet, whose separately
drawn cab-leading Afmpz 890 matches this to 1 px).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import railkit as R  # noqa: E402
from render import T  # noqa: E402

SRC = os.path.join(HERE, "src", "czr_obb_railjet.png")
OUT = os.path.join(REPO, "vehicle-rail", "obb", "railjet", "sprites", "railjet.png")
# source rows (CZR object order): Bmpvz_1, Bmpz_2..4 (identical art), ARbmpz_5, Ampz_6, Afmpz_7
BMPVZ, BMPZ, ARBMPZ, AMPZ, AFMPZ = 0, 1, 4, 5, 6
LABELS = ["Bmpvz", "Bmpz", "ARbmpz", "Ampz", "Afmpz (cab at tail)",
          "Bmpvz turned", "Bmpz turned", "ARbmpz turned", "Ampz turned", "Afmpz (cab leading)"]


def source_rows():
    from PIL import Image
    src = np.array(Image.open(SRC).convert("RGB"))
    rows = []
    for r in range(src.shape[0] // 128):
        band = src[r * 128:(r + 1) * 128]
        lifted = np.zeros_like(band)
        lifted[:, :] = T
        lifted[:-4] = band[4:]
        rows.append([lifted[:, c * 128:(c + 1) * 128].copy() for c in range(8)])
    return rows


def _bbox(t):
    ys, xs = np.nonzero((t != np.array(T, np.uint8)).any(2))
    return xs.min(), ys.min(), xs.max(), ys.max()


def _shift(t, dx, dy):
    out = np.zeros_like(t)
    out[:, :] = T
    h, w = t.shape[:2]
    out[max(0, dy):min(h, h + dy), max(0, dx):min(w, w + dx)] = \
        t[max(0, -dy):min(h, h - dy), max(0, -dx):min(w, w - dx)]
    return out


def turned(row):
    """The car turned round: column c + 4 moved onto the bounding box of column c."""
    out = []
    for c in range(8):
        src = row[(c + 4) % 8]
        a, b = _bbox(row[c]), _bbox(src)
        dx = int(round(((a[0] + a[2]) - (b[0] + b[2])) / 2))
        dy = int(round(((a[1] + a[3]) - (b[1] + b[3])) / 2))
        out.append(_shift(src, dx, dy))
    return out


def rows():
    s = source_rows()
    direct = [s[BMPVZ], s[BMPZ], s[ARBMPZ], s[AMPZ], turned(s[AFMPZ])]
    return direct + [turned(r) for r in direct[:4]] + [s[AFMPZ]]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        os.makedirs(prev, exist_ok=True)
    rs = rows()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    R.save_rows(rs, OUT)
    if prev:
        R.preview(rs, os.path.join(prev, "obb_railjet.png"), z=4, labels=LABELS)
    print("wrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
