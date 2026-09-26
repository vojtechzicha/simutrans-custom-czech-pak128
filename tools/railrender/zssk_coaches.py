#!/usr/bin/env python3
"""Regenerate the ZSSK (Slovak railways) coach sheets: red / white / grey
long-distance scheme, every ZSSK coach type that runs through the Czech
Republic in 2026.

    python tools/railrender/zssk_coaches.py                  # all families
    python tools/railrender/zssk_coaches.py vozy_z           # only these families
    python tools/railrender/zssk_coaches.py --preview DIR    # also 4x previews

Families (vehicle-rail/zssk/...):
  vozy_z   26.4 m UIC-Z2 coaches: Ampz, Bmpz, Bmz, Bdghmeer
  vozy_y   24.5 m UIC-Y coaches: Apeer, Aeer, Beer, Bpeer 29-70, ARpeer
  wlabmee  WLABmee 62 56 71-90 sleeper (Waggonbau Görlitz, 26.4 m)

Every coach is a coachkit.Coach built from its vagonWEB side drawings
(popisy/img/ZSSK/<type>-a.gif / -b.gif, 10 px = 1 m; the "-a" drawing is
side a, "-b" side b), painted with one coachkit.Livery: ZSSK red from the
cant rail down to just under the windows, a white middle band and a light
grey sill band (the drawings' 3.2 / 1.9 / 1.1 / 0.9 m heights), red doors
with a grey foot, red / white / grey end walls, the orange ZSSK arc logo on
the white band near the left end of each side (as seen), the passenger
information display near the right end, white class numerals by the doors
and the thin yellow 1st class line along the top of the red (A cars only,
on the ARpeer only over the 1st class half). See coachkit.py for the
conventions. Change the tables and regenerate instead of painting the PNGs.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import coachkit as CK  # noqa: E402
from coachkit import Win, Door, Band, Mark, RoofBox  # noqa: E402

# ====================================================================== livery
# Colours: sunlit photo samples (Bmpz 22-70 006 at Budapest-Nyugati, Ampz
# 10-70 005, Bmz 21-70 104, Bdghmeer 28-70 028, ARpeer 85-70 002, WLABmee
# 71-90 005; see the family.yaml comments), checked against the native
# ZSSK_Bmpz / ZSSK_Ampeer paint (#BD2129 red).
RED = 0xC41F24
WHITE = 0xFAF9F5
GREY = 0xAAA9A3
YELLOW = 0xF2CF0A
ORANGE = 0xE8641E
DISPLAY = 0x34373C
PICTO = 0x4A4D52
UNDER = 0x303134

# Heights (m above rail). The drawings give red 1.9-3.2 m (up to the roof
# curve), white 1.1-1.9, grey 0.9-1.1 (a grey skirt to 0.55 on the ŽOS
# Vrútky Z2 cars), windows 2.0-3.1 with their frames. The body side of the
# kit ends at 3.75 m; like the native pak128.cs coaches the paint runs to
# that edge (red up to the roof) and down to 0.34 m (dark underframe row
# on the unskirted cars), so the side is as tall as the natives'. The
# boundaries sit half-way between the renderer's sample heights (w/n/e/s
# views: 0.16 0.35 0.54 0.72 0.91 1.10 1.29 1.47 1.66 1.85 2.04 2.22 2.41
# 2.60 2.79 2.97 3.16 3.35 3.54 3.72; ne/sw: 0.35 0.67 0.99 1.30 1.62
# 1.94 2.26 2.57 2.89 3.21 3.53), so every band gets the same number of
# pixel rows in every view: grey 1, white 2, red 1 under the glass, glass 3,
# red 1-2 above (the yellow 1st class line is the top row).
SILL = 0.34           # painted body bottom
GREY_Z0 = 0.70        # dark underframe row below (unskirted cars)
WHITE_Z0 = 1.01
RED_Z0 = 1.76
WIN_Z = (2.13, 3.19)
YEL_Z0 = 3.45
EAVES = 3.80          # above the side top: no roof colour on the side face


def livery(roof, roof_top, skirt=False):
    bands = [Band(RED_Z0, 3.80, RED, over_doors=False),          # red, up to the roof
             Band(0.0, WHITE_Z0, GREY)]                          # grey sill band + door feet
    # dark underframe row (on the skirted cars only the part below the skirt)
    bands.append(Band(0.0, 0.60 if skirt else GREY_Z0, UNDER, over_doors=False))
    return CK.Livery(
        "zssk", body=WHITE, roof=roof, roof_top=roof_top, roof_eq=0x7E8284,
        ends=WHITE, end_bands=True, door=RED, door_frame=0x4A2226,
        under=0x2E2F31, bogie=0x252628, bogie_frame=0x393B3E, gangway=0x1D1E20,
        frost=0xC9CED1, dark_glass=0x2A3038, glass_hi_m=0.32, bands=bands)


ZSSK = livery(0xB8B9B6, 0xC4C5C1)                 # UIC-Z2: light grey roof
ZSSK_SKIRT = livery(0xB8B9B6, 0xC4C5C1, skirt=True)
# UIC-Y bodies: darker weathered roof (Aeer 044 photo; research: Y roofs darker)
ZSSK_Y = livery(0x9A9EA0, 0xA6AAAC)


def with_first(liv, *lines):
    return liv.derive(bands=liv.bands + list(lines))


def first_line(x0=None, x1=None, side="both"):
    """1st class: the yellow line along the top of the red, between the doors."""
    return Band(YEL_Z0, 3.80, YELLOW, x0=x0, x1=x1, side=side, over_doors=False)


def numeral(x, side="both"):
    """white class numeral beside a door (drawing position of its left edge)."""
    return Mark(x, x + 0.30, 2.50, 3.10, 0xF4F4F2, side=side)


def logo(xa, xb):
    """orange ZSSK arc logo on the white band, per side as seen."""
    return [Mark(xa, xa + 0.85, 1.40, 1.70, ORANGE, side="a"),
            Mark(xb, xb + 0.85, 1.40, 1.70, ORANGE, side="b")]


def display(xa, xb, w=0.8):
    """passenger information display box on the white band."""
    return [Mark(xa, xa + w, 1.40, 1.70, DISPLAY, side="a"),
            Mark(xb, xb + w, 1.40, 1.70, DISPLAY, side="b")]


def coach(name, length_m, **kw):
    """coachkit.Coach with the ZSSK band geometry (see the heights above)."""
    base = dict(sill_m=SILL, eaves_m=EAVES, win_z=WIN_Z, frost_z=WIN_Z, door_z=(SILL, 3.40),
                door_win_z=WIN_Z, underframe=False)
    base.update(kw)
    return CK.Coach(name, length_m, **base)


# ====================================================================== UIC-Z2 26.4 m
Z_DOORS = [Door(0.80, 1.80), Door(24.60, 25.60)]
Z_BOGIES = (3.65, 22.65)


def ampz():
    """Ampz 61 56 10-70 (ŽOS Vrútky 2020-21): open 1st class, 52 seats.
    vagonWEB Ampz-a/-b: 8 big windows, two small ones by each door on side a
    (the outer one the WC), one on side b; skirted body."""
    big = [Win(4.9, 6.3), Win(7.0, 8.4), Win(9.1, 10.5), Win(11.2, 12.6),
           Win(13.8, 15.2), Win(15.9, 17.3), Win(18.0, 19.4), Win(20.1, 21.5)]
    return coach("Ampz", 26.4,
               windows=[Win(2.0, 2.8, "f"), Win(3.5, 4.3)] + big + [Win(22.1, 22.9), Win(23.6, 24.4, "f")],
               windows_b=[Win(3.5, 4.3)] + big + [Win(22.1, 22.9)],
               doors=Z_DOORS, bogies=Z_BOGIES, roof="ac")


def bmpz():
    """Bmpz 61 56 22-70 (ŽOS Vrútky 2018-20): open 2nd class, 84 seats.
    vagonWEB Bmpz-a/-b; skirted body."""
    big = CK.row_of(5.2, 1.3, 2.075, 8)
    return coach("Bmpz", 26.4,
               windows=[Win(2.1, 2.8, "f"), Win(3.5, 4.3)] + big + [Win(22.0, 22.8), Win(23.5, 24.2, "f")],
               windows_b=[Win(3.5, 4.3)] + big + [Win(22.0, 22.8)],
               doors=Z_DOORS, bogies=Z_BOGIES, roof="ac")


def bmz():
    """Bmz 61 56 21-70 1xx (ŽOS Trnava rebuild of Bautzen Bmeer, 2018-20):
    11 compartments, 66 seats, WCs at both ends (vagonWEB Bmz-a/-b)."""
    comp = CK.row_of(3.1, 1.3, 1.89, 11)
    return coach("Bmz", 26.4,
               windows=[Win(1.8, 2.6, "f")] + comp + [Win(23.8, 24.6, "f")],
               doors=[Door(0.50, 1.60), Door(24.80, 25.90)], bogies=Z_BOGIES, roof="ac")


def bdghmeer():
    """Bdghmeer 61 56 28-70 (ŽOS Vrútky 2009-14, IS = with displays, 026-030):
    2nd class + bike / luggage area behind a double loading door + wheelchair
    lift (vagonWEB Bdghmeer-IS-a/-b; the two sides differ)."""
    wa = [Win(1.8, 3.0), Win(3.7, 4.9), Win(5.6, 6.8), Win(7.5, 8.7), Win(9.4, 10.6),
          Win(11.3, 12.5), Win(13.5, 14.7), Win(15.2, 16.0), Win(20.8, 22.1, "f"), Win(22.7, 24.0)]
    wb = [Win(2.4, 3.7), Win(4.3, 5.6), Win(11.7, 12.9), Win(13.9, 15.1), Win(15.8, 17.0),
          Win(17.7, 18.9), Win(19.6, 20.8), Win(21.5, 22.7), Win(23.4, 24.6)]
    ends = [Door(0.50, 1.50), Door(24.90, 25.90)]
    return coach("Bdghmeer", 26.4, windows=wa, windows_b=wb,
               doors=ends + [Door(17.2, 19.3, kind="double")],
               doors_b=ends + [Door(7.1, 9.2, kind="double")],
               bogies=Z_BOGIES, roof="ac")


def load_door_bands(xa, xb):
    """the loading door leaves carry the body's white band (drawings)."""
    return [Mark(xa[0], xa[1], WHITE_Z0, RED_Z0, WHITE, side="a", over_doors=True),
            Mark(xb[0], xb[1], WHITE_Z0, RED_Z0, WHITE, side="b", over_doors=True)]


