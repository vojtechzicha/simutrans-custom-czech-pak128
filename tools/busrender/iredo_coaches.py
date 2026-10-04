"""IREDO (Královéhradecký kraj) regional coaches and SOR ICN: render the
sprite sheets and write the family.yaml of each vehicle-bus/iredo/<family>
listed in FAMILIES below.

    python tools/busrender/iredo_coaches.py [family ...] [--yaml] [--preview DIR]

Without --yaml only the sheets are written; with --yaml the family.yaml files
are (re)generated from FAMILIES too (review the diff). Same packaging rules
as tools/busrender/iredo.py (whose fields() / fam() / yaml_text() this
driver reuses); bodies are in iredo_coachmodels.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import iredo as I                              # noqa: E402
import iredo_coachmodels as CM                 # noqa: E402  (registers its liveries)
from iredo import fields, fam, BUS, MIDI       # noqa: E402
from rj_buses import row_for                   # noqa: E402
from rj_buscommon import save_rows, preview    # noqa: E402

FAMDIR = I.FAMDIR

# liveries this driver adds to iredo.LIVERY (paint name; operators per family)
LIVERY = {}
for _k, _v in LIVERY.items():
    I.LIVERY.setdefault(_k, _v)

FAMILIES = {
    # ------------------------------------------------------------ Setra
    "setra_s_415_le_business": fam("SetraS415LE", "Setra_S_415_LE_business", "Setra S 415 LE business", BUS,
        [("bila", "BusLine KHK")],
        fields(680000, 90, 100, 11, 260, 8, 2014),
        "Setra S 415 LE business low-entry interurban, 12.18 x 2.55 x 3.13 m, doors 1-2-0,\n"
        "OM 936 260 kW. KHK 2026: BusLine KHK 4 (white, Hradec Králové), CDS Náchod's\n"
        "two left in 2025."),
    "setra_s_418_le_business": fam("SetraS418LE", "Setra_S_418_LE_business", "Setra S 418 LE business", BUS,
        [("cds", "CDS Náchod")],
        fields(780000, 112, 100, 14, 290, 10, 2016),
        "Setra S 418 LE business low-entry interurban, 14.64 m, three axles (tag axle),\n"
        "doors 1-2-0, OM 470 290 kW. KHK 2026: CDS Náchod 3 (2020, Náchod 2, Broumov 1)."),
    # ------------------------------------------------------------ Iveco / Irisbus
    "evadys_12m": fam("IvecoEvadys", "Evadys_12M", "Iveco Evadys 12M", BUS,
        [("bila", "BusLine KHK")],
        fields(700000, 72, 100, 12, 265, 8, 2014),
        "Iveco Evadys 12M high-floor intercity coach, 12.11 x 2.55 x 3.5 m, doors 1-1-0,\n"
        "Cursor 9 265 kW, ~55 seats. KHK 2026: BusLine KHK 1 (2019, Jičín)."),
    "irisbus_arway_12m": fam("IrisbusArway", "Irisbus_Arway_12M", "Irisbus Arway 12M", BUS,
        [("bila", "KAD")],
        fields(580000, 78, 100, 11, 243, 8, 2006),
        "Irisbus Arway 12M high-floor intercity, 12.0 x 2.55 x 3.3 m, doors 1-1-0, Cursor 8\n"
        "243 kW. KHK 2026: KAD 1 (2013); BusLine KHK ran one (2009) until 8/2021."),
    # ------------------------------------------------------------ Karosa
    "karosa_axer": dict(fam("KarosaAxerTown", "Karosa_Axer", "Karosa Axer", BUS,
        [("bila", "L&Z Line")],
        fields(520000, 80, 100, 11, 213, 8, 2002),
        "Karosa Axer 12M / 12,8M (C 956.1074 / .1076) high-floor intercity, one object\n"
        "drawn as the 12M (12.0 x 2.55 x 3.18 m, doors 2-2-0, Cursor 8 213 kW). KHK:\n"
        "L&Z Line 8H5 0256 (borrowed, since 4/2026) runs MHD Nová Paka (outside IREDO,\n"
        "so no kraj sticker on the rear window)."),
        dir="vehicle-bus/mhd-nova-paka", agency="MHDNovaPaka", agency_name="MHD Nová Paka"),
    # ------------------------------------------------------------ Irizar
    "irizar_i4_14m": fam("IrizarI4", "Irizar_i4_14M", "Irizar i4 14M", BUS,
        [("bila", "KAD")],
        fields(800000, 78, 100, 14, 302, 10, 2011),
        "Irizar i4 14M (Scania K 6x2*4) high-floor intercity coach, 13.97 x 2.55 x 3.5 m,\n"
        "three axles (tag axle), doors 1-1-0, ~63 seats, 302 kW. KHK 2026: KAD 7\n"
        "(2022-2025; 5 white, 2 in PID livery)."),
    # ------------------------------------------------------------ SOR ICN
    "sor_icn_12_3": fam("SorICN", "SOR_ICN_12_3", "SOR ICN 12,3", BUS,
        [("bila", "BusLine KHK")],
        fields(650000, 92, 100, 11, 235, 8, 2022),
        "SOR ICN 12,3 low-entry interurban (new-generation SOR), 12.33 x 2.55 x 3.15 m,\n"
        "doors 1-2-0, FPT NEF 6.7 ~235 kW. KHK 2026: BusLine KHK 2 (2024, Hradec Králové)."),
    "sor_icn_10_5": fam("SorICN105", "SOR_ICN_10_5", "SOR ICN 10,5", BUS,
        [("bila", "KAD")],
        fields(590000, 80, 100, 10, 210, 7, 2022),
        "SOR ICN 10,5 low-entry interurban, 10.6 m, doors 1-2-0. KHK 2026: KAD 2 (2023);\n"
        "Transdev Čechy's 4 (2022) run for BusLine Pardubicko."),
    "sor_icn_9_5": fam("SorICN95", "SOR_ICN_9_5", "SOR ICN 9,5", MIDI,
        [("cds", "CDS Náchod")],
        fields(540000, 73, 90, 9, 184, 7, 2023),
        "SOR ICN 9,5 low-entry midibus, 9.55 x 2.525 x 3.12 m, doors 1-2-0, FPT NEF 6.7\n"
        "184 kW. KHK 2026: CDS Náchod 4 (2025, Náchod 3, Broumov 1)."),
}


def yaml_text(folder, f):
    t = I.yaml_text(folder, f)
    if f.get("agency"):
        t = t.replace("agency: IREDO", f"agency: {f['agency']}")
        t = t.replace('agency_en: "IREDO"', f'agency_en: "{f["agency_name"]}"')
        t = t.replace('agency_cs: "IREDO"', f'agency_cs: "{f["agency_name"]}"')
    t = t.replace("tools/busrender/iredo_models.py; regenerate with tools/busrender/iredo.py.",
                  "tools/busrender/iredo_coachmodels.py; regenerate with\n"
                  "# tools/busrender/iredo_coaches.py.")
    return t.replace("Generated by tools/busrender/iredo.py --yaml.",
                     "Generated by tools/busrender/iredo_coaches.py --yaml.")


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
        cls = getattr(CM, f["model"])
        d = os.path.join(I.REPO, f["dir"], folder) if f.get("dir") else os.path.join(FAMDIR, folder)
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
