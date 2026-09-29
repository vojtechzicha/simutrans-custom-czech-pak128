"""Fit the water-lane origin of the native pak128.cs small ferries: the screen
position of the hull centre at the waterline, per view, found by sliding a box
hull silhouette (L x B x 1.2 m at the render.py scale) over the extracted
sprite and keeping the offset that covers the most sprite pixels.

The inputs in src/ are rows extracted with tools/pak_extract.py from
pak128.cs vehicles.ships-ferries.pak (Ferry_yeu_128set) and
vehicle.Veveri_ship_128set.pak. The two agree within 1-2 px; boatkit.ORIGINS
is their mean.

usage: python tools/shiprender/fitlane.py
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "busrender"))
import render as R  # noqa: E402

KEY = [231, 255, 255]


def sil(path):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    return [np.abs(a[:, c * 128:(c + 1) * 128] - KEY).sum(2) > 0 for c in range(8)]


def hull_mask(view, L, B, hz):
    boxes = [R.Box("h", 0, L, -B / 2, B / 2, 0, hz)]
    img, _ = R.render(view, boxes, lambda p: (0, 0, 0), L, (64, 96))
    return np.abs(img.astype(int) - KEY).sum(2) > 0


def fit(path, L, B, hz):
    ss = sil(path)
    res = {}
    for c, d in enumerate(R.DIRS):
        ys, xs = np.nonzero(hull_mask(d, L, B, hz))
        tgt = ss[c]
        best = None
        for dx in range(-30, 31):
            for dy in range(-30, 31):
                yy, xx = ys + dy, xs + dx
                ok = (yy >= 0) & (yy < 128) & (xx >= 0) & (xx < 128)
                hit = tgt[yy[ok], xx[ok]].sum()
                if best is None or hit > best[0]:
                    best = (hit, dx, dy)
        res[d] = (64 + best[1], 96 + best[2], best[0], len(ys))
    return res


if __name__ == "__main__":
    # effective hull size of each native at the render.py scale (side-view length, end-view width)
    for f, L, B in [("Ferry_yeu_128set.png", 14.6, 4.2), ("Veveri_ship_128set.png", 15.0, 4.0)]:
        print(f)
        for d, v in fit(os.path.join(HERE, "src", f), L, B, 1.2).items():
            print("  %-2s origin (%d,%d) hit %d/%d" % (d, *v))
