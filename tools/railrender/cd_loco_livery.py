"""Shared ČD locomotive livery colours and slugs (tools/railrender/cd_loco_*.py).

Every ČD loco generator takes its paint from here, so a mixed train of 362s,
754s and Vectrons reads as one corporate fleet and matches the ČD units
(tools/railpaint/palette.py holds the RAL anchors; the values are re-exported).

Layouts, checked on Commons photos (Category:CZ Class 362 of ČD in Najbrt
livery, 2024-2026):

najbrt2   ČD Najbrt 2 on locomotives: SKY upper body up to the roof edge, a
          WHITE stripe at headlight level (just under the side windows'
          bottom edge on the cab, running round both fronts), SAPPHIRE lower
          body below the stripe down to the solebar, frame / bogies near
          black, roof and roof gear UMBRA grey. Cab fronts: SKY above the
          stripe, white stripe, SAPPHIRE below; windscreen surround black.
          Dark-blue ČD logo + "České dráhy" on each side, mid-body, in the SKY
          zone; small white ČD logo on each front under the windscreens.
najbrt1_2 ČD Najbrt 1.2 ("lichoběžníky"): LGREY body and cab fronts, grey
          (N12_GREY) frame and roof; on each side a big SAPPHIRE trapezoid
          over a SKY one, rising from the solebar toward one end and covering
          about the middle half of the side (see 362.092 / 362.109 photos);
          SKY windscreen surround on the fronts, dark-blue ČD logo on the
          front and in the trapezoid-free part of each side.
najbrt1   as najbrt1_2, white (N1_WHITE) body with a white frame and roof.

Colour slugs and display names (use exactly these in family.yaml):
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "railpaint"))
import palette as P  # noqa: E402

SAPPHIRE = P.SAPPHIRE        # RAL 5003 lower body / trapezoid
SKY = P.SKY                  # RAL 5015 (units); locos read lighter, use LOCO_SKY
LOCO_SKY = (60, 148, 214)    # loco light blue: N2 upper body, N1.2 lower trapezoid
                             # (every loco photo is clearly lighter than RAL 5015)
LGREY = P.LGREY              # RAL 7035 N1.2 body
UMBRA = P.UMBRA              # RAL 7022 roof
WHITE = (236, 240, 242)      # N2 stripe, front logos
N12_GREY = (112, 116, 118)   # N1.2 frame + roof
N1_WHITE = (232, 236, 238)   # N1 body / frame / roof
FRAME = (38, 40, 43)         # solebar, bogies, buffer beam (all schemes)
PLOUGH = P.YELLOW            # yellow ploughs / buffer beam stripes

# older ČD / ČSD schemes still carried by regular (non-retro) locos
RC_RED = (176, 37, 42)       # ČSD red-cream "polomáčený" (704)
RC_CREAM = (239, 228, 192)
BC_BLUE = (31, 63, 122)      # ČD 1990s blue-cream (210, 754)
BC_CREAM = (239, 228, 192)
RY_RED = (200, 32, 46)       # ČD red-yellow (210, 754)
RY_YELLOW = (242, 194, 0)
RB_RED = (200, 32, 46)       # 714 red-blue (1990s modernisation)
RB_BLUE = SAPPHIRE
OB_ORANGE = (240, 125, 26)   # 799 orange-blue
OB_BLUE = SAPPHIRE
GY_GREEN = (47, 94, 58)      # ČSD green with yellow band (163)
GY_YELLOW = (242, 194, 0)

LIVERIES = {
    # slug:           (name_en,                 name_cs)
    "najbrt2":        ("Najbrt 2",              "Najbrt 2"),
    "najbrt1_2":      ("Najbrt 1.2",            "Najbrt 1.2"),
    "najbrt1":        ("Najbrt 1",              "Najbrt 1"),
    "vectron":        ("ČD Vectron",            "ČD Vectron"),
    "vectronrsl":     ("ČD Vectron, RS Lease", "ČD Vectron, RS Lease"),
    "cd384":          ("ČD 230 km/h",           "ČD 230 km/h"),
    "cd109e":         ("ČD 109E",               "ČD 109E"),
    "cervenokremova": ("red-cream",             "červeno-krémová"),
    "modrokremova":   ("blue-cream",            "modro-krémová"),
    "cervenozluta":   ("red-yellow",            "červeno-žlutá"),
    "cervenomodra":   ("red-blue",              "červeno-modrá"),
    "oranzovomodra":  ("orange-blue",           "oranžovo-modrá"),
    "zelenozluta":    ("green-yellow",          "zeleno-žlutá"),
    "oranzovokremova": ("orange-cream",         "oranžovo-krémová"),
    "zelenokremova":  ("green-cream",           "zeleno-krémová"),
}
