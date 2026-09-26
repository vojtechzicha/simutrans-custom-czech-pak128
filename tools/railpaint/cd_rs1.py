"""ČD Stadler RS1 "RegioSpider" families 840, 841, 841.2 and 841.3.

Every livery is painted on one drawing: the pak128.CS CD_840 body by Lubak91
(from vehicle.motorak.840_841.pak, extracted with tools/pak_extract.py), frozen
in src/rs1/cd_840_rs1.png. Zones come from row rules in the pure views plus
colour touch-ups (fix()), and warp.py carries them to the diagonal views; the
upstream shading is kept.

Liveries (see liveries.md): Najbrt 1 / 2, Liberecký kraj (IDOL), Pardubický
kraj, DÚK zeleno-bílá, HzL krémovo-červená, PID šedo-červená, světle šedá.
FAMILIES says which family carries which.

Run:  python tools/railpaint/cd_rs1.py [family ...] [--preview DIR]
      (no family = all; writes vehicle-rail/ceske-drahy/<family>/sprites/*.png)
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warp
from body import Body, auto_doors, hexarr, lum, SIDE_COLS, END_COLS
from paint import paint, recolor_lum, add_marks, save_sheet, unspecial, shade, preview
from palette import SAPPHIRE, SKY, LGREY, N2_STRIPE, dk

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
SRC = os.path.join(HERE, "src", "rs1", "cd_840_rs1.png")

# ---------------------------------------------------------------- body ------
# Pure side view (ne / sw): roof rows 76-81 (A/C boxes over the doors), side
# face rows 82-92: 82 cantrail, 83-84 band above the windows, 85-89 window band,
# 90 stripe, 91-92 lower body, 93 skirt + bogies (kept).
# Pure end view: 88 (se) / 91 (nw) roof cap, then the windscreen frame, 4 rows of
# windscreen + the destination-display row, headlight row, lens row, the band
# under the lamps, 2 rows of lower front (coupler kept dark) and the skirt edge.
SIDE_ROWS = [(0, 0, "S_CANT"), (1, 1, "S_UP1"), (2, 2, "S_UP2"), (3, 7, "S_WIN"), (8, 8, "S_BELT"),
             (9, 9, "S_LOW1"), (10, 10, "S_LOW2")]
END_ROWS = [(0, 0, "E_CAP"), (1, 1, "E_WFRAME"), (2, 6, "E_WIN"), (7, 7, "E_LAMP"), (8, 8, "E_LAMP2"),
            (9, 9, "E_BAND"), (10, 11, "E_LOW"), (12, 12, "E_SKIRT")]
EXTRA = ["S_DOORF", "S_WFRAME", "DISPLAY", "CABGLASS", "ROOF_BOX", "E_LOWD", "LENS", "WSCREEN"]


def glass_none(t, col):
    return np.zeros(t.shape[1:3], bool)


def fix(body, col):
    """Colour-based zones on top of the geometric ones (all views)."""
    Z = body.Z
    sl = slice(col * 128, (col + 1) * 128)
    lab = body.lab[:, sl]
    b = body.base[:, sl].astype(int)
    v = hexarr(b)
    L = lum(b.astype(float))
    chroma = b.max(axis=-1) - b.min(axis=-1)
    face = body.face[:, sl]
    body_px = lab != Z["T"]
    # destination displays (special green) -> plain amber
    lab[np.isin(v, (0x01DD01, 0x00DE00)) & body_px] = Z["DISPLAY"]
    # cab glass: windscreen and cab side windows are the non-darkening grey
    lab[(v == 0x6B6B6B) & body_px] = Z["CABGLASS"]
    # passenger glass: neutral dark greys inside the window band and the doors
    win = (lab == Z["S_WIN"]) | (lab == Z["S_DOOR"])
    glass = win & (chroma < 18) & (L >= 45) & (L <= 100) & (v != 0x3A3A3A)
    lab[glass] = Z["GLASS"]
    # lens of the lower lamp in the front mask
    lab[(v == 0x57656F) & (face == "E")] = Z["LENS"]
    lab[(v == 0x57656F) & (face != "E") & body_px & (lab != Z["GLASS"])] = Z["LENS"]
    # windscreen frame / glass rows: neutral pixels stay as drawn (dark frame)
    for z in ("E_WFRAME", "E_WIN"):
        lab[(lab == Z[z]) & (chroma < 20)] = Z["WSCREEN"]
    # black bottom frame of the big windows (drawn in the stripe row)
    lab[(lab == Z["S_BELT"]) & (L < 30)] = Z["S_WFRAME"]
    # dark coupler / buffer area of the lower front
    lab[(lab == Z["E_LOW"]) & (L < 75)] = Z["E_LOWD"]
    # light A/C boxes on the roof
    lab[((lab == Z["ROOF"]) | (lab == Z["ROOF_EDGE"])) & (chroma < 10) & (L >= 145) & (L < 175)] = Z["ROOF_BOX"]
    # door frame columns (outermost column of each door range) -> S_DOORF
    dm = lab == Z["S_DOOR"]
    if dm.any():
        src = col if col in SIDE_COLS else warp.SIDE_SRC.get(col)
        if src is not None:
            st = body.base[:, src * 128:(src + 1) * 128]
            m = ~np.all(st == np.array((231, 255, 255)), axis=-1)
            xs = np.where(m.any(axis=0))[0]
            x0, x1 = xs.min(), xs.max()
            edges = set()
            for a, bb in body.door_ranges[src]:
                edges |= {a, bb}
            ys, xs2 = np.where(dm)
            for y, x in zip(ys, xs2):
                sx = int(round(x0 + body.U[y, col * 128 + x] * (x1 - x0))) if col not in SIDE_COLS else x
                if sx in edges:
                    lab[y, x] = Z["S_DOORF"]
    body.lab[:, sl] = lab


RS1 = dict(
    name="rs1",
    refs=[(SRC, 0)],
    side_top={3: 82, 7: 82}, end_top={1: 91, 5: 88},
    side_rows=SIDE_ROWS, end_rows=END_ROWS, extra_zones=EXTRA,
    doors=auto_doors(9, dark=80), door_rows=(0, 10),
    glass_extra=glass_none,
    fix=fix,
)

_body = None


def body():
    global _body
    if _body is None:
        _body = Body(RS1)
    return _body


# -------------------------------------------------------------- colours -----
LIGHT_ROOF = (198, 202, 205)
DOOR_BLUE = (38, 66, 138)       # Najbrt door leaves on RS1: a darker blue than the body
YELLOW = (238, 196, 24)          # front skirt edge
AMBER = (240, 160, 24)           # LED destination display (plain, not special)
LENS_GREY = (196, 200, 204)
WHITE = (240, 241, 243)
DARK = (46, 48, 52)

# Liberecký kraj / IDOL
LK_RED = (200, 32, 30)
LK_ROOF = (204, 207, 210)
# Pardubický kraj on RS1
PK_NAVY = (33, 58, 128)
PK_RED = (228, 64, 46)
PK_WHITE = (236, 238, 241)
PK_YELLOW = (230, 190, 0)
# Doprava Ústeckého kraje
DUK_GREEN = (92, 178, 74)
DUK_GREY = (220, 224, 226)
DUK_ROOF = (198, 202, 205)
# Hohenzollerische Landesbahn (HzL)
HZL_CREAM = (232, 224, 196)
HZL_RED = (184, 36, 60)
HZL_ROOF = (200, 198, 188)
# PID
PID_GREY = (205, 209, 213)
PID_RED = (216, 64, 58)
PID_DARK = (52, 54, 58)
PID_LOWER = (92, 96, 100)
# plain light grey
LG = (210, 214, 217)

DOOR_L, DOOR_R = 0.24, 0.30      # door 1 in w (= distance from the nearer end, 0..0.5)
DOORS_U = [(0.242, 0.303), (0.697, 0.758)]   # both doors in u (pure side view x, 0..1)


def w_of(c):
    return min(c["u"], 1 - c["u"])


def edge_col(c):
    """True for the outermost columns of the pure end view (the rounded
    corners where the side wraps round the cab)."""
    return c["u"] <= 0.001 or c["u"] >= 0.999


def in_panel(u, k, lean=0.05, m=0.026):
    """HzL / DÚK door panels: parallelograms round each door, constant width,
    top shifted to the right in both side views ('/' - the scheme looks the same
    from either side, photo 841.222)."""
    t = max(0.0, min(1.0, k / 10.0))
    for d0, d1 in DOORS_U:
        if d0 - m - lean * t <= u <= d1 + m + lean * (1 - t):
            return True
    return False


# ------------------------------------------------------------- liveries -----
def scaled(v, f):
    """Colour or callable, brightened / darkened by f."""
    if callable(v):
        return lambda c: (lambda r: dk(r, f) if isinstance(r, tuple) and len(r) == 3 else r)(v(c))
    return dk(v, f)


def common(spec):
    """Split the row-group keys into the per-row zones (so the upstream paint
    differences between rows don't read as shading) and add the fixed parts.
    The top row of the band above the windows gets a slight highlight: the
    body side curves in towards the roof there."""
    if "S_UP" in spec:
        v = spec.pop("S_UP")
        spec["S_UP1"], spec["S_UP2"] = scaled(v, 1.06), v
    if "S_LOW" in spec:
        v = spec.pop("S_LOW")
        spec["S_LOW1"], spec["S_LOW2"] = v, v
    spec.setdefault("DISPLAY", (AMBER, "flat"))
    spec.setdefault("LENS", (LENS_GREY, "flat"))
    return spec


def najbrt(n2):
    roof = SAPPHIRE if n2 else LIGHT_ROOF
    return common({
        "S_CANT": N2_STRIPE if n2 else LIGHT_ROOF,
        "S_UP": SKY, "S_WIN": SKY, "S_BELT": SAPPHIRE, "S_LOW": LGREY,
        "S_DOOR": DOOR_BLUE, "S_DOORF": SKY,
        "E_CAP": roof, "E_WFRAME": SKY, "E_WIN": SKY, "E_LAMP": SKY, "E_LAMP2": SKY,
        "E_BAND": SAPPHIRE, "E_LOW": LGREY, "E_SKIRT": YELLOW,
    }), roof


def libereckykraj():
    def low(c):
        w = w_of(c)
        # the red bottom band sweeps up into the cab front at both ends
        lim = 10 - max(0.0, (0.10 - w) / 0.10) * 3.2
        return LK_RED if c["k"] >= lim else WHITE

    def edge_white(c):
        return WHITE if edge_col(c) else LK_RED
    return common({
        "S_CANT": WHITE, "S_UP": WHITE, "S_WIN": WHITE, "S_BELT": low, "S_LOW": low,
        "S_DOOR": LK_RED, "S_DOORF": LK_RED,
        "E_CAP": LK_RED, "E_WFRAME": LK_RED, "E_WIN": LK_RED,
        "E_LAMP": edge_white, "E_LAMP2": edge_white, "E_BAND": edge_white,
        "E_LOW": LK_RED, "E_LOWD": dk(LK_RED, 0.55), "E_SKIRT": YELLOW,
    }), LK_ROOF


def pardubickykraj():
    def edge_white(c):
        return PK_WHITE if not edge_col(c) else PK_WHITE
    return common({
        "S_CANT": PK_RED, "S_UP": PK_WHITE, "S_WIN": PK_WHITE, "S_BELT": PK_WHITE,
        "S_LOW": lambda c: PK_NAVY if c["k"] >= 10 else PK_WHITE,
        "S_DOOR": PK_YELLOW, "S_DOORF": PK_NAVY,
        "E_CAP": PK_NAVY, "E_WFRAME": PK_WHITE, "E_WIN": PK_WHITE,
        "E_LAMP": PK_WHITE, "E_LAMP2": PK_WHITE, "E_BAND": PK_NAVY,
        "E_LOW": PK_NAVY, "E_LOWD": dk(PK_NAVY, 0.6), "E_SKIRT": YELLOW,
    }), PK_NAVY


def panel_livery(body_c, panel_c, door_c, low_c, low_rows, roof, front):
    """DÚK / HzL layout: body colour with slanted panels round the doors and a
    full-length band at the bottom."""
    def side(c):
        if c["k"] >= low_rows:
            return low_c
        return panel_c if in_panel(c["u"], c["k"]) else body_c

    spec = {"S_CANT": roof, "S_UP": side, "S_WIN": side, "S_BELT": side, "S_LOW": side,
            "S_DOOR": door_c, "S_DOORF": side}
    spec.update(front)
    return common(spec), roof


def dukzelenobila():
    def mask(c):
        return DUK_GREEN if edge_col(c) else DUK_GREY
    front = {"E_CAP": DUK_GREY, "E_WFRAME": mask, "E_WIN": mask, "E_LAMP": mask, "E_LAMP2": mask,
             "E_BAND": mask, "E_LOW": DUK_GREY, "E_SKIRT": DUK_GREY}
    return panel_livery(DUK_GREEN, DUK_GREY, DUK_GREY, DUK_GREY, 10, DUK_ROOF, front)


def hzlkremovacervena():
    front = {"E_CAP": HZL_CREAM, "E_WFRAME": HZL_CREAM, "E_WIN": HZL_CREAM, "E_LAMP": HZL_CREAM,
             "E_LAMP2": HZL_CREAM, "E_BAND": HZL_RED, "E_LOW": HZL_RED, "E_LOWD": dk(HZL_RED, 0.5),
             "E_SKIRT": HZL_RED}
    return panel_livery(HZL_CREAM, HZL_RED, HZL_RED, HZL_RED, 10, HZL_ROOF, front)


def pidsedocervena():
    def block(c):
        w = w_of(c)
        return 0.075 <= w <= DOOR_L - 0.012

    def side(c):
        if block(c):
            return PID_DARK if c["zone"] == "S_WIN" else PID_RED
        return PID_DARK if c["zone"] == "S_WIN" else PID_GREY

    def panel(c):
        # red vertical panel right of centre on both cab fronts
        return PID_RED if 0.55 <= c["u"] <= 0.82 and not edge_col(c) else PID_GREY
    return common({
        "S_CANT": PID_GREY, "S_UP": side, "S_WIN": side, "S_BELT": side, "S_LOW": side,
        "S_DOOR": PID_GREY, "S_DOORF": side,
        "E_CAP": PID_GREY, "E_WFRAME": PID_GREY, "E_WIN": PID_GREY,
        "E_LAMP": panel, "E_LAMP2": panel, "E_BAND": panel,
        "E_LOW": lambda c: PID_RED if 0.55 <= c["u"] <= 0.82 and not edge_col(c) else PID_LOWER,
        "E_SKIRT": YELLOW,
    }), dk(PID_GREY, 0.95)


def svetlesheda():
    return common({
        "S_CANT": LG, "S_UP": LG, "S_WIN": LG, "S_BELT": LG, "S_LOW": LG,
        "S_DOOR": LG, "S_DOORF": LG,
        "E_CAP": LG, "E_WFRAME": LG, "E_WIN": LG, "E_LAMP": LG, "E_LAMP2": LG,
        "E_BAND": LG, "E_LOW": (78, 80, 84), "E_SKIRT": YELLOW,
    }), dk(LG, 0.95)


# ------------------------------------------------------------ marks ---------
def marks(name):
    """(side marks, front marks): (u from the rear, width, k, colour)."""
    if name in ("najbrt1", "najbrt2"):
        side = [(0.55, 0.05, 9, SAPPHIRE), (0.62, 0.06, 9, (64, 100, 170))]
        return side, [(0.62, 0.12, 7, WHITE)]
    if name == "libereckykraj":
        # red IDOL rings behind each cab (the route-line graphics are too fine for 128 px)
        side = [(0.035, 0.02, 5, LK_RED), (0.035, 0.02, 7, LK_RED), (0.965, 0.02, 5, LK_RED), (0.965, 0.02, 7, LK_RED)]
        return side, [(0.62, 0.12, 7, WHITE)]
    if name == "pardubickykraj":
        side = [(0.62, 0.03, 9, (210, 40, 40)), (0.66, 0.04, 9, PK_NAVY), (0.45, 0.06, 9, (60, 90, 170))]
        return side, [(0.62, 0.12, 8, PK_NAVY)]
    if name == "dukzelenobila":
        return [(0.55, 0.05, 9, WHITE)], [(0.62, 0.12, 7, DARK)]
    if name == "hzlkremovacervena":
        return [(0.55, 0.06, 9, DARK)], [(0.62, 0.12, 7, DARK)]
    if name == "pidsedocervena":
        return [(0.60, 0.04, 9, (48, 50, 54)), (0.40, 0.04, 9, PID_RED)], [(0.68, 0.08, 7, WHITE)]
    if name == "svetlesheda":
        return [(0.55, 0.05, 9, DARK)], [(0.62, 0.12, 7, DARK)]
    return [], []


LIVERIES = {
    "najbrt1": lambda: najbrt(False),
    "najbrt2": lambda: najbrt(True),
    "libereckykraj": libereckykraj,
    "pardubickykraj": pardubickykraj,
    "dukzelenobila": dukzelenobila,
    "hzlkremovacervena": hzlkremovacervena,
    "pidsedocervena": pidsedocervena,
    "svetlesheda": svetlesheda,
}

FAMILIES = {
    "840": ["najbrt1", "libereckykraj"],
    "841": ["najbrt1"],
    "841_2": ["dukzelenobila", "hzlkremovacervena", "pardubickykraj", "pidsedocervena", "najbrt2", "svetlesheda"],
    "841_3": ["pidsedocervena"],
}


def render(name):
    b = body()
    spec, roof = LIVERIES[name]()
    a = paint(b, spec)
    a = recolor_lum(b, a, "ROOF", roof)
    a = recolor_lum(b, a, "ROOF_EDGE", roof, ref_lum=np.median(lum(b.base.astype(float))[b.lab == b.Z["ROOF"]]))
    box = roof if name not in ("pardubickykraj",) else (232, 234, 236)
    if name in ("najbrt2",):
        box = SAPPHIRE
    a = recolor_lum(b, a, "ROOF_BOX", box, ref_lum=np.median(lum(b.base.astype(float))[b.lab == b.Z["ROOF_BOX"]]))
    sm, em = marks(name)
    a = add_marks(b, a, side=sm, end=em)
    # CABGLASS / WSCREEN keep the drawn grey but must not stay special
    return unspecial(a)


def main(argv):
    """Write the sheets of the given families (all when none are given)."""
    fams = [a for a in argv if not a.startswith("--") and a in FAMILIES]
    pv = argv[argv.index("--preview") + 1] if "--preview" in argv else None
    fams = fams or list(FAMILIES)
    rendered, written = {}, []
    for fam in fams:
        d = os.path.join(FAM, fam, "sprites")
        os.makedirs(d, exist_ok=True)
        for l in FAMILIES[fam]:
            if l not in rendered:
                rendered[l] = render(l)
            written.append(save_sheet([rendered[l]], os.path.join(d, f"{l}.png")))
            print("wrote", written[-1])
    if pv:
        os.makedirs(pv, exist_ok=True)
        preview(written, os.path.join(pv, "rs1.png"), z=3)
    return written


if __name__ == "__main__":
    main(sys.argv[1:])
