"""Prague (PID) city buses rendered with the pak128 box renderer: the parametric
bodies of dpmhk.py (imported, never edited, so the DPMHK sheets stay
byte-identical) painted in the Prague liveries.

Liveries (texture rules on the dpmhk Veh model):
  A  pidsedocervena        PID 2021 scheme: grey body, continuous black glazing band
                           up to the roof edge, red vertical columns placed per body
                           (lower body, crossing the roof as transverse bands), red
                           block on the vehicle's left of the lower front and rear.
                           Colours and details as the DPP ENS 12 (vehicle-bus/dpp/ens_12).
  B  pidcervenomodrobila   old PID "trikolora": blue (RAL 5005) roof, roof pods, cant
                           and front cap; black glazing band, white band, red lower
                           body. Colours as the DPP NB 12 PID sheet.
  C  dppcervenobila        DPP city red-white: white roof, black glazing band, white
                           band, red lower body; black front cap with the red SOR trim.
  W  bila                  plain white (#F2F2F0), black glazing band.

Bodies: SOR NS 12 / NS 18 and Iveco Urbanway 12M from dpmhk.py (repainted, the
NS 12 diesel roof and rear engine louvres added as spec keys), plus the SOR NC 18
(low-floor suburban articulated, NB 18 face) built here from photos.

usage: python tools/busrender/praha.py [family ...] [--preview DIR]
       python tools/busrender/praha.py --variants DIR     NC 18 variant sheets only
"""
import os, sys, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dpmhk as H                                                    # noqa: E402
from dpmhk import Veh, mk, sh, inr, HW, KCU, PER_CU, NS12, NS18, UW12   # noqa: E402
from render import render, DIRS                                     # noqa: E402

BLACK, FRAME, GLASS, GLASS2 = H.BLACK, H.FRAME, H.GLASS, H.GLASS2
HEADL, TAILL, AMBER, SILVER = H.HEADL, H.TAILL, H.AMBER, H.SILVER
LOUVRE = (0x44, 0x46, 0x4A)       # engine-bay louvre slats (lines between black)
LIP = (0x50, 0x52, 0x56)          # dark grey bumper lip / skirt (NC 18)

# ------------------------------------------------------------------ palettes
# base colours are the top-face value; sides get x0.93, front/rear x0.87 (dpmhk.SHADE)
PAL = {
    # PID 2021 grey-red: the exact values of the DPP ENS 12 render
    "A": dict(body=(0xC6, 0xC8, 0xCB), red=(0xCF, 0x1F, 0x2B), roof=(0xD2, 0xD4, 0xD7),
              trim=(0xE8, 0xEA, 0xEC), white=None),
    # trikolora: sides land on the DPP NB 12 PID sheet values (1E4893 / C00A13 / E9E9E9)
    "B": dict(body=(0xFA, 0xFA, 0xFA), red=(0xCF, 0x0B, 0x15), roof=(0x26, 0x57, 0xAD),
              blue=(0x21, 0x4E, 0x9E), trim=(0xE8, 0xEA, 0xEC), white=(0xFA, 0xFA, 0xFA)),
    # DPP red-white (as the DPP NB 12 / NB 18 sheets: roof FFFFFF, sides E9E9E9, red C00A13)
    "C": dict(body=(0xFA, 0xFA, 0xFA), red=(0xCF, 0x0B, 0x15), roof=(0xFF, 0xFF, 0xFF),
              trim=(0xCF, 0x0B, 0x15), white=(0xFA, 0xFA, 0xFA)),
    # plain white
    "W": dict(body=(0xF2, 0xF2, 0xF0), red=None, roof=(0xF4, 0xF4, 0xF2),
              trim=(0xF2, 0xF2, 0xF0), white=(0xF2, 0xF2, 0xF0)),
}
ZWHITE = 0.87      # top of the red lower body under the white band (B, C): 2 px of white

