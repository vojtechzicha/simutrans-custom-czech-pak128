"""Leo Express loco-hauled coaches: ex-DB IC cars (Avmmz 106.5, Bpmmz 284.5,
Bpmmbz 285.3) in DB light grey with orange doors + LE logo, and the hired
RDC/BTE couchette Bvcmz 248.5 in RDC blue.

26.40 m over buffers -> length 13 (pak128.cs coach convention, 2.03 m / cu).
Positions come from the vagonWEB side drawings (10 px = 1 m), in metres from
the car's left end in the drawing; u = metres / M.
"""
import numpy as np
import railkit as R
from railkit import Paint, Part
from render import DIRS

L = 13.0
M = 26.4 / 13.0            # metres per carunit
W = R.W_STD
ZB = 1.4                   # body bottom (skirt starts)
ZS = R.H_SIDE              # 10.0 side top
ZR = ZS + R.H_CAP          # roof top
PX = 0.375                 # metres per model px (4.05 m roof = 10.8)


def zm(h):
    """height above rail in metres -> model z."""
    return h / PX


# windows: (from_m, to_m, kind) kind: 'w' passenger glass, 'f' frosted WC
WIN = {
    "Avmmz": [(1.7, 3.0, "f")] + [(a / 10, b / 10, "w") for a, b in
              [(34, 46), (56, 68), (79, 91), (102, 114), (125, 137), (148, 160), (171, 183), (194, 206), (217, 229)]]
             + [(23.3, 24.6, "f")],
    "Bpmmz": [(1.7, 3.0, "f"), (3.6, 4.2, "w")] + [(a / 10, b / 10, "w") for a, b in
              [(49, 61), (68, 80), (87, 99), (106, 118), (125, 137), (144, 156), (163, 175), (182, 194), (201, 213)]]
             + [(22.0, 22.6, "w"), (23.3, 24.6, "f")],
    # accessible car: the wheelchair end has two large windows, fewer seat bays
    "Bpmmbz": [(1.7, 3.0, "f"), (3.6, 4.2, "w")] + [(a / 10, b / 10, "w") for a, b in
               [(49, 61), (68, 80), (87, 99), (106, 118), (125, 137), (144, 156), (163, 175)]]
              + [(18.4, 20.4, "w"), (20.9, 22.9, "w"), (23.3, 24.6, "f")],
    "Bvcmz": [(1.8, 2.5, "f")] + [(a / 10, b / 10, "w") for a, b in
              [(31, 42), (50, 61), (69, 80), (88, 99), (107, 118), (126, 137), (145, 156), (164, 175), (183, 194), (202, 213), (221, 232)]]
             + [(23.8, 24.5, "f")],
}
DOORS = [(0.60, 1.40), (25.0, 25.8)]      # metres, single-leaf end doors
BOGIES = [3.7, 22.7]                        # bogie centres (19.0 m apart)


def palette(liv):
    if liv == "rdcmodra":
        return dict(body=Paint(0x2254BE), roof=Paint(0xA5A7A6, top=0xB0B2B1), skirt=Paint(0x1D47A2),
                    door=Paint(0x2254BE), doorframe=Paint(0xE4E6E6), under=Paint(0x2A2C2E),
                    frost=Paint(0xB7C2CA), logo=None, text=Paint(0xE8ECF0), band=None)
    return dict(body=Paint(0xE2E4E3), roof=Paint(0x8F9497, top=0x9A9FA2), skirt=Paint(0xA3A7A9),
                door=Paint(0xF06A0C), doorframe=None, under=Paint(0x3A3D3F),
                frost=Paint(0xC4CDD3), logo=Paint(0x3A3D40), dot=Paint(0xF06A0C), text=None,
                band=Paint(0xCFD2D2))


