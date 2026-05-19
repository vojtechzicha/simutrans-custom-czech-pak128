#!/usr/bin/env python3
"""Build script for the VZ pak128 addon set.

Walks every ``vehicle-*/.../family.yaml`` under the project root, expands each
family across its liveries, writes per-livery DAT / PNG / .tab files into a
temporary ``build/`` tree, and invokes ``makeobj`` to emit ``.pak`` files into
``dist/``.

Usage:
    python build.py                # build everything
    python build.py --clean        # wipe build/ and dist/ first, then build
    python build.py <family-dir>   # build a single family by directory or yaml path

``makeobj`` is located via the ``MAKEOBJ_PATH`` environment variable; if unset,
``makeobj`` on PATH is used.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"

DIRECTIONS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]


def slug(s: str) -> str:
    return s.replace(".", "_")


def basename_for(family: dict, livery: dict) -> str:
    return f"VZ-{family['agency']}-{slug(family['type'])}-{livery['color']}"


def emit_dat(family: dict, livery: dict) -> str:
    bn = basename_for(family, livery)
    copyright_line = f"{family['copyright']}, vojtechzicha"
    vehicles = family["vehicles"]
    blocks = []

    other_ids = {v["id"]: [p["id"] for p in vehicles if p["id"] != v["id"]] for v in vehicles}

    for v in vehicles:
        obj_name = f"{bn}-{slug(v['id'])}"
        lines = [
            "obj=vehicle",
            f"name={obj_name}",
            f"copyright={copyright_line}",
        ]
        for k, val in v["fields"].items():
            lines.append(f"{k}={val}")
        if v.get("extended"):
            lines.append("")
            lines.append("# extended")
            for k, val in v["extended"].items():
                lines.append(f"{k}={val}")
        lines.append("")
        reverse = v.get("reverse", False)
        for col, d in enumerate(DIRECTIONS):
            src_col = (col + 4) % 8 if reverse else col
            lines.append(f"emptyimage[{d}]={bn}.{v['row']}.{src_col},0,4")
        lines.append("")
        can_head = v.get("head", True)
        can_tail = v.get("tail", True)
        prev_partners = v.get("prev", other_ids[v["id"]])
        next_partners = v.get("next", other_ids[v["id"]])
        prev_entries = (["none"] if can_head else []) + [f"{bn}-{slug(pid)}" for pid in prev_partners]
        next_entries = (["none"] if can_tail else []) + [f"{bn}-{slug(pid)}" for pid in next_partners]
        for idx, entry in enumerate(prev_entries):
            lines.append(f"Constraint[Prev][{idx}]={entry}")
        for idx, entry in enumerate(next_entries):
            lines.append(f"Constraint[Next][{idx}]={entry}")
        blocks.append("\n".join(lines))

    sep = "\n" + "-" * 40 + "\n\n"
    return sep.join(blocks) + "\n"


def emit_tab(family: dict, livery: dict, lang: str) -> str:
    bn = basename_for(family, livery)
    disp = family["display"]
    if lang == "en":
        header = "# Language: English"
        agency, fam_name = disp["agency_en"], disp["family_en"]
        livery_name, class_word, role_key = livery["name_en"], "Class", "role_en"
    elif lang == "cs":
        header = "# Language: Čeština"
        agency, fam_name = disp["agency_cs"], disp["family_cs"]
        livery_name, class_word, role_key = livery["name_cs"], "řada", "role_cs"
    else:
        raise ValueError(f"unsupported lang: {lang}")

    out = [header, ""]
    for v in family["vehicles"]:
        obj_name = f"{bn}-{slug(v['id'])}"
        disp_id = v.get("display_id", v["id"])
        display = f"{agency} {class_word} {disp_id} {fam_name} {v[role_key]} ({livery_name})"
        out.append(obj_name)
        out.append(display)
        out.append("")
    return "\n".join(out)


def build_family(family_yaml: Path) -> tuple[int, int]:
    """Build all liveries of one family. Returns (succeeded, failed)."""
    family = yaml.safe_load(family_yaml.read_text(encoding="utf-8"))
    family_dir = family_yaml.parent
    makeobj = os.environ.get("MAKEOBJ_PATH", "makeobj")
    DIST.mkdir(exist_ok=True)

    ok = fail = 0
    for livery in family["liveries"]:
        bn = basename_for(family, livery)
        png_src = family_dir / "sprites" / f"{livery['color']}.png"
        if not png_src.exists():
            print(f"  [skip] {bn}: missing sprite {png_src}", file=sys.stderr)
            fail += 1
            continue

        out_dir = BUILD / bn
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)

        shutil.copy2(png_src, out_dir / f"{bn}.png")
        (out_dir / f"{bn}.dat").write_text(emit_dat(family, livery), encoding="utf-8")
        (out_dir / f"{bn}.en.tab").write_text(emit_tab(family, livery, "en"), encoding="utf-8")
        (out_dir / f"{bn}.cs.tab").write_text(emit_tab(family, livery, "cs"), encoding="utf-8")

        pak = DIST / f"{bn}.pak"
        try:
            result = subprocess.run(
                [makeobj, "pak128", str(pak), str(out_dir)],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            print(
                f"  [fail] {bn}: makeobj not found (set MAKEOBJ_PATH or add it to PATH)",
                file=sys.stderr,
            )
            fail += 1
            continue

        if result.returncode != 0:
            print(f"  [fail] {bn}: makeobj exit {result.returncode}", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            fail += 1
        else:
            print(f"  [ok]   {bn} -> {pak.relative_to(ROOT)}")
            ok += 1
    return ok, fail


def discover_families(target: Path | None) -> list[Path]:
    if target is None:
        return [
            p
            for p in ROOT.rglob("family.yaml")
            if p.relative_to(ROOT).parts and p.relative_to(ROOT).parts[0].startswith("vehicle-")
        ]
    target = target.resolve()
    if target.is_file() and target.name == "family.yaml":
        return [target]
    if target.is_dir():
        candidate = target / "family.yaml"
        if candidate.is_file():
            return [candidate]
    print(f"no family.yaml found at {target}", file=sys.stderr)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Build VZ pak128 addons.")
    parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        help="Optional family directory or family.yaml to build (default: all).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe build/ and dist/ before building.",
    )
    args = parser.parse_args()

    if args.clean:
        for d in (BUILD, DIST):
            if d.exists():
                shutil.rmtree(d)
                print(f"cleaned {d.relative_to(ROOT)}")

    families = discover_families(args.target)
    if not families:
        print("no families found", file=sys.stderr)
        return 1

    total_ok = total_fail = 0
    for fy in sorted(families):
        rel = fy.relative_to(ROOT)
        print(f"== {rel} ==")
        ok, fail = build_family(fy)
        total_ok += ok
        total_fail += fail

    print(f"\nbuilt {total_ok} | failed {total_fail}")
    return 0 if total_fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
