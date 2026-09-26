"""RegioJet Pesa electric multiple units, drawn from scratch with the pak128 box
raycaster (render.py + railkit.py):

  654  Pesa Elf.eu 2-car   654 (Bo'Bo', leads) + 954 (2'2', trails)       DUK green-yellow
  655  Pesa Elf.eu 3-car   655 (Bo'Bo', leads) + 055 + 955 (trails)        PID grey-red
  666  Pesa InterRegio200 4-car  666-A (leads) + 666-2 + 666-3 + 666-B     RegioJet yellow
  667  Pesa InterRegio200 3-car  667-A (leads) + 667-2 + 667-B             RegioJet yellow

Regenerate with `python tools/railrender/rj_pesa.py [family ...] [--preview DIR]`
(or through tools/railrender/regiojet.py). Change the model and regenerate;
never paint the PNGs.

Model conventions (see railkit.py): the whole unit sits on one u axis (carunits
behind the unit's front coupler), every car has its own owner and is rendered
with its front on the calibrated anchor (car k's front at sum(lengths[:k])), so
the joints close in all 8 views. Inside a car everything is placed in metres
`m` from the car's reference end: the coupler tip for a cab car (the lead car's
front, the tail car's rear) and the front joint for a middle car. Each car maps
its real length onto its carunits (M = metres per cu). Heights `h` are metres
above the rail head (model z = h / 0.375).

Elf.eu dimensions come from the vagonWEB scale side drawings 654-duk-a and
655-pid-a (10 px = 1 m, research/photos/654, 655), read with the rail head one
row under the wheels so the cab hood tops out at Pesa's 4.28 m: car bodies
25.85 m (654 cars, 655 end cars) and 23.9 m (055), cab hood 4.3 m, roof 3.8 m,
low floor 0.6 m, window band 1.3-2.9 m (DUK) / stepped 1.9-3.3 and 1.3-2.5 m
(PID), one double door per car side (two on the 055). InterRegio200 geometry is
estimated from the RegioJet/Pesa release photos (see the 666 family.yaml).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "regiojet")

import numpy as np                       # noqa: E402
import railkit as R                      # noqa: E402
from railkit import Paint, Part          # noqa: E402
from render import DIRS                  # noqa: E402

PX = 0.375                 # metres per model px (height)


def zm(h):
    return h / PX


def interp(x, pts):
    return float(np.interp(x, [a for a, b in pts], [b for a, b in pts]))


# ------------------------------------------------------------------ shared colours
WS = (0x2A, 0x33, 0x3C)          # windscreen / cab side window: plain, never lit
WS_HI = (0x4C, 0x5E, 0x6E)
BAND = Paint(0x25292C)           # black window band (= rjcoach BAND)
BAND_ELF = Paint(0x232628)
UNDER = Paint(0x19191A)
BOGIE = Paint(0x232426)
BOGIE_HI = Paint(0x3E4144)
HUB = Paint(0x6A6E72)
COUPLER = Paint(0x3A3C3F)
BELLOWS = Paint(0x3A3D40, top=0x44474A)
BELLOWS_DK = Paint(0x2C2E31)
RJ_RED = (0xE3, 0x34, 0x2F)
RJ_BLUE = (0x1F, 0x3A, 0x93)
YELLOW = 0xFFB612                # rjcoach YELLOW (RAL 1028 lifted to the sunlit photo value)
PANTO = (0x70, 0x74, 0x78)
PANTO_HEAD = (0x2A, 0x2A, 0x2C)


# ------------------------------------------------------------------ car frame
class Car:
    """One car of a unit. cab: 'front' (lead cab car, reference end = its front
    coupler), 'rear' (tail cab car, reference end = its rear coupler) or None
    (middle car, reference end = its front joint)."""

    def __init__(self, unit, k, cid, u0, L, length_m, cab):
        self.unit, self.k, self.id = unit, k, cid
        self.u0, self.L, self.M = float(u0), float(L), length_m / float(L)
        self.len_m = length_m
        self.cab = cab
        self.owner = f"c{k}"

    def m_of(self, u):
        if self.cab == "rear":
            return (self.u0 + self.L - u) * self.M
        return (u - self.u0) * self.M

    def u_of(self, m):
        if self.cab == "rear":
            return self.u0 + self.L - m / self.M
        return self.u0 + m / self.M

    def seen(self, m, face):
        """metres from the car's screen-left end as seen on side `face`
        (-v side: screen-left = front of the unit, +v side: its rear)."""
        u = self.u_of(m)
        return (u - self.u0) * self.M if face == "-v" else (self.u0 + self.L - u) * self.M

    def vl(self, v):
        """lateral position as seen from this car's own cab (+ = driver's right)."""
        return -v if self.cab == "rear" else v

    def box(self, m0, m1, v0, v1, z0, z1, mat):
        a, b = self.u_of(m0), self.u_of(m1)
        return Part(min(a, b), max(a, b), v0, v1, z0, z1, mat, self.owner)


def text_t(car, face, a, b, m):
    """0..1 position of m inside the lettering block [a, b] (car metres),
    read left to right as seen on `face`."""
    sa, sb = sorted((car.seen(a, face), car.seen(b, face)))
    return (car.seen(m, face) - sa) / max(1e-6, sb - sa)


def rj_logo(t):
    """'|| REGIOJET' across t = 0..1: two red bars, red REGIO, blue JET."""
    if t < 0.07 or 0.11 <= t < 0.18:
        return RJ_RED
    if 0.18 <= t < 0.26:
        return None
    if t < 0.66:
        return RJ_RED
    return RJ_BLUE


# ------------------------------------------------------------------ generic unit
class Unit:
    """A fixed multiple unit. Subclasses give the layout (CARS), geometry
    constants and the paint functions side() / front() / top_nose()."""
    W = 0.92
    CAP = 0.18                 # roof cap inset
    GAP = 0.22                 # body end short of a joint (cu), bellows between
    Z_BB = zm(1.0)             # body bottom over the bogies
    Z_LF = zm(0.22)            # body bottom (skirt) in the low-floor part
    ZS = zm(3.45)              # side wall top
    ZR = zm(3.80)              # roof crest
    ZH = zm(4.28)              # cab hood / roof equipment top
    CAB = 4.2                  # cab part (m from the coupler tip)
    SKIRT_END = 2.0            # front skirt/plough ends here (m)
    PROF = []                  # (h metres, m front surface) cab profile
    HOOD_REAR = []             # (h, m) rear edge of the raised cab hood (above ZR)
    WHEEL_BASE = 2.7

    def __init__(self, liv):
        self.liv = liv
        self.cars = []
        u = 0.0
        n = len(self.CARS)
        for k, (cid, L, length_m) in enumerate(self.CARS):
            cab = "front" if k == 0 else ("rear" if k == n - 1 else None)
            self.cars.append(Car(self, k, cid, u, L, length_m, cab))
            u += L
        self.parts = []
        self.lines = []
        for c in self.cars:
            self.build_car(c)
        self.build_joints()

    # ---------------------------------------------------------- geometry helpers
    def nose_m(self, h):
        return interp(h, self.PROF)

    def plan_hw(self, h, d):
        """half width of the rounded cab d metres behind the local front surface."""
        tab = [(0.0, 0.74), (0.12, 0.86), (0.3, 0.94), (0.6, 0.985), (1.0, 1.0)]
        r = interp(d, tab)
        return r * self.front_hw(h)

    def front_hw(self, h):
        """head-on half width at height h (the cab leans in towards the top)."""
        top = self.ZH * PX
        t = max(0.0, (h - 3.0) / (top - 3.0))
        return self.W * (1 - 0.16 * t ** 1.6)

    def slab_rear(self, car, h):
        if h < self.Z_BB * PX:
            return self.SKIRT_END
        if h <= self.ZR * PX + 1e-6:
            return self.CAB
        return interp(h, self.HOOD_REAR)

    def low_floor(self, car):
        """(m0, m1) of the low-floor skirt (body down to Z_LF)."""
        return None

    def bogies(self, car):
        return []

    # ---------------------------------------------------------- materials
    def mat_for(self, car):
        def mat(f, u, v, z, d):
            m = car.m_of(u)
            h = z * PX
            if f == "+z":
                return self.top(car, m, v, h)
            if f in ("+v", "-v"):
                return self.side(car, m, h, f, v)
            out = "-u" if car.cab == "front" else "+u"
            if car.cab is not None and f == out:
                if m < self.CAB - 0.03:
                    return self.front(car, car.vl(v), h, m)      # nose slabs
                if m < self.CAB + 0.3:
                    return self.side(car, m, h, "-v", v)         # step at the body box end
            return self.end_face(car, m, v, h)
        return mat

    def top(self, car, m, v, h):
        if car.cab is not None and m < self.CAB - 0.03 and h < self.ZR * PX - 0.02:
            return self.front(car, car.vl(v), h, m, top=True)   # steps of the nose slabs
        if car.cab is not None and m < self.CAB + 0.05 and h >= self.ZR * PX - 0.02:
            return self.hood_top(car, m, v, h)
        return self.roof(car, m, v, h)

    def end_face(self, car, m, v, h):
        return self.body_colour(car, m, h)

    # ---------------------------------------------------------- build
    def build_car(self, car):
        mat = self.mat_for(car)
        W = self.W
        P = self.parts
        m_end = car.len_m - self.GAP * car.M                     # joint end of the body
        m_start = self.CAB if car.cab else self.GAP * car.M       # body box start
        # body over the bogies (whole length) and the low-floor skirt
        P.append(car.box(m_start, m_end, -W, W, self.Z_BB, self.ZS, mat))
        lf = self.low_floor(car)
        if lf:
            P.append(car.box(lf[0], lf[1], -W, W, self.Z_LF, self.Z_BB + 0.01, mat))
        # roof cap
        P.append(car.box(m_start - 0.02, m_end - 0.04, -W + self.CAP, W - self.CAP, self.ZS, self.ZR, mat))
        if car.cab:
            self.build_cab(car, mat)
            # coupler
            P.append(car.box(0.0, self.nose_m(1.0) + 0.05, -0.2, 0.2, zm(0.85), zm(1.2),
                             lambda *a: COUPLER))
        # underframe shadow between the bogies (high-floor parts only show it)
        bg = self.bogies(car)
        if len(bg) == 2:
            P.append(car.box(bg[0] + 1.6, bg[1] - 1.6, -W + 0.3, W - 0.3, zm(0.45), self.Z_BB,
                             lambda *a: UNDER))
        for bc in bg:
            P.extend(self.bogie_parts(car, bc))
        self.build_roof(car)

    def build_cab(self, car, mat):
        """stacked slabs following PROF (front) and plan rounding."""
        W = self.W
        z_bot = zm(self.PROF[0][0])
        zs = list(np.arange(z_bot, self.Z_BB, 0.4)) + [self.Z_BB] + \
            list(np.arange(self.Z_BB + 0.33, self.ZR, 0.33)) + [self.ZR] + \
            list(np.arange(self.ZR + 0.25, self.ZH, 0.25))
        zs = sorted(set(round(x, 3) for x in zs if x < self.ZH - 0.05))
        dsteps = [0.0, 0.06, 0.13, 0.22, 0.34, 0.5, 0.7, 1.0, 99.0]
        for i, z0 in enumerate(zs):
            z1 = zs[i + 1] if i + 1 < len(zs) else self.ZH
            zc = (z0 + z1) / 2
            h = zc * PX
            mf = self.nose_m(h)
            end = self.slab_rear(car, h)
            if mf >= end:
                continue
            for k in range(len(dsteps) - 1):
                a, b = mf + dsteps[k], min(end, mf + dsteps[k + 1])
                if a >= b:
                    break
                hh = self.plan_hw(h, (dsteps[k] + min(dsteps[k + 1], 1.5)) / 2)
                if z0 >= self.ZS - 0.01:
                    hh = min(hh, W - self.CAP * (0.3 if z0 < self.ZR - 0.01 else 1.2))
                self.parts.append(car.box(a, b, -hh, hh, z0, z1, mat))

    def bogie_parts(self, car, bc):
        wb = self.WHEEL_BASE
        axles = (bc - wb / 2, bc + wb / 2)

        def bm(f, u, v, z, d):
            if f in ("+v", "-v"):
                m = car.m_of(u)
                if 0.35 < z < 1.3 and any(abs(m - a) < 0.25 for a in axles):
                    return HUB
                if 1.3 <= z < 2.0:
                    return BOGIE_HI
            return BOGIE
        half = (wb / 2 + 0.55)
        return [car.box(bc - half, bc + half, -self.W + 0.12, self.W - 0.12, 0.0, self.Z_BB + 0.02, bm)]

    def build_joints(self):
        W = self.W
        for a, b in zip(self.cars[:-1], self.cars[1:]):
            J = b.u0
            g0, g1 = J - self.GAP - 0.03, J + self.GAP + 0.03

            def bel(f, u, v, z, d):
                if f == "+z":
                    return BELLOWS
                if f in ("+v", "-v"):
                    return BELLOWS if int(u * 24) % 2 == 0 else BELLOWS_DK
                return BELLOWS_DK
            self.parts.append(Part(g0, g1, -W + 0.14, W - 0.14, self.Z_BB + 0.2, self.ZS + 0.15, bel, a.owner))

    def build_roof(self, car):
        pass

    def roof_box(self, car, m0, m1, hw, paint, z1=None):
        z1 = self.ZH if z1 is None else z1
        self.parts.append(car.box(m0, m1, -hw, hw, self.ZR - 0.05, z1, lambda *a: paint))

    def pantograph(self, car, m_base, raised=True, fold=+1):
        """fold=+1: knee towards larger car-m."""
        zb = self.ZH + 0.1
        ub = car.u_of(m_base)
        du = (car.u_of(m_base + 1.0) - ub)          # u per metre along +m
        base = Paint(0x55595E, top=0x6E7378)
        self.parts.append(car.box(m_base - 0.8, m_base + 0.8, -0.5, 0.5, self.ZR - 0.05, zb, lambda *a: base))
        if raised:
            f = fold * (1 if du > 0 else -1)
            self.lines += R.pantograph(ub, zb, car.owner, fold=f, reach=0.95, height=5.4,
                                       col=PANTO, head=PANTO_HEAD, half_head=0.62, thick=False)
        else:
            ue = car.u_of(m_base + fold * 1.7)
            self.lines += [((ub, 0.0, zb + 0.1), (ue, 0.0, zb + 0.45), PANTO, car.owner, False),
                           ((ue, -0.5, zb + 0.45), (ue, 0.5, zb + 0.45), PANTO_HEAD, car.owner, False)]

    # ---------------------------------------------------------- render
    def rows(self):
        out = []
        for c in self.cars:
            lo, hi = c.u0 - 3.0, c.u0 + c.L + 3.0
            parts = [p for p in self.parts if p.b[1] >= lo and p.b[0] <= hi]
            lines = [l for l in self.lines if lo <= l[0][0] <= hi]
            out.append([R.vehicle_tile(parts, lines, d, c.u0, {c.owner}) for d in DIRS])
        return out


# ================================================================== Elf.eu (654 / 655)
class Elf(Unit):
    W = R.W_STD * 2.82 / 2.825
    # cab profile from the 654/655 drawings (h, m): skirt, blunt lower front,
    # windscreen leaning back into the raised cab hood
    PROF = [(0.22, 0.72), (0.6, 0.62), (1.3, 0.66), (1.7, 0.78), (2.1, 0.9), (2.5, 1.0),
            (2.8, 1.1), (3.0, 1.2), (3.2, 1.3), (3.4, 1.48), (3.6, 1.62), (3.8, 1.8),
            (4.0, 2.0), (4.15, 2.25), (4.3, 2.6)]
    HOOD_REAR = [(3.80, 5.9), (4.05, 5.0), (4.30, 4.2)]
    CAB = 4.7
    SKIRT_END = 2.0
    BOGIE_C = (5.15, 22.35)          # bogie centres from the cab coupler (drawing)
    WHEEL_BASE = 2.7
    LF = (7.6, 20.0)                 # low-floor skirt between the bogies (cab car metres)

    def bogies(self, car):
        L = car.len_m
        if car.cab:
            return list(self.BOGIE_C)
        return [3.6, L - 3.6]

    def low_floor(self, car):
        if car.cab:
            return self.LF
        return (6.0, car.len_m - 6.0)

    # windscreen wrap on the cab side: rear edge (m) vs height, from the drawing
    def ws_rear(self, h):
        return interp(h, [(2.1, 2.9), (2.4, 3.1), (2.7, 3.3), (3.1, 3.4), (3.45, 3.5)])

    def hood_top(self, car, m, v, h):
        return self.C["cap"]


class U654(Elf):
    """654 (Bo'Bo' motor car, leads, headlights) + 954 (2'2' driving trailer
    with the pantograph, tail lights). 2 x 13 cu, 25.85 m per car."""
    CARS = [("654", 13, 25.85), ("954", 13, 25.85)]
    # side layout (m from the cab coupler tip), vagonWEB 654-duk-a
    WIN_HI = [(5.3, 6.1), (6.4, 7.7), (20.2, 21.6), (21.9, 23.2), (23.6, 25.0)]
    WIN_LO = [(8.0, 9.4), (11.7, 13.1), (13.4, 14.2), (16.8, 18.1), (18.5, 19.8)]
    DOOR = (9.7, 11.4)
    STRIPES = [(4.35, 7.6), (20.2, 25.6)]
    CABWIN = (3.9, 4.6)

    def __init__(self, liv="dukzelenozluta"):
        g = 0x90CE40
        self.C = dict(
            body=Paint(g), body_hi=Paint(0xA2D956, top=0xB0E068),
            band=BAND_ELF, stripe=Paint(0xF4B81C), frame=Paint(0xEDB51B, top=0xF2BE2A),
            cap=Paint(0xB9BFC4, top=0xC6CCD0), roof=Paint(0x5E6468, top=0x686E72),
            skirt=Paint(0x6C7175), lowblack=Paint(0x1E2022), door=Paint(0xBFC3C6),
            doorsplit=Paint(0x4E5358), roofbox=Paint(0x44484C, top=0x4E5256),
            roofbox2=Paint(0x7A8085, top=0x878D92), grille=Paint(0x303437, top=0x3A3E42))
        super().__init__(liv)

    def body_colour(self, car, m, h):
        C = self.C
        if h < 0.8:
            return C["skirt"]
        if h > 3.43:
            return C["body_hi"]
        return C["body"]

    def roof(self, car, m, v, h):
        if abs(v) > self.W - self.CAP - 0.02:
            return self.C["body_hi"]
        return self.C["roof"]

    # ---- cab side
    def cab_side(self, car, m, h, face):
        C = self.C
        front = self.nose_m(h)
        if h >= 3.45:
            if m < self.ws_rear(3.45) + 0.3 and h < 3.9:
                return C["frame"]                # top corner of the yellow frame
            if h >= 3.72:
                return C["cap"]                  # silver stripe along the cab hood
            return C["body_hi"]
        if 2.05 <= h < 3.45:
            r = self.ws_rear(h)
            if m < r:
                return WS_HI if h > 3.2 else WS
            if m < r + 0.32:
                return C["frame"]                # yellow frame seen from the side
            if self.CABWIN[0] <= m <= self.CABWIN[1] and 2.5 <= h <= 3.2:
                return WS
        if 1.62 <= h < 2.05 and m < front + 0.45:
            return C["frame"]                    # lower yellow of the frame round the corner
        if 1.22 <= h < 1.62 and m < front + 0.3:
            return C["lowblack"]
        if h < 0.8:
            return C["skirt"] if m < self.SKIRT_END + 0.1 else UNDER
        return self.body_colour(car, m, h)

    def side(self, car, m, h, face, v):
        C = self.C
        if car.cab and m < self.CAB + 0.02:
            return self.cab_side(car, m, h, face)
        if h >= self.ZS * PX - 0.02:
            return C["body_hi"]
        # door (silver, two leaves with windows, reaching the step)
        a, b = self.DOOR
        if a <= m <= b and 0.4 <= h <= 2.9:
            t = (m - a) / (b - a)
            if 0.47 <= t <= 0.53 or t < 0.06 or t > 0.94:
                return C["doorsplit"]
            if 1.5 <= h <= 2.5 and (0.14 <= t <= 0.40 or 0.60 <= t <= 0.86):
                return R.GLASS_HI if h > 2.25 else R.GLASS
            return C["door"]
        band0 = 4.35 + (h - 1.3) * 0.6
        if 1.3 <= h < 2.9 and m >= band0:
            for (p, q) in self.STRIPES:
                if p <= m <= q and h < 1.75:
                    # RJ logo at the left end of each stripe as seen
                    t = text_t(car, face, p + 0.15, p + 1.75, m) if car.seen(p, face) < car.seen(q, face) \
                        else text_t(car, face, q - 1.75, q - 0.15, m)
                    if 0.0 <= t <= 1.0 and h >= 1.38 and h <= 1.66:
                        lc = rj_logo(t)
                        if lc is not None:
                            return lc
                    return C["stripe"]
            for (p, q) in self.WIN_HI:
                if p + 0.06 <= m <= q - 0.06 and 2.0 <= h <= 2.8:
                    return R.GLASS_HI if h > 2.55 else R.GLASS
            for (p, q) in self.WIN_LO:
                if p + 0.06 <= m <= q - 0.06 and 1.4 <= h <= 2.1:
                    return R.GLASS_HI if h > 1.9 else R.GLASS
            return C["band"]
        lf = self.low_floor(car)
        if h < 0.8:
            if lf and lf[0] + 0.3 <= m <= lf[1] - 0.3:
                return C["skirt"]
            return UNDER
        return self.body_colour(car, m, h)

    def end_face(self, car, m, v, h):
        if 1.3 <= h < 2.9:
            return self.C["band"]
        return self.body_colour(car, m, h)

    # ---- cab front
    def front(self, car, vl, h, m, top=False):
        C = self.C
        av = abs(vl)
        hw = self.front_hw(h)
        lamp_head = car.cab == "front"
        if h < 0.8:
            return C["skirt"]
        if h < 1.22:                                  # lower front: black centre, green corners
            return C["lowblack"] if av < 0.5 else C["body"]
        if h < 1.62:                                  # black lamp band (tail lights)
            if not top and not lamp_head and 0.46 <= av <= 0.74:
                return R.TAIL
            return C["lowblack"]
        if h < 2.05:                                  # yellow band with the round headlights
            if not top and lamp_head and 0.46 <= av <= 0.72:
                return R.HEAD
            return C["frame"]
        if h < 3.62:                                  # black windscreen field in the yellow frame
            if av > hw - 0.16:
                return C["frame"]
            return WS_HI if h > 3.3 else WS
        if h < 3.85:
            return C["frame"]                         # top of the frame
        return C["cap"]


class U655(Elf):
    """655 (Bo'Bo' motor car, leads) + 055 (intermediate, 2 doors) + 955
    (driving trailer, 1st class, pantograph, tail lights). 13 + 12 + 13 cu."""
    CARS = [("655", 13, 25.8), ("055", 12, 23.9), ("955", 13, 25.8)]
    # end cars (m from the cab coupler tip), vagonWEB 655-pid-a
    E_HI = [(5.3, 6.1), (6.4, 7.7), (20.2, 21.6), (21.9, 23.2), (23.6, 25.0)]
    E_LO = [(8.1, 9.4), (11.8, 13.1), (13.4, 14.2), (16.8, 18.1), (18.5, 19.8)]
    E_DOOR = (9.6, 11.4)
    E_RED = (11.6, 16.5)
    E_HIBAND = [(0.0, 9.6), (20.1, 25.6)]      # high band 1.9-3.3 m (low band elsewhere)
    E_LOBAND = (11.4, 20.1)                    # low band 1.3-2.5 m
    E_PID = (16.9, 18.2)
    # middle car (m from its front joint)
    M_HI = [(1.0, 2.2), (2.7, 3.9), (4.4, 5.6), (18.2, 19.6), (19.9, 21.2), (21.7, 22.9)]
    M_LO = [(6.0, 7.4), (9.8, 10.9), (11.4, 12.5), (13.0, 14.2), (16.5, 17.9)]
    M_DOORS = [(7.7, 9.6), (14.5, 16.2)]
    M_RED = (9.6, 14.3)
    M_HIBAND = [(0.0, 7.7), (16.2, 24.0)]
    M_LOBAND = (9.6, 14.5)

    def __init__(self, liv="pidsedocervena"):
        self.C = dict(
            body=Paint(0xD6D9DC), body_hi=Paint(0xE2E5E8, top=0xE8EBEE),
            band=Paint(0x222527), red=Paint(0xD9111B), red_hi=Paint(0xE8242E),
            cap=Paint(0xDCE0E3, top=0xE6E9EC), roof=Paint(0xB4B9BD, top=0xC0C5C9),
            skirt=Paint(0x6A6F73), lowblack=Paint(0x1E2022), door=Paint(0x26292C),
            doorframe=Paint(0x9EA3A7), letter=Paint(0x1C1E20), gold=Paint(0xE0A816),
            roofbox=Paint(0x5C6166, top=0x6A6F74), roofbox2=Paint(0x7E8489, top=0x8E9499),
            grille=Paint(0x3A3E42, top=0x4A4E52))
        super().__init__(liv)

    def layout(self, car):
        if car.cab:
            return dict(hi=self.E_HI, lo=self.E_LO, doors=[self.E_DOOR], red=self.E_RED,
                        hiband=self.E_HIBAND, loband=self.E_LOBAND)
        return dict(hi=self.M_HI, lo=self.M_LO, doors=self.M_DOORS, red=self.M_RED,
                    hiband=self.M_HIBAND, loband=self.M_LOBAND)

    def body_colour(self, car, m, h):
        C = self.C
        if h < 0.8 and car.cab and m < self.CAB:
            return C["skirt"]
        r = self.layout(car)["red"]
        if r[0] <= m <= r[1]:
            return C["red_hi"] if h > 3.43 else C["red"]
        return C["body_hi"] if h > 3.43 else C["body"]

    def roof(self, car, m, v, h):
        r = self.layout(car)["red"]
        if abs(v) > self.W - self.CAP - 0.1:
            if r[0] <= m <= r[1]:
                return self.C["red_hi"]
            return self.C["body_hi"]
        return self.C["roof"]

    def cab_side(self, car, m, h, face):
        C = self.C
        front = self.nose_m(h)
        if h >= 3.45 and m < interp(h, [(3.45, 4.7), (3.8, 5.6), (4.3, 4.3)]):
            return C["cap"]
        if 1.9 <= h < 3.45:
            r = self.ws_rear(max(h, 2.1))
            if m < r:
                return WS_HI if h > 3.15 else WS
            if 3.3 <= h:
                return C["body_hi"]
            if self.CABWIN[0] <= m <= self.CABWIN[1] and 2.5 <= h <= 3.2:
                return WS
            return C["band"]                     # the black band runs into the windscreen
        if 1.35 <= h < 1.9 and m < front + 0.35:
            return C["lowblack"]
        if h < 0.8:
            return C["skirt"] if m < self.SKIRT_END + 0.1 else UNDER
        # red nose accent on the driver's left corner (seen round the corner)
        return self.body_colour(car, m, h)

    CABWIN = (3.9, 4.6)

    def side(self, car, m, h, face, v):
        C = self.C
        if car.cab and m < self.CAB + 0.02:
            return self.cab_side(car, m, h, face)
        lay = self.layout(car)
        red = lay["red"][0] <= m <= lay["red"][1]
        if h >= self.ZS * PX - 0.02:
            return C["red_hi"] if red else C["body_hi"]
        for (a, b) in lay["doors"]:
            if a <= m <= b and 0.4 <= h <= 2.9:
                t = (m - a) / (b - a)
                if t < 0.07 or t > 0.93 or h > 2.8:
                    return C["doorframe"]
                if 0.48 <= t <= 0.52:
                    return C["doorframe"]
                if 1.5 <= h <= 2.5 and (0.16 <= t <= 0.40 or 0.60 <= t <= 0.84):
                    return R.GLASS_HI if h > 2.25 else R.GLASS
                return C["door"]
        in_hi = any(a <= m <= b for (a, b) in lay["hiband"])
        lb = lay["loband"]
        in_lo = lb[0] <= m <= lb[1]
        # windows (low windows may hang below the high band in their own frame)
        for (a, b) in lay["hi"]:
            if a + 0.06 <= m <= b - 0.06 and 2.0 <= h <= 2.8:
                return R.GLASS_HI if h > 2.55 else R.GLASS
        for (a, b) in lay["lo"]:
            if a + 0.06 <= m <= b - 0.06 and 1.4 <= h <= 2.2:
                return R.GLASS_HI if h > 2.0 else R.GLASS
            if a - 0.1 <= m <= b + 0.1 and 1.3 <= h <= 2.3:
                return C["band"]                 # window frame
        # 1st class line on the 955 (above the band, cab to door)
        if car.id == "955" and 3.8 <= m <= 9.5 and 2.95 <= h < 3.3:
            return C["gold"]
        if in_hi and 1.9 <= h < 3.3:
            return C["band"]
        if in_lo and 1.3 <= h < 2.5:
            return C["band"]
        # black "|| REGIOJET" low on the grey behind the cab
        if car.cab and 4.1 <= m <= 6.5 and 1.12 <= h <= 1.62:
            t = text_t(car, face, 4.1, 6.5, m)
            if t < 0.07 or 0.11 <= t < 0.17 or (t >= 0.25 and int((t - 0.25) * 22) % 3 != 2):
                return C["letter"]
        # red "pid" on the grey panel of the end cars
        if car.cab and self.E_PID[0] <= m <= self.E_PID[1] and 2.75 <= h <= 3.15:
            t = text_t(car, face, self.E_PID[0], self.E_PID[1], m)
            if t < 0.25:
                return C["letter"] if h > 2.95 else C["body"]   # S-train sign
            if t > 0.4:
                return C["red"]
        if h < 0.8:
            lf = self.low_floor(car)
            if lf and lf[0] + 0.3 <= m <= lf[1] - 0.3:
                return C["red"] if red else C["skirt"]
            return UNDER
        return self.body_colour(car, m, h)

    def end_face(self, car, m, v, h):
        return self.body_colour(car, m, h)

    def front(self, car, vl, h, m, top=False):
        C = self.C
        av = abs(vl)
        hw = self.front_hw(h)
        lamp_head = car.cab == "front"
        red_side = vl < 0                      # red accent on the driver's left corner
        if h < 0.8:
            return C["skirt"]
        if h < 1.35:
            if av < 0.5:
                return C["lowblack"]
            return C["red"] if red_side else C["body"]
        if h < 1.9:                                   # lamp band
            if not top and 0.5 <= av <= 0.74 and 1.45 <= h <= 1.8:
                return R.HEAD if lamp_head else R.TAIL
            if red_side and av > 0.3:
                return C["red"]
            return C["body"]
        if h < 3.5:                                   # windscreen
            if av > hw - 0.14:
                return C["red"] if red_side else C["body"]
            return WS_HI if h > 3.2 else WS
        return C["cap"]


# ================================================================== InterRegio200 (666 / 667)
class IR200(Unit):
    """Pesa InterRegio200 for RegioJet: RJ yellow, black band, black cab glazing
    with a silver edge, dark-grey roof covers, one single-leaf door per car side."""
    W = R.W_STD * 2.85 / 2.825
    Z_BB = zm(1.05)
    Z_LF = zm(0.45)
    ZS = zm(3.50)
    ZR = zm(3.90)
    ZH = zm(4.12)                # cab roof top; roof covers reach 4.2 m
    CAB = 4.7
    SKIRT_END = 1.9
    PROF = [(0.45, 0.62), (0.8, 0.56), (1.2, 0.52), (1.6, 0.55), (1.9, 0.66), (2.2, 0.9),
            (2.6, 1.3), (3.0, 1.85), (3.4, 2.5), (3.7, 3.05), (3.9, 3.6), (4.05, 4.25), (4.12, 4.6)]
    HOOD_REAR = [(3.9, 4.7), (4.12, 4.7)]
    WHEEL_BASE = 2.6
    BAND = (1.72, 3.0)
    HIWIN = (1.85, 2.7)
    LOWIN = (1.25, 2.15)

    def __init__(self, liv="zluta"):
        self.C = dict(
            body=Paint(YELLOW), body_hi=Paint(0xFFC23A, top=0xFFC846),
            band=BAND, silver=Paint(0xC4CACE, top=0xD0D5D9), door=Paint(0xA9AEB1),
            doorsplit=Paint(0x5C6164), roof=Paint(0x585D60, top=0x676C6F),
            cover=Paint(0x686D71, top=0x767B7F), cover2=Paint(0x5E6367, top=0x6C7175),
            skirt=Paint(0x2E3133), lowblack=Paint(0x1E2022), white=Paint(0xE8EAEB),
            grille=Paint(0x2A2D30))
        super().__init__(liv)

    def front_hw(self, h):
        t = max(0.0, (h - 2.4) / (self.ZH * PX - 2.4))
        return self.W * (1 - 0.30 * t ** 1.3)

    def plan_hw(self, h, d):
        tab = [(0.0, 0.66), (0.15, 0.80), (0.35, 0.90), (0.7, 0.97), (1.2, 1.0)]
        return interp(d, tab) * self.front_hw(h)

    def bogies(self, car):
        L = car.len_m
        if car.cab:
            return [5.0, L - 3.7]
        return [3.7, L - 3.7]

    def low_floor(self, car):
        if car.cab:
            return (8.4, car.len_m - 6.2)
        return (6.2, car.len_m - 6.2)

    def door(self, car):
        if car.cab:
            return (10.8, 12.0)
        return (car.len_m - 7.6, car.len_m - 6.4)

    def windows(self, car):
        """[(m0, m1, low?)] passenger windows."""
        L = car.len_m
        d0, d1 = self.door(car)
        out = []
        if car.cab:
            out += [(5.2, 6.4, False), (6.9, 8.0, False), (9.2, 10.4, True)]
            x = 12.4
            while x + 1.2 <= L - 6.6:
                out.append((x, x + 1.2, True))
                x += 1.6
            x = L - 6.2
            while x + 1.2 <= L - 0.9:
                out.append((x, x + 1.2, False))
                x += 1.75
        else:
            x = 1.0
            while x + 1.2 <= d0 - 5.2:
                out.append((x, x + 1.2, False))
                x += 1.75
            x2 = d0 - 5.0
            while x2 + 1.2 <= d0 - 0.3:
                out.append((x2, x2 + 1.2, True))
                x2 += 1.6
            out += [(d1 + 0.4, d1 + 1.6, True), (d1 + 2.0, d1 + 3.2, False), (d1 + 3.75, d1 + 4.95, False)]
        return out

    def body_colour(self, car, m, h):
        C = self.C
        if h < 0.62:
            return C["skirt"]
        return C["body_hi"] if h > 3.48 else C["body"]

    def roof(self, car, m, v, h):
        return self.C["roof"]

    def hood_top(self, car, m, v, h):
        return self.C["body_hi"]

    def silver_h(self, m):
        """height of the silver line along the windscreen's upper edge (cab side)."""
        return interp(m, [(0.9, 2.05), (2.5, 2.75), (4.6, 3.95)])

    def cab_side(self, car, m, h, face):
        C = self.C
        front = self.nose_m(h)
        s = self.silver_h(m)
        if h >= s + 0.2:
            return C["body_hi"] if h > 3.3 else C["body"]       # yellow cab roof
        if h >= s:
            return C["silver"]
        if h >= 2.05 and m < 4.45:
            return WS_HI if h > s - 0.25 else WS                # windscreen / cab glazing
        if 1.2 <= h < 1.9 and m < front + 0.55:
            return C["lowblack"]                                 # headlight mask round the corner
        if h < 0.62:
            return C["skirt"]
        # red/blue logo low behind the cab is drawn in side()
        return self.body_colour(car, m, h)

    def side(self, car, m, h, face, v):
        C = self.C
        if car.cab and m < self.CAB + 0.02:
            return self.cab_side(car, m, h, face)
        if h >= self.ZS * PX - 0.02:
            return C["roof"]
        d0, d1 = self.door(car)
        if d0 <= m <= d1 and 0.55 <= h <= 2.72:
            t = (m - d0) / (d1 - d0)
            if t < 0.08 or t > 0.92 or h > 2.62:
                return C["doorsplit"]
            if 1.45 <= h <= 2.45 and 0.22 <= t <= 0.78:
                return R.GLASS_HI if h > 2.2 else R.GLASS
            return C["door"]
        b0, b1 = self.BAND
        for (a, b, low) in self.windows(car):
            w0, w1 = self.LOWIN if low else self.HIWIN
            if a + 0.07 <= m <= b - 0.07 and w0 <= h <= w1:
                return R.GLASS_HI if h > w1 - 0.25 else R.GLASS
            if low and a - 0.12 <= m <= b + 0.12 and w0 - 0.1 <= h < b0:
                return C["band"]                 # frame of a low window under the band
        if b0 <= h < b1:
            # white class word on the band of the lead car ("Business")
            if car.id.endswith("A") and 16.8 <= m <= 18.8 and 2.72 <= h <= 2.95:
                t = text_t(car, face, 16.8, 18.8, m)
                if int(t * 9) % 3 != 2:
                    return C["white"]
            return C["band"]
        # "|| REGIOJET" low behind the cab (red + blue on yellow)
        if car.cab and 6.0 <= m <= 7.6 and 1.22 <= h <= 1.55:
            lc = rj_logo(text_t(car, face, 6.0, 7.6, m))
            if lc is not None:
                return lc
        lf = self.low_floor(car)
        if h < 0.62:
            return C["skirt"] if (lf and lf[0] <= m <= lf[1]) else UNDER
        return self.body_colour(car, m, h)

    def end_face(self, car, m, v, h):
        if self.BAND[0] <= h < self.BAND[1]:
            return self.C["band"]
        return self.body_colour(car, m, h)

    def front(self, car, vl, h, m, top=False):
        C = self.C
        av = abs(vl)
        hw = self.front_hw(h)
        lamp_head = car.cab == "front"
        if h < 0.62:
            return C["skirt"]
        if h < 1.2:                                  # yellow fairings, black centre + grilles
            if av < 0.42:
                return C["lowblack"]
            if av < 0.56:
                return C["grille"]
            return C["body"]
        if h < 1.9:                                  # black headlight mask
            if not top and 0.52 <= av <= 0.78 and 1.38 <= h <= 1.72:
                return R.HEAD if lamp_head else R.TAIL
            return C["lowblack"]
        if h < 2.05:
            return C["body"] if av > 0.45 else C["lowblack"]
        if h < 3.85:                                 # windscreen, silver edges up top
            if av > hw - 0.13 and h > 2.5:
                return C["silver"]
            return WS_HI if h > 3.4 else WS
        return C["body_hi"]


