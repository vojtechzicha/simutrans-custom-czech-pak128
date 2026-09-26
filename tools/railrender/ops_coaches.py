#!/usr/bin/env python3
"""Regenerate the ÖBB IC, ÖBB Nightjet and Die Länderbahn alex coach sheets.

    python tools/railrender/ops_coaches.py                  # all families
    python tools/railrender/ops_coaches.py nightjet         # only these families
    python tools/railrender/ops_coaches.py --preview DIR    # also 4x previews

Families (vehicle-rail/...):  obb/ic, obb/nightjet, die-landerbahn/alexvozy.
Every coach is a coachkit.Coach built from its vagonWEB side drawings
(10 px = 1 m; the "-a" drawing is side a, "-b" side b) and painted with a
coachkit.Livery; see coachkit.py for the conventions. Photos used for the
liveries are listed in each family.yaml. Change the tables and regenerate
instead of painting the PNGs by hand. Only these three families live here.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import coachkit as CK  # noqa: E402
from coachkit import Win, Door, Band, Mark  # noqa: E402

UICZ_DOORS = [Door(0.50, 1.50), Door(24.90, 25.90)]


# ====================================================================== ÖBB
# --- coach types (vagonWEB OeBB/Bmpz-2991-2019-a/b, Bmz-2191-1-2019-a/b)
def bmpz_29_91():
    """ÖBB Bmpz 73 81 29-91: open 2nd class, 74 seats + 2 wheelchair places,
    bike space behind the pictogram windows at both ends."""
    big = CK.row_of(4.20, 1.30, 2.0875, 9)
    bike = [Win(3.00, 3.90), Win(22.50, 23.40)]
    return CK.Coach("Bmpz 29-91", 26.4,
                    windows=[Win(1.80, 2.70, "f")] + bike[:1] + big + bike[1:] + [Win(23.70, 24.60, "f")],
                    windows_b=bike[:1] + big + bike[1:],        # no WCs on side b
                    doors=UICZ_DOORS, bogies=(3.55, 22.65), win_z=(1.95, 3.05))


def bmz_21_91():
    """ÖBB Bmz 73 81 21-91: 11-compartment 2nd class, 66 seats. WCs at both
    ends of side a; the corridor side b has small end windows there."""
    comp = CK.row_of(3.10, 1.30, 1.89, 11)
    return CK.Coach("Bmz 21-91", 26.4,
                    windows=[Win(1.80, 2.70, "f")] + comp + [Win(23.70, 24.60, "f")],
                    windows_b=[Win(1.80, 2.70)] + comp + [Win(23.70, 24.60)],
                    doors=UICZ_DOORS, bogies=(3.55, 22.65), win_z=(1.95, 3.05))


# --- ÖBB "Valousek" IC livery: light grey body, mid-grey window band, white
# line under the red roof, red stripe along the sill (photos Wien Meidling
# Bmpz, ÖBB Bmz Neunkirchen; drawing colours from vagonWEB)
OBB_RED = 0xC81E28
OBB_IC = CK.Livery(
    "obbsedocervena", body=0xCDCFD2, roof=0xC4282E, roof_top=0xB82B30,
    ends=0x585C60, end_door=0xB0242A, door=0xC7CACD, door_frame=0x34373A,
    under=0x34373A, frost=0xB8C0C6,
    bands=[Band(0.85, None, OBB_RED, px=1),           # sill stripe: the bottom body row
           Band(1.90, 3.40, 0xA2A6AA),                # window band grey
           Band.line(3.40, 0xE6E8EA)])                # white line under the red roof


def obb_logo(x_a, x_b, z0=1.42, z1=1.80):
    """red ÖBB wordmark on the light lower body, per side as seen (mid-car on
    the Wien Meidling Bmpz photo; the vagonWEB drawing has it further left)."""
    return [Mark(x_a, x_a + 0.95, z0, z1, 0xD8232C, side="a"),
            Mark(x_b, x_b + 0.95, z0, z1, 0xD8232C, side="b")]


OBB_IC_ROWS = [
    ("Bmpz29-91", bmpz_29_91, obb_logo(11.7, 11.7)),
    ("Bmz21-91", bmz_21_91, obb_logo(11.7, 11.7)),
]


def rows_obb_ic():
    return [CK.coach_tiles(make(), OBB_IC, marks=mk) for (_, make, mk) in OBB_IC_ROWS]


# --- Nightjet coach types (vagonWEB OeBB/Bcmz-5991-1-nj-a/b,
# WLABmz-7290-nj-a/b, D-/BTEX/Bvcmbz249-nj-a/b, Bmz-2191-1-nj-a/b)
def bcmz_59_91():
    """ÖBB Bcmz 73 81 59-91.1 couchette, 11 compartments (4/6 berths)."""
    comp = CK.row_of(3.10, 1.30, 1.89, 11)
    return CK.Coach("Bcmz 59-91", 26.4,
                    windows=[Win(1.80, 2.60, "f")] + comp + [Win(23.75, 24.55, "f")],
                    windows_b=[Win(1.80, 2.60)] + comp + [Win(23.70, 24.50)],
                    doors=UICZ_DOORS, bogies=(3.55, 22.65), win_z=(1.98, 3.02))


def wlabmz_72_90():
    """ÖBB WLABmz 61 80 72-90 sleeper (ex-DB): entrance at ONE end only.
    Side a = corridor side (13 windows), side b = compartment side with six
    big windows; the door is at the right of drawing a / left of drawing b,
    i.e. the same physical end."""
    corridor = [(2.4, 3.3), (4.4, 5.3), (5.7, 6.6), (7.7, 8.6), (9.0, 9.9), (10.8, 12.1),
                (12.5, 13.4), (14.2, 15.5), (15.9, 16.8), (17.6, 18.9), (19.3, 20.2),
                (20.9, 21.8), (23.1, 24.0)]
    compart = [(2.7, 3.9), (6.5, 7.7), (9.9, 11.1), (14.5, 15.7), (18.0, 19.2), (21.9, 23.1)]
    return CK.Coach("WLABmz 72-90", 26.4,
                    windows=[Win(a, b) for a, b in corridor],
                    windows_b=[Win(a, b) for a, b in compart],
                    doors=[Door(24.90, 25.80)], doors_b=[Door(0.60, 1.50)],
                    bogies=(3.55, 22.65), win_z=(1.98, 2.95))


def bvcmbz_59_90():
    """BTEX Bvcmbz 61 80 59-90 (ex-DB Bvcmbz 249, couchette with a wheelchair
    compartment), leased to ÖBB and painted like the Nightjet cars (vagonWEB
    Bvcmbz249-nj; photo 61 80 59-90 010-9 in NJ 425, 26 Jun 2024). Rounded
    roof ends, windows with wide silver frames."""
    big_a = CK.row_of(5.00, 1.20, 1.90, 10)
    big_b = CK.row_of(3.10, 1.20, 1.90, 11)
    return CK.Coach("Bvcmbz 59-90", 26.4,
                    windows=[Win(2.60, 3.40, "f")] + big_a + [Win(23.80, 24.60, "f")],
                    windows_b=[Win(1.80, 2.60)] + big_b + [Win(23.80, 24.60)],
                    doors=[Door(0.45, 1.35), Door(25.00, 25.90)], bogies=(3.55, 22.65),
                    win_z=(2.00, 2.95), roof_end_m=0.9)


NJ_BLUE = 0x252D70        # sunlit Bmz 21-91 152 (bahnbilder 1385290, Jun 2024)
NJ_RED = 0xE0262A
NJ_GREY = 0xA9ACAD
NIGHTJET = CK.Livery(
    "nightjet", body=NJ_BLUE, roof=0xAEB5B8, roof_top=0xB6BDC0,
    ends=0x3C3F44, door=0xC3C9C6, door_frame=0x2E3034, under=0x3E3B38,
    bogie=0x2A2826, bogie_frame=0x4A4540, frost=0xA7AAB8,
    window_frame=None,
    bands=[Band.line(1.98, NJ_RED),                   # the red line under the windows
           Band.line(1.98, NJ_GREY, below=1),         # thin grey line right under it
           Band(3.06, 3.40, 0x2E3780, over_doors=False)])   # lighter blue roof shoulder
# silver window rims (couchettes, sleepers, the BTEX car; photos 1385292/3)
NIGHTJET_RIMS = NIGHTJET.derive(window_frame=0xA6ACB0, frame_m=0.10, frame_z=0.10)


def nj_marks(label, logo, word):
    """Lettering as read off the sunlit 2024 broadsides (bahnbilder 1385290-3),
    positions as seen from the left end, the same on both sides: the white
    car-type label ("sitzwagen", "liegewagen", "schlafwagen"), the red ÖBB
    logo mid-car and the big grey outline "nightjet" wordmark right of it
    (reads as a light blue-grey dash at 1x). All sit in the blue under the
    red/grey lines. (The vagonWEB drawings show an older lettering layout.)"""
    m = []
    for s in ("a", "b"):
        m += [Mark(label[0], label[1], 0.98, 1.20, 0xE2E6EE, side=s, kind="text", pitch=0.34, duty=0.7),
              Mark(logo, logo + 1.0, 0.92, 1.22, 0xE63036, side=s),
              Mark(word[0], word[1], 0.88, 1.22, 0x8F8BB8, side=s, kind="text", pitch=0.55, duty=0.64)]
    return m


NJ_ROWS = [
    ("Bcmz59-91", bcmz_59_91, NIGHTJET_RIMS, nj_marks((6.2, 8.4), 13.9, (19.7, 22.4))),
    ("WLABmz72-90", wlabmz_72_90, NIGHTJET_RIMS, nj_marks((7.7, 10.1), 13.4, (19.4, 22.2))),
    ("Bvcmbz59-90", bvcmbz_59_90, NIGHTJET_RIMS, nj_marks((6.0, 8.3), 13.9, (19.8, 22.4))),
    ("Bmz21-91", bmz_21_91, NIGHTJET, nj_marks((8.9, 10.8), 14.2, (19.3, 21.8))),
]


def rows_nightjet():
    return [CK.coach_tiles(make(), liv, marks=mk) for (_, make, liv, mk) in NJ_ROWS]


# ====================================================================== DLB
# --- ex-FS Z1 coaches (vagonWEB D-/DLB/B-2190-alex-a/b, ABbmdz-a/b): same
# body and window layout, 11 windows in light-grey frames, swing doors.
def z1(name, first_class=None):
    win = CK.row_of(3.10, 1.30, 1.90, 11)
    return CK.Coach(name, 26.4,
                    windows=[Win(1.80, 2.60, "f")] + win + [Win(23.80, 24.60, "f")],
                    windows_b=[Win(1.85, 2.55)] + win + [Win(23.85, 24.55)],
                    doors=UICZ_DOORS, bogies=(3.55, 22.65), win_z=(1.98, 2.96), eaves_m=3.22)


def abvmz():
    """ex-DB Avmz 111 rebuilt 2007 into ABvmz (20/33 + 2): a deep blue skirt
    reaching lower than on the Z1s, folding doors with a narrow window."""
    win = CK.row_of(3.20, 1.20, 2.10, 10)
    return CK.Coach("ABvmz 39-90", 26.4,
                    windows=[Win(1.80, 2.60, "f")] + win,
                    windows_b=[Win(1.85, 2.55)] + win + [Win(23.90, 24.60)],
                    doors=[Door(0.50, 1.50, style="fold"), Door(24.90, 25.90, style="fold")],
                    bogies=(3.60, 22.80), sill_m=0.66, win_z=(1.98, 3.05), eaves_m=3.42)


# "grey alex" on the Z1 (photo hellertal 910536, Bmz 61 83 21-90 174-5,
# Munich 2019; 2026: bahnbilder 1440718/1437913): mid-grey upper body with
# light-framed windows, a thin orange line under the windows, a white lower
# panel with the blue "alex" logo, a dark grey skirt, light blue-grey roof.
ALEX_LOGO = {"B": 0x5AAEDC, "D": 0x1F3A5C}
ALEX_GREY = CK.Livery(
    "alex", body=0x80878D, roof=0xA9B1B8, roof_top=0xB3BBC2, ends=0x4A4F54,
    door=0x80878D, door_frame=0x2E3134, window_frame=0xABB1B6, frame_m=0.10, frame_z=0.09,
    frost=0xC2C8CC, under=0x34373A,
    bands=[Band(1.00, 1.96, 0xE9EBEB),                # white lower panel
           Band(0.85, None, 0x50555B, px=1),          # dark grey skirt: bottom body row
           Band.line(1.96, 0xF2A200),                 # orange line under the windows
           Band.line(3.22, 0xE2E5E7, over_doors=False)])    # white line under the roof
FIRST_Z1 = Band.line(3.22, 0xF4B400, x0=9.5, x1=15.1, over_doors=False)  # 1st class section

# "blue alex" on the ABvmz (photos hellertal 860585, 2023; bahnbilder 1437913,
# Regensburg 3 Apr 2026, first car behind ES 64 U2-096 of the Praha train)
ALEX_BLUE = CK.Livery(
    "alex", body=0x2479AE, roof=0xC2C7CB, roof_top=0xCBD0D4, ends=0x1F6897,
    door=0x2479AE, door_frame=0x1A3A4C, window_frame=0x93A4AC, frame_m=0.09, frame_z=0.08,
    frost=0xB9C6CC, under=0x2C2F32, end_bands=True,
    bands=[Band(1.00, 1.96, 0xE6E2D2),                # cream lower band
           Band.line(1.96, 0xF2A200),                 # orange line
           Band.line(3.42, 0xF0F3F4, over_doors=False)])    # white line under the roof
FIRST_ABVMZ = Band.line(3.42, 0xE8C443, x0=2.9, x1=11.1, over_doors=False)   # 1st class section


def alex_logo(x=4.5):
    """blue '= alex' logo on the light lower panel near the left end (as seen)
    on both sides: light-blue bars + dark lettering."""
    return [Mark(x, x + 1.9, 1.18, 1.52, side=s, kind="bitmap", bitmap=["BB.DDDDD"], legend=ALEX_LOGO)
            for s in ("a", "b")]


ALEX_ROWS = [
    ("Bmz61-83-21-90", lambda: z1("Bmz 21-90"), ALEX_GREY, alex_logo()),
    ("ABbmdz61-83-21-90", lambda: z1("ABbmdz 21-90"), ALEX_GREY.derive(bands=ALEX_GREY.bands + [FIRST_Z1]),
     alex_logo()),
    ("ABvmz56-80-39-90", abvmz, ALEX_BLUE.derive(bands=ALEX_BLUE.bands + [FIRST_ABVMZ]), alex_logo()),
]


def rows_alex():
    return [CK.coach_tiles(make(), liv, marks=mk) for (_, make, liv, mk) in ALEX_ROWS]


# ====================================================================== main
JOBS = {
    "ic": (os.path.join("obb", "ic"), [("obbsedocervena", rows_obb_ic, [r[0] for r in OBB_IC_ROWS])]),
    "nightjet": (os.path.join("obb", "nightjet"), [("nightjet", rows_nightjet, [r[0] for r in NJ_ROWS])]),
    "alexvozy": (os.path.join("die-landerbahn", "alexvozy"), [("alex", rows_alex, [r[0] for r in ALEX_ROWS])]),
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
