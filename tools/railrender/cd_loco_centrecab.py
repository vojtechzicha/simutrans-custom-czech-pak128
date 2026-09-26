#!/usr/bin/env python3
"""ČD centre-cab electric shunters 111, 210 and 113 as box models.

    python tools/railrender/cd_loco_centrecab.py [family ...] [--preview DIR]

All three are Škoda hood units with a tower cab in the middle (ČSD E 458.1,
S 458.0 and E 426.0): 14.4 m over buffers, Bo'Bo', a low walkway frame with
end platforms, a hood each side of the cab, one pantograph on the cab roof.
Drawn at length 7 (14.4 m at 26.4 m = 13 cu is 7.1 cu), like the RegioJet 730
and 740 hood units; the natives CD_111 / CD_210 / CD_113 use length 8 with a
~6.7 cu body, which left a gap to the next vehicle.

Scale, heights and the depth-tested handrail lines come from rj_shunters.py
(imported, not edited): 1 model px = 0.375 m, locomotive heights x 1.08.

Classes (photos: Commons categories "CZ Class 111 of ČD in Najbrt livery",
"CZ Class 210 of ČD", "CZ Class 113", 2019-2024):
  111  E 458.1 (Škoda 78E, 1981), 3 kV DC. Flat-topped hoods with vertical
       louvre panels, square tower cab, walkway handrails, yellow ploughs.
  210  S 458.0 (Škoda 51E, 1972), 25 kV AC. The same body family with a taller
       cab roof box (the AC roof gear sits on the cab) and grilles along the
       hood tops.
  113  E 426.0 (Škoda 45E?, 1973), 1.5 kV DC Tábor - Bechyně. Hood ends
       chamfered at the top (sloped front plates with the headlights), a lower
       cab roof.

Liveries (colours from cd_loco_livery.py):
  najbrt2         SKY hoods and cab, a WHITE stripe round hoods and cab at the
                  lamp line, SAPPHIRE frame (solebar) with the white ČD logo,
                  UMBRA-grey cab roof, yellow ploughs (111.006, 111.021; 210
                  at Vyšší Brod 2024).
  najbrt1_2       LGREY hoods and cab, a SAPPHIRE-over-SKY trapezoid on each
                  hood side rising toward the cab, light grey frame (111.019).
  modrokremova    ČD 1990s blue-cream: dark blue body, a cream stripe round
                  hoods and cab and a cream V on each hood end, cream cab top
                  (210.021 Plzeň, 210.023 Tišnov).
  cervenozluta    the same layout in red with yellow (210.059).
  oranzovokremova 113.001 factory scheme (since 2019): orange hoods and lower
                  cab, cream upper cab and cab roof, black frame with white
                  lettering (Commons "Loko113001").
  zelenokremova   113.002 / 113.003: green hoods and lower cab with a cream
                  stripe round the body and a cream V on the hood ends, cream
                  upper cab, dark brown-grey frame.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
import cd_loco_livery as CL  # noqa: E402
from rj_shunters import (zm, box, buffers, bogie, corner_steps, rail_lines,  # noqa: E402
                         posts_between, tile, lines_for_view, WS, WS_HI)
from render import DIRS  # noqa: E402

# colours only this file needs (not in cd_loco_livery.py)
ORANGE_113 = (232, 104, 44)      # 113.001 factory orange
GREEN_113 = (58, 128, 76)        # 113.002 / 003 mid green
FRAME_113G = (74, 70, 64)        # dark brown-grey frame of the green 113s
# (the N2 cab roof is light blue like the cab on these shunters, photos
#  111.006 / 111.021, not the blue-grey of the E99 family's main roof)
N12_ROOF = (170, 175, 178)       # N1.2 roof
N12_SILL = (58, 61, 64)          # N1.2 frame / sill
LOUVRE_K = 0.80                  # louvre panels: body colour x this

L = 7.0
MU = L / 14.4                    # cu per metre along the loco


def U(m):
    return m * MU


def dk(c, f):
    return tuple(max(0, min(255, int(round(x * f)))) for x in c)


def paint(c, top=None):
    return Paint(c, top=top if top is not None else dk(c, 1.04))


# ------------------------------------------------------------------ class geometry
GEOM = {
    # hood / cab positions in metres from the front buffer face
    "111": dict(hood0=1.35, cab0=5.85, cab1=8.55, hood1=13.05, zhood=3.00, zcab=4.10,
                zroof=4.35, chamfer=False, roofbox=False, grille=False),
    "210": dict(hood0=1.30, cab0=5.80, cab1=8.60, hood1=13.10, zhood=3.05, zcab=4.10,
                zroof=4.35, chamfer=False, roofbox=True, grille=True),
    "113": dict(hood0=1.40, cab0=5.95, cab1=8.45, hood1=13.00, zhood=2.95, zcab=4.00,
                zroof=4.22, chamfer=True, roofbox=False, grille=False),
}
ZFB = zm(0.95)          # frame bottom (solebar lower edge)
ZW = zm(1.55)           # walkway
ZSTR0, ZSTR1 = zm(2.25), zm(2.55)   # stripe (lamp line) on hoods and cab
ZWIN0 = zm(3.10)        # cab window bottom (above the hoods)
WF, WH, WC = 0.92, 0.66, 0.84


# ------------------------------------------------------------------ liveries
def livery(liv):
    """returns dict of zone paints + flags"""
    W = paint(CL.WHITE)
    if liv == "najbrt2":
        return dict(body=paint(CL.LOCO_SKY), stripe=W, frame=paint(CL.SAPPHIRE), cabtop=None,
                    roof=paint(CL.LOCO_SKY), vee=None, trap=None,
                    logo=W, plough=paint(CL.PLOUGH), beam=paint(CL.SAPPHIRE))
    if liv == "najbrt1_2":
        return dict(body=paint(CL.LGREY), stripe=None, frame=paint(N12_SILL), cabtop=None,
                    roof=paint(N12_ROOF), vee=None,
                    trap=(paint(CL.SAPPHIRE), paint(CL.LOCO_SKY)), logo=paint(CL.WHITE),
                    plough=paint(CL.PLOUGH), beam=paint(N12_SILL))
    if liv == "modrokremova":
        cr = paint(CL.BC_CREAM)
        return dict(body=paint(CL.BC_BLUE), stripe=cr, frame=paint(CL.FRAME), cabtop=cr,
                    roof=paint(dk(CL.BC_CREAM, 0.80)), vee=cr, trap=None, logo=cr,
                    plough=paint(CL.PLOUGH), beam=paint(CL.FRAME))
    if liv == "cervenozluta":
        y = paint(CL.RY_YELLOW)
        return dict(body=paint(CL.RY_RED), stripe=y, frame=paint((84, 86, 88)), cabtop=y,
                    roof=paint((150, 150, 146)), vee=y, trap=None, logo=paint(CL.WHITE),
                    plough=paint(CL.PLOUGH), beam=paint(CL.FRAME))
    if liv == "oranzovokremova":
        cr = paint(CL.RC_CREAM)
        return dict(body=paint(ORANGE_113), stripe=None, frame=paint(CL.FRAME), cabtop=cr,
                    roof=paint(dk(CL.RC_CREAM, 0.92)), vee=None, trap=None, logo=paint(CL.WHITE),
                    plough=paint(CL.PLOUGH), beam=paint(CL.FRAME))
    if liv == "zelenokremova":
        cr = paint(CL.RC_CREAM)
        return dict(body=paint(GREEN_113), stripe=cr, frame=paint(FRAME_113G), cabtop=cr,
                    roof=paint(dk(CL.RC_CREAM, 0.88)), vee=cr, trap=None, logo=paint(CL.WHITE),
                    plough=paint(CL.PLOUGH), beam=paint(FRAME_113G))
    raise KeyError(liv)


def louvred(p):
    return Paint(dk(p.base, LOUVRE_K), top=p.topc)


# ------------------------------------------------------------------ model
def build(cls, liv):
    G = GEOM[cls]
    C = livery(liv)
    UB, UR = 0.30, L - 0.30
    H0, C0, C1, H1 = U(G["hood0"]), U(G["cab0"]), U(G["cab1"]), U(G["hood1"])
    ZH, ZCS, ZCR = zm(G["zhood"]), zm(G["zcab"]), zm(G["zroof"])
    body, stripe = C["body"], C["stripe"]
    LV = louvred(body)
    parts, side_lines = [], []

    def band(z):
        if stripe is not None and ZSTR0 <= z < ZSTR1:
            return stripe
        return body

    # ---- frame: solebar (livery frame colour) with the logo, dark walkway
    def logo_at(u, z, face):
        # small ČD logo + "České dráhy" on the solebar behind the cab, both sides
        if C["logo"] is None or not (ZFB + 0.45 <= z <= ZW - 0.40):
            return None
        a, b = C1 + 0.35, C1 + 1.45
        if a <= u <= b:
            t = (u - a) / (b - a)
            if t < 0.22 or (0.30 < t and int(t * 18) % 2 == 0):
                return C["logo"]
        return None

    def frame_mat(f, u, v, z, d):
        if f == "+z":
            return Paint(0x3A3C3E)
        if f in ("+v", "-v"):
            lg = logo_at(u, z, f)
            if lg is not None:
                return lg
        return C["frame"]
    parts.append(box(UB, UR, -WF, WF, ZFB, ZW, frame_mat))
    # buffer beams: livery beam colour, yellow plough strip at the bottom
    for (a, b) in ((UB, UB + 0.10), (UR - 0.10, UR)):
        parts.append(box(a, b, -WF + 0.04, WF - 0.04, zm(0.30), ZW,
                         lambda f, u, v, z, d: C["plough"] if z < zm(0.62) else C["beam"]))
    buffers(L, zm(1.06), parts)
    for uc in (U(3.65), U(10.75)):
        bogie(uc, parts, U(2.6), Paint(0x2C2E30), W=0.80)
    parts.append(box(U(5.2), U(9.2), -0.66, 0.66, zm(0.55), ZFB, Paint(0x2A2C2E)))

    # ---- hoods
    def hood_mat(front):
        u_out = H0 if front else H1          # outer (end) face position
        u_in = C0 if front else C1

        def m(f, u, v, z, d):
            if f == "+z":
                if G["grille"] and abs(v) < 0.40 and abs(u - (u_out + u_in) / 2) < abs(u_in - u_out) / 2 - 0.25:
                    return Paint(dk(body.topc, 0.78))
                return body
            outer = (f == "-u" and front) or (f == "+u" and not front)
            if f in ("-u", "+u") and outer:
                if abs(v) > 0.18 and abs(v) < 0.46 and ZH - zm(0.55) < z < ZH - zm(0.25):
                    return R.HEAD               # twin headlights under the hood top
                if C["vee"] is not None and ZW + zm(0.30) < z < ZH - zm(0.62):
                    # V chevron: two slanting bands meeting low in the middle
                    zz = z - (ZW + zm(0.30))
                    if abs(abs(v) * 3.2 - zz * 0.55 - 0.35) < 0.40:
                        return C["vee"]
                return band(z)
            if f in ("+v", "-v"):
                if C["trap"] is not None:
                    tp = trapezoid(u, z, front)
                    if tp is not None:
                        return tp
                # vertical louvre panels along the hood (dark every other 0.16 cu)
                span = abs(u_in - u_out)
                t = (u - min(u_in, u_out)) / span
                if 0.08 < t < 0.92 and ZW + zm(0.25) < z < ZH - zm(0.20) and not (
                        stripe is not None and ZSTR0 - 0.3 <= z < ZSTR1 + 0.3):
                    if int(u / 0.16) % 3 == 0:
                        return LV
            return band(z)
        return m

    def trapezoid(u, z, front):
        # N1.2: SAPPHIRE trapezoid rising toward the cab, SKY strip on its
        # outer edge; measured from the hood's inner (cab) end
        sap, sky = C["trap"]
        u_in = C0 if front else C1
        dist = abs(u - u_in)                    # 0 at the cab
        h = (z - ZW) / (ZH - ZW)                # 0 at the walkway, 1 at the top
        if h < 0.02 or h > 0.98:
            return None
        edge = 1.95 - 1.00 * h                  # sloped outer edge
        if dist < edge - 0.26:
            return sap
        if dist < edge:
            return sky
        return None

    for front in (True, False):
        a, b = (H0, C0) if front else (C1, H1)
        if G["chamfer"]:
            # 113: the outer hood end slopes back at the top
            zc = ZH - zm(0.60)
            ua, ub = (a + 0.28, b) if front else (a, b - 0.28)
            parts.append(box(a, b, -WH, WH, ZW, zc, hood_mat(front)))
            for i in range(4):
                z0 = zc + (ZH - zc) * i / 4
                z1 = zc + (ZH - zc) * (i + 1) / 4
                k = (i + 1) / 4 * 0.28
                aa, bb = (a + k, b) if front else (a, b - k)
                parts.append(box(aa, bb, -WH, WH, z0, z1, hood_mat(front)))
        else:
            parts.append(box(a, b, -WH, WH, ZW, ZH, hood_mat(front)))

    # ---- tower cab
    cabtop = C["cabtop"]

    def cab_zone(z):
        if cabtop is not None and z >= ZWIN0 - zm(0.10):
            return cabtop
        return band(z)

    def cab_mat(f, u, v, z, d):
        if f == "+z":
            return C["roof"]
        cu = u - C0
        cl = C1 - C0
        if f in ("+v", "-v"):
            if ZWIN0 <= z <= ZCS - zm(0.22):
                # door window toward one end, a sliding window toward the other
                if 0.14 <= cu <= 0.40 or cl - 0.62 <= cu <= cl - 0.16:
                    return WS_HI if z > ZCS - zm(0.50) else WS
            if 0.10 <= cu <= 0.44 and ZW + 0.3 <= z < ZWIN0:
                return dk_paint(cab_zone(z), 0.88)      # door leaf
            return cab_zone(z)
        if ZH + 0.25 <= z <= ZCS - zm(0.22) and abs(v) < WC - 0.12 and abs(v) > 0.05:
            return WS_HI if z > ZCS - zm(0.55) else WS
        return cab_zone(z)
    parts.append(box(C0, C1, -WC, WC, ZW, ZCS, cab_mat))
    parts.append(box(C0 - 0.04, C1 + 0.04, -WC - 0.02, WC + 0.02, ZCS, ZCS + 0.35,
                     lambda f, u, v, z, d: C["roof"] if f == "+z" else (cabtop or body)))
    parts.append(box(C0 + 0.10, C1 - 0.10, -WC + 0.20, WC - 0.20, ZCS + 0.35, ZCR,
                     lambda f, u, v, z, d: C["roof"]))
    ztop = ZCR
    if G["roofbox"]:
        # 210: AC gear (main switch, insulators) on the cab roof
        parts.append(box(C0 + 0.25, C1 - 0.25, -0.40, 0.40, ZCR, ZCR + 0.55,
                         lambda f, u, v, z, d: Paint(0x6A6E70, top=0x7C8082)))
        ztop = ZCR + 0.55
    # pantograph base + arm (folded toward the rear)
    parts.append(box(C0 + 0.35, C1 - 0.35, -0.36, 0.36, ztop, ztop + 0.30,
                     lambda f, u, v, z, d: Paint(0x4A4E52)))
    pl = R.pantograph((C0 + C1) / 2 - 0.30, ztop + 0.30, "V", fold=+1, reach=0.75, height=4.4,
                      col=(0x70, 0x74, 0x78), head=(0x2A, 0x2A, 0x2C), half_head=0.55, thick=False)
    pan = [(a, b, col) for (a, b, col, own, th) in pl]

    # ---- steps and handrails
    corner_steps(UB, UR, zm(0.35), ZFB, parts, C["frame"], C["plough"])
    K = (0xE8, 0xE8, 0xE4) if liv.startswith("najbrt") else (0x2A, 0x2A, 0x2C)
    zt = ZW + zm(0.95)
    for s, face in ((1, "+v"), (-1, "-v")):
        vv = s * (WF - 0.03)
        ls = rail_lines(H0 + 0.05, C0 - 0.05, vv, ZW, zt, K, posts_between(H0 + 0.05, C0 - 0.05, 0.9))
        ls += rail_lines(C1 + 0.05, H1 - 0.05, vv, ZW, zt, K, posts_between(C1 + 0.05, H1 - 0.05, 0.9))
        side_lines.append((face, ls))
    for face, uu in (("-u", UB + 0.06), ("+u", UR - 0.06)):
        ls = []
        for s in (-1, 1):
            ls.append(((uu, s * (WF - 0.03), zt), (uu, s * 0.72, zt), K))
            ls.append(((uu, s * 0.72, ZW), (uu, s * 0.72, zt), K))
        side_lines.append((face, ls))
    return parts, side_lines, pan


def dk_paint(p, f):
    return Paint(dk(p.base, f), top=p.topc)


# ------------------------------------------------------------------ jobs
JOBS = {
    "111": ["najbrt2", "najbrt1_2"],
    "210": ["najbrt2", "modrokremova", "cervenozluta"],
    "113": ["oranzovokremova", "zelenokremova"],
}


def row(cls, liv):
    parts, side_lines, pan = build(cls, liv)
    return [tile(parts, lines_for_view(side_lines, d) + pan, d) for d in DIRS]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for liv in JOBS[fam]:
            rows = [row(fam, liv)]
            out = os.path.join(FAM, fam, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=[f"{fam} {liv}"])
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
