#!/usr/bin/env python3
"""Siemens Taurus (ES64U2 / ES64U4) of ÖBB and PKP Intercity in the 2026-09-26
render style (style.py), on the livery-parametric Taurus body of
cd_loco_classic.py (imported, not edited).

    python tools/railrender/taurus.py [obb/1216 obb/1116 pkp-intercity/eu44 ...] [--preview DIR]

writes vehicle-rail/<family>/sprites/<livery>.png.

Liveries (colours measured on the previous sheets, which were repaints of the
pak128.CS obb_1216 / obb_1016 drawings; layouts from the photos in each
family.yaml):
  obb/1216 railjet     carmine body; slate-grey lower field whose top edge rises
                       from just behind the front cab door towards the rear cab,
                       a thin bright-red line on that edge; black windscreen band
                       wrapping round the cab side windows. The grey "railjet"
                       wordmark is left out (1-px lettering reads as noise).
  obb/1216, obb/1116 obbcervena
                       ÖBB red, dark-grey solebar band; the white "ÖBB" wordmark
                       is left out for the same reason.
  pkp-intercity/eu44 intercity
                       silver body, royal-blue cab ends swept back along the cab
                       side, thin orange line along the top of the side,
                       dark-grey skirt, the orange "iC" mark left of centre.
  pkp-intercity/eu44 intercitypruh
                       the same plus the royal-blue band across the middle of the
                       side, solid from the cab doors and ending cleanly where
                       its halftone dots thin out towards the logo.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))

import railkit as R  # noqa: E402
from render import DIRS  # noqa: E402
from cd_loco_classic import Taurus, pc  # noqa: E402
import restyle_kit as K  # noqa: E402

RJ_CARMINE = (0xA8, 0x16, 0x2A)
RJ_SLATE = (0x55, 0x58, 0x5E)
RJ_LINE = (0xF0, 0x2A, 0x30)
BLACK = (0x26, 0x26, 0x28)
OBB_RED = (0xD9, 0x11, 0x1B)
OBB_GREY = (0x66, 0x66, 0x66)
PKP_SILVER = (0xB9, 0xBD, 0xBB)
PKP_SKIRT = (0x5A, 0x5C, 0x55)
PKP_BLUE = (0x2E, 0x45, 0x95)
PKP_ORANGE = (0xEE, 0x6A, 0x2A)
FRAME = (0x3E, 0x40, 0x42)

# PKP IC "iC" mark (o = orange, b = blue), as pkp_locos.IC_MARK
IC_MARK = ["o.oo.bb",
           "..o..b.",
           "o.o..b.",
           "o.oo.bb"]
PPC = {"ne": 5.66, "sw": 5.66, "w": 4.0, "e": 4.0, "n": 4.0, "s": 4.0, "nw": 2.83, "se": 2.83}


class OpsTaurus(Taurus):
    def __init__(self, liv):
        self.lv = liv
        t = {"railjet": dict(body=RJ_CARMINE, band=RJ_CARMINE, low=RJ_SLATE, low_rows=1,
                             cab=BLACK, nose=RJ_CARMINE, frame=FRAME),
             "obbcervena": dict(body=OBB_RED, band=OBB_RED, low=OBB_GREY, low_rows=0,
                                cab=OBB_RED, nose=OBB_RED, frame=FRAME),
             "intercity": dict(body=PKP_SILVER, band=PKP_SILVER, low=PKP_SKIRT, low_rows=0,
                               cab=PKP_BLUE, nose=PKP_BLUE, frame=FRAME),
             "intercitypruh": dict(body=PKP_SILVER, band=PKP_SILVER, low=PKP_SKIRT, low_rows=0,
                                   cab=PKP_BLUE, nose=PKP_BLUE, frame=FRAME)}[liv]
        super().__init__(t)

    def side_detail(self, f, u, v, z, d, r, top, cu):
        t, L = self.t, self.L
        along = (L - u) if f == "+v" else u      # as read, left to right
        if self.lv == "railjet":
            # black windscreen band wrapping round the cab side windows
            if r >= top - 1 and cu < self.UCAB:
                return t["cab"]
            # slate lower field rising towards the rear (train) end
            fu = u                                  # from the leading cab
            if fu > self.UCAB + 0.2:
                k = 1 + int(round(2.0 * min(1.0, (fu - self.UCAB - 0.2) / (L - 2 * self.UCAB - 0.4))))
                if r <= k:
                    return t["low"]
                if r == k + 1:
                    return pc(RJ_LINE)
            return None
        if self.lv in ("intercity", "intercitypruh"):
            if r >= 5 and cu < self.UCAB + 0.10 * (r - 5):
                return t["cab"]
            if cu < 0.55 and r >= 1:
                return t["cab"]                     # blue front corners
            if r == top:
                return pc(PKP_ORANGE)               # thin orange top line
            # "iC" mark left of centre as read, rows 1..4
            cw = 1.0 / PPC.get(d, 5.66) * 0.98
            x0 = 0.36 * L - 0.62
            i = int(np.floor((along - x0) / cw)); j = 4 - r
            if 0 <= j < 4 and 0 <= i < 7:
                ch = IC_MARK[j][i]
                if ch == "o":
                    return pc(PKP_ORANGE)
                if ch == "b":
                    return pc(PKP_BLUE)
            if self.lv == "intercitypruh" and r in (2, 3):
                a = along / L
                if a < 0.25 or a > 0.63:
                    return pc(PKP_BLUE)
            return None
        return super().side_detail(f, u, v, z, d, r, top, cu)


FAMILIES = {
    "obb/1216": ["railjet", "obbcervena"],
    "obb/1116": ["obbcervena"],
    "pkp-intercity/eu44": ["intercity", "intercitypruh"],
}


def row(liv):
    parts, lines = OpsTaurus(liv).build()
    return [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(FAMILIES)):
        for liv in FAMILIES[fam]:
            rows = [row(liv)]
            out = os.path.join(REPO, "vehicle-rail", fam, "sprites", f"{liv}.png")
            K.save_styled(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam.replace('/', '_')}_{liv}.png"), z=4, labels=[liv])
            print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
