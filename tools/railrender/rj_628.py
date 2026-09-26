"""RegioJet UK class 628.2 + 928.2 (ex-DB 628.2 / 928.2 two-car DMU, Duewag /
LHB 1987-88) in the DUK green-yellow livery of RegioJet UK.

Geometry = Arriva's model (db628.py, the same ex-DB 628.2): this script only
adds the RegioJet livery and the RegioJet front logo; db628.py is imported, not
edited.

  row 0  "628"  motor car, cab at its front (outer) end, headlights, leads
  row 1  "928"  driving trailer, cab at its rear (outer) end, tail lights
  each car 22.7 m over buffers -> length 11 cu (like the Arriva 845 / 945)

Livery "dukzelenozluta" (DUK wrap, RegioJet UK, 15 Dec 2019 onwards), from the
Commons photos 628 302 (Usti n. L., 27 Sep 2021), 928 307 (Usti-Uporiny,
12 Sep 2020) and the vagonWEB drawing 628-duk-a:
  - yellow-green body (#8CBF4A lit; vagonWEB #69A826, photos #729B50 in shade),
    a lighter green strip under the grey roof,
  - continuous black-grey window band (vagonWEB #232323, 1.8-3.0 m) with the
    windows in it, white "Doprava Usteckeho kraje" logo on the band behind the
    first door (a few white px),
  - thin anthracite skirt line along the bottom of the side wall,
  - yellow doors (all doors) with black windows,
  - front: anthracite mask with a white outline (roof edge, front corners,
    and a line across above the lower band), black windscreen, yellow lower
    front band (#F2B01A) with the red "|| REGIO" + blue "JET" logo between the
    lamps, the yellow sweeping round the cab corner onto the cab side, dark-grey
    buffer beam and skirt,
  - light-grey roof, engine exhaust on the 628.

Regenerate with `python tools/railrender/rj_628.py [--preview DIR]` (or via the
RegioJet driver). Change the model and regenerate; never paint the PNGs.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")

import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402
import db628 as D                        # noqa: E402
from db628 import zp, PX, M, L_CAR, W, BODY_END, CABDOOR, INNERDOOR, CABWIN  # noqa: E402

LIVERIES = ["dukzelenozluta"]

GREEN = 0x86BC44          # lit yellow-green (photos 628 302/307, sunlit ~#8FBD50)
GREEN_TOP = 0xA4D062      # lighter strip under the roof (vagonWEB 93C064 / 7CB343)
BAND = 0x2A2D30           # window band (vagonWEB #232323, photos #2B3035)
YELLOW = 0xF4B11A         # doors, lower front band (photo #F2B01A)
MASK = 0x33373C           # anthracite front mask
WHITE_LINE = 0xE8ECEE     # white outline round the mask
SKIRT = 0x3C3F42          # bottom line of the side wall / skirt
RJ_RED = (0xE3, 0x34, 0x2F)
RJ_BLUE = (0x1F, 0x3A, 0x93)


def livery(name):
    if name != "dukzelenozluta":
        return D.livery(name)
    green = Paint(GREEN)
    yellow = Paint(YELLOW)
    return dict(
        name=name, body=green, band=Paint(BAND), door=yellow, doorframe=yellow,
        innerdoor=yellow, word_z=(0.0, 0.0),        # no Arriva wordmark
        roofside=Paint(GREEN_TOP), roof=Paint(GREEN_TOP, top=0xAEB3B7),
        mask=Paint(MASK), masktop=Paint(MASK, top=0x3E4247),
        lowfront=yellow, logo=RJ_RED, letters=Paint(0xEEF0F0),
        white=Paint(WHITE_LINE), skirtline=Paint(SKIRT),
        beam=Paint(0x2E3134), skirt=Paint(0x34373A), skirtedge=Paint(0x34373A),
        ac=False, lowband=None)


Z_SKIRT = zp(1.08)        # anthracite line at the bottom of the side wall (~1 px)
Z_TOPG = zp(3.40)         # green strip above the band up to the roof
Z_WHITE0, Z_WHITE1 = zp(1.90), zp(2.22)   # white line across the front above the yellow band


class RJCar(D.Car):
    def __init__(self, liv, owner, s_cab, dirn, motor, lamp):
        self.C = livery(liv)
        self.owner, self.s_cab, self.dirn = owner, s_cab, dirn
        self.motor, self.lamp = motor, lamp

    def zone(self, m, z, cs):
        C = self.C
        if C["name"] != "dukzelenozluta":
            return super().zone(m, z, cs)
        zm = z * PX
        if m < CABDOOR[0]:
            # cab side: yellow sweeping back from the lower front band, a white
            # edge at the front corner, black mask round the cab side window
            t = (m - D.FRONT_M) / (CABDOOR[0] - D.FRONT_M)          # 0 front .. 1 door
            ytop = 1.90 - 0.55 * max(0.0, t)                          # yellow top falls towards the door
            if zm < 1.08:
                return C["skirtline"]
            if zm <= ytop:
                return C["lowfront"]
            if zm < 1.98:
                return C["body"]
            if m < D.FRONT_M + 0.22:
                return C["white"]
            return C["mask"] if zm < 3.62 else C["roofside"]
        if zm < 1.08:
            return C["skirtline"]
        if Z_B0 <= z <= Z_B1:
            return C["band"]
        if z > Z_B1:
            return C["roofside"] if z >= Z_TOPG else C["band"]
        return C["body"]

    def side(self, m, z, cs):
        C = self.C
        r = super().side(m, z, cs)
        if C["name"] != "dukzelenozluta":
            return r
        # lettering must read left to right as seen: on the car's own right side
        # screen-left is its rear (larger m), on its own left side its front
        def along(a, b):
            x = (m - a) / (b - a)
            return 1 - x if cs == "R" else x
        if r is C["band"] and 5.15 <= m <= 6.45 and zp(2.28) <= z <= zp(2.92):
            # white "Doprava Usteckeho kraje" logo on the band behind the vestibule window
            x = along(5.15, 6.45)
            return C["letters"] if (x < 0.32 or x > 0.45) else C["band"]
        if r is C["body"] and 13.0 <= m <= 16.6 and zp(1.24) <= z <= zp(1.80):
            # "|| REGIO" red + "JET" blue on the green below the windows
            x = along(13.0, 16.6)
            if 0.13 <= x <= 0.19:
                return r                    # gap after the two slanted bars
            return Paint(RJ_RED) if x < 0.66 else Paint(RJ_BLUE)
        return r

    def front(self, m, vl, z):
        C = self.C
        if C["name"] != "dukzelenozluta":
            return super().front(m, vl, z)
        av = abs(vl)
        hw = D.front_halfwidth(z)
        if z < D.Z_MASK0:
            # round lamps near the corners (photo 628 302: head + tail lamp in
            # one housing), narrower than the Arriva model to leave room for the logo
            if D.Z_LAMP0 <= z <= D.Z_LAMP1 and 0.47 <= av <= 0.76:
                outer = av > 0.62
                if self.lamp is R.HEAD:
                    return R.HEAD
                if self.lamp is R.TAIL:
                    return R.TAIL if outer else (0x5A, 0x5E, 0x62)
            if zp(1.50) <= z <= zp(1.84) and av < 0.40:
                # "|| REGIO" red, "JET" blue; seen from the front the vehicle's
                # +v side is on the viewer's left, so the text runs from +vl to -vl
                return RJ_BLUE if vl < -0.14 else RJ_RED
            if z < zp(1.30):
                return C["beam"]
            return C["lowfront"]
        if z <= Z_WHITE1:
            return C["white"]
        if av > hw - 0.10:
            return C["white"]
        if av < hw - 0.10 and D.Z_WS0 <= z <= D.Z_WS1:
            return D.WS_HI if z > zp(3.12) else D.WS
        if self.lamp is R.HEAD and av < 0.085 and zp(1.98) <= z <= zp(2.14):
            return R.HEAD
        return C["mask"]


Z_B0, Z_B1 = D.Z_B0, D.Z_B1


def unit(liv):
    A = RJCar(liv, "A", 0.0, +1, True, R.HEAD)
    B = RJCar(liv, "B", 2 * L_CAR, -1, False, R.TAIL)
    parts = []
    for c in (A, B):
        parts += c.parts() + c.roof_parts() + c.under_parts()
    parts.append(Part(BODY_END / M - 0.02, (2 * L_CAR - BODY_END) / M + 0.02,
                      -W + 0.10, W - 0.10, D.Z_BOT + 0.35, D.ZS - 0.15,
                      lambda f, u, v, z, d: D.BELLOWS if f != "+z" else Paint(0x3A3C40), "A"))
    return parts, [], [("A", 0.0), ("B", 11.0)]


def rows_for(liv):
    parts, lines, cars = unit(liv)
    return [[R.vehicle_tile(parts, lines, d, uf, {own}) for d in DIRS] for (own, uf) in cars]


JOBS = {"628_2": [(c, (lambda c=c: rows_for(c)), ["628", "928"]) for c in LIVERIES]}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        os.makedirs(prev, exist_ok=True)
    for fam, jobs in JOBS.items():
        for liv, make, labels in jobs:
            rows = make()
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
