"""RegioJet loco-hauled coaches, drawn from vagonWEB scale side drawings.

Every RJ day coach is a 26.4 m UIC-Z / DB-IC body (length 13 cu, 2.03 m/cu,
2.825 m wide, 4.05 m to the roof crown). What tells them apart is the window
rhythm, the door type, the roof (dark / light / red foil, flat Eurofima roof or
the round UIC-X couchette roof) and small lettering, so each type below is a
list of openings in metres from the car's front buffer face, read from the
vagonWEB drawing `-a` (10 px = 1 m; research/drawings/). The rhythm families:

  E9      9 wide windows, 2.3 m pitch    Ampz 18-91, Amz 19-90, Avmz, Avmmz
  E6+4    6 narrow + 4 wide              ABmz 30-90, Ampz 18-95
  E11     11 windows, 1.9 m pitch        Bmz 21-91 / 28-91 / 21-90
  DBn16   16 narrow (DB Apmz 121/125)    Bmpz 28-90 (Low cost / Relax)
  DBn14+2 same with wide end windows     Apmmz 126.1
  DBo9    9 wide + 2x2 small             Bpmz 294 (Low cost)
  SBBo10  10 wide, silvery glass         Bmpz 20-73 (R8)
  AST     9 windows in the middle 60 %   Bmpz 20-90 / 20-70 Astra
  UX      11 two-pane windows, round     Bcmz / Bvcmz / Bmz 29-90 (UIC-X)
          light roof with sloping ends

The livery is Patrik Kotas's 2011 scheme: RAL 1028 melon yellow, an anthracite
window band and metallic silver doors, with the red/navy "|| REGIOJET" logo
low on the body towards the right-hand end as seen from either side.
"""
import railkit as R
from railkit import Paint, Part, Lit
from render import DIRS

L = 13.0
M = 26.4 / 13.0            # metres per carunit
W = R.W_STD
PX = 0.375                 # metres per model px
ZB = 1.4                   # body bottom (skirt starts)
ZS = R.H_SIDE              # 10.0 = 3.75 m, side wall top
ZR = ZS + R.H_CAP          # 10.8 = 4.05 m, roof crown


def zm(h):
    """height above rail in metres -> model z."""
    return h / PX


def row(start, n, pitch, w, kind="w"):
    return [(round(start + i * pitch, 3), round(start + i * pitch + w, 3), kind) for i in range(n)]


# ------------------------------------------------------------------ types
# win:   (from_m, to_m, kind); kinds: w glass, f frosted WC, s silvery glass,
#        m glass with a centre mullion, p glass split 1.0 + 0.4, t two-pane
#        drop-light (transom), v louvred vestibule window
# num:   metres of the white class numerals on the band ("1" or "2")
# doors: leaf spans; door: plug | fold
# roof:  euro | db | astra | ux  (profile + where the yellow meets the roof)
# rc:    default roof colour dark | light
# skirt: dark | light
# marks: (lm_from, lm_to, z_from_m, z_to_m, colour) small boxes on the lower
#        body in "as seen" metres (left to right), e.g. display boxes
DOORS_STD = [(0.6, 1.4), (25.0, 25.8)]

