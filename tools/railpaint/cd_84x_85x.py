#!/usr/bin/env python3
"""ČD 842 "Kvatro", 843 "Rakev" and 854 "Hydra" with their trailers: zone-map
repaints of Sim's pak128.CS drawings.

Families and liveries (sheet rows in family order; a car a livery never had
leaves its row blank):
  842  rows 842, 054, 954, 954-front, 954.2, 954.2-front - najbrt1 (842),
       najbrt2 (all six), cervenokremova (all but the 842)
  843  rows 843, 043, 943 - najbrt1, najbrt2 (all three),
                            cervenokremova (843, 043)
  854  row 854            - najbrt2, cervenokremova
054 = Bdtn 756/757 intermediate trailer, 954 = Bfbrdtn 794 control car, 954.2
= ABfbrdtn 795 control car with 1st class at the gangway end (yellow line under
the roof there), all drawn with the 854 set; 043 = Btn 753, 943 = Bftn 791.
The -front rows are the control cars turned round to lead a set (cab ahead),
see turn_round().

Frozen bases (src/84x_85x/, source coordinates, one 128-px row per ref; the
first ref of a body gives its FIX pixels, the others help the zone map):
  842.png  the two upstream halves of 842_balkan composited into one sprite
  843.png  the same for 843_balkan
  943.png, 043.png  pak128.CS rail-psg mail/842_843/943_balkan, 043_balkan
  854.png  CD 854 "Hydra", ČSD M 296.1 and uni_854 (vehicle.motorak.853_854 /
           854_uni, both halves of each split car composited)
  954.png  Bfbrdtn 954 and ABfbrdtn 954 (853_854); the ABfbrdtn row is the
           base of the 954.2
  054.png  uni_054 (854_uni)
pak128.CS splits these long cars into two halves with complementary
checkerboard dithering; painting one half alone leaves a checkerboard in the
s view, hence the composites.

  python tools/railpaint/cd_84x_85x.py [family …] [--preview DIR]

writes vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png (and, with
--preview, 4x previews into DIR). Colours come from palette.py (Najbrt, ČD
red-cream); change the livery dicts below and regenerate instead of painting
the PNGs by hand.
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from body import Body, lum, auto_doors
from paint import paint, recolor_lum, add_marks, save_sheet, preview
from palette import (SAPPHIRE, SKY, LGREY, N2_STRIPE, UMBRA, RC_RED, RC_CREAM,
                     RC_ROOF, BLACK, YELLOW, dk)
import warp

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
SRC = os.path.join(HERE, "src", "84x_85x") + os.sep


# ------------------------------------------------------------ zone helpers
def win_glass(k0, k1, top):
    """Window glass that the upstream draws as plain dark greys: neutral or
    blue-grey pixels in the window rows of the side faces (pure views)."""
    def f(t, col):
        b = t[0].astype(int)
        m = np.zeros(b.shape[:2], bool)
        if col not in top:
            return m
        y0, y1 = top[col] + k0, top[col] + k1
        L = lum(b.astype(float))
        neutral = (b.max(axis=-1) - b.min(axis=-1)) < 40
        bluish = (b[..., 2] >= b[..., 0]) & (L < 130)
        sel = (neutral | bluish) & (L < 125)
        m[y0:y1 + 1] = sel[y0:y1 + 1]
        return m
    return f


def glass_like(px):
    """A diagonal-view pixel that looks like window glass (dark grey or
    blue-grey, not livery red / cream / player yellow)."""
    r, g, b = (int(v) for v in px)
    L = 0.299 * r + 0.587 * g + 0.114 * b
    return L < 125 and (max(r, g, b) - min(r, g, b) < 40 or (b >= r and L < 130))


def red_doors(k_probe):
    """Door x-ranges: where the red-cream base is red in the cream band row."""
    def f(body, col, top):
        t = body.base[:, col * 128:(col + 1) * 128]
        y = top + k_probe
        xs = [x for x in range(128) if t[y, x][0] > 140 and t[y, x][1] < 100]
        runs, cur = [], []
        for x in xs:
            if cur and x != cur[-1] + 1:
                runs.append(cur); cur = []
            cur.append(x)
        if cur:
            runs.append(cur)
        return [(r[0], r[-1]) for r in runs if len(r) >= 2]
    return f


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


# ------------------------------------------------------------ bodies
# 84x: dark gangway / mask pixels keep their colour (fix), stray glass in the
# diagonal views stays glass (diag_glass), gangway end walls get E_WALL.
SIDE_84X = [(0, 0, "S_TOP"), (1, 4, "S_WIN"), (5, 5, "S_BELT"), (6, 7, "S_LOW"), (8, 8, "S_SKIRT"), (9, 9, "S_SOLE")]
COMMON_84X = dict(fix=keep_dark, diag_glass=glass_like, extra_zones=["E_WALL"])

B842 = dict(
    name="842",
    refs=[(SRC + "842.png", 0)],
    base=0,
    side_top={3: 83, 7: 83},
    end_top={1: 91, 5: 87},
    side_rows=SIDE_84X,
    doors=auto_doors(8), door_rows=(1, 9), windscreen=True,
    end_rows={1: [(0, 1, "E_TOP"), (2, 5, "E_WIN"), (6, 7, "E_BELOW"), (8, 9, "E_LAMP"), (10, 11, "E_LOW"), (12, 12, "E_BEAM")],
              5: [(0, 1, "E_TOP"), (2, 5, "E_WIN"), (6, 8, "E_BELOW"), (9, 9, "E_LAMP"), (10, 11, "E_LOW"), (12, 12, "E_BEAM")]},
    **COMMON_84X,
)

B843 = dict(
    name="843",
    refs=[(SRC + "843.png", 0)],
    side_top={3: 83, 7: 83}, end_top={1: 90, 5: 86},
    side_rows=SIDE_84X, doors=auto_doors(8), door_rows=(1, 9), windscreen=True,
    end_rows=[(0, 2, "E_TOP"), (3, 6, "E_WIN"), (7, 7, "E_BELOW"), (8, 8, "E_LAMP"), (9, 9, "E_BELOW2"),
              (10, 12, "E_LOW"), (13, 13, "E_BEAM")],
    **COMMON_84X,
)

# 943 control trailer: cab end = nw view (col 1), gangway end = se view (col 5)
B943 = dict(
    name="943",
    refs=[(SRC + "943.png", 0)],
    side_top={3: 83, 7: 83}, end_top={1: 83, 5: 88},
    side_rows=SIDE_84X, doors=auto_doors(8), door_rows=(1, 9), windscreen=True,
    end_rows={1: [(0, 0, "E_TOP"), (1, 4, "E_WIN"), (5, 5, "E_BELOW"), (6, 6, "E_LAMP"), (7, 7, "E_BELOW2"),
                  (8, 10, "E_LOW"), (11, 11, "E_BEAM")],
              5: [(0, 0, "E_TOP"), (1, 7, "E_WALL"), (8, 8, "E_BEAM")]},
    **COMMON_84X,
)

# 043 intermediate trailer: gangway ends both ways
B043 = dict(
    name="043",
    refs=[(SRC + "043.png", 0)],
    side_top={3: 83, 7: 83}, end_top={1: 83, 5: 88},
    side_rows=SIDE_84X, doors=auto_doors(8), door_rows=(1, 9),
    end_rows=[(0, 0, "E_TOP"), (1, 7, "E_WALL"), (8, 8, "E_BEAM")],
    **COMMON_84X,
)

# 85x: 854 railcar and the 954 / 054 trailers (854-set drawings)
SIDE_85X = [(0, 0, "S_TOP"), (1, 3, "S_WIN"), (4, 4, "S_BELT"), (5, 6, "S_BAND"), (7, 7, "S_LOW"), (8, 9, "S_SOLE")]
END_85X = [(0, 0, "E_TOP"), (1, 3, "E_WIN"), (4, 5, "E_BAND"), (6, 8, "E_LOW"), (9, 9, "E_BEAM"), (10, 10, "E_PLOUGH")]
ST = {3: 83, 7: 83}

B854 = dict(
    name="854",
    refs=[(SRC + "854.png", 0), (SRC + "854.png", 1), (SRC + "854.png", 2)],   # CD 854, M 296.1, uni_854
    side_top=ST, end_top={1: 93, 5: 89},
    side_rows=SIDE_85X, end_rows=END_85X,
    doors=red_doors(5), door_rows=(0, 7),
    glass_extra=win_glass(1, 3, ST), diag_glass=glass_like, windscreen=True, fix=keep_dark,
)

# 954 control car: cab (full front) = nw view, gangway end = se view
B954 = dict(
    name="954",
    refs=[(SRC + "954.png", 0), (SRC + "954.png", 1)],                        # Bfbrdtn, ABfbrdtn
    side_top=ST, end_top={1: 93, 5: 89},
    side_rows=SIDE_85X,
    end_rows={1: END_85X,
              5: [(0, 0, "E_TOP"), (1, 5, "E_WALL"), (6, 8, "E_LOW"), (9, 9, "E_BEAM")]},
    doors=red_doors(5), door_rows=(0, 7),
    glass_extra=win_glass(1, 3, ST), diag_glass=glass_like, windscreen=True, fix=keep_dark,
)

# 954.2 (ABfbrdtn 795): the same body on Sim's ABfbrdtn drawing
B954A = dict(B954, name="954A", refs=[(SRC + "954.png", 1), (SRC + "954.png", 0)])

B054 = dict(
    name="054",
    refs=[(SRC + "054.png", 0)],
    side_top=ST, end_top={1: 89, 5: 89},
    side_rows=SIDE_85X,
    end_rows=[(0, 0, "E_TOP"), (1, 5, "E_WALL"), (6, 8, "E_LOW"), (9, 9, "E_BEAM")],
    doors={3: [(16, 19), (77, 81)], 7: [(39, 43), (101, 104)]}, door_rows=(0, 7),
    glass_extra=win_glass(1, 3, ST), diag_glass=glass_like, fix=keep_dark,
)

_cache = {}


BODY = {"954.2": "954A"}


def body(name):
    name = BODY.get(name, name)
    if name not in _cache:
        _cache[name] = Body(globals()["B" + name])
    return _cache[name]


# ------------------------------------------------------------ 842 / 843 liveries
STAINLESS = (178, 182, 184)      # N1 roof on 843/943/043 (ribbed stainless, reads light)
RC_ROOF2 = (176, 176, 168)       # red-cream roof (light grey / stainless)
UNDER = (38, 38, 40)
PLOUGH_Y = (235, 182, 22)
MASK = (24, 26, 30)              # 843: black mask over windscreens + gangway door
CABGLASS = (40, 46, 54)          # cab windscreens (dark, not lit)
UF_DARK = (46, 44, 44)
SOOT = (74, 80, 100)             # sapphire roof darkened by exhaust soot (854 N2 photos)


def by_k(table, default):
    """Colour by row offset k inside a zone: table {k: colour}."""
    return lambda c: table.get(c["k"], default)


def livery_84x(veh, name):
    if name in ("najbrt1", "najbrt2"):
        n2 = name == "najbrt2"
        spec = {
            "S_TOP": SKY, "S_WIN": SKY, "S_BELT": SAPPHIRE, "S_LOW": LGREY,
            "S_SKIRT": dk(LGREY, 0.62), "S_SOLE": UNDER, "S_DOOR": SAPPHIRE,
            "E_TOP": SKY, "E_WIN": SKY, "E_LOW": LGREY, "E_BEAM": PLOUGH_Y,
            "WSCREEN": MASK if veh == "843" else CABGLASS,
        }
        if veh == "842":
            # stripe crosses the front at the upper-headlamp level
            spec["E_BELOW"] = by_k({6: SKY}, SAPPHIRE)
            spec["E_LAMP"] = LGREY
        else:
            # 843 / 943: lamp pairs in the sky blue, stripe just below them
            spec["E_BELOW"] = SKY
            spec["E_LAMP"] = SKY
            spec["E_BELOW2"] = SAPPHIRE
        # gangway end walls: sky / stripe / grey like the side
        spec["E_WALL"] = lambda c: SKY if c["k"] <= 4 else (SAPPHIRE if c["k"] == 5 else LGREY)
        spec["ROOF_EDGE"] = N2_STRIPE if n2 else SKY
        roof = SAPPHIRE if n2 else (UMBRA if veh == "842" else STAINLESS)
        return spec, roof
    if name == "cervenokremova":
        spec = {
            "ROOF_EDGE": RC_RED,
            "S_TOP": RC_RED, "S_WIN": RC_RED, "S_BELT": RC_RED, "S_LOW": RC_CREAM,
            "S_SKIRT": dk(RC_RED, 0.7), "S_SOLE": UNDER, "S_DOOR": RC_RED,
            "E_TOP": RC_RED, "E_WIN": RC_RED, "E_BELOW": RC_RED, "E_LAMP": RC_RED,
            "E_BELOW2": RC_CREAM, "E_LOW": by_k({12: RC_RED}, RC_CREAM), "E_BEAM": PLOUGH_Y,
            "E_WALL": lambda c: RC_RED if c["k"] <= 5 else RC_CREAM,
            "WSCREEN": MASK if veh == "843" else CABGLASS,
        }
        return spec, RC_ROOF2
    raise KeyError(name)


def marks_84x(veh, name):
    cab = veh in ("842", "843", "943")
    if name in ("najbrt1", "najbrt2"):
        side = [(0.34, 0.04, 6, SAPPHIRE), (0.34, 0.04, 7, SAPPHIRE)]
        if cab:
            side += [(0.84, 0.06, 5, (225, 228, 228))]      # white number on the stripe
        end = [(0.5, 0.14, 10, SAPPHIRE)] if cab else []
        return side, end
    if name == "cervenokremova":
        side = [(0.34, 0.04, 6, BLACK), (0.34, 0.04, 7, BLACK)]
        end = [(0.5, 0.14, 10, BLACK)] if cab else []
        return side, end
    return [], []


def render_84x(veh, name):
    b = body(veh)
    spec, roof = livery_84x(veh, name)
    a = paint(b, spec)
    a = fill_fix_livery(b, a)
    a = recolor_lum(b, a, "ROOF", roof)
    s, e = marks_84x(veh, name)
    return add_marks(b, a, side=s, end=e)


# ------------------------------------------------------------ 854 / 954 / 054 liveries
def plough(c_body):
    """E_PLOUGH row: the plough's lower edge is yellow."""
    return lambda ctx: PLOUGH_Y


