"""ČD two-axle shunters 704, 794 and 799 as box models.

Same scale and helpers as tools/railrender/rj_shunters.py (imported, not
copied): 26.4 m = 13 cu along the track, W_STD 0.92 cu = half of a 2.825 m
body across it, 1 model px = 0.375 m up, heights x 1.08 like the native
pak128.cs locomotives. u = cu behind the front buffer face, v = cu to the
right, z = model px above the rail head. All three are drawn at length 4, like
the RegioJet 703 (7.22 m) and the native CD_704 (4).

  704  ČKD T 238.0 (1988-94), 7.50 m, Bo. Long hood leading, cab off-centre
       towards the rear, short hood behind it; cab roof overhangs both cab
       ends. Proportions from Commons "Tabor (49509029913)" (704, side-on):
       long hood 0.08-3.27 m, cab 3.27-5.63 m, short hood 5.63-6.70 m from the
       front beam (beams 6.8 m apart), hood top 2.4 m, cab side 3.3 m, roof
       3.5 m, walkway 1.0 m.
  794  CZ LOKO (2015/2017-19), 7.94 m, Bo, Caterpillar C13 328 kW, 60 km/h.
       Long hood leading, raised end cab at the rear with a sun visor over
       the front windows; two red radiator guards on each hood side next to
       the cab. Commons "Lokomotiva 794 010 - 9 obr.02-08": hood 0.2-4.8 m,
       cab 4.8-7.3 m, hood top 2.9 m, cab roof 3.7 m, walkway 1.25 m.
  799  "Adéla" ADL (JLS / ČD 1992-97 on 700/701/702 frames), 7.24 m, B,
       hybrid: Zetor 37 kW diesel or a 84 V traction battery, 10 km/h. Low
       hoods both sides of a tall central cab, big overhanging roof. Commons
       Category:CZ Class 799 (Maloměřice, Ústí, Přerov).

Liveries (cd_loco_livery.py colours):
  704 cervenokremova  ČSD red-cream: red hoods and cab, a cream band at the
                      middle of the hood height round the whole loco, dark
                      grey frame, weathered red-grey roof (704.011, Tábor).
  704 najbrt2         704.014 (Ústí n. L. 2025): sapphire frame, hoods and
                      cab sky blue above a white band at walkway+0.4 m, the
                      cab window zone and roof sapphire, white louvre panels.
  704 najbrt1_2       inferred from the 362/754 N1.2: light grey body, a
                      sapphire-over-sky trapezoid on the long hood rising
                      towards the cab, grey frame and roof (no photo found).
  794 najbrt2         794.010: sapphire frame, hood side from the bottom
                      sapphire / white / sky / thin white / sapphire top edge,
                      the same bands on the cab, sapphire roof, red radiator
                      guards.
  799 oranzovomodra   orange hoods and cab, light-blue roof, cream upper
                      panel with the lamps on both hood ends, dark grey frame
                      with yellow-black chevrons on the beams.
  799 najbrt2         no photo found; painted like the 704 N2 (sapphire frame
                      and roof, sky body over a white band).

Headlights at both ends, cab glass plain (never the lit specials).

    python tools/railrender/cd_loco_shunter.py [704|794|799 ...] [--preview DIR]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
import rj_shunters as S  # noqa: E402
from rj_shunters import box, buffers, axle_wheels, corner_steps, render_row, rail_lines, \
    posts_between, zm, vm, WS, WS_HI  # noqa: E402
import cd_loco_livery as C  # noqa: E402

L = 4.0
UB = 0.22                   # buffer beam faces
UR = L - UB

# colours local to the shunters (reported to the parent session)
OB_ROOF = (84, 160, 222)    # 799 light-blue cab roof
OB_CREAM = (236, 226, 196)  # 799 hood-end lamp panels
CHEV_Y = (242, 194, 0)
CHEV_K = (34, 34, 36)
RADIATOR = (196, 48, 44)    # 794 red radiator guards
RC_ROOF = (122, 92, 88)     # 704 red-cream: weathered roof
DGREY = (58, 60, 63)        # dark grey frame (red-cream 704, 799 orange)
N12_ROOF = (170, 175, 178)  # N1.2 roof and sill as on the E99 family (362 / 162)
N12_SILL = (58, 61, 64)


def P(c, top=None):
    return Paint(c, top=top if top is not None else c)


def dk(c, f):
    return tuple(max(0, min(255, int(round(x * f)))) for x in c)


def um(m, span):
    """metres from the front beam -> u (beam faces UB..UR = `span` m)."""
    return UB + m * (UR - UB) / span


def chevrons(v, z, a=P(CHEV_Y), b=P(CHEV_K)):
    return a if int((abs(v) / 0.177 + z) / 2) % 2 == 0 else b


# ------------------------------------------------------------------ liveries
def livery_704(name):
    if name == "cervenokremova":
        red, cream = P(C.RC_RED, dk(C.RC_RED, 1.05)), P(C.RC_CREAM)
        return dict(frame=P(DGREY), roof=P(RC_ROOF, dk(RC_ROOF, 1.08)), end=None, hoodtop=red,
                    bands=[(zm(1.40), red), (zm(2.05), cream), (99, red)],
                    cab_bands=[(zm(1.40), red), (zm(2.05), cream), (99, red)],
                    win=red, louvre=P(dk(C.RC_RED, 0.72)), trap=None, logo=P(C.RC_RED))
    if name == "najbrt2":
        sky, white, sap = P(C.LOCO_SKY), P(C.WHITE), P(C.SAPPHIRE, dk(C.SAPPHIRE, 1.15))
        return dict(frame=sap, roof=sap, end=None, hoodtop=P(dk(C.LOCO_SKY, 0.9)),
                    bands=[(zm(1.35), white), (zm(1.62), white), (99, sky)],
                    cab_bands=[(zm(1.35), white), (zm(1.62), white), (zm(2.40), sky), (99, sap)],
                    win=sap, louvre=P(C.WHITE), trap=None, logo=P(C.WHITE))
    if name == "najbrt1_2":
        grey = P(C.LGREY)
        return dict(frame=P(N12_SILL), roof=P(N12_ROOF), end=None, hoodtop=P(N12_ROOF),
                    bands=[(99, grey)], cab_bands=[(99, grey)], win=P(C.LOCO_SKY),
                    louvre=P(dk(C.LGREY, 0.8)), trap=(P(C.SAPPHIRE), P(C.LOCO_SKY)), logo=P(C.SAPPHIRE))
    raise KeyError(name)


def band_at(bands, z):
    for top, p in bands:
        if z < top:
            return p
    return bands[-1][1]


# ------------------------------------------------------------------ 704
def build_704(liv):
    K = livery_704(liv)
    span = 6.8
    UH0, UH1 = um(0.08, span), um(3.27, span)     # long hood (leading)
    UC0, UC1 = UH1, um(5.63, span)                # cab
    US0, US1 = UC1, um(6.70, span)                # short hood
    ZFB, ZW = zm(0.55), zm(1.00)
    ZHT = zm(2.40)                                # hood top
    ZCS, ZCR = zm(3.30), zm(3.52)
    WF, WH, WC = 0.92, vm(1.18), vm(1.45)
    ZWIN0 = zm(2.20)
    parts, side_lines = [], []

    def trapezoid(u, z, side):
        """N1.2: sapphire over sky, rising from the hood bottom towards the cab."""
        if K["trap"] is None:
            return None
        t = (u - UH0) / (UH1 - UH0)
        if not 0.08 < t < 0.98:
            return None
        h = (z - ZW) / (ZHT - ZW)
        edge = 0.15 + 0.85 * (t - 0.08) / 0.9       # sloped front edge
        if h < edge * 0.75:
            return K["trap"][0]
        if h < edge * 0.75 + 0.18:
            return K["trap"][1]
        return None

    def hood(u0, u1, outer_face):
        def m(f, u, v, z, d):
            if f == "+z":
                return K["roof"] if K["trap"] is None and liv != "najbrt2" else \
                    (K["frame"] if liv == "najbrt2" else K["roof"])
            if f in ("-u", "+u"):
                if f == outer_face:
                    if abs(v) < 0.12 and z > ZHT - 1.4 and z < ZHT - 0.5:
                        return R.HEAD
                    if 0.34 < abs(v) < 0.56 and ZW + 0.8 < z < ZW + 1.7:
                        return R.HEAD
                    if abs(v) < 0.26 and ZW + 2.2 < z < ZHT - 1.8:
                        return K["louvre"]
                return band_at(K["bands"], z)
            tp = trapezoid(u, z, f) if u1 <= UH1 + 1e-6 else None
            if tp is not None:
                return tp
            # louvred doors along the hood sides
            rel = (u - u0) / 0.42
            if u0 + 0.12 < u < u1 - 0.12 and (rel % 1.0) < 0.62 and \
                    band_at(K["bands"], z) is not band_at(K["bands"], ZW + 0.1) and \
                    ZW + 2.0 < z < ZHT - 0.7 and liv != "najbrt1_2":
                return K["louvre"] if liv == "cervenokremova" else band_at(K["bands"], z)
            if liv == "najbrt2" and u1 <= UH1 + 1e-6 and UH1 - 0.62 < u < UH1 - 0.30 and \
                    zm(1.75) < z < zm(2.05):
                return K["logo"]                     # white ČD logo near the cab
            if liv == "cervenokremova" and u1 <= UH1 + 1e-6 and UH1 - 0.62 < u < UH1 - 0.30 and \
                    zm(1.55) < z < zm(1.90):
                return K["logo"]
            return band_at(K["bands"], z)
        return m

    # frame, beams, buffers, wheels
    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, lambda f, u, v, z, d:
                     chevrons(v, z) if f in ("-u", "+u") else K["frame"]))
    for (a, b) in ((UB, UB + 0.12), (UR - 0.12, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.28), ZFB, lambda f, u, v, z, d:
                         chevrons(v, z) if f in ("-u", "+u") else K["frame"]))
    buffers(L, zm(1.03), parts)
    for a in (um(0.70, span), um(5.10, span)):
        axle_wheels(a, parts, 0.5, 0.80)
    parts.append(box(um(1.6, span), um(3.6, span), -0.66, 0.66, zm(0.35), ZFB, P(dk(C.FRAME, 1.2))))
    # hoods
    parts.append(box(UH0, UH1, -WH, WH, ZW, ZHT, hood(UH0, UH1, "-u")))
    parts.append(box(US0, US1, -WH, WH, ZW, ZHT, hood(US0, US1, "+u")))
    hroof = K["hoodtop"]
    for (a, b) in ((UH0, UH1), (US0, US1)):
        parts.append(box(a + 0.04, b - 0.02, -WH + 0.12, WH - 0.12, ZHT, ZHT + 0.35, hroof))
    parts.append(box(UH1 - 0.34, UH1 - 0.20, -0.12, 0.12, ZHT + 0.35, ZHT + 1.6, P((48, 50, 52))))

    # cab
    def cab(f, u, v, z, d):
        if f == "+z":
            return K["roof"]
        base = band_at(K["cab_bands"], z)
        if z >= ZWIN0:
            base = K["win"] if liv != "cervenokremova" else base
        cu = (u - UC0) / (UC1 - UC0)
        if f in ("+v", "-v") and ZWIN0 + 0.4 <= z <= ZCS - 0.5:
            if 0.08 <= cu <= 0.28 or 0.40 <= cu <= 0.64 or 0.74 <= cu <= 0.94:
                return WS_HI if z > ZCS - 1.6 else WS
        if f in ("-u", "+u") and z >= ZHT + 0.3 and z <= ZCS - 0.5 and abs(v) < WC - 0.10:
            return WS_HI if z > ZCS - 1.6 else WS
        return base
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZCS, cab))
    parts.append(box(UC0 - 0.16, UC1 + 0.16, -WC - 0.04, WC + 0.04, ZCS, ZCS + 0.32, K["roof"]))
    parts.append(box(UC0 - 0.05, UC1 + 0.05, -WC + 0.14, WC - 0.14, ZCS + 0.32, ZCR + 0.2, K["roof"]))
    corner_steps(UB, UR, zm(0.25), ZFB, parts, K["frame"], P(CHEV_Y))

    rail = (0xE8, 0xEA, 0xEA) if liv != "cervenokremova" else (0xD8, 0xD8, 0xD4)
    zt = ZW + 3.0
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        side_lines.append((face, rail_lines(UB + 0.05, UH0 + 1.1, vv, ZW, zt, rail,
                                            posts_between(UB + 0.05, UH0 + 1.1, 0.55))))
    return parts, side_lines


# ------------------------------------------------------------------ 794
def build_794():
    span = 7.2
    sky, white, sap = P(C.LOCO_SKY), P(C.WHITE), P(C.SAPPHIRE, dk(C.SAPPHIRE, 1.15))
    UH0, UH1 = um(0.15, span), um(4.55, span)      # long hood (leading)
    UC0, UC1 = UH1, um(7.05, span)                 # raised end cab
    ZFB, ZW = zm(0.60), zm(1.25)
    ZHT = zm(2.90)
    ZCS, ZCR = zm(3.50), zm(3.72)
    WF, WH, WC = 0.92, vm(1.12), vm(1.45)
    bands = [(zm(1.50), sap), (zm(1.97), white), (zm(2.60), sky), (zm(2.80), white), (99, sap)]
    cab_bands = [(zm(1.50), sap), (zm(1.97), white), (zm(2.60), sky), (zm(2.80), white), (99, sky)]
    parts, side_lines = [], []

    def hood(f, u, v, z, d):
        if f == "+z":
            return sap
        if f == "-u":
            if abs(v) < 0.30 and zm(1.55) < z < zm(2.70):
                return P((40, 42, 46))               # big front grille
            if 0.42 < abs(v) < 0.60 and zm(1.95) < z < zm(2.30):
                return R.HEAD
            return band_at(bands, z)
        if f in ("+v", "-v"):
            if UH1 - 1.05 < u < UH1 - 0.18 and zm(1.55) < z < zm(2.70):
                return P(RADIATOR, dk(RADIATOR, 1.1))  # red radiator guards
            if UH1 - 1.50 < u < UH1 - 1.20 and zm(1.60) < z < zm(2.55):
                return P((70, 74, 80))               # louvre
        return band_at(bands, z)

    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, lambda f, u, v, z, d:
                     chevrons(v, z) if f in ("-u", "+u") else sap))
    for (a, b) in ((UB, UB + 0.12), (UR - 0.12, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.30), ZFB, lambda f, u, v, z, d:
                         chevrons(v, z) if f in ("-u", "+u") else sap))
    buffers(L, zm(1.05), parts)
    for a in (um(1.8, span), um(5.9, span)):
        axle_wheels(a, parts, 0.55, 0.80)
    parts.append(box(UH0, UH1, -WH, WH, ZW, ZHT, hood))
    parts.append(box(UH0 + 0.06, UH1, -WH + 0.10, WH - 0.10, ZHT, ZHT + 0.30, sap))
    parts.append(box(UH1 - 0.62, UH1 - 0.50, -0.10, 0.10, ZHT + 0.30, ZHT + 1.7, P((150, 154, 158))))

    def cab(f, u, v, z, d):
        if f == "+z":
            return sap
        cu = (u - UC0) / (UC1 - UC0)
        if f in ("+v", "-v") and zm(2.85) <= z <= ZCS - 0.5:
            if 0.10 <= cu <= 0.34 or 0.48 <= cu <= 0.70 or 0.76 <= cu <= 0.94:
                return WS_HI if z > ZCS - 1.6 else WS
            return sap if (cu < 0.10 or cu > 0.94) else sky
        if f in ("-u", "+u") and ZHT + 0.4 <= z <= ZCS - 0.5 and abs(v) < WC - 0.10:
            return WS_HI if z > ZCS - 1.6 else WS
        if f == "+u" and 0.40 < abs(v) < 0.60 and zm(1.95) < z < zm(2.30):
            return R.HEAD
        if f in ("+v", "-v") and 0.50 < cu < 0.85 and zm(2.10) < z < zm(2.45):
            return sap                                # ČD logo + lettering
        return band_at(cab_bands, z)
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZCS, cab))
    # flat roof with the sun visor over the front windows
    parts.append(box(UC0 - 0.34, UC1 + 0.06, -WC - 0.05, WC + 0.05, ZCS, ZCS + 0.30, sap))
    parts.append(box(UC0 - 0.02, UC1 - 0.02, -WC + 0.20, WC - 0.20, ZCS + 0.30, ZCR + 0.25, sap))
    corner_steps(UB, UR, zm(0.28), ZFB, parts, sap, P(CHEV_Y))

    rail = (0xE8, 0xEA, 0xEA)
    zt = ZW + 3.0
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        side_lines.append((face, rail_lines(UB + 0.05, UH1 - 0.05, vv, ZW, zt, rail,
                                            posts_between(UB + 0.05, UH1 - 0.05, 0.62))))
    return parts, side_lines


# ------------------------------------------------------------------ 799
def livery_799(name):
    if name == "oranzovomodra":
        o = P(C.OB_ORANGE, dk(C.OB_ORANGE, 1.05))
        return dict(frame=P(DGREY), roof=P(OB_ROOF, dk(OB_ROOF, 1.05)), hoodtop=o,
                    bands=[(99, o)], end=P(OB_CREAM), cabwin=o)
    if name == "najbrt2":
        sky, white, sap = P(C.LOCO_SKY), P(C.WHITE), P(C.SAPPHIRE, dk(C.SAPPHIRE, 1.15))
        return dict(frame=sap, roof=sap, hoodtop=P(dk(C.LOCO_SKY, 0.9)),
                    bands=[(zm(1.30), white), (99, sky)], end=None, cabwin=sky)
    raise KeyError(name)


def build_799(liv):
    K = livery_799(liv)
    span = 6.6
    UH0, UH1 = um(0.10, span), um(2.35, span)      # front hood
    UC0, UC1 = UH1, um(4.30, span)                 # central cab
    US0, US1 = UC1, um(6.50, span)                 # rear hood
    ZFB, ZW = zm(0.45), zm(1.00)
    ZHT = zm(2.00)
    ZCS, ZCR = zm(3.05), zm(3.25)
    WF, WH, WC = 0.92, vm(1.15), vm(1.30)
    parts, side_lines = [], []

    def hood(outer):
        def m(f, u, v, z, d):
            if f == "+z":
                return K["hoodtop"]
            if f == outer:
                if abs(v) < 0.14 and zm(1.70) < z < zm(1.90):
                    return R.HEAD
                if 0.30 < abs(v) < 0.56 and zm(1.35) < z < zm(1.65):
                    return R.HEAD
                if K["end"] is not None and z > zm(1.30):
                    return K["end"]
            return band_at(K["bands"], z)
        return m

    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, lambda f, u, v, z, d:
                     chevrons(v, z) if f in ("-u", "+u") else K["frame"]))
    for (a, b) in ((UB, UB + 0.12), (UR - 0.12, UR)):
        parts.append(box(a, b, -WF, WF, zm(0.22), ZFB, lambda f, u, v, z, d:
                         chevrons(v, z) if f in ("-u", "+u") else K["frame"]))
    buffers(L, zm(1.00), parts)
    for a in (um(1.25, span), um(5.35, span)):
        axle_wheels(a, parts, 0.45, 0.80)
    parts.append(box(UH0, UH1, -WH, WH, ZW, ZHT, hood("-u")))
    parts.append(box(US0, US1, -WH, WH, ZW, ZHT, hood("+u")))

    def cab(f, u, v, z, d):
        if f == "+z":
            return K["roof"]
        cu = (u - UC0) / (UC1 - UC0)
        if f in ("+v", "-v") and zm(2.20) <= z <= ZCS - 0.5:
            if 0.08 <= cu <= 0.40 or 0.56 <= cu <= 0.92:
                return WS_HI if z > ZCS - 1.6 else WS
            return K["cabwin"]
        if f in ("-u", "+u") and ZHT + 0.3 <= z <= ZCS - 0.5 and abs(v) < WC - 0.10:
            return WS_HI if z > ZCS - 1.6 else WS
        return band_at(K["bands"], z)
    parts.append(box(UC0, UC1, -WC, WC, ZW, ZCS, cab))
    # big overhanging roof
    parts.append(box(UC0 - 0.22, UC1 + 0.22, -WC - 0.10, WC + 0.10, ZCS, ZCS + 0.40, K["roof"]))
    corner_steps(UB, UR, zm(0.22), ZFB, parts, K["frame"], P(CHEV_Y))

    rail = (0xD8, 0xDA, 0xDA)
    zt = ZHT + 1.2
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        ls = rail_lines(UH0 + 0.3, UH1 - 0.1, vv, ZW, zt, rail, [UH0 + 0.3, UH1 - 0.1])
        ls += rail_lines(US0 + 0.1, US1 - 0.3, vv, ZW, zt, rail, [US0 + 0.1, US1 - 0.3])
        side_lines.append((face, ls))
    return parts, side_lines


# ------------------------------------------------------------------ jobs
def job(fn, *a):
    return lambda: [render_row(fn(*a))]


JOBS = {
    "704": [(liv, job(build_704, liv), ["704"]) for liv in ("cervenokremova", "najbrt2", "najbrt1_2")],
    "794": [("najbrt2", job(build_794), ["794"])],
    "799": [(liv, job(build_799, liv), ["799"]) for liv in ("oranzovomodra", "najbrt2")],
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
