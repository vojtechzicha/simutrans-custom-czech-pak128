"""ČD PESA LINK II families: 844 RegioShark and 847 RegioFox.

One body drawing (pak128_czr CZR-CD-847 / 847b, shifted up 4 px for the rail
image_offset [0, 4]) carries every livery of both classes. Row 0 = front
section (cab ahead), row 1 = rear section (cab behind); the two are mirror
images drawn at their own tile positions, so both rows are kept.

Frozen inputs in src/pesa/ (the upstream-derived sheets as the repo shipped
them before this repaint): 847_blue.png (base drawing, Najbrt-banded), 844_teal.png
(the upstream teal 844, zone reference) and 847_pid.png (the upstream PID 847,
a 1 px-shifted variant of the same drawing, aligned here at run time; it gives
the doors, the cab hood and the PID red-block positions).

Liveries (see liveries.md): 844 Najbrt 2, Pardubický kraj, Plzeňský kraj;
847 Najbrt 2, PID šedo-červená, Plzeňský kraj, Pardubický kraj.

Run:  python tools/railpaint/cd_pesa.py [844|847 ...] [--preview DIR] [--zones DIR]
      (no family = both; writes vehicle-rail/ceske-drahy/<family>/sprites/*.png)
"""
import io, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from body import Body, T, hexarr, lum, SIDE_COLS, END_COLS, DIAG_COLS
from paint import paint, recolor_lum, add_marks, save_sheet, unspecial, shade, preview
import palette as P

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
SRC_N2 = os.path.join(HERE, "src", "pesa", "847_blue.png")
SRC_844 = os.path.join(HERE, "src", "pesa", "844_teal.png")
SRC_PID = os.path.join(HERE, "src", "pesa", "847_pid.png")

# PID drawing -> blue drawing: (row, col) -> (dx, dy)
PID_SHIFT = {(0, 2): (0, -1), (0, 4): (1, 0), (0, 5): (0, -1), (1, 6): (0, -1)}


def aligned_pid():
    """The upstream PID sheet aligned to the blue drawing, as PNG bytes:
    per-view shifts, then residual silhouette differences fixed (outside the
    blue silhouette -> background, holes inside it -> the blue pixel)."""
    a = np.array(Image.open(SRC_PID).convert("RGB"))
    n = np.array(Image.open(SRC_N2).convert("RGB"))
    out = a.copy()
    for (r, c), (dx, dy) in PID_SHIFT.items():
        t = a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128]
        out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = np.roll(np.roll(t, dy, 0), dx, 1)
    mb = ~np.all(n == T, axis=2)
    mp = ~np.all(out == T, axis=2)
    out[~mb] = T
    out[mb & ~mp] = n[mb & ~mp]
    buf = io.BytesIO()
    Image.fromarray(out).save(buf, format="PNG")
    return buf.getvalue()


SIDE_ROWS = [(0, 0, "S_TOP"), (1, 5, "S_WIN"), (6, 6, "S_BELT"), (7, 8, "S_LOW"), (9, 10, "S_SKIRT")]
CAB_ROWS = [(0, 4, "E_WIN"), (5, 8, "E_PANEL"), (9, 9, "E_LAMP"), (10, 12, "E_LOW"), (13, 15, "E_GRILLE"),
            (16, 16, "E_EDGE")]
JOINT_ROWS = [(0, 0, "J_TOP"), (1, 7, "J_WALL")]

def cls_of(c):
    """Colour class of an upstream pixel: navy / sky / lgrey / dark / roof /
    yellow / black / other."""
    r, g, b = int(c[0]), int(c[1]), int(c[2])
    l = 0.299 * r + 0.587 * g + 0.114 * b
    if (r, g, b) == (231, 255, 255):
        return "T"
    if r > 200 and g > 150 and b < 60:
        return "yellow"
    if max(r, g, b) < 12:
        return "black"
    if b > 140 and g > 60 and r < 60:
        return "sky"
    if b > r + 25 and l < 80:
        return "navy"
    if 8 <= b - r < 40 and l > 100:
        return "lgrey"
    if max(r, g, b) - min(r, g, b) < 12:
        return "grey"
    return "other"