def coach(kind, liv, u0=0.0, owner="C", flip=False):
    """Parts of one coach whose front buffer face is at consist-u u0.
    flip: draw the car turned (window pattern mirrored)."""
    C = palette(liv)
    win = WIN[kind]
    parts = []

    def m_at(u):
        m = (u - u0) * M
        return 26.4 - m if flip else m

    def side(f, u, v, z, d):
        m_raw = m_at(u)
        # the -v side is the car turned 180 deg: mirror the pattern
        m = 26.4 - m_raw if f == "-v" else m_raw
        # the logo must read left to right as seen: on the -v side screen-left
        # is the car's front end, on the +v side its rear end
        lm = m_raw if f == "-v" else 26.4 - m_raw
        for (a, b) in DOORS:
            if a <= m <= b and zm(0.55) <= z <= zm(3.35):
                if C["doorframe"] is not None and (m - a < 0.12 or b - m < 0.12 or z > zm(3.22)):
                    return C["doorframe"]
                if zm(2.05) <= z <= zm(2.95) and a + 0.2 <= m <= b - 0.2:
                    return R.GLASS
                return C["door"]
        for (a, b, k) in win:
            if a - 0.08 <= m <= b + 0.08 and zm(1.9) <= z <= zm(3.1):
                if k == "f":
                    return C["frost"] if z > zm(2.25) else C["body"]
                return R.GLASS_HI if z > zm(2.9) else R.GLASS
        if C["logo"] is not None:
            # "leo express" + orange dots/slash next to door 1, below the windows
            if 2.2 <= lm <= 5.2 and zm(0.95) <= z <= zm(1.9):
                if lm < 2.75:
                    if (lm < 2.45 and z > zm(1.55)) or (lm >= 2.45 and zm(1.05) <= z <= zm(1.45)):
                        return C["dot"]
                    return C["body"]
                row_hi = z > zm(1.45)
                if row_hi and lm > 3.9:
                    return C["body"]
                return C["logo"]
        if C["text"] is not None and zm(1.15) <= z <= zm(1.5) and (7.4 <= m <= 9.6 or 16.8 <= m <= 19.0):
            # white "RDC Zugkraft, die verbindet." lettering, broken into words
            if int((m - 7.4) / 0.55) % 3 != 2:
                return C["text"]
        if C["band"] is not None and zm(1.75) <= z <= zm(1.95):
            return C["band"]          # ghost of the removed DB red stripe
        if z < zm(0.95):
            return C["skirt"]
        return C["body"]

    def end(f, u, v, z, d):
        if abs(v) < 0.42 and z < ZS - 0.6:
            return Paint(0x2B2D2F)        # gangway bellows / door
        return C["body"]

    def body_mat(f, u, v, z, d):
        if f == "+z":
            return C["roof"]
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        return end(f, u, v, z, d)

    ub0, ub1 = u0 + 0.14, u0 + L - 0.14
    parts.append(Part(ub0, ub1, -W, W, ZB, ZS, body_mat, owner))
    parts.append(Part(ub0 + 0.05, ub1 - 0.05, -W + 0.2, W - 0.2, ZS, ZR, lambda *a: C["roof"], owner))
    # gangways + buffers
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        parts.append(Part(a, b, -0.40, 0.40, 2.6, ZS - 0.8, lambda *a: Paint(0x2B2D2F), owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *a: Paint(0x1E2022), owner))
    # underframe equipment + bogies
    parts.append(Part(u0 + 3.3, u0 + L - 3.3, -W + 0.25, W - 0.25, 0.0, ZB,
                      lambda *a: C["under"], owner))
    for bm in BOGIES:
        bc = u0 + bm / M
        parts.append(Part(bc - 0.72, bc + 0.72, -W + 0.12, W - 0.12, 0.0, ZB,
                          lambda f, u, v, z, d: Paint(0x3C3F42) if (f in ("+v", "-v") and z > 1.0) else Paint(0x1E2022),
                          owner))
    return parts


KINDS = ["Avmmz", "Bpmmz", "Bpmmbz"]


def rows_for(liv, kinds):
    rows = []
    for k in kinds:
        parts = coach(k, liv)
        rows.append([R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS])
    return rows


if __name__ == "__main__":
    import leo
    leo.main()
