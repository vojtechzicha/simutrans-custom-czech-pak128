"""Map every pixel of a diagonal view (w, n, e, s) of a pak128 vehicle sprite onto
the pure views it is a sheared copy of.

In pak128 all heights are drawn vertically at the same scale in every view, so the
visible side face of a diagonal view is the pure side view (ne / sw) sheared by
slope +-0.5 and compressed horizontally by 4 / 5.66, and the visible end face is
the pure end view (nw = rear, se = front) sheared the other way. The two offsets
of each map are fitted by matching colour features of all reference liveries.

Column order: 0 w, 1 nw, 2 n, 3 ne, 4 e, 5 se, 6 s, 7 sw.
"""
import numpy as np

T = np.array((231, 255, 255))
SIDE_SRC = {0: 7, 2: 3, 4: 3, 6: 7}
END_SRC = {0: 1, 2: 1, 4: 5, 6: 5}
SIDE_SLOPE = {0: 0.5, 2: -0.5, 4: 0.5, 6: -0.5}
SCALE = 5.657 / 4.0
GLASS = (0x4D4D4D, 0x57656F)


def tile(refs, col):
    """[n,128,128,3] int array of one direction column of every reference."""
    return refs[:, :, col * 128:(col + 1) * 128]


def features(t):
    """Shading-robust per-pixel features of [n,128,128,3] reference tiles."""
    t = t.astype(float)
    lum = 0.299 * t[..., 0] + 0.587 * t[..., 1] + 0.114 * t[..., 2]
    chroma = (t - lum[..., None]) / (lum[..., None] + 25.0) * 60.0
    v = (t[..., 0].astype(int) << 16) | (t[..., 1].astype(int) << 8) | t[..., 2].astype(int)
    glass = np.isin(v, GLASS).astype(float) * 40.0
    dark = (lum < 70).astype(float) * 15.0
    bright = (lum > 200).astype(float) * 15.0
    f = np.concatenate([chroma, glass[..., None], dark[..., None], bright[..., None]], axis=-1)
    return np.moveaxis(f, 0, 2).reshape(128, 128, -1)   # [128,128,n*6]


def body_mask(t):
    return ~np.all(t[0] == T, axis=-1)


def apply(xs, ys, s, slope, bx, by):
    """Source coordinates for diagonal pixels (xs, ys)."""
    sx = np.rint(s * xs + bx).astype(int)
    sy = np.rint(ys - slope * xs + by).astype(int)
    return sx, sy


def fit(fd, md, fs, ms, slope, pts, keep=0.6, s_range=(1.36, 1.47), bx_range=None, by_range=(-40, 41)):
    """Best (s, bx, by) mapping diagonal pixels `pts` onto the source view.
    Score: trimmed mean feature distance (the best `keep` fraction of the
    points whose source is a body pixel), penalising low coverage."""
    ys, xs = pts
    best = (1e18, None)
    for s in np.arange(s_range[0], s_range[1] + 1e-9, 0.01):
        bxr = bx_range if bx_range is not None else (int(-s * 128) - 10, 128 + 10)
        for bx in range(*bxr):
            sx0 = s * xs + bx
            okx = (sx0 >= -0.5) & (sx0 < 127.5)
            if okx.mean() < 0.3:
                continue
            for by in range(*by_range):
                sx, sy = apply(xs, ys, s, slope, bx, by)
                ok = (sx >= 0) & (sx < 128) & (sy >= 0) & (sy < 128)
                ok[ok] &= ms[sy[ok], sx[ok]]
                n = ok.sum()
                if n < keep * len(xs):
                    continue
                d = np.abs(fd[ys[ok], xs[ok]] - fs[sy[ok], sx[ok]]).sum(axis=1)
                k = int(keep * len(xs))
                sc = np.partition(d, k - 1)[:k].mean()
                if sc < best[0]:
                    best = (sc, (s, bx, by))
    return best


