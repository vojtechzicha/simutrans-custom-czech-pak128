"""DP Ostrava Solaris buses and trolleybuses (Urbino II/III/IV bodies) as one
parametric model on the DPMHK box renderer (dpmhk.py, render.py).

Families (vehicle-bus/dpo/, vehicle-trolleybus/dpo/):
  solarisurbino10_s3 / 12_s3 / 15_s3 / 18_s3   Urbino III, old blue-white-yellow
  solarisurbino12_s4 / 12_s4_electric / 18_s4  Urbino IV, turquoise
  26trsolaris(_partial), 27trsolaris            Skoda 26Tr / 27Tr, Urbino III body, turquoise
  27trsolaris_partial                           Skoda 27Tr of 2024, Urbino IV body, turquoise
  solaristrollino_12ac / 15ac / 18ac            Solaris Trollino (II / III), old scheme

Geometry follows dpmhk.py: single vehicles at their real length, articulated
sections at 4/3 m per carunit with the real joint on the section boundary,
positions in the specs in REAL metres from the front. Every vehicle (single
ones too) is placed by the section rule of CLAUDE.md: its body is shifted
(4 - length/2) carunits along travel from the native 12 m footprint
(dpmhk.ORIGINS), so its front sits where the front of a native 12 m bus sits.

What is drawn (photos in the 2026-10-18 DPO audit):
- Urbino II / III face: black windscreen mask with a "smile" at the bottom,
  III with the rounded dome over the destination display (two narrower boxes on
  the roof front); II (Trollino 12) flat-topped.
- Urbino IV face: raked black front cap (the front cut back in steps above the
  nose), the black frieze over the windows with the body colour coming down in
  slanted wedges under the roof fairings, black rear corner wedges.
- Doors on the right only: 2-2-2 (U10 1-2-2, door 1 single-leaf), U18 2-2-2-2.
- Engine tower (black louvred panel instead of the last left window) on the
  diesel / CNG buses only.
- Roof kits per type: AC pods, CNG / battery / traction fairings, battery boxes,
  hatches, retriever racks; poles aimed at the pak128.cs trolleybus wire of the
  own lane (dpmhk.WIRES = elec_trolleybus_plain_* wire art), in the
  photographed colours.
- Liveries: dpomodrozluta (blue roof edge, white band, black windows, white
  panel, orange-yellow stripe, blue skirt) and dpotyrkysova (the DPO palette of
  tools/tramrender/dpo_palette.py: body 00ADD6, roof 44C1E4, black window band,
  white line under the windows). Side faces are flat (one colour in every view).
- Glass: passenger and door glass on the lit-at-night specials (4D4D4D, 57656F
  as the reflection row); windscreen and driver's window plain.

usage: python tools/busrender/dpo_solaris.py [family ...] [--preview DIR] [--opt key=value ...]
       python tools/busrender/dpo_solaris.py [family ...] --variants DIR
The look options (OPTS) are the choices put to the owner: the Urbino III dome
and the Urbino IV cap bold or subtle, the turquoise fairing tops in the roof
colour or a step lighter, the Trollino 12 / 15 roof white (photos) or blue.
--variants writes every family an option changes with its other value into
DIR/<option>-<value>/ and leaves sprites/ alone.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dpmhk as H                                                       # noqa: E402
from render import Box, render, DIRS                                    # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
KCU = H.KCU
HW = H.HW
T = H.T


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# ------------------------------------------------------------------ palette
# turquoise (tools/tramrender/dpo_palette.py)
TQ = rgb(0x00ADD6)
TQ_ROOF = rgb(0x44C1E4)
TQ_SHOULDER = rgb(0x22B7DD)        # the one in-between step at the roof edge
TQ_FAIR_HI = rgb(0x6ACFEB)         # contrast variant: fairing tops a step lighter
WHITE = rgb(0xECEEEE)
MASK = rgb(0x1A1C1E)
CAB_GLASS = rgb(0x34444E)          # plain (never lit): windscreen, driver's window
CAB_GLASS_TOP = rgb(0x40525C)
PILLAR = rgb(0x121314)
# old scheme (dpomodrozluta), from the 7518 / 7519 photos
OB = rgb(0x2468C0)                 # skirt, bumper, roof-edge band, rear frame
OB_ROOF = rgb(0x5596DC)            # roof top: medium blue
OB_SHOULDER = rgb(0x3C7FCE)
ORANGE = rgb(0xF5A21E)             # the thin orange-yellow stripe, one colour everywhere
OWHITE = rgb(0xEEEEEC)
ROOFW = rgb(0xEAEAE8)              # white Trollino roof
ROOFW_SIDE = rgb(0xD6D8D8)
# common
GLASS = H.GLASS                    # 4D4D4D special
GLASS2 = H.GLASS2                  # 57656F special
HEADL = H.HEADL
TAILL = H.TAILL
AMBER = rgb(0xF0961E)              # DPO orange LED displays
SILVER = rgb(0xB4B8BC)
STEP = rgb(0x505256)
LOUVRE = rgb(0x5C5E62)
HATCH = rgb(0x2A2C30)
BATT = rgb(0xA6AAAE)
BATT_SIDE = rgb(0x84888C)
ACW = rgb(0xEEEEEE)
ACW_SIDE = rgb(0xD2D4D6)
GRILLE = rgb(0x8A8E94)
RAIL = rgb(0x9A9EA4)
RAIL_HI = rgb(0xC6CACE)

FLAT = {"top": 1.0, "right": 1.0, "left": 1.0, "front": 0.92, "rear": 0.92}
POD = {"top": 1.0, "right": 1.0, "left": 1.0, "front": 0.9, "rear": 0.9}


def sh(c, f, tab=FLAT):
    k = tab.get(f, 1.0)
    return tuple(int(max(0, min(255, round(v * k)))) for v in c)


def inr(v, a, b):
    return a <= v < b


# ------------------------------------------------------------------ options
# the look choices the owner picks from (preview variants)
OPTS = {
    "dome": "bold",          # Urbino III dome over the display: bold | subtle
    "cap": "bold",           # Urbino IV raked cap: bold | subtle
    "fairtop": "roof",       # turquoise fairing tops: roof (44C1E4) | light (a step lighter)
    "trollino_roof": "white",  # Trollino 12 / 15 roof: white (photos) | blue
}
# (length, half width, height above the roof) per tier, from the widest
DOME = {"bold": [(1.80, 1.05, 0.22), (1.25, 0.78, 0.42), (0.65, 0.48, 0.60)],
        "subtle": [(1.20, 0.90, 0.16), (0.60, 0.55, 0.26)]}
# (z from, z to, setback of the front from the bumper line) per step, one pixel row each
RAKE = {"bold": [(1.30, 1.55, 0.10), (1.55, 1.80, 0.20), (1.80, 2.05, 0.32), (2.05, 2.30, 0.44),
                 (2.30, 2.55, 0.56), (2.55, 2.80, 0.70), (2.80, 9.0, 0.85)],
        "subtle": [(1.30, 1.80, 0.08), (1.80, 2.30, 0.18), (2.30, 2.80, 0.30), (2.80, 9.0, 0.42)]}

# ------------------------------------------------------------------ bodies
# real metres from the front; doors on the right; z: 0.25 m = one pixel row
# z0 0.30 skirt bottom | 0.80 stripe | 1.05 white | 1.30 windows | 2.55 cant | 2.80 roof edge | 3.05 roof
BASE = dict(z0=0.30, zr=3.05, zwin0=1.30, zwin1=2.55, zband0=1.30, zband1=2.80, cap=0.0,
            pods=[], mirrors=True, joints=[], cu=[8], rear="u3", tower=False, kit=[], hatches=[],
            single=[], frieze=[], poles=None, rack=None, polecol=None, lens=None)


def mk(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


U10 = mk(BASE, face="u3", real_len=9.94, axles=[2.08, 6.88],
         doors=[(0.40, 1.22), (3.78, 5.08), (7.95, 9.25)], single=[0],
         drv=(0.30, 1.55), sidedisp=(1.40, 2.90))
U12 = mk(BASE, face="u3", real_len=12.0, axles=[2.70, 8.60],
         doors=[(0.30, 1.58), (4.95, 6.25), (9.35, 10.65)],
         drv=(0.30, 1.65), sidedisp=(1.75, 3.25))
U15 = mk(BASE, face="u3", real_len=14.59, axles=[2.70, 9.50, 11.19],
         doors=[(0.30, 1.58), (5.25, 6.55), (11.90, 13.20)],
         drv=(0.30, 1.65), sidedisp=(1.75, 3.25))
U18_3 = mk(BASE, face="u3", real_len=18.0, joints=[10.10], cu=[8, 6], axles=[2.70, 7.83, 14.60],
           doors=[(0.30, 1.58), (4.50, 5.80), (10.75, 12.05), (15.30, 16.60)],
           drv=(0.30, 1.65), sidedisp=(1.75, 3.25))
U18_4 = mk(U18_3, face="u4", rear="u4", axles=[2.70, 8.60, 14.60], joints=[10.20],
           doors=[(0.30, 1.58), (4.95, 6.25), (10.85, 12.15), (15.30, 16.60)])

# frieze: real-metre spans where the body colour comes down over the black
# frieze of the Urbino IV (under the roof fairing), as (front edge, rear edge)
FRIEZE12 = [(3.40, 8.40)]
FRIEZE18 = [(3.40, 10.20), (10.20, 10.90)]

MODELS = {
    # Urbino 10 III diesel (7505-7524): blue AC pod at the front, two hatches, engine tower
    "u10": mk(U10, tower=True, kit=[dict(a=0.85, b=2.25, h=0.26, hw=0.62, kind="ac")],
              hatches=[4.30, 6.90]),
    # Urbino 12 III diesel (7725-7787)
    "u12_3": mk(U12, tower=True, kit=[dict(a=0.85, b=2.45, h=0.26, hw=0.66, kind="ac")],
                hatches=[4.80, 8.20]),
    # Urbino 12 III CNG (7121-7190; no object of its own, preview only): blue gas fairing
    "u12_3cng": mk(U12, tower=True, kit=[dict(a=1.20, b=8.70, h=0.42, hw=1.06, kind="fair", rf=0.8, rr=0.4)]),
    # Urbino 12 IV CNG (7211-7275): long gas fairing sloping down to the front, saloon AC behind it
    "u12_4": mk(U12, face="u4", rear="u4", tower=True, frieze=FRIEZE12,
                kit=[dict(a=2.30, b=9.40, h=0.44, hw=1.08, kind="fair", rf=1.30, rr=0.40),
                     dict(a=9.80, b=11.30, h=0.24, hw=0.80, kind="fair")]),
    # Urbino 12 IV electric (5008-5031): battery fairing, OppCharge contact rails, no tower
    "u12_4e": mk(U12, face="u4", rear="u4", frieze=FRIEZE12,
                 kit=[dict(a=2.00, b=10.60, h=0.42, hw=1.08, kind="fair", rf=0.90, rr=0.60)]
                 + [dict(a=2.25, b=3.35, h=0.18, hw=0.07, t=t, z0=0.42, kind="rail") for t in (-0.55, -0.2, 0.2, 0.55)]),
    # Urbino 15 III diesel (7617-7625): white AC pod at the front, tandem rear axles
    "u15": mk(U15, tower=True, kit=[dict(a=0.85, b=2.60, h=0.28, hw=0.70, kind="acw")],
              hatches=[5.0, 9.0, 12.4]),
    # Urbino 18 III diesel (7801-7807): blue AC pod on the front section
    "u18_3": mk(U18_3, tower=True, kit=[dict(a=0.85, b=2.45, h=0.26, hw=0.66, kind="ac")],
                hatches=[5.2, 8.6, 13.0, 16.4]),
    # Urbino 18 IV CNG (7866-7922): gas fairing on the front section, AC on the rear one
    "u18_4": mk(U18_4, tower=True, frieze=FRIEZE18,
                kit=[dict(a=2.30, b=9.50, h=0.44, hw=1.08, kind="fair", rf=1.30, rr=0.40),
                     dict(a=12.30, b=13.90, h=0.26, hw=0.85, kind="fair")]),
    # Skoda 26Tr (Urbino III 12 m): driver AC, long traction fairing, poles behind it, saloon AC
    "26tr": mk(U12, kit=[dict(a=0.30, b=1.45, h=0.20, hw=0.70, kind="fair"),
                         dict(a=1.65, b=6.25, h=0.46, hw=1.04, kind="fair", rf=0.45, rr=0.30),
                         dict(a=9.40, b=10.90, h=0.24, hw=0.78, kind="fair")],
               poles=(6.70, 0.30), polecol="26tr"),
    # 26Tr with traction batteries (3731-3740): shorter fairing with a battery box on it,
    # poles further forward, saloon AC and a second battery box at the rear
    "26trp": mk(U12, kit=[dict(a=0.30, b=1.35, h=0.20, hw=0.70, kind="fair"),
                          dict(a=1.50, b=5.55, h=0.42, hw=1.04, kind="fair", rf=0.40, rr=0.30),
                          dict(a=2.20, b=4.90, h=0.20, hw=0.80, z0=0.42, kind="batt"),
                          dict(a=8.40, b=9.80, h=0.24, hw=0.78, kind="fair"),
                          dict(a=10.10, b=11.50, h=0.24, hw=0.82, kind="batt")],
                poles=(6.05, 0.30), polecol="26tr"),
    # Skoda 27Tr (Urbino III 18 m, 3802-3812): fairing over the rear of the front section, poles
    # 1.3 m behind the joint, grey retriever rack over the rear
    "27tr": mk(U18_3, kit=[dict(a=0.30, b=1.40, h=0.20, hw=0.70, kind="fair"),
                           dict(a=4.70, b=9.55, h=0.44, hw=1.04, kind="fair", rf=0.50, rr=0.0),
                           dict(a=10.65, b=11.95, h=0.40, hw=1.00, kind="fair", rf=0.0, rr=0.30)],
               poles=(11.40, 0.30), rack=(14.40, 17.30, 0.30), polecol="27tr"),
    # Skoda 27Tr of 2024 (Urbino IV 18 m, traction batteries): grey battery boxes on the rear section
    "27trp": mk(U18_4, frieze=FRIEZE18,
                kit=[dict(a=1.90, b=9.55, h=0.44, hw=1.06, kind="fair", rf=1.10, rr=0.0),
                     dict(a=10.70, b=12.00, h=0.40, hw=1.00, kind="fair", rf=0.0, rr=0.30),
                     dict(a=12.70, b=14.30, h=0.26, hw=0.86, kind="batt"),
                     dict(a=14.70, b=16.90, h=0.26, hw=0.86, kind="batt")],
                poles=(11.40, 0.30), polecol="27tr"),
    # Solaris Trollino 12 AC (Urbino II face): white AC dome, traction fairing, poles mid-roof
    "tr12": mk(U12, face="u2", kit=[dict(a=0.55, b=1.85, h=0.28, hw=0.70, kind="acw"),
                                    dict(a=2.20, b=6.05, h=0.40, hw=1.00, kind="fair", rf=0.35, rr=0.30),
                                    dict(a=9.10, b=10.70, h=0.22, hw=0.80, kind="fair")],
               poles=(6.45, 0.30), polecol="trollino"),
    # Solaris Trollino 15 AC (3601): long fairing, poles above the tandem, resistor rack at the rear
    "tr15": mk(U15, kit=[dict(a=0.55, b=1.95, h=0.28, hw=0.70, kind="acw"),
                         dict(a=2.40, b=9.90, h=0.40, hw=1.00, kind="fair", rf=0.40, rr=0.30)],
               poles=(10.40, 0.30), rack=(11.30, 13.90, 0.30), polecol="trollino"),
    # Solaris Trollino 18 AC (3801): long fairing on the front section, poles behind the joint
    "tr18": mk(U18_3, kit=[dict(a=0.55, b=1.85, h=0.26, hw=0.70, kind="ac"),
                           dict(a=2.20, b=9.55, h=0.42, hw=1.04, kind="fair", rf=0.40, rr=0.0),
                           dict(a=10.65, b=11.95, h=0.40, hw=1.00, kind="fair", rf=0.0, rr=0.30)],
               poles=(11.30, 0.30), rack=(14.40, 17.30, 0.30), polecol="trollino"),
}

# pole colour along the pole: list of (fraction from the base, colour); the tip pixel last
POLECOL = {
    "trollino": ([(0.30, rgb(0x1E1E20)), (1.01, rgb(0xF2C800))], rgb(0x2A2A2C)),   # black foot, yellow
    "26tr": ([(0.86, rgb(0xA4A8AC)), (1.01, rgb(0xF2C800))], rgb(0xF2C800)),       # silver-grey, yellow tips
    "27tr": ([(0.45, rgb(0xF0F0EE)), (0.70, rgb(0xB4B6B8)), (1.01, rgb(0x5A5C60))], rgb(0x3A3C40)),  # white to dark grey
}
POLEBASE = rgb(0x404246)


# ------------------------------------------------------------------ vehicle
class Solaris(H.Veh):
    def __init__(self, sp, livery, opts):
        self.opts = opts
        super().__init__(sp, livery)
        M = self.M
        self.kitm = []
        for k in sp["kit"]:
            self.kitm.append(dict(k, a=M(k["a"]), b=M(k["b"])))
        self.hatchm = [M(x) for x in sp["hatches"]]
        self.friezem = [(M(a), M(b)) for a, b in sp["frieze"]]
        self.single_doors = set(sp["single"])
        self.rake = RAKE[opts["cap"]] if self.face == "u4" else []
        self.sbmax = max((sb for _, _, sb in self.rake), default=0.0)
        self.dome = DOME[opts["dome"]] if self.face == "u3" else []
        self.STEPC = STEP

    # ------------------------------------------------------------ livery
    def setup_livery(self):
        L = self.liv
        if L == "tq":
            self.BODY, self.ROOF, self.EDGE, self.SHOULDER = TQ, TQ_ROOF, TQ, TQ_SHOULDER
            self.FAIR_TOP = TQ_FAIR_HI if self.opts["fairtop"] == "light" else TQ_ROOF
            self.FAIR_SIDE = TQ
        else:
            white = L == "oldw"
            self.BODY = OB
            self.ROOF = ROOFW if white else OB_ROOF
            self.EDGE = OB
            self.SHOULDER = OB if white else OB_SHOULDER
            self.FAIR_TOP = ROOFW if white else OB_ROOF
            self.FAIR_SIDE = ROOFW_SIDE if white else OB

    @property
    def old(self):
        return self.liv != "tq"

    # ------------------------------------------------------------ geometry
    def boxes(self, i, body_only=False):
        L = self.sec_len(i)
        U0, U1 = self.U[i], self.U[i + 1]
        last = len(self.cu) - 1
        s_of = lambda u: U1 - u
        hb = self.BW / 2
        front_b = hb if i > 0 else 0.0
        rear_b = hb if i < last else 0.0
        bx = []
        if i == 0 and self.rake:
            sm = self.sbmax
            bx.append(Box("body%d" % i, rear_b, L - sm, -HW, HW, self.Z0, self.ZR))
            bx.append(Box("nose", L - sm, L, -HW, HW, self.Z0, self.rake[0][0]))
            for k, (z0, z1, sb) in enumerate(self.rake):
                if sb < sm - 1e-6:
                    bx.append(Box("nose", L - sm, L - sb, -HW, HW, z0, min(z1, self.ZR)))
        else:
            bx.append(Box("body%d" % i, rear_b, L - front_b, -HW, HW, self.Z0, self.ZR))
        if body_only:
            return bx
        if front_b:
            bx.append(Box("bell_f", L - front_b, L, -HW + 0.06, HW - 0.06, self.Z0 + 0.04, self.ZR - 0.04))
        if rear_b:
            bx.append(Box("bell_r", 0.0, rear_b, -HW + 0.06, HW - 0.06, self.Z0 + 0.04, self.ZR - 0.04))
        # roof kit (pods, fairings with stepped ends, battery boxes, rails)
        lo_lim = U0 + (hb if i > 0 else 0.0)
        hi_lim = U1 - (hb if i < last else 0.0)
        for k, p in enumerate(self.kitm):
            for a, b, z0, z1 in self.kit_pieces(p):
                a2, b2 = max(a, lo_lim), min(b, hi_lim)
                if b2 > a2 + 0.05:
                    t = p.get("t", 0.0)
                    bx.append(Box("kit%d" % k, s_of(b2), s_of(a2), t - p["hw"], t + p["hw"],
                                  self.ZR + z0, self.ZR + z1))
        # Urbino III dome over the destination display
        if i == 0:
            for k, (dl, dhw, dh) in enumerate(self.dome):
                z0 = self.ZR + (self.dome[k - 1][2] if k else 0.0)
                bx.append(Box("dome%d" % k, L - dl, L, -dhw, dhw, z0, self.ZR + dh))
        if self.rack:
            a, b = self.M(self.rack[0]), self.M(self.rack[1])
            a, b = max(a, U0), min(b, U1)
            if b > a:
                zt = self.ZR + self.rack[2]
                for sg in (-1, 1):
                    t0 = sg * (HW - 0.34)
                    bx.append(Box("rail", s_of(b), s_of(a), min(t0, t0 + sg * 0.16), max(t0, t0 + sg * 0.16),
                                  zt - 0.14, zt))
                for q in (a, (a + b) / 2, b):
                    if U0 <= q - 0.22 and q <= U1:
                        bx.append(Box("rail", s_of(q), s_of(q) + 0.22, -HW + 0.34, HW - 0.34, zt - 0.14, zt))
        if self.poles:
            pb = self.M(self.poles[0])
            if U0 <= pb < U1:
                top = self.roof_top(pb)
                bx.append(Box("polebase", s_of(pb) - 0.55, s_of(pb) + 0.55, -0.55, 0.55, top, top + 0.16))
        for k, a in enumerate(self.axles):
            if U0 <= a < U1:
                bx.append(Box("wheel%d" % k, s_of(a) - 0.62, s_of(a) + 0.62, -HW + 0.07, HW - 0.07, 0.0, 1.12,
                              faces={"left", "right"}))
        if i == 0 and self.sp["mirrors"]:
            sm = self.setback(2.3)
            for t0, t1 in ((-HW - 0.12, -HW + 0.02), (HW - 0.02, HW + 0.12)):
                bx.append(Box("mirror", L - sm - 0.10, L - sm + 0.22, t0, t1, 2.05, 2.65,
                              faces={"front", "right", "left", "top"}))
        return bx

    def kit_pieces(self, p):
        """(a, b, z0, z1) in drawn metres; fairings get lower steps at the ends"""
        a, b, h, z0 = p["a"], p["b"], p["h"], p.get("z0", 0.0)
        rf, rr = p.get("rf", 0.0), p.get("rr", 0.0)
        out = []
        if rf > 0:                     # the front end slopes down to the roof in steps
            n = 3 if rf >= 0.9 else 2
            for k in range(n):
                out.append((a + rf * k / n, a + rf * (k + 1) / n, z0, z0 + h * (k + 1) / (n + 1)))
        out.append((a + rf, b - rr, z0, z0 + h))
        if rr > 0:
            out.append((b - rr, b, z0, z0 + h * 0.55))
        return out

    def on_ramp(self, k, u):
        """u lies on a sloped end of fairing k (its stepped end faces read as one slope)"""
        rf, rr = k.get("rf", 0.0), k.get("rr", 0.0)
        return (rf > 0 and u < k["a"] + rf + 0.02) or (rr > 0 and u > k["b"] - rr - 0.02)

    def setback(self, z):
        for z0, z1, sb in self.rake:
            if z0 <= z < z1:
                return sb
        return 0.0

    def roof_top(self, u):
        top = self.ZR
        for p in self.kitm:
            for a, b, z0, z1 in self.kit_pieces(p):
                if a <= u <= b and p["kind"] != "rail":
                    top = max(top, self.ZR + z1)
        return top

    # ------------------------------------------------------------ textures
    def tex_for(self, i):
        U1 = self.U[i + 1]
        last = len(self.cu) - 1

        def tex(p):
            u = U1 - p.s
            self.curU1 = U1
            self.cur_i = i
            b = p.box
            if b.startswith("wheel"):
                return self.tex_wheel(p, u)
            if b.startswith("bell"):
                return self.tex_bellows(p, u)
            if b == "polebase":
                return sh(POLEBASE, p.face, POD)
            if b == "rail":
                return sh(RAIL, p.face, POD)
            if b == "mirror":
                return sh(MASK, p.face)
            if b.startswith("kit"):
                return self.tex_kit(p, u, self.kitm[int(b[3:])])
            if b.startswith("dome"):
                return self.tex_dome(p, u, int(b[4:]))
            f = p.face
            if b == "nose":
                if f == "front":
                    return self.tex_front(p)
                if f == "top":
                    return self.tex_front(p, dz=-0.02)
                return self.tex_side(p, u, U1)
            if f == "top":
                return self.tex_roof(p, u)
            if f in ("left", "right"):
                return self.tex_side(p, u, U1)
            if f == "front":
                return self.tex_front(p) if i == 0 else sh(H.BELLOWS_D, f)
            return self.tex_rear(p) if i == last else sh(H.BELLOWS_D, f)
        return tex

    def tex_kit(self, p, u, k):
        f = p.face
        kind = k["kind"]
        if kind == "rail":
            return RAIL_HI if f == "top" else RAIL
        if kind == "batt":
            if f == "top":
                return BATT if int((u * 3.0)) % 2 == 0 or abs(p.t) > k["hw"] - 0.2 else rgb(0x9A9EA2)
            return sh(BATT_SIDE, f, POD)
        if kind == "acw" or (kind == "ac" and self.liv == "oldw"):
            if f == "top":
                return GRILLE if abs(p.t) < 0.22 else ACW
            return sh(ACW_SIDE, f, POD)
        if kind == "ac":
            top, side = (self.FAIR_TOP, self.FAIR_SIDE)
            if f == "top":
                return GRILLE if abs(p.t) < 0.20 else top
            return sh(side, f, POD)
        # fairing; the steps of a sloped end show their faces in the top colour
        if f == "top" or (f in ("front", "rear") and self.on_ramp(k, u)):
            return self.FAIR_TOP
        return sh(self.FAIR_SIDE, f, POD)

    def tex_dome(self, p, u, k):
        """the dome is roof-coloured; the black mask arches up into the cap row below it"""
        if p.face == "top":
            return self.ROOF
        return sh(self.EDGE, p.face)

    def tex_roof(self, p, u):
        t = abs(p.t)
        if self.rake and u < self.sbmax + 0.45 and self.cur_i == 0:
            return MASK                                   # IV: the black cap runs onto the roof
        for hx in self.hatchm:
            if abs(u - hx) < 0.34 and t < 0.32:
                return HATCH
        if t > HW - 0.30:
            return self.SHOULDER
        return self.ROOF

    def door_at(self, u):
        for k, (d0, d1) in enumerate(self.doors):
            if d0 <= u < d1:
                return k, d0, d1
        return None

    def end_lamp(self, p, u, U1):
        """head / tail light wrapping round the body corner onto the side"""
        i = self.cur_i
        z = p.z
        lo, hi = p.rng(0)                 # s range of the pixel (s = 0 rear .. L front)
        L = self.sec_len(i)
        if i == 0 and hi >= L - self.setback(z) - 0.16 and inr(z, 0.55, 0.80):
            return HEADL
        if i == len(self.cu) - 1 and lo <= 0.16 and inr(z, 0.55, 1.05):
            return TAILL
        return None

    def tex_side(self, p, u, U1):
        z, f = p.z, p.face
        right = f == "right"
        for a in self.axles:
            if abs(u - a) < 0.62 and z < 1.02 and math.hypot(u - a, z - self.WR) < 0.62:
                return None
        lamp = self.end_lamp(p, u, U1)
        if lamp:
            return lamp
        i = self.cur_i
        front = i == 0
        Uend = self.U[-1]
        # front corner: the black mask wraps round the A-pillar
        if front:
            sb = self.setback(z)
            if self.face == "u4" and u < self.sbmax + 0.30 and z >= self.ZWIN0:
                return MASK
            if self.face in ("u3", "u2") and u < sb + 0.22 and inr(z, self.ZWIN0, self.ZWIN1 + 0.25):
                return MASK
        # rear corner wedge of the Urbino IV
        if self.face == "u4" and i == len(self.cu) - 1:
            if inr(z, self.ZWIN0 - 0.50, self.ZWIN0) and u > Uend - 0.30 - 0.9 * (z - (self.ZWIN0 - 0.50)):
                return MASK
        if right:
            d = self.door_at(u)
            if d and z < self.ZWIN1:
                return self.tex_door(p, u, U1, d)
        tw = self.tower_at(u, right)
        if tw and inr(z, self.ZWIN0, self.ZWIN1):
            return MASK if int(round((z - self.ZWIN0) / 0.25)) % 2 == 0 else LOUVRE
        if inr(z, self.ZWIN0, self.ZWIN1):
            return self.window(p, u, U1, right)
        if z >= self.ZWIN1:
            return self.cant(p, u, right)
        return self.lower(p, u, right)

    def tower_at(self, u, right):
        if right or not self.sp["tower"]:
            return False
        Uend = self.U[-1]
        return Uend - 1.30 <= u < Uend - 0.25

    def tex_door(self, p, u, U1, d):
        k, d0, d1 = d
        z = p.z
        if self.ln(p, U1, d0 + 0.02) or self.ln(p, U1, d1 - 0.02):
            return PILLAR
        if k not in self.single_doors and self.ln(p, U1, (d0 + d1) / 2):
            return PILLAR
        if p.rng(2)[0] < self.Z0 + 0.14:
            return STEP
        if z >= self.ZWIN1 - 0.12:
            return PILLAR
        if z >= self.ZWIN1 - 0.37:
            return GLASS2
        return GLASS

    def window(self, p, u, U1, right):
        z = p.z
        if right and inr(u, *self.sidedisp) and z >= self.ZWIN1 - 0.25:
            return AMBER
        i = self.cur_i
        U0s, U1s = self.U[i], self.U[i + 1]
        a = U0s + (self.BW / 2 if i > 0 else 0.25)
        b = U1s - (self.BW / 2 if i < len(self.cu) - 1 else 0.25)
        if not (a + 0.08 <= u < b - 0.08):
            return PILLAR
        if self.ln(p, U1, a + 0.10) or self.ln(p, U1, b - 0.10):
            return PILLAR
        if not right and i == 0 and inr(u, *self.drv):
            if self.ln(p, U1, self.drv[1]):
                return PILLAR
            return CAB_GLASS_TOP if z >= self.ZWIN1 - 0.25 else CAB_GLASS
        stops = [a, b]
        if right:
            for d0, d1 in self.doors:
                if a < d0 < b:
                    stops.append(d0)
                if a < d1 < b:
                    stops.append(d1)
        elif i == 0:
            stops.append(self.drv[1])
        if not right and self.sp["tower"] and i == len(self.cu) - 1:
            stops.append(self.U[-1] - 1.30)
        stops = sorted(stops)
        for q0, q1 in zip(stops[:-1], stops[1:]):
            if q0 <= u < q1:
                n = max(1, int(round((q1 - q0) / 1.45)))
                for k in range(1, n):
                    if self.ln(p, U1, q0 + (q1 - q0) * k / n):
                        return PILLAR
                if self.ln(p, U1, q0 + 0.02) or self.ln(p, U1, q1 - 0.02):
                    return PILLAR
                break
        return GLASS2 if z >= self.ZWIN1 - 0.25 else GLASS

    def in_frieze_gap(self, u, z):
        """Urbino IV: is (u, z) on the body-colour wedge that comes down over the frieze?
        The wedge edges slant forward with depth (the colour comes down toward the front)."""
        dz = (self.ZR - z)                 # 0 at the roof edge .. 0.5 at the window top
        for a, b in self.friezem:
            if a - 0.9 * dz <= u < b - 0.9 * dz:
                return True
        return False

    def cant(self, p, u, right):
        """side above the windows (z >= ZWIN1)"""
        f = p.face
        z = p.z
        if self.face == "u4":
            if self.in_frieze_gap(u, z):
                return self.BODY
            return MASK
        if self.old:
            if z < self.ZWIN1 + 0.25:
                return OWHITE
            return self.EDGE
        return self.BODY

    def lower(self, p, u, right):
        z = p.z
        if self.old:
            if z < self.Z0 + 0.50:
                return OB
            if z < self.Z0 + 0.75:
                return ORANGE
            return OWHITE
        if z >= self.ZWIN0 - 0.25:
            return WHITE
        return TQ

    # ---------------- front / rear faces ---------------------------------
    def tex_front(self, p, dz=0.0):
        t, z = p.t, p.z + dz
        f = "front"
        a = abs(t)
        old = self.old
        face = self.face
        body = self.BODY
        if z < 0.55:
            return sh(body, f)
        if z < 0.80:                                    # headlight row
            if a > HW - 0.46:
                if a < HW - 0.12:
                    return HEADL
                return sh(SILVER, f)
            if face == "u4":
                return sh(body, f)
            return sh(SILVER if old else body, f)
        if z < 1.05:                                    # stripe through the headlight tops
            return ORANGE if old else WHITE
        if z < 1.30:
            if face in ("u3", "u2") and a < 0.62:
                return MASK                             # the mask's "smile"
            return sh(OWHITE if old else body, f)
        if z < 2.55:
            if a > HW - 0.12:
                return MASK
            return CAB_GLASS_TOP if z >= 2.30 else CAB_GLASS
        if z < 2.80:
            if a < 0.95:
                return AMBER if z < 2.75 else MASK
            return MASK
        # roof cap
        if face == "u4":
            return MASK
        if face == "u3" and a < 0.62:
            return MASK                                 # the mask arches into the dome
        return sh(self.EDGE, f)

    def tex_rear(self, p):
        t, z = p.t, p.z
        f = "rear"
        a = abs(t)
        old = self.old
        diesel = self.sp["tower"]
        body = self.BODY
        if a > HW - 0.28 and inr(z, 0.55, 1.05):
            return TAILL
        if z < 0.80:
            return sh(body, f)
        if z < 1.05:
            return ORANGE if old else WHITE
        zg0 = 1.55 if diesel else 1.30                  # engine lid under the rear window
        if z < zg0:
            if self.face == "u4":
                return sh(body, f)
            return sh(OWHITE if old else body, f)
        if self.face == "u4":
            if a > HW - 0.14 or z >= 2.55:
                if inr(z, 2.55, 2.80) and inr(t, -0.80, -0.20):
                    return AMBER
                return MASK
            return GLASS2 if z >= 2.30 else GLASS
        if z < 2.55:
            if a > HW - 0.22:
                return sh(self.EDGE if old else body, f)
            return GLASS2 if z >= 2.30 else GLASS
        if z < 2.80:
            if a > HW - 0.22:
                return sh(self.EDGE if old else body, f)
            if inr(t, -0.80, -0.20):
                return AMBER
            return MASK
        return sh(self.EDGE, f)


# ------------------------------------------------------------------ poles
def draw_poles(img, view, L, origin, bs, bz, bt, polecol):
    segs, tipc = POLECOL[polecol]
    for base, tip in H.pole_tips(view, L, origin, bs, bz, bt):
        if tip is None:
            print("  no wire for pole in", view)
            continue
        bx, by = int(math.floor(base[0])), int(math.floor(base[1]))
        pts = H.bresenham(bx, by, tip[2], tip[3])
        n = max(1, len(pts) - 1)
        for k, (x, y) in enumerate(pts):
            fr = k / n
            col = next(c for lim, c in segs if fr < lim)
            if 0 <= x < 128 and 0 <= y < 128:
                img[y, x] = col
        img[tip[3], tip[2]] = tipc


# ------------------------------------------------------------------ build
def build(sp, livery, lens, opts):
    m = Solaris(sp, livery, opts)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        yl = lens[i]
        tiles = []
        for d in DIRS:
            o = np.array(H.origin_for(d)) + (4 - yl / 2.0) * H.PER_CU[d]
            img, zb = render(d, m.boxes(i), m.tex_for(i), L, o)
            if m.poles:
                pb = m.M(m.poles[0])
                if m.U[i] <= pb < m.U[i + 1]:
                    s = m.U[i + 1] - pb
                    draw_poles(img, d, L, o, s, m.roof_top(pb) + 0.16, m.poles[1], sp["polecol"])
            tiles.append(img)
        rows.append(tiles)
    return rows


OLD, TQL = "old", "tq"
TRW = "trollino"     # old scheme on a Trollino 12 / 15: white or blue roof by OPTS["trollino_roof"]

# family dir -> (yaml lengths per section, {livery colour: [(model, livery key), ...]})
FAMILIES = {
    # dpotyrkysova: no DPO Urbino 10 ever ran in turquoise and the owner dropped it
    # (2026-10-19), but the saves still use the object; it stays until they are migrated
    "vehicle-bus/dpo/solarisurbino10_s3": ([7], {"dpomodrozluta": [("u10", OLD)], "dpotyrkysova": [("u10", TQL)]}),
    "vehicle-bus/dpo/solarisurbino12_s3": ([8], {"dpomodrozluta": [("u12_3", OLD)]}),
    "vehicle-bus/dpo/solarisurbino12_s4": ([8], {"dpotyrkysova": [("u12_4", TQL)]}),
    "vehicle-bus/dpo/solarisurbino12_s4_electric": ([8], {"dpotyrkysova": [("u12_4e", TQL)]}),
    "vehicle-bus/dpo/solarisurbino15_s3": ([10], {"dpomodrozluta": [("u15", OLD)]}),
    "vehicle-bus/dpo/solarisurbino18_s3": ([8, 6], {"dpomodrozluta": [("u18_3", OLD)]}),
    "vehicle-bus/dpo/solarisurbino18_s4": ([8, 6], {"dpotyrkysova": [("u18_4", TQL)]}),
    "vehicle-trolleybus/dpo/26trsolaris": ([8], {"dpotyrkysova": [("26tr", TQL)]}),
    "vehicle-trolleybus/dpo/26trsolaris_partial": ([8], {"dpotyrkysova": [("26trp", TQL)]}),
    "vehicle-trolleybus/dpo/27trsolaris": ([8, 6], {"dpotyrkysova": [("27tr", TQL)]}),
    "vehicle-trolleybus/dpo/27trsolaris_partial": ([8, 6], {"dpotyrkysova": [("27trp", TQL)]}),
    "vehicle-trolleybus/dpo/solaristrollino_12ac": ([8], {"dpomodrozluta": [("tr12", TRW)]}),
    "vehicle-trolleybus/dpo/solaristrollino_15ac": ([10], {"dpomodrozluta": [("tr15", TRW)]}),
    "vehicle-trolleybus/dpo/solaristrollino_18ac": ([8, 6], {"dpomodrozluta": [("tr18", OLD)]}),
}


def livery_key(liv, opts):
    if liv == TRW:
        return "oldw" if opts["trollino_roof"] == "white" else OLD
    return liv


def build_family(fam, opts):
    lens, livs = FAMILIES[fam]
    out = {}
    for color, parts in livs.items():
        rows = []
        for model, liv in parts:
            rows += build(MODELS[model], livery_key(liv, opts), lens, opts)
        out[color] = rows
    return out


def sheet(rows):
    a = np.zeros((128 * len(rows), 1024, 3), np.uint8)
    a[:] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    return a


def check_specials(a, label):
    flat = a.reshape(-1, 3).astype(np.int64)
    used = set(np.unique((flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]).tolist())
    bad = (used & H.SPECIAL) - H.ALLOWED
    if bad:
        raise SystemExit(f"{label}: unintended special colours {sorted(hex(b) for b in bad)}")


def parse_opts(args):
    opts = dict(OPTS)
    while "--opt" in args:
        i = args.index("--opt")
        k, v = args[i + 1].split("=", 1)
        if k not in opts:
            raise SystemExit(f"unknown option {k}")
        opts[k] = v
        del args[i:i + 2]
    return opts


# the other value of every look option, and the families it changes
CHOICES = {
    "dome": ("subtle", {"u3"}),
    "cap": ("subtle", {"u4"}),
    "fairtop": ("light", {"tq"}),
    "trollino_roof": ("blue", {"trollino"}),
}


def affected(fam, key):
    tags = CHOICES[key][1]
    for parts in FAMILIES[fam][1].values():
        for model, liv in parts:
            if MODELS[model]["face"] in tags or liv in tags:
                return True
    return False


def write_variants(out, names):
    """every family a look option changes, rendered with the option's other value,
    into out/<option>-<value>/; sprites/ stays untouched"""
    for key, (val, _) in CHOICES.items():
        opts = dict(OPTS, **{key: val})
        d = os.path.join(out, f"{key}-{val}")
        os.makedirs(d, exist_ok=True)
        for fam in FAMILIES:
            name = fam.split("/")[-1]
            if (names and name not in names) or not affected(fam, key):
                continue
            for color, rows in build_family(fam, opts).items():
                a = sheet(rows)
                check_specials(a, f"{fam} {color} {key}={val}")
                Image.fromarray(a).save(os.path.join(d, f"{name}-{color}.png"))
                print(f"{key}={val}: {name}-{color}.png")


def main():
    args = sys.argv[1:]
    pv = None
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
        os.makedirs(pv, exist_ok=True)
    if "--variants" in args:
        i = args.index("--variants")
        out = args[i + 1]
        del args[i:i + 2]
        write_variants(out, args)
        return
    opts = parse_opts(args)
    for fam in FAMILIES:
        name = fam.split("/")[-1]
        if args and name not in args:
            continue
        sd = os.path.join(REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        for color, rows in build_family(fam, opts).items():
            a = sheet(rows)
            check_specials(a, f"{fam} {color}")
            Image.fromarray(a).save(os.path.join(sd, color + ".png"))
            if pv:
                H.preview(a, os.path.join(pv, f"{name}-{color}.png"))
            print(f"{fam}/sprites/{color}.png  rows={len(rows)}")


if __name__ == "__main__":
    main()
