"""ČD loco-hauled coaches, drawn from vagonWEB scale side drawings.

Every type is a list of openings (windows, doors) in metres from the car's front
buffer face, read from the vagonWEB drawing `popisy/img/CD/<name>-a.gif`
(10 px = 1 m; the drawing name is noted per type). Rendered with railkit
(the box raycaster calibrated to the native CD_Bmz241), 24.5 m cars as length 12,
26.4-26.9 m cars as length 13 (about 2.04 m per carunit).

The blue Najbrt coaches differ little in reality, so each type keeps the real
details that survive at ~70 px per car:
  - length (24.5 m UIC-Y = 12 cu, 26.4 m UIC-Z/X = 13 cu)
  - window rhythm (compartment 1.9 m pitch, wide saloon windows, 1st class 2.1 m)
  - doors: end doors (plug / folding), honecker doors at 1/4 and 3/4, the wide
    lift door of Bbdgmee 236 / Bhmpz 228, luggage doors of BDs 449
  - window frames: the ex-ÖBB cars carry white, black or blue frames (vagonWEB
    variants -br / -cr / -mr), the rebuilt cars dark rubber
  - roof: Najbrt 2 sapphire, Najbrt 1 umbra grey, ÖBB red; AC units or vents
  - the yellow 1st-class line over the 1st-class part only, the inverted dark
    band of restaurant / sleeper / couchette cars, the blue lower body of BD
  - pictograms on the window band: bicycle, wheelchair, children's compartment
"""
import railkit as R
from railkit import Paint, Part, Lit
from render import DIRS

PX = 0.375                 # metres per model px
W = R.W_STD
ZB = 1.4                   # body bottom (skirt starts), model px
ZS = R.H_SIDE              # 10.0 = 3.75 m, side wall top
ZR = ZS + R.H_CAP          # 10.8 = 4.05 m, roof crown


def row(start, n, pitch, w, kind="w"):
    return [(round(start + i * pitch, 2), round(start + i * pitch + w, 2), kind) for i in range(n)]


# ------------------------------------------------------------------ types
# L:      length over buffers, m
# win:    (from_m, to_m, kind); kinds: w glass, f frosted (WC), m glass with a
#         centre mullion, t drop-light (transom bar, non-AC cars), p panorama
# doors:  leaf spans; door: plug | fold | dbl (honecker double leaf)
# first:  spans (m) that carry the yellow 1st-class line; "all" = whole car
# inv:    restaurant / sleeper / couchette colours (dark window band)
# frame:  window frame colour: w white, k black, b blue, None = dark rubber
# roofp:  z (UIC-Z, flat curve), y (UIC-Y, rounded with sloping ends), x (honecker)
# ac:     roof AC units; vents: small roof ventilators (non-AC)
# picto:  (m_from, m_to, kind) pictograms on the window band: bike, wheel, kids
# lift:   index of the wide lift door in `doors` (blue wheelchair square)
E26 = [(0.5, 1.5), (24.9, 25.9)]
E24 = [(0.5, 1.4), (23.1, 24.0)]
E24P = [(0.5, 1.5), (23.0, 24.0)]

