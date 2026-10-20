"""PID regional buses (the suburban and regional lines around Prague, ordered by
Středočeský kraj / IDSK and Prague): render the sprite sheets and write the
family.yaml of every vehicle-bus/pid/<family>.

    python tools/busrender/pid.py [family ...] [--yaml] [--preview DIR]

Package (TODO "a PID package for the regional lines", 2026-10-20): agency PID
-> VZ-PID-bus.pak. As in VZ-Praha there is one object per type x livery,
shared by every operator that runs it; the operator appears only in the livery
display name. Types already drawn in VZ-Praha / VZ-DPPraha in the same livery
(city-type buses that also work suburban lines) are NOT repeated here: the
regional lines use those objects.

Scope: the 2024 contracts (35 areas, 13 operators, about 1,530 buses) and the
direct awards, October 2026 (seznam-autobusu registers, open-ended periods; 11
days of deployment records). 92 % wear the PID 2021 grey-red, 6 % the old
red-blue-white "trikolóra"; advert wraps get no object.

Liveries (on the IREDO coach-pipeline bodies; colours as praha.py "A" / "B"):
  pidsedocervena       PID 2021 grey-red: grey body, black glazing band up to
                       the roof edge, a red column behind the front axle and
                       one over the rear axle (lower body, cant and a band
                       across the roof), a red block on the vehicle's left of
                       the lower front and rear
  pidcervenomodrobila  the old trikolóra: blue roof and cant, black glazing
                       band, white band, red lower body, red bumpers
"""
import os
import sys
import textwrap

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import odis_town as T                                                   # noqa: E402
import iredo_models as M                                                # noqa: E402
import iredo_coachmodels as CM                                          # noqa: E402
from rj_vrender import Sh                                               # noqa: E402
from rj_buses import row_for                                            # noqa: E402
from rj_busmodels import W2                                             # noqa: E402

PID_GREY = (0xC6, 0xC8, 0xCB)
PID_ROOF = (0xD2, 0xD4, 0xD7)
PID_RED = (0xCF, 0x1F, 0x2B)
TRI_WHITE = (0xFA, 0xFA, 0xFA)
TRI_RED = (0xCF, 0x0B, 0x15)
TRI_BLUE = (0x21, 0x4E, 0x9E)
TRI_ROOF = (0x26, 0x57, 0xAD)


def sill(bus, x):
    band = bus.band_at(x)
    return band[0] if band else bus.R_BAND0


def band_top(bus, x):
    band = bus.band_at(x)
    return band[1] if band else bus.R_TOP


# ====================================================================== liveries
class PidA(M.Livery):
    """PID 2021 grey-red (the red columns at the body's PID_COLS, real metres)"""
    slug = "pid-a"
    body = PID_GREY
    roof = PID_ROOF
    ac = PID_ROOF
    seam = (0xB4, 0xB6, 0xBA)

    @staticmethod
    def cols(bus):
        c = getattr(bus, "PID_COLS", None)
        if c is not None:
            return c
        a0, a1 = bus.axles[0], bus.axles[-1]
        return ((a0 - 0.25, a0 + 1.55), (a1 - 0.85, a1 + 0.85))

    def column(self, bus, x):
        return any(a <= x < b for a, b in self.cols(bus))

    def side(self, bus, x, k, right):
        col = self.column(bus, x)
        if k < sill(bus, x):
            return PID_RED if col else None
        if k >= band_top(bus, x):
            return PID_RED if col else M.BLACK          # the cant: black, red over a column
        return None

    def front(self, bus, v, k):
        if k <= 3 and v < -0.15 and not (k == 2 and v < -W2 + 0.55):
            return PID_RED                              # red block on the vehicle's left
        return None

    def rear(self, bus, v, k):
        return PID_RED if k <= 3 and v < -0.15 else None


class PidB(M.Livery):
    """the old PID trikolóra"""
    slug = "pid-b"
    body = TRI_WHITE
    roof = TRI_ROOF
    ac = TRI_ROOF
    seam = (0xE0, 0xE0, 0xE0)
    bumper = TRI_RED
    TOP_RED = 2                                         # red up to row 2 (0.87 m)

    def side(self, bus, x, k, right):
        if k <= self.TOP_RED:
            return TRI_RED
        if k >= band_top(bus, x):
            return TRI_BLUE
        return None

    def front(self, bus, v, k):
        return TRI_RED if k <= 1 else None

    def rear(self, bus, v, k):
        return TRI_RED if k <= 2 else None

    def ac_side(self):
        return Sh(tuple(c * 0.90 for c in TRI_ROOF))


for _lv in (PidA, PidB):
    M.LIVERIES[_lv.slug] = _lv


class Pid:
    """body mixin: no IREDO sticker, amber LED displays (the IREDO default),
    the red PID columns continued across the roof"""
    KHK_STICKER = False

    def roof(self, u, v):
        if hasattr(self.lv, "column") and self.lv.column(self, self.X(u)):
            return PID_RED
        return super().roof(u, v)


