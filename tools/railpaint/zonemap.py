"""Zone-map painter for the Sim pak128.CS 810 railcar / Btax 780 (class 010)
trailer body, used by cd_sukafon.py (ČD 809, 810 + 010, 811 + 012).

This is the older, body-specific sibling of body.py / paint.py. All upstream
liveries of one vehicle (src/sukafon/, row 0 of the Sim rail-psg mail/810
sheets) share silhouette and shading, so a pixel's colours across those
reference liveries identify what it is:

- zones are assigned by hand rules on the pure side (ne, col 3 / sw, col 7) and
  end views (nw, col 1 / se, col 5), where the geometry is trivial;
- every body pixel of the diagonal views (w, n, e, s) gets the zone of its
  nearest prototype pixel (colour signature over all reference liveries);
- roof = the fixed pixels above the body in each column.

paint(veh, spec) -> one 128x1024 RGB sprite row. spec maps zone name -> colour,
callable(ctx) -> colour, (colour, "flat") or None (keep the base pixel). A colour
is multiplied by the pixel's shade factor (the lighting common to all reference
liveries), so direction lighting and edge highlights of the original art
survive. ctx = dict(col, x, y, k = row offset in the zone band, u = position
along the body 0..1, zone, lab, fac). Window glass always ends up as the lit
specials 0x4D4D4D / 0x57656F; other special colours are nudged off (unspecial).

Zones: T, FIX, GLASS, HEAD, TAIL, ROOF, ROOF_EDGE (lowest roof row along the
side, only when the spec names it), side band S_TOP, S_PIL, S_DOOR, S_BELT,
S_LOW1, S_LOW2, S_SKIRT, S_SOLE, end band E_TOP, E_PIL, E_BELOW, E_LAMP, E_LOW1,
E_LOW2, E_BEAM.

Extras: add_marks (lettering / logos, a pixel or two), add_exhaust (810 roof
stack with soot), add_roof_box (flat roof box such as the 811's A/C unit).
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src", "sukafon")
T = np.array((231, 255, 255))

ZONES = ["T", "FIX", "GLASS", "HEAD", "TAIL", "ROOF",
         "S_TOP", "S_PIL", "S_DOOR", "S_BELT", "S_LOW1", "S_LOW2", "S_SKIRT", "S_SOLE",
         "E_TOP", "E_PIL", "E_BELOW", "E_LAMP", "E_LOW1", "E_LOW2", "E_BEAM"]
Z = {n: i for i, n in enumerate(ZONES)}

# reference liveries of the Sim sheets (rail-psg mail/810), row 0 each; the first
# is the base the paint starts from
REFS = {
    "810": ["810_CSD.png", "810_balkan.png", "810_ZD.png", "810.png", "810_blonski.png", "810_viamont.png", "810_modry.png"],
    "010": ["Btax_CSD_bez_baglu.png", "010_balkan_bez_baglu.png", "Btax_bez_baglu.png", "Btax_modry_bez_baglu.png",
            "010_ZD_bez_baglu.png", "Btax_viamont_bez_baglu.png"],
}

LIT_GLASS = (0x4D, 0x4D, 0x4D)
LIT_GLASS_HI = (0x57, 0x65, 0x6F)
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
KEEP_SPECIAL = {0x4D4D4D, 0x57656F, 0xFFFF53, 0xFF211D}


# ------------------------------------------------------------------ zone map

def load(veh):
    """-> int array [n_refs, 128, 1024, 3]: row 0 (lit) of each reference sheet."""
    return np.stack([np.array(Image.open(os.path.join(SRC, f)).convert("RGB"))[:128, :1024]
                     for f in REFS[veh]]).astype(int)


def lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def base_labels(refs):
    """Fixed classes + 'var' mask (pixels that differ between liveries) for one row."""
    r0 = refs[0]
    lab = np.full((128, 1024), Z["FIX"], int)
    lab[np.all(r0 == T, axis=2)] = Z["T"]
    v = (r0[..., 0] << 16) | (r0[..., 1] << 8) | r0[..., 2]
    var = np.zeros((128, 1024), bool)
    for r in refs[1:]:
        var |= np.any(r != r0, axis=2)
    glass = np.isin(v, [0x4D4D4D, 0x57656F])
    # a window that some livery draws lit is glass in all of them
    for r in refs[1:]:
        vv = (r[..., 0] << 16) | (r[..., 1] << 8) | r[..., 2]
        glass |= np.isin(vv, [0x4D4D4D, 0x57656F])
    lab[glass] = Z["GLASS"]
    lab[v == 0xFFFF53] = Z["HEAD"]
    lab[v == 0xFF211D] = Z["TAIL"]
    return lab, var & ~glass & (v != 0xFFFF53) & (v != 0xFF211D)


def side_rules(lab, var, refs, col, top_row):
    """Zone the var pixels of a pure side view tile by row offset from the top strip."""
    x0 = col * 128
    bal = refs[1]
    for y in range(128):
        for x in range(x0, x0 + 128):
            if not var[y, x]:
                continue
            k = y - top_row
            if k == 0:
                z = "S_TOP"
            elif 1 <= k <= 3:
                z = "S_PIL"
            elif k == 4:
                z = "S_BELT"
            elif k == 5:
                z = "S_LOW1"
            elif k == 6:
                z = "S_LOW2"
            elif k == 7:
                z = "S_SKIRT"
            else:
                z = "S_SOLE"
            lab[y, x] = Z[z]
    # doors: columns where the balkan livery is dark navy through the lower rows
    for x in range(x0, x0 + 128):
        dark = [lum(bal[y, x]) < 75 and bal[y, x][2] > bal[y, x][0] + 15 for y in range(top_row + 5, top_row + 8)]
        if sum(dark) >= 2:
            for y in range(top_row + 1, top_row + 8):
                if var[y, x]:
                    lab[y, x] = Z["S_DOOR"]


def end_rules(lab, var, refs, col, top_row):
    x0 = col * 128
    for y in range(128):
        for x in range(x0, x0 + 128):
            if not var[y, x]:
                continue
            k = y - top_row
            if k == 0:
                z = "E_TOP"
            elif 1 <= k <= 4:
                z = "E_PIL"
            elif k == 5:
                z = "E_BELOW"
            elif k == 6:
                z = "E_LAMP"
            elif k == 7:
                z = "E_LOW1"
            elif k == 8:
                z = "E_LOW2"
            else:
                z = "E_BEAM"
            lab[y, x] = Z[z]


def features(refs, y, x, extra):
    f = [refs[i, y, x] / 255.0 for i in range(refs.shape[0])]
    return np.concatenate(f + [np.array(extra)])


def build(veh):
    """-> (zone label array [128, 1024], reference rows)."""
    refs = load(veh)
    lab, var = base_labels(refs)
    # geometry of the pure views (identical for 810 and Btax)
    side_rules(lab, var, refs, 3, 84)
    side_rules(lab, var, refs, 7, 84)
    end_rules(lab, var, refs, 1, 78)
    end_rules(lab, var, refs, 5, 89)
    # prototypes
    P, PZ = [], []
    for col in (1, 3, 5, 7):
        for y in range(128):
            for x in range(col * 128, col * 128 + 128):
                if var[y, x]:
                    P.append(features(refs, y, x, []))
                    PZ.append(lab[y, x])
    P = np.array(P)
    PZ = np.array(PZ)
    # diagonal views: nearest prototype
    for col in (0, 2, 4, 6):
        for y in range(128):
            for x in range(col * 128, col * 128 + 128):
                if var[y, x]:
                    f = features(refs, y, x, [])
                    d = ((P - f) ** 2).sum(axis=1)
                    lab[y, x] = PZ[int(np.argmin(d))]
    # roof: fixed pixels above the body in each column
    body = np.zeros(lab.shape, bool)
    for zn, zi in Z.items():
        if zn[:2] in ("S_", "E_") or zn in ("GLASS", "HEAD", "TAIL"):
            body |= lab == zi
    L = lum(refs[0])
    for x in range(lab.shape[1]):
        ys = np.where(body[:, x])[0]
        top = ys.min() if len(ys) else 128
        for y in range(top):
            if lab[y, x] == Z["FIX"] and L[y, x] > 70:
                lab[y, x] = Z["ROOF"]
    return lab, refs


PALETTE = {
    "T": (231, 255, 255), "FIX": (60, 60, 60), "ROOF": (130, 130, 130), "GLASS": (0, 0, 0), "HEAD": (255, 255, 0), "TAIL": (255, 0, 0),
    "S_TOP": (255, 150, 200), "S_PIL": (240, 80, 160), "S_DOOR": (140, 0, 200), "S_BELT": (0, 160, 255),
    "S_LOW1": (0, 220, 120), "S_LOW2": (120, 200, 0), "S_SKIRT": (255, 170, 0), "S_SOLE": (170, 90, 20),
    "E_TOP": (255, 255, 160), "E_PIL": (200, 200, 90), "E_BELOW": (0, 255, 255), "E_LAMP": (255, 120, 120),
    "E_LOW1": (120, 255, 200), "E_LOW2": (80, 150, 150), "E_BEAM": (150, 120, 255),
}


def falsecolor(lab):
    """Zone map as a false-colour image (for checking the rules)."""
    out = np.zeros(lab.shape + (3,), np.uint8)
    for n, i in Z.items():
        out[lab == i] = PALETTE[n]
    return out


# ------------------------------------------------------------------ painting

_cache = {}


def zones(veh):
    """-> (labels, reference rows, shade factors, row-offset map), built once per run."""
    if veh not in _cache:
        lab, refs = build(veh)
        _cache[veh] = (lab, refs, shade_factors(lab, refs), kmap(lab))
    return _cache[veh]


REF_VIEW = {"S": (3, 7), "E": (1, 5), "R": (3, 7)}
EDGE_TOL = 0.14


def shade_factors(lab, refs):
    """Per-pixel lighting factor: for each reference livery, luminance relative to
    the zone's median in the pure side/end views; median over liveries."""
    n = refs.shape[0]
    L = lum(refs)  # [n,128,1024]
    fac = np.ones((128, 1024))
    for zn, zi in Z.items():
        if zn[:2] not in ("S_", "E_") and zn != "ROOF":
            continue
        m = lab == zi
        if not m.any():
            continue
        cols = REF_VIEW[zn[0]]
        vm = np.zeros_like(m)
        for c in cols:
            vm[:, c * 128:(c + 1) * 128] = m[:, c * 128:(c + 1) * 128]
        if not vm.any():
            vm = m
        rel = []
        for i in range(n):
            med = np.median(L[i][vm])
            rel.append(L[i] / max(med, 1.0))
        rel = np.median(np.stack(rel), axis=0)
        if zn == "ROOF":           # keep the roof's own curvature shading
            fac[m] = rel[m]
            continue
        # face level per tile; keep a pixel's own factor only where it is a
        # clear edge highlight / shadow
        for c in range(8):
            mc = np.zeros_like(m); mc[:, c * 128:(c + 1) * 128] = m[:, c * 128:(c + 1) * 128]
            if not mc.any():
                continue
            face = np.median(rel[mc])
            px = rel[mc]
            fac[mc] = np.where(np.abs(px - face) > EDGE_TOL, px, face)
    return np.clip(fac, 0.55, 1.35)


