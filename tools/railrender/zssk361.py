"""ZSSK class 361.1 (Skoda 69E "Persing" body, ZOS Vrutky dual-system rebuild
of the class 163) as a box model on the pak128.cs-calibrated railkit renderer.

The installed pak128.CS ZSSK_361.1_Pershing is the generic 163 drawing
(squat body, no portholes, oversized yellow pantographs), so the class is
rendered from scratch like the Leo Express Vectron (vectron.py).

Real: 16.8 m over buffers, 2.94 m wide, 4.65 m high (pantographs down),
Bo'Bo', 86 t, 3.6 MW (3 kV) / 3.2 MW (25 kV), 160 km/h. Drawn at length 8 like
every 16-17 m pak128.cs loco (CD 163/363, EP09, EU07).
u: 0 = front buffer face; v lateral (+v right); z model px (0.375 m).
Real positions are metres from the nearer buffer face (the body is symmetric).

Liveries (photos: 361 124 Praha hl.n., 361 126 Praha 2024, 361 128 Vsetin,
361 107 Bratislava 2018 = cervenobila; 361 129 Praha 2023 (two photos), 361 129
Kolin line Aug 2025 = korporatni):
  cervenobila  red upper body (69 % of the side), off-white ribbed band (19 %),
               grey frame (12 %), light-grey roof; front: red with the two
               windscreens in white frames, off-white band with the two lamp
               pairs and the number, grey lower front, yellow buffer beam.
  korporatni   ZSSK corporate scheme (2022+, 361 129): cabs and fronts as
               above; machine-room side red with a thin white line along the
               top, a white wedge in front of the right-hand cab door as seen
               (the same from either side), the red running down to the frame
               in front of it with the big white ZSSK arc logo, the off-white
               lower band only on the left part.

Regenerate: python zssk361.py [--preview DIR]  (writes the family sheets)
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(WT, "tools", "railrender"))
import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402

L = 8.0
LEN_M = 16.8
MPC = LEN_M / L
W = 0.92 * 2.94 / 2.825
PX = 0.375

ZB = 3.1            # body side bottom
ZG = 4.1            # top of the grey frame band
ZW = 5.65           # top of the off-white band (red above)
ZS = 11.3           # cantrail
ZR = 12.1           # roof ridge
UB = 0.26           # buffers
UN = 0.28           # front face at the buffer beam level
UWT = 0.40          # windscreen top recedes to here (slight rake)
ZWIN0, ZWIN1 = 8.3, 10.75
CAB_M = 3.15        # metres from the buffer face: end of the cab (behind the door)
CABWIN = (0.95, 1.70)
DOOR = (2.05, 2.95)
PORTS = [4.25, 5.55]          # porthole centres, metres from the nearer end
PORT_R = 0.36                 # radius (m)
PORT_Z = 9.0
PORT_RZ = 0.95                # radius in z
BOGIES = (4.3, 12.5)
BOG_HALF = 1.45
PANTOS = [(3.4, False), (13.4, True)]     # metres from the front, raised?

RED = Paint(0xB8202A, top=0xC02632)
WHITE = Paint(0xE6E2DA)
GREY = Paint(0x8E8A86)
FRAME = Paint(0x55524F)
ROOF = Paint(0xB2B0AC, top=0xBDBBB7)
ROOF_DK = Paint(0x8E8C88, top=0x9A9894)
GRILLE = Paint(0x55585C, top=0x5E6166)
GRILLE_DK = Paint(0x3C3F43, top=0x44474B)
YELLOW = Paint(0xE8C21A)
UNDER = Paint(0x2A2B2C)
BOGIE = Paint(0x262728)
BOGIE_HI = Paint(0x3C3E40)
BUFFER = Paint(0x2E3032)
DOORLINE = Paint(0x7A1418)
HANDLE = Paint(0xD8D4CC)
WS = (0x2A, 0x34, 0x3D)
WS_HI = (0x4F, 0x62, 0x72)
PORT = (0x22, 0x2A, 0x32)
PORT_HI = (0x46, 0x56, 0x64)
FRAMEW = (0xEE, 0xEC, 0xE6)
PANTO = (0x7A, 0x24, 0x22)
PANTO_HEAD = (0x2C, 0x2C, 0x2E)
LOGO = (0xF2, 0xF0, 0xEA)
ORANGE = (0xE8, 0x7A, 0x1E)
PPC = {"ne": 5.66, "sw": 5.66, "w": 4.0, "e": 4.0, "n": 4.0, "s": 4.0, "nw": 2.83, "se": 2.83}

# big ZSSK arc logo (corporate scheme): white arc + pointer, 5 rows
ARC = [".###.",
       "##..#",
       "#.#.#",
       "#...#",
       ".###."]


def dm_of(u):
    return min(u, L - u) * MPC


def rib(z, d):
    """faint horizontal corrugation of the machine-room panels"""
    return int(np.floor(z * R.KZ[d] * 1.0)) % 2 == 0


class Model:
    def __init__(self, liv):
        self.liv = liv

    # ----------------------------------------------------------- side
    def side(self, f, u, v, z, d):
        sgn = 1 if f == "+v" else -1
        dm = dm_of(u)
        along = (L - u) if sgn > 0 else u
        if z < ZG:
            return GREY
        # cab side window
        if CABWIN[0] <= dm <= CABWIN[1] and ZWIN0 <= z <= ZWIN1:
            return WS_HI if z > ZWIN1 - 0.7 else WS
        # cab door: white handrails along both edges, dark-red top frame,
        # dark window
        if DOOR[0] <= dm <= DOOR[1] and ZW - 0.2 <= z <= ZS - 0.6:
            if dm < DOOR[0] + 0.22 or dm > DOOR[1] - 0.22:
                return HANDLE if z < ZWIN1 else DOORLINE
            if z > ZS - 0.95:
                return DOORLINE
            if DOOR[0] + 0.3 <= dm <= DOOR[1] - 0.3 and ZWIN0 + 0.2 <= z <= ZWIN1 - 0.2:
                return WS
            return self.paint_side(dm, along, z, d, door=True)
        # portholes
        for pc in PORTS:
            if ((dm - pc) / PORT_R) ** 2 + ((z - PORT_Z) / PORT_RZ) ** 2 <= 1.0:
                return PORT_HI if z > PORT_Z + 0.35 else PORT
        return self.paint_side(dm, along, z, d)

    def paint_side(self, dm, along, z, d, door=False):
        cab = dm < CAB_M
        if self.liv == "korporatni" and not cab and not door:
            return self.corp_side(dm, along, z, d)
        if z < ZW:
            return WHITE
        return RED

    def corp_side(self, dm, along, z, d):
        # machine room between the doors: along from a0 to a1 (as seen)
        a0 = CAB_M / MPC
        a1 = L - CAB_M / MPC
        t = (along - a0) / (a1 - a0)            # 0 left .. 1 right as seen
        hz = (z - ZG) / (ZS - ZG)               # 0 frame top .. 1 cantrail
        if z > ZS - 0.7:
            return WHITE                        # thin white line along the top
        # white wedge in front of the right-hand door: left edge slants from
        # 80 % (top) to 93 % (bottom)
        edge = 0.93 - 0.13 * hz
        if t >= edge:
            return WHITE
        # big ZSSK arc logo on the red, low in front of the wedge
        k = PPC.get(d, 5.66)
        cu = 1.0 / k
        lx = along - (a0 + 0.70 * (a1 - a0))
        i = int(np.floor(lx / cu)); j = int(np.floor((8.3 - z) / 0.85))
        if 0 <= j < len(ARC) and 0 <= i < len(ARC[0]) and ARC[j][i] == "#":
            return Paint(0xEEEAE2)
        # off-white lower band only on the left 58 %
        if z < ZW and t < 0.58:
            return WHITE
        return RED

    # ----------------------------------------------------------- ends
    def end_face(self, u, v, z, d, rear):
        av = abs(v)
        if z < ZB - 0.05:
            return YELLOW if z < 2.3 else GREY
        if z < ZG:
            return GREY
        if z < ZW:
            # off-white band with two round lamps each side: at the front both
            # lit (headlights), at the rear the inner ones are the tail lights
            if 0.46 <= av <= 0.86 and 4.2 <= z <= 5.55:
                if rear:
                    return R.TAIL if av < 0.68 else (0x3A, 0x3A, 0x3C)
                return R.HEAD
            if av < 0.30 and 4.5 <= z <= 5.2:
                return (0x2A, 0x2A, 0x2C)             # number
            return WHITE
        # two windscreens, each in a 1-px white frame, on the red front
        for (v0, v1) in ((-0.84, -0.10), (0.10, 0.84)):
            if v0 <= v <= v1 and ZWIN0 <= z <= ZWIN1:
                if v0 + 0.09 <= v <= v1 - 0.09 and ZWIN0 + 0.35 <= z <= ZWIN1 - 0.35:
                    return WS_HI if z > ZWIN1 - 1.0 else WS
                return FRAMEW
        # top headlight + small ZSSK logo under the windscreen
        if av < 0.12 and 7.2 <= z <= 7.9:
            return R.HEAD if not rear else (0x3A, 0x3A, 0x3C)
        if av < 0.12 and 6.2 <= z <= 6.9:
            return LOGO
        return RED

    # ----------------------------------------------------------- material
    def mat(self, f, u, v, z, d):
        rear = u > L / 2
        cu = min(u, L - u)
        if f in ("+v", "-v"):
            return self.side(f, u, v, z, d)
        if f in ("-u", "+u"):
            return self.end_face(u, v, z, d, f == "+u")
        if z < ZS - 0.05 and cu < UWT + 0.01:
            return self.end_face(u, v, z, d, rear)
        return RED

    def build(self):
        own = "V"
        parts, lines = [], []
        mat = self.mat
        # main body
        parts.append(Part(UWT, L - UWT, -W, W, ZB, ZS, mat, own))
        # front ends: vertical below the windscreen, slight rake above,
        # rounded vertical corners (inset slabs)
        for z0 in np.arange(ZB, ZS - 1e-6, 0.4):
            z1 = min(ZS, z0 + 0.4)
            zc = (z0 + z1) / 2
            uf = UN if zc < ZWIN0 - 0.2 else UN + (UWT - UN) * min(1.0, (zc - ZWIN0 + 0.2) / (ZS - ZWIN0 + 0.2))
            if uf < UWT - 1e-6:
                parts.append(Part(uf, UWT, -W + 0.08, W - 0.08, z0, z1, mat, own))
                parts.append(Part(L - UWT, L - uf, -W + 0.08, W - 0.08, z0, z1, mat, own))
            parts.append(Part(uf + 0.05, UWT + 0.01, -W, W, z0, z1, mat, own))
            parts.append(Part(L - UWT - 0.01, L - uf - 0.05, -W, W, z0, z1, mat, own))
        # roof: sloping sides + flat top, grilles on the slopes of the machine
        # room, rounded cab roofs
        def roof_mat(f, u, v, z, d):
            # dark louvre grilles on the roof slopes of the machine room
            m = u * MPC
            if (5.9 <= m <= 8.2 or 8.6 <= m <= 10.9) and abs(v) > W - 0.70 and z < ZS + 0.6:
                if f == "+z":
                    return GRILLE if int(np.floor(u * 8)) % 2 == 0 else GRILLE_DK
                return GRILLE_DK
            if f == "+z":
                return ROOF
            return ROOF_DK
        slope = [(0.00, 0.30, 0.00), (0.30, 0.55, 0.14), (0.55, 0.80, 0.30)]
        for (dz0, dz1, inset) in slope:
            parts.append(Part(UWT + 0.05 + inset * 0.6, L - UWT - 0.05 - inset * 0.6, -W + inset + 0.05, W - inset - 0.05,
                              ZS + dz0, ZS + dz1, roof_mat, own))
        # equipment on the roof: box near the rear cab + insulators
        parts.append(Part(L - 2.4 / MPC, L - 1.1 / MPC, -0.40, 0.40, ZS + 0.8, ZS + 1.6,
                          lambda f, u, v, z, d: Paint(0x9C9A96, top=0xA8A6A2), own))
        # frame + underframe
        parts.append(Part(UN + 0.05, L - UN - 0.05, -W + 0.05, W - 0.05, ZB - 0.5, ZB,
                          lambda *a: FRAME, own))
        for bm in BOGIES:
            bc = bm / MPC
            hb = BOG_HALF / MPC
            parts.append(Part(bc - hb, bc + hb, -W + 0.12, W - 0.12, 0.0, ZB - 0.5,
                              lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.3 < z < 2.0) else BOGIE, own))
        b0 = BOGIES[0] / MPC + BOG_HALF / MPC
        b1 = BOGIES[1] / MPC - BOG_HALF / MPC
        parts.append(Part(b0, b1, -W + 0.25, W - 0.25, 1.0, ZB - 0.5, lambda *a: UNDER, own))
        # buffer beams (grey with the yellow lower edge) + buffers
        def beam(f, u, v, z, d):
            return YELLOW if z < 2.1 else GREY
        for (a, b) in ((UB, UN + 0.06), (L - UN - 0.06, L - UB)):
            parts.append(Part(a, b, -W + 0.03, W - 0.03, 1.3, ZB, beam, own))
        for (a, b) in ((0.0, UB), (L - UB, L)):
            for vc in (-0.62, 0.62):
                parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.2, 2.9, lambda *a: BUFFER, own))
        # pantographs (single-arm, red-brown), rear one raised
        zr = ZS + 0.8
        for (pm, up) in PANTOS:
            uc = pm / MPC
            parts.append(Part(uc - 0.40, uc + 0.40, -0.38, 0.38, zr, zr + 0.3,
                              lambda *a: Paint(0x5E2420), own))
            if up:
                lines += R.pantograph(uc + 0.30, zr + 0.3, own, fold=-1, reach=0.85, height=5.0,
                                      col=PANTO, head=PANTO_HEAD, half_head=0.62, thick=False)
            else:
                lines += [((uc + 0.35, 0.0, zr + 0.45), (uc - 0.45, 0.0, zr + 0.65), PANTO, own, False),
                          ((uc - 0.45, -0.55, zr + 0.7), (uc - 0.45, 0.55, zr + 0.7), PANTO_HEAD, own, False)]
        return parts, lines


def rows(liv):
    parts, lines = Model(liv).build()
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]


LIVERIES = ("cervenobila", "korporatni")


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for liv in LIVERIES:
        r = rows(liv)
        out = os.path.join(WT, "vehicle-rail", "zssk", "361_1", "sprites", liv + ".png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        R.save_rows(r, out)
        if prev:
            R.preview(r, os.path.join(prev, "361_1_%s.png" % liv), z=4, labels=[liv])
        print("wrote", out)


if __name__ == "__main__":
    main()
