"""DPmML Tatra T3M.3 (family vehicle-tram/dp-most-litvinov/t3m3): the TV14
details painted onto Lubak91's Most T3 sheet.

The base is the former Most T3 sheet, frozen in src/most_t3_lubak91.png
(1024x128, one row, 8 views). Every edit is a pixel edit on that drawing, so
the hand-drawn look stays. What the 2021-2026 photos of the Most cars show and
the base lacks:

  LED     the roll-sign boxes (orange ff7f27 on the base: front above the
          windscreen, side in the first window behind the middle door, rear
          line number) are LED displays now: a black panel with green text.
  doors   the folding doors are yellow leaves with tall dark windows, split at
          sill height; the base draws them as grey leaves (9c9c9c) with a beige
          sill bar (afa67f). In the side view the glass becomes two straight
          slits per door (the base's zigzag folding pattern reads as crosses
          once the leaves are yellow); the diagonal views keep their pattern.
  dash    a dark rubber bumper band runs across the front just under the
          headlights, with the red skirt below it.
  rear    (candidate c) the same band under the tail lights.
  panto   (candidate c) the diamond pantograph is painted yellow; the base
          arms are dark ochre. Head bar and base stay dark.

Candidates: a = LED + doors, b = a + front band, c = b + rear band +
yellow pantograph.

  python tools/railpaint/most_t3m3.py {a|b|c} [--out PATH] [--preview DIR]

writes vehicle-tram/dp-most-litvinov/t3m3/sprites/mostzlutocervena.png unless
--out is given; --preview writes the current sheet and all three candidates
side by side on grass, 8 views at 1x and 3x.
"""
import hashlib
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(HERE, "src", "most_t3_lubak91.png")
BASE_SHA256 = "0cfd9741d54542f79a8bcab18730c35007d4d5a04285c3d9dd84f7d9d22d9342"
SPRITE = os.path.join(REPO, "vehicle-tram", "dp-most-litvinov", "t3m3", "sprites",
                      "mostzlutocervena.png")

BG = (231, 255, 255)
YELLOW = (255, 242, 0)        # body yellow of the base
LED_PANEL = (38, 38, 38)      # 262626, already on the base (pantograph head)
LED_TEXT = (1, 221, 1)        # 01DD01: the always-lit green special, so the displays glow at night
BAND = (62, 62, 62)           # 3e3e3e, already on the base
GRASS = (78, 136, 56)         # pak128.CS temperate grass (tools/gen_shops.py)

# base colours that get recoloured
DOOR_GREY = (156, 156, 156)   # 9c9c9c door leaves (views 2, 3, 4 only)
DOOR_SILL = (175, 166, 127)   # afa67f sill bar across the doors (view 3)
ROLLSIGN = (255, 127, 39)     # ff7f27 displays
PANTO = {(99, 80, 0): (196, 170, 22),     # 635000 arms in shade
         (103, 83, 0): (214, 188, 30),    # 675300
         (115, 93, 0): (232, 206, 40)}    # 735d00 lit arms

# Simutrans image_t::rgbtab (see tools/pak_extract.py): no new colour may hit one
RGBTAB = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}

# Displays, per view: (pixels that become the green text). Every other
# ROLLSIGN pixel of that view becomes the black panel. Coordinates are
# within the 128-px view tile. Ends of a display and the front display seen
# edge-on from the side stay panel.
LED_TEXT_PX = {
    0: [(80, 95)],                                   # rear line number
    1: [(62, 99)],                                   # rear line number
    2: [(71, 83), (45, 95)],                         # front display, rear number
    3: [(44, 85), (45, 85), (46, 85)],               # side display
    4: [(52, 82), (52, 83),                          # side display
        (70, 88), (71, 88), (72, 88), (73, 87)],     # front display
    5: [(61, 89), (62, 89), (63, 89)],               # front display
    6: [(52, 86), (52, 87), (53, 87), (53, 88), (54, 88)],  # front display
    7: [(105, 87)],                                  # rear line number
}

# Front bumper band: one pixel row just under the headlights, measured on the
# straight-on photo of 257 (headlight centre, band, skirt) and scaled to the
# se view's front face; the diagonal views follow the drawn face.
FRONT_BAND = {
    5: [(x, 97) for x in range(57, 68)],
    4: [(x, 97) for x in range(67, 77)],
    6: [(x, 97) for x in range(49, 59)],
    3: [(69, 92), (70, 92), (71, 92)],               # front end seen from the side
    7: [(47, 92)],                                   # (x44-46 already dark there)
}
REAR_BAND = {
    1: [(x, 104) for x in range(58, 67)],
    0: [(x, 101) for x in range(73, 83)],
    2: [(x, 101) for x in range(44, 53)],
}