class U666(IR200):
    CARS = [("666-A", 13, 26.5), ("666-2", 13, 26.0), ("666-3", 13, 26.0), ("666-B", 13, 26.5)]

    def build_roof(self, car):
        roof_covers(self, car)
        if car.k == 1:
            self.pantograph(car, 2.4, raised=True, fold=+1)


class U667(IR200):
    CARS = [("667-A", 13, 26.5), ("667-2", 13, 26.0), ("667-B", 13, 26.5)]

    def build_roof(self, car):
        roof_covers(self, car)
        if car.k == 1:
            self.pantograph(car, 2.4, raised=True, fold=+1)


def roof_covers(u, car):
    """IR200: long dark-grey equipment covers along the roof (release photos)."""
    L = car.len_m
    C = u.C
    zt = zm(4.15)
    if car.cab:
        segs = [(5.0, 9.6, C["cover"]), (10.2, 16.8, C["cover2"]), (17.4, 21.6, C["cover"]),
                (22.2, L - 0.9, C["cover2"])]
    else:
        segs = [(4.4 if car.k == 1 else 0.9, 7.8, C["cover"]), (8.4, 15.2, C["cover2"]),
                (15.8, 20.4, C["cover"]), (21.0, L - 0.9, C["cover2"])]
    for (a, b, p) in segs:
        u.roof_box(car, a, b, 0.66, p, z1=zt)