TYPES = {
    # --- UIC-Z 26.4 m built for ČD (Siemens / SGP), EC/IC stock
    "Ampz143": dict(    # Ampz-n2: open 1st class, 10 wide windows
        L=26.4, win=[(1.8, 2.5, "f")] + row(5.0, 9, 1.9, 1.3) + [(23.9, 24.6, "f")],
        doors=E26, door="plug", first="all", roofp="z", ac=[(9.5, 11.5), (15.0, 17.0)]),
    "Ampz146": dict(    # SGP 1998: same saloon, windows split by a mullion, grey skirt
        L=26.4, win=[(1.8, 2.5, "f")] + row(5.0, 9, 1.9, 1.3, "m") + [(23.9, 24.6, "f")],
        doors=E26, door="plug", first="all", roofp="z", ac=[(12.2, 14.2)], skirt="grey"),
    "Bmz241": dict(     # Bmz-n2: 11 compartments, 1.9 m pitch
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.9, 1.1) + [(23.9, 24.6, "f")],
        doors=E26, door="plug", roofp="z", ac=[(9.5, 11.5), (15.0, 17.0)]),
    "Bmz245": dict(     # SGP 1999 twin of 241, grey skirt, single roof unit
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.9, 1.1) + [(23.9, 24.6, "f")],
        doors=E26, door="plug", roofp="z", ac=[(12.2, 14.2)], skirt="grey"),
    "WRmz815": dict(    # WRmz-n2: restaurant, kitchen end with small windows
        L=26.9, win=row(2.6, 2, 1.2, 0.6, "f") + row(5.6, 3, 1.9, 1.3) + row(12.8, 5, 2.2, 1.6),
        doors=[(0.5, 1.5)], door="plug", inv=True, roofp="z", ac=[(3.0, 5.0), (15.0, 17.0)],
        word="restaurant"),
    "WLABmz826": dict(  # WLABmz-n2: sleeper, 12 compartments, small high windows
        L=26.4, win=row(3.6, 12, 1.7, 0.9) + [(24.0, 24.6, "f")],
        doors=[(0.5, 1.5), (24.9, 25.9)], door="plug", inv=True, roofp="z",
        ac=[(4.0, 6.0), (20.0, 22.0)], word="sleeper", band=(2.25, 3.10)),
    # --- ex-ÖBB UIC-Z 26.4 m (Eurofima / Z1 family); same body, the frames differ
    "Bmz226": dict(     # no drawing; the 61 54 / 61 81 cars as Bmz 235, blue frames
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1) + [(23.8, 24.5, "f")],
        doors=E26, door="fold", roofp="z", frame="b", ac=[(12.2, 14.2)]),
    "Bmz232": dict(     # Bmz232-n2-cr: black frames
        L=26.4, win=[(1.8, 2.7, "f")] + row(3.1, 11, 1.89, 1.3) + [(23.7, 24.6, "f")],
        doors=[(0.6, 1.4), (25.0, 25.8)], door="plug", roofp="z", frame="k",
        ac=[(12.2, 14.2)]),
    "Bmz234": dict(     # Bmz234-n2-br: no AC, drop-light windows, white frames
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1, "t") + [(23.8, 24.5, "f")],
        doors=E26, door="fold", roofp="z", frame="w", vents=True),
    "Bmz235": dict(     # Bmz235-n2-br: white frames
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1) + [(23.8, 24.5, "f")],
        doors=E26, door="fold", roofp="z", frame="w", ac=[(12.2, 14.2)]),
    "Bmz229": dict(     # Bmz229-n2-br: kids' cinema compartment, painted panel
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1) + [(23.8, 24.5, "f")],
        doors=E26, door="fold", roofp="z", frame="w", ac=[(12.2, 14.2)],
        picto=[(10.0, 11.4, "kids")]),
    "Bmz224": dict(     # DPOV 2019 rebuild: plug doors, blue frames, grey skirt
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1) + [(23.8, 24.5, "f")],
        doors=E26, door="plug", roofp="z", frame="b", ac=[(9.5, 11.5), (15.0, 17.0)],
        skirt="grey"),
    "Bdmz223": dict(    # Pars nova 2019: 10 compartments + bike area at one end
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 10, 1.89, 1.1) + [(22.1, 24.5, "w")],
        doors=E26, door="plug", roofp="z", frame="b", ac=[(9.5, 11.5)],
        picto=[(22.3, 23.1, "bike")]),
    "Bdmpz227": dict(   # Pars nova 2015: open saloon, wide windows, bike area
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.3, 8, 2.3, 1.5) + [(22.0, 24.5, "w")],
        doors=E26, door="plug", roofp="z", ac=[(9.5, 11.5), (15.0, 17.0)],
        picto=[(22.3, 23.1, "bike")]),
    "Bhmpz228": dict(   # Pars nova 2015: compartments + saloon, wide lift door
        L=26.4, win=[(1.9, 2.6, "f")] + row(3.2, 6, 1.89, 1.1) + [(16.0, 17.5, "w"),
                                                              (20.4, 21.9, "w"), (22.4, 23.5, "w")],
        doors=[(0.5, 1.5), (14.3, 15.6), (24.9, 25.9)], door="plug", lift=1, roofp="z",
        ac=[(9.5, 11.5), (17.5, 19.5)]),
    "ABmz346": dict(    # ABmz346-n2-mr: 6 2nd-class + 4 wide 1st-class compartments
        L=26.4, win=[(1.8, 2.7, "f")] + row(3.2, 6, 1.9, 1.1) + row(14.8, 4, 2.3, 1.3) + [(23.7, 24.6, "f")],
        doors=E26, door="fold", first=[(14.3, 24.9)], roofp="z", frame="b", ac=[(12.2, 14.2)]),
    "Amz138": dict(     # SGP 1989-93 1st class compartments, 9 wide windows
        L=26.4, win=[(2.0, 2.7, "f")] + row(3.5, 9, 2.3, 1.3) + [(23.8, 24.5, "f")],
        doors=E26, door="plug", first="all", roofp="z", frame="k", ac=[(12.2, 14.2)]),
    "WRmz817": dict(    # WRmz817-n2: restaurant, kitchen windows then 6 wide
        L=26.9, win=row(2.4, 2, 1.3, 0.8, "f") + [(7.0, 7.8, "f")] + row(8.8, 6, 2.3, 1.6),
        doors=[(0.5, 1.5), (25.2, 26.2)], door="plug", inv=True, roofp="z",
        ac=[(3.0, 5.0), (15.0, 17.0)], word="restaurant"),
    "Bcmz834": dict(    # Bcmz834-n2-br: couchette, 10 compartments, white frames
        L=26.4, win=[(1.8, 2.6, "f")] + row(3.8, 10, 2.0, 1.3) + [(23.8, 24.6, "f")],
        doors=E26, door="fold", inv=True, roofp="z", frame="w", ac=[(12.2, 14.2)],
        word="sleeper"),
    # --- ex-DR Bautzen UIC-Z/X 26.4 m, rebuilt
    "Bbdgmee236": dict(  # Bbdgmsee236: 7 compartments, lift door, bike saloon
        L=26.4, win=row(1.8, 7, 1.87, 1.1) + [(19.7, 20.3, "f"), (21.3, 22.4, "w"), (23.0, 24.1, "w")],
        doors=[(0.5, 1.5), (18.1, 19.4), (24.9, 25.9)], door="plug", lift=1, roofp="z",
        ac=[(9.5, 11.5)], picto=[(15.0, 17.2, "bike")]),
    "Bdmpee233": dict(   # Bdmpee233-n2: open saloon, 10 windows with drop-light tops
        L=26.4, win=[(3.8, 4.3, "f")] + row(5.1, 9, 1.9, 1.1) + [(22.2, 22.7, "f")],
        doors=E26, door="plug", roofp="z", ac=[(9.5, 11.5), (15.0, 17.0)],
        picto=[(2.4, 3.2, "bike")]),
    "ARmpee829": dict(   # 1st class (22 seats) + bistro, inverted colours
        L=26.4, win=[(1.9, 2.5, "f")] + row(3.2, 4, 1.9, 1.2) + row(11.8, 5, 2.2, 1.5) + [(23.9, 24.5, "f")],
        doors=E26, door="plug", inv=True, first=[(0.5, 10.8)], roofp="z",
        ac=[(4.0, 6.0), (15.0, 17.0)], word="bistro"),
    "ARmpee832": dict(   # ex-BRcm: 1st class + bistro, wide windows in the bistro
        L=26.4, win=[(1.9, 2.5, "f")] + row(3.2, 5, 1.9, 1.2) + [(13.3, 15.8, "w"), (16.6, 19.1, "w"),
                                                               (19.9, 22.4, "w")],
        doors=E26, door="plug", inv=True, first=[(0.5, 12.6)], roofp="z",
        ac=[(4.0, 6.0), (15.0, 17.0)], word="bistro"),
    "WLABmee823": dict(  # WLABmee-n2: sleeper, 10 compartments
        L=26.4, win=[(2.8, 3.5, "f")] + row(4.9, 10, 1.9, 1.0) + [(24.1, 24.6, "f")],
        doors=[(0.5, 1.5), (24.9, 25.9)], door="plug", inv=True, roofp="z",
        ac=[(4.0, 6.0), (20.0, 22.0)], word="sleeper", band=(2.25, 3.10)),
    # --- honecker UIC-X 26.4 m (Bautzen 1989-90), doors at 1/4 and 3/4
    "Bdmtee281": dict(   # Bdmtee-n2: 2 bike areas, no AC
        L=26.4, win=row(0.7, 3, 1.5, 1.1, "t") + [(5.4, 6.1, "t")] + row(8.9, 6, 1.5, 1.1, "t")
        + [(20.4, 20.9, "f")] + row(21.6, 3, 1.5, 1.1, "t"),
        doors=[(6.4, 8.5), (17.9, 20.0)], door="dbl", roofp="x", vents=True,
        picto=[(3.7, 4.8, "bike"), (21.6, 22.7, "bike")]),
    "Bdmtee275": dict(   # one bike area rebuilt into a service compartment
        L=26.4, win=row(0.7, 3, 1.5, 1.1, "t") + [(5.4, 6.1, "t")] + row(8.9, 6, 1.5, 1.1, "t")
        + [(20.4, 20.9, "f"), (21.6, 22.7, "f")] + row(23.1, 2, 1.5, 1.1, "t"),
        doors=[(6.4, 8.5), (17.9, 20.0)], door="dbl", roofp="x", vents=True,
        picto=[(3.7, 4.8, "bike")]),
    "Bdmtee267": dict(   # refurbished 263/265-268: fixed windows, AC units
        L=26.4, win=row(0.7, 3, 1.5, 1.1) + [(5.4, 6.1, "w")] + row(8.9, 6, 1.5, 1.1)
        + [(20.4, 20.9, "f")] + row(21.6, 3, 1.5, 1.1),
        doors=[(6.4, 8.5), (17.9, 20.0)], door="dbl", roofp="x", ac=[(3.0, 5.0), (21.4, 23.4)],
        picto=[(3.7, 4.8, "bike")]),
    # --- ex-Hungarian UIC-Y 24.5 m (Dunakeszi rebuilds), AC
    "Aee140": dict(      # Aee140: 9 1st-class compartments
        L=24.5, win=[(1.8, 2.4, "f")] + row(3.3, 9, 2.1, 1.3) + [(22.1, 22.7, "f")],
        doors=E24P, door="plug", first="all", roofp="y", ac=[(10.0, 12.0)]),
    "Apee139": dict(     # Apee139-n2: open 1st class, 10 windows
        L=24.5, win=[(1.8, 2.6, "f")] + row(3.1, 10, 1.9, 1.3) + [(21.9, 22.7, "f")],
        doors=E24P, door="plug", first="all", roofp="y", ac=[(7.0, 9.0), (14.5, 16.5)]),
    "Bee238": dict(      # Bee238: 10 compartments
        L=24.5, win=[(1.7, 2.5, "f")] + row(3.1, 10, 1.9, 1.3) + [(22.0, 22.8, "f")],
        doors=E24P, door="plug", roofp="y", ac=[(10.0, 12.0)]),
    "Bpee237": dict(     # Bpee237: open saloon, the same openings, two roof units
        L=24.5, win=[(1.7, 2.5, "f")] + row(3.1, 10, 1.9, 1.3, "m") + [(22.0, 22.8, "f")],
        doors=E24P, door="plug", roofp="y", ac=[(7.0, 9.0), (14.5, 16.5)]),
    # --- Bautzen Y/B 70 UIC-Y 24.5 m
    "Aee145": dict(      # Aee152-n2: 9 1st-class compartments, mullioned windows
        L=24.5, win=[(1.8, 2.6, "f")] + row(3.3, 9, 2.07, 1.1, "m") + [(21.9, 22.7, "f")],
        doors=E24, door="fold", first="all", roofp="y", ac=[(10.0, 12.0)]),
    "AB349": dict(       # AB-n2: 4 1st + 5 2nd compartments, yellow over the 1st half
        L=24.5, win=[(1.9, 2.5, "f")] + row(3.2, 9, 2.1, 1.3, "t") + [(22.0, 22.6, "f")],
        doors=E24, door="fold", first=[(11.1, 23.1)], roofp="y", vents=True),
    "Bee272": dict(      # Bee272-n2: 22-seat saloon + 6 compartments
        L=24.5, win=[(1.9, 2.5, "f")] + row(3.2, 4, 1.9, 1.1) + row(10.8, 6, 1.9, 1.1, "m") + [(22.0, 22.6, "f")],
        doors=E24, door="fold", roofp="y", ac=[(10.0, 12.0)]),
    "Bee273": dict(      # Bee273-n2: compartments of varied size, 10 windows
        L=24.5, win=[(1.8, 2.6, "f")] + row(3.1, 10, 1.9, 1.3) + [(21.9, 22.7, "f")],
        doors=E24, door="fold", roofp="y", ac=[(10.0, 12.0)]),
    "Bd264": dict(       # Bd264-n2: compartments + bike room at one end (no AC)
        L=24.5, win=[(1.9, 2.5, "f")] + row(3.2, 9, 1.87, 1.3, "t") + [(20.3, 21.2, "w"), (21.9, 22.7, "w")],
        doors=E24, door="fold", roofp="y", vents=True, picto=[(20.3, 21.2, "bike")]),
    "BDs449": dict(      # BDs-n2: 5 compartments + luggage room with double door
        L=24.5, win=[(1.9, 2.5, "f")] + row(3.2, 5, 1.9, 1.3, "t") + [(12.9, 13.7, "w"),
                                                                  (18.8, 20.2, "w"), (21.9, 22.5, "f")],
        doors=[(0.5, 1.4), (15.2, 17.3), (23.1, 24.0)], door="fold", roofp="y", vents=True,
        picto=[(18.8, 20.2, "bike")]),
    # --- Vagónka Studénka UIC-Y 24.5 m
    "Bdpee231": dict(    # Bdpee231-n2: big undivided saloon windows (ex Bp 282)
        L=24.5, win=[(2.0, 2.5, "f")] + row(3.2, 10, 1.7, 1.1, "p") + [(20.2, 20.7, "f")],
        doors=E24P, door="plug", roofp="y", ac=[(7.0, 9.0), (14.5, 16.5)],
        picto=[(21.2, 22.4, "bike")]),
    "ABpee347": dict(    # ABpee347: open 1st + 2nd saloons, yellow over the 1st half
        L=24.5, win=[(1.8, 2.4, "f")] + row(3.1, 5, 1.7, 1.3, "p") + [(11.8, 12.9, "f")]
        + row(13.3, 5, 1.7, 1.3, "p"),
        doors=[(0.5, 1.6), (22.9, 24.0)], door="plug", first=[(0.5, 11.8)], roofp="y",
        ac=[(7.0, 9.0), (14.5, 16.5)]),
    "Bdtee276": dict(    # Bdtee276: open saloon, 12 narrow windows, sliding plug doors
        L=24.5, win=[(2.0, 2.5, "f")] + row(3.1, 11, 1.7, 1.3) + [(21.9, 22.6, "f")],
        doors=E24P, door="plug", roofp="y", ac=[(10.0, 12.0)], picto=[(3.1, 4.4, "bike")]),
    "Bdt279": dict(      # Bdt279: open saloon, 12 drop-light windows, no AC
        L=24.5, win=[(1.9, 2.6, "f")] + row(3.1, 11, 1.7, 1.3, "t") + [(22.0, 22.5, "f")],
        doors=E24, door="fold", roofp="y", vents=True, picto=[(20.1, 21.4, "bike")]),
    "Bdt280": dict(      # Bdt-n2: the same body, without the bike pictogram
        L=24.5, win=[(1.9, 2.6, "f")] + row(3.1, 11, 1.7, 1.3, "t") + [(22.0, 22.5, "f")],
        doors=E24, door="fold", roofp="y", vents=True),
    # --- driving trailers (sysel): openings listed with the cab at 0 m
    "Bfhpvee295": dict(  # Bfhpvee295-n2: cab, bike/PRM area, double door, saloon
        L=24.5, cab=True, win=[(0.9, 1.4, "w"), (1.8, 2.2, "w"), (4.1, 5.2, "w")] + row(9.5, 7, 1.8, 1.1)
        + [(22.0, 22.5, "f")],
        doors=[(7.1, 8.8), (23.0, 24.0)], door="dbl", roofp="y", ac=[(12.0, 14.0)],
        picto=[(4.1, 5.2, "bike")]),
    "ABfhpvee395": dict(  # the same body with 1st class next to the cab
        L=24.5, cab=True, win=[(0.9, 1.4, "w"), (1.8, 2.2, "w"), (4.1, 5.2, "w")] + row(9.5, 7, 1.8, 1.1)
        + [(22.0, 22.5, "f")],
        doors=[(7.1, 8.8), (23.0, 24.0)], door="dbl", first=[(9.0, 16.2)], roofp="y", ac=[(12.0, 14.0)]),
    # --- double-deck (dd): Görlitz DDm and Škoda 13Ev, 26.8 m; openings per deck
    "Bdmteeo294": dict(  # Bmto-n2 / Bdmteeo294: Görlitz, bike area in one end
        L=26.8, dd="gorlitz", up=row(8.5, 6, 1.7, 1.3), low=row(8.5, 6, 1.7, 1.3),
        endwin=[(2.3, 3.6), (21.6, 22.9), (23.4, 24.1)], doors=[(6.4, 8.1), (19.8, 21.5)],
        picto=[(2.3, 3.6, "bike")]),
    "Bdmteeo296": dict(  # the same Görlitz body without the bike area
        L=26.8, dd="gorlitz", up=row(8.5, 6, 1.7, 1.3), low=row(8.5, 6, 1.7, 1.3),
        endwin=[(2.3, 3.6), (21.6, 22.9), (23.4, 24.1)], doors=[(6.4, 8.1), (19.8, 21.5)]),
    "ABfbdmteeo396": dict(  # Škoda 13Ev cab car: 1st class upstairs next to the cab
        L=26.8, dd="13ev", cab=True, up=row(7.6, 8, 1.75, 1.3), low=row(7.6, 7, 1.75, 1.3),
        endwin=[(3.4, 4.6), (23.0, 24.2)], doors=[(5.6, 7.1), (20.3, 21.8)],
        first=[(7.3, 14.6)], picto=[(8.0, 10.0, "wheel")]),
    "Bdmteeo297": dict(  # 13Ev middle car, 2nd class
        L=26.8, dd="13ev", up=row(3.0, 12, 1.75, 1.3), low=row(7.6, 7, 1.75, 1.3),
        endwin=[(2.4, 3.6), (23.2, 24.4)], doors=[(5.6, 7.1), (20.3, 21.8)]),
    "Bdmteeo298": dict(  # 13Ev middle car with the multi-purpose (bike) space
        L=26.8, dd="13ev", up=row(3.0, 12, 1.75, 1.3), low=row(7.6, 3, 1.75, 1.3) + [(15.2, 19.8)],
        endwin=[(2.4, 3.6), (23.2, 24.4)], doors=[(5.6, 7.1), (20.3, 21.8)],
        picto=[(15.6, 17.0, "bike")]),
}

