"""Škoda RegioPanter body (TommPa9's pak128.CS / pak128_czr drawings) as a
reusable zone-map painter: every RegioPanter-bodied family (ČD 440 / 640 / 640.1
/ 640.2 / 650 / 650.2 / 690.2, JMK Moravia 530 / 550) is a livery dict painted on
the same three cars, so all schemes share one silhouette.

Car types (one Body each, same silhouette as every TommPa9 Panter sheet):
  "A"  pantograph cab car, cab at the FRONT (se view)   640 / 650 / 440 / 530 / 550 drawing
  "M"  middle car, gangways both ends                   642 / 442 / 533 / 532
  "B"  cab car without pantograph, cab at the REAR (nw)  641 / 651 / 441 / 531 / 551
All coordinates are SOURCE-sheet coordinates (what the repo PNG holds; makeobj
adds the rail image_offset [0, 4]). Sprites extracted from compiled paks
(tools/pak_extract.py) are 4 px lower; the frozen bases in src/ are shifted back.

Frozen bases (src/, drawn by TommPa9; the first ref of each car is the paint
base, the others only help the warp fits):
  czr_640.png  pak128_czr ČD 640 set (rows 640 / 642 / 641, lit glass marked)
  czr_650.png  pak128_czr ČD 650 "P2" set (rows 650 / 651)
  czr_690.png  pak128_czr ČD 690 set (rows 690 / 691)
  czr_jmk.png  pak128_czr JMK 530 and 550 cab cars
  czr_642.png  pak128_czr ČD 642 middle car
  cs_640/641/642.png  the native pak128.CS CD_640 / 641 / 642

API
  body(car)                      -> Body (cached)
  geo(car)                       -> Geo: doors / cab hood positions, u from the rear
  paint_car(car, livery)         -> uint8 [128, 1024, 3] sprite row
  sheet(cars, livery, out)       -> writes a sheet, rows in the given order
  preview(paths, out, z)
  python panter.py [A M B] [--out DIR]  -> false-colour zone maps (zpanter_<car>.png)
A livery is a dict {zone: colour | callable(ctx) | None} (see paint.py; a
callable gets ctx col, x, y, k, u, face, zone, fac and may return
(colour, "flat")), plus optional keys:
  "_roof": (skin, boxes)         roof skin / equipment-box colours (luminance kept)
  "_marks": [(u, w, k, colour)]  side marks, u from the car's REAR (0..1)
  "_end_marks": [(v, w, k, colour)]
  "_post": callable(car, body, a) -> a   final touch-ups (rarely needed)
Zones (S_* side face, k = rows below the cant stripe; E_* end faces):
  ROOF, ROOF_EDGE            roof (handled by "_roof"; ROOF_EDGE = lowest row)
  S_CANT  k0 cant-rail stripe along the side
  S_TOP   k1 top body row (1st-class stripe row)
  S_BODY  k2..5 window band        S_LINE k6 thin line under the windows
  S_GREY  k7 lower stripe          S_VAL  k8 valance / sill
  S_DOOR  door leaves (k1..8)      S_FIRST 1st-class stripe pixels (TommPa9 yellow)
  S_HOOD  light GRP cab hood seen from the side (slope over the cab window, nose)
  S_CABWIN cab side window (never lit)       S_WEDGE area under the cab window
  E_CANT/E_TOP/E_BODY/E_LINE/E_GREY/E_VAL   gangway end, same rows as the side
  E_HOOD  hood / headlight pods on the cab front     E_VISOR cap above the windscreen
  E_PANEL front panel under the windscreen           E_SKIRT lower front skirt
  E_BEAM  anti-climber                               WSCREEN windscreen (plain dark)
  E_GANG  gangway door / bellows (kept dark)          GLASS / HEAD / TAIL  lamps and glass
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from body import Body, T, hexarr, lum, SIDE_COLS, END_COLS, DIAG_COLS
from paint import paint, save_sheet, unspecial, shade, add_marks, recolor_lum
from paint import preview as _preview
import palette as P

SRC = os.path.join(HERE, "src") + os.sep

HEADLAMP = (0xFF, 0xFF, 0x53)
TAILLAMP = (0xFF, 0x21, 0x1D)
LAMP_OFF = (190, 194, 198)
CABGLASS = (40, 46, 54)

# lamp specials the TommPa9 art uses on the cab fronts
FRONT_LAMPS = {0xC2B2D2, 0xC1B1D1, 0xE4E4FF}

REFS = {
    # base first (lit glass already marked), then other liveries of the same
    # drawing for the warp fits
    "A": [(SRC + "czr_640.png", 0), (SRC + "cs_640.png", 0), (SRC + "czr_650.png", 0),
          (SRC + "czr_690.png", 0), (SRC + "czr_jmk.png", 0), (SRC + "czr_jmk.png", 1)],
    "M": [(SRC + "czr_640.png", 1), (SRC + "cs_642.png", 0), (SRC + "czr_642.png", 0)],
    "B": [(SRC + "czr_640.png", 2), (SRC + "cs_641.png", 0), (SRC + "czr_650.png", 1),
          (SRC + "czr_690.png", 1)],
}
# end-face top rows (source coords): cab faces 17 rows tall, gangway ends 9
END_TOP = {"A": {1: 97, 5: 84}, "M": {1: 97, 5: 90}, "B": {1: 91, 5: 90}}
CAB_COL = {"A": 5, "M": None, "B": 1}          # end view that shows the cab
SIDE_TOP = {3: 83, 7: 83}
SIDE_ROWS = [(0, 0, "S_CANT"), (1, 1, "S_TOP"), (2, 5, "S_BODY"), (6, 6, "S_LINE"), (7, 7, "S_GREY"),
             (8, 8, "S_VAL")]
GANG_ROWS = [(0, 0, "E_CANT"), (1, 1, "E_TOP"), (2, 5, "E_BODY"), (6, 6, "E_LINE"), (7, 7, "E_GREY"),
             (8, 8, "E_VAL")]
CAB_ROWS = [(0, 4, "E_VISOR"), (5, 8, "E_WIN"), (9, 11, "E_PANEL"), (12, 15, "E_SKIRT"), (16, 16, "E_BEAM")]
EXTRA = ["S_HOOD", "S_CABWIN", "S_WEDGE", "S_FIRST", "E_HOOD", "E_GANG", "WSCREEN", "E_CAM"]


def _chroma(b):
    return b.max(axis=-1) - b.min(axis=-1)


def _navy(b):
    return (b[..., 2] > b[..., 0] + 25) & (lum(b.astype(float)) < 45)


def _blue(b):
    return (b[..., 2] > b[..., 0] + 60) & (lum(b.astype(float)) >= 45)


def _light(b):
    return (lum(b.astype(float)) > 135) & (_chroma(b) < 40) & ~_blue(b)


def _yellow(b):
    return (b[..., 0] > 180) & (b[..., 1] > 130) & (b[..., 2] < 90)


class PanterBody(Body):
    """Row rules for the side / gangway ends, colour-class rules for the cab."""

    def build(self):
        super().build()
        # lamps in every view (the warp only carries the pure views' ones)
        v = hexarr(self.base)
        body = self.lab != self.Z["T"]
        self.lab[body & np.isin(v, list(FRONT_LAMPS))] = self.Z["HEAD"]
        self.lab[body & (v == 0xFF211D)] = self.Z["TAIL"]

    def pure(self, col, top, rows, face):
        lab, K, U = super().pure(col, top, rows, face)
        Z = self.Z
        b = self.base[:, col * 128:(col + 1) * 128].astype(int)
        v = hexarr(b)
        body = lab != Z["T"]
        car = self.cfg["car"]
        lamps = np.isin(v, list(FRONT_LAMPS)) & body
        lab[lamps] = Z["HEAD"]
        if face == "S":
            # cab end of this side view: 640 (A) front, 641 (B) rear
            cab_right = (car == "A") == (col == 3)
            xs = np.where(body.any(axis=0))[0]
            x0, x1 = xs.min(), xs.max()
            dist = (x1 - np.arange(128)) if cab_right else (np.arange(128) - x0)
            if car in ("A", "B"):
                near = (dist <= 12)[None, :] & body & (K >= -1) & (K <= 8)
                hood = near & _light(b) & ~((K == 7) & (dist[None, :] > 3))
                lab[hood] = Z["S_HOOD"]
                lab[near & np.isin(v, [0x6B6B6B, 0x6C6C6C])] = Z["S_CABWIN"]
                wedge = near & _navy(b) & (K >= 1) & (K <= 5) & (dist[None, :] <= 7)
                lab[wedge] = Z["S_WEDGE"]
            lab[body & _yellow(b) & (K >= 0) & (K <= 2)] = Z["S_FIRST"]
            lab[lamps] = Z["HEAD"]
            lab[body & (v == 0xFF211D)] = Z["TAIL"]
        else:
            if col == CAB_COL[car]:
                faceb = body & (K >= 0)
                lab[faceb & _light(b)] = Z["E_HOOD"]
                lab[faceb & np.isin(v, [0x6B6B6B, 0x6C6C6C])] = Z["WSCREEN"]
                lab[faceb & (K <= 4) & (v == 0x4D4D4D)] = Z["E_CAM"]
                xc = np.where(body.any(0))[0].mean()
                lab[faceb & (K >= 12) & (K <= 14) & (lum(b.astype(float)) < 90) &
                    (np.abs(np.arange(128)[None, :] - xc) < 2.6)] = Z["E_GANG"]
                lab[faceb & _yellow(b)] = Z["E_BEAM"]
                lab[lamps] = Z["HEAD"]
                lab[body & (v == 0xFF211D)] = Z["TAIL"]
            else:
                # gangway: black frame + bellows stay dark
                g = body & (K >= 1) & (K <= 7) & (lum(b.astype(float)) < 140) & ~_blue(b) & ~_navy(b)
                lab[g] = Z["E_GANG"]
        return lab, K, U


_bodies = {}


def body(car):
    if car not in _bodies:
        cab = CAB_COL[car]
        end_rows = {c: (CAB_ROWS if c == cab else GANG_ROWS) for c in END_COLS}
        cfg = dict(name="panter" + car, car=car, refs=REFS[car], base=0,
                   side_top=SIDE_TOP, end_top=END_TOP[car],
                   side_rows=SIDE_ROWS, end_rows=end_rows,
                   doors=_doors, door_rows=(1, 8), extra_zones=EXTRA,
                   diag_glass=lambda px: max(px) < 90 and max(px) - min(px) < 30)
        _bodies[car] = PanterBody(cfg)
    return _bodies[car]


def _doors(body, col, top):
    """Door x-ranges: navy columns in the body band (k 2..4) away from the cab."""
    t = body.base[:, col * 128:(col + 1) * 128].astype(int)
    m = _navy(t[top + 2:top + 4]).all(axis=0)
    xs = [x for x in range(128) if m[x]]
    runs, cur = [], []
    for x in xs:
        if cur and x != cur[-1] + 1:
            runs.append(cur); cur = []
        cur.append(x)
    if cur:
        runs.append(cur)
    return [(r[0], r[-1]) for r in runs if len(r) >= 3]


ZPAL = {"T": (231, 255, 255), "FIX": (90, 90, 40), "GLASS": (0, 0, 0), "HEAD": (255, 255, 0), "TAIL": (255, 0, 0),
        "ROOF": (150, 150, 150), "ROOF_EDGE": (100, 100, 100), "S_CANT": (255, 255, 255), "S_TOP": (0, 255, 255),
        "S_BODY": (120, 180, 255), "S_LINE": (0, 0, 160), "S_GREY": (200, 200, 200), "S_VAL": (0, 120, 120),
        "S_DOOR": (220, 0, 0), "S_FIRST": (255, 200, 0), "S_HOOD": (255, 150, 200), "S_CABWIN": (255, 120, 0),
        "S_WEDGE": (140, 0, 200), "E_CANT": (255, 255, 255), "E_TOP": (0, 255, 255), "E_BODY": (120, 180, 255),
        "E_LINE": (0, 0, 160), "E_GREY": (200, 200, 200), "E_VAL": (0, 120, 120), "E_HOOD": (255, 150, 200),
        "E_VISOR": (140, 80, 20), "E_PANEL": (0, 200, 0), "E_SKIRT": (0, 90, 0), "E_BEAM": (255, 200, 0),
        "WSCREEN": (255, 120, 0), "E_GANG": (60, 20, 60), "E_CAM": (255, 0, 255), "E_WIN": (255, 180, 120)}


def falsecolor(car, out):
    b = body(car)
    fc = np.zeros((128, 1024, 3), np.uint8)
    for n, i in b.Z.items():
        fc[b.lab == i] = ZPAL.get(n, (255, 0, 255))
    pal = ZPAL
    tmp = out + ".sheet.png"
    Image.fromarray(np.concatenate([b.base.astype(np.uint8), fc], 0)).save(tmp)
    preview([tmp], out, 5)
    os.remove(tmp)
    return {n: b.door_ranges.get(n) for n in (3, 7)}, pal


# ---------------------------------------------------------------- painting
ROOF_BOX = {0x787878: 1.0, 0x333333: 0.44, 0x373737: 0.47, 0x3B3B3B: 0.5, 0x414141: 0.55,
            0x454545: 0.58, 0x464646: 0.59, 0x313131: 0.42}       # box tops / walls
ROOF_SKIN = {0x515151: 1.0, 0x4E4E4E: 0.96, 0x4A4A4A: 0.91, 0x525252: 1.0, 0x5A5A5A: 1.1}
ROOF_PANEL = {0x109AFA}                                              # cab front panel edge


class Geo:
    """Per-car geometry helpers for livery callables.
      ur[y, x]   u along the car from its REAR end (0) to its front (1),
                 every side / roof pixel of every view (-1 elsewhere)
      doors      [(u0, u1), ...] door leaves, u from the rear
      cab        "front" (A), "rear" (B) or None (M)
      hood_u     u (from the rear) where the cab hood starts at window height
      hood_top_u same at the cant rail (the hood slopes back over the cab window)
      k, face, zone(y, x)"""

    def __init__(self, car):
        import warp
        b = body(car)
        self.car, self.b = car, b
        self.cab = {"A": "front", "B": "rear"}.get(car)
        ur = b.U.copy()
        for c in range(8):
            src = c if c in (3, 7) else warp.SIDE_SRC.get(c, c)
            if src == 7:
                sl = slice(c * 128, (c + 1) * 128)
                f = np.isin(b.face[:, sl], ["S", "R"])
                ur[:, sl][f] = 1 - b.U[:, sl][f]
        self.ur = ur
        # doors / hood from the pure ne view (front on the right)
        sl = slice(3 * 128, 4 * 128)
        body_m = b.lab[:, sl] != b.Z["T"]
        xs = np.where(body_m.any(axis=0))[0]
        x0, x1 = xs.min(), xs.max()
        self.doors = [((a - x0) / (x1 - x0), (e - x0) / (x1 - x0)) for a, e in b.door_ranges[3]]
        self.hood_u = self.hood_top_u = None
        for k, attr in ((3, "hood_u"), (0, "hood_top_u")):
            hood = (b.lab[:, sl] == b.Z["S_HOOD"]) & (b.K[:, sl] == k)
            hx = np.where(hood.any(axis=0))[0]
            if self.cab and len(hx):
                setattr(self, attr, ((hx.min() - x0) if self.cab == "front" else (hx.max() - x0)) / (x1 - x0))
        self.px = 1.0 / (x1 - x0)          # one pure-side pixel in u

    def at(self, ctx):
        return self.ur[ctx["y"], ctx["col"] * 128 + ctx["x"]]


_geo = {}


def geo(car):
    if car not in _geo:
        _geo[car] = Geo(car)
    return _geo[car]


def paint_car(car, livery):
    """One sprite row of car type "A" / "M" / "B" in a livery dict. Callables
    get ctx + ctx["ur"] (u from the rear) and ctx["geo"]."""
    b = body(car)
    g = geo(car)
    spec = {}
    for k, v in livery.items():
        if k.startswith("_"):
            continue
        if callable(v):
            spec[k] = (lambda f: lambda ctx: f(dict(ctx, ur=g.at(ctx), geo=g)))(v)
        else:
            spec[k] = v
    a = paint(b, spec)
    af = a.astype(float)
    v = hexarr(b.base)
    L = lum(b.base.astype(float))
    roof = b.lab == b.Z["ROOF"]
    if "_roof" in livery:
        skin_c, box_c = livery["_roof"][:2]
        for code, f in ROOF_BOX.items():
            m = roof & (v == code)
            af[m] = np.clip(np.array(box_c, float) * f, 0, 255)
        for code, f in ROOF_SKIN.items():
            m = roof & (v == code)
            af[m] = np.clip(np.array(skin_c, float) * f, 0, 255)
    if "E_PANEL" in livery and not callable(livery["E_PANEL"]):
        m = roof & np.isin(v, list(ROOF_PANEL))
        af[m] = livery["E_PANEL"]
    # lamps: headlights on the front cab, the rear cab shows its tail lights
    head = b.lab == b.Z["HEAD"]
    af[head] = HEADLAMP if car == "A" else livery.get("_lamp_off", LAMP_OFF)
    af[b.lab == b.Z["TAIL"]] = TAILLAMP if car == "B" else livery.get("_lamp_off", LAMP_OFF)
    a = unspecial(np.rint(af).astype(np.uint8))
    # the two lamp colours must stay exact specials
    a[head & (car == "A")] = HEADLAMP
    a[(b.lab == b.Z["TAIL"]) & (car == "B")] = TAILLAMP
    if livery.get("_marks") or livery.get("_end_marks"):
        a = add_marks(b, a, side=livery.get("_marks", ()), end=livery.get("_end_marks", ()))
    if "_post" in livery:
        a = livery["_post"](car, b, a)
    return a


def sheet(cars, livery, out):
    """Write a sheet with one row per car type (e.g. "AMB" for a 3-car unit)."""
    rows = [paint_car(c, livery) for c in cars]
    return save_sheet(rows, out)


def preview(paths, out, z=3):
    return _preview(paths, out, z)


if __name__ == "__main__":
    args = sys.argv[1:]
    out_dir = "."
    if "--out" in args:
        i = args.index("--out")
        out_dir = args[i + 1]
        del args[i:i + 2]
    os.makedirs(out_dir, exist_ok=True)
    for car in args or "AMB":
        d, pal = falsecolor(car, os.path.join(out_dir, f"zpanter_{car}.png"))
        print(car, d, {c: (round(f["side"][3], 1), round(f["end"][3], 1)) for c, f in body(car).fits.items()})
