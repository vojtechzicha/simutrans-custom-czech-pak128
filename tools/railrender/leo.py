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
    import ric, flirt, lint, talgo
    return {
        "193": [(liv, (lambda liv=liv: vectron_rows(liv)), ["193"]) for liv in ("bilooranzova", "railpool")],
        "ic": [("sedooranzova", lambda: ric.rows_for("sedooranzova", ric.KINDS), ric.KINDS)],
        "bvcmz": [("rdcmodra", lambda: ric.rows_for("rdcmodra", ["Bvcmz"]), ["Bvcmz"])],
        "480": [(liv, (lambda liv=liv: flirt.render_unit(liv)), flirt.LABELS) for liv in flirt.LIVERIES],
        "846": [("bilooranzova", lambda: lint.rows_for("lint41", "bilooranzova"), ["846-A", "846-B"])],
        "648": [("modrostribrnazluta", lambda: lint.rows_for("lint41", "modrostribrnazluta"), ["648-A", "648-B"])],
        "832": [("bilooranzova", lambda: lint.rows_for("lint27", "bilooranzova"), ["832"])],
        "talgo6": [("bilooranzova", talgo.render_rows, [k for k, _ in talgo.ROWS])],
    }


STYLED = {"193"}   # locomotives: rendered in the 2026-09-26 style (style.py)


def vectron_rows(liv):
    """The Vectron in the agreed style: the real Vectron MS has no cab side
    window (vectron.py draws one; painted over here), dark roof gutter instead
    of a light rim, light pantograph arms with a dark head bar."""
    import vectron as V
    import restyle_kit as K
    C = V.livery(liv)
    parts, lines = V.build(liv)
    for p in parts:
        if getattr(p.mat, "__name__", "") == "body_mat":
            m0 = p.mat

            def m(f, u, v, z, d, m0=m0):
                cu = min(u, V.L - u)
                if f in ("+v", "-v") and 0.60 <= cu <= 1.20 and 7.9 <= z <= 10.7:
                    if C["orange"] is not None:
                        if z >= 10.6:
                            return C["orange"]
                        if cu < 0.62 + (z - 5.6) * 0.06:
                            return C["orange"]
                    return C["body"]
                return m0(f, u, v, z, d)
            m.__name__ = "body_mat"
            p.mat = m
    K.roof_restyle(parts, V.ZS, V.ZR)
    if liv in LIGHTER:
        _lighten(parts, LIGHTER[liv])
    lines = K.restyle_lines(lines)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]


# style.polish deepens mid tones and the outline + gutter darken the top, which made
# the silver Railpool Vectron read far darker than the old sheet (user review
# 2026-09-26). These base colours bring the polished side back to the old sheet's
# brightness (ne side 0x919698, band 0x1A7BBA). Keys are vectron.livery() bases.
LIGHTER = {"railpool": {
    (0xA9, 0xAE, 0xB1): ((0xBA, 0xBF, 0xC2), (0xB0, 0xB5, 0xB8)),   # body, roof cap, cab roof
    (0xA3, 0xA8, 0xAB): ((0xB4, 0xB9, 0xBC), None),                  # doors
    (0x8E, 0x93, 0x96): ((0xA0, 0xA5, 0xA8), None),                  # lower skirt
    (0x1E, 0x8F, 0xD8): ((0x58, 0xB1, 0xEF), None),                  # light-blue band
    (0x4A, 0x50, 0x54): ((0x55, 0x5B, 0x5F), (0x62, 0x68, 0x6C)),    # roof equipment
    (0x3A, 0x3F, 0x43): ((0x44, 0x4A, 0x4F), (0x50, 0x56, 0x5B)),    # roof equipment, dark
}}


def _lighten(parts, remap):
    from railkit import Paint
    table = {k: Paint(b, top=t) if t else Paint(b) for k, (b, t) in remap.items()}
    for p in parts:
        m0 = p.mat

        def m(f, u, v, z, d, m0=m0):
            x = m0(f, u, v, z, d)
            if isinstance(x, Paint):
                return table.get(tuple(x.base), x)
            return x
        m.__name__ = getattr(m0, "__name__", "mat")
        p.mat = m


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
            if fam in STYLED:
                import restyle_kit as K
                K.save_styled(rows, out)
            else:
                R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
