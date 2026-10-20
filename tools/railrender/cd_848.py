#!/usr/bin/env python3
"""ČD class 848 (Stadler GTW 2/6, ex-DB 646) in Najbrt 2 with the Olomoucký kraj
decals: the GTW box model of gtw.py (geometry untouched, shared with the Arriva
848s, so both operators' units have one silhouette) with the ČD livery. The
owner picked this render over the repainted ZSSK 840 drawing on 2026-10-20.

    python tools/railrender/cd_848.py                  # writes the ČD 848 sheet
    python tools/railrender/cd_848.py --preview DIR    # also a 4x preview

Livery najbrt2 (photos of 848.015 / 016, Arciol24 on Wikimedia Commons, 2025):
sapphire roof, a white stripe under the roof edge, the sky-blue band over the
flush black window band, a thin sapphire stripe, white lower body, sapphire
doors; a sky surround round the cab side window; the power module keeps the
bands with a dark engine-room panel. Front: sapphire cap, sky windscreen
surround and lamp panel with the white ČD logo, sapphire stripe, white cheeks,
black skirt with the yellow edge. On the white lower body the dark-blue
"Jedeme v tom spolu…" slogan and the OLKRAJ.CZ flower behind the cab.

The sky band takes the top of the window band (2.51 m up) so it reads as one
full pixel row at 1×, as on the photos. gtw.py's livery table and classes are
not modified: this module adds the livery and subclasses EndCar / Module.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
import gtw as G  # noqa: E402

SAPPHIRE = Paint(0x1E345E, top=0x24406E)     # RAL 5003, as tools/railpaint/palette.py
SKY = Paint(0x2678C0)                        # RAL 5015
WHITE = Paint(0xE6E9EA)
BAND = Paint(0x1E2028)                       # flush black glazing band
PANEL = Paint(0x2E3036)                      # power-module engine-room panel
SLOGAN = Paint(0x2C467C)                     # dark-blue decal lettering on the white

Z_WHITE0 = 7.80          # white stripe under the roof edge (2.92-3.20 m)
Z_SKY0 = 6.70            # sky band (2.51-2.92 m); the glazing ends under it
Z_SAPH0 = 2.80           # sapphire stripe under the windows (1.05-1.28 m)
CAB_SKY = 3.70           # sky surround round the cab side window (car-local m)

LIVERY = "najbrt2"
OUT = os.path.join(REPO, "vehicle-rail", "ceske-drahy", "848", "sprites", LIVERY + ".png")


def livery():
    return G.with_roof(dict(
        kind="n2", hiwin=False,
        body=WHITE, roof=SAPPHIRE, roofbox=Paint(0x1E345E, top=0x2C4A7C),
        pillar=BAND, door=SAPPHIRE, doorframe=Paint(0x182A4C), doorsplit=Paint(0x101C34),
        lampband=SKY, hood=SKY, visor=SAPPHIRE, lowfront=WHITE,
        grille=Paint(0x18305A, top=0x223C68), louvre=Paint(0x3A3E46),
        modroof=Paint(0x1E345E, top=0x6A7078), word=WHITE))


class EndCar(G.EndCar):
    def __init__(self, liv, owner, dirn, lamp):
        super().__init__("arrivamodra", owner, dirn, lamp)
        self.C = livery()

    def front(self, m, vl, z):
        av = abs(vl)
        if z < G.Z_PLOUGH:
            return G.YELLOW_EDGE if z < 0.95 else G.PLOUGH
        hw = G.front_hw(z)
        if z < G.Z_LB0:
            if z >= 2.9:
                return SAPPHIRE
            return WHITE if av > 0.55 else G.DARK
        if z < G.Z_LB1:
            if 0.46 <= av <= 0.80 and 3.60 <= z <= 4.30:
                return self.lamp
            if av < 0.22 and 3.70 <= z <= 4.20:
                return WHITE                               # ČD logo
            return SKY
        if z < 9.35:
            if av < hw - 0.22 and 4.70 <= z <= 9.10:
                if 8.35 <= z <= 8.90 and av < 0.45:
                    return G.AMBER                         # LED destination display
                return G.WS_HI if z > 7.7 else G.WS
            return SKY
        return SAPPHIRE

    def side(self, m, z, cs):
        C = self.C
        if m < G.nose_m(z) + 0.42:
            return self.front(m, G.W, z)
        if z > G.ZS:
            if 9.40 <= m <= 10.90 and z < G.ZC1:
                return C["grille"]                         # AC air intake on the roof curve
            return C["roof_hi"] if z > G.ZC1 else C["roof"]
        if G.cabwin(m, z):
            return G.WS_HI if z > 6.5 else G.WS
        a, b = G.DOOR
        if a <= m <= b and G.Z_FLOOR <= z <= G.Z_DOOR1:
            t = (m - a) / (b - a)
            if t < 0.07 or t > 0.93 or z > G.Z_DOOR1 - 0.35:
                return C["doorframe"]
            if 0.47 <= t <= 0.53:
                return C["doorsplit"]
            if (0.15 <= t <= 0.41 or 0.59 <= t <= 0.85) and 2.9 <= z <= 6.6:
                return R.GLASS_HI if z > 6.15 else R.GLASS
            return C["door"]
        if z >= Z_WHITE0:
            return WHITE
        if z >= Z_SKY0:
            return SKY
        if z >= G.Z_WIN0:
            if m < CAB_SKY:
                return SKY                                 # sky surround of the cab
            for (wa, wb) in G.WINDOWS:
                if wa <= m <= wb:
                    return R.GLASS_HI if z > G.Z_WIN1 - 0.5 else R.GLASS
            return BAND
        if z >= Z_SAPH0:
            return SAPPHIRE
        # Olomoucký kraj decals on the white lower body
        if 5.90 <= m <= 6.40 and 1.70 <= z <= 2.30:
            return SAPPHIRE                                # OLKRAJ.CZ flower
        if 9.20 <= m <= 12.40 and 1.80 <= z <= 2.30:
            x = (m - 9.20) / 3.20
            if int(x * 10) % 2 == 0:
                return SLOGAN                              # "Jedeme v tom spolu…"
        return WHITE


class Module(G.Module):
    def __init__(self, liv, owner="M"):
        super().__init__("arrivamodra", owner)
        self.C = livery()

    def side(self, s, z, f):
        C = self.C
        if f == "-v":
            louv, upper = (20.35, 21.05), (17.65, 20.10)
        else:
            louv, upper = (17.61, 18.31), (18.56, 21.01)
        if z > G.ZS:
            if upper[0] <= s <= upper[1] and z < G.ZC1:
                return C["grille"]                         # cooler intakes on the roof curve
            return C["roof_hi"] if z > G.ZC1 else C["roof"]
        if z >= Z_WHITE0:
            return WHITE
        if z >= Z_SKY0:
            return SKY
        if louv[0] <= s <= louv[1] and 2.9 <= z <= 6.9:
            return C["louvre"]
        if z >= G.Z_WIN0:
            return PANEL
        if z >= Z_SAPH0:
            return SAPPHIRE
        return WHITE


def rows():
    """Sheet rows of the unit: front end car, power module, rear end car."""
    A = EndCar(LIVERY, "A", +1, R.HEAD)
    B = EndCar(LIVERY, "B", -1, R.TAIL)
    M = Module(LIVERY)
    parts = A.parts() + M.parts() + B.parts()
    cars = [("A", 0.0), ("M", float(G.LENGTHS[0])), ("B", float(G.LENGTHS[0] + G.LENGTHS[1]))]
    return [[R.vehicle_tile(parts, [], d, uf, {own}) for d in G.DIRS] for (own, uf) in cars]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        os.makedirs(prev, exist_ok=True)
    r = rows()
    R.save_rows(r, OUT)
    if prev:
        R.preview(r, os.path.join(prev, f"848_{LIVERY}.png"), z=4, labels=["848A", "848M", "848B"])
    print("wrote", os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
