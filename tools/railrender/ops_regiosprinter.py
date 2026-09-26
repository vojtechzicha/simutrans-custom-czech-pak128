#!/usr/bin/env python3
"""RegioSprinter liveries of Die Laenderbahn CZ (654) and AZD Praha (818) on
the shared RegioSprinter box model (regiosprinter.py, the GWTR 818 geometry),
wrapped without editing it, like arriva_lint.py wraps lint.py.

    python tools/railrender/ops_regiosprinter.py                 # both families
    python tools/railrender/ops_regiosprinter.py 654             # one family dir
    python tools/railrender/ops_regiosprinter.py --preview DIR   # + 4x previews

  vehicle-rail/die-landerbahn-cz/654  livery vogtlandbahn   on the ex-Vogtlandbahn
        front (Scharfenberg coupler in a bag, no side buffers)
  vehicle-rail/azd-praha/818          livery svestkovadraha on the ex-Rurtalbahn
        front (side buffers, screw coupling)

Only the paint is new: EndModule / MidModule are subclassed with their own
front / side / top / mat; geometry comes from regiosprinter.parts().  Roof
equipment follows the photos: the DLB units have no roof AC housings (smooth
blue roof with small grilles, photos dlbcz_rs_1 / _4 / _8), the AZD units carry
green housings where the model has its AC boxes plus a light-grey box on each
cab roof (azd_rs_1 / _3 / _4 / _5).
Livery zones measured on the research photos (S/research/ops/photos/dlb, azd):
  vogtlandbahn   dlbcz_rs_4 (VT 44 broadside), _3 (VT 34 cab), _9 (VT 39 logos),
                 _1 (VT 42 roof)
  svestkovadraha azd_rs_4 (818 008 broadside), _3 (818 010), _1 (front),
                 _2 (roof), _6 (other side)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
from render import DIRS  # noqa: E402
import regiosprinter as RS  # noqa: E402

PX, W = RS.PX, RS.W
H_BAND_TOP = 2.80          # window tops: livery band above (to the cant)
PANEL_BAND = (0.86, 1.24)  # DLB yellow waist stripe / front lamp band (drawn 1 px)


# ------------------------------------------------------------------ liveries
def livery(name):
    if name == "vogtlandbahn":
        # Vogtlandbahn scheme kept by DLB CZ with DUK + DLB logos: leaf-green
        # body, ultramarine roof and band over the windows sweeping down both
        # front corners to the skirt, golden-yellow waist stripe from the corner
        # band to the door and across the front at lamp height, dark blue door
        # leaves, green cab roof front, green snowplough, dark coupler bag.
        green = Paint(0x5BB84A, top=0x6AC259)
        blue = Paint(0x22418F, top=0x3B5AA8)
        return dict(
            name=name, kind="vbg",
            body=green, pillar=blue, pillar_h=0.55, band=blue,
            roofside=blue, roofledge=Paint(0x22418F, top=0x2E4C9C), rooftop=blue,
            cabtop=Paint(0x5BB84A, top=0x68C056), cabfront=green,
            stripe=Paint(0xF0B81E), bandlamp=(0xD0, 0x4A, 0x1C),
            lowfront=green, skirt=Paint(0x54AE44, top=0x62BA52),
            door=Paint(0x28448A), doorframe=Paint(0x1D3264), doorsplit=Paint(0x16264C),
            doorpanel=Paint(0x28448A), grille=Paint(0x16306E),
            remap={id(RS.TURQ): Paint(0x54AE44, top=0x62BA52),
                   id(RS.BAG): Paint(0x2C3A30, top=0x36463A)},
            roof_ac=None)
    if name == "svestkovadraha":
        # DUK "Svestkova draha" (AZD): grass-green body and roof, lemon-yellow
        # band from the window tops over the cant on all modules, turning down
        # both front corners to the buffer beam; big navy disc with the lilac-
        # white script and a navy plum leaf behind each cab; glazed door leaves
        # with a navy lower panel (white DUK / AZD logos); green roof housings.
        green = Paint(0x3FA535, top=0x4DB041)
        yel = Paint(0xEEDD38, top=0xF0E24A)
        box = Paint(0x3A9E31, top=0x55B848)
        return dict(
            name=name, kind="rtb",
            body=green, pillar=yel, pillar_h=0.80, band=yel,
            roofside=yel, roofledge=Paint(0xEEDD38, top=0xE8D836),
            rooftop=Paint(0x3FA535, top=0x4CAF40),
            cabtop=Paint(0x3FA535, top=0x4CAF40), cabfront=green,
            stripe=None, bandlamp=None, lowfront=green, skirt=green,
            door=Paint(0x303236), doorframe=Paint(0x26282B), doorsplit=Paint(0x1E1F21),
            doorpanel=Paint(0x2B2F5A), navy=Paint(0x2B2F5A), script=Paint(0xC9C2E6),
            grille=None, remap={},
            roof_ac=(box, Paint(0x2C7F26)), cabbox=Paint(0xB8BCC0, top=0xC8CCD0))
    raise ValueError(name)


LIVERIES = {"vogtlandbahn": "vbg", "svestkovadraha": "rtb"}


def remapped(parts, remap):
    """Swap equipment colours of the shared parts (by object identity)."""
    if not remap:
        return parts
    for p in parts:
        orig = p.mat

        def mat(f, u, v, z, d, orig=orig):
            c = orig(f, u, v, z, d)
            return remap.get(id(c), c)
        p.mat = mat
    return parts


def returns(p, paints):
    """True if part p paints its top face with one of `paints` (AC housings)."""
    u0, u1, v0, v1, z0, z1 = p.b
    c = p.mat("+z", (u0 + u1) / 2, (v0 + v1) / 2, z1, "w")
    return any(c is q for q in paints)


def disc(m, h):
    """AZD navy disc behind the cab (1.6 m) -> None / 'disc' / 'script' / 'leaf'."""
    x, y = (m - 2.55) / 0.80, (h - 1.25) / 0.78
    if x * x + y * y <= 1.0:
        if abs(y - 0.12) < 0.13 and -0.55 < x < 0.50:
            return "script"                  # "Svestkova draha" (one line at 1x)
        return "disc"
    lx, ly = (m - 3.55) / 0.26, (h - 1.30) / 0.24
    if lx * lx + ly * ly <= 1.0:
        return "leaf"                        # plum leaf under the first window
    return None


# ------------------------------------------------------------------ end module
class OpsEnd(RS.EndModule):
    def __init__(self, kind, owner, dirn, lamp, liv):
        super().__init__(kind, owner, dirn, lamp)
        self.L = livery(liv)

    def front(self, m, vl, z):
        L = self.L
        h = z * PX
        av = abs(vl)
        hw = RS.front_hw(z)
        corner = av > hw - 0.21
        if h < 0.55:
            return L["skirt"] if L["kind"] == "vbg" else RS.BEAM
        if corner and h >= L["pillar_h"] and h < 3.10:
            return L["pillar"]                  # corner band down the A-pillar
        if h < 1.52:
            if L["stripe"] is not None and PANEL_BAND[0] <= h < PANEL_BAND[1]:
                if 0.50 <= av <= 0.78 and 0.95 <= h <= 1.17:
                    return L["bandlamp"]        # red / amber lamp units
                return L["stripe"]
            return L["lowfront"]
        if h <= 3.04 and av < hw - 0.20:
            if 0.46 <= av and h <= 2.00:
                return self.lamp                # lamps behind the windscreen corners
            if h >= 2.84:
                return RS.DISPLAY
            return RS.WS_HI if h > 2.55 else RS.WS
        return L["cabfront"]

    def side(self, m, z, f):
        L = self.L
        h = z * PX
        nm = RS.nose_m(z)
        if m < nm + 0.22:
            return self.front(m, W, z)          # rounded front corners
        if z > RS.ZC:                           # roof side
            if L["grille"] is not None and 5.3 <= m <= 5.95 and z < RS.ZC1:
                return L["grille"]              # roof air grille over the door
            return L["pillar"] if m < RS.M_CAB else L["roofside"]
        if m < nm + 0.45 and h >= L["pillar_h"]:
            return L["pillar"]                  # the corner band on the side
        # cab side window (plain glass), bottom rising aft
        if nm + 0.45 <= m <= RS.CABWIN[1]:
            hb = RS.H_CABWIN[0] + 0.30 * max(0.0, (m - 1.15) / (RS.CABWIN[1] - 1.15)) ** 2
            if hb <= h <= RS.H_CABWIN[1]:
                return RS.WS_HI if h > 2.62 else RS.WS
        # double door: framed leaves, tall glass, coloured lower panels
        a, b = RS.DOOR
        if a <= m <= b and RS.H_DOOR[0] <= h <= RS.H_DOOR[1]:
            t = (m - a) / (b - a)
            if t < 0.06 or t > 0.94 or h > RS.H_DOOR[1] - 0.10:
                return L["doorframe"]
            if 0.47 <= t <= 0.53:
                return L["doorsplit"]
            g0 = RS.H_DOORGLASS[0] if L["kind"] == "rtb" else 1.30
            if g0 <= h <= RS.H_DOORGLASS[1] and (0.12 <= t <= 0.42 or 0.58 <= t <= 0.88):
                return R.GLASS_HI if h > RS.H_DOORGLASS[1] - 0.22 else R.GLASS
            if h < g0:
                if L["kind"] == "rtb" and 0.62 <= t <= 0.84 and 0.62 <= h <= 0.92:
                    return (0xF2, 0xF4, 0xF6)   # white DUK / AZD logos
                return L["doorpanel"]
            return L["door"]
        # passenger windows
        if RS.WIN1[0] <= m <= RS.WIN1[1] and RS.H_WIN1[0] <= h <= RS.H_WIN1[1]:
            return R.GLASS_HI if h > RS.H_WIN1[1] - 0.22 else R.GLASS
        if RS.WIN2[0] <= m <= RS.WIN2[1] and RS.H_WIN[0] <= h <= RS.H_WIN[1]:
            return R.GLASS_HI if h > RS.H_WIN[1] - 0.22 else R.GLASS
        # livery
        if h >= H_BAND_TOP:
            return L["band"]
        if L["kind"] == "vbg":
            if PANEL_BAND[0] <= h < PANEL_BAND[1] and m < RS.DOOR[0] - 0.06:
                return L["stripe"]
            if 2.15 <= m <= 2.60 and 1.28 <= h <= 1.66:
                # DUK arrows mark: blue / yellow over red / green
                hi, fr = h > 1.47, m < 2.37
                return Paint((0x2A6AC8 if fr else 0xF2C21A) if hi else (0xE2342A if fr else 0x39A935))
            if h < RS.Z_BOT * PX + 0.02 and m < RS.SKIRT_END:
                return L["skirt"]
            return L["body"]
        dk = disc(m, h)
        if dk == "script":
            return L["script"]
        if dk is not None:
            return L["navy"]
        return L["body"]

    def top(self, m, vl, z):
        L = self.L
        if m < RS.M_CAB and z < RS.ZR - 0.05:
            if z < RS.ZC or m < RS.nose_m(z) + 0.22:
                return self.front(m, vl, z)     # tops of the nose slabs
        if z < RS.ZC - 0.05:
            return L["body"]                    # skirt steps
        if z < RS.ZR - 0.1:
            return L["roofledge"]
        if L["kind"] == "vbg" and m < 1.75 and abs(vl) < W - RS.IN2 - 0.10:
            return L["cabtop"]                  # green top of the cab, blue sweeps aft
        return L["rooftop"]

    def mat(self, f, u, v, z, d):
        m = self.m_of(u)
        vl = v * self.dirn
        if f == "+z":
            return self.top(m, vl, z)
        if f in ("+v", "-v"):
            return self.side(m, z, f)
        if m < RS.M_CAB + 0.01:
            return self.front(m, vl, z)
        if z > RS.ZC:
            return self.L["roofside"]
        return RS.JOINT_END

    def parts(self):
        return remapped(super().parts(), self.L["remap"])

    def roof_parts(self):
        L = self.L
        P = []
        if L["roof_ac"] is not None:
            body, grille = L["roof_ac"]

            def ac(f, u, v, z, d):
                if f in ("+v", "-v") and RS.ZR + 0.25 < z < RS.ZR + 0.75 and (self.m_of(u) * 1.4) % 1.0 < 0.5:
                    return grille
                return body
            # roof housings where the shared model has its AC box
            P.append(self.box(5.5, 8.9, -0.62, 0.62, RS.ZR - 0.05, RS.ZR + 0.95, ac))
            # light-grey box on the cab roof front
            cb = L["cabbox"]
            P.append(self.box(1.05, 1.65, -0.42, 0.42, RS.ZR - 0.10, RS.ZR + 0.45, lambda *a: cb))
        # engine exhaust behind the cab, horn fin on the cab roof (shared model)
        P.append(self.box(2.45, 2.85, -0.34, -0.06, RS.ZR - 0.05, RS.ZR + 0.85, lambda *a: RS.EXHAUST))
        P.append(self.box(1.00, 1.30, 0.12, 0.26, RS.ZR - 0.05, RS.ZR + 0.70, lambda *a: RS.FIN))
        return P


# ------------------------------------------------------------------ middle module
class OpsMid(RS.MidModule):
    def __init__(self, kind, owner, liv):
        super().__init__(kind, owner)
        self.L = livery(liv)

    def side(self, a, z):
        L = self.L
        h = z * PX
        if z > RS.ZC:
            return L["roofside"]
        if RS.MID_WIN[0] <= a <= RS.MID_WIN[1] and RS.H_WIN[0] <= h <= RS.H_WIN[1]:
            if abs(a - (RS.MID_WIN[0] + RS.MID_WIN[1]) / 2) < 0.04:
                return RS.DOORFRAME             # thin mullion
            return R.GLASS_HI if h > RS.H_WIN[1] - 0.22 else R.GLASS
        if h >= H_BAND_TOP:
            return L["band"]
        return L["body"]

    def mat(self, f, u, v, z, d):
        a = u * RS.M - RS.S_MID0
        if f == "+z":
            if z > RS.ZR - 0.1:
                return self.L["rooftop"]
            if z > RS.ZC - 0.05:
                return self.L["roofledge"]
            return self.L["body"]
        if f in ("+v", "-v"):
            return self.side(a, z)
        return RS.JOINT_END

    def parts(self):
        P = super().parts()
        if self.L["roof_ac"] is None:
            return [p for p in P if not returns(p, (RS.AC_VBG, RS.AC_RTB))]
        body = self.L["roof_ac"][0]
        return remapped(P, {id(RS.AC_VBG): body, id(RS.AC_RTB): body})


# ------------------------------------------------------------------ the car
def car(liv):
    kind = LIVERIES[liv]
    A = OpsEnd(kind, "A", +1, R.HEAD, liv)
    B = OpsEnd(kind, "A", -1, R.TAIL, liv)
    Mm = OpsMid(kind, "A", liv)
    parts = A.parts() + A.roof_parts() + Mm.parts() + B.parts() + B.roof_parts()
    return parts, []


def rows_for(liv):
    """One row: the whole RegioSprinter (one Simutrans vehicle, length 12)."""
    parts, lines = car(liv)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"A"}) for d in DIRS]]


# family dir -> [(livery, preview labels)]
FAMILIES = {
    "die-landerbahn-cz/654": [("vogtlandbahn", ["654"])],
    "azd-praha/818": [("svestkovadraha", ["818"])],
}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    want = [a.strip("/\\").replace("\\", "/") for a in args]
    todo = [f for f in FAMILIES if not want or any(f.endswith(w) for w in want)]
    for fam in todo:
        for liv, labels in FAMILIES[fam]:
            rows = rows_for(liv)
            out = os.path.join(REPO, "vehicle-rail", *fam.split("/"), "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam.split('/')[-1]}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
