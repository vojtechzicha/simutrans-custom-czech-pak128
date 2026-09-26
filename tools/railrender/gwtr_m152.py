"""GW Train Regio M 152.0 family: 810, 816 and the 814.5 + 914.5 RegioNova.

Zone-map repaints of the CeskeDrahy sheets, i.e. Sim's pak128.CS drawings as
already repainted per ČD livery in this repo:

  vehicle-rail/ceske-drahy/810/sprites/*.png     row 0: the 810 railcar
  vehicle-rail/ceske-drahy/814_0/sprites/*.png   row 0: 914, cab leading
                                                 row 2: 814.0, cab leading

All ČD liveries of one drawing share its silhouette, glass and shading, so the
per-livery pixel differences locate every painted zone.  For each drawing
(Body) the script

  1. labels every pixel with its face (side / end / roof / fixed), its row k
     inside the face and its position along the car (u, 0 = rear or inner end,
     1 = cab) or across the end face (v):
       - the pure views (ne/sw sides, nw/se ends) by their rows and columns,
       - the diagonal views (w, n, e, s) through fitted shear maps onto the
         pure views (pak128 draws heights vertically in every view, so a
         diagonal side face is the ne/sw side compressed by 4/5.66 and
         sheared by 1/2; its end face the nw/se end sheared the other way),
         the rows then snapped per column onto the source's own row pattern;
  2. shades every livery pixel with the lighting of its view and face (the
     south-facing side = 1.0, as railkit's rendered trains, so the palette
     colours show exactly there) times its own edge highlight or shadow in
     the ČD sheets (median over the liveries, ČD lettering ignored);
  3. paints a GWTR design given as a function of (face, k, u / v), keeping the
     lit window glass (0x4D4D4D / 0x57656F), the lamps of the source row and
     the fixed dark parts (bogies, buffers, neutralised); windscreens and cab
     side windows become plain dark glass, the ČD yellow plough the livery.

The 816's roof units are boxes drawn with railkit's renderer on the 810 body.

The rear-facing 814.5 / 914.5 rows are the front-facing cars turned round
exactly as in the ČD sheets (direction columns shifted by 4, moved one
carunit forward, head / tail lamps swapped).

Regenerate with `python tools/railrender/gwtr.py 810 816 814_5`.
"""
import os
import numpy as np
from PIL import Image

import railkit as R
from render import DIRS

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CD = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

LIVERIES_810 = ["oranzovozelena", "zlutocerna"]
LIVERIES_816 = ["oranzovozelena"]
LIVERIES_814 = ["oranzovozelena"]

T = (231, 255, 255)
TA = np.array(T)

SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}
GLASS, GLASS_HI = 0x4D4D4D, 0x57656F
HEAD, TAIL = 0xFFFF53, 0xFF211D
KEEP = {GLASS, GLASS_HI, HEAD, TAIL}

# direction columns: 0 w, 1 nw, 2 n, 3 ne, 4 e, 5 se, 6 s, 7 sw
SIDE_VIEWS, END_VIEWS, DIAG_VIEWS = (3, 7), (1, 5), (0, 2, 4, 6)
SIDE_SRC = {0: 7, 2: 3, 4: 3, 6: 7}      # pure side view a diagonal side face copies
END_SRC = {0: 1, 2: 1, 4: 5, 6: 5}       # nw = rear / inner end, se = front (cab)
SLOPE = {0: 0.5, 2: -0.5, 4: 0.5, 6: -0.5}
# screen direction of travel per view (roof rows run along it)
HEADING = {0: (-2, -1), 1: (0, -1), 2: (2, -1), 3: (1, 0), 4: (2, 1), 5: (0, 1), 6: (-2, 1), 7: (-1, 0)}

# faces: transparent, side, end, roof, fixed (outside the side face)
F_T, F_S, F_E, F_R, F_X = 0, 1, 2, 3, 4
# pixel kinds handed to a design: livery pixel, windscreen, fixed part
K_PAINT, K_WSCREEN, K_FIX = 0, 4, 6


def hexv(a):
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def rnd(v):
    """Round half up (Python's round() is half-to-even, which makes pixel
    staircases alternate)."""
    return int(np.floor(v + 0.5))


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def lum(a):
    a = a.astype(float)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def safe(c):
    """Round, clip and nudge a colour off Simutrans' special colour table."""
    c = tuple(int(max(0, min(255, round(float(x))))) for x in c)
    h = (c[0] << 16) | (c[1] << 8) | c[2]
    if h in SPECIAL and h not in KEEP:
        c = (c[0], c[1], c[2] + 1 if c[2] < 255 else c[2] - 1)
    return c


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ------------------------------------------------------------------ sources
SOURCES = {
    # name: family dir, sheet row, liveries (first = base for fixed pixels),
    #       liveries whose zones are (nearly) row-uniform (row signatures),
    #       upstream sheets that are not zone-painted (ignored for the livery
    #       mask: their fixed parts differ from the ČD repaints)
    "810": dict(fam="810", row=0,
                livs=["cervenokremova", "najbrt1", "najbrt2", "pardubickykraj", "pidcervenomodrobila"],
                sig=["cervenokremova", "najbrt1", "najbrt2", "pardubickykraj", "pidcervenomodrobila"],
                side_top=84, end_top={1: 78, 5: 89}),
    "914": dict(fam="814_0", row=0,
                livs=["najbrt2", "pardubickykraj", "vysocina", "plzenskykraj", "pidsedocervena", "zlutozelena"],
                sig=["najbrt2", "pardubickykraj", "vysocina", "plzenskykraj"],
                upstream=["zlutozelena"],
                side_top=83, end_top={1: 78, 5: 88}),
    "814": dict(fam="814_0", row=2,
                livs=["najbrt2", "pardubickykraj", "vysocina", "plzenskykraj", "pidsedocervena", "zlutozelena"],
                sig=["najbrt2", "pardubickykraj", "vysocina", "plzenskykraj"],
                upstream=["zlutozelena"],
                side_top=83, end_top={1: 78, 5: 88}),
}


