#!/usr/bin/env python3
"""Regenerate the rendered sheets of the small / foreign operator families that
have no generator of their own.

    python tools/railrender/ops.py                 # all of them
    python tools/railrender/ops.py kzc/749 mbm-rail/708   # only these family dirs
    python tools/railrender/ops.py --preview DIR   # also write 4x previews to DIR

Covered here: KŽC 749 / 751 (kzc_t478.py), the ČSD green Y coaches
(kzc_yvoz.py), Bix / RBix (kzc_bix.py), MBM rail M 131.1 and its Blm trailer
(mbm_hurvinek.py), MBM rail 708 (mbm_708.py) and ZSSK 361.1 (zssk361.py).

The other rendered families of this set regenerate with their own model
scripts (each has a main):
  ops_regiosprinter.py  die-landerbahn-cz/654, azd-praha/818
  ops_desiro.py         die-landerbahn/642 (trilex), db-regio/642
  db612.py              db-regio/612
  er20.py               die-landerbahn/223
  ops_coaches.py        obb/ic, obb/nightjet, die-landerbahn/alexvozy
  es_coaches.py         european-sleeper/vozy
  traxx.py              european-sleeper/186
  ops_vectron.py        pkp-intercity/vectron
  pkp_locos.py          pkp-intercity/ep09, eu07
  impuls.py, elf2.py    koleje-dolnoslaskie/*, koleje-slaskie/*
  obb_dosto.py, obb_cityshuttle.py, obb_cityjet.py   obb/dosto, cityshuttle, 4746
  zssk_coaches.py       zssk/vozy_z, vozy_y, wlabmee
  mav_pkp_coaches.py    mav/*, pkp-intercity/vozy, nocni
Repaints of upstream art (RS1 650, 810 / 811 / 813 families, 830 / 851, KŽC Bmx,
ÖBB 1116 / 1216, PKP EU44) are painted from pak128.CS sheets and are not
regenerated from a model.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
RAIL = os.path.join(REPO, "vehicle-rail")

import railkit as R  # noqa: E402

# 749 / 751: family livery -> kzc_t478 model key
T478 = {"749": [("vinovosediva", "rudenka"), ("cervenosediva", "cervena"), ("modrobila", "modrobila")],
        "751": [("cervenozluta", "cervenozluta")]}


def jobs():
    """family dir -> list of (livery, rows-callable, preview labels)."""
    import kzc_t478, kzc_yvoz, kzc_bix, mbm_hurvinek, mbm_708, zssk361
    out = {}
    for fam, livs in T478.items():
        out["kzc/" + fam] = [(c, (lambda m=m: kzc_t478.rows(m)), [fam]) for c, m in livs]
    out["kzc/y_vozy"] = [("csdzelena", kzc_yvoz.rows, kzc_yvoz.LABELS)]
    out["kzc/bix"] = [("polomaceny", kzc_bix.rows, kzc_bix.LABELS)]
    out["mbm-rail/m131_1"] = [("vinova", lambda: mbm_hurvinek.render_rows(mbm_hurvinek.M131), ["M131.1"])]
    out["mbm-rail/blm"] = [("tmavocervena", lambda: mbm_hurvinek.render_rows(mbm_hurvinek.BLM), ["Blm"])]
    out["mbm-rail/708"] = [("oranzovomodra", mbm_708.render_rows, ["708"])]
    out["zssk/361_1"] = [(liv, (lambda liv=liv: zssk361.rows(liv)), ["361.1"]) for liv in zssk361.LIVERIES]
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
            out = os.path.join(RAIL, *fam.split("/"), "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam.replace('/', '_')}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