def classes(t):
    return np.array([[cls_of(t[y, x]) for x in range(t.shape[1])] for y in range(t.shape[0])])


def refine(body, col):
    """Colour-driven touch-ups of the rule zones (runs per view). The blue
    upstream (ref 0) says which pixels are painted and in which band; the PID
    upstream (ref 2) marks doors (black) and the cab hood (grey)."""
    Z = body.Z
    sl = slice(col * 128, (col + 1) * 128)
    lab, K, U, face = body.lab[:, sl], body.K[:, sl], body.U[:, sl], body.face[:, sl]
    n = hexarr(body.refs[0][:, sl])
    nc = classes(body.refs[0][:, sl])
    pc = classes(body.refs[2][:, sl])
    p = hexarr(body.refs[2][:, sl])
    for y in range(128):
        for x in range(128):
            z = body.zones[lab[y, x]]
            if z == "T":
                continue
            nv, c, pv = int(n[y, x]), nc[y, x], int(p[y, x])
            f = face[y, x]
            if nv in (0x6B6B6B, 0x6C6C6C) and f != "E":
                lab[y, x] = Z["CABGLASS"]           # cab side / door windows, not lit
                continue
            if z in ("GLASS", "HEAD", "TAIL"):
                continue
            if f == "S" and (z.startswith("S_") or z == "FIX"):
                # the upstream drawing already carries the Najbrt banding, so
                # its colour decides the band; K only splits the navy parts
                k = K[y, x]
                if c == "black":
                    lab[y, x] = Z["FIX"]
                elif c == "navy" and pc[y, x] == "black" and k >= 1:
                    lab[y, x] = Z["S_DOOR"]
                elif c == "navy":
                    lab[y, x] = Z["S_TOP"] if k <= 0 else Z["S_HOOD"] if k <= 4 else                         Z["S_BELT"] if k <= 7 else Z["S_SKIRT"]
                elif c == "sky":
                    lab[y, x] = Z["S_WIN"]
                elif c == "lgrey":
                    lab[y, x] = Z["S_LOW"] if k >= 5 else Z["S_CABLOW"]
                elif c == "grey" and k >= 6:
                    lab[y, x] = Z["S_SKIRT"]        # underframe covers / powerpack
                elif c in ("grey", "other") and z in ("S_WIN", "S_TOP", "S_BELT"):
                    lab[y, x] = Z["FIX"]
            elif f == "E" and (z.startswith("E_") or z == "FIX"):
                # cab end, top to bottom (k from the end face): hood sides,
                # black windscreen band (k <= 4), ČD panel (6c6c6c, k 5-8),
                # lamp band (k 9-12: light sides, navy centre), lower front
                # (3b3b3b sides, k 13-14) around the coupler (4c4c4c), skirt
                # (4c4c4c, k 15) and the yellow edge
                k = K[y, x]
                if nv in (0x3B3B3B, 0x4E4E4E):
                    lab[y, x] = Z["WSCREEN"] if k <= 8 else Z["E_LOWFRONT"]
                elif nv in (0x6C6C6C, 0x6B6B6B):
                    lab[y, x] = Z["E_PANEL"]
                elif nv == 0x4C4C4C:
                    lab[y, x] = Z["E_COUPLER"] if k <= 14 else Z["E_SKIRT"]
                elif c == "yellow":
                    lab[y, x] = Z["E_EDGE"]
                elif c == "lgrey":
                    lab[y, x] = Z["E_BANDSIDE"]
                elif c == "navy":
                    if 9 <= k <= 12:
                        # the hood edge continues down the outer corners
                        edge = x == 0 or x == 127 or nc[y, x - 1] == "T" or nc[y, x + 1] == "T"
                        lab[y, x] = Z["E_HOOD"] if edge else Z["E_BANDMID"]
                    else:
                        lab[y, x] = Z["E_HOOD"]
                elif c == "sky":
                    lab[y, x] = Z["E_PANEL"]
                elif c in ("grey", "black") and k >= 13:
                    lab[y, x] = Z["E_COUPLER"]
            if z in ("J_TOP", "J_WALL"):
                # the end wall at the Jakobs joint wears the side colours
                lab[y, x] = {"sky": Z["S_WIN"], "navy": Z["S_BELT"], "lgrey": Z["S_LOW"]}.get(c, Z["FIX"])
            if f == "R" or z in ("ROOF", "ROOF_EDGE"):
                if c == "navy":
                    # side walls seen edge-on in the end views, hood tops
                    lab[y, x] = Z["S_HOOD"] if f != "E" else Z["E_HOOD"]
    # livery-coloured pixels the warp left unmapped (joint / cab edges of the
    # diagonal views): take the zone of the nearest mapped pixel of the same
    # colour class, else a default by class
    painted = ("navy", "sky", "lgrey", "yellow")
    ys, xs = np.where(lab == Z["FIX"])
    for y, x in zip(ys, xs):
        c = nc[y, x]
        if c not in painted:
            continue
        best = None
        for r in (1, 2, 3):
            cand = [(y + dy, x + dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
                    if 0 <= y + dy < 128 and 0 <= x + dx < 128 and nc[y + dy, x + dx] == c
                    and body.zones[lab[y + dy, x + dx]] not in ("FIX", "T", "GLASS")]
            if cand:
                best = min(cand, key=lambda q: abs(q[0] - y) + abs(q[1] - x))
                break
        if best:
            lab[y, x], K[y, x], U[y, x], face[y, x] = lab[best], K[best], U[best], face[best]
        else:
            lab[y, x] = {"sky": Z["S_WIN"], "navy": Z["S_BELT"], "lgrey": Z["S_LOW"]}.get(c, Z["E_EDGE"])
    lower_bands(body, col, lab, nc)
    body.lab[:, sl] = lab


SIDE_SLOPE = {0: 0.5, 2: -0.5, 3: 0.0, 4: 0.5, 6: -0.5, 7: 0.0}
KEEP = ("S_DOOR", "GLASS", "CABGLASS", "HEAD", "TAIL", "S_HOOD", "S_CABLOW", "T")


def lower_bands(body, col, lab, nc):
    """The lower side, per screen column (a vertical line on the side face in
    every view): the navy stripe under the windows, two rows of the light
    lower band, then one row of the bottom band (the upstream underframe
    covers); anything lower is underframe. The stripe row is found where the
    window band meets the light band; elsewhere (doors, windows cutting the
    stripe) it comes from the straight line through the found rows."""
    if col not in SIDE_SLOPE:
        return
    Z = body.Z
    zones = body.zones
    face = body.face[:, col * 128:(col + 1) * 128]
    s = SIDE_SLOPE[col]
    found = {}
    for x in range(128):
        ys = np.where(face[:, x] == "S")[0]
        for y in ys:
            if y < 1 or y > 125:
                continue
            above = nc[y - 1, x] == "sky" or zones[lab[y - 1, x]] in ("GLASS",)
            if nc[y, x] == "navy" and above and nc[y + 1, x] == "lgrey" and zones[lab[y, x]] != "S_DOOR":
                found[x] = y
                break
    if not found:
        return
    off = np.median([y - s * x for x, y in found.items()])
    uc = ucab(body, "front" if body.name == "pesa_front" else "rear")[:, col * 128:(col + 1) * 128]
    for x in range(128):
        ys = np.where(face[:, x] == "S")[0]
        if not len(ys):
            continue
        yb = found.get(x)
        if yb is None or abs(yb - (off + s * x)) > 1.01:
            yb = int(np.floor(off + s * x + 0.5))
        # the bottom band sweeps up toward the cab
        u = uc[min(127, yb + 1), x]
        rows = [(0, "S_BELT"), (1, "S_LOW"), (2, "S_LOW"), (3, "S_SKIRT")]
        if u >= 0.955:
            rows = [(0, "S_BELT"), (1, "S_LOW"), (2, "S_SKIRT"), (3, "S_SKIRT")]
        if u >= 0.975:
            rows = [(0, "S_BELT"), (1, "S_SKIRT"), (2, "S_SKIRT"), (3, "S_SKIRT")]
        for dy, zn in rows:
            y = yb + dy
            if not (0 <= y < 128) or face[y, x] != "S" or nc[y, x] in ("black", "T"):
                continue
            if zones[lab[y, x]] in KEEP:
                continue
            lab[y, x] = Z[zn]
        for y in range(yb + 4, 128):
            if face[y, x] == "S" and zones[lab[y, x]] in ("S_LOW", "S_SKIRT", "S_BELT", "S_WIN"):
                lab[y, x] = Z["FIX"]


def cfg_front(refs):
    return dict(
        name="pesa_front", refs=refs, base=0,
        side_top={3: 83, 7: 82}, end_top={1: 88, 5: 82},
        side_rows=SIDE_ROWS,
        end_rows={1: JOINT_ROWS, 5: CAB_ROWS},
        extra_zones=["S_HOOD", "S_CABLOW", "CABGLASS", "WSCREEN", "E_HOOD", "E_BANDSIDE", "E_BANDMID",
                     "E_LOWFRONT", "E_COUPLER", "E_SKIRT", "E_EDGE"],
        fix=refine,
    )


def cfg_rear(refs):
    return dict(
        name="pesa_rear", refs=refs, base=0,
        side_top={3: 82, 7: 83}, end_top={1: 80, 5: 90},
        side_rows=SIDE_ROWS,
        end_rows={1: CAB_ROWS, 5: JOINT_ROWS},
        extra_zones=["S_HOOD", "S_CABLOW", "CABGLASS", "WSCREEN", "E_HOOD", "E_BANDSIDE", "E_BANDMID",
                     "E_LOWFRONT", "E_COUPLER", "E_SKIRT", "E_EDGE"],
        fix=refine,
    )


_bodies = {}


def bodies():
    if not _bodies:
        pid = aligned_pid()
        refs0 = [(SRC_N2, 0), (SRC_844, 0), (io.BytesIO(pid), 0)]
        refs1 = [(SRC_N2, 1), (SRC_844, 1), (io.BytesIO(pid), 1)]
        _bodies["front"] = Body(cfg_front(refs0))
        _bodies["rear"] = Body(cfg_rear(refs1))
        for bd in _bodies.values():
            flat_shade(bd)
    return _bodies


# zones whose pixels were re-banded from the upstream colours: the upstream
# per-pixel brightness there belongs to a different band (e.g. the dark
# underframe covers now painted light grey), so they are painted flat
FLAT = ("S_TOP", "S_WIN", "S_BELT", "S_LOW", "S_SKIRT", "S_DOOR", "S_HOOD", "S_CABLOW",
        "E_HOOD", "E_PANEL", "E_BANDSIDE", "E_BANDMID", "E_LOWFRONT", "E_SKIRT", "E_EDGE", "WSCREEN")


def flat_shade(body):
    import paint as PT
    fac = body.shade()
    for zn in FLAT:
        if zn not in body.Z:
            continue
        m = body.lab == body.Z[zn]
        for c in range(8):
            mc = np.zeros_like(m)
            mc[:, c * 128:(c + 1) * 128] = m[:, c * 128:(c + 1) * 128]
            if mc.any():
                # the upstream draws every face of the body in the same
                # colours in all 8 views (no face lighting), so do the same
                fac[mc] = 1.0
    PT._shade[body.name] = fac




# ---------------------------------------------------------------------------
# liveries

YELLOW1 = (235, 180, 20)        # RAL 1003, 1st-class stripe / skirt edge
CAB_GLASS = (44, 48, 54)        # cab side windows: dark, not lit
BLACK = (22, 22, 24)

PK_NAVY = (24, 51, 122)
PK_RED = (222, 47, 40)
PK_WHITE = (236, 237, 233)
PK_YELLOW = (245, 210, 30)
PK_SKY = (31, 160, 224)

PL_BLUE = (21, 86, 168)
PL_WHITE = (230, 233, 232)
PL_GREEN = (18, 160, 122)
PL_YELLOW = (232, 164, 0)
PL_DOOR = (242, 194, 0)
PL_SKIRT = (95, 97, 99)
PL_ALU = (186, 190, 192)

PID_GREY = (185, 188, 182)      # RAL 7038
PID_RED = (204, 31, 26)         # RAL 3020
PID_BLACK = (20, 20, 20)        # RAL 9005
PID_DGREY = (75, 77, 70)        # RAL 7022


def u_from_rear(body):
    import warp
    ur = body.U.copy()
    for c in range(8):
        src = c if c in (3, 7) else warp.SIDE_SRC.get(c, c)
        if src == 7:
            sl = slice(c * 128, (c + 1) * 128)
            f = body.face[:, sl] == "S"
            ur[:, sl][f] = 1 - body.U[:, sl][f]
    return ur


def ucab(body, part):
    """0 at the Jakobs joint .. 1 at the cab, on the side faces."""
    ur = u_from_rear(body)
    return ur if part == "front" else 1 - ur


def base_hex(body, ref=0):
    return hexarr(body.refs[ref])


def spec_for(cls, liv, body, part):
    """zone -> colour (or callable). Roof handled separately."""
    uc = ucab(body, part)
    nb = base_hex(body, 0)
    pr = base_hex(body, 2)

    def at(ctx):
        return ctx["y"], ctx["col"] * 128 + ctx["x"]

    def first_class(normal, yellow=YELLOW1, lo=0.62, hi=0.93):
        # 1st class: a yellow segment of the cantrail stripe over the
        # high-floor windows behind the cab of the front section
        def f(ctx):
            y, X = at(ctx)
            if part == "front" and ctx["face"] == "S" and lo <= uc[y, X] <= hi:
                return yellow
            return normal(ctx) if callable(normal) else normal
        return f

    def navy_only(colour):
        # joint end: recolour only the painted (navy) pixels, keep bellows
        def f(ctx):
            y, X = at(ctx)
            return colour if int(nb[y, X]) in NAVY else None
        return f

    def pid_red(normal):
        def f(ctx):
            y, X = at(ctx)
            return PID_RED if int(pr[y, X]) == 0xED1C24 else normal
        return f

    # the PID front stripe: in the pure cab views the columns where the
    # upstream draws red below the windscreen, filled top to bottom
    stripe = set()
    for c in (1, 5):
        e = (body.face[:, c * 128:(c + 1) * 128] == "E") & (body.K[:, c * 128:(c + 1) * 128] >= 9)
        ys, xs = np.where(e & (pr[:, c * 128:(c + 1) * 128] == 0xED1C24))
        for x in set(xs.tolist()):
            if (xs == x).sum() >= 2:
                stripe.add((c, x))

    def pid_front(normal):
        def f(ctx):
            y, X = at(ctx)
            if (ctx["col"], ctx["x"]) in stripe and ctx["k"] >= 5:
                return PID_RED
            if int(pr[y, X]) == 0xED1C24:
                return PID_RED
            return normal(ctx) if callable(normal) else normal
        return f

    WS = (30, 32, 36)                    # black windscreen band
    if liv == "najbrt2":
        fox = cls == "847"
        s = {
            "S_TOP": first_class(P.N2_STRIPE), "S_WIN": P.SKY, "S_BELT": P.SAPPHIRE, "S_LOW": P.LGREY,
            "S_SKIRT": P.SAPPHIRE, "S_DOOR": P.SAPPHIRE, "S_HOOD": P.SAPPHIRE, "S_CABLOW": P.LGREY,
            "WSCREEN": WS, "E_HOOD": P.SAPPHIRE, "E_PANEL": P.SKY,
            # 847: black grille band with the headlights at its ends; 844:
            # headlight clusters in the light front under the sapphire nose
            "E_BANDSIDE": BLACK if fox else P.LGREY, "E_BANDMID": BLACK if fox else P.SAPPHIRE,
            "E_LOWFRONT": P.LGREY, "E_SKIRT": P.SAPPHIRE, "E_EDGE": YELLOW1,
            "J_TOP": P.SAPPHIRE, "J_WALL": navy_only(P.SAPPHIRE), "CABGLASS": CAB_GLASS,
        }
        roof = (P.SAPPHIRE, None)
    elif liv == "pardubickykraj":
        fox = cls == "847"
        s = {
            "S_TOP": PK_RED, "S_WIN": PK_WHITE, "S_BELT": PK_NAVY, "S_LOW": PK_WHITE,
            "S_SKIRT": PK_NAVY, "S_DOOR": PK_YELLOW, "S_HOOD": PK_NAVY, "S_CABLOW": PK_WHITE,
            "WSCREEN": WS, "E_HOOD": PK_NAVY, "E_PANEL": PK_SKY if fox else PK_WHITE,
            "E_BANDSIDE": BLACK if fox else PK_WHITE, "E_BANDMID": BLACK if fox else PK_NAVY,
            "E_LOWFRONT": PK_WHITE, "E_SKIRT": PK_NAVY, "E_EDGE": YELLOW1 if fox else PK_NAVY,
            "J_TOP": PK_NAVY, "J_WALL": navy_only(PK_NAVY), "CABGLASS": CAB_GLASS,
        }
        roof = (PK_NAVY, None)
    elif liv == "plzenskykraj":
        fox = cls == "847"
        if fox:
            # three parallel swooshes (green / white / yellow) rising toward
            # the cab between door and cab, and a second set by the joint
            lines = []
            for (u0, k0, u1, k1) in ((0.48, 8, 0.78, 1), (0.04, 8, 0.36, 1)):
                for i, colour in enumerate((PL_GREEN, PL_WHITE, PL_YELLOW)):
                    d = 0.03 * i
                    lines.append((u0 + d, k0, u1 + d, k1, colour))
        else:
            # 844: white arc over the windows from the cab, green + yellow
            # bands descending from the door area toward the cab
            lines = [(0.50, 1, 0.86, 1, PL_WHITE), (0.86, 1, 0.94, 0, PL_WHITE),
                     (0.34, 1, 0.84, 7, PL_GREEN), (0.30, 1, 0.80, 7, PL_GREEN),
                     (0.38, 1, 0.88, 7, PL_YELLOW), (0.42, 1, 0.92, 7, PL_YELLOW)]

        def pl_side(normal):
            def f(ctx):
                y, X = at(ctx)
                u, k = uc[y, X], ctx["k"]
                for (u0, k0, u1, k1, colour) in (lines if ctx["face"] == "S" else ()):
                    if min(u0, u1) - 0.01 <= u <= max(u0, u1) + 0.01:
                        t = (u - u0) / (u1 - u0) if u1 != u0 else 0
                        if abs(k - (k0 + t * (k1 - k0))) <= 0.5:
                            return colour
                return normal(ctx) if callable(normal) else normal
            return f

        s = {
            "S_TOP": pl_side(PL_BLUE), "S_WIN": pl_side(PL_BLUE), "S_BELT": pl_side(PL_BLUE),
            "S_LOW": pl_side(PL_BLUE), "S_SKIRT": PL_SKIRT, "S_DOOR": PL_DOOR, "S_HOOD": PL_WHITE,
            "S_CABLOW": PL_BLUE,
            "WSCREEN": WS, "E_HOOD": PL_WHITE, "E_PANEL": PL_BLUE,
            "E_BANDSIDE": BLACK if fox else PL_BLUE, "E_BANDMID": BLACK if fox else PL_BLUE,
            "E_LOWFRONT": PL_BLUE, "E_SKIRT": PL_BLUE if fox else PL_SKIRT,
            "E_EDGE": PL_YELLOW if fox else PL_SKIRT,
            "J_TOP": PL_BLUE, "J_WALL": navy_only(PL_BLUE), "CABGLASS": CAB_GLASS,
        }
        roof = (PL_WHITE, PL_ALU if fox else None)
    elif liv == "pidsedocervena":
        # red block between door and cab, cantrail to body bottom (the
        # black window band runs through it); its extent along the section
        # comes from the upstream PID sheet
        # (the cantrail row of the pure side views; the longest red run there,
        # which leaves out the red cab corner)
        b0, b1 = 1.0, 0.0
        for c in (3, 7):
            sl = slice(c * 128, (c + 1) * 128)
            m = (body.face[:, sl] == "S") & (body.K[:, sl] == 0) & (pr[:, sl] == 0xED1C24)
            xs = sorted(set(np.where(m)[1].tolist()))
            runs, cur = [], []
            for x in xs:
                if cur and x != cur[-1] + 1:
                    runs.append(cur); cur = []
                cur.append(x)
            if cur:
                runs.append(cur)
            if not runs:
                continue
            run = max(runs, key=len)
            ys = np.where(m[:, run[0]])[0]
            us = [uc[ys[0], c * 128 + x] for x in (run[0], run[-1])]
            b0, b1 = min(b0, *us), max(b1, *us)

        def pid_block(normal):
            def f(ctx):
                y, X = at(ctx)
                if ctx["face"] == "S" and b0 <= uc[y, X] <= b1:
                    return PID_RED
                return normal(ctx) if callable(normal) else normal
            return f

        s = {
            "S_TOP": first_class(pid_block(PID_GREY), lo=max(0.62, b1 + 0.03)), "S_WIN": pid_red(PID_BLACK),
            "S_BELT": pid_block(PID_GREY), "S_LOW": pid_block(PID_GREY), "S_SKIRT": pid_block(PID_GREY),
            "S_DOOR": PID_BLACK, "S_HOOD": pid_red(PID_GREY), "S_CABLOW": pid_red(PID_GREY),
            "WSCREEN": WS, "E_HOOD": pid_red(PID_GREY), "E_PANEL": pid_front(PID_GREY),
            "E_BANDSIDE": pid_front(BLACK), "E_BANDMID": pid_front(BLACK),
            "E_LOWFRONT": pid_front(PID_GREY), "E_SKIRT": pid_front(PID_GREY), "E_EDGE": YELLOW1,
            "J_TOP": PID_GREY, "J_WALL": navy_only(PID_GREY), "CABGLASS": CAB_GLASS,
        }
        roof = (PID_GREY, PID_DGREY)
    else:
        raise KeyError(liv)
    return s, roof


def paint_roof(body, a, roof):
    """Roof plate in the livery roof colour keeping the upstream shading; the
    darker equipment boxes either follow the plate (eq None) or get their own
    colour."""
    plate, eq = roof
    Z = body.Z
    m = (body.lab == Z["ROOF"]) | (body.lab == Z["ROOF_EDGE"])
    L = lum(body.base.astype(float))
    ref = np.median(L[m & (L > 100)])
    a = a.astype(float)
    ys, xs = np.where(m)
    for y, x in zip(ys, xs):
        l = L[y, x]
        if eq is not None and l < 95:
            c = np.array(eq, float) * np.clip((l / 70.0) ** 0.7, 0.6, 1.4)
        else:
            c = np.array(plate, float) * np.clip((l / ref) ** 0.7, 0.55, 1.45)
        a[y, x] = np.clip(c, 0, 255)
    return unspecial(np.rint(a).astype(np.uint8))


def marks_for(cls, liv):
    """Side marks (uc, width, k, colour) with uc 0 = joint .. 1 = cab, and the
    front-panel logo colour (None = no logo)."""
    if liv == "najbrt2":
        brand = (0.78, 0.10, 7, P.SAPPHIRE)           # RegioFox / RegioShark wordmark
        return [brand, (0.30, 0.07, 7, P.SAPPHIRE), (0.72, 0.03, 7, P.SKY)], WHITE_LOGO
    if liv == "pardubickykraj":
        return [(0.70, 0.12, 7, PK_NAVY), (0.62, 0.02, 7, PK_RED)], WHITE_LOGO if cls == "847" else PK_NAVY
    if liv == "pidsedocervena":
        return [(0.66, 0.05, 7, PID_RED), (0.30, 0.06, 1, PID_BLACK)], WHITE_LOGO
    if liv == "plzenskykraj":
        return [(0.80, 0.12, 7, PL_WHITE)], WHITE_LOGO
    return [], None


WHITE_LOGO = (236, 238, 240)


def add_pesa_marks(body, a, part, marks, logo):
    fac = shade(body)
    uc = ucab(body, part)
    a = a.astype(float)
    Z = body.zones
    for u, w, k, colour in marks:
        m = (body.face == "S") & (body.K == k) & (np.abs(uc - u) <= w / 2)
        for y, x in zip(*np.where(m)):
            if Z[body.lab[y, x]] in ("S_TOP", "S_WIN", "S_BELT", "S_LOW"):
                a[y, x] = np.clip(np.array(colour, float) * fac[y, x], 0, 255)
    if logo is not None:
        # a 2 px logo in the middle of the front panel of the cab end
        m = (body.lab == body.Z["E_PANEL"]) & (body.face == "E")
        for col in range(8):
            sl = slice(col * 128, (col + 1) * 128)
            mc = m[:, sl]
            ys, xs = np.where(mc)
            if len(xs) < 6:
                continue
            cy = int(np.median(ys))
            cx = int(round(xs.mean()))
            for dx in (0, 1) if col in (1, 5) else (0,):
                if mc[cy, cx + dx - (1 if col in (1, 5) else 0)]:
                    a[cy, col * 128 + cx + dx - (1 if col in (1, 5) else 0)] = logo
    return unspecial(np.rint(a).astype(np.uint8))


def render(cls, liv):
    b = bodies()
    rows = []
    marks, logo = marks_for(cls, liv)
    for part in ("front", "rear"):
        bd = b[part]
        spec, roof = spec_for(cls, liv, bd, part)
        a = paint(bd, spec)
        a = paint_roof(bd, a, roof)
        a = add_pesa_marks(bd, a, part, marks, logo)
        a = lamps(bd, a, part)
        rows.append(a)
    return rows


HEAD = (0xFF, 0xFF, 0x53)
TAIL = (0xFF, 0x21, 0x1D)
TAIL_OFF = (110, 22, 24)


def lamps(body, a, part):
    """Front section: the cab lamps are lit headlights, its red tail lamps
    are off. Rear section: the cab shows lit red tail lamps."""
    v = hexarr(body.base)
    a = a.copy()
    lamp = np.isin(v, [0xC1B1D1, 0xC2B2D2])
    if part == "front":
        a[lamp | (v == 0xE4E4FF)] = HEAD
        a[v == 0xFF211D] = TAIL_OFF
    else:
        a[lamp] = TAIL
    return a


LIVERIES = {"844": ["najbrt2", "pardubickykraj", "plzenskykraj"],
            "847": ["najbrt2", "pidsedocervena", "plzenskykraj", "pardubickykraj"]}


def main(argv):
    """Write the sheets of the given classes (both when none are given)."""
    fams = [a for a in argv if a in LIVERIES] or list(LIVERIES)
    pv = argv[argv.index("--preview") + 1] if "--preview" in argv else None
    zd = argv[argv.index("--zones") + 1] if "--zones" in argv else None
    written = []
    for cls in fams:
        for liv in LIVERIES[cls]:
            written.append(save_sheet(render(cls, liv), os.path.join(FAM, cls, "sprites", f"{liv}.png")))
            print("wrote", written[-1])
    if pv:
        os.makedirs(pv, exist_ok=True)
        preview(written, os.path.join(pv, "pesa.png"), z=3)
    if zd:
        os.makedirs(zd, exist_ok=True)
        for k, bd in bodies().items():
            fc, pal = bd.falsecolor()
            Image.fromarray(np.concatenate([bd.base.astype(np.uint8), fc], 0)).save(os.path.join(zd, f"z_pesa_{k}.png"))
    return written


if __name__ == "__main__":
    main(sys.argv[1:])