# Side view (3), the three doors: x of the left leaf edge, rows of the glass.
DOORS_V3 = (17, 37, 61)
DOOR_ROWS = list(range(85, 89)) + list(range(90, 94))


def load_base():
    with open(BASE, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != BASE_SHA256:
        raise SystemExit(f"{BASE}: unexpected content (sha256 {digest})")
    a = np.array(Image.open(BASE).convert("RGB"))
    assert a.shape == (128, 1024, 3), a.shape
    return a


def put(a, view, pts, col):
    for x, y in pts:
        px = a[y, view * 128 + x]
        if tuple(px) == BG:
            raise SystemExit(f"view {view} ({x},{y}) is background")
        a[y, view * 128 + x] = col


def recolor(a, src, dst, views=range(8), ymax=128):
    n = 0
    for v in views:
        tile = a[:ymax, v * 128:(v + 1) * 128]
        m = np.all(tile == src, axis=2)
        tile[m] = dst
        n += int(m.sum())
    return n


def paint(cand):
    a = load_base()
    # LED displays
    for v in range(8):
        tile = a[:, v * 128:(v + 1) * 128]
        m = np.all(tile == ROLLSIGN, axis=2)
        txt = LED_TEXT_PX.get(v, [])
        for x, y in txt:
            if not m[y, x]:
                raise SystemExit(f"view {v} ({x},{y}) is not a display pixel")
        tile[m] = LED_PANEL
        for x, y in txt:
            tile[y, x] = LED_TEXT
    # doors: yellow leaves, the glass stays the lit-window special 4D4D4D
    assert recolor(a, DOOR_GREY, YELLOW, views=(2, 3, 4)) == 84
    assert recolor(a, DOOR_GREY, YELLOW) == 0
    assert recolor(a, DOOR_SILL, YELLOW, views=(3,)) == 12
    # side view: the base's zigzag folding pattern turns into crosses once the
    # grey leaves are yellow, so draw the glass as two straight slits per door
    glass = (77, 77, 77)
    for x0 in DOORS_V3:
        for y in DOOR_ROWS:
            for i, col in enumerate((YELLOW, glass, YELLOW, glass, YELLOW)):
                a[y, 3 * 128 + x0 + i] = col
    if cand in ("b", "c"):
        for v, pts in FRONT_BAND.items():
            put(a, v, pts, BAND)
    if cand == "c":
        for v, pts in REAR_BAND.items():
            put(a, v, pts, BAND)
        for src, dst in PANTO.items():
            recolor(a, src, dst, ymax=82)
    check(a)
    return a


def check(a):
    base = load_base()
    new = {tuple(c) for c in a.reshape(-1, 3)} - {tuple(c) for c in base.reshape(-1, 3)}
    bad = [c for c in new if (c[0] << 16 | c[1] << 8 | c[2]) in RGBTAB - {0x01DD01}]
    if bad:
        raise SystemExit(f"new colours hit rgbtab specials: {bad}")


def on_grass(a, z):
    a = a.copy()
    a[np.all(a == BG, axis=2)] = GRASS
    im = Image.fromarray(a[48:112])          # every view lies in rows 55-107
    return im.resize((im.width * z, im.height * z), Image.NEAREST)


def preview(sheets, path):
    """one block per sheet: label, 8 views at 1x, 8 views at 3x"""
    blocks = []
    for label, a in sheets:
        one, three = on_grass(a, 1), on_grass(a, 3)
        h = 14 + one.height + 4 + three.height + 10
        blk = Image.new("RGB", (three.width, h), (40, 40, 40))
        ImageDraw.Draw(blk).text((4, 1), label, fill=(255, 255, 255))
        blk.paste(one, (0, 14))
        blk.paste(three, (0, 14 + one.height + 4))
        blocks.append(blk)
    out = Image.new("RGB", (blocks[0].width, sum(b.height for b in blocks)), (40, 40, 40))
    y = 0
    for b in blocks:
        out.paste(b, (0, y))
        y += b.height
    out.save(path)


def main():
    args = sys.argv[1:]
    out = pv = None
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        del args[i:i + 2]
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or args[0] not in ("a", "b", "c"):
        raise SystemExit(__doc__)
    cand = args[0]
    a = paint(cand)
    Image.fromarray(a).save(out or SPRITE)
    print("wrote", out or SPRITE)
    if pv:
        os.makedirs(pv, exist_ok=True)
        sheets = [("current (Lubak91 Most T3)", load_base())]
        sheets += [(f"candidate {c}", paint(c)) for c in "abc"]
        preview(sheets, os.path.join(pv, "t3m3_candidates.png"))
        for c in "abc":
            Image.fromarray(paint(c)).save(os.path.join(pv, f"t3m3_{c}.png"))
        print("previews in", pv)


if __name__ == "__main__":
    main()
