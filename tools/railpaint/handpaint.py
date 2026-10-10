"""Repaint TommPa9's hand-drawn pak128.cs locomotive sheets in other liveries.

The user prefers TommPa9's drawings to any box render (Eso, Brejlovec,
2026-10-10), so these families keep his silhouette, shading and details and
change only the paint. A HandBase is one silhouette drawn by him in several
reference liveries (sheets in source coordinates, lifted 4 px from the pak).
Every solid pixel of the base sheet gets

  face  'S' side wall, 'E' end face, 'R' roof (above the face top),
        'U' under the face (frame, bogies, buffer beam)
  K     row from the face top of its column (0 = first face row)
  U     0 front .. 1 rear along a side face, 0 .. 1 across an end face

The face tops are exact. In the pure views (ne / sw sides, nw / se ends) they
are fixed rows; in the diagonal views each column is aligned to the pure
view's row profile across all reference liveries and the result is forced onto
exact 2:1 stairs, so one-row stripes stay one row in every view. (railpaint's
body.py / warp.py maps diagonal rows through a rounded shear and is off by one
in every other column, which breaks 1-px stripes on these small sheets.)

Liveries are painted either by rules on (face, K) or by transferring the layout
of one of his own sheets in that livery: every template colour maps to a zone
name and the zone takes a palette colour (palette.py / cd_loco_livery.py), so
his stripes, wedges and window frames survive in the shared ČD colours. Colours
are albedos as seen on the south-facing side (w / e views); FACT darkens them
per view and face like his own palette steps.
"""
import numpy as np
from PIL import Image

T = np.array([231, 255, 255])
SIDE_SRC = {0: 7, 2: 3, 4: 3, 6: 7}
END_SRC = {0: 1, 2: 1, 4: 5, 6: 5}
SLOPE = {0: 1, 4: 1, 2: -1, 6: -1}          # side top on screen: w / e down-right, n / s up-right
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
KEEP_SPECIAL = {0xFFFF53, 0xFF211D}           # head / tail lights

# face brightness per view relative to the albedo (south-facing side = 1):
# TommPa9 draws the pure views one palette step darker than w / e and the n / s
# sides one more; an end face takes the opposite step of its view's side.
FACT = {"S": {0: 1.0, 4: 1.0, 3: 0.87, 7: 0.87, 2: 0.76, 6: 0.76},
        "E": {1: 0.87, 5: 0.87, 0: 0.76, 4: 0.76, 2: 1.0, 6: 1.0}}


def hexarr(a):
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def lum(a):
    a = a.astype(float)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def load(path):
    return np.array(Image.open(path).convert("RGB")).astype(int)[:128, :1024]


def shade(c, f):
    """Contrast-preserving shade: mid tones move most, white and black least,
    the way his palette steps do (blue 0x003A73 -> 0x00428C, white E6 -> EF)."""
    out = []
    for v in c:
        v = float(v)
        out.append(int(max(0, min(255, round(v + (f - 1.0) * v * (1.0 - v / 255.0) * 2.2)))))
    return tuple(out)


def scale(c, f):
    return tuple(int(max(0, min(255, round(v * f)))) for v in c)


def unspecial(a, painted):
    """Nudge painted pixels off the special-colour table (his own glass
    0x6B6B6B and lamps stay bit-exact where they were not painted)."""
    hx = hexarr(a)
    bad = np.isin(hx, list(SPECIAL - KEEP_SPECIAL)) & painted
    a[bad, 2] = np.where(a[bad, 2] < 255, a[bad, 2] + 1, 254)
    return a


def _feat(R):
    R = R.astype(float)
    L = lum(R)
    n = R / (L[..., None] + 30.0)
    dark = (L < 60).astype(float)[..., None] * 0.8
    return np.concatenate([n, dark], axis=-1)


