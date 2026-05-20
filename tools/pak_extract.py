#!/usr/bin/env python3
"""Extract sprite sheets from compiled Simutrans .pak files.

Walks the pak node tree, finds the first IMG1 imagelist inside each VHCL
(vehicle) node, decodes its IMG entries, and composes them side-by-side into
a single PNG row matching the project's `family.yaml` sprite layout
(tile size 128×128, 8 direction columns).

Usage:
    python tools/pak_extract.py <input.pak> <output.png> [--tile N]

For a vehicle pak the result is a 1024×128 sheet; for multi-vehicle paks the
output stacks rows in declaration order.

Notes on format (pak v1003):
  - File header: text + 0x1A + uint32 LE version.
  - Node header: char[4] type + uint16 LE children + uint16 LE size + bytes.
  - IMG payload header (10 bytes):
      sint16 x, sint16 y, sint16 w, uint8 _pad, sint16 h (unaligned), uint8 zoomable
  - Pixel RLE per row:
      while True:
        skip = u16; if skip == 0: break (end of row, trailing transparent implicit)
        paint = u16; pixels = u16 × paint
  - Pixel values < 0x8000: RGB565 (with 0x0000 as a valid pure-black color)
  - Pixel values >= 0x8000: simutrans player/special colors — we render with
    a placeholder palette so the user can see which pixels are tintable.
"""

import argparse
import struct
import sys
from pathlib import Path
from PIL import Image

# pak128 transparent key — a fully opaque cyan pixel. makeobj recognises this
# exact RGB at build time as the transparent colour, so we encode transparency
# in the PNG by writing this colour (not by setting the alpha channel).
TRANSPARENT = (231, 255, 255, 255)

# Pak IMG node ordering inside vehicle paks vs this project's PNG column
# convention. The project stores columns in makeobj's standard
# [w, nw, n, ne, e, se, s, sw] order; pak128.cs source vehicles instead store
# the IMG list in [w, n, ne, nw, e, s, sw, se] order. This table maps each
# project column to the pak's IMG index that should fill it.
PAK_TO_PROJECT_DIR = [1, 3, 0, 2, 5, 7, 4, 6]

# Placeholder palette for simutrans special pixels (player colors etc.).
# Range 0x8000..0x801F is the player-color band: pak128.cs typically paints
# vehicle bodies with these, then the simutrans renderer recolors them at
# draw time per the player's livery. Without that recolor pass we render
# them as a neutral silver gradient so the silhouette looks roughly like
# the in-game default — the user is expected to recolor for the target
# livery anyway.
SPECIAL_PALETTE = {
    **{0x8000 + i: (
        int(50 + 180 * (i / 31)),
        int(50 + 180 * (i / 31)),
        int(55 + 185 * (i / 31)),
        255,
    ) for i in range(32)},
}


