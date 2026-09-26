"""ČD InterPanter (Škoda 10Ev) 660.0 (660 + 662 + 661) and 660.1 (660 + 662 +
064 + 662 + 661) in Najbrt 2, their only livery.

Base: the native pak128.CS InterPanter by TommPa9 (CD_660 / 662 / 064 / 661,
frozen in src/cs_*.png, shifted to source coordinates: the images extracted
from the compiled pak sit 4 px lower). It is already drawn in the Najbrt 2 layout
(sky-blue body, white cant rail, sapphire waist line, light-grey stripe, dark
valance, sapphire single door per side, light-grey cab hood), with a flat
palette. The body zones (the Body configs below, body.py + warp.py) say where a pixel sits;
the native colour class says what it is (unlike panter.py, the livery is not a
zone dict: this body has one livery, recoloured class by class). Changes to the
native drawing:

  - body blues / navies -> the shared Najbrt SKY / SAPPHIRE (shading kept as
    the native luminance ratio inside each colour class),
  - valance (dark grey) -> sapphire; cant rail, stripe, cab hood -> neutral
    light grey / near white,
  - roof skin (525252) -> light grey, roof equipment boxes -> sapphire (box
    tops lighter), pantograph / insulators unchanged,
  - window glass -> lit special 0x4D4D4D (lit only when loaded); windscreens
    and cab side windows (0x6B6B6B specials) -> plain dark glass,
  - 1st-class stripe: none on the 660 (2nd class only), native one on the 662,
    added over the 1st-class part of the 661,
  - headlights -> 0xFFFF53 on the 660 cab; the 661 cab keeps its tail lights
    and gets unlit head lamps,
  - small white ČD logo behind each cab and "InterPanter" at the inner ends.

  python tools/railpaint/interpanter.py [--preview DIR]

writes vehicle-rail/ceske-drahy/660_0 and 660_1/sprites/najbrt2.png.
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from body import Body, auto_doors, hexarr, lum
from paint import save_sheet, unspecial, add_marks, shade, preview
from palette import SAPPHIRE, SKY, YELLOW

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
SRC = os.path.join(HERE, "src") + os.sep

# ------------------------------------------------------------ bodies
Q = 0x4A4A4A
SIDE = [(0, 0, "S_CANT"), (1, 5, "S_BODY"), (6, 6, "S_LINE"), (7, 7, "S_STRIPE"), (8, 8, "S_VAL")]
GANG = [(0, 0, "E_CANT"), (1, 5, "E_BODY"), (6, 6, "E_LINE"), (7, 7, "E_STRIPE"), (8, 8, "E_VAL")]
CAB = [(0, 3, "E_WIN"), (4, 6, "E_PANEL"), (7, 10, "E_LOW"), (11, 11, "E_BEAM")]


def glass_extra(t, col):
    """Native window glass is plain 0x4A4A4A: the band rows of the pure side views."""
    v = hexarr(t)
    m = np.zeros(v.shape[1:], bool)
    if col in (3, 7):
        m[84:90] = (v[:, 84:90] == Q).any(axis=0)
    return m


def diag_glass(px):
    return (int(px[0]) << 16 | int(px[1]) << 8 | int(px[2])) == Q


def cfg(name, png, cab_col=None):
    """cab_col: end-view column that shows this car's cab (5 = se, 1 = nw)."""
    end_top = {1: 97, 5: 90}
    end_rows = {1: GANG, 5: GANG}
    if cab_col == 5:
        end_top[5] = 89
        end_rows[5] = CAB
    elif cab_col == 1:
        end_top[1] = 96
        end_rows[1] = CAB
    return dict(name=name, refs=[(SRC + png, 0)], base=0,
                side_top={3: 83, 7: 83}, end_top=end_top,
                side_rows=SIDE, end_rows=end_rows,
                doors=auto_doors(2, min_w=3, dark=40), door_rows=(1, 8),
                glass_extra=glass_extra, diag_glass=diag_glass,
                extra_zones=["WSCREEN"])


CFG = {
    "660": cfg("ip660", "cs_660.png", cab_col=5),
    "662": cfg("ip662", "cs_662.png"),
    "064": cfg("ip064", "cs_064.png"),
    "661": cfg("ip661", "cs_661.png", cab_col=1),
}
_cache = {}


def get_body(n):
    if n not in _cache:
        _cache[n] = Body(CFG[n])
    return _cache[n]


# ------------------------------------------------------------ colours
HOOD = (238, 240, 242)          # cab hood, cant rail: light grey / near white (#EEF0F2)
STRIPE = (221, 226, 230)        # light-grey stripe (#DDE2E7)
ROOF_SKIN = (176, 182, 188)     # roof skin between the equipment boxes
BOX_TOP = (40, 78, 124)         # sapphire roof equipment, lit top (#1C4C7A..)
CABGLASS = (40, 46, 56)         # windscreens / cab side windows, never lit
LAMP_OFF = (214, 218, 222)      # unlit head lamps on the rear cab
WHITE = (240, 242, 244)         # lettering

# native colour classes (flat TommPa9 palette) and their reference shade
BLUE = {0x0063C5, 0x1073E6, 0x004A9C, 0x109CFF}
NAVY = {0x001942, 0x102152, 0x001031, 0x00103A, 0x10214A, 0x001029}
LIGHT = {0xF7F7FF, 0xE6EFF7, 0xD6DEE6, 0xC5CED6, 0xB5BDC5, 0x9CA5AD, 0x8C949C, 0x7B848C}
DARK = {0x4A4A4A, 0x3A3A3A, 0x424242, 0x313131}
YEL = {0xFFC508, 0xFFC500, 0xF7B500}
REF = {"blue": 0x0063C5, "navy": 0x001942, "light": 0xF7F7FF, "roofR": 0x7B7B7B, "yel": 0xFFC508}
LAMPS = {0xC1B1D1, 0xC5B5D6}    # head lamp pods of the native cab (0xC1B1D1 is a lamp special)
WSCREEN = {0x6B6B6B}
Q = 0x4A4A4A


