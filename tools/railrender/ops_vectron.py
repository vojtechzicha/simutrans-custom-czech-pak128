#!/usr/bin/env python3
"""Siemens Vectron MS locomotives leased to PKP Intercity that haul its trains
across Czech track: the Leo Express Vectron model (vectron.py, geometry shared,
not edited) in three lessors' liveries.

    python tools/railrender/ops_vectron.py [--preview DIR]

writes vehicle-rail/pkp-intercity/vectron/sprites/<livery>.png.

  balticexpress   Cargounit / Industrial Division 91 51 5 370 07x/09x (6193 xxx),
                  "Baltic Express" wrap: sky-blue cab ends and cab roofs, white
                  machine-room sides with a pale watercolour sea, big dark-blue
                  italic "BALTIC EXPRESS" + slogan, red-orange "iC" logo behind the
                  cab door, vertical red "CARGOUNIT" line at the blue/white edge,
                  anthracite lower band and machine-room roof, black lower front.
  kierunekeuropa  ELL 91 80 6193 428 in PKP IC blue with the "Kierunek EUROPA!"
                  side graphic: "iC" logo, white "EUROPA!", gold EU stars, a
                  halftone map of Europe in light blue and a stacked list of
                  white city names; grey lower band and lower front.
  gmpbila         Green Mobility Partners 91 81 1293 206: plain silver-white,
                  anthracite lower band and machine-room roof, black lower front
                  (photo: Kotomierz, Sep 2025, on IC 265 Baltic Express).

Photos (Commons, vagonWEB): 5370 073 Bohumin
Mar 2026, 5370 076 Wroclaw Jan 2025, 5370 075 Warszawa Wsch. Apr 2026 (side-on),
193 428 Warszawa Zachodnia Feb 2026 (both), 1293 206 Kotomierz Sep 2025.
The real Vectron MS has no cab side window between the windscreen and the cab
door (all photos), so these liveries paint over the one vectron.py draws there.
Lettering reads left to right as seen on both sides (photos of both sides).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "pkp-intercity", "vectron")

import numpy as np  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
from render import DIRS  # noqa: E402
import vectron as V  # noqa: E402

L, W, ZB, ZS = V.L, V.W, V.ZB, V.ZS
Z_LOW = 4.3            # top of the dark lower band on the side (photos ~19 %)
Z_FRONT_LOW = 4.7      # front: dark below the headlight housings
CAB_ROOF = 2.0         # the cab module's roof reaches back past the door (photo 075)
DOOR = (1.36, 1.80)    # vectron.py cab door


# ------------------------------------------------------------------ lettering
# 5-row pixel font; a text block is placed on the side in model units and
# sampled by COVERAGE of the screen pixel's footprint (0.25 cu x 1 z in the
# straight views), so small lettering turns into the right amount of ink at 1x
# instead of aliasing to random dots.
FONT = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"], "E": ["###", "#..", "##.", "#..", "###"],
    "I": ["#", "#", "#", "#", "#"], "K": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"], "O": [".#.", "#.#", "#.#", "#.#", ".#."],
    "P": ["##.", "#.#", "##.", "#..", "#.."], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Z": ["###", "..#", ".#.", "#..", "###"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"], "M": ["#.#", "###", "###", "#.#", "#.#"],
    "N": ["#.#", "###", "###", "###", "#.#"], "!": ["#", "#", "#", ".", "#"],
    " ": ["..", "..", "..", "..", ".."],
}


class Text:
    """A line of FONT text stretched into the box x0..x1 (cu, as read), z0..z1,
    sheared by `italic` cu per z (to the right going up)."""
    def __init__(self, s, x0, x1, z0, z1, italic=0.0, sub=8):
        cols = []
        for i, ch in enumerate(s):
            g = FONT[ch]
            if i:
                cols.append([0] * 5)
            for c in range(len(g[0])):
                cols.append([1 if g[r][c] == "#" else 0 for r in range(5)])
        bm = np.array(cols, float).T                    # 5 x n, row 0 = top
        self.bm = np.kron(bm, np.ones((sub, sub)))      # supersampled
        self.x0, self.x1, self.z0, self.z1, self.it = x0, x1, z0, z1, italic
        h, w = self.bm.shape
        self.sat = np.zeros((h + 1, w + 1))
        self.sat[1:, 1:] = self.bm.cumsum(0).cumsum(1)

    def cov(self, x, z, dx=0.25, dz=1.0):
        """Ink coverage (0..1) of the footprint centred on (x, z)."""
        x = x - self.it * (z - self.z0)
        h, w = self.bm.shape
        fx = lambda xx: np.clip((xx - self.x0) / (self.x1 - self.x0) * w, 0, w)
        fz = lambda zz: np.clip((self.z1 - zz) / (self.z1 - self.z0) * h, 0, h)
        a0, a1 = int(round(float(fx(x - dx / 2)))), int(round(float(fx(x + dx / 2))))
        b0, b1 = int(round(float(fz(z + dz / 2)))), int(round(float(fz(z - dz / 2))))
        if a1 <= a0 or b1 <= b0:
            return 0.0
        s = self.sat[b1, a1] - self.sat[b0, a1] - self.sat[b1, a0] + self.sat[b0, a0]
        return s / ((dx / (self.x1 - self.x0) * w) * (dz / (self.z1 - self.z0) * h))


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ink(bg, fg, c, lo=0.22, hi=0.55):
    """Background -> ink by coverage: none below lo, full above hi, a half tone
    between (keeps small lettering legible at 1x without speckle)."""
    if c <= lo:
        return bg
    if c >= hi:
        return fg
    return mix(bg, fg, 0.5)


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# ------------------------------------------------------------------ liveries
# The keys vectron.build() reads must exist (it still draws the geometry, the
# windscreen, door window, lamps); every Paint it returns is repainted below.
def _table(body, cabroof):
    return dict(body=Paint(body), roofcap=Paint(cabroof), orange=None, mask=Paint(cabroof),
                lower=Paint(0x2D2F34), door=Paint(body), logo=None, band=None,
                cabroof=Paint(cabroof))


LIVERIES = {
    "balticexpress": dict(
        name_en="Baltic Express", name_cs="Baltic Express",
        cab=0x2E98D8, cabroof_top=0x3AA6E2, body=0xE7EBF0, door=0xD9DEE5,
        low=0x2D2F35, frontlow=0x1E2023, roof=0x3C424A, roof_top=0x4A5159,
        text=0x173E96, wash=0xB4CCEA, wash2=0xD2DFF0,
        red=0xD8262C, logo_red=0xE0482A, logo_grey=0x8C939B),
    "kierunekeuropa": dict(
        name_en="Kierunek EUROPA!", name_cs="Kierunek EUROPA!",
        cab=0x2A56A8, cabroof_top=0x3462B4, body=0x2A56A8, door=0x2750A0,
        low=0x4E535B, frontlow=0x5A5F66, roof=0x3C424A, roof_top=0x4A5159,
        text=0xF2F4F7, map=0x62A8E2, map2=0x3F7CC6, star=0xF2C230,
        logo_red=0xEE5A2A, logo_grey=0xC9D2E4),
    "gmpbila": dict(
        name_en="GMP white", name_cs="GMP bílá",
        cab=0xDDE2E7, cabroof_top=0xD2D7DC, body=0xDDE2E7, door=0xCFD4DA,
        low=0x34373C, frontlow=0x1E2023, roof=0x3C424A, roof_top=0x4A5159),
}

_orig_livery = V.livery


def _livery(name):
    if name in LIVERIES:
        c = LIVERIES[name]
        return _table(c["body"], c["cab"])
    return _orig_livery(name)


V.livery = _livery   # vectron.build() looks the table up through this name

# side artwork (x = cu from the LEFT end as seen, z = model px)
BE_LOGO = (2.05, 3.35)                         # "iC" logo box behind the door
BE_TEXT = Text("BALTIC EXPRESS", 3.75, 9.05, 7.7, 10.5, italic=0.10)
BE_SLOGAN = Text("MORZE AZ DO CZECH", 5.9, 8.95, 5.95, 6.95, italic=0.05)
KE_TEXT = Text("EUROPA!", 3.35, 5.35, 6.6, 8.9)
KE_KIER = Text("KIERUNEK", 3.4, 4.7, 9.2, 9.9)
KE_MAP = (5.6, 7.1)
KE_CITIES = (7.25, 7.95)


def _europe(x, z):
    """Rough outline of the halftone Europe map (x across as read, z up)."""
    t = (x - KE_MAP[0]) / (KE_MAP[1] - KE_MAP[0])
    if not (0.0 <= t <= 1.0):
        return False
    # west coast leaning right towards the top, Scandinavia as a tall lobe,
    # the east open (the map is cut by the panel edge on the loco)
    lo = 4.9 + 1.2 * abs(t - 0.45)
    hi = 8.2 + 2.2 * max(0.0, 1 - abs(t - 0.62) / 0.22)
    return lo <= z <= min(hi, 10.6) and t >= 0.05 + 0.18 * max(0.0, (z - 7.0) / 3.0)


def _logo_ic(c, x, z, x0, w=1.25):
    """PKP IC "iC" logo: red-orange i+C and the grey chain of C rings."""
    t = (x - x0) * 1.25 / w
    if 7.6 <= z <= 10.2:
        if 0.0 <= t <= 0.55:
            return rgb(c["logo_red"])
        if 0.55 < t <= 1.25 and (z > 9.4 or z < 8.4 or t < 0.8):
            return rgb(c["logo_grey"])
    if 6.2 <= z <= 6.9 and 0.0 <= t <= 1.25:
        return mix(rgb(c["body"]), (0x40, 0x44, 0x4C), 0.6)     # "PKP INTERCITY"
    return None


def side_art(liv, x, cu, z):
    """Side colour at (x, z); None = plain body colour."""
    c = LIVERIES[liv]
    body = rgb(c["body"])
    if liv == "balticexpress":
        if 0.86 <= cu <= 1.06 and 5.0 <= z <= 10.6:
            return rgb(c["red"])                           # vertical "CARGOUNIT"
        if cu < 1.9:
            return None
        lg = _logo_ic(c, x, z, BE_LOGO[0]) if x < L / 2 else None
        if lg is not None:
            return lg
        # watercolour: pale sea below / sky behind the text, fading to the ends
        fade = max(0.0, min(1.0, (x - 3.4) / 1.4, (L - 1.0 - x) / 0.9))
        bg = body
        if fade > 0:
            if z < 7.2:
                bg = mix(body, rgb(c["wash"]), 0.85 * fade)
            elif z < 10.8 and x > 5.6:
                bg = mix(body, rgb(c["wash2"]), fade)
        t = BE_TEXT.cov(x, z)
        col = ink(bg, rgb(c["text"]), t, 0.28, 0.45)
        if col == bg:
            col = ink(bg, rgb(c["text"]), BE_SLOGAN.cov(x, z), 0.3, 0.7)
        return col if col != body else None
    if liv == "kierunekeuropa":
        if cu < 1.9:
            return None
        lg = _logo_ic(c, x, z, 1.95, 0.95) if x < L / 2 else None
        if lg is not None:
            return lg
        col = ink(body, rgb(c["text"]), KE_TEXT.cov(x, z), 0.12, 0.3)
        if col == body:
            col = ink(body, mix(body, rgb(c["text"]), 0.8), KE_KIER.cov(x, z), 0.25, 0.6)
        if col != body:
            return col
        # gold EU stars: a loose ring round the lettering
        for (sx, sz) in ((3.15, 7.3), (3.2, 8.8), (5.5, 7.6), (4.3, 6.1), (5.45, 9.2)):
            if abs(x - sx) < 0.13 and abs(z - sz) < 0.5:
                return rgb(c["star"])
        if _europe(x, z):
            # halftone dots: a checker in model units, brighter towards the east
            k = int(np.floor(x / 0.25)) + int(np.floor(z))
            return rgb(c["map"]) if k % 2 == 0 else rgb(c["map2"])
        if KE_CITIES[0] <= x <= KE_CITIES[1] and 5.0 <= z <= 10.4:
            row = int(np.floor(z - 5.0))
            if row % 2 == 0:
                ln = (0.70, 0.55, 0.80, 0.45, 0.75, 0.60)[row // 2 % 6]
                if x <= KE_CITIES[0] + ln:
                    return rgb(c["text"])
        return None
    return None


def body_paint(liv, f, u, v, z, d, orig):
    """Repaint a body/roof-cap face; `orig` = what vectron.py returned there."""
    c = LIVERIES[liv]
    cu = min(u, L - u)
    if f in ("+v", "-v"):
        if isinstance(orig, (int, tuple)):
            # vectron.py's cab side window (not on the real MS): paint it over
            if not (0.60 <= cu <= 1.20 and 7.9 <= z <= 10.7):
                return orig
        if z > ZS + 0.01:                                   # roof cap sides
            return Paint(c["cab"]) if cu < CAB_ROOF else Paint(c["roof"])
        if z < Z_LOW:
            return Paint(c["low"])
        if liv == "balticexpress" and cu < 0.80:
            return Paint(c["cab"])
        if DOOR[0] <= cu <= DOOR[1] and 3.2 <= z <= 10.8:
            return Paint(c["door"])
        x = u if f == "-v" else L - u
        art = side_art(liv, x, cu, z)
        if art is not None:
            return Paint(art)
        return Paint(c["body"])
    if f == "+z":
        if isinstance(orig, (int, tuple)):
            return orig                                     # windscreen tops
        if z < ZS - 0.05:
            return Paint(c["cab"], top=c["cabroof_top"])    # sloped nose steps
        return Paint(c["cab"], top=c["cabroof_top"]) if cu < CAB_ROOF else \
            Paint(c["roof"], top=c["roof_top"])
    # cab fronts (-u lead cab, +u rear cab)
    if isinstance(orig, (int, tuple)):
        return orig                                         # windscreen, lamps
    if z < Z_FRONT_LOW:
        return Paint(c["frontlow"])
    if 5.7 <= z <= 6.5 and abs(v) < 0.42:
        return Paint(0x23262A)                              # grille bars
    return Paint(c["cab"])


def build(liv):
    parts, lines = V.build(liv)
    for p in parts:
        if getattr(p.mat, "__name__", "") in ("body_mat", "roof_mat"):
            p.mat = (lambda m: lambda f, u, v, z, d: body_paint(liv, f, u, v, z, d, m(f, u, v, z, d)))(p.mat)
    return parts, lines


def rows_for(liv):
    """In the agreed 2026-09-26 style (style.py): dark roof gutter, light
    pantograph arms with a dark head bar; main() runs style.polish()."""
    import restyle_kit as K
    parts, lines = build(liv)
    K.roof_restyle(parts, V.ZS, V.ZR)
    lines = K.restyle_lines(lines)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for liv in (args or list(LIVERIES)):
        rows = rows_for(liv)
        out = os.path.join(FAM, "sprites", f"{liv}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        import restyle_kit as K
        K.save_styled(rows, out)
        if prev:
            R.preview(rows, os.path.join(prev, f"vectron_{liv}.png"), z=4, labels=[liv])
        print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
