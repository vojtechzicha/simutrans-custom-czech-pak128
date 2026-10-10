"""Put the DP Ostrava buses and trolleybuses at the native position along the road.

The DPO sheets came from several upstream artists and sat up to 14 px ahead
of or behind the native pak128.cs 12 m buses in some views (sideways they
were already on the lane). In game a bus jumped when it turned onto a
diagonal. This script moves every view of every DPO bus/trolleybus sheet
along the direction of travel only, so that the lead section's body centre
lands where the length rule puts it (CLAUDE.md, "Section placement"):

    centre = native 12 m centre (rj_lane.MEDIAN) + (4 - L/2) carunits forward

with L the lead section's drawn length in carunits, measured in the ne and sw
views against the native 12 m bus (VZ DPP SOR NB 12, on the native median,
length 8). Many DPO families keep the default `length: 8` in family.yaml even
where the bus is shorter, so the drawing, not the yaml, sets L: a short bus
keeps its own length and has its front where a 12 m bus has its front. All rows of a
sheet (the sections of an articulated bus) move by the lead section's shift,
which keeps the joints. Nothing moves sideways, so trolleybus poles stay on
the wire. Shifts under 2 px are left alone; running the script again changes
nothing.

usage: python tools/busrender/dpo_lane.py [--dry-run] [family ...]
Run it after tools/busrender/dpo_derived.py, which builds two DPO sheets from
others.
"""
import argparse
import glob
import os
import sys

import numpy as np
import yaml
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from rj_lane import metrics, MEDIAN  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = np.array([231, 255, 255])
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
# screen px per carunit of travel, as (x, y) of the direction of travel
STEP = {"w": (-4, -2), "e": (4, 2), "n": (4, -2), "s": (-4, 2),
        "ne": (5.66, 0), "sw": (-5.66, 0), "nw": (0, -2.83), "se": (0, 2.83)}
MIN_SHIFT = 2
REF = os.path.join(ROOT, "vehicle-bus/dpp/sor_nb_12/sprites/pidsedocervena.png")


def body_mask(tile):
    from scipy import ndimage
    m = ~np.all(tile == T, axis=2)
    mo = ndimage.binary_opening(m, structure=np.ones((3, 3)))     # drop poles, mirrors
    lab, n = ndimage.label(mo)
    if n == 0:
        return mo
    sizes = ndimage.sum(mo, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def x_extent(tile):
    xs = np.where(body_mask(tile).any(axis=0))[0]
    return xs.max() - xs.min() + 1


def drawn_length(sheet, row):
    """Lead section length in carunits from its ne / sw width against the reference."""
    ref = np.array(Image.open(REF).convert("RGB"))[:128]
    out = []
    for d in ("ne", "sw"):
        i = DIRS.index(d)
        t = sheet[row * 128:(row + 1) * 128, i * 128:(i + 1) * 128]
        r = ref[:, i * 128:(i + 1) * 128]
        out.append(8 + (x_extent(t) - x_extent(r)) / 5.66)
    return sum(out) / 2


def families(names):
    out = []
    for root in ("vehicle-bus/dpo", "vehicle-trolleybus/dpo"):
        for fy in sorted(glob.glob(os.path.join(ROOT, root, "*", "family.yaml"))):
            fam = os.path.basename(os.path.dirname(fy))
            if not names or fam in names:
                out.append(fy)
    return out


def shift_tile(tile, dx, dy):
    out = np.empty_like(tile)
    out[:] = T
    m = ~np.all(tile == T, axis=2)
    ys, xs = np.where(m)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < 128) & (nx >= 0) & (nx < 128)
    if not ok.all():
        raise SystemExit(f"shift ({dx},{dy}) pushes {int((~ok).sum())} px off the tile")
    out[ny, nx] = tile[ys, xs]
    return out


def view_shift(tile, d, length):
    """(dx, dy) that puts the body centre of `tile` at the length-rule target."""
    X, C = metrics(tile, d)
    mx, mc = MEDIAN[d]
    sx, sy = STEP[d]
    ahead = 4 - length / 2                     # carunits forward of the 12 m centre
    if d in ("nw", "se"):                      # vertical travel: C is the y centre
        dy = (mc + ahead * sy) - C
        dx = 0.0
    else:                                      # X is the x centre; y follows the road slope
        dx = (mx + ahead * sx) - X
        dy = dx * sy / sx
    dx, dy = int(round(dx)), int(round(dy))
    if max(abs(dx), abs(dy)) < MIN_SHIFT:
        return 0, 0
    return dx, dy


def process(fy, dry):
    fam = yaml.safe_load(open(fy, encoding="utf-8"))
    lead = fam["vehicles"][0]
    yaml_len = lead["fields"].get("length", 8)
    lead_row = lead.get("row", 0)
    name = os.path.basename(os.path.dirname(fy))
    for png in sorted(glob.glob(os.path.join(os.path.dirname(fy), "sprites", "*.png"))):
        a = np.array(Image.open(png).convert("RGB"))
        rows = a.shape[0] // 128
        length = drawn_length(a, lead_row)
        shifts = []
        for i, d in enumerate(DIRS):
            lead_tile = a[lead_row * 128:(lead_row + 1) * 128, i * 128:(i + 1) * 128]
            dx, dy = view_shift(lead_tile, d, length)
            shifts.append((d, dx, dy))
            if (dx, dy) != (0, 0):
                for r in range(rows):
                    sl = (slice(r * 128, (r + 1) * 128), slice(i * 128, (i + 1) * 128))
                    a[sl] = shift_tile(a[sl], dx, dy)
        moved = [f"{d}{dx:+d},{dy:+d}" for d, dx, dy in shifts if (dx, dy) != (0, 0)]
        print(f"{name:28s} L={length:4.1f} (yaml {yaml_len:<2}) {os.path.basename(png):22s} {' '.join(moved) or 'ok'}")
        if moved and not dry:
            Image.fromarray(a).save(png, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("families", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for fy in families(args.families):
        process(fy, args.dry_run)


if __name__ == "__main__":
    main()