SIDE_K = {"S_TOP": 0, "S_BELT": 4, "S_LOW1": 5, "S_LOW2": 6, "S_SKIRT": 7, "S_SOLE": 8}
END_K = {"E_TOP": 0, "E_BELOW": 5, "E_LAMP": 6, "E_LOW1": 7, "E_LOW2": 8, "E_BEAM": 9}


def kmap(lab):
    """Row offset k inside the side band (S_*) or end band (E_*) for every body
    pixel, from the anchor zones in the same column."""
    K = np.full(lab.shape, -1, int)
    for x in range(lab.shape[1]):
        col = lab[:, x]
        for table, pre in ((SIDE_K, "S_"), (END_K, "E_")):
            anchors = [(y, table[ZONES[col[y]]]) for y in range(128) if ZONES[col[y]] in table]
            if not anchors:
                continue
            ys = np.array([a[0] for a in anchors]); ks = np.array([a[1] for a in anchors])
            y0 = int(np.median(ys - ks))          # y where k == 0
            for y in range(128):
                zn = ZONES[col[y]]
                if zn.startswith(pre) or (zn == "GLASS"):
                    if zn == "GLASS" and K[y, x] >= 0:
                        continue
                    K[y, x] = y - y0
    return K


def roof_edge_mask(lab):
    """ROOF pixels directly above the side band's top row (S_TOP), i.e. the
    lowest roof row along the side wall."""
    m = np.zeros(lab.shape, bool)
    for x in range(lab.shape[1]):
        ys = np.where(lab[:, x] == Z["S_TOP"])[0]
        if len(ys):
            y = ys.min() - 1
            if y >= 0 and lab[y, x] == Z["ROOF"]:
                m[y, x] = True
    return m