# ====================================================================== bodies
import odis as O                                                        # noqa: E402


def body(name, *bases, **attrs):
    """a PID body class: Pid first, amber displays on the odis Regio bodies"""
    attrs.setdefault("DISP", M.LED)
    return type(name, (Pid,) + bases, attrs)


PCrosswayLELine = body("PCrosswayLELine", M.CrosswayLELine)
PCrosswayLELine145 = body("PCrosswayLELine145", M.CrosswayLELine145)
PCrosswayLELine108 = body("PCrosswayLELine108", M.CrosswayLELine108)
PCrosswayLELineNP = body("PCrosswayLELineNP", O.OCrosswayLELineNP)
PCrosswayLine = body("PCrosswayLine", M.CrosswayLine)
PCrosswayLECityNP = body("PCrosswayLECityNP", O.OCrosswayLECity)
PCrosswayLECity12 = body("PCrosswayLECity12", M.CrosswayLECity12)
PIrisbusCrosswayLE = body("PIrisbusCrosswayLE", M.IrisbusCrosswayLE)
PIrisbusCrosswayLE108 = body("PIrisbusCrosswayLE108", M.IrisbusCrosswayLE108)
PIrisbusCrossway = body("PIrisbusCrossway", M.IrisbusCrossway)
PSetra415 = body("PSetra415", CM.SetraS415LE)
PSetra418 = body("PSetra418", CM.SetraS418LE)
PSorCN12 = body("PSorCN12", O.OSorCN12)
PSorCN123 = body("PSorCN123", M.SorCN)
PSorCN105 = body("PSorCN105", O.OSorCN105)
PSorCN95 = body("PSorCN95", M.SorCN95)
PSorCNG12 = body("PSorCNG12", O.OSorCNG12)
PSorICN12 = body("PSorICN12", CM.SorICN)
PSorICN105 = body("PSorICN105", CM.SorICN105)
PSorC105 = body("PSorC105", M.SorC105)
PSorC95 = body("PSorC95", M.SorC95)


class _CrosswayLELine13(M.CrosswayLELine):
    """Iveco Crossway LE LINE 12M stretched to the 13M: tag axle, the middle door
    further back"""
    real_len = 13.0
    axles = (2.65, 9.30, 10.65)
    DOORS = ((0.32, 1.32, "le"), (5.60, 6.80, "le"))
    BAND = ((0.0, 13.0, 6, 11),)
    AC = (2.5, 6.2)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 7.40, 8.90, 10.4, 11.9)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 10.1, 11.6)


PCrosswayLELine13 = body("PCrosswayLELine13", _CrosswayLELine13)


def scania_port(name, Ls):
    """a VTPsim Scania Citywide sheet ported and its ring stand-in painted out (odis.py)"""
    return lambda: O.strip_marks(T.port_native(name, Ls[0], T.LEDW, T.CSAD_GREEN)[0], Ls)


def dekstra_cng():
    """the IREDO white Dekstra LE 37 with the low CNG box of the odis.py LE 37 L CNG"""
    return T.repaint(T.load_rows("vehicle-bus/iredo/dekstra_le_37/sprites/bila.png"), T.z_white,
                     {"white": ((0xEE, 0xEE, 0xEC), T.WHITE)}, [[7.0, 7.5, 8.0]], None,
                     [[(0.30, 0.70, 0.22, 0.80)]], T.WHITE_POD)


def praha_rows(spec_fn, key):
    """rows of a dpmhk.py body painted by praha.py's PVeh ("A" grey-red, "B" trikolóra);
    spec_fn() builds the spec (praha / dpmhk imported on use)"""
    def build():
        import numpy as np
        import praha as PR
        return [[np.array(t)[:, :, :3].copy() for t in r] for r in PR.build(spec_fn(), key)]
    return build


def _nb18():
    import dpmhk as H
    # SOR NB 18 (Arriva City / Arriva Střední Čechy): red columns round the three axles
    # (photo 9932), A/C units between the roof bands
    return H.mk(H.NB18, pods=[(3.6, 6.0, 0.24, 0.85, "ac"), (12.9, 14.4, 0.22, 0.80, "ac")],
                reds=[(1.8, 3.9), (9.4, 11.3), (14.6, 16.4)], tower=True)


def _nbg12():
    import dpmhk as H
    # SOR NBG 12 (Arriva City 2017): the CNG fairing over the front two thirds
    return H.mk(H.NB12, pods=[(1.6, 7.6, 0.36, 1.00, "body")], reds=[(1.6, 3.7), (7.7, 9.5)])


def _nbg18():
    import dpmhk as H
    return H.mk(H.NB18, pods=[(1.8, 10.0, 0.36, 1.00, "body"), (13.0, 15.6, 0.30, 0.95, "body")],
                reds=[(1.8, 3.9), (9.4, 11.3), (14.6, 16.4)], tower=True)


def _uw12cng_b():
    import dpmhk as H
    import praha as PR
    return H.mk(PR.PUW12B, pods=[(1.6, 8.6, 0.36, 1.00, "body")])


