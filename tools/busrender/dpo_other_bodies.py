"""Rendered DP Ostrava bodies on the dpmhk.py parametric bus (render.py box
raycaster): the Ekova Electron 12 (5005-5007, DPO turquoise) and the SOR EBN
10.5 (5001-5004, the old DPO blue-white-yellow scheme).

Both subclass dpmhk.Veh and override only the paint and the end faces, so the
geometry rules (windows, posts, doors, wheels, mirrors, roof pods) are those of
the DPMHK SOR / Iveco bodies. dpmhk.py itself is not changed.

Positions are real metres from the front. Bands are whole multiples of 0.25 m,
so each is the same number of pixel rows in every view.
"""
import math

import dpmhk as H
from dpmhk import Veh, mk, inr, sh, FRAME, AMBER, SILVER
import dpo_otherkit as K

HW = H.HW

# ------------------------------------------------------------------ Ekova Electron 12
# 11.98 m, wheelbase 5.90 m, doors 2-2-2 (front overhang, mid-wheelbase, behind
# the rear axle). Tall glazing from 1.20 m with a thin white sill line under it,
# a tall turquoise band over the windows and a full-length roof fairing that
# steps down over the last ~1.8 m (photos of 5005 / 5006). No pantograph:
# plug and OppCharge (the pantograph is on the charging mast).
EKOVA = dict(
    face="ekova", rear="ekova", real_len=11.98, joints=[], cu=[8],
    axles=[2.65, 8.55],
    doors=[(0.35, 1.60), (4.75, 6.05), (9.20, 10.45)],
    drv=(0.30, 1.55),
    z0=0.32, zr=2.95, zwin0=1.20, zwin1=2.45, zband0=1.20, zband1=2.95,
    cap=0.0, sidedisp=(1.80, 2.80), pods=[], mirrors=True,
)
# variant A: the fairing nearly flush with the sides, 0.5 m; B: inset 0.3 m
# from each side, so the roof edge shows as a light rim, 0.45 m
EKOVA_A = mk(EKOVA, pods=[(0.15, 10.15, 0.50, HW - 0.05, "fair"), (10.15, 11.80, 0.25, HW - 0.05, "fair")])
EKOVA_B = mk(EKOVA, pods=[(0.15, 10.15, 0.45, HW - 0.32, "fair"), (10.15, 11.80, 0.20, HW - 0.32, "fair")])


class Ekova(Veh):
    def setup_livery(self):
        self.ROOF = K.ROOF
        self.TRIM = K.MASK

    def tex_roof(self, p, u):
        return K.ROOF

    def tex_pod(self, p, u, k):
        return K.ROOF if p.face == "top" else K.BODY

    def tex_side(self, p, u, U1):
        z = p.z
        if u < 0.28 and z >= 1.15:
            return K.MASK                     # the black front mask wraps round the corner
        right = p.face == "right"
        if not right and 10.95 <= u < 11.70 and self.ZWIN0 <= z < self.ZWIN1:
            # louvred cooling panel instead of the last left window
            if self.ln(p, U1, 10.97) or self.ln(p, U1, 11.68):
                return FRAME
            return K.MASK if int((z - self.ZWIN0) / 0.25) % 2 == 0 else (0x50, 0x56, 0x5A)
        if not right and 11.15 <= u < 11.65 and 0.55 <= z < 1.05 and not (11.38 <= u < 11.42):
            return K.MASK                     # two small grilles at the rear left corner
        return super().tex_side(p, u, U1)

    def glass_band(self, p, u, U1, right):
        if p.z >= self.ZWIN1 + 0.05:
            return K.BODY                     # (dpmhk puts the side display over the windows)
        c = super().glass_band(p, u, U1, right)
        if not right and inr(u, *self.drv) and c in (K.GLASS, K.GLASS2):
            return K.CAB                      # driver's window: plain glass
        if right and inr(u, *self.sp["sidedisp"]) and p.z >= self.ZWIN1 - 0.25 and c in (K.GLASS, K.GLASS2):
            return AMBER                      # side destination display behind the glass
        return K.GLASS if c == K.GLASS2 else c    # dark tinted glazing, as on the DPO sheets

    def cant(self, p, u):
        return K.BODY

    def lower(self, p, u, right):
        if self.ZBAND0 - 0.25 <= p.z < self.ZBAND0:
            return K.WLINE                    # the white line under the glazing
        return K.BODY

    def tex_front(self, p):
        t, z = p.t, p.z
        a = abs(t)
        if z < 0.38:
            return K.MASK
        if z < 1.15:
            if a > HW - 0.55 and 0.50 <= z < 0.88:
                if 0.55 <= z < 0.80 and HW - 0.42 < a < HW - 0.08:
                    return K.HEADL
                return K.MASK                 # black lamp housings at the corners
            if 0.55 <= z < 0.80:
                return K.WLINE                # white band between the lamps
            return K.BODY
        if inr(z, 2.52, 2.78) and a < 0.95:
            return AMBER
        if inr(z, 1.20, 2.45) and a < HW - 0.14:
            return K.CAB_TOP if z >= 2.20 else K.CAB
        return K.MASK

    def tex_rear(self, p):
        t, z = p.t, p.z
        a = abs(t)
        if z < 0.38:
            return K.MASK
        if a > HW - 0.26 and inr(z, 0.75, 1.40):
            return K.TAILL
        if inr(z, 2.42, 2.64) and inr(t, 0.20, 0.80):
            return AMBER
        if inr(z, 1.70, 2.70) and a < HW - 0.24:
            return K.MASK
        return K.BODY


