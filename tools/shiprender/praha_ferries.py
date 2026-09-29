"""PID Prague ferry boats of 2026 (VZ-Praha-water), rendered with boatkit.py:

  vehicle-water/praha/naomi    Pražské Benátky Naomi type (P1 Břehule, P5 Břehouš,
                               P6 Ledňáček), true size, bold detail
  vehicle-water/praha/kazi     Pražské Benátky Kazi type (P2 Baba), true size
  vehicle-water/praha/holka_2  Prague Boats Holka 2 (P4), drawn at 1.2x

The size and detail level of each boat are the variants the user picked
(2026-09-29): `bold` = deeper plain canopy valance with a light top outline and
the top railing only; `scallop` (the fine variant) = a scalloped valance edge
and two railings. The 1.2x scale multiplies every length and height alike.

usage: python tools/shiprender/praha_ferries.py [family ...] [--preview DIR]
  writes vehicle-water/praha/<family>/sprites/<livery>.png; --preview also
  writes <family>.png: the 8 views on water tiles at 1x and 4x next to the
  native Ferry_yeu_128set (src/) and the DPP SOR NB 12 bus for scale.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from boatkit import Boat, build_row, save_sheet, T

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

# ---------------------------------------------------------------- palettes
PB = dict(  # Pražské Benátky: black hull, red deck, bottle-green canopy, varnished wheelhouse
    HULL=(0x1C, 0x1E, 0x22), GUNWALE=(0xC8, 0x42, 0x3E), DECK=(0xA8, 0x3A, 0x34),
    LETTER=(0xE6, 0xE6, 0xE2), POST=(0x20, 0x20, 0x22), RAIL=(0x26, 0x26, 0x28),
    CANOPY=(0x1F, 0x5A, 0x45), VALANCE=(0x16, 0x46, 0x35), CAN_EDGE_TOP=(0x3A, 0x7E, 0x64),
    WOOD=(0xA4, 0x58, 0x2A), FRAME=(0x6E, 0x2A, 0x14), CREAM=(0xE8, 0xE2, 0xD4),
    CAB_ROOF=(0x6E, 0x2A, 0x14), BENCH=(0x86, 0x50, 0x2C),
    BUOY_A=(0xD8, 0x30, 0x28), BUOY_B=(0xF2, 0xF0, 0xEC),
    STAFF=(0x5A, 0x3A, 0x22), FLAG_W=(0xF4, 0xF4, 0xF2), FLAG_R=(0xD7, 0x14, 0x1A), FLAG_B=(0x11, 0x45, 0x7E),
    CONSOLE=(0, 0, 0), CONSOLE_TOP=(0, 0, 0), CONSOLE_TEXT=(0, 0, 0),
)
PPS = dict(PB,  # Prague Boats Holka 2: blue pontoon, grey deck, blue canopy with white skirt
    HULL=(0x26, 0x5E, 0xAE), GUNWALE=(0x34, 0x36, 0x3A), DECK=(0xB4, 0xB2, 0xAA),
    LETTER=(0xE6, 0xE6, 0xE2), POST=(0xB6, 0xBA, 0xC0), RAIL=(0xA8, 0xAC, 0xB2),
    CANOPY=(0x4C, 0x86, 0xD0), VALANCE=(0xEC, 0xEE, 0xF0), CAN_EDGE_TOP=(0xEC, 0xEE, 0xF0),
    BENCH=(0x9E, 0x7C, 0x58), STAFF=(0x90, 0x94, 0x9A),
    CONSOLE=(0xEE, 0xEC, 0xE8), CONSOLE_TOP=(0x4A, 0x4E, 0x54), CONSOLE_TEXT=(0x1E, 0x4A, 0xA8),
)
LIFEBUOY_OR = (0xF0, 0x6A, 0x1E)
LAMP_GREEN = (0x2A, 0xB0, 0x4A)
WHITE = (0xF2, 0xF2, 0xF0)


def scaled(d, k):
    """scale every length of a parameter dict by k (positions and heights alike,
    so proportions stay true)"""
    def sc(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v * k
        if isinstance(v, tuple):
            return tuple(sc(x) if not isinstance(x, (tuple, set, str)) and not isinstance(x, bool) else x
                         for x in v)
        if isinstance(v, list):
            return [sc(x) for x in v]
        return v
    return {kk: (sc(v) if kk in SCALE_KEYS else v) for kk, v in d.items()}


SCALE_KEYS = {"L", "B", "deck", "hull", "can_s", "can_z", "can_over", "posts", "end_posts",
              "rail_s", "rail_in", "rails", "gates", "benches", "cabin", "win_z", "buoys",
              "names", "flag", "masts", "console", "console_text_z", "gw", "gw_side"}


# ---------------------------------------------------------------- Naomi
def naomi(k=1.0, bold=False):
    L, B, D = 8.5, 3.15, 0.55
    p = dict(
        L=L, B=B, deck=D,
        # rake: stern slightly, bow more (photo c34c: stem foot ~0.5 m aft of the top)
        hull=[(0.0, 0.18, 0.30, 0.55, 0.05), (0.18, 0.38, 0.12, 0.25, 0.0), (0.38, D, 0.0, 0.0, 0.0)],
        hull_low=None, gw=0.16, gw_side=0.0,
        can_s=(0.10, L - 0.10), can_z=(2.85, 3.05), can_over=0.05,
        posts=[0.25, 1.95, 3.65, 5.30, 7.00, L - 0.25], end_posts=[-(B / 2 - 0.1), 0.0, B / 2 - 0.1],
        rail_s=(0.18, L - 0.18), rail_in=0.08, rails=[0.50, 0.92], gates=[],
        # side benches + a central table aft of the wheelhouse
        benches=[(0.6, 4.9, B / 2 - 0.62, B / 2 - 0.16, D, D + 0.45),
                 (0.6, 4.9, -B / 2 + 0.16, -B / 2 + 0.62, D, D + 0.45),
                 (1.4, 4.2, -0.35, 0.35, D, D + 0.75)],
        # wheelhouse 62-83 % of the length, 1.5 m wide, up to the canopy
        cabin=(5.30, 7.00, -0.75, 0.75, 2.85), win_z=(1.05, 1.85),
        buoys=[(6.45, 0.95, ("right", "left"))],
        console=None, console_text_z=0,
        names=[(L - 0.95, L - 0.25, 0.30), (L - 2.10, L - 1.45, 0.30)],
        flag=(0.12, 3.45),
        masts=[(6.15, 0.0, 3.05, 3.55, WHITE)],
        lamps=[],
        scallop=not bold, can_edge=bold,
    )
    if bold:
        p["can_z"] = (2.75, 3.05)
        p["rails"] = [0.92]
    p = scaled(p, k)
    # buoy faces tuple was scaled as a tuple of strings: restore
    p["buoys"] = [(b[0], b[1], ("right", "left")) for b in p["buoys"]]
    return Boat(**PB, **p)


# ---------------------------------------------------------------- Kazi (Baba)
def kazi(k=1.0, bold=False):
    L, B, D = 11.2, 3.7, 0.70
    p = dict(
        L=L, B=B, deck=D,
        # naháč-style hull: strongly raked, raised bow (photo c33c), slight stern rake
        hull=[(0.0, 0.22, 0.35, 0.95, 0.05), (0.22, 0.46, 0.15, 0.50, 0.0), (0.46, D, 0.0, 0.12, 0.0),
              (D, D + 0.14, L - 0.95, 0.0, 0.0)],
        hull_low=None, gw=0.16, gw_side=0.0,
        can_s=(0.30, L - 0.30), can_z=(2.90, 3.10), can_over=0.05,
        posts=[0.40, 2.30, 4.20, 6.10, 8.00, 9.90, L - 0.40], end_posts=[-(B / 2 - 0.1), 0.0, B / 2 - 0.1],
        rail_s=(0.25, L - 0.35), rail_in=0.08, rails=[0.50, 0.92], gates=[],
        benches=[(0.8, 7.6, B / 2 - 0.62, B / 2 - 0.16, D, D + 0.45),
                 (0.8, 7.6, -B / 2 + 0.16, -B / 2 + 0.62, D, D + 0.45),
                 (1.4, 3.9, -0.40, 0.40, D, D + 0.75), (4.6, 7.1, -0.40, 0.40, D, D + 0.75)],
        # wheelhouse near the bow (15-27 % from the bow, photo c33c)
        cabin=(8.15, 9.55, -0.80, 0.80, 2.90), win_z=(1.05, 1.85),
        buoys=[(9.0, 0.95, ("right", "left"))],
        console=None, console_text_z=0,
        names=[(L - 0.90, L - 0.35, 0.42), (L - 3.10, L - 1.40, 0.42)],
        flag=(0.20, 3.55),
        masts=[(8.85, 0.0, 3.10, 3.65, WHITE)],
        lamps=[],
        scallop=not bold, can_edge=bold,
    )
    if bold:
        p["can_z"] = (2.80, 3.10)
        p["rails"] = [0.92]
    p = scaled(p, k)
    p["buoys"] = [(b[0], b[1], ("right", "left")) for b in p["buoys"]]
    return Boat(**PB, **p)


# ---------------------------------------------------------------- Holka 2
def holka(k=1.0, bold=False):
    L, B, D = 6.5, 2.6, 0.50
    p = dict(
        L=L, B=B, deck=D,
        # flat steel pontoon, rounded ends, dark bottom band (photos hk2c / hk4c)
        hull=[(0.0, 0.18, 0.30, 0.30, 0.15), (0.18, D, 0.0, 0.0, 0.0)],
        hull_low=(0.12, (0x14, 0x34, 0x66)), gw=0.12, gw_side=0.0,
        can_s=(0.05, L - 0.05), can_z=(2.35, 2.60), can_over=0.03,
        posts=[0.15, 1.70, 3.25, 4.80, L - 0.15], end_posts=[-(B / 2 - 0.08), B / 2 - 0.08],
        rail_s=(0.10, L - 0.10), rail_in=0.05, rails=[0.45, 0.90], gates=[],
        # back-to-back bench down the middle
        benches=[(1.0, 4.9, -0.45, 0.45, D, D + 0.45), (1.0, 4.9, -0.05, 0.05, D, D + 0.90)],
        cabin=None, win_z=(0, 0), buoys=[],
        # white helm console with "HOLKA 2" at the bow corner
        console=(5.45, 6.40, 0.05, B / 2 - 0.02, D + 1.05), console_text_z=0.62,
        names=[],
        flag=(0.10, 2.95),
        masts=[],
        lamps=[],
        scallop=False, can_edge=bold,
    )
    if bold:
        p["can_z"] = (2.25, 2.60)
    p = scaled(p, k)
    p["hull_low"] = (0.12 * k, (0x14, 0x34, 0x66))
    b = Boat(**PPS, **p)
    L, B, D = b.L, b.B, b.deck
    # orange lifebuoy on the stern railing, green lamp on the canopy at the bow
    b.lamps = [(0.10 * k, -0.55 * k, D + 0.62 * k, LIFEBUOY_OR), (0.10 * k, -0.30 * k, D + 0.62 * k, LIFEBUOY_OR),
               (L - 0.15 * k, B / 2 - 0.1 * k, 2.60 * k + 0.25 * k, LAMP_GREEN)]
    return b


# family dir -> (livery colour, boat)
FAMILIES = {
    "vehicle-water/praha/naomi": ("pbcernocervena", lambda: naomi(1.0, True)),
    "vehicle-water/praha/kazi": ("pbcernocervena", lambda: kazi(1.0, False)),
    "vehicle-water/praha/holka_2": ("ppsmodrobila", lambda: holka(1.2, True)),
}

# ---------------------------------------------------------------- preview
WATER, WATER_EDGE = (54, 96, 140), (62, 106, 150)
GRASS, GRASS_EDGE = (96, 128, 64), (106, 138, 74)
NATIVE = os.path.join(HERE, "src", "Ferry_yeu_128set.png")
BUS = os.path.join(REPO, "vehicle-bus", "dpp", "sor_nb_12", "sprites", "dppcervenobila.png")


def _tile(fill, edge):
    im = Image.new("RGB", (128, 128), (40, 44, 48))
    d = ImageDraw.Draw(im)
    d.polygon([(64, 64), (128, 96), (64, 128), (0, 96)], fill=fill, outline=edge)
    return np.array(im)


def _strip(sheet, fill=WATER, edge=WATER_EDGE):
    bg = _tile(fill, edge)
    out = []
    for c in range(8):
        cell = sheet[0:128, c * 128:(c + 1) * 128]
        t = bg.copy()
        m = np.any(cell != T, axis=2)
        t[m] = cell[m]
        out.append(t)
    return np.concatenate(out, axis=1)


def preview(sheet, path):
    rows = [_strip(sheet)]
    if os.path.exists(NATIVE):
        rows.append(_strip(np.array(Image.open(NATIVE).convert("RGB"))))
    if os.path.exists(BUS):
        rows.append(_strip(np.array(Image.open(BUS).convert("RGB")), GRASS, GRASS_EDGE))
    one = np.concatenate(rows, axis=0)
    z = np.concatenate(rows[:2], axis=0)[:, :]
    z = np.array(Image.fromarray(z).resize((z.shape[1] * 4, z.shape[0] * 4), Image.NEAREST))
    pad = np.full((one.shape[0], z.shape[1] - one.shape[1], 3), 250, np.uint8)
    gap = np.full((8, z.shape[1], 3), 250, np.uint8)
    Image.fromarray(np.concatenate([np.concatenate([one, pad], axis=1), gap, z], axis=0)).save(path)


def main():
    args = sys.argv[1:]
    pv = None
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
        os.makedirs(pv, exist_ok=True)
    known = {f.split("/")[-1] for f in FAMILIES}
    for a in args:
        if a not in known:
            raise SystemExit(f"unknown family {a!r}; known: {sorted(known)}")
    for fam, (color, make) in FAMILIES.items():
        name = fam.split("/")[-1]
        if args and name not in args:
            continue
        sd = os.path.join(REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        path = os.path.join(sd, color + ".png")
        sheet = save_sheet([build_row(make())], path)
        print("wrote", os.path.relpath(path, REPO))
        if pv:
            preview(sheet, os.path.join(pv, name + ".png"))


if __name__ == "__main__":
    main()
