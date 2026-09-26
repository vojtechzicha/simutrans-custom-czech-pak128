"""ČD RegioPanter families (440, 640, 640.1, 640.2, 650, 650.2, 690.2) and the
JMK Moravia 530 / 550 on the shared Panter body (panter.py): Najbrt 2, Najbrt
1.2, PID grey-red, Plzeňský kraj (650.2), ČD green-blue-white (690.2 battery
units) and Jihomoravský kraj (Moravia).

  python tools/railpaint/cd_panter.py [family ...] [--preview DIR]

writes vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png (FAMILIES below
gives the car types per sheet row and the liveries). The livery descriptions
(photo research, September 2026) are in liveries.md. A livery is a zone dict
(see panter.py); livery(name, car) picks the dict for a sheet row.
"""
import os, sys, shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import panter
from palette import (SAPPHIRE, SKY, LGREY, YELLOW, PID_GREY, PID_RED, PID_BLACK, PID_DOOR, PID_DGREY, dk)
import palette as P
from panto_xfer import transplant

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

# ------------------------------------------------------------------ colours
CANT = (228, 232, 236)            # cant rail / roof edge (near white)
HOOD = (236, 239, 242)            # GRP cab hood
N_SKIN = (200, 205, 210)          # roof skin
N2_BOX = (52, 84, 136)            # sapphire roof boxes (top face; walls darker)
N12_BOX = (98, 102, 106)          # dark-grey roof boxes (walls ~RAL 7022)
N12_VISOR = (74, 79, 87)
CAM = ((30, 32, 36), "flat")
GLASS_DARK = (panter.CABGLASS, "flat")
WHITE_MARK = (238, 240, 242)


def wedge_n2(ctx):
    """N2: dark surround of the cab side window, plain sky blue below it."""
    return SAPPHIRE if ctx["k"] <= 3 else SKY


def visor(cap, hood):
    """Cab front above the windscreen: the top two rows are the hood's GRP
    edge, the rest the visor / roof cap with the camera box."""
    return lambda ctx: hood if ctx["k"] <= 1 else cap


def najbrt(version):
    n12 = version == "1.2"
    liv = {
        "ROOF_EDGE": CANT,
        "S_CANT": CANT, "S_TOP": SKY, "S_BODY": SKY, "S_FIRST": YELLOW,
        "S_LINE": SAPPHIRE, "S_GREY": LGREY, "S_VAL": LGREY if n12 else SAPPHIRE,
        "S_DOOR": SAPPHIRE, "S_HOOD": HOOD, "S_CABWIN": GLASS_DARK,
        "S_WEDGE": SAPPHIRE if n12 else wedge_n2,
        "E_CANT": CANT, "E_TOP": SKY, "E_BODY": SKY, "E_LINE": SAPPHIRE, "E_GREY": LGREY,
        "E_VAL": LGREY if n12 else SAPPHIRE,
        "E_HOOD": HOOD, "E_VISOR": visor(N12_VISOR if n12 else SAPPHIRE, HOOD), "E_CAM": CAM,
        "WSCREEN": GLASS_DARK, "E_WIN": GLASS_DARK,
        "E_PANEL": SKY, "E_SKIRT": SAPPHIRE, "E_BEAM": YELLOW,
        "_roof": (N_SKIN, N12_BOX if n12 else N2_BOX),
        # white ČD logo behind the cab / on the front panel (1-2 px)
        "_end_marks": [(0.5, 0.14, 10, WHITE_MARK)],
    }
    return liv


def najbrt_marks(car):
    """Side ČD logo on the sky blue behind the cab."""
    if car == "A":
        return [(0.79, 0.03, 3, WHITE_MARK)]
    if car == "B":
        return [(0.21, 0.03, 3, WHITE_MARK)]
    return []


# ------------------------------------------------------------------ PID
STRIPE_W = 6                      # pure-side px (~2.2 m) of a door-side red block


