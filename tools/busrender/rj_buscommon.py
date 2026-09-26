"""Shared helpers for repainting pak128 vehicle sprite rows (8 tiles of 128x128,
project column order w, nw, n, ne, e, se, s, sw)."""
import os
import numpy as np
from PIL import Image

T = (231, 255, 255)
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
WORK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(WORK, "base")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # repo root

# Simutrans special colours (image_t::rgbtab). Anything we paint must avoid
# these unless the special behaviour is intended.
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
LIT_WINDOW = (0x4D, 0x4D, 0x4D)     # special: dark grey glass by day, lit yellow at night
HEADLIGHT = (0xFF, 0xFF, 0x53)      # special: yellow light
TAILLIGHT = (0xFF, 0x21, 0x1D)      # special: red light

# DPMP palette
RED_HI = (0xD5, 0x0B, 0x15)
RED = (0xC0, 0x0A, 0x13)
RED_LO = (0xAC, 0x09, 0x11)
AMBER = (0xF0, 0xA0, 0x18)          # destination displays: amber LED (non-special)


def hexv(c):
    return (int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2])


def load_row(path, row=0):
    im = np.array(Image.open(path).convert("RGB"))
    return [im[row * 128:(row + 1) * 128, c * 128:(c + 1) * 128].copy() for c in range(8)]


def save_rows(rows, path):
    out = np.zeros((128 * len(rows), 1024, 3), dtype=np.uint8)
    out[:, :] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    Image.fromarray(out).save(path)
    check_specials(out, path)


def check_specials(arr, label=""):
    flat = arr.reshape(-1, 3)
    vals = (flat[:, 0].astype(np.int64) << 16) | (flat[:, 1].astype(np.int64) << 8) | flat[:, 2]
    used = {v for v in np.unique(vals).tolist() if v in SPECIAL}
    allowed = {hexv(LIT_WINDOW), hexv(HEADLIGHT), hexv(TAILLIGHT), 0x57656F}
    bad = used - allowed
    if bad:
        print(f"WARNING {label}: unintended special colours {[hex(b) for b in bad]}")


def classify(c):
    r, g, b = int(c[0]), int(c[1]), int(c[2])
    if (r, g, b) == T:
        return "."
    h = (r << 16) | (g << 8) | b
    sp = {0xFF211D: "r", 0xFFFF53: "y", 0x6B6B6B: "G", 0x57656F: "g", 0x4D4D4D: "g", 0x7F9BF1: "b", 0xE3E3FF: "l"}
    if h in sp:
        return sp[h]
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 18:
        if mx >= 245: return "W"
        if mx >= 215: return "w"
        if mx >= 160: return "s"
        if mx >= 100: return "m"
        if mx >= 60: return "d"
        return "K"
    if r > 150 and g < 90 and b < 90: return "R"
    if r > 200 and g > 100 and b < 100: return "o"
    if r > 180 and g > 180 and b < 120: return "Y"
    if b > r and b > g: return "B"
    if g > r and g > b: return "E"
    return "?"


def cmap(tile):
    return np.array([[classify(tile[y, x]) for x in range(128)] for y in range(128)])


def recolor(tile, mask, color):
    tile[mask] = color


def put(tile, pts, color):
    for x, y in pts:
        tile[y, x] = color


def dump(tile, pad=1):
    m = cmap(tile)
    ys, xs = np.where(m != ".")
    x0, x1, y0, y1 = xs.min() - pad, xs.max() + pad, ys.min() - pad, ys.max() + pad
    lines = ["     " + "".join(str((x // 10) % 10) for x in range(x0, x1 + 1)),
             "     " + "".join(str(x % 10) for x in range(x0, x1 + 1))]
    for y in range(y0, y1 + 1):
        lines.append(f"{y:4d} " + "".join(m[y, x] for x in range(x0, x1 + 1)))
    return "\n".join(lines)


def preview(rows, out, z=5, bg=(96, 104, 96), labels=None):
    """Zoomed 8-direction preview of one or more rows (each tile cropped to the
    union bbox of its column across rows)."""
    from PIL import ImageDraw
    crops = []
    for c in range(8):
        boxes = []
        for tiles in rows:
            m = ~np.all(tiles[c] == np.array(T), axis=2)
            ys, xs = np.where(m)
            if len(xs): boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
        x0 = min(b[0] for b in boxes) - 2; y0 = min(b[1] for b in boxes) - 2
        x1 = max(b[2] for b in boxes) + 3; y1 = max(b[3] for b in boxes) + 3
        crops.append((x0, y0, x1, y1))
    cells = []
    for tiles in rows:
        line = []
        for c, (x0, y0, x1, y1) in enumerate(crops):
            t = tiles[c][y0:y1, x0:x1].copy()
            m = np.all(t == np.array(T), axis=2)
            t[m] = bg
            im = Image.fromarray(t).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
            line.append(im)
        cells.append(line)
    W = sum(max(cells[r][c].width for r in range(len(rows))) + 6 for c in range(8))
    H = sum(max(im.height for im in line) + 6 for line in cells) + 14
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    x = 0
    for c in range(8):
        d.text((x + 2, 1), DIRS[c], fill=(0, 0, 0))
        y = 14
        for r in range(len(rows)):
            canvas.paste(cells[r][c], (x, y)); y += cells[r][c].height + 6
        x += max(cells[r][c].width for r in range(len(rows))) + 6
    canvas.save(out)
    return out


def unspecial(t, keep=None):
    """Nudge any special-colour pixel not in `keep` (hex set) by one blue step so
    makeobj stores it as a plain colour (visually identical)."""
    keep = keep if keep is not None else {hexv(LIT_WINDOW), hexv(HEADLIGHT), hexv(TAILLIGHT)}
    flat = t.reshape(-1, 3)
    vals = (flat[:, 0].astype(np.int64) << 16) | (flat[:, 1].astype(np.int64) << 8) | flat[:, 2]
    for v in set(np.unique(vals).tolist()) & SPECIAL - keep:
        idx = vals == v
        b = flat[idx, 2].astype(int)
        flat[idx, 2] = np.where(b < 255, b + 1, b - 1)
    return t