Z_ROWS = [
    ("Ampz", ampz, with_first(ZSSK_SKIRT, first_line(1.9, 24.5)),
     logo(5.3, 5.3) + display(20.4, 20.4) + [numeral(3.05), numeral(23.1)]),
    ("Bmpz", bmpz, ZSSK_SKIRT,
     logo(5.2, 5.2) + display(20.0, 20.0) + [numeral(3.05), numeral(23.05)]),
    ("Bmz", bmz, ZSSK,
     logo(5.15, 5.15) + display(22.35, 22.35) + [numeral(2.7), numeral(23.4)]),
    ("Bdghmeer", bdghmeer, ZSSK,
     logo(4.0, 4.6) + display(21.1, 21.7) + load_door_bands((17.2, 19.3), (7.1, 9.2))
     + [numeral(3.2, "a"), numeral(19.9, "a"), numeral(6.2, "b"), numeral(22.9, "b")]),
]


def rows_z():
    return [CK.coach_tiles(make(), liv, marks=mk) for (_, make, liv, mk) in Z_ROWS]


# ====================================================================== UIC-Y 24.5 m
Y_DOORS = [Door(0.50, 1.50), Door(23.00, 24.00)]
Y_BOGIES = (3.65, 20.75)


def y_coach(name, big, wc_a=(True, True), wc_b=(True, True)):
    """UIC-Y body (ŽOS Vrútky modernisation): doors at both ends, a small WC
    window by each door where the drawing has one."""
    def wins(flags):
        return (([Win(1.9, 2.6, "f")] if flags[0] else []) + list(big)
                + ([Win(21.9, 22.6, "f")] if flags[1] else []))
    return coach(name, 24.5, windows=wins(wc_a), windows_b=wins(wc_b), doors=Y_DOORS, bogies=Y_BOGIES)