def pid_red(ur, g):
    w = STRIPE_W * g.px
    for u0, u1 in g.doors:
        cab_side = (g.cab == "front" and u0 > 0.5) or (g.cab == "rear" and u1 < 0.5)
        if cab_side:
            # from the door to the rear edge of the hood (its top slope)
            if g.cab == "front" and u1 + 0.5 * g.px < ur < g.hood_top_u - 0.5 * g.px:
                return True
            if g.cab == "rear" and g.hood_top_u + 0.5 * g.px < ur < u0 - 0.5 * g.px:
                return True
        elif u1 < 0.5:
            if u0 - w - 0.5 * g.px <= ur < u0 - 0.5 * g.px:
                return True
        else:
            if u1 + 0.5 * g.px < ur <= u1 + w + 0.5 * g.px:
                return True
    return False


def pid_side(ctx):
    z, k, g, ur = ctx["zone"], ctx["k"], ctx["geo"], ctx["ur"]
    if z == "S_BODY":
        return PID_BLACK
    red = pid_red(ur, g)
    if z == "S_TOP" and red and g.cab and k == 1:
        cab_block = (g.cab == "front" and ur > 0.5) or (g.cab == "rear" and ur < 0.5)
        if cab_block:
            return YELLOW                      # 1st class at both cab ends
    return PID_RED if red else PID_GREY


def pid_panel(ctx):
    return PID_RED if ctx["u"] > 0.5 else PID_GREY


def pid_skirt(ctx):
    return PID_GREY if ctx["k"] <= 13 else PID_DGREY


PID = {
    "ROOF_EDGE": PID_GREY,
    "S_CANT": pid_side, "S_TOP": pid_side, "S_BODY": pid_side, "S_LINE": pid_side, "S_GREY": pid_side,
    "S_VAL": pid_side, "S_FIRST": YELLOW, "S_DOOR": PID_DOOR, "S_HOOD": dk(PID_GREY, 1.05),
    "S_CABWIN": GLASS_DARK, "S_WEDGE": PID_BLACK,
    "E_CANT": PID_GREY, "E_TOP": PID_GREY, "E_BODY": PID_BLACK, "E_LINE": PID_GREY, "E_GREY": PID_GREY,
    "E_VAL": PID_GREY,
    "E_HOOD": dk(PID_GREY, 1.05), "E_VISOR": visor((56, 62, 70), dk(PID_GREY, 1.05)), "E_CAM": CAM, "WSCREEN": GLASS_DARK,
    "E_WIN": GLASS_DARK, "E_PANEL": pid_panel, "E_SKIRT": pid_skirt, "E_BEAM": YELLOW,
    "_roof": (PID_GREY, dk(PID_DGREY, 1.35)),
    # white ČD logo on the red front block, red "pid" on the grey half
    "_end_marks": [(0.72, 0.1, 10, WHITE_MARK), (0.28, 0.1, 10, PID_RED)],
}


GANG_DARK = (38, 40, 44)          # gangway frame / bellows, coupler recess


# ------------------------------------------------------------------ helpers
def d_cab(ctx):
    """Pure-side px (72 per car) from the cab nose (None on a middle car)."""
    g, ur = ctx["geo"], ctx["ur"]
    if ur < 0 or not g.cab:
        return None
    return (1 - ur) / g.px if g.cab == "front" else ur / g.px


def d_end(ctx):
    """Pure-side px from the nearer end of the car (cab nose or coupling)."""
    g, ur = ctx["geo"], ctx["ur"]
    if ur < 0:
        return 36.0
    return min(ur, 1 - ur) / g.px