def side_columns(lab, col):
    """x-range (tile coords) of the side face in one tile: columns holding S_LOW1."""
    t = lab[:, col * 128:(col + 1) * 128]
    xs = np.where((t == Z["S_LOW1"]).any(axis=0))[0]
    return (xs.min(), xs.max()) if len(xs) else None


def add_marks(a, veh, marks, end_marks=()):
    """Small lettering / logo marks.
    marks: (u, width_u, k, colour) on the side face; u = 0..1 along the side.
    end_marks: (dx, k, colour) on the pure end views (nw/se), dx from the centre column."""
    lab, refs, fac, K = zones(veh)
    for col in (0, 2, 3, 4, 6, 7):
        sc = side_columns(lab, col)
        if not sc:
            continue
        sx0, sx1 = sc
        for u, w, k, colour in marks:
            for xx in range(sx0, sx1 + 1):
                uu = (xx - sx0) / max(1, sx1 - sx0)
                if abs(uu - u) > w / 2:
                    continue
                x = col * 128 + xx
                for y in range(128):
                    if K[y, x] == k and ZONES[lab[y, x]] in ("S_BELT", "S_LOW1", "S_LOW2", "S_SKIRT", "S_TOP", "S_PIL"):
                        a[y, x] = np.clip(np.array(colour, float) * fac[y, x], 0, 255)
    for col in (1, 5):
        t = lab[:, col * 128:(col + 1) * 128]
        xs = np.where((t == Z["E_LAMP"]).any(axis=0))[0]
        if not len(xs):
            continue
        cx = (xs.min() + xs.max()) // 2
        for dx, k, colour in end_marks:
            x = col * 128 + cx + dx
            for y in range(128):
                if K[y, x] == k and ZONES[lab[y, x]].startswith("E_"):
                    a[y, x] = np.clip(np.array(colour, float) * fac[y, x], 0, 255)
    return unspecial(a)


