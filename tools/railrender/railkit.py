"""Rail vehicle kit on top of render.py (orthographic pak128 box raycaster).

Model coordinates (per consist): u = carunits BEHIND the consist front (0 = nose
of the lead vehicle), v = lateral carunits (+v = right-hand side in the travel
direction), z = height in "model px" above the rail head (w-view pixels).

pak128.cs rail art is not isometrically consistent: heights are drawn ~18 %
taller in the ne/sw views than in the other views (measured on CD Bmz241, OBB railjet Bmpz, OBB 1216, DB 642).
KZ reproduces that so our vehicles match natives side by side.

Lighting (measured on the same natives): the south-facing side (w/e views) is
the full colour, the south-east-facing side (ne/sw views) ~0.87, the
east-facing side (n/s views) ~0.72; roofs keep their own colour.

Front anchor (screen position of u=0, v=0, z=0 of the vehicle being drawn),
calibrated to the native Bmz241 / 1216 / 642 front edges: Simutrans anchors
every vehicle at its front, so the anchor does not depend on the length.
"""
import math
import numpy as np
from render import Box, render as _render, DIRS, back_vec, frame, T, local_to_screen

KZ = {"w": 1.0, "e": 1.0, "n": 1.0, "s": 1.0, "nw": 1.0, "se": 1.0, "ne": 1.18, "sw": 1.18}
# Native coach fit (colfit.py vs CD_Bmz241_t, all 8 views within 1 px):
# half width W = 0.92 cu, side wall z 0..10 (incl. underframe), roof cap +0.8
# inset 0.2, body length ~ L - 0.2 cu.
W_STD = 0.92
H_SIDE = 10.0
H_CAP = 0.8


# ------------------------------------------------------------------ colours
def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
GLASS = (0x4D, 0x4D, 0x4D)       # special 28: lit at night (loaded image)
GLASS_HI = (0x57, 0x65, 0x6F)    # special 16: lit, lighter
HEAD = (0xFF, 0xFF, 0x53)        # special: headlight, always on
TAIL = (0xFF, 0x21, 0x1D)        # special: tail light, always on
KEEP = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


def safe(c):
    """Nudge a colour off the special table (one blue step)."""
    c = tuple(int(max(0, min(255, round(x)))) for x in c)
    h = (c[0] << 16) | (c[1] << 8) | c[2]
    if h in SPECIAL and h not in KEEP:
        c = (c[0], c[1], c[2] + 1 if c[2] < 255 else c[2] - 1)
    return c


def face_factor(d, face):
    """Brightness factor of a face in view d (1 = south-facing side)."""
    if face == "+z":
        return None
    f, r = frame(d)
    ax, sg = face[1], (1 if face[0] == "+" else -1)
    if ax == "u":
        n = -f * sg
    elif ax == "v":
        n = r * sg
    else:
        return 0.55          # underside (rarely visible)
    nx, ny = n[0], n[1]
    # south 1.0, south-east ~0.86, east 0.72, south-west ~1.0 (natives)
    return max(0.5, 1.0 - 0.28 * max(0.0, nx) ** 2 - 0.10 * max(0.0, -ny))


class Paint:
    """A paint colour: sides use face_factor, tops use `top` (default = base)."""
    def __init__(self, base, top=None, name=""):
        self.base = rgb(base) if isinstance(base, int) else tuple(base)
        self.topc = (rgb(top) if isinstance(top, int) else tuple(top)) if top is not None else self.base
        self.name = name

    def at(self, d, face):
        k = face_factor(d, face)
        if k is None:
            return safe(self.topc)
        return safe(tuple(c * k for c in self.base))


class Lit:
    """A colour that must not be shaded (glass specials, lamps)."""
    def __init__(self, c):
        self.c = c

    def at(self, d, face):
        return self.c


def P(x):
    """Resolve a paint spec (Paint / Lit / tuple) for a face."""
    return x


# ------------------------------------------------------------------ geometry
class Part:
    """An axis-aligned box of the model. mat(face, u, v, z, d) -> Paint/Lit/RGB."""
    def __init__(self, u0, u1, v0, v1, z0, z1, mat, owner):
        self.b = (u0, u1, v0, v1, z0, z1)
        self.mat = mat
        self.owner = owner