# ------------------------------------------------------------------ Plzeňský kraj
# The IDPK design as measured for the Arriva 650 (tools/railrender/
# regiopanter_idpk.py; the same ex-ČD units): key per (u, h), u = side px
# behind the cab nose (72 px = 26.45 m), h = row under the cant stripe.
#   g green / w white / y yellow swoosh, L white lettering (PLZEŇSKÝ KRAJ)
def idpk_design(first):
    d = {}

    def put(pts, k):
        for u, h in pts:
            d[(u, h)] = k

    put([(3, 6), (4, 6), (5, 5), (6, 5), (7, 4), (8, 4), (13, 3), (13, 2), (14, 2), (15, 2),
         (16, 2), (17, 2), (18, 3), (19, 3)], "g")
    put([(5, 6), (6, 6), (7, 5), (8, 5)], "w")
    put([(9, 6), (10, 6), (11, 6), (12, 6)], "L")
    if first:
        put([(u, 1) for u in range(8, 20)], "y")      # 1st-class top bar hood -> door 1
    else:
        put([(u, 1) for u in range(11, 17)], "y")
    put([(25, 6), (25, 5), (25, 4), (26, 3), (27, 2), (28, 1)], "g")
    put([(27, 3), (28, 2), (29, 1)], "w")
    put([(28, 3), (29, 2), (30, 1)], "y")
    put([(45, 1), (44, 2), (43, 3), (40, 4), (40, 5), (40, 6)], "g")
    put([(44, 1), (43, 2), (42, 3)], "w")
    put([(43, 1), (42, 2), (41, 3)], "y")
    put([(70, 6), (69, 6), (68, 6), (67, 6), (66, 6), (65, 6), (64, 5), (63, 5), (62, 5),
         (61, 5), (60, 5), (59, 5), (58, 5), (57, 4), (57, 3), (57, 2), (56, 1), (55, 1)], "g")
    put([(63, 6), (62, 6), (61, 6), (60, 6), (59, 6), (58, 6)], "y")
    return d


IDPK_KEY = {"g": P.IDPK_GREEN, "w": P.IDPK_WHITE, "y": P.IDPK_YELLOW, "L": P.IDPK_LETTER}
IDPK_D = {"A": idpk_design(True), "B": idpk_design(False)}


def idpk_side(ctx):
    z, k = ctx["zone"], ctx["k"]
    if z == "S_DOOR":
        return P.IDPK_DOOR
    if k <= 0:
        return P.IDPK_WHITE
    if k >= 7:
        return P.IDPK_SKIRT
    d = d_cab(ctx)
    if d is not None:
        key = IDPK_D["A" if ctx["geo"].cab == "front" else "B"].get((int(round(d)), k))
        if key:
            return IDPK_KEY[key]
    return P.IDPK_BLUE


SIDE_ZONES = ("S_CANT", "S_TOP", "S_BODY", "S_LINE", "S_GREY", "S_VAL", "S_FIRST", "S_WEDGE", "S_DOOR")
PLZEN = {z: idpk_side for z in SIDE_ZONES}
PLZEN.update({
    "ROOF_EDGE": P.IDPK_ROOF_EDGE, "S_HOOD": P.IDPK_WHITE, "S_CABWIN": GLASS_DARK,
    "E_CANT": P.IDPK_WHITE, "E_TOP": P.IDPK_BLUE, "E_BODY": P.IDPK_BLUE, "E_LINE": P.IDPK_BLUE,
    "E_GREY": P.IDPK_SKIRT, "E_VAL": P.IDPK_SKIRT,
    "E_HOOD": P.IDPK_WHITE, "E_VISOR": visor(P.IDPK_BLUE, P.IDPK_WHITE), "E_CAM": CAM,
    "WSCREEN": GLASS_DARK, "E_WIN": GLASS_DARK, "E_PANEL": P.IDPK_PANEL, "E_SKIRT": P.IDPK_SKIRT,
    "E_BEAM": P.IDPK_BEAM, "E_GANG": GANG_DARK,
    "_roof": (P.IDPK_ROOF, P.IDPK_BOX),
    # white PLZEŇSKÝ KRAJ wordmark under the kraj emblem on the front panel
    "_end_marks": [(0.5, 0.2, 10, WHITE_MARK)],
})


# ------------------------------------------------------------------ 690.2 battery units
GREEN_TO, LOOPS_TO = 0.54, 0.75       # fraction of the car from the cab nose


def bemu_side(ctx):
    z, k = ctx["zone"], ctx["k"]
    g = ctx["geo"]
    if z == "S_DOOR":
        return P.BEMU_DOOR
    if k <= 0:
        return P.BEMU_CANT
    if k == 6:
        return SAPPHIRE
    if k == 7:
        return P.BEMU_STRIPE
    if k >= 8:
        return SAPPHIRE
    d = d_cab(ctx)
    f = 0.5 if d is None else d * g.px
    if k == 1 and g.cab == "front":
        # 1st-class stripe under the cant from the hood to door 1 (690.2 car)
        door1 = min(1 - u1 for u0, u1 in g.doors)
        if f < door1:
            return YELLOW
    if f < GREEN_TO:
        return P.BEMU_GREEN
    if f < LOOPS_TO:
        # interlocking-loop chain: green outlines on navy
        return P.BEMU_LOOP if (ctx["x"] + ctx["y"]) % 2 == 0 else P.BEMU_NAVY
    return P.BEMU_NAVY


