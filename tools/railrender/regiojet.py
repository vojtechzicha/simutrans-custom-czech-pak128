#!/usr/bin/env python3
"""Regenerate every RegioJet rail sprite sheet from its model.

    python tools/railrender/regiojet.py                 # all families
    python tools/railrender/regiojet.py obb 386_2       # only these family dirs
    python tools/railrender/regiojet.py --preview DIR   # also write 4x previews to DIR

Writes vehicle-rail/regiojet/<family>/sprites/<livery>.png. Needs numpy and
Pillow. The sheets are original art rendered by render.py/railkit.py (a box
raycaster calibrated to native pak128.cs rail sprites, see railkit.py); change
the model scripts and regenerate instead of painting the PNGs by hand.
"""
import importlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")

import railkit as R  # noqa: E402
import rjcoach  # noqa: E402
from render import T  # noqa: E402

# coach family dir -> (car codes in row order, {livery: codes drawn in that livery})
COACHES = {
    "obb": (["A000", "A100", "AB000", "Bk000", "Bk100"],
            {"zluta": None, "zlutacervenastrecha": ["A000", "Bk000"]}),
    "sbb": (["Am000", "Am900", "Bp000"], {"zluta": None}),
    "db": (["Am500", "Ak100", "Bm100", "Ap100", "Ap200", "Bp200", "Bp200.9", "Bp100", "Bp500"], {"zluta": None}),
    "astra": (["Bm000"], {"zluta": None}),
    "uicx": (["Bc100", "Bc300", "Bc200", "B200"], {"zluta": None}),
}
# model scripts of the other families; each exposes JOBS like the coach jobs below
MODULES = ["rj_locos", "rj_pesa", "rj_665", "rj_regiopanter", "rj_628", "rj_shunters"]


def _empty_row():
    """A transparent row for a car that never wore this livery (rows are fixed indices)."""
    t = np.zeros((128, 128, 3), np.uint8)
    t[:, :] = T
    return [t.copy() for _ in range(8)]


def jobs():
    """family dir -> list of (livery, rows-callable, preview labels)."""
    out = {}
    for fam, (codes, livs) in COACHES.items():
        out[fam] = []
        for liv, only in livs.items():
            def make(codes=codes, liv=liv, only=only):
                return [rjcoach.tiles(c, liv) if (only is None or c in only) else _empty_row() for c in codes]
            out[fam].append((liv, make, codes))
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except ImportError:
            continue
        out.update(mod.JOBS)
    return out


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    todo = jobs()
    for fam in (args or list(todo)):
        for liv, make, labels in todo[fam]:
            rows = make()
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