# ------------------------------------------------------------------ bodies
# SOR NS 12 diesel (Arriva City 2024-26, Stenbus 2019-25, ARANEA 2017): the ENS 12
# geometry (black cap 1.20 m, red columns over both axles) with a roof A/C unit
# between the red roof bands and the louvred engine bay in the last window bay
# of both sides (engine tower in the left rear corner).
PNS12 = mk(NS12, cap=1.20, pods=[(3.80, 7.35, 0.24, 0.85, "ac")],
           reds=[(1.75, 3.75), (7.60, 9.47)], louvre=(11.30, 11.80, "lr"), tower=True)
# SOR NS 18 diesel: three red columns (front axle, ahead of the middle axle, rear
# axle; photo 9378); A/C units between the roof bands
PNS18 = mk(NS18, cap=1.20, pods=[(3.80, 6.40, 0.24, 0.85, "ac"), (12.0, 14.2, 0.22, 0.80, "ac")],
           reds=[(1.75, 3.75), (6.45, 8.00), (14.30, 16.20)], louvre=(18.05, 18.55, "lr"), tower=True)
# DPP 5998 (2021): cap as the DPMHK NS, A/C behind the cap, a low unit mid front
# section, one on the rear section (photos zdopravy.cz 12/2021)
DNS18 = mk(NS18, pods=[(1.80, 3.60, 0.22, 0.80, "ac"), (5.20, 7.20, 0.14, 0.70, "ac"),
                       (12.2, 13.8, 0.20, 0.75, "ac")], louvre=(18.05, 18.55, "lr"), tower=True)
# Iveco Urbanway 12M. B = 2015-2020 cars (2013 face), A = the 2024 cars 8136-8140
# (2024 face; 5 of the 8 grey-red cars): red columns from photos of 8136 / 8139
PUW12B = mk(UW12, pods=[(2.20, 4.60, 0.24, 0.85, "ac")])
PUW12A = mk(UW12, face="uw2", pods=[(2.20, 4.60, 0.24, 0.85, "ac")],
            reds=[(1.85, 4.10), (7.40, 9.55)])
# BDS-BUS 6J2 3507 (Brno lines 48 / 74; 2019, ex MHD Moravsky Krumlov): plain
# white, 2013 face, 2-2-2 doors, green LED displays (as the DPMB families), the
# engine-bay grille low in the left rear corner
PUW12W = mk(UW12, pods=[(1.40, 4.60, 0.24, 0.85, "ac")], led=(0x62, 0xD6, 0x4A),
            vent=(10.85, 11.55, "l"))

# SOR NC 18 (NEW body): 18.75 x 2.55 x 2.90 m, wheelbase 6.18 + 6.57 m, overhangs
# 2.47 / 3.53 m (SOR data via cs.wikipedia), 3 double doors (2 in the front
# section, 1 behind the joint), low floor throughout, NB 18 face, engine in the
# left rear corner. Door / joint positions measured by projective fit on the
# Autotec 2010 side photo and on Arriva 9930.
NC18 = dict(
    face="nc", rear="nc", real_len=18.75, joints=[11.10], cu=[8, 6],
    axles=[2.47, 8.65, 15.22],
    doors=[(0.32, 1.57), (6.35, 7.65), (12.30, 13.60)],
    drv=(0.35, 1.57),
    z0=0.26, zr=2.92, zwin0=1.26, zwin1=2.46, zband0=1.14, zband1=2.72,
    cap=0.0, sidedisp=(1.95, 3.25), mirrors=True,
    pods=[(0.30, 2.00, 0.14, 0.80, "ac"), (2.30, 3.30, 0.24, 0.80, "ac"), (3.60, 4.70, 0.24, 0.80, "ac"),
          (5.30, 7.60, 0.20, 0.85, "ac"), (8.10, 9.90, 0.10, 0.70, "dark"),
          (11.80, 12.90, 0.24, 0.80, "ac"), (13.00, 15.40, 0.20, 0.85, "ac"),
          (17.60, 18.60, 0.22, 1.00, "body")],
    dip=[(1.57, 6.35, 0.90)],            # black band reaches lower between doors 1 and 2 (9930)
    louvre=(17.95, 18.55, "l"),           # engine bay, left rear corner
)
NC_VARIANTS = {
    # v1: as measured (SOR overhang 2.47 m, the 9930 deep black panel, 7 roof units)
    "v1": NC18,
    # v2: plainer: no deep panel, 4 roof units, roof 3.00 m
    "v2": mk(NC18, zr=3.00, dip=[],
             pods=[(0.40, 2.00, 0.14, 0.80, "ac"), (3.00, 4.60, 0.24, 0.85, "ac"),
                   (11.80, 13.40, 0.24, 0.85, "ac"), (17.60, 18.60, 0.22, 1.00, "body")]),
    # v3: photo-measured front overhang 2.78 m (axles 2.78 / 8.96 / 15.53), doors
    # moved with it, a slimmer white nose (black mask down to 0.90 m)
    "v3": mk(NC18, axles=[2.78, 8.96, 15.53], doors=[(0.32, 1.57), (6.55, 7.85), (12.40, 13.70)],
             nose=0.90),
}


