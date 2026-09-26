#!/usr/bin/env python3
"""ČD "Šukafon" sheets: the 809 and 810 railcars, the 010 (Btax 780) trailer and
the 2020 MSK rebuild 811 with its 012 (BDtax 782) trailer.

All of them are zone-map repaints (zonemap.py) of Sim's pak128.CS drawings in
rail-psg mail/810: the 810 railcar and the Btax 780 trailer, frozen in
src/sukafon/ (row 0 of each upstream livery sheet; together they give the
zones and the shading). Liveries, researched from photos and RAL-anchored:

  810  najbrt1, najbrt2, cervenokremova (ČD 1998 variant), pardubickykraj (2019),
       pidcervenomodrobila (the old PID scheme, 810 263 / 289); the 010 row only
       in the three liveries the trailer really wore
  809  najbrt1, najbrt2, cervenokremova, cervenozluta (ČSD "unifik 88", 809 281)
  811  najbrt2 with Moravskoslezský kraj marks, plus the flat roof A/C unit;
       the 012 trailer is the Btax body in the same scheme

    python tools/railpaint/cd_sukafon.py                 # all three families
    python tools/railpaint/cd_sukafon.py 810 811         # only these family dirs
    python tools/railpaint/cd_sukafon.py --preview DIR   # also 4x previews in DIR

Writes vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png. Change the
livery dicts and regenerate rather than editing the PNGs.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from zonemap import paint, save, add_marks, add_exhaust, add_roof_box
from palette import (SAPPHIRE, SKY, LGREY, UMBRA, N2_STRIPE, UF_GREY, RC_RED, RC_CREAM, RC_ROOF,
                     BLACK, PLATE_RED, TEXT_GREY)

REPO = os.path.dirname(os.path.dirname(HERE))
FAMDIR = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

# --- family-local colours (shared ones come from palette.py) -----------------
PLOUGH = (236, 182, 22)        # yellow bottom edge of the 810 snowplough
PK_BLUE = (30, 56, 104)        # Pardubický kraj on the 810 (2019)
PK_RED = (222, 36, 42)
PK_GREY = (210, 215, 218)
PK_YELLOW = (246, 192, 0)
PK_EMBLEM_Y = (250, 200, 20)
OPID_BLUE = (22, 92, 172)      # old PID červeno-modro-bílá (not the grey-red PID_*)
OPID_WHITE = (236, 236, 236)
OPID_RED = (218, 34, 44)
RY_RED = (160, 32, 44)         # ČSD "unifik 88" red (809 281)
RY_YELLOW = (235, 185, 50)     # its golden-yellow band
RY_ROOF = (180, 180, 172)
MSK_RED = (220, 45, 45)        # Moravskoslezský kraj logo on the 811
RING_GREY = (150, 152, 158)


def plough(colour_beam, veh):
    """E_BEAM: the beam itself in the livery colour; on the 810 the plough's
    lower edge (the row below the beam) is yellow, the 010 has no plough."""
    def f(c):
        if c["k"] >= 10:
            return PLOUGH if veh == "810" else (52, 52, 52)
        return colour_beam
    return f


def livery(name, veh):
    if name == "najbrt1":
        return {
            "ROOF": UMBRA,
            "S_TOP": SKY, "S_PIL": SKY, "S_DOOR": SAPPHIRE, "S_BELT": SAPPHIRE,
            "S_LOW1": LGREY, "S_LOW2": LGREY, "S_SKIRT": LGREY, "S_SOLE": UF_GREY,
            "E_TOP": SKY, "E_PIL": SKY, "E_BELOW": SAPPHIRE, "E_LAMP": LGREY,
            "E_LOW1": LGREY, "E_LOW2": LGREY, "E_BEAM": plough(UF_GREY, veh),
        }
    if name == "najbrt2":
        return {
            "ROOF": SAPPHIRE, "ROOF_EDGE": N2_STRIPE,
            "S_TOP": SKY, "S_PIL": SKY, "S_DOOR": SAPPHIRE, "S_BELT": SAPPHIRE,
            "S_LOW1": LGREY, "S_LOW2": LGREY, "S_SKIRT": LGREY, "S_SOLE": SAPPHIRE,
            "E_TOP": SAPPHIRE, "E_PIL": SKY, "E_BELOW": SAPPHIRE, "E_LAMP": LGREY,
            "E_LOW1": LGREY, "E_LOW2": LGREY, "E_BEAM": plough(SAPPHIRE, veh),
        }
    if name == "cervenokremova":
        return {
            "ROOF": RC_ROOF,
            "S_TOP": RC_RED, "S_PIL": RC_RED, "S_DOOR": RC_RED, "S_BELT": RC_CREAM,
            "S_LOW1": RC_CREAM, "S_LOW2": RC_RED, "S_SKIRT": RC_RED, "S_SOLE": RC_RED,
            "E_TOP": RC_RED, "E_PIL": RC_RED, "E_BELOW": RC_CREAM, "E_LAMP": RC_CREAM,
            "E_LOW1": RC_RED, "E_LOW2": RC_RED, "E_BEAM": plough(RC_RED, veh),
        }
    if name == "cervenozluta":
        # ČSD unifik 88: red body, golden-yellow band below the windows that
        # crosses the doors and runs round the fronts at lamp level
        def door(c):
            return RY_YELLOW if c["k"] in (4, 5) else RY_RED
        return {
            "ROOF": RY_ROOF,
            "S_TOP": RY_RED, "S_PIL": RY_RED, "S_DOOR": door, "S_BELT": RY_YELLOW,
            "S_LOW1": RY_YELLOW, "S_LOW2": RY_RED, "S_SKIRT": RY_RED, "S_SOLE": RY_RED,
            "E_TOP": RY_RED, "E_PIL": RY_RED, "E_BELOW": RY_YELLOW, "E_LAMP": RY_YELLOW,
            "E_LOW1": RY_RED, "E_LOW2": RY_RED, "E_BEAM": plough(RY_RED, veh),
        }
    if name == "pardubickykraj":
        return {
            "ROOF": PK_BLUE,
            "S_TOP": PK_RED, "S_PIL": PK_GREY, "S_DOOR": PK_YELLOW, "S_BELT": PK_BLUE,
            "S_LOW1": PK_GREY, "S_LOW2": PK_GREY, "S_SKIRT": PK_GREY, "S_SOLE": PK_BLUE,
            "E_TOP": PK_BLUE, "E_PIL": PK_RED, "E_BELOW": PK_BLUE, "E_LAMP": PK_GREY,
            "E_LOW1": PK_GREY, "E_LOW2": PK_GREY, "E_BEAM": plough(PK_BLUE, veh),
        }
    if name == "pidcervenomodrobila":
        return {
            "ROOF": OPID_BLUE,
            "S_TOP": OPID_BLUE, "S_PIL": OPID_BLUE, "S_DOOR": OPID_RED, "S_BELT": OPID_BLUE,
            "S_LOW1": OPID_WHITE, "S_LOW2": OPID_WHITE, "S_SKIRT": OPID_RED, "S_SOLE": OPID_RED,
            "E_TOP": OPID_BLUE, "E_PIL": OPID_BLUE, "E_BELOW": OPID_BLUE, "E_LAMP": OPID_WHITE,
            "E_LOW1": OPID_WHITE, "E_LOW2": OPID_RED, "E_BEAM": plough(OPID_RED, veh),
        }
    raise KeyError(name)


def marks(name, veh):
    """(side marks, front marks) - lettering and logos, a pixel or two each."""
    cab = veh == "810"
    if name == "najbrt1":
        side = [(0.50, 0.05, 5, SAPPHIRE), (0.50, 0.05, 6, SAPPHIRE)]
        if cab:
            side += [(0.72, 0.05, 5, PLATE_RED)]
        return side, [(-2, 6, SAPPHIRE)] if cab else []
    if name == "najbrt2":
        side = [(0.25, 0.05, 5, SAPPHIRE), (0.31, 0.05, 5, (70, 96, 140))]
        return side, [(0, 6, SAPPHIRE)] if cab else []
    if name == "cervenokremova":
        side = [(0.20, 0.03, 4, (58, 52, 50)), (0.20, 0.03, 5, (58, 52, 50))]
        return side, [(0, 6, BLACK)] if cab else []
    if name == "cervenozluta":
        side = [(0.20, 0.03, 4, (58, 52, 50)), (0.20, 0.03, 5, (58, 52, 50))]
        return side, [(0, 6, BLACK)] if cab else []
    if name == "pardubickykraj":
        side = [(0.24, 0.04, 5, PK_EMBLEM_Y), (0.24, 0.04, 6, PK_BLUE), (0.33, 0.09, 6, TEXT_GREY)]
        return side, [(-1, 6, PK_EMBLEM_Y), (1, 6, PK_BLUE)] if cab else []
    if name == "pidcervenomodrobila":
        side = [(0.44, 0.05, 5, OPID_BLUE), (0.44, 0.05, 6, OPID_BLUE), (0.55, 0.04, 5, OPID_RED),
                (0.66, 0.05, 5, OPID_BLUE), (0.66, 0.05, 6, OPID_BLUE)]
        return side, [(-2, 6, OPID_BLUE)] if cab else []
    return [], []


def marks_811():
    """811 (2020) in Najbrt 2 + Moravskoslezský kraj: ČD logo and lettering, the
    red/blue MSK logo and grey ring ornaments on the lower side; ČD logo centred
    and the MSK logo under the right lamps on the fronts."""
    side = [(0.25, 0.05, 5, SAPPHIRE), (0.31, 0.05, 5, (70, 96, 140)),
            (0.45, 0.04, 5, MSK_RED), (0.45, 0.04, 6, SAPPHIRE),
            (0.60, 0.03, 6, RING_GREY), (0.66, 0.03, 6, MSK_RED), (0.72, 0.03, 6, RING_GREY)]
    front = [(0, 6, SAPPHIRE), (3, 7, MSK_RED)]
    return side, front


# family dir -> (bodies in sheet-row order, liveries). The 811 / 012 use the
# 810 / 010 bodies.
FAMILIES = {
    "810": (["810", "010"], ["najbrt1", "najbrt2", "cervenokremova", "pardubickykraj", "pidcervenomodrobila"]),
    "809": (["810"], ["najbrt1", "najbrt2", "cervenokremova", "cervenozluta"]),
    "811": (["810", "010"], ["najbrt2"]),
}
# liveries the 010 trailer really wore (sheet rows past the 810 are dropped otherwise)
TRAILER_LIVERIES = {"najbrt1", "najbrt2", "cervenokremova"}


def render(fam, liv):
    """-> sprite rows of one family sheet."""
    vehs, _ = FAMILIES[fam]
    rows = []
    for v in vehs:
        if v == "010" and liv not in TRAILER_LIVERIES:
            continue
        a = paint(v, livery(liv, v))
        sm, em = marks_811() if fam == "811" else marks(liv, v)
        a = add_marks(a, v, sm, em)
        if v == "810":
            a = add_exhaust(a, v, u=0.86)
        if fam == "811" and v == "810":
            # 2020 rebuild: flat sapphire A/C unit centred on the roof, silver grille
            a = add_roof_box(a, v, 0.39, 0.62, vmax=1.0, top=(52, 78, 124), side=(20, 34, 62),
                             grille_u=(0.12, 0.88))
        rows.append(a)
    return rows


def run(families=None, prev=None):
    """Write the sheets of the given family dirs (default: all); with prev, also
    a 4x preview per family into that directory."""
    families = list(FAMILIES) if not families else families
    for fam in families:
        paths = []
        for liv in FAMILIES[fam][1]:
            p = save(render(fam, liv), os.path.join(FAMDIR, fam, "sprites", f"{liv}.png"))
            print("wrote", os.path.relpath(p, REPO))
            paths.append(p)
        if prev:
            from paint import preview
            os.makedirs(prev, exist_ok=True)
            preview(paths, os.path.join(prev, f"{fam}.png"), 4)


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
    unknown = [f for f in args if f not in FAMILIES]
    if unknown:
        sys.exit(f"unknown family dir(s): {', '.join(unknown)} (known: {', '.join(FAMILIES)})")
    run(args, prev)


if __name__ == "__main__":
    main()
