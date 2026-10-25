"""Town (MHD) buses of the ODIS region (Moravskoslezský kraj) that had no pak
of their own: render or repaint the sprite sheets and write the family.yaml
files.

    python tools/busrender/odis_town.py [family ...] [--yaml] [--preview DIR]
    python tools/busrender/odis_town.py --csad-static

Without --yaml only the sheets are written; with --yaml the family.yaml files
are (re)generated from FAMILIES too (review the diff). A family is named by
its folder (sor_nsg_12) or agency/folder (mhd-havirov/sor_nsg_12).
--csad-static writes the static Frýdek-Místek 3ČSAD sheets (FM_CSAD) from
their frozen sources in src/odis/, the green in CSAD["green"].

Packages (user, 2026-10-20): every ODIS town with MHD gets its own
MHD<Town> pak, and the ODIS pak (regional buses, later) holds no town bus.
Ostrava, Opava, Frýdek-Místek, Třinec, Český Těšín, Nový Jičín, Studénka and
Krnov already had one; this driver adds the four the region had folded in:
  MHDHavirov   (vehicle-bus/mhd-havirov/)   Transdev Slezsko, the blue city
               scheme of the 2024-2033 contract on every bus except the three
               2018 e-buses (green metallic, the F-M sheet)
  MHDKarvina   (vehicle-bus/mhd-karvina/)   Transdev Slezsko: the white-black
               city scheme (SOR NS 12 2023), 3ČSAD white-green and plain white
  MHDOrlova    (vehicle-bus/mhd-orlova/)    Transdev Slezsko: 3ČSAD white-green,
               the white Isuzu; the depot's Stratos LF 38 CNG and Crossway LE
               LINE 10,8M that work lines 501/505 every day in 2026 included
  MHDBruntal   (vehicle-bus/mhd-bruntal/)   Transdev Morava: the one SOR CNG 12
               in the Bruntál scheme (the kraj ring in green, BRUNTÁL logo)
and one bus to the Nový Jičín pak:
  MHDNovyJicin (vehicle-bus/mhd-novy-jicin/) ARRIVA's reserve SOR BN 10,5 in the
               red-black town scheme (the EBN 9,5 sheet there is a static PNG)
Scope: the vehicles each town's MHD runs in October 2026 (seznam-autobusu
periods "od m/yyyy", duty logs); stored, reserve and regional stand-in buses
are left out. Same body + same paint as an existing sheet = a copy of that
sheet (the 3ČSAD white-green Urbanway and Citywide of Frýdek-Místek, the 2018
3ČSAD e-bus), as for the other packages.

Methods, picked per type:
  * SOR NS 12 / NSG 12 / NSG 18: the parametric dpmhk.py body (imported, never
    edited) painted by OVeh below, with the 2023 SOR face where the bus has it.
  * SOR CN (CNG 10,5, CNG 12) and Crossway LE LINE 10,8M: the IREDO box models
    of iredo_models.py with liveries defined here (registered at import).
  * Bodies with no parametric model: the hand-drawn sheets already in the repo
    (lane-normalised, glass in the lit specials) repainted zone by zone with
    their shading kept, roof boxes added where the sheet lacks the CNG
    fairing. VTPsim's pak128.cs ODIS sheets (CZ-vehicle-bus.pak, frozen in
    src/odis/) are ported for the types the repo had no body of: their glass
    turned into the lit specials (driver's glass plain), the green displays
    into the bus's own, and every view moved to the native lane by the length
    rule.
"""
import colorsys
import os
import sys
import math

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import dpmhk as H                                                       # noqa: E402
from dpmhk import Veh, sh, inr, HW                                      # noqa: E402
from render import render, Box, DIRS                                    # noqa: E402
import iredo_models as M                                                # noqa: E402
from rj_vrender import Sh                                               # noqa: E402
from rj_busmodels import W2                                             # noqa: E402
from rj_buses import row_for                                            # noqa: E402
from rj_lane import metrics, MEDIAN                                     # noqa: E402
import khk_town as K                                                    # noqa: E402

T = K.T
SRC = os.path.join(HERE, "src", "odis")

# ---------------------------------------------------------------- palette
LEDW = (0xEC, 0xEE, 0xE4)          # white LED destination displays (plain colour)
AMBER = (0xF0, 0xA0, 0x18)         # amber LED displays (plain colour)
SCREEN = (0x4D, 0x4D, 0x4E)        # driver's / windscreen glass: a step off special 28, never lit
SCREEN_HI = (0x57, 0x65, 0x6E)
GLASS, GLASS2 = H.GLASS, H.GLASS2  # specials 28 / 16, lit while passengers are aboard
BLACK = H.BLACK
WHITE = (0xF4, 0xF4, 0xF2)
# Havířov city scheme (2022-): one azure blue all over; the roof is the same
# paint seen from above, drawn lighter so the body shape reads (render-style)
HAV_BLUE = (0x15, 0x85, 0xD8)
HAV_ROOF = (0x3F, 0xA8, 0xEE)
HAV_LOGO = (0xF6, 0xF6, 0xF6)      # white city logo (three linked arches over HAVÍŘOV)
HAV_YEL = (0xDC, 0xCB, 0x10)       # yellow script slogan "město pro život"
# 3ČSAD white-green. CSAD_GREEN is the emerald of the CZR and Frýdek-Místek
# sheets, kept as the key VTPsim's green (6BBD29) is ported as, which the zone
# repaints tell apart best. The paint is CSAD["green"]: a yellow-green near
# RAL 6018 (photos 94CE57 in sun to 20611F overcast), the owner's pick of
# 2026-10-24 over the emerald, which read "too green"; odis.py --variant
# csad=X switches it for previews. CSAD["line"]: the dark line over the skirt
# (about 5 cm, a fifth of a pixel), None = left out.
CSAD_GREEN = (0x22, 0xB1, 0x4C)
CSAD = dict(green=(0x57, 0xA6, 0x39), line=None)
# Karviná white-black (2024-2033 contract)
KAR_BLACK = (0x16, 0x17, 0x1A)
# Nový Jičín red (the "červená metalíza" of the town's SOR EBN 9,5 sheet: sides, roof)
NJ_RED = (0xA5, 0x1D, 0x24)
NJ_ROOF = (0xB2, 0x26, 0x2D)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def hexc(c):
    return (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])


def neutral(c, lo=0xB0, tol=14):
    r, g, b = (int(v) for v in c)
    return max(r, g, b) - min(r, g, b) <= tol and max(r, g, b) >= lo


def scaled(base, k):
    return K.safe(tuple(int(max(0, min(255, round(v * k)))) for v in base))


