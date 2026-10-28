"""Iveco / Irisbus Crossway LE town fleets on the iredo_models.py Crossway
bodies: render the sprite sheets of their vehicle-bus families. Until
2026-10-28 these were Lubak91's hand-drawn sheets; the owner then asked for
one drawing per bus type (the render). The family.yaml files are written by
hand.

    python tools/busrender/crossway_town.py [family ...] [--preview DIR]

A family is named by its path under vehicle-bus/ (dpmb/crossway_le_city_12m)
or by its folder name alone.

The town liveries are bands on the white body, counted in pixel rows of the
side (TownBands): "skirt" n rows up from the body's lowest row, "raised" n
rows from one row above it (a white row under the band), "sill" the n rows
right under the glazing, "lower" everything from the bottom up to n rows
under the glazing, "cant" the row under the roof edge (the glazing stops one
row lower), "rise" a 1-px diagonal ((x0, x1, k0, k1) in place of n). A band can be limited to a stretch of the side (real metres from
the front). FRONT gives whole rows of the front (k: colour; k 4 is the band
under the windscreen, 3 the grey bar, 1 the bumper beside the plate), kept
off the headlamps and the plate; disp is the display colour. The PID schemes
(pid-a / pid-b), the 3ČSAD white-green (odis_town CsadWG) and the plain white
without the IREDO sticker (bilapk) come from their own drivers.

The details were checked against photos and the old hand-drawn sheets
(2026-10-28): the DPMB band under the windscreen, the sill line and the green
displays, the DPMP cant row and raised side band, the DPP band under the
windscreen and red lower front.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import iredo_models as M                       # noqa: E402
import pid                                     # noqa: E402,F401  (registers pid-a / pid-b)
import odis_town                               # noqa: E402,F401  (registers 3csadbilozelena)
import odis as O                               # noqa: E402
from rj_buses import row_for                   # noqa: E402
from rj_buscommon import save_rows, preview    # noqa: E402

WHITE = (0xF2, 0xF2, 0xF0)
DPMB_RED = (0xD8, 0x24, 0x1C)
DPMP_RED = (0xD2, 0x1E, 0x2B)
DPP_RED = (0xCF, 0x0B, 0x15)
JMK_RED = (0xD4, 0x1F, 0x26)
JMK_GREY = (0xA8, 0xAC, 0xB0)
TESIN_YEL = (0xF0, 0xC0, 0x20)
ARRIVA_BLUE = (0x1E, 0x9C, 0xD7)
ARRIVA_ROOF = (0x2A, 0xA8, 0xE0)
PRIBRAM_RED = (0xDE, 0x1F, 0x2A)
LEDG = (0x62, 0xD6, 0x4A)              # green LED displays (Brno, DPMB, IDS JMK)
COMETT_ORANGE = (0xF5, 0x60, 0x1C)
BLACK = (0x1E, 0x1E, 0x20)


class TownBands(M.Livery):
    """a town scheme of bands on the side (see the module docstring)"""
    sticker = False
    BANDS = ()
    FRONT = {}

    def side(self, bus, x, k, right):
        band = bus.band_at(x)
        b0 = band[0] if band else bus.R_BAND0
        for kind, n, col, *span in self.BANDS:
            if span and not (span[0] <= x < (span[1] if span[1] is not None else 99.0)):
                continue
            if kind == "skirt" and bus.SKIRT <= k < bus.SKIRT + n:
                return col
            if kind == "raised" and bus.SKIRT + 1 <= k < bus.SKIRT + 1 + n:
                return col
            if kind == "sill" and b0 - n <= k < b0:
                return col
            if kind == "lower" and bus.SKIRT <= k < b0 - n:
                return col
            if kind == "cant" and k == bus.top_row(x) - 1:
                return col
            if kind == "rise":                          # a 1-px diagonal (x0, x1, k0, k1)
                x0, x1, k0, k1 = n
                if x0 <= x < x1 and k == int(round(k0 + (k1 - k0) * (x - x0) / (x1 - x0))):
                    return col
        return None

    def front(self, bus, v, k):
        col = self.FRONT.get(k)
        if col is None:
            return None
        av = abs(v)
        if k == 2 and av > bus.W2 - 0.50:
            return None                                 # the headlamps
        if k == 1 and av < 0.28:
            return None                                 # the plate
        return col(v) if callable(col) else col


def town(slug, bands=(), body=WHITE, roof=None, bumper=None, ac=None, front=None, disp=None):
    attrs = dict(slug=slug, BANDS=tuple(bands), body=body, roof=roof or body,
                 ac=ac or (roof or body), bumper=bumper, FRONT=dict(front or {}))
    if disp:
        attrs["disp"] = disp
    if any(b[0] == "cant" for b in bands):
        attrs["cant"] = True
    cls = type("Town_" + slug.replace("-", "_"), (TownBands,), attrs)
    M.LIVERIES[slug] = cls
    return cls


# DPMB white-red: the red skirt (two rows), the red band under the windscreen
# (it carries the BRNO lettering), green displays; the LE CITY has the red line
# under the windows only behind the middle door (photos of 2744, 7829), the LE
# LINE along its whole length (2911), the 14,5M from the middle door back (7826)
DPMB_FRONT = {4: DPMB_RED}
town("t-dpmb", [("skirt", 2, DPMB_RED), ("sill", 1, DPMB_RED, 6.30, None)], bumper=DPMB_RED,
     front=DPMB_FRONT, disp=LEDG)
town("t-dpmb-line", [("skirt", 2, DPMB_RED), ("sill", 1, DPMB_RED)], bumper=DPMB_RED,
     front=DPMB_FRONT, disp=LEDG)
town("t-dpmb-145", [("skirt", 2, DPMB_RED), ("sill", 1, DPMB_RED, 7.60, None)], bumper=DPMB_RED,
     front=DPMB_FRONT, disp=LEDG)
# DPMP white-red (NRP): the red row under the roof edge, the red band on the
# lower side with a white row under it (broken by the wheel arches), the red
# stripe with the emblem across the front at headlamp height over a light
# bumper (photos of 63, 64)
town("t-dpmp", [("cant", 1, DPMP_RED), ("raised", 2, DPMP_RED)], front={3: DPMP_RED})
# the DPMP hybrid (69): plain white (photos of 69)
town("t-dpmp-hybrid")
# DPP city scheme on the Crossways: the red stripe under the windows, a white
# band, the red lower body from the wheel-arch tops; the red band under the
# windscreen and the red lower front (photo of 4506)
DPP_FRONT = {4: DPP_RED, 3: DPP_RED, 2: DPP_RED, 1: DPP_RED}
town("t-dpp", [("sill", 1, DPP_RED), ("lower", 2, DPP_RED)], bumper=DPP_RED, front=DPP_FRONT)
# the Stenbus Irisbus Crossway LE 12M (1748, Praha) in the DPP colours: no
# stripe under the windows, the red lower front (photo 440456)
town("t-dpp-nosill", [("lower", 2, DPP_RED)], bumper=DPP_RED, front={2: DPP_RED, 1: DPP_RED})
# IDS JMK (Brno BDS-BUS): red roof over the black glazing, white band, the
# silver-grey lower body, green displays
town("t-idsjmk", [("skirt", 2, JMK_GREY)], roof=JMK_RED, ac=WHITE, bumper=JMK_GREY, disp=LEDG)
# COMETT Tábor: white; the COMETT swoosh, black and orange, across the lower
# front (photos of 25, 41)
town("t-comett", front={3: lambda v: BLACK if v < 0 else COMETT_ORANGE})
# Český Těšín: the thin yellow strip under the windows
town("t-tesin", [("sill", 1, TESIN_YEL)])
# Arriva blue (Přerov, Trutnov): blue from roof to skirt
town("t-arriva", body=ARRIVA_BLUE, roof=ARRIVA_ROOF, ac=ARRIVA_ROOF, bumper=ARRIVA_BLUE)
# Přerov: the thin white swoosh rising from the front wheel arch towards the
# windows, green displays (photos of 15, 16 and 1TI 2914)
town("t-arriva-prerov", [("rise", (1.95, 3.45, 2, 5), WHITE)], body=ARRIVA_BLUE, roof=ARRIVA_ROOF,
     ac=ARRIVA_ROOF, bumper=ARRIVA_BLUE, disp=LEDG)
# Příbram (Arriva): red all over
town("t-pribram", body=PRIBRAM_RED, roof=PRIBRAM_RED, bumper=PRIBRAM_RED)


class CrosswayLECity12NP(O.Regio, M.CrosswayLECity12):
    """the DPMB Crossway LE CITY 12M NP (CNG): two roof boxes, the CNG
    fairing over the front half, longer and taller, the A/C behind it
    (photo of 7830)"""
    DISP = M.LED
    AC = (2.0, 6.6)
    AC_H = 0.26
    REAR_AC = (7.2, 9.4, 0.18)


# the DPP 14,5M in the PID grey-red: the red columns continue across the roof
CrosswayLECity145Pid = pid.body("CrosswayLECity145Pid", M.CrosswayLECity145)


def body(name):
    """a body class of this module, iredo_models.py (the town variants live
    there too) or odis.py"""
    return globals().get(name) or getattr(M, name, None) or getattr(O, name)


# family -> {livery colour: [(body, livery slug), ...] in sprite-row order}
FAMILIES = {
    "brno/crossway_le_city_12m": {"idsjmk": [("CrosswayLECity12", "t-idsjmk")]},
    "dpmb/crossway_le_city_12m": {"dpmbbilocervena": [("CrosswayLECity12NP", "t-dpmb")]},
    "dpmb/crossway_le_city_14_5m": {"dpmbbilocervena": [("CrosswayLECity145", "t-dpmb-145")]},
    "dpmb/crossway_le_line_12m": {"dpmbbilocervena": [("CrosswayLELine", "t-dpmb-line")]},
    "dpmp/crossway_le_city_12m": {"dpmpbilocervena": [("CrosswayLECity12", "t-dpmp"),
                                                      ("CrosswayLECity12Hybrid", "t-dpmp-hybrid")]},
    "dpp/crossway_le_12_8m": {"dppcervenobila": [("IrisbusCrosswayLE128", "t-dpp")]},
    "dpp/crossway_le_city_14_5m": {"pidsedocervena": [("CrosswayLECity145Pid", "pid-a")]},
    "mhd-cesky-tesin/crossway_le_city_10_8m": {"ceskytesinbilozluta": [("CrosswayLECity108x3", "t-tesin")]},
    "mhd-frydek-mistek/crossway_le_city_12m": {"3csadbilozelena": [("CrosswayLECity12", "3csadbilozelena")]},
    "mhd-prerov/crossway_le_city_12m": {"arrivamodra": [("CrosswayLECity12", "t-arriva-prerov")]},
    "mhd-pribram/crossway_le_city_12m": {"pribramcervena": [("CrosswayLECity12", "t-pribram")]},
    "mhd-tabor/crossway_le_city_12m_cng": {"comettbila": [("OCrosswayLECity", "t-comett")]},
    "praha/crossway_le_12_8m": {"bila": [("IrisbusCrosswayLE128", "bilapk")],
                                "pidcervenomodrobila": [("IrisbusCrosswayLE128", "pid-b")]},
    "praha/crossway_le_12m": {"mestskacervenobila": [("IrisbusCrosswayLE", "t-dpp-nosill")]},
    "praha/crossway_le_city_12m": {"bila": [("CrosswayLECity12", "bilapk")]},
}


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    for fam, livs in FAMILIES.items():
        if argv and fam not in argv and fam.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, "vehicle-bus", *fam.split("/"), "sprites")
        os.makedirs(d, exist_ok=True)
        for colour, parts in livs.items():
            rows = [row_for(body(b), slug) for b, slug in parts]
            save_rows(rows, os.path.join(d, colour + ".png"))
            if prev:
                os.makedirs(prev, exist_ok=True)
                preview(rows, os.path.join(prev, f"{fam.replace('/', '-')}-{colour}.png"), z=4)
            print(f"vehicle-bus/{fam}/sprites/{colour}.png  rows={len(rows)}")


if __name__ == "__main__":
    main(sys.argv[1:])