def rgb(h):
    return np.array(((h >> 16) & 255, (h >> 8) & 255, h & 255), float)


def lumh(h):
    return float(lum(rgb(h)))


def scaled(colour, native, ref):
    f = lumh(native) / lumh(ref)
    return np.clip(np.array(colour, float) * f, 0, 255)


def paint_car(n, stripe=None, cab=None):
    """n: native car ('660', '662', '064', '661'); stripe: None | 'native' |
    (u0, u1) span (u from the car's rear) for the 1st-class stripe;
    cab: None | 'front' (head lamps) | 'rear' (tail lamps)."""
    b = get_body(n)
    Z = b.Z
    zn = np.array(b.zones)[b.lab]
    v = hexarr(b.base)
    out = b.base.astype(float).copy()
    H, W = v.shape
    for y in range(H):
        for x in range(W):
            z = zn[y, x]
            if z == "T":
                continue
            c = int(v[y, x])
            roof = z in ("ROOF", "ROOF_EDGE")
            if c in BLUE:
                out[y, x] = scaled(SKY, c, REF["blue"])
            elif c in NAVY:
                out[y, x] = scaled(SAPPHIRE, c, REF["navy"])
            elif c in LIGHT:
                if z in ("E_BODY", "E_LINE") and c == 0x7B848C:
                    continue                       # gangway door
                tgt = STRIPE if z == "S_STRIPE" else HOOD
                out[y, x] = scaled(tgt, c, REF["light"])
            elif c in YEL:
                if z.startswith("E_") or z == "FIX":
                    out[y, x] = scaled(YELLOW, c, REF["yel"])       # anti-climber
                elif stripe == "native":
                    out[y, x] = scaled(YELLOW, c, REF["yel"])
                else:
                    out[y, x] = scaled(SKY, 0x0063C5, REF["blue"])  # no stripe here
            elif c in WSCREEN:
                out[y, x] = CABGLASS
            elif c in LAMPS or c == 0xE6E6FF:
                out[y, x] = (0xFF, 0xFF, 0x53) if cab == "front" else LAMP_OFF
            elif c == 0x4D4D4D and z != "GLASS":
                out[y, x] = CABGLASS                               # camera box on the cap
            elif roof and c == 0x525252:
                out[y, x] = ROOF_SKIN
            elif roof and c == 0x7B7B7B:
                out[y, x] = BOX_TOP
            elif roof and c in DARK:
                out[y, x] = scaled(BOX_TOP, c, REF["roofR"])
            elif c in DARK and z in ("S_VAL", "S_STRIPE"):
                out[y, x] = scaled(SAPPHIRE, c, 0x4A4A4A) * 0.8   # valance
            elif c in DARK and z == "E_LOW" and c != Q:
                out[y, x] = scaled(SAPPHIRE, c, 0x4A4A4A) * 0.8   # lower front sides
            elif c == 0x848484 and z == "E_VAL":
                out[y, x] = scaled(SAPPHIRE, c, 0x848484) * 0.8
    g = b.lab == Z["GLASS"]
    out[g] = (0x4D, 0x4D, 0x4D)
    a = unspecial(np.rint(out).astype(np.uint8))
    # 1st-class stripe over part of the car (661)
    if isinstance(stripe, tuple):
        u0, u1 = stripe
        a = add_marks(b, a, side=[((u0 + u1) / 2, u1 - u0, 1, YELLOW)], side_zones=["S_BODY"])
    # lettering: ČD logo behind the cab(s), "InterPanter" at the inner end(s)
    marks = []
    # (k 5 = the lowest body row, clear of the window band on the raised ends)
    if cab == "front":
        marks += [(0.85, 0.05, 5, WHITE), (0.07, 0.07, 5, WHITE)]
    elif cab == "rear":
        marks += [(0.15, 0.05, 5, WHITE), (0.93, 0.07, 5, WHITE)]
    else:
        marks += [(0.07, 0.07, 5, WHITE), (0.93, 0.07, 5, WHITE)]
    a = add_marks(b, a, side=marks, side_zones=["S_BODY"])
    # marks must not land on glass or doors (side_zones already excludes them)
    return a


def glass_ok(a):
    v = hexarr(a)
    return int((v == 0x4D4D4D).sum())


CARS = {
    "660": dict(n="660", stripe=None, cab="front"),
    "662": dict(n="662", stripe="native"),
    "064": dict(n="064", stripe=None),
    "661": dict(n="661", stripe=(0.55, 0.78), cab="rear"),
}


def run(prev=None):
    """Regenerate both InterPanter sheets; with prev, also write zoom-4
    previews into that directory."""
    rows = {k: paint_car(**v) for k, v in CARS.items()}
    p0 = os.path.join(FAM, "660_0", "sprites", "najbrt2.png")
    p1 = os.path.join(FAM, "660_1", "sprites", "najbrt2.png")
    save_sheet([rows["660"], rows["662"], rows["661"]], p0)
    save_sheet([rows["660"], rows["662"], rows["064"], rows["662"], rows["661"]], p1)
    for p in (p0, p1):
        print("wrote", os.path.relpath(p, REPO))
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview([p0], os.path.join(prev, "660_0_najbrt2.png"), 4)
        preview([p1], os.path.join(prev, "660_1_najbrt2.png"), 4)
    return p0, p1


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
    run(prev)


if __name__ == "__main__":
    main()