# class words on the lower body (restaurant / sleeper), as seen: from, to, colour
WORDS = {
    "restaurant": (3.0, 9.0),
    "bistro": (13.0, 18.0),
    "sleeper": (3.0, 9.5),
}

# ------------------------------------------------------------------ colours
# Najbrt (tools/railpaint/palette.py values, RAL anchored)
SAPPHIRE = (30, 52, 94)
SKY = (38, 120, 192)
LGREY = (206, 211, 209)
LOWER = (230, 234, 233)    # RAL 7035 lifted: the natives' lower body reads near-white in the sun
UMBRA = (104, 106, 100)
N2_STRIPE = (214, 220, 224)
YELLOW = (242, 194, 0)
SKIRT = (34, 40, 58)
SKIRT_GREY = (86, 90, 96)
UNDER = (0x2A, 0x2C, 0x2E)
BOGIE = (0x23, 0x24, 0x26)
BOGIE_FRAME = (0x3C, 0x3F, 0x42)
FROST = (0x9A, 0xA4, 0xAA)
NUM = (0xF2, 0xF2, 0xF2)
WHEEL_BLUE = (0x1F, 0x5F, 0xB0)
FRAMES = {"w": (0xE4, 0xE7, 0xE7), "k": (0x34, 0x36, 0x3A), "b": (0x18, 0x5E, 0xB0)}
# ÖBB "valousek" grey/red as still worn by four Bmz 232
OBB_RED = (0xC8, 0x10, 0x18)
OBB_GREY = (0xCF, 0xD1, 0xD1)
OBB_BAND = (0x9C, 0xA0, 0xA2)
OBB_SKIRT = (0x70, 0x72, 0x74)
ROOFS = {
    "n2": Paint((34, 56, 110), top=(38, 62, 146)),
    "n1": Paint(UMBRA, top=(116, 118, 112)),
    "red": Paint((0x9C, 0x1C, 0x20), top=(0xA8, 0x23, 0x27)),
}

