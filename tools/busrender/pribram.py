"""MHD Příbram (Arriva Střední Čechy): the red-black scheme on the Conecto LF.

    python tools/busrender/pribram.py [--preview DIR]

The town fleet wears two paints in 2026 (seznam-autobusu register, 3 Nov
2026): red all over (9502, 9535, 9537: the VTPsim sheet pribramcervena) and
the red-black of the other 13 (MHD Příbram "červeno-černá"): the same red
with the black skirt along the lower side under the wheel-arch tops (photo
seznam-autobusu 254265 of 9522). This repaints the red sheet: the red zones
keep their colour and shading, the lowest two rows of the sides go black.
The Crossway LE CITY 12M (9829) in the same scheme comes from crossway_town.py
(t-pribram-rc).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import odis_town as T                                                   # noqa: E402

SRC = "vehicle-bus/mhd-pribram/conecto_lf/sprites/pribramcervena.png"
OUT = "vehicle-bus/mhd-pribram/conecto_lf/sprites/pribramcervenocerna.png"
BLACK = (0x1E, 0x1E, 0x20)
ROWS = 2                        # the black skirt, pixel rows
L12 = [[11.5, 12.0, 12.5]]


def z_red(c):
    """the Příbram red of the VTPsim sheet"""
    if T.hexc(c) in T.H.SPECIAL:
        return None
    r, g, b = c
    if r > 0x90 and g < 0x50 and b < 0x50:
        return "red"
    return None


def skirt(o, paint, geo, d, r):
    """the lowest ROWS painted pixels of every side-face column in black,
    shaded like the red (the fitted box's heights are too coarse on this
    VTPsim sheet for a cut by metres)"""
    if d not in T.SIDE:
        return o
    o = o.copy()
    side = paint & ((geo["face"] == 4) | (geo["face"] == 5))
    for x in range(128):
        ys = np.where(side[:, x])[0]
        for y in ys[-ROWS:]:
            k = max(0.70, min(1.15, T.lum(o[y, x]) / T.lum((0xDE, 0x1F, 0x2A))))
            o[y, x] = T.scaled(BLACK, k)
    return o


def rows():
    src = T.load_rows(SRC)
    reds = {}
    for t in src[0]:
        for y, x in zip(*np.where(np.ones(t.shape[:2], bool))):
            c = tuple(int(v) for v in t[y, x])
            if z_red(c):
                reds[c] = reds.get(c, 0) + 1
    base = max(reds, key=reds.get)                  # the sheet's own red, so the red stays as it is
    return T.repaint(src, z_red, {"red": (base, base)}, L12, skirt)


def main(argv):
    out = rows()
    T.save_sheet(out, os.path.join(REPO, OUT))
    print(OUT)
    if "--preview" in argv:
        d = argv[argv.index("--preview") + 1]
        os.makedirs(d, exist_ok=True)
        T.preview(out, os.path.join(d, "pribram-conecto_lf-pribramcervenocerna.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
