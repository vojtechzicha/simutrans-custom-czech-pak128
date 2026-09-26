"""RegioJet coaches: render the sprite sheets of the VZ-RegioJet-bus families.

    python tools/busrender/rj_buses.py [family ...] [--preview DIR]

Families (WT/vehicle-bus/regiojet/<family>/sprites/<livery>.png):
  irizar_i8     zluta, zlutostribrna
  setra_s531dt  zluta
  irizar_pb     zluta

Models: rj_busmodels.py (box models), rendered with rj_vrender.py (vectorised copy of
the DP Ostrava bus raycaster, pak128 road projection) and placed on the
median lane footprint of native pak128.cs 12 m buses (rj_lane.py MEDIAN):
a bare single-deck box of the model's drawn length and width is rendered,
its footprint (body x-centre and lower-edge intercept) is shifted onto the
median, and the same whole-pixel shift is applied to the real model, so a
longer body extends equally forward and back along the lane and never moves
sideways (image_offset [0, 0] in family.yaml).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from rj_vrender import Box, render, DIRS
import rj_busmodels as C
from rj_buscommon import save_rows, preview
from rj_lane import metrics, shift_tile, SLOPE, MEDIAN

WT = os.path.dirname(os.path.dirname(HERE))   # repo root
FAMDIR = os.path.join(WT, "vehicle-bus", "regiojet")


def calibration(m):
    """Whole-pixel shift per view that puts a plain single-deck box of the
    model's footprint onto the native median footprint."""
    L = m.L
    ref = [Box(0.0, L, -C.W2, C.W2, m.Z0, 3.0, lambda *a: (0xFF, 0xB6, 0x12)),
           Box(0.5, L - 0.6, -C.W2 + 0.35, C.W2 - 0.35, 0.0, m.Z0, lambda *a: (20, 20, 20))]
    cal = {}
    for d in DIRS:
        X, Cc = metrics(render(ref, L, d), d)
        tx, tc = MEDIAN[d]
        dx = int(round(tx - X))
        dy = int(round(tc - Cc)) if d in ("nw", "se") else int(round(tc - (Cc - SLOPE[d] * dx)))
        cal[d] = (dx, dy)
    return cal


def row_for(cls, livery):
    m = cls(livery)
    L, boxes, lines = m.model()
    cal = calibration(m)
    return [shift_tile(render(boxes, L, d, lines), *cal[d]) for d in DIRS]


JOBS = {
    "irizar_i8": [("zluta", lambda: [row_for(C.IrizarI8, "zluta")], ["Irizar i8"]),
                  ("zlutostribrna", lambda: [row_for(C.IrizarI8, "zlutostribrna")], ["Irizar i8 2019"])],
    "setra_s531dt": [("zluta", lambda: [row_for(C.SetraS531DT, "zluta")], ["Setra S 531 DT"])],
    "irizar_pb": [("zluta", lambda: [row_for(C.IrizarPB, "zluta")], ["Irizar PB"])],
}


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    fams = argv or list(JOBS)
    for fam in fams:
        for livery, rows_fn, labels in JOBS[fam]:
            rows = rows_fn()
            out = os.path.join(FAMDIR, fam, "sprites", f"{livery}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            save_rows(rows, out)
            print("wrote", out)
            if prev:
                os.makedirs(prev, exist_ok=True)
                preview(rows, os.path.join(prev, f"{fam}_{livery}.png"), z=5)


if __name__ == "__main__":
    main(sys.argv[1:])