# ------------------------------------------------------------------ SOR EBN 10.5
# 10.37 m, wheelbase 6.32 m, overhangs 2.35 / 1.70 m; doors 1 (front overhang),
# 2 (mid-wheelbase) and 3 (just ahead of the rear axle). Old DPO scheme (photos
# of 5002 / 5004): white body and roof, a thin blue roof edge, black window band
# from 1.62 m, white panel, orange line, blue lower zone; blue roof pods and a
# big blue unit at the rear of the roof. Towards the front the window line,
# the orange line and the blue zone drop (the driver's window reaches lower and
# the orange line meets the front at headlight height).
EBN_BLUE = (0x1E, 0x78, 0xD8)
EBN_POD_TOP = (0x6E, 0xA2, 0xE2)
EBN_ORANGE = (0xF2, 0x9A, 0x1E)
EBN_WHITE = (0xF4, 0xF4, 0xF2)
EBN_ROOF = (0xEC, 0xEC, 0xEA)
EBN_LOUVRE = (0xC4, 0xC6, 0xC8)

EBN105 = dict(
    face="ebn105", rear="ebn105", real_len=10.37, joints=[], cu=[8],
    axles=[2.35, 8.67],
    doors=[(0.30, 1.50), (4.40, 5.60), (6.85, 8.05)],
    drv=(0.30, 1.50),
    z0=0.37, zr=2.87, zwin0=1.62, zwin1=2.62, zband0=1.12, zband1=2.87,
    cap=0.0, sidedisp=(2.05, 3.55), mirrors=True,
    pods=[(1.30, 2.40, 0.18, 0.45, "pod"), (3.40, 5.20, 0.18, 0.45, "pod"),
          (7.80, 9.95, 0.30, 0.78, "pod")],
    sweep=(0.10, 1.10),
)
# A: the orange line drops over the first metre behind the front corner (as on
# the photos, ahead of the front wheel arch); B: a longer, gentler sweep from
# the front axle
EBN_A = EBN105
EBN_B = mk(EBN105, sweep=(0.10, 2.35))


