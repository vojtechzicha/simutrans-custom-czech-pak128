"""ČD 642 Desiro Classic (DÚK zeleno-bílá) and ČD 848 Stadler GTW 2/6 (Najbrt 2
with Olomoucký kraj decals).

Upstream drawings (frozen in src/642_848/, the 1024-px sprite columns only):
- 642: the pak128.CS DB Desiro sheets db_desiro_2.png / db_desiro.png (rail-psg
  mail/), row 0 = 642a (cab ahead), row 1 = 642b (cab behind);
- 848: the pak128.CS ZSSK 840 GTW drawings (rail-psg mail/840_841/:
  zssk_840_a(_freight), zssk_840_b = power module, zssk_840_c(_freight)).

The upstream liveries (DB red, ZSSK) do not follow the Czech schemes, so the
pure views are zoned by hand-written geometry rules on the upstream colour
classes; the diagonal views get their zones through warp.py. Liveries:
642 dukzelenobila (the six ex-HLB units at Děčín), 848 najbrt2 (12 units for
Olomoucký kraj).

  python tools/railpaint/cd_642_848.py [642] [848] [--preview DIR]

writes vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png; --preview also
writes zoomed previews and the zone false-colour maps into DIR.
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warp
from body import Body, T, hexarr, lum, SIDE_COLS, END_COLS, DIAG_COLS
from paint import paint, recolor_lum, add_marks, save_sheet, unspecial, shade, preview
from palette import SAPPHIRE, SKY, N2_STRIPE, dk

REPO = os.path.dirname(os.path.dirname(HERE))
FAMDIR = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
SRC = os.path.join(HERE, "src", "642_848") + os.sep

SPC = {0x4d4d4d: 'g', 0x57656f: 'G', 0x6b6b6b: '6', 0x9b9b9b: '9', 0xb3b3b3: '3', 0xe3e3ff: 'e',
       0xffff53: 'Y', 0xff211d: 'T', 0x01dd01: 'E'}


def cls(p):
    """Coarse colour class of one upstream pixel (same letters as cmap.py)."""
    r, g, b = (int(v) for v in p)
    v = (r << 16) | (g << 8) | b
    if (r, g, b) == (231, 255, 255):
        return '.'
    if v in SPC:
        return SPC[v]
    mx = max(r, g, b)
    if r > 120 and g < 70:
        return 'R' if r > 170 else 'r'
    if b > r + 25 and b > g + 10:
        return 'B' if mx > 110 else 'n'
    if g > r + 20 and g > b:
        return 'V'
    if r > 150 and g > 120 and b < 90:
        return 'y'
    if mx < 45:
        return 'k'
    if mx < 90:
        return 'd'
    if mx < 140:
        return 'm'
    if mx < 200:
        return 's'
    return 'w'


GLASSY = set('gG6953')


class RuleBody(Body):
    """Body whose pure views are zoned by cfg['side_fn'] / cfg['end_fn']
    (body, col, top) -> (lab, K, U), with zone names from cfg['extra_zones']."""

    def pure(self, col, top, rows, face):
        fn = self.cfg["side_fn"] if face == "S" else self.cfg["end_fn"]
        return fn(self, col, top)

    def cmap(self, col):
        t = self.base[:, col * 128:(col + 1) * 128]
        return np.array([[cls(t[y, x]) for x in range(128)] for y in range(128)])

    def new(self, col):
        t = self.base[:, col * 128:(col + 1) * 128]
        body = ~np.all(t == T, axis=-1)
        lab = np.full((128, 128), self.Z["FIX"], int)
        lab[~body] = self.Z["T"]
        ys, xs = np.where(body)
        U = np.full((128, 128), -1.0)
        U[body] = (xs - xs.min()) / max(1, xs.max() - xs.min())
        K = np.full((128, 128), -99, int)
        return body, lab, K, U, xs.min(), xs.max()

    def build(self):
        super().build()
        Z = self.Z
        # headlight / display specials by base colour in every view
        v = hexarr(self.base)
        body = self.lab != Z["T"]
        self.lab[body & (v == 0xE3E3FF)] = Z["HEAD"]
        self.lab[body & (v == 0x01DD01)] = Z["DISPLAY"]
        # glass on an end face is the (unlit) windscreen
        self.lab[(self.face == "E") & (self.lab == Z["GLASS"])] = Z["WSCREEN"]
        # diagonal-view pixels demoted to FIX next to glass keep the old body
        # colour; give them the body zone of their face instead
        if "body_classes" in self.cfg:
            bc = np.array([[cls(self.base[y, x]) in self.cfg["body_classes"] for x in range(1024)] for y in range(128)])
            fix = self.lab == Z["FIX"]
            self.lab[fix & bc & (self.face == "S")] = Z[self.cfg["body_zone"]["S"]]
            self.lab[fix & bc & (self.face == "E")] = Z[self.cfg["body_zone"]["E"]]
        self.fill_roof_u()

    def fill_roof_u(self):
        """Diagonal-view roof pixels above the side face get U from the side map."""
        for col in DIAG_COLS:
            s, bx, by, _ = self.fits[col]["side"]
            src = warp.SIDE_SRC[col]
            ts = self.base[:, src * 128:(src + 1) * 128]
            xs = np.where(~np.all(ts == T, axis=-1).all(axis=0))[0]
            x0, x1 = xs.min(), xs.max()
            sl = slice(col * 128, (col + 1) * 128)
            lab, U = self.lab[:, sl], self.U[:, sl]
            ys, xx = np.where(np.isin(lab, [self.Z["ROOF"], self.Z["ROOF_EDGE"]]) & (U < 0))
            sx = s * xx + bx
            U[ys, xx] = np.clip((sx - x0) / max(1, x1 - x0), 0, 1)

    def dist_from(self, cab_right):
        """Per-pixel distance (pure side px) from the cab nose, for side and roof
        pixels; cab_right[src_col] says whether the cab is at the right end of that
        pure side view."""
        D = np.full((128, 1024), 1e3)
        for col in range(8):
            if col in END_COLS:
                continue
            src = col if col in SIDE_COLS else warp.SIDE_SRC[col]
            ts = self.base[:, src * 128:(src + 1) * 128]
            xs = np.where((~np.all(ts == T, axis=-1)).any(axis=0))[0]
            L = xs.max() - xs.min()
            sl = slice(col * 128, (col + 1) * 128)
            U = self.U[:, sl]
            ok = U >= 0
            d = (1 - U) * L if cab_right[src] else U * L
            D[:, sl][ok] = d[ok]
        return D


# ---------------------------------------------------------------------------
# ČD 642 Desiro Classic (DÚK)
# ---------------------------------------------------------------------------
# pure side geometry per (sheet row, col): door x-range, cab at the Right/Left end
DES_SIDE = {(0, 3): ((49, 53), "R"), (0, 7): ((67, 71), "L"),
            (1, 3): ((56, 59), "L"), (1, 7): ((60, 64), "R")}
DES_TOP = 82          # first body row under the roof (cantrail) in both side views
# end views: row -> (cab end col, cab top, joint end col, joint top)
DES_END = {0: dict(cab=5, cab_top=87, joint=1, joint_top=85),
           1: dict(cab=1, cab_top=84, joint=5, joint_top=88)}


def des_side(row):
    def f(b, col, top):
        Z = b.Z
        body, lab, K, U, x0, x1 = b.new(col)
        c = b.cmap(col)
        (d0, d1), cab = DES_SIDE[(row, col)]
        for y, x in zip(*np.where(body)):
            k = y - top
            K[y, x] = k
            ch = c[y, x]
            door = d0 <= x <= d1
            high = (x > d1) if cab == "R" else (x < d0)       # cab side of the door = high floor
            if k < 0:
                z = "ROOF"
            elif ch in GLASSY and 2 <= k <= 7:
                z = "GLASS"
            elif ch in "YT":
                z = "HEAD" if ch == "Y" else "TAIL"
            elif ch == "E":
                z = "DISPLAY"
            elif k <= 1:
                z = "S_DOOR" if (door and k == 1) else "S_BODY"
            elif k <= 7:
                if door:
                    z = "S_DOOR"
                elif ch in "Rr" or k == 7 or (high and k >= 5):
                    z = "S_BODY"
                else:
                    z = "S_PILLAR"
            elif k == 8:
                z = "S_DOOR" if door else "S_STRIPE"
            elif k == 9:
                z = "S_DOOR" if door else ("S_SKIRT" if high else "S_BODY")
            elif k == 10:
                z = "S_SKIRT"
            else:
                z = "FIX"
            lab[y, x] = Z[z]
        return lab, K, U
    return f


def des_end(row):
    e = DES_END[row]

    def f(b, col, top):
        Z = b.Z
        body, lab, K, U, x0, x1 = b.new(col)
        c = b.cmap(col)
        cab = col == e["cab"]
        top = e["cab_top"] if cab else e["joint_top"]
        for y, x in zip(*np.where(body)):
            k = y - top
            K[y, x] = k
            ch = c[y, x]
            edge = x in (x0, x1)
            if k < 0:
                z = "ROOF"
            elif not cab:
                z = "E_JTOP" if k == 0 else ("E_BELLOWS" if k <= 8 else "FIX")
            elif ch in "YT":
                z = "HEAD" if ch == "Y" else "TAIL"
            elif ch in "EV" and 4 <= k <= 6:
                z = "DISPLAY"
            elif k <= 2:
                z = "E_SIDEG" if edge else "WSCREEN"
            elif k == 3:
                z = "E_SIDEG" if edge else "E_FRAME"
            elif k <= 6:
                z = "E_SIDEG" if edge else "E_GLASSBAND"
            elif k == 7:
                z = "E_NUMSTRIP"
            elif k == 8:
                z = "E_STRIPEW" if (x <= x0 + 1 or x >= x1 - 1) else "E_RECESS"
            elif k <= 11:
                z = "E_SKIRT" if ch not in "k" else "FIX"
            else:
                z = "FIX"
            lab[y, x] = Z[z]
        return lab, K, U
    return f


DES_ZONES = ["S_CABGLASS", "S_BODY", "S_PILLAR", "S_STRIPE", "S_SKIRT", "DISPLAY", "WSCREEN",
             "E_JTOP", "E_BELLOWS", "E_SIDEG", "E_FRAME", "E_GLASSBAND", "E_NUMSTRIP",
             "E_STRIPEW", "E_RECESS", "E_SKIRT"]


def des_cfg(row):
    e = DES_END[row]
    end_top = {e["cab"]: e["cab_top"], e["joint"]: e["joint_top"]}
    return dict(name=f"642{'ab'[row]}",
                refs=[(SRC + "db_desiro_2.png", row), (SRC + "db_desiro.png", row)],
                base=0, side_top={3: DES_TOP, 7: DES_TOP}, end_top=end_top,
                side_rows=[], end_rows=[], extra_zones=DES_ZONES,
                side_fn=des_side(row), end_fn=des_end(row),
                body_classes="Rr", body_zone={"S": "S_BODY", "E": "E_SIDEG"},
                glass_extra=lambda t, col: np.isin(hexarr(t), [0x6B6B6B, 0x9B9B9B]).any(axis=0))


# DÚK colours (photo research, September 2026)
DUK_GREEN = (58, 166, 74)       # #3AA64A
DUK_ROOF = (202, 207, 210)      # #D5DADD in photos, a touch darker so the roof shading reads
DUK_WHITE = (228, 231, 232)     # #E4E7E8 stripe, swoosh, doors
DUK_SKIRT = (69, 73, 76)        # #45494C
DUK_DARK = (30, 32, 35)         # coupler recess, window surround
DUK_GLASSBAND = (34, 36, 40)
WSCREEN_TINT = (58, 64, 72)
AMBER = (240, 160, 24)
CAB_GLASS = (72, 74, 78)        # driver's cab windows: glass look, never lit
DUK_ORANGE = (236, 128, 40)     # DÚK logo arrows
DUK_BLUE = (40, 110, 190)
BELLOWS = (48, 50, 54)


def swoosh_d(k):
    """Centre of the white cab swoosh, px from the cab nose, at side row k."""
    return 11.5 - 9.5 * k / 8


def des_paint(row):
    b = RuleBody(des_cfg(row))
    (_, cab3), (_, cab7) = DES_SIDE[(row, 3)], DES_SIDE[(row, 7)]
    D = b.dist_from({3: cab3 == "R", 7: cab7 == "R"})
    e = DES_END[row]
    b.lab[(b.lab == b.Z["GLASS"]) & (D <= 5.5) & (b.face == "S")] = b.Z["S_CABGLASS"]

    def tol(ctx):
        # the diagonal views compress the side by 1/sqrt(2): widen the band
        return 0.9 if ctx["col"] in SIDE_COLS else 1.25

    def side_body(ctx):
        d = D[ctx["y"], ctx["col"] * 128 + ctx["x"]]
        k = ctx["k"]
        if abs(d - swoosh_d(k)) <= tol(ctx):
            return DUK_WHITE
        if 2.2 <= d <= 5.2 and 2 <= k <= 5:
            return (CAB_GLASS, "flat")          # cab side window (not lit)
        return DUK_GREEN

    def roof(ctx):
        col, y = ctx["col"], ctx["y"]
        if col in END_COLS:
            return DUK_GREEN if (col == e["cab"] and ctx["k"] >= -6) else DUK_ROOF
        d = D[y, col * 128 + ctx["x"]]
        return DUK_GREEN if d < swoosh_d(0) - 0.9 else DUK_ROOF

    spec = {
        "S_CABGLASS": (CAB_GLASS, "flat"),
        "ROOF": roof, "ROOF_EDGE": roof,
        "S_BODY": side_body, "S_PILLAR": side_body, "S_STRIPE": DUK_WHITE,
        "S_DOOR": lambda c: DUK_DARK if cls(b.base[c["y"], c["col"] * 128 + c["x"]]) in "k" else DUK_WHITE,
        "S_SKIRT": lambda c: DUK_WHITE if abs(D[c["y"], c["col"] * 128 + c["x"]] - swoosh_d(c["k"])) <= tol(c) else DUK_SKIRT,
        "DISPLAY": (AMBER, "flat"), "HEAD": ((0xFF, 0xFF, 0x53), "flat"),
        "WSCREEN": WSCREEN_TINT,
        "E_JTOP": DUK_GREEN, "E_BELLOWS": BELLOWS,
        "E_SIDEG": DUK_GREEN, "E_FRAME": DUK_DARK, "E_GLASSBAND": DUK_GLASSBAND,
        "E_NUMSTRIP": DUK_GREEN, "E_STRIPEW": DUK_WHITE, "E_RECESS": DUK_DARK, "E_SKIRT": DUK_SKIRT,
    }
    a = paint(b, spec)
    # ČD logo, DÚK logo and "ústecký kraj" behind the cab swoosh; running number
    # on the front strip and the ČD logo in the lower glass band
    L = 58.0
    ur = (lambda d: 1 - d / L) if row == 0 else (lambda d: d / L)
    a = add_marks(b, a, side=[(ur(14), 0.03, 6, DUK_WHITE), (ur(19), 0.02, 6, DUK_ORANGE),
                              (ur(20), 0.02, 6, DUK_BLUE), (ur(25), 0.04, 6, DUK_WHITE)],
                  side_zones={"S_BODY"})
    a = add_marks(b, a, end=[(0.72, 0.1, 7, DUK_WHITE), (0.5, 0.1, 6, DUK_WHITE)],
                  end_zones={"E_NUMSTRIP", "E_GLASSBAND"})
    return b, a



# ---------------------------------------------------------------------------
# ČD 848 Stadler GTW 2/6 (Najbrt 2 + Olomoucký kraj decals)
# ---------------------------------------------------------------------------
G840 = SRC
GTW_TOP = 81          # first painted side row (white stripe) on every GTW body
# end cars: pure side (col) -> (door x-range, cab at Right/Left); car c mirrors car a
GTW_SIDE = {"a": {3: ((62, 65), "R"), 7: ((55, 58), "L")},
            "c": {3: ((55, 58), "L"), 7: ((62, 65), "R")}}
GTW_END = {"a": dict(cab=5, cab_top=86, joint=1, joint_top=82),
           "c": dict(cab=1, cab_top=79, joint=5, joint_top=89),
           "b": dict(cab=None, joint=None, top={1: 69, 5: 90})}
GTW_CAB_D = 11        # side px from the nose that belong to the cab (sky surround)


def gtw_side(car):
    def f(b, col, top):
        Z = b.Z
        body, lab, K, U, x0, x1 = b.new(col)
        c = b.cmap(col)
        if car == "b":
            door, cab = None, None
        else:
            door, cab = GTW_SIDE[car][col]
        for y, x in zip(*np.where(body)):
            k = y - top
            K[y, x] = k
            ch = c[y, x]
            isdoor = door is not None and door[0] <= x <= door[1]
            d = None if cab is None else ((x1 - x) if cab == "R" else (x - x0))
            incab = d is not None and d <= GTW_CAB_D
            if k < 0:
                z = "ROOF"
            elif ch in "YT":
                z = "HEAD" if ch == "Y" else "TAIL"
            elif ch == "e":
                z = "HEAD"
            elif ch in "EV" and 4 <= k <= 8:
                z = "DISPLAY"
            elif k <= 1:
                z = "S_WHITE"
            elif k <= 3:
                z = "S_SKY"
            elif k <= 8:
                if car == "b":
                    z = "S_PANEL"
                elif isdoor:
                    z = "GLASS" if ch in GLASSY and k >= 5 else "S_DOOR"
                elif ch in GLASSY and k >= 5:
                    z = "GLASS"
                else:
                    z = "S_SKY" if incab else "S_BAND"
            elif k == 9:
                z = "S_DOOR" if isdoor else "S_STRIPE"
            elif k <= 11:
                z = "S_DOOR" if isdoor else "S_LOW"
            else:
                z = "FIX"
            lab[y, x] = Z[z]
        return lab, K, U
    return f


def gtw_end(car):
    e = GTW_END[car]

    def f(b, col, top):
        Z = b.Z
        body, lab, K, U, x0, x1 = b.new(col)
        c = b.cmap(col)
        cab = col == e["cab"]
        if car == "b":
            top = e["top"][col]
        else:
            top = e["cab_top"] if cab else e["joint_top"]
        for y, x in zip(*np.where(body)):
            k = y - top
            K[y, x] = k
            ch = c[y, x]
            edge = x <= x0 + 1 or x >= x1 - 1
            if k < 0:
                z = "ROOF"
            elif not cab:
                z = "E_BELLOWS" if k <= 9 else "FIX"
            elif ch in "YTe":
                z = "TAIL" if ch == "T" else "HEAD"
            elif ch in "EV" and 2 <= k <= 3:
                z = "DISPLAY"
            elif k <= 1:
                z = "E_CAP"
            elif k <= 3:
                z = "E_PILLAR" if edge else "E_GLASSBAND"
            elif k <= 6:
                z = "E_PILLAR" if edge else "WSCREEN"
            elif k <= 9:
                z = "E_LAMP"
            elif k == 10:
                z = "E_STRIPE"
            elif k == 11:
                z = "E_CHEEK" if edge else "E_RECESS"
            elif k == 12:
                z = "E_PLOUGH"
            else:
                z = "FIX"
            lab[y, x] = Z[z]
        return lab, K, U
    return f


GTW_ZONES = ["S_CABGLASS", "S_WHITE", "S_SKY", "S_BAND", "S_PANEL", "S_STRIPE", "S_LOW", "DISPLAY", "WSCREEN",
             "E_BELLOWS", "E_CAP", "E_PILLAR", "E_GLASSBAND", "E_LAMP", "E_STRIPE", "E_CHEEK",
             "E_RECESS", "E_PLOUGH"]


def gtw_cfg(car):
    refs = {"a": [(G840 + "zssk_840_a_freight.png", 0), (G840 + "zssk_840_a.png", 0)],
            "b": [(G840 + "zssk_840_b.png", 0)],
            "c": [(G840 + "zssk_840_c_freight.png", 0), (G840 + "zssk_840_c.png", 0)]}[car]
    e = GTW_END[car]
    end_top = e["top"] if car == "b" else {e["cab"]: e["cab_top"], e["joint"]: e["joint_top"]}
    return dict(name=f"848{car}", refs=refs, base=0,
                side_top={3: GTW_TOP, 7: GTW_TOP}, end_top=end_top,
                side_rows=[], end_rows=[], extra_zones=GTW_ZONES,
                side_fn=gtw_side(car), end_fn=gtw_end(car),
                glass_extra=lambda t, col: np.isin(hexarr(t), [0x6B6B6B, 0xB3B3B3]).any(axis=0))


N2_WHITE = (230, 233, 234)      # 848 white stripe + lower body (#E6E9EA)
GTW_BAND = (30, 32, 40)         # flush black glazing band (#1E2028)
GTW_PANEL = (46, 48, 54)        # power-module engine-room panel (#2E3036)
GTW_RECESS = (30, 32, 35)
GTW_YELLOW = (232, 176, 20)     # skirt bottom edge (#E8B014)
OK_YELLOW = (246, 196, 30)      # Olomoucký kraj logo petals
SLOGAN_BLUE = (44, 70, 124)     # dark-blue decal lettering on the white lower body
OK_RED = (220, 50, 50)


def flatten_shade(b, side_zones, end_zones, ref_zone):
    """The upstream GTW livery does not follow the ČD zones (a navy stripe and
    white upper side share one ČD band), so its per-pixel lighting would stripe
    the new colours. Give those zones one face-level factor per tile: the side
    factor from a zone that is one colour in the upstream art (ref_zone), the end
    factor from the median over the end face."""
    fac = shade(b)
    Z = b.Z
    for col in range(8):
        sl = slice(col * 128, (col + 1) * 128)
        lab, f = b.lab[:, sl], fac[:, sl]
        ref = lab == Z[ref_zone]
        fs = float(np.median(f[ref])) if ref.any() else 1.0
        for zn in side_zones:
            f[lab == Z[zn]] = fs
        em = np.isin(lab, [Z[z] for z in end_zones])
        if em.any():
            f[em] = 1.0 if col in END_COLS else float(np.median(f[em]))
    return fac


# power module diagonal views: the vertical corner edge between side and end
# face (side face on the left of it for w/e, on the right for n/s), read off
# the upstream art; the warp is unreliable on a body this small
GTW_MODULE_CORNER = {0: ("L", 47), 4: ("L", 71), 2: ("R", 79), 6: ("R", 55)}


def gtw_module_diag(b):
    """Re-zone the power module's diagonal views by geometry: K from the fitted
    side shear, side/end split at the corner edge."""
    Z = b.Z
    for col, (side_at, xc) in GTW_MODULE_CORNER.items():
        s, bx, by, _ = b.fits[col]["side"]
        slope = warp.SIDE_SLOPE[col]
        sl = slice(col * 128, (col + 1) * 128)
        lab, K, face = b.lab[:, sl], b.K[:, sl], b.face[:, sl]
        body = lab != Z["T"]
        for y, x in zip(*np.where(body)):
            k = int(round(y - slope * x + by)) - GTW_TOP
            onside = x <= xc if side_at == "L" else x >= xc
            if lab[y, x] in (Z["HEAD"], Z["TAIL"], Z["GLASS"]):
                continue
            if k < 0:
                z, f = "ROOF", "R"
            elif not onside:
                z, f = ("E_BELLOWS" if k <= 11 else "FIX"), "E"
            elif k <= 1:
                z, f = "S_WHITE", "S"
            elif k <= 3:
                z, f = "S_SKY", "S"
            elif k <= 8:
                z, f = "S_PANEL", "S"
            elif k == 9:
                z, f = "S_STRIPE", "S"
            elif k <= 11:
                z, f = "S_LOW", "S"
            else:
                z, f = "FIX", ""
            lab[y, x], K[y, x], face[y, x] = Z[z], k, f


def gtw_paint(car):
    b = RuleBody(gtw_cfg(car))
    if car == "b":
        gtw_module_diag(b)
    else:
        right = {"a": {3: True, 7: False}, "c": {3: False, 7: True}}[car]
        D = b.dist_from(right)
        b.lab[(b.lab == b.Z["GLASS"]) & (D <= GTW_CAB_D) & (b.face == "S")] = b.Z["S_CABGLASS"]
    flatten_shade(b, ["S_SKY", "S_BAND", "S_STRIPE", "S_LOW", "S_DOOR", "S_PANEL"],
                  ["E_CAP", "E_PILLAR", "E_GLASSBAND", "E_LAMP", "E_STRIPE", "E_CHEEK", "E_RECESS", "E_BELLOWS"],
                  "S_WHITE")
    spec = {
        "S_CABGLASS": (CAB_GLASS, "flat"),
        "S_WHITE": N2_WHITE, "S_SKY": SKY, "S_BAND": GTW_BAND, "S_PANEL": GTW_PANEL,
        "S_STRIPE": SAPPHIRE, "S_LOW": N2_WHITE, "S_DOOR": SAPPHIRE,
        "DISPLAY": (AMBER, "flat"), "HEAD": ((0xFF, 0xFF, 0x53), "flat"),
        "WSCREEN": WSCREEN_TINT, "E_BELLOWS": BELLOWS,
        "E_CAP": SAPPHIRE, "E_PILLAR": SKY, "E_GLASSBAND": GTW_BAND, "E_LAMP": SKY,
        "E_STRIPE": SAPPHIRE, "E_CHEEK": N2_WHITE, "E_RECESS": GTW_RECESS,
        "E_PLOUGH": (GTW_YELLOW, "flat"),
    }
    a = paint(b, spec)
    # flush black glazing: every window in the darker lit-glass special
    v = hexarr(a)
    a[v == 0x57656F] = (0x4D, 0x4D, 0x4D)
    a = recolor_lum(b, a, "ROOF", SAPPHIRE)
    a = recolor_lum(b, a, "ROOF_EDGE", SAPPHIRE)
    if car != "b":
        # u from the rear: car a has its cab at the front, car c at the rear
        L = 44.0
        ur = (lambda d: 1 - d / L) if car == "a" else (lambda d: d / L)
        # OLKRAJ.CZ flower under the cab window, "Jedeme v tom spolu…" between cab and door
        side = [(ur(8), 0.02, 10, SAPPHIRE),
                (ur(13.5), 0.08, 11, SLOGAN_BLUE)]
        if car == "a":
            side += [(ur(38), 0.02, 10, OK_YELLOW), (ur(39), 0.02, 10, OK_RED), (ur(39), 0.02, 11, SKY)]
        else:
            side += [(ur(38), 0.05, 10, SAPPHIRE)]                     # "ČD České dráhy"
        a = add_marks(b, a, side=side, side_zones={"S_LOW"})
        a = add_marks(b, a, end=[(0.5, 0.12, 8, N2_WHITE), (0.82, 0.12, 0, N2_WHITE)],
                      end_zones={"E_LAMP", "E_CAP"})
    return b, a

def render(fam):
    """-> (sheet rows, bodies) of a family's only livery."""
    if fam == "642":
        res = [des_paint(r) for r in (0, 1)]
    elif fam == "848":
        res = [gtw_paint(car) for car in "abc"]
    else:
        raise KeyError(fam)
    return [a for _, a in res], [b for b, _ in res]


LIVERY = {"642": "dukzelenobila", "848": "najbrt2"}


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    fams = argv or list(LIVERY)
    for fam in fams:
        rows, bodies = render(fam)
        d = os.path.join(FAMDIR, fam, "sprites")
        os.makedirs(d, exist_ok=True)
        p = save_sheet(rows, os.path.join(d, LIVERY[fam] + ".png"))
        print("wrote", p)
        if prev:
            os.makedirs(prev, exist_ok=True)
            preview([p], os.path.join(prev, f"p{fam}.png"))
            for b in bodies:
                fc, _ = b.falsecolor()
                Image.fromarray(np.concatenate([b.base.astype(np.uint8), fc], 0)).save(
                    os.path.join(prev, f"z{b.name}.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
