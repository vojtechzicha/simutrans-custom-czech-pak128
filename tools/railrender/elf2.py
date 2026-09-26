#!/usr/bin/env python3
"""Pesa Elf 2 EMUs of Koleje Śląskie (line S71 Katowice - Chałupki - Bohumín),
drawn from scratch with the pak128 box raycaster: the articulated unit model of
impuls.py (Unit) with the Elf 2 cab and the KŚ Elf painter.

    python tools/railrender/elf2.py                  # every sheet
    python tools/railrender/elf2.py 22wed            # only this family
    python tools/railrender/elf2.py --preview DIR    # also 4x previews

  22wed  22WEd(g), 4 sections A-C-D-B (10, 8, 8, 10 cu), livery bilomodra
  21wea  21WEa(g), 3 sections A-C-B (10, 8, 10 cu), livery bilomodra

Positions are unit metres measured on the vagonweb side drawings 22WEd-a /
21WEa-a (10 px = 1 m, coupler face = 0) and checked on photos 22WEd-002
Gliwice, 22WEd-012 Częstochowa, 21WEa-002 Katowice, 21WEa-003, 21WEa-002B and
22WEd-010B (front).  The Elf 2 is taller than the Impuls (4.28 m) with a long
raked nose whose roof slopes down to the windscreen.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import railkit as R                      # noqa: E402
from railkit import Paint                # noqa: E402
import impuls as I                       # noqa: E402
from impuls import zm, zmt, Spec, WS, WS_HI, DISP, AMBER, LAMP_OFF   # noqa: E402


class NoseElf2(I.Nose):
    """Long raked nose: bumper at the coupler face + 0.55 m, windscreen raked
    ~50 deg, the cab roof sloping down to it (vagonweb 22WEd-a profile)."""
    CAB_M = 4.4
    PROF = [(0.8, 0.70), (1.5, 0.58), (3.7, 0.60), (5.33, 1.00), (6.67, 1.40),
            (8.0, 1.90), (9.33, 2.60), (10.13, 3.25), (10.72, 4.20)]

    def corner(self, z):
        W = self.W
        if z < 1.5:
            return 0.60, 0.30, W - 0.06
        if z < 3.7:
            return 1.25, 0.42, W
        if z < 5.4:
            return 1.20, 0.40, W
        if z < self.ZS:
            return 1.10, 0.36, W
        return 1.10, 0.34, W - 0.12


class KSElfLivery(I.KSLivery):
    """KŚ white / azure on the Elf 2 body: azure nose with a dark grey face
    mask (windscreen and the centre panel down to the coupler), headlights in
    the azure beside it, azure roof edge band, black window band, yellow doors
    in azure frames, KŚ ribbon behind the cab door."""
    MASK = Paint(0x2C2F33)
    Z_TOPBAND = zm(3.36)
    Z_BAND0, Z_BAND1 = zm(1.42), zm(2.90)
    Z_STRIPE0, Z_STRIPE1 = zm(0.78), zm(1.12)
    RIB_X0 = 5.0
    BAND_START = 6.55

    def white_edge(self, h):
        return float(np.interp(h, [0.7, 1.0, 1.4, 1.9, 2.5, 3.0, 3.3],
                               [4.0, 3.2, 2.75, 2.55, 2.6, 2.85, 3.3]))

    def cab_side(self, U, xp, xe, z):
        S = U.S
        h = zmt(z)
        if z > self.Z_TOPBAND - 0.3 and xe < S.cab_m:
            return self.BLUE
        edge = self.white_edge(h)
        # cab side window: dark, rounded front, in the azure behind the windscreen
        fe = 2.15 + (h - 2.1) * 0.55
        if 2.05 <= h <= 3.2 and fe <= xe <= 3.30:
            if xe > 3.2 or h > 3.1 or xe < fe + 0.08:
                return self.MASK
            return WS_HI if h > 2.85 else WS
        if xe < edge:
            if h < 0.78:
                return self.SKIRT
            return self.BLUE
        # cab door (white leaf, grey frame, small window)
        if 3.45 <= xe <= 4.25 and 0.75 <= h <= 3.05:
            if xe < 3.53 or xe > 4.17 or h > 2.97:
                return Paint(0x9FA3A6)
            if 2.15 <= h <= 2.85 and 3.62 <= xe <= 4.08:
                return WS
            return self.BODY
        if xe < S.cab_m + 0.6:
            if self.Z_STRIPE0 <= z <= self.Z_STRIPE1:
                return self.BLUE
            if z < self.Z_STRIPE0:
                return self.SKIRT
            return self.BODY
        return None

    def nose(self, U, end, f, m, v, z):
        S, N = U.S, U.N
        av = abs(v)
        mf = N.front(z)
        dm = m - mf
        h = zmt(z)
        if f == "+z" and z >= S.ZS - 0.1:
            return self.BLUE
        if z < 1.0:
            return self.SKIRT
        if h < 1.25:
            # lower front: coupler recess in the centre, black grilles at the corners
            if av < 0.40 and dm < 0.5 and h > 0.5:
                return self.BLACK
            if 0.52 <= av <= 0.84 and 0.55 <= h <= 1.15 and dm < 0.4:
                return self.BLACK
            return self.BLUE
        if h < 2.15:
            # headlights: slanted eyes in the azure beside the mask
            if 0.50 <= av <= 0.86 and 1.55 <= h <= 2.05:
                if 0.58 <= av <= 0.78 and 1.65 <= h <= 1.95:
                    if end == "A":
                        return R.HEAD
                    return R.TAIL if av > 0.68 else LAMP_OFF
                return self.BLACK
            if av < 0.46:
                return self.MASK          # centre panel with the unit number
            return self.BLUE
        if z < S.ZS - 0.1:
            lim = 0.80 - 0.10 * (z - zm(2.15)) / (S.ZS - zm(2.15))
            if av < lim:
                if z > S.ZS - 0.95:
                    if abs(z - (S.ZS - 0.5)) < 0.2 and av < lim - 0.25:
                        return AMBER
                    return DISP
                if av > lim - 0.08 or h < 2.3:
                    return self.MASK
                return WS_HI if (z > 7.9 or (v > 0.3 and z > 6.8)) else WS
            return self.BLUE
        return self.BLUE


H_ELF = dict(W=R.W_STD * 2.88 / 2.825, ZBOT=zm(0.60), ZBOG=zm(1.02), ZS=zm(3.65), ZCAP=zm(3.88),
             ZR=zm(4.02), CAP1=0.07, CAP2=0.26, bogie_cut=1.55,
             ZWF0=zm(1.55), ZWF1=zm(2.80), ZWG0=zm(1.62), ZWG1=zm(2.76), WF=0.0,
             ZD0=zm(0.62), ZD1=zm(3.02), ZDW0=zm(1.55), ZDW1=zm(2.75), DF=0.14, DFT=0.30,
             cab_m=4.4, roof_pod=False)

PILLAR, WIN = 0.5, 1.3


def fill_windows(gaps):
    """regular 1.3 m windows with 0.5 m pillars, centred in each gap."""
    out = []
    for (a, b) in gaps:
        n = int((b - a + PILLAR) // (WIN + PILLAR))
        if n <= 0:
            continue
        tot = n * WIN + (n - 1) * PILLAR
        x = a + (b - a - tot) / 2
        for i in range(n):
            out.append((round(x, 2), round(x + WIN, 2)))
            x += WIN + PILLAR
    return out


def layout(xend, joints, doors, cab_end=6.5, margin=0.30, joint_m=0.55):
    obst = [(0, cab_end), (xend - cab_end, xend)]
    obst += [(a - margin, b + margin) for (a, b) in doors]
    obst += [(j - joint_m, j + joint_m) for j in joints]
    obst.sort()
    gaps = []
    for (a0, b0), (a1, b1) in zip(obst, obst[1:]):
        if a1 - b0 > WIN:
            gaps.append((b0, a1))
    return fill_windows(gaps)


def spec_22wed():
    xend = 76.9
    joints = [22.0, 38.45, 54.9]
    doors = [(9.7, 11.4), (17.0, 18.7), (25.6, 27.3), (33.2, 34.9),
             (42.0, 43.7), (49.6, 51.3), (58.2, 59.9), (65.5, 67.2)]
    roof = [(7.0, 8.0, 0.25, 0.50, "box"), (8.1, 11.8, 0.30, 0.66, "box"), (12.6, 15.2, 0.30, 0.62, "box"),
            (15.3, 18.3, 0.25, 0.55, "box"), (26.8, 31.0, 0.30, 0.62, "box"), (45.9, 50.1, 0.30, 0.62, "box"),
            (58.6, 61.6, 0.25, 0.55, "box"), (61.7, 64.3, 0.30, 0.62, "box"), (65.1, 68.8, 0.30, 0.66, "box"),
            (68.9, 69.9, 0.25, 0.50, "box")]
    return Spec(name="22WEd", lengths=[10, 8, 8, 10], joints=joints, xend=xend, doors=doors,
                windows=layout(xend, joints, doors), bogies=[5.45, xend - 5.45], roofboxes=roof,
                pantos=[(24.6, False, +1), (52.3, True, -1)], **H_ELF)


def spec_21wea():
    xend = 60.5
    joints = [22.0, 38.5]
    doors = [(9.7, 11.4), (25.6, 27.3), (33.2, 34.9), (49.1, 50.8)]
    roof = [(7.0, 8.0, 0.25, 0.50, "box"), (8.1, 11.8, 0.30, 0.66, "box"), (12.6, 15.2, 0.30, 0.62, "box"),
            (15.3, 18.3, 0.25, 0.55, "box"), (26.8, 31.0, 0.30, 0.62, "box"),
            (42.2, 45.2, 0.25, 0.55, "box"), (45.3, 47.9, 0.30, 0.62, "box"), (48.7, 52.4, 0.30, 0.66, "box"),
            (52.5, 53.5, 0.25, 0.50, "box")]
    return Spec(name="21WEa", lengths=[10, 8, 10], joints=joints, xend=xend, doors=doors,
                windows=layout(xend, joints, doors), bogies=[5.45, xend - 5.45], roofboxes=roof,
                pantos=[(24.6, False, +1), (35.9, True, -1)], **H_ELF)


def unit(fam):
    S = spec_22wed() if fam == "22wed" else spec_21wea()
    return I.Unit(S, KSElfLivery(), NoseElf2(S.W, S.ZS, S.ZR, S.ZCAP))


FAMILIES = {
    "22wed": ("koleje-slaskie", "bilomodra", ["22WEd-A", "22WEd-C", "22WEd-D", "22WEd-B"]),
    "21wea": ("koleje-slaskie", "bilomodra", ["21WEa-A", "21WEa-C", "21WEa-B"]),
}


if __name__ == "__main__":
    I.run(FAMILIES, unit, sys.argv[1:])