class Ebn105(Veh):
    def setup_livery(self):
        self.ROOF = EBN_ROOF
        self.TRIM = EBN_BLUE

    def tex_roof(self, p, u):
        return EBN_ROOF

    def tex_pod(self, p, u, k):
        return EBN_POD_TOP if p.face == "top" else sh(EBN_BLUE, p.face)

    def line_z(self, u):
        """centre height of the orange line at u"""
        u0, u1 = self.sp["sweep"]
        if u >= u1:
            return 1.00
        f = max(0.0, (u - u0) / (u1 - u0))
        return 0.75 + 0.25 * f

    def win_bottom(self, u, right):
        """the driver's window reaches lower at the front"""
        if not right and u < 1.45:
            return 1.37
        return self.ZWIN0

    def tex_side(self, p, u, U1):
        z, f = p.z, p.face
        right = f == "right"
        for a in self.axles:
            if abs(u - a) < 0.62 and z < 1.02 and math.hypot(u - a, z - self.WR) < 0.62:
                return None
        if z >= self.ZWIN1:
            return sh(EBN_BLUE, f)                       # the thin blue roof edge
        if right:
            d = self.door_at(u)
            if d:
                return self.tex_door(p, u, U1, d)
        wb = self.win_bottom(u, right)
        if z >= wb:
            if not right and 9.75 <= u < 10.20:
                # louvre behind the last left window
                return sh(EBN_LOUVRE, f) if int((z - wb) / 0.25) % 2 else sh(EBN_WHITE, f)
            save = self.ZWIN0
            self.ZWIN0 = wb
            c = self.glass_band(p, u, U1, right)
            self.ZWIN0 = save
            if not right and inr(u, *self.drv) and c in (K.GLASS, K.GLASS2):
                return K.CAB
            return K.GLASS if c == K.GLASS2 else c
        lz = self.line_z(u)
        if abs(z - lz) < 0.125:
            return sh(EBN_ORANGE, f)
        if z > lz:
            return sh(EBN_WHITE, f)
        return sh(EBN_BLUE, f)

    def tex_door(self, p, u, U1, d):
        d0, d1 = d
        z = p.z
        if self.ln(p, U1, d0 + 0.02) or self.ln(p, U1, d1 - 0.02):
            return FRAME
        if self.ln(p, U1, (d0 + d1) / 2):
            return FRAME
        if p.rng(2)[0] < self.Z0 + 0.14:
            return H.STEP
        if z >= self.ZWIN1 - 0.08:
            return FRAME
        return K.GLASS

    def tex_front(self, p):
        t, z = p.t, p.z
        a = abs(t)
        f = "front"
        if z < 0.37:
            return K.MASK
        if z < 0.62:
            if a > HW - 0.55 and 0.40 <= z:
                return K.HEADL if a < HW - 0.10 else sh(SILVER, f)
            return sh(EBN_BLUE, f)
        if z < 0.87:
            return sh(EBN_ORANGE, f)
        if z < 1.25:
            return sh(EBN_WHITE, f)
        if z >= 2.62:
            return sh(EBN_WHITE, f)
        if a > HW - 0.10:
            return K.MASK
        if inr(z, 2.37, 2.62):
            return AMBER if a < 0.95 else K.MASK
        return K.CAB_TOP if z >= 2.12 else K.CAB

    def tex_rear(self, p):
        t, z = p.t, p.z
        a = abs(t)
        f = "rear"
        if z < 0.37:
            return K.MASK
        if a > HW - 0.28 and inr(z, 0.95, 1.62):
            return K.TAILL
        if z < 0.95:
            return sh(EBN_BLUE, f)
        if z >= 2.62:
            if a > HW - 0.20:
                return K.TAILL                           # the red marker lamps up at the corners
            return sh(EBN_BLUE, f) if z >= 2.75 else sh(EBN_WHITE, f)
        if inr(z, 1.87, 2.62) and a < HW - 0.28:
            if inr(z, 2.37, 2.62) and inr(t, 0.10, 0.70):
                return AMBER
            return K.GLASS
        if inr(z, 1.37, 1.87) and a < HW - 0.40 and int((z - 1.37) / 0.25) % 2 == 1:
            return sh(EBN_LOUVRE, f)
        return sh(EBN_WHITE, f)


def build(cls, sp):
    """one row of 8 views, rendered on the dpmhk lane origins (centred)"""
    import numpy as np
    from render import render, DIRS
    m = cls(sp, "dpo")
    tiles = []
    for d in DIRS:
        o = np.array(H.origin_for(d))
        img, _ = render(d, m.boxes(0), m.tex_for(0), m.sec_len(0), o)
        tiles.append(img)
    return [tiles]