def rgb565_to_rgba(v):
    r = (v >> 11) & 0x1F
    g = (v >> 5) & 0x3F
    b = v & 0x1F
    return ((r * 255 + 15) // 31, (g * 255 + 31) // 63, (b * 255 + 15) // 31, 255)


def rgb555_to_rgba(v):
    r = (v >> 10) & 0x1F
    g = (v >> 5) & 0x1F
    b = v & 0x1F
    return ((r * 255 + 15) // 31, (g * 255 + 15) // 31, (b * 255 + 15) // 31, 255)


PIXEL_DECODE = rgb555_to_rgba  # default; switch with --rgb565 CLI flag


def pixel_to_rgba(v):
    if v >= 0x8000:
        if v in SPECIAL_PALETTE:
            return SPECIAL_PALETTE[v]
        # Unknown special — use magenta as a "look at me" marker.
        return (255, 0, 255, 255)
    return PIXEL_DECODE(v)


def transparent_pixel_to_rgba(v):
    """Decode a pixel from a paint run flagged with TRANSPARENT_RUN.

    Simutrans encodes such pixels as semi-transparent overlays:
        value = 0x8020 + rgb343_index * 31 + alpha
    where rgb343_index is a 10-bit RGB index (3 R, 4 G, 3 B) and alpha 0..30.
    These pixels blend with whatever underlies them at draw time (the player
    color layer). For static extraction we render them semi-transparent over
    a neutral grey so the silhouette still shows but the colour does not get
    misinterpreted as a solid RGB565 pixel.
    """
    if v < 0x8020:
        # Edge case — shouldn't really happen inside a flagged run, but be safe.
        return (0, 0, 0, 0)
    idx = v - 0x8020
    rgb343 = idx // 31
    alpha = idx % 31
    r3 = (rgb343 >> 7) & 0x07
    g4 = (rgb343 >> 3) & 0x0F
    b3 = rgb343 & 0x07
    r = (r3 * 255 + 3) // 7
    g = (g4 * 255 + 7) // 15
    b = (b3 * 255 + 3) // 7
    # alpha is 0..30 in the encoding; map to 0..255 for the PNG.
    a = (alpha * 255 + 15) // 30
    return (r, g, b, a)


class Node:
    __slots__ = ("type", "data", "children")

    def __init__(self, ntype, data, children):
        self.type = ntype
        self.data = data
        self.children = children


def parse_pak(buf: bytes):
    # Skip the human-readable header up to 0x1A.
    eof = buf.index(b"\x1A")
    pos = eof + 1
    (version,) = struct.unpack_from("<I", buf, pos)
    pos += 4
    root, pos = read_node(buf, pos)
    return version, root


def read_node(buf, pos):
    ntype = buf[pos:pos + 4].decode("ascii", errors="replace")
    nchildren, size = struct.unpack_from("<HH", buf, pos + 4)
    pos += 8
    data = buf[pos:pos + size]
    pos += size
    children = []
    for _ in range(nchildren):
        child, pos = read_node(buf, pos)
        children.append(child)
    return Node(ntype, data, children), pos


def find_vehicles(node):
    if node.type == "VHCL":
        yield node
    for c in node.children:
        yield from find_vehicles(c)


def decode_img(node):
    """Decode an IMG node into an (xoff, yoff, RGBA pixel grid).

    Simutrans uses three image-format versions, identified by a version byte
    at offset 6 of the IMG payload (this is independent of the outer pak file
    format version):
      - v3: x/y/w as sint16, h as sint16 at unaligned offset 7. 10-byte header.
      - v1/v2: x/y as sint16, w/h as uint8, len as uint16. 10-byte header.
      - v0: legacy, x/w/y/h as uint8, len as uint32. 12-byte header.
    """
    data = node.data
    if len(data) < 10:
        return None
    # Bytes 0-3 always s16 x, s16 y. Byte 6 identifies the image version.
    x, y = struct.unpack_from("<hh", data, 0)
    img_version = data[6]
    if img_version == 3:
        w = struct.unpack_from("<h", data, 4)[0]
        h = struct.unpack_from("<h", data, 7)[0]
        header_size = 10
    elif img_version in (1, 2):
        w = data[4]
        h = data[5]
        header_size = 10
    elif img_version == 0:
        if len(data) < 12:
            return None
        # v0: u8 x, u8 w, u8 y, u8 h, u32 len, u8 dummy[2], u8 zoomable
        x = data[0]
        w = data[1]
        y = data[2]
        h = data[3]
        header_size = 12
    else:
        return None
    if w <= 0 or h <= 0:
        return None
    pixels = data[header_size:]
    # RLE decode — canonical simutrans format:
    #   per row: skip0, paint0, paint0×pixels, skip1, paint1, paint1×pixels, ...
    #            terminated when a *subsequent* skip reads as 0 (after the first
    #            paint run). The first skip of a row may be 0 (no leading
    #            transparent pixels) and that's not a terminator.
    #   paint counts may have the TRANSPARENT_RUN flag (0x8000) — the pixels
    #   in that run are semi-transparent and encoded specially. We mask it off
    #   and read the count from the low 15 bits.
    #
    # Two row-width conventions:
    #   - v3 paks: RLE positions are bounding-box-relative (0..w-1), and we
    #     render into a w-wide grid at offset (x, y).
    #   - v0/v1/v2 paks: RLE positions are tile-relative (0..127), so we
    #     render into a 128-wide grid whose row range corresponds to the
    #     bounding box's rows; x in the header is informational and ignored
    #     for placement (the painted columns are already inside the row).
    TRANSPARENT_RUN = 0x8000
    if img_version == 3:
        grid_w = w
        x_offset_for_paste = x
    else:
        grid_w = 128
        x_offset_for_paste = 0
    grid = [[TRANSPARENT] * grid_w for _ in range(h)]
    p = 0
    n = len(pixels)
    for row in range(h):
        col = 0
        if p + 2 > n:
            break
        skip = struct.unpack_from("<H", pixels, p)[0]
        p += 2
        col += skip
        while True:
            if p + 2 > n:
                break
            paint = struct.unpack_from("<H", pixels, p)[0]
            p += 2
            paint_count = paint & ~TRANSPARENT_RUN
            is_transparent_run = bool(paint & TRANSPARENT_RUN)
            for _ in range(paint_count):
                if p + 2 > n:
                    break
                v = struct.unpack_from("<H", pixels, p)[0]
                p += 2
                if 0 <= col < grid_w:
                    grid[row][col] = transparent_pixel_to_rgba(v) if is_transparent_run else pixel_to_rgba(v)
                col += 1
            if p + 2 > n:
                break
            skip = struct.unpack_from("<H", pixels, p)[0]
            p += 2
            if skip == 0:
                break  # end of row
            col += skip
    return x_offset_for_paste, y, len(grid[0]) if grid else 0, h, grid


def render_image(img, tile):
    """Place a decoded IMG into a fresh tile-sized RGBA canvas."""
    canvas = Image.new("RGBA", (tile, tile), TRANSPARENT)
    if img is None:
        return canvas
    x, y, w, h, grid = img
    flat = bytes(
        c
        for row in grid
        for px in row
        for c in px
    )
    sprite = Image.frombytes("RGBA", (w, h), flat)
    # Composite at (x, y) within the tile.
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def find_imagelists(vhcl):
    return [c for c in vhcl.children if c.type == "IMG1"]


def first_8dir_imagelist(vhcl):
    """The first IMG1 list with 8 IMG children is the emptyimage 8-direction set."""
    for imglist in find_imagelists(vhcl):
        imgs = [c for c in imglist.children if c.type.startswith("IMG")]
        if len(imgs) == 8:
            return imgs
    # Fallback: first imagelist with any IMG children.
    for imglist in find_imagelists(vhcl):
        imgs = [c for c in imglist.children if c.type.startswith("IMG")]
        if imgs:
            return imgs
    return []


def extract(pak_path: Path, out_path: Path, tile: int, vehicle_filter):
    buf = pak_path.read_bytes()
    version, root = parse_pak(buf)
    print(f"pak version: {version}", file=sys.stderr)
    vehicles = list(find_vehicles(root))
    if not vehicles:
        sys.exit("no VHCL nodes found")
    rows = []
    for v in vehicles:
        # Vehicle name = first TEXT child
        name = next(
            (c.data.rstrip(b"\x00").decode("ascii", errors="replace")
             for c in v.children if c.type == "TEXT"),
            "?",
        )
        if vehicle_filter and name not in vehicle_filter:
            continue
        imgs = first_8dir_imagelist(v)
        print(f"vehicle '{name}': {len(imgs)} images", file=sys.stderr)
        sheet = Image.new("RGBA", (tile * 8, tile), TRANSPARENT)
        for project_col in range(8):
            pak_col = PAK_TO_PROJECT_DIR[project_col]
            if pak_col >= len(imgs):
                continue
            decoded = decode_img(imgs[pak_col])
            tile_img = render_image(decoded, tile)
            sheet.paste(tile_img, (project_col * tile, 0))
        rows.append(sheet)
    if not rows:
        sys.exit("no images found (check --vehicle filter)")
    out = Image.new("RGBA", (tile * 8, tile * len(rows)), TRANSPARENT)
    for i, r in enumerate(rows):
        out.paste(r, (0, i * tile))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    print(f"wrote {out_path} ({out.width}×{out.height})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pak", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--tile", type=int, default=128)
    ap.add_argument(
        "--vehicle",
        action="append",
        help="extract only the named vehicle(s); may be repeated",
    )
    ap.add_argument(
        "--rgb565",
        action="store_true",
        help="decode pixels as RGB565 instead of the default RGB555 "
             "(simutrans pak128.cs paks use RGB555 with the top bit reserved)",
    )
    args = ap.parse_args()
    if args.rgb565:
        global PIXEL_DECODE
        PIXEL_DECODE = rgb565_to_rgba
    extract(args.pak, args.out, args.tile, set(args.vehicle or []))


if __name__ == "__main__":
    main()
