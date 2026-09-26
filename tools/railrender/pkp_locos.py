"""PKP Intercity EP09 (Pafawag 104E) and EU07 (Pafawag/HCP 4E) box models.

Both are 3 kV DC Bo'Bo' locomotives that reach the Czech Republic only on the
border legs Chalupki / Zebrzydowice - Bohumin. Drawn at length 8 like every
16-17 m pak128.cs locomotive (CD 140/150/163/363, ZSSK 361).

u: 0 = front buffer face (cab 1), L = rear buffer face (cab 2).
v: lateral carunits (+v = right-hand side in the travel direction).
z: model px above rail (1 px = 0.375 m); locos are drawn ~1-2 px taller than
   the coaches like the natives (see vectron.py).
Real positions are metres from the nearer end (both locos are symmetric),
mapped to carunits with L / length.

Livery "intercity" = the current PKP Intercity loco scheme (vagonWEB
EP09-IC2 / EU07-IC2 drawings; photos EP09-008/017/027/047 Krakow 2024, EP09-013
Poznan 2025, EU07-092 Krakow 2023, EU07-302 / EU07-360 Poznan 2021):
  - silver-grey body, a thin royal-blue line along the top of the side;
  - royal-blue front face (from the lamp line to the roof), blue front corner
    strip up the cab side, blue lower half of the cab side;
  - a royal-blue band across the lower half of the side, solid at both ends,
    breaking up in halftone dots round a silver gap left of centre as seen
    (the same from either side) that carries the orange "iC" + blue outlined
    "C" logo and "PKP INTERCITY" in blue (the lettering is left out: at 1x it
    is noise; the band ends cleanly where its dots thin out to half);
  - thin silver line under the band, dark-grey frame, black bogies;
  - EU07: silver bar under the front windows, round lamps; EP09: raked
    windscreen. The small IC logo on the fronts is left out: at 1x it would
    be a single orange pixel that reads as a tail light.

Regenerate: python tools/railrender/pkp_locos.py [ep09|eu07 ...] [--preview DIR]
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "pkp-intercity")

L = 8.0
PX = 0.375


def zm(h):
    return h / PX


# ------------------------------------------------------------------ colours
SILVER = Paint(0xC6CACD, top=0xB6BABD)
BLUE = Paint(0x2B3F9C, top=0x33479F)
BLUE_TOP = Paint(0x2B3F9C)
FRAME = Paint(0x4A4C4E)
SKIRT = Paint(0x3E4042)
UNDER = Paint(0x26282A)
BOGIE = Paint(0x232425)
BOGIE_HI = Paint(0x3A3C3E)
ROOF = Paint(0x7C8084, top=0x8A8E92)
ROOF_DK = Paint(0x5E6266, top=0x6A6E72)
ROOFEQ = Paint(0x55595D, top=0x60646A)
LINE = Paint(0xD6D9DB)                  # thin silver-white line under the band
GRILLE = Paint(0x3C4046)
GRILLE_HI = Paint(0x565B62)
DOORLINE = Paint(0x8C9094)              # door leaf frame on silver
DOORLINE_B = Paint(0x1C2A70)            # door leaf frame on blue
HANDRAIL = Paint(0xE4E6E8)
BUFFER = Paint(0x2E3032)
WS = (0x2A, 0x34, 0x3D)                 # cab glass, plain (loco: never lit)
WS_HI = (0x4F, 0x62, 0x72)
WS_FRAME = (0x14, 0x16, 0x18)
ORANGE = (0xEE, 0x5A, 0x20)
LOGO_B = (0x24, 0x36, 0x8C)
PANTO = (0x8A, 0x2E, 0x26)              # red-brown pantograph frames (photos)
PANTO_HEAD = (0x2E, 0x2E, 0x30)
INSUL = (0x6E, 0x3A, 0x30)
PPC = {"ne": 5.66, "sw": 5.66, "w": 4.0, "e": 4.0, "n": 4.0, "s": 4.0, "nw": 2.83, "se": 2.83}

# ------------------------------------------------------------------ models
EP09 = dict(
    name="EP09", length=16.74, W=0.92 * 2.974 / 2.825,
    ZB=zm(1.20),          # body side bottom (frame bottom edge)
    ZSK=zm(1.80),         # top of the dark frame band
    ZL=zm(1.92),          # top of the thin silver line = bottom of the blue band
    ZBT=zm(2.86),         # top of the blue band
    ZS=11.4, ZR=12.2,     # cantrail / roof top (drawn like the Vectron)
    UB=0.28,              # buffer length
    nose="raked", UN=0.30, ZWIN=7.9, UWT=0.62,  # front face, windscreen foot, top recession
    front_win=[(-0.86, -0.06), (0.06, 0.86)],   # windscreen panes (v), z ZWIN+0.4 .. ZS-0.6
    lamps=[(-0.60, 5.9), (0.60, 5.9)],
    roof_lamp=True,
    cab_win=(1.15, 1.75, 8.3, 10.5),            # metres from end, z
    door=(1.95, 2.60),                          # metres from end
    grilles=[(4.05, 4.35), (6.05, 6.35), (8.22, 8.52)],   # metres from end (mirrored)
    smallwin=[],
    grille_z=(8.3, 10.6),
    bogies=(4.25, 12.49), bogie_half=1.45,
    pantos=[(3.4, "single", False), (13.3, "single", True)],   # metres from front, raised?
    roof_boxes=[(6.2, 7.8), (8.9, 10.5)],
    band=dict(solid0=0.20, fade0=0.30, logo=0.36, text=0.49, fade1=0.58, solid1=0.68),
    cab_len=2.65,       # metres from the end: cab section (blue lower half)
)
EU07 = dict(
    name="EU07", length=15.915, W=0.92 * 3.00 / 2.825,
    ZB=zm(1.22), ZSK=zm(1.80), ZL=zm(1.92), ZBT=zm(2.80),
    ZS=11.2, ZR=12.0,
    UB=0.30,
    nose="flat", UN=0.30, ZWIN=8.2, UWT=0.36,
    front_win=[(-0.86, -0.28), (-0.16, 0.16), (0.28, 0.86)],
    lamps=[(-0.62, 6.0), (0.62, 6.0)],
    roof_lamp=True,
    cab_win=(1.10, 1.60, 8.3, 10.3),
    door=(1.95, 2.65),
    grilles=[(3.95, 5.05), (6.50, 7.60)],
    smallwin=[(3.15, 3.45), (5.55, 5.80)],
    grille_z=(8.2, 10.4),
    bogies=(3.95, 11.965), bogie_half=1.40,
    pantos=[(3.3, "diamond", False), (12.6, "diamond", True)],
    roof_boxes=[(5.9, 10.0)],
    band=dict(solid0=0.20, fade0=0.32, logo=0.38, text=0.50, fade1=0.58, solid1=0.68),
    cab_len=2.75,
)
MODELS = {"ep09": EP09, "eu07": EU07}


def band_density(M, a):
    """blue density of the lower band at `a` = along / L as seen (0 = left)."""
    b = M["band"]
    if a < b["solid0"] or a >= b["solid1"]:
        return 1.0
    if a < b["fade0"]:
        return 1.0 - (a - b["solid0"]) / (b["fade0"] - b["solid0"])
    if a >= b["fade1"]:
        return (a - b["fade1"]) / (b["solid1"] - b["fade1"])
    return 0.0


# 4-row IC mark: orange "iC" + blue outlined "C"; "PKP INTERCITY" one row
IC_MARK = ["o.oo.bb",
           "..o..b.",
           "o.o..b.",
           "o.oo.bb"]


def glyph_at(bm, a, z, a0, z_top, cu, cz):
    i = int(np.floor((a - a0) / cu)); j = int(np.floor((z_top - z) / cz))
    if 0 <= j < len(bm) and 0 <= i < len(bm[0]):
        return bm[j][i]
    return "."


class Loco:
    def __init__(self, M):
        self.M = M
        self.W = M["W"]
        self.mpc = M["length"] / L          # metres per carunit

    def corner(self):
        """metres from the buffer face covered by the blue front corner strip"""
        return self.M["UN"] * self.mpc + 0.45

    def dm(self, u):
        """metres from the nearer end"""
        return min(u, L - u) * self.mpc

    # --------------------------------------------------------- side
    def side(self, f, u, v, z, d):
        M = self.M
        sgn = 1 if f == "+v" else -1
        dm = self.dm(u)
        along = (L - u) if sgn > 0 else u
        a = along / L
        cab = dm < M["cab_len"]
        # frame
        if z < M["ZSK"]:
            return SKIRT
        if z < M["ZL"]:
            return LINE
        # cab side window
        cw = M["cab_win"]
        if cw[0] <= dm <= cw[1] and cw[2] <= z <= cw[3]:
            return WS_HI if z > cw[3] - 0.7 else WS
        # door leaf with frame, handrails either side
        d0, d1 = M["door"]
        if d0 - 0.16 <= dm <= d1 + 0.16 and M["ZL"] <= z <= M["ZS"] - 0.9:
            if dm < d0 - 0.02 or dm > d1 + 0.02:
                return HANDRAIL if z < M["ZS"] - 1.8 else self.body_at(dm, a, z, u, d)
            if z > M["ZS"] - 1.3:
                return DOORLINE if not self.blue_at(dm, z) else DOORLINE_B
            if d0 + 0.14 <= dm <= d1 - 0.14 and cw[2] <= z <= cw[3] - 0.4:
                return WS                   # door window
            if dm < d0 + 0.07 or dm > d1 - 0.07:
                return DOORLINE if not self.blue_at(dm, z) else DOORLINE_B
            return self.body_at(dm, a, z, u, d)
        # machine-room grilles / small windows (upper silver part)
        gz = M["grille_z"]
        for (g0, g1) in M["grilles"]:
            if g0 <= dm <= g1 and gz[0] <= z <= gz[1]:
                return GRILLE_HI if (int(np.floor(z * 1.18 * 1.0)) % 2 == 0) else GRILLE
        for (g0, g1) in M["smallwin"]:
            if g0 <= dm <= g1 and gz[0] + 0.6 <= z <= gz[1] - 0.4:
                return WS
        # logo / text on the silver gap
        if not cab and M["ZL"] <= z <= M["ZBT"] + 0.9:
            cu = 1.0 / PPC.get(d, 5.66) * 0.98
            ch = glyph_at(IC_MARK, along, z, M["band"]["logo"] * L - 0.62, M["ZBT"] + 0.7, cu, 0.85)
            if ch == "o":
                return ORANGE
            if ch == "b":
                return LOGO_B
        return self.body_at(dm, a, z, u, d)

    def blue_at(self, dm, z):
        M = self.M
        if z > M["ZS"] - 0.75:
            return True
        if dm < self.corner():
            return z >= M["ZL"]
        if dm < M["cab_len"]:
            return M["ZL"] <= z <= M["ZBT"]
        return False

    def body_at(self, dm, a, z, u, d):
        M = self.M
        if z > M["ZS"] - 0.75:
            return BLUE_TOP                   # top line, whole length
        if dm < self.corner() and z >= M["ZL"]:
            return BLUE                       # front corner strip up to the roof
        if M["ZL"] <= z <= M["ZBT"]:
            if dm < M["cab_len"]:
                return BLUE
            # the real band dissolves into halftone dots round the logo gap; at
            # 1x a dither reads as noise, so the band ends where the dots thin
            # out to half (2026-09-26 style: no 1-px noise)
            return BLUE if band_density(M, a) >= 0.5 else SILVER
        return SILVER

    # --------------------------------------------------------- ends
    def front_face(self, f, u, v, z, d, rear):
        M = self.M
        av = abs(v)
        if z < M["ZSK"]:
            return SKIRT
        for (lv, lz) in M["lamps"]:
            if abs(v - lv) < 0.17 and abs(z - lz) < 0.6:
                return R.TAIL if rear else R.HEAD
        if z < M["ZL"] + 0.2:
            return LINE
        zw0, zw1 = M["ZWIN"], M["ZS"] - 0.55
        for (v0, v1) in M["front_win"]:
            if v0 <= v <= v1 and zw0 <= z <= zw1:
                if v0 + 0.07 <= v <= v1 - 0.07 and z <= zw1 - 0.3:
                    return WS_HI if z > zw1 - 1.0 else WS
                return WS_FRAME
        if M["name"] == "EU07" and zw0 - 0.8 <= z < zw0 - 0.1:
            vv = -v if rear else v
            if -0.9 <= vv <= 0.05:
                return SILVER                 # silver bar under the windows
        return BLUE

    # --------------------------------------------------------- material
    def mat(self, f, u, v, z, d):
        M = self.M
        rear = u > L / 2
        if f in ("+v", "-v"):
            return self.side(f, u, v, z, d)
        if f == "-u":
            return self.front_face(f, u, v, z, d, False)
        if f == "+u":
            return self.front_face(f, u, v, z, d, True)
        # +z: tops of the raked windscreen slabs belong to the front
        cu = min(u, L - u)
        if z < M["ZS"] - 0.05 and cu < M["UWT"] + 0.01:
            return self.front_face(f, u, v, z, d, rear)
        if z < M["ZS"] + 0.05:
            return BLUE_TOP                   # the thin top line seen from above
        return ROOF

    # --------------------------------------------------------- geometry
    def build(self):
        M = self.M
        W = self.W
        own = "V"
        parts, lines = [], []
        mat = self.mat
        UN, UWT = M["UN"], M["UWT"]
        zw = M["ZWIN"]

        def nose_u(z):
            if M["nose"] == "flat" or z < zw - 0.3:
                return UN
            t = min(1.0, (z - (zw - 0.3)) / (M["ZS"] - (zw - 0.3)))
            return UN + (UWT - UN) * t

        # main body
        parts.append(Part(UWT, L - UWT, -W, W, M["ZB"], M["ZS"], mat, own))
        for z0 in np.arange(M["ZB"], M["ZS"] - 1e-6, 0.4):
            z1 = min(M["ZS"], z0 + 0.4)
            uf = nose_u((z0 + z1) / 2)
            if uf >= UWT - 1e-6:
                continue
            # chamfered front corners (EP09 more than EU07)
            tap = 0.10 if M["nose"] == "raked" else 0.05
            parts.append(Part(uf, UWT, -W + tap, W - tap, z0, z1, mat, own))
            parts.append(Part(L - UWT, L - uf, -W + tap, W - tap, z0, z1, mat, own))
            parts.append(Part(uf + 0.10, UWT, -W, W, z0, z1, mat, own))
            parts.append(Part(L - UWT, L - uf - 0.10, -W, W, z0, z1, mat, own))
        # roof: rounded cantrail (inset step) + cap
        def roof_mat(f, u, v, z, d):
            if f == "+z":
                return ROOF
            return ROOF_DK
        parts.append(Part(UWT + 0.04, L - UWT - 0.04, -W + 0.14, W - 0.14, M["ZS"], M["ZS"] + 0.45, roof_mat, own))
        parts.append(Part(UWT + 0.20, L - UWT - 0.20, -W + 0.36, W - 0.36, M["ZS"] + 0.45, M["ZR"], roof_mat, own))
        # roof lamp boxes at both ends
        if M["roof_lamp"]:
            for (a, b, rear) in ((UWT - 0.04, UWT + 0.30, False), (L - UWT - 0.30, L - UWT + 0.04, True)):
                def lamp_mat(f, u, v, z, d, rear=rear):
                    if (f == "-u" and not rear) and abs(v) < 0.13 and z > M["ZS"] + 0.3:
                        return R.HEAD
                    if f == "+u" and rear and abs(v) < 0.13 and z > M["ZS"] + 0.3:
                        return (0x55, 0x2A, 0x26)          # rear roof lamp: off
                    return ROOF_DK
                parts.append(Part(a, b, -0.22, 0.22, M["ZS"], M["ZS"] + 1.1, lamp_mat, own))
        # roof equipment boxes
        for (m0, m1) in M["roof_boxes"]:
            u0, u1 = m0 / self.mpc, m1 / self.mpc
            parts.append(Part(u0, u1, -0.42, 0.42, M["ZR"], M["ZR"] + 0.7, lambda *a: ROOFEQ, own))
        # frame / underframe
        parts.append(Part(UN + 0.05, L - UN - 0.05, -W + 0.06, W - 0.06, M["ZB"] - 0.6, M["ZB"],
                          lambda *a: FRAME, own))
        for bm in M["bogies"]:
            bc = bm / self.mpc
            hb = M["bogie_half"] / self.mpc
            parts.append(Part(bc - hb, bc + hb, -W + 0.12, W - 0.12, 0.0, M["ZB"] - 0.6,
                              lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.3 < z < 2.0) else BOGIE, own))
        b0 = M["bogies"][0] / self.mpc + M["bogie_half"] / self.mpc
        b1 = M["bogies"][1] / self.mpc - M["bogie_half"] / self.mpc
        parts.append(Part(b0, b1, -W + 0.25, W - 0.25, 1.0, M["ZB"] - 0.6, lambda *a: UNDER, own))
        # buffer beams + buffers
        for (a, b) in ((M["UB"], UN + 0.06), (L - UN - 0.06, L - M["UB"])):
            parts.append(Part(a, b, -W + 0.04, W - 0.04, 1.4, M["ZB"] + 0.2, lambda *a: SKIRT, own))
        for (a, b) in ((0.0, M["UB"]), (L - M["UB"], L)):
            for vc in (-0.62, 0.62):
                parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.2, 2.9, lambda *a: BUFFER, own))
        # pantographs
        zr = M["ZR"]
        for (pm, kind, up) in M["pantos"]:
            uc = pm / self.mpc
            # base frame (flat red-brown box)
            parts.append(Part(uc - 0.42, uc + 0.42, -0.40, 0.40, zr, zr + 0.35,
                              lambda *a: Paint(0x6E2E28), own))
            if kind == "single":
                if up:
                    lines += R.pantograph(uc - 0.30, zr + 0.35, own, fold=+1, reach=0.85, height=5.0,
                                          col=PANTO, head=PANTO_HEAD, half_head=0.62, thick=False)
                else:
                    lines += [((uc - 0.35, 0.0, zr + 0.55), (uc + 0.45, 0.0, zr + 0.75), PANTO, own, False),
                              ((uc + 0.45, -0.55, zr + 0.8), (uc + 0.45, 0.55, zr + 0.8), PANTO_HEAD, own, True)]
            else:
                if up:
                    lines += diamond(uc, zr + 0.35, own, half=0.62, height=5.0)
                else:
                    lines += diamond(uc, zr + 0.35, own, half=0.66, height=0.7)
        return parts, lines


def diamond(uc, zb, own, half=0.62, height=5.0):
    """diamond (rhombus) pantograph standing on its lower vertex, seen from the
    side; the collector head across the top vertex."""
    zm_ = zb + height * 0.5
    zt = zb + height
    col = PANTO
    out = []
    vv = 0.0
    out += [((uc, vv, zb), (uc - half, vv, zm_), col, own, False),
            ((uc, vv, zb), (uc + half, vv, zm_), col, own, False),
            ((uc - half, vv, zm_), (uc, vv, zt), col, own, False),
            ((uc + half, vv, zm_), (uc, vv, zt), col, own, False)]
    out.append(((uc, -0.66, zt), (uc, 0.66, zt), PANTO_HEAD, own, True))
    return out


def sheet(key):
    """In the agreed 2026-09-26 style (style.py): the lower roof step's sides are
    the dark gutter, light pantograph arms with a dark head bar; main() runs
    style.polish()."""
    import restyle_kit as K
    lo = Loco(MODELS[key])
    parts, lines = lo.build()
    zs = MODELS[key]["ZS"]
    for p in parts:
        if abs(p.b[4] - zs) < 1e-6 and abs(p.b[5] - (zs + 0.45)) < 1e-6:
            p.mat = K.gutter(p.mat, lambda f, u, v, z, d: True)
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
    for key in (args or list(MODELS)):
        rows = sheet(key)
        out = os.path.join(FAM, key, "sprites", "intercity.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        import restyle_kit as K
        K.save_styled(rows, out)
        if prev:
            R.preview(rows, os.path.join(prev, f"{key}_intercity.png"), z=4, labels=[key.upper()])
        print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
