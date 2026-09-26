"""ČD 471 CityElefant (471 + 071 + 971) in its four 2026 liveries:
cityelefantcervena (the 2006 white / light-blue / red scheme), pidsedocervena,
najbrt1 and najbrt2 (colours: palette.py, research notes in liveries.md).

Body: the native pak128.CS 471 drawing by TommPa9 (CD_471_Esus_I/II/III, same
silhouette, three reference liveries), frozen in src/471/cd_471_esus.png, one
row per reference (II., I., III., II._071, I._071, III._071, II._971, I._971),
in source coordinates (the images extracted from the compiled paks sit 4 px
lower; they were shifted up once when frozen). Zones come from row bands of the pure views
(k = row under the roof: 0 roof-edge line, 1-3 upper deck, 4-6 between the
decks / end-section windows, 7-9 lower deck, 10 line, 11-12 skirt) and from
the car's segments along its length (end section, door, double-deck middle),
found from the doors of the Esus II drawing. Diagonal views through warp.py.
Changes to the native drawing beyond the livery: a thin grey pantograph instead
of the black blob, lit glass only in passenger windows, plain dark windscreens,
the round top lamp of the 471 cab as a headlight (dark on the 971), dark grey
gangway doors, a yellow plough, stray pixel islands removed.

  python tools/railpaint/cd_471.py [--preview DIR]

writes vehicle-rail/ceske-drahy/471/sprites/<livery>.png.
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warp
from body import Body, T, hexarr, lum, SIDE_COLS, END_COLS, DIAG_COLS
from paint import paint, save_sheet, unspecial, preview
from palette import (SAPPHIRE, SKY, LGREY, N2_STRIPE, UF_GREY, PID_GREY, PID_RED, PID_BLACK,
                     PID_DOOR, YELLOW, dk)

REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "vehicle-rail", "ceske-drahy", "471", "sprites")
SRC = os.path.join(HERE, "src", "471", "cd_471_esus.png")
SRC_ROWS = ["II.", "I.", "III.", "II._071", "I._071", "III._071", "II._971", "I._971"]


def up(name):
    """(frozen sheet, row) of one native reference drawing."""
    return SRC, SRC_ROWS.index(name)


# ------------------------------------------------------------------ colours
CABGLASS = (52, 58, 66)         # windscreen / cab side windows (never lit)
PANTO = (92, 97, 104)           # pantograph arms
PANTO_HI = (150, 155, 160)
BEAM = (40, 42, 44)

# CityElefant 2006
CE_BLUE = (90, 143, 196)
CE_RED = (210, 71, 47)
CE_SILVER = (213, 215, 212)
CE_WHITE = (230, 234, 234)
CE_SKIRT = (78, 90, 100)
CE_MASK = (86, 91, 97)
CE_ROOF = (200, 203, 204)


# ------------------------------------------------------------------ body
def cls(p):
    r, g, b = (int(v) for v in p)
    if b > r + 40 and b > g:
        return "blue"
    if r > g + 80 and r > b + 80:
        return "red"
    if r > 150 and g > 120 and b < 90:
        return "yellow"
    return "neutral"


GANG = [(0, 10, "E_GBODY"), (11, 13, "E_GBEAM")]
CAB = [(0, 2, "E_CAP"), (3, 4, "E_MASK"), (5, 7, "E_WIN"), (8, 9, "E_MASK2"), (10, 10, "E_LAMP"),
       (11, 11, "E_LOW"), (12, 12, "E_BEAM"), (13, 13, "E_PLOUGH")]
SIDE = [(0, 0, "S_L0"), (1, 3, "S_UP"), (4, 6, "S_MID"), (7, 9, "S_LOW"), (10, 10, "S_L1"),
        (11, 11, "S_SKIRT"), (12, 12, "S_SKIRT2")]

CARS = {
    "471": dict(refs=["II.", "I.", "III."], end_top={1: 94, 5: 87}, cab="F",
                end_rows={1: GANG, 5: CAB}),
    "071": dict(refs=["II._071", "I._071", "III._071"], end_top={1: 94, 5: 87}, cab=None,
                end_rows={1: GANG, 5: GANG}),
    "971": dict(refs=["II._971", "I._971"], end_top={1: 94, 5: 87}, cab="R",
                end_rows={1: CAB, 5: GANG}),
}


class B471(Body):
    def pure(self, col, top, rows, face):
        lab, K, U = super().pure(col, top, rows, face)
        Z = self.Z
        t = self.base[:, col * 128:(col + 1) * 128]
        v = hexarr(t)
        body = lab != Z["T"]
        grey6 = body & (v == 0x6B6B6B)
        lab[grey6] = Z["WSCREEN"] if face == "E" else Z["CABWIN"]
        if face == "E":
            # gangway: the black frame and the door inside it keep the base pixels
            gb = lab == Z["E_GBODY"]
            if gb.any():
                fr = np.where((lum(t[top + 3].astype(float)) < 30) & body[top + 3])[0]
                if len(fr):
                    g0, g1 = fr.min(), fr.max()
                    ys, xs = np.where(gb)
                    inside = (xs >= g0) & (xs <= g1) & (K[ys, xs] >= 3)
                    ys, xs = ys[inside], xs[inside]
                    dark = lum(t[ys, xs].astype(float)) < 60
                    lab[ys[dark], xs[dark]] = Z["FIX"]
                    lab[ys[~dark], xs[~dark]] = Z["GANGDOOR"]
            # the round top lamp of the cab front: a headlight on the 471, dark on the 971
            lamp = body & ((v == 0x4D4D4D) | (lab == Z["GLASS"])) & (K <= 3)
            lab[lamp] = Z["HEAD"] if (v[lamp] == 0x4D4D4D).any() else Z["LAMPDARK"]
        return lab, K, U

    def build(self):
        super().build()
        Z = self.Z
        v = hexarr(self.base)
        body = self.lab != Z["T"]
        # 0x6B6B6B in the diagonal views: windscreen on end faces, cab windows on the side
        g6 = body & (v == 0x6B6B6B)
        self.lab[g6 & (self.face == "E")] = Z["WSCREEN"]
        self.lab[g6 & (self.face != "E")] = Z["CABWIN"]
        top_lamp = body & (self.face == "E") & (self.K <= 3) & (self.K >= 0)
        self.lab[top_lamp & (v == 0x4D4D4D)] = Z["HEAD"]
        self.lab[top_lamp & (self.lab == Z["GLASS"])] = Z["LAMPDARK"]
        # pantograph: black pixels (in every reference) with the side face below them
        L = lum(self.refs.astype(float)).max(axis=0)
        blk = body & (L < 25)
        for col in range(8):
            sl = slice(col * 128, (col + 1) * 128)
            f = self.face[:, sl]
            b = blk[:, sl]
            sidey = np.where((f == "S").any(axis=1))[0]
            if not len(sidey):
                continue
            for x in range(128):
                ys = np.where(b[:, x])[0]
                if not len(ys):
                    continue
                below = np.where(f[:, x] == "S")[0]
                if not len(below):
                    below = np.where(f[:, x] == "E")[0]
                if not len(below):
                    continue
                for y in ys:
                    if y < below.min():
                        self.lab[y, col * 128 + x] = Z["PANTO"]
        self.classes = np.array([[cls(self.base[y, x]) for x in range(1024)] for y in range(128)])

    def shade(self, lo=0.6, hi=1.35):
        """Factor = pixel luminance / median luminance of the same colour class
        in the same zone of the pure views, median over the references."""
        n = len(self.refs)
        C = [np.array([[cls(self.refs[i][y, x]) for x in range(1024)] for y in range(128)]) for i in range(n)]
        # brightness: luminance for greys; the max channel for saturated colours, whose
        # lighter tints in the native diagonal views are desaturation, not light
        Lum = lum(self.refs.astype(float))
        V = self.refs.max(axis=-1).astype(float)
        L = np.stack([np.where(C[i] == "neutral", Lum[i], V[i]) for i in range(n)])
        pure = np.zeros((128, 1024), bool)
        for c in SIDE_COLS + END_COLS:
            pure[:, c * 128:(c + 1) * 128] = True
        facs = np.full((n, 128, 1024), np.nan)
        for zn, zi in self.Z.items():
            if zn in ("T", "FIX", "GLASS", "HEAD", "TAIL"):
                continue
            m = self.lab == zi
            if not m.any():
                continue
            mp = m & pure
            if zn in ("ROOF", "ROOF_EDGE", "PANTO"):
                mp = m & pure
            for i in range(n):
                for c in ("blue", "red", "yellow", "neutral"):
                    mc = m & (C[i] == c)
                    if not mc.any():
                        continue
                    ref = mp & (C[i] == c)
                    if ref.sum() < 3:
                        ref = mc
                    med = max(np.median(L[i][ref]), 1.0)
                    facs[i][mc] = L[i][mc] / med
        with np.errstate(all="ignore"):
            fac = np.nanmedian(facs, axis=0)
        fac[np.isnan(fac)] = 1.0
        # one light level per face and view; only clear highlights / shadows keep their own
        skip = [self.Z[z] for z in ("T", "FIX", "GLASS", "HEAD", "TAIL", "PANTO", "CABWIN", "WSCREEN", "LAMPDARK")]
        for col in range(8):
            sl = slice(col * 128, (col + 1) * 128)
            for face in ("S", "E", "R"):
                m = (self.face[:, sl] == face) & ~np.isin(self.lab[:, sl], skip)
                if m.sum() < 5:
                    continue
                f = fac[:, sl]
                med = np.median(f[m])
                keep = np.abs(f - med) > 0.16
                f[m & ~keep] = med
        return np.clip(fac, lo, hi)


def make_body(car):
    c = CARS[car]
    cfg = dict(
        name="471_" + car,
        refs=[up(r) for r in c["refs"]],
        base=0,
        side_top={3: 80, 7: 80},
        end_top=c["end_top"],
        side_rows=SIDE,
        end_rows=c["end_rows"],
        doors=find_doors, door_rows=(4, 12),
        glass_extra=glass_extra,
        diag_glass=lambda px: False,       # window frames of the diagonal views take the row zone
        extra_zones=["CABWIN", "WSCREEN", "PANTO", "LAMPDARK", "GANGDOOR"],
    )
    b = B471(cfg)
    b.car = car
    b.cab = c["cab"]
    b.geom = side_geometry(b)
    return b


def glass_extra(t, col):
    v = hexarr(t)
    return np.isin(v, (0x4A4A4A, 0x424242)).all(axis=0)


def find_doors(body, col, top):
    """Doors = runs of red at the skirt row (k 11) of the Esus II drawing."""
    t = body.base[:, col * 128:(col + 1) * 128]
    y = top + 11
    xs = [x for x in range(128) if cls(t[y, x]) == "red"]
    runs, cur = [], []
    for x in xs:
        if cur and x != cur[-1] + 1:
            runs.append(cur); cur = []
        cur.append(x)
    if cur:
        runs.append(cur)
    return [(r[0], r[-1]) for r in runs if len(r) >= 2]


def side_geometry(b):
    """Per pure side view: body x extent and the two door ranges."""
    g = {}
    for col in SIDE_COLS:
        t = b.base[:, col * 128:(col + 1) * 128]
        m = ~np.all(t == T, axis=-1)
        xs = np.where(m.any(axis=0))[0]
        g[col] = dict(x0=xs.min(), x1=xs.max(), doors=b.door_ranges[col])
    return g


def segment(b, col, u):
    """-> (seg, t): seg in endR, doorR, mid, doorF, endF; t = 0 at the door side
    of an end section -> 1 at the car end (for end sections), else 0."""
    src = col if col in SIDE_COLS else warp.SIDE_SRC[col]
    g = b.geom[src]
    x = g["x0"] + u * (g["x1"] - g["x0"])
    (a0, a1), (c0, c1) = g["doors"][0], g["doors"][-1]
    left_is_front = src == 7
    if x < a0:
        seg, t = "endL", (a0 - x) / max(1, a0 - g["x0"])
    elif x <= a1:
        seg, t = "doorL", 0
    elif x < c0:
        seg, t = "mid", 0
    elif x <= c1:
        seg, t = "doorR", 0
    else:
        seg, t = "endR", (x - c1) / max(1, g["x1"] - c1)
    if seg in ("endL", "doorL"):
        seg = seg.replace("L", "F" if left_is_front else "R")
    elif seg in ("endR", "doorR"):
        seg = seg[:-1] + ("R" if left_is_front else "F")
    return seg, t


def is_cab_section(b, seg):
    return (b.cab == "F" and seg == "endF") or (b.cab == "R" and seg == "endR")


def base_cls(b, ctx):
    return b.classes[ctx["y"], ctx["col"] * 128 + ctx["x"]]


def base_dark(b, ctx):
    p = b.base[ctx["y"], ctx["col"] * 128 + ctx["x"]]
    return lum(p.astype(float)) < 60


# ------------------------------------------------------------------ liveries
def livery_spec(b, name):
    """zone -> callable(ctx) for livery `name`."""

    def side(ctx):
        k = ctx["k"]
        seg, t = segment(b, ctx["col"], ctx["u"])
        c = base_cls(b, ctx)
        zone = ctx["zone"]
        if zone == "S_SKIRT2" and base_dark(b, ctx):
            return None
        if c == "yellow" and k == 4:
            return YELLOW
        door = zone == "S_DOOR"
        cab = is_cab_section(b, seg)
        end = seg.startswith("end")
        if name == "cityelefantcervena":
            if door:
                return CE_RED
            if zone in ("S_L0", "S_L1"):
                return CE_WHITE if c == "neutral" else (CE_RED if c == "red" else CE_BLUE)
            if zone in ("S_SKIRT", "S_SKIRT2"):
                return CE_SKIRT if c == "neutral" else CE_RED
            return {"blue": CE_BLUE, "red": CE_RED, "neutral": CE_SILVER}.get(c, CE_SILVER)
        if name == "pidsedocervena":
            if door:
                return PID_DOOR if k >= 7 else PID_GREY
            if end:
                if 4 <= k <= 6:
                    return PID_BLACK
                inner = t < (0.45 if cab else 0.5)
                return PID_RED if inner and k <= 11 else PID_GREY
            if 1 <= k <= 3 or 7 <= k <= 9:
                return PID_BLACK
            return PID_GREY
        if name == "najbrt1":
            if door:
                return SAPPHIRE
            if k <= 3:
                return LGREY
            if k <= 6:
                if cab and t > 0.58:
                    return SAPPHIRE
                return SKY
            if k == 7:
                return SAPPHIRE
            if k <= 10:
                return LGREY
            return UF_GREY
        if name == "najbrt2":
            if door:
                return SAPPHIRE
            line = 3 if end else 4
            if k < line:
                return SAPPHIRE
            if k == line:
                return N2_STRIPE
            if k <= 6:
                return SKY
            if k == 7:
                return SAPPHIRE
            if k <= 10:
                return LGREY
            return SAPPHIRE
        raise KeyError(name)

    def gang(ctx):
        """Gangway end faces: the colours of the outer end of the end sections."""
        k = ctx["k"]
        c = base_cls(b, ctx)
        if name == "cityelefantcervena":
            if k == 0:
                return CE_WHITE
            return {"blue": CE_BLUE, "red": CE_RED}.get(c, CE_SILVER)
        if name == "pidsedocervena":
            return PID_BLACK if 4 <= k <= 6 else PID_GREY
        if name == "najbrt1":
            return LGREY if k <= 3 else SKY if k <= 6 else SAPPHIRE if k == 7 else LGREY
        if name == "najbrt2":
            return (SAPPHIRE if k <= 2 else N2_STRIPE if k == 3 else SKY if k <= 6 else
                    SAPPHIRE if k == 7 else LGREY)

    def cab_front(ctx):
        k, u, zone = ctx["k"], ctx["u"], ctx["zone"]
        edge = u <= 0.02 or u >= 0.98
        if zone == "E_LAMP" and base_cls(b, ctx) == "yellow":
            return None
        if zone == "E_BEAM":
            return BEAM
        if zone == "E_PLOUGH":
            return YELLOW
        if name == "cityelefantcervena":
            if zone == "E_CAP":
                return CE_WHITE if k == 0 else CE_SILVER
            if zone == "E_LOW" or edge:
                return CE_SILVER
            return CE_MASK
        if name == "pidsedocervena":
            if zone == "E_CAP" or edge:
                return PID_GREY
            if zone in ("E_MASK", "E_WIN"):
                return PID_BLACK
            return PID_RED if 0.56 <= u <= 0.8 else PID_GREY
        if name == "najbrt1":
            if zone == "E_CAP":
                return LGREY
            if edge and k <= 7:
                return SAPPHIRE
            if zone == "E_LOW":
                return LGREY
            return SKY
        if name == "najbrt2":
            if k == 0 or (edge and k <= 3):
                return SAPPHIRE
            if k == 4:
                return N2_STRIPE
            if zone == "E_LOW":
                return LGREY
            if edge:
                return SKY
            return SKY

    roof = {"cityelefantcervena": CE_ROOF, "pidsedocervena": PID_GREY,
            "najbrt1": LGREY, "najbrt2": SAPPHIRE}[name]
    spec = {
        "ROOF": roof, "ROOF_EDGE": roof,
        "PANTO": (PANTO, "flat"),
        "CABWIN": (CABGLASS, "flat"),
        "LAMPDARK": ((70, 74, 80), "flat"),
        "HEAD": ((0xFF, 0xFF, 0x53), "flat"),     # incl. the round top lamp of the 471 cab
        "GANGDOOR": (66, 69, 73),
        "WSCREEN": lambda ctx: ((CABGLASS if ctx["k"] > 5 else dk(CABGLASS, 1.35)), "flat"),
        "E_GBODY": gang, "E_GBEAM": BEAM,
    }
    for z in ("S_L0", "S_UP", "S_MID", "S_LOW", "S_L1", "S_SKIRT", "S_SKIRT2", "S_DOOR"):
        spec[z] = side
    for z in ("E_CAP", "E_MASK", "E_WIN", "E_MASK2", "E_LAMP", "E_LOW", "E_BEAM", "E_PLOUGH"):
        spec[z] = cab_front
    return spec


LIVERIES = ["cityelefantcervena", "pidsedocervena", "najbrt1", "najbrt2"]


def render(b, name):
    a = paint(b, livery_spec(b, name))
    return drop_strays(a)


def drop_strays(a, min_px=12):
    """Clear tiny pixel islands the native drawing has far from the body."""
    from scipy import ndimage
    out = a.copy()
    for col in range(8):
        sl = slice(col * 128, (col + 1) * 128)
        m = ~np.all(out[:, sl] == T, axis=-1)
        lab, n = ndimage.label(m, structure=np.ones((3, 3)))
        for i in range(1, n + 1):
            r = lab == i
            if r.sum() < min_px:
                out[:, sl][r] = T
    return out


def run(prev=None):
    bodies = [make_body(c) for c in ("471", "071", "971")]
    os.makedirs(OUT, exist_ok=True)
    outs = []
    for name in LIVERIES:
        rows = [render(b, name) for b in bodies]
        p = save_sheet(rows, os.path.join(OUT, name + ".png"))
        outs.append(p)
        print("wrote", p)
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview(outs, os.path.join(prev, "p471.png"), z=3)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    prev = args[args.index("--preview") + 1] if "--preview" in args else None
    run(prev)


if __name__ == "__main__":
    main()