def body_extent(lab, col):
    """x-range and orientation info of the body in one tile (for position-dependent patterns)."""
    t = lab[:, col * 128:(col + 1) * 128]
    ys, xs = np.where((t != Z["T"]))
    return xs.min(), xs.max(), ys.min(), ys.max()


def paint(veh, spec, base_index=0, fac_scale=1.0):
    lab, refs, fac, K = zones(veh)
    out = refs[base_index].copy().astype(float)
    if spec.get("ROOF_EDGE") is not None:
        lab = lab.copy()
        lab[roof_edge_mask(lab)] = -1
    for col in range(8):
        bx0, bx1, by0, by1 = body_extent(lab, col)
        for y in range(128):
            for xx in range(128):
                x = col * 128 + xx
                zi = lab[y, x]
                zn = "ROOF_EDGE" if zi == -1 else ZONES[zi]
                if zn not in spec or spec[zn] is None:
                    continue
                s = spec[zn]
                ctx = dict(col=col, x=xx, y=y, u=(xx - bx0) / max(1, bx1 - bx0), zone=zn, lab=lab, fac=fac[y, x], k=K[y, x])
                c = s(ctx) if callable(s) else s
                if c is None:
                    continue
                if isinstance(c, tuple) and len(c) == 2 and c[1] == "flat":
                    out[y, x] = c[0]
                    continue
                f = 1 + (fac[y, x] - 1) * fac_scale
                out[y, x] = np.clip(np.array(c, float) * f, 0, 255)
    # glass: every GLASS pixel lit (take the lit tone from whichever reference
    # livery draws that pixel lit, preferring its upper-row highlight tone)
    g = lab == Z["GLASS"]
    lit = np.zeros(lab.shape, int)
    for r in refs:
        v = (r[..., 0] << 16) | (r[..., 1] << 8) | r[..., 2]
        lit = np.where((lit == 0) & np.isin(v, [0x4D4D4D, 0x57656F]), v, lit)
    out[g & (lit == 0x57656F)] = LIT_GLASS_HI
    out[g & (lit != 0x57656F)] = LIT_GLASS
    out = np.rint(out).astype(np.uint8)
    return unspecial(out)


def unspecial(a):
    """Nudge special-colour pixels other than lit glass and lamps one blue step
    so makeobj stores them as plain colours (visually identical)."""
    flat = a.reshape(-1, 3)
    vals = (flat[:, 0].astype(np.int64) << 16) | (flat[:, 1].astype(np.int64) << 8) | flat[:, 2]
    for v in set(np.unique(vals).tolist()) & (SPECIAL - KEEP_SPECIAL):
        idx = vals == v
        b = flat[idx, 2].astype(int)
        flat[idx, 2] = np.where(b < 255, b + 1, b - 1)
    return a


def save(rows, path):
    """Write sprite rows (uint8 [128, 1024, 3] each) as one sheet."""
    out = np.concatenate(rows, axis=0)
    Image.fromarray(out).save(path)
    return path


# screen-space heading of each direction column (w, nw, n, ne, e, se, s, sw)
HEADING = [(-2, -1), (0, -1), (2, -1), (1, 0), (2, 1), (0, 1), (-2, 1), (-1, 0)]


