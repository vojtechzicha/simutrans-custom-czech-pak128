"""ČD RegioNova: 814.0 + 914 (family 814_0) and the 814.2 + 014 + 814.2 trio
(family 814_2), every livery on the Sim pak128.CS 814 drawings.

Upstream drawings (frozen in src/814/, the 1024-px sprite columns only; from
pak128.CS rail-psg mail/814): cd914p_zhasnuty = 914 with its cab ahead (the
unlit sheet), cd814p = 814 motor car with its cab ahead (zd814p, same
silhouette, as second reference), cd014s = the 014 middle car.

Only the three front-facing bodies are zoned and painted. Every rear-facing car
is the same car turned round: the upstream rear drawings (cd814z, zd914z) are
exactly the front drawing with the direction columns shifted by 4, moved one
carunit forward along travel and with head / tail lamps swapped (checked pixel
for pixel), see rearify().

Liveries: 814_0 zlutozelena, najbrt2, plzenskykraj, pardubickykraj, vysocina,
pidsedocervena; 814_2 zlutozelena, najbrt2, pidsedocervena.
Sheet rows: 814_0 = 0 914 (cab ahead), 1 814.0 (cab behind), 2 814.0-reverse
(cab ahead), 3 914-reverse (cab behind); 814_2 = 0 814.2-front, 1 014,
2 814.2-rear.

  python tools/railpaint/cd_814.py [814_0] [814_2] [--preview DIR]

writes vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png; --preview also
writes zoomed previews and the zone false-colour maps into DIR.
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warp
from body import Body, lum, hexarr
from paint import paint, recolor_lum, add_marks, save_sheet, unspecial, preview
from palette import SAPPHIRE, SKY, LGREY, N2_STRIPE, dk

REPO = os.path.dirname(os.path.dirname(HERE))
FAMDIR = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
I = os.path.join(HERE, "src", "814") + os.sep
T = np.array((231, 255, 255))


# ---- helpers shared with the 854 painter (cd_85x) ---------------------------
def keep_dark(body, col):
    """Near-black neutral pixels on the faces (gangway posts, canopy,
    handrails, coupler recess) keep their base colour."""
    sl = slice(col * 128, (col + 1) * 128)
    b = body.base[:, sl].astype(int)
    dark = (lum(b.astype(float)) < 48) & ((b.max(axis=-1) - b.min(axis=-1)) < 25)
    lab = body.lab[:, sl]
    Z = body.Z
    face = np.isin(lab, [Z[z] for z in body.zones if z.startswith(("E_", "S_"))]) & (lab != Z["S_SOLE"])
    lab[dark & face] = Z["FIX"]


def fill_fix_livery(b, a, passes=3):
    """FIX pixels that still show the base livery (saturated red / cream /
    player-colour yellow) are stray paint the zone rules missed: give them the
    median colour of their painted, non-FIX neighbours."""
    Z = b.Z
    base = b.base.astype(int)
    sat = (base.max(axis=-1) - base.min(axis=-1)) > 45
    v = (base[..., 0] << 16) | (base[..., 1] << 8) | base[..., 2]
    special = np.isin(v, [0xFFFF53, 0xFF211D, 0x4D4D4D, 0x57656F])
    todo = (b.lab == Z["FIX"]) & sat & ~special
    good = ~np.isin(b.lab, [Z["T"], Z["FIX"], Z["GLASS"], Z["HEAD"], Z["TAIL"]])
    a = a.copy()
    for _ in range(passes):
        ys, xs = np.where(todo)
        done = []
        for y, x in zip(ys, xs):
            nb = [(y + dy, x + dx) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
                  if 0 <= y + dy < 128 and (x + dx) // 128 == x // 128 and good[y + dy, x + dx]]
            if nb:
                a[y, x] = np.median(np.array([a[p] for p in nb]), axis=0).astype(np.uint8)
                done.append((y, x))
        for y, x in done:
            todo[y, x] = False
            good[y, x] = True
    return a


# ---- bodies -----------------------------------------------------------------
def unlit_glass(t, col):
    """The unlit upstream sheet (cd914p_zhasnuty) draws its windows in plain
    greys 4E4E4E / 586670; they are glass."""
    v = hexarr(t[0])
    return np.isin(v, [0x4E4E4E, 0x586670])


def glass_like(px):
    r, g, b = (int(v) for v in px)
    return (r, g, b) in ((0x4E, 0x4E, 0x4E), (0x58, 0x66, 0x70), (0x4D, 0x4D, 0x4D), (0x57, 0x65, 0x6F))


def windscreen_6b(body, col):
    """0x6B6B6B is the cab windscreen in every view (front face, its side
    profile, the diagonals): WSCREEN, dark but not lit."""
    Z = body.Z
    if "WSCREEN" not in Z:
        body.zones.append("WSCREEN"); Z["WSCREEN"] = len(body.zones) - 1
    sl = slice(col * 128, (col + 1) * 128)
    v = hexarr(body.base[:, sl])
    lab = body.lab[:, sl]
    lab[(v == 0x6B6B6B) & (lab != Z["T"])] = Z["WSCREEN"]
    keep_dark(body, col)


SIDE = [(0, 0, "S_TOP"), (1, 4, "S_WIN"), (5, 5, "S_BELT"), (6, 8, "S_LOW"), (9, 9, "S_SKIRT")]
# cab end (the front face of the front-facing bodies, se view)
CAB = [(0, 1, "E_CAP"), (2, 6, "E_WIN"), (7, 8, "E_LAMP"), (9, 9, "E_BELOW"), (10, 11, "E_LOW"), (12, 12, "E_BEAM")]
# gangway end (nw view of every body; both ends of the 014)
GANG = [(0, 0, "E_TOP"), (1, 4, "E_WALLU"), (5, 5, "E_WALLS"), (6, 8, "E_WALLL"), (9, 10, "E_GBEAM")]


def mirror_doors(d3):
    """Door x-ranges of the sw view mirrored from the ne view (the body spans
    x 42..83 in ne and 37..78 in sw for these drawings)."""
    return [(37 + 83 - b, 37 + 83 - a) for a, b in d3]


B914 = dict(
    name="914p", refs=[(I + "cd914p_zhasnuty.png", 0)],
    side_top={3: 83, 7: 83}, end_top={1: 78, 5: 88},
    side_rows=SIDE, end_rows={1: GANG, 5: CAB},
    doors={3: [(61, 65)], 7: mirror_doors([(61, 65)])}, door_rows=(1, 9),
    glass_extra=unlit_glass, diag_glass=glass_like, fix=windscreen_6b,
    extra_zones=["WSCREEN", "S_SOLE"],
)
B814 = dict(
    name="814p", refs=[(I + "cd814p.png", 0), (I + "zd814p.png", 0)],
    side_top={3: 83, 7: 83}, end_top={1: 78, 5: 88},
    side_rows=SIDE, end_rows={1: GANG, 5: CAB},
    doors={3: [(45, 48), (75, 78)], 7: mirror_doors([(45, 48), (75, 78)])}, door_rows=(1, 9),
    diag_glass=glass_like, fix=windscreen_6b,
    extra_zones=["WSCREEN", "S_SOLE"],
)
B014 = dict(
    name="014", refs=[(I + "cd014s.png", 0)],
    side_top={3: 83, 7: 83}, end_top={1: 78, 5: 89},
    side_rows=SIDE, end_rows=GANG,
    doors={3: [(61, 65)], 7: [(60, 64)]}, door_rows=(1, 9),
    diag_glass=glass_like, fix=windscreen_6b,
    extra_zones=["WSCREEN", "S_SOLE"],
)

_cache = {}


def get(name):
    if name not in _cache:
        b = Body({"914": B914, "814": B814, "014": B014}[name])
        edge_sides(b)
        # the only references are the yellow-green (and ZD) sheets, whose
        # livery bands are baked into the luminance: flat face-level shading,
        # only strong outline pixels keep their own factor
        import paint as _p
        _p._shade[b.name] = b.shade(edge_tol=0.6)
        _cache[name] = b
    return _cache[name]


def edge_sides(b):
    """In the pure end views the outermost body columns along the roof are the
    side walls seen edge-on (drawn in the side colour upstream): S_EDGE."""
    Z = b.Z
    if "S_EDGE" not in Z:
        b.zones.append("S_EDGE"); Z["S_EDGE"] = len(b.zones) - 1
    for col in (1, 5):
        sl = slice(col * 128, (col + 1) * 128)
        lab = b.lab[:, sl]
        body = lab != Z["T"]
        ys, xs = np.where(body)
        for x in (xs.min(), xs.max()):
            for y in range(128):
                if lab[y, x] in (Z["ROOF"], Z["ROOF_EDGE"]):
                    lab[y, x] = Z["S_EDGE"]


# ---- turning a car round ----------------------------------------------------
# one carunit forward along the new heading, per direction column
REAR_SHIFT = [(-4, -2), (0, -11), (4, -2), (6, 0), (4, 2), (0, 11), (-4, 2), (-6, 0)]


def rearify(a):
    """Front-facing sheet row -> the same car facing backwards (cab at the
    rear): columns shifted by 4, moved one carunit forward, lamps swapped."""
    out = np.zeros_like(a); out[:] = T
    for c in range(8):
        src = a[:, ((c + 4) % 8) * 128:((c + 4) % 8 + 1) * 128]
        dx, dy = REAR_SHIFT[c]
        m = ~np.all(src == T, axis=-1)
        ys, xs = np.where(m)
        ny, nx = ys + dy, xs + dx
        ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
        assert ok.all(), f"rearify pushes pixels out of tile {c}"
        tile = out[:, c * 128:(c + 1) * 128]
        tile[ny, nx] = src[ys, xs]
    v = hexarr(out)
    head, tail = v == 0xFFFF53, v == 0xFF211D
    out[head] = (0xFF, 0x21, 0x1D)
    out[tail] = (0xFF, 0xFF, 0x53)
    return out


# ---- liveries ---------------------------------------------------------------
# colours: photo research (September 2026); Najbrt from palette.py and the
# regional schemes matched to the RS1 / PESA sheets where it is the same design

CABGLASS = (52, 58, 66)          # cab windscreen: dark glass, not lit
YELLOW_EDGE = (238, 196, 24)     # yellow strip along the bottom of the front
UNDER = (46, 48, 52)
WHITE = (238, 240, 239)
N2_ROOF = (64, 80, 112)          # sapphire roof, weathered (reads grey-blue from above)

PK_NAVY = (33, 58, 128)          # as the RS1 painter (cd_rs1)
PK_RED = (228, 64, 46)
PK_YELLOW = (230, 190, 0)
PK_MASK = (196, 202, 208)
VY_GREEN = (109, 190, 69)        # Kraj Vysočina light green #6DBE45
PL_BLUE = (31, 78, 158)          # Plzeňský kraj royal blue #1F4E9E
PL_MASK = (11, 58, 122)          # dark royal blue headlight mask
PL_YELLOW = (243, 195, 0)
PL_GREEN = (68, 165, 71)
PL_SKIRT = (58, 63, 66)          # anthracite skirt
PID_GREY = (210, 213, 210)       # PID light grey #D2D5D2
PID_RED = (217, 42, 43)
PID_BLACK = (30, 31, 34)
PID_LOWFRONT = (140, 143, 144)
PID_YELLOW = (232, 184, 48)


def by_k(table, default):
    return lambda c: table.get(c["k"], default)


def ur(c):
    """Position along the car from its inner (gangway) end, 0, to its cab end,
    1, on both sides (the sw side view has the cab on the left)."""
    col = c["col"]
    src = col if col in (3, 7) else warp.SIDE_SRC.get(col, col)
    return 1 - c["u"] if src == 7 else c["u"]


def pid_blocks(veh):
    """PID pyjama blocks along the car below and above the black window band:
    (start, end, colour) in ur() coordinates, from the photos."""
    if veh == "814":      # from the cab: grey cab section, door, long red, grey (pid logo), red, grey
        return [(0.00, 0.10, PID_GREY), (0.10, 0.30, PID_RED), (0.30, 0.52, PID_GREY),
                (0.52, 0.86, PID_RED), (0.86, 1.01, PID_GREY)]
    if veh == "914":      # cab section grey, red, grey block by the low-floor door, red, grey inner end
        return [(0.00, 0.14, PID_GREY), (0.14, 0.40, PID_RED), (0.40, 0.62, PID_GREY),
                (0.62, 0.84, PID_RED), (0.84, 1.01, PID_GREY)]
    return [(0.00, 0.16, PID_GREY), (0.16, 0.42, PID_RED), (0.42, 0.60, PID_GREY),
            (0.60, 0.84, PID_RED), (0.84, 1.01, PID_GREY)]


def block(veh):
    bl = pid_blocks(veh)

    def f(c):
        u = ur(c)
        for a, b, col in bl:
            if a <= u < b:
                return col
        return PID_GREY
    return f


def frame(edge, inner, w=0.14):
    """End-face rows whose outer pixels are a coloured frame (the red / green
    U round the windscreen and headlight mask on the Pardubice / Vysočina
    fronts, the white corner pillars on Plzeň)."""
    return lambda c: edge if (c["u"] < w or c["u"] > 1 - w) else inner


def swoosh(base, lines):
    """Plzeň: thin diagonal swoosh lines rising towards the ends; lines are
    (u0, colour): a pixel is on a line where ur - u0 == 0.035 * (8 - k)."""
    def f(c):
        u, k = ur(c), c["k"]
        for u0, col in lines:
            if abs((u - u0) - 0.035 * (8 - k)) < 0.02:
                return col
        return base
    return f


def livery(name, veh):
    """-> (zone spec, roof colour or None to keep the upstream roof)."""
    if name == "zlutozelena":
        return {"WSCREEN": CABGLASS}, None
    if name == "najbrt2":
        # white roof-edge strip, sky window band, sapphire stripe, white lower
        # body, sapphire bottom band and doors; front: sapphire dome, white
        # windscreen surround, sky mask, white band, sapphire lower front
        return {
            "ROOF_EDGE": N2_STRIPE, "S_EDGE": SKY,
            "S_TOP": SKY, "S_WIN": SKY, "S_BELT": SAPPHIRE, "S_LOW": LGREY, "S_SKIRT": SAPPHIRE,
            "S_DOOR": SAPPHIRE,
            "E_CAP": by_k({1: N2_STRIPE}, SAPPHIRE), "E_WIN": N2_STRIPE, "E_LAMP": SKY,
            "E_BELOW": LGREY, "E_LOW": SAPPHIRE, "E_BEAM": YELLOW_EDGE,
            "E_TOP": N2_STRIPE, "E_WALLU": SKY, "E_WALLS": SAPPHIRE, "E_WALLL": LGREY, "E_GBEAM": SAPPHIRE,
            "WSCREEN": CABGLASS,
        }, N2_ROOF
    if name == "pidsedocervena":
        blk = block(veh)
        red_band = lambda c: PID_RED if 0.52 <= c["u"] <= 0.84 else PID_GREY
        return {
            "ROOF_EDGE": PID_GREY, "S_EDGE": PID_GREY,
            "S_TOP": blk, "S_WIN": PID_BLACK, "S_BELT": blk, "S_LOW": blk, "S_SKIRT": blk,
            "S_DOOR": PID_BLACK,
            "E_CAP": PID_GREY, "E_WIN": PID_GREY, "E_LAMP": red_band, "E_BELOW": red_band,
            "E_LOW": PID_LOWFRONT, "E_BEAM": PID_YELLOW,
            "E_TOP": PID_GREY, "E_WALLU": PID_GREY, "E_WALLS": PID_GREY, "E_WALLL": PID_GREY,
            "E_GBEAM": PID_LOWFRONT, "WSCREEN": CABGLASS,
        }, PID_GREY
    if name == "plzenskykraj":
        sw = swoosh(PL_BLUE, [(0.08, PL_GREEN), (0.12, PL_YELLOW), (0.62, PL_GREEN), (0.66, PL_YELLOW)])
        return {
            "ROOF_EDGE": WHITE, "S_EDGE": WHITE,
            "S_TOP": WHITE, "S_WIN": PL_BLUE, "S_BELT": sw, "S_LOW": sw, "S_SKIRT": PL_SKIRT,
            "S_DOOR": PL_YELLOW,
            "E_CAP": by_k({1: WHITE}, PL_BLUE), "E_WIN": WHITE, "E_LAMP": frame(WHITE, PL_MASK),
            "E_BELOW": WHITE, "E_LOW": PL_BLUE, "E_BEAM": YELLOW_EDGE,
            "E_TOP": WHITE, "E_WALLU": PL_BLUE, "E_WALLS": PL_BLUE, "E_WALLL": PL_BLUE, "E_GBEAM": PL_SKIRT,
            "WSCREEN": CABGLASS,
        }, PL_BLUE
    if name in ("pardubickykraj", "vysocina"):
        acc, door = (PK_RED, PK_YELLOW) if name == "pardubickykraj" else (VY_GREEN, VY_GREEN)
        mask = PK_MASK if name == "pardubickykraj" else (226, 230, 232)
        return {
            "ROOF_EDGE": PK_NAVY, "S_EDGE": acc,
            "S_TOP": acc, "S_WIN": WHITE, "S_BELT": WHITE, "S_LOW": WHITE,
            "S_SKIRT": PK_NAVY, "S_DOOR": door,
            "E_CAP": PK_NAVY, "E_WIN": acc, "E_LAMP": frame(acc, mask),
            "E_BELOW": WHITE, "E_LOW": PK_NAVY, "E_BEAM": YELLOW_EDGE,
            "E_TOP": acc, "E_WALLU": WHITE, "E_WALLS": WHITE, "E_WALLL": WHITE, "E_GBEAM": PK_NAVY,
            "WSCREEN": CABGLASS,
        }, PK_NAVY
    raise KeyError(name)


def marks(name, veh):
    """(side marks, end marks). add_marks() measures side u from the rear,
    which is the inner end of a front-facing car (the cab is at u = 1)."""
    cab = veh in ("914", "814")
    if name == "najbrt2":
        side = [(0.45, 0.10, 7, SAPPHIRE)]                              # "ČD České dráhy"
        if veh in ("914", "014"):
            side += [(0.72, 0.06, 6, SAPPHIRE), (0.30, 0.06, 6, SKY)]   # pictograms, RegioNova logo
        end = [(0.5, 0.12, 7, (236, 240, 244))] if cab else []         # white ČD logo on the mask
        return side, end
    if name == "pidsedocervena":
        side = [(0.41, 0.10, 7, PID_RED)] if veh == "814" else [(0.51, 0.08, 7, (90, 94, 98))]
        end = [(0.30, 0.10, 7, PID_RED), (0.68, 0.08, 8, (240, 242, 244))] if cab else []
        return side, end
    if name == "plzenskykraj":
        side = [(0.42, 0.20, 6, WHITE)]                                 # PLZEŇSKÝ KRAJ wordmark
        end = [(0.5, 0.10, 7, (236, 240, 244))] if cab else []
        return side, end
    if name == "pardubickykraj":
        side = [(0.62, 0.05, 5, PK_NAVY), (0.62, 0.05, 6, PK_YELLOW), (0.70, 0.10, 6, (70, 72, 78)),
                (0.30, 0.08, 7, PK_NAVY)]
        end = [(0.40, 0.06, 7, PK_NAVY), (0.60, 0.06, 7, PK_YELLOW), (0.30, 0.10, 9, PK_RED)] if cab else []
        return side, end
    if name == "vysocina":
        side = [(0.28, 0.06, 6, VY_GREEN), (0.35, 0.08, 6, PK_NAVY), (0.55, 0.14, 6, SKY)]
        end = [(0.42, 0.06, 7, VY_GREEN), (0.58, 0.06, 7, PK_NAVY), (0.30, 0.10, 9, VY_GREEN)] if cab else []
        return side, end
    return [], []


def render_front(veh, liv):
    b = get(veh)
    spec, roof = livery(liv, veh)
    a = paint(b, spec)
    if liv != "zlutozelena":
        a = fill_fix_livery(b, a)
    if roof is not None:
        a = recolor_lum(b, a, "ROOF", roof)
    s, e = marks(liv, veh)
    a = add_marks(b, a, side=s, end=e)
    return unspecial(a)


# ---- sheets ----------------------------------------------------------------
FAMILIES = {
    "814_0": ["zlutozelena", "najbrt2", "plzenskykraj", "pardubickykraj", "vysocina", "pidsedocervena"],
    "814_2": ["zlutozelena", "najbrt2", "pidsedocervena"],
}


def render(fam, liv):
    """-> the sheet rows of one family livery (see the module docstring)."""
    m814 = render_front("814", liv)
    if fam == "814_0":
        m914 = render_front("914", liv)
        return [m914, rearify(m814), m814, rearify(m914)]
    return [m814, render_front("014", liv), rearify(m814)]


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    fams = argv or list(FAMILIES)
    written = []
    for fam in fams:
        for liv in FAMILIES[fam]:
            p = save_sheet(render(fam, liv), os.path.join(FAMDIR, fam, "sprites", liv + ".png"))
            print("wrote", p)
            written.append(p)
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview(written, os.path.join(prev, "p814.png"))
        for n in ("914", "814", "014"):
            fc, _ = get(n).falsecolor()
            Image.fromarray(np.concatenate([get(n).base.astype(np.uint8), fc], 0)).save(
                os.path.join(prev, f"z{n}.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