def _load(fam, liv, row):
    p = os.path.join(CD, fam, "sprites", f"{liv}.png")
    return np.array(Image.open(p).convert("RGB"))[row * 128:(row + 1) * 128, :1024].astype(int)


# ------------------------------------------------------------------ analysis
def _features(t):
    """Shading-robust per-pixel features of [n,128,W,3] reference tiles."""
    t = t.astype(float)
    L = lum(t)
    chroma = (t - L[..., None]) / (L[..., None] + 25.0) * 60.0
    v = hexv(t.astype(int))
    glass = np.isin(v, (GLASS, GLASS_HI)).astype(float) * 40.0
    dark = (L < 70) * 15.0
    bright = (L > 200) * 15.0
    f = np.concatenate([chroma, glass[..., None], dark[..., None], bright[..., None]], axis=-1)
    return np.moveaxis(f, 0, -2).reshape(t.shape[1], t.shape[2], -1)


def _fit(fd, pts, fs, ms, slope, s_list, bxr, byr, keep):
    """Best (s, bx, by) mapping diagonal pixels pts onto a pure view:
    sx = s*x + bx, sy = y - slope*x + by; score = trimmed mean feature
    distance over the best `keep` fraction of the points."""
    ys, xs = pts
    best = (1e18, None)
    k = max(1, int(keep * len(xs)))
    for s in s_list:
        sx = np.floor(s * xs[None, :] + np.arange(*bxr)[:, None] + 0.5).astype(int)       # [nbx, n]
        for by in range(*byr):
            sy = np.floor(ys - slope * xs + by + 0.5).astype(int)
            for i, bx in enumerate(range(*bxr)):
                x = sx[i]
                ok = (x >= 0) & (x < 128) & (sy >= 0) & (sy < 128)
                ok[ok] &= ms[sy[ok], x[ok]]
                if ok.sum() < k:
                    continue
                d = np.abs(fd[ys[ok], xs[ok]] - fs[sy[ok], x[ok]]).sum(axis=1)
                sc = np.partition(d, k - 1)[:k].mean()
                if sc < best[0]:
                    best = (sc, (s, bx, by))
    return best