def fit_view(refs, col, end_top, verbose=False):
    """-> dict with side / end maps and per-pixel assignment for diagonal col."""
    td = tile(refs, col)
    fd, md = features(td), body_mask(td)
    out = {}
    ys, xs = np.where(md)
    msrc = body_mask(tile(refs, SIDE_SRC[col]))
    sys_, sxs_ = np.where(msrc)
    cxd, cyd = (xs.min() + xs.max()) / 2, ys.mean()
    cxs, cys = (sxs_.min() + sxs_.max()) / 2, sys_.mean()
    bx0 = int(round(cxs - SCALE * cxd)); by0 = int(round(cys - (cyd - SIDE_SLOPE[col] * cxd)))
    sc_side, (s, bx, by) = fit(fd, md, features(tile(refs, SIDE_SRC[col])), msrc,
                               SIDE_SLOPE[col], (ys, xs), keep=0.6,
                               bx_range=(bx0 - 30, bx0 + 31), by_range=(by0 - 25, by0 + 26))
    out["side"] = (s, bx, by, sc_side)
    fs, ms = features(tile(refs, SIDE_SRC[col])), body_mask(tile(refs, SIDE_SRC[col]))
    sx, sy = apply(xs, ys, s, SIDE_SLOPE[col], bx, by)
    ok = (sx >= 0) & (sx < 128) & (sy >= 0) & (sy < 128)
    ok[ok] &= ms[sy[ok], sx[ok]]
    dside = np.full(len(xs), 1e9)
    dside[ok] = np.abs(fd[ys[ok], xs[ok]] - fs[sy[ok], sx[ok]]).sum(axis=1)
    # end face: fit on the points the side map explains worst / not at all
    fe, me = features(tile(refs, END_SRC[col])), body_mask(tile(refs, END_SRC[col]))
    me[:end_top[END_SRC[col]]] = False          # the end face proper, not the roof behind it
    thr = np.percentile(dside[ok], 80) if ok.any() else 0
    cand = (~ok) | (dside > thr)
    ce = (ys[cand], xs[cand])
    eys, exs = np.where(me)
    cxe, cye = (exs.min() + exs.max()) / 2, eys.mean()
    # the visible end face sits at one x-extreme of the diagonal body:
    # w, e -> right end; n, s -> left end
    right = col in (0, 4)
    xext = xs.max() - 4 if right else xs.min() + 4
    bxe0 = int(round(cxe - SCALE * xext))
    sel = (xs >= xs.max() - 14) if right else (xs <= xs.min() + 14)
    sel &= (~ok) | (dside > thr)
    ce = (ys[sel], xs[sel])
    yce = ys[sel].mean(); xce = xs[sel].mean()
    bye0 = int(round(cye - (yce + SIDE_SLOPE[col] * xce)))
    sc_end, (se, bxe, bye) = fit(fd, md, fe, me, -SIDE_SLOPE[col], ce, keep=0.4,
                                 s_range=(1.30, 1.52), bx_range=(bxe0 - 14, bxe0 + 15),
                                 by_range=(bye0 - 30, bye0 + 31))
    out["end"] = (se, bxe, bye, sc_end)
    if verbose:
        print(f"col {col}: side s={s:.2f} bx={bx} by={by} score={sc_side:.1f} | end s={se:.2f} bx={bxe} by={bye} score={sc_end:.1f}")
    return out


def source_maps(refs, col, fitres, end_top):
    """Per diagonal pixel: side-source (x,y) and end-source (x,y) (or -1), and
    the feature distance of each (1e9 if the source is not a body pixel)."""
    td = tile(refs, col)
    fd, md = features(td), body_mask(td)
    ys, xs = np.where(md)
    res = {}
    for face, src, slope in (("side", SIDE_SRC[col], SIDE_SLOPE[col]), ("end", END_SRC[col], -SIDE_SLOPE[col])):
        s, bx, by, _ = fitres[face]
        ts = tile(refs, src)
        fs, ms = features(ts), body_mask(ts)
        if face == "end":
            ms[:end_top[src]] = False
        sx, sy = apply(xs, ys, s, slope, bx, by)
        inb = (sx >= 0) & (sx < 128) & (sy >= 0) & (sy < 128)
        ok = inb.copy()
        ok[ok] &= ms[sy[ok], sx[ok]]
        d = np.full(len(xs), 1e9)
        d[ok] = np.abs(fd[ys[ok], xs[ok]] - fs[sy[ok], sx[ok]]).sum(axis=1)
        res[face] = (sx, sy, ok, d, inb)
    return (ys, xs), res
