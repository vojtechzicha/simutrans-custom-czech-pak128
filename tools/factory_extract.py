#!/usr/bin/env python3
"""Extract a factory's building from a compiled pak as an industry sheet.

Writes the sheet in build.py's industry layout, so an upstream city factory can
be ported 1:1 into an ``industry.yaml`` set:

  - back images: row = season * 4 + layout, column = tile y * w + x of that
    layout (the odd layouts swap the dims);
  - front images (only with ``--front``): row = 8 + (season * 4 + layout) *
    tiles + tile, column = animation phase.

Front images may hang over their tile (a roof sign), so they are pasted
``--front-offset X Y`` pixels up-left of their true place; the industry.yaml
object gives build.py the same offset (``front: {offset: [X, Y]}``) and makeobj
adds it back. It also prints the factory's data in industry.yaml terms.

Usage:
    python tools/factory_extract.py <pak> <factory name> <out.png> [--front-offset X Y]
"""

import argparse
import struct
import sys
from pathlib import Path

from PIL import Image

from pak_extract import TRANSPARENT, decode_img, parse_pak

TILE = 128
LAYOUTS = 4
SITES = {0: "land", 1: "water", 2: "city", 3: "shore", 4: "river"}


def u16(data: bytes, pos: int) -> int:
    return struct.unpack_from("<H", data, pos)[0]


def factories(node):
    if node.type == "FACT":
        yield node
    for c in node.children:
        yield from factories(c)


def text(node) -> str:
    return node.data.split(b"\0")[0].decode("latin-1")


def building_name(fact) -> str:
    buil = next(c for c in fact.children if c.type == "BUIL")
    return text(next(c for c in buil.children if c.type == "TEXT"))


def factory_fields(fact) -> dict:
    """factory_reader.cc, node versions 3-5 (the fields they share)."""
    d = fact.data
    assert u16(d, 0) & 0x7FFF in (3, 4, 5), "unsupported factory node version"
    pax_boost, mail_boost = u16(d, 28), u16(d, 30)
    return {
        "location": SITES[u16(d, 2)], "productivity": u16(d, 4), "range": u16(d, 6),
        "distributionweight": u16(d, 8), "mapcolor": d[10],
        # makeobj stores the boosts as boost * 256 / 1000
        "passenger_boost (pak)": pax_boost, "mail_boost (pak)": mail_boost,
        "passenger_demand": u16(d, 34), "mail_demand": u16(d, 36),
    }


def goods(fact) -> list:
    out = []
    for c in fact.children:
        if c.type == "FSUP":
            ref = next(x for x in c.children if x.type == "XREF")
            capacity, suppliers, consumption = (u16(c.data, i) for i in (0, 2, 4))
            # makeobj stores the input factor (percent) as factor * 256 / 100
            out.append({"good": ref.data[5:].split(b"\0")[0].decode("latin-1"), "capacity": capacity,
                        "suppliers": suppliers, "consumption (pak)": consumption})
    return out


def paste(sheet: Image.Image, img, row: int, col: int, dx: int = 0, dy: int = 0) -> None:
    x, y, w, h, grid = img
    x, y = x - dx, y - dy
    assert 0 <= x and 0 <= y and x + w <= TILE and y + h <= TILE, f"image at {x},{y} {w}x{h} leaves its cell"
    for j, line in enumerate(grid):
        for i, px in enumerate(line):
            if px != TRANSPARENT:
                assert px[3] == 255, "semi-transparent pixel"
                sheet.putpixel((col * TILE + x + i, row * TILE + y + j), px)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pak", type=Path)
    ap.add_argument("name")
    ap.add_argument("out", type=Path)
    ap.add_argument("--front-offset", type=int, nargs=2, default=(0, 0), metavar=("X", "Y"))
    a = ap.parse_args()

    _, root = parse_pak(a.pak.read_bytes())
    fact = next((f for f in factories(root) if building_name(f) == a.name), None)
    if fact is None:
        print(f"no factory {a.name} in {a.pak}", file=sys.stderr)
        return 1
    buil = next(c for c in fact.children if c.type == "BUIL")
    bd = buil.data
    assert u16(bd, 0) & 0x7FFF in (8, 9, 10), "unsupported building node version"
    w, h, layouts = u16(bd, 10), u16(bd, 12), bd[14]
    assert layouts == LAYOUTS, "industry sets have four layouts"
    texts = [text(c) for c in buil.children if c.type == "TEXT"]
    tiles = [c for c in buil.children if c.type == "TILE"]
    per_layout = w * h
    seasons = max(t.data[6] for t in tiles)
    phases = max(u16(t.data, 2) for t in tiles)
    has_front = phases > 1 or any(lst.children for t in tiles for arr in t.children[1::2] for lst in arr.children)
    rows = 2 * LAYOUTS + (2 * LAYOUTS * per_layout if has_front else 0)
    assert seasons == 2 and per_layout <= 8 and phases <= 8
    sheet = Image.new("RGBA", (8 * TILE, rows * TILE), TRANSPARENT)
    for t in tiles:
        index = u16(t.data, 4)
        layout, cell = divmod(index, per_layout)
        for season in range(seasons):
            back, front = t.children[2 * season], t.children[2 * season + 1]
            assert len(back.children) == 1, "only height 0"
            for phase, img in enumerate(back.children[0].children):
                d = decode_img(img)
                if d is not None:
                    assert phase == 0, "animated back image"
                    paste(sheet, d, season * LAYOUTS + layout, cell)
            for lst in front.children:
                for phase, img in enumerate(lst.children):
                    d = decode_img(img)
                    if d is not None:
                        row = 2 * LAYOUTS + (season * LAYOUTS + layout) * per_layout + cell
                        paste(sheet, d, row, phase, *a.front_offset)
    sheet.convert("RGB").save(a.out)

    print(f"name={texts[0]} copyright={texts[1] if len(texts) > 1 else ''}")
    print(f"dims={w},{h} level={u16(bd, 4)} seasons={seasons} phases={phases} front={has_front}")
    print(factory_fields(fact))
    for g in goods(fact):
        print("  ", g)
    print(f"wrote {a.out} ({sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
