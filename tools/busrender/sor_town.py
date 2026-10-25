"""SOR city buses (NS, NB / NBG, EBN and the trolleybuses on their bodies) of
the town fleets, on the dpmhk.py bodies with the common SOR base
(dpmhk.SOR_SHAPE, owner 2026-10-24): render the sprite sheets of their
vehicle-bus / vehicle-trolleybus families. The family.yaml files are written
by hand.

    python tools/busrender/sor_town.py [family ...] [--preview DIR]

A family is named by its path under vehicle-bus/ or vehicle-trolleybus/
(mhd-kladno/sor_ns_12_electric) or by its folder name alone.

TVeh paints a town livery from a palette (TOWNS) instead of the DPMHK colours
of dpmhk.Veh. Palette keys, all colours top-face values (the sides get the
dpmhk.SHADE factors):
    body, roof     body colour (cant, rear panel default); roof top
    pod            roof boxes (A/C units, battery / CNG fairings); default roof
    lower          the lower body under the window band (default body)
    skirt          (height, colour): a strip from the body's lowest point ZB up
    bands          extra lower-body bands [(z_top, colour), ...] over the
                   skirt, the first whose z_top is above the pixel paints it
    disp           destination display colour
    front          face colours: bumper (lowest), chin (between the lamps),
                   mask (the white / coloured nose of the NB), corner (the
                   lamp surrounds of the NS / EBN), trim (A-pillars)
    rear           bumper, panel (between the lamps), upper (round the rear
                   window)
    cant           colour of the top row of the side under the roof edge
                   (default: the black window band runs up to it)
    decal          optional f(veh, p, u, right) -> colour or None on the
                   lower body (logos, chevrons)
    overlay        the same over the whole side, glass included (the Opava
                   ribbon)
    poles          trolley pole colours: pole, tip, and (fraction, colour)
                   for the upper sleeve and the lower base (default dpmhk's)
Heights are real metres above the road; with the base the body starts at ZB
(Z0 + SKIRT), so a band below ZB is not drawn.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import numpy as np                                                      # noqa: E402
import dpmhk as H                                                       # noqa: E402
from dpmhk import Veh, mk, sh, inr, HW, PER_CU, DIRS                     # noqa: E402
from render import render                                               # noqa: E402

BLACK, FRAME, GLASS, GLASS2 = H.BLACK, H.FRAME, H.GLASS, H.GLASS2
HEADL, TAILL, SILVER = H.HEADL, H.TAILL, H.SILVER
WHITE = (0xF6, 0xF6, 0xF6)
ROOFW = (0xEE, 0xEE, 0xEE)
AMBER = H.AMBER
SCREEN = (0x2A, 0x34, 0x3D)        # driver's glass, never lit
CAB_GLASS = (0x4D, 0x4D, 0x4E)     # the windscreen: a step off the lit special, dark at night
SCREEN_HI = (0x4F, 0x62, 0x72)


# ====================================================================== palettes
KLADNO_RED = (0xED, 0x1C, 0x24)
MOST_YEL = (0xFF, 0xE8, 0x00)
DPP_RED = (0xCF, 0x0B, 0x15)
DPMB_RED = (0xD8, 0x24, 0x1C)
LEDG = (0x62, 0xD6, 0x4A)          # green LED displays (Brno, Most, Opava, Olomouc)
DPMO_NAVY = (0x2B, 0x33, 0x7A)
DPMO_RED = (0xD5, 0x1A, 0x1F)
MDPO_RED = (0xC8, 0x10, 0x1C)
FM_GREEN = (0x17, 0x7B, 0x35)      # zelená metalíza (F-M / Havířov e-buses)
FM_GREEN_ROOF = (0x22, 0x8E, 0x45)
FM_GREEN_LOW = (0x22, 0xB1, 0x4C)  # its bright green lower body (VTPsim's sheet)
FM_GREEN_DK = (0x10, 0x52, 0x24)
FM_SKY = (0x8E, 0xC3, 0xE6)        # the Frýdek-Místek wrap: light blue
FM_BLUE = (0x3C, 0x7F, 0xB0)
FM_NSG_GREY = (0xC3, 0xC3, 0xC3)
FM_NSG_SKY = (0x99, 0xD9, 0xEA)
FM_NSG_LINE = (0x39, 0x39, 0x3A)
FM_GREY = (0x8C, 0x8C, 0x8D)
HAV_BLUE = (0x3F, 0xA8, 0xEE)      # Havířov city blue (as the VTPsim / odis_town sheets)
HAV_BLUE_DK = (0x15, 0x85, 0xD8)
HAV_YEL = (0xF6, 0xD0, 0x2A)
KRNOV_YEL = (0xF2, 0xB7, 0x05)
KRNOV_BLUE = (0x2A, 0x5A, 0xA8)
KRNOV_NAVY = (0x1C, 0x26, 0x52)
TRINEC_LIME = (0xB5, 0xE6, 0x1D)
TRUT_CYAN = (0x30, 0xBE, 0xEA)
CHR_RED = (0xDC, 0x34, 0x38)
HRAN_GREEN = (0x5C, 0xB5, 0x47)
NJ_RED = (0xA5, 0x1D, 0x24)
NJ_ROOF = (0xB2, 0x26, 0x2D)
ARRIVA_BLUE = (0x0A, 0xA3, 0xD2)
ARRIVA_ROOF = (0x2A, 0xB4, 0xDE)
DPO_BLUE = (0x28, 0x8C, 0xD2)
LIGHT_GREY = (0xD8, 0xD8, 0xD8)


CW = 0.2355        # one pixel along the body in the ne / sw views, metres


def _hash(*v):
    h = 2166136261
    for x in v:
        h = ((h ^ (int(x) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


def lower_row(v, p):
    """0 = the body row right under the window band, 1 the next one down, -1
    the lowest row of the band"""
    return math.floor((v.ZBAND0 - p.z) / 0.25)


def glass_row(v, p):
    """0 = the lowest glass row of the window band, counting up"""
    return math.floor((p.z - v.ZWIN0) / 0.25)


def from_rear(v, u):
    """whole pixels from the rear end of the body"""
    return int((v.U[-1] - u) / CW)


def section_of(v, u):
    """(section index, fraction along that section from its front)"""
    for k in range(len(v.U) - 1):
        if u < v.U[k + 1] or k == len(v.U) - 2:
            return k, (u - v.U[k]) / (v.U[k + 1] - v.U[k])


# Krnov (from the old VTPsim-based sheet): golden-yellow + blue chevron pairs,
# three rows tall, pointing to the rear (yellow ahead of blue), in the lower
# window band and on the lower body, and the navy "krnov" wordmark behind the
# front axle; metres from the front, per side
KRNOV_MARKS = {
    True: dict(band=(3.5, 7.8), lower=(4.5,), word=3.1),         # door side
    False: dict(band=(7.8,), lower=(0.3, 5.2), word=2.4),
}
KRNOV_WORD = ["#.##.#", "######"]


def krnov(v, p, u, right):
    if right and v.door_at(u):
        return None
    m = KRNOV_MARKS[right]
    rows = ((glass_row(v, p), 2, m["band"]), (lower_row(v, p) - 1, 0, m["lower"]))
    for r, top, marks in rows:
        k = top - r if top else r            # 0 = the chevron's top row
        if not 0 <= k <= 2:
            continue
        for a in marks:
            c = math.floor((u - v.M(a)) / CW) - (1 if k == 1 else 0)
            if c == 0:
                return KRNOV_YEL
            if c == 2:
                return KRNOV_BLUE
    r = lower_row(v, p) - 1
    c = math.floor((u - v.M(m["word"])) / CW)
    if 0 <= r < len(KRNOV_WORD) and 0 <= c < len(KRNOV_WORD[0]) and KRNOV_WORD[r][c] == "#":
        return KRNOV_NAVY
    return None


def seg_px(u, z, a, b):
    """distance in pixels (CW along the body, 0.25 m up) from (u, z) to the
    segment a-b"""
    ux, uz = (u - a[0]) / CW, (z - a[1]) / 0.25
    vx, vz = (b[0] - a[0]) / CW, (b[1] - a[1]) / 0.25
    t = max(0.0, min(1.0, (ux * vx + uz * vz) / max(1e-9, vx * vx + vz * vz)))
    return math.hypot(ux - t * vx, uz - t * vz)


def mdpo_ribbon(v, p, u, right):
    """Opava 2026 e-bus (VTPsim-based sheet, photos): a thin red ribbon from
    the roof edge over the second door falling steeply forward to the front
    wheel arch, then back along the body just under the windows with one oval
    loop up into the windows over the middle section, rising at the rear (an
    overlay, over the glass too)"""
    L = v.U[-1]
    zl = v.ZBAND0 - 0.30                       # the line under the windows
    segs = [((v.M(3.8), v.ZR), (v.M(2.1), zl)),
            ((v.M(2.1), zl), (L - 1.0, zl)),
            ((L - 1.0, zl), (L - 0.25, v.ZBAND0 + 0.55))]
    if any(seg_px(u, p.z, a, b) < 0.6 for a, b in segs):
        return MDPO_RED
    uc, zc = v.M(4.9), (zl + v.ZWIN1 - 0.20) / 2      # the loop
    au, az = 0.75, (v.ZWIN1 - 0.20 - zl) / 2
    r = math.hypot((u - uc) / au, (p.z - zc) / az)
    if abs(r - 1.0) * min(au / CW, az / 0.25) < 0.6:
        return MDPO_RED
    return None


def havirov_logo(v, p, u, right):
    """Havířov: the white three-arch logo, then the yellow "město pro život"
    script on the lower body behind the front door"""
    a = v.M(2.0)
    if inr(u, a, a + 0.9) and v.ZB + 0.15 <= p.z < v.ZBAND0 - 0.05:
        return WHITE if int((u - a) / 0.30) % 3 != 2 else None
    b = a + 1.1
    if inr(u, b, b + 2.4) and v.ZB + 0.30 <= p.z < v.ZBAND0 - 0.05:
        return HAV_YEL if int((u - b) / 0.30) % 4 != 3 else None
    return None


# Trutnov MHD (photos seznam-autobusu 398768, 415210, 442882; the old
# khk_town sheets): a scattered mosaic of small blocks straddling the lower edge
# of the window band, denser towards the rear, and the white TRUTNOV MHD logo
# behind the front axle; per section (mosaic span, logo span) as fractions
MOSAIC = [(0xF3, 0x8B, 0x1F), (0xE0, 0x2E, 0x8C), (0xFF, 0xD2, 0x1E), (0x1E, 0x50, 0xA8),
          (0x9C, 0xE4, 0xFA)]
TRUT_SPANS = {1: [((0.45, 0.98), (0.30, 0.40))],
              2: [((0.55, 0.98), (0.28, 0.38)), ((0.30, 0.98), (0.06, 0.22))]}


def trutnov(v, p, u, right):
    if right and v.door_at(u):
        return None
    k, f = section_of(v, u)
    mos, logo = TRUT_SPANS[len(v.U) - 1][k]
    r = lower_row(v, p)
    cell = int(u / CW)
    if mos[0] <= f <= mos[1]:
        t = (f - mos[0]) / (mos[1] - mos[0])
        h = _hash(k, cell, right)
        if (h % 1000) / 1000.0 < 0.28 + 0.62 * t:
            rows = {0}
            if (h >> 14) % 2:
                rows.add(-1)                       # the block reaches up into the band
            elif (h >> 15) % 3 == 0:
                rows.add(1)
            if r in rows:
                return MOSAIC[(h >> 10) % len(MOSAIC)]
    if logo[0] <= f <= logo[1] and (r == 1 or (r == 2 and cell % 2 == 0)):
        return WHITE
    return None


def arriva_swoosh(v, p, u, right):
    """Přerov (Arriva): the short white swoosh rising from ahead of the front
    wheel arch towards the rear (as on Lubak91's Přerov sheet)"""
    a, b = v.M(0.9), v.M(2.3)
    s = (u - a) / (b - a)
    if 0.0 <= s <= 1.0 and abs(p.z - (v.ZB + 0.10 + 0.70 * s)) < 0.14:
        return WHITE
    return None


# Hranice: the white line-art of town landmarks on the rear windows (the old
# Lubak91-based sheet), pixels from the rear, rows from the top of the glass
HRANICE_ART = ["............#.",
               ".#....##....#.",
               ".#...#..#...#.",
               "###..####..###"]


def hranice(v, p, u, right):
    k = 3 - glass_row(v, p)
    c = from_rear(v, u) - 3
    if 0 <= k < 4 and 0 <= c < len(HRANICE_ART[0]) and HRANICE_ART[k][c] == "#":
        return WHITE
    return None


def nj_marks(v, p, u, right):
    """Nový Jičín: the white lettering on the rear quarter of the window band
    (a bar and a dash, as on the old Lubak91-based sheet)"""
    k = glass_row(v, p)
    c = from_rear(v, u)
    if (c == 3 and 1 <= k <= 3) or (6 <= c <= 8 and k == 2):
        return WHITE
    return None


CHR_TEXT = "MĚSTSKÁ AUTOBUSOVÁ DOPRAVA CHRUDIM"


def chr_lettering(v, p, u, right):
    """Chrudim 42079: "MĚSTSKÁ AUTOBUSOVÁ DOPRAVA CHRUDIM" in black on the
    white strip over the windows, a dotted line at this scale (0.2-0.9 of the
    length, gaps at the word breaks)"""
    if p.z < v.ZR - 0.25:
        return None
    L = v.U[-1]
    f = u / L
    if not 0.2 <= f < 0.9:
        return None
    cell = int(u / CW)
    ch = CHR_TEXT[min(len(CHR_TEXT) - 1, int((f - 0.2) / 0.7 * len(CHR_TEXT)))]
    return BLACK if ch != " " and cell % 2 == 0 else None


def fm_speckle(v, p, u, right):
    """the Frýdek-Místek city wrap on the NS 12 electric (VTPsim's sheet): a
    speckled skyline of light blue, blue and grey over the lower body from
    behind the front door back, denser towards the bottom, under one white row"""
    r = lower_row(v, p)
    if u < 1.4 or r < 1:
        return None
    h = _hash(int(u / CW), r, right)
    if (h % 1000) / 1000.0 >= (0.15, 0.40, 0.75, 0.85, 0.90)[min(r, 5) - 1]:
        return None
    return (FM_SKY, FM_SKY, FM_BLUE, FM_GREY, FM_SKY, FM_BLUE, BLACK)[(h >> 10) % 7]


def dark_line(u0, u1):
    """a dark line along the middle of the lower body from u0 to u1 (VTPsim's
    F-M sheets: the NSG 12 wrap, the green e-bus)"""
    def draw(v, p, u, right):
        if lower_row(v, p) == 2 and u0 <= u < u1:
            return FM_NSG_LINE
        return None
    return draw


TOWNS = {
    # Městská doprava Kladno: white, the black sill under the window band, a bold
    # red band straight under it, a white skirt strip; black front mask with red
    # lamp corners (NS) / white front with a black band and red corners (NB);
    # black upper rear and bumper, white middle
    "kladno": dict(body=WHITE, roof=ROOFW, lower=KLADNO_RED, skirt=(0.25, WHITE),
                   disp=AMBER,
                   front=dict(bumper=BLACK, chin=BLACK, mask=WHITE, corner=KLADNO_RED, trim=BLACK),
                   rear=dict(bumper=BLACK, panel=WHITE, upper=BLACK)),
    # DP Most a Litvínova (NS): white, the yellow lower sides over a dark trim;
    # black front mask outlined in yellow, the red apron between the lamps;
    # yellow upper rear, white middle, red bumper
    "most_ns": dict(body=WHITE, roof=ROOFW, lower=MOST_YEL, skirt=(0.12, (0x30, 0x30, 0x30)), disp=LEDG,
                    front=dict(bumper=DPP_RED, chin=DPP_RED, mask=WHITE, corner=MOST_YEL, trim=MOST_YEL),
                    rear=dict(bumper=DPP_RED, panel=WHITE, upper=MOST_YEL)),
    # its NB 12 / 18: white with the yellow skirt line; the ex-Prague front
    # (red lower front, the black band under the windscreen with yellow
    # corners), the yellow upper rear framing the rear window, red bumpers
    "most_nb": dict(body=WHITE, roof=ROOFW, lower=WHITE, skirt=(0.25, MOST_YEL), disp=LEDG,
                    front=dict(bumper=DPP_RED, band=DPP_RED, mask=BLACK, corner=MOST_YEL, trim=WHITE),
                    rear=dict(bumper=DPP_RED, panel=WHITE, upper=MOST_YEL)),
    # the DPP city red-white of the ex-DPP NB 12 83 in Most (green LED); the
    # NB 18 189 (ex-DPP 6668) keeps the Prague amber displays (most_dpp18)
    "most_dpp": dict(body=WHITE, roof=(0xFF, 0xFF, 0xFF), lower=WHITE, bands=[(0.87, DPP_RED)], disp=LEDG,
                     front=dict(bumper=DPP_RED, chin=BLACK, mask=BLACK, trim=BLACK),
                     rear=dict(bumper=DPP_RED, panel=WHITE, upper=BLACK)),
    # DPMB white-red: the red skirt; the NS with the black cap and the red
    # swoosh up the front corners, a white smile line over the red apron; the NB
    # with the black mask over a white band and a red apron
    "dpmb": dict(body=WHITE, roof=(0xF2, 0xF2, 0xF0), lower=WHITE, skirt=(0.30, DPMB_RED), disp=LEDG,
                 front=dict(bumper=DPMB_RED, chin=WHITE, mask=BLACK, band=WHITE, corner=SILVER, trim=DPMB_RED),
                 rear=dict(bumper=DPMB_RED, panel=WHITE, upper=BLACK)),
    # its NS 12 and TNS 12 (the earlier VZ render, DPMB drawing sor-ns.png): the
    # red apron with white lamp corners, the black rear over the red bumper,
    # yellow sleeves on the upper pole ends (photos of 3065, 3068)
    "dpmb_ns": dict(body=WHITE, roof=(0xF2, 0xF2, 0xF0), lower=WHITE, skirt=(0.30, DPMB_RED), disp=LEDG,
                    front=dict(bumper=DPMB_RED, chin=DPMB_RED, mask=BLACK, corner=WHITE, trim=DPMB_RED),
                    rear=dict(bumper=DPMB_RED, panel=BLACK, upper=BLACK),
                    poles=dict(pole=H.POLE, tip=H.TIP, sleeve=(0.35, H.TIP))),
    # DPMO: white, the window band outlined in red (the top row of the side
    # and a line under the windows), the red stripe over the navy skirt, the
    # red line round the black front section; black front mask, navy bumper
    "dpmo": dict(body=WHITE, roof=ROOFW, lower=WHITE, skirt=(0.25, DPMO_NAVY), stripe=(0.25, 0.50, DPMO_RED),
                 cant=DPMO_RED, sill=DPMO_RED, disp=LEDG,
                 front=dict(bumper=DPMO_NAVY, chin=BLACK, mask=BLACK, corner=SILVER, trim=DPMO_RED),
                 rear=dict(bumper=DPMO_NAVY, panel=WHITE, upper=BLACK)),
    # MDPO Opava white-red: the red roof edge sweeping down the A-pillar, the
    # straight red skirt; black mask, white strip, red apron
    "mdpo": dict(body=WHITE, roof=ROOFW, roofedge=MDPO_RED, lower=WHITE, skirt=(0.30, MDPO_RED), disp=LEDG,
                 poles=dict(pole=H.POLE, tip=H.TIP, sleeve=(0.55, H.TIP)),       # 32Tr: P4T's sheet
                 front=dict(bumper=MDPO_RED, chin=WHITE, mask=BLACK, band=WHITE, corner=SILVER, trim=MDPO_RED),
                 rear=dict(bumper=MDPO_RED, panel=WHITE, upper=BLACK)),
    # MDPO 2026 e-bus: white, no red skirt, the thin red ribbon; white front
    "mdpo_e": dict(body=WHITE, roof=ROOFW, lower=WHITE, overlay=mdpo_ribbon, disp=LEDG,
                   front=dict(bumper=LIGHT_GREY, chin=WHITE, mask=WHITE, corner=SILVER, trim=WHITE),
                   rear=dict(bumper=LIGHT_GREY, panel=WHITE, upper=BLACK)),
    # green metallic (F-M and Havířov e-buses of 2018): dark green upper body,
    # the bright green lower body with a dark line, bright green rear over a
    # dark green bumper
    "zelenametaliza": dict(body=FM_GREEN, roof=FM_GREEN_ROOF, lower=FM_GREEN_LOW, decal=dark_line(1.4, 8.7),
                           disp=AMBER,
                           front=dict(bumper=FM_GREEN, chin=FM_GREEN, mask=FM_GREEN, corner=SILVER, trim=FM_GREEN),
                           rear=dict(bumper=FM_GREEN_DK, panel=FM_GREEN_LOW, upper=BLACK)),
    # the Frýdek-Místek city wrap: white with the speckled skyline (NS 12 e)
    "fm_polep": dict(body=WHITE, roof=(0xDA, 0xDA, 0xDA), lower=WHITE, decal=fm_speckle, disp=AMBER,
                     front=dict(bumper=WHITE, chin=WHITE, mask=WHITE, corner=SILVER, trim=BLACK),
                     rear=dict(bumper=FM_SKY, panel=WHITE, upper=BLACK)),
    # the same wrap on the grey NSG 12: the light-blue lower body
    "fm_polep_nsg": dict(body=FM_NSG_GREY, roof=FM_NSG_GREY, lower=FM_NSG_SKY,
                         decal=dark_line(1.4, 5.9), disp=AMBER,
                         front=dict(bumper=FM_NSG_SKY, chin=FM_NSG_GREY, mask=FM_NSG_GREY, corner=SILVER,
                                    trim=BLACK),
                         rear=dict(bumper=FM_NSG_SKY, panel=FM_NSG_SKY, upper=BLACK)),
    # Havířov city blue with the logo and slogan (NBG 18)
    "havirov": dict(body=HAV_BLUE, roof=HAV_BLUE, pod=HAV_BLUE, lower=HAV_BLUE_DK, decal=havirov_logo,
                    disp=(0xEC, 0xEE, 0xE4),
                    front=dict(bumper=HAV_BLUE_DK, chin=HAV_BLUE, mask=HAV_BLUE, trim=HAV_BLUE),
                    rear=dict(bumper=HAV_BLUE_DK, panel=HAV_BLUE, upper=HAV_BLUE)),
    # Krnov city white: the black belt line, the chevron pairs and the wordmark
    "krnov": dict(body=WHITE, roof=ROOFW, lower=WHITE, sill=BLACK, overlay=krnov,
                  disp=AMBER,
                  front=dict(bumper=BLACK, chin=BLACK, mask=WHITE, corner=SILVER, trim=BLACK),
                  rear=dict(bumper=BLACK, panel=WHITE, upper=BLACK)),
    # Třinec white-green: the lime skirt and roof unit, lime front corners,
    # lime upper rear and bumper
    "trinec": dict(body=WHITE, roof=ROOFW, pod=TRINEC_LIME, lower=WHITE, skirt=(0.25, TRINEC_LIME), disp=AMBER,
                   front=dict(bumper=TRINEC_LIME, chin=BLACK, mask=WHITE, corner=TRINEC_LIME, trim=TRINEC_LIME),
                   rear=dict(bumper=TRINEC_LIME, panel=WHITE, upper=TRINEC_LIME)),
    # Trutnov MHD light blue with the mosaic and the TRUTNOV MHD logo
    "trutnov": dict(body=TRUT_CYAN, roof=TRUT_CYAN, lower=TRUT_CYAN, overlay=trutnov, disp=AMBER,
                    front=dict(bumper=TRUT_CYAN, chin=TRUT_CYAN, mask=TRUT_CYAN, trim=TRUT_CYAN),
                    rear=dict(bumper=TRUT_CYAN, panel=TRUT_CYAN, upper=TRUT_CYAN)),
    # MHD Chrudim (ARRIVA): all red / white with the lettering on a white strip
    # over the windows / white with the red stripe right under the windows
    "chrudim_red": dict(body=CHR_RED, roof=CHR_RED, lower=CHR_RED, disp=AMBER,
                        front=dict(bumper=CHR_RED, chin=WHITE, mask=WHITE, trim=CHR_RED),
                        rear=dict(bumper=CHR_RED, panel=CHR_RED, upper=CHR_RED)),
    "chrudim_white": dict(body=WHITE, roof=ROOFW, lower=WHITE, cant=WHITE, overlay=chr_lettering, disp=AMBER,
                          front=dict(bumper=DPP_RED, chin=WHITE, mask=WHITE, trim=WHITE),
                          rear=dict(bumper=DPP_RED, panel=WHITE, upper=WHITE)),
    "chrudim_pruh": dict(body=WHITE, roof=ROOFW, lower=WHITE, stripe=(0.40, 0.90, CHR_RED), disp=AMBER,
                         front=dict(bumper=DPP_RED, chin=WHITE, mask=WHITE, trim=WHITE),
                         rear=dict(bumper=DPP_RED, panel=WHITE, upper=WHITE)),
    # MHD Hranice: apple green with the white belt line under the windows, the
    # green top row of the side and the landmark line-art on the rear windows
    "hranice": dict(body=WHITE, roof=(0xE2, 0xE2, 0xE2), lower=HRAN_GREEN, cant=HRAN_GREEN, sill=WHITE,
                    overlay=hranice, disp=AMBER,
                    front=dict(bumper=HRAN_GREEN, chin=BLACK, mask=HRAN_GREEN, corner=SILVER, trim=BLACK),
                    rear=dict(bumper=HRAN_GREEN, panel=WHITE, upper=BLACK)),
    # Nový Jičín red metallic, the white lettering on the rear windows
    "nj": dict(body=NJ_RED, roof=NJ_ROOF, lower=NJ_RED, overlay=nj_marks, disp=AMBER,
               front=dict(bumper=NJ_RED, chin=BLACK, mask=NJ_RED, corner=SILVER, trim=NJ_RED),
               rear=dict(bumper=NJ_RED, panel=NJ_RED, upper=BLACK)),
    # Arriva blue (Přerov) with the white swoosh at the rear
    "arriva": dict(body=ARRIVA_BLUE, roof=ARRIVA_ROOF, lower=ARRIVA_BLUE, decal=arriva_swoosh, disp=AMBER,
                   front=dict(bumper=ARRIVA_BLUE, chin=BLACK, mask=ARRIVA_BLUE, corner=SILVER, trim=ARRIVA_BLUE),
                   rear=dict(bumper=ARRIVA_BLUE, panel=ARRIVA_BLUE, upper=BLACK)),
    # DPO TNB 12: white, the blue roof edge and front band
    "dpo_tnb": dict(body=WHITE, roof=ROOFW, roofedge=DPO_BLUE, lower=WHITE, disp=AMBER,
                    # light grey poles with a dark base (photos of 3912)
                    poles=dict(pole=(0xC8, 0xCC, 0xD0), tip=(0x30, 0x32, 0x34), base=(0.18, (0x50, 0x54, 0x58))),
                    front=dict(bumper=LIGHT_GREY, chin=WHITE, mask=WHITE, band=DPO_BLUE, trim=DPO_BLUE),
                    rear=dict(bumper=LIGHT_GREY, panel=WHITE, upper=DPO_BLUE)),
}
TOWNS["most_dpp18"] = dict(TOWNS["most_dpp"], disp=AMBER)


# ====================================================================== body
class TVeh(Veh):
    """an SOR city body of dpmhk.py in a town palette (TOWNS)"""
    # fronts keep their bumper, apron and lamps (dpmhk.Veh.face_split); the
    # rears paint their two bumper rows over ZB themselves
    FACE_SPLIT = {("front", "ns"): 1.14, ("front", "ebn"): 1.14, ("front", "nb"): 0.82}

    def setup_livery(self):
        self.P = TOWNS[self.liv]
        self.ROOF = self.P["roof"]
        self.TRIM = self.P["front"].get("trim", BLACK)

    def col(self, c, f):
        return sh(c, f)

    # roof ----------------------------------------------------------------
    def tex_roof(self, p, u):
        if self.face in ("ns", "ebn") and u < self.cap:
            return BLACK if abs(p.t) < HW - 0.30 else self.TRIM
        if self.P.get("roofedge") and abs(p.t) > HW - 0.30:
            return self.P["roofedge"]
        return self.ROOF

    def tex_pod(self, p, u, k):
        f = p.face
        c = self.P.get("pod", self.ROOF)
        if self.pods[k][4] == "ac" and f == "top" and abs(p.t) < 0.25:
            return tuple(int(v * 0.86) for v in c)          # condenser grille
        if self.pods[k][4] == "dark":
            return sh((0x50, 0x52, 0x56), f)
        return c if f == "top" else sh(c, f)

    # sides ---------------------------------------------------------------
    def door_kick(self):
        return None

    def tex_side(self, p, u, U1):
        c = super().tex_side(p, u, U1)
        ov = self.P.get("overlay")
        if ov and c is not None:
            o = ov(self, p, u, p.face == "right")
            if o is not None:
                return sh(o, p.face)
        if c == AMBER:
            return self.P["disp"]
        right = p.face == "right"
        if not right and inr(u, *self.drv) and self.ZWIN0 <= p.z < self.ZWIN1:
            if c == GLASS:
                return SCREEN                               # the driver's window is never lit
            if c == GLASS2:
                return SCREEN_HI
        return c

    def cant(self, p, u):
        if self.face in ("ns", "ebn") and u < self.cap:
            return BLACK
        if self.P.get("cant") and p.z >= self.ZR - 0.25:
            return sh(self.P["cant"], p.face)
        if p.z < self.ZBAND1:
            return sh(BLACK, p.face)
        return sh(self.P["body"], p.face)

    def lower(self, p, u, right):
        z, f = p.z, p.face
        P = self.P
        dec = P.get("decal")
        if dec:
            c = dec(self, p, u, right)
            if c is not None:
                return sh(c, f)
        if P.get("sill") and z >= self.ZBAND0 - 0.25:
            return sh(P["sill"], f)
        sk = P.get("skirt")
        if sk and z < self.ZB + sk[0]:
            return sh(sk[1], f)
        st = P.get("stripe")
        if st and self.ZB + st[0] <= z < self.ZB + st[1]:
            return sh(st[2], f)
        for ztop, c in P.get("bands", ()):
            if z < ztop:
                return sh(c, f)
        return sh(P.get("lower", P["body"]), f)

    # front ---------------------------------------------------------------
    def tex_front(self, p):
        t, z = p.t, p.z
        f = "front"
        a = abs(t)
        F = self.P["front"]
        disp = self.P["disp"]
        if self.face == "nb":
            if z < 0.34:
                return BLACK
            if a > HW - 0.36 and inr(z, 0.58, 0.82):
                return HEADL if a < HW - 0.10 else sh(F.get("corner", SILVER), f)
            if z < 0.70:
                return sh(F["bumper"], f)
            if F.get("band") and z < 0.82:
                return sh(F["band"], f)
            if z < 1.12:
                return sh(F["mask"], f)
            if a > HW - 0.08:
                return sh(F["mask"], f)
            if inr(z, 2.36, 2.62) and a < 1.00:
                return disp
            if inr(z, 1.16, 2.70) and a < HW - 0.12:
                return CAB_GLASS
            return sh(F["mask"], f)
        if self.face == "ebn":
            if z < 0.36:
                return BLACK
            if z < 0.80:
                if a > HW - 0.40 and inr(z, 0.50, 0.70):
                    return HEADL if a < HW - 0.10 else sh(F.get("corner", SILVER), f)
                return sh(F["bumper"], f)
            if z < 1.10:
                return sh(F["chin"], f)
            if a > HW - 0.10:
                return self.TRIM
            if inr(z, 1.14, 2.46) and a < HW - 0.16:
                return CAB_GLASS
            if inr(z, 2.54, 2.82) and a < 0.98:
                return disp
            return BLACK
        # ns
        if z < 0.44:
            return sh(F["bumper"], f)
        if z < 1.08:
            if a > HW - 0.40:
                if inr(z, 0.62, 0.88) and a < HW - 0.10:
                    return HEADL
                return sh(F.get("corner", SILVER), f)
            if z > 0.98:
                return sh(SILVER, f)
            return sh(F["chin"], f)
        if a > HW - 0.10:
            return self.TRIM
        if inr(z, 1.14, 2.42) and a < HW - 0.16:
            return CAB_GLASS
        if inr(z, 2.52, 2.82) and a < 0.98:
            return disp
        return BLACK

    # rear ----------------------------------------------------------------
    def tex_rear(self, p):
        t, z = p.t, p.z
        f = "rear"
        a = abs(t)
        R = self.P["rear"]
        disp = self.P["disp"]
        if self.rearstyle == "nb":
            if z < 0.30:
                return BLACK
            if a > HW - 0.26 and inr(z, 0.70, 1.30):
                return TAILL
            if z < max(0.64, self.ZB + 0.40):        # two rows over the raised body bottom
                return sh(R["bumper"], f)
            if z < 1.74:
                if inr(z, 1.36, 1.74) and a < HW - 0.25 and int((z - 1.36) / 0.09) % 2 == 1:
                    return sh((0xC8, 0xCA, 0xCC), f)        # the louvred panel
                return sh(R["panel"], f)
            if inr(z, 2.36, 2.58) and inr(t, 0.25, 0.80):
                return disp
            if inr(z, 1.78, 2.62) and a < HW - 0.22:
                return GLASS
            return sh(R["upper"], f)
        if a > HW - 0.26 and inr(z, 0.55, 1.35):
            return TAILL
        if z < max(0.45, self.ZB + 0.40):
            return sh(R["bumper"], f)
        if z >= self.ZBAND0 + 0.20:
            if inr(z, 2.42, 2.62) and inr(t, 0.30, 0.80):
                return disp
            if inr(z, 1.75, 2.62) and a < HW - 0.30:
                return GLASS
            return sh(R["upper"], f)
        return sh(R["panel"], f)


def draw_poles(img, view, L, origin, bs, bz, bt, cols):
    """dpmhk.draw_poles in a palette's colours: the pole, an upper sleeve and
    a lower base as fractions of its length, the tip"""
    for base, tip in H.pole_tips(view, L, origin, bs, bz, bt):
        if tip is None:
            continue
        pts = list(H.bresenham(int(math.floor(base[0])), int(math.floor(base[1])), tip[2], tip[3]))
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            c = cols["pole"]
            if "sleeve" in cols and i >= n * (1.0 - cols["sleeve"][0]):
                c = cols["sleeve"][1]
            elif "base" in cols and i < n * cols["base"][0]:
                c = cols["base"][1]
            if 0 <= x < 128 and 0 <= y < 128:
                img[y, x] = c
        img[tip[3], tip[2]] = cols["tip"]


def build(sp, livery):
    """the sheet rows of a body spec in a town palette, sections placed by the
    section rule (as dpmhk.build)"""
    m = TVeh(sp, livery)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        tiles = []
        for d in DIRS:
            o = np.array(H.origin_for(d))
            if not m.single:
                o = o + (4 - l / 2.0) * PER_CU[d]
            img, zb = render(d, m.boxes(i), m.tex_for(i), L, o)
            if m.poles:
                pb = m.M(m.poles[0])
                if m.U[i] <= pb < m.U[i + 1]:
                    s = m.U[i + 1] - pb
                    if "poles" in m.P:
                        draw_poles(img, d, L, o, s, m.roof_top(pb) + 0.16, m.poles[1], m.P["poles"])
                    else:
                        H.draw_poles(img, d, L, o, s, m.roof_top(pb) + 0.16, m.poles[1], H.TIP)
            tiles.append(img)
        rows.append(tiles)
    return rows


# ====================================================================== bodies
WINRISE = 0.25     # the town window line one row higher (owner, 2026-10-25)


def town(base, **kw):
    """a town body: base spec with the raised window line"""
    return mk(base, winrise=WINRISE, **kw)


# SOR NS 12 electric (Kladno 51-58): the long battery fairing
KL_NS12E = town(H.NS12, pods=[(1.70, 11.75, 0.26, 1.10, "fair")])
# SOR NS 18 electric (Kladno 59-66): low battery fairings along both sections
KL_NS18E = town(H.NS18, pods=[(1.70, 10.40, 0.22, 1.05, "fair"), (12.0, 18.20, 0.22, 1.05, "fair")])
# SOR NBG 18 (Kladno 44-47): doors 2-0-2-2-0 (front, before the joint, behind
# it), an A/C unit behind the front, the CNG fairing over the rear half of the
# front section, an A/C unit on the rear section
KL_NBG18 = town(H.NB18, doors=[(0.30, 1.55), (9.80, 11.00), (13.10, 14.30)],
              pods=[(1.20, 2.60, 0.22, 0.80, "ac"), (5.80, 11.60, 0.34, 1.00, "fair"),
                    (14.80, 16.20, 0.22, 0.80, "ac")])
# SOR EBN 11,1 (Kladno): the battery fairings of the EBN 11
KL_EBN11 = town(H.EBN11, real_len=11.1,
              pods=[(1.20, 3.60, 0.30, 0.95, "fair"), (4.20, 6.60, 0.30, 0.95, "fair"),
                    (7.20, 9.60, 0.30, 0.95, "fair")])


AC = "ac"
FAIR = "fair"
# DP Most a Litvínova: NS 12 / 18 with two A/C units; NB 12 / 18 with the small
# white A/C unit behind the front
MOST_NS12 = town(H.NS12, pods=[(1.80, 3.60, 0.22, 0.80, AC), (8.00, 9.40, 0.22, 0.80, AC)])
MOST_NS18 = town(H.NS18, pods=[(1.80, 3.60, 0.22, 0.80, AC), (12.20, 13.80, 0.20, 0.75, AC)])
MOST_NB12 = town(H.NB12, pods=[(0.80, 2.00, 0.22, 0.80, AC)])
MOST_NB18 = town(H.NB18, pods=[(0.80, 2.00, 0.22, 0.80, AC)])
# car 189 (ex-DPP 6668): the two A/C units of the DPP NB 18 flanking the bellows
MOST_NB18_DPP = town(H.NB18, pods=[(10.40, 11.80, 0.22, 0.80, AC), (12.80, 14.00, 0.22, 0.80, AC)])
# DPMB: NS 12 with one A/C unit at 0.47-0.66 of the length; NBG 12 with the tall
# CNG fairing over the front-middle roof and the A/C unit ahead of it; TNS 12
# with the plain roof pod and the poles
DPMB_NS12 = town(H.NS12, pods=[(5.60, 7.90, 0.24, 0.85, AC)])
DPMB_NBG12 = town(H.NB12, pods=[(1.40, 2.40, 0.22, 0.80, AC), (2.60, 8.00, 0.36, 1.00, FAIR)])
DPMB_TNS12 = town(H.NS12, pods=[(1.80, 7.20, 0.26, 1.00, FAIR)], poles=(7.60, 0.30))
# DPMO 501: the battery and A/C pods
DPMO_NS12E = town(H.NS12, pods=[(1.70, 8.00, 0.26, 1.05, FAIR), (8.40, 9.80, 0.22, 0.80, AC)])
# MDPO Opava: the NS 12 electric's battery and A/C pods, the NSG 12's big CNG
# fairing and A/C unit, the Škoda 32Tr (dpmhk.py's model, poles)
MDPO_NS12E = town(H.NS12, pods=[(1.70, 8.60, 0.28, 1.05, FAIR), (9.00, 10.20, 0.22, 0.80, AC)])
MDPO_NSG12 = town(H.NS12, pods=[(1.60, 7.40, 0.36, 1.00, FAIR), (8.00, 9.20, 0.22, 0.80, AC)])
MDPO_32TR = town(H.MODELS["32tr"])
# Frýdek-Místek / Havířov: the NS 12 electric's long battery fairing, the NSG 12
# CNG fairing and A/C unit; the Havířov NBG 18 fairings
FM_NS12E = town(H.NS12, pods=[(1.70, 11.75, 0.26, 1.10, FAIR)])
FM_NSG12 = town(H.NS12, pods=[(1.60, 7.40, 0.36, 1.00, FAIR), (8.00, 9.20, 0.22, 0.80, AC)])
HAV_NBG18 = town(H.NB18, pods=[(1.80, 10.00, 0.36, 1.00, FAIR), (13.00, 15.60, 0.30, 0.95, FAIR)])
# Krnov and Třinec NS 12
KRN_NS12 = town(H.NS12, pods=[(1.80, 3.60, 0.22, 0.80, AC), (8.00, 9.40, 0.22, 0.80, AC)])
TRI_NS12 = town(H.NS12, pods=[(3.00, 5.00, 0.24, 0.85, AC)])
# Trutnov NB 12 / NBG 18, Chrudim NB 12
TRU_NB12 = town(H.NB12, pods=[(0.80, 2.00, 0.22, 0.80, AC)])
TRU_NBG18 = town(H.NB18, pods=[(1.80, 10.00, 0.36, 1.00, FAIR), (13.00, 15.60, 0.30, 0.95, FAIR)])
CHR_NB12 = town(H.NB12, pods=[(0.80, 2.00, 0.22, 0.80, AC)])
# the Lubak91 EBN towns: the EBN 9,5 and 11,1 battery fairings
EBN95 = town(H.MODELS["ebn95"])
PRE_EBN11 = town(H.EBN11, real_len=11.1,
                 pods=[(1.20, 3.60, 0.30, 0.95, FAIR), (4.20, 6.60, 0.30, 0.95, FAIR), (7.20, 9.60, 0.30, 0.95, FAIR)])
# DPO SOR TNB 12: the Škoda 30Tr body (TNB 12) with its fairing, poles and rack
DPO_TNB12 = town(H.MODELS["30tr"])

# family (path under the repo) -> {livery colour: [(spec, palette), ...] in row order}
FAMILIES = {
    "vehicle-bus/mhd-kladno/sor_ns_12_electric": {"kladnobilocervena": [(KL_NS12E, "kladno")]},
    "vehicle-bus/mhd-kladno/sor_ns_18_electric": {"kladnobilocervena": [(KL_NS18E, "kladno")]},
    "vehicle-bus/mhd-kladno/sor_nbg_18": {"kladnobilocervena": [(KL_NBG18, "kladno")]},
    "vehicle-bus/mhd-kladno/sor_ebn_11_1": {"kladnobilocervena": [(KL_EBN11, "kladno")]},
    "vehicle-bus/dp-most-litvinov/sor_ns_12": {"mostzlutocervena": [(MOST_NS12, "most_ns")]},
    "vehicle-bus/dp-most-litvinov/sor_ns_18": {"mostzlutocervena": [(MOST_NS18, "most_ns")]},
    "vehicle-bus/dp-most-litvinov/nb_12": {"mostzlutocervena": [(MOST_NB12, "most_nb")],
                                           "prahacervenobila": [(MOST_NB12, "most_dpp")]},
    "vehicle-bus/dp-most-litvinov/sor_nb_18": {"mostzlutocervena": [(MOST_NB18, "most_nb")],
                                               "prahacervenobila": [(MOST_NB18_DPP, "most_dpp18")]},
    "vehicle-bus/dpmb/sor_ns_12": {"dpmbbilocervena": [(DPMB_NS12, "dpmb_ns")]},
    "vehicle-bus/dpmb/sor_nbg_12": {"dpmbbilocervena": [(DPMB_NBG12, "dpmb")]},
    "vehicle-trolleybus/dpmb/tns_12": {"dpmbbilocervena": [(DPMB_TNS12, "dpmb_ns")]},
    "vehicle-bus/dpmo/sor_ns_12_electric": {"dpmobilomodrocervena": [(DPMO_NS12E, "dpmo")]},
    "vehicle-bus/mdpo/sor_ns_12_electric": {"mdpobilagrafika": [(MDPO_NS12E, "mdpo_e")]},
    "vehicle-bus/mdpo/sor_nsg_12": {"mdpobilocervena": [(MDPO_NSG12, "mdpo")]},
    "vehicle-trolleybus/mdpo/32tr": {"mdpobilocervena": [(MDPO_32TR, "mdpo")]},
    "vehicle-bus/mhd-frydek-mistek/sor_ns_12_electric": {"zelenametaliza": [(FM_NS12E, "zelenametaliza")],
                                                         "frydekmistekpolep": [(FM_NS12E, "fm_polep")]},
    "vehicle-bus/mhd-frydek-mistek/sor_nsg_12": {"frydekmistekpolep": [(FM_NSG12, "fm_polep_nsg")]},
    "vehicle-bus/mhd-havirov/sor_ns_12_electric": {"zelenametaliza": [(FM_NS12E, "zelenametaliza")]},
    "vehicle-bus/mhd-havirov/sor_nbg_18": {"havirovmodra": [(HAV_NBG18, "havirov")]},
    "vehicle-bus/mhd-krnov/sor_ns_12": {"krnovbila": [(KRN_NS12, "krnov")]},
    "vehicle-bus/mhd-trinec/sor_ns_12": {"trinecbilozelena": [(TRI_NS12, "trinec")]},
    "vehicle-bus/mhd-trutnov/sor_nb_12": {"trutnovmhd": [(TRU_NB12, "trutnov")]},
    "vehicle-bus/mhd-trutnov/sor_nbg_18": {"trutnovmhd": [(TRU_NBG18, "trutnov")]},
    "vehicle-bus/iredo/sor_nb_12": {"chrudimcervena": [(CHR_NB12, "chrudim_red")],
                                    "chrudimbila": [(CHR_NB12, "chrudim_white")],
                                    "bilacervenypruh": [(CHR_NB12, "chrudim_pruh")]},
    "vehicle-bus/mhd-hranice/sor_ebn_9_5": {"hranicezelena": [(EBN95, "hranice")]},
    "vehicle-bus/mhd-novy-jicin/sor_ebn_9_5": {"cervenametaliza": [(EBN95, "nj")]},
    "vehicle-bus/mhd-prerov/sor_ebn_11_1": {"arrivamodra": [(PRE_EBN11, "arriva")]},
    "vehicle-trolleybus/dpo/sor_tnb_12": {"bilamodrastrecha": [(DPO_TNB12, "dpo_tnb")]},
}


def main(argv):
    pv = None
    if "--preview" in argv:
        i = argv.index("--preview")
        pv = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
        os.makedirs(pv, exist_ok=True)
    for fam, livs in FAMILIES.items():
        key = fam.split("/", 1)[1]
        if argv and key not in argv and fam.split("/")[-1] not in argv:
            continue
        sd = os.path.join(REPO, *fam.split("/"), "sprites")
        os.makedirs(sd, exist_ok=True)
        for color, parts in livs.items():
            rows = []
            for sp, liv in parts:
                rows += build(sp, liv)
            sheet = H.save_rows(rows, os.path.join(sd, color + ".png"))
            if pv:
                H.preview(sheet, os.path.join(pv, f"{fam.split('/')[-1]}-{color}.png"))
            print(f"{fam}/sprites/{color}.png  rows={len(rows)}")


if __name__ == "__main__":
    main(sys.argv[1:])