class Body:
    """Face / row / position labels, kinds and shading of one Sim drawing."""

    def __init__(self, name):
        cfg = SOURCES[name]
        self.name = name
        self.cfg = cfg
        self.refs = np.stack([_load(cfg["fam"], l, cfg["row"]) for l in cfg["livs"]])
        self.sig_refs = np.stack([self.refs[cfg["livs"].index(l)] for l in cfg["sig"]])
        self.base = self.refs[0]
        self.stop = cfg["side_top"]
        self.etop = cfg["end_top"]
        self.body = ~np.all(self.base == TA, axis=-1)
        v = hexv(self.refs)
        self.glass = np.isin(v, (GLASS, GLASS_HI)).any(axis=0) & self.body
        self.glass_hi = (v == GLASS_HI).any(axis=0)
        bv = hexv(self.base)
        self.head = bv == HEAD
        self.tail = bv == TAIL
        painted = np.stack([r for l, r in zip(cfg["livs"], self.refs) if l not in cfg.get("upstream", ())])
        self.var = np.zeros_like(self.body)
        for i in range(1, len(painted)):
            self.var |= np.any(painted[i] != painted[0], axis=-1)
        self.var &= self.body & ~self.glass & ~self.head & ~self.tail
        self.face = np.full((128, 1024), F_T, int)
        self.K = np.full((128, 1024), -99, int)
        self.U = np.full((128, 1024), -1.0)
        self.fits = {}
        self._clusters()
        self._pure()
        self._row_sets()
        self._diag()
        self._roof_u()
        self._shading()
        # door leaves: yellow in the Pardubický kraj livery and yellow in the
        # Plzeňský kraj one (RegioNova) / red in the PID one (810); a yellow
        # emblem of one livery alone is not a door
        def ref(l):
            return self.refs[cfg["livs"].index(l)]

        def yellow(a):
            return (a[..., 0] > 150) & (a[..., 1] > 110) & (a[..., 2] < 90)
        pk = ref("pardubickykraj")
        if "plzenskykraj" in cfg["livs"]:
            second = yellow(ref("plzenskykraj"))
        else:
            pid = ref("pidcervenomodrobila")
            second = (pid[..., 0] > 120) & (pid[..., 1] < 80) & (pid[..., 2] < 90)
        self.door = yellow(pk) & second & self.var & (self.face == F_S)

    # ---- lighting ---------------------------------------------------------
    # face lighting per view: sides as railkit (south side 1.0, ne / sw 0.87,
    # n / s 0.72; Sim's sides measure the same), ends as measured on the ČD
    # 810 sheets (w / e 0.80, n / s 0.96, nw / se 0.84; railkit 0.72 / 1.0 / 0.86)
    LEVEL = {F_S: {0: 1.0, 4: 1.0, 3: 0.87, 7: 0.87, 2: 0.72, 6: 0.72},
             F_E: {0: 0.80, 4: 0.80, 2: 0.96, 6: 0.96, 1: 0.84, 5: 0.84}}

    def _shading(self):
        """fac = lighting level of the pixel's view and face (LEVEL) times the
        pixel's own edge highlight or shadow against its zone in that view
        (median over the ČD liveries, skipping clipped colours); the roof
        keeps its per-pixel curvature shading against the w / e roofs."""
        L = lum(self.sig_refs)
        n = len(L)
        views = [np.zeros((128, 1024), bool) for _ in range(8)]
        for c in range(8):
            views[c][:, c * 128:(c + 1) * 128] = True
        we = views[0] | views[4]
        cl = self.cl
        fac = np.ones((128, 1024))
        for c in range(8):
            for f in (F_S, F_E):
                lv = self.LEVEL[f].get(c, 0.85)
                for z in np.unique(cl[views[c] & (self.face == f) & (cl >= 0)]):
                    m = (cl == z) & views[c] & (self.face == f)
                    ys, xs = np.where(m)
                    # per livery: deviation from the zone, but only where the
                    # pixel has the zone's colour (not a ČD logo or lettering)
                    num = np.zeros(len(ys))
                    dev = np.full((n, len(ys)), np.nan)
                    for i in range(n):
                        med = np.median(L[i][m])
                        if not 12 < med < 250:
                            continue
                        px = self.sig_refs[i][ys, xs].astype(float)
                        mc = np.median(self.sig_refs[i][m].astype(float), axis=0)
                        ch_p = px / (lum(px)[:, None] + 8.0)
                        ch_m = mc / (lum(mc) + 8.0)
                        ok = np.abs(ch_p - ch_m).sum(axis=1) < 0.15
                        dev[i, ok] = L[i][ys, xs][ok] / med
                        num += ok
                    d = np.ones(len(ys))
                    for j in np.where(num > 0)[0]:
                        col = dev[:, j]
                        d[j] = np.median(col[~np.isnan(col)])
                    d = np.where(np.abs(d - 1.0) > 0.09, d, 1.0)
                    fac[ys, xs] = lv * d
        # roof: each pixel against its zone on the w / e roofs
        roof = self.face == F_R
        ref_all = np.array([np.median(L[i][roof & we & (cl >= 0)]) for i in range(n)])
        for z in np.unique(cl[roof & (cl >= 0)]):
            m = (cl == z) & roof
            mr = m & we
            a = np.array([np.median(L[i][mr]) for i in range(n)]) if mr.sum() >= 2 else ref_all
            ys, xs = np.where(m)
            r = [L[i][ys, xs] / a[i] for i in range(n) if 12 < a[i] < 250]
            fac[ys, xs] = np.median(np.stack(r), axis=0) if r else 1.0
        self.fac = np.clip(fac, 0.45, 1.35)

    # ---- row signatures ---------------------------------------------------
    def _clusters(self):
        """Group livery pixels by their colour across the row-uniform ČD
        liveries (rgb / luminance per livery: shading cancels out); every
        group is one painted zone of the ČD sheets."""
        r = self.sig_refs.astype(float)
        s = r / (lum(r)[..., None] + 8.0)
        S = np.moveaxis(s, 0, 2).reshape(128, 1024, -1)
        self.cl = np.full((128, 1024), -1, int)
        cent = []
        thr = 0.25 * S.shape[-1] / 3
        ys, xs = np.where(self.var)
        for y, x in zip(ys, xs):
            v = S[y, x]
            best, bd = -1, thr
            for i, c in enumerate(cent):
                d = np.abs(c - v).sum()
                if d < bd:
                    best, bd = i, d
            if best < 0:
                cent.append(v.copy())
                best = len(cent) - 1
            self.cl[y, x] = best
        self.ncl = len(cent)

    def _row_sets(self):
        """Rows k each zone occupies in the pure side views / pure end views."""
        self.ksets = {F_S: {}, F_E: {}}
        for f, views in ((F_S, SIDE_VIEWS), (F_E, END_VIEWS)):
            for c in views:
                sl = slice(c * 128, (c + 1) * 128)
                m = (self.cl[:, sl] >= 0) & (self.face[:, sl] == f)
                for cl, k in zip(self.cl[:, sl][m], self.K[:, sl][m]):
                    self.ksets[f].setdefault(cl, set()).add(int(k))

    # ---- helpers ----------------------------------------------------------
    def tile(self, a, c):
        return a[..., c * 128:(c + 1) * 128] if a.ndim == 2 else a[:, :, c * 128:(c + 1) * 128]

    def side_x(self, c):
        """x range of the side face in pure side view c (livery columns at the
        belt row, i.e. without buffers and gangway bellows)."""
        y = self.stop + 5
        xs = [x for x in range(128) if self.var[y, c * 128 + x] or self.glass[y, c * 128 + x]]
        return min(xs), max(xs)

    def end_x(self, c):
        y = self.etop[c] + 1
        xs = [x for x in range(128) if self.body[y, c * 128 + x]]
        return min(xs), max(xs)

    # ---- pure views -------------------------------------------------------
    def _pure(self):
        for c in SIDE_VIEWS:
            x0, x1 = self.side_x(c)
            self.sx = getattr(self, "sx", {})
            self.sx[c] = (x0, x1)
            for y in range(128):
                for x in range(128):
                    X = c * 128 + x
                    if not self.body[y, X]:
                        continue
                    k = y - self.stop
                    if k < 0:
                        self.face[y, X] = F_R
                    elif x0 <= x <= x1:
                        self.face[y, X] = F_S
                    else:
                        self.face[y, X] = F_X
                    self.K[y, X] = k
                    u = (x - x0) / (x1 - x0)
                    self.U[y, X] = u if c == 3 else 1.0 - u
        for c in END_VIEWS:
            x0, x1 = self.end_x(c)
            self.ex = getattr(self, "ex", {})
            self.ex[c] = (x0, x1)
            for y in range(128):
                for x in range(128):
                    X = c * 128 + x
                    if not self.body[y, X]:
                        continue
                    k = y - self.etop[c]
                    self.face[y, X] = F_R if k < 0 else F_E
                    self.K[y, X] = k
                    self.U[y, X] = (x - x0) / (x1 - x0)

    # ---- diagonal views ---------------------------------------------------
    def _diag(self):
        feats = {c: _features(self.tile(self.sig_refs, c)) for c in range(8)}
        masks = {c: self.tile(self.body, c) for c in range(8)}
        for c in DIAG_VIEWS:
            fd, md = feats[c], masks[c]
            ys, xs = np.where(md)
            sc, ec = SIDE_SRC[c], END_SRC[c]
            # side map
            ms = masks[sc]
            sys_, sxs_ = np.where(ms)
            cxd, cyd = (xs.min() + xs.max()) / 2, ys.mean()
            cxs, cys = (sxs_.min() + sxs_.max()) / 2, sys_.mean()
            bx0 = int(round(cxs - 1.414 * cxd))
            by0 = int(round(cys - (cyd - SLOPE[c] * cxd)))
            s_fit = _fit(fd, (ys, xs), feats[sc], ms, SLOPE[c], (1.38, 1.40, 1.42, 1.44),
                         (bx0 - 12, bx0 + 13), (by0 - 12, by0 + 13), 0.6)[1]
            # end map, fitted on the pixels at the visible end
            me = masks[ec].copy()
            me[:self.etop[ec]] = False
            right = c in (0, 4)
            sel = (xs >= xs.max() - 10) if right else (xs <= xs.min() + 10)
            sel &= ys > ys.mean() - 2
            eys, exs = np.where(me)
            xext = xs.max() - 3 if right else xs.min() + 3
            bxe0 = int(round((exs.min() + exs.max()) / 2 - 1.414 * xext))
            bye0 = int(round(eys.mean() - (ys[sel].mean() + SLOPE[c] * xs[sel].mean())))
            e_fit = _fit(fd, (ys[sel], xs[sel]), feats[ec], me, -SLOPE[c], (1.38, 1.40, 1.42, 1.44),
                         (bxe0 - 20, bxe0 + 21), (bye0 - 25, bye0 + 26), 0.4)[1]
            self.fits[c] = (s_fit, e_fit)
            self._label_diag(c, s_fit, e_fit)

    def _label_diag(self, c, s_fit, e_fit):
        s, bx, by = s_fit
        se, bxe, bye = e_fit
        sc, ec = SIDE_SRC[c], END_SRC[c]
        m = SLOPE[c]
        x0, x1 = self.sx[sc]
        ex0, ex1 = self.ex[ec]
        # the visible end of the side face in the pure side view, and the
        # diagonal-view column of the corner between side and end face
        vis_front = c in (4, 6)
        x_end = (x1 if sc == 3 else x0) if vis_front else (x0 if sc == 3 else x1)
        xc = (x_end - bx) / s
        end_right = c in (0, 4)
        for x in range(128):
            X = c * 128 + x
            col = np.where(self.body[:, X])[0]
            if not len(col):
                continue
            is_end = (x > xc) if end_right else (x < xc)
            if is_end:
                ybase = [y + m * x + bye for y in col]          # end rows slope the other way
                top, face = self.etop[ec], F_E
            else:
                ybase = [y - m * x + by for y in col]
                top, face = self.stop, F_S
            # snap the rows of this column onto the zones' known rows (single-
            # row zones such as a belt stripe decide; ties keep the shear map)
            ks = self.ksets[face]
            best = None
            for dy in (0, -1, 1, -2, 2):
                sc_ = 0.0
                for y, yb in zip(col, ybase):
                    cl = self.cl[y, X]
                    if cl < 0 or cl not in ks:
                        continue
                    k = rnd(yb) + dy - top
                    if k in ks[cl]:
                        sc_ += 1.0 / len(ks[cl])
                if best is None or sc_ > best[0] + 1e-9:
                    best = (sc_, dy)
            dy = best[1]
            for y, yb in zip(col, ybase):
                sy = rnd(yb) + dy
                k = sy - top
                self.K[y, X] = k
                if k < 0:
                    self.face[y, X] = F_R
                else:
                    self.face[y, X] = face
                if face == F_S and k >= 0:
                    sxf = s * x + bx
                    u = (sxf - x0) / (x1 - x0)
                    self.U[y, X] = min(1.0, max(0.0, u if sc == 3 else 1.0 - u))
                elif face == F_E and k >= 0:
                    exf = se * x + bxe
                    self.U[y, X] = min(1.0, max(0.0, (exf - ex0) / (ex1 - ex0)))

    # ---- roof -------------------------------------------------------------
    def _roof_u(self):
        """u along the car (0 rear, 1 front) for roof pixels: distance from the
        roof's front end measured along screen lines parallel to the heading,
        so the roof's curvature and lateral position cancel out."""
        for c in range(8):
            hx, hy = HEADING[c]
            ys, xs = np.where(self.tile(self.face, c) == F_R)
            if not len(xs):
                continue
            if c in (3, 7):
                key = ys.copy(); proj = xs * hx
            elif c in (1, 5):
                key = xs.copy(); proj = ys * hy
            else:
                key = np.floor((hx * ys - hy * xs) / 2.0).astype(int)
                proj = xs * np.sign(hx)
            lines = {}
            for i, kk in enumerate(key):
                lo, hi = lines.get(kk, (1e9, -1e9))
                lines[kk] = (min(lo, proj[i]), max(hi, proj[i]))
            L = np.median([hi - lo for lo, hi in lines.values()])
            for i in range(len(xs)):
                lo, hi = lines[key[i]]
                u = 1.0 - (hi - proj[i]) / max(1.0, L)
                self.U[ys[i], c * 128 + xs[i]] = min(1.0, max(0.0, u))
        # in the end views the outermost roof columns are the side walls seen
        # edge-on where the ČD sheets paint them in a side colour (not the
        # roof's): side face, row 0, u along the car
        roof_cl = np.bincount(self.cl[(self.face == F_R) & (self.cl >= 0)]).argmax()
        for c in END_VIEWS:
            x0, x1 = self.ex[c]
            for x in (x0, x1):
                X = c * 128 + x
                for y in range(self.etop[c]):
                    if self.face[y, X] == F_R and self.cl[y, X] >= 0 and self.cl[y, X] != roof_cl:
                        self.face[y, X] = F_S
                        self.K[y, X] = 0


