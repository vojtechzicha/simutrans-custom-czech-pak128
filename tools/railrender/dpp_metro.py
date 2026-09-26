#!/usr/bin/env python3
"""DP Praha rail: the Prague metro (81-71M, M1) and the Petřín funicular cars.

    python tools/railrender/dpp_metro.py                  # every family
    python tools/railrender/dpp_metro.py m1 lanovka_2026  # only these family dirs
    python tools/railrender/dpp_metro.py --preview DIR    # also write 4x previews

Sheets: vehicle-rail/dpp/<family>/sprites/<livery>.png, one row per consist
position (lead cab car, the intermediate cars, rear cab car). Drawn from scratch
with the pak128.cs-calibrated box renderer (railkit) in the agreed render style
(style.py); change the model here and regenerate.

Scale: metro cars 19.2-19.5 m as length 9 (2.13 m per carunit, the length of
TommPa9's native Metro_8171M cars), funicular cars 12.1-12.3 m as length 6.
Metro cars are 2.71 m wide and 3.66 m high, a little narrower and lower than a
mainline coach; the funicular cars 2.40-2.45 m wide. Heights are in model px of
0.375 m (railkit / cdcoach convention).

Sources (research 2026-09-26, cs.wikipedia, tram-bus.cz, dpp.cz, Commons photos):
  81-71M  Mytishchi 81-71 modernised by Škoda 1996-2011, 93 sets on lines A + B.
          2Mt + 4Mt + 3Mt + 4Mt + 2Mt, all powered (4 x 110 kW per car). Silver-grey
          ribbed body, white lower band with a red stripe, red cantrail band, red
          door leaves with two tall windows, one rounded window per door bay; Škoda
          grey front mask with a large black windscreen and the red "M" logo.
  M1      ČKD / Siemens 2000-2011, 53 sets on line C. M1.1 + M1.2 + M1.3 + M1.2 + M1.1,
          all powered (4 x 141.5 kW per car). Metallic silver, dark window band,
          one red-orange stripe under the windows along the whole train, dark
          door pillars; raked silver nose, red band + chevron behind the cab.
  Petřín  1985 Vagónka Studénka cars (3rd generation, last ran 13 Sep 2024): cream
          body, teal-green window frames, skirt and front apron; 2026 Doppelmayr /
          Garaventa cars (4th generation, trial service from 22 Sep 2026): white
          shell framing gloss-black ends, almost fully glazed sides, dark roof.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM_DIR = os.path.join(REPO, "vehicle-rail", "dpp")

import railkit as R  # noqa: E402
import style  # noqa: E402
from railkit import Paint, Part, Lit  # noqa: E402
from render import DIRS  # noqa: E402

PX = 0.375                 # metres per model px

# ------------------------------------------------------------------ colours
DARK = (0x24, 0x26, 0x28)       # rubber, seams, underframe
BOGIE = (0x23, 0x24, 0x26)
BOGIE_FRAME = (0x3C, 0x3F, 0x42)
UNDER = (0x2E, 0x30, 0x32)
CABGLASS = (0x1C, 0x20, 0x24)   # windscreens: plain (not lit)
DISPLAY = (0x16, 0x17, 0x18)
DISPLAY_TXT = (0xF0, 0x8A, 0x20)
WHITE = (0xEE, 0xEF, 0xEC)

# 81-71M
G_GREY = (0xB4, 0xB8, 0xBA)     # silver-grey body
G_RED = (0xD4, 0x1E, 0x24)
G_WHITE = (0xE8, 0xE9, 0xE4)
G_ROOF = Paint((0x8C, 0x90, 0x94), top=(0x9A, 0x9E, 0xA2))
G_MASK = (0x9C, 0xA0, 0xA4)     # Škoda front mask, a shade darker than the body

# M1
S_SILVER = (0xC0, 0xC4, 0xC8)
S_PILLAR = (0x5A, 0x5E, 0x62)   # dark grey door pillars
S_ORANGE = (0xF0, 0x48, 0x22)   # red-orange stripe
S_RED = (0xD8, 0x28, 0x24)      # cab-side band
S_ROOF = Paint((0xA8, 0xAC, 0xB0), top=(0xB6, 0xBA, 0xBE))
S_SKIRT = (0x70, 0x74, 0x78)

# Petřín 1985
F_CREAM = (0xE6, 0xDE, 0xC4)
F_TEAL = (0x1C, 0x6A, 0x66)
F_ROOF = Paint((0xCE, 0xC6, 0xAE), top=(0xDA, 0xD2, 0xBA))
# Petřín 2026
N_WHITE = (0xEE, 0xF0, 0xF0)
N_BLACK = (0x16, 0x18, 0x1A)
N_ROOF = Paint((0x4A, 0x4E, 0x52), top=(0x58, 0x5C, 0x60))


def P(c):
    return Paint(c)


# ------------------------------------------------------------------ helpers
def bogies(parts, u0, L, M, centres, W, owner, zb):
    for bm in centres:
        c = u0 + bm / M
        parts.append(Part(c - 0.55, c + 0.55, -W + 0.12, W - 0.12, 0.0, zb,
                          lambda f, u, v, z, d: P(BOGIE_FRAME) if (f in ("+v", "-v") and z > zb - 0.7)
                          else P(BOGIE), owner))


def in_spans(m, spans):
    for i, sp in enumerate(spans):
        if sp[0] <= m <= sp[1]:
            return i, sp
    return None, None


# ------------------------------------------------------------------ metro car
class Metro:
    """One metro car with its front at consist-u u0.
    kind: "81-71M" | "M1"; cab: None | "front" (cab leading) | "rear" (cab at the tail).
    `rib` draws the 81-71M body ribbing (every other grey row a shade darker)."""

    L = 9.0
    ZB = 1.0            # body bottom (0.375 m)
    ZS = 9.4            # side wall top
    ZR = 10.2           # roof crown
    W = 0.92            # half width, carunits: coach width, like the natives
    # The real car (2.71 m wide, 3.66 m high) is a little smaller than a coach, but
    # TommPa9's native Metro_8171M is drawn wider and taller still; true-scale boxes
    # looked skinny next to the natives, so the metro gets the coach section.

    def __init__(self, kind, cab=None, rib=True, band=False, u0=0.0, owner="C"):
        self.kind, self.cab, self.rib, self.u0, self.owner = kind, cab, rib, u0, owner
        self.band = band        # M1: glazing fills the whole bay between the door pillars
        self.Lm = (19.40 if kind == "81-71M" else 19.52) if cab else 19.21
        self.M = self.Lm / self.L
        Lm = self.Lm
        # openings in metres from the car's (non-cab or cab) front end, cab first
        if kind == "81-71M":
            dc = [3.0, 7.4, 11.8, 16.2] if not cab else [3.4, 7.8, 12.2, 16.6]
            self.doors = [(c - 0.65, c + 0.65) for c in dc]
            self.wins = []
            edges = [0.0 if not cab else 2.0] + [x for c in dc for x in (c - 0.65, c + 0.65)] + [Lm]
            for a, b in zip(edges[0::2], edges[1::2]):
                g = b - a
                if g > 1.4:
                    w = min(1.45, g - 0.8)
                    c = (a + b) / 2
                    self.wins.append((c - w / 2, c + w / 2))
        else:
            dc = [3.1, 7.5, 11.9, 16.3] if not cab else [3.5, 7.9, 12.3, 16.7]
            self.doors = [(c - 0.8, c + 0.8) for c in dc]
            edges = [0.0 if not cab else 2.0] + [x for c in dc for x in (c - 0.8, c + 0.8)] + [Lm]
            ins = 0.12 if band else 0.45
            self.wins = [(a + ins, b - ins) for a, b in zip(edges[0::2], edges[1::2]) if b - a > 1.2]
        self.cabdoor = (1.05, 1.65) if cab else None

    # physical metres from the cab end (or the car front for intermediate cars)
    def m_of(self, u):
        m = (u - self.u0) * self.M
        return self.Lm - m if self.cab == "rear" else m

    # ---------------------------------------------------------- 81-71M
    def side_81(self, f, u, v, z, d):
        m = self.m_of(u)
        rib = self.rib and int(np.floor(z)) % 2 == 1
        grey = P(tuple(c * style.RIB for c in G_GREY)) if rib else P(G_GREY)
        if z >= 8.4:
            return P(G_RED)                                  # cantrail band
        # lower livery: white / red stripe / white, across the doors too
        if z < 2.0:
            return P(G_WHITE)
        if z < 3.0:
            return P(G_RED)
        if z < 3.8:
            return P(G_WHITE)
        i, dr = in_spans(m, self.doors)
        if dr:
            a, b = dr
            mid = (a + b) / 2
            if abs(m - mid) < 0.07:
                return P(DARK)
            if 4.3 <= z <= 7.8 and (a + 0.18 <= m <= mid - 0.14 or mid + 0.14 <= m <= b - 0.18):
                return R.GLASS
            return P(G_RED)
        if self.cabdoor and self.cabdoor[0] <= m <= self.cabdoor[1]:
            if 4.6 <= z <= 7.2 and self.cabdoor[0] + 0.12 <= m <= self.cabdoor[1] - 0.12:
                return P(CABGLASS)
            return P(G_MASK)
        if self.cab and m < 1.0 and 4.8 <= z <= 7.4 and 0.2 <= m <= 0.8:
            return P(CABGLASS)                               # cab side window
        i, w = in_spans(m, self.wins)
        if w and 4.2 <= z <= 7.9:
            a, b = w
            if a + 0.1 <= m <= b - 0.1 and 4.4 <= z <= 7.7:
                return R.GLASS_HI if z > 6.9 else R.GLASS
            return P(DARK)
        return grey

    def face_81(self, f, u, v, z, d, cab):
        av = abs(v)
        if z >= 8.4:
            return P(G_RED) if av > self.W - 0.12 else P(G_MASK)
        if cab:
            if 7.8 <= z < 8.4:
                return P(DISPLAY)
            if 4.4 <= z < 7.8 and av <= self.W - 0.1:
                return P(CABGLASS)
            if 2.0 <= z <= 2.9 and 0.46 <= av <= 0.72:
                return Lit(R.HEAD if cab == "front" else R.TAIL)
            if 3.0 <= z <= 3.9 and av <= 0.16:
                return P(G_RED)                              # "M" logo
            if z < 1.6:
                return P(DARK)
            return P(G_MASK)
        # gangway end
        if av < 0.35 and 1.6 <= z <= 7.6:
            return P(DARK)
        if z < 2.0 or 3.0 <= z < 3.8:
            return P(G_WHITE)
        if z < 3.0:
            return P(G_RED)
        return P(G_GREY)

    # ---------------------------------------------------------- M1
    def side_m1(self, f, u, v, z, d):
        m = self.m_of(u)
        stripe = 3.6 <= z < 4.6
        # cab-side red band + chevron behind the cab door
        if self.cab:
            if 1.7 <= m <= 2.0 and 2.0 <= z <= 8.8:
                return P(S_RED)
            if 2.0 < m <= 3.2 and stripe:
                # chevron: the stripe rises into the band
                return P(S_ORANGE)
        i, dr = in_spans(m, self.doors)
        if dr:
            a, b = dr
            if m < a + 0.22 or m > b - 0.22:
                return P(S_ORANGE) if stripe else P(S_PILLAR)
            mid = (a + b) / 2
            if abs(m - mid) < 0.06:
                return P(DARK)
            if 3.0 <= z <= 8.3 and (a + 0.34 <= m <= mid - 0.12 or mid + 0.12 <= m <= b - 0.34):
                return P(S_ORANGE) if stripe else R.GLASS
            return P(S_ORANGE) if stripe else P(S_SILVER)
        if stripe:
            return P(S_ORANGE)
        if self.cabdoor and self.cabdoor[0] <= m <= self.cabdoor[1]:
            if 4.8 <= z <= 7.8 and self.cabdoor[0] + 0.1 <= m <= self.cabdoor[1] - 0.1:
                return P(CABGLASS)
            return P(S_SILVER)
        if self.cab and m < 1.0 and 4.8 <= z <= 7.8 and 0.3 <= m <= 0.9:
            return P(CABGLASS)
        i, w = in_spans(m, self.wins)
        if w and 4.6 <= z <= 8.5:
            a, b = w
            n = max(1, int(round((b - a) / 1.5)))
            mul = any(abs(m - (a + (b - a) * k / n)) < 0.05 for k in range(1, n))
            if mul or z < 4.8 or z > 8.3:
                return P(DARK)
            return R.GLASS_HI if z > 7.5 else R.GLASS
        if z < 1.8:
            return P(S_SKIRT)
        return P(S_SILVER)

    def face_m1(self, f, u, v, z, d, cab):
        av = abs(v)
        if cab:
            if 8.0 <= z < 8.8 and av <= self.W - 0.18:
                return P(DISPLAY)
            if 3.9 <= z < 8.8 and av <= self.W - 0.08:
                return P(CABGLASS)
            if 1.9 <= z <= 2.7 and 0.44 <= av <= 0.72:
                return Lit(R.HEAD if cab == "front" else R.TAIL)
            if 2.8 <= z <= 3.6 and av <= 0.16:
                return P(S_RED)                              # "M" logo
            if z < 1.4:
                return P(DARK)
            return P(S_SILVER)
        if av < 0.35 and 1.6 <= z <= 7.8:
            return P(DARK)
        return P(S_ORANGE) if 3.6 <= z < 4.6 else P(S_SILVER)

    # ---------------------------------------------------------- assembly
    def parts(self):
        kind, cab, u0, L, W, o = self.kind, self.cab, self.u0, self.L, self.W, self.owner
        m1 = kind == "M1"
        side = self.side_m1 if m1 else self.side_81
        face = self.face_m1 if m1 else self.face_81
        roof = S_ROOF if m1 else G_ROOF
        cab_face = "-u" if cab == "front" else "+u"

        def body(f, u, v, z, d):
            if f == "+z":
                return roof
            if f in ("+v", "-v"):
                return side(f, u, v, z, d)
            is_cab = cab is not None and f == cab_face
            return face(f, u, v, z, d, cab if is_cab else None)

        parts = []
        ub0, ub1 = u0 + 0.08, u0 + L - 0.08
        if cab == "front":
            ub0 = u0 + (0.22 if m1 else 0.12)
        elif cab == "rear":
            ub1 = u0 + L - (0.22 if m1 else 0.12)
        parts.append(Part(ub0, ub1, -W, W, self.ZB, self.ZS, body, o))
        # roof: dark gutter under a slightly inset crown (style: never a light rim)
        gut = P(style.GUTTER)
        parts.append(Part(ub0 + 0.04, ub1 - 0.04, -W + 0.06, W - 0.06, self.ZS, self.ZS + 0.35,
                          lambda f, u, v, z, d: roof if f == "+z" else gut, o))
        parts.append(Part(ub0 + 0.1, ub1 - 0.1, -W + 0.2, W - 0.2, self.ZS + 0.35, self.ZR,
                          lambda f, u, v, z, d: roof, o))
        # cab nose: the M1's raked lower nose and bumper, the 81-71M's flat mask
        if cab:
            sgn = -1 if cab == "front" else 1
            end = ub0 if cab == "front" else ub1
            nose = 0.14 if m1 else 0.06
            a, b = (end - nose, end) if cab == "front" else (end, end + nose)
            parts.append(Part(a, b, -W + 0.06, W - 0.06, self.ZB, 3.8 if m1 else 3.0, body, o))
            # coupler
            cu = end + sgn * (nose + 0.06)
            parts.append(Part(min(cu, end), max(cu, end), -0.12, 0.12, 0.9, 1.6,
                              lambda *a_: P(DARK), o))
        # gangway ends
        for (a, b, is_cab) in ((u0 + 0.01, ub0, cab == "front"), (ub1, u0 + L - 0.01, cab == "rear")):
            if is_cab or b - a < 0.03:
                continue
            parts.append(Part(a, b, -0.34, 0.34, 1.8, 7.6, lambda *a_: P(DARK), o))
        # underframe + bogies (bogie centres 2.6 m from the ends)
        parts.append(Part(u0 + 1.8, u0 + L - 1.8, -W + 0.22, W - 0.22, 0.0, self.ZB,
                          lambda *a_: P(UNDER), o))
        bogies(parts, u0, L, self.M, (2.6, self.Lm - 2.6), W, o, self.ZB + 0.3)
        # roof equipment: two low grey boxes (vent / AC housings)
        box = Paint((0x70, 0x74, 0x78), top=(0x80, 0x84, 0x88))
        for (a, b) in ((5.0, 6.6), (12.6, 14.2)):
            if cab == "rear":
                a, b = self.Lm - b, self.Lm - a
            parts.append(Part(u0 + a / self.M, u0 + b / self.M, -0.4, 0.4, self.ZR, self.ZR + 0.45,
                              lambda *a_: box, o))
        return parts


# ------------------------------------------------------------------ funicular
class Funicular:
    """Petřín funicular car, drawn level (the engine draws every vehicle level on
    slopes as well). gen: 1985 | 2026. Both ends are cab ends: headlights at the
    leading end, tail lights at the trailing end."""

    L = 6.0

    def __init__(self, gen, u0=0.0, owner="C"):
        self.gen, self.u0, self.owner = gen, u0, owner
        self.Lm = 12.1 if gen == 1985 else 12.3
        self.M = self.Lm / self.L
        self.W = 0.92 * (2.40 if gen == 1985 else 2.45) / 2.85
        self.ZB = 1.4
        self.ZS = 8.0
        self.ZR = 8.6
        # 4 compartments, each with a door on both sides (1985: door + 2 windows)
        cm = self.Lm / 4
        self.comp = [(k * cm, (k + 1) * cm) for k in range(4)]

    def side_old(self, f, u, v, z, d):
        m = (u - self.u0) * self.M
        if z >= 7.6:
            return P(F_CREAM)
        if z < 2.4:
            return P(F_TEAL)                                  # teal skirt
        # compartments: door (front third) then two windows, teal frames
        for (a, b) in self.comp:
            if a <= m <= b:
                w = b - a
                door = (a + 0.15, a + 0.15 + 0.85)
                if door[0] <= m <= door[1]:
                    if 2.8 <= z <= 7.3 and door[0] + 0.1 <= m <= door[1] - 0.1:
                        return R.GLASS
                    return P(F_TEAL)
                wa = door[1] + 0.2
                ww = (b - 0.2 - wa) / 2
                for k in range(2):
                    x0 = wa + k * ww
                    if x0 + 0.04 <= m <= x0 + ww - 0.04 and 3.2 <= z <= 7.5:
                        if x0 + 0.12 <= m <= x0 + ww - 0.12 and 3.4 <= z <= 7.3:
                            return R.GLASS_HI if z > 6.6 else R.GLASS
                        return P(F_TEAL)
        return P(F_CREAM)

    def face_old(self, f, u, v, z, d, lead):
        av = abs(v)
        if z >= 7.6:
            return P(F_CREAM)
        if 4.2 <= z <= 7.3 and av <= self.W - 0.08:
            # 3-pane windscreen with cream mullions
            if abs(av - self.W / 3) < 0.05:
                return P(F_CREAM)
            return P(CABGLASS)
        if z < 4.0:
            if 1.9 <= z <= 2.6 and 0.40 <= av <= 0.62:
                return Lit(R.HEAD if lead else R.TAIL)
            if 2.9 <= z <= 3.5 and av <= 0.12:
                return P(WHITE)                               # DPP logo
            return P(F_TEAL)                                  # teal front apron
        return P(F_CREAM)

    def side_new(self, f, u, v, z, d):
        m = (u - self.u0) * self.M
        if z >= 7.2:
            return P(N_WHITE)                                 # white shell top edge
        if z < 3.0:
            return P(N_WHITE)                                 # white skirt
        if m < 0.45 or m > self.Lm - 0.45:
            return P(N_WHITE)                                 # shell frames the ends
        # glazing with slim black mullions ~1.3 m apart; door sills in white
        n = 9
        span = self.Lm - 0.7
        k = (m - 0.35) / span * n
        if abs(k - round(k)) * span / n < 0.06:
            return P(N_BLACK)
        for (a, b) in self.comp:
            if a + 0.3 <= m <= a + 1.1 and z < 3.3:
                return P(N_WHITE)
        return R.GLASS_HI if z > 6.8 else R.GLASS

    def face_new(self, f, u, v, z, d, lead):
        av = abs(v)
        if av > self.W - 0.14 or z >= 7.4 or z < 2.0:
            return P(N_WHITE)                                 # white frame round the end
        if z >= 4.6:
            return P(N_BLACK)                                 # windscreen, gloss black
        if 2.2 <= z <= 2.8 and 0.36 <= av <= 0.56:
            return Lit(R.HEAD if lead else R.TAIL)
        if 3.4 <= z <= 4.0 and av <= 0.1:
            return P(WHITE)                                   # DPP logo
        return P(N_BLACK)

    def parts(self):
        u0, L, W, o = self.u0, self.L, self.W, self.owner
        old = self.gen == 1985
        side = self.side_old if old else self.side_new
        face = self.face_old if old else self.face_new
        roof = F_ROOF if old else N_ROOF

        def body(f, u, v, z, d):
            if f == "+z":
                return roof
            if f in ("+v", "-v"):
                return side(f, u, v, z, d)
            return face(f, u, v, z, d, f == "-u")

        parts = [Part(u0 + 0.05, u0 + L - 0.05, -W, W, self.ZB, self.ZS, body, o)]
        gut = P(style.GUTTER)
        parts.append(Part(u0 + 0.08, u0 + L - 0.08, -W + 0.05, W - 0.05, self.ZS, self.ZS + 0.3,
                          lambda f, u, v, z, d: roof if f == "+z" else gut, o))
        parts.append(Part(u0 + 0.15, u0 + L - 0.15, -W + 0.15, W - 0.15, self.ZS + 0.3, self.ZR,
                          lambda f, u, v, z, d: roof, o))
        if not old:     # black equipment box at each roof end
            bx = Paint((0x22, 0x24, 0x26), top=(0x2E, 0x30, 0x32))
            for (a, b) in ((0.5, 1.4), (L - 1.4, L - 0.5)):
                parts.append(Part(u0 + a, u0 + b, -0.45, 0.45, self.ZR, self.ZR + 0.5, lambda *a_: bx, o))
        # frame + two axles (funicular cars run on two single axles / short bogies)
        parts.append(Part(u0 + 0.6, u0 + L - 0.6, -W + 0.18, W - 0.18, 0.0, self.ZB,
                          lambda *a_: P(UNDER), o))
        bogies(parts, u0, L, self.M, (2.2, self.Lm - 2.2), W, o, self.ZB)
        return parts


# ------------------------------------------------------------------ families
# family dir -> (vehicles: [(id, builder)], liveries: {slug: (en, cs)})
def _m(kind, cab=None, **kw):
    return lambda: Metro(kind, cab, **kw).parts()


FAMILIES = {
    "81_71m": dict(liv="sedocervena", rows=[
        ("2Mt-front", _m("81-71M", "front")),
        ("4Mt", _m("81-71M")),
        ("3Mt", _m("81-71M")),
        ("2Mt-rear", _m("81-71M", "rear")),
    ]),
    "m1": dict(liv="stribrnocervena", rows=[
        ("M1.1-front", _m("M1", "front", band=True)),
        ("M1.2", _m("M1", band=True)),
        ("M1.3", _m("M1", band=True)),
        ("M1.1-rear", _m("M1", "rear", band=True)),
    ]),
    "lanovka_1985": dict(liv="kremovozelena", rows=[
        ("1985", lambda: Funicular(1985).parts()),
    ]),
    "lanovka_2026": dict(liv="bilocerna", rows=[
        ("2026", lambda: Funicular(2026).parts()),
    ]),
}


def rows_of(fam, polish=True):
    rows = []
    for (_, build) in FAMILIES[fam]["rows"]:
        parts = build()
        rows.append([R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS])
    if polish:
        from PIL import Image
        sheet = np.zeros((128 * len(rows), 1024, 3), np.uint8)
        for r, tiles in enumerate(rows):
            for c, t in enumerate(tiles):
                sheet[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
        sheet = np.array(style.polish(Image.fromarray(sheet), **style.POLISH))
        rows = [[sheet[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] for c in range(8)]
                for r in range(len(rows))]
    return rows


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        del argv[i:i + 2]
    fams = argv or list(FAMILIES)
    for fam in fams:
        rows = rows_of(fam)
        out = os.path.join(FAM_DIR, fam, "sprites", FAMILIES[fam]["liv"] + ".png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        R.save_rows(rows, out)
        print("wrote", out)
        if prev:
            os.makedirs(prev, exist_ok=True)
            R.preview(rows, os.path.join(prev, fam + ".png"),
                      labels=[v for (v, _) in FAMILIES[fam]["rows"]])


if __name__ == "__main__":
    main(sys.argv[1:])
