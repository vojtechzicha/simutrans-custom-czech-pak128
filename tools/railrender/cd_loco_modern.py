#!/usr/bin/env python3
"""ČD modern electric locomotives, box models on the calibrated rail renderer.

    python tools/railrender/cd_loco_modern.py [family ...] [--preview DIR]

Families (vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png):
  193  Siemens Vectron MS: vectron (the ten ELL units 193.289-298, "We connect
       people and places" with the city skyline) and vectronrsl (the RS Lease
       units: silver body, blue cab ends and roof-edge band)
  384  Siemens Vectron MS 230 km/h: cd384 (white, navy speed lines, big ČD logo)

The Vectron geometry is vectron.py's (imported, not edited); only the paint
changes, as rj_locos.VectronRJ does. The ČD 380 keeps TommPa9's hand-drawn
sheets (the user preferred them to a render). Scale: the 19 m Vectrons are
length 10 like the native 1216 / ES64U2 / CZR 193. Sides / fronts are painted by whole pixel rows counted from a
base line (rj_locos.prow), so the diagonal views never show half-pixel
slivers; lettering is a pixel bitmap (rj_locos.Glyphs).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import railkit as R  # noqa: E402
from railkit import Paint, Part  # noqa: E402
from render import DIRS  # noqa: E402
import cd_loco_livery as CL  # noqa: E402
import style as ST  # noqa: E402
from rj_locos import (Glyphs, EndGlyphs, prow, vc, scr, in_cols, in_vcols,  # noqa: E402
                      on_col, bogie, _uu, WS, WS_HI, P_BOGIE)

# ------------------------------------------------------------------ colours
SKY = Paint(CL.LOCO_SKY, top=tuple(min(255, c + 12) for c in CL.LOCO_SKY))
SAPPH = Paint(CL.SAPPHIRE, top=tuple(c + 10 for c in CL.SAPPHIRE))
WHITE = Paint(CL.WHITE)
# own colours (photos 193.296, 193.024, 384.014, 380.008, 380.013)
VEC_BLUE = Paint((28, 60, 136), top=(36, 70, 146))    # Vectron cab ends: brighter than RAL 5003
VEC_SKYLINE = Paint((24, 82, 150))                      # skyline print in the light-blue band
VEC_SILVER = Paint((222, 226, 229), top=(210, 214, 217))
NAVY = Paint((36, 50, 118), top=(44, 58, 126))          # 384 navy
W384 = Paint((238, 241, 243), top=(226, 229, 232))
FRAME = Paint(CL.FRAME)
FRAME_GREY = Paint((74, 78, 82))                        # Vectron grey underframe skirt
ROOF = Paint(ST.ROOF_TOP, top=ST.ROOF_TOP)              # agreed render style (style.py)
ROOF_DK = Paint(ST.ROOF, top=ST.ROOF_TOP)
GUTTER = Paint(ST.GUTTER, top=ST.GUTTER)                # dark line where roof meets body
RED = Paint((200, 30, 40))
BLACK = Paint((28, 30, 32))

LOGO_COLS = {"n": NAVY, "b": SAPPH, "v": VEC_BLUE, "w": WHITE, "r": RED, "s": SKY}

# "ČD" mark + "České dráhy" as tiny bitmaps (one cell = one screen pixel)
CD_MARK_H = ["xxx.xx", "x...xx", "xxx.xx"]
CD_MARK_D = ["xx.x", "x..x", "xx.x"]
CD_TEXT_H = ["xxxxx.xxxxx", "..........."]
CD_TEXT_D = ["xxx.xxx"]


def mark(col, text=True, mode="H"):
    m = CD_MARK_H if mode == "H" else CD_MARK_D
    t = CD_TEXT_H if mode == "H" else CD_TEXT_D
    rows = [r.replace("x", col) for r in m]
    if text:
        tt = [r.replace("x", col) for r in t] + ["." * len(t[0])] * (len(m) - len(t))
        rows = [a + "." + b for a, b in zip(rows, tt[::-1][::-1])]
        # text sits on the upper rows of the mark
    return rows


def hsh(n):
    """cheap deterministic hash -> 0..1 (skyline heights)."""
    n = (n * 374761393 + 668265263) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


# ================================================================== Vectron (ČD)
class VectronCD:
    """vectron.py geometry, ČD paint. Side rows count from ZG (top of the grey
    underframe skirt, 1.35 m); `top` is the roof gutter row."""

    def __init__(self, liv):
        import vectron as V
        self.V = V
        self.liv = liv
        self.ZG = V.ZB + 1.0
        L = V.L
        if liv == "cd384":
            self.logo = Glyphs(2.05, self.ZG, (3, 3), mark("n", False, "H"), mark("n", False, "D"), LOGO_COLS)
        elif liv == "vectron":
            self.logo = Glyphs(1.62, self.ZG, (6, 5), mark("v", False, "H"), mark("v", False, "D"), LOGO_COLS)
        else:
            self.logo = Glyphs(4.4, self.ZG, (4, 3), mark("v", False, "H"), mark("v", False, "D"), LOGO_COLS)
        self.L = L

    # ---------------------------------------------------------------- sides
    def door(self, d, u, v, z, r, top):
        """cab doors just behind both cabs: dark outline + window."""
        L = self.L
        near = u < L / 2
        da, db = _uu(L, near, 1.06, 1.46)
        if da - 0.1 <= u <= db + 0.1:
            if on_col(d, u, v, z, da, v) or on_col(d, u, v, z, db, v):
                return BLACK
            if da <= u <= db and (top - 4) <= r <= top - 2 and in_cols(d, u, v, z, *_uu(L, near, 1.14, 1.38)):
                return WS
        return None

    def side(self, f, u, v, z, d):
        L = self.L
        cu = min(u, L - u)
        if z < self.ZG:
            return FRAME_GREY
        k = vc(d)
        r = prow(d, z, self.ZG)
        top = 7 if k == "D" else 8
        # cab side window (in front of the door)
        if 0.66 <= cu <= 0.98 and top - 3 <= r <= top - 1:
            return WS
        dr = self.door(d, u, v, z, r, top)
        if dr is not None:
            return dr
        return getattr(self, "side_" + self.liv)(f, u, v, z, d, cu, r, top)

    def side_vectron(self, f, u, v, z, d, cu, r, top):
        # ELL 193.289-298: blue cab ends, white upper band with the slogan,
        # light-blue lower half with the Praha-Dresden-Berlin-Hamburg skyline
        if r >= top:
            return VEC_BLUE
        if cu < 1.02 and r >= 2:
            return VEC_BLUE
        white_lo = top - 3
        if r >= white_lo:
            p = self.logo.at(f, u, v, z, d, self.L)
            if p is not None:
                return p
            return WHITE
        # skyline in the light-blue band (the middle of the side)
        if 2.6 <= cu and r >= 1:
            c = math.floor(scr(d, u, v, z)[0]) // 3
            h = 1 + int(hsh(c) * 2.4)
            if r <= h:
                return VEC_SKYLINE
        return SKY

    def side_vectronrsl(self, f, u, v, z, d, cu, r, top):
        # RS Lease units: silver body, light-blue band along the roof edge,
        # blue cab top sweeping into a light-blue curve down the cab edge
        if r >= top:
            return VEC_BLUE if cu < 1.02 else SKY
        if cu < 1.02:
            if r >= top - 1:
                return VEC_BLUE
            if cu < 0.34 + 0.085 * r:
                return SKY
        p = self.logo.at(f, u, v, z, d, self.L)
        if p is not None:
            return p
        return VEC_SILVER

    def side_cd384(self, f, u, v, z, d, cu, r, top):
        L = self.L
        if r >= top - 1:
            return NAVY
        # navy sweep following the cab edge from the roof band to the nose
        t = r / max(1, top - 1)
        cc = 0.28 + 0.72 * t * t
        if cu < 1.2 and abs(cu - cc) < 0.16:
            return NAVY
        p = self.logo.at(f, u, v, z, d, L)
        if p is not None:
            return p
        # big ČD mark (outline) toward cab 2, over the speed lines
        s = u
        if 7.15 <= s <= 8.05 and 1 <= r <= top - 2:
            edge = (r in (1, top - 2) or on_col(d, u, v, z, 7.15, v) or on_col(d, u, v, z, 8.05, v))
            return NAVY if edge else W384
        # speed lines: every other row navy, starting further forward in the
        # middle rows, running on to the cab 2 end
        if 1 <= r <= top - 2 and r % 2 == 1:
            starts = [6.2, 5.0, 4.4, 4.8, 5.6, 6.4]
            st = starts[(r // 2) % len(starts)]
            if st <= s <= L - 0.30:
                return NAVY
        return W384

    # ---------------------------------------------------------------- fronts
    def front(self, f, u, v, z, d):
        """End face rows from ZG: 0-2 lower panel (headlights on 1), 3 band,
        4-6 windscreen, 7+ cab roof."""
        V = self.V
        W = V.W
        av = abs(v)
        if z < self.ZG:
            return FRAME_GREY
        r = prow(d, z, self.ZG)
        rear = f == "+u"
        liv = self.liv
        cap = NAVY if liv == "cd384" else VEC_BLUE
        if r >= 7:
            return cap
        if r >= 4:
            if av < W - 0.16:
                return WS_HI if r == 6 else WS
            return W384 if liv == "cd384" else cap
        if r == 3:
            if liv == "cd384":
                return NAVY if av < 0.12 else W384
            if liv == "vectronrsl":
                return SKY
            return VEC_BLUE if av > 0.2 else SKY
        sg = 1 if v > 0 else -1
        if av >= 0.64:
            if r == 1 and in_vcols(d, u, v, z, 0.68 * sg, 0.82 * sg):
                return R.TAIL if rear else R.HEAD
            return NAVY if liv == "cd384" else (FRAME_GREY if liv == "vectronrsl" else VEC_BLUE)
        wedge = 0.10 + 0.07 * r
        if liv != "cd384" and av < wedge:
            return SKY
        if 0.14 <= av and r in (0, 2):
            return W384 if liv == "cd384" else WHITE
        if liv == "cd384":
            return NAVY
        return FRAME_GREY if liv == "vectronrsl" else VEC_BLUE

    def build(self):
        V = self.V
        parts, lines = V.build("railpool")
        L = V.L
        cap = NAVY if self.liv == "cd384" else VEC_BLUE

        def body(f, u, v, z, d):
            if f == "+z" and z < V.ZS - 0.05:
                return self.front("-u" if u < L / 2 else "+u", u, v, z, d)
            if f == "+z":
                return cap if min(u, L - u) < V.UCAB else ROOF
            if f in ("+v", "-v"):
                return self.side(f, u, v, z, d)
            return self.front(f, u, v, z, d)

        def roof(f, u, v, z, d):
            cu = min(u, L - u)
            if cu < V.UCAB:
                return cap
            if f == "+z":
                return ROOF
            return GUTTER
        for p in parts:
            name = getattr(p.mat, "__name__", "")
            if name == "body_mat":
                p.mat = body
            elif name == "roof_mat":
                p.mat = roof
        parts = [p for p in parts if not (p.b[4] == 0.0 and abs(p.b[5] - V.ZB) < 1e-9
                                          and abs((p.b[1] - p.b[0]) - 2.5) < 1e-6)]
        for bc in (2.5, 7.5):
            parts += bogie(bc, 1.0, 0.76, V.W, V.ZB, "V")
        # snowploughs: the 384 has the split plough (two halves)
        for (a, b) in ((0.12, 0.40), (L - 0.40, L - 0.12)):
            if self.liv == "cd384":
                for (v0, v1) in ((-0.78, -0.10), (0.10, 0.78)):
                    parts.append(Part(a, b, v0, v1, 0.4, 1.6, lambda *x: Paint(0x8A9095), "V"))
            else:
                parts.append(Part(a, b, -0.78, 0.78, 0.4, 1.6, lambda *x: Paint(0x9AA0A5), "V"))
        return parts, panto_style(lines)


def panto_style(lines):
    """Agreed pantograph style: light arms 1 px, dark grey head bar 2 px."""
    out = []
    for (a, b, c, own, thick) in lines:
        head = a[2] == b[2] and a[1] != b[1]
        out.append((a, b, ST.PANTO_HEAD, own, True) if head else (a, b, ST.PANTO_ARM, own, False))
    return out


def vectron_row(liv):
    parts, lines = VectronCD(liv).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


# ================================================================== jobs
JOBS = {
    "193": [("vectron", lambda: [vectron_row("vectron")], ["193 ELL"]),
            ("vectronrsl", lambda: [vectron_row("vectronrsl")], ["193 RSL"])],
    "384": [("cd384", lambda: [vectron_row("cd384")], ["384"])],
}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for liv, make, labels in JOBS[fam]:
            rows = make()
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            ST.polish(Image.open(out), **ST.POLISH).save(out)   # agreed style post-process
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