# ------------------------------------------------------------------ painting
WSCREEN = (0x2E, 0x3E, 0x4C)          # windscreens, cab side windows: plain dark glass
WS_SRC = {0x6B6B6C, 0x6C6C6C, 0x6B6B6B, 0x343A42}

_BODIES = {}


def get_body(name):
    if name not in _BODIES:
        _BODIES[name] = Body(name)
    return _BODIES[name]


def paint(b, design):
    """Paint body b. design(ctx) -> albedo colour (multiplied by the pixel's
    shading factor), ("flat", colour), or None to keep the source pixel.
    ctx keys: view, x, y (tile coords), face, k, u, kind (K_PAINT livery
    pixel / K_WSCREEN / K_FIX fixed part), base (source pixel), fac (its
    shading), lv (lighting of its view and face), door (door leaf)."""
    out = b.base.astype(float).copy()
    bv = hexv(b.base)
    ys, xs = np.where(b.body)
    for y, X in zip(ys, xs):
        v = int(bv[y, X])
        if b.glass[y, X]:
            out[y, X] = rgb(v) if v in (GLASS, GLASS_HI) else rgb(GLASS_HI if b.glass_hi[y, X] else GLASS)
            continue
        if v in (HEAD, TAIL):
            continue
        if b.var[y, X]:
            kind = K_PAINT
        elif v in WS_SRC:
            kind = K_WSCREEN
        else:
            kind = K_FIX
        ctx = dict(view=X // 128, x=X % 128, y=y, face=int(b.face[y, X]), k=int(b.K[y, X]),
                   u=float(b.U[y, X]), kind=kind, base=tuple(int(c) for c in b.base[y, X]),
                   fac=float(b.fac[y, X]), door=bool(b.door[y, X]),
                   lv=b.LEVEL.get(int(b.face[y, X]), {}).get(X // 128, 1.0))
        c = design(ctx)
        if c is None:
            if kind == K_WSCREEN:
                out[y, X] = WSCREEN
            elif kind == K_FIX:
                out[y, X] = neutral_dark(b.base[y, X])
            continue
        if isinstance(c, tuple) and len(c) == 2 and c[0] == "flat":
            out[y, X] = c[1]
            continue
        f = ctx["fac"] if kind == K_PAINT else 1.0
        out[y, X] = np.array(c, float) * f
    res = np.zeros((128, 1024, 3), np.uint8)
    res[:] = T
    for y, X in zip(ys, xs):
        res[y, X] = safe(out[y, X]) if int(hexv(out[y, X].round().astype(int))) not in KEEP else out[y, X]
    return res


def neutral_dark(c):
    """Fixed dark parts keep their luminance but lose the tint of the ČD /
    upstream livery they sat in (dark green, brown, red shadows)."""
    c = np.array(c, float)
    if c.max() - c.min() > 14 and lum(c) < 110:
        L = lum(c)
        return np.array((L, L, L * 1.02))
    return c


def split(row):
    return [row[:, c * 128:(c + 1) * 128].copy() for c in range(8)]


# screen reading direction of the side: in the ne-side views (e, n, ne) the
# car's front is on the right, in the sw-side views (w, s, sw) on the left
def reads_forward(view):
    return view in (2, 3, 4)


# ------------------------------------------------------------------ GWTR palette
ORANGE = (0xE8, 0x64, 0x1E)
GREEN = (0x11, 0x6B, 0x48)
LIME = (0x52, 0xC0, 0x40)
WHITE = (0xF2, 0xF4, 0xF5)
ROOF = (0xC3, 0xC7, 0xCA)
UNDER = (0x3A, 0x3C, 0x3F)            # underframe / bogie shadows
BLACK = (0x22, 0x23, 0x25)
YELLOW = (0xF2, 0xD2, 0x1A)           # 810 602 "Jarek"

def lw(ctx, n=1.0):
    """Width in u of n pixels of the side face in this view (the side faces
    are 36-38 px long in the pure views, compressed by 1.414 in diagonals)."""
    px = 1.0 if ctx["view"] in SIDE_VIEWS else 1.414
    return n * px / 36.0


def wordmark(pattern, t, row):
    """Sample a wordmark bitmap (list of strings, '#' = letter) at t 0..1 along
    it and row."""
    w = len(pattern[0])
    i = min(w - 1, max(0, int(t * w)))
    return pattern[row][i] == "#"


# ------------------------------------------------------------------ GWTR orange
# "GW TRAIN" on the side: bitmaps for the full-length (ne/sw, ~36 px) and the
# diagonal views (~26 px), sampled along the lettering's u range
WM_BIG = {   # 810 / 816: big letters, rows k0..k0+2
    "side": ["##.#.#.###.##.#.",
             "#..#.#..#..##.#.",
             "##.###..#..#..#."],
    "diag": ["#.##.##.#.#",
             "#.##..#..#.",
             "#.##..#.#.#"],
}
WM_SMALL = {  # RegioNova: GW TRAIN one line under the windows, rows k0..k0+1
    "side": ["##.#.###.",
             "##.#.#.#."],
    "diag": ["##.##.#",
             "#..#.##"],
}


class Scheme:
    """GWTR orange with dark-green car ends as a function of (face, k, u).

    side (u 0 = rear / inner end, 1 = cab):
      cab end green for k <= lime_k - 1 and u >= fb(k), fb linear from
      fb0 (k = 0) to fb1 (k = lime_k - 1); a lime edge one pixel wide along
      it and the lime band on row lime_k (u >= fb1);
      rear / inner end green for k <= rk and u <= rb(k), rb from rb0 to rb1,
      lime edge along it (and a lime band on row rk + 1 when rear_band);
      doors green when green_doors; white wordmark (u0, u1, k0, bitmaps).
    ends: (last green row, rows of the white logo between the lamps, lime
      row) for the cab front and the rear / gangway end; orange below.
    """

    def __init__(self, **kw):
        self.__dict__.update(kw)

    # -- side ---------------------------------------------------------------
    def side(self, ctx):
        k, u = ctx["k"], ctx["u"]
        if k > self.side_last:
            return self.under
        w = lw(ctx, 1.2)
        if ctx["door"] and self.green_doors:
            return GREEN
        L = self.lime_k
        if k < L:
            fb = self.fb0 + (self.fb1 - self.fb0) * k / max(1, L - 1)
            if u >= fb:
                return GREEN
            if u >= fb - w:
                return LIME
        elif k == L and u >= self.fb1 - w:
            return LIME
        if k <= self.rk:
            rb = self.rb0 + (self.rb1 - self.rb0) * k / max(1, self.rk)
            if u <= rb:
                return GREEN
            if u <= rb + w:
                return LIME
        elif self.rear_band and k == self.rk + 1 and u <= self.rb1 + w:
            return LIME
        u0, u1, k0, pats = self.wm
        pat = pats["side"] if ctx["view"] in SIDE_VIEWS else pats["diag"]
        if k0 <= k < k0 + len(pat) and u0 <= u <= u1:
            t = (u - u0) / (u1 - u0)
            if not reads_forward(ctx["view"]):
                t = 1.0 - t
            if wordmark(pat, t, k - k0):
                return WHITE
        return ORANGE

    # -- ends ---------------------------------------------------------------
    def end_rows(self, front):
        return self.cab_rows if (front or self.rear_is_cab) else self.gang_rows

    def end(self, ctx, front):
        k, v = ctx["k"], ctx["u"]
        green_to, logo_k, lime_k = self.end_rows(front)
        if k <= green_to:
            if logo_k is not None and k in logo_k and self.logo[0] <= v <= self.logo[1]:
                t = (v - self.logo[0]) / (self.logo[1] - self.logo[0])
                if int(t * 5) != 2:                 # GW | TRAIN
                    return WHITE
            return GREEN
        c = LIME if k == lime_k else ORANGE
        if not (front or self.rear_is_cab):
            # gangway end: a plain wall, without the bright outline Sim draws
            # round the gangway door (it reads as a stray glyph in orange)
            return ("flat", safe(np.array(c, float) * min(ctx["fac"], ctx["lv"])))
        return c

    def __call__(self, ctx):
        f, kind = ctx["face"], ctx["kind"]
        if kind == K_WSCREEN:
            return None
        front = ctx["view"] in (4, 5, 6)
        if f == F_R:
            if kind != K_PAINT:
                return None
            if ctx["u"] >= self.cap:
                return GREEN
            return self.roof
        if f == F_S:
            return self.side(ctx) if kind == K_PAINT else None
        if f == F_E:
            if kind == K_FIX:
                b = ctx["base"]
                if b[0] > 120 and b[1] > 70 and b[2] < 60 and b[0] - b[2] > 80:
                    # ČD / upstream plough and beam yellow -> orange apron
                    return ("flat", safe(mix(ORANGE, (0, 0, 0), 0.08 if b[1] > 200 else 0.35)))
                logo_k = self.end_rows(front)[1]
                if logo_k is not None and ctx["k"] in logo_k and self.logo[0] <= ctx["u"] <= self.logo[1] \
                        and lum(np.array(b, float)) < 60:
                    return ("flat", WHITE)          # the ČD front logo spot -> GW TRAIN
                return None
            return self.end(ctx, front)
        return None


ROOF_816 = (0x6E, 0x72, 0x76)

M152_ORANGE = dict(
    side_last=9, under=UNDER, green_doors=False,
    lime_k=6, fb0=0.66, fb1=0.785,               # 810 492 photos: green back over the last window
    rk=5, rb0=0.18, rb1=0.105, rear_band=True,   # rear door end: green door, lime rising forward
    wm=(7.5 / 36, 23.5 / 36, 4, WM_BIG),         # side pixels 8..23 of 36: one bitmap column each
    cab_rows=(6, (6,), 7), gang_rows=(6, (6,), 7), rear_is_cab=True, logo=(0.28, 0.72),
    roof=ROOF, cap=0.965,
)


def m152_orange():
    return Scheme(**M152_ORANGE)


def m152_816():
    """816: as the 810 but a dark-grey roof (816 001 / 004 photos)."""
    return Scheme(**dict(M152_ORANGE, roof=ROOF_816))


# ------------------------------------------------------------------ 810 602 "Jarek"
GW_BIG = {   # big black italic "GW" on the rear third of the side, rows k1..k7
    "side": ["...##.#..#.#",
             "..#...#..#.#",
             ".#..#.#.#.#.",
             "#..##.#.#.#.",
             "#...#.##.##.",
             "####..#..#..",
             "............"],
    "diag": [".##.#.#.#",
             "#...#.#.#",
             "#.#.#.#.#",
             "#.#.####.",
             "###.#..#.",
             ".........",
             "........."],
}


def m152_yellow():
    """810 602 "Jarek": GW yellow, black front cap and upper windscreen frame,
    black band along the bottom edge, black GW on the front and a big black
    italic GW on the rear third of the side, light-grey roof."""
    def design(ctx):
        f, k, u, kind = ctx["face"], ctx["k"], ctx["u"], ctx["kind"]
        if kind == K_WSCREEN:
            return None
        if f == F_R:
            if kind != K_PAINT:
                return None
            return BLACK if u >= 0.965 else ROOF
        if f == F_S:
            if kind != K_PAINT:
                return None
            if k >= 9:
                return UNDER
            if k == 8:
                return BLACK
            u0, u1 = 0.07, 0.36
            pat = GW_BIG["side"] if ctx["view"] in SIDE_VIEWS else GW_BIG["diag"]
            if 1 <= k <= 7 and u0 <= u <= u1:
                t = (u - u0) / (u1 - u0)
                if not reads_forward(ctx["view"]):
                    t = 1.0 - t
                if wordmark(pat, t, k - 1):
                    return BLACK
            if k == 5 and 0.58 <= u <= 0.74 and int((u - 0.58) / 0.16 * 6) % 3 != 2:
                return (0x5A, 0x55, 0x3A)            # small "GW TrainRegio" lettering
            return YELLOW
        if f == F_E:
            if kind == K_FIX:
                b = ctx["base"]
                if b[0] > 120 and b[1] > 70 and b[2] < 60 and b[0] - b[2] > 80:
                    return ("flat", BLACK)          # lower front edge
                if k == 6 and 0.28 <= u <= 0.72 and lum(np.array(b, float)) < 60:
                    return ("flat", BLACK)
                return None
            v = u
            if k == 0:
                return BLACK
            if k == 1 and (v < 0.12 or v > 0.88):
                return BLACK
            if k == 6 and 0.3 <= v <= 0.7:
                return BLACK                         # GW logo under the windscreen
            return YELLOW
        return None
    return design


# ------------------------------------------------------------------ 816 roof units
# The roof units are drawn as boxes with railkit's renderer.  The ČD 810
# silhouette matches a railkit box of 6.4 x 1.84 carunits, z 1..11 (29 px
# mismatch per view, from the rounded ends) with the front anchor moved by
# these offsets (fitted per view on the silhouette):
M152_ROOF_Z = 11.0
M152_ANCHOR_OFF = {"w": (1, 3), "nw": (0, 2), "n": (-1, 3), "ne": (-2, 2),
                   "e": (-2, 2), "se": (0, 1), "s": (2, 2), "sw": (2, 2)}
# (u0, u1 carunits behind the cab front, half width, height above the crown,
#  top colour, wall colour): the white Eberspächer A/C unit on the cab roof and
#  the flat light-grey saloon unit a little behind mid-roof (816 001 / 004 photos)
UNITS_816 = [
    (0.30, 1.15, 0.58, 1.5, 0xEEF0F0, 0xC6CACD),
    (2.95, 4.15, 0.50, 0.9, 0xCDD1D4, 0xA4A8AC),
]


def roof_units(row, units):
    """Draw roof boxes over an 810-body row (railkit projection + lighting)."""
    out = row.copy()
    for c, d in enumerate(DIRS):
        ax, ay = R.ANCHOR[d]
        ox, oy = M152_ANCHOR_OFF[d]
        parts = []
        for u0, u1, hw, h, top, wall in units:
            paint = R.Paint(wall, top=top)
            parts.append(R.Part(u0, u1, -hw, hw, M152_ROOF_Z - 0.6, M152_ROOF_Z + h,
                                (lambda p: lambda *a: p)(paint), "unit"))
        img, own = R.render_view(parts, [], d, (ax + ox, ay + oy))
        ys, xs = np.where(own == "unit")
        for y, x in zip(ys, xs):
            out[y, c * 128 + x] = safe(img[y, x])
    return out


# ------------------------------------------------------------------ RegioNova 814.5 + 914.5
REGIONOVA = dict(
    side_last=9, under=UNDER, green_doors=True,
    lime_k=7, rk=5, rear_band=False,
    wm=(0.57, 0.77, 5, WM_SMALL),
    cab_rows=(8, (7,), 9), gang_rows=(1, None, 2), rear_is_cab=False, logo=(0.3, 0.7),
    roof=ROOF, cap=0.975,
)
SCHEME_914 = dict(REGIONOVA, fb0=0.74, fb1=0.90, rb0=0.22, rb1=0.02)   # low-floor door green
SCHEME_814 = dict(REGIONOVA, fb0=0.72, fb1=0.82, rb0=0.17, rb1=0.07)   # doors at both ends


# ------------------------------------------------------------------ turning a car round
# one carunit forward along the new heading, per direction column
REAR_SHIFT = [(-4, -2), (0, -11), (4, -2), (6, 0), (4, 2), (0, 11), (-4, 2), (-6, 0)]


def rearify(a):
    """Front-facing row -> the same car facing backwards (cab at the rear):
    direction columns shifted by 4, moved one carunit forward along the new
    heading, head and tail lamps swapped (as the ČD 814_0 rows 1 / 3)."""
    out = np.zeros_like(a)
    out[:] = T
    for c in range(8):
        src = a[:, ((c + 4) % 8) * 128:((c + 4) % 8 + 1) * 128]
        dx, dy = REAR_SHIFT[c]
        ys, xs = np.where(~np.all(src == TA, axis=-1))
        out[:, c * 128:(c + 1) * 128][ys + dy, xs + dx] = src[ys, xs]
    v = hexv(out)
    out[v == HEAD] = rgb(TAIL)
    out[v == TAIL] = rgb(HEAD)
    return out


# ------------------------------------------------------------------ public API
def rows_810(liv):
    """[810] in `liv` (LIVERIES_810)."""
    b = get_body("810")
    design = {"oranzovozelena": m152_orange, "zlutocerna": m152_yellow}[liv]()
    return [split(paint(b, design))]


def rows_816(liv):
    """[816]: the 810 body in GWTR orange with the dark-grey roof, the white
    Eberspächer A/C unit on the cab roof and the flat saloon unit mid-roof."""
    assert liv in LIVERIES_816
    row = paint(get_body("810"), m152_816())
    return [split(roof_units(row, UNITS_816))]


def rows_814(liv):
    """[914.5 leading, 814.5 trailing, 814.5 leading, 914.5 trailing]."""
    assert liv in LIVERIES_814
    m914 = paint(get_body("914"), Scheme(**SCHEME_914))
    m814 = paint(get_body("814"), Scheme(**SCHEME_814))
    return [split(r) for r in (m914, rearify(m814), m814, rearify(m914))]
