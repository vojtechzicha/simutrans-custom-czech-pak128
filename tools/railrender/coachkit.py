"""coachkit: generic builder for loco-hauled passenger coaches (rendered sprites).

Generalises ric.py (the Leo Express ex-DB IC coaches) into a data-driven kit:
a coach TYPE is a table of metre positions read off the vagonWEB side drawings
(10 px = 1 m, both axes; rail head = bottom of the wheels), a LIVERY is a colour
table plus horizontal bands, stripes, coloured doors/ends and logo/lettering
blocks. Both sides are drawn correctly, the other side mirrored or given
separately, exactly as the two drawings show.

Stable API (other model scripts import this module; do not change signatures)
----------------------------------------------------------------------------
    import coachkit as CK

    bmz = CK.Coach("Bmz", length_m=26.4,
                   windows=[CK.Win(1.8, 2.7, "f")] + CK.row_of(3.1, 1.3, 1.9, 11),
                   doors=[CK.Door(0.5, 1.5), CK.Door(24.9, 25.9)],
                   bogies=(3.55, 22.65))
    liv = CK.Livery("obb", body=0xCDCFD2, roof=0xC4282E, end_door=0xB0242A,
                    bands=[CK.Band(1.90, 3.40, 0xA2A6AA),            # window band
                           CK.Band(0.85, None, 0xC81E28, px=1),      # 1-px sill stripe
                           CK.Band.line(3.40, 0xE6E8EA)],           # 1-px line under roof
                    marks=[CK.Mark(11.7, 12.7, 1.42, 1.80, 0xD8232C)])   # logo
    rows = CK.render_rows([(bmz, liv), (bmz, liv, {"flip": True})])
    CK.save_sheet(rows, "sprites/obbsedocervena.png")   # 1024 x 128*n, special-colour check
    CK.preview(rows, "prev.png", labels=["Bmz", "Bmz turned"])
    bmz.length_cu        # -> 13: the integer `length` for family.yaml

Units and conventions
- All positions are METRES as read off the vagonWEB drawing of a side, x from
  the drawing's LEFT edge (buffer face = 0), heights z above the rail head.
  The drawing is 10 px per metre: x_m = px / 10, z_m = (rail_y - py) / 10.
- Side "a" = the vagonWEB "-a" drawing, side "b" = the "-b" drawing (the true
  other side, drawn as seen: what is on the left in "a" is on the right in
  "b"). If a type gives no `windows_b` / `doors_b`, side b is side a mirrored
  (same physical positions on both sides, the usual case).
- Model placement: side a is the vehicle's left-hand side (-v face), seen with
  the vehicle FRONT on the screen-left; side b is the right-hand side (+v),
  front on the screen-right. `flip=True` turns the coach (b on the left).
  Lettering/logos (Mark) always read left to right as seen, on both sides.
- Length: length_m over buffers is drawn at the pak128.cs rail scale
  26.4 m = 13 carunits (M = 2.0308 m/cu) and rounded to an integer `length_cu`
  (24.5 m -> 12, 26.4 m -> 13, 27.5 m -> 14). The drawing is stretched by
  length_cu * M / length_m so that the body fills exactly `length_cu`; the
  coach is anchored at its front like every Simutrans vehicle (railkit.ANCHOR),
  so the next vehicle starts `length_cu` behind it and joints close in every
  view (CLAUDE.md "Section placement").
- Heights: 1 model px = 0.375 m; the side wall ends at 3.75 m (z 10, calibrated
  to native CD_Bmz241) and the roof cap reaches height_m (4.05 m -> z 10.8).
  Width scales the calibrated half width R.W_STD (0.92 cu for 2.825 m).

Classes
- Win(x0, x1, kind="w", z0=None, z1=None)
    kind "w" passenger glass (lit at night: GLASS + GLASS_HI top row),
         "p" large panorama glass (lit, Coach.pano_z),
         "h" small high lit window (Coach.high_z, e.g. corridor-end lights),
         "f" frosted WC / washroom glass (Livery.frost, never lit, Coach.frost_z),
         "x" dark unlit glass (staff / luggage / service rooms, Livery.dark_glass).
    z0/z1 override the kind's default height range (metres).
- Door(x0, x1, kind="single", style="swing", window=True)
    kind "single" one leaf, "double" two leaves (split line + two windows),
    style "swing" (hinged UIC door: leaf with a tall window), "plug" (flush
    sliding-plug door: same, the window a bit lower and wider), "fold"
    (folding/fold-away door: two narrow windows). The leaf reaches from
    Coach.door_z[0] (the step, below the body sill) to Coach.door_z[1]; it gets
    Livery.door (default body colour) with a Livery.door_frame outline that is
    exactly 1 px wide in every view; a door narrower than 3 px in a view is
    drawn 3 px wide about its centre (frame + leaf/window + frame), so it
    always reads as a framed door reaching below the sill (a real 0.9-1.0 m
    door is 2-3 px at this scale). Double doors get the centre split when
    they are >= 5 px wide. Bands with over_doors=True cross the leaves.
- Coach(name, length_m=26.4, windows=(), doors=(), windows_b=None,
        doors_b=None, bogies=(3.55, 22.65), width_m=2.825, height_m=4.05,
        sill_m=0.85, eaves_m=3.40, win_z=(1.95, 3.05), pano_z=(1.75, 3.10),
        high_z=(2.45, 3.05), frost_z=(2.20, 3.05), door_z=(0.45, 3.10),
        door_win_z=(1.95, 2.95), roof="plain", roof_items=(), gangway="uic",
        marks=(), length_cu=None, bogie_wheelbase_m=2.5, underframe=True,
        roof_end_m=0.10)
    roof_end_m: how far the roof cap stops short of the body ends (rounded
    roof ends, e.g. 0.9 on ex-DB Bvcmz/Bvcmbz couchettes).
    roof: "plain" | "ac" (Coach.ac_units(...) boxes are added) | "sleeper"
    (low full-length roof duct + tank covers) - or give roof_items yourself.
    roof_items: RoofBox(x0, x1, half_width_m, height_m, color_key="roof_eq")
    (x in side-a drawing metres).  gangway: "uic" rubber bellows + end door,
    "none" (closed ends).  marks: type-specific Mark list (e.g. pictograms).
- Band(z0, z1, color, x0=None, x1=None, side="both", over_doors=True,
       px=None, below=0)   /   Band.line(z_top, color, px=1, below=0, ...)
    horizontal band / stripe on the body sides (metres), painted in list order
    over Livery.body, under windows and marks. x0/x1 limit it along the car in
    side-a drawing coordinates (mirrored to side b like windows, unless
    side="a"/"b" gives it per side in that side's own drawing coordinates).
    over_doors=False leaves door leaves in Livery.door.
    px=N (or Band.line) = exactly N pixel rows in every view, hanging from
    z1 (z1=None: standing on z0); below=k shifts it k rows down (up), so
    Band.line(1.98, red) + Band.line(1.98, grey, below=1) is a red line with
    a grey line right under it, one pixel each, in all 8 views. Use it for
    signature stripes thinner than ~0.4 m (they would flicker otherwise).
- Mark(x0, x1, z0, z1, color, side="both", kind="solid", pitch=0.45, duty=0.6,
       bitmap=None, legend=None, over_doors=False, fn=None)
    a logo / lettering block. kind "solid", "text" (strokes pitch/duty in
    reading direction: stands in for lettering at 1x), "bitmap" (rows of
    chars top to bottom, stretched over the block; legend maps char ->
    colour, "." or " " = transparent), "func" (fn(t, z) -> colour or None,
    t = metres from the block's left edge as read, z = height in metres).
    Marks win over bands but not over windows/doors. x in side-a drawing
    coordinates; with
    side="both" the block is mirrored to side b but still reads left to right.
    side="a"/"b": the block only on that side, in that side's coordinates.
- Livery(name, body, roof, **colours)  colour keys (int 0xRRGGBB, RGB tuple,
    railkit Paint or None):
      body        side base colour                     (required)
      roof        roof cap + side above eaves_m         (required)
      roof_top    top face of the roof (default roof)
      roof_side   side above Coach.eaves_m (default roof; None = body colour)
      roof_eq     roof equipment (AC boxes, ducts)
      ends        end walls (default: body); end_bands=True continues the
                  full-length bands across the end walls
      end_door, end_window   gangway end door (default: gangway colour) and
                  its window (plain, not lit)
      door        door leaves (default: body)       door_frame  door outline
      door_frame_m  outline width in metres; None (default) = exactly one
                  screen pixel in every view (crisp 1-px door outlines)
      window_frame  frame around every passenger window (default None)
      frame_m, frame_z   frame width/height in metres (default 0.10 / 0.10)
      frost, dark_glass, gangway, buffer, under (underframe), bogie,
      bogie_frame
      bands=[Band...], marks=[Mark...]
    Livery.derive(name=None, bands=None, marks=None, **changes) returns a
    modified copy (e.g. per-coach window frames or an extra 1st class line).
    Also: wheel / hub (wheel rims seen below the bogies), roof_curve (top-face
    darkening towards the eaves, default 0.20), glass_hi_m (height of the
    lighter GLASS_HI top row of each window, default 0.28).

Functions
- row_of(x0, width, pitch, n, kind="w") -> [Win]: n evenly pitched windows.
- mirror(items, length_m) -> side-b list of mirrored Win / Door.
- coach_parts(coach, livery, u0=0.0, owner="C", flip=False, marks=()) -> [Part]
  (railkit Parts, to combine with extra parts of your own, e.g. a luggage
  van's big doors; the body Part is first).
- coach_tiles(coach, livery, flip=False, marks=(), extra=None) -> 8 tiles
  (numpy 128x128x3, direction order w nw n ne e se s sw); extra(parts, u0,
  owner) may append Parts before rendering.
- render_rows(items) -> rows; item = (coach, livery) or (coach, livery, opts)
  with opts keys flip / marks / extra.
- save_sheet(rows, path), preview(rows, path, labels=None, z=4): railkit.
- px_m(coach, d) -> (metres along the side, metres of height) per screen
  pixel in view d (for your own pixel-exact features).
- python coachkit.py scan <drawing.gif> [y ...]  prints colour runs of the
  given drawing rows as metre ranges (window/door positions for the tables).

Colours: passenger glass uses the lit-at-night specials (R.GLASS 0x4D4D4D,
R.GLASS_HI 0x57656F); everything else goes through railkit.safe(), which nudges
accidental special colours off the table. save_sheet prints a WARNING if any
unintended special colour survives.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint, Part, Lit  # noqa: E402
from render import DIRS  # noqa: E402

M = 26.4 / 13.0            # metres per carunit (pak128.cs rail coach scale)
PX = 0.375                 # metres per model px (height)
ZS = R.H_SIDE              # 10.0: side wall top (3.75 m)
_BODY_END = 0.14           # cu between buffer face and body end (gangway/buffers)
# sampling pitch on a body side, per view: carunits of u per screen pixel
# column and model-z per screen row. An edge band exactly one pitch wide
# always hits exactly one pixel, whatever the sub-pixel phase: used for door
# frames ("px" widths) so every door gets a crisp 1-px outline in every view.
_S2 = 2 ** 0.5
_U_PITCH = {"w": 0.25, "e": 0.25, "n": 0.25, "s": 0.25,
            "ne": 1 / (4 * _S2), "sw": 1 / (4 * _S2), "nw": 1 / (4 * _S2), "se": 1 / (4 * _S2)}
# (nw/se show the sides edge-on; they use the ne/sw pitch)
DOOR_MIN_PX = 3            # a door is at least frame + leaf + frame pixels wide


def px_m(coach, d):
    """(metres along the drawing, metres of height) covered by one screen
    pixel on this coach's side in view d."""
    return _U_PITCH[d] * coach.scale, PX / R.KZ[d]


