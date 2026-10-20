"""DPO Ostrava Škoda 03T Astra (Inekon LTM 10.08) sheet, patched from TommPa9's
drawing, and the Inekon 01 Trio derived from it.

    python tools/tramrender/dpo_astra.py [--preview DIR]

Reads the frozen upstream sheet tools/tramrender/src/dpo/ltm1008_astra_dpomodrozluta.png
(TommPa9, as extracted from the CZ tram pak), writes
vehicle-tram/dpo/ltm1008_astra/sprites/dpomodrozluta.png, then regenerates the
Trio (vehicle-tram/dpo/t2001_trio) with tools/tramrender/dpo_trio.py, which reads
the Astra sheet from disk: running dpo_trio.py afterwards gives the same Trio.
Change the fixes here and regenerate, never edit the PNGs.

Fixes (audit 2026-10-19; photos on Commons: 03T Astra 1201 left side, 1206 right
side, 1207 from above, 1209 right side; Trio 1258 / 1259):

* Roof equipment boxes: on the photos the containers behind the pantograph, on
  the middle section and on the rear section are dark grey metal (1207 from
  above, 1201 / 1206 against the sky), standing on a light grey roof. TommPa9
  drew them in the roof's light greys. Every box pixel above the cant line
  (box top C5C5C5, faces ADADAD / 9C9C9C, shadow 848484; plus the BDBDBD top
  of the low box by the rear joint, BOX_TOP_EXTRA) is recoloured one-for-one
  into a dark olive-grey ramp (BOX_MAP), so his box shapes and light / shade
  steps stay. The roof plane (B5B5B5, BDBDBD), the far roof edge (8C8C8C), the
  roof caps over the joints (C5C5C5 over 949494, 7B7B7B) and the white A/C
  unit over the cab stay as they are.
  dpo_trio.py places the Trio's light-grey cab fairing (the owner's pick) by
  fractions of the row-0 roof extent, measured on the roof colours (C5C5C5 and
  ADADAD among them). So the front-most and rear-most roof pixels of each
  row-0 view keep a roof colour (a box corner there becomes roof plane
  B5B5B5, 4 px in all): the Trio's fairing lands exactly where it was, and the
  Trio differs from the previous one only where the Astra sheet changed.
* Cab glass: the windscreen and the driver's side window were on the lit-window
  specials 4D4D4D / 57656F, so the cab lit up at night with passengers aboard.
  They are nudged one step off (4D4D4E / 57656E): identical by day, never lit.
  Passenger windows, door glass and the rear window keep the specials. The
  cab regions per view are in CAB (the driver's side window is the first bay
  behind the windscreen, per 1201 left and 1206 right).
* Rear section door: checked against 1206 and 1209 (right side; Olomouc Trio
  205 agrees): the rear section reads, from the tail, narrow window, door,
  wide window, window. The n, ne and e views of row 2 already show exactly
  that (one window bay behind the door), so the door stays where TommPa9 put
  it.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tramkit as tk  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
BASE = os.path.join(HERE, "src", "dpo", "ltm1008_astra_dpomodrozluta.png")
ASTRA = os.path.join(ROOT, "vehicle-tram", "dpo", "ltm1008_astra", "sprites", "dpomodrozluta.png")
TRIO = os.path.join(ROOT, "vehicle-tram", "dpo", "t2001_trio", "sprites", "dpomodrozluta.png")


def hx(h):
    return (h >> 16) & 255, (h >> 8) & 255, h & 255


# TommPa9's light box greys -> dark olive-grey metal, step for step (top lightest).
BOX_MAP = {
    0xC5C5C5: 0x70726C,   # box top
    0xADADAD: 0x5E605A,   # lit side face
    0x9C9C9C: 0x51534D,   # shaded face
    0x848484: 0x41433D,   # shadow side
}
# The lower box next to the joint on the rear section has a BDBDBD top in the
# ne / sw / se / nw views (its sides are box colours); those pixels, per
# (row, col), get the dark box top too.
BOX_TOP_EXTRA = {
    (2, 3): [(78, 80), (79, 80), (78, 81), (79, 81)],
    (2, 7): [(42, 80), (43, 80), (42, 81), (43, 81)],
    (2, 5): [(x, 86) for x in range(60, 67)],
    (2, 1): [(x, 60) for x in range(60, 67)],
}
# Colours that start the car body below the roof in a pixel column (cant, window
# band, doors, lower body): box colours under them are body, not roof.
STOP = {0x4284C5, 0x4D4D4D, 0x57656F, 0xFFCE08, 0xE6E6E6, 0xD6D6D6, 0xEFEFEF,
        0xF7F7F7, 0xCECECE, 0x006BD6, 0x52ADFF, 0x84BDFF, 0x5AADFF}
# Row-0 white A/C unit over the cab (dpo_trio.AC_BOX): never a box, never a stop.
AC_BOX = {0: (44, 73, 49, 77), 1: (62, 60, 65, 62), 2: (79, 73, 82, 77), 3: (75, 80, 80, 84),
          4: (69, 86, 75, 90), 5: (62, 86, 65, 90), 6: (53, 86, 59, 90), 7: (40, 80, 45, 84)}

# Cab glass per row-0 view, (x0, y0, x1, y1) exclusive: the driver's side window
# (left side w / s / sw: the first bay behind the windscreen; right side n / ne /
# e: the bay between the front door and the windscreen) and the windscreen
# (front face, se / e / s, and its edge in ne / sw).
CAB = {
    0: [(41, 77, 43, 86)],
    2: [(85, 77, 87, 87)],
    3: [(76, 85, 80, 95), (81, 82, 83, 94)],
    4: [(68, 89, 70, 99), (71, 90, 79, 101)],
    5: [(59, 90, 68, 100)],
    6: [(49, 90, 57, 100), (58, 89, 60, 99)],
    7: [(37, 82, 39, 94), (40, 86, 44, 95)],
}
PLAIN = {0x4D4D4D: 0x4D4D4E, 0x57656F: 0x57656E}


def hexarr(t):
    t = t.astype(np.int64)
    return (t[..., 0] << 16) | (t[..., 1] << 8) | t[..., 2]


def box_mask(t, row, col):
    v = hexarr(t)
    cand = np.isin(v, list(BOX_MAP))
    stop = np.isin(v, list(STOP))
    if row == 0:
        x0, y0, x1, y1 = AC_BOX[col]
        cand[y0:y1, x0:x1] = False
        stop[y0:y1, x0:x1] = False
    for x in range(128):
        ys = np.nonzero(stop[:, x])[0]
        if len(ys):
            cand[ys[0]:, x] = False
    # Lone 2-3 px runs at the ends of the roof are the roof caps over the
    # joints (C5C5C5 above the 949494 gangway roof), not boxes.
    cand = _drop_small(cand, 3)
    if row == 0:
        cand &= ~_roof_ends(t, col)
    return cand


# dpo_trio.py places the Trio's cab fairing by fractions of the row-0 roof
# extent, the roof being every pixel in these colours (dpo_trio.ROOF_COLS).
TRIO_ROOF = {0xB5B5B5, 0xBDBDBD, 0xC5C5C5, 0xADADAD}


def _roof_ends(t, col):
    """The row-0 roof pixels at the front-most and rear-most position along
    the car. They keep their colour so dpo_trio.py measures the same roof
    extent and lands the Trio's fairing where it was (the rear-most one is a
    corner pixel of the box behind the pantograph in the w / e / s views)."""
    v = hexarr(t)
    roof = np.isin(v, list(TRIO_ROOF))
    ys, xs = np.nonzero(roof)
    du = np.array(tk.PER_CU[tk.DIRS[col]], float)
    du /= np.linalg.norm(du)
    s = xs * du[0] + ys * du[1]
    keep = np.zeros(t.shape[:2], bool)
    ends = np.isclose(s, s.min()) | np.isclose(s, s.max())
    keep[ys[ends], xs[ends]] = True
    return keep


def _drop_small(m, nmax):
    seen = np.zeros_like(m)
    out = m.copy()
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        stack, pts = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            pts.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < 128 and 0 <= nx < 128 and m[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        if len(pts) <= nmax:
            for cy, cx in pts:
                out[cy, cx] = False
    return out


def darken_boxes(t, row, col):
    m = box_mask(t, row, col)
    v = hexarr(t)
    if row == 0:
        # a box corner that is also the end of the roof becomes roof plane
        ends = _roof_ends(t, col) & np.isin(v, list(BOX_MAP))
        t[ends] = hx(0xB5B5B5)
    for src, dst in BOX_MAP.items():
        sel = m & (v == src)
        t[sel] = tk.safe(hx(dst))
    for x, y in BOX_TOP_EXTRA.get((row, col), []):
        assert v[y, x] == 0xBDBDBD, (row, col, x, y)
        t[y, x] = tk.safe(hx(BOX_MAP[0xC5C5C5]))


def plain_cab(t, col):
    v = hexarr(t)
    for x0, y0, x1, y1 in CAB.get(col, []):
        for src, dst in PLAIN.items():
            sub = v[y0:y1, x0:x1] == src
            t[y0:y1, x0:x1][sub] = hx(dst)


def build():
    sh = tk.load(BASE).copy()
    for row in range(3):
        for col in range(8):
            t = tk.tile(sh, row, col)
            darken_boxes(t, row, col)
            if row == 0:
                plain_cab(t, col)
    return sh


def build_trio(astra_path=ASTRA):
    """The Trio from the Astra sheet at astra_path (default: the one build()
    wrote), exactly as `python tools/tramrender/dpo_trio.py` makes it."""
    import dpo_trio  # noqa: E402
    keep = dpo_trio.ASTRA
    dpo_trio.ASTRA = astra_path
    try:
        return dpo_trio.build("A")
    finally:
        dpo_trio.ASTRA = keep


# ------------------------------------------------------------------ preview
def _strip(sh, row, z):
    cells = []
    for c in range(8):
        cell = tk._on_grass(tk.tile(sh, row, c), row * 8 + c)
        im = Image.fromarray(cell)
        cells.append(im.resize((128 * z, 128 * z), Image.NEAREST) if z > 1 else im)
    w = sum(c.width for c in cells)
    out = Image.new("RGB", (w, cells[0].height))
    x = 0
    for c in cells:
        out.paste(c, (x, 0)); x += c.width
    return out


def preview(pairs, out, crop=(34, 56, 94, 106)):
    """pairs: [(label, before, after)]; each row at 1x and 4x, before above after.
    The 4x strips show only the crop window of each tile."""
    x0, y0, x1, y1 = crop
    blocks = []
    for label, before, after in pairs:
        for row in range(before.shape[0] // 128):
            for tag, sh in (("before", before), ("after", after)):
                one = _strip(sh, row, 1)
                cr = np.concatenate([tk._on_grass(tk.tile(sh, row, c), row * 8 + c)[y0:y1, x0:x1]
                                     for c in range(8)], axis=1)
                four = Image.fromarray(cr).resize((cr.shape[1] * 4, cr.shape[0] * 4), Image.NEAREST)
                blocks.append((f"{label} row {row} {tag}  (1x full tiles; 4x crop x{x0}-{x1} y{y0}-{y1}; "
                               f"views w nw n ne e se s sw)", one, four))
    W = max(max(b[1].width, b[2].width) for b in blocks)
    H = sum(14 + b[1].height + b[2].height + 8 for b in blocks)
    img = Image.new("RGB", (W, H), (250, 250, 250))
    dr = ImageDraw.Draw(img)
    y = 0
    for lab, one, four in blocks:
        dr.text((4, y + 1), lab, fill=(0, 0, 0)); y += 14
        img.paste(one, (0, y)); y += one.height
        img.paste(four, (0, y)); y += four.height + 8
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", help="directory for before/after previews")
    a = ap.parse_args()
    sh = build()
    tk.save(sh, ASTRA)
    print("wrote", os.path.relpath(ASTRA, ROOT))
    trio = build_trio()
    tk.save(trio, TRIO)
    print("wrote", os.path.relpath(TRIO, ROOT))
    if a.preview:
        base = tk.load(BASE)
        old_trio = build_trio(BASE)     # the Trio as it was, from the unpatched Astra
        print("preview", preview([("Astra", base, sh)], os.path.join(a.preview, "astra_before_after.png")))
        print("preview", preview([("Trio", old_trio, trio)], os.path.join(a.preview, "trio_before_after.png")))


if __name__ == "__main__":
    main()
