"""IREDO (Královéhradecký kraj) regional buses: render the sprite sheets and
write the family.yaml of every vehicle-bus/iredo/<family>.

    python tools/busrender/iredo.py [family ...] [--yaml] [--preview DIR]

Without --yaml only the sheets are written; with --yaml the family.yaml files
are (re)generated from FAMILIES too (review the diff).

Bodies and liveries: iredo_models.py (coach pipeline, see its docstring).
Packaging (user, 2026-10-04): agency IREDO -> VZ-IREDO-bus.pak, one object per
type x livery shared by every operator that runs it; the operator appears only
in the livery display name. The kraj has no uniform IREDO paint: each contract
operator keeps its own scheme, and all carry the kraj sticker panel on the rear
window (drawn on every body).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import iredo_models as M                       # noqa: E402
from rj_buses import row_for                   # noqa: E402
from rj_buscommon import save_rows, preview    # noqa: E402

FAMDIR = os.path.join(REPO, "vehicle-bus", "iredo")

# livery slug -> (name_en, name_cs) of the paint; operators are appended per family
LIVERY = {
    "bila": ("white", "bílá"),
    "transdev": ("white with the red figure", "bílá s červenou postavou"),
    "cds": ("yellow", "žlutá"),
    "ptransport": ("yellow-red", "žluto-červená"),
    "ptransportzluta": ("yellow with red bumpers", "žlutá s červenými nárazníky"),
    "buslinezelena": ("green", "zelená"),
    "buslinezlutozelena": ("yellow-green", "žlutozelená"),
}

# size classes: default fields (scaled like the DPP / Praha families: 12 m =
# length 8, ~10.5 m = 7, ~9.5 m = 7, ~8.5 m = 6, 13 m = 9, 14.5 m = 10)
BASE = {"waytype": "road", "freight": "Passagiere", "intro_month": 1,
        "retire_year": 2060, "retire_month": 12, "engine_type": "diesel"}


def fields(cost, payload, speed, weight, power, length, intro, run=None, fixed=None,
           gear=54, smoke="Diesel_small", **kw):
    f = dict(cost=cost, payload=payload, speed=speed, weight=weight,
             runningcost=run or round(cost / 25000),
             fixed_cost=fixed or round(cost / 4900),
             intro_year=intro)
    f.update(BASE)
    f.update(dict(length=length, power=power, gear=gear))
    if smoke:
        f["smoke"] = smoke
    f.update(kw)
    order = ["cost", "payload", "speed", "weight", "runningcost", "fixed_cost",
             "intro_year", "intro_month", "retire_year", "retire_month", "waytype",
             "freight", "length", "engine_type", "power", "gear", "smoke"]
    return {k: f[k] for k in order if k in f}


def fam(model, type_, name, role, liveries, flds, note):
    return dict(model=model, type=type_, name=name, role=role, liveries=liveries,
                fields=flds, note=note)


BUS = ("bus", "autobus")
MIDI = ("midibus", "midibus")

FAMILIES = {
    # ------------------------------------------------------------ SOR
    "sor_cn_12_3": fam("SorCN", "SOR_CN_12_3", "SOR CN 12,3", BUS,
        [("bila", "BusLine KHK, KAD"), ("transdev", "Transdev Čechy, KAD")],
        fields(620000, 90, 100, 11, 235, 8, 2020),
        "SOR CN 12,3 low-entry interurban, 12.3 m, doors 1-2-0, ~49 seats + standing,\n"
        "Cummins 6.7 l ~235 kW. KHK 2026: BusLine KHK 30 (white), Transdev Čechy 35\n"
        "(white + red figure), KAD 4."),
    "sor_cn_10_5": fam("SorCN105", "SOR_CN_10_5", "SOR CN 10,5", BUS,
        [("bila", "BusLine KHK, KAD"), ("transdev", "Transdev Čechy"), ("cds", "CDS Náchod"),
         ("buslinezelena", "BusLine KHK"), ("buslinezlutozelena", "BusLine KHK")],
        fields(560000, 78, 100, 10, 210, 7, 2011),
        "SOR CN 10,5 low-entry interurban, 10.6 m. KHK 2026: BusLine KHK 26 (17 white,\n"
        "7 yellow-green, 2 green), Transdev Čechy 33, CDS Náchod 5, KAD 2."),
    "sor_cn_9_5": fam("SorCN95", "SOR_CN_9_5", "SOR CN 9,5", MIDI,
        [("bila", "BusLine KHK"), ("transdev", "Transdev Čechy"), ("cds", "CDS Náchod"),
         ("buslinezelena", "BusLine KHK")],
        fields(520000, 68, 90, 9, 180, 7, 2011),
        "SOR CN 9,5 low-entry midibus, 9.5 m. KHK 2026: BusLine KHK 11, Transdev\n"
        "Čechy 11, CDS Náchod 5."),
    "sor_cn_8_5": fam("SorCN85", "SOR_CN_8_5", "SOR CN 8,5", MIDI,
        [("bila", "KAD")],
        fields(470000, 58, 90, 8, 160, 6, 2010),
        "SOR CN 8,5 low-entry midibus, 8.5 m. KHK 2026: KAD 1."),
    "sor_cng_12_3": fam("SorCNG", "SOR_CNG_12_3", "SOR CNG 12,3", BUS,
        [("buslinezelena", "BusLine KHK")],
        fields(660000, 88, 100, 12, 228, 8, 2015, smoke=None),
        "SOR CNG 12,3: the CN 12,3 on compressed gas, tank fairing over the front roof.\n"
        "KHK 2026: BusLine KHK 2 (green). CNG: engine_type diesel (upstream\n"
        "convention), no smoke."),
    "sor_c_10_5": fam("SorC105", "SOR_C_10_5", "SOR C 10,5", BUS,
        [("bila", "BusLine KHK, Transdev Čechy"), ("transdev", "Transdev Čechy"), ("cds", "CDS Náchod")],
        fields(520000, 75, 100, 10, 200, 7, 2005),
        "SOR C 10,5 high-floor interurban, 10.5 m, doors 1-1-0. KHK 2026: BusLine KHK 2,\n"
        "Transdev Čechy 3, CDS Náchod 2."),
    "sor_c_9_5": fam("SorC95", "SOR_C_9_5", "SOR C 9,5", MIDI,
        [("cds", "CDS Náchod"), ("bila", "KAD")],
        fields(480000, 65, 90, 9, 180, 7, 2005),
        "SOR C 9,5 high-floor midibus. KHK 2026: CDS Náchod 2, KAD 1."),
    "sor_lc_12": fam("SorLC12", "SOR_LC_12", "SOR LC 12", BUS,
        [("cds", "CDS Náchod")],
        fields(600000, 70, 100, 11, 220, 8, 2009),
        "SOR LC 12 long-distance high-floor bus. KHK 2026: CDS Náchod 2."),
    "sor_lc_10_5": fam("SorLC105", "SOR_LC_10_5", "SOR LC 10,5", BUS,
        [("cds", "CDS Náchod")],
        fields(540000, 60, 100, 10, 200, 7, 2009),
        "SOR LC 10,5 long-distance high-floor bus. KHK 2026: CDS Náchod 1."),
    # ------------------------------------------------------------ Iveco
    "crossway_le_line_12m": fam("CrosswayLELine", "Crossway_LE_Line_12M", "Iveco Crossway LE LINE 12M", BUS,
        [("bila", "BusLine KHK, KAD"), ("transdev", "Transdev Čechy, KAD"), ("cds", "CDS Náchod"),
         ("ptransport", "P-transport"), ("ptransportzluta", "P-transport"), ("buslinezelena", "BusLine KHK")],
        fields(640000, 92, 100, 11, 243, 8, 2014),
        "Iveco Crossway LE LINE 12M low-entry interurban (2013+ front), doors 2-2-0.\n"
        "KHK 2026: BusLine KHK 23 (white, 8 green), Transdev Čechy 23, CDS Náchod 31,\n"
        "P-transport 7, KAD 6."),
    "crossway_le_line_10_8m": fam("CrosswayLELine108", "Crossway_LE_Line_10_8M", "Iveco Crossway LE LINE 10,8M", BUS,
        [("bila", "BusLine KHK"), ("buslinezelena", "BusLine KHK"), ("cds", "CDS Náchod"),
         ("ptransport", "P-transport")],
        fields(590000, 80, 100, 10, 210, 7, 2014),
        "Iveco Crossway LE LINE 10,8M. KHK 2026: BusLine KHK 7 (4 white, 3 green), CDS\n"
        "Náchod 3, P-transport 1."),
    "crossway_le_line_14_5m": fam("CrosswayLELine145", "Crossway_LE_Line_14_5M", "Iveco Crossway LE LINE 14,5M", BUS,
        [("bila", "BusLine KHK"), ("transdev", "Transdev Čechy"), ("cds", "CDS Náchod")],
        fields(720000, 110, 100, 14, 265, 10, 2018),
        "Iveco Crossway LE LINE 14,5M, three axles (tag axle). KHK 2026: BusLine KHK 4,\n"
        "Transdev Čechy 4, CDS Náchod 1."),
    "crossway_line_12m": fam("CrosswayLine", "Crossway_Line_12M", "Iveco Crossway LINE 12M", BUS,
        [("cds", "CDS Náchod"), ("ptransport", "P-transport"), ("bila", "KAD")],
        fields(600000, 80, 100, 11, 243, 8, 2015),
        "Iveco Crossway LINE 12M high-floor interurban, doors 1-1-0. KHK 2026: CDS\n"
        "Náchod 19, P-transport 6, KAD 1."),
    "crossway_line_13m": fam("CrosswayLine13", "Crossway_Line_13M", "Iveco Crossway LINE 13M", BUS,
        [("bila", "BusLine KHK"), ("ptransport", "P-transport")],
        fields(650000, 88, 100, 12, 265, 9, 2018),
        "Iveco Crossway LINE 13M, three axles. KHK 2026: BusLine KHK 1, P-transport 1."),
    "crossway_pro_13m": fam("CrosswayPro13", "Crossway_Pro_13M", "Iveco Crossway PRO 13M", BUS,
        [("bila", "BusLine KHK")],
        fields(680000, 85, 100, 12, 265, 9, 2017),
        "Iveco Crossway PRO 13M, three axles. KHK 2026: BusLine KHK 4."),
    "crossway_le_city_12m": fam("CrosswayLECity12", "Crossway_LE_City_12M", "Iveco Crossway LE CITY 12M", BUS,
        [("transdev", "Transdev Čechy")],
        fields(630000, 100, 85, 11, 243, 8, 2014),
        "Iveco Crossway LE CITY 12M, three double doors. KHK 2026: Transdev Čechy 1."),
    "irisbus_crossway_le_12m": fam("IrisbusCrosswayLE", "Irisbus_Crossway_LE_12M", "Irisbus Crossway LE 12M", BUS,
        [("transdev", "Transdev Čechy"), ("bila", "Transdev Čechy"), ("ptransport", "P-transport")],
        fields(600000, 92, 100, 11, 243, 8, 2007),
        "Irisbus Crossway LE 12M (2007-2013 front). KHK 2026: Transdev Čechy 6 (4 with\n"
        "the figure), P-transport 1."),
    "irisbus_crossway_le_10_8m": fam("IrisbusCrosswayLE108", "Irisbus_Crossway_LE_10_8M", "Irisbus Crossway LE 10,8M", BUS,
        [("cds", "CDS Náchod")],
        fields(560000, 80, 100, 10, 210, 7, 2009),
        "Irisbus Crossway LE 10,8M. KHK 2026: CDS Náchod 1."),
    "irisbus_crossway_12m": fam("IrisbusCrossway", "Irisbus_Crossway_12M", "Irisbus Crossway 12M", BUS,
        [("bila", "BusLine KHK"), ("ptransport", "P-transport"), ("ptransportzluta", "P-transport")],
        fields(560000, 80, 100, 11, 243, 8, 2006),
        "Irisbus Crossway 12M high-floor interurban (2006-2013). KHK 2026: BusLine KHK 5,\n"
        "P-transport 2."),
    "irisbus_crossway_12_8m": fam("IrisbusCrossway128", "Irisbus_Crossway_12_8M", "Irisbus Crossway 12,8M", BUS,
        [("bila", "BusLine KHK, Transdev Čechy"), ("ptransport", "P-transport")],
        fields(590000, 86, 100, 12, 243, 9, 2006),
        "Irisbus Crossway 12,8M high-floor interurban. KHK 2026: BusLine KHK 1, Transdev\n"
        "Čechy 1, P-transport 1."),
}


def yaml_text(folder, f):
    lines = [
        "agency: IREDO",
        f'type: "{f["type"]}"',
        "# Sprites carry their own lane placement (body footprint on the median of",
        "# native pak128.cs 12 m buses), so no extra shift.",
        "image_offset: [0, 0]",
        "# Windows light up at night only while passengers are aboard.",
        "windows_lit_when_loaded: true",
        "copyright: vojtechzicha",
        "",
        "display:",
        '  agency_en: "IREDO"',
        '  agency_cs: "IREDO"',
        f'  family_en: "{f["name"]}"',
        f'  family_cs: "{f["name"]}"',
        "",
    ]
    lines += ["# " + l for l in f["note"].split("\n")]
    lines += [
        f"# Sprite: original box-model render (vojtechzicha), model {f['model']} in",
        "# tools/busrender/iredo_models.py; regenerate with tools/busrender/iredo.py.",
        "# Generated by tools/busrender/iredo.py --yaml.",
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
        en, cs = LIVERY[slug]
        lines += [f"  - color: {slug}",
                  f'    name_en: "{en} · {ops}"',
                  f'    name_cs: "{cs} · {ops}"']
    return "\n".join(lines) + "\n"


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    do_yaml = "--yaml" in argv
    argv = [a for a in argv if a != "--yaml"]
    for folder in (argv or list(FAMILIES)):
        f = FAMILIES[folder]
        cls = getattr(M, f["model"])
        d = os.path.join(FAMDIR, folder)
        os.makedirs(os.path.join(d, "sprites"), exist_ok=True)
        rows_all = []
        for slug, _ in f["liveries"]:
            rows = [row_for(cls, slug)]
            rows_all += rows
            save_rows(rows, os.path.join(d, "sprites", f"{slug}.png"))
        if do_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(yaml_text(folder, f))
        print("wrote", folder, [s for s, _ in f["liveries"]])
        if prev:
            os.makedirs(prev, exist_ok=True)
            preview(rows_all, os.path.join(prev, f"{folder}.png"), z=4)


if __name__ == "__main__":
    main(sys.argv[1:])