def _uw12cng_a():
    import dpmhk as H
    import praha as PR
    return H.mk(PR.PUW12A, pods=[(1.6, 8.6, 0.36, 1.00, "body")])


PID_GREY_SIDE = (0xC0, 0xC2, 0xC5)


def pid_decal(cols, zwin=(1.10, 2.45)):
    """decals() for odis_town.repaint: the PID grey-red on a fitted hand-drawn sheet
    already repainted grey. cols = [(f0, f1)] body fractions of the red columns;
    zwin = (window bottom, window top) metres. The columns are red on the lower body,
    the cant and the roof; the cant elsewhere is black (the glazing band up to the
    roof edge)."""
    def draw(o, paint, geo, d, r):
        o = o.copy()
        face, frac, z = geo["face"], geo["frac"], geo["z"]
        for y, x in zip(*np.where(paint)):
            f, zz, fc = float(frac[y, x]), float(z[y, x]), int(face[y, x])
            col = any(a <= f < b for a, b in cols)
            if fc == 1:
                if col:
                    o[y, x] = T.scaled(PID_RED, max(0.7, min(1.1, T.lum(o[y, x]) / T.lum(PID_ROOF))))
                continue
            if fc not in (4, 5):
                continue
            k = max(0.6, min(1.1, T.lum(o[y, x]) / T.lum(PID_GREY_SIDE)))
            if zz >= zwin[1]:
                o[y, x] = T.scaled(PID_RED, k) if col else (0x1E, 0x1F, 0x22)
            elif zz < zwin[0] and col:
                o[y, x] = T.scaled(PID_RED, k)
        return o
    return draw


def z_any_light(c):
    """light neutral body paint and the red / blue of the PID sheets (all repainted)"""
    if T.hexc(c) in T.H.SPECIAL:
        return None
    if T.neutral(c, 0xA8, tol=18):
        return "white"
    r, g, b = c
    if r > 0xA0 and g < 0x50 and b < 0x50:
        return "white"
    if b > 0x80 and r < 0x50:
        return "white"
    if g > r + 0x30 and g > b + 0x20:
        return "white"                                  # 3ČSAD green of the ODIS / VTPsim sheets
    return None


PID_ZONES = {"white": (PID_GREY_SIDE, PID_ROOF), "green": (PID_GREY_SIDE, PID_ROOF)}


def pid_repaint(src, Ls, cols, zwin=(1.10, 2.45), zone_of=z_any_light, pods=None):
    """a repo sheet repainted in the PID grey-red with its columns"""
    def build():
        rows = T.load_rows(src) if isinstance(src, str) else src()
        return T.repaint(rows, zone_of, PID_ZONES, Ls, pid_decal(cols, zwin), pods,
                         (PID_GREY_SIDE, PID_ROOF), T.disp(M.LED, frm=(0xF0A018, 0xF7A21B, 0xECEEE4)))
    return build


def man_intercity_le14():
    """MAN Lion's Intercity LE 14 (Lutan): praha_man.IntercityLE stretched to 13.9 m
    in the PID grey-red ("A") of the Prague Lion's Intercity LE 12"""
    import praha_man as PM
    import numpy as np
    cls = PM.stretched(PM.IntercityLE, 13.9)
    row = PM.build_row(cls, "A", None, label="lions_intercity_le_14")
    return [[np.array(t)[:, :, :3].copy() for t in row]]


# ====================================================================== families
f_ = T.f_
PID = ("PID", "PID", "PID")
BUS, MIDI = T.BUS, T.MIDI
SMOKE = "Diesel_small"


def A(ops):
    return ("pidsedocervena", f"PID grey-red · {ops}", f"PID šedo-červená · {ops}")


def B(ops):
    return ("pidcervenomodrobila", f"PID red-blue-white · {ops}", f"PID červeno-modro-bílá · {ops}")


def model(cls, liv):
    return lambda: [row_for(cls, liv)]


def flow(text, width=78):
    return textwrap.fill(" ".join(text.split()), width)


def rendered(cls):
    base = [b for b in cls.__mro__ if b.__module__ in ("iredo_models", "iredo_coachmodels")][0]
    via = [b for b in cls.__mro__ if b.__module__ == "odis"]
    extra = f" (with the roof of odis.{via[0].__name__})" if via else ""
    return (f"original box-model render (vojtechzicha): {base.__name__} of {base.__module__}.py"
            f"{extra} painted in the PID liveries of tools/busrender/pid.py.")


def fam(folder, type_, name, role, flds, livs, cls, note, sprite=None, copyright="vojtechzicha"):
    """livs: [(livery tuple, M.LIVERIES key)]; cls: a body class, or a function
    returning the rows (then the key is ignored)"""
    lv = []
    for (slug, en, cs), key in livs:
        fn = model(cls, key) if isinstance(cls, type) else cls
        lv.append((slug, en, cs, fn))
    short = name.replace("Iveco ", "").replace("Irisbus ", "").replace("MAN ", "")
    return ("pid/" + folder, dict(agency=PID, type=type_, name=(name, name), copyright=copyright,
                                  vehicles=T.one(type_, short, role, flds),
                                  liveries=lv, note=flow(note),
                                  sprite=flow(sprite or rendered(cls), 70), allow=()))


