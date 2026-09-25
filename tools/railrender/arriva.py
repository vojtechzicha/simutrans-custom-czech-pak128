#!/usr/bin/env python3
"""Regenerate every Arriva vlaky sprite sheet from its box model.

    python tools/railrender/arriva.py                 # all families
    python tools/railrender/arriva.py 846 832         # only these family dirs
    python tools/railrender/arriva.py --preview DIR   # also write 4x previews to DIR

Writes vehicle-rail/arriva/<family>/sprites/<livery>.png. Needs numpy and
Pillow. The sheets are original art rendered by render.py/railkit.py (a box
raycaster calibrated to native pak128.cs rail sprites, see railkit.py); change
the model scripts and regenerate instead of painting the PNGs by hand.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "arriva")

import railkit as R  # noqa: E402


def jobs():
    """family dir -> list of (livery, rows-callable, preview labels)."""
    import arriva_lint, db628, desiro, gtw, regiopanter_idpk
    return {
        "845": [(c, (lambda c=c: db628.rows_for(c)), ["845", "945"]) for c in db628.LIVERIES],
        "846": [(c, (lambda c=c: arriva_lint.rows_for("lint41", c)), ["846-A", "846-B"])
                for c in arriva_lint.LIVERIES],
        "832": [(c, (lambda c=c: arriva_lint.rows_for("lint27", c)), ["832"])
                for c in arriva_lint.LIVERIES],
        "642": [(c, (lambda c=c: desiro.rows_for(c)), ["642A", "642B"]) for c in desiro.LIVERIES],
        "848": [(c, (lambda c=c: gtw.rows_for(c)), ["848A", "848M", "848B"]) for c in gtw.LIVERIES],
        "650": [("plzenskykraj", regiopanter_idpk.rows, ["650", "651"])],
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
