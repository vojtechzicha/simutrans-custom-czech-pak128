#!/usr/bin/env python3
"""Regenerate every GW Train Regio sprite sheet.

    python tools/railrender/gwtr.py                 # all families
    python tools/railrender/gwtr.py 845 818         # only these family dirs
    python tools/railrender/gwtr.py --preview DIR   # also write 4x previews to DIR

Writes vehicle-rail/gw-train-regio/<family>/sprites/<livery>.png. Needs numpy
and Pillow. The 845 and 818 are original art rendered from box models
(render.py/railkit.py); the 841.2, the 810 / 816 and the 814.5 are zone-map
repaints of the matching CeskeDrahy sheets. Change the scripts and regenerate
instead of painting the PNGs by hand.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "gw-train-regio")

import railkit as R  # noqa: E402


def _m152_810(liv):
    """810 family sheet: row 0 = 810, row 1 = 816 (only in the 816's liveries)."""
    import gwtr_m152 as g
    rows = g.rows_810(liv)
    if liv in g.LIVERIES_816:
        rows += g.rows_816(liv)
    return rows


def jobs():
    """family dir -> (liveries, rows function, preview labels)."""
    import db628, gwtr_m152, gwtr_rs1, regiosprinter
    return {
        "845": (db628.GWTR_LIVERIES, db628.rows_gwtr, ["845", "945", "845 rear"]),
        "818": (regiosprinter.LIVERIES, regiosprinter.rows_for, ["818.0", "818.2"]),
        "841_2": (gwtr_rs1.LIVERIES, gwtr_rs1.rows_for, ["841.2"]),
        "810": (gwtr_m152.LIVERIES_810, _m152_810, ["810", "816"]),
        "814_5": (gwtr_m152.LIVERIES_814, gwtr_m152.rows_814,
                  ["914.5", "814.5", "814.5 rev", "914.5 rev"]),
    }


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
        livs, make, labels = todo[fam]
        for liv in livs:
            rows = make(liv)
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