def zm(h):
    """height above the rail in metres -> model z (px)."""
    return h / PX


def _paint(c):
    if c is None or isinstance(c, (Paint, Lit)):
        return c
    if isinstance(c, int):
        return Paint(c)
    return Paint(tuple(c))


# ------------------------------------------------------------------ data types
class Win:
    """A window on one side: x0..x1 metres (drawing), kind w/p/h/f/x."""
    def __init__(self, x0, x1, kind="w", z0=None, z1=None):
        self.x0, self.x1, self.kind, self.z0, self.z1 = float(x0), float(x1), kind, z0, z1

    def mirrored(self, L):
        return Win(L - self.x1, L - self.x0, self.kind, self.z0, self.z1)

    def __repr__(self):
        return "Win(%.2f, %.2f, %r)" % (self.x0, self.x1, self.kind)


class Door:
    """A bodyside door: x0..x1 metres (drawing, outer edges of the frame)."""
    def __init__(self, x0, x1, kind="single", style="swing", window=True):
        self.x0, self.x1, self.kind, self.style, self.window = float(x0), float(x1), kind, style, window

    def mirrored(self, L):
        return Door(L - self.x1, L - self.x0, self.kind, self.style, self.window)

    def __repr__(self):
        return "Door(%.2f, %.2f, %r, %r)" % (self.x0, self.x1, self.kind, self.style)


