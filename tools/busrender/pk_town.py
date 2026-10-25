"""Town (MHD) buses of Pardubický kraj outside DP města Pardubice: repaint or
copy existing sheets and write the family.yaml files.

    python tools/busrender/pk_town.py [family ...] [--yaml] [--preview DIR]

Packages (the KHK rule, 2026-10-04): town lines integrated in IREDO go into
VZ-IREDO-bus (Chrudim and Přelouč, run by ARRIVA autobusy); the others get
their own MHD<Town> pak (Ústí nad Orlicí: ČSAD Ústí nad Orlicí; Litomyšl and
Polička: Zlatovánek). Svitavy, Česká Třebová, Lanškroun, Vysoké Mýto, Hlinsko
and Moravská Třebová have no fixed-line MHD. Scope: the October 2026 fleets
(Pardubický kraj research of 2026-10-20); reserves left out.

Every sheet starts from a repo sheet of the same body (copied or repainted by
odis_town.repaint, shading kept); decals are drawn on the fitted box.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import odis_town as T                                                   # noqa: E402

WHITE = (0xF2, 0xF2, 0xF0)
WHITE_TOP = (0xF6, 0xF6, 0xF4)
STRIPE_RED = (0xC8, 0x14, 0x1E)     # Arriva's "white with a red stripe"
LIT_RED = (0xC8, 0x32, 0x3A)        # the Litomyšl wrap's lower band
NAVY = (0x1E, 0x2E, 0x6E)           # MHD Ústí nad Orlicí lettering
BLACK = (0x1A, 0x1A, 0x1C)
W_ZONES = {"white": (WHITE, WHITE_TOP)}


def z_light(c):
    """every light neutral pixel (the white or grey body) and the PID reds"""
    if T.hexc(c) in T.H.SPECIAL:
        return None
    if T.neutral(c, 0xA8, tol=18):
        return "white"
    r, g, b = c
    if r > 0xA0 and g < 0x50 and b < 0x50:
        return "white"
    return None


def stripe_decal(colour, rows=2, zmin=0.90, base=None):
    """decals(): a stripe `rows` pixels tall under the window band of both sides:
    per side column, the rows below its lowest dark pixel above zmin metres
    (door glazing runs lower, so door columns stay unpainted)"""
    def draw(o, paint, geo, d, r):
        if base is not None:
            o = base(o, paint, geo, d, r)
        if d not in T.SIDE:
            return o
        side = (geo["face"] == 4) | (geo["face"] == 5)
        dark = (o.max(axis=2) < 0x60) & ~T.is_bg(o)
        o = o.copy()
        for x in range(128):
            ys = [y for y in range(128) if side[y, x] and dark[y, x] and float(geo["z"][y, x]) > zmin]
            if not ys:
                continue
            y0 = max(ys) + 1
            f = float(geo["frac"][min(127, y0), x])
            if not 0.04 < f < 0.97:
                continue
            for dy in range(rows):
                T.put(o, paint, x, y0 + dy, colour)
        return o
    return draw


def cant_dots(colour, f0, f1, base=None):
    """decals(): a dotted line (lettering at this scale) in the body row just
    above the window band, between body fractions f0 and f1"""
    def draw(o, paint, geo, d, r):
        if base is not None:
            o = base(o, paint, geo, d, r)
        if d not in T.SIDE:
            return o
        side = (geo["face"] == 4) | (geo["face"] == 5)
        dark = (o.max(axis=2) < 0x60) & ~T.is_bg(o)
        o = o.copy()
        for x in range(128):
            ys = [y for y in range(127) if side[y, x] and dark[y, x]]
            if not ys:
                continue
            y = min(ys) - 1
            if y < 0 or not paint[y, x]:
                continue
            f = float(geo["frac"][y, x])
            if f0 <= f < f1 and x % 2 == 0:
                o[y, x] = colour
        return o
    return draw


def temsa_white():
    """the praha_small.py TEMSA MD9 LE render with the PID scheme A minus its red
    blocks (grey), repainted white, the Chrudim lettering over the rear windows"""
    import praha_small as PS
    sp = PS.mk(PS.TEMSA, livery=dict(kind="A", blocks_r=[], blocks_l=[], bands=[], rub=0.62, zcant=2.76))
    rows = [[np.array(t)[:, :, :3].copy() for t in PS.build(sp)]]
    return T.repaint(rows, z_light, W_ZONES, [[8.8, 9.3, 9.8]], cant_dots(BLACK, 0.45, 0.95))


def citaro_le_white():
    """the praha_man.py Citaro C2 LE Ü render repainted white"""
    import praha_man as PM
    row = PM.build_row(PM.CitaroC2LEU, "A", None, label="citaro_c2_le_u")
    rows = [[np.array(t)[:, :, :3].copy() for t in row]]
    return T.repaint(rows, z_light, W_ZONES, L12)


def copy_rows(src):
    return lambda: T.load_rows(src)


def repaint(src, zones, Ls, decals=None, zone_of=z_light, recol=None):
    return lambda: T.repaint(T.load_rows(src), zone_of, zones, Ls, decals, None, None, recol)


L12 = [[11.5, 12.0, 12.5]]

# ====================================================================== families
f_ = T.f_
IREDO = ("IREDO", "IREDO", "IREDO")
USTI = ("MHDUstiNadOrlici", "MHD Ústí nad Orlicí", "MHD Ústí nad Orlicí")
LITOMYSL = ("MHDLitomysl", "MHD Litomyšl", "MHD Litomyšl")
POLICKA = ("MHDPolicka", "MHD Polička", "MHD Polička")
BUS, MIDI = T.BUS, T.MIDI
MINI = ("minibus", "minibus")


def fam(key, agency, type_, name, role, flds, livs, note, sprite, copyright):
    return (key, dict(agency=agency, type=type_, name=(name, name), copyright=copyright,
                      vehicles=T.one(type_, name, role, flds), liveries=livs,
                      note=note, sprite=sprite, allow=()))


FAMILIES = dict([
    # ------------------------------------------------------------ MHD Chrudim (IREDO)
    fam("iredo/urbanway_12m_cng", IREDO, "Urbanway_12M_CNG", "Iveco Urbanway 12M CNG", BUS,
        f_(800000, 95, 80, 12, 24, 135, 2016, 8, "diesel", 213, 56, retire=2050),
        [("kladnobilocervena", "MAD Kladno white-red · ARRIVA autobusy (MHD Chrudim)",
          "MAD Kladno, bílo-červená · ARRIVA autobusy (MHD Chrudim)",
          copy_rows("vehicle-bus/mhd-kladno/urbanway_12m_cng/sprites/kladnobilocervena.png"))],
        "Iveco Urbanway 12M CNG (CNG: engine_type diesel, no smoke), doors 2-2-2. MHD\n"
        "Chrudim, ARRIVA autobusy: 64676 and 64677 (2016, ex MAD Kladno, here since\n"
        "2-3/2025), still in the MAD Kladno white with the red stripe.",
        "Lubak91's Urbanway 12M CNG, the MHD Kladno sheet as is\n"
        "(vehicle-bus/mhd-kladno/urbanway_12m_cng).", "Lubak91"),
    fam("iredo/conecto_lf", IREDO, "Conecto_LF", "Mercedes-Benz Conecto LF", BUS,
        f_(600000, 100, 75, 11, 23, 118, 2016, 8, "diesel", 220, 54, smoke="Diesel_small"),
        [("bilacervenypruh", "white with a red stripe · ARRIVA autobusy (MHD Chrudim)",
          "bílá s červeným pruhem · ARRIVA autobusy (MHD Chrudim)",
          repaint("vehicle-bus/mhd-kolin/conecto_lf/sprites/bila.png", W_ZONES, L12,
                  stripe_decal(STRIPE_RED, zmin=0.5)))],
        "Mercedes-Benz Conecto LF, doors 2-2-2. MHD Chrudim, ARRIVA autobusy: 62168 (2016,\n"
        "since 4/2026), white with a red stripe under the windows.",
        "VTPsim's Conecto LF (the white Kolín sheet, vehicle-bus/mhd-kolin/conecto_lf)\n"
        "repainted by odis_town.repaint, the red stripe by pk_town.py.", "VTPsim"),
    fam("iredo/temsa_md9_le", IREDO, "TEMSA_MD9_LE", "TEMSA MD9 LE", MIDI,
        f_(420000, 60, 80, 8, 18, 92, 2021, 7, "diesel", 160, 54, smoke="Diesel_small"),
        [("chrudimbila", "MHD Chrudim white · ARRIVA autobusy", "MHD Chrudim, bílá · ARRIVA autobusy",
          temsa_white)],
        "TEMSA MD9 LE midibus, 9.3 m. MHD Chrudim, ARRIVA autobusy: 100901 (2021, since\n"
        "2/2023), white with the town's \"MĚSTSKÁ AUTOBUSOVÁ DOPRAVA CHRUDIM\" lettering over\n"
        "the rear windows (a dotted line here).",
        "original box render (vojtechzicha): the TEMSA MD9 LE body of\n"
        "tools/busrender/praha_small.py, white, the lettering by pk_town.py.", "vojtechzicha"),
    # ------------------------------------------------------------ regional one-offs
    fam("iredo/citaro_c2_le_u", IREDO, "Citaro_C2_LE_U", "Mercedes-Benz Citaro C2 LE Ü", BUS,
        f_(640000, 90, 100, 11, 24, 120, 2017, 8, "diesel", 220, 54, smoke="Diesel_small"),
        [("bilapk", "white, Pardubický kraj · CAR-TOUR", "bílá, Pardubický kraj · CAR-TOUR",
          citaro_le_white)],
        "Mercedes-Benz Citaro C2 LE Ü low-entry interurban, 12.1 m, doors 1-2-0.\n"
        "Pardubický kraj 2026: CAR-TOUR 1 (2017, here since 1/2024, Holicko lines\n"
        "650600 / 650601), kraj white, no KHK sticker.",
        "original box render (vojtechzicha): praha_man.CitaroC2LEU of\n"
        "tools/busrender/praha_man.py, repainted white by pk_town.py.", "vojtechzicha"),
    # ------------------------------------------------------------ MHD Přelouč (IREDO)
    fam("iredo/sor_bn_8_5", IREDO, "SOR_BN_8_5", "SOR BN 8,5", MIDI,
        f_(420000, 60, 75, 8, 17, 86, 2016, 6, "diesel", 160, 54, smoke="Diesel_small"),
        [("bila", "white · ARRIVA autobusy (MHD Přelouč)", "bílá · ARRIVA autobusy (MHD Přelouč)",
          copy_rows("vehicle-bus/mhd-trutnov/sor_bn_8_5/sprites/bila.png"))],
        "SOR BN 8,5 low-floor midibus. MHD Přelouč (line 655101, integrated in IREDO),\n"
        "ARRIVA autobusy: 72237 (2017) and the ex-demonstrator 71754 (reserve), white.",
        "the white Trutnov sheet as is (vehicle-bus/mhd-trutnov/sor_bn_8_5): SorBN85 of\n"
        "tools/busrender/iredo_models.py on the common SOR base of 2026-10-24.", "vojtechzicha"),
    # ------------------------------------------------------------ own town paks
    fam("mhd-usti-nad-orlici/rosero_first", USTI, "Rosero_First", "Rošero First FCLLI", MIDI,
        f_(290000, 33, 90, 5, 15, 80, 2018, 5, "diesel", 132, 54, retire=2050, smoke="Diesel_small"),
        [("mhdusti", "white, MHD Ústí nad Orlicí lettering · ČSAD Ústí nad Orlicí",
          "bílá s grafikou MHD Ústí nad Orlicí · ČSAD Ústí nad Orlicí",
          repaint("vehicle-bus/iredo/rosero_first/sprites/bilapk.png", W_ZONES, [[7.0, 7.5, 8.0]],
                  cant_dots(NAVY, 0.15, 0.85))),
         ("bila", "white · ČSAD Ústí nad Orlicí", "bílá · ČSAD Ústí nad Orlicí",
          copy_rows("vehicle-bus/iredo/rosero_first/sprites/bilapk.png"))],
        "Rošero-P First FCLLI midibus on the Iveco Daily. MHD Ústí nad Orlicí (line 705100,\n"
        "not in IREDO), ČSAD Ústí nad Orlicí 2026: 80504 (2018) and 114960 (2023) white\n"
        "with the dark-blue \"Městská hromadná doprava\" and the town arms over the side\n"
        "windows (a dotted line here); 114240 (2023, ex MHD Říčany, since 9/2025) white.",
        "VTPsim's Rošero First (the IREDO white sheet without the KHK sticker,\n"
        "vehicle-bus/iredo/rosero_first), the lettering by pk_town.py.", "VTPsim"),
    fam("mhd-litomysl/rosero_first", LITOMYSL, "Rosero_First", "Rošero First FCLEI", MIDI,
        f_(280000, 30, 90, 5, 15, 78, 2019, 5, "diesel", 132, 54, retire=2050, smoke="Diesel_small"),
        [("litomysl", "Litomyšl red-white · Zlatovánek", "Litomyšl, červeno-bílá · Zlatovánek",
          repaint("vehicle-bus/iredo/rosero_first/sprites/bilapk.png", W_ZONES, [[7.0, 7.5, 8.0]],
                  T.skirt_decal(LIT_RED, 1.05)))],
        "Rošero-P First FCLEI midibus. MHD Litomyšl (line 685010, weekdays, not in IREDO),\n"
        "Zlatovánek: 88952 (2019), the town wrap: white upper body, red lower band with\n"
        "the white \"Litomyšl\" lettering.",
        "VTPsim's Rošero First (the IREDO white sheet, vehicle-bus/iredo/rosero_first)\n"
        "repainted by odis_town.repaint with the red lower band of skirt_decal.", "VTPsim"),
    fam("mhd-policka/iveco_daily_50c15", POLICKA, "Iveco_Daily_50C15", "Iveco Daily 50C15", MINI,
        f_(160000, 19, 90, 3, 12, 60, 2014, 5, "diesel", 110, 66, retire=2050, smoke="Diesel_small"),
        [("sedametaliza", "grey metallic · Zlatovánek", "šedá metalíza · Zlatovánek",
          copy_rows("vehicle-bus/mhd-nova-paka/iveco_daily_50c13/sprites/stribrna.png"))],
        "Iveco Daily 50C15 minibus. MHD Polička (lines 685001-685003, not in IREDO),\n"
        "Zlatovánek: 51776 (ex RUBAN, since 9/2022), grey metallic with the town's\n"
        "\"městská doprava\" lettering (not drawn). The Renault Master reserve is left out.",
        "the Iveco Daily 50C13 render of vehicle-bus/mhd-nova-paka (same silver-grey van at\n"
        "this scale) as is.", "vojtechzicha"),
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
                fh.write(T.yaml_text(f, "pk_town.py"))


if __name__ == "__main__":
    main(sys.argv[1:])