def city(folder, type_, name, vehicles, livs, note):
    """a family on the dpmhk.py city bodies painted by praha.py; livs: [(livery
    tuple, rows function)]"""
    lv = [(slug, en, cs, fn) for (slug, en, cs), fn in livs]
    return ("pid/" + folder, dict(agency=PID, type=type_, name=(name, name), copyright="vojtechzicha",
                                  vehicles=vehicles, liveries=lv, note=flow(note),
                                  sprite=flow("original box-model render (vojtechzicha): the dpmhk.py"
                                              " body painted by praha.py PVeh in the PID liveries, spec"
                                              " in tools/busrender/pid.py.", 70), allow=()))


def sheet(folder, type_, name, role, flds, livs, note, sprite, copyright):
    """a family repainted from a repo sheet; livs: [(livery tuple, rows function)]"""
    lv = [(slug, en, cs, fn) for (slug, en, cs), fn in livs]
    return ("pid/" + folder, dict(agency=PID, type=type_, name=(name, name), copyright=copyright,
                                  vehicles=T.one(type_, name.replace("Iveco ", "").replace("Irisbus ", "")
                                                 .replace("Scania ", ""), role, flds),
                                  liveries=lv, note=flow(note), sprite=flow(sprite, 70), allow=()))


GR = "PID 2021 grey-red (pidsedocervena)."
RBW = "the old PID red-blue-white (pidcervenomodrobila)."