TYPES = {
    # --- ex-ÖBB / SBB Eurofima bodies (flat roof, yellow up over the curve)
    "Ampz1891": dict(   # A000: ex-ÖBB Amoz, 9 compartments (Business + Relax)
        win=[(2.0, 2.7, "f")] + row(3.5, 9, 2.3, 1.3, "w") + [(23.8, 24.5, "f")],
        num=[(2.8, 3.2), (23.3, 23.7)], door="plug", roof="euro", rc="dark", skirt="dark",
        word="business"),
    "Ampz1895": dict(   # A100: ex-ÖBB ABmoz body, 6 narrow + 4 wide
        win=[(1.9, 2.6, "f")] + row(3.3, 6, 1.9, 1.1, "m") + row(14.9, 4, 2.3, 1.3, "w") + [(23.8, 24.5, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="plug", roof="euro", rc="dark", skirt="dark",
        word="business"),
    "ABmz3090": dict(   # AB000: same body as A100, Standard
        win=[(1.9, 2.6, "f")] + row(3.3, 6, 1.9, 1.1, "w") + row(14.9, 4, 2.3, 1.3, "w") + [(23.8, 24.5, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="plug", roof="euro", rc="dark", skirt="dark",
        word=None),
    "Bmz2191": dict(    # Bk000: Eurofima 2nd class, 11 compartments (+ kids)
        win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1, "w") + [(23.8, 24.5, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="plug", roof="euro", rc="dark", skirt="dark",
        word="kids"),
    "Bmz2190": dict(    # Bk100: ÖBB's own Z1 21-70.0, folding doors, LED display
        win=[(1.9, 2.6, "f")] + row(3.2, 11, 1.89, 1.1, "w") + [(23.8, 24.5, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="fold", doors=[(0.5, 1.5), (24.9, 25.9)],
        roof="euro", rc="dark", skirt="dark", word="kids",
        marks=[(3.2, 4.0, 1.25, 1.65, 0x1A1C1E)]),
    "Amz1990": dict(    # Am000: ex-SBB Eurofima 1st class, R8 car 1
        win=[(1.7, 2.4, "f")] + row(3.3, 9, 2.3, 1.3, "w") + [(23.9, 24.6, "f")],
        num=[(2.7, 3.0), (23.3, 23.6)], numcol="1", door="plug", roof="euro", rc="dark",
        skirt="light", word=None,
        marks=[(3.6, 4.0, 1.35, 1.7, 0x8E1F14), (21.8, 23.2, 1.3, 1.75, 0x3A1612)]),
    "Bmz2990": dict(    # Am900: the same SBB car, via DB, 2nd class
        win=[(1.7, 2.4, "f")] + row(3.3, 9, 2.3, 1.3, "w") + [(23.9, 24.6, "f")],
        num=[(2.7, 3.0), (23.3, 23.6)], door="plug", roof="euro", rc="dark", skirt="light",
        word=None, marks=[(21.8, 23.2, 1.3, 1.75, 0x3A1612)]),
    # --- ex-DB IC bodies (dark roof down to 3.5 m, thin yellow line)
    "Avmz1991": dict(   # Am500: ex-DB Avümz 111 TEE compartment car, R8 car 2
        win=[(1.8, 2.7, "f")] + row(3.3, 9, 2.3, 1.5, "p") + [(23.7, 24.6, "f")],
        num=[(2.8, 3.2), (23.2, 23.6)], door="fold", roof="db", rc="dark", skirt="dark",
        word=None, marks=[(21.7, 22.6, 1.3, 1.7, 0x2A0E0C)]),
    "Avmmz1991": dict(  # Ak100: ex-DB Avmmz 106.1 (Eurofima, IC-mod)
        win=[(1.9, 2.6, "f")] + row(3.4, 9, 2.3, 1.3, "m") + [(23.8, 24.5, "f")],
        num=[(2.8, 3.2), (23.2, 23.6)], door="plug", roof="db", rc="dark", skirt="dark",
        word=None, marks=[(21.7, 22.6, 1.3, 1.7, 0x16181A)]),
    "Bmpz2890": dict(   # Bm100 / Ap100: ex-DB Apmz 121/125, 16 narrow windows
        win=[(1.8, 2.9, "f")] + row(3.7, 16, 1.2, 0.85, "w") + [(23.6, 24.8, "f")],
        num=[(3.2, 3.5), (23.0, 23.3)], door="fold", roof="db", rc="dark", skirt="dark",
        word="lowcost", marks=[(21.8, 22.6, 1.3, 1.7, 0x2A0E0C)]),
    "Apmmz1890": dict(  # Ap200: ex-DB Apmmz 126.1, wide windows at both ends
        win=[(1.8, 2.7, "f"), (3.3, 4.7, "w")] + row(4.9, 14, 1.2, 0.85, "w") + [(21.7, 23.1, "w"), (23.7, 24.6, "f")],
        num=[(2.8, 3.2), (23.2, 23.6)], door="plug", roof="db", rc="dark", skirt="dark",
        word="relax", marks=[(21.8, 22.6, 1.3, 1.7, 0x2A0E0C)]),
    "Bpmz2091": dict(   # Bp200 / Bp500: ex-DB Bpmz 291/294 open 2nd class
        win=[(1.7, 2.4, "f"), (3.7, 4.4, "w")] + row(4.9, 9, 1.9, 1.3, "w") + [(22.1, 22.8, "w"), (24.0, 24.7, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="plug", roof="db", rc="dark", skirt="dark",
        word="lowcost", marks=[(21.4, 22.3, 1.3, 1.7, 0x2A0E0C)]),
    "Bpmbz2991": dict(  # Bp100: wheelchair version, blue pictogram on a door leaf
        win=[(1.7, 2.4, "f"), (3.7, 4.4, "w")] + row(4.9, 9, 1.9, 1.3, "w") + [(22.1, 22.8, "w"), (24.0, 24.7, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="plug", roof="db", rc="dark", skirt="dark",
        word="lowcost", wheelchair=True, marks=[(21.4, 22.3, 1.3, 1.7, 0x2A0E0C)]),
    "Bmpz2073": dict(   # Bp000: ex-SBB 1980 Schlieren open car, silvery glass
        win=[(1.8, 2.6, "v")] + row(3.9, 10, 1.9, 1.4, "s") + [(23.8, 24.6, "v")],
        num=[(3.0, 3.3), (23.1, 23.4)], door="plug", doors=[(0.7, 1.6), (24.8, 25.7)],
        roof="euro", rc="dark", skirt="dark", word="lowcost"),
    "Bmpz2090": dict(   # Bm000: new-build ASTRA Arad, windows in the middle 60 %
        win=[(4.0, 4.7, "w")] + row(5.3, 9, 1.8, 1.2, "w") + [(21.5, 22.2, "w")],
        num=[], door="plug", doors=[(0.6, 1.5), (24.9, 25.8)], roof="astra", rc="light",
        skirt="dark", word=None, band=(1.85, 3.15),
        marks=[(21.9, 22.9, 1.3, 1.7, 0x16181A)]),
    # --- UIC-X couchette bodies (round light roof, drop-light windows)
    "Bcmz5091": dict(   # Bc100 / Bc300: ex-DB Bcm 243 couchette
        win=[(1.9, 2.5, "f")] + row(3.2, 11, 1.9, 1.0, "t") + [(23.9, 24.5, "f")],
        num=[(2.7, 3.1), (23.3, 23.7)], door="fold", roof="ux", rc="light", skirt="dark",
        word="night"),
    "Bcmz5990": dict(   # Bc200 / B200: ex-DB Bvcmbz 249, wheelchair door inboard
        win=[(2.5, 2.9, "f"), (3.1, 3.7, "f")] + row(5.1, 10, 1.9, 1.0, "t") + [(23.9, 24.5, "f")],
        num=[(1.9, 2.3), (23.3, 23.7)], door="fold", roof="ux", rc="light", skirt="dark",
        word="night", wheelchair=True),
}

# RJ car codes (printed on every car, used in RJ consist lists) -> body + overrides
CARS = {
    "A000": ("Ampz1891", {}),
    "A100": ("Ampz1895", {}),
    "AB000": ("ABmz3090", {}),
    "Bk000": ("Bmz2191", {}),
    "Bk100": ("Bmz2190", {}),
    "Am000": ("Amz1990", {}),
    "Am900": ("Bmz2990", {}),
    "Bp000": ("Bmpz2073", {}),
    "Am500": ("Avmz1991", {}),
    "Ak100": ("Avmmz1991", {}),
    "Bm100": ("Bmpz2890", {"word": "lowcost"}),
    "Ap100": ("Bmpz2890", {"word": "relax"}),
    "Ap200": ("Apmmz1890", {}),
    "Bp200": ("Bpmz2091", {}),
    "Bp200.9": ("Bpmz2091", {"bike": True}),     # R8 reinforcement car, 18 bike places
    "Bp100": ("Bpmbz2991", {}),
    "Bp500": ("Bpmz2091", {"rc": "light", "skirt": "light"}),   # fresh 2026 repaints
    "Bm000": ("Bmpz2090", {}),
    "Bc100": ("Bcmz5091", {}),
    "Bc300": ("Bcmz5091", {}),
    "Bc200": ("Bcmz5990", {}),
    "B200": ("Bcmz5990", {"word": "bistro"}),
}


def spec(code):
    body, over = CARS[code]
    s = dict(TYPES[body])
    s.update(over)
    return s


# class words / pictograms on the lower body near the left end as seen:
# (lm_from, lm_to, colour, dashed); a coloured pictogram block follows some
WORDS = {
    "business": (3.4, 6.8, 0x5F6366, True),
    "relax": (3.4, 5.2, 0x5F6366, True),
    "lowcost": (3.4, 6.0, 0x3F4347, True),
    "kids": (3.4, 4.8, 0x5F6366, True),
    "night": (3.4, 5.6, 0x2B3F7A, True),
    "bistro": (3.4, 5.2, 0x5F6366, True),
}
PICTO = {"kids": 0x3C8FD0, "bistro": 0xB5282C, "night": 0x2B3F7A}

# where the grey roof starts on the side (metres) and the roof profile
ROOF_EDGE = {"euro": 3.62, "db": 3.48, "astra": 3.70, "ux": 3.40}

# ------------------------------------------------------------------ colours
YELLOW = 0xFFB612          # RAL 1028 melon yellow (#F4A900), lifted to the sunlit photo value
YELLOW_HI = 0xFFC83A       # cantrail / roof-curve highlight
BAND = 0x25292C            # anthracite window band (a touch darker than real, so glass reads)
SILVER = 0xA9AEB1
SILVER_JOINT = 0x5C6164
FROST = 0x8E989E
VEST = 0x7C868C
ROOFS = {
    "dark": Paint(0x585D60, top=0x676C6F),
    "light": Paint(0xA3AAAE, top=0xB5BCBF),
    "red": Paint(0x9C1C20, top=0xA82327),       # weathered ÖBB traffic red (RAL 3020)
}
SKIRTS = {"dark": Paint(0x3A3E41), "light": Paint(0x8D9396)}
UNDER = Paint(0x2A2C2E)
BOGIE = Paint(0x232426)
BOGIE_FRAME = Paint(0x3C3F42)
LOGO_RED = 0xD2232A
LOGO_NAVY = 0x2A2F6B
WORD = 0x6E7275
NUM = 0xF2F2F2
WHEEL_BLUE = 0x1F5FB0


def palette(liv, spec):
    """Colour set for livery `liv` on car spec `spec`."""
    rc = spec["rc"]
    if liv == "zlutacervenastrecha":      # foil-wrapped ex-ÖBB car, ÖBB red roof left on
        rc = "red"
    return dict(body=Paint(YELLOW), hi=Paint(YELLOW_HI), band=Paint(BAND), roof=ROOFS[rc],
                skirt=SKIRTS[spec["skirt"]], door=Paint(SILVER), joint=Paint(SILVER_JOINT))


# ------------------------------------------------------------------ model
def coach(code, liv, u0=0.0, owner="C"):
    """Parts of RJ car `code` (see CARS) whose front buffer face is at consist-u u0."""
    S = spec(code)
    C = palette(liv, S)
    doors = S.get("doors", DOORS_STD)
    b0, b1 = S.get("band", (1.95, 3.10))
    g0, g1 = b0 + 0.10, b1 - 0.12            # glass inside the band
    edge = ROOF_EDGE[S["roof"]]
    word = S.get("word")
    parts = []

    def side(f, u, v, z, d):
        m = (u - u0) * M                     # physical metres from the front
        lm = m if f == "-v" else 26.4 - m    # metres as seen, left to right
        h = z * PX
        # doors (single leaf, silver; folding doors show a centre joint)
        for (a, b) in doors:
            if a <= m <= b and 0.55 <= h <= 3.35:
                if S.get("wheelchair") and (a, b) == doors[0] and 1.2 <= h <= 1.6 and a + 0.25 <= m <= b - 0.25:
                    return Paint(WHEEL_BLUE)
                if 2.05 <= h <= 2.95 and a + 0.28 <= m <= b - 0.28:
                    return R.GLASS
                if S["door"] == "fold" and abs(m - (a + b) / 2) < 0.07:
                    return C["joint"]
                return C["door"]
        # roof / cantrail
        if h >= edge:
            return C["roof"]
        if h > b1:
            return C["hi"] if h > b1 + 0.35 else C["body"]
        # window band
        if h >= b0:
            for (a, b, k) in S["win"]:
                if a <= m <= b and g0 <= h <= g1:
                    if k == "f":
                        return Paint(FROST)
                    if k == "v":
                        return Paint(VEST) if h > g1 - 0.3 else R.GLASS
                    if k == "s":
                        return R.GLASS if h < g0 + 0.25 else R.GLASS_HI
                    if k == "m" and abs(m - (a + b) / 2) < 0.08:
                        return C["band"]
                    if k == "p" and b - 0.48 <= m <= b - 0.40:
                        return C["band"]
                    if k == "t":
                        if abs(h - (g1 - 0.30)) < 0.07:
                            return C["band"]
                        return R.GLASS_HI if h > g1 - 0.30 else R.GLASS
                    return R.GLASS_HI if h > g1 - 0.22 else R.GLASS
            for (a, b) in S.get("num", []):
                if a <= m <= b and 2.35 <= h <= 2.75:
                    return Paint(NUM)
            if S.get("bike") and 5.0 <= lm <= 5.9 and 2.3 <= h <= 2.8:
                return Paint(NUM)             # white bicycle pictogram in the bike area
            return C["band"]
        # lower body: logo, class word, display boxes
        if 1.20 <= h <= 1.55:
            if 19.3 <= lm <= 20.3:
                return Paint(LOGO_RED)
            if 20.3 < lm <= 20.9:
                return Paint(LOGO_NAVY)
            if word:
                a, b, col, dashed = WORDS[word]
                if a <= lm <= b and not (dashed and int((lm - a) / 0.45) % 3 == 2):
                    return Paint(col)
                if word in PICTO and b + 0.3 <= lm <= b + 0.9:
                    return Paint(PICTO[word])
        for (a, b, z0, z1, col) in S.get("marks", []):
            if a <= lm <= b and z0 <= h <= z1:
                return Paint(col)
        if h < 0.95:
            return C["skirt"]
        return C["body"]

    def end(f, u, v, z, d):
        h = z * PX
        if abs(v) < 0.42 and h < 3.4:
            return Paint(0x2B2D2F)          # gangway door / bellows
        if h >= edge:
            return C["roof"]
        if b0 <= h <= b1:
            return C["band"]
        if h < 0.95:
            return C["skirt"]
        return C["body"]

    def body_mat(f, u, v, z, d):
        if f == "+z":
            return C["roof"]
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        return end(f, u, v, z, d)

    ub0, ub1 = u0 + 0.14, u0 + L - 0.14
    if S["roof"] == "ux":
        # UIC-X: lower side wall, round roof whose ends slope down
        zw = zm(3.40)
        parts.append(Part(ub0, ub1, -W, W, ZB, zw, body_mat, owner))
        prof = [(zw, zw + 0.75, 0.10, 0.10), (zw + 0.75, zw + 1.35, 0.30, 0.35),
                (zw + 1.35, ZR, 0.62, 0.62)]
        for (za, zb, inset, uend) in prof:
            parts.append(Part(ub0 + uend, ub1 - uend, -W + inset, W - inset, za, zb,
                              lambda *a: C["roof"], owner))
    else:
        parts.append(Part(ub0, ub1, -W, W, ZB, ZS, body_mat, owner))
        parts.append(Part(ub0 + 0.05, ub1 - 0.05, -W + 0.2, W - 0.2, ZS, ZR,
                          lambda *a: C["roof"], owner))
    # gangways + buffers
    for (a, b) in ((u0 + 0.02, ub0), (ub1, u0 + L - 0.02)):
        parts.append(Part(a, b, -0.40, 0.40, 2.6, ZS - 0.8, lambda *a: Paint(0x2B2D2F), owner))
        for vc in (-0.64, 0.64):
            parts.append(Part(a, b, vc - 0.13, vc + 0.13, 2.4, 3.1, lambda *a: Paint(0x1E2022), owner))
    # underframe equipment + bogies (centres 19.0 m apart)
    parts.append(Part(u0 + 3.3, u0 + L - 3.3, -W + 0.25, W - 0.25, 0.0, ZB, lambda *a: UNDER, owner))
    for bm in (3.7, 22.7):
        bc = u0 + bm / M
        parts.append(Part(bc - 0.72, bc + 0.72, -W + 0.12, W - 0.12, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_FRAME if (f in ("+v", "-v") and z > 1.0) else BOGIE,
                          owner))
    return parts


def tiles(code, liv):
    parts = coach(code, liv)
    return [R.vehicle_tile(parts, [], d, 0.0, {"C"}) for d in DIRS]
