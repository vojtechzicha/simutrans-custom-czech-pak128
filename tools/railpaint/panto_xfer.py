"""Pantograph transplant: give a Panter "B" car (cab at the rear) the
pantograph of the "A" drawing at its inner end.

B seen in view c is the A body turned 180 degrees, i.e. A seen in view
(c + 4) % 8, shifted along the track (a 13-carunit car sits off-centre, and
the offset flips with the direction). For every view the shift is fitted on
the silhouettes, and the A pixels that stick out ABOVE B's silhouette (the
pantograph arms) are copied onto B.
"""
import numpy as np

T = np.array((231, 255, 255))


def _mask(t):
    return ~np.all(t == T, axis=-1)


def fit(ma, mb, rx=44, ry=24):
    best = None
    ys, xs = np.where(ma)
    for dy in range(-ry, ry + 1):
        for dx in range(-rx, rx + 1):
            y2, x2 = ys + dy, xs + dx
            ok = (y2 >= 0) & (y2 < 128) & (x2 >= 0) & (x2 < 128)
            hit = mb[y2[ok], x2[ok]].sum()
            s = hit * 2 - ok.sum() - mb.sum()
            if best is None or s > best[0]:
                best = (s, dx, dy)
    return best[1], best[2]


def transplant(a_row, b_row, margin=1):
    """a_row, b_row: [128, 1024, 3] painted rows of the A and B cars.
    Returns b_row with A's pantograph pixels added (views fitted per column)."""
    out = b_row.copy()
    for c in range(8):
        ca = (c + 4) % 8
        ta = a_row[:, ca * 128:(ca + 1) * 128]
        tb = out[:, c * 128:(c + 1) * 128]
        ma, mb = _mask(ta), _mask(tb)
        dx, dy = fit(ma, mb)
        top_b = np.where(mb.any(axis=0), mb.argmax(axis=0), 128)
        ys, xs = np.where(ma)
        moved = []
        for y, x in zip(ys, xs):
            y2, x2 = y + dy, x + dx
            if not (0 <= y2 < 128 and 0 <= x2 < 128):
                continue
            if mb[y2, x2]:
                continue
            if y2 >= top_b[x2] - margin + 1 and top_b[x2] < 128:
                continue          # not above B's roof in that column
            tb[y2, x2] = ta[y, x]
            moved.append((y2, x2))
        if not moved:
            continue
        # the arms' black lines where they cross the roof (base, lower arm):
        # black A pixels next to the transplanted ones
        my, mx = np.array(moved).T
        y0, y1, x0, x1 = my.min() - 3, my.max() + 6, mx.min() - 3, mx.max() + 3
        for y, x in zip(ys, xs):
            y2, x2 = y + dy, x + dx
            if not (y0 <= y2 <= y1 and x0 <= x2 <= x1 and 0 <= y2 < 128 and 0 <= x2 < 128):
                continue
            if mb[y2, x2] and max(ta[y, x]) < 36:
                tb[y2, x2] = ta[y, x]
    return out