FAMILIES = dict([
    fam("crossway_le_line_12m", "Crossway_LE_Line_12M", "Iveco Crossway LE LINE 12M", BUS,
        f_(640000, 92, 100, 11, 26, 131, 2014, 8, "diesel", 243, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy, Arriva City, ČSAD Střední Čechy, Arriva autobusy, ČSAD Polkost, "
            "OAD Kolín, Martin Uher, Transdev Střední Čechy, ZDAR and others"), "pid-a"),
         (B("Martin Uher bus"), "pid-b")],
        PCrosswayLELine,
        "Iveco Crossway LE LINE 12M low-entry interurban, the biggest PID regional type: 425"
        " buses (2014-2026) in " + GR + " One (Martin Uher bus, 2015) in " + RBW +
        " The 2025-26 deliveries with the facelift front are drawn the same."),
    fam("crossway_le_line_14_5m", "Crossway_LE_Line_14_5M", "Iveco Crossway LE LINE 14,5M", BUS,
        f_(720000, 110, 100, 14, 29, 147, 2018, 10, "diesel", 265, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy, ČSAD Střední Čechy, OAD Kolín, Transdev Střední Čechy, Arriva autobusy"),
          "pid-a")],
        PCrosswayLELine145,
        "Iveco Crossway LE LINE 14,5M, three axles: 78 buses (2018-2025) in " + GR),
    fam("crossway_le_line_12m_np", "Crossway_LE_Line_12M_NP", "Iveco Crossway LE LINE 12M NP", BUS,
        f_(680000, 92, 90, 12, 27, 139, 2019, 8, "diesel", 243, 54),
        [(A("ČSAD Střední Čechy, Ekoservis Transpeed"), "pid-a")],
        PCrosswayLELineNP,
        "Iveco Crossway LE LINE 12M NP (CNG; engine_type diesel, no smoke), the long flat CNG"
        " fairing: 67 buses (2019-2020) in " + GR),
    fam("crossway_line_12m", "Crossway_Line_12M", "Iveco Crossway LINE 12M", BUS,
        f_(600000, 80, 100, 11, 24, 122, 2013, 8, "diesel", 243, 54, smoke=SMOKE),
        [(A("Transdev Střední Čechy, ZDAR, Arriva autobusy, Arriva Střední Čechy, OAD Kolín, ČSAD Polkost"),
          "pid-a"),
         (B("Martin Uher bus"), "pid-b")],
        PCrosswayLine,
        "Iveco Crossway LINE 12M high-floor interurban: 33 buses (2013-2024) in " + GR +
        " One (Martin Uher bus) in " + RBW),
    fam("crossway_le_line_10_8m", "Crossway_LE_Line_10_8M", "Iveco Crossway LE LINE 10,8M", BUS,
        f_(590000, 80, 100, 10, 24, 120, 2014, 7, "diesel", 210, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy, Lamer, Lextrans"), "pid-a")],
        PCrosswayLELine108,
        "Iveco Crossway LE LINE 10,8M: 4 buses in " + GR),
    fam("crossway_le_city_12m_np", "Crossway_LE_City_12M_NP", "Iveco Crossway LE CITY 12M NP", BUS,
        f_(660000, 100, 85, 12, 26, 135, 2019, 8, "diesel", 243, 54),
        [(A("Arriva City, ČSAD Střední Čechy"), "pid-a")],
        PCrosswayLECityNP,
        "Iveco Crossway LE CITY 12M NP (CNG; engine_type diesel, no smoke), doors 2-2-0, the"
        " long flat CNG fairing: 21 buses (2019-2020) in " + GR),
    fam("crossway_le_city_12m", "Crossway_LE_City_12M", "Iveco Crossway LE CITY 12M", BUS,
        f_(630000, 100, 85, 11, 25, 129, 2014, 8, "diesel", 243, 54, smoke=SMOKE),
        [(A("Arriva autobusy"), "pid-a")],
        PCrosswayLECity12,
        "Iveco Crossway LE CITY 12M (diesel), three double doors: 6 buses (2014-2017) in " + GR),
    fam("irisbus_crossway_le_12m", "Irisbus_Crossway_LE_12M", "Irisbus Crossway LE 12M", BUS,
        f_(600000, 92, 100, 11, 24, 122, 2009, 8, "diesel", 243, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy, Transdev Střední Čechy, Martin Uher"), "pid-a")],
        PIrisbusCrosswayLE,
        "Irisbus Crossway LE 12M (2009-2014 front): 10 buses in " + GR),
    fam("irisbus_crossway_le_10_8m", "Irisbus_Crossway_LE_10_8M", "Irisbus Crossway LE 10,8M", BUS,
        f_(570000, 80, 100, 10, 23, 116, 2013, 7, "diesel", 213, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy"), "pid-a")],
        PIrisbusCrosswayLE108,
        "Irisbus Crossway LE 10,8M: 3 buses (2013) in " + GR),
    fam("irisbus_crossway_12m", "Irisbus_Crossway_12M", "Irisbus Crossway 12M", BUS,
        f_(580000, 80, 100, 11, 23, 118, 2012, 8, "diesel", 243, 54, smoke=SMOKE),
        [(B("Martin Uher bus"), "pid-b")],
        PIrisbusCrossway,
        "Irisbus Crossway 12M high-floor interurban: 2 buses (2012) in " + RBW),
    fam("setra_s_415_le_business", "Setra_S_415_LE_business", "Setra S 415 LE business", BUS,
        f_(680000, 90, 100, 11, 27, 139, 2014, 8, "diesel", 260, 54, smoke=SMOKE),
        [(A("ČSAD Benešov, ČSAD Slaný"), "pid-a")],
        PSetra415,
        "Setra S 415 LE business: 116 buses (2020-2024) in " + GR),
    fam("setra_s_418_le_business", "Setra_S_418_LE_business", "Setra S 418 LE business", BUS,
        f_(760000, 108, 100, 13, 30, 155, 2016, 10, "diesel", 290, 54, smoke=SMOKE),
        [(A("ČSAD Slaný, ČSAD Benešov"), "pid-a")],
        PSetra418,
        "Setra S 418 LE business, three axles: 26 buses (2024) in " + GR),
    fam("sor_cn_12", "SOR_CN_12", "SOR CN 12", BUS,
        f_(620000, 90, 100, 11, 25, 127, 2013, 8, "diesel", 235, 54, smoke=SMOKE),
        [(A("OAD Kolín, AKV bus, ZDAR, Arriva Střední Čechy, Transdev Střední Čechy, Lutan"), "pid-a"),
         (B("OAD Kolín"), "pid-b")],
        PSorCN12,
        "SOR CN 12 low-entry interurban: 44 buses (2013-2021) in " + GR + " Two (OAD Kolín,"
        " 2014) in " + RBW),
    fam("sor_cn_12_3", "SOR_CN_12_3", "SOR CN 12,3", BUS,
        f_(620000, 90, 100, 11, 25, 127, 2014, 8, "diesel", 235, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy, Transdev Střední Čechy, Arriva City"), "pid-a")],
        PSorCN123,
        "SOR CN 12,3: 16 buses (2014-2017) in " + GR),
    fam("sor_cng_12", "SOR_CNG_12", "SOR CNG 12", BUS,
        f_(650000, 90, 90, 12, 26, 132, 2020, 8, "diesel", 213, 54),
        [(A("OAD Kolín"), "pid-a")],
        PSorCNG12,
        "SOR CNG 12 (CNG; engine_type diesel, no smoke), the tank fairing over the front half:"
        " 20 buses (OAD Kolín, 2020) in " + GR),
    fam("sor_cng_12_3", "SOR_CNG_12_3", "SOR CNG 12,3", BUS,
        f_(650000, 90, 90, 12, 26, 132, 2015, 8, "diesel", 213, 54),
        [(A("Arriva City"), "pid-a")],
        PSorCNG12,
        "SOR CNG 12,3 (CNG; engine_type diesel, no smoke): 11 buses (Arriva City, 2015-2016)"
        " in " + GR + " Drawn as the SOR CNG 12."),
    fam("sor_cn_10_5", "SOR_CN_10_5", "SOR CN 10,5", BUS,
        f_(560000, 78, 100, 10, 22, 114, 2013, 7, "diesel", 210, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy, Arriva autobusy, Lutan"), "pid-a")],
        PSorCN105,
        "SOR CN 10,5: 12 buses (2013-2021) in " + GR),
    fam("sor_cn_9_5", "SOR_CN_9_5", "SOR CN 9,5", MIDI,
        f_(520000, 68, 90, 9, 21, 106, 2019, 7, "diesel", 180, 54, smoke=SMOKE),
        [(A("ČSAD Střední Čechy"), "pid-a")],
        PSorCN95,
        "SOR CN 9,5 low-entry midibus: 4 buses (ČSAD Střední Čechy, 2019) in " + GR +
        " The trikolóra ones are the VZ-Praha SOR CN 9,5."),
    fam("sor_icn_12", "SOR_ICN_12", "SOR ICN 12", BUS,
        f_(660000, 90, 100, 11, 26, 135, 2023, 8, "diesel", 235, 54, smoke=SMOKE),
        [(A("OAD Kolín, Arriva autobusy, Transdev Střední Čechy, AKV bus"), "pid-a")],
        PSorICN12,
        "SOR ICN 12, flat roof and deep glazing: 49 buses (2023-2024) in " + GR),
    fam("sor_icn_10_5", "SOR_ICN_10_5", "SOR ICN 10,5", BUS,
        f_(600000, 76, 100, 10, 24, 122, 2024, 7, "diesel", 210, 54, smoke=SMOKE),
        [(A("ZDAR, Lutan"), "pid-a")],
        PSorICN105,
        "SOR ICN 10,5: 11 buses (2024) in " + GR),
    fam("sor_c_10_5", "SOR_C_10_5", "SOR C 10,5", BUS,
        f_(520000, 75, 100, 10, 21, 106, 2018, 7, "diesel", 200, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy"), "pid-a")],
        PSorC105,
        "SOR C 10,5 high-floor interurban: 1 bus (2018) in " + GR),
    fam("sor_c_9_5", "SOR_C_9_5", "SOR C 9,5", MIDI,
        f_(500000, 66, 90, 9, 20, 102, 2019, 7, "diesel", 180, 54, smoke=SMOKE),
        [(A("AD Kohout"), "pid-a")],
        PSorC95,
        "SOR C 9,5 high-floor midibus: 1 bus (2019) in " + GR),
    fam("lions_intercity_le_14", "Lions_Intercity_LE_14", "MAN Lion's Intercity LE 14", BUS,
        f_(740000, 104, 100, 13, 29, 151, 2024, 9, "diesel", 243, 54, smoke=SMOKE),
        [(A("Lutan"), None)],
        man_intercity_le14,
        "MAN LEÜ 330 Lion's Intercity LE 14 (13.9 m): 4 buses (Lutan, 2024) in " + GR +
        " The 12 m Lion's Intercity LE is the VZ-Praha object.",
        sprite="original box-model render (vojtechzicha): praha_man.IntercityLE of"
               " tools/busrender/praha_man.py stretched to 13.9 m, PID grey-red."),
    # ------------------------------------------------------------ dpmhk.py bodies (praha.py PVeh)
    city("sor_nb_18", "SOR_NB_18", "SOR NB 18",
         T.artic("SOR_NB_18", "NB 18",
                 f_(560000, 100, 75, 11, 22, 115, 2011, 9, "diesel", 0, 54),
                 f_(420000, 60, 75, 7, 16, 82, 2011, 5, "diesel", 260, 61, smoke=SMOKE)),
         [(A("Arriva City, Arriva Střední Čechy"), praha_rows(_nb18, "A")),
          (B("OAD Kolín"), praha_rows(_nb18, "B"))],
         "SOR NB 18 low-floor articulated, front section 9 + rear 5 as the DPMHK NB 18: 44"
         " buses (2016-2019; Arriva City 37, Arriva Střední Čechy 7) in " + GR + " One (OAD"
         " Kolín, 2011) in " + RBW),
    city("sor_nbg_12", "SOR_NBG_12", "SOR NBG 12",
         T.one("SOR_NBG_12", "NBG 12", BUS, f_(600000, 100, 75, 12, 23, 120, 2017, 8, "diesel", 213, 54)),
         [(A("Arriva City"), praha_rows(_nbg12, "A"))],
         "SOR NBG 12 (CNG; engine_type diesel, no smoke), the CNG fairing over the front two"
         " thirds: 18 buses (Arriva City, 2017) in " + GR),
    city("sor_nbg_18", "SOR_NBG_18", "SOR NBG 18",
         T.artic("SOR_NBG_18", "NBG 18",
                 f_(600000, 100, 75, 12, 23, 120, 2017, 9, "diesel", 0, 54),
                 f_(450000, 60, 75, 8, 17, 86, 2017, 5, "diesel", 265, 61)),
         [(A("Arriva City"), praha_rows(_nbg18, "A"))],
         "SOR NBG 18 (CNG; engine_type diesel, no smoke): 15 buses (Arriva City, 2017-2020)"
         " in " + GR),
    city("urbanway_12m_cng", "Urbanway_12M_CNG", "Iveco Urbanway 12M CNG",
         T.one("Urbanway_12M_CNG", "Urbanway 12M CNG", BUS,
               f_(800000, 95, 80, 12, 24, 135, 2015, 8, "diesel", 213, 56)),
         [(B("AD Střední Čechy, Arriva City"), praha_rows(_uw12cng_b, "B")),
          (A("ČSAD Střední Čechy"), praha_rows(_uw12cng_a, "A"))],
         "Iveco Urbanway 12M CNG (CNG; engine_type diesel, no smoke), the CNG fairing over the"
         " front two thirds: 9 buses (2018-2019) in " + RBW + " Two (ČSAD Střední Čechy,"
         " 2018) in " + GR),
    fam("crossway_le_line_13m", "Crossway_LE_Line_13M", "Iveco Crossway LE LINE 13M", BUS,
        f_(660000, 98, 100, 12, 27, 135, 2014, 9, "diesel", 265, 54, smoke=SMOKE),
        [(A("Arriva Střední Čechy"), "pid-a")],
        PCrosswayLELine13,
        "Iveco Crossway LE LINE 13M, tag axle: 2 buses (Arriva Střední Čechy, 2014) in " + GR),
    # ------------------------------------------------------------ repainted hand-drawn sheets
    sheet("rosero_first_xl", "Rosero_First_XL", "Rošero First FCLLI XL", MIDI,
          f_(300000, 38, 90, 6, 15, 82, 2021, 5, "diesel", 132, 54, smoke=SMOKE),
          [(A("Arriva City, Arriva Střední Čechy, Arriva autobusy, ČSAD Benešov, Kokořínský SOK,"
              " ČSAD Polkost, Lextrans, ZDAR, Lutan"),
            pid_repaint("vehicle-bus/praha/rosero_first/sprites/bila.png", [[7.0, 7.5, 8.0]],
                        [(0.30, 0.52), (0.70, 0.88)], (1.05, 2.35)))],
          "ROŠERO-P First FCLLI XL low-entry midibus on the Iveco Daily (and one XL CNG):"
          " 31 buses (2021-2026) in " + GR + " Drawn on the FCLLI sheet.",
          "VTPsim's Rošero First (the white Prague sheet, vehicle-bus/praha/rosero_first)"
          " repainted by odis_town.repaint, the PID columns by pid.pid_decal.", "VTPsim"),
    sheet("stratos_le_37", "Stratos_LE_37", "SKD Iveco Stratos LE 37", MIDI,
          f_(290000, 37, 90, 5, 15, 80, 2016, 5, "diesel", 132, 54, smoke=SMOKE),
          [(A("Lutan"),
            pid_repaint("vehicle-bus/praha/stratos_le_37/sprites/pidcervenomodrobila.png", [[7.0, 7.5, 8.0]],
                        [(0.30, 0.52), (0.70, 0.88)], (1.05, 2.35)))],
          "SKD Iveco Stratos LE 37 midibus: 1 bus (Lutan, 2016) in " + GR + " The trikolóra"
          " ones are the VZ-Praha object.",
          "VTPsim's Stratos LE 37 (the Prague sheet, vehicle-bus/praha/stratos_le_37)"
          " repainted by odis_town.repaint, the PID columns by pid.pid_decal.", "VTPsim"),
    sheet("irisbus_crossway_le_12_8m", "Irisbus_Crossway_LE_12_8M", "Irisbus Crossway LE 12,8M", BUS,
          f_(610000, 98, 100, 12, 25, 125, 2013, 9, "diesel", 243, 54, smoke=SMOKE),
          [(A("Arriva Střední Čechy"),
            pid_repaint("vehicle-bus/praha/crossway_le_12_8m/sprites/bila.png", [[12.0, 12.8, 13.5]],
                        [(0.20, 0.33), (0.66, 0.80)], (1.15, 2.50)))],
          "Irisbus Crossway LE 12,8M: 1 bus (Arriva Střední Čechy, 2013) in " + GR,
          "the white Prague Crossway LE 12,8M sheet (vehicle-bus/praha/crossway_le_12_8m)"
          " repainted by odis_town.repaint, the PID columns by pid.pid_decal.", "vojtechzicha"),
    sheet("dekstra_le_37", "Dekstra_LE_37", "Dekstra LE 37", MIDI,
          f_(300000, 37, 90, 5, 15, 80, 2019, 5, "diesel", 132, 54, smoke=SMOKE),
          [(A("Lamer, Lutan"),
            pid_repaint("vehicle-bus/iredo/dekstra_le_37/sprites/bila.png", [[7.0, 7.5, 8.0]],
                        [(0.28, 0.50), (0.68, 0.86)], (1.05, 2.35)))],
          "Dekstra LE 37 midibus: 3 buses (2019-2020) in " + GR,
          "VTPsim's Dekstra LE 37 (the IREDO white sheet, vehicle-bus/iredo/dekstra_le_37)"
          " repainted by odis_town.repaint, the PID columns by pid.pid_decal.", "VTPsim"),
    sheet("dekstra_le_37_cng", "Dekstra_LE_37_CNG", "Dekstra LE 37 L CNG", MIDI,
          f_(420000, 45, 80, 6, 16, 85, 2021, 5, "diesel", 125, 50),
          [(A("Kokořínský SOK, Lutan"),
            pid_repaint(dekstra_cng, [[7.0, 7.5, 8.0]], [(0.28, 0.50), (0.68, 0.86)], (1.05, 2.35)))],
          "Dekstra LE 37 L CNG (CNG; engine_type diesel, no smoke), the low CNG box: 4 buses"
          " (2021-2022) in " + GR,
          "VTPsim's Dekstra LE 37 (the IREDO white sheet) with the CNG box of odis.py,"
          " repainted by odis_town.repaint, the PID columns by pid.pid_decal.", "VTPsim"),
    sheet("scania_citywide_suburban_le_15m_cng", "Citywide_Suburban_LE_15M_CNG",
          "Scania Citywide Suburban LE 15M CNG", BUS,
          f_(900000, 120, 90, 14, 34, 170, 2019, 10, "diesel", 250, 55),
          [(A("Arriva Střední Čechy, Arriva City"),
            pid_repaint(scania_port("CZ-ODIS-ScaniaCitywideLE15M_Suburban-Green", [[13.5, 14.5, 15.5]]),
                        [[13.5, 14.5, 15.5]], [(0.16, 0.28), (0.62, 0.74)], (1.10, 2.45),
                        pods=[[(0.18, 0.55, 0.22, 0.95)]]))],
          "Scania Citywide Suburban LE 15M CNG (CNG; engine_type diesel, no smoke), three"
          " axles: 9 buses (2019) in " + GR,
          "VTPsim's pak128.cs Citywide LE 15M suburban (frozen in tools/busrender/src/odis/)"
          " ported by odis_town.port_native, repainted, the PID columns by pid.pid_decal.", "VTPsim"),
    sheet("scania_citywide_le_15m", "Citywide_LE_15M", "Scania Citywide LE 15M", BUS,
          f_(880000, 125, 85, 14, 33, 165, 2020, 10, "diesel", 250, 55, smoke=SMOKE),
          [(A("Lutan"),
            pid_repaint(scania_port("CZ-ODIS-ScaniaCitywideLE15M_Suburban-Green", [[13.5, 14.5, 15.5]]),
                        [[13.5, 14.5, 15.5]], [(0.16, 0.28), (0.62, 0.74)], (1.10, 2.45)))],
          "Scania Citywide LE 15M (diesel), three axles: 1 bus (Lutan, 2020) in " + GR,
          "VTPsim's pak128.cs Citywide LE 15M (frozen in tools/busrender/src/odis/) ported by"
          " odis_town.port_native, repainted, the PID columns by pid.pid_decal.", "VTPsim"),
    sheet("scania_citywide_le_12m", "Citywide_LE_12M", "Scania Citywide LE 12M", BUS,
          f_(780000, 95, 85, 12, 30, 148, 2019, 8, "diesel", 206, 55, smoke=SMOKE),
          [(A("ČSAD Polkost"),
            pid_repaint(scania_port("CZ-ODIS-ScaniaCitywideLE128M_Suburban-Green", [[11.5, 12.0, 12.5]]),
                        [[11.5, 12.0, 12.5]], [(0.20, 0.34), (0.66, 0.80)], (1.10, 2.45)))],
          "Scania Citywide LE 12M (diesel): 1 bus (ČSAD Polkost, 2019) in " + GR,
          "VTPsim's pak128.cs Citywide LE suburban (frozen in tools/busrender/src/odis/) ported"
          " by odis_town.port_native, repainted, the PID columns by pid.pid_decal.", "VTPsim"),
])


# ====================================================================== main
def main(argv):
    pv = None
    if "--preview" in argv:
        i = argv.index("--preview")
        pv = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
        os.makedirs(pv, exist_ok=True)
    do_yaml = "--yaml" in argv
    argv = [a for a in argv if a != "--yaml"]
    for key, f in FAMILIES.items():
        if argv and key not in argv and key.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, "vehicle-bus", *key.split("/"))
        os.makedirs(os.path.join(d, "sprites"), exist_ok=True)
        for slug, _, _, fn in f["liveries"]:
            rows = fn()
            T.save_sheet(rows, os.path.join(d, "sprites", slug + ".png"), f.get("allow", ()))
            if pv:
                T.preview(rows, os.path.join(pv, f"{key.replace('/', '-')}-{slug}.png"))
            print(f"vehicle-bus/{key}/sprites/{slug}.png  rows={len(rows)}")
        if do_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(T.yaml_text(f, "pid.py"))


if __name__ == "__main__":
    main(sys.argv[1:])