class RoofBox:
    """Roof equipment box: x0..x1 metres (side-a drawing), half width and
    height in metres above the roof top, colour = a Livery key or a colour."""
    def __init__(self, x0, x1, half_width_m=0.6, height_m=0.3, color_key="roof_eq"):
        self.x0, self.x1, self.hw, self.h, self.color_key = float(x0), float(x1), half_width_m, height_m, color_key


class Band:
    """Horizontal band / stripe on the body sides (metres).
    px=N makes it exactly N screen-pixel rows tall in EVERY view (thin
    signature lines that must never vanish or double): the rows hang down from
    z1 (or, with z1=None, stand up from z0), shifted by `below` rows."""
    def __init__(self, z0, z1, color, x0=None, x1=None, side="both", over_doors=True, px=None, below=0):
        self.z0, self.z1, self.color = z0, z1, _paint(color)
        self.x0, self.x1, self.side, self.over_doors = x0, x1, side, over_doors
        self.px, self.below = px, below

    @classmethod
    def line(cls, z_top, color, px=1, below=0, **kw):
        """a stripe exactly px pixel rows tall whose top edge is z_top metres
        (below=k: the k-th row under it, to stack lines pixel-exactly)."""
        return cls(None, z_top, color, px=px, below=below, **kw)

    def zrange(self, view=None):
        """(z0, z1) in metres as drawn in view (half-open at z0 for px bands)."""
        if self.px is None or view is None:
            if self.px is not None:      # no view: approximate with w-view rows
                pz = PX
                return self._px_range(pz)
            return self.z0, self.z1
        return self._px_range(PX / R.KZ[view])

    def _px_range(self, pz):
        if self.z1 is not None:
            top = self.z1 - self.below * pz
            return top - self.px * pz + 1e-6, top
        bot = self.z0 + self.below * pz
        return bot + 1e-6, bot + self.px * pz