# ------------------------------------------------------------------ Elf roofs
def elf_roof(u, car, pant):
    """roof boxes read off the vagonWEB drawings (m from the car's reference end)."""
    C = u.C
    rb, rb2, gr = C["roofbox"], C["roofbox2"], C["grille"]
    if car.cab:
        u.roof_box(car, 6.4, 8.4, 0.55, rb2)
        u.roof_box(car, 9.2, 10.3, 0.55, gr)
        u.roof_box(car, 10.4, 11.9, 0.55, rb)
        u.roof_box(car, 13.7, 17.8, 0.66, rb)
        u.roof_box(car, 18.2, 19.7, 0.55, rb)
        u.roof_box(car, 19.8, 20.9, 0.55, gr)
        if pant:
            u.pantograph(car, 21.2, raised=True, fold=-1)
            u.roof_box(car, 23.6, 25.0, 0.5, rb2)
        else:
            u.roof_box(car, 21.3, 23.3, 0.55, rb2)
            u.roof_box(car, 23.7, 25.1, 0.5, rb2)
    else:
        u.roof_box(car, 0.7, 2.2, 0.5, rb2)
        u.roof_box(car, 2.7, 4.8, 0.55, rb2)
        u.roof_box(car, 5.3, 8.1, 0.6, gr)
        u.roof_box(car, 9.7, 13.2, 0.66, rb)
        u.roof_box(car, 15.5, 18.3, 0.6, gr)
        u.roof_box(car, 19.1, 21.2, 0.55, rb2)
        u.roof_box(car, 21.7, 23.2, 0.5, rb2)


class R654(U654):
    def build_roof(self, car):
        elf_roof(self, car, pant=(car.id == "954"))


class R655(U655):
    def build_roof(self, car):
        elf_roof(self, car, pant=(car.id == "955"))


# ------------------------------------------------------------------ jobs
LABELS = {"654": ["654", "954"], "655": ["655", "055", "955"],
          "666": ["666-A", "666-2", "666-3", "666-B"], "667": ["667-A", "667-2", "667-B"]}
UNITS = {"654": (R654, "dukzelenozluta"), "655": (R655, "pidsedocervena"),
         "666": (U666, "zluta"), "667": (U667, "zluta")}
LENGTHS = {f: [c[1] for c in cls.CARS] for f, (cls, _) in UNITS.items()}


def rows_for(fam):
    cls, liv = UNITS[fam]
    return cls(liv).rows()


JOBS = {fam: [(liv, (lambda fam=fam: rows_for(fam)), LABELS[fam])] for fam, (cls, liv) in UNITS.items()}


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