def bemu_panel(ctx):
    return P.BEMU_GREEN_DK if ctx["k"] <= 9 else P.BEMU_GREEN


BEMU = {z: bemu_side for z in SIDE_ZONES}
BEMU.update({
    "ROOF_EDGE": P.BEMU_CANT, "S_HOOD": HOOD, "S_CABWIN": GLASS_DARK,
    "E_CANT": P.BEMU_CANT, "E_TOP": P.BEMU_NAVY, "E_BODY": P.BEMU_NAVY, "E_LINE": SAPPHIRE,
    "E_GREY": P.BEMU_STRIPE, "E_VAL": SAPPHIRE,
    "E_HOOD": HOOD, "E_VISOR": visor(SAPPHIRE, HOOD), "E_CAM": CAM,
    "WSCREEN": GLASS_DARK, "E_WIN": GLASS_DARK, "E_PANEL": bemu_panel, "E_SKIRT": SAPPHIRE,
    "E_BEAM": YELLOW, "E_GANG": GANG_DARK,
    "_roof": ((200, 205, 210), P.BEMU_BOX),
    "_end_marks": [(0.5, 0.14, 10, WHITE_MARK)],        # white ČD logo on the green panel
})


def bemu_marks(car):
    """White "RegioPanter" wordmark / ČD logo on the green behind the cab."""
    if car == "A":
        return [(0.78, 0.05, 5, WHITE_MARK)]
    if car == "B":
        return [(0.22, 0.05, 5, WHITE_MARK)]
    return []


# ------------------------------------------------------------------ JMK Moravia
# Low-floor middle section: magenta roof band, white upper band, black window
# band (the low windows, k 4-6), white lower band, black skirt. Over the
# bogies (high-floor ends, high windows k 2-4) the black rises to the roof band
# above a tall white panel; the two steps are ~30 degree diagonals (upper one
# 4.5 -> 5.9 m, lower one 3.8 -> 5.0 m from the nose / coupling).
UP_D0, LO_D0, STEP = 12.5, 10.5, 1.5


def jmk_tick(ctx):
    """JMK's stretched "m": 1-px magenta ticks ~1.4 m beside every door."""
    g, ur = ctx["geo"], ctx["ur"]
    w = 4 * g.px
    for u0, u1 in g.doors:
        for t in (u0 - w, u1 + w):
            if abs(ur - t) < 0.5 * g.px:
                return True
    return False


def jmk_side(ctx):
    z, k = ctx["zone"], ctx["k"]
    if z == "S_DOOR":
        return P.JMK_WHITE if k <= 1 else P.JMK_MAGENTA
    if k <= 0:
        return P.JMK_MAGENTA
    if k >= 8:
        return P.JMK_BLACK
    d = d_end(ctx)
    if 1 <= k <= 3:
        if d < UP_D0 + STEP * (k - 1):
            return P.JMK_BLACK
        return P.JMK_MAGENTA if (k == 1 and jmk_tick(ctx)) else P.JMK_WHITE
    if k == 4:
        return P.JMK_BLACK
    if k in (5, 6):
        return P.JMK_WHITE if d < LO_D0 + STEP * (k - 5) else P.JMK_BLACK
    # k == 7: thin lower white band / bottom of the tall panel
    return P.JMK_MAGENTA if (d >= LO_D0 + 2 * STEP and jmk_tick(ctx)) else P.JMK_WHITE


def jmk_hood(ctx):
    """Magenta nose wedge; the tall white panel runs forward under it."""
    k = ctx["k"]
    if k >= 8:
        return P.JMK_BLACK
    return P.JMK_WHITE if k == 7 else P.JMK_MAGENTA


def jmk_pillars(inner):
    """Cab front: magenta pillars on the outer ~20 % each side."""
    return lambda ctx: P.JMK_MAGENTA if (ctx["u"] < 0.21 or ctx["u"] > 0.79) else inner