class Mark:
    """Logo / lettering block (metres, drawing coordinates of its side)."""
    def __init__(self, x0, x1, z0, z1, color=None, side="both", kind="solid", pitch=0.45, duty=0.6,
                 bitmap=None, legend=None, over_doors=False, fn=None):
        self.x0, self.x1, self.z0, self.z1 = float(x0), float(x1), z0, z1
        self.color = _paint(color)
        self.side, self.kind, self.pitch, self.duty = side, kind, pitch, duty
        self.bitmap = bitmap
        self.legend = {k: _paint(v) for k, v in (legend or {}).items()}
        self.over_doors = over_doors
        self.fn = fn

    def at(self, t, z):
        """colour at reading coordinate t (metres from the block's left) and
        height z (metres), or None = transparent."""
        if self.kind == "solid":
            return self.color
        if self.kind == "text":
            k = t / self.pitch
            return self.color if (k - int(k)) < self.duty else None
        if self.kind == "func":
            c = self.fn(t, z)
            return _paint(c) if c is not None else None
        if self.kind == "bitmap":
            rows = self.bitmap
            nr = len(rows)
            nc = max(len(r) for r in rows)
            ri = int((self.z1 - z) / (self.z1 - self.z0) * nr)
            ci = int(t / (self.x1 - self.x0) * nc)
            ri = min(max(ri, 0), nr - 1)
            ci = min(max(ci, 0), nc - 1)
            ch = rows[ri][ci] if ci < len(rows[ri]) else "."
            if ch in ". ":
                return None
            return self.legend.get(ch, self.color)
        return None


class Coach:
    """A coach type: geometry + window/door layout in drawing metres."""
    def __init__(self, name, length_m=26.4, windows=(), doors=(), windows_b=None, doors_b=None,
                 bogies=(3.55, 22.65), width_m=2.825, height_m=4.05, sill_m=0.85, eaves_m=3.40,
                 win_z=(1.95, 3.05), pano_z=(1.75, 3.10), high_z=(2.45, 3.05), frost_z=(2.20, 3.05),
                 door_z=(0.45, 3.10), door_win_z=(1.95, 2.95), roof="plain", roof_items=(),
                 gangway="uic", marks=(), length_cu=None, bogie_wheelbase_m=2.5, underframe=True,
                 roof_end_m=0.10):
        self.name = name
        self.length_m = float(length_m)
        self.length_cu = int(length_cu if length_cu is not None else max(1, round(length_m / M)))
        self.windows = list(windows)
        self.doors = list(doors)
        self.windows_b = list(windows_b) if windows_b is not None else [w.mirrored(self.length_m) for w in self.windows]
        self.doors_b = list(doors_b) if doors_b is not None else [d.mirrored(self.length_m) for d in self.doors]
        self.bogies = tuple(bogies)
        self.width_m, self.height_m = width_m, height_m
        self.sill_m, self.eaves_m = sill_m, eaves_m
        self.win_z, self.pano_z, self.high_z, self.frost_z = win_z, pano_z, high_z, frost_z
        self.door_z, self.door_win_z = door_z, door_win_z
        self.roof = roof
        self.roof_items = list(roof_items)
        self.gangway = gangway
        self.marks = list(marks)
        self.bogie_wheelbase_m = bogie_wheelbase_m
        self.underframe = underframe
        self.roof_end_m = roof_end_m

    # --- presets for roof equipment
    def ac_units(self, at=(4.5, 21.9), length_m=2.6, half_width_m=0.62, height_m=0.30):
        """Add air-conditioning boxes centred at the given drawing metres."""
        for c in at:
            self.roof_items.append(RoofBox(c - length_m / 2, c + length_m / 2, half_width_m, height_m))
        return self

    @property
    def scale(self):
        """drawing metres per model carunit for this coach."""
        return self.length_m / self.length_cu

    def half_width(self):
        return R.W_STD * self.width_m / 2.825


