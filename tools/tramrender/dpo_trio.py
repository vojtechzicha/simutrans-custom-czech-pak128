"""DPO Ostrava Inekon 01 Trio (T2001) sheet, derived from the Škoda 03T Astra
(LTM 10.08) sheet (TommPa9) that it has shared so far.

    python tools/tramrender/dpo_trio.py [--variant A|B] [--preview DIR]

The Astra sheet is read at run time (vehicle-tram/dpo/ltm1008_astra) and left
untouched; the result is written to vehicle-tram/dpo/t2001_trio. Only the front
end of the front section (row 0) changes; the middle section and the rear end
look the same on both types in the photos (1258 vs 1201 / 1212), so rows 1 and
2 are copied.

Differences from the photos (Commons: Trio 1255, 1256, 1258, 1259; Astra 1201,
1207, 1212), at the 7-11 px the face has here:

* Front mask: the Astra has a straight blue band under the windscreen with the
  headlights in it. The Trio has a blue crescent under the windscreen that dips
  to a point in the middle (logo), with the headlights in the white corners
  beside it.
* Cab roof: the Astra has a tall white louvred A/C box right at the front edge;
  the Trio a lower, light-grey fairing set further back.
* Variant B also: the windscreen leans back further and the nose bulges 1 px
  forward at bumper height (side views); the glass and roof corners are rounded
  (front view); the blue window band runs round the cab side window, where the
  Astra's cab side is white.

Doors, pantograph position and the side livery split behind the cab do not
differ visibly at this scale.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tramkit as tk  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ASTRA = os.path.join(ROOT, "vehicle-tram", "dpo", "ltm1008_astra", "sprites", "dpomodrozluta.png")
TRIO = os.path.join(ROOT, "vehicle-tram", "dpo", "t2001_trio", "sprites", "dpomodrozluta.png")

H = tk.hexrgb
BLUE, YELLOW, WHITE = H("4284C5"), H("FFCE08"), H("EFEFEF")
LAMP = H("FFFF53")
UNIT_TOP, UNIT_SIDE = (226, 228, 230), (160, 163, 166)
AC_COLS = {H("F7F7F7"), H("EFEFEF"), H("848484"), H("7B7B7B")}
ROOF_COLS = [H("B5B5B5"), H("BDBDBD"), H("C5C5C5"), H("ADADAD")]
# Astra A/C unit bounding box per view (x0, y0, x1, y1, exclusive), row 0
AC_BOX = {0: (44, 73, 49, 77), 1: (62, 60, 65, 62), 2: (79, 73, 82, 77), 3: (75, 80, 80, 84),
          4: (69, 86, 75, 90), 5: (62, 86, 65, 90), 6: (53, 86, 59, 90), 7: (40, 80, 45, 84)}


def erase_ac(t, col):
    """Paint the Astra A/C pixels with the neighbouring roof colour."""
    x0, y0, x1, y1 = AC_BOX[col]
    m = np.zeros(t.shape[:2], bool)
    for y in range(y0, y1):
        for x in range(x0, x1):
            m[y, x] = tuple(int(v) for v in t[y, x]) in AC_COLS
    src = t.copy()
    for y, x in zip(*np.nonzero(m)):
        best = None
        for dist in range(1, 8):
            for dx, dy in ((0, dist), (-dist, 0), (dist, 0), (0, -dist)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < 128 and 0 <= xx < 128 and not m[yy, xx]:
                    c = tuple(int(v) for v in src[yy, xx])
                    if c in ROOF_COLS:
                        best = c
                        break
            if best:
                break
        t[y, x] = best or ROOF_COLS[0]


def put(t, pts, col):
    for x, y in pts:
        t[y, x] = tk.safe(col) if col not in tk.KEEP_RAW else col


def trio_face(t, xs, lv1, lamps, point):
    """Levels 2 (lamp row) and 3 (glass bottom) of a front face.

    xs: face columns left to right; lv1: {x: y of the yellow band};
    lamps: the headlight columns; point: the columns of the crescent's point
    (blue on the lamp row). Level 3 is blue between white corners."""
    xl, xr = xs[0], xs[-1]
    for x in xs:
        y2, y3 = lv1[x] - 1, lv1[x] - 2
        t[y3, x] = WHITE if x in (xl, xr) else BLUE
        t[y2, x] = LAMP if x in lamps else BLUE if x in point else WHITE


def variant_a(t, col):
    erase_ac(t, col)
    tk.roof_box(t, tk.DIRS[col], ROOF_COLS, 0.10, 0.40, 0.75, 2, UNIT_TOP, UNIT_SIDE)
    if col == 5:    # se: front view, face x58..68, yellow band at y 100
        xs = list(range(59, 68))
        trio_face(t, xs, {x: 100 for x in xs}, (60, 66), (62, 63, 64))
    elif col == 6:  # s: face x49..55, band steps down to the right
        xs = list(range(49, 56))
        trio_face(t, xs, {x: 97 + (x - 48) // 2 for x in xs}, (49, 55), (51, 52, 53))
    elif col == 4:  # e: face x72..78, band steps up to the right
        xs = list(range(72, 79))
        trio_face(t, xs, {x: 100 - (x - 72) // 2 for x in xs}, (72, 78), (74, 75, 76))
    elif col == 3:  # ne side view, front column x82
        put(t, [(82, 92), (82, 93), (81, 93)], BLUE)
        put(t, [(82, 94)], WHITE)
    elif col == 7:  # sw side view, front column x37
        put(t, [(37, 92), (37, 93), (38, 93)], BLUE)
        put(t, [(37, 94)], WHITE)


def variant_b(t, col):
    variant_a(t, col)
    if col == 3:
        put(t, [(82, 84), (82, 85), (81, 82), (81, 83)], tk.BG)  # windscreen leans back
        put(t, [(83, 94)], WHITE)                      # nose bulge at bumper height
        put(t, [(83, 95)], YELLOW)
        put(t, [(82, 96)], BLUE)
        put(t, [(x, 93) for x in range(76, 80)], BLUE)  # band under the cab window
        put(t, [(80, y) for y in range(88, 93)], BLUE)  # and its front pillar
    elif col == 7:
        put(t, [(37, 84), (37, 85), (38, 82), (38, 83)], tk.BG)
        put(t, [(36, 94)], WHITE)
        put(t, [(36, 95)], YELLOW)
        put(t, [(37, 96)], BLUE)
        put(t, [(x, 93) for x in range(40, 44)], BLUE)
        put(t, [(39, y) for y in range(88, 93)], BLUE)
    elif col == 5:
        put(t, [(59, 92)], H("E6E6E6"))               # rounded glass corners
        put(t, [(67, 92)], H("D6D6D6"))
        put(t, [(58, 89), (68, 89)], tk.BG)           # rounded roof corners


def build(variant):
    sh = tk.load(ASTRA).copy()
    for col in range(8):
        t = tk.tile(sh, 0, col)
        (variant_a if variant == "A" else variant_b)(t, col)
    return sh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="A", choices=["A", "B"])
    ap.add_argument("--preview")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    sh = build(a.variant)
    if not a.no_write:
        tk.save(sh, TRIO)
        print("wrote", os.path.relpath(TRIO, ROOT))
    if a.preview:
        astra = tk.load(ASTRA)
        ents = [("current Trio = Astra sheet", astra), ("Trio variant A", build("A")),
                ("Trio variant B", build("B"))]
        print("preview", tk.preview(ents, os.path.join(a.preview, "t2001_trio.png"), rows=[0]))
        for v in "AB":
            tk.save(build(v), os.path.join(a.preview, f"t2001_trio_{v}.png"))


if __name__ == "__main__":
    main()