def load_rows(rel, rows=None):
    """sprite rows of a repo sheet (path relative to the repo) or of a frozen
    source in src/odis/ (bare file name)"""
    p = os.path.join(REPO, *rel.split("/")) if "/" in rel else os.path.join(SRC, rel)
    a = np.array(Image.open(p).convert("RGB"))
    out = [[a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)]
           for r in range(a.shape[0] // 128)]
    return out if rows is None else [out[r] for r in rows]


def is_bg(t):
    return np.all(t == T, axis=2)


def load(src, rows=None):
    """rows of a sheet path (see load_rows) or of a callable returning rows"""
    return src() if callable(src) else load_rows(src, rows)


def inpaint(rows, deco):
    """paint decoration pixels out: each takes the nearest plain pixel left or
    right of it in the same screen row (glass on the window band, paint below)"""
    out = []
    for tiles in rows:
        row = []
        for t in tiles:
            m = np.zeros((128, 128), bool)
            for y, x in zip(*np.where(~is_bg(t))):
                m[y, x] = deco(t, y, x)
            o = t.copy()
            for y, x in zip(*np.where(m)):
                for dx in range(1, 9):
                    hit = [xx for xx in (x - dx, x + dx)
                           if 0 <= xx < 128 and not m[y, xx] and not np.all(t[y, xx] == T)]
                    if hit:
                        o[y, x] = t[y, hit[0]]
                        break
            row.append(o)
        out.append(row)
    return out


# ---------------------------------------------------------------- box fit
_FIT = {}


def fit(tile, d, Ls):
    """the box (length, roof height, half width, whole-pixel shift) that best
    covers the sprite silhouette of one view (as khk_town.fit_box), with its
    parameters: dict(face, frac, z, L, zr, hw, dx, dy)"""
    key = (tile.tobytes(), d, tuple(Ls))
    if key in _FIT:
        return _FIT[key]
    m = ~is_bg(tile)
    best = None
    for L in Ls:
        for zr in (2.9, 3.1, 3.3, 3.5):
            for hw in (1.20, 1.31, 1.45):
                g = K._box_geo(d, L, zr, hw)
                b = ~is_bg(g)
                for dx in range(-6, 7):
                    for dy in range(-6, 7):
                        bb = np.roll(np.roll(b, dy, 0), dx, 1)
                        iou = (bb & m).sum() / max(1, (bb | m).sum())
                        if best is None or iou > best[0]:
                            best = (iou, L, zr, hw, g, dx, dy)
    iou, L, zr, hw, g, dx, dy = best
    g = np.roll(np.roll(g, dy, 0), dx, 1)
    face = np.where(is_bg(g), 0, g[:, :, 0]).astype(int)
    frac = (L - g[:, :, 1] / 16.0) / L
    out = dict(face=face, frac=frac, z=g[:, :, 2] / 50.0, L=L, zr=zr, hw=hw, dx=dx, dy=dy, iou=iou)
    _FIT[key] = out
    return out


def top_mask(tile, geo):
    """roof pixels: the fitted box's top face and everything drawn above the
    box in the same screen column (roof pods, fairings)"""
    face = geo["face"]
    m = ~is_bg(tile)
    top = (face == 1) & m
    for x in range(128):
        ys = np.where(face[:, x] != 0)[0]
        if len(ys):
            top[:ys.min(), x] |= m[:ys.min(), x]
        else:
            top[:, x] |= m[:, x]
    return top


def add_pods(tile, geo, d, pods, top, side):
    """draw roof boxes on a fitted sprite: pods = [(f0, f1, h, hw)] with f the
    fraction of the body from the front; top / side are the colours of the
    pod's top and side faces (side shaded per face like the renders)"""
    if not pods:
        return tile
    L, zr = geo["L"], geo["zr"]
    boxes = [Box("pod%d" % i, L * (1 - f1), L * (1 - f0), -hw, hw, zr - 0.04, zr + h)
             for i, (f0, f1, h, hw) in enumerate(pods)]

    def tex(p):
        if p.face == "top":
            return top
        return sh(side, p.face)
    img, _ = render(d, boxes, tex, L, np.array(H.origin_for(d), float))
    img = np.roll(np.roll(img, geo["dy"], 0), geo["dx"], 1)
    out = tile.copy()
    m = ~is_bg(img)
    out[m] = img[m]
    return out


# ---------------------------------------------------------------- repaint
def dark_count(tile):
    """per pixel, the number of dark pixels in its 5x5 neighbourhood"""
    dark = ((tile.max(axis=2) < 0x56) & ~is_bg(tile)).astype(int)
    p = np.pad(dark, 2)
    out = np.zeros_like(dark)
    for dy in range(5):
        for dx in range(5):
            out += p[dy:dy + 128, dx:dx + 128]
    return out


def zone_map(tile, zone_of, hubs=True):
    """per pixel the paint zone (str) or None; light pixels boxed in by dark
    ones (wheel hubs, door handrails) are never paint"""
    z = np.empty((128, 128), dtype=object)
    z[:] = None
    dc = dark_count(tile) if hubs else None
    cache = {}
    for y in range(128):
        for x in range(128):
            c = tuple(int(v) for v in tile[y, x])
            if c == T:
                continue
            if c not in cache:
                cache[c] = zone_of(c)
            zz = cache[c]
            if zz is None:
                continue
            if hubs and zz == "white" and dc[y, x] >= 13:
                continue
            z[y, x] = zz
    return z


def repaint(src_rows, zone_of, targets, Ls, decals=None, pods=None, pod_cols=None, recol=None,
            hubs=True):
    """repaint hand-drawn rows zone by zone, keeping the shading.
    zone_of(colour) -> zone name / None; targets: zone -> (side colour, roof
    colour); each pixel takes its target scaled by its luminance over the
    zone's median luminance (separately for roof and the rest), so the
    artist's light and shade stay. Ls: per row the fit lengths. decals(out,
    paint, geo, d, r) draws on the result; pods per row [(f0, f1, h, hw)];
    recol(colour) -> colour for the other pixels (displays, glass)."""
    maps = []
    stats = {}
    for r, tiles in enumerate(src_rows):
        row = []
        for d, t in zip(DIRS, tiles):
            geo = fit(t, d, Ls[r])
            zm = zone_map(t, zone_of, hubs)
            top = top_mask(t, geo)
            row.append((geo, zm, top))
            for y, x in zip(*np.where(zm != None)):              # noqa: E711
                stats.setdefault((zm[y, x], bool(top[y, x])), []).append(lum(t[y, x]))
        maps.append(row)
    med = {k: float(np.median(v)) for k, v in stats.items()}
    rows = []
    for r, tiles in enumerate(src_rows):
        out_row = []
        for c, (d, t) in enumerate(zip(DIRS, tiles)):
            geo, zm, top = maps[r][c]
            o = t.copy()
            for y in range(128):
                for x in range(128):
                    zz = zm[y, x]
                    if zz is None:
                        if recol is not None:
                            col = tuple(int(v) for v in t[y, x])
                            if col != T:
                                n = recol(col)
                                if n is not None:
                                    o[y, x] = n
                        continue
                    tp = bool(top[y, x])
                    ref = med.get((zz, tp)) or med.get((zz, not tp))
                    k = max(0.55, min(1.12, lum(t[y, x]) / ref))
                    base = targets[zz][1 if tp else 0]
                    o[y, x] = scaled(base, k)
            if pods and pods[r]:
                side, top_c = pod_cols
                o = add_pods(o, geo, d, pods[r], top_c, side)
            if decals is not None:
                paint = zm != None                                  # noqa: E711
                o = decals(o, paint, geo, d, r)
            out_row.append(o)
        rows.append(out_row)
    return rows


# ---------------------------------------------------------------- decals
SIDE = {"w", "e", "n", "s", "ne", "sw"}


def lower_panel(tile, paint, geo, d):
    """per screen column of the side faces: (y of the first body row under the
    window band, face id, fraction from the front)"""
    line = K.band_line(tile, paint, geo, d)
    out = {}
    for x, y in line.items():
        if y + 1 < 128:
            out[x] = (y + 1, int(geo["face"][y + 1, x]), float(geo["frac"][y + 1, x]))
    return out


def decal_columns(panel, face, f0, f1):
    """the screen columns of one side whose body fraction lies in [f0, f1),
    sorted left to right as seen"""
    return sorted(x for x, (y, fc, f) in panel.items() if fc == face and f0 <= f < f1)


def put(o, paint, x, y, col):
    if 0 <= y < 128 and paint[y, x]:
        o[y, x] = col


def havirov_decals(logo_r=(0.56, 0.71), slogan_r=(0.29, 0.44), logo_l=(0.40, 0.55),
                   slogan_l=(0.56, 0.71), figure=None):
    """the white city logo (three linked arches) and the yellow slogan on the
    lower panel of both sides; reading left to right the logo comes first on
    either side, so on the door side it sits behind the middle door (slogan
    ahead of it) and on the other side ahead of mid-length (slogan behind it).
    figure = (f0, f1): the big white Transdev figure on the rear corners."""
    def draw(o, paint, geo, d, r):
        if d not in SIDE or r != 0 and figure is None:
            return o
        panel = lower_panel(o, paint, geo, d)
        o = o.copy()
        for face, lr, sr in ((4, logo_r, slogan_r), (5, logo_l, slogan_l)):
            if r == 0:
                cols = decal_columns(panel, face, *lr)
                for i, x in enumerate(cols):
                    y = panel[x][0]
                    if i % 3 != 2 or i == len(cols) - 1:
                        put(o, paint, x, y + 1, HAV_LOGO)
                        put(o, paint, x, y + 2, HAV_LOGO)
                cols = decal_columns(panel, face, *sr)
                for i, x in enumerate(cols):
                    y = panel[x][0]
                    if i % 4 != 3:
                        put(o, paint, x, y + 1, HAV_YEL)
                    if i % 3 == 1:
                        put(o, paint, x, y + 2, HAV_YEL)
            if figure is not None:
                cols = decal_columns(panel, face, *figure)
                for i, x in enumerate(cols):
                    y = panel[x][0]
                    for yy in (y, y + 1, y + 2):
                        if (i + yy) % 2 == 0:
                            put(o, paint, x, yy, HAV_LOGO)
        return o
    return draw


def skirt_decal(colour, z_top, base=None):
    """decals(): the paint below z_top metres (side, front and rear faces) in
    `colour`, shaded like the white it replaces (the 3ČSAD green skirt on
    sheets drawn plain white)"""
    def draw(o, paint, geo, d, r):
        if base is not None:
            o = base(o, paint, geo, d, r)
        o = o.copy()
        z = geo["z"]
        for y, x in zip(*np.where(paint & (geo["face"] != 1) & (geo["face"] != 0))):
            if float(z[y, x]) < z_top:
                k = max(0.55, min(1.12, lum(o[y, x]) / lum(WHITE)))
                o[y, x] = scaled(colour, k)
        return o
    return draw


# ---------------------------------------------------------------- output
def save_sheet(rows, path, allow=()):
    return K.save_sheet(rows, path, allow)


def preview(rows, path, z=4):
    K.preview(rows, path, z)


# ====================================================================== natives
# screen px per carunit of travel (CLAUDE.md "Section placement")
STEP = {"w": (-4, -2), "e": (4, 2), "n": (4, -2), "s": (-4, 2),
        "ne": (5.66, 0), "sw": (-5.66, 0), "nw": (0, -2.83), "se": (0, 2.83)}
SLOPE = {"w": 0.5, "e": 0.5, "n": -0.5, "s": -0.5, "ne": 0.0, "sw": 0.0}
NB12_REF = "tools/busrender/src/sor_nb_12-lane-ref.png"     # a native-placed 12 m bus (VTPsim's DPP NB 12)


def body_extent(tile):
    from scipy import ndimage
    m = ~is_bg(tile)
    mo = ndimage.binary_opening(m, structure=np.ones((3, 3)))
    lab, n = ndimage.label(mo)
    if n == 0:
        return 0
    big = lab == (1 + int(np.argmax(ndimage.sum(mo, lab, range(1, n + 1)))))
    xs = np.where(big.any(axis=0))[0]
    return xs.max() - xs.min() + 1


def drawn_length(tiles):
    """length in carunits from the ne / sw width against a native 12 m bus"""
    ref = load_rows(NB12_REF)[0]
    out = [8 + (body_extent(tiles[DIRS.index(d)]) - body_extent(ref[DIRS.index(d)])) / 5.66
           for d in ("ne", "sw")]
    return sum(out) / 2


def shift_tile(tile, dx, dy):
    out = np.empty_like(tile)
    out[:] = T
    ys, xs = np.where(~is_bg(tile))
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
    if not ok.all():
        raise SystemExit(f"shift ({dx},{dy}) pushes {int((~ok).sum())} px off the tile")
    out[ny, nx] = tile[ys, xs]
    return out


def place(tiles, length):
    """move every view so the body sits where the length rule puts a bus of
    `length` drawn carunits: its front where a native 12 m bus has its front,
    on the native lane (sideways too: VTPsim's sheets sit off the lane)"""
    out = []
    for d, t in zip(DIRS, tiles):
        X, C = metrics(t, d)
        mx, mc = MEDIAN[d]
        sx, sy = STEP[d]
        ahead = 4 - length / 2
        if d in ("nw", "se"):
            dx = mx - X
            dy = (mc + ahead * sy) - C
        else:
            dx = (mx + ahead * sx) - X
            dy = dx * sy / sx                          # along the road
            dy += mc - (C + dy - SLOPE[d] * dx)        # then onto the lane
        out.append(shift_tile(t, int(round(dx)), int(round(dy))))
    return out


def port_native(name, Ls, display=LEDW, green=None):
    """a VTPsim pak128.cs sheet frozen in src/odis/: passenger glass into the
    lit specials, the windscreen and driver's window plain, the green-LED
    displays into `display`, the other specials nudged off, placed on the lane;
    green = (colour) recolours VTPsim's 3ČSAD green (6BBD29) to the repo's"""
    tiles = load_rows(name + ".png")[0]
    length = drawn_length(tiles)
    tiles = place(tiles, length)
    out = []
    for d, t in zip(DIRS, tiles):
        geo = fit(t, d, Ls)
        o = t.copy()
        for y, x in zip(*np.where(~is_bg(t))):
            c = tuple(int(v) for v in t[y, x])
            h = hexc(c)
            cab = geo["face"][y, x] == 2 or (geo["face"][y, x] == 5 and geo["frac"][y, x] < 0.10)
            if h == 0x6B6B6B:
                o[y, x] = SCREEN if cab else GLASS
            elif h == 0x9B9B9B:
                o[y, x] = SCREEN_HI if cab else GLASS2
            elif h == 0x01DD01:
                o[y, x] = display
            elif green is not None and c[1] > c[0] + 0x30 and c[1] > c[2] + 0x30:
                o[y, x] = scaled(green, lum(c) / lum((0x6B, 0xBD, 0x29)))
            elif h in H.SPECIAL and h not in H.ALLOWED:
                o[y, x] = K.safe(c)
        out.append(o)
    return [out], length


# ====================================================================== SOR NS renders
# OVeh paints the dpmhk.py bodies (H.NS12 / H.NS18). Palette keys:
#   body / roof   side and roof colour; pod_side the roof boxes' sides
#   black0        Karviná: black from this height up to the roof edge (white skirt below)
#   mask, pillar  lower front mask and windscreen pillars (2023 face)
#   disp          destination display colour
#   decals        "havirov" (logo + slogan), "karvina" (white wordmark on the black)
OPAL = {
    "hav": dict(body=HAV_BLUE, roof=HAV_ROOF, pod_side=HAV_BLUE, black0=None, disp=LEDW,
                mask=HAV_BLUE, pillar=HAV_BLUE, decals="havirov"),
    "kar": dict(body=WHITE, roof=(0xF2, 0xF2, 0xF0), pod_side=(0xEC, 0xEC, 0xEA), black0=0.80, disp=LEDW,
                mask=WHITE, pillar=KAR_BLACK, decals="karvina", dark_glass=True),
}


class OVeh(Veh):
    FACE_SPLIT = {}            # its faces lost nothing distinct on the base
    def setup_livery(self):
        self.P = OPAL[self.liv]
        self.ROOF = self.P["roof"]
        self.TRIM = BLACK
        self.newface = self.sp.get("newface", False)
        self.ns_decal = {k: tuple(self.M(v) for v in r) for k, r in self.sp.get("decal", {}).items()}

    def tex_roof(self, p, u):
        if self.newface and u < 0.45:
            return BLACK                                  # the black cap over the windscreen
        if not self.newface and u < self.cap:
            return BLACK if abs(p.t) < HW - 0.30 else self.TRIM
        return self.ROOF

    def tex_pod(self, p, u, k):
        f = p.face
        if f == "top":
            if self.pods[k][4] == "ac" and abs(p.t) < 0.25:
                return scaled(self.ROOF, 0.86)            # condenser grille
            return self.ROOF
        return sh(self.P["pod_side"], f)

    def tex_side(self, p, u, U1):
        z, f = p.z, p.face
        right = f == "right"
        for a in self.axles:
            if abs(u - a) < 0.62 and z < 1.02 and math.hypot(u - a, z - self.WR) < 0.62:
                return None
        if u < 0.26 and z >= self.ZBAND0:
            return BLACK                                  # windscreen frame wrapping round
        if not self.newface and u < self.cap and z >= self.ZBAND1 + 0.17:
            return BLACK
        if right:
            d = self.door_at(u)
            if d and z < self.ZWIN1 + 0.05:
                return self.tex_door(p, u, U1, d)
        if z >= self.ZBAND0:
            if z < self.ZWIN1 + 0.05 or (right and inr(u, *self.sidedisp) and z < self.ZWIN1 + 0.30):
                c = self.glass_band(p, u, U1, right)
                if c == H.AMBER:
                    return self.P["disp"]
                if c == GLASS2 and self.P.get("dark_glass"):
                    c = GLASS                             # tinted glass reads black
                if not right and inr(u, *self.drv):
                    if c == GLASS:
                        return SCREEN                     # driver's window, never lit
                    if c == GLASS2:
                        return SCREEN_HI
                return c
            return self.cant(p, u)
        return self.lower(p, u, right)

    def cant(self, p, u):
        if self.newface and u < 0.45:
            return BLACK
        if p.z < self.ZBAND1:
            return sh(BLACK, p.face)
        return sh(self.P["body"], p.face)

    def door_kick(self):
        return None

    def decal(self, p, u, right):
        """Havířov: white logo (three arches) then the yellow slogan, reading
        left to right on both sides; Karviná: the white wordmark on the black"""
        z = p.z
        kind = self.P["decals"]
        side = "r" if right else "l"
        if kind == "havirov":
            a, b = self.ns_decal["logo_" + side]
            if inr(u, a, b) and inr(z, 0.62, 1.12):
                i = int((u - a) / 0.30)
                return HAV_LOGO if i % 3 != 2 else None
            a, b = self.ns_decal["slogan_" + side]
            if inr(u, a, b):
                i = int((u - a) / 0.30)
                if inr(z, 0.88, 1.12) and i % 4 != 3:
                    return HAV_YEL
                if inr(z, 0.62, 0.88) and i % 3 == 1:
                    return HAV_YEL
        elif kind == "karvina":
            a, b = self.ns_decal["logo_" + side]
            if inr(u, a, b) and inr(z, 0.95, 1.20) and int((u - a) / 0.30) % 3 != 1:
                return HAV_LOGO
        return None

    def lower(self, p, u, right):
        z, f = p.z, p.face
        c = self.decal(p, u, right)
        if c is not None:
            return c
        b0 = self.P["black0"]
        if b0 is not None and z >= b0:
            return sh(KAR_BLACK, f)
        return sh(self.P["body"], f)

    def tex_front(self, p):
        t, z = p.t, p.z
        f = "front"
        a = abs(t)
        P = self.P
        if self.newface:
            # 2023 SOR NS face: black from the windscreen down to the lamps,
            # body-colour lower mask rising to the corners, black LED lamp pods
            # in the corners, black grille band in the bumper
            if z < 0.30:
                return BLACK
            if z < 0.44 and a < HW - 0.44:
                return BLACK
            vtop = 0.98 + 0.14 * (a / HW)
            if z < vtop:
                if a > HW - 0.42 and z >= 0.50:
                    if inr(z, 0.62, 0.80) and inr(a, HW - 0.36, HW - 0.12):
                        return H.HEADL
                    return BLACK
                return sh(P["mask"], f)
            if a > HW - 0.10:
                return sh(P["pillar"], f)
            if inr(z, 1.12, 2.46) and a < HW - 0.16:
                return SCREEN
            if inr(z, 2.54, 2.82) and a < 0.98:
                return P["disp"]
            return BLACK
        # 2022 face (NSG 18 prototype): black mask, silver lamp clusters and trim
        if z < 0.44:
            return BLACK
        if z < 1.08:
            if a > HW - 0.40:
                if inr(z, 0.62, 0.88) and a < HW - 0.10:
                    return H.HEADL
                return sh(H.SILVER, f)
            if z > 0.98:
                return sh(H.SILVER, f)
            return BLACK
        if a > HW - 0.10:
            return sh(P["pillar"], f)
        if inr(z, 1.14, 2.42) and a < HW - 0.16:
            return SCREEN
        if inr(z, 2.52, 2.82) and a < 0.98:
            return P["disp"]
        return BLACK

    def tex_rear(self, p):
        t, z = p.t, p.z
        f = "rear"
        a = abs(t)
        P = self.P
        if a > HW - 0.26 and inr(z, 0.55, 1.35):
            return H.TAILL
        if z < 0.40:
            return BLACK
        if z >= self.ZR - 0.24:
            return sh(P["roof"], f)
        if z >= self.ZBAND0 + 0.20:
            if inr(z, 2.42, 2.62) and inr(t, 0.30, 0.80):
                return P["disp"]
            if inr(z, 1.75, 2.62) and a < HW - 0.30:
                return GLASS
            if self.sp.get("grille") and inr(z, 1.40, 2.62) and t < -0.30:
                return sh((0x2C, 0x2E, 0x32), f)          # engine-air grille (diesel)
            return BLACK
        return sh(P["body"], f)


def ns_rows(sp, liv):
    m = OVeh(sp, liv)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        tiles = []
        for d in DIRS:
            o = np.array(H.origin_for(d), float)
            if not m.single:
                o = o + (4 - l / 2.0) * H.PER_CU[d]
            img, _ = render(d, m.boxes(i), m.tex_for(i), L, o)
            tiles.append(img)
        rows.append(tiles)
    return rows


# decal spans in real metres from the front: logo / slogan, door side (r) and the other side (l)
NS12_DECAL = dict(logo_r=(6.40, 7.90), slogan_r=(3.40, 4.75), logo_l=(4.70, 6.20), slogan_l=(6.35, 7.85))
NS18_DECAL = dict(logo_r=(6.30, 7.85), slogan_r=(3.40, 4.70), logo_l=(4.70, 6.20), slogan_l=(6.35, 7.85))
KAR_DECAL = dict(logo_r=(6.40, 7.90), logo_l=(4.60, 6.10))
# Havířov SOR NSG 12 (2025-26, 2023 face): a low unit behind the cap and the long
# CNG fairing over the middle, both in the body blue (photos Transdev / dopravacek)
NSG12 = H.mk(H.NS12, newface=True, decal=NS12_DECAL,
             pods=[(1.40, 3.10, 0.14, 0.85, "ac"), (3.40, 8.30, 0.30, 1.05, "fair")])
# Havířov SOR NSG 18 prototype (2022 face): fairing over the front section, a
# low box on the rear section
NSG18 = H.mk(H.NS18, cap=0.80, decal=NS18_DECAL,
             pods=[(2.00, 4.00, 0.18, 0.90, "ac"), (4.40, 10.40, 0.30, 1.05, "fair"),
                   (12.40, 14.60, 0.22, 0.90, "fair")])
# Karviná SOR NS 12 (2023): the diesel with a roof A/C unit and the rear air
# grille; the electric with battery boxes over the front two thirds and the A/C
KNS12 = H.mk(H.NS12, newface=True, decal=KAR_DECAL, grille=True,
             pods=[(3.40, 6.20, 0.22, 0.85, "ac")])
KNS12E = H.mk(H.NS12, newface=True, decal=KAR_DECAL,
              pods=[(1.50, 4.30, 0.26, 1.00, "fair"), (4.60, 7.40, 0.26, 1.00, "fair"),
                    (7.80, 9.80, 0.22, 0.85, "ac")])


# ====================================================================== IREDO models
def reading_col(bus, x, a, b, right):
    """screen column of x in the span [a, b), counted left to right as seen
    (on the door side screen-left is the rear)"""
    return bus.colidx(x, b, backwards=True) if right else bus.colidx(x, a)


class HavBlue(M.Livery):
    """Havířov city blue: one azure blue, roof boxes in the same paint; the
    white logo behind the middle door and the yellow slogan ahead of it on
    the door side, on the other side the logo at mid-length, slogan behind."""
    slug = "havirovmodra"
    body = HAV_BLUE
    roof = HAV_ROOF
    ac = HAV_ROOF
    seam = (0x10, 0x6E, 0xB6)
    LOGO_R = (6.35, 7.25)
    SLOGAN_R = (3.15, 4.95)
    LOGO_L = (4.10, 5.40)
    SLOGAN_L = (5.60, 7.20)

    def side(self, bus, x, k, right):
        band = bus.band_at(x)
        if band is None:
            return None
        b0 = band[0]
        spans = (((self.LOGO_R, "logo"), (self.SLOGAN_R, "slogan")) if right else
                 ((self.LOGO_L, "logo"), (self.SLOGAN_L, "slogan")))
        for (a, b), kind in spans:
            if not a <= x < b:
                continue
            c = reading_col(bus, x, a, b, right)
            if kind == "logo" and k in (b0 - 1, b0 - 2) and c % 3 != 2:
                return HAV_LOGO
            if kind == "slogan":
                if k == b0 - 1 and c % 4 != 3:
                    return HAV_YEL
                if k == b0 - 2 and c % 3 == 1:
                    return HAV_YEL
        return None

    def ac_side(self):
        return Sh(HAV_BLUE)


class CsadWG(M.Livery):
    """3ČSAD white-green: white body and roof, the green skirt straight along
    the side up to row TOP (a body's CSAD_TOP overrides it), the white band
    from there to the windows at least as tall as the green (the owner,
    2026-10-24: in the game the white was too small and the bus read green,
    not white and green); with SWEEP (a body's CSAD_SWEEP overrides it) the
    green rises to the windows behind the front door, as on the Crossways.
    The lower front is green up to the headlamps (the lamps, the SOR badge
    and the plate stay), the lower rear up to row 2 round the tail lamps."""
    slug = "3csadbilozelena"
    body = WHITE
    roof = (0xF2, 0xF2, 0xF0)
    ac = (0xEE, 0xEE, 0xEC)
    seam = (0xDA, 0xDB, 0xD9)
    TOP = 2
    SWEEP = True

    def __init__(self):
        self.bumper = CSAD["green"]

    def top(self, bus, x, b0):
        """the skirt's top row at x under glazing from row b0"""
        top_g = getattr(bus, "CSAD_TOP", self.TOP)
        top_g = min(top_g, bus.SKIRT - 1 + (b0 - bus.SKIRT) // 2)     # no more green rows than white
        if getattr(bus, "CSAD_SWEEP", self.SWEEP):
            d1 = bus.DOORS[0][1]
            if x < d1:
                return b0 - 1
            if x < d1 + 1.0:
                return top_g + int(round((b0 - 1 - top_g) * (1 - (x - d1) / 1.0)))
        return top_g

    def side(self, bus, x, k, right):
        band = bus.band_at(x)
        b0 = band[0] if band else bus.R_BAND0
        top = self.top(bus, x, b0)
        if k <= top:
            return CSAD["green"]
        if k == top + 1 and top < b0 - 1 and CSAD["line"] is not None:
            return CSAD["line"]
        return None

    def front(self, bus, v, k):
        """the headlamp row between the lamps (rows 0-1 are the bumper)"""
        av = abs(v)
        badge, lamp = (0.12, 0.55) if isinstance(bus, M.SorFace) else (0.0, 0.48)
        if k == 2 and badge <= av < bus.W2 - lamp:
            return CSAD["green"]
        return None

    def rear(self, bus, v, k):
        """up to row 2, round the tail lamps and the plate"""
        av = abs(v)
        if k > 2 or (k >= 1 and av > bus.W2 - 0.22) or (k == 1 and av < 0.28):
            return None
        return CSAD["green"]


class Bruntal(M.Livery):
    """MHD Bruntál (Transdev Morava SOR CNG 12): plain white, the kraj ring
    over the rear axle in three greens (below the windows only its rear arc),
    the BRUNTÁL logo on the panel behind the front axle: teal, green and
    light-blue bands, then navy lettering."""
    slug = "bruntalbila"
    body = WHITE
    roof = (0xF2, 0xF2, 0xF0)
    ac = (0xEE, 0xEE, 0xEC)
    seam = (0xDA, 0xDB, 0xD9)
    RING = [(0xC6, 0xDA, 0x9A), (0xA8, 0xCB, 0x6E), (0x8D, 0xBE, 0x50)]
    LOGO = [(0x25, 0x69, 0x5D), (0x3A, 0xA2, 0x35), (0x1B, 0xA0, 0xC4)]
    NAVY = (0x27, 0x22, 0x5F)
    PALE = (0xDA, 0xE8, 0xBC)      # the ring printed see-through on the glass

    def ring(self, bus, x, k, b0):
        """the ring centred over the rear axle at the window line: full on the
        glass (pale), only its rear arc on the paint below"""
        xc = bus.axles[-1]
        r = math.hypot((x - xc) / 1.05, (k - b0) / 4.4)
        if not 0.40 <= r <= 1.0:
            return None
        if k >= b0:
            return self.PALE
        if x < xc - 0.25:
            return None
        ang = math.atan2(k - b0, x - xc)
        return self.RING[int((ang + math.pi) / (math.pi / 5)) % 3]

    def side(self, bus, x, k, right):
        band = bus.band_at(x)
        b0 = band[0] if band else bus.R_BAND0
        c = self.ring(bus, x, k, b0)
        if c is not None and k < b0:
            return c
        a, b = bus.axles[0] + 0.75, bus.DOORS[1][0] - 0.20
        if a <= x < b and k == b0 - 1:
            c = reading_col(bus, x, a, b, right)
            if c < 3:
                return self.LOGO[c]
            if c % 2 == 0 or c == 4:
                return self.NAVY
        return None


for _lv in (HavBlue, CsadWG, Bruntal):
    M.LIVERIES[_lv.slug] = _lv


class TownBus:
    """town bus: no IREDO kraj sticker, the town's display colour"""
    KHK_STICKER = False
    DISP = LEDW

    def front_face(self, v, av, k, d):
        c = super().front_face(v, av, k, d)
        return self.DISP if c == M.LED else c


class HavCNG105(TownBus, M.SorCN105):
    """SOR CNG 10,5 (2015): the CN 10,5 with the CNG fairing over the low roof"""
    AC = (0.9, 5.4)
    AC_H = 0.34
    HATCHES = (9.1,)


class BruCNG12(TownBus, M.SorCNG):
    """SOR CNG 12 (2015); the green ring reaches over the windows"""

    def side(self, u, z, right):
        x, k = self.X(u), self.row(z)
        band = self.band_at(x)
        if band and band[0] <= k < band[1] and self.wheel(u, z) is None                 and not (right and self.door(x, k) is not None):
            c = self.lv.ring(self, x, k, band[0])
            if c is not None:
                return c
        return super().side(u, z, right)


class OrlCrossway108(TownBus, M.CrosswayLELine108):
    DISP = K.LEDG


class OrlIrisbus(TownBus, M.IrisbusCrosswayLE):
    """Irisbus Crossway LE 12M (2012-2013), the Orlová stand-ins 393 / 401:
    3ČSAD white-green, green LED displays"""
    DISP = K.LEDG


class NjRed(M.Livery):
    """Nový Jičín red on ARRIVA's BN 10,5 7577 (layout unverified, as the town's
    EBN 9,5): red all over, the black mask round the headlamps over a red bumper"""
    slug = "njcervenocerna"
    sticker = False
    body = NJ_RED
    roof = NJ_ROOF
    ac = NJ_ROOF
    seam = (0x8A, 0x16, 0x1C)
    bumper = NJ_RED

    def front(self, bus, v, k):
        return KAR_BLACK if 2 <= k <= 3 else None


M.LIVERIES[NjRed.slug] = NjRed


class OrlBN95(TownBus, M.SorBN95):
    """SOR BN 9,5 (Orlová 434): 3ČSAD white-green, white LED displays"""


class NjBN105(TownBus, M.SorBN105):
    """SOR BN 10,5 (ARRIVA 7577): amber LED displays"""
    DISP = M.LED


class HavBNG105(TownBus, M.SorCN105):
    """SOR BNG 10,5 (2016): the low-floor SOR of the CN 10,5 family, no step in
    the window line or roof, CNG fairing over the front two thirds, green LEDs"""
    BAND = ((0.0, 10.6, 5, 11),)
    ROOF_STEP = None
    DOOR_RAISE = 0
    REAR_GLASS = (7, 10)
    AC = (0.9, 6.4)
    AC_H = 0.34
    HATCHES = (9.1,)
    DISP = K.LEDG


# ====================================================================== sheets
L12 = [11.5, 12.0, 12.5]
FM = "vehicle-bus/mhd-frydek-mistek/"
# the Frýdek-Místek 3ČSAD sheets as ported (the emerald green), frozen in
# src/odis/ as FM-<family>-3csadbilozelena.png: the Havířov, Karviná and
# Orlová sheets read them, and --csad-static writes the F-M sheets from them
# in CSAD["green"]
FM_CSAD = ("crossway_le_city_12m", "scania_citywide_lf_12m_cng", "urbanway_12m_cng")


def fm_src(fam):
    return "FM-" + fam + "-3csadbilozelena.png"


UW_SRC = fm_src("urbanway_12m_cng")
CW_SRC = fm_src("scania_citywide_lf_12m_cng")
CW_ALLOW = (0xC1B1D1, 0xE3E3FF)    # specials the Citywide source art already uses (lamp glass)
SW_SRC = "vehicle-bus/dpmp/streetway_12m/sprites/ivecopredvadeci.png"
SW18_SRC = "vehicle-bus/dpp/streetway_18m/sprites/pidsedocervena.png"
DEK_SRC = "vehicle-bus/mhd-tabor/dekstra_lf_38_cng/sprites/comettbila.png"
ROS_SRC = "vehicle-bus/mhd-tabor/rosero_first/sprites/comettbila.png"
NOVO_SRC = "vehicle-bus/mhd-kolin/novociti_life/sprites/bila.png"
PAPER = (0xD8, 0xD8, 0xCE)         # Orlová Isuzu: paper destination board behind the windscreen
ISUZU_BLUE = (0x2E, 0x3C, 0x80)    # its dark-blue roof unit


def z_white_green(c):
    """3ČSAD white-green sheets (F-M Urbanway / Citywide, VTPsim natives)"""
    if hexc(c) in H.SPECIAL:
        return None
    if neutral(c, 0xB0):
        return "white"
    if c[1] > c[0] + 0x30 and c[1] > c[2] + 0x20:
        return "green"
    return None


def z_green(c):
    return "green" if z_white_green(c) == "green" else None


def z_white(c):
    return "white" if z_white_green(c) == "white" else None


SWOOSH = {0xE86A20, 0xC81E14, 0xD50B15, 0xC00A13, 0xAC0911}


def streetway_src():
    """the DPMP Streetway sheet with the demonstrator's red-orange swoosh (which
    crosses the windows) painted out; the lone orange side markers stay"""
    def deco(t, y, x):
        h = hexc(t[y, x])
        if h in SWOOSH:
            return True
        if h == 0xFF8040:
            n = [hexc(t[yy, xx]) for yy in range(max(0, y - 1), min(128, y + 2))
                 for xx in range(max(0, x - 1), min(128, x + 2)) if (yy, xx) != (y, x)]
            return any(v in SWOOSH or v == 0xFF8040 for v in n)
        return False
    return inpaint(load_rows(SW_SRC), deco)


def z_streetway(c):
    return z_white(c)


def z_pid(c):
    """DPP PID grey-red (Streetway 18M): the light greys and the reds are paint"""
    if hexc(c) in H.SPECIAL:
        return None
    r, g, b = c
    if neutral(c, 0xB0, tol=16):
        return "white"
    if r > g + 0x60 and r > b + 0x60:
        return "red"
    return None


def z_red_white(c):
    """Kladno white-red (VTPsim SOR NBG 18)"""
    if hexc(c) in H.SPECIAL:
        return None
    if neutral(c, 0xB0):
        return "white"
    r, g, b = c
    if r > 0x90 and g < 0x30 and b < 0x30:
        return "red"
    return None


def z_comett(c):
    """Tábor COMETT white (Dekstra / Rošero): white and the orange patch"""
    if hexc(c) == 0xF55F1B:
        return "white"
    return z_white(c)


def disp(colour, frm=(0xF0A018, 0xF7A21B)):
    """recol rule: the sheet's display colour into `colour`"""
    return lambda c: colour if hexc(c) in frm else None


HAV = {z: (HAV_BLUE, HAV_ROOF) for z in ("white", "green", "red")}
HAV_POD = (HAV_BLUE, HAV_ROOF)                  # (sides, top)
WHITE_POD = ((0xEC, 0xEC, 0xEA), (0xF4, 0xF4, 0xF2))
TO_WHITE = {"green": (WHITE, WHITE), "white": (WHITE, WHITE)}


def hav_rows(src, zone_of, Ls, pods=None, figure=None, recol=None, rows=None):
    return lambda: repaint(load(src, rows), zone_of, HAV, Ls, havirov_decals(figure=figure),
                           pods, HAV_POD, recol or disp(LEDW))


def hav_native(name, Ls, display=LEDW, pods=None):
    def build():
        rows, _ = port_native(name, Ls[0], display)
        return repaint(rows, z_white_green, HAV, Ls, havirov_decals(), pods, HAV_POD)
    return build


def csad_px(c):
    """recol rule: the emerald 3ČSAD green of a ported sheet (CSAD_GREEN and its
    shades: hue from 112 degrees) into CSAD["green"] at the same luminance
    ratio; specials and other colours stay"""
    if hexc(c) in H.SPECIAL or z_white_green(c) != "green":
        return None
    if colorsys.rgb_to_hsv(*[v / 255 for v in c])[0] * 360 < 112:
        return None
    return scaled(CSAD["green"], lum(c) / lum(CSAD_GREEN))


def recols(*rules):
    """recol rule: the first of `rules` that changes the colour"""
    def rule(c):
        for r in rules:
            n = r(c)
            if n is not None:
                return n
        return None
    return rule


def write_fm_csad():
    """the static Frýdek-Místek 3ČSAD sheets from their frozen sources, the
    green in CSAD["green"]"""
    for fam in FM_CSAD:
        rows = [[K.recolour(t, csad_px) for t in tiles] for tiles in load_rows(fm_src(fam))]
        a = np.array(Image.open(os.path.join(SRC, fm_src(fam))).convert("RGB")).reshape(-1, 3).astype(np.int64)
        used = set(np.unique((a[:, 0] << 16) | (a[:, 1] << 8) | a[:, 2]).tolist())
        rel = FM + fam + "/sprites/3csadbilozelena.png"
        save_sheet(rows, os.path.join(REPO, *rel.split("/")), used & H.SPECIAL)
        print(rel)


def copy_rows(src, recol=None):
    """an existing sheet, only the display colour changed (or none)"""
    def build():
        rows = load_rows(src)
        if recol is None:
            return rows
        return [[K.recolour(t, recol) for t in tiles] for tiles in rows]
    return build


def white_rows(src, zone_of, Ls, pods=None, recol=None):
    return lambda: repaint(load(src), zone_of, TO_WHITE, Ls, None, pods, WHITE_POD, recol or disp(LEDW))


def ns(sp, liv):
    return lambda: ns_rows(sp, liv)


def model(cls, liv):
    return lambda: [row_for(cls, liv)]


def stratos_rows():
    """Orlová Stratos LF 38 CNG 619: VTPsim's ODIS Stratos (3ČSAD white-green)
    ported, its grey roof white, the short CNG box added, the two-tone green
    CNG roundel over the rear of both sides, amber displays"""
    rows, _ = port_native("CZ-ODIS-IvecoStratos_LF38-Green", [7.0, 7.5, 8.0], AMBER, CSAD["green"])

    def zone(c):
        return "roof" if hexc(c) in (0xC5C5C5, 0xBDBDBD) else None

    def roundel(o, paint, geo, d, r):
        if d not in SIDE:
            return o
        panel = lower_panel(o, paint, geo, d)
        o = o.copy()
        for face in (4, 5):
            cols = decal_columns(panel, face, 0.78, 0.95)
            for i, x in enumerate(cols):
                y = panel[x][0]
                ring = (0x9B, 0xD2, 0x7A) if i in (0, len(cols) - 1) else CSAD["green"]
                put(o, paint, x, y, ring)
                if 0 < i < len(cols) - 1:
                    put(o, paint, x, y + 1, (0x9B, 0xD2, 0x7A))
        return o
    def paint_all(c):
        return "white" if neutral(c, 0xB0) and hexc(c) not in H.SPECIAL else zone(c)
    return repaint(rows, paint_all, {"roof": ((0xE6, 0xE6, 0xE4), (0xF4, 0xF4, 0xF2)),
                                     "white": ((0xE6, 0xE6, 0xE4), (0xF4, 0xF4, 0xF2))},
                   [[7.0, 7.5, 8.0]], roundel, [[(0.32, 0.62, 0.24, 0.80)]], WHITE_POD)


def isuzu_rows():
    """Orlová Isuzu NovoCiti Life 996: the plain white Kolín car with the dark
    blue roof unit and a paper board instead of the LED display"""
    return repaint(load_rows(NOVO_SRC), z_white, {"white": ((0xF2, 0xF2, 0xF0), (0xF6, 0xF6, 0xF4))},
                   [[6.5, 7.0, 7.5]], None, [[(0.68, 0.92, 0.18, 0.70)]], (ISUZU_BLUE, (0x3A, 0x4A, 0x96)),
                   disp(PAPER))


# ====================================================================== families
def f_(cost, payload, speed, weight, run, fixed, intro, length, engine, power, gear,
       intro_month=1, retire=2060, smoke=None):
    return K.f_(cost, payload, speed, weight, run, fixed, intro, length, engine, power, gear,
                intro_month=intro_month, retire=retire, smoke=smoke)


HAVIROV = ("MHDHavirov", "MHD Havířov", "MHD Havířov")
NOVYJICIN = ("MHDNovyJicin", "MHD Nový Jičín", "MHD Nový Jičín")
KARVINA = ("MHDKarvina", "MHD Karviná", "MHD Karviná")
ORLOVA = ("MHDOrlova", "MHD Orlová", "MHD Orlová")
BRUNTAL = ("MHDBruntal", "MHD Bruntál", "MHD Bruntál")
BUS = ("bus", "autobus")
EBUS = ("electric bus", "elektrobus")
MIDI = ("midibus", "midibus")
HAV_NAME = ("Havířov city blue", "modrá města Havířov")
WG_NAME = ("3ČSAD white-green", "3ČSAD bílo-zelená")
W_NAME = ("white", "bílá")
KAR_NAME = ("Karviná white-black", "Karviná, bílo-černá")

RENDER_NS = ("original box-model render (vojtechzicha): the SOR NS body of\n"
             "tools/busrender/dpmhk.py painted by odis_town.OVeh.")
RENDER_IR = ("original box-model render (vojtechzicha): {cls} of\n"
             "tools/busrender/iredo_models.py with the livery of odis_town.py.")
HAV_DECALS = ("the white city logo (three linked arches) and the yellow \"město pro\n"
              "život\" script on the lower side, the logo first reading left to right on\n"
              "both sides")


def one(vid, display, role, fields):
    return [dict(id=vid, display=display, role=role, fields=fields)]


def artic(base, display, fa, fb):
    return [dict(id=base + "-A", display=display, role=("front section", "přední díl"), row=0,
                 head=True, tail=False, next=[base + "-B"], fields=fa),
            dict(id=base + "-B", display=display, role=("rear section", "zadní díl"), row=1,
                 head=False, tail=True, prev=[base + "-A"], fields=fb)]


FAMILIES = {
    # ------------------------------------------------------------ Havířov
    "mhd-havirov/streetway_12m_cng": dict(
        agency=HAVIROV, type="Streetway_12M_CNG", name=("Iveco Streetway 12M CNG", "Iveco Streetway 12M CNG"),
        copyright="Lubak91",
        vehicles=one("Streetway_12M_CNG", "Streetway 12M CNG", BUS,
                     f_(750000, 85, 80, 12, 24, 135, 2023, 8, "diesel", 243, 55, intro_month=6, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME,
                   hav_rows(streetway_src, z_streetway, [L12], [[(0.10, 0.60, 0.32, 1.05)]]))],
        note="Iveco Streetway 12M CNG (bioCNG, built in Turkey), doors 2-2-2. Havířov MHD\n"
             "(Transdev Slezsko): 40-1325 to 40-1341, 17 cars (6/2023 - 12/2024), bought\n"
             "for the 2024-2033 city contract. Blue city scheme from new; " + HAV_DECALS + ";\n"
             "white LED displays (photos zdopravy.cz, seznam-autobusu). The big white\n"
             "Transdev figure on the rear corners is left out (only noise at 1x). CNG:\n"
             "engine_type diesel, no smoke.",
        sprite="Lubak91's Streetway body (the DPMP demonstrator sheet, its swoosh painted\n"
               "out), repainted blue by odis_town.repaint with the CNG fairing added over\n"
               "the middle of the roof."),
    "mhd-havirov/urbanway_12m_cng": dict(
        agency=HAVIROV, type="Urbanway_12M_CNG", name=("Iveco Urbanway 12M CNG", "Iveco Urbanway 12M CNG"),
        copyright="Lubak91",
        vehicles=one("Urbanway_12M_CNG", "Urbanway 12M CNG", BUS,
                     f_(800000, 95, 80, 12, 24, 135, 2015, 8, "diesel", 213, 56, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, hav_rows(UW_SRC, z_white_green, [L12]))],
        note="Iveco Urbanway 12M CNG, doors 2-2-2. Havířov MHD: 18 cars, 40-1001 (2015, ex\n"
             "Iveco demonstrator) to 40-1019 (2021), incl. four ex Karviná (40-1004 - 1007,\n"
             "since 11/2023); repainted from 3ČSAD white-green into the blue city scheme\n"
             "12/2023 - 12/2025. " + HAV_DECALS[0].upper() + HAV_DECALS[1:] + ".",
        sprite="the Frýdek-Místek Urbanway 12M CNG sheet (Lubak91's body with the CNG\n"
               "fairing), repainted blue by odis_town.repaint."),
    "mhd-havirov/sor_nsg_12": dict(
        agency=HAVIROV, type="SOR_NSG_12", name=("SOR NSG 12", "SOR NSG 12"), copyright="vojtechzicha",
        vehicles=one("SOR_NSG_12", "NSG 12", BUS,
                     f_(800000, 95, 80, 12, 24, 135, 2025, 8, "diesel", 213, 53, intro_month=4, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, ns(NSG12, "hav"))],
        note="SOR NSG 12 (CNG), the 2023 SOR face, doors 2-2-2. Havířov MHD: 40-1542, 1543\n"
             "(4/2025) and 40-1544, 1545 (6/2026). Blue city scheme with the black cap\n"
             "and lamp mask, the CNG fairing in the body blue; " + HAV_DECALS + "\n"
             "(photos Transdev Slezsko, dopravacek.eu).",
        sprite=RENDER_NS),
    "mhd-havirov/scania_citywide_le_15m_cng": dict(
        agency=HAVIROV, type="Citywide_LE_15M_CNG",
        name=("Scania Citywide LE 15M CNG", "Scania Citywide LE 15M CNG"), copyright="VTPsim",
        vehicles=one("Citywide_LE_15M_CNG", "Citywide LE 15M CNG", BUS,
                     f_(900000, 120, 80, 14, 28, 160, 2017, 10, "diesel", 250, 55, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME,
                   hav_native("CZ-ODIS-ScaniaCitywideLE15M_Suburban-Green", [[13.5, 14.5, 15.5]],
                              pods=[[(0.10, 0.55, 0.30, 1.05)]]))],
        note="Scania Citywide LE 15M CNG, three axles, doors 1-2-1. Havířov MHD: 40-0001\n"
             "(2017) and 40-0002 (2019), blue since 11/2023. Length 10: the body is\n"
             "drawn 15 m long like the native Citywide 15.",
        sprite="VTPsim's ODIS Citywide LE 15M (CZ-vehicle-bus.pak, frozen in\n"
               "tools/busrender/src/odis/) ported by odis_town.port_native (lit glass,\n"
               "lane) and repainted blue, CNG fairing added."),
    "mhd-havirov/scania_citywide_lf_12m_cng": dict(
        allow=CW_ALLOW,
        agency=HAVIROV, type="Citywide_LF_12M_CNG",
        name=("Scania Citywide LF 12M CNG", "Scania Citywide LF 12M CNG"), copyright="Lubak91",
        vehicles=one("Citywide_LF_12M_CNG", "Citywide LF 12M CNG", BUS,
                     f_(800000, 95, 80, 12, 24, 135, 2017, 8, "diesel", 206, 55, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, hav_rows(CW_SRC, z_white_green, [L12]))],
        note="Scania Citywide LF 12M CNG. Havířov MHD: 40-1120 and 40-1121 (2017), blue\n"
             "since 12/2023 and 11/2024.",
        sprite="the Frýdek-Místek Citywide LF 12M CNG sheet, repainted blue by\n"
               "odis_town.repaint."),
    "mhd-havirov/sor_nsg_18": dict(
        agency=HAVIROV, type="SOR_NSG_18", name=("SOR NSG 18", "SOR NSG 18"), copyright="vojtechzicha",
        vehicles=artic("SOR_NSG_18", "NSG 18",
                       f_(580000, 90, 80, 10, 16, 80, 2022, 8, "diesel", None, None, intro_month=7, retire=2050),
                       f_(420000, 60, 80, 7, 12, 55, 2022, 6, "diesel", 265, 62, intro_month=7, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, ns(NSG18, "hav"))],
        note="SOR NSG 18 (CNG), the 2022 prototype, doors 2-2-2-2. Havířov MHD: 40-0204\n"
             "(ex SOR Libchavy, since 7/2022), blue city scheme with the black SOR mask.\n"
             "Fixed consist: front section A (8) + powered rear section B (6).",
        sprite=RENDER_NS),
    "mhd-havirov/streetway_18m_cng": dict(
        agency=HAVIROV, type="Streetway_18M_CNG", name=("Iveco Streetway 18M CNG", "Iveco Streetway 18M CNG"),
        copyright="Lubak91",
        vehicles=artic("Streetway_18M_CNG", "Streetway 18M CNG",
                       f_(520000, 90, 90, 10, 25, 128, 2022, 8, "diesel", None, None, retire=2050),
                       f_(380000, 61, 90, 8, 11, 56, 2022, 6, "diesel", 265, 62, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME,
                   hav_rows(SW18_SRC, z_pid, [[11.0, 11.5, 12.0], [7.0, 7.5, 8.0]],
                            [[(0.14, 0.90, 0.30, 1.05)], [(0.10, 0.45, 0.22, 0.90)]],
                            recol=disp(LEDW, (0xF7A21B,))))],
        note="Iveco Streetway 18M CNG, articulated, doors 2-2-2-2. Havířov MHD: 40-0305\n"
             "(2022, ex Iveco demonstrator, since 9/2023), blue. Fixed consist: front\n"
             "section A (8) + powered rear section B (6), as the DPP Streetway 18M.",
        sprite="Lubak91's Streetway 18M (the DPP sheet), repainted blue by\n"
               "odis_town.repaint with the CNG fairings added."),
    "mhd-havirov/citelis_12m_cng": dict(
        agency=HAVIROV, type="Citelis_12M_CNG", name=("Irisbus Citelis 12M CNG", "Irisbus Citelis 12M CNG"),
        copyright="VTPsim",
        vehicles=one("Citelis_12M_CNG", "Citelis 12M CNG", BUS,
                     f_(650000, 100, 80, 11, 24, 123, 2014, 8, "diesel", 213, 55, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME,
                   hav_native("CZ-ODIS-Irisbus_Citelis12-Green", [[11.0, 11.5, 12.0]], K.LEDG,
                              [[(0.12, 0.62, 0.30, 1.0)]]))],
        note="Irisbus Citelis 12M CNG. Havířov MHD: 40-1486 (2014), the last Citelis,\n"
             "blue since 12/2025, green LED displays.",
        sprite="VTPsim's ODIS Citelis 12 (CZ-vehicle-bus.pak, frozen in\n"
               "tools/busrender/src/odis/) ported by odis_town.port_native and repainted\n"
               "blue, CNG fairing added."),
    "mhd-havirov/sor_bng_10_5": dict(
        agency=HAVIROV, type="SOR_BNG_10_5", name=("SOR BNG 10,5", "SOR BNG 10,5"), copyright="vojtechzicha",
        vehicles=one("SOR_BNG_10_5", "BNG 10,5", BUS,
                     f_(560000, 80, 80, 10, 22, 114, 2016, 7, "diesel", 213, 54, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, model(HavBNG105, "havirovmodra"))],
        note="SOR BNG 10,5 (CNG), low floor. Havířov MHD: 40-2001 (2016), blue since\n"
             "7/2023, green LED displays (photo seznam-autobusu).",
        sprite=RENDER_IR.format(cls="SorCN105 (flat window line, CNG fairing)")),
    "mhd-havirov/sor_cng_10_5": dict(
        agency=HAVIROV, type="SOR_CNG_10_5", name=("SOR CNG 10,5", "SOR CNG 10,5"), copyright="vojtechzicha",
        vehicles=one("SOR_CNG_10_5", "CNG 10,5", BUS,
                     f_(560000, 78, 90, 10, 22, 114, 2015, 7, "diesel", 213, 54, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, model(HavCNG105, "havirovmodra"))],
        note="SOR CNG 10,5 (the CN 10,5 low-entry with CNG). Havířov MHD: 40-2002 (2015,\n"
             "ex ČSAD Frýdek-Místek, in Havířov since 2/2021), blue since 3/2023.",
        sprite=RENDER_IR.format(cls="SorCN105 (CNG fairing)")),
    "mhd-havirov/dekstra_lf_38_cng": dict(
        agency=HAVIROV, type="Dekstra_LF_38_CNG", name=("Dekstra LF 38 CNG", "Dekstra LF 38 CNG"),
        copyright="VTPsim",
        vehicles=one("Dekstra_LF_38_CNG", "Dekstra LF 38 CNG", MIDI,
                     f_(300000, 40, 80, 5, 18, 85, 2017, 6, "diesel", 100, 55, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, hav_rows(DEK_SRC, z_comett, [[7.0, 7.5, 8.0]]))],
        note="Dekstra LF 38 CNG (Iveco Daily 70C), 7.7 m midibus. Havířov MHD: 40-4001 to\n"
             "40-4005 (2017-2019), blue since 7-8/2023.",
        sprite="the Tábor Dekstra LF 38 CNG sheet (VTPsim's art shortened), repainted\n"
               "blue by odis_town.repaint."),
    "mhd-havirov/rosero_first_cng": dict(
        agency=HAVIROV, type="Rosero_First_CNG", name=("Rošero-P First FCLLI CNG", "Rošero-P First FCLLI CNG"),
        copyright="VTPsim",
        vehicles=one("Rosero_First_CNG", "Rošero First CNG", MIDI,
                     f_(245000, 30, 90, 5, 18, 85, 2025, 6, "diesel", 100, 55, intro_month=12, retire=2050)),
        liveries=[("havirovmodra", *HAV_NAME, hav_rows(ROS_SRC, z_comett, [[7.0, 7.5, 8.0]]))],
        note="Rošero-P First FCLLI CNG (Iveco Daily), 8 m midibus. Havířov MHD: 40-4006\n"
             "(12/2025), blue from new.",
        sprite="the Tábor Rošero First sheet (VTPsim's art shortened), repainted blue by\n"
               "odis_town.repaint."),
    # ------------------------------------------------------------ Karviná
    "mhd-karvina/sor_ns_12": dict(
        agency=KARVINA, type="SOR_NS_12", name=("SOR NS 12", "SOR NS 12"), copyright="vojtechzicha",
        vehicles=one("SOR_NS_12", "NS 12", BUS,
                     f_(700000, 100, 80, 12, 22, 140, 2023, 8, "diesel", 210, 53, intro_month=11,
                        retire=2050, smoke="Diesel_small")),
        liveries=[("karvinabilocerna", *KAR_NAME, ns(KNS12, "kar"))],
        note="SOR NS 12 diesel, the 2023 SOR face. Karviná MHD (Transdev Slezsko):\n"
             "50-1409 to 50-1414 (11/2023). The city's white-black scheme of the\n"
             "2024-2033 contract: white roof and roof edge, gloss black from the roof\n"
             "down to the arch tops (windows, pillars and panels all black), white\n"
             "skirt, white lower front with black lamp pods, white rear; the white\n"
             "\"karviná\" wordmark on the black; white LED displays (photos seznam-autobusu).",
        sprite=RENDER_NS),
    "mhd-karvina/sor_ns_12_electric": dict(
        agency=KARVINA, type="SOR_NS_12_electric", name=("SOR NS 12 electric", "SOR NS 12 electric"),
        copyright="vojtechzicha",
        vehicles=one("SOR_NS_12_electric", "NS 12 electric", EBUS,
                     f_(950000, 85, 80, 12, 20, 150, 2024, 8, "battery", 160, 53, retire=2050)),
        liveries=[("karvinabilocerna", *KAR_NAME, ns(KNS12E, "kar"))],
        note="SOR NS 12 electric, the 2023 SOR face. Karviná MHD: 50-1216 and 50-1217\n"
             "(1/2024), white-black like the diesels, white battery boxes on the roof.",
        sprite=RENDER_NS),
    "mhd-karvina/urbanway_12m_cng": dict(
        agency=KARVINA, type="Urbanway_12M_CNG", name=("Iveco Urbanway 12M CNG", "Iveco Urbanway 12M CNG"),
        copyright="Lubak91",
        vehicles=one("Urbanway_12M_CNG", "Urbanway 12M CNG", BUS,
                     f_(800000, 95, 80, 12, 24, 135, 2017, 8, "diesel", 213, 56, intro_month=12, retire=2050)),
        liveries=[("3csadbilozelena", *WG_NAME, copy_rows(UW_SRC, recols(disp(LEDW), csad_px))),
                  ("bila", *W_NAME, white_rows(UW_SRC, z_green, [L12]))],
        note="Iveco Urbanway 12M CNG. Karviná MHD: 50-1001 to 50-1005 (2017-2020) in 3ČSAD\n"
             "white-green, 50-1006 (2021) plain white with the factory black glazing\n"
             "since 7/2024; Transdev and \"karviná\" logos, white LED displays.",
        sprite="the Frýdek-Místek Urbanway 12M CNG sheet (Lubak91's body): unchanged\n"
               "except the white LED displays, and with the green turned white for 50-1006."),
    "mhd-karvina/streetway_12m_cng": dict(
        agency=KARVINA, type="Streetway_12M_CNG", name=("Iveco Streetway 12M CNG", "Iveco Streetway 12M CNG"),
        copyright="Lubak91",
        vehicles=one("Streetway_12M_CNG", "Streetway 12M CNG", BUS,
                     f_(750000, 85, 80, 12, 24, 135, 2023, 8, "diesel", 243, 55, intro_month=10, retire=2050)),
        liveries=[("bila", *W_NAME, white_rows(streetway_src, z_streetway, [L12], [[(0.10, 0.60, 0.32, 1.05)]]))],
        note="Iveco Streetway 12M CNG (bioCNG). Karviná MHD: 50-1307 (10/2023), plain white\n"
             "with the factory black glazing, Transdev and \"karviná\" logos.",
        sprite="Lubak91's Streetway body (the DPMP sheet), its swoosh painted out and\n"
               "the CNG fairing added by odis_town.repaint."),
    "mhd-karvina/scania_citywide_lf_12m_cng": dict(
        allow=CW_ALLOW,
        agency=KARVINA, type="Citywide_LF_12M_CNG",
        name=("Scania Citywide LF 12M CNG", "Scania Citywide LF 12M CNG"), copyright="Lubak91",
        vehicles=one("Citywide_LF_12M_CNG", "Citywide LF 12M CNG", BUS,
                     f_(800000, 95, 80, 12, 24, 135, 2019, 8, "diesel", 206, 55, retire=2050)),
        liveries=[("3csadbilozelena", *WG_NAME, copy_rows(CW_SRC, recols(disp(LEDW), csad_px)))],
        note="Scania Citywide LF 12M CNG. Karviná MHD: 50-1108 (2019), 3ČSAD white-green.",
        sprite="the Frýdek-Místek Citywide LF 12M CNG sheet, white LED displays."),
    # ------------------------------------------------------------ Orlová
    "mhd-orlova/urbanway_12m_cng": dict(
        agency=ORLOVA, type="Urbanway_12M_CNG", name=("Iveco Urbanway 12M CNG", "Iveco Urbanway 12M CNG"),
        copyright="Lubak91",
        vehicles=one("Urbanway_12M_CNG", "Urbanway 12M CNG", BUS,
                     f_(800000, 95, 80, 12, 24, 135, 2017, 8, "diesel", 213, 56, retire=2050)),
        liveries=[("3csadbilozelena", *WG_NAME, copy_rows(UW_SRC, recols(disp(LEDW), csad_px)))],
        note="Iveco Urbanway 12M CNG. Orlová MHD (Transdev Slezsko): 50-1091 and 50-1092\n"
             "(2017), 3ČSAD white-green with Transdev logos, white LED displays.",
        sprite="the Frýdek-Místek Urbanway 12M CNG sheet, white LED displays."),
    "mhd-orlova/sor_bn_9_5": dict(
        agency=ORLOVA, type="SOR_BN_9_5", name=("SOR BN 9,5", "SOR BN 9,5"), copyright="vojtechzicha",
        vehicles=one("SOR_BN_9_5", "BN 9,5", MIDI,
                     f_(455000, 74, 80, 8, 22, 120, 2016, 7, "diesel", 185, 53, retire=2050,
                        smoke="Diesel_small")),
        liveries=[("3csadbilozelena", *WG_NAME, model(OrlBN95, "3csadbilozelena"))],
        note="SOR BN 9,5. Orlová MHD: 434 (2016), 3ČSAD white-green (tall green skirt),\n"
             "white LED displays.",
        sprite=RENDER_IR.format(cls="SorBN95") + "\nThe common SOR base of 2026-10-24."),
    "mhd-orlova/novociti_life": dict(
        agency=ORLOVA, type="NovoCiti_Life", name=("Isuzu NovoCiti Life", "Isuzu NovoCiti Life"),
        copyright="VTPsim",
        vehicles=one("NovoCiti_Life", "NovoCiti Life", MIDI,
                     f_(450000, 60, 90, 7, 18, 100, 2020, 6, "diesel", 137, 55, retire=2050,
                        smoke="Diesel_small")),
        liveries=[("bila", *W_NAME, isuzu_rows)],
        note="Isuzu NovoCiti Life (Class I), ex demonstrator. Orlová MHD: 996 (2020), line\n"
             "505: white with the black glasshouse, a dark-blue unit on the rear roof, a\n"
             "paper board instead of an LED display.",
        sprite="the Kolín NovoCiti Life sheet (VTPsim's Urbino 8 body shortened), the\n"
               "roof unit added and the display a paper board (odis_town.isuzu_rows)."),
    "mhd-orlova/stratos_lf_38_cng": dict(
        agency=ORLOVA, type="Stratos_LF_38_CNG", name=("SKD Stratos LF 38 CNG", "SKD Stratos LF 38 CNG"),
        copyright="VTPsim",
        vehicles=one("Stratos_LF_38_CNG", "Stratos LF 38 CNG", MIDI,
                     f_(300000, 40, 80, 5, 18, 85, 2014, 6, "diesel", 100, 55, retire=2050)),
        liveries=[("3csadbilozelena", *WG_NAME, stratos_rows)],
        note="SKD Stratos LF 38 CNG (Iveco Daily). 619 / 33-4051 (2014), an Orlová depot\n"
             "bus that is the main bus of line 505 in 2026: 3ČSAD white-green, white roof\n"
             "and CNG box, the two-tone green CNG roundel over the rear, amber LED.",
        sprite="VTPsim's ODIS Stratos LF 38 (CZ-vehicle-bus.pak, frozen in\n"
               "tools/busrender/src/odis/) ported, roof white, CNG box and roundel added\n"
               "(odis_town.stratos_rows)."),
    "mhd-orlova/crossway_le_line_10_8m": dict(
        agency=ORLOVA, type="Crossway_LE_Line_10_8M",
        name=("Iveco Crossway LE LINE 10,8M", "Iveco Crossway LE LINE 10,8M"), copyright="vojtechzicha",
        vehicles=one("Crossway_LE_Line_10_8M", "Crossway LE LINE 10,8M", BUS,
                     f_(590000, 80, 100, 10, 24, 120, 2014, 7, "diesel", 210, 54, retire=2050,
                        smoke="Diesel_small")),
        liveries=[("3csadbilozelena", *WG_NAME, model(OrlCrossway108, "3csadbilozelena"))],
        note="Iveco Crossway LE LINE 10,8M (2014). 600 and 411, Orlová depot buses on lines\n"
             "501 and 505 in 2026: 3ČSAD white-green, the green sweeping up to the\n"
             "windows behind the front door, green LED displays.",
        sprite=RENDER_IR.format(cls="CrosswayLELine108")),
    "mhd-orlova/irisbus_crossway_le_12m": dict(
        agency=ORLOVA, type="Irisbus_Crossway_LE_12M",
        name=("Irisbus Crossway LE 12M", "Irisbus Crossway LE 12M"), copyright="vojtechzicha",
        vehicles=one("Irisbus_Crossway_LE_12M", "Crossway LE 12M", BUS,
                     f_(600000, 92, 100, 11, 24, 122, 2012, 8, "diesel", 243, 54, retire=2050,
                        smoke="Diesel_small")),
        liveries=[("3csadbilozelena", *WG_NAME, model(OrlIrisbus, "3csadbilozelena"))],
        note="Irisbus Crossway LE 12M (2012-2013, ex Transdev Střední Čechy). 393 and 401,\n"
             "Karviná depot reserves that work Orlová lines 501-504 in 2025-2026 (393: 501 x18\n"
             "in August 2026): 3ČSAD white-green without the kraj ring, the green rising to\n"
             "the windows behind the front door, green LED displays.",
        sprite=RENDER_IR.format(cls="IrisbusCrosswayLE")),
    "mhd-orlova/dekstra_lf_38_cng": dict(
        agency=ORLOVA, type="Dekstra_LF_38_CNG", name=("Dekstra LF 38 CNG", "Dekstra LF 38 CNG"),
        copyright="VTPsim",
        vehicles=one("Dekstra_LF_38_CNG", "Dekstra LF 38 CNG", MIDI,
                     f_(300000, 40, 80, 5, 18, 85, 2020, 6, "diesel", 100, 55, retire=2050)),
        liveries=[("3csadbilozelena", *WG_NAME, lambda: repaint(
            load_rows(DEK_SRC), z_comett, {"white": ((0xF2, 0xF2, 0xF0), (0xF6, 0xF6, 0xF4))},
            [[7.0, 7.5, 8.0]], skirt_decal(CSAD["green"], 1.0), None, None, disp(LEDW)))],
        note="Dekstra LF 38 CNG (Iveco Daily 70C14 CNG), 7.7 m midibus. 448 (2020, ex ČSAD\n"
             "Karviná), stored from mid-2025, back on lines 501 / 503 in October 2026: 3ČSAD\n"
             "white-green (the lower third green, green bumper), white LED displays.",
        sprite="the Tábor Dekstra LF 38 CNG sheet (VTPsim's art shortened), repainted by\n"
               "odis_town.repaint with the green skirt of skirt_decal."),
    # ------------------------------------------------------------ Bruntál
    "mhd-bruntal/sor_cng_12": dict(
        agency=BRUNTAL, type="SOR_CNG_12", name=("SOR CNG 12", "SOR CNG 12"), copyright="vojtechzicha",
        vehicles=one("SOR_CNG_12", "CNG 12", BUS,
                     f_(620000, 90, 90, 11, 25, 127, 2015, 8, "diesel", 213, 54, retire=2050)),
        liveries=[("bruntalbila", "Bruntál, white", "Bruntál, bílá", model(BruCNG12, "bruntalbila"))],
        note="SOR CNG 12 (2015, ex ČSAD Karviná). Bruntál MHD (Transdev Morava, lines 851,\n"
             "852): 83-1052 (9T6 8123), since 2/2021: white, the BRUNTÁL logo behind the\n"
             "front axle, the kraj ring over the rear axle in greens, white LED displays\n"
             "(photos vhdfoto, seznam-autobusu). Weekend and stand-in buses are Transdev\n"
             "Morava regional SOR CN in the regional scheme: not drawn here.",
        sprite=RENDER_IR.format(cls="SorCNG")),
    # ------------------------------------------------------------ Nový Jičín
    "mhd-novy-jicin/sor_bn_10_5": dict(
        agency=NOVYJICIN, type="SOR_BN_10_5", name=("SOR BN 10.5", "SOR BN 10,5"), copyright="vojtechzicha",
        vehicles=one("SOR_BN_10_5", "BN 10,5", BUS,
                     f_(490000, 85, 90, 9, 24, 150, 2015, 7, "diesel", 185, 53, smoke="Diesel_small")),
        liveries=[("cervenocerna", "red-black", "červeno-černá", model(NjBN105, "njcervenocerna"))],
        note="SOR BN 10,5, doors 1-2-1. ARRIVA autobusy 7577 (2TT 8558, built 2015; ex 5E6 6355\n"
             "at Čáslav for MHD Kutná Hora), reserve bus for MHD Nový Jičín (lines 601-604)\n"
             "since 7/2025, repainted red-black in 2025 (seznam-autobusu vuz/61645,\n"
             "\"2025-dosud červeno-černá\"). UNVERIFIED LAYOUT: no photo after the repaint\n"
             "exists, so the scheme is drawn as the town's EBN 9,5 red with a black window\n"
             "band and a black front mask; correct it once a photo turns up. Its Thermo King\n"
             "roof A/C (2025) is not drawn: no photo shows its shape.",
        sprite=RENDER_IR.format(cls="SorBN105") + "\nThe common SOR base of 2026-10-24; length 7 like every\n"
               "SOR of about 10.5 m."),
}


def yaml_text(f, driver="odis_town.py"):
    ag, ag_en, ag_cs = f["agency"]
    L = [f"agency: {ag}",
         f'type: "{f["type"]}"',
         "# Sprites carry their own lane placement (body footprint on the median of",
         "# native pak128.cs 12 m buses), so no extra shift.",
         "image_offset: [0, 0]",
         "# Windows light up at night only while passengers are aboard.",
         "windows_lit_when_loaded: true",
         f"copyright: {f['copyright']}",
         "",
         "display:",
         f'  agency_en: "{ag_en}"',
         f'  agency_cs: "{ag_cs}"',
         f'  family_en: "{f["name"][0]}"',
         f'  family_cs: "{f["name"][1]}"',
         ""]
    L += ["# " + l for l in f["note"].split("\n")]
    L += [("# Sprite: " if i == 0 else "# ") + l for i, l in enumerate(f["sprite"].split("\n"))]
    L += [f"# Regenerate with tools/busrender/{driver} (family.yaml: --yaml).", "", "vehicles:"]
    for i, v in enumerate(f["vehicles"]):
        if i:
            L.append("")
        L += [f'  - id: "{v["id"]}"',
              f'    display_id: "{v["display"]}"',
              f'    role_en: "{v["role"][0]}"',
              f'    role_cs: "{v["role"][1]}"',
              f'    row: {v.get("row", 0)}']
        for k in ("head", "tail"):
            if k in v:
                L.append(f"    {k}: {str(v[k]).lower()}")
        L.append("    prev: [" + ", ".join(f'"{p}"' for p in v.get("prev", [])) + "]")
        L.append("    next: [" + ", ".join(f'"{p}"' for p in v.get("next", [])) + "]")
        L.append("    fields:")
        for k, val in v["fields"].items():
            if val is not None:
                L.append(f"      {k}: {val}")
    L += ["", "liveries:"]
    for slug, en, cs, _ in f["liveries"]:
        L += [f"  - color: {slug}", f'    name_en: "{en}"', f'    name_cs: "{cs}"']
    return "\n".join(L) + "\n"


def main(argv):
    pv = None
    if "--preview" in argv:
        i = argv.index("--preview")
        pv = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
        os.makedirs(pv, exist_ok=True)
    if "--csad-static" in argv:                 # the static Frýdek-Místek 3ČSAD sheets
        argv = [a for a in argv if a != "--csad-static"]
        write_fm_csad()
        if not argv:
            return
    do_yaml = "--yaml" in argv
    argv = [a for a in argv if a != "--yaml"]
    for key, f in FAMILIES.items():
        if argv and key not in argv and key.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, "vehicle-bus", *key.split("/"))
        os.makedirs(os.path.join(d, "sprites"), exist_ok=True)
        for slug, _, _, fn in f["liveries"]:
            rows = fn()
            save_sheet(rows, os.path.join(d, "sprites", slug + ".png"), f.get("allow", ()))
            if pv:
                preview(rows, os.path.join(pv, f"{key.replace('/', '-')}-{slug}.png"))
            print(f"vehicle-bus/{key}/sprites/{slug}.png  rows={len(rows)}")
        if do_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(yaml_text(f))


if __name__ == "__main__":
    main(sys.argv[1:])