class Livery:
    """Colour table + bands + marks. Colours: int 0xRRGGBB, RGB tuple, Paint."""
    DEFAULTS = dict(
        roof_top=None, roof_side="roof", roof_eq=0x6E7276, roof_curve=0.20, ends=None, end_door=None,
        end_window=0x7A8894, end_bands=False,
        door=None, door_frame=0x3C3F42, door_frame_m=None, window_frame=None, frame_m=0.10, frame_z=0.10,
        frost=0xC4CDD3, dark_glass=0x2A343D, gangway=0x2B2D2F, buffer=0x1E2022,
        under=0x35383B, bogie=0x24262A, bogie_frame=0x3C3F42, wheel=0xB4B8BA, hub=0x6E7276,
        glass_hi_m=0.28)

    def __init__(self, name, body, roof, bands=(), marks=(), **kw):
        unknown = set(kw) - set(self.DEFAULTS)
        if unknown:
            raise TypeError("unknown livery keys: %s" % sorted(unknown))
        self.name = name
        self._raw = dict(self.DEFAULTS)
        self._raw.update(kw)
        self._raw["body"] = body
        self._raw["roof"] = roof
        self.bands = list(bands)
        self.marks = list(marks)
        self._resolve()

    def _resolve(self):
        r = self._raw
        self.body = _paint(r["body"])
        rt = r["roof_top"]
        roof = r["roof"]
        if isinstance(roof, Paint):
            self.roof = roof if rt is None else Paint(roof.base, top=rt)
        else:
            self.roof = Paint(roof, top=rt if rt is not None else roof)
        rs = r["roof_side"]
        self.roof_side = self.roof if rs == "roof" else _paint(rs)
        self.roof_eq = _paint(r["roof_eq"])
        self.ends = _paint(r["ends"]) or self.body
        self.end_door = _paint(r["end_door"])
        self.end_window = _paint(r["end_window"])
        self.end_bands = r["end_bands"]
        self.roof_curve = r["roof_curve"]
        self.wheel = _paint(r["wheel"])
        self.hub = _paint(r["hub"])
        self.door = _paint(r["door"]) or self.body
        self.door_frame = _paint(r["door_frame"])
        self.window_frame = _paint(r["window_frame"])
        self.frost = _paint(r["frost"])
        self.dark_glass = _paint(r["dark_glass"])
        self.gangway = _paint(r["gangway"])
        self.buffer = _paint(r["buffer"])
        self.under = _paint(r["under"])
        self.bogie = _paint(r["bogie"])
        self.bogie_frame = _paint(r["bogie_frame"])
        self.door_frame_m = r["door_frame_m"]
        self.frame_m, self.frame_z = r["frame_m"], r["frame_z"]
        self.glass_hi_m = r["glass_hi_m"]

    def derive(self, name=None, bands=None, marks=None, **changes):
        raw = dict(self._raw)
        raw.update(changes)
        body, roof = raw.pop("body"), raw.pop("roof")
        return Livery(name or self.name, body, roof,
                      bands=self.bands if bands is None else bands,
                      marks=self.marks if marks is None else marks, **raw)

    def color(self, key):
        return getattr(self, key) if isinstance(key, str) else _paint(key)


def row_of(x0, width, pitch, n, kind="w"):
    """n windows of `width` metres, the first starting at x0, every `pitch` m."""
    return [Win(x0 + i * pitch, x0 + i * pitch + width, kind) for i in range(n)]


def mirror(items, length_m=26.4):
    return [it.mirrored(length_m) for it in items]


# ------------------------------------------------------------------ painting
def _in(a, x, b):
    return a <= x <= b


def _side_marks(marks, side, L):
    """marks placed on `side` in that side's drawing coordinates."""
    out = []
    for mk in marks:
        if mk.side == side:
            out.append((mk.x0, mk.x1, mk))
        elif mk.side == "both":
            if side == "a":
                out.append((mk.x0, mk.x1, mk))
            else:
                out.append((L - mk.x1, L - mk.x0, mk))
    return out


def _side_bands(bands, side, L):
    out = []
    for b in bands:
        if b.side not in ("both", side):
            continue
        if b.x0 is None:
            out.append((None, None, b))
        elif b.side == "both" and side == "b":
            out.append((L - b.x1, L - b.x0, b))
        else:
            out.append((b.x0, b.x1, b))
    return out


