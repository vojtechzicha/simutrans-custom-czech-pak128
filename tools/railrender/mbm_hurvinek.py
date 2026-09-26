"""Tatra two-axle railcar M 131.1 "Hurvínek" and its Studénka Clm/Blm trailer,
drawn from scratch with the pak128 box raycaster of the worktree
(tools/railrender/render.py + railkit.py, calibrated to native pak128.cs rail).

Real vehicles
  M 131.1 (ČSD 801): Tatra Kopřivnice 1948-56, A1, 12.10 m over buffers, body
    11.2 m, 3.0 m wide, 3.56 m high, wheelbase 6.5 m, 16.6 t, Tatra T 301 113.9 kW,
    60 km/h, 48 seats. Octagonal body: the end vestibules taper in plan to a flat
    front with a centre gangway door between two windows; roof headlight at both
    ends, a long raised roof cover (KŽC drawing M131.1302, photos
    zub_M1311280_2022, zub_Zubrnice_2025_01, zub_Hurvinek).
  Blm (ex Clm, Vagónka Studénka 1948-50): companion trailer of the same
    octagonal type, 12.20 m over buffers, body 11.25 m, 3.0 m wide, 3.28 m
    high, wheelbase 6.5 m, 10.8 t, 53 seats, coal stove (roof chimney), six
    windows with transom lights, doors in the tapered vestibule walls
    (vlaky.net "Přípojné vozy řada Clm 1948-1950": side and plan drawing, photo
    of Blm 5-2243 - the very car MBM rail runs at Bruntál 2026).

Model coordinates: s = metres behind the front buffer face, u = s / M carunits
(M = LOB / length), v lateral carunits (+v right-hand side), z model px
(1 px = 0.375 m). Side A = the drawing's side (front end on the left); the
other side is the 180-degree turn of it (point-symmetric cars).
"""
import os
import sys

RR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RR)

import numpy as np          # noqa: E402
import railkit as R         # noqa: E402
from railkit import Paint, Part, Lit   # noqa: E402
from render import DIRS     # noqa: E402

PX = 0.375


def zm(h):
    return h / PX


WS = (0x46, 0x52, 0x5C)           # cab windscreens: plain, never lit
WS_HI = (0x5E, 0x6C, 0x78)
BLACK = Paint(0x1E1F21)
WHEEL = Paint(0x2A2B2D)
AXLEBOX = Paint(0x4A4C4F)
BUFFER = Paint(0x1A1B1C)
YELLOW = Paint(0xE8C21A)
RAIL = (0xD6, 0xD8, 0xD8)         # hand rails
BELLOWS = Paint(0x1C1C1E)


# ---------------------------------------------------------------- the two cars
M131 = dict(
    name="M131.1", lob=12.10, L=6, body=(0.46, 11.64), width=3.0,
    taper=0.95, end_half=0.60,              # vestibule taper (m) / end face half width (cu)
    zb=0.85, zs=3.05, zr=3.37, zbox=3.56,   # heights (m)
    win=(2.04, 2.72), line=(1.68, 2.04),    # window band, white line (1 px)
    doors=[(0.85, 1.43), (10.00, 10.58)],
    windows=[(1.61, 2.07), (2.61, 3.62), (4.10, 5.12), (5.61, 6.61), (7.02, 8.02),
             (8.45, 9.45), (10.82, 11.28)],
    joints=[2.40, 9.67],
    wheels=[2.80, 9.30], roofbox=(2.25, 9.85), chimney=None,
    engine=(4.3, 7.0), railcar=True, transoms=False, panels=[],
    colours=dict(body=0x8C1C24, line=0xEEEDE6, roof=0xA9AEB1, roofside=0x969A9D,
                 door=0x7E1820, frame=0x4E0E13),
)
BLM = dict(
    name="Blm", lob=12.20, L=6, body=(0.475, 11.725), width=3.0,
    taper=1.30, end_half=0.66,
    zb=0.88, zs=2.99, zr=3.28, zbox=None,
    win=(1.90, 2.74), line=None,
    doors=[(0.97, 1.62), (10.43, 11.08)],
    windows=[(2.01, 3.14), (3.44, 4.52), (4.85, 5.92), (6.16, 7.24), (7.56, 8.64), (8.95, 10.03)],
    joints=[1.83, 10.33],
    wheels=[2.85, 9.35], roofbox=None, chimney=6.9,
    engine=None, railcar=False, transoms=False, panels=[4.72, 7.40],
    colours=dict(body=0x9A2029, line=None, roof=0x909395, roofside=0x7E8183,
                 door=0x8E1C25, frame=0x5A1016),
)