def livery_85x(name):
    if name == "najbrt2":
        return {
            "ROOF_EDGE": N2_STRIPE,
            "S_TOP": SKY, "S_WIN": SKY, "S_BELT": SAPPHIRE, "S_BAND": LGREY, "S_LOW": LGREY,
            "S_SOLE": SAPPHIRE, "S_DOOR": SAPPHIRE,
            "E_TOP": N2_STRIPE, "E_WIN": SKY, "E_BAND": LGREY, "E_LOW": SAPPHIRE, "E_BEAM": SAPPHIRE,
            "E_PLOUGH": plough(SAPPHIRE), "E_WALL": SAPPHIRE, "WSCREEN": CABGLASS,
        }, SAPPHIRE
    if name == "cervenokremova":
        return {
            "ROOF_EDGE": RC_RED,
            "S_TOP": RC_RED, "S_WIN": RC_RED, "S_BELT": RC_RED, "S_BAND": RC_CREAM, "S_LOW": RC_RED,
            "S_SOLE": UF_DARK, "S_DOOR": RC_RED,
            "E_TOP": RC_RED, "E_WIN": RC_RED, "E_BAND": RC_CREAM, "E_LOW": RC_RED, "E_BEAM": RC_RED,
            "E_PLOUGH": plough(RC_RED), "E_WALL": RC_RED, "WSCREEN": CABGLASS,
        }, RC_ROOF
    raise KeyError(name)