# ------------------------------------------------------------------ vehicle
class PVeh(Veh):
    def setup_livery(self):
        sp = self.sp
        self.P = PAL[self.liv]
        self.TRIM = self.P["trim"]
        self.ROOF = self.P["roof"]
        self.reds = [(self.M(a), self.M(b)) for a, b in sp.get("reds", [])]
        self.dip = [(self.M(a), self.M(b), z) for a, b, z in sp.get("dip", [])]
        lv = sp.get("louvre")
        self.louvre = (self.M(lv[0]), self.M(lv[1]), lv[2]) if lv else None
        vt = sp.get("vent")
        self.vent = (self.M(vt[0]), self.M(vt[1]), vt[2]) if vt else None
        self.DISP = sp.get("led", AMBER)

    # helpers -----------------------------------------------------------
    def red_at(self, u):
        return any(a <= u < b for a, b in self.reds)

    def side_col(self, name, f):
        c = self.P[name]
        if name == "roof" and self.liv == "B":
            c = self.P["blue"]
        return sh(c, f)

    # roof ----------------------------------------------------------------
    def tex_roof(self, p, u):
        L = self.liv
        if self.face == "ns" and u < self.cap:
            if L == "B":
                return self.P["roof"]
            if abs(p.t) > HW - 0.30:
                return self.TRIM
            return BLACK
        if L == "A" and self.red_at(u):
            return self.P["red"]
        return self.P["roof"]

    def tex_pod(self, p, u, k):
        f = p.face
        kind = self.pods[k][4]
        L = self.liv
        if kind == "dark":
            return sh((0x50, 0x52, 0x56), f)
        if self.face == "ns" and u < self.cap:
            return sh(BLACK, f) if L != "B" else self.side_col("roof", f)
        if L == "A":
            if self.red_at(u) and not (kind == "ac" and f == "top" and abs(p.t) < 0.25):
                return sh(self.P["red"], f) if f != "top" else self.P["red"]
            col = self.P["roof"] if f == "top" else self.P["body"]
        elif L == "B":
            col = self.P["roof"] if f == "top" else self.P["blue"]
        else:
            col = self.P["roof"]
        if kind == "ac" and f == "top" and abs(p.t) < 0.25:
            return tuple(int(v * 0.62) for v in col)            # condenser grille
        return col if f == "top" else sh(col, f)

    # side ----------------------------------------------------------------
    def tex_side(self, p, u, U1):
        z, f = p.z, p.face
        right = f == "right"
        L = self.liv
        for a in self.axles:
            if abs(u - a) < 0.62 and z < 1.02 and math.hypot(u - a, z - self.WR) < 0.62:
                return None
        if self.face == "ns":
            # SOR front corner "wing" up the A-pillar and along the cap edge
            if u < 0.26 and z >= 0.45:
                return self.TRIM if L != "B" else sh(self.P["trim"], f)
            if u < self.cap and z >= self.ZBAND1 + 0.17 and L != "B":
                return self.TRIM
        if right:
            d = self.door_at(u)
            if d and z < self.ZWIN1 + 0.05:
                return self.tex_door(p, u, U1, d)
        if z >= self.ZBAND0:
            if z < self.ZWIN1 + 0.05 or (right and inr(u, *self.sidedisp) and z < self.ZWIN1 + 0.30):
                return self.glass_band(p, u, U1, right)
            return self.cant(p, u)
        for a, b, zd in self.dip:
            if a <= u < b and z >= zd:
                return sh(BLACK, f)
        return self.lower(p, u, right)

    def door_kick(self):
        return None

    def tex_door(self, p, u, U1, d):
        c = Veh.tex_door(self, p, u, U1, d)
        if c == H.HANDRAIL and self.liv == "A":
            return FRAME                              # plain black mid post, as the DPP ENS 12
        return c

    def glass_band(self, p, u, U1, right):
        lv = self.louvre
        if lv and lv[0] <= u < lv[1] and (right is False or lv[2] == "lr") and \
                self.ZWIN0 - 0.05 <= p.z < self.ZWIN1:
            k = int(math.floor((p.z - self.ZWIN0) / 0.25))
            return sh(LOUVRE, p.face) if k % 2 == 0 else FRAME
        c = Veh.glass_band(self, p, u, U1, right)
        return self.DISP if c == AMBER else c

    def cant(self, p, u):
        f = p.face
        if self.face == "ns" and u < self.cap:
            return sh(BLACK, f) if self.liv != "B" else self.side_col("roof", f)
        if self.liv in ("A", "C"):
            return sh(BLACK, f)                       # band runs up to the roof edge
        if p.z < self.ZBAND1:
            return sh(BLACK, f)
        return self.side_col("roof", f)

    def lower(self, p, u, right):
        L = self.liv
        f = p.face
        z = p.z
        if L == "A":
            if self.face == "ns" and not right and inr(u, *self.drv):
                return sh(BLACK, f)                   # black panel under the driver's window
            return sh(self.P["red"] if self.red_at(u) else self.P["body"], f)
        if L == "C" and self.face == "ns":
            xb = self.front_arch() - 0.10             # black ahead of the front arch, red skirt
            if u < xb:
                return sh(self.P["red"] if z < self.Z0 + 0.26 else BLACK, f)
        if L in ("B", "C"):
            return sh(self.P["white"] if z >= ZWHITE else self.P["red"], f)
        vt = self.vent
        if vt and vt[0] <= u < vt[1] and not right and inr(z, 0.50, 0.95):
            k = int(math.floor((z - 0.50) / 0.25))
            return sh(LOUVRE, f) if k % 2 == 0 else sh((0x8A, 0x8C, 0x90), f)
        if z < self.Z0 + 0.10:
            return sh(LIP, f)
        return sh(self.P["body"], f)

    # front ---------------------------------------------------------------
    def tex_front(self, p):
        t, z = p.t, p.z
        f = "front"
        a = abs(t)
        L = self.liv
        P = self.P
        if self.face == "ns":
            if L == "A":                                   # = DPP ENS 12
                if z < 0.46:
                    return BLACK
                if z < 1.00:
                    if a > HW - 0.36:
                        return HEADL if inr(z, 0.60, 0.86) and a < HW - 0.08 else FRAME
                    if -1.00 <= t < -0.16:
                        return sh(P["red"], f)
                    return sh(P["body"], f)
            elif L == "B":                                 # photos of 1752 / 1759
                if z < 0.40:
                    return BLACK
                if z < 1.00:
                    if a > HW - 0.40 and z >= 0.60:
                        if inr(z, 0.64, 0.88) and a < HW - 0.10:
                            return HEADL
                        return sh(SILVER, f)
                    if z > 0.92:
                        return sh(SILVER, f)
                    if z < 0.60 or (a > HW - 0.40):
                        return sh(P["red"], f)
                    return sh(P["white"], f)
            else:                                          # C: DPP 5998
                if z < 0.44:
                    return BLACK
                if z < 1.00:
                    if a > HW - 0.40 and z >= 0.54:
                        if inr(z, 0.62, 0.86) and a < HW - 0.10:
                            return HEADL
                        return sh(P["white"], f)
                    if z > 0.90:
                        return sh(SILVER, f)
                    return sh(P["red"], f)
            if a > HW - 0.10:
                return self.TRIM if L != "B" else sh(P["trim"], f)
            if inr(z, 1.06, 2.42) and a < HW - 0.16:
                return GLASS
            if inr(z, 2.52, 2.82) and a < 0.98:
                return self.DISP
            if L == "B" and z >= 2.86:
                return sh(P["blue"], f)
            return BLACK
        if self.face == "uw2":                             # Urbanway 2024 face, PID A (8139)
            if z < 0.30:
                return BLACK
            if z < 1.02:
                if a > HW - 0.50 and inr(z, 0.70, 0.84):
                    return HEADL if a < HW - 0.12 else sh(SILVER, f)
                if -0.95 <= t < 0.02:
                    return sh(P["red"], f)
                if inr(z, 0.78, 0.90) and 0.10 < t < 0.70:
                    return sh((0x60, 0x62, 0x66), f)       # IVECO letters
                return sh(P["body"], f)
            if a > HW - 0.08 and z < 2.72:
                return sh(P["body"], f)
            if inr(z, 2.40, 2.66) and a < 1.00:
                return self.DISP
            if inr(z, 1.22, 2.72) and a < HW - 0.12:
                return GLASS
            if z < 1.22:
                return BLACK
            return sh(P["body"], f) if z >= 2.86 else BLACK
        if self.face == "uw1":                             # Urbanway 2013 face, trikolora (8096)
            if z < 0.32:
                return BLACK
            up = 0.62 + (0.30 if a > HW - 0.45 else 0.0)
            if a > HW - 0.44 and inr(z, 0.66, 0.86):
                return HEADL if a < HW - 0.12 else sh(SILVER, f)
            if z < up and P["red"]:
                return sh(P["red"], f)
            if z < 1.14:
                if inr(z, 0.92, 1.06) and a < 0.80:
                    return sh(SILVER, f)
                return sh(P["white"], f)
            if a > HW - 0.08:
                return sh(P.get("blue", P["white"]), f)    # thin (blue) A-pillar edge
            if inr(z, 2.40, 2.66) and a < 1.00:
                return self.DISP
            if inr(z, 1.16, 2.72) and a < HW - 0.12:
                return GLASS
            if z >= 2.72:
                return sh(P.get("blue", P["white"]), f)
            return sh(P["white"], f)
        if self.face == "nc":                              # SOR NB-style face in white (9930)
            nose = self.sp.get("nose", 1.00)
            if z < 0.28:
                return sh(LIP, f)
            wing = nose + (0.12 if a > HW - 0.50 else 0.0)  # the white nose rises at the corners
            if z < wing:
                if a > HW - 0.50 and inr(z, 0.48, 0.74):
                    return HEADL if a < HW - 0.14 else sh(SILVER, f)
                return sh(P["white"], f)
            if a > HW - 0.07:
                return sh(P["white"], f)
            if inr(z, 2.42, 2.64) and a < 1.00:
                return self.DISP
            if inr(z, 1.32, 2.70) and a < HW - 0.14:
                return GLASS
            if z >= 2.78:
                return sh(P["white"], f)
            return BLACK
        return Veh.tex_front(self, p)

    # rear ----------------------------------------------------------------
    def tex_rear(self, p):
        t, z = p.t, p.z
        f = "rear"
        a = abs(t)
        st = self.rearstyle
        L = self.liv
        P = self.P
        if st == "ns":
            if a > HW - 0.26 and inr(z, 0.55, 1.35):
                return TAILL
            if z < 0.45:
                return BLACK
            if z >= self.ZBAND0:
                if L == "B" and z >= self.ZBAND1:
                    return sh(P["blue"], f)
                if self.sp.get("tower") and t < -0.05 and inr(z, 1.75, 2.62) and a < HW - 0.30:
                    k = int(math.floor((z - 1.75) / 0.25))
                    return sh(LOUVRE, f) if k % 2 == 0 else FRAME   # engine tower grille, left
                if inr(z, 2.42, 2.62) and inr(t, 0.30, 0.80):
                    return self.DISP                                    # route number, right
                if inr(z, 1.85, 2.62) and a < HW - 0.30 and (t > 0.05 or not self.sp.get("tower")):
                    return GLASS
                return BLACK
            if L == "A":
                return sh(P["red"] if -0.95 <= t < -0.15 else P["body"], f)
            return sh(P["white"] if z >= ZWHITE else P["red"], f)
        if st == "uw":
            if z < 0.30:
                return BLACK
            if a > HW - 0.26 and inr(z, 0.70, 1.30):
                return TAILL
            if z < 1.30:
                if L == "A":
                    return sh(P["red"] if -0.95 <= t < -0.15 else P["body"], f)
                if L == "W":
                    return sh(P["white"], f)
                return sh(P["white"] if z >= ZWHITE else P["red"], f)
            if inr(z, 2.36, 2.58) and inr(t, 0.25, 0.80):
                return self.DISP
            if inr(z, 1.55, 2.62) and a < HW - 0.22:
                return GLASS
            if L == "B" and z >= 2.72:
                return sh(P["blue"], f)
            if L == "A":
                return BLACK if z < 2.80 else sh(P["body"], f)
            return sh(P["white"], f)
        if st == "nc":                                     # NC 18 rear (Autotec / Hrncire photos)
            if z < 0.28:
                return sh(LIP, f)
            if a > HW - 0.24 and inr(z, 0.62, 1.42):
                return TAILL
            if inr(z, 1.34, 1.76) and a < HW - 0.30:
                k = int(math.floor((z - 1.34) / 0.14))
                return sh((0x9A, 0x9C, 0xA0), f) if k % 2 == 0 else sh(P["white"], f)   # grille
            if inr(z, 2.40, 2.60) and inr(t, 0.25, 0.75):
                return self.DISP
            if inr(z, 1.86, 2.66) and a < HW - 0.20:
                return GLASS
            return sh(P["white"], f)
        return Veh.tex_rear(self, p)