def apeer():
    """Apeer 61 56 19-70 017-022 (ex-Görlitz Bc 59-41, 2002): 9 compartments,
    1st class (vagonWEB Apeer-a/-b; no WC window at the right of side b)."""
    return y_coach("Apeer", CK.row_of(3.2, 1.3, 2.1, 9), wc_b=(True, False))


def aeer():
    """Aeer 61 56 19-70 031-045 (Bautzen UIC-Y, 2003-05): 9 compartments, 1st class."""
    return y_coach("Aeer", CK.row_of(3.2, 1.3, 2.1, 9))


def beer():
    """Beer 61 56 20-70 021-072 (Bautzen UIC-Y, 2003-06): 10 compartments, 2nd class."""
    return y_coach("Beer", CK.row_of(3.1, 1.3, 1.89, 10))


def bpeer():
    """Bpeer 61 56 29-70 (open 2nd class with bike hooks, 2000-03)."""
    return y_coach("Bpeer 29-70", CK.row_of(3.2, 1.3, 2.1, 9), wc_b=(True, False))


def arpeer():
    """ARpeer 61 56 85-70 001-003 (ex-Győr, 2001): bistro (17) + 1st class
    (24), door only at the 1st class end. Side a after the photo of 002-8
    (kitchen end blank, 3+1 bistro windows; the vagonWEB drawing ARpeer-IS-a
    also shows windows at 0.5-1.2 and 7.6-8.9 that the car does not have);
    side b as drawn (ARpeer-IS-b)."""
    wa = [Win(1.9, 3.2), Win(3.8, 5.1), Win(5.7, 7.0), Win(9.5, 10.8), Win(12.2, 12.9),
          Win(13.7, 15.0), Win(15.8, 17.1), Win(17.8, 19.1), Win(19.8, 21.1), Win(21.8, 22.5, "f")]
    wb = [Win(3.1, 4.4), Win(5.1, 6.4), Win(7.1, 8.4), Win(9.1, 10.4),
          Win(11.1, 11.8), Win(13.7, 15.0), Win(15.6, 16.9), Win(17.5, 18.8), Win(19.4, 20.7),
          Win(21.3, 22.6), Win(23.2, 23.9)]
    return coach("ARpeer", 24.5, windows=wa, windows_b=wb,
               doors=[Door(23.0, 24.0)], doors_b=[Door(0.5, 1.5)],
               bogies=Y_BOGIES)