def marks_85x(name, veh):
    if name == "najbrt2":
        # sapphire ČD logo on the grey lower body, white number on the stripe
        side = [(0.30, 0.04, 5, SAPPHIRE), (0.30, 0.04, 6, SAPPHIRE), (0.62, 0.05, 4, (220, 224, 228))]
        end = [(0.5, 0.12, 4, SAPPHIRE)] if veh in ("854", "954") else []
        return side, end
    if name == "cervenokremova":
        side = [(0.30, 0.04, 5, BLACK), (0.30, 0.04, 6, BLACK)]
        end = [(0.5, 0.12, 4, BLACK)] if veh in ("854", "954") else []
        return side, end
    return [], []


# 954.2: the 1st class (15 seats, three open bays) fills the gangway end; the
# roof-edge line is yellow over it (vagonWEB drawing, photos of 795 2xx)
FIRST_END = 0.28


def from_gangway(c):
    """Position along a control car drawn cab-behind, 0 = gangway end, 1 =
    cab; None off the side faces."""
    col = c["col"]
    src = col if col in (3, 7) else warp.SIDE_SRC.get(col)
    if src is None:
        return None
    return 1 - c["u"] if src == 3 else c["u"]


def first_line(other):
    def f(c):
        g = from_gangway(c)
        return YELLOW if g is not None and 0 <= g < FIRST_END else other
    return f


