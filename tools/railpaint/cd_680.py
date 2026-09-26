"""ČD 680 Pendolino (681 + 081 + 683 + 084 + 684 + 082 + 682) in the Kotas
livery (the only one it ever wore): silver body, anthracite window band with a
yellow line under it, turquoise cantrail stripe and lower band / skirt, grey
roof, anthracite cab "helmet" and a yellow band across the nose.

The upstream pak128.CS Pendolino (TommPa9, rail-psg mail/680/cd_680_pendolino.png,
frozen in src/680/cd_680_pendolino.png as the repo shipped it until 2026-09) is
drawn in the same stripe layout
but with sky blue where the real train is turquoise and a sky-blue roof. Its
palette is flat (one exact colour per zone and shade), so zones come straight
from the upstream colour classes, with position rules only for the pantograph
yellow and the cab front:

  ROOF   75BAFF                         -> grey roof
  SIDE   6AB5FF 59ACFF 4FA7FF 46A3FF    -> turquoise (cantrail stripe, lower
         359AFF 2D96FF (+ 00FFFF 008080    band, skirt, lower nose)
         nose accents)
  SILVER DADADA CACACA E1E1E1 CFCFCF ... -> cool silver
  DARK   414141 303030 363636 ...       -> anthracite (window band, helmet,
                                           roof equipment, underframe)
  YELLOW F2F200 FFFF22 D5D500 ...       -> golden yellow line / nose band
  PANTO  FFFF00 (all views), FFF200 in the pure side views -> grey pantograph
  6B6B6B / 6C6C6C windscreens (special colours) -> plain dark cab glass

Every colour keeps the upstream shading (luminance relative to the class
reference). On the cab front (end view facing the cab) the row above the
headlight row is painted yellow too, so the nose band is as broad as on the
real train, and stray lit glass in the helmet becomes cab glass.

  python tools/railpaint/cd_680.py [--preview DIR]

writes vehicle-rail/ceske-drahy/680/sprites/cdpendolino.png.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paint import save_sheet, preview

REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy", "680")
SRC = os.path.join(HERE, "src", "680", "cd_680_pendolino.png")   # frozen upstream sheet
OUT = os.path.join(FAM, "sprites", "cdpendolino.png")

T = 0xE7FFFF

# ------------------------------------------------------------ Kotas palette
SILVER = (208, 212, 218)      # body (photo #C0C4C8 lit .. #DCDBE1 direct sun)
ROOF = (160, 166, 172)        # roof skin, a step darker than the side
TURQ = (34, 166, 190)         # cantrail stripe, lower band, skirt (#22A6BE)
GOLD = (240, 194, 30)         # yellow line and nose band (#F0C020)
ANTH_TINT = (1.0, 1.07, 1.2)  # anthracite = upstream neutral dark, cool tint (#3F454D)
PANTO = (92, 94, 99)          # pantograph frame (dark so it reads on the grey roof)
CABGLASS = (44, 52, 64)       # windscreens, never lit

ROOF_C = {0x75BAFF}
SIDE_C = {0x6AB5FF, 0x59ACFF, 0x4FA7FF, 0x46A3FF, 0x359AFF, 0x2D96FF, 0x00FFFF, 0x008080}
SILVER_C = {0xDADADA, 0xCACACA, 0xE1E1E1, 0xCFCFCF, 0xDDDDDD, 0xC4C4C4}
DARK_C = {0x414141, 0x303030, 0x363636, 0x3A3A3A, 0x282828, 0x373737, 0x1B1B1B, 0x232323, 0x414241, 0x3D3D3D}
YEL_C = {0xF2F200, 0xFFFF22, 0xD5D500, 0xE1E100, 0xCACA00, 0xFFFF0D, 0xFFFF42}
WSCREEN_C = {0x6B6B6B, 0x6C6C6C}
LIT = 0x4D4D4D

CAB_ROWS = {0: 5, 6: 1}       # sprite row -> end-view column that shows its cab


def hx(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def scaled(target, native, ref):
    f = lum(hx(native)) / lum(hx(ref))
    return tuple(int(max(0, min(255, round(v * f)))) for v in target)


def repaint():
    a = np.array(Image.open(SRC).convert("RGB"))
    v = (a[..., 0].astype(int) << 16) | (a[..., 1].astype(int) << 8) | a[..., 2]
    out = a.copy()
    H, W = v.shape
    col_of = np.arange(W)[None, :].repeat(H, 0) // 128
    row_of = np.arange(H)[:, None].repeat(W, 1) // 128

    table = {}
    for c in ROOF_C:
        table[c] = scaled(ROOF, c, 0x75BAFF)
    for c in SIDE_C:
        table[c] = scaled(TURQ, c, 0x4FA7FF)
    for c in SILVER_C:
        table[c] = scaled(SILVER, c, 0xDADADA)
    for c in YEL_C:
        table[c] = scaled(GOLD, c, 0xF2F200)
    for c in DARK_C:
        g = hx(c)[0]
        table[c] = tuple(int(min(255, round(g * t))) for t in ANTH_TINT)
    for c in WSCREEN_C:
        table[c] = CABGLASS
    table[0xFF8040] = GOLD               # amber pixels beside the headlights
    for c, rgb in table.items():
        out[v == c] = rgb

    # pantograph: FFFF00 everywhere, FFF200 in the pure side views; FFF200 on
    # the cab front of the 682 is nose paint
    side = np.isin(col_of, (3, 7))
    out[v == 0xFFFF00] = PANTO
    out[(v == 0xFFF200) & side] = PANTO
    out[(v == 0xFFF200) & ~side] = GOLD

    # cab fronts: broaden the nose band, no lit glass in the helmet
    for r, c in CAB_ROWS.items():
        sl = (slice(r * 128, (r + 1) * 128), slice(c * 128, (c + 1) * 128))
        tv, to = v[sl], out[sl]
        lamp = np.isin(tv, (0xFFFF53, 0xFF211D)).any(axis=1)
        y = int(np.where(lamp)[0][0])
        to[y - 1, np.isin(tv[y - 1], list(DARK_C))] = GOLD
        to[tv == LIT] = CABGLASS
    return out


def run(prev=None):
    out = repaint()
    rows = [out[r * 128:(r + 1) * 128] for r in range(out.shape[0] // 128)]
    save_sheet(rows, OUT)
    print("wrote", OUT)
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview([OUT], os.path.join(prev, "p680.png"), z=3)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    prev = args[args.index("--preview") + 1] if "--preview" in args else None
    run(prev)


if __name__ == "__main__":
    main()
