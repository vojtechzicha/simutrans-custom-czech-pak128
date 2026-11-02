"""Buses of the neighbouring regions that work PID lines in Středočeský kraj:
render the sprite sheets and write the family.yaml of every family.

    python tools/busrender/regions.py [family ...] [--yaml] [--preview DIR]

Packaging (owner, 2026-11-02): one pak per region, like VZ-IREDO / VZ-ODIS,
one object per type x livery shared by every operator that runs it; the
operator appears only in the livery display name. A plain white bus uses the
existing white object (VZ-IREDO / VZ-DPPraha) and a PID grey-red one the
VZ-PID object; these paks hold only the regions' and operators' own paint.

    idol/     agency IDOL   -> VZ-IDOL-bus     Liberecký kraj (IDOL)
    jikord/   agency JIKORD -> VZ-JIKORD-bus   Jihočeský kraj (IDESKA)
    duk/      agency DUK    -> VZ-DUK-bus      Ústecký kraj (DÚK)

Scope: the buses the PID live map showed on the twelve Středočeský okres
sheets on 2026-11-02 (fleet desk request of simutrans-timetable-4d), paint
checked on seznam-autobusu.cz the same day.

Bodies and liveries are those of iredo_models.py / iredo_coachmodels.py (the
coach pipeline, the low shape), with the liveries and the few new bodies
below. No KHK sticker on any of them.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import iredo_models as M                       # noqa: E402
import iredo_coachmodels as CM                 # noqa: E402
from iredo_models import BLACK, Sh             # noqa: E402
from rj_buses import row_for                   # noqa: E402
from rj_buscommon import save_rows, preview    # noqa: E402
from iredo import fields, BUS, MIDI            # noqa: E402

WHITE = (0xF2, 0xF2, 0xF0)


def _decal(bus, x, k, right, x0, top, fig, colours):
    """a pixel decal laid out in screen columns from real x0 (its front end),
    reading left to right as seen on both sides; top = its top row"""
    r = top - k
    if not 0 <= r < len(fig):
        return None
    w = len(fig[0]) * bus.pw()
    if right:
        c = bus.colidx(x, x0 + w, backwards=True)
    else:
        c = bus.colidx(x, x0)
    row = fig[r]
    if 0 <= c < len(row) and row[c] != ".":
        return colours[row[c]]
    return None


def sill(bus, x):
    band = bus.band_at(x)
    return band[0] if band else bus.R_BAND0


# ====================================================================== liveries
class Idol(M.Livery):
    """IDOL (Liberecký kraj): white, the red IDOL ring with 'idol' and the red
    'Liberecký kraj' stripes logo under the windows behind the front door, a
    red IDOL mark on the lower front (left) and rear. BusLine LK 270 (photo
    seznam-autobusu 433880), 258 (432066 / 432067); ČSAD Liberec 643 / 777
    ('červený polep IDOL'). No KHK sticker."""
    slug = "idol"
    sticker = False
    RED = (0xD7, 0x1F, 0x26)
    # as seen, front end on the left: 'Liberecký kraj' stripes, gap, ring + 'idol'
    LOGO = ["r.r.....rr.rr.r",
            ".r.r...r..rr.rr"]

    def side(self, bus, x, k, right):
        top = sill(bus, x) - 2
        x0 = bus.axles[0] + 0.45
        return _decal(bus, x, k, right, x0, top, self.LOGO, {"r": self.RED})

    def front(self, bus, v, k):
        return self.RED if k == 3 and -0.95 <= v < -0.55 else None

    def rear(self, bus, v, k):
        return self.RED if k == 3 and 0.50 <= v < 0.90 else None


class Ideska(M.Livery):
    """IDESKA (Jihočeský kraj, 2026): dark petrol green body and roof, the
    glazing band black up to the roof edge, a bright green stroke across the
    upper glazing over the rear axle that drops to a green bar at the rear
    corner, white IDESKA lettering on the lower side, the lower front petrol
    green under a black band. ČSAD AUTOBUSY České Budějovice 17271 (Evadys
    13M, 2026, photo seznam-autobusu 453150)."""
    slug = "ideska"
    sticker = False
    body = (0x0A, 0x62, 0x64)
    roof = (0x1C, 0x78, 0x76)
    ac = (0x1C, 0x78, 0x76)
    seam = (0x08, 0x50, 0x52)
    cant = True
    GREEN = (0x4E, 0xB0, 0x3E)
    disp = (0x62, 0xD6, 0x4A)                           # green LED destination display
    TEXT = ["w.ww.ww.ww.w.w.ww",
            "w.ww.ww..w.ww..ww"]

    def side(self, bus, x, k, right):
        L = bus.real_len
        band = bus.band_at(x)
        k0, k1 = band if band else (bus.R_BAND0, bus.R_TOP)
        # the stroke (a foil over the upper glazing on the bus) drawn on the cant
        # over the rear axle, and the green bar down the rear corner
        if k >= k1:
            return self.GREEN if 0.58 * L <= x < 0.80 * L else BLACK
        if x >= L - 1.15 and 1 <= k < k0 - 1:
            return self.GREEN
        x0 = bus.axles[1] - 0.6 - len(self.TEXT[0]) * bus.pw()
        return _decal(bus, x, k, right, x0, k0 - 2, self.TEXT, {"w": WHITE})

    def front(self, bus, v, k):
        return WHITE if k == 3 and abs(v) < 0.30 else None

    def rear(self, bus, v, k):
        return self.GREEN if 3 <= k <= 5 and v < -0.60 else None


class Busem(M.Livery):
    """BUSEM (ČSAD AUTOBUSY České Budějovice's brand before IDESKA): white with
    the blue 'busem' lettering and its blue-yellow-red mark on the lower rear
    side and the blue web address on the rear. 17231 (photo seznam-autobusu
    273658)."""
    slug = "busem"
    sticker = False
    BLUE = (0x1F, 0x4E, 0x9A)
    YELLOW = (0xF2, 0xC2, 0x1A)
    RED = (0xD4, 0x22, 0x2A)
    LOGO = ["y.bb.b.b.bb.bb.bbb",
            "r.bb.bbb.bb.bb.b.b"]

    def side(self, bus, x, k, right):
        x0 = bus.real_len - 1.35 - len(self.LOGO[0]) * bus.pw()
        return _decal(bus, x, k, right, x0, sill(bus, x) - 2, self.LOGO,
                      {"b": self.BLUE, "y": self.YELLOW, "r": self.RED})

    def rear(self, bus, v, k):
        return self.BLUE if k == 3 and abs(v) < 0.80 else None


class DukZelena(M.Livery):
    """DÚK (Doprava Ústeckého kraje) green: green body, lighter green roof,
    black glazing band, the black windscreen surround down to the lamps on the
    front. DSÚK 12908 (Otokar Vectio U LE, 2023, photos seznam-autobusu
    368238, 444644); the 'Na výlet' advert band left out."""
    slug = "dukzelena"
    sticker = False
    body = (0x4A, 0xAC, 0x2C)
    roof = (0x62, 0xBE, 0x44)
    ac = (0x62, 0xBE, 0x44)
    seam = (0x3C, 0x92, 0x24)
    disp = (0xF4, 0xF4, 0xF0)                           # white LED displays (Bustec)

    def rear(self, bus, v, k):
        return None


for _lv in (Idol, Ideska, Busem, DukZelena):
    M.LIVERIES[_lv.slug] = _lv


# ====================================================================== bodies
class CrosswayPro12(M.CrosswayLine):
    """Iveco Crossway PRO 12M: the LINE 12M body with the PRO's high window
    line, drawn as the LINE 12M with fixed windows (as CrosswayPro13)."""


class CrosswayLine108(M.CrosswayLine):
    """Iveco Crossway LINE 10,8M: high floor, doors 1-1-0, the middle door
    between the axles; the LE LINE 10,8M's length and axles."""
    real_len = 10.8
    axles = (2.60, 7.70)
    DOORS = ((0.30, 1.28, "hf"), (5.85, 6.80, "hf"))
    BAND = ((0.0, 10.8, 6, 11),)
    AC = (2.3, 5.4)

    def pillars(self, right):
        if right:
            return (2.62, 4.10, 5.60, 7.05, 8.55, 9.75)
        return (2.62, 4.10, 5.60, 7.10, 8.60, 9.85)


class IntouroL(CM.MercedesIntegroL):
    """Mercedes-Benz Intouro III L: 13.1 m, tag axle, doors 1-2-0 (the double
    middle door ahead of the drive axle), the Integro II L body with the
    Intouro face. BusLine LK 258 (2024, photos seznam-autobusu 432066 /
    432067)."""
    DOORS = ((0.30, 1.25, "hf"), (6.40, 7.60, "hf"))


class Evadys13(CM.IvecoEvadys):
    """Iveco Evadys 13M: 12.96 m, two axles, wheelbase 7.07 m (Iveco data
    sheet). 17271 shows no middle door on its right side (photo
    seznam-autobusu 453150), so doors 1-0-0."""
    real_len = 12.96
    axles = (2.66, 9.73)
    BAND = ((0.0, 12.96, 7, 12),)
    DOORS = ((0.30, 1.25, "hf"),)
    AC = (6.9, 10.8)

    def pillars(self, right):
        if right:
            return (2.60, 4.70, 6.80, 8.90, 11.00)
        return (2.60, 4.70, 6.80, 8.90, 11.00)

    def seams(self, right):
        return (4.3, 6.4, 10.6)


class VectioFace:
    """Otokar Vectio U LE front: the tall windscreen with the display behind
    its top, a black band carrying the OTOKAR letters under it, the lower
    front in body colour with the lamps at the corners (photo 368238)."""
    WS = M.SCREEN
    WS_HI = M.SCREEN_HI

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            return getattr(self.lv, "disp", M.LED) if av < 0.9 else BLACK
        if k >= 5:
            if av > self.W2 - 0.07:
                return BLACK
            return self.WS_HI if k == top - 2 else self.WS
        if k == 4:
            return Sh(M.CHROME) if av < 0.30 else BLACK
        if d is not None:
            return Sh(d)
        if k == 3:
            return Sh(self.lv.body)
        if k == 2:
            return M.HEAD if av > self.W2 - 0.45 else Sh(self.lv.body)
        if k == 1:
            return M.PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class VectioULE(VectioFace, M.CrosswayLELine108):
    """Otokar Vectio U LE: low-entry midibus, 9.27 m (Otokar data sheet),
    doors 1-2-0 (the double door between the axles, just ahead of the rear
    wheel), the black glazing band, the A/C over the front half of the roof.
    DSÚK 12908 / 12940 / 12942 / 12943 (2023, photos seznam-autobusu 368238,
    444644)."""
    real_len = 9.27
    axles = (2.15, 6.60)
    DOORS = ((0.30, 1.20, "le"), (4.25, 5.45, "le"))
    BAND = ((0.0, 9.27, 6, 11),)
    AC = (2.0, 4.6)

    def pillars(self, right):
        if right:
            return (2.40, 3.65, 6.00, 7.50, 8.60)
        return (2.40, 3.75, 5.10, 6.45, 7.80, 8.75)

    def seams(self, right):
        return (3.4, 7.6) if right else (1.4, 3.2, 5.0, 7.6)


# ====================================================================== families
IDOL = ("IDOL", "IDOL", "IDOL", "vehicle-bus/idol")
JIKORD = ("JIKORD", "IDESKA", "IDESKA", "vehicle-bus/jikord")
DUK = ("DUK", "DÚK", "DÚK", "vehicle-bus/duk")

LIVERY = {
    "idol": ("white, IDOL", "bílá, IDOL"),
    "ideska": ("IDESKA petrol green", "IDESKA, tmavě zelená se zelenými pruhy"),
    "busem": ("white, busem", "bílá, busem"),
    "dukzelena": ("DÚK green", "DÚK, zelená"),
}


def fam(region, model, type_, name, role, liveries, flds, note):
    return dict(region=region, model=model, type=type_, name=name, role=role,
                liveries=liveries, fields=flds, note=note)


FAMILIES = {
    # ------------------------------------------------------------ IDOL
    "idol/crossway_line_13m": fam(IDOL, M.CrosswayLine13, "Crossway_Line_13M", "Iveco Crossway LINE 13M", BUS,
        [("idol", "BusLine LK, ČSAD Liberec")],
        fields(650000, 88, 100, 12, 265, 9, 2018),
        "Iveco Crossway LINE 13M high-floor interurban, tag axle, doors 1-2-0. On PID\n"
        "lines (Mladoboleslavsko, Mělnicko) 2026: BusLine LK 270 (2025, photo\n"
        "seznam-autobusu 433880) and ČSAD Liberec, white with the IDOL logos."),
    "idol/crossway_pro_12m": fam(IDOL, CrosswayPro12, "Crossway_Pro_12M", "Iveco Crossway PRO 12M", BUS,
        [("idol", "BusLine LK, ČSAD Liberec")],
        fields(640000, 80, 100, 11, 265, 8, 2015),
        "Iveco Crossway PRO 12M high-floor interurban, doors 1-2-0. On PID lines\n"
        "(Mladoboleslavsko) 2026: BusLine LK 305 (2017), ČSAD Liberec 643 (2015, ex ČAD\n"
        "Blansko), white with the IDOL logos. KAD's plain white one is the VZ-DPPraha\n"
        "white object."),
    "idol/intouro_iii_l": fam(IDOL, IntouroL, "Intouro_III_L", "Mercedes-Benz Intouro III L", BUS,
        [("idol", "BusLine LK")],
        fields(700000, 96, 100, 13, 260, 9, 2024),
        "Mercedes-Benz Intouro III L high-floor intercity, 13.1 m, tag axle, doors\n"
        "1-2-0. On PID lines (Mladoboleslavsko, line 720) 2026: BusLine LK 258 / 271 /\n"
        "272 (2024), white with the IDOL logos (photos seznam-autobusu 432066 / 432067)."),
    "idol/irisbus_crossway_12_8m": fam(IDOL, M.IrisbusCrossway128, "Irisbus_Crossway_12_8M",
        "Irisbus Crossway 12,8M", BUS,
        [("idol", "ČSAD Liberec")],
        fields(590000, 86, 100, 12, 243, 9, 2006),
        "Irisbus Crossway 12,8M high-floor interurban. On PID lines (line 345) 2026:\n"
        "ČSAD Liberec 777 (2012, ex Diendorfer / ABAS), white with the IDOL logos."),
    # ------------------------------------------------------------ JIKORD
    "jikord/evadys_13m": fam(JIKORD, Evadys13, "Evadys_13M", "Iveco Evadys 13M", BUS,
        [("ideska", "ČSAD AUTOBUSY České Budějovice")],
        fields(740000, 80, 100, 13, 265, 9, 2026),
        "Iveco Evadys 13M high-floor intercity coach, 12.96 m, two axles. On PID lines\n"
        "(Příbramsko) 2026: ČSAD AUTOBUSY České Budějovice 17271 / 17272 (2026,\n"
        "Prachatice), the IDESKA scheme (photo seznam-autobusu 453150)."),
    "jikord/crossway_line_10_8m": fam(JIKORD, CrosswayLine108, "Crossway_Line_10_8M",
        "Iveco Crossway LINE 10,8M", BUS,
        [("busem", "ČSAD AUTOBUSY České Budějovice")],
        fields(580000, 75, 100, 10, 210, 7, 2017),
        "Iveco Crossway LINE 10,8M high-floor interurban, doors 1-2-0. On PID lines\n"
        "(Příbramsko) 2026: ČSAD AUTOBUSY České Budějovice 17231 / 17233 (2017,\n"
        "Písek), white with the busem lettering (photo seznam-autobusu 273658)."),
    # ------------------------------------------------------------ DÚK
    "duk/vectio_u_le": fam(DUK, VectioULE, "Vectio_U_LE", "Otokar Vectio U LE", MIDI,
        [("dukzelena", "DSÚK")],
        fields(520000, 62, 90, 9, 220, 6, 2023),
        "Otokar Vectio U LE low-entry midibus, 9.27 m, doors 1-2-0, Cummins B6.7 220 kW.\n"
        "On PID lines (Kladensko, Rakovnicko; lines 708 and others) 2026: DSÚK 12908 /\n"
        "12940 / 12942 / 12943 (2023, Louny), DÚK green (photos seznam-autobusu\n"
        "368238, 444644)."),
}


def yaml_text(key, f):
    agency, en, cs, _ = f["region"]
    m = f["model"]
    lines = [
        f"agency: {agency}",
        f'type: "{f["type"]}"',
        "# Sprites carry their own lane placement (body footprint on the median of",
        "# native pak128.cs 12 m buses), so no extra shift.",
        "image_offset: [0, 0]",
        "# Windows light up at night only while passengers are aboard.",
        "windows_lit_when_loaded: true",
        "copyright: vojtechzicha",
        "",
        "display:",
        f'  agency_en: "{en}"',
        f'  agency_cs: "{cs}"',
        f'  family_en: "{f["name"]}"',
        f'  family_cs: "{f["name"]}"',
        "",
    ]
    lines += ["# " + ln for ln in f["note"].split("\n")]
    lines += [
        f"# Sprite: original box-model render (vojtechzicha), model {m.__name__} of",
        f"# tools/busrender/{m.__module__}.py; regenerate with tools/busrender/regions.py.",
        "# Generated by tools/busrender/regions.py --yaml.",
        "",
        "vehicles:",
        f'  - id: "{f["type"]}"',
        f'    display_id: "{f["name"]}"',
        f'    role_en: "{f["role"][0]}"',
        f'    role_cs: "{f["role"][1]}"',
        "    row: 0",
        "    prev: []",
        "    next: []",
        "    fields:",
    ]
    for k, v in f["fields"].items():
        lines.append(f"      {k}: {v}")
    lines += ["", "liveries:"]
    for slug, ops in f["liveries"]:
        len_, lcs = LIVERY[slug]
        lines += [f"  - color: {slug}",
                  f'    name_en: "{len_} · {ops}"',
                  f'    name_cs: "{lcs} · {ops}"']
    return "\n".join(lines) + "\n"


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    do_yaml = "--yaml" in argv
    argv = [a for a in argv if a != "--yaml"]
    for key, f in FAMILIES.items():
        if argv and key not in argv and key.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, f["region"][3], key.split("/")[-1])
        os.makedirs(os.path.join(d, "sprites"), exist_ok=True)
        rows_all = []
        for slug, _ in f["liveries"]:
            rows = [row_for(f["model"], slug)]
            rows_all += rows
            save_rows(rows, os.path.join(d, "sprites", f"{slug}.png"))
        if do_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(yaml_text(key, f))
        print("wrote", key, [s for s, _ in f["liveries"]])
        if prev:
            os.makedirs(prev, exist_ok=True)
            preview(rows_all, os.path.join(prev, f"{key.replace('/', '-')}.png"), z=4)


if __name__ == "__main__":
    main(sys.argv[1:])