def roof_point(lab, col, u, side=0.0):
    """Pixel (x, y) in tile coords on the roof at length fraction u (0 = rear end,
    1 = front end, by heading) and lateral offset side (-1..1 across the roof)."""
    t = lab[:, col * 128:(col + 1) * 128]
    ys, xs = np.where((t == Z["ROOF"]) | (t == -1))
    hx, hy = HEADING[col]
    n = (hx * hx + hy * hy) ** 0.5
    hx, hy = hx / n, hy / n
    p = xs * hx + ys * hy
    target = p.min() + u * (p.max() - p.min())
    sel = np.abs(p - target) <= 1.0
    if col in (1, 5):
        sel = np.abs(p - target) <= 0.5
    sx, sy = xs[sel], ys[sel]
    # across the roof: perpendicular to the heading
    q = sx * (-hy) + sy * hx
    qt = (q.min() + q.max()) / 2 + side * (q.max() - q.min()) / 2
    k = int(np.argmin(np.abs(q - qt)))
    return int(sx[k]), int(sy[k])


def add_exhaust(a, veh, u=0.9, pipe=(34, 34, 36), soot=0.72):
    """810 exhaust stack on the roof centreline near one end, with a light soot
    stain on the roof just behind it."""
    lab, refs, fac, K = zones(veh)
    for col in range(8):
        x, y = roof_point(lab, col, u)
        X = col * 128 + x
        hx, hy = HEADING[col]
        # soot trails towards the rear (opposite to heading), one pixel
        for dx, dy in ((-np.sign(hx), -np.sign(hy) if hx == 0 else 0), (1, 0), (-1, 0)):
            xx, yy = X + int(dx), y + int(dy)
            if lab[yy, xx] == Z["ROOF"]:
                a[yy, xx] = (a[yy, xx] * soot).astype(np.uint8)
        a[y, X] = pipe
        a[y - 1, X] = pipe
    return unspecial(a)


def roof_uv(lab, col):
    """(xs, ys, u, v) of the roof pixels of one tile: u along the body (0 rear,
    1 front, by heading), v across the roof (-1..1)."""
    t = lab[:, col * 128:(col + 1) * 128]
    ys, xs = np.where((t == Z["ROOF"]) | (t == -1))
    hx, hy = HEADING[col]
    n = (hx * hx + hy * hy) ** 0.5
    hx, hy = hx / n, hy / n
    p = xs * hx + ys * hy
    q = xs * (-hy) + ys * hx
    u = (p - p.min()) / max(1e-6, p.max() - p.min())
    # across: normalise within each slice along the body
    v = np.zeros_like(q, dtype=float)
    for i in range(len(xs)):
        sl = np.abs(p - p[i]) <= 1.0
        lo, hi = q[sl].min(), q[sl].max()
        v[i] = 0.0 if hi - lo < 1e-6 else 2 * (q[i] - lo) / (hi - lo) - 1
    return xs, ys, u, v, p.max() - p.min()


def add_roof_box(a, veh, u0, u1, vmax=0.8, top=(46, 70, 114), side=(22, 38, 70),
                 grille=(168, 174, 180), grille_u=(0.0, 1.0), gw=0.15):
    """A flat box on the roof (e.g. an A/C unit): top face lifted 1 px, a 1 px
    darker face along its near edge, and a light grille line on the centreline."""
    lab, refs, fac, K = zones(veh)
    for col in range(8):
        xs, ys, u, v, plen = roof_uv(lab, col)
        on_top = lab[ys, col * 128 + xs] == Z["ROOF"]      # not the side-wall roof edge
        sel = (u >= u0) & (u <= u1) & (np.abs(v) <= vmax) & on_top
        bx, by, bu, bv = xs[sel], ys[sel], u[sel], v[sel]
        if not len(bx):
            continue
        X0 = col * 128
        # near (bottom-most) pixel of each column becomes the side face; the grille
        # is the one pixel per column closest to the roof centreline
        near, mid = {}, {}
        for x, y, uu, vv in zip(bx, by, bu, bv):
            near[x] = max(near.get(x, -1), y)
            f = (uu - u0) / max(1e-6, u1 - u0)
            key = int(round(uu * plen))               # one slice along the body
            if grille_u[0] <= f <= grille_u[1] and (key not in mid or abs(vv) < mid[key][2]):
                mid[key] = (x, y, abs(vv))
        for x, y in zip(bx, by):
            a[y - 1, X0 + x] = top
        for x, y, _ in mid.values():
            a[y - 1, X0 + x] = grille
        for x, y in near.items():
            a[y, X0 + x] = side
    return unspecial(a)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        sys.exit("usage: zonemap.py 810|010 out.png   (false-colour zone map of one body)")
    lab, _ = build(sys.argv[1])
    Image.fromarray(falsecolor(lab)).save(sys.argv[2])
