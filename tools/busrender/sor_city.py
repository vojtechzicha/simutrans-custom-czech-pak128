"""SOR buses outside iredo.py, pid.py, odis.py and odis_town.py on the shared
box bodies of iredo_models.py / iredo_coachmodels.py (the owner's common SOR
base of 2026-10-24, iredo_models.SHAPE): render the sprite sheets of their
vehicle-bus families. Their family.yaml files are written by hand.

    python tools/busrender/sor_city.py [family ...] [--preview DIR]

A family is named by its path under vehicle-bus/ (brno/sor_cn_12) or by its
folder name alone. Bodies keep the length scale of the IREDO families (12 m =
8, about 9.5 m = 7). The PID cars take the liveries and roof bands of pid.py;
the others are painted here:
    idsjmk          IDS JMK (BDS-BUS, Brno line 74): white, the red cant rail
                    over the windows, a dark belt line at the arch tops, a
                    silver-grey lower body, grey bumpers, green LED displays
    stenbus         Stenbus turquoise, a thin yellow line along the sides at
                    the arch tops, amber LED displays
    dpmb            DPMB white-red: the red lower third under a white strip,
                    round the rear too, the red bumper sweeping up at the front
                    corners, green LED displays
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import odis_town as T                                                   # noqa: E402
import iredo_models as M                                                # noqa: E402
import iredo_coachmodels as CM                                          # noqa: E402
import khk_town as K                                                    # noqa: E402
import pid as P                                                         # noqa: E402  (registers pid-a / pid-b)
from rj_buses import row_for                                            # noqa: E402
from rj_vrender import Sh                                               # noqa: E402

GREY_LOW = (0xC6, 0xC6, 0xC4)      # IDS JMK silver-grey lower body (the pak128_czr IDS JMK grey)
JMK_RED = (0xE1, 0x1B, 0x22)       # IDS JMK red
BELT = (0x3A, 0x3C, 0x3F)          # dark belt line
TURQ = (0x08, 0xAA, 0xAA)          # Stenbus turquoise (as the repainted VTPsim sheet)
TURQ_ROOF = (0x14, 0xB4, 0xB4)
TURQ_SEAM = (0x07, 0x8D, 0x8D)
STEN_YELLOW = (0xF2, 0xC2, 0x00)
DPMB_RED = (0xCD, 0x20, 0x1A)      # DPMB red (as the previous DPMB render)


# ====================================================================== liveries
class IdsJmk(M.Livery):
    """IDS JMK (BDS-BUS SOR CN 12 on Brno line 74): white, the red cant rail
    over the windows (the red line along the roof edges), a white band under
    the windows, a dark belt line at the arch tops, the silver-grey lower body
    and grey bumpers, the white A/C pod, light grey roof"""
    slug = "idsjmk"
    sticker = False
    cant = True
    body = (0xEC, 0xEC, 0xEA)
    roof = (0xD8, 0xD8, 0xD6)
    ac = (0xEC, 0xEC, 0xEA)
    seam = (0xB4, 0xB4, 0xB2)
    bumper = GREY_LOW
    BELT_ROW = 3

    def side(self, bus, x, k, right):
        band = bus.band_at(x)
        if band and k >= band[1]:
            return JMK_RED                               # the cant rail
        if k == self.BELT_ROW:
            return BELT
        if k < self.BELT_ROW:
            return GREY_LOW
        return None

    def front(self, bus, v, k):
        return GREY_LOW if k <= 1 else None

    def rear(self, bus, v, k):
        return GREY_LOW if k < self.BELT_ROW else None


class Stenbus(M.Livery):
    """Stenbus 1700 (Prague X221, 2026): turquoise all over, roof and front
    too, a thin yellow line low along both sides at the arch tops, none on the
    front"""
    slug = "stenbus"
    sticker = False
    body = TURQ
    roof = TURQ_ROOF
    ac = TURQ_ROOF
    seam = TURQ_SEAM
    LINE_ROW = 3

    def side(self, bus, x, k, right):
        return STEN_YELLOW if k == self.LINE_ROW and 0.30 <= x < bus.real_len - 0.25 else None


class Dpmb(M.Livery):
    """DPMB Brno white-red (ICN 9,5 7527-7546): white body and roof, the red
    lower third under a white strip, continued round the rear, a red bumper
    sweeping up at the front corners"""
    slug = "dpmb"
    sticker = False
    body = (0xF8, 0xF8, 0xF6)
    roof = (0xF0, 0xF0, 0xEE)
    ac = (0xF2, 0xF2, 0xF0)
    seam = (0xDC, 0xDC, 0xDA)
    bumper = DPMB_RED

    def red_top(self, bus, x):
        band = bus.band_at(x)
        return (band[0] if band else bus.R_BAND0) - 2      # one white row under the windows

    def side(self, bus, x, k, right):
        return DPMB_RED if k <= self.red_top(bus, x) else None

    def front(self, bus, v, k):
        if k <= 1 or (k == 2 and abs(v) > bus.W2 - 0.45):
            return DPMB_RED
        return None

    def rear(self, bus, v, k):
        return DPMB_RED if k <= bus.R_BAND0 - 3 else None


for _lv in (IdsJmk, Stenbus, Dpmb):
    M.LIVERIES[_lv.slug] = _lv


# ====================================================================== bodies
class GreenLED(T.TownBus):
    DISP = K.LEDG


class AmberLED(T.TownBus):
    DISP = M.LED


class BrnoCN12(GreenLED, M.SorCN):
    """SOR CN 12 (BDS-BUS, IDS JMK): drawn on the CN 12,3 body like every CN 12;
    the red line along both roof edges and the red cap over the windscreen,
    as the IDS JMK buses wear them"""
    def roof(self, u, v):
        if abs(v) > self.W2 - 0.30:
            return JMK_RED
        return super().roof(u, v)

    def front_face(self, v, av, k, d):
        if k >= self.R_TOP:
            return Sh(JMK_RED)
        return super().front_face(v, av, k, d)


class StenbusCN95(AmberLED, M.SorCN95):
    """SOR CN 9,5 (Stenbus 1700)"""


class DpmbICN95(GreenLED, CM.SorICN95):
    """SOR ICN 9,5 (DPMB 7527-7546)"""


PSorICN95 = P.body("PSorICN95", CM.SorICN95)


# family (path under vehicle-bus/) -> [(livery file, body class, M.LIVERIES key)]
FAMILIES = {
    "brno/sor_cn_12": [("idsjmk", BrnoCN12, "idsjmk")],
    "praha/sor_cn_9_5": [("pidcervenomodrobila", P.PSorCN95, "pid-b"),
                         ("tyrkysovozluta", StenbusCN95, "stenbus")],
    "praha/sor_icn_9_5": [("pidsedocervena", PSorICN95, "pid-a")],
    "dpp/icn_9_5": [("pidsedocervena", PSorICN95, "pid-a")],
    "dpmb/icn_9_5": [("dpmbbilocervena", DpmbICN95, "dpmb")],
}


# ====================================================================== main
def main(argv):
    pv = None
    if "--preview" in argv:
        i = argv.index("--preview")
        pv = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
        os.makedirs(pv, exist_ok=True)
    for key, livs in FAMILIES.items():
        if argv and key not in argv and key.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, "vehicle-bus", *key.split("/"), "sprites")
        os.makedirs(d, exist_ok=True)
        for slug, cls, lv in livs:
            rows = [row_for(cls, lv)]
            T.save_sheet(rows, os.path.join(d, slug + ".png"))
            if pv:
                T.preview(rows, os.path.join(pv, f"{key.replace('/', '-')}-{slug}.png"))
            print(f"vehicle-bus/{key}/sprites/{slug}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
