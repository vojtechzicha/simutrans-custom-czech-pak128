"""Leo Express Stadler FLIRT, class 480 (5-car EMU, Bo'2'2'2'2'Bo').

Whole unit modelled in one u axis (carunits behind the A-car coupler face):
car lengths 10, 8, 8, 8, 10 (end cars 21.08 m coupler -> Jakobs centre,
middle cars 16.0 m Jakobs -> Jakobs; 90.18 m = 44 cu). Car k's front at
u = 0, 10, 18, 26, 34; joints (Jakobs bogie centres) at 10, 18, 26, 34.
Positions: metres from the Stadler datasheet side drawing (63.72 px/m),
corrected by the G3 broadside photo (car 1 has 5 windows behind the door,
car 2 has a blank catering panel on the +v side). End cars map metres ->
cu with 21.08/10, middle cars with 16/8.
z: model px above rail (1 px = 0.375 m).

Liveries:
  cernozlata    G1 2012-2019: gloss black, champagne-gold cantrail band with
                white pinstripe, sweeping down on the end cars to the cab front,
                gold cab hood + roof fairing to the door, white headlight ring,
                yellow skirt, white LEO EXPRESS.
  cerna         G2 2019-2023: all black, thin orange door outlines, big orange
                outline "leo" on car 3, small white logo on the end cars.
  cernooranzova G3 2023+: black, orange U-hood, orange door leaves, white ring,
                yellow-orange skirt, big white "leo express" behind the cabs,
                network map on car 3, ticket slogans on cars 2 and 4.
"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402

LENGTHS = [10, 8, 8, 8, 10]
U0 = [0, 10, 18, 26, 34]
UEND = 44.0
JOINTS = [10.0, 18.0, 26.0, 34.0]
ME = 21.08 / 10.0          # metres per cu, end cars
MM = 16.0 / 8.0            # metres per cu, middle cars
PX = 0.375
W = 0.94                   # 2.88 m wide (R.W_STD 0.92 = 2.825 m)
CAP = 0.10                 # roof fairing inset


def zm(h):
    return h / PX


ZBOT = zm(0.78)            # 2.08 body bottom (low floor, door sill)
ZBOG = zm(0.94)            # 2.5 body bottom over the powered bogie
ZS = zm(3.42)              # 9.12 cantrail (side wall top)
ZR = zm(4.02)              # 10.72 roof top
ZWL0, ZWH0, ZW1 = zm(1.57), zm(1.80), zm(2.59)   # window bottom low/high floor, top
ZD0, ZD1 = ZBOT, zm(3.03)                          # door
ZDW0, ZDW1 = zm(1.62), zm(2.56)                    # door window
HALFJ = 0.14               # body end gap either side of a joint
WSH = 0.07                 # shrink windows 7 cm each end -> ~0.47 m pillars read as 1 px

# --- windows / doors (metres). End cars: from the coupler face.
END_WIN = [(5.89, 7.36, "h"), (7.69, 9.15, "h"), (11.58, 13.04, "l"), (13.37, 14.83, "l"),
           (15.18, 16.64, "l"), (16.97, 18.42, "l"), (18.76, 20.22, "l")]
END_WC = (4.19, 5.19)
END_DOOR = (10.12, 11.19)
# middle cars: from the car's front joint (the A side)
MID_WIN = {
    1: [(0.82, 2.28), (2.61, 4.07), (4.43, 5.89), (6.25, 7.71), (7.97, 9.43, "-v"), (11.96, 13.42), (13.75, 15.21)],
    2: [(1.0 + 1.79 * i, 2.46 + 1.79 * i) for i in range(8)],
    3: [(0.82, 2.29), (2.6, 4.08), (6.59, 8.05), (8.38, 9.84), (10.17, 11.63), (11.95, 13.41), (13.76, 15.22)],
}
MID_DOOR = {1: (10.5, 11.58), 2: None, 3: (4.44, 5.51)}

# --- plain colours
WS = (0x38, 0x47, 0x55)          # windscreen / cab windows (not lit)
WS_HI = (0x60, 0x74, 0x88)
DISP = (0x1A, 0x1C, 0x1E)
AMBER = (0xF0, 0xA0, 0x18)
WHITE = Paint(0xEEEEEE)
BODY_LO = Paint(0x26282B)
BODY_HI = Paint(0x313438)
BODY_CAP = Paint(0x3A3D42, top=0x44484E)
BELLOWS = Paint(0x3E4145)
BELLOWS_DK = Paint(0x2E3033)
BOGIE = Paint(0x232426)
BOGIE_HI = Paint(0x3C3F42)
UNDER = Paint(0x19191A)
COUPLER = Paint(0x3A3C3F)
ROOFEQ = Paint(0x4A4E53, top=0x5A5F65)
ROOFEQ2 = Paint(0x44484D, top=0x52575C)
GRILLE = Paint(0x4A4E53, top=0x6A6F75)
PANTO_BASE = Paint(0x55595E, top=0x6E7378)


def palette(liv):
    black = Paint(0x2C2E31, top=0x44484E)
    C = dict(name=liv, body=black, roof=black, capside=Paint(0x303236, top=0x3D4146))
    if liv == "cernozlata":
        C.update(hood=Paint(0xC2A77E, top=0xCDB48C), band=Paint(0xC2A77E), pin=Paint(0xEAEAEA),
                 skirt=Paint(0xF4C03A), ring=WHITE, door=black, doorframe=Paint(0x4E5156),
                 logo=WHITE, dot=Paint(0xC2A77E))
    elif liv == "cerna":
        C.update(hood=None, band=None, pin=None, skirt=Paint(0x303236), ring=None, door=black,
                 doorframe=Paint(0xEE7A26), logo=WHITE, dot=Paint(0xF2B02A), bigleo=Paint(0xEE7A26))
    else:  # cernooranzova
        C.update(hood=Paint(0xF39A2E, top=0xF5A640), band=None, pin=None, skirt=Paint(0xF2A62A),
                 ring=WHITE, door=Paint(0xF39A2E), doorframe=None, logo=WHITE, dot=Paint(0xF39A2E),
                 orange=Paint(0xF39A2E))
    return C


# ---------------------------------------------------------------- nose geometry
# centreline front of the cab (u from the coupler face) vs height z
PROF = [(4.0, 0.35), (6.05, 0.49), (8.13, 0.68), (9.33, 0.85), (10.24, 1.03), (10.72, 1.33)]


def nose_front(z):
    if z < 1.3:
        return 0.40            # yellow skirt plate
    if z < 2.4:
        return 0.42            # chin
    if z < 4.0:
        return 0.35            # nose tip (headlight / coupler level)
    zs = [p[0] for p in PROF]; us = [p[1] for p in PROF]
    return float(np.interp(z, zs, us))


def corner(z):
    """plan-view corner: (Ru along u, Rv along v, max half width)."""
    if z < 1.3:
        return 0.45, 0.28, W - 0.05
    if z < 4.0:
        return 0.90, 0.52, W
    if z < 5.4:
        return 0.55, 0.34, W
    if z < ZS:
        return 0.28, 0.22, W
    return 0.50, 0.30, W - CAP


def half_width(z, du):
    Ru, Rv, hw = corner(z)
    if du >= Ru:
        return hw
    t = 1.0 - du / Ru
    return hw - Rv * (1.0 - np.sqrt(max(0.0, 1.0 - t * t)))


UN = 2.0     # nose slabs end here (u from coupler); main body behind


def zb_hood(ul):
    """G1/G3 hood boundary on the cab side: hood colour above this height.
    Traced from the G3 broadside (m, h): (0.7,1.56) (0.95,2.2) (1.6,3.0)
    (2.5,3.62) (3.8,4.1) -> the band sweeps from the roof down along the
    windscreen edge to headlight level; the cab side window stays black."""
    return float(np.interp(ul, [0.33, 0.45, 0.76, 1.19, 1.8], [4.2, 5.9, 8.0, 9.65, 10.9],
                           left=4.2, right=99.0))


# ---------------------------------------------------------------- text helpers
def bars(xl, z, rows):
    """rows: list of (x0, x1, z0, z1) bold text bars (one per text line)."""
    for (a, b, z0, z1) in rows:
        if a <= xl <= b and z0 <= z <= z1:
            return True
    return False


def dot_hit(xl, z, pts, rx=0.16, rz=0.30):
    for (x, zz) in pts:
        if abs(xl - x) <= rx and abs(z - zz) <= rz:
            return True
    return False


# ---------------------------------------------------------------- model
class Unit:
    def __init__(self, liv):
        self.C = palette(liv)
        self.parts = []
        self.lines = []
        self.build()

    # --- which car / local coords
    @staticmethod
    def car_of(u):
        for k in range(4, -1, -1):
            if u >= U0[k] - 1e-6:
                return k
        return 0

    def bodyc(self, z):
        """black body with lifted shading: the upper body and the roof fairing
        catch the sky like the gloss paint in the photos."""
        if z > ZS - 0.02:
            return BODY_CAP
        if z > 7.3:
            return BODY_HI
        if z < 3.2:
            return BODY_LO
        return self.C["body"]

    # --------------------------------------------------------- end car paint
    def end_side(self, k, sgn, ul, z, v=None):
        """side paint of an end car; ul = cu from its coupler face."""
        C = self.C
        m = ul * ME
        rear = (k == 4)
        # reading direction: +v side screen-left = larger u
        # car A: larger u = larger m ; car B: larger u = smaller m
        left_is_far = (sgn > 0) == (k == 0)      # screen-left is the joint end

        # cab zone handled by the nose painter when close to the nose surface
        du = ul - nose_front(z)
        Ru, _, _ = corner(z)
        if ul < UN and du < Ru + 0.10:
            return self.nose(k, "side", ul, v, z)
        # hood (G1/G3) over the cab side
        if C["hood"] is not None and z > zb_hood(ul):
            return C["hood"]
        # G1 gold roof fairing back to the door
        if C["name"] == "cernozlata" and z > ZS + 0.55 and m < 11.6:
            return C["hood"]
        if z > ZS - 0.02:
            return self.bodyc(z)
        # door
        d = self.door_px(END_DOOR, m, z, left_is_far)
        if d is not None:
            return d
        # passenger windows
        for (a, b, kind) in END_WIN:
            if a + WSH <= m <= b - WSH:
                z0 = ZWH0 if kind == "h" else ZWL0
                if z0 <= z <= ZW1:
                    if C["name"] == "cernozlata":
                        pass
                    return R.GLASS_HI if z > ZW1 - 0.45 else R.GLASS
        # G1 sweep band (drawn after windows so windows win)
        if C["name"] == "cernozlata":
            s = min(1.0, max(0.0, (9.5 - m) / 8.0))
            ztop = 8.9 - 4.2 * s ** 2.2
            if ztop - 1.02 <= z <= ztop:
                return C["band"]
            if ztop - 1.98 <= z < ztop - 1.02:
                return C["pin"]
        # cab windows behind the corner (plain dark, not lit)
        if ul < 1.36 and 5.2 <= z <= 7.6:
            return WS_HI if z > 7.2 else WS
        # WC window (frosted, plain) - under the G3 logo
        if END_WC[0] <= m <= END_WC[1] and zm(1.33) <= z <= zm(2.35) and C["name"] != "cernooranzova":
            return Paint(0x4A4F55)
        # logos
        lg = self.end_logo(m, z, left_is_far)
        if lg is not None:
            return lg
        if z < ZBOG and ul < 3.5 and z < ZBOT + 0.3:
            return self.bodyc(z)
        return self.bodyc(z)

    def end_logo(self, m, z, left_is_far):
        C = self.C
        name = C["name"]
        if name == "cernooranzova":
            a, b = 2.1, 6.4
            if not (a <= m <= b and 2.9 <= z <= 7.5):
                return None
            xl = (b - m) if left_is_far else (m - a)     # 0 at screen-left
            if dot_hit(xl, z, [(0.18, 6.85), (0.48, 6.2), (0.82, 5.6)], rx=0.17, rz=0.33):
                return C["dot"]
            # slash under the dots
            if 0.05 <= xl <= 0.95 and 3.1 <= z <= 4.7:
                zc = 3.1 + (xl - 0.05) / 0.9 * 1.6
                if abs(z - zc) <= 0.42:
                    return C["dot"]
            if bars(xl, z, [(1.25, 2.55, 5.3, 7.3), (1.15, 4.3, 3.1, 4.85)]):
                return C["logo"]
            return None
        if name == "cerna":
            a, b = 5.6, 7.7
            if not (a <= m <= b and 2.5 <= z <= 4.75):
                return None
            xl = (b - m) if left_is_far else (m - a)
            if dot_hit(xl, z, [(0.12, 4.45), (0.32, 4.0)], rx=0.12, rz=0.25):
                return C["dot"]
            if bars(xl, z, [(0.55, 1.25, 3.75, 4.75), (0.5, 2.1, 2.55, 3.45)]):
                return C["logo"]
            return None
        # cernozlata: italic LEO EXPRESS under the sweep
        a, b = 3.6, 7.9
        if not (a <= m <= b and 2.6 <= z <= 4.7):
            return None
        xl = (b - m) if left_is_far else (m - a)
        if bars(xl, z, [(0.0, 1.3, 2.7, 4.7), (1.5, 4.3, 2.7, 3.7)]):
            return C["logo"]
        return None

    def door_px(self, door, m, z, left_is_far):
        C = self.C
        a, b = door
        if not (a <= m <= b and ZD0 <= z <= ZD1):
            return None
        c = (a + b) / 2
        fw = 0.30 * (b - a) if C["name"] == "cerna" else 0.17
        if C["doorframe"] is not None:
            if m - a < fw or b - m < fw or z > ZD1 - 0.45:
                return C["doorframe"]
        if abs(m - c) <= 0.24 and ZDW0 <= z <= ZDW1:
            return R.GLASS_HI if z > ZDW1 - 0.4 else R.GLASS
        return C["door"]

    # --------------------------------------------------------- nose paint
    def nose(self, k, face, ul, v, z):
        """paint of the cab nose surface (front face, corners, sloped tops).
        Position based: av = lateral distance from the centre line."""
        C = self.C
        rear = (k == 4)
        av = abs(v) if v is not None else W
        uf = nose_front(z)
        du = ul - uf
        Ru, Rv, hw = corner(z)
        hood = C["hood"]
        g3 = C["name"] == "cernooranzova"
        # roof over the cab
        if z >= ZR - 0.02:
            if hood is not None and ul * ME < 3.6:
                return hood
            return C["roof"]
        # skirt / chin / coupler level
        if z < 1.3:
            return C["skirt"] if av < W - 0.12 or du < 0.3 else self.bodyc(z)
        if z < 3.8:
            return self.bodyc(z)
        # headlight / ring band
        if z < 5.4:
            if 4.15 <= z <= 5.1 and 0.42 <= av <= 0.76:
                return R.TAIL if rear else R.HEAD
            ring = C["ring"]
            if ring is not None and av < 0.86 and (z < 4.15 or z > 5.1 or av > 0.76):
                return ring
            if 4.35 <= z <= 4.95 and av < 0.26:
                return C["logo"]
            if g3 and z > 5.05 and av >= 0.84 and du < Ru + 0.3:
                return hood
            return self.bodyc(z)
        # windscreen band (glass narrows slightly towards the top)
        if z < ZW_TOP:
            lim = 0.76 - 0.10 * (z - 5.4) / (ZW_TOP - 5.4)
            if av < lim:
                if z > ZW_TOP - 1.1 or (v is not None and v > 0.25 and z > 6.6):
                    return WS_HI
                return WS
            if du < Ru + 0.35:
                return hood if hood is not None else C["body"]
            return self.bodyc(z)
        # destination display above the windscreen
        if z < ZS + 0.55 and av < 0.46:
            if abs(z - 9.3) < 0.22 and av < 0.34:
                return AMBER
            return DISP
        if hood is not None:
            return hood
        return C["capside"] if z > ZS else C["body"]

    # --------------------------------------------------------- middle car paint
    def mid_side(self, k, sgn, u, z):
        C = self.C
        m = (u - U0[k]) * MM
        side = "+v" if sgn > 0 else "-v"
        left_is_far = sgn > 0          # screen-left = larger u = larger m
        if z > ZS - 0.02:
            return self.bodyc(z)
        door = MID_DOOR[k]
        if door is not None:
            d = self.door_px(door, m, z, left_is_far)
            if d is not None:
                return d
        # G1 cantrail band
        if C["band"] is not None:
            if 7.88 <= z <= 8.9:
                return C["band"]
            if 6.92 <= z < 7.88:
                return C["pin"]
        # G3 network map on car 3 (over the windows)
        if C["name"] == "cernooranzova" and k == 2:
            mp = self.map_px(m, z, left_is_far)
            if mp is not None:
                return mp
        for w in MID_WIN[k]:
            a, b = w[0], w[1]
            if len(w) > 2 and w[2] != side:
                continue
            if a + WSH <= m <= b - WSH and ZWL0 <= z <= ZW1:
                return R.GLASS_HI if z > ZW1 - 0.45 else R.GLASS
        # G3 slogans (car 2 near car 1, car 4 near car 5)
        if C["name"] == "cernooranzova" and k in (1, 3):
            a, b = (0.9, 4.1) if k == 1 else (11.9, 15.1)
            if a <= m <= b and 3.05 <= z <= 3.65:
                xl = (b - m) if left_is_far else (m - a)
                return C["orange"] if xl > 2.3 else C["logo"]
        # G2 big orange outline "leo" on car 3
        if C["name"] == "cerna" and k == 2:
            lp = self.bigleo_px(m, z, left_is_far)
            if lp is not None:
                return lp
        return self.bodyc(z)

    def map_px(self, m, z, left_is_far):
        """G3 network map (+v side as photographed: trunk from the car-4 end,
        fork near the car-2 end into an upper Krakow/Lviv branch and a lower
        Kosice/Mukachevo branch). Lines 1 px, stations white, names as dashes."""
        C = self.C
        xl = (16.0 - m) if left_is_far else m     # 0 = screen-left end of car 3
        o, wt = C["orange"], C["logo"]
        zt, zu, zd = 5.55, 7.75, 3.55             # trunk, upper, lower branch
        dots = [(1.8, zt), (3.9, zt), (6.0, zt), (7.9, zt), (10.6, zu), (12.3, zu),
                (11.3, zd), (13.1, zd), (14.7, zd)]
        if dot_hit(xl, z, dots, rx=0.22, rz=0.5):
            return wt
        if 0.4 <= xl <= 8.8 and abs(z - zt) <= 0.5:
            return o
        if 8.8 <= xl <= 9.8:
            t = (xl - 8.8) / 1.0
            if abs(z - (zt + (zu - zt) * t)) <= 0.55 or abs(z - (zt + (zd - zt) * t)) <= 0.55:
                return o
        if 9.8 <= xl <= 12.7 and abs(z - zu) <= 0.5:
            return o
        if 9.8 <= xl <= 15.0 and abs(z - zd) <= 0.5:
            return o
        # city names: short white dashes under the lower branch / above the upper
        names = [(10.0, 11.1), (11.7, 12.5), (13.0, 14.3)]
        if 2.25 <= z <= 2.85 and any(p <= xl <= q for p, q in names):
            return wt
        if 8.35 <= z <= 8.9 and any(p <= xl <= q for p, q in [(9.9, 11.2), (11.8, 12.8)]):
            return wt
        if 2.25 <= z <= 2.85 and any(p <= xl <= q for p, q in [(1.2, 2.4), (3.2, 4.4), (5.3, 6.5)]):
            return wt
        return None

    def bigleo_px(self, m, z, left_is_far):
        """orange outline 'leo' rotated 90 deg (reads bottom -> top), car 3 centre."""
        C = self.C
        a, b = 6.6, 9.2
        if not (a <= m <= b and 2.4 <= z <= 8.9):
            return None
        xl = (b - m) if left_is_far else (m - a)
        o = C["bigleo"]
        t = 0.22
        # 'l' : a long bar across the bottom of the rotated word -> vertical stroke at left
        if xl <= t + 0.05:
            return o
        # 'e' (upper) and 'o' (lower) outlines to its right
        for (z0, z1) in ((5.9, 8.9), (2.4, 5.5)):
            if z0 <= z <= z1 and 0.6 <= xl <= 2.6:
                if xl - 0.6 < t or 2.6 - xl < t or z - z0 < 0.35 or z1 - z < 0.35:
                    return o
                if z0 > 5 and abs(z - (z0 + z1) / 2) < 0.2 and xl < 1.9:
                    return o          # the bar of the 'e'
        return None

    # --------------------------------------------------------- materials
    def mat_for(self, k):
        C = self.C

        def mat(f, u, v, z, d):
            if k in (0, 4):
                ul = u if k == 0 else UEND - u
                fl = f
                if k == 4 and f in ("-u", "+u"):
                    fl = "-u" if f == "+u" else "+u"
                if f == "+z":
                    if z < ZR - 0.05 and ul < UN + 0.05:
                        return self.nose(k, f, ul, v, z)
                    if ul < UN + 0.2:
                        return self.nose(k, f, ul, v, max(z, ZR))
                    return C["roof"]
                if fl == "-u" and ul < UN:
                    return self.nose(k, fl, ul, v, z)
                if f in ("+v", "-v"):
                    return self.end_side(k, 1 if f == "+v" else -1, ul, z, v)
                return self.bodyc(z)           # joint end faces
            if f == "+z":
                return C["roof"]
            if f in ("+v", "-v"):
                return self.mid_side(k, 1 if f == "+v" else -1, u, z)
            return self.bodyc(z)
        return mat

    def add(self, u0, u1, v0, v1, z0, z1, mat, own):
        self.parts.append(Part(u0, u1, v0, v1, z0, z1, mat, own))

    def add_end(self, k, ul0, ul1, v0, v1, z0, z1, mat, own):
        if k == 0:
            self.add(ul0, ul1, v0, v1, z0, z1, mat, own)
        else:
            self.add(UEND - ul1, UEND - ul0, v0, v1, z0, z1, mat, own)

    def build(self):
        C = self.C
        for k in range(5):
            own = f"c{k}"
            mat = self.mat_for(k)
            if k in (0, 4):
                self.build_end(k, mat, own)
            else:
                u0, u1 = U0[k] + HALFJ, U0[k] + LENGTHS[k] - HALFJ
                self.add(u0, u1, -W, W, ZBOT, ZS, mat, own)
                self.add(u0 + 0.04, u1 - 0.04, -W + CAP, W - CAP, ZS, ZR, mat, own)
                # underbody shadow between the Jakobs bogies
                self.add(U0[k] + 1.0, U0[k] + LENGTHS[k] - 1.0, -W + 0.30, W - 0.30, 1.35, ZBOT,
                         lambda *a: UNDER, own)
        # joints: bellows + Jakobs bogie, owned by the car in front
        for j, J in enumerate(JOINTS):
            own = f"c{j}"
            self.add(J - HALFJ - 0.02, J + HALFJ + 0.02, -W + 0.12, W - 0.12, ZBOT + 0.25, ZS + 0.35,
                     lambda f, u, v, z, d: BELLOWS if f in ("+v", "-v") and int((u - 0) * 20) % 2 == 0 or f == "+z"
                     else BELLOWS_DK, own)
            self.parts += R.bogie(J, own, W=W, half=0.78, z1=2.15, col=BOGIE, frame=BOGIE_HI)
        # powered bogies under the cabs
        for (k, uc) in ((0, 5.16 / ME), (4, UEND - 5.16 / ME)):
            self.parts += R.bogie(uc, f"c{k}", W=W, half=0.80, z1=2.35, col=BOGIE, frame=BOGIE_HI)
        self.build_roof()

    def build_end(self, k, mat, own):
        # nose slabs: layers in z, each split into u-strips following the plan corner
        layers = [(0.35, 1.3), (1.3, 2.4), (2.4, 4.0)]
        z = 4.0
        while z < ZR - 1e-6:
            z1 = min(ZR, z + 0.4)
            layers.append((z, z1))
            z = z1
        for (z0, z1) in layers:
            zc = (z0 + z1) / 2
            uf = nose_front(zc)
            Ru, Rv, hw = corner(zc)
            n = 6 if Ru > 0.4 else 4
            uend = 1.5 if z1 <= 2.4 else UN
            for i in range(n):
                a = uf + Ru * i / n
                b = uf + Ru * (i + 1) / n
                h = half_width(zc, (a + b) / 2 - uf)
                self.add_end(k, a, b, -h, h, z0, z1, mat, own)
            b = uf + Ru
            if b < uend:
                self.add_end(k, b, uend, -hw, hw, z0, z1, mat, own)
        # main body
        self.add_end(k, UN, 3.5, -W, W, ZBOG, ZS, mat, own)
        self.add_end(k, 3.5, 10 - HALFJ, -W, W, ZBOT, ZS, mat, own)
        self.add_end(k, UN, 10 - HALFJ - 0.04, -W + CAP, W - CAP, ZS, ZR, mat, own)
        # coupler
        self.add_end(k, 0.05, 0.40, -0.18, 0.18, 2.6, 3.5, lambda *a: COUPLER, own)
        # underbody shadow behind the powered bogie
        self.add_end(k, 3.5, 9.0, -W + 0.30, W - 0.30, 1.35, ZBOT, lambda *a: UNDER, own)

    def build_roof(self):
        def box(k, m0, m1, h, hw, paint, from_coupler=True):
            """k: car; m0..m1 metres (end cars: from coupler; middles: from front joint)."""
            if k in (0, 4):
                a, b = m0 / ME, m1 / ME
                if k == 4:
                    a, b = UEND - b, UEND - a
            else:
                a, b = U0[k] + m0 / MM, U0[k] + m1 / MM
            self.add(a, b, -hw, hw, ZR - 0.05, ZR + h, lambda *x: paint, f"c{k}")

        for k in (0, 4):
            box(k, 4.4, 5.1, 0.45, 0.35, ROOFEQ2)
            box(k, 5.8, 6.9, 0.35, 0.55, ROOFEQ)
            box(k, 7.1, 9.5, 0.55, 0.72, ROOFEQ)          # big two-panel roof box
            box(k, 11.3, 12.4, 0.35, 0.50, ROOFEQ2)
            box(k, 14.9, 15.6, 0.30, 0.30, ROOFEQ2)
            box(k, 17.8, 18.9, 0.30, 0.45, ROOFEQ2)
        box(4, 21.08 - 5.7, 21.08 - 4.3, 0.55, 0.62, GRILLE)  # AC with grilles (car 5)
        # car 2: pantograph at the car-1 end, raised
        box(1, 0.35, 2.05, 0.40, 0.45, PANTO_BASE)
        box(1, 3.3, 4.6, 0.40, 0.40, ROOFEQ2)
        box(1, 9.8, 12.0, 0.55, 0.62, GRILLE)
        # car 3: AC unit
        box(2, 16.0 - 7.0, 16.0 - 4.3, 0.55, 0.62, GRILLE)
        box(2, 11.0, 12.6, 0.30, 0.45, ROOFEQ2)
        # car 4: pantograph at the car-5 end, lowered
        box(3, 16.0 - 2.05, 16.0 - 0.35, 0.40, 0.45, PANTO_BASE)
        box(3, 16.0 - 4.6, 16.0 - 3.3, 0.40, 0.40, ROOFEQ2)
        box(3, 4.0, 6.2, 0.55, 0.62, GRILLE)
        zb = ZR + 0.4
        # raised pantograph on car 2 (knee trailing towards car 3)
        ub = U0[1] + 0.55
        self.lines += R.pantograph(ub, zb, "c1", fold=+1, reach=0.95, height=5.6,
                                   col=(0x70, 0x74, 0x78), head=(0x2A, 0x2A, 0x2C), half_head=0.62,
                                   thick=False)
        # lowered pantograph on car 4: frame lying on the base
        ub = U0[3] + 8.0 - 0.55
        pc = (0x70, 0x74, 0x78)
        self.lines += [((ub, 0.0, zb + 0.1), (ub - 0.85, 0.0, zb + 0.45), pc, "c3", False),
                       ((ub - 0.85, -0.5, zb + 0.45), (ub - 0.85, 0.5, zb + 0.45), (0x2A, 0x2A, 0x2C), "c3", False)]


ZW_TOP = zm(3.28)     # windscreen top (8.75)


def render_unit(liv):
    un = Unit(liv)
    rows = []
    for k in range(5):
        lo, hi = U0[k] - 3.0, U0[k] + LENGTHS[k] + 3.0
        parts = [p for p in un.parts if p.b[1] >= lo and p.b[0] <= hi]
        lines = [l for l in un.lines if lo <= l[0][0] <= hi]
        rows.append([R.vehicle_tile(parts, lines, d, float(U0[k]), {f"c{k}"}) for d in DIRS])
    return rows


LIVERIES = ["cernozlata", "cerna", "cernooranzova"]
LABELS = ["480-A", "480-2", "480-3", "480-4", "480-B"]


if __name__ == "__main__":
    import leo
    leo.main()