def render_85x(veh, liv):
    b = body(veh)
    spec, roof = livery_85x(liv)
    if veh == "954.2":
        spec["ROOF_EDGE"] = first_line(spec["ROOF_EDGE"])
    a = paint(b, spec)
    a = fill_fix_livery(b, a)
    a = recolor_lum(b, a, "ROOF", SOOT if (liv == "najbrt2" and veh == "854") else roof)
    s, e = marks_85x(liv, veh)
    return add_marks(b, a, side=s, end=e)


# ------------------------------------------------------------ turning a car round
# screen pixels per carunit of travel, per direction column (w nw n ne e se s sw)
PX_PER_CU = [(-4, -2), (0, -2.83), (4, -2), (5.66, 0), (4, 2), (0, 2.83), (-4, 2), (-5.66, 0)]
T = (231, 255, 255)


def turn_round(a, length):
    """A sheet row -> the same car facing the other way: direction columns
    shifted by 4, head / tail lamps swapped, and the body moved so it sits
    (4 - length/2) carunits along travel again (turning flips that offset, so
    the move is 8 - length carunits forward)."""
    out = np.zeros_like(a); out[:] = T
    cu = 8 - length
    for c in range(8):
        src = a[:, ((c + 4) % 8) * 128:((c + 4) % 8 + 1) * 128]
        dx, dy = (int(round(v * cu)) for v in PX_PER_CU[c])
        ys, xs = np.where(~np.all(src == T, axis=-1))
        ny, nx = ys + dy, xs + dx
        ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
        assert ok.all(), f"turn_round pushes pixels out of tile {c}"
        out[:, c * 128:(c + 1) * 128][ny, nx] = src[ys, xs]
    v = (out[..., 0].astype(int) << 16) | (out[..., 1].astype(int) << 8) | out[..., 2]
    out[v == 0xFFFF53] = (0xFF, 0x21, 0x1D)
    out[v == 0xFF211D] = (0xFF, 0xFF, 0x53)
    return out


