#!/usr/bin/env python3
"""Extract roadsign / signal objects (SIGN nodes) from compiled Simutrans paks.

Every object becomes one sheet ``<out>/<Name>.png``: 4 columns (the image
directions N, S, W, E, as ``Image[i]`` lists them) by one row per state
(``Image[4*row + col]``), plus a last row holding the cursor (col 0) and the
toolbar icon (col 1). Tiles are 128×128; special colours come out as their
exact ``image_t::rgbtab`` RGB (see pak_extract.py), so makeobj rebuilds them
unchanged.

With ``--meta FILE`` the object data (flags, cost, speed, dates, waytype,
offset_left, copyright, image count) is written as YAML, in pak order. With
``--dat FILE`` a makeobj .dat re-creating the objects 1:1 (same names, data and
images, sprite refs into the extracted sheets) is written next to them.

Usage:
    python tools/sign_extract.py <in.pak> <out_dir> [--meta meta.yaml] [--dat objs.dat] [--only NAME ...]
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pak_extract import TRANSPARENT, decode_img, parse_pak, render_image  # noqa: E402

TILE = 128

# roadsign_desc_t::types
FLAG_NAMES = {
    0x001: "one_way", 0x002: "choose", 0x004: "private", 0x008: "signal",
    0x010: "presignal", 0x020: "only_backimage", 0x040: "longblock",
    0x080: "end_of_choose", 0x100: "priority", 0x200: "platform", 0x400: "station_boundary",
}
WAYTYPES = {1: "road", 2: "track", 3: "water", 4: "air", 7: "tram_track", 16: "air"}


def text(node) -> str:
    return node.data.split(b"\0")[0].decode("latin-1")


def signs(node):
    if node.type == "SIGN":
        yield node
    for c in node.children:
        yield from signs(c)


def read_sign(node) -> dict:
    d = node.data
    raw = struct.unpack_from("<H", d, 0)[0]
    version = raw & 0x7FFF if raw & 0x8000 else 0
    if version < 4:
        raise ValueError(f"roadsign node version {version} not supported")
    min_speed, cost = struct.unpack_from("<HI", d, 2)
    if version >= 5:
        flags = struct.unpack_from("<H", d, 8)[0]
        offset_left, wtyp = d[10], d[11]
        intro, retire = struct.unpack_from("<HH", d, 12)
    else:
        flags, offset_left, wtyp = d[8], d[9], d[10]
        intro, retire = struct.unpack_from("<HH", d, 11)
    images = [c for il in node.children if il.type == "IMG1" for c in il.children]
    skin = []
    for c in node.children:
        if c.type == "CURS":
            skin = [g for il in c.children if il.type == "IMG1" for g in il.children]
    return {
        "name": text(node.children[0]),
        "copyright": text(node.children[1]) if len(node.children) > 1 else "",
        "flags": [n for bit, n in FLAG_NAMES.items() if flags & bit],
        "min_speed": min_speed,
        "cost": cost // 100,
        "offset_left": offset_left,
        "waytype": WAYTYPES.get(wtyp, wtyp),
        "intro": [intro // 12, intro % 12 + 1],
        "retire": [retire // 12, retire % 12 + 1],
        "images": len(images),
        "_imgs": images,
        "_skin": skin,
    }


def sheet(obj: dict) -> Image.Image:
    n = obj["images"]
    rows = (n + 3) // 4
    im = Image.new("RGBA", (4 * TILE, (rows + 1) * TILE), TRANSPARENT)
    for i, node in enumerate(obj["_imgs"]):
        im.paste(render_image(decode_img(node), TILE), ((i % 4) * TILE, (i // 4) * TILE))
    for i, node in enumerate(obj["_skin"][:2]):
        im.paste(render_image(decode_img(node), TILE), (i * TILE, rows * TILE))
    return im.convert("RGB")


FLAG_KEYS = {"one_way": "single_way", "private": "is_private", "only_backimage": "no_foreground",
             "end_of_choose": "end_of_choose", "station_boundary": "station_boundary"}


def dat_entry(o: dict, sprite_prefix: str = "") -> str:
    """makeobj keys for one extracted object (inverse of roadsign_writer.cc)."""
    f = set(o["flags"])
    lines = ["Obj=roadsign", f"Name={o['name']}", f"copyright={o['copyright']}", f"waytype={o['waytype']}"]
    if "signal" in f and "longblock" not in f:
        lines.append("is_signal=1")
        if "choose" in f:
            lines.append("free_route=1")
        if "platform" in f:
            lines.append("is_platformsignal=1")
    elif "presignal" in f:
        lines.append("is_presignal=1")
    elif "priority" in f:
        lines.append("is_prioritysignal=1")
    elif "longblock" in f:
        lines.append("is_longblocksignal=1")
    else:
        if "choose" in f:
            lines.append("free_route=1")
        lines += [f"{key}=1" for flag, key in FLAG_KEYS.items() if flag in f]
    if o["min_speed"]:
        lines.append(f"min_speed={o['min_speed']}")
    lines += [f"cost={o['cost']}", f"offset_left={o['offset_left']}",
              f"intro_year={o['intro'][0]}", f"intro_month={o['intro'][1]}",
              f"retire_year={o['retire'][0]}", f"retire_month={o['retire'][1]}"]
    bn = sprite_prefix + o["name"]
    rows = (o["images"] + 3) // 4
    lines += [f"Image[{i}]={bn}.{i // 4}.{i % 4}" for i in range(o["images"])]
    if o.get("_skin"):
        lines += [f"cursor={bn}.{rows}.0", f"icon=> {bn}.{rows}.1"]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pak", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--dat", type=Path)
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    _, root = parse_pak(args.pak.read_bytes())
    objs = [read_sign(s) for s in signs(root)]
    if args.only:
        objs = [o for o in objs if o["name"] in args.only]
    args.out.mkdir(parents=True, exist_ok=True)
    for o in objs:
        sheet(o).save(args.out / f"{o['name']}.png")
    if args.meta:
        clean = [{k: v for k, v in o.items() if not k.startswith("_")} for o in objs]
        args.meta.write_text(yaml.safe_dump(clean, sort_keys=False, allow_unicode=True), encoding="utf-8")
    if args.dat:
        prefix = args.out.resolve().relative_to(args.dat.resolve().parent).as_posix() + "/"
        prefix = "" if prefix == "./" else prefix
        args.dat.write_text("---\n".join(dat_entry(o, prefix) for o in objs), encoding="utf-8")
    print(f"{len(objs)} objects -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
