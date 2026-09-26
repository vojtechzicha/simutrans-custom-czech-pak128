"""ČKD T 478.1 / T 478.2 (ČD 749 / 751 / 752) "zamračená / bardotka" for KŽC.

Real (spz.logout.cz 751_data, KŽC side drawings T478.xxxx.png, 114.2 px/m):
16.50 m over buffers, 3.074 m wide, 4.103 m high, Bo'Bo', bogie pivots 9.0 m,
bogie wheelbase 2.4 m, wheels 1.0 m. Drawn at length 8 like the pak128.cs
T 478 (16.5 m / 8 cu = 2.06 m per cu).

u: 0 = front buffer face (cab 1), 8 = rear buffer face (cab 2).
Heights from the KŽC drawing (m above rail) -> model px via zm(); locos are
drawn ~2 px taller than coaches like the natives (KH).

Liveries (checked on kzc.cz and Commons photos, 2025-26):
  rudenka      749.006 (autumn 2025 repaint, kzc.cz news 1075/1094/1115/1126):
               dark wine red body + nose, light grey roof, frame band,
               underframe and bogies, yellow star on the nose, wine red pilot.
  cervena      749.253 (kzc.cz vehicle photos, news 1091/1123): red body,
               light grey roof, dark slate-grey frame band / underframe,
               yellow band along the bottom of both cab noses (front + cab
               sides up to the cab door), red/white chevrons on the pilot.
  modrobila    749.259 (Mšeno Aug 2025, Praha hl.n.): blue roof + upper body,
               light-grey (white) nose and a white band along the lower side,
               thin blue stripe under it, black frame band and underframe.
  cervenozluta 751.033 (Jedlová 2025, news 1077/1083/1118/1122): red-orange
               body, broad yellow band across the nose and along the side,
               red frame band, light grey roof, grey bogies.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import railkit as R
from railkit import Paint, Part, Lit
from render import DIRS

L = 8.0
M = 16.5 / L                 # metres per carunit
W = 0.92 * 3.074 / 2.825     # half width, cu
KH = 1.18                    # height exaggeration (natives draw locos taller)


def zm(h):
    return h / 0.375 * KH


def um(x_px):
    """KŽC drawing x (114.2 px/m, 0 = front buffer face) -> u."""
    return x_px / 114.2 / M


# heights (m)
Z_FRAME0 = zm(1.17)   # body / frame band bottom
Z_RED0 = zm(1.56)     # frame band top = main colour bottom
Z_NOSE = zm(2.72)     # nose top (windscreen sill)
Z_SIDE = zm(3.30)     # top of the painted side, grey cant above
Z_WALL = zm(3.64)     # side wall top
Z_ROOF1 = zm(3.92)
Z_ROOF = zm(4.10)
Z_VIS0 = zm(3.52)     # visor (roof brow) bottom at the cab front

# u positions
U_BUF = 0.15          # buffer depth
U_BEAM = 0.30         # buffer beam / frame band front
U_CAB = 0.46          # full-width body starts (windscreen top recess)
U_VIS = 0.22          # visor front
U_DOOR = (um(205), um(282))
U_CABWIN = (um(130), um(197))
U_WINS = [(um(641), um(697)), (um(812), um(868)), (um(1078), um(1134)), (um(1249), um(1305))]
U_GRILLE = (um(300), um(540))
U_LOGO = (um(556), um(634))
U_PLATE = (um(897), um(982))
U_EMBLEM = (um(1560), um(1602))
BOGIES = (3.75 / M, 12.75 / M)

WS = (0x28, 0x31, 0x39)
WS_HI = (0x4E, 0x60, 0x6E)
CABGLASS = (0x33, 0x3D, 0x46)
DARK = Paint(0x2A2B2D)
BLACKISH = Paint(0x1C1D1F)
BUFFER = Paint(0x2E2F31)
LAMP_OFF = (0x9A, 0x9E, 0xA0)


def shade(p, k):
    """A darker variant of a Paint (same face shading on top)."""
    return Paint(tuple(int(c * k) for c in p.base), top=tuple(int(c * k) for c in p.topc))


def livery(name):
    grey = Paint(0xAAB3B1, top=0xB4BCBA)          # light grey roof (drawing B2BEBC, darker in photos)
    if name == "rudenka":
        red = Paint(0x8A2334)
        lg = Paint(0xA9B1AF)
        return dict(body=red, roof=grey, cant=grey, frame=lg, under=Paint(0x9CA4A2), bogie=Paint(0x8E9694),
                    nose=red, pilot=Paint(0x7E1F30), pilot_edge=Paint(0xE6E6E0), chevron=None,
                    bands=[], nose_bands=[], cab_bands=[], emblem=(0xE8, 0xC0, 0x30), wscreen_sur=red,
                    logo_bg=Paint(0x3A3C3E))
    if name == "cervena":
        red = Paint(0xA52634)
        yel = Paint(0xF0C21A)
        slate = Paint(0x4F5B5B)
        return dict(body=red, roof=grey, cant=grey, frame=slate, under=Paint(0x454E4E), bogie=Paint(0x3E4545),
                    nose=red, pilot=Paint(0xB02834), pilot_edge=Paint(0xE8E6E2), chevron=Paint(0xEDEBE6),
                    bands=[], nose_bands=[(1.58, 1.92, yel)], cab_bands=[(1.58, 1.92, yel, um(170))],
                    emblem=(0xE8, 0xC0, 0x30), wscreen_sur=red, logo_bg=Paint(0x3A3C3E))
    if name == "modrobila":
        blue = Paint(0x2A7ECF)
        roofb = Paint(0x2466B4, top=0x2B6FC0)
        white = Paint(0xE4E6E3)
        blk = Paint(0x2A2A2B)
        return dict(body=blue, roof=roofb, cant=blue, frame=blk, under=Paint(0x262728), bogie=Paint(0x2E2F31),
                    nose=white, pilot=Paint(0xC8321E), pilot_edge=Paint(0xE8C21A), chevron=Paint(0x262626),
                    bands=[(1.56, 1.94, blue), (1.94, 2.46, white)], nose_bands=[],
                    cab_bands=[(1.56, 2.72, white, um(175))],
                    emblem=(0x30, 0x34, 0x3A), wscreen_sur=blue, logo_bg=Paint(0x3A3C3E))
    # cervenozluta: 751.033
    red = Paint(0xD8361E)
    yel = Paint(0xF2B81C)
    return dict(body=red, roof=grey, cant=grey, frame=red, under=Paint(0x8A908E), bogie=Paint(0x7A807E),
                nose=red, pilot=Paint(0xD0341E), pilot_edge=Paint(0xF0C020), chevron=Paint(0x262626),
                bands=[(1.80, 2.36, yel)], nose_bands=[(1.80, 2.36, yel)], cab_bands=[],
                emblem=(0x40, 0x34, 0x20), wscreen_sur=red, logo_bg=Paint(0x3A3C3E))


def nose_u(z):
    """Front face u of the cab at height z (model px), front end."""
    h = z / zm(1.0)
    if h < 1.17:
        return U_BEAM
    if h < 1.56:
        return U_BEAM - 0.02       # frame band with the lower lamps
    if h < 2.72:
        # lower nose leans back towards the bottom (drawing x 62 -> 32)
        t = (h - 1.56) / (2.72 - 1.56)
        return 0.27 - 0.13 * t
    if h < 3.52:
        # raked windscreen, recessed under the brow
        t = (h - 2.72) / (3.52 - 2.72)
        return 0.28 + 0.16 * t
    return U_VIS                    # the brow (visor) juts forward


def build(liv):
    C = livery(liv)
    parts, lines = [], []
    own = "V"

    def cab_local(u):
        return (u, "f") if u < L / 2 else (L - u, "r")

    def band_at(h, bands):
        for (a, b, p) in bands:
            if a <= h < b:
                return p
        return None

    def side(f, u, v, z, d):
        h = z / zm(1.0)
        cu, end = cab_local(u)
        # frame band (solebar)
        if h < 1.56:
            return C["frame"]
        if h >= 3.30:
            # grey cant with louvre rows over the machine room
            if 1.15 <= u <= 6.9 and 3.36 <= h <= 3.58 and not (U_DOOR[1] + 0.05 < cu < U_DOOR[1] + 0.1):
                if int((h - 3.36) / 0.075) % 2 == 1:
                    return Paint(0x6E7674) if C["cant"] is C["roof"] else Paint(0x1D4F8E)
            return C["cant"]
        # cab-end band (yellow on 749.253, white nose wrap on 749.259)
        base = None
        for (a, b, p, ulim) in C["cab_bands"]:
            if cu < ulim and a <= h < b:
                base = p
        if base is None:
            base = band_at(h, C["bands"]) or C["body"]
        # cab door (both ends): door window, dark gap on the machine-room side
        if U_DOOR[0] <= cu <= U_DOOR[1] and 1.62 <= h <= 3.25:
            if 2.8 <= h <= 3.18 and U_DOOR[0] + 0.04 <= cu <= U_DOOR[1] - 0.10:
                return CABGLASS
            if U_DOOR[1] - cu < 0.10:
                return shade(base, 0.55)
        # cab side window
        if U_CABWIN[0] <= cu <= U_CABWIN[1] and 2.80 <= h <= 3.22:
            return WS_HI if h > 3.12 else CABGLASS
        # machine-room windows (both sides, same physical u)
        for (a, b) in U_WINS:
            if a <= u <= b and 2.67 <= h <= 3.10:
                return CABGLASS
        # radiator grille behind cab 1 (both sides): louvres every other px row
        if U_GRILLE[0] <= u <= U_GRILLE[1] and 1.90 <= h <= 3.22:
            return shade(base, 0.62) if int(z) % 2 == 0 else shade(base, 0.86)
        # KŽC logo (dark plate) and the number plate
        if U_LOGO[0] <= u <= U_LOGO[1] and 2.08 <= h <= 2.42:
            return C["logo_bg"]
        if U_PLATE[0] <= u <= U_PLATE[1] and 1.78 <= h <= 2.06:
            return Paint(0xC8322A) if liv not in ("rudenka",) else Paint(0xE4E4DC)
        return base

    def front_face(f, u, v, z, d, rear):
        h = z / zm(1.0)
        av = abs(v)
        if h >= 3.50:
            return C["roof"] if not (h >= 3.62 and av < 0.20) else C["roof"]
        if h >= 2.72:
            # windscreens (two panes, centre pillar) framed by body colour
            if av < W - 0.14 and 2.80 <= h <= 3.44 and av > 0.09:
                return WS_HI if h > 3.30 else WS
            return C["wscreen_sur"]
        if h >= 1.56:
            # nose: bands, emblem / star in the middle
            p = band_at(h, C["nose_bands"])
            if 2.12 <= h <= 2.40 and av < 0.10 and C["emblem"] is not None:
                return C["emblem"]
            if p is not None:
                return p
            return C["nose"]
        if h >= 1.17:
            # frame band with the two lower lamps
            if 1.26 <= h <= 1.46 and 0.52 <= av <= 0.72:
                return R.TAIL if rear else R.HEAD
            return C["frame"]
        return C["frame"]

    def body_mat(f, u, v, z, d):
        rear = u > L / 2
        if f == "+z":
            h = z / zm(1.0)
            if h < 2.75:
                return C["nose"] if h > 1.56 else C["frame"]
            if h < 3.5:
                # tops of the stepped windscreen slabs read as the raked screen
                return front_face("-u", u, v, z, d, rear)
            cu, _ = cab_local(u)
            return C["roof"]
        if f in ("+v", "-v"):
            cu, _ = cab_local(u)
            if cu < U_CAB - 0.01:
                # side of the protruding nose / windscreen slabs
                h = z / zm(1.0)
                if 2.72 <= h < 3.50:
                    return C["wscreen_sur"]
                for (a, b, p, ulim) in C["cab_bands"]:
                    if a <= h < b:
                        return p
                p = band_at(h, C["nose_bands"])
                if p is not None and h >= 1.56:
                    return p
                if h < 1.56:
                    return C["frame"]
                if h >= 3.5:
                    return C["roof"]
                return C["nose"]
            return side(f, u, v, z, d)
        return front_face(f, u, v, z, d, rear)

    # main body (full width) between the cab recesses
    parts.append(Part(U_CAB, L - U_CAB, -W, W, Z_FRAME0, Z_WALL, body_mat, own))
    # stepped cab-front slabs at both ends
    step = 0.25
    for z0 in np.arange(Z_FRAME0, Z_WALL, step):
        z1 = min(Z_WALL, z0 + step)
        uf = nose_u((z0 + z1) / 2)
        h = (z0 + z1) / 2 / zm(1.0)
        taper = 0.08 if h < 2.72 else (0.12 if h < 3.5 else 0.04)
        parts.append(Part(uf, U_CAB, -W + taper, W - taper, z0, z1, body_mat, own))
        parts.append(Part(L - U_CAB, L - uf, -W + taper, W - taper, z0, z1, body_mat, own))

    # roof: rounded in two steps (grey cant is the wall top)
    def roof_mat(f, u, v, z, d):
        if f == "+z":
            # two roof fans over the radiator (dark discs) + hatch line
            if (1.30 <= u <= 1.70 or 1.84 <= u <= 2.28) and abs(v) < 0.34:
                return Paint(0x3A3E40, top=0x3A3E40)
            return C["roof"]
        return C["roof"]

    parts.append(Part(U_VIS + 0.02, L - U_VIS - 0.02, -W + 0.12, W - 0.12, Z_WALL, Z_ROOF1, roof_mat, own))
    parts.append(Part(U_CAB, L - U_CAB, -W + 0.34, W - 0.34, Z_ROOF1, Z_ROOF, roof_mat, own))

    # roof headlight (big lamp on the brow): lit at the front end only
    def lamp_mat(rear):
        def m(f, u, v, z, d):
            if f in ("-u", "+u"):
                if rear:
                    return LAMP_OFF
                return R.HEAD
            return Paint(0x5A6062, top=0x6A7072)
        return m
    parts.append(Part(U_VIS - 0.03, U_VIS + 0.22, -0.20, 0.20, zm(3.66), zm(4.14), lamp_mat(False), own))
    parts.append(Part(L - U_VIS - 0.22, L - U_VIS + 0.03, -0.20, 0.20, zm(3.66), zm(4.14), lamp_mat(True), own))
    # horns on the cab roof
    for uc in (0.62, L - 0.62):
        parts.append(Part(uc - 0.06, uc + 0.06, -0.26, 0.26, Z_ROOF - 0.1, Z_ROOF + 0.45,
                          lambda *a: Paint(0x8A8E86, top=0x9A9E96), own))

    # bogies (two Bo bogies) + underframe tank / air reservoirs
    for bc in BOGIES:
        half = 1.70 / M
        def bog(f, u, v, z, d, bc=bc):
            if f in ("+v", "-v"):
                if 1.2 < z < 2.3:
                    return C["bogie"]
                return BLACKISH
            return C["bogie"]
        parts.append(Part(bc - half, bc + half, -W + 0.14, W - 0.14, 0.0, zm(1.12), bog, own))
    parts.append(Part(um(820), um(1300), -W + 0.22, W - 0.22, zm(0.42), Z_FRAME0,
                      lambda *a: C["under"], own))
    parts.append(Part(um(655), um(805), -W + 0.30, W - 0.30, zm(0.55), Z_FRAME0,
                      lambda *a: Paint(0x55595B) if liv != "rudenka" else C["under"], own))
    # buffer beam + pilot at both ends
    for front in (True, False):
        a, b = (U_BUF, U_BEAM + 0.1) if front else (L - U_BEAM - 0.1, L - U_BUF)
        def beam(f, u, v, z, d):
            return C["frame"]
        parts.append(Part(a, b, -W + 0.06, W - 0.06, zm(0.92), Z_FRAME0, beam, own))
        pa, pb = (U_BEAM - 0.02, U_BEAM + 0.14) if front else (L - U_BEAM - 0.14, L - U_BEAM + 0.02)
        def pilot(f, u, v, z, d):
            h = z / zm(1.0)
            if h < 0.30:
                return C["pilot_edge"]
            if C["chevron"] is not None and h < 0.55 and f in ("-u", "+u"):
                if int((v + 1.0) / 0.22) % 2 == 0:
                    return C["chevron"]
            return C["pilot"]
        parts.append(Part(pa, pb, -W + 0.20, W - 0.20, zm(0.18), zm(0.92), pilot, own))
        ba, bb = (0.0, U_BUF) if front else (L - U_BUF, L)
        for vc in (-0.64, 0.64):
            parts.append(Part(ba, bb, vc - 0.14, vc + 0.14, 2.5, 3.3, lambda *a: BUFFER, own))
    return parts, lines


LIVERIES = ["rudenka", "cervena", "modrobila", "cervenozluta"]


def rows(liv):
    parts, lines = build(liv)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]