class Car:
    def __init__(self, spec, owner="C"):
        self.S = spec
        self.owner = owner
        self.M = spec["lob"] / spec["L"]
        self.W = R.W_STD * spec["width"] / 2.825
        c = spec["colours"]
        self.body = Paint(c["body"])
        self.line = Paint(c["line"]) if c["line"] else None
        self.roof = Paint(c["roofside"], top=c["roof"])
        self.door = Paint(c["door"])
        self.frame = Paint(c["frame"])
        self.darkpanel = Paint(tuple(int(x * 0.82) for x in R.rgb(c["body"])))

    # ---- helpers
    def u(self, s):
        return s / self.M

    def s(self, u):
        return u * self.M

    def half_width(self, s):
        """plan half width (cu) at s: straight sides, tapered vestibules."""
        S = self.S
        s0, s1 = S["body"]
        t = S["taper"]
        d = min(s - s0, s1 - s)
        if d >= t:
            return self.W
        f = max(0.0, d) / t
        return S["end_half"] + (self.W - S["end_half"]) * f

    # ---- materials
    def side_colour(self, sa, z):
        """side pattern at side-A metres sa (front end = small sa), height z."""
        S = self.S
        zb, zs = zm(S["zb"]), zm(S["zs"])
        w0, w1 = zm(S["win"][0]), zm(S["win"][1])
        for (a, b) in S["doors"]:
            if a <= sa <= b:
                edge = (sa - a) < 0.10 or (b - sa) < 0.10
                if w0 + 0.1 <= z <= w1 and a + 0.12 <= sa <= b - 0.12:
                    return R.GLASS_HI if z > w1 - 0.5 else R.GLASS
                if z > w1 + 0.2 and z < w1 + 0.55:
                    return self.frame               # door head
                if edge:
                    return self.frame
                return self.door
        for (a, b) in S["windows"]:
            if a <= sa <= b and w0 <= z <= w1:
                return R.GLASS_HI if z > w1 - 0.5 else R.GLASS
            if S["transoms"] and a + 0.15 <= sa <= b - 0.15 and w1 + 0.25 <= z <= w1 + 0.62:
                return Paint(0x3A2A2C)              # transom light (not lit)
        if self.line is not None and zm(S["line"][0]) <= z <= zm(S["line"][1]):
            return self.line
        for j in S["joints"] + S["panels"]:
            if abs(sa - j) < 0.07 and z < w0:
                return self.darkpanel
        return self.body

    def end_colour(self, v, z, front):
        """flat end face; v as seen looking at the face (symmetric anyway)."""
        S = self.S
        av = abs(v)
        w0, w1 = zm(S["win"][0]), zm(S["win"][1])
        if S["railcar"]:
            # centre gangway door, two windscreens, lamps below the white line
            if av < 0.12:
                if w0 + 0.1 <= z <= w1:
                    return WS_HI if z > w1 - 0.5 else WS
                if av > 0.08 and z < w1:
                    return self.frame
                return self.door
            if 0.17 <= av <= S["end_half"] - 0.07 and w0 <= z <= w1:
                return WS_HI if z > w1 - 0.5 else WS
            if self.line is not None and zm(S["line"][0]) <= z <= zm(S["line"][1]):
                return self.line
            if 0.28 <= av <= 0.48 and 3.30 <= z <= 4.38:
                return R.HEAD if front else R.TAIL
            return self.body
        # trailer: centre door with window
        if av < 0.14:
            if w0 + 0.1 <= z <= w1 and av < 0.10:
                return R.GLASS
            return self.door if av < 0.11 else self.frame
        if 0.22 <= av <= S["end_half"] - 0.12 and w0 <= z <= w1:
            return R.GLASS
        return self.body

    def mat(self, f, u, v, z, d):
        S = self.S
        s = self.s(u)
        s0, s1 = S["body"]
        zs = zm(S["zs"])
        if f == "+z":
            return self.roof
        if f in ("+v", "-v"):
            sa = s if f == "+v" else S["lob"] - s
            return self.side_colour(sa, z)
        # u faces: the true end face, or a step of the tapered vestibule wall
        front = s < S["lob"] / 2
        at_end = (s - s0 < 0.12) if front else (s1 - s < 0.12)
        if at_end and abs(v) <= S["end_half"] + 0.02:
            return self.end_colour(v, z, front)
        # tapered wall: carries the side pattern of the side it belongs to
        sa = s if v > 0 else S["lob"] - s
        return self.side_colour(sa, z)

    # ---- geometry
    def parts(self):
        S, own = self.S, self.owner
        P = []
        s0, s1 = S["body"]
        zb, zs, zr = zm(S["zb"]), zm(S["zs"]), zm(S["zr"])
        t = S["taper"]
        n = 5
        mat = self.mat
        # straight middle
        P.append(Part(self.u(s0 + t), self.u(s1 - t), -self.W, self.W, zb, zs, mat, own))
        # tapered vestibules: n slabs per end
        for k in range(n):
            a, b = s0 + t * k / n, s0 + t * (k + 1) / n
            hw = self.half_width((a + b) / 2)
            P.append(Part(self.u(a), self.u(b), -hw, hw, zb, zs, mat, own))
            a2, b2 = s1 - t * (k + 1) / n, s1 - t * k / n
            P.append(Part(self.u(a2), self.u(b2), -hw, hw, zb, zs, mat, own))
        # roof: cap slabs following the plan, inset
        roofmat = lambda *a: self.roof
        inset = 0.16
        P.append(Part(self.u(s0 + t), self.u(s1 - t), -self.W + inset, self.W - inset, zs, zr, roofmat, own))
        for k in range(n):
            a, b = s0 + t * k / n, s0 + t * (k + 1) / n
            hw = self.half_width((a + b) / 2) - inset
            P.append(Part(self.u(a + 0.05), self.u(b), -hw, hw, zs, zr - 0.25 * (n - k) / n, roofmat, own))
            a2, b2 = s1 - t * (k + 1) / n, s1 - t * k / n
            P.append(Part(self.u(a2), self.u(b2 - 0.05), -hw, hw, zs, zr - 0.25 * (n - k) / n, roofmat, own))
        # a narrower crown so the arched roof reads as arched
        P.append(Part(self.u(s0 + t), self.u(s1 - t), -self.W * 0.55, self.W * 0.55, zr - 0.05, zr + 0.2,
                      roofmat, own))
        if S["roofbox"]:
            a, b = S["roofbox"]
            boxp = Paint(0x8E9295, top=0xB4B8BB)
            P.append(Part(self.u(a), self.u(b), -0.40, 0.40, zr, zm(S["zbox"]), lambda *x: boxp, own))
        if S["railcar"]:
            # roof headlights at both ends (lamp faces outwards)
            for front in (True, False):
                sc = s0 + 0.05 if front else s1 - 0.40
                face = "-u" if front else "+u"

                def lampmat(f, u, v, z, d, front=front, face=face):
                    if f == face and abs(v) < 0.11 and z > zr - 0.05:
                        return R.HEAD if front else Paint(0x6A6C6E)
                    return Paint(0x7E8285, top=0x9A9EA1)
                P.append(Part(self.u(sc), self.u(sc + 0.35), -0.17, 0.17, zr - 0.35, zr + 0.55, lampmat, own))
        if S["chimney"]:
            c = S["chimney"]
            P.append(Part(self.u(c - 0.12), self.u(c + 0.12), 0.05, 0.25, zr, zr + 0.7,
                          lambda *x: Paint(0x2A2A2C, top=0x1A1A1A), own))
            P.append(Part(self.u(c - 0.2), self.u(c + 0.2), 0.0, 0.30, zr + 0.6, zr + 0.8,
                          lambda *x: Paint(0x2A2A2C, top=0x3A3A3C), own))
        # underframe: solebar, wheels + axle boxes, engine, steps, buffers
        P.append(Part(self.u(s0 + 0.2), self.u(s1 - 0.2), -self.W + 0.10, self.W - 0.10, zb - 0.55, zb,
                      lambda *x: BLACK, own))
        for wc in S["wheels"]:
            def wmat(f, u, v, z, d):
                if f in ("+v", "-v") and 1.0 < z < 1.8:
                    return AXLEBOX
                return WHEEL
            P.append(Part(self.u(wc - 0.48), self.u(wc + 0.48), -self.W + 0.16, self.W - 0.16, 0.0, zb - 0.1,
                          wmat, own))
        if S["engine"]:
            a, b = S["engine"]
            P.append(Part(self.u(a), self.u(b), -0.62, 0.62, 0.9, zb, lambda *x: Paint(0x303235), own))
        else:
            # battery / stove boxes of the trailer
            P.append(Part(self.u(5.3), self.u(6.9), -0.55, 0.55, 1.1, zb, lambda *x: Paint(0x303235), own))
        # steps under the doors (yellow edge), both sides
        for (a, b) in S["doors"]:
            for (aa, bb) in ((a, b), (S["lob"] - b, S["lob"] - a)):
                hw = self.half_width((aa + bb) / 2)

                def smat(f, u, v, z, d):
                    if f in ("+v", "-v", "-u", "+u") and z < 1.45:
                        return YELLOW
                    return BLACK
                P.append(Part(self.u(aa + 0.05), self.u(bb - 0.05), -hw + 0.04, hw - 0.04, 1.05, zb, smat, own))
        # buffer beams + buffers
        for front in (True, False):
            if front:
                bs, be = 0.0, s0
            else:
                bs, be = s1, S["lob"]
            eh = S["end_half"]
            beam = self.body if S["railcar"] else BLACK
            P.append(Part(self.u(s0 - 0.10) if front else self.u(s1), self.u(s0) if front else self.u(s1 + 0.10),
                          -eh - 0.12, eh + 0.12, zb - 0.6, zb + 0.35, lambda *x: beam, own))
            for vc in (-0.60, 0.60):
                P.append(Part(self.u(bs + (0.02 if front else 0.0)), self.u(be - (0.0 if front else 0.02)),
                              vc - 0.12, vc + 0.12, zm(0.93), zm(1.18), lambda *x: BUFFER, own))
        return P

    def lines(self):
        """hand rails beside the doors (both sides)."""
        S, own = self.S, self.owner
        L = []
        z0, z1 = zm(S["zb"]) + 0.6, zm(S["win"][1]) - 0.2
        for (a, b) in S["doors"]:
            # rail on the body side of each door, both sides of the car
            for (sa, sgn) in ((b + 0.08, 1), (S["lob"] - (b + 0.08), -1)):
                hw = self.half_width(sa) + 0.02
                uu = self.u(sa)
                L.append(((uu, sgn * hw, z0), (uu, sgn * hw, z1), RAIL, own))
        return L


def render_rows(spec):
    car = Car(spec, "C")
    parts, lines = car.parts(), []
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"C"}) for d in DIRS]]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for spec, fn in ((M131, "m131"), (BLM, "blm")):
        rows = render_rows(spec)
        R.save_rows(rows, os.path.join(out, fn + ".png"))
        R.preview(rows, os.path.join(out, fn + "_prev.png"), z=5, labels=[spec["name"]])
        print("wrote", fn)