class _SidePainter:
    """Colour of a point (x metres as seen, z metres) on one side."""
    def __init__(self, coach, liv, side, marks):
        self.c, self.l = coach, liv
        L = coach.length_m
        self.wins = coach.windows if side == "a" else coach.windows_b
        self.doors = coach.doors if side == "a" else coach.doors_b
        self.marks = _side_marks(list(coach.marks) + list(liv.marks) + list(marks), side, L)
        self.bands = _side_bands(liv.bands, side, L)

    def _glass(self, z, z1):
        return R.GLASS_HI if z > z1 - self.l.glass_hi_m else R.GLASS

    def _window(self, w, x, z):
        c, l = self.c, self.l
        zr = {"w": c.win_z, "p": c.pano_z, "h": c.high_z, "f": c.frost_z, "x": c.win_z}.get(w.kind, c.win_z)
        z0 = w.z0 if w.z0 is not None else zr[0]
        z1 = w.z1 if w.z1 is not None else zr[1]
        if not (_in(w.x0, x, w.x1) and _in(z0, z, z1)):
            return None
        if w.kind == "f":
            return l.frost
        if w.kind == "x":
            return l.dark_glass
        if l.window_frame is not None:
            if (x - w.x0 < l.frame_m or w.x1 - x < l.frame_m or z - z0 < l.frame_z or z1 - z < l.frame_z):
                return l.window_frame
            return self._glass(z, z1 - l.frame_z)
        return self._glass(z, z1)

    def _door_span(self, d, view):
        """door extent (x0, x1, frame width, frame height) as drawn in view:
        with pixel-exact frames (door_frame_m None) a narrow door is widened
        about its centre to DOOR_MIN_PX pixels, so frame + leaf + frame always
        show (a real 0.9-1.0 m door is 2-3 px wide at pak128 scale)."""
        l = self.l
        x0, x1 = d.x0, d.x1
        if l.door_frame_m is not None:
            return x0, x1, l.door_frame_m, l.door_frame_m
        if view is None:
            return x0, x1, 0.2, 0.2
        fm, fz = px_m(self.c, view)
        minw = DOOR_MIN_PX * fm + 1e-6
        if x1 - x0 < minw:
            cx = (x0 + x1) / 2
            x0, x1 = cx - minw / 2, cx + minw / 2
        return x0, x1, fm, fz

    def _door(self, d, x, z, view=None):
        c, l = self.c, self.l
        x0, x1, fm, fz = self._door_span(d, view)
        if not (_in(x0, x, x1) and _in(c.door_z[0], z, c.door_z[1])):
            return None
        if l.door_frame is not None:
            if x - x0 < fm or x1 - x < fm or c.door_z[1] - z < fz:
                return l.door_frame
            if d.kind == "double" and x1 - x0 >= 5 * fm and abs(x - (x0 + x1) / 2) < fm * 0.5:
                return l.door_frame
        if d.window:
            wz0, wz1 = c.door_win_z
            if d.style == "plug":
                wz0, wz1 = wz0 - 0.1, wz1 - 0.05
            mx = max(0.22 if d.kind == "single" else 0.14, fm if l.door_frame is not None else 0.0)
            if _in(wz0, z, wz1):
                if (d.kind == "double" or d.style == "fold") and x1 - x0 >= 5 * fm:
                    mid = (x0 + x1) / 2
                    if (_in(x0 + mx, x, mid - fm * 0.5) or _in(mid + fm * 0.5, x, x1 - mx)):
                        return self._glass(z, wz1)
                elif _in(x0 + mx, x, x1 - mx):
                    return self._glass(z, wz1)
        for (a, b, band) in reversed(self.bands):
            bz0, bz1 = band.zrange(view)
            if band.over_doors and _in(bz0, z, bz1) and (a is None or _in(a, x, b)):
                return band.color
        for (a, b, mk) in self.marks:
            if mk.over_doors and _in(a, x, b) and _in(mk.z0, z, mk.z1):
                col = mk.at(x - a, z)
                if col is not None:
                    return col
        return l.door

    def color(self, x, z, view=None):
        """colour at drawing metre x (as seen) and height z metres; view = the
        direction being rendered (enables pixel-exact door outlines)."""
        c, l = self.c, self.l
        for d in self.doors:
            col = self._door(d, x, z, view)
            if col is not None:
                return col
        if z < c.sill_m:
            return l.under                       # door-step boxes beside a door
        for w in self.wins:
            col = self._window(w, x, z)
            if col is not None:
                return col
        for (a, b, mk) in self.marks:
            if _in(a, x, b) and _in(mk.z0, z, mk.z1):
                col = mk.at(x - a, z)
                if col is not None:
                    return col
        if z >= c.eaves_m and l.roof_side is not None:
            return l.roof_side
        for (a, b, band) in reversed(self.bands):
            bz0, bz1 = band.zrange(view)
            if _in(bz0, z, bz1) and (a is None or _in(a, x, b)):
                return band.color
        return l.body


