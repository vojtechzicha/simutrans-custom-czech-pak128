"""Iveco / Irisbus Crossway LE town fleets on the iredo_models.py Crossway
bodies: render the sprite sheets of their vehicle-bus families. Until
2026-10-28 these were Lubak91's hand-drawn sheets; the owner then asked for
one drawing per bus type (the render). The family.yaml files are written by
hand.

    python tools/busrender/crossway_town.py [family ...] [--preview DIR]

A family is named by its path under vehicle-bus/ (dpmb/crossway_le_city_12m)
or by its folder name alone.

The town liveries are bands on the white body, counted in pixel rows of the
side (TownBands): "skirt" n rows up from the body's lowest row, "sill" the n
rows right under the glazing, "lower" everything from the bottom up to n rows
under the glazing. The PID schemes (pid-a / pid-b), the 3ČSAD white-green
(odis_town CsadWG) and the plain white without the IREDO sticker (bilapk)
come from their own drivers.
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


class TownBands(M.Livery):
    """a town scheme of bands on the side (see the module docstring)"""
    sticker = False
    BANDS = ()

    def side(self, bus, x, k, right):
        band = bus.band_at(x)
        b0 = band[0] if band else bus.R_BAND0
        for kind, n, col in self.BANDS:
            if kind == "skirt" and bus.SKIRT <= k < bus.SKIRT + n:
                return col
            if kind == "sill" and b0 - n <= k < b0:
                return col
            if kind == "lower" and bus.SKIRT <= k < b0 - n:
                return col
        return None


def town(slug, bands=(), body=WHITE, roof=None, bumper=None, ac=None):
    cls = type("Town_" + slug.replace("-", "_"), (TownBands,), dict(
        slug=slug, BANDS=tuple(bands), body=body, roof=roof or body,
        ac=ac or (roof or body), bumper=bumper))
    M.LIVERIES[slug] = cls
    return cls


# DPMB white-red: the red skirt (two rows)
town("t-dpmb", [("skirt", 2, DPMB_RED)], bumper=DPMB_RED)
# DPMP white-red (NRP): a red line under the windows and the red skirt
town("t-dpmp", [("sill", 1, DPMP_RED), ("skirt", 1, DPMP_RED)], bumper=DPMP_RED)
# DPP city scheme on the Crossways: the red stripe under the windows, a white
# band, the red lower body from the wheel-arch tops
town("t-dpp", [("sill", 1, DPP_RED), ("lower", 2, DPP_RED)], bumper=DPP_RED)
# IDS JMK (Brno BDS-BUS): red roof over the black glazing, white band, the
# silver-grey lower body
town("t-idsjmk", [("skirt", 2, JMK_GREY)], roof=JMK_RED, ac=WHITE, bumper=JMK_GREY)
# Český Těšín: the thin yellow strip under the windows
town("t-tesin", [("sill", 1, TESIN_YEL)])
# Arriva blue (Přerov, Trutnov): blue from roof to skirt
town("t-arriva", body=ARRIVA_BLUE, roof=ARRIVA_ROOF, ac=ARRIVA_ROOF, bumper=ARRIVA_BLUE)
# Příbram (Arriva): red all over
town("t-pribram", body=PRIBRAM_RED, roof=PRIBRAM_RED, bumper=PRIBRAM_RED)


def body(name):
    """a body class of iredo_models.py (the town variants live there too) or odis.py"""
    return getattr(M, name, None) or getattr(O, name)


# family -> {livery colour: [(body, livery slug), ...] in sprite-row order}
FAMILIES = {
    "brno/crossway_le_city_12m": {"idsjmk": [("CrosswayLECity12", "t-idsjmk")]},
    "dpmb/crossway_le_city_12m": {"dpmbbilocervena": [("CrosswayLECity12", "t-dpmb")]},
    "dpmb/crossway_le_city_14_5m": {"dpmbbilocervena": [("CrosswayLECity145", "t-dpmb")]},
    "dpmb/crossway_le_line_12m": {"dpmbbilocervena": [("CrosswayLELine", "t-dpmb")]},
    "dpmp/crossway_le_city_12m": {"dpmpbilocervena": [("CrosswayLECity12", "t-dpmp"),
                                                      ("CrosswayLECity12Hybrid", "t-dpmp")]},
    "dpp/crossway_le_12_8m": {"dppcervenobila": [("IrisbusCrosswayLE128", "t-dpp")]},
    "dpp/crossway_le_city_14_5m": {"pidsedocervena": [("CrosswayLECity145", "pid-a")]},
    "mhd-cesky-tesin/crossway_le_city_10_8m": {"ceskytesinbilozluta": [("CrosswayLECity108x3", "t-tesin")]},
    "mhd-frydek-mistek/crossway_le_city_12m": {"3csadbilozelena": [("CrosswayLECity12", "3csadbilozelena")]},
    "mhd-prerov/crossway_le_city_12m": {"arrivamodra": [("CrosswayLECity12", "t-arriva")]},
    "mhd-pribram/crossway_le_city_12m": {"pribramcervena": [("CrosswayLECity12", "t-pribram")]},
    "mhd-tabor/crossway_le_city_12m_cng": {"comettbila": [("OCrosswayLECity", "bilapk")]},
    "praha/crossway_le_12_8m": {"bila": [("IrisbusCrosswayLE128", "bilapk")],
                                "pidcervenomodrobila": [("IrisbusCrosswayLE128", "pid-b")]},
    "praha/crossway_le_12m": {"mestskacervenobila": [("IrisbusCrosswayLE", "t-dpp")]},
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
