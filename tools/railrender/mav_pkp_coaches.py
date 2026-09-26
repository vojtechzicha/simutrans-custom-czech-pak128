#!/usr/bin/env python3
"""Regenerate the MÁV and PKP Intercity coach sheets (coaches that run
through the Czech Republic in 2026).

    python tools/railrender/mav_pkp_coaches.py                  # all families
    python tools/railrender/mav_pkp_coaches.py mavic pkpvozy    # only these
    python tools/railrender/mav_pkp_coaches.py --preview DIR    # also 4x previews

Families (vehicle-rail/...):
  mavic     mav/ic                   MÁV day coaches of EC 130/131 "Báthory"
                                     and EN 476/477 "Metropol"
  mavnoc    mav/nocni                MÁV sleeper + couchettes (EN 40476/40457
                                     with ÖBB NJ 456/457 Břeclav - Praha - Děčín)
  pkpvozy   pkp-intercity/vozy       PKP IC 26.4 m day coaches (Wien - Břeclav -
                                     Ostrava - Bohumín corridor, Baltic Express)
  pkpnoc    pkp-intercity/nocni      PKP IC couchette + sleepers (EN 406/407
                                     Chopin, EN 476/477 cars, IC 460/461)

Every coach is a coachkit.Coach built from its vagonWEB side drawings
(10 px = 1 m) and painted with a coachkit.Livery; see coachkit.py for the
conventions. Change the tables and regenerate instead of painting the PNGs.

Pixel rows. The body side of the kit (sill 0.85 m .. 3.75 m) is 8 screen
rows in the w/e/n/s/nw/se views and 9 in ne/sw. Every signature stripe is a
px-exact Band (Band.line(3.75, px=1, below=k) = the k-th row from the top),
so it is exactly one row in every view, and the windows (1.95 .. 3.06 m) are
exactly rows 2-4 (3 rows) in every view:
  row 0   cant rail: PKP class line (green / yellow / red), MÁV blue line
  row 1   MÁV turquoise upper swoosh / PKP light grey
  row 2-4 window band (MÁV IC+: row 2 is the white/turquoise field above
          a lower 2-row band, windows rows 3-4 like the real 0.8 m band)
  row 5   MÁV white field with the turquoise wedges / PKP white belt
  row 6   MÁV turquoise lower band / PKP blue stripe (IC logo) / L2 orange
  row 7   MÁV blue lower band / PKP light grey / L2 blue
  (ne/sw only: one more row at the sill = MÁV white strip, PKP grey)

MÁV "IC" livery (2016+). The swooshes are read off the vagonWEB drawing of
the Bmz 2191.1 (START/Bmz-2191-1-m-a) row by row and kept as one base pattern
(MAV_Z1, and MAV_ICP for the IC+ cars). All diagonals lean the same way
("/", bottom further left) on BOTH sides as seen - the drawings of the
Bmz 2191.3, WLABmz and Bbdpmz sides a and b, and the photos of Bcmz 202-1
(Koper, Aug 2026) and Bmz 104 (vagonWEB 2023) agree. Cars with a large
blue end zone at one end (WLABmz, Bcmz, WRRmz, Bbdpmz) push that end's
swoosh inwards by the zone length (s_left / s_right), which reproduces their
drawings within 0.2 m.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import coachkit as CK  # noqa: E402
from coachkit import Win, Door, Band, Mark, RoofBox  # noqa: E402
from railkit import Part, Paint  # noqa: E402

TOP = 3.75                 # body side top (m): row k hangs from here
WIN_Z = (1.95, 3.06)       # 3 rows (rows 2-4) in every view
WIN_Z_ICP = (1.95, 2.69)   # 2 rows (rows 3-4): the lower IC+ band
DOOR_Z = (0.45, 3.254)     # leaf from the step to row 1 (its top frame)
DOOR_WIN_Z = (1.95, 3.00)  # door window = the window rows


def row(k, color, x0=None, x1=None, side="both", px=1, over_doors=False):
    """px-exact band: the k-th screen row from the side top (k = 0..7)."""
    return Band.line(TOP, color, px=px, below=k, x0=x0, x1=x1, side=side, over_doors=over_doors)


def coach(name, length_m=26.4, **kw):
    kw.setdefault("win_z", WIN_Z)
    kw.setdefault("frost_z", WIN_Z)
    kw.setdefault("high_z", WIN_Z)
    kw.setdefault("door_z", DOOR_Z)
    kw.setdefault("door_win_z", DOOR_WIN_Z)
    kw.setdefault("eaves_m", 3.80)          # no roof colour on the side face
    return CK.Coach(name, length_m, **kw)


# ====================================================================== MÁV
M_BLUE = 0x1C4B91          # enciánkék (gentian blue), photos Bpmz 412 / Bmz 104
M_TURQ = 0x33AFCF          # lagúnakék (lagoon blue): swooshes and doors
M_WHITE = 0xDFE2DE         # szürkésfehér (greyish white)
M_BAND = 0x1E2433          # blackish-blue window band
M_ROOF = 0x9A9C9E
M_GOLD = 0xC9A227
M_NAVY = 0x1C2F6E
M_PICTO = 0xECEEF0         # white pictograms on the blue end zones
COL = {"b": M_BLUE, "t": M_TURQ, "W": M_WHITE}

# Base pattern of one side as seen, per semantic row: [(x from, code), ...]
# (metres along the drawing, codes b/t/W). Read off START/Bmz-2191-1-m-a
# (Z1: CAF / DWA / GOŠA 26.4 m cars) and START/Bpmz-2091-4-a (IC+).
MAV_Z1 = {
    "U": [(0, "b"), (3.0, "W"), (5.2, "b"), (22.5, "W"), (24.1, "b")],          # 3.45 m
    "T": [(0, "b"), (2.9, "W"), (5.1, "b"), (5.9, "t"), (21.5, "b"), (22.5, "W"), (24.05, "b")],
    "W": [(0, "b"), (2.25, "W"), (4.35, "b"), (5.2, "t"), (6.8, "W"), (19.5, "t"), (21.1, "b"),
          (21.9, "W"), (23.3, "b")],                                            # 1.85 m
    "t": [(0, "b"), (2.1, "W"), (4.2, "b"), (5.0, "t"), (20.9, "b"), (21.75, "W"), (23.3, "b")],
    "L": [(0, "b"), (2.0, "W"), (4.1, "b"), (21.35, "W"), (23.15, "b")],         # 1.35 m
    "S": [(0, "b"), (1.9, "W"), (23.05, "b")],                                   # 1.15 m
}
MAV_ICP = {
    "U": [(0, "b"), (2.95, "W"), (5.45, "b"), (22.45, "W"), (24.1, "b")],
    "T": [(0, "b"), (2.9, "W"), (5.25, "b"), (6.1, "t"), (21.5, "b"), (22.5, "W"), (24.05, "b")],
    "Bt": [(0, "b"), (2.75, "W"), (4.85, "b"), (5.7, "t"), (7.3, "W"), (20.0, "t"), (21.4, "b"),
           (22.4, "W"), (23.9, "b")],                                           # 2.8 m, above the band
    "W": MAV_Z1["W"],
    "t": [(0, "b"), (2.1, "W"), (4.2, "b"), (5.0, "t"), (20.9, "b"), (21.75, "W"), (23.75, "b")],
    "L": [(0, "b"), (2.0, "W"), (4.1, "b"), (21.35, "W"), (23.75, "b")],
    "S": [(0, "b"), (1.9, "W"), (23.8, "b")],
}


def _code(pat, x):
    c = pat[0][1]
    for (x0, cc) in pat:
        if x >= x0:
            c = cc
    return c


def _runs(pat, L, sl, sr, step=0.05):
    """(x0, x1, code) runs of a base pattern on a side whose left / right end
    swoosh is pushed inwards by sl / sr metres (big blue end zones)."""
    out = []
    n = int(round(L / step))
    for i in range(n):
        x = (i + 0.5) * step
        xb = x - sl if x < L / 2 else x + sr
        c = "b" if (xb < 0 or xb > L) else _code(pat, xb)
        if out and out[-1][2] == c:
            out[-1][1] = (i + 1) * step
        else:
            out.append([i * step, (i + 1) * step, c])
    return [(a, b, c) for a, b, c in out]


def mav_bands(L, sides, icplus=False):
    """Livery bands of a MÁV car. sides: {"a"/"b": (s_left, s_right, band_x0,
    band_x1)} - the swoosh shifts and the window band extent of that side as
    seen. Rows: 0 U, 1 T, 2-4 band (IC+: 2 Bt, 3-4 band), 5 W, 6 t, 7 L,
    and the S row (white sill strip) in the extra ne/sw row."""
    pat = MAV_ICP if icplus else MAV_Z1
    bands = []
    for side, (sl, sr, bx0, bx1) in sides.items():
        # sill strip first (metres, lowest priority: only the ne/sw extra row)
        for a, b, c in _runs(pat["S"], L, sl, sr):
            bands.append(Band(0.0, 1.21, COL[c], x0=a, x1=b, side=side, over_doors=False))
        plan = [(0, "U"), (1, "T"), (5, "W"), (6, "t"), (7, "L")]
        if icplus:
            plan.append((2, "Bt"))
        for k, key in plan:
            for a, b, c in _runs(pat[key], L, sl, sr):
                bands.append(row(k, COL[c], a, b, side))
        # window band rows: the T pattern outside the band (end zones and the
        # white wedge where a shortened band ends under it), dark inside
        k0, n = (3, 2) if icplus else (2, 3)
        for a, b, c in _runs(pat["T"], L, sl, sr):
            bands.append(Band.line(TOP, COL[c], px=n, below=k0, x0=a, x1=b, side=side, over_doors=False))
        bands.append(Band.line(TOP, M_BAND, px=n, below=k0, x0=bx0, x1=bx1, side=side, over_doors=False))
    return bands


def mav_livery(bands, marks=()):
    return CK.Livery(
        "mavic", body=M_WHITE, roof=M_ROOF, roof_top=0xA5A7A9, roof_eq=0x7C8084,
        ends=M_BLUE, door=M_TURQ, door_frame=0x10285A, frost=0x7C8894, dark_glass=0x2A343D,
        under=0x3E454D, bogie=0x2E2F31, bogie_frame=0x44474B, gangway=0x24262A,
        glass_hi_m=0.37, bands=bands, marks=list(marks))


def mav_logo(x, side):
    """MÁV winged wheel (gold) + navy wordmark on the white lower wedge."""
    return [Mark(x, x + 0.45, 1.13, 1.50, M_GOLD, side=side),
            Mark(x + 0.55, x + 1.7, 1.13, 1.50, M_NAVY, side=side, kind="text", pitch=0.40, duty=0.6)]


def mav_plate(x, side="both"):
    """white class plate with the black numeral beside a door, on the band."""
    return [Mark(x, x + 0.40, 2.20, 2.95, 0xE6E8EA, side=side)]


BED = ["WWWWW", "W...W"]                       # bed / couchette pictogram
BIKE = ["WW.GWW", "WW..WW"]                    # two wheels + green check
CUTLERY = [".W.W", "W.W.", "W.W."]            # knife and fork


def picto(x0, x1, z0, z1, bitmap, side):
    return Mark(x0, x1, z0, z1, M_PICTO, side=side, kind="bitmap", bitmap=bitmap,
                legend={"W": M_PICTO, "G": 0x2FA84F})


def mav_roof_ends(coach_, blue=M_BLUE, cap_m=1.4):
    """extra(): the blue end zones continue over the roof ends."""
    def extra(parts, u0, owner):
        s = coach_.scale
        L = coach_.length_cu
        W = coach_.half_width()
        zs = min(CK.ZS, CK.zm(coach_.height_m) - 0.5)
        zr = CK.zm(coach_.height_m)
        re_ = coach_.roof_end_m / s
        ub0, ub1 = u0 + 0.14 + re_, u0 + L - 0.14 - re_
        pb = Paint(blue, top=blue)
        for a, b in ((ub0 - 0.01, ub0 + cap_m / s), (ub1 - cap_m / s, ub1 + 0.01)):
            parts.append(Part(a, b, -W + 0.19, W - 0.19, zs - 0.02, zr + 0.03, lambda *a_: pb, owner))
    return extra


Z1_DOORS = [Door(0.50, 1.60), Door(24.80, 25.90)]


def mav_amz():
    """Amz 61 55 19-91 (1991.1 CAF / 1991.3 DWA): 9 compartments, 54 seats."""
    win = [Win(1.9, 2.5, "f")] + CK.row_of(3.4, 1.3, 2.3, 9) + [Win(23.9, 24.5, "f")]
    c = coach("Amz 19-91", windows=win, doors=Z1_DOORS, roof="ac")
    bands = mav_bands(26.4, {"a": (0, 0, 1.6, 24.8), "b": (0, 0, 1.6, 24.8)})
    marks = mav_plate(2.60) + mav_logo(2.40, "a") + mav_logo(2.40, "b")
    return c, mav_livery(bands, marks)


def mav_bmz():
    """Bmz 61 55 21-91 (2191.0 GOŠA / .1 CAF / .3 DWA): 11 compartments, 66
    seats; frosted WCs on the compartment side a, clear end windows on the
    corridor side b (Bmz-2191-3-m-b)."""
    comp = CK.row_of(3.1, 1.2, 1.9, 11)
    c = coach("Bmz 21-91", windows=[Win(1.9, 2.5, "f")] + comp + [Win(23.9, 24.5, "f")],
              windows_b=[Win(1.9, 2.5)] + comp + [Win(23.9, 24.5)], doors=Z1_DOORS, roof="ac")
    bands = mav_bands(26.4, {"a": (0, 0, 1.6, 24.8), "b": (0, 0, 1.6, 24.8)})
    marks = mav_plate(2.60) + mav_logo(2.40, "a") + mav_logo(2.40, "b")
    return c, mav_livery(bands, marks)


def mav_bpmz():
    """Bpmz 61 55 20-91.1 (CAF) / 20-71 (DWA): open 2nd class, 80 seats."""
    win = [Win(1.9, 2.5, "f")] + CK.row_of(3.1, 1.3, 2.1, 10) + [Win(23.9, 24.5, "f")]
    c = coach("Bpmz 20-91", windows=win, doors=Z1_DOORS, roof="ac")
    bands = mav_bands(26.4, {"a": (0, 0, 1.6, 24.8), "b": (0, 0, 1.6, 24.8)})
    marks = mav_plate(2.60) + mav_logo(2.40, "a") + mav_logo(2.40, "b")
    return c, mav_livery(bands, marks)


def mav_bpmz_icp():
    """Bpmz 61 55 20-91.4 IC+ (MÁV Szolnok 2019): open, 80 seats, flush
    windows in a lower band (1.9-2.7 m)."""
    win = [Win(2.3, 2.9)] + CK.row_of(3.7, 1.3, 2.1, 10)
    c = coach("Bpmz 20-91 IC+", windows=win, doors=Z1_DOORS, win_z=WIN_Z_ICP, frost_z=WIN_Z_ICP,
              door_win_z=WIN_Z_ICP, roof="ac")
    bands = mav_bands(26.4, {"a": (0, 0, 1.6, 24.8), "b": (0, 0, 1.6, 24.8)}, icplus=True)
    marks = mav_plate(3.10) + mav_logo(2.40, "a") + mav_logo(2.40, "b")
    return c, mav_livery(bands, marks)


def mav_bbdpmz():
    """Bbdpmz 61 55 84-91.4 IC+ multi-purpose car (8 bikes, wheelchair
    place): the second door moved inboard (6.0-7.2 m on side a), a blue end
    zone with two windows and the big white bicycle pictogram beyond it
    (drawings Bbdpmz-8491-4-a/b, photo Bbdpmz 406-8 Kőbánya-Kispest)."""
    win_a = [Win(2.1, 3.5), Win(4.1, 5.5)] + CK.row_of(7.9, 1.3, 2.1, 8)
    doors_a = [Door(6.00, 7.20), Door(24.80, 25.90)]
    c = coach("Bbdpmz 84-91 IC+", windows=win_a, doors=doors_a, win_z=WIN_Z_ICP, frost_z=WIN_Z_ICP,
              door_win_z=WIN_Z_ICP, roof="ac")
    bands = mav_bands(26.4, {"a": (5.5, 0, 7.3, 24.7), "b": (0, 5.6, 1.7, 19.1)}, icplus=True)
    marks = (mav_plate(9.40, "a") + mav_plate(16.60, "b") + mav_plate(22.00, "a") + mav_plate(4.00, "b")
             + [picto(0.9, 4.3, 1.20, 1.90, BIKE, "a"), picto(22.1, 25.5, 1.20, 1.90, BIKE, "b")]
             + mav_logo(10.9, "a") + mav_logo(2.40, "b"))
    return c, mav_livery(bands, marks)


def mav_wrrmz():
    """WRRmz 61 55 88-71 (DWA 1995, rebuilt 2020-21): bistro-restaurant,
    30 + 21 places, one entrance (right of drawing a), the kitchen zone with
    two small windows in the big blue end zone, the white knife and fork on
    the blue at the other end (drawing WRRmz-m-a)."""
    dining = [Win(2.0, 3.2), Win(3.9, 5.1), Win(5.7, 6.9), Win(7.5, 8.7), Win(9.3, 10.5)]
    bar = [Win(11.6, 12.8), Win(15.4, 16.6), Win(19.2, 20.4)]
    kitchen = [Win(21.0, 22.2, "x"), Win(22.9, 24.1, "x")]
    c = coach("WRRmz 88-71", windows=dining + bar + kitchen, doors=[Door(24.80, 25.90)], roof="ac")
    bands = mav_bands(26.4, {"a": (0, 3.0, 1.9, 20.8), "b": (3.0, 0, 5.6, 24.5)})
    marks = ([picto(0.35, 1.75, 1.60, 2.95, CUTLERY, "a"), picto(24.65, 26.05, 1.60, 2.95, CUTLERY, "b")]
             + mav_logo(2.40, "a") + mav_logo(5.40, "b"))
    return c, mav_livery(bands, marks)


def mav_wlabmz():
    """WLABmz 62 55 71-91.0 (Waggonbau Görlitz 1994-95, ex-RŽD/LG, MÁV since
    2020): 11 x 3 berths. Side a = compartment side (12 windows, one of them
    in the blue end zone with the bed pictogram), side b = corridor side
    (drawings WLABmz-7191-0-m-a/b, photo 003-7 Wien)."""
    comp = [Win(3.2, 4.1)] + [Win(x, x + 0.9) for x in (6.2, 7.7, 9.4, 10.9, 12.6, 14.1, 15.8, 17.3,
                                                         19.0, 20.5, 22.2)]
    corr = [Win(2.0, 2.4, "f"), Win(2.6, 3.5)] + [Win(x, x + 0.9) for x in (5.7, 9.0, 12.2, 15.3, 18.6)] \
        + [Win(21.5, 22.4)]
    c = coach("WLABmz 71-91", windows=comp, windows_b=corr,
              doors=[Door(0.40, 1.50), Door(24.85, 25.95)], doors_b=[Door(0.45, 1.55), Door(24.9, 26.0)],
              roof="sleeper")
    bands = mav_bands(26.4, {"a": (2.6, 0, 4.9, 24.9), "b": (0, 2.6, 1.5, 19.6)})
    marks = ([picto(1.9, 3.9, 1.30, 1.85, BED, "a"), picto(22.5, 24.5, 1.30, 1.85, BED, "b")]
             + mav_logo(7.0, "a") + mav_logo(2.40, "b"))
    return c, mav_livery(bands, marks)


def mav_bcmz_2():
    """Bcmz 61 55 50-91.2 (ex-DB Bvcmz, rebuilt, MÁV since 2020): couchette,
    10 compartments; narrow doors near the ends, rounded roof ends, the
    couchette pictogram on the blue end zone beside two separate windows
    (drawing Bcmz-5091-2-m-a; photo 202-1 Koper Aug 2026 shows that zone at
    the other end on the other side, i.e. at the same physical end)."""
    win_a = [Win(1.9, 2.5, "f"), Win(3.2, 4.2)] + CK.row_of(5.1, 1.0, 1.9, 10) + [Win(23.9, 24.5, "f")]
    c = coach("Bcmz 50-91.2", windows=win_a, doors=[Door(0.35, 1.35), Door(25.05, 26.05)],
              roof="plain", roof_end_m=0.9)
    bands = mav_bands(26.4, {"a": (2.8, 0, 5.0, 25.0), "b": (0, 2.8, 1.4, 21.4)})
    marks = ([picto(1.6, 3.7, 1.30, 1.85, BED, "a"), picto(22.7, 24.8, 1.30, 1.85, BED, "b")]
             + mav_logo(5.2, "a") + mav_logo(2.40, "b"))
    return c, mav_livery(bands, marks)


def mav_bcmz_1():
    """Bcmz 61 55 50-91.1 (CAF 1994, rebuilt 2018-20): couchette, the Bmz
    2191.1 body; the first compartment window stands in the blue end zone
    (drawing Bcmz-5091-1-m-a)."""
    win_a = [Win(1.9, 2.5, "f"), Win(3.1, 4.3)] + CK.row_of(5.0, 1.2, 1.9, 10) + [Win(23.9, 24.5, "f")]
    c = coach("Bcmz 50-91.1", windows=win_a, doors=Z1_DOORS, roof="ac")
    bands = mav_bands(26.4, {"a": (2.7, 0, 4.9, 24.8), "b": (0, 2.7, 1.6, 21.5)})
    marks = ([picto(1.6, 3.7, 1.30, 1.85, BED, "a"), picto(22.7, 24.8, 1.30, 1.85, BED, "b")]
             + mav_logo(5.2, "a") + mav_logo(2.40, "b"))
    return c, mav_livery(bands, marks)


MAV_IC_ROWS = [("Amz19-91", mav_amz), ("Bmz21-91", mav_bmz), ("Bpmz20-91", mav_bpmz),
               ("Bpmz20-91-ICp", mav_bpmz_icp), ("Bbdpmz84-91", mav_bbdpmz), ("WRRmz88-71", mav_wrrmz)]
MAV_NOC_ROWS = [("WLABmz71-91", mav_wlabmz), ("Bcmz50-91-2", mav_bcmz_2), ("Bcmz50-91-1", mav_bcmz_1)]


def rows_mav(table):
    out = []
    for _, make in table:
        c, liv = make()
        out.append(CK.coach_tiles(c, liv, extra=mav_roof_ends(c)))
    return out


# ====================================================================== PKP IC
# L1 current day scheme (2025/26 photos: B 11 mnouz 171A 185-3 Koper Aug
# 2026, B 9 mnopuvz 154A-10 and A 9 mnouz Z2A vagonWEB May 2026, B 10 bmnouz
# XBN Wien May 2026, WRmnouz 194-5 Warszawa Dec 2024): light grey body, the
# class line at the cant rail, a black window band with blue doors, a white
# belt under it, the ultramarine stripe interrupted by the IC logo near the
# left end (as seen), light grey below. The older look (framed windows on
# grey, grey doors: photos 144A 2012, 170A 2015, Trako 2017, Z2A Praha 2022)
# is gone from the 2026 photos, so it is not shipped.
P_BODY = 0xC5C9CF
P_BELT = 0xE8EAEC
P_STRIPE = 0x2F3596
P_BAND = 0x2B2B30
P_DOOR = 0x2B3E9E
P_GREEN = 0x2DB34A
P_YELLOW = 0xEBC40F
P_RED = 0xC8102E
P_ORANGE = 0xF26522
P_NUM = 0x3050B8


def pkp_l1(line, band_x, logo_x=3.0, extra_bands=(), marks=()):
    bx0, bx1 = band_x
    bands = [Band(0.0, 1.21, P_BODY),                              # grey sill row (ne/sw)
             row(0, line, 1.55, 24.85),                            # class line
             row(1, P_BODY),
             Band.line(TOP, P_BAND, px=3, below=2, x0=bx0, x1=bx1, over_doors=False),
             row(5, P_BELT),
             row(6, P_STRIPE, 1.55, logo_x - 0.1, side="a"), row(6, P_STRIPE, logo_x + 2.5, 24.85, side="a"),
             row(6, P_STRIPE, 1.55, logo_x - 0.1, side="b"), row(6, P_STRIPE, logo_x + 2.5, 24.85, side="b"),
             row(7, P_BODY)] + list(extra_bands)
    logo = []
    for s in ("a", "b"):
        logo += [Mark(logo_x, logo_x + 0.9, 1.13, 1.85, P_ORANGE, side=s),
                 Mark(logo_x + 1.1, logo_x + 2.4, 1.13, 1.48, 0x202226, side=s, kind="text", pitch=0.40,
                      duty=0.6)]
    return CK.Livery(
        "intercity", body=P_BODY, roof=0xB0B4B8, roof_top=0xBEC2C6, roof_eq=0x8A8E92,
        ends=0xB4B8BE, door=P_DOOR, door_frame=0x161A42, frost=0x7E848C, dark_glass=0x59616B,
        under=0x5A5F64, bogie=0x2E3033, bogie_frame=0x46494D, gangway=0x2A2C2E,
        glass_hi_m=0.37, bands=bands, marks=logo + list(marks))


def numerals(xs, side="both"):
    """the big blue class numeral beside each door (on the grey, window height)."""
    return [Mark(x, x + 0.40, 2.25, 2.95, P_NUM, side=side) for x in xs]


PKP_DOORS = [Door(0.50, 1.50), Door(24.90, 25.90)]


def pkp_a9():
    """A 9 emnouz / A 9 mnouz (HCP Z2 156A / 139A, FPS Z2A): 1st class, 9
    compartments (drawings A9emnouz-156A-m-v2-a, A9mnouz-Z2AMg-FPS-m-a)."""
    win = [Win(1.8, 2.4, "f")] + CK.row_of(3.65, 1.35, 2.2, 9) + [Win(24.0, 24.6, "f")]
    c = coach("A 9 emnouz", windows=win, doors=PKP_DOORS, roof="ac")
    return c, pkp_l1(P_YELLOW, (3.55, 22.85), marks=numerals((2.95, 23.05)))


def pkp_b11():
    """B 11 mnouz (HCP Z2 144A / 170A / 171A / 136A, FPS XB / Z2B): 11
    compartments, 66 seats (drawings B11mnouz-171A-m-a, -144A-FPS-m-a)."""
    win = [Win(1.8, 2.4, "f")] + CK.row_of(3.1, 1.3, 1.9, 11) + [Win(24.0, 24.6, "f")]
    c = coach("B 11 mnouz", windows=win, doors=PKP_DOORS, roof="ac")
    return c, pkp_l1(P_GREEN, (3.05, 23.35), marks=numerals((2.55, 23.45)))


def pkp_b10b():
    """B 10 bmnouz (FPS Z1B-20 / XBN, 156A): 10 compartments and a wheelchair
    place with its big WC at one end, where the band has no window (drawing
    B10bmnouz-Z1B-FPS-a)."""
    win = [Win(1.8, 2.4, "f")] + CK.row_of(3.1, 1.3, 1.9, 10) + [Win(24.0, 24.6, "f")]
    c = coach("B 10 bmnouz", windows=win, doors=PKP_DOORS, roof="ac")
    return c, pkp_l1(P_GREEN, (3.05, 23.15),
                     marks=numerals((2.55, 23.25)) + [Mark(21.9, 22.4, 1.55, 1.85, P_STRIPE)])


def pkp_b9():
    """B 9 mnopuvz (Pesa 154A / 154Aa, HCP 159A): open 2nd class, 72 seats,
    bicycle places behind the last window (drawing B9mnopuvz-154A-Pesa-a;
    photo 154A-10 vagonWEB Apr 2026 with the black bicycle pictogram)."""
    win = CK.row_of(3.7, 1.2, 2.2, 9)
    c = coach("B 9 mnopuvz", windows=win, doors=PKP_DOORS, roof="ac")
    return c, pkp_l1(P_GREEN, (3.6, 22.8),
                     marks=numerals((2.95, 23.1)) + [Mark(22.9, 23.7, 1.55, 1.85, 0x202226, side="a"),
                                                     Mark(2.7, 3.5, 1.55, 1.85, 0x202226, side="b")])


def pkp_wr():
    """WRmnouz (61 51 88-70 19x, 406A): restaurant car, one entrance at the
    kitchen end; two kitchen windows, 7 dining windows (drawing
    WRmnouz-m-a/b; photo 194-5 Warszawa Dec 2024: red line + black band)."""
    win = [Win(3.7, 4.8, "x"), Win(7.3, 8.4, "x")] + CK.row_of(11.2, 1.1, 1.8, 7) + [Win(23.8, 24.4, "x")]
    c = coach("WRmnouz", windows=win, doors=[Door(0.50, 1.50)], roof="ac")
    return c, pkp_l1(P_RED, (3.6, 23.2))


# L3 older restaurant scheme on the "WRmnouz a" cars 61 51 88-70 182 / 183
# (in the corridor sets in Aug-Sep 2026; drawing WRmnouz-a, photos 182-0 Wien
# Dec 2019, 190-3 in EC 100 at Wien 2018): pale blue-grey body, separate
# windows, a red band under the roof, white belt and blue stripe.
def pkp_wr_old():
    win = [Win(3.7, 4.8, "x"), Win(7.3, 8.4, "x")] + CK.row_of(9.4, 1.2, 1.8, 8) + [Win(23.8, 24.4, "x")]
    c = coach("WRmnouz a", windows=win, doors=[Door(0.50, 1.50)], roof="ac")
    body = 0xC6CDD9
    bands = [Band(0.0, 1.21, 0xB9C0CB), row(0, 0xB8141C), row(5, 0xE6E9EC),
             row(6, P_STRIPE, 1.55, 2.9, side="a"), row(6, P_STRIPE, 5.5, 24.85, side="a"),
             row(6, P_STRIPE, 1.55, 2.9, side="b"), row(6, P_STRIPE, 5.5, 24.85, side="b"),
             row(7, 0xB9C0CB)]
    liv = pkp_l1(P_RED, (0, 0)).derive(body=body, door=0xB9C0CB, door_frame=0x3C4046, ends=0xAEB5C0,
                                       bands=bands)
    return c, liv


PKP_DAY_ROWS = [("A9emnouz", pkp_a9), ("B11mnouz", pkp_b11), ("B10bmnouz", pkp_b10b),
                ("B9mnopuvz", pkp_b9), ("WRmnouz", pkp_wr), ("WRmnouz-a", pkp_wr_old)]


# L2 night scheme (photos 134Ab 006-5 Budapest Jun 2019, 308A Świnoujście
# Jul 2017, 134A Warszawa 2012): ultramarine body, separate windows, a white
# band under the windows with the orange line in its lower part, ultramarine
# below, blue doors and ends.
N_BLUE = 0x3040A8
N_WHITE = 0xEEF0F6
N_ORANGE = 0xF05A28


def pkp_l2():
    bands = [row(5, N_WHITE), row(6, N_ORANGE), row(7, N_BLUE)]
    logo = []
    for s in ("a", "b"):
        logo += [Mark(9.0, 9.9, 1.50, 1.87, P_ORANGE, side=s),
                 Mark(10.0, 11.3, 1.50, 1.87, 0x202226, side=s, kind="text", pitch=0.40, duty=0.6)]
    return CK.Livery(
        "modrobila", body=N_BLUE, roof=0xA8ACB0, roof_top=0xB4B8BC, roof_eq=0x80848A,
        ends=N_BLUE, door=N_BLUE, door_frame=0x141A4A, frost=0x7E848C, dark_glass=0x2A2E36,
        under=0x4A4F55, bogie=0x2E3033, bogie_frame=0x46494D, gangway=0x2A2C2E,
        glass_hi_m=0.37, bands=bands, marks=logo)


def pkp_bc10():
    """Bc 10 mnouz 134Ab (HCP 1991-92; 172A modernised): couchette, 10
    compartments + attendant, the entrance at one end only (drawings
    Bc10mnouz-134Ab-m-a/b)."""
    win = [Win(1.8, 2.4, "f")] + CK.row_of(3.3, 1.1, 1.89, 11) + [Win(24.0, 24.6, "f")]
    c = coach("Bc 10 mnouz", windows=win, doors=[Door(0.50, 1.50)], roof="ac")
    return c, pkp_l2()


def pkp_wlab10():
    """WLAB 10 mnouz 305Ad: sleeper, 10 compartments + attendant, entrance at
    one end (drawing WLABmnouz-305Ad-m-a)."""
    xs = (2.2, 4.0, 5.8, 7.6, 9.4, 13.0, 14.8, 16.6, 18.4, 20.2, 22.0)
    c = coach("WLAB 10 mnouz", windows=[Win(x, x + 1.0) for x in xs], doors=[Door(24.90, 25.90)],
              roof="sleeper")
    return c, pkp_l2()


def pkp_wlab9():
    """WLAB 9 bmnouz 308A: 24.5 m sleeper, 9 compartments incl. an accessible
    one (drawing WLAB9bnouz-308A-m-a, photo 308A Świnoujście 2017)."""
    xs = (3.3, 5.0, 6.7, 8.4, 10.1, 11.8, 13.5, 15.2, 16.9, 18.6)
    win = [Win(1.9, 2.6)] + [Win(x, x + 0.9) for x in xs] + [Win(21.5, 22.2, "f")]
    c = coach("WLAB 9 bmnouz", 24.5, windows=win, doors=[Door(23.00, 24.00)], bogies=(3.65, 20.65),
              bogie_wheelbase_m=2.3, roof="sleeper")
    return c, pkp_l2()


PKP_NOC_ROWS = [("Bc10mnouz", pkp_bc10), ("WLAB10mnouz", pkp_wlab10), ("WLAB9bmnouz", pkp_wlab9)]


def rows_simple(table):
    out = []
    for _, make in table:
        c, liv = make()
        out.append(CK.coach_tiles(c, liv))
    return out


# ====================================================================== main
JOBS = {
    "mavic": (os.path.join("mav", "ic"), [("mavic", lambda: rows_mav(MAV_IC_ROWS), MAV_IC_ROWS)]),
    "mavnoc": (os.path.join("mav", "nocni"), [("mavic", lambda: rows_mav(MAV_NOC_ROWS), MAV_NOC_ROWS)]),
    "pkpvozy": (os.path.join("pkp-intercity", "vozy"),
                [("intercity", lambda: rows_simple(PKP_DAY_ROWS), PKP_DAY_ROWS)]),
    "pkpnoc": (os.path.join("pkp-intercity", "nocni"),
               [("modrobila", lambda: rows_simple(PKP_NOC_ROWS), PKP_NOC_ROWS)]),
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
        for liv, make, table in sheets:
            rows = make()
            out = os.path.join(REPO, "vehicle-rail", rel, "sprites", liv + ".png")
            CK.save_sheet(rows, out)
            if prev:
                CK.preview(rows, os.path.join(prev, "%s_%s.png" % (fam, liv)), labels=[r[0] for r in table])
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
