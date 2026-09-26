"""Helpers that apply the agreed 2026-09-26 render style (style.py) to models
written before it, without changing those models' default output.

- restyle_lines(lines): pantograph arms -> style.PANTO_ARM (1 px), collector
  head bars -> style.PANTO_HEAD (2 px).
- gutter(mat, is_roof_side): wrap a material so the roof slab's side faces
  become the dark style.GUTTER line instead of a light rim.
- save_styled(rows, path): save the sheet, then run style.polish(**POLISH).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
import style as S  # noqa: E402

GUTTER = Paint(S.GUTTER, top=S.GUTTER)


def restyle_lines(lines):
    """Recolour pantograph lines: a bar running across v is the collector head."""
    out = []
    for ln in lines:
        a, b, col, own = ln[:4]
        if abs(a[1] - b[1]) > 1e-6 and abs(a[0] - b[0]) < 1e-6:
            out.append((a, b, S.PANTO_HEAD, own, True))
        else:
            out.append((a, b, S.PANTO_ARM, own, False))
    return out


def gutter(mat, is_roof_side):
    """Material wrapper: `is_roof_side(f, u, v, z, d)` -> paint the dark gutter."""
    def m(f, u, v, z, d):
        if f != "+z" and is_roof_side(f, u, v, z, d):
            return GUTTER
        return mat(f, u, v, z, d)
    m.__name__ = getattr(mat, "__name__", "mat")
    return m


def save_styled(rows, path):
    R.save_rows(rows, path)
    im = Image.open(path)
    im.load()
    S.polish(im.copy(), **S.POLISH).save(path)


def roof_restyle(parts, zs, zr, eps=1e-6):
    """Generic box-loco roof pass: the side faces of every part that starts at the
    side top `zs` and ends at the roof `zr` (the roof cap) become the gutter, and
    the exposed top ledge of parts ending at `zs` (the strip between the wall and
    an inset roof cap) too, so no light rim is left where roof meets body."""
    for p in parts:
        z0, z1 = p.b[4], p.b[5]
        if abs(z0 - zs) < eps and abs(z1 - zr) < eps:
            p.mat = gutter(p.mat, lambda f, u, v, z, d: True)
        elif abs(z1 - zs) < eps:
            m0 = p.mat

            def m(f, u, v, z, d, m0=m0):
                if f == "+z" and z >= zs - 0.05:
                    return GUTTER
                return m0(f, u, v, z, d)
            m.__name__ = getattr(m0, "__name__", "mat")
            p.mat = m
    return parts
