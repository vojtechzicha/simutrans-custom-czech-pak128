"""Paint a livery onto a Body (body.py) and write / preview sheets.

spec: {zone: colour | callable(ctx) -> colour | None}. Zones not in spec keep
the base pixel. A colour is multiplied by the pixel's shade factor, so the
original lighting and edge highlights survive. A callable may return
(colour, "flat") to skip shading. ctx: col, x, y, k, u, face, zone, fac.
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import Body, T, hexarr, lum

LIT_GLASS = (0x4D, 0x4D, 0x4D)
LIT_GLASS_HI = (0x57, 0x65, 0x6F)
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
KEEP_SPECIAL = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


def unspecial(a, keep=KEEP_SPECIAL):
    flat = a.reshape(-1, 3)
    vals = hexarr(flat)
    for v in set(np.unique(vals).tolist()) & (SPECIAL - keep):
        idx = vals == v
        b = flat[idx, 2].astype(int)
        flat[idx, 2] = np.where(b < 255, b + 1, b - 1)
    return a


_shade = {}


def shade(body):
    if body.name not in _shade:
        _shade[body.name] = body.shade()
    return _shade[body.name]


def paint(body, spec, glass="lit"):
    """-> uint8 [128,1024,3]."""
    fac = shade(body)
    out = body.base.astype(float).copy()
    zn_of = body.zones
    ys, xs = np.where(body.lab != body.Z["T"])
    for y, x in zip(ys, xs):
        zn = zn_of[body.lab[y, x]]
        s = spec.get(zn)
        if s is None:
            continue
        ctx = dict(col=x // 128, x=x % 128, y=y, k=body.K[y, x], u=body.U[y, x], face=body.face[y, x],
                   zone=zn, fac=fac[y, x])
        c = s(ctx) if callable(s) else s
        if c is None:
            continue
        if isinstance(c, tuple) and len(c) == 2 and c[1] == "flat":
            out[y, x] = c[0]
            continue
        out[y, x] = np.clip(np.array(c, float) * fac[y, x], 0, 255)
    if glass == "lit":
        g = body.lab == body.Z["GLASS"]
        v = hexarr(body.refs)
        hi = (v == 0x57656F).any(axis=0)
        out[g & hi] = LIT_GLASS_HI
        out[g & ~hi] = LIT_GLASS
    out = np.rint(out).astype(np.uint8)
    return unspecial(out)


def recolor_lum(body, a, zone, colour, ref_lum=None):
    """Recolour a zone keeping the base pixel's own luminance variation (for
    roofs with equipment): new = colour * lum(px) / median lum(zone)."""
    m = body.lab == body.Z[zone]
    L = lum(body.base.astype(float))
    med = ref_lum if ref_lum is not None else np.median(L[m])
    f = np.clip(L / max(med, 1.0), 0.45, 1.6)
    a = a.astype(float)
    a[m] = np.clip(np.array(colour, float)[None, :] * f[m][:, None], 0, 255)
    return unspecial(np.rint(a).astype(np.uint8))


def save_sheet(rows, path):
    """Write sprite rows (uint8 [128, 1024, 3] each) as one sheet and warn about
    special colours other than lit glass and lamps."""
    out = np.concatenate(rows, axis=0)
    Image.fromarray(out).save(path)
    v = hexarr(out)
    bad = set(np.unique(v).tolist()) & (SPECIAL - KEEP_SPECIAL)
    if bad:
        print("WARNING special colours", [hex(b) for b in bad], path)
    return path


def add_marks(body, a, side=(), end=(), side_zones=None, end_zones=None):
    """Small logos / lettering, a pixel or two each, on every view.
    side: (u, width_u, k, colour) on the side faces, u = 0..1 along the car
          from its rear (0) to its front (1) on both sides;
    end:  (v, width_v, k, colour) on the end faces, v = 0..1 across the end.
    Only pixels of the listed body zones are touched (default: all S_* / E_*
    zones except doors). Colours are shaded like the livery."""
    fac = shade(body)
    a = a.astype(float)
    Z = body.zones
    import warp
    # u from the rear: the ne side view has the front on the right, sw on the left
    ur = body.U.copy()
    for c in range(8):
        src = c if c in (3, 7) else warp.SIDE_SRC.get(c, c)
        if src == 7:
            sl = slice(c * 128, (c + 1) * 128)
            f = body.face[:, sl] == "S"
            ur[:, sl][f] = 1 - body.U[:, sl][f]
    for marks, face, zones in ((side, "S", side_zones), (end, "E", end_zones)):
        uu = ur if face == "S" else body.U
        for u, w, k, colour in marks:
            m = (body.face == face) & (body.K == k) & (np.abs(uu - u) <= w / 2)
            ys, xs = np.where(m)
            for y, x in zip(ys, xs):
                zn = Z[body.lab[y, x]]
                allowed = (zn.startswith(face + "_") and zn != "S_DOOR") if zones is None else zn in zones
                if allowed:
                    a[y, x] = np.clip(np.array(colour, float) * fac[y, x], 0, 255)
    return unspecial(np.rint(a).astype(np.uint8))


DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]


def preview(sheets, out, z=4, bg=(110, 120, 110)):
    """Zoomed preview of sheets (paths): every sprite row becomes one line of
    its 8 tiles, each column cropped to the union bbox of that column."""
    from PIL import ImageDraw
    lines = []
    for p in sheets:
        a = np.array(Image.open(p).convert("RGB"))
        for r in range(a.shape[0] // 128):
            lines.append((f"{os.path.basename(p)} r{r}",
                          [a[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] for c in range(8)]))
    crops = []
    for c in range(8):
        bb = []
        for _, tiles in lines:
            ys, xs = np.where(~np.all(tiles[c] == T, axis=2))
            if len(xs):
                bb.append((xs.min(), ys.min(), xs.max(), ys.max()))
        if not bb:
            crops.append((0, 0, 8, 8))
            continue
        crops.append((min(b[0] for b in bb) - 2, min(b[1] for b in bb) - 2,
                      max(b[2] for b in bb) + 3, max(b[3] for b in bb) + 3))
    cw = [(x1 - x0) * z for x0, y0, x1, y1 in crops]
    ch = max((y1 - y0) * z for x0, y0, x1, y1 in crops)
    img = Image.new("RGB", (sum(cw) + 8 * 4 + 4, len(lines) * (ch + 16) + 4), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    for i, (lab, tiles) in enumerate(lines):
        y = i * (ch + 16)
        dr.text((2, y), lab, fill=(0, 0, 0))
        x = 2
        for c, (x0, y0, x1, y1) in enumerate(crops):
            t = tiles[c][y0:y1, x0:x1].copy()
            t[np.all(t == T, axis=2)] = bg
            img.paste(Image.fromarray(t).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST), (x, y + 13))
            x += cw[c] + 4
    img.save(out)
    return out