# ------------------------------------------------------------------ build
def build(sp, livery):
    m = PVeh(sp, livery)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        tiles = []
        for d in DIRS:
            o = np.array(H.origin_for(d))
            if not m.single:
                o = o + (4 - l / 2.0) * PER_CU[d]
            img, _ = render(d, m.boxes(i), m.tex_for(i), L, o)
            tiles.append(img)
        rows.append(tiles)
    return rows


A, B, C, W = "pidsedocervena", "pidcervenomodrobila", "dppcervenobila", "bila"
KEY = {A: "A", B: "B", C: "C", W: "W"}

# family dir -> {livery colour: [model spec, ...] in sprite-row order}
FAMILIES = {
    "vehicle-bus/praha/sor_ns_12": {A: [PNS12], B: [PNS12]},
    "vehicle-bus/praha/sor_ns_18": {A: [PNS18]},
    "vehicle-bus/praha/urbanway_12m": {B: [PUW12B], A: [PUW12A]},
    "vehicle-bus/praha/sor_nc_18": {W: [NC18]},
    "vehicle-bus/dpp/sor_ns_18": {C: [DNS18]},
    "vehicle-bus/brno/urbanway_12m": {W: [PUW12W]},
}


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
        os.makedirs(out, exist_ok=True)
        for k, sp in NC_VARIANTS.items():
            sheet = H.save_rows(build(sp, "W"), os.path.join(out, f"sor_nc_18_{k}_sheet.png"))
            print("variant", k)
        return
    for fam, livs in FAMILIES.items():
        if args and fam.split("/")[-1] not in args and fam not in args:
            continue
        sd = os.path.join(H.REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        for color, specs in livs.items():
            rows = []
            for sp in specs:
                rows += build(sp, KEY[color])
            sheet = H.save_rows(rows, os.path.join(sd, color + ".png"))
            if pv:
                H.preview(sheet, os.path.join(pv, f"{fam.split('/')[-2]}-{fam.split('/')[-1]}-{color}.png"))
            print(f"{fam}/sprites/{color}.png  rows={len(rows)}")


if __name__ == "__main__":
    main()