# ------------------------------------------------------------------ geometry
def coach_parts(coach, liv, u0=0.0, owner="C", flip=False, marks=()):
    """railkit Parts of one coach whose front buffer face is at consist-u u0."""
    L = coach.length_cu
    s = coach.scale
    W = coach.half_width()
    zr = zm(coach.height_m)
    zs = min(ZS, zr - 0.5)
    zsill = zm(coach.sill_m)
    pa = _SidePainter(coach, liv, "a", marks)
    pb = _SidePainter(coach, liv, "b", marks)
    left, right = (pb, pa) if flip else (pa, pb)   # painters of the -v / +v faces

    def x_of(face, u):
        uu = u - u0
        return uu * s if face == "-v" else (L - uu) * s

    def roof_mat(f, u, v, z, d):
        if f == "+z":
            # curved roof: the top face darkens towards the eaves
            k = 1.0 - liv.roof_curve * min(1.0, abs(v) / W) ** 2
            return R.safe(tuple(c * k for c in liv.roof.topc))
        return liv.roof

    def end_mat(f, u, v, z, d):
        if coach.gangway != "none" and abs(v) < 0.42 and z < zs - 0.6:
            return liv.gangway
        if liv.end_bands:
            zz = z * PX
            for band in reversed(liv.bands):
                bz0, bz1 = band.zrange(d)
                if band.x0 is None and bz0 <= zz <= bz1:
                    return band.color
        return liv.ends

    def body_mat(f, u, v, z, d):
        if f == "+z":
            return roof_mat(f, u, v, z, d)
        if f in ("+v", "-v"):
            p = left if f == "-v" else right
            return p.color(x_of(f, u), z * PX, d)
        return end_mat(f, u, v, z, d)

    def gangway_mat(f, u, v, z, d):
        # rubber bellows frame around the end door (UIC gangway) with its window
        if f in ("-u", "+u") and abs(v) < 0.26 and zm(1.25) <= z <= zs - 1.25:
            if liv.end_window is not None and abs(v) < 0.15 and zm(2.05) <= z <= zm(2.85):
                return liv.end_window
            if liv.end_door is not None:
                return liv.end_door
        return liv.gangway

    parts = []
    ub0, ub1 = u0 + _BODY_END, u0 + L - _BODY_END
    parts.append(Part(ub0, ub1, -W, W, zsill, zs, body_mat, owner))
    # roof cap (inset like the calibrated Bmz241 fit)
    re_ = coach.roof_end_m / s
    parts.append(Part(ub0 + re_, ub1 - re_, -W + 0.2, W - 0.2, zs, zr, roof_mat, owner))
    # door steps: the door leaf continues below the sill to the step
    zstep = zm(coach.door_z[0])
    if zstep < zsill:
        for face, doors_side in (("-v", left), ("+v", right)):
            for dr in doors_side.doors:
                # wide enough for the widest view-widened door (see _door_span)
                grow = max(0.0, (DOOR_MIN_PX * 0.25 * s - (dr.x1 - dr.x0)) / 2) + 0.05
                xa, xb = dr.x0 - grow, dr.x1 + grow
                a, b = sorted((u0 + (xa / s if face == "-v" else L - xa / s),
                               u0 + (xb / s if face == "-v" else L - xb / s)))
                a, b = max(a, u0 + _BODY_END), min(b, u0 + L - _BODY_END)
                v0, v1 = (-W, -W + 0.3) if face == "-v" else (W - 0.3, W)
                p = doors_side

                def step_mat(f, u, v, z, d, p=p, face=face):
                    if f == face:
                        return p.color(x_of(face, u), z * PX, d)
                    if f == "+z":
                        return liv.door
                    return liv.door_frame or liv.door
                parts.append(Part(a, b, v0, v1, zstep, zsill, step_mat, owner))
    # gangways + buffers
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        if coach.gangway != "none":
            parts.append(Part(a, b, -0.40, 0.40, zm(1.0), zs - 0.8, gangway_mat, owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, zm(0.9), zm(1.17), lambda *a_: liv.buffer, owner))
    # underframe equipment between the bogies + bogies
    hb = coach.bogie_wheelbase_m / 2 / s + 0.1
    if coach.underframe and len(coach.bogies) >= 2:
        ua = u0 + min(coach.bogies) / s + hb + 0.15
        ub = u0 + max(coach.bogies) / s - hb - 0.15
        if ub > ua:
            parts.append(Part(ua, ub, -W + 0.25, W - 0.25, zm(0.35), zsill, lambda *a_: liv.under, owner))
    zb = min(zsill, zm(0.95))
    zw = zm(0.40)                 # wheel rims seen below the bogie frame
    rw = 0.46 / s                 # wheel radius in cu
    for bm in coach.bogies:
        bc = u0 + bm / s
        parts.append(Part(bc - hb, bc + hb, -W + 0.12, W - 0.12, 0.0, zb,
                          lambda f, u, v, z, d: liv.bogie_frame if (f in ("+v", "-v") and z > zb - 0.8) else liv.bogie,
                          owner))
        # wheelsets: light rims with a dark hub, like the native coaches
        for ax in (bc - coach.bogie_wheelbase_m / 2 / s, bc + coach.bogie_wheelbase_m / 2 / s):
            def wheel_mat(f, u, v, z, d, ax=ax):
                if f in ("+v", "-v"):
                    return liv.hub if abs(u - ax) < 0.34 * rw else liv.wheel
                return liv.bogie
            for (v0, v1) in ((-W + 0.03, -W + 0.2), (W - 0.2, W - 0.03)):
                parts.append(Part(ax - rw, ax + rw, v0, v1, 0.0, zw, wheel_mat, owner))
    # roof equipment
    items = list(coach.roof_items)
    if coach.roof == "ac" and not items:
        tmp = Coach("tmp", coach.length_m)
        tmp.ac_units(at=(4.5, coach.length_m - 4.5))
        items = tmp.roof_items
    if coach.roof == "sleeper" and not items:
        items = [RoofBox(3.0, coach.length_m - 3.0, 0.30, 0.12),
                 RoofBox(1.8, 3.4, 0.55, 0.22), RoofBox(coach.length_m - 3.4, coach.length_m - 1.8, 0.55, 0.22)]
    for it in items:
        # roof items are placed in side-a coordinates: x -> u like the -v side
        a, b = it.x0 / s, it.x1 / s
        if flip:
            a, b = L - b, L - a
        hw = it.hw / (2.825 / 2) * R.W_STD
        col = liv.color(it.color_key)
        parts.append(Part(u0 + a, u0 + b, -hw, hw, zr - 0.05, zr + zm(it.h), lambda *a_, col=col: col, owner))
    return parts