def render(veh, liv):
    if veh.endswith("-front"):
        return turn_round(render(veh[:-len("-front")], liv), 12)
    return render_85x(veh, liv) if veh in ("854", "954", "954.2", "054") else render_84x(veh, liv)


# ------------------------------------------------------------ families
FAMILIES = {
    # family dir: (sheet rows, {livery: cars that exist in it})
    "842": (["842", "054", "954", "954-front", "954.2", "954.2-front"],
            {"najbrt1": ["842"],
             "najbrt2": ["842", "054", "954", "954-front", "954.2", "954.2-front"],
             "cervenokremova": ["054", "954", "954-front", "954.2", "954.2-front"]}),
    "843": (["843", "043", "943"], {"najbrt1": ["843", "043", "943"], "najbrt2": ["843", "043", "943"],
                                     "cervenokremova": ["843", "043"]}),
    "854": (["854"], {"najbrt2": ["854"], "cervenokremova": ["854"]}),
}
BLANK = np.zeros((128, 1024, 3), np.uint8)
BLANK[:] = (231, 255, 255)


def run(families, prev=None):
    """Write the sheets of the given family dirs; with prev, 4x previews there."""
    for fam in families:
        rows, livs = FAMILIES[fam]
        for liv, present in livs.items():
            last = max(rows.index(v) for v in present)
            out = [render(v, liv) if v in present else BLANK for v in rows[:last + 1]]
            p = save_sheet(out, os.path.join(FAM, fam, "sprites", liv + ".png"))
            print("wrote", os.path.relpath(p, REPO))
            if prev:
                os.makedirs(prev, exist_ok=True)
                preview([p], os.path.join(prev, f"{fam}_{liv}.png"), 4)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
    unknown = [f for f in args if f not in FAMILIES]
    if unknown:
        sys.exit(f"unknown family dir(s): {', '.join(unknown)}")
    run(args or list(FAMILIES), prev)


if __name__ == "__main__":
    main()