class HandBase:
    """refs: sheet arrays sharing one silhouette; base: index of the sheet whose
    details are kept. side_top {3: y, 7: y}, end_top {1: y, 5: y}: the first
    face row in the pure views. nk_side / nk_end: face rows (K 0 .. nk-1); rows
    below are 'U'. end_width: columns of the end face in the diagonal views
    (None: find the split by alignment cost)."""

    def __init__(self, refs, base, side_top, end_top, nk_side, nk_end,
                 side_prof_x=range(50, 72), end_prof_x=(59, 60, 61, 65, 66, 67), end_width=None):
        self.R = np.stack(refs)
        self.base = self.R[base].copy()
        self.solid = ~np.all(self.base == T, axis=2)
        self.side_top, self.end_top = side_top, end_top
        self.nk_side, self.nk_end = nk_side, nk_end
        self.end_width = end_width
        H, W = self.solid.shape
        self.face = np.full((H, W), "", "U1")
        self.K = np.full((H, W), -99, int)
        self.U = np.full((H, W), -1.0)
        self.top = {}
        F = _feat(self.R)
        for c in (3, 7):
            self._pure(c, side_top[c], "S", nk_side)
        for c in (1, 5):
            self._pure(c, end_top[c], "E", nk_end)
        for c in (0, 2, 4, 6):
            self._diag(c, F, list(side_prof_x), list(end_prof_x))
        self.col = np.tile(np.repeat(np.arange(8), 128), (H, 1))

    def _pure(self, c, top, face, nk):
        sl = slice(c * 128, (c + 1) * 128)
        ys, xs = np.where(self.solid[:, sl])
        x0, x1 = xs.min(), xs.max()
        for y, x in zip(ys, xs):
            k = y - top
            X = c * 128 + x
            self.K[y, X] = k
            self.face[y, X] = "R" if k < 0 else (face if k < nk else "U")
            if face == "S":     # ne (3) travels right: front at x1; sw (7) front at x0
                self.U[y, X] = (x1 - x) / (x1 - x0) if c == 3 else (x - x0) / (x1 - x0)
            else:
                self.U[y, X] = (x - x0) / (x1 - x0)
            self.top[(c, x)] = top

    @staticmethod
    def _profile(F, col, top, xs, k0, k1):
        return np.stack([np.median(F[:, top + k, [col * 128 + x for x in xs]], axis=1)
                         for k in range(k0, k1 + 1)], axis=1)

    def _align(self, F, c, x, prof, k0):
        best = (1e9, None)
        X = c * 128 + x
        for y0 in range(40, 110):
            d, cnt = 0.0, 0
            for i in range(prof.shape[1]):
                y = y0 + k0 + i
                if 0 <= y < 128 and self.solid[y, X]:
                    d += np.abs(F[:, y, X] - prof[:, i]).sum()
                    cnt += 1
            if cnt >= prof.shape[1] - 3 and d / cnt < best[0]:
                best = (d / cnt, y0)
        return best

    @staticmethod
    def _stair(xs, ys, sg):
        best = (1e18, None)
        for p in (0, 1):
            base = np.array([sg * ((x + p) // 2) for x in xs])
            a = int(round(np.median(np.array(ys) - base)))
            err = np.abs(np.array(ys) - (a + base)).sum()
            if err < best[0]:
                best = (err, (a, p))
        a, p = best[1]
        return lambda x: a + sg * ((x + p) // 2)

    def _diag(self, c, F, sp_x, ep_x):
        sc, ec = SIDE_SRC[c], END_SRC[c]
        sp = self._profile(F, sc, self.side_top[sc], sp_x, -2, self.nk_side)
        ep = self._profile(F, ec, self.end_top[ec], ep_x, -2, self.nk_end)
        xs = np.where(self.solid[:, c * 128:(c + 1) * 128].any(axis=0))[0]
        rs = [(x,) + self._align(F, c, x, sp, -2) + self._align(F, c, x, ep, -2) for x in xs]
        right_end = c in (0, 4)           # visible end face: right in w / e, left in n / s
        n = len(rs)
        best = (1e18, None)
        for split in (range(n // 2, n) if self.end_width is None else [n - self.end_width]):
            side, end = (rs[:split], rs[split:]) if right_end else (rs[n - split:], rs[:n - split])
            cost = sum(r[1] for r in side if r[2] is not None) + sum(r[3] for r in end if r[4] is not None)
            cost += 1e6 * (sum(r[2] is None for r in side) + sum(r[4] is None for r in end))
            if cost < best[0]:
                best = (cost, (side, end))
        side, end = best[1]
        gs = [(r[0], r[2]) for r in side if r[2] is not None and r[1] < 12]
        ge = [(r[0], r[4]) for r in end if r[4] is not None and r[3] < 12]
        fs = self._stair([g[0] for g in gs], [g[1] for g in gs], SLOPE[c])
        fe = self._stair([g[0] for g in ge], [g[1] for g in ge], -SLOPE[c]) if len(ge) >= 2 else None
        sx, ex = [r[0] for r in side], [r[0] for r in end]
        xa, xb = min(sx), max(sx)
        front_left = c in (0, 6)          # w travels up-left, s down-left: front at the left
        for x in xs:
            X = c * 128 + x
            if x in ex and fe is not None:
                top, face, nk = fe(x), "E", self.nk_end
                u = (x - min(ex)) / max(1, max(ex) - min(ex))
            else:
                top, face, nk = fs(x), "S", self.nk_side
                u = (x - xa) / max(1, xb - xa)
                if not front_left:
                    u = 1 - u
            self.top[(c, x)] = top
            for y in np.where(self.solid[:, X])[0]:
                k = y - top
                self.K[y, X] = k
                self.face[y, X] = "R" if k < 0 else (face if k < nk else "U")
                self.U[y, X] = u

    # ------------------------------------------------------------ helpers
    def factor(self, y, x, face=None):
        f = face or self.face[y, x]
        return FACT[f].get(self.col[y, x], 0.87) if f in ("S", "E") else 1.0

    def column_u(self, c):
        """median side-face u per column of view c."""
        out = {}
        for x in range(128):
            m = self.face[:, c * 128 + x] == "S"
            if m.any():
                out[x] = float(np.median(self.U[m, c * 128 + x]))
        return out

    def end_columns(self, c):
        return {x for x in range(128) if (self.face[:, c * 128 + x] == "E").any()}


def template_zones(hb, tmpl, cmap):
    """Zone name per pixel from a template sheet of the same silhouette: every
    template colour listed in cmap names its zone; pixels the template leaves
    unlisted (its own windows, marks) take the commonest zone of their row
    (view, face, K) so the base's paint under them follows the stripe."""
    v = hexarr(tmpl)
    H, W = v.shape
    z = np.full((H, W), "", object)
    for hx, name in cmap.items():
        z[(v == hx) & hb.solid] = name
    for c in range(8):
        sl = slice(c * 128, (c + 1) * 128)
        for f in ("S", "E", "U", "R"):
            m = hb.face[:, sl] == f
            if not m.any():
                continue
            for k in np.unique(hb.K[:, sl][m]):
                mk = m & (hb.K[:, sl] == k)
                names = [n for n in z[:, sl][mk] if n]
                if not names:
                    continue
                common = max(set(names), key=names.count)
                zz = z[:, sl]
                zz[mk & (zz == "")] = common
    return z


def even_slots(cols, n):
    """n evenly spaced picks from a sorted column list."""
    if not cols:
        return []
    return sorted({cols[min(len(cols) - 1, int((i + 0.5) * len(cols) / n))] for i in range(n)})


def save(a, path):
    Image.fromarray(a.astype(np.uint8)).save(path)
    v = hexarr(a)
    bad = set(np.unique(v).tolist()) & (SPECIAL - KEEP_SPECIAL - {0x6B6B6B, 0xC1B1D1, 0x9B9B9B})
    if bad:
        print("  note: special colours kept from the base:", [hex(b) for b in sorted(bad)], path)