EDGE = {"z": 3.34, "y": 3.30, "x": 3.38}     # where the roof colour starts on the side, m


def palette(liv, S):
    """Colour zones for livery `liv` on type spec S."""
    roof = S.get("roof")
    n1 = liv in ("najbrt1", "najbrtbd1")
    if liv == "obb":
        return dict(lower=OBB_GREY, under=OBB_RED, band=OBB_BAND, stripe=OBB_GREY,
                    roof=ROOFS["red"], door=OBB_BAND, skirt=OBB_SKIRT, obb=True)
    C = dict(lower=LOWER, under=SAPPHIRE, band=SKY, stripe=SKY if n1 else N2_STRIPE,
             roof=ROOFS["n1" if n1 else "n2"], door=SAPPHIRE,
             skirt=SKIRT_GREY if S.get("skirt") == "grey" else SKIRT)
    if roof == "red" and not n1:
        C["roof"] = ROOFS["red"]
    if S.get("inv"):                         # restaurant / sleeper / couchette
        C.update(under=SKY, band=SAPPHIRE)
    if liv.startswith("najbrtbd"):           # BD: blue lower body as well
        C.update(lower=SKY)
    return C


def in_first(S, m):
    f = S.get("first")
    if f == "all":
        return True
    return bool(f) and any(a <= m <= b for (a, b) in f)