def coach_tiles(coach, liv, flip=False, marks=(), extra=None):
    """The 8 direction tiles of one coach (lead vehicle position, u0 = 0)."""
    parts = coach_parts(coach, liv, 0.0, "C", flip=flip, marks=marks)
    if extra is not None:
        extra(parts, 0.0, "C")
    return [R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS]


def render_rows(items):
    """items: (coach, livery) or (coach, livery, opts) -> list of 8-tile rows."""
    rows = []
    for it in items:
        coach, liv = it[0], it[1]
        opts = it[2] if len(it) > 2 else {}
        rows.append(coach_tiles(coach, liv, flip=opts.get("flip", False), marks=opts.get("marks", ()),
                                extra=opts.get("extra")))
    return rows


def save_sheet(rows, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return R.save_rows(rows, path)


def preview(rows, path, labels=None, z=4):
    return R.preview(rows, path, z=z, labels=labels)


# ------------------------------------------------------------------ drawing scan
def scan(path, ys, rail_y=None, tol=40):
    """Colour runs of vagonWEB drawing rows: [(y, z_m, [(x0_m, x1_m, hex)])].
    rail_y defaults to the lowest non-white row + 1."""
    from PIL import Image
    im = np.array(Image.open(path).convert("RGB")).astype(int)
    if rail_y is None:
        nonwhite = np.where(~np.all(im > 245, axis=2).all(axis=1))[0]
        rail_y = int(nonwhite.max()) + 1 if len(nonwhite) else im.shape[0]
    out = []
    for y in ys:
        row = im[y]
        runs, x0 = [], 0
        for x in range(1, len(row) + 1):
            if x == len(row) or np.abs(row[x] - row[x0]).sum() > tol:
                runs.append((x0 / 10.0, x / 10.0, "%02x%02x%02x" % tuple(row[x0])))
                x0 = x
        out.append((y, (rail_y - y) / 10.0, runs))
    return out


def _main(argv):
    if len(argv) >= 2 and argv[0] == "scan":
        path = argv[1]
        ys = [int(a) for a in argv[2:]] or [15, 25]
        for y, z, runs in scan(path, ys):
            print("y=%d (z %.2f m):" % (y, z), " ".join("%.1f-%.1f:%s" % r for r in runs))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
