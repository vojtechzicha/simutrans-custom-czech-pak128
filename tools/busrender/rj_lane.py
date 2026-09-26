"""Lane placement normaliser: shift each direction tile so the vehicle body's
bbox centre (poles removed by morphological opening) matches the median of
native pak128.cs 12 m buses/trolleybuses (measured from compiled paks: Man Lions
City, Mercedes Citaro, SMC H-98, Škoda 21Tr/24Tr, CZR Urbanway/SOR NB/NBG/Citelis/
Crossway/26Tr/32Tr).

usage: rj_lane.py in.png out.png [--threshold 2] [--report]
"""
import sys, os
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
from rj_buscommon import *

# Height-independent footprint metrics (X = body x-centre, C = lower-edge
# intercept along the road slope; vertical views: C = y-centre), median of core
# native pak128.cs 12 m vehicles. Natives agree on C within +-2 px.
MEDIAN = {"w": (57.2, 57.5), "nw": (73.0, 81.2), "n": (83.2, 139.0), "ne": (65.2, 105.5),
          "e": (45.2, 74.0), "se": (50.0, 83.0), "s": (65.5, 120.5), "sw": (64.5, 92.0)}
SLOPE = {"w": 0.5, "e": 0.5, "n": -0.5, "s": -0.5, "ne": 0.0, "sw": 0.0}


def metrics(tile, d):
    m = ~np.all(tile == np.array(T), axis=2)
    mo = ndimage.binary_opening(m, structure=np.ones((3, 3)))
    lab, n = ndimage.label(mo)
    sizes = ndimage.sum(mo, lab, range(1, n + 1))
    big = lab == (1 + int(np.argmax(sizes)))
    ys, xs = np.where(big)
    X = (xs.min() + xs.max()) / 2
    if d in SLOPE:
        cs = [np.where(big[:, x])[0].max() - SLOPE[d] * x
              for x in range(xs.min(), xs.max() + 1) if big[:, x].any()]
        C = float(np.median(cs))
    else:
        C = (ys.min() + ys.max()) / 2
    return X, C


def shift_for(tile, d, lat_thr=2, lon_thr=4):
    X, C = metrics(tile, d)
    mx, mc = MEDIAN[d]
    if d in ("nw", "se"):
        dx = int(round(mx - X)) if abs(mx - X) >= lat_thr else 0
        dy = int(round(mc - C)) if abs(mc - C) >= lon_thr else 0
        return dx, dy, X, C
    dx = int(round(mx - X)) if abs(mx - X) >= lon_thr else 0
    # C' = C + dy - slope*dx  ->  choose dy so that C' ~ mc
    need = mc - (C - SLOPE[d] * dx)
    dy = int(round(need)) if abs(need) >= lat_thr else 0
    return dx, dy, X, C


def shift_tile(tile, dx, dy):
    out = np.zeros_like(tile); out[:, :] = T
    m = ~np.all(tile == np.array(T), axis=2)
    ys, xs = np.where(m)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
    if not ok.all():
        raise ValueError(f"shift ({dx},{dy}) pushes pixels out of the tile")
    out[ny, nx] = tile[ys, xs]
    return out


def normalize_rows(rows, threshold=2, report=True, label=""):
    out = []
    for r, tiles in enumerate(rows):
        nt = []
        for c, d in enumerate(DIRS):
            dx, dy, X, C = shift_for(tiles[c], d, lat_thr=threshold)
            if report and (dx or dy):
                print(f"  {label} row{r} {d:2s}: X={X:.1f} C={C:.1f} (median {MEDIAN[d]}) -> shift ({dx:+d},{dy:+d})")
            nt.append(shift_tile(tiles[c], dx, dy) if (dx or dy) else tiles[c].copy())
        out.append(nt)
    return out


def load_all_rows(path):
    im = np.array(Image.open(path).convert("RGB"))
    n = im.shape[0] // 128
    return [load_row(path, r) for r in range(n)]


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    thr = 2
    if "--threshold" in sys.argv:
        thr = float(sys.argv[sys.argv.index("--threshold") + 1])
    rows = load_all_rows(src)
    rows = normalize_rows(rows, thr, True, os.path.basename(src))
    save_rows(rows, dst)