def _resolve(x, d, face):
    if isinstance(x, (Paint, Lit)):
        return x.at(d, face)
    if isinstance(x, int):
        return safe(rgb(x))
    return x


def render_view(parts, lines, d, anchor, size=128):
    k = KZ[d]
    boxes = []
    for p in parts:
        u0, u1, v0, v1, z0, z1 = p.b
        m = p.mat
        boxes.append(Box(u0, u1, v0, v1, z0 * k, z1 * k,
                         (lambda m: lambda f, u, v, z, dd: _resolve(m(f, u, v, z / k, dd), dd, f))(m),
                         p.owner))
    ls = []
    for ln in lines:
        (a, b, col, own) = ln[:4]
        thick = ln[4] if len(ln) > 4 else False
        col = safe(rgb(col)) if isinstance(col, int) else col
        ls.append(((a[0], a[1], a[2] * k), (b[0], b[1], b[2] * k), col, own, thick))
    return _render(boxes, d, anchor, size=size, lines=ls)


# Front anchors (u=0,v=0,z=0 of the drawn vehicle) in SOURCE-sheet pixels,
# i.e. before makeobj's rail image offset (0,4) that the build applies
# (image_offset default). Calibrated on the pak128.CS source PNGs
# CD_Bmz241_t / railjet_Bmpz-1 / obb_1216 (front edge + bottom edge).
ANCHOR = {"w": (43.0, 79.0), "nw": (63.5, 69.0), "n": (85.0, 79.0), "ne": (83.5, 91.0),
          "e": (75.0, 95.0), "se": (63.5, 99.0), "s": (53.0, 95.0), "sw": (37.5, 91.0)}


def vehicle_tile(parts, lines, d, u_front, keep, anchor=None):
    """Render the whole consist with the scene shifted so that the vehicle whose
    front is at consist-u `u_front` sits on the front anchor; keep only pixels
    owned by `keep` (set of owner names)."""
    bx, by = back_vec(d)
    ax, ay = (anchor or ANCHOR)[d]
    a = (ax - u_front * bx, ay - u_front * by)
    img, owner = render_view(parts, lines, d, a)
    mask = np.isin(owner, list(keep))
    out = img.copy()
    out[~mask] = T
    return out


def bbox(t):
    m = ~np.all(t == np.array(T), axis=2)
    ys, xs = np.where(m)
    if not len(xs):
        return None
    return xs.min(), xs.max(), ys.min(), ys.max()


def calibrate(ref_png, L, W=0.97, H=12.5):
    """Front-bottom-centre anchors that align a plain L x 2W x H box with the
    native sprite's bbox (front edge + bottom edge per view)."""
    from PIL import Image
    im = np.array(Image.open(ref_png).convert("RGB"))
    res = {}
    for c, d in enumerate(DIRS):
        rb = bbox(im[:, c * 128:(c + 1) * 128])
        parts = [Part(0, L, -W, W, 0, H, lambda *a: (200, 200, 200), "b")]
        img, _ = render_view(parts, [], d, (128.0, 128.0), size=256)
        bb = bbox(img)
        # x: centre match; y: bottom match
        ax = 128 + (rb[0] + rb[1]) / 2 - (bb[0] + bb[1]) / 2
        ay = 128 + rb[3] - bb[3]
        res[d] = (ax, ay, (bb[1] - bb[0]) - (rb[1] - rb[0]), (bb[3] - bb[2]) - (rb[3] - rb[2]))
    return res


def save_rows(rows, path):
    from PIL import Image
    out = np.zeros((128 * len(rows), 1024, 3), dtype=np.uint8)
    out[:, :] = T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            out[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    flat = out.reshape(-1, 3).astype(np.int64)
    vals = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]
    bad = {v for v in np.unique(vals).tolist() if v in SPECIAL and v not in KEEP}
    if bad:
        print("WARNING unintended specials", [hex(b) for b in bad])
    Image.fromarray(out).save(path)
    return out


