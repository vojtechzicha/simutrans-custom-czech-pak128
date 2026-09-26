#!/usr/bin/env python3
"""Regenerate the European Sleeper coach sheets (ES 452/453 Praha - Brussels).

    python tools/railrender/es_coaches.py                 # every livery sheet
    python tools/railrender/es_coaches.py --preview DIR   # also 4x previews

Writes vehicle-rail/european-sleeper/vozy/sprites/<livery>.png. Every coach is
a coachkit.Coach built from its vagonWEB side drawings (10 px = 1 m, "-a" =
side a, "-b" = side b) and painted with a coachkit.Livery; photos used are
listed in the family.yaml. Change the tables and regenerate instead of painting
the PNGs by hand.

Sheet rows (same row per vehicle in every livery sheet; a vehicle that does not
wear a livery leaves its row empty in that sheet):
  0 Bvcmz 248     couchette (Euro-Express classic / Euro-Express moon / RDC blue)
  1 Bvcmz 248.3   couchette, folding doors (Euro-Express moon)
  2 Bcomh         couchette (Euro-Express classic)
  3 Am            seated car, "Budget" (Euro-Express classic)
  4 WLABmz AB33   sleeper of BTEX (RDC blue)
  5 WLABee AB30   CIWL type P sleeper of GfF, 24.0 m (stainless)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "vehicle-rail", "european-sleeper", "vozy", "sprites")

import numpy as np  # noqa: E402
import coachkit as CK  # noqa: E402
from coachkit import Win, Door, Band, Mark  # noqa: E402
import ric  # noqa: E402  (RDC Bvcmz window table: same car pool as leo-express/bvcmz)

L264 = 26.4


# ====================================================================== types
def bvcmz248():
    """Euro-Express Bvcmz 248 (vagonWEB D-/EURO/Bvcmz248-euro-a/b and -neu-a/b):
    11 windows 1.0 m wide at a 1.9 m pitch, a WC window at each end of side a
    (corridor end windows on side b), narrow swing doors at both ends."""
    win = CK.row_of(3.2, 1.0, 1.9, 11)
    return CK.Coach("Bvcmz 248", L264,
                    windows=[Win(1.9, 2.5, "f")] + win + [Win(23.9, 24.5, "f")],
                    windows_b=[Win(1.9, 2.5)] + win + [Win(23.9, 24.5)],
                    doors=[Door(0.35, 1.15), Door(25.25, 26.05)], bogies=(3.55, 22.65),
                    sill_m=0.85, eaves_m=3.25, win_z=(2.10, 3.02), frost_z=(2.25, 3.02),
                    door_z=(0.45, 3.15), door_win_z=(2.05, 2.95))


def bvcmz2483():
    """Bvcmz 248.3 61 80 50-71 202 (vagonWEB Bvcmz248.3_z-neu-a/b): the same
    window layout, grey window frames, pivoting-folding doors ("Drehfalttüren",
    Commons photo Rotterdam 22 Jul 2024), silver roof."""
    c = bvcmz248()
    c.name = "Bvcmz 248.3"
    c.doors = [Door(0.40, 1.40, style="fold"), Door(25.00, 26.00, style="fold")]
    c.doors_b = CK.mirror(c.doors, L264)
    return c


def bcomh():
    """Euro-Express Bcomh 56 80 50-70 057/058 (vagonWEB Bcomh-a/b): body and
    window layout as the Bvcmz, drop windows with a sash bar."""
    c = bvcmz248()
    c.name = "Bcomh"
    return c


def am():
    """Euro-Express Am 56 80 11-80 019/021 (vagonWEB Am-euro-a/b): compartment
    car, 11 windows, WC windows at 1.8-2.4 m, used as ES "Budget" seats."""
    win = CK.row_of(3.2, 1.0, 1.9, 11)
    return CK.Coach("Am", L264,
                    windows=[Win(1.8, 2.4, "f")] + win + [Win(24.0, 24.6, "f")],
                    windows_b=[Win(1.8, 2.4)] + win + [Win(24.0, 24.6)],
                    doors=[Door(0.30, 1.15), Door(25.25, 26.10)], bogies=(3.55, 22.65),
                    sill_m=0.85, eaves_m=3.25, win_z=(2.10, 3.02), frost_z=(2.25, 3.02),
                    door_z=(0.45, 3.15), door_win_z=(2.05, 2.95))


def bvcmz_rdc():
    """RDC Bvcmz 248 in RDC blue (61 80 50-71 112 ran in ES 452 in May 2026):
    windows, doors and heights from ric.py so it looks exactly like the
    leo-express/bvcmz car of the same pool."""
    win = [Win(a, b, "f" if k == "f" else "w") for (a, b, k) in ric.WIN["Bvcmz"]]
    doors = [Door(a, b) for (a, b) in ric.DOORS]
    return CK.Coach("Bvcmz 248 RDC", L264, windows=win, doors=doors, bogies=tuple(ric.BOGIES),
                    sill_m=0.53, eaves_m=3.40, win_z=(1.9, 3.1), frost_z=(2.25, 3.1),
                    door_z=(0.55, 3.35), door_win_z=(2.05, 2.95))


def wlabmz_ab33():
    """BTEX WLABmz AB33 61 81 71-71 455/457/463 (vagonWEB
    WLABmz-7171-AB33-RDC2-a/b, -RDC_TCS-a/b; Commons photos of sister cars
    456/462 at Paris Nord, 7 Apr 2026): entrance at one end only; side a with
    paired compartment windows and two frosted windows at the far end, side b
    (corridor) with eight wide windows."""
    pairs = [(5.1, 5.9), (6.3, 7.1), (8.9, 9.7), (10.1, 10.9), (12.6, 13.4), (13.8, 14.6),
             (16.4, 17.2), (17.6, 18.4), (20.1, 20.9), (21.3, 22.1), (23.8, 24.6)]
    wide = [(2.2, 3.6), (4.7, 6.1), (7.2, 8.6), (9.7, 11.1), (12.2, 13.6), (14.7, 16.1),
            (17.2, 18.6), (19.7, 21.1)]
    return CK.Coach("WLABmz AB33", L264,
                    windows=[Win(1.6, 2.1, "f"), Win(2.9, 3.4, "f")] + [Win(a, b) for a, b in pairs],
                    windows_b=[Win(a, b) for a, b in wide] + [Win(24.1, 24.6, "f")],
                    doors=[Door(25.0, 26.0)], doors_b=[Door(0.4, 1.4)], bogies=(3.55, 22.65),
                    sill_m=0.85, eaves_m=3.40, win_z=(2.0, 3.0), frost_z=(2.2, 3.0),
                    door_z=(0.45, 3.30), door_win_z=(2.05, 2.95))


def wlabee_ab30():
    """GfF WLABee AB30 61 81 70-70 001/003/004, a CIWL type P sleeper, 24.0 m
    over buffers (vagonWEB WLABee-7070-AB30-a/b, 240 px): corridor side a with
    twenty small windows and the door at the right, compartment side b with ten
    windows and the door at the left (same end)."""
    small = [(2.8, 3.3), (3.8, 4.3), (4.9, 5.4), (5.9, 6.4), (6.8, 7.3), (7.8, 8.3), (8.9, 9.4),
             (9.9, 10.4), (10.8, 11.3), (11.8, 12.3), (12.9, 13.4), (13.9, 14.4), (14.8, 15.3),
             (15.8, 16.3), (16.9, 17.4), (17.9, 18.4), (18.8, 19.3), (19.8, 20.3), (20.9, 21.4),
             (21.9, 22.4)]
    big = CK.row_of(2.1, 0.9, 1.93, 10)
    return CK.Coach("WLABee AB30", 24.0,
                    windows=[Win(1.3, 2.0, "f")] + [Win(a, b) for a, b in small],
                    windows_b=big,
                    doors=[Door(22.8, 23.7)], doors_b=[Door(0.3, 1.2)], bogies=(3.2, 20.8),
                    height_m=4.15, sill_m=0.95, eaves_m=3.35, win_z=(2.1, 3.0),
                    door_z=(0.50, 3.25), door_win_z=(2.1, 2.95))


# ==================================================================== liveries
# Euro-Express classic (vinovokremova): wine red with cream lines - one under
# the roof, a thin one right under the windows and the wide band lower down
# (vagonWEB Bvcmz248-euro, photos Commons "European Sleeper w Euro Express
# Bvcmz 248.3 118-9 / 232-1" 27 Mar 2024, bahnbilder 1444473 Brussels
# 24 Apr 2026, Rotterdam CS 2025).
WINE = 0x952444
CREAM = 0xEAE0C6
EE_CLASSIC = CK.Livery(
    "vinovokremova", body=WINE, roof=0x7C2239, roof_top=0x8C2E45, ends=0x5A1A2C,
    door=WINE, door_frame=0x3A1420, frost=0xCDC6C0, under=0x2C2A2A, end_bands=True,
    bands=[Band.line(3.25, CREAM),                    # line under the roof
           Band.line(2.10, CREAM),                    # thin line right under the windows
           Band.line(2.10, CREAM, below=2)])          # the wide cream band lower down

# Euro-Express "new" livery with the moon (euroexpressmesic): magenta, a cream
# swoosh from the upper left down into a big crescent moon and on, rising to
# the upper right, lighter pink above it, stars, "COUCHETTE" and
# "www.Euro-Express.eu" (vagonWEB Bvcmz248-neu-a/b; photo 56 80 50-71 118-9,
# bahnbilder 1444474, ES 452 Prague - Brussels, 24 Apr 2026).
MAGENTA = 0xC22B6C
PINK = 0xDE78AA
SWOOSH = 0xF2E8D6


def _curve(x):
    """height (m) of the swoosh as seen, or None where it does not run."""
    if 5.0 <= x <= 9.3:
        return 3.10 - (x - 5.0) / 4.3 * 1.55
    if 10.3 <= x <= 20.0:
        return 1.52 + 1.20 * ((x - 10.3) / 9.7) ** 1.25
    if 20.0 < x <= 24.2:
        return 2.72 + (x - 20.0) / 4.2 * 0.40
    return None


def _moon(x, z):
    """cream crescent moon open to the right (centre 9.85 m / 2.25 m)."""
    rx, rz = 0.95, 0.80
    d0 = ((x - 9.85) / rx) ** 2 + ((z - 2.25) / rz) ** 2
    d1 = ((x - 10.35) / (rx * 0.85)) ** 2 + ((z - 2.30) / (rz * 0.85)) ** 2
    return d0 <= 1.0 and d1 > 1.0


def moon_side(t, z):
    x = t                      # the mark spans the whole side: t = drawing x
    if _moon(x, z):
        return SWOOSH
    c = _curve(x)
    if c is not None:
        if abs(z - c) <= 0.19:
            return SWOOSH
        if x >= 10.3 and z > c and z < 3.2:
            return PINK
    return None


def moon_marks(extra_left=0.0):
    m = []
    for s in ("a", "b"):          # the same composition, as seen, on both sides
        m += [Mark(0.0, L264, 1.0, 3.25, side=s, kind="func", fn=moon_side),
              Mark(3.3, 6.2, 1.15, 1.42, 0xF4EEE6, side=s, kind="text", pitch=0.32, duty=0.72),
              Mark(12.2, 17.6, 1.15, 1.42, 0xF4EEE6, side=s, kind="text", pitch=0.36, duty=0.7),
              Mark(23.55, 23.8, 1.45, 3.0, 0xF4EEE6, side=s),          # vertical "COUCHETTE"
              Mark(7.3, 7.55, 2.95, 3.2, 0xFFF6E0, side=s),            # stars
              Mark(18.6, 18.85, 1.2, 1.45, 0xFFF6E0, side=s),
              Mark(21.3, 21.55, 2.3, 2.55, 0xFFF6E0, side=s)]
    return m


EE_MOON = CK.Livery(
    "euroexpressmesic", body=MAGENTA, roof=0x7E3050, roof_top=0x8C3A5A, ends=0x5E1838,
    door=MAGENTA, door_frame=0x3E1026, frost=0xD7C9CE, under=0x2C2A2A, end_bands=False,
    bands=[Band(0.85, None, 0x962056, px=1)],        # darker skirt row
    marks=[])
# Bvcmz 248.3 in the moon livery: silver roof, grey window frames, grey skirt
EE_MOON_2483 = EE_MOON.derive(roof=0xB2B4B6, roof_top=0xBEC0C2, window_frame=0x8E8E8E,
                              bands=[Band(0.85, None, 0x646464, px=1)])

# RDC blue (rdcmodra): exactly the colours of ric.py / leo-express/bvcmz
_R = ric.palette("rdcmodra")


def _c(p):
    return p.base


RDC = CK.Livery(
    "rdcmodra", body=_c(_R["body"]), roof=_c(_R["roof"]), roof_top=_R["roof"].topc,
    door=_c(_R["door"]), door_frame=_c(_R["doorframe"]), door_frame_m=0.12,
    under=_c(_R["under"]), frost=_c(_R["frost"]), ends=_c(_R["body"]),
    bands=[Band(0.0, 0.95, _c(_R["skirt"]))])
RDC_TEXT = _c(_R["text"])


def rdc_bvcmz_marks():
    # white "RDC Zugkraft, die verbindet." broken into words, as in ric.py
    m = []
    for s in ("a", "b"):
        for (a, b) in ((7.4, 9.6), (16.8, 19.0)):
            m.append(Mark(a, b, 1.15, 1.5, RDC_TEXT, side=s, kind="text", pitch=0.55, duty=0.66))
    return m


def rdc_wlab_marks():
    # white "RDC" logos + "Schlafwagen / sleeper" by the door end (photos 2026)
    m = []
    for s, door_x in (("a", 22.3), ("b", 2.2)):
        m += [Mark(9.2, 10.4, 1.35, 1.62, RDC_TEXT, side=s, kind="text", pitch=0.4, duty=0.75),
              Mark(16.9, 18.1, 1.35, 1.62, RDC_TEXT, side=s, kind="text", pitch=0.4, duty=0.75),
              Mark(door_x, door_x + 1.6, 1.30, 1.58, RDC_TEXT, side=s, kind="text", pitch=0.3, duty=0.7)]
    return m


# GfF stainless (nerezova): stainless-steel body, the ribbed lower half a shade
# lighter, a yellow line under the roof, a dark blue line along the sill,
# white doors in blue frames (vagonWEB WLABee-7070-AB30; Commons photo of
# WLABee 004 at Rotterdam 22 Jul 2024).
GFF = CK.Livery(
    "nerezova", body=0xA8ABAC, roof=0x707274, roof_top=0x7C7E80, ends=0x8E9192,
    door=0xDCDCDA, door_frame=0x283C7A, window_frame=0x7A7D7E, frame_m=0.08, frame_z=0.08,
    frost=0xC8CACC, under=0x2A2A2C,
    bands=[Band(1.10, 2.10, 0xB8BCBE),                # ribbed lower half
           Band(0.95, None, 0x1E2A5E, px=1),          # dark blue sill line
           Band.line(3.35, 0xD6C92C)])                # yellow line under the roof


def ee_script():
    """white "Euro-Express" script on the Bcomh (photo Rotterdam CS 2025)."""
    return [Mark(15.8, 20.6, 1.55, 1.78, 0xF4EEE6, side=s, kind="text", pitch=0.4, duty=0.7) for s in ("a", "b")]


# ======================================================================= rows
ROWS = ["Bvcmz248", "Bvcmz248.3", "Bcomh", "Am", "WLABmz-AB33", "WLABee-AB30"]
SHEETS = {
    "vinovokremova": {"Bvcmz248": (bvcmz248, EE_CLASSIC, ()),
                      "Bcomh": (bcomh, EE_CLASSIC, ee_script()),
                      "Am": (am, EE_CLASSIC, ())},
    "euroexpressmesic": {"Bvcmz248": (bvcmz248, EE_MOON, moon_marks()),
                         "Bvcmz248.3": (bvcmz2483, EE_MOON_2483, moon_marks())},
    "rdcmodra": {"Bvcmz248": (bvcmz_rdc, RDC, rdc_bvcmz_marks()),
                 "WLABmz-AB33": (wlabmz_ab33, RDC, rdc_wlab_marks())},
    "nerezova": {"WLABee-AB30": (wlabee_ab30, GFF, ())},
}
EMPTY = None


def rows_for(livery):
    """all 6 rows; rows of vehicles absent from this livery stay transparent
    (and are not referenced by the build)."""
    blank = np.zeros((128, 128, 3), np.uint8)
    blank[:, :] = CK.R.T
    out = []
    for key in ROWS:
        if key in SHEETS[livery]:
            make, liv, marks = SHEETS[livery][key]
            out.append(CK.coach_tiles(make(), liv, marks=marks))
        else:
            out.append([blank.copy() for _ in range(8)])
    return out


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for liv in (args or list(SHEETS)):
        rows = rows_for(liv)
        out = os.path.join(OUT, liv + ".png")
        CK.save_sheet(rows, out)
        if prev:
            keep = [r for r, k in zip(rows, ROWS) if k in SHEETS[liv]]
            CK.preview(keep, os.path.join(prev, "es_%s.png" % liv),
                       labels=[k for k in ROWS if k in SHEETS[liv]])
        print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
