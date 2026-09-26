"""Shared livery colours (unshaded albedo; paint.py multiplies them by each
pixel's shade factor). Keep every painted family on the same values so a mixed
ČD fleet reads as one corporate scheme; add new schemes here rather than as
family-local constants."""

# ČD corporate "Najbrt" scheme (RAL anchored, see liveries.md)
SAPPHIRE = (30, 52, 94)        # RAL 5003
SKY = (38, 120, 192)           # RAL 5015
LGREY = (206, 211, 209)        # RAL 7035
UMBRA = (104, 106, 100)        # RAL 7022 roof (weathered)
N2_STRIPE = (214, 220, 224)    # light stripe under the Najbrt 2 roof edge
YELLOW = (242, 194, 0)         # 1st-class stripe, plough (RAL 1003)
UF_GREY = (64, 66, 62)         # underframe / skirts
BLACK = (28, 28, 30)
WHITE = (236, 238, 238)

# PID grey-red (ROPID 2025 vehicle rules: RAL 7038 grey, RAL 3020 red, RAL 9005
# black doors / window bands, RAL 7022 roof gear, RAL 1003 yellow)
PID_GREY = (196, 200, 202)
PID_RED = (204, 34, 41)
PID_BLACK = (30, 31, 33)
PID_DOOR = (38, 40, 41)
PID_DGREY = (75, 77, 70)

# Plzeňský kraj (IDPK) on the RegioPanter: the values measured for the Arriva 650
# (tools/railrender/regiopanter_idpk.py), shared with the ČD 650.2
IDPK_BLUE = (22, 94, 188)
IDPK_DOOR = (246, 200, 28)
IDPK_YELLOW = (248, 210, 34)
IDPK_GREEN = (52, 172, 74)
IDPK_WHITE = (242, 245, 248)
IDPK_LETTER = (232, 238, 244)
IDPK_SKIRT = (94, 99, 106)
IDPK_PANEL = (63, 111, 179)       # cab front panel (mid blue)
IDPK_BOX = (52, 78, 146)          # roof fairings, top faces
IDPK_ROOF = (136, 142, 149)
IDPK_ROOF_EDGE = (188, 194, 200)
IDPK_BEAM = (242, 194, 48)

# ČD battery RegioPanter 690.2 "zeleno-modro-bílá"
BEMU_GREEN = (6, 152, 90)
BEMU_GREEN_DK = (15, 122, 69)     # wiper-line band on the front panel
BEMU_NAVY = (11, 44, 85)
BEMU_LOOP = (28, 146, 109)        # loop-chain pattern between green and navy
BEMU_DOOR = (8, 38, 72)
BEMU_STRIPE = (201, 200, 187)
BEMU_CANT = (214, 214, 208)
BEMU_BOX = (26, 62, 112)          # battery / equipment boxes, top faces

# Jihomoravský kraj (JMK) "Moravia" 530 / 550: Pantone 1787 C magenta, white, black
JMK_MAGENTA = (224, 68, 95)
JMK_WHITE = (220, 227, 229)
JMK_BLACK = (30, 33, 38)
JMK_ROOF = (186, 192, 197)
JMK_BOX = (202, 208, 212)
JMK_YELLOW = (226, 178, 54)


def dk(c, f):
    """Darker / lighter version of a colour (albedo scale)."""
    return tuple(max(0, min(255, int(round(v * f)))) for v in c)

# ČD 1990s red-cream
RC_RED = (178, 30, 40)
RC_CREAM = (234, 222, 184)
RC_ROOF = (168, 168, 163)

# marks
PLATE_RED = (200, 34, 44)
TEXT_GREY = (80, 84, 90)
