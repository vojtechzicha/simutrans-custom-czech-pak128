#!/usr/bin/env python3
"""Regenerate every Leo Express sprite sheet from its box model.

    python tools/railrender/leo.py                 # all families
    python tools/railrender/leo.py 480 talgo6      # only these family dirs
    python tools/railrender/leo.py --preview DIR   # also write 4x previews to DIR

Writes vehicle-rail/leo-express/<family>/sprites/<livery>.png. Needs numpy and
Pillow. The sheets are original art rendered by render.py/railkit.py (a box
raycaster calibrated to native pak128.cs rail sprites, see railkit.py); change
the model scripts and regenerate instead of painting the PNGs by hand.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "leo-express")

import railkit as R  # noqa: E402
from render import DIRS  # noqa: E402


def jobs():
    """family dir -> list of (livery, rows-callable, preview labels)."""
    import vectron, ric, flirt, lint, talgo
    return {
        "193": [(liv, (lambda liv=liv: [[R.vehicle_tile(*vectron.build(liv), d, 0.0, {"V"}) for d in DIRS]]), ["193"])
                for liv in ("bilooranzova", "railpool")],
        "ic": [("sedooranzova", lambda: ric.rows_for("sedooranzova", ric.KINDS), ric.KINDS)],
        "bvcmz": [("rdcmodra", lambda: ric.rows_for("rdcmodra", ["Bvcmz"]), ["Bvcmz"])],
        "480": [(liv, (lambda liv=liv: flirt.render_unit(liv)), flirt.LABELS) for liv in flirt.LIVERIES],
        "846": [("bilooranzova", lambda: lint.rows_for("lint41", "bilooranzova"), ["846-A", "846-B"])],
        "648": [("modrostribrnazluta", lambda: lint.rows_for("lint41", "modrostribrnazluta"), ["648-A", "648-B"])],
        "832": [("bilooranzova", lambda: lint.rows_for("lint27", "bilooranzova"), ["832"])],
        "talgo6": [("bilooranzova", talgo.render_rows, [k for k, _ in talgo.ROWS])],
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