# ------------------------------------------------------------------ model
def coach(code, liv, u0=0.0, owner="C", cab=None):
    """Parts of ČD coach `code` (see TYPES) whose front buffer face is at consist-u u0.
    Driving trailers (`cab` in the type) take cab="front" (cab leading, the
    locomotive pushes) or cab="rear" (cab at the tail of a hauled train)."""
    S = TYPES[code]
    if S.get("dd"):
        return dd(code, liv, u0, owner, cab)
    flip = S.get("cab") and cab == "rear"
    Lm = S["L"]
    L = 12.0 if Lm < 25.5 else 13.0
    M = Lm / L
    C = palette(liv, S)
    obb = C.get("obb", False)
    doors = S["doors"]
    b0, b1 = S.get("band", (2.00, 3.10))     # window band, m above rail
    g0, g1 = b0 + 0.10, b1 - 0.10            # glass inside the band
    edge = EDGE[S["roofp"]]
    frame = FRAMES.get(S.get("frame")) if not obb else None
    wins = S["win"]
    # class numerals in the gaps next to the first and last windows
    nums = []
    if len(wins) > 3:
        for (a, b) in ((wins[0][1], wins[1][0]), (wins[-2][1], wins[-1][0])):
            if b - a >= 0.35:
                c = (a + b) / 2
                nums.append((c - 0.13, c + 0.13))
    P = {k: Paint(v) for k, v in C.items() if isinstance(v, tuple)}
    roofp = C["roof"]

    def side(f, u, v, z, d):
        m = (u - u0) * M                     # physical metres from the front
        lm = m if f == "-v" else Lm - m      # metres as seen, left to right
        if flip:                             # openings are listed cab first
            m = Lm - m
        h = z * PX
        # doors
        for i, (a, b) in enumerate(doors):
            if a <= m <= b and 0.50 <= h <= edge - 0.02:
                if S.get("lift") == i and 1.3 <= h <= 1.75 and a + 0.35 <= m <= b - 0.35:
                    return Paint(WHEEL_BLUE)
                mid = (a + b) / 2
                if S["door"] == "dbl":
                    if abs(m - mid) < 0.06:
                        return Paint(UNDER)
                    if 2.0 <= h <= 2.9 and (a + 0.2 <= m <= mid - 0.2 or mid + 0.2 <= m <= b - 0.2):
                        return R.GLASS
                    return P["door"]
                if 2.05 <= h <= 2.95 and a + 0.25 <= m <= b - 0.25:
                    return R.GLASS
                if S["door"] == "fold" and abs(m - mid) < 0.07:
                    return Paint(UNDER)
                return P["door"]
        # roof curve
        if h >= edge:
            return roofp
        # stripe above the window band: yellow over 1st class
        if h > b1:
            if in_first(S, m) and h >= b1 + 0.03:
                return Paint(YELLOW)
            if obb:
                return P["stripe"]
            return P["stripe"] if h >= b1 + 0.05 else P["band"]
        # window band
        if h >= b0:
            for (a, b, k) in wins:
                if a <= m <= b and b0 + 0.04 <= h <= b1 - 0.04:
                    inner = a + 0.08 <= m <= b - 0.08 and g0 <= h <= g1
                    if not inner:
                        return Paint(frame) if frame else Paint(UNDER)
                    if k == "f":
                        return Paint(FROST)
                    if k == "m" and abs(m - (a + b) / 2) < 0.08:
                        return Paint(frame) if frame else P["band"]
                    if k == "t" and abs(h - (g1 - 0.28)) < 0.06:
                        return Paint(frame) if frame else P["band"]
                    return R.GLASS_HI if h > g1 - 0.22 else R.GLASS
            for (a, b) in nums:
                if a <= m <= b and 2.35 <= h <= 2.75:
                    return Paint(NUM)
            for (a, b, kind) in S.get("picto", []):
                if a <= lm <= b and 2.30 <= h <= 2.85:
                    if kind == "kids":
                        return Paint((0xE8, 0xB0, 0x20) if int(lm * 3) % 2 else (0xD0, 0x30, 0x40))
                    if kind == "bike":
                        return Paint(NUM) if abs(h - 2.55) < 0.12 else P["band"]
            return P["band"]
        # dark stripe under the windows
        if h >= b0 - 0.20:
            return P["under"] if not obb else P["lower"]
        # lower body: ČD logo + lettering, class words
        if not obb and 1.25 <= h <= 1.55:
            if 3.0 <= lm <= 3.5:
                return Paint(SAPPHIRE)
            if S.get("word"):
                a, b = WORDS[S["word"]]
                if a + 1.0 <= lm <= b + 1.0 and int((lm - a) / 0.4) % 3 != 2:
                    return Paint((0x3A, 0x4E, 0x8C))
            elif 3.8 <= lm <= 6.0 and int((lm - 3.8) / 0.35) % 3 != 2:
                return Paint((0x5A, 0x6A, 0x98))
        if obb and 0.95 <= h <= 1.15:
            return Paint(OBB_RED)
        if h < 0.78:
            return P["skirt"]
        return P["lower"]

    def cabface(f, u, v, z, d):
        h = z * PX
        if h >= edge:
            return roofp
        if 2.15 <= h <= 3.05 and 0.10 <= abs(v) <= W - 0.12:
            return R.GLASS
        if 1.05 <= h <= 1.35 and 0.50 <= abs(v) <= 0.75:
            return Lit(R.HEAD if cab == "front" else R.TAIL)
        if h < 0.78:
            return P["skirt"]
        if h < b0 - 0.2:
            return P["lower"] if abs(v) > 0.3 else P["band"]
        return P["band"]

    def end(f, u, v, z, d):
        h = z * PX
        if S.get("cab") and f == ("+u" if flip else "-u"):
            return cabface(f, u, v, z, d)
        if abs(v) < 0.42 and h < 3.4:
            return Paint((0x2B, 0x2D, 0x2F))   # gangway door / bellows
        if h >= edge:
            return roofp
        if b0 <= h <= b1:
            return P["band"]
        if h < 0.95:
            return P["skirt"]
        return P["lower"]

    def body_mat(f, u, v, z, d):
        if f == "+z":
            return roofp
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        return end(f, u, v, z, d)

    parts = []
    ub0, ub1 = u0 + 0.14, u0 + L - 0.14
    if S.get("cab"):                         # sysel: bulging cab end, no gangway
        if flip:
            ub1 = u0 + L - 0.05
        else:
            ub0 = u0 + 0.05
    parts.append(Part(ub0, ub1, -W, W, ZB, ZS, body_mat, owner))
    if S["roofp"] == "y":                    # UIC-Y: roof ends slope down
        parts.append(Part(ub0 + 0.35, ub1 - 0.35, -W + 0.2, W - 0.2, ZS, ZR, lambda *a: roofp, owner))
    elif S["roofp"] == "x":                  # honecker: rounded, narrower crown
        parts.append(Part(ub0 + 0.15, ub1 - 0.15, -W + 0.28, W - 0.28, ZS, ZR, lambda *a: roofp, owner))
    else:
        parts.append(Part(ub0 + 0.05, ub1 - 0.05, -W + 0.2, W - 0.2, ZS, ZR, lambda *a: roofp, owner))
    # roof equipment: AC units (light grey boxes) or small ventilators
    ac_paint = Paint((0x8C, 0x92, 0x96), top=(0xA4, 0xAA, 0xAE))
    for (a, b) in S.get("ac", []):
        parts.append(Part(u0 + a / M, u0 + b / M, -0.45, 0.45, ZR, ZR + 0.7, lambda *a_: ac_paint, owner))
    if S.get("vents"):
        vp = Paint((0x3A, 0x3E, 0x44), top=(0x4A, 0x4E, 0x54))
        for i in range(5):
            uc = u0 + (2.0 + i * (L - 4.0) / 4)
            parts.append(Part(uc - 0.18, uc + 0.18, -0.2, 0.2, ZR, ZR + 0.45, lambda *a_: vp, owner))
    # gangways + buffers
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        if b - a < 0.05:
            continue
        parts.append(Part(a, b, -0.40, 0.40, 2.6, ZS - 0.8, lambda *a_: Paint((0x2B, 0x2D, 0x2F)), owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *a_: Paint((0x1E, 0x20, 0x22)), owner))
    # underframe equipment + bogies
    parts.append(Part(u0 + 3.3, u0 + L - 3.3, -W + 0.25, W - 0.25, 0.0, ZB, lambda *a_: Paint(UNDER), owner))
    bc = 2.5 if Lm < 25.5 else 3.7
    for bm in (bc, Lm - bc):
        c = u0 + bm / M
        parts.append(Part(c - 0.72, c + 0.72, -W + 0.12, W - 0.12, 0.0, ZB,
                          lambda f, u, v, z, d: Paint(BOGIE_FRAME) if (f in ("+v", "-v") and z > 1.0)
                          else Paint(BOGIE), owner))
    return parts