# ------------------------------------------------------------------ helpers
def slices(u_a, u_b, n, fn, owner):
    """n thin parts between u_a and u_b; fn(t, u0, u1) -> list of Part-args
    (v0, v1, z0, z1, mat) for the slice at fraction t (0 at u_a)."""
    out = []
    for i in range(n):
        u0 = u_a + (u_b - u_a) * i / n
        u1 = u_a + (u_b - u_a) * (i + 1) / n
        t = (i + 0.5) / n
        for (v0, v1, z0, z1, mat) in fn(t, min(u0, u1), max(u0, u1)):
            out.append(Part(min(u0, u1), max(u0, u1), v0, v1, z0, z1, mat, owner))
    return out


def bogie(u, owner, W=W_STD, half=1.1, z1=1.6, col=None, frame=None):
    """Bogie centred at u: dark frame box + wheels (drawn slightly inset)."""
    col = col or Paint(0x2A2A2C)
    frame = frame or Paint(0x3A3A3C)
    return [Part(u - half, u + half, -W + 0.12, W - 0.12, 0.0, z1,
                 lambda f, uu, v, z, d: frame if (f in ("+v", "-v") and z > z1 - 0.8) else col, owner)]


def pantograph(u_base, z_roof, owner, fold=+1, reach=1.0, height=7.0, col=(0x5A, 0x5C, 0x60),
               head=(0x2A, 0x2A, 0x2C), half_head=0.7, thick=True):
    """Single-arm pantograph lines. fold=+1: knee trails (towards larger u)."""
    zr = z_roof
    ub, uk, uh = u_base, u_base + fold * reach, u_base + fold * 0.15
    zk, zh = zr + height * 0.48, zr + height
    return [
        ((ub, 0.0, zr), (uk, 0.0, zk), col, owner, thick),
        ((uk, 0.0, zk), (uh, 0.0, zh), col, owner, thick),
        ((uh, -half_head, zh), (uh, half_head, zh), head, owner, True),
    ]


def roof_box(u0, u1, owner, zr, h=1.0, hw=0.55, paint=None):
    paint = paint or Paint(0x6A6E72, top=0x7A7E82)
    return Part(u0, u1, -hw, hw, zr, zr + h, lambda *a: paint, owner)


def gangway(u, owner, half=0.12, W=W_STD, z0=1.5, z1=9.0, paint=None):
    paint = paint or Paint(0x26282A)
    return Part(u - half, u + half, -W + 0.25, W - 0.25, z0, z1, lambda *a: paint, owner)


def preview(rows, out, z=4, labels=None, bg=(96, 104, 96)):
    """Zoomed sheet: every row's 8 tiles cropped to the union bbox per column."""
    from PIL import Image, ImageDraw
    crops = []
    for c in range(8):
        bbs = [bbox(r[c]) for r in rows if bbox(r[c])]
        x0 = min(b[0] for b in bbs) - 2; x1 = max(b[1] for b in bbs) + 3
        y0 = min(b[2] for b in bbs) - 2; y1 = max(b[3] for b in bbs) + 3
        crops.append((x0, x1, y0, y1))
    colw = [(x1 - x0) * z + 6 for (x0, x1, y0, y1) in crops]
    rowh = [max((y1 - y0) for (x0, x1, y0, y1) in crops) * z + 6 for _ in rows]
    img = Image.new("RGB", (sum(colw) + 90, sum(rowh) + 14), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    y = 14
    for ri, r in enumerate(rows):
        x = 90
        if labels:
            dr.text((2, y + 2), labels[ri], fill=(0, 0, 0))
        for c in range(8):
            x0, x1, y0, y1 = crops[c]
            t = r[c][y0:y1, x0:x1].copy()
            m = np.all(t == np.array(T), axis=2)
            t[m] = bg
            img.paste(Image.fromarray(t).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST), (x, y))
            if ri == 0:
                dr.text((x + 2, 1), DIRS[c], fill=(0, 0, 0))
            x += colw[c]
        y += rowh[ri]
    img.save(out)
    return out