MORAVIA = {z: jmk_side for z in SIDE_ZONES}
MORAVIA.update({
    "ROOF_EDGE": P.JMK_MAGENTA, "S_HOOD": jmk_hood, "S_CABWIN": GLASS_DARK,
    "E_CANT": P.JMK_MAGENTA, "E_TOP": P.JMK_BLACK, "E_BODY": P.JMK_BLACK, "E_LINE": P.JMK_BLACK,
    "E_GREY": P.JMK_BLACK, "E_VAL": P.JMK_BLACK,
    "E_HOOD": P.JMK_MAGENTA, "E_VISOR": jmk_pillars(P.JMK_BLACK), "E_CAM": CAM,
    "WSCREEN": GLASS_DARK, "E_WIN": jmk_pillars(GLASS_DARK),
    "E_PANEL": jmk_pillars(P.JMK_BLACK), "E_SKIRT": P.JMK_BLACK, "E_BEAM": P.JMK_YELLOW,
    "E_GANG": P.JMK_BLACK,
    "_roof": (P.JMK_ROOF, P.JMK_BOX),
    # white number + "jmk" (white j / k, magenta m) on the black front
    "_end_marks": [(0.42, 0.08, 10, WHITE_MARK), (0.5, 0.08, 10, P.JMK_MAGENTA),
                   (0.58, 0.08, 10, WHITE_MARK)],
})


def livery(name, car):
    if name == "plzenskykraj":
        return dict(PLZEN)
    if name == "cdzelenomodrobila":
        liv = dict(BEMU)
        liv["_marks"] = bemu_marks(car)
        return liv
    if name == "jihomoravskykraj":
        return dict(MORAVIA)
    if name == "pidsedocervena":
        liv = dict(PID)
        # black ČD logo + red "pid" lettering on the grey car middle
        liv["_marks"] = []
        return liv
    liv = najbrt("1.2" if name == "najbrt1_2" else "2")
    liv["_marks"] = najbrt_marks(car)
    return liv


def paint_row(c, name):
    """c: "A" / "M" / "B", or "P" = a B car carrying the A car's pantograph at
    its inner end (Moravia 531)."""
    if c == "P":
        return transplant(panter.paint_car("A", livery(name, "A")), panter.paint_car("B", livery(name, "B")))
    return panter.paint_car(c, livery(name, c))


def write_sheet(cars, name, out):
    rows = [paint_row(c, name) for c in cars]
    return panter.save_sheet(rows, out)


FAMILIES = {
    # family dir: (cars in sheet-row order, liveries)
    "640": ("AMB", ["najbrt1_2", "najbrt2"]),
    "640_1": ("AMB", ["najbrt1_2", "najbrt2"]),
    "440": ("AMB", ["najbrt1_2", "najbrt2"]),
    "640_2": ("AMB", ["najbrt2", "pidsedocervena"]),
    "650": ("AB", ["najbrt1_2", "najbrt2"]),
    "650_2": ("AB", ["najbrt2", "plzenskykraj"]),
    "690_2": ("AB", ["cdzelenomodrobila"]),
    "530": ("AMMP", ["jihomoravskykraj"]),
    "550": ("AB", ["jihomoravskykraj"]),
}


def run(only=(), prev=None):
    """Regenerate the sheets of the given family dirs (default: all); with
    prev, also write a zoom-4 preview per livery into that directory."""
    done = {}
    outs = []
    for fam, (cars, livs) in FAMILIES.items():
        if only and fam not in only:
            continue
        d = os.path.join(FAM, fam, "sprites")
        os.makedirs(d, exist_ok=True)
        for lv in livs:
            out = os.path.join(d, lv + ".png")
            key = (cars, lv)
            if key in done:
                shutil.copyfile(done[key], out)
            else:
                write_sheet(cars, lv, out)
                done[key] = out
            outs.append(out)
            print("wrote", os.path.relpath(out, REPO))
            if prev:
                os.makedirs(prev, exist_ok=True)
                panter.preview([out], os.path.join(prev, f"{fam}_{lv}.png"), 4)
    return outs


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
    run(args, prev)


if __name__ == "__main__":
    main()
