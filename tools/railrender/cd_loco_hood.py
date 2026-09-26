"""ČD hood diesel locomotives 714 and 743.2 as box models.

Same kit and scale as the RegioJet shunters (rj_shunters.py, whose geometry
helpers are imported): 1 model px = 0.375 m up, heights x 1.08 like the native
pak128.cs locomotives, u = cu behind the front buffer face, v = cu to the
right, z = model px above the rail head. Colours come from cd_loco_livery.py.

  714   ČKD T 444.1 rebuilt 1992-2000 (Caterpillar engine), 14.24 m over
        buffers, drawn at length 7 like the native CD_714. Low short hood with
        the black exhaust stack (leading), raised cab, long hood behind it;
        Bo'Bo'. Proportions from Commons photos of 714.006, 714.204, 714.217:
        short hood about 3.3 m, cab 2.4 m, long hood 6.6 m, hoods 3.2 m high,
        cab roof 4.25 m.
  743.2 CZ LOKO EffiShunter 1000M rebuild of the 742 (2022-2023), 13.6 m on
        the 742 frame, drawn at length 7 like the native CD_742. Short hood
        (leading), the new tall square CZ LOKO cab with big windows, long hood
        with a louvre band; Bo'Bo'. From Commons photos of 743.201-204, 210.

Liveries (Commons photos, 2014-2025):
  714 cervenomodra  1990s ČD scheme: red hood ends with a white V round the
                    radiator grille, the red wrapping a little onto the hood
                    sides, blue louvred hood sides, red cab and roof, light
                    grey frame with yellow lower buffer beam edges.
  714 najbrt1_2     light grey hood ends and frame corners, hood sides sky blue
                    over a sapphire trapezoid rising toward the cab (714.222),
                    sky cab with a sapphire top, grey frame and roof.
  714 / 743.2 najbrt2  sky upper body, a white stripe at lamp height round the
                    whole loco, sapphire lower body and frame, sapphire cab top
                    and roof, yellow lower beam edges (714.202, 743.204).

    python tools/railrender/cd_loco_hood.py [714|743_2 ...] [--preview DIR]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
import cd_loco_livery as C  # noqa: E402
from rj_shunters import (box, buffers, bogie, corner_steps, rail_lines,  # noqa: E402
                         posts_between, render_row, zm, WS, WS_HI)


def P(c, top=None):
    return Paint(c, top=top)


def lighter(c, f):
    return tuple(min(255, int(round(x * f))) for x in c)


SKY, SAPH, WHITE = P(C.LOCO_SKY), P(C.SAPPHIRE), P(C.WHITE)
LGREY = P(C.LGREY)
FRAME_DK = P(C.FRAME)
YEL = P(C.PLOUGH)
BOGIE_DK = Paint(0x2E3033)
LOUVRE_SKY = P(lighter(C.LOCO_SKY, 0.78))
LOUVRE_SAPH = P(lighter(C.SAPPHIRE, 0.72))
# N1.2 roof / sill as on the E99 family (coordinator, 2026-09-26)
N12_ROOF = (170, 175, 178)
N12_SILL = (58, 61, 64)
EXHAUST = Paint(0x232426, top=0x1A1B1C)
LOGO_DK = P(C.SAPPHIRE)

# 714 red-blue (1990s): colours read off the 714.006 / 714.217 photos
RB = dict(red=P(C.RB_RED), blue=Paint(0x2A4A9C), louvre=Paint(0x1E3570),
          frame=Paint(0xA9ADAE, top=0x9A9EA0), roof=P(lighter(C.RB_RED, 0.9)))


def _walk_rails(L, UB, UR, US1, UL0, zt, col, side_lines, ZW, WF):
    """handrails along the walkways beside both hoods and round the ends."""
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        ls = rail_lines(UL0 + 0.12, UR - 0.04, vv, ZW, zt, col, posts_between(UL0 + 0.12, UR - 0.04, 1.5))
        ls += rail_lines(UB + 0.04, US1 - 0.06, vv, ZW, zt, col, posts_between(UB + 0.04, US1 - 0.06, 1.5))
        side_lines.append((face, ls))
    for face, uu in (("-u", UB + 0.04), ("+u", UR - 0.04)):
        ls = []
        for s in (-1, 1):
            ls.append(((uu, s * (WF - 0.03), zt), (uu, s * 0.74, zt), col))
            ls.append(((uu, s * 0.74, ZW), (uu, s * 0.74, zt), col))
        side_lines.append((face, ls))


# ------------------------------------------------------------------ 714
def build_714(liv):
    L = 7.0
    M = L / 14.24                   # cu per metre along the track
    UB = 0.24
    UR = L - UB
    US0, US1 = UB + 0.55 * M, UB + 0.55 * M + 3.3 * M      # short hood (front)
    UC0, UC1 = US1, US1 + 2.4 * M                          # cab
    UL0, UL1 = UC1, UR - 0.55 * M                          # long hood
    ZFB, ZW = zm(0.95), zm(1.50)
    ZHS = zm(3.05)                  # hood side top
    ZHT = zm(3.25)                  # hood roof crown
    ZCS, ZCR = zm(4.00), zm(4.30)   # cab side top, cab roof
    ZST0, ZST1 = zm(2.15), zm(2.15) + 1.0     # N2 white stripe (lamp height)
    WF, WH, WC = 0.92, 0.64, 0.90
    WRAP = 0.36 * M                 # end colour wrapping onto the hood sides
    parts, side_lines = [], []

    if liv == "cervenomodra":
        frame_p, roof_p, cab_p, rail = RB["frame"], RB["roof"], RB["red"], 0xB9BDBF
    elif liv == "najbrt2":
        frame_p, roof_p, cab_p, rail = SAPH, Paint(C.SAPPHIRE, top=lighter(C.SAPPHIRE, 1.15)), SKY, 0xC9CED1
    else:                            # najbrt1_2
        frame_p = Paint(N12_SILL)
        roof_p, cab_p, rail = Paint(N12_ROOF), SKY, 0xC9CED1

    def n2_band(z):
        if z < ZST0:
            return SAPH
        if z < ZST1:
            return WHITE
        return SKY

    def side_col(u, z, u0, u1, outer_u):
        """hood side colour (without louvres) at u, z."""
        near_end = abs(u - outer_u) < WRAP
        if liv == "cervenomodra":
            return RB["red"] if near_end else RB["blue"]
        if liv == "najbrt2":
            return n2_band(z)
        # najbrt1_2: grey wrap at the outer end, sapphire trapezoid under sky
        if near_end:
            return LGREY
        t = (u - UB) / (UR - UB)          # 0 at the front, 1 at the rear
        ztop = ZW + (ZHS - ZW) * (0.15 + 0.65 * t)
        return SAPH if z < min(ZHS - 1.0, ztop) else SKY

    def end_face(v, z, top):
        """outer hood end: lamps, grille and the livery."""
        if abs(v) < 0.20 and top - 1.3 < z < top - 0.5:
            return R.HEAD                               # twin top headlights
        if abs(v) > WH - 0.20 and ZW + 1.4 < z < ZW + 2.1:
            return R.HEAD                               # lower lamps (white)
        if abs(v) > WH - 0.20 and ZW + 0.6 < z < ZW + 1.4:
            return Paint(0x8A1E22)                      # red tail lamp glass
        grille = abs(v) < 0.30 and ZW + 1.2 < z < top - 1.6
        if liv == "cervenomodra":
            if grille:
                return Paint(0x6E7274)
            # white V: widest at the top, point down at the centre
            s = abs(v) / WH
            t = (z - (ZW + 0.8)) / (top - 1.4 - (ZW + 0.8))
            if 0 < t < 1 and s < 0.25 + 0.75 * t and s > 0.20 * t:
                return WHITE
            return RB["red"]
        if liv == "najbrt2":
            if grille:
                return LOUVRE_SKY if z >= ZST1 else LOUVRE_SAPH
            return n2_band(z)
        if grille:
            return Paint(0xA6A9A6)
        return LGREY

    def hood_mat(u0, u1, front, top):
        outer_u = u0 if front else u1

        def m(f, u, v, z, d):
            if f == "+z":
                if liv == "cervenomodra":
                    return RB["red"] if abs(u - outer_u) < WRAP else RB["blue"]
                if liv == "najbrt2":
                    return SKY
                return LGREY if abs(u - outer_u) < WRAP else SKY
            if f in ("-u", "+u"):
                outer = (f == "-u" and front) or (f == "+u" and not front)
                if outer:
                    return end_face(v, z, top)
                return side_col(u0 + 0.5 if front else u1 - 0.5, z, u0, u1, outer_u)
            b = side_col(u, z, u0, u1, outer_u)
            # louvred doors: dark slots in two rows along the hood side
            if abs(u - outer_u) >= WRAP + 0.05 and ZW + 0.7 < z < top - 0.5 \
                    and not (liv == "najbrt2" and ZST0 - 0.3 < z < ZST1 + 0.3):
                rel = (u - u0) / 0.34
                if (rel % 1.0) < 0.28 and u0 + 0.12 < u < u1 - 0.12:
                    if liv == "cervenomodra":
                        return RB["louvre"] if b is RB["blue"] else b
                    if b is SKY:
                        return LOUVRE_SKY
                    if b is SAPH:
                        return LOUVRE_SAPH
            return b
        return m

    # frame and beams
    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, lambda f, u, v, z, d: frame_p))
    for (a, b) in ((UB, UB + 0.10), (UR - 0.10, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.50), ZFB,
                         lambda f, u, v, z, d: YEL if z < zm(0.66) else frame_p))
    buffers(L, zm(1.06), parts)
    for uc in (UB + 3.4 * M, UR - 3.4 * M):
        bogie(uc, parts, 2.4 * M, BOGIE_DK)
    parts.append(box(UC0 - 0.2, UC1 + 0.9, -0.66, 0.66, zm(0.50), ZFB, Paint(0x3A3C3F, top=0x44474A)))
    # hoods
    parts.append(box(US0, US1, -WH, WH, ZW, ZHS, hood_mat(US0, US1, True, ZHS)))
    parts.append(box(UL0, UL1, -WH, WH, ZW, ZHS, hood_mat(UL0, UL1, False, ZHS)))
    for (a, b, fr) in ((US0, US1, True), (UL0, UL1, False)):
        mat = hood_mat(a, b, fr, ZHS)
        parts.append(box(a + 0.04, b - 0.04, -WH + 0.10, WH - 0.10, ZHS, ZHT,
                         lambda f, u, v, z, d, _m=mat: _m("+z", u, v, z, d)))
    # exhaust stack on the short hood next to the cab, above the cab roof
    parts.append(box(US1 - 0.34, US1 - 0.14, -0.13, 0.13, ZHT, ZCR + 0.9, EXHAUST))

    # cab
    ZWIN0 = ZHS + 0.2

    def cab_mat(f, u, v, z, d):
        if f == "+z":
            return roof_p
        win = ZWIN0 <= z <= ZCS - 0.45
        top_band = z > ZCS - 1.0
        if liv != "cervenomodra" and top_band:
            return SAPH                              # dark cab top (N1.2 / N2)
        if f in ("+v", "-v"):
            cu = (u - UC0) / (UC1 - UC0)
            if win and (0.10 <= cu <= 0.42 or 0.55 <= cu <= 0.90):
                return WS_HI if z > ZCS - 1.4 else WS
            if liv == "najbrt2":
                if ZST0 <= z < ZST1:
                    return WHITE
                if z < ZST0:
                    return SAPH
                if 0.52 < cu < 0.86 and ZST1 + 0.6 <= z < ZST1 + 1.6:
                    return LOGO_DK                       # ČD logo
            if liv == "najbrt1_2" and z < ZW + 1.4:
                return SAPH
            return cab_p
        if win and abs(v) < WC - 0.10 and abs(v) > 0.06:
            return WS_HI if z > ZCS - 1.4 else WS    # front / rear windscreens
        if liv == "najbrt2":
            return n2_band(z)
        return cab_p
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZCS, cab_mat))
    parts.append(box(UC0 - 0.05, UC1 + 0.05, -WC - 0.02, WC + 0.02, ZCS, ZCS + 0.4,
                     lambda f, u, v, z, d: roof_p))
    parts.append(box(UC0 + 0.06, UC1 - 0.06, -WC + 0.22, WC - 0.22, ZCS + 0.4, ZCR,
                     lambda f, u, v, z, d: roof_p))
    parts.append(box(UC0 + 0.35, UC0 + 0.45, -0.22, 0.22, ZCR, ZCR + 0.5, EXHAUST))   # horns

    corner_steps(UB, UR, zm(0.35), ZFB, parts, frame_p, YEL)
    _walk_rails(L, UB, UR, US1, UL0, ZW + 2.9, rail, side_lines, ZW, WF)
    return parts, side_lines


# ------------------------------------------------------------------ 743.2
def build_743_2(liv="najbrt2"):
    L = 7.0
    M = L / 13.6
    UB = 0.24
    UR = L - UB
    US0, US1 = UB + 0.45 * M, UB + 0.45 * M + 2.0 * M      # short hood (front)
    UC0, UC1 = US1, US1 + 2.7 * M                          # cab
    UL0, UL1 = UC1, UR - 0.45 * M                          # long hood
    ZFB, ZW = zm(0.95), zm(1.55)
    ZHS, ZHT = zm(3.15), zm(3.35)
    ZCS, ZCR = zm(4.20), zm(4.40)
    ZST0, ZST1 = zm(2.25), zm(2.25) + 1.0
    WF, WH, WC = 0.92, 0.66, 0.92
    parts, side_lines = [], []

    def band(z):
        if z < ZST0:
            return SAPH
        if z < ZST1:
            return WHITE
        return SKY

    def hood_mat(u0, u1, front, top):
        def m(f, u, v, z, d):
            if f == "+z":
                return Paint(C.LOCO_SKY, top=lighter(C.LOCO_SKY, 0.92))
            if f in ("-u", "+u"):
                outer = (f == "-u" and front) or (f == "+u" and not front)
                if outer:
                    if abs(v) < 0.18 and top - 1.2 < z < top - 0.5:
                        return R.HEAD
                    if abs(v) > WH - 0.22 and ZST0 - 0.2 < z < ZST1 + 0.6:
                        return R.HEAD                   # twin lamps at the stripe
                    if abs(v) > WH - 0.22 and ZW + 0.4 < z < ZST0 - 0.2:
                        return Paint(0x8A1E22)
                    if abs(v) < 0.24 and ZST1 + 0.5 < z < top - 1.6 and front:
                        return LOGO_DK                  # ČD logo on the nose
                return band(z)
            b = band(z)
            # long hood: a lighter louvre band high on the side
            if not front and ZST1 + 0.6 < z < top - 0.5 and u0 + 0.25 < u < u1 - 0.25:
                if ((u - u0) / 0.30) % 1.0 < 0.30:
                    return LOUVRE_SKY
            return b
        return m

    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, lambda f, u, v, z, d: SAPH))
    for (a, b) in ((UB, UB + 0.10), (UR - 0.10, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.50), ZFB,
                         lambda f, u, v, z, d: YEL if z < zm(0.68) else SAPH))
    buffers(L, zm(1.06), parts)
    for uc in (UB + 3.2 * M, UR - 3.2 * M):
        bogie(uc, parts, 2.4 * M, BOGIE_DK)
    parts.append(box(UC0 + 0.4, UL0 + 1.2, -0.68, 0.68, zm(0.50), ZFB, Paint(0x3A3C3F, top=0x44474A)))
    parts.append(box(US0, US1, -WH, WH, ZW, ZHS, hood_mat(US0, US1, True, ZHS)))
    parts.append(box(UL0, UL1, -WH, WH, ZW, ZHS, hood_mat(UL0, UL1, False, ZHS)))
    for (a, b) in ((US0, US1), (UL0, UL1)):
        parts.append(box(a + 0.04, b - 0.04, -WH + 0.12, WH - 0.12, ZHS, ZHT,
                         lambda f, u, v, z, d: Paint(C.LOCO_SKY, top=lighter(C.LOCO_SKY, 0.92))))
    # exhaust silencer box on the long hood, near its cab end
    parts.append(box(UL0 + 0.35, UL0 + 0.75, -0.24, 0.24, ZHT, ZHT + 0.9, Paint(0x5A6066, top=0x4A5055)))

    ZWIN0 = ZHS + 0.1
    CAB_TOP = SAPH

    def cab_mat(f, u, v, z, d):
        if f == "+z":
            return Paint(C.SAPPHIRE, top=lighter(C.SAPPHIRE, 1.2))
        win = ZWIN0 <= z <= ZCS - 0.4
        if f in ("+v", "-v"):
            cu = (u - UC0) / (UC1 - UC0)
            if win and (0.08 <= cu <= 0.30 or 0.40 <= cu <= 0.92):
                return WS_HI if z > ZCS - 1.3 else WS
            if z > ZCS - 1.0:
                return CAB_TOP
            if 0.45 < cu < 0.85 and ZST1 + 0.3 <= z < ZWIN0 - 0.2:
                return WHITE                             # "České dráhy" lettering
            return band(z)
        if win and abs(v) < WC - 0.08 and abs(v) > 0.05:
            return WS_HI if z > ZCS - 1.3 else WS
        if z > ZCS - 1.0 or z >= ZWIN0 - 0.4:
            return CAB_TOP                               # dark window surround
        return band(z)
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZCS, cab_mat))
    parts.append(box(UC0 - 0.06, UC1 + 0.06, -WC - 0.03, WC + 0.03, ZCS, ZCR,
                     lambda f, u, v, z, d: Paint(C.SAPPHIRE, top=lighter(C.SAPPHIRE, 1.2))))
    parts.append(box(UC0 + 0.30, UC0 + 0.42, -0.20, 0.20, ZCR, ZCR + 0.5, EXHAUST))    # horns

    corner_steps(UB, UR, zm(0.35), ZFB, parts, SAPH, YEL)
    _walk_rails(L, UB, UR, US1, UL0, ZW + 2.9, 0xC9CED1, side_lines, ZW, WF)
    return parts, side_lines


# ------------------------------------------------------------------ jobs
JOBS = {
    "714": [(liv, (lambda l=liv: [render_row(build_714(l))]), ["714"])
            for liv in ("cervenomodra", "najbrt2", "najbrt1_2")],
    "743_2": [("najbrt2", lambda: [render_row(build_743_2())], ["743.2"])],
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
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