def bike_picto(xs, side):
    return [Mark(x, x + 0.6, 1.40, 1.70, PICTO, side=side) for x in xs]


Y_ROWS = [
    ("Apeer", apeer, with_first(ZSSK_Y, first_line(1.5, 23.0)),
     logo(5.6, 5.6) + [numeral(2.75), numeral(21.55)]),
    ("Aeer", aeer, with_first(ZSSK_Y, first_line(1.5, 23.0)),
     logo(5.6, 5.6) + [numeral(2.75), numeral(21.55)]),
    ("Beer", beer, ZSSK_Y,
     logo(5.3, 5.3) + [numeral(2.75), numeral(21.55)]),
    ("Bpeer29-70", bpeer, ZSSK_Y,
     logo(5.6, 5.6) + bike_picto((2.55, 21.35), "a") + bike_picto((2.55, 21.35), "b")
     + [numeral(2.75), numeral(21.55)]),
    ("ARpeer", arpeer, with_first(ZSSK_Y, first_line(13.3, 23.0, "a"), first_line(1.5, 10.7, "b")),
     logo(4.1, 5.4) + [numeral(11.5, "a"), numeral(21.45, "a"), numeral(2.75, "b"), numeral(12.9, "b")]),
]


def rows_y():
    return [CK.coach_tiles(make(), liv, marks=mk) for (_, make, liv, mk) in Y_ROWS]


# ====================================================================== WLABmee
def wlabmee():
    """WLABmee 62 56 71-90 (Waggonbau Görlitz 1994-95 for RŽD, ŽSR 1997):
    11 three-berth compartments. Side a (corridor, photo 005-2) 14 windows,
    the first two with a transom bar, the last a WC; side b 7 windows
    (vagonWEB WLABmee-a/-b). Doors at both ends."""
    wa = [Win(3.0, 4.2), Win(4.8, 5.7), Win(6.1, 7.3), Win(7.6, 8.8), Win(9.3, 10.5),
          Win(10.8, 12.0), Win(12.5, 13.7), Win(14.0, 15.2), Win(15.7, 16.9), Win(17.2, 18.4),
          Win(18.9, 20.1), Win(20.4, 21.6), Win(22.1, 23.3), Win(23.6, 24.5, "f")]
    wb = CK.row_of(2.8, 1.2, 3.1, 7)
    return coach("WLABmee", 26.4, windows=wa, windows_b=wb,
               doors=[Door(0.45, 1.45), Door(24.95, 25.95)],
               bogies=(3.95, 22.35), roof_items=[RoofBox(3.4, 5.4, 0.62, 0.28), RoofBox(21.0, 23.0, 0.62, 0.28)])


WL_ROWS = [
    ("WLABmee", wlabmee, ZSSK.derive(roof=0xAEB0AE, roof_top=0xBABCB9), logo(4.9, 4.9)),
]


def rows_wl():
    return [CK.coach_tiles(make(), liv, marks=mk) for (_, make, liv, mk) in WL_ROWS]


# ====================================================================== main
JOBS = {
    "vozy_z": (os.path.join("zssk", "vozy_z"), [("cervenobilasiva", rows_z, [r[0] for r in Z_ROWS])]),
    "vozy_y": (os.path.join("zssk", "vozy_y"), [("cervenobilasiva", rows_y, [r[0] for r in Y_ROWS])]),
    "wlabmee": (os.path.join("zssk", "wlabmee"), [("cervenobilasiva", rows_wl, [r[0] for r in WL_ROWS])]),
}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        rel, sheets = JOBS[fam]
        for liv, make, labels in sheets:
            rows = make()
            out = os.path.join(REPO, "vehicle-rail", rel, "sprites", liv + ".png")
            CK.save_sheet(rows, out)
            if prev:
                CK.preview(rows, os.path.join(prev, "%s_%s.png" % (fam, liv)), labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