# ------------------------------------------------------------------ double-deck
ZDS = 4.40 / PX            # dd side wall top (4.40 m)
ZDR = 4.63 / PX            # dd roof crown
EV_DOOR = (38, 40, 41)


def dd(code, liv, u0=0.0, owner="C", cab=None):
    """Double-deck car: dropped floor between the bogies, two window rows.
    Görlitz (vagonWEB Bmto-n2): navy upper band with the upper-deck windows, a
    light line, sky-blue band (windows of the end sections), navy line, light
    grey lower deck. Škoda 13Ev: sky-blue upper deck, light grey lower deck,
    dark-blue roof and skirt, dark plug double doors."""
    S = TYPES[code]
    Lm = S["L"]
    L = 13.0
    M = Lm / L
    flip = S.get("cab") and cab == "rear"
    ev = S["dd"] == "13ev"
    e0, e1 = 4.6, Lm - 4.6               # low-floor section between the bogies
    P = dict(roof=ROOFS["n2"], navy=Paint(SAPPHIRE), sky=Paint(SKY), lower=Paint(LOWER),
             stripe=Paint(N2_STRIPE), skirt=Paint(SKIRT), door=Paint(SAPPHIRE))

    def win_at(spans, m, h, lo, hi):
        for sp in spans:
            a, b = sp[0], sp[1]
            if a <= m <= b and lo <= h <= hi:
                if a + 0.08 <= m <= b - 0.08 and lo + 0.07 <= h <= hi - 0.07:
                    return R.GLASS_HI if h > hi - 0.2 else R.GLASS
                return Paint(UNDER)
        return None

    def side(f, u, v, z, d):
        m = (u - u0) * M
        lm = m if f == "-v" else Lm - m
        if flip:
            m = Lm - m
        h = z * PX
        mid = e0 <= m <= e1
        for (a, b) in S["doors"]:
            if a <= m <= b and 0.35 <= h <= 2.95:
                if abs(m - (a + b) / 2) < 0.06:
                    return Paint(UNDER)
                if 1.2 <= h <= 2.6 and a + 0.18 <= m <= b - 0.18:
                    return R.GLASS
                return Paint(EV_DOOR) if ev else P["door"]
        if h >= 4.05:
            return P["roof"]
        for (a, b, kind) in S.get("picto", []):
            if a <= lm <= b and (1.2 <= h <= 1.6 if mid else 2.2 <= h <= 2.6):
                return Paint(WHEEL_BLUE) if kind == "wheel" else Paint(NUM)
        if ev:
            # 13Ev: sky-blue upper deck (windows 3.0-3.85), light grey lower deck
            if h >= 2.85:
                if in_first(S, m) and 3.92 <= h:
                    return Paint(YELLOW)
                return win_at(S["up"], m, h, 3.0, 3.85) or P["sky"]
            if h >= 2.70:
                return P["navy"]
            w = win_at(S["low"], m, h, 1.0, 1.95) if mid else win_at(S["endwin"], m, h, 1.9, 2.65)
            if w:
                return w
            return P["navy"] if h < 0.75 else P["lower"]
        # Görlitz
        if h >= 3.10:
            if in_first(S, m) and 3.95 <= h:
                return Paint(YELLOW)
            return (win_at(S["up"], m, h, 3.2, 3.85) if mid else None) or P["navy"]
        if h >= 3.0:
            return P["stripe"]
        if h >= 1.9 and not mid:
            w = win_at(S["endwin"], m, h, 2.0, 2.75)
            if w:
                return w
        if h >= 2.1:
            return P["sky"]
        if h >= 1.9:
            return P["navy"]
        w = win_at(S["low"], m, h, 0.9, 1.75) if mid else None
        if w:
            return w
        return P["skirt"] if h < 0.55 else P["lower"]

    def cabface(f, u, v, z, d):
        h = z * PX
        if h >= 4.05:
            return P["roof"]
        if 2.3 <= h <= 3.3 and abs(v) <= W - 0.1:
            return R.GLASS
        if 1.2 <= h <= 1.5 and 0.45 <= abs(v) <= 0.75:
            return Lit(R.HEAD if cab == "front" else R.TAIL)
        if h < 0.9:
            return P["navy"]
        return Paint((0xE8, 0xEC, 0xEE)) if 1.6 <= h <= 2.2 else P["sky"]

    def end(f, u, v, z, d):
        h = z * PX
        if S.get("cab") and f == ("+u" if flip else "-u"):
            return cabface(f, u, v, z, d)
        if abs(v) < 0.42 and 1.0 <= h < 3.0:
            return Paint((0x2B, 0x2D, 0x2F))
        if h >= 4.05:
            return P["roof"]
        return P["sky"] if h >= 2.1 else P["lower"]

    def mat(f, u, v, z, d):
        if f == "+z":
            return P["roof"]
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        return end(f, u, v, z, d)

    parts = []
    ub0, ub1 = u0 + 0.14, u0 + L - 0.14
    if S.get("cab"):
        if flip:
            ub1 = u0 + L - 0.05
        else:
            ub0 = u0 + 0.05
    um0, um1 = u0 + e0 / M, u0 + e1 / M
    zlow = 0.35 / PX
    parts.append(Part(ub0, um0, -W, W, ZB, ZDS, mat, owner))
    parts.append(Part(um0, um1, -W, W, zlow, ZDS, mat, owner))
    parts.append(Part(um1, ub1, -W, W, ZB, ZDS, mat, owner))
    parts.append(Part(ub0 + 0.1, ub1 - 0.1, -W + 0.22, W - 0.22, ZDS, ZDR, lambda *a: P["roof"], owner))
    if ev:
        acp = Paint((0x8C, 0x92, 0x96), top=(0xA4, 0xAA, 0xAE))
        for (a, b) in ((2.0, 4.0), (22.8, 24.8)):
            parts.append(Part(u0 + a / M, u0 + b / M, -0.45, 0.45, ZDR, ZDR + 0.6, lambda *a_: acp, owner))
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        if b - a < 0.05:
            continue
        parts.append(Part(a, b, -0.40, 0.40, 2.6, ZS - 0.8, lambda *a_: Paint((0x2B, 0x2D, 0x2F)), owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *a_: Paint((0x1E, 0x20, 0x22)), owner))
    for bm in (2.4, Lm - 2.4):
        c = u0 + bm / M
        parts.append(Part(c - 0.72, c + 0.72, -W + 0.12, W - 0.12, 0.0, ZB,
                          lambda f, u, v, z, d: Paint(BOGIE_FRAME) if (f in ("+v", "-v") and z > 1.0)
                          else Paint(BOGIE), owner))
    return parts


def length(code):
    return 12 if TYPES[code]["L"] < 25.5 else 13


def tiles(code, liv, cab=None):
    parts = coach(code, liv, cab=cab)
    return [R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS]
