#!/usr/bin/env python3
"""Build script for the VZ pak128 addon set.

Walks every ``vehicle-*/.../family.yaml`` under the project root, groups them by
(agency, mode), and emits one ``.pak`` per group into ``dist/`` — e.g.
``dist/VZ-CeskeDrahy-rail.pak`` contains every family and livery for ČD's rail
fleet. Station sets (``station-*/.../station.yaml``) and industry sets
(``industry-*/.../industry.yaml``) are grouped the same way by their ``group``
field, e.g. ``dist/VZ-Stations-rail.pak``, ``dist/VZ-Supermarkets-city.pak``.
Per-livery DAT / PNG files live side-by-side inside one shared build directory
so a single ``makeobj`` invocation bundles them.

Usage:
    python build.py                # build every agency-mode pak
    python build.py --clean        # wipe build/ and dist/ first, then build
    python build.py <path>         # build the agency-mode pak that <path> belongs to
                                   # (family dir, family.yaml, or agency dir all work)
    python build.py --no-install   # skip the install step (see below)
    python build.py -y             # auto-confirm orphan deletion during install

After a successful build, if ``PAK_TARGET_DIR`` is set in the environment (or
``.env``), the script syncs both the paks and their translation files:
``dist/VZ-*.pak`` is copied to ``PAK_TARGET_DIR/`` and
``dist/text/<lang>.VZ-*.tab`` is copied to ``PAK_TARGET_DIR/text/``. (Simutrans
only loads loose translation tabs from the pak's ``text/`` subfolder, and only
matches a dot-separated language prefix/suffix in the filename — see
``translator::load_files_from_folder`` in simutrans-extended.) It prompts before
deleting any VZ artifact that exists in the target but not in dist (``-y`` skips
the prompt); legacy tab filenames left at the pak root by older builds are
swept up by the same prompt. Skip the install step with ``--no-install`` or by
leaving ``PAK_TARGET_DIR`` unset.

``makeobj`` is located via the ``MAKEOBJ_PATH`` environment variable; if unset,
``makeobj`` on PATH is used. A ``.env`` file in the project root is auto-loaded
on startup (existing environment variables take precedence); see ``.env.example``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"

DIRECTIONS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]


def load_dotenv(path: Path) -> None:
    """Minimal .env loader. KEY=VALUE per line; blank lines and ``#`` comments
    are ignored. Optional surrounding single/double quotes are stripped. Existing
    environment variables are NOT overwritten."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def slug(s: str) -> str:
    return s.replace(".", "_")


def basename_for(family: dict, livery: dict) -> str:
    """The per-livery object basename: used for object name=, the livery's PNG
    file in the shared build dir, and sprite refs inside the .dat."""
    return f"VZ-{family['agency']}-{slug(family['type'])}-{livery['color']}"


SOURCE_ROOTS = {"family.yaml": "vehicle-", "station.yaml": "station-", "industry.yaml": "industry-"}


def mode_for(source_yaml: Path) -> str:
    """Derive the transport mode from the top-level folder (vehicle-rail → rail,
    station-rail → rail, industry-city → city)."""
    rel = source_yaml.relative_to(ROOT)
    top = rel.parts[0]
    prefix = SOURCE_ROOTS[source_yaml.name]
    assert top.startswith(prefix), f"unexpected top folder: {top}"
    return top[len(prefix):]


def group_for(source_yaml: Path, data: dict) -> str:
    """The pak group token: a vehicle family's agency, a station or industry
    set's group."""
    return data["agency"] if source_yaml.name == "family.yaml" else data["group"]


def pak_basename_for(agency: str, mode: str) -> str:
    """The output .pak basename: VZ-<Agency>-<mode>."""
    return f"VZ-{agency}-{mode}"


# Simutrans special colours that light up at night on windows (image_t::rgbtab
# 16, 17, 27, 28), mapped to a visually identical plain colour: by day the two
# render the same, at night only the special one glows.
WINDOW_LIGHTS_TO_UNLIT = {
    (0x57, 0x65, 0x6F): (0x57, 0x65, 0x6E),
    (0x7F, 0x9B, 0xF1): (0x7F, 0x9B, 0xF0),
    (0xC1, 0xB1, 0xD1): (0xC1, 0xB1, 0xD0),
    (0x4D, 0x4D, 0x4D): (0x4D, 0x4D, 0x4E),
}
UNLIT_SUFFIX = "-unlit"


def write_unlit_png(src: Path, dst: Path) -> None:
    """Copy src to dst with every lit-window special colour replaced by its plain
    twin. Needs Pillow (only for families that use windows_lit_when_loaded)."""
    from PIL import Image

    img = Image.open(src)
    img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    step = len(img.getbands())
    lookup = {bytes(k): bytes(v) for k, v in WINDOW_LIGHTS_TO_UNLIT.items()}
    data = bytearray(img.tobytes())
    for i in range(0, len(data), step):
        new = lookup.get(bytes(data[i:i + 3]))
        if new:
            data[i:i + 3] = new
    Image.frombytes(img.mode, img.size, bytes(data)).save(dst)


def in_livery(vehicle: dict, livery: dict) -> bool:
    """A vehicle's optional `liveries:` list names the liveries it exists in
    (e.g. a trailer never painted in a railcar's regional scheme); default all."""
    only = vehicle.get("liveries")
    return only is None or livery["color"] in only


def check_vehicle_liveries(family: dict) -> None:
    colors = {lv["color"] for lv in family["liveries"]}
    for v in family["vehicles"]:
        unknown = set(v.get("liveries") or []) - colors
        if unknown:
            raise ValueError(f"vehicle {v['id']}: unknown liveries {sorted(unknown)}")


def emit_dat(family: dict, livery: dict) -> str:
    bn = basename_for(family, livery)
    # Upstream credit first, vojtechzicha last and only once (families whose
    # art is drawn here from scratch may name just vojtechzicha).
    credits = [c.strip() for c in str(family["copyright"]).split(",")]
    credits = [c for c in credits if c and c.lower() != "vojtechzicha"]
    copyright_line = ", ".join(credits + ["vojtechzicha"])
    check_vehicle_liveries(family)
    by_id = {v["id"]: v for v in family["vehicles"]}
    vehicles = [v for v in family["vehicles"] if in_livery(v, livery)]
    blocks = []

    other_ids = {v["id"]: [p["id"] for p in vehicles if p["id"] != v["id"]] for v in vehicles}
    # Pixel offset makeobj applies to every image. The historical [0, 4] suits the
    # rail sources; road sprites drawn to the pak128.cs lane convention need [0, 0].
    x_off, y_off = family.get("image_offset", [0, 4])

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
        # windows_lit_when_loaded: the sheet as drawn (glass on the lit-at-night
        # special colours) becomes the freight image, shown while anyone is aboard;
        # the empty image is a derived copy whose glass never lights up.
        lit_when_loaded = family.get("windows_lit_when_loaded", False)
        empty_bn = f"{bn}{UNLIT_SUFFIX}" if lit_when_loaded else bn
        for col, d in enumerate(DIRECTIONS):
            src_col = (col + 4) % 8 if reverse else col
            lines.append(f"emptyimage[{d}]={empty_bn}.{v['row']}.{src_col},{x_off},{y_off}")
        if lit_when_loaded:
            for col, d in enumerate(DIRECTIONS):
                src_col = (col + 4) % 8 if reverse else col
                lines.append(f"freightimage[{d}]={bn}.{v['row']}.{src_col},{x_off},{y_off}")
        lines.append("")
        can_head = v.get("head", True)
        can_tail = v.get("tail", True)
        prev_partners = v.get("prev", other_ids[v["id"]])
        next_partners = v.get("next", other_ids[v["id"]])
        # couple_liveries: a partner id resolves to that vehicle in EVERY livery
        # of the family (so cars of different paint can couple), not just this one.
        # Liveries a partner does not exist in (its `liveries:` list) are skipped.
        def partner_bns(pid: str) -> list[str]:
            pv = by_id.get(pid, {})
            if v.get("couple_liveries", False):
                return [basename_for(family, lv) for lv in family["liveries"] if in_livery(pv, lv)]
            return [bn] if in_livery(pv, livery) else []
        # prev/next: any -> no constraint on that side at all, so the vehicle couples
        # with anything, like native locomotives and coaches (loco-hauled stock).
        def entries(partners, open_end: bool) -> list[str]:
            if partners == "any":
                return []
            return (["none"] if open_end else []) + [
                f"{b}-{slug(pid)}" for pid in partners for b in partner_bns(pid)]
        for idx, entry in enumerate(entries(prev_partners, can_head)):
            lines.append(f"Constraint[Prev][{idx}]={entry}")
        for idx, entry in enumerate(entries(next_partners, can_tail)):
            lines.append(f"Constraint[Next][{idx}]={entry}")
        blocks.append("\n".join(lines))

    sep = "\n" + "-" * 40 + "\n\n"
    return sep.join(blocks) + "\n"


# Modes that use Czech railway "class" nomenclature in display strings. For
# these, display strings include a "Class <id>" / "řada <id>" prefix between
# agency and family name. Other modes (bus, tram, …) drop the prefix because
# buses/trams don't have a class numbering scheme in Czech transport usage —
# the family name (e.g. "Tatra T3", "Irisbus Citelis 12M") already names them.
MODES_WITH_CLASS_PREFIX = {"rail"}


def emit_tab_entries(family: dict, livery: dict, lang: str, mode: str) -> list[str]:
    """Return the per-object lines (object name + display string) for one
    family×livery in a given language. The lines are emitted as bare pairs with
    no blank separator (matching the upstream tab format Simutrans expects)."""
    bn = basename_for(family, livery)
    disp = family["display"]
    if lang == "en":
        agency, fam_name = disp["agency_en"], disp["family_en"]
        livery_name, class_word, role_key = livery["name_en"], "Class", "role_en"
    elif lang == "cz":
        agency, fam_name = disp["agency_cs"], disp["family_cs"]
        livery_name, class_word, role_key = livery["name_cs"], "řada", "role_cs"
    else:
        raise ValueError(f"unsupported lang: {lang}")

    use_class = mode in MODES_WITH_CLASS_PREFIX

    out: list[str] = []
    for v in family["vehicles"]:
        if not in_livery(v, livery):
            continue
        obj_name = f"{bn}-{slug(v['id'])}"
        if use_class:
            disp_id = v.get("display_id", v["id"])
            display = f"{agency} {class_word} {disp_id} {fam_name} {v[role_key]} ({livery_name})"
        else:
            display = f"{agency} {fam_name} {v[role_key]} ({livery_name})"
        out.append(obj_name)
        out.append(display)
    return out


# Station sets (station-<mode>/.../station.yaml). Every object is a 16-layout
# through stop drawn on the standard sheet written by tools/gen_platforms.py:
# rows 0-1 back / 2-3 front images for season 0 (layouts 0-7, 8-15), rows 4-7
# the same for season 1 (snow), row 8 = build cursor (col 0) and 32x32 toolbar
# icon (col 1). Cells left entirely transparent are not referenced.
STATION_LAYOUTS = 16
STATION_SEASONS = 2
STATION_CURSOR = (8, 0)
STATION_ICON = (8, 1)
MODE_WAYTYPES = {"rail": "track"}
TRANSPARENT_RGB = (231, 255, 255)


def station_basename(spec: dict, obj: dict) -> str:
    return f"VZ-{spec['group']}-{obj['id']}"


def station_sheet_cell(kind: str, season: int, layout: int) -> tuple[int, int]:
    row = (0 if kind == "back" else 2) + season * 4 + layout // 8
    return row, layout % 8


def nonempty_cells(png: Path, tile: int = 128) -> set[tuple[int, int]]:
    """(row, col) of every sheet cell holding at least one visible pixel."""
    from PIL import Image

    img = Image.open(png).convert("RGB")
    cells = set()
    for r in range(img.height // tile):
        for c in range(img.width // tile):
            colors = img.crop((c * tile, r * tile, (c + 1) * tile, (r + 1) * tile)).getcolors(1 << 16)
            if colors is None or any(rgb != TRANSPARENT_RGB for _, rgb in colors):
                cells.add((r, c))
    return cells


def emit_station_dat(spec: dict, obj: dict, mode: str, cells: set[tuple[int, int]]) -> str:
    bn = station_basename(spec, obj)
    credit = spec.get("copyright")
    fields = {"type": "stop", "waytype": MODE_WAYTYPES[mode], "noinfo": 1}
    fields.update(obj.get("fields", {}))
    lines = [
        "obj=building",
        f"name={bn}",
        f"copyright={credit + ', ' if credit else ''}vojtechzicha",
        f"dims=1,1,{STATION_LAYOUTS}",
    ]
    lines += [f"{k}={v}" for k, v in fields.items()]
    lines.append(f"icon=> {bn}.{STATION_ICON[0]}.{STATION_ICON[1]}")
    lines.append(f"cursor={bn}.{STATION_CURSOR[0]}.{STATION_CURSOR[1]}")
    lines.append("")
    for season in range(STATION_SEASONS):
        for layout in range(STATION_LAYOUTS):
            for kind, key in (("back", "BackImage"), ("front", "FrontImage")):
                row, col = station_sheet_cell(kind, season, layout)
                if (row, col) in cells:
                    lines.append(f"{key}[{layout}][0][0][0][0][{season}]={bn}.{row}.{col}")
    return "\n".join(lines) + "\n"


def emit_station_tab_entries(spec: dict, obj: dict, lang: str) -> list[str]:
    return [station_basename(spec, obj), obj["name_en"] if lang == "en" else obj["name_cs"]]


def stage_station_set(station_yaml: Path, mode: str, out_dir: Path,
                      tab_lines: dict[str, list[str]]) -> tuple[int, int]:
    """Write the .dat/.png of every object of one station.yaml into out_dir."""
    spec = yaml.safe_load(station_yaml.read_text(encoding="utf-8"))
    ok = fail = 0
    for obj in spec["objects"]:
        bn = station_basename(spec, obj)
        png_src = station_yaml.parent / "sprites" / f"{obj['sprite']}.png"
        if not png_src.exists():
            print(f"  [skip] {bn}: missing sprite {png_src}", file=sys.stderr)
            fail += 1
            continue
        shutil.copy2(png_src, out_dir / f"{bn}.png")
        dat = emit_station_dat(spec, obj, mode, nonempty_cells(png_src))
        (out_dir / f"{bn}.dat").write_text(dat, encoding="utf-8")
        for lang in TAB_LANGS:
            tab_lines[lang].extend(emit_station_tab_entries(spec, obj, lang))
        ok += 1
    return ok, fail


# Industry sets (industry-<location>/.../industry.yaml): city consumer
# factories drawn by tools/gen_shops.py. Every object has four layouts and two
# seasons on one sheet: row = season * 4 + layout, column = tile y * w + x of
# that layout, where the odd layouts swap the object's dims. makeobj keys tile
# images as backimage[layout][y][x][height][phase][season].
INDUSTRY_LAYOUTS = 4
INDUSTRY_SEASONS = 2


def industry_basename(spec: dict, obj: dict) -> str:
    return f"VZ-{spec['group']}-{obj['id']}"


def industry_fields(spec: dict, obj: dict) -> dict:
    """Set defaults, then the size class's fields, then the object's own."""
    fields = dict(spec.get("defaults", {}))
    fields.update(spec["classes"][obj["class"]].get("fields", {}))
    fields.update(obj.get("fields", {}))
    return fields


def industry_goods(spec: dict, obj: dict) -> list[dict]:
    return spec["goods"][obj.get("goods", spec["classes"][obj["class"]]["goods"])]


def emit_industry_dat(spec: dict, obj: dict) -> str:
    bn = industry_basename(spec, obj)
    credit = spec.get("copyright")
    lines = [
        "obj=factory",
        f"name={bn}",
        f"copyright={credit + ', ' if credit else ''}vojtechzicha",
    ]
    lines += [f"{k}={v}" for k, v in industry_fields(spec, obj).items()]
    for i, g in enumerate(industry_goods(spec, obj)):
        lines += [
            f"inputgood[{i}]={g['good']}",
            f"inputcapacity[{i}]={g['capacity']}",
            f"inputsupplier[{i}]={g.get('suppliers', 0)}",
            f"inputfactor[{i}]={g['factor']}",
        ]
    x_dim, y_dim = obj["dims"]
    lines.append(f"dims={x_dim},{y_dim},{INDUSTRY_LAYOUTS}")
    lines.append("")
    for season in range(INDUSTRY_SEASONS):
        for layout in range(INDUSTRY_LAYOUTS):
            w, h = (x_dim, y_dim) if layout % 2 == 0 else (y_dim, x_dim)
            row = season * INDUSTRY_LAYOUTS + layout
            for y in range(h):
                for x in range(w):
                    lines.append(f"backimage[{layout}][{y}][{x}][0][0][{season}]={bn}.{row}.{y * w + x}")
    return "\n".join(lines) + "\n"


def emit_industry_tab_entries(spec: dict, obj: dict, lang: str) -> list[str]:
    """The factory's name, plus the text of its info window's Details tab
    (``factory_<name>_details``) when the object has one."""
    bn = industry_basename(spec, obj)
    suffix = "en" if lang == "en" else "cs"
    out = [bn, obj[f"name_{suffix}"]]
    details = obj.get(f"details_{suffix}")
    if details:
        out += [f"factory_{bn}_details", " ".join(details.split())]
    return out


def stage_industry_set(industry_yaml: Path, out_dir: Path,
                       tab_lines: dict[str, list[str]]) -> tuple[int, int]:
    """Write the .dat/.png of every object of one industry.yaml into out_dir."""
    spec = yaml.safe_load(industry_yaml.read_text(encoding="utf-8"))
    ok = fail = 0
    for obj in spec["objects"]:
        bn = industry_basename(spec, obj)
        png_src = industry_yaml.parent / "sprites" / f"{obj['sprite']}.png"
        if not png_src.exists():
            print(f"  [skip] {bn}: missing sprite {png_src}", file=sys.stderr)
            fail += 1
            continue
        shutil.copy2(png_src, out_dir / f"{bn}.png")
        (out_dir / f"{bn}.dat").write_text(emit_industry_dat(spec, obj), encoding="utf-8")
        for lang in TAB_LANGS:
            tab_lines[lang].extend(emit_industry_tab_entries(spec, obj, lang))
        ok += 1
    return ok, fail


# Languages emitted for each agency-mode pak. Filenames are <lang>.<pak_bn>.tab
# (e.g. cz.VZ-CeskeDrahy-rail.tab) — Simutrans's translator::load_files_from_folder
# only matches a DOT-separated language prefix/suffix, not the underscore form
# used by some upstream orphan files at the pak root. Czech uses 'cz' (not 'cs')
# to match this pak's language code. Encoding is UTF-8 with BOM: Simutrans
# auto-detects via is_unicode_file() and decodes correctly for both languages,
# so we keep full diacritics in both en and cz.
TAB_LANGS = ("en", "cz")
TAB_DIRNAME = "text"
UTF8_BOM = b"\xef\xbb\xbf"


def build_pak(agency: str, mode: str, family_yamls: list[Path]) -> tuple[int, int]:
    """Build a single agency-mode pak from the given family.yaml (or
    station.yaml / industry.yaml) files. Returns (succeeded, failed)
    liveries/objects."""
    pak_bn = pak_basename_for(agency, mode)
    out_dir = BUILD / pak_bn
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    DIST.mkdir(exist_ok=True)

    tab_lines: dict[str, list[str]] = {lang: [] for lang in TAB_LANGS}

    ok = fail = 0
    for fy in sorted(family_yamls):
        if fy.name in ("station.yaml", "industry.yaml"):
            if fy.name == "station.yaml":
                s_ok, s_fail = stage_station_set(fy, mode, out_dir, tab_lines)
            else:
                s_ok, s_fail = stage_industry_set(fy, out_dir, tab_lines)
            ok += s_ok
            fail += s_fail
            continue
        family = yaml.safe_load(fy.read_text(encoding="utf-8"))
        family_dir = fy.parent
        for livery in family["liveries"]:
            bn = basename_for(family, livery)
            png_src = family_dir / "sprites" / f"{livery['color']}.png"
            if not png_src.exists():
                print(f"  [skip] {bn}: missing sprite {png_src}", file=sys.stderr)
                fail += 1
                continue
            shutil.copy2(png_src, out_dir / f"{bn}.png")
            if family.get("windows_lit_when_loaded", False):
                write_unlit_png(png_src, out_dir / f"{bn}{UNLIT_SUFFIX}.png")
            (out_dir / f"{bn}.dat").write_text(emit_dat(family, livery), encoding="utf-8")
            for lang in TAB_LANGS:
                tab_lines[lang].extend(emit_tab_entries(family, livery, lang, mode))
            ok += 1

    if ok == 0:
        print(f"  [skip] {pak_bn}: no liveries built", file=sys.stderr)
        return ok, fail

    tab_out = DIST / TAB_DIRNAME
    tab_out.mkdir(exist_ok=True)
    for lang in TAB_LANGS:
        body = "\n".join(tab_lines[lang]) + "\n"
        (tab_out / f"{lang}.{pak_bn}.tab").write_bytes(UTF8_BOM + body.encode("utf-8"))

    pak = DIST / f"{pak_bn}.pak"
    makeobj = os.environ.get("MAKEOBJ_PATH", "makeobj")
    try:
        # makeobj on Windows silently writes an empty pak when given absolute,
        # backslash, or trailing-slashless input dir paths. So: forward slashes,
        # relative to ROOT, and a trailing slash on the input directory.
        rel_pak = pak.relative_to(ROOT).as_posix()
        rel_out = out_dir.relative_to(ROOT).as_posix() + "/"
        result = subprocess.run(
            [makeobj, "pak128", rel_pak, rel_out],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print(
            f"  [fail] {pak_bn}: makeobj not found (set MAKEOBJ_PATH or add it to PATH)",
            file=sys.stderr,
        )
        return 0, ok + fail

    if result.returncode != 0:
        print(f"  [fail] {pak_bn}: makeobj exit {result.returncode}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return 0, ok + fail

    print(f"  [ok]   {pak_bn} -> {pak.relative_to(ROOT)} ({ok} liveries)")
    return ok, fail


def all_families() -> list[Path]:
    """All family.yaml files under a vehicle-* root, station.yaml files
    under a station-* root and industry.yaml files under an industry-* root."""
    found = []
    for name, prefix in SOURCE_ROOTS.items():
        found += [
            p
            for p in ROOT.rglob(name)
            if p.relative_to(ROOT).parts and p.relative_to(ROOT).parts[0].startswith(prefix)
        ]
    return found


def group_by_agency_mode(family_yamls: list[Path]) -> dict[tuple[str, str], list[Path]]:
    groups: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for fy in family_yamls:
        data = yaml.safe_load(fy.read_text(encoding="utf-8"))
        groups[(group_for(fy, data), mode_for(fy))].append(fy)
    return groups


def select_target_groups(target: Path | None, all_groups: dict[tuple[str, str], list[Path]]) -> dict[tuple[str, str], list[Path]]:
    """If target is None, return every group. Otherwise expand the target up to
    the agency-mode pak(s) it belongs to: a family path picks its own group; an
    agency dir picks every group whose families live under it."""
    if target is None:
        return all_groups
    target = target.resolve()
    if not target.exists():
        print(f"no such path: {target}", file=sys.stderr)
        return {}

    if target.is_file() and target.name in SOURCE_ROOTS:
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
        key = (group_for(target, data), mode_for(target))
        return {key: all_groups.get(key, [])} if key in all_groups else {}

    if target.is_dir():
        selected: dict[tuple[str, str], list[Path]] = {}
        for key, fys in all_groups.items():
            if any(target in fy.parents for fy in fys):
                selected[key] = fys
        if selected:
            return selected

    print(f"no family.yaml, station.yaml or industry.yaml found at or under {target}", file=sys.stderr)
    return {}


def planned_pak_names(groups: dict[tuple[str, str], list[Path]]) -> set[str]:
    """Pak filenames the build is expected to produce in dist/ for the given
    agency-mode groups."""
    return {f"{pak_basename_for(a, m)}.pak" for (a, m) in groups}


def planned_tab_names(groups: dict[tuple[str, str], list[Path]]) -> set[str]:
    """Tab filenames the build is expected to produce in dist/text/."""
    return {
        f"{lang}.{pak_basename_for(a, m)}.tab"
        for (a, m) in groups
        for lang in TAB_LANGS
    }


def prune_stale_artifacts(planned_paks: set[str], planned_tabs: set[str]) -> int:
    """Delete VZ-*.pak files in dist/ and <lang>.VZ-*.tab files in dist/text/
    that no longer match a planned output for any agency-mode group."""
    count = 0
    if DIST.is_dir():
        for pak in DIST.glob("VZ-*.pak"):
            if pak.name not in planned_paks:
                pak.unlink()
                print(f"pruned stale {pak.relative_to(ROOT)}")
                count += 1
    tab_dir = DIST / TAB_DIRNAME
    if tab_dir.is_dir():
        for lang in TAB_LANGS:
            for tab in tab_dir.glob(f"{lang}.VZ-*.tab"):
                if tab.name not in planned_tabs:
                    tab.unlink()
                    print(f"pruned stale {tab.relative_to(ROOT)}")
                    count += 1
    return count


def _collect_paks(directory: Path) -> dict[str, Path]:
    """Map filename -> path for every VZ-*.pak in directory."""
    if not directory.is_dir():
        return {}
    return {p.name: p for p in directory.glob("VZ-*.pak")}


def _collect_tabs(directory: Path) -> dict[str, Path]:
    """Map filename -> path for every <lang>.VZ-*.tab in directory."""
    if not directory.is_dir():
        return {}
    found: dict[str, Path] = {}
    for lang in TAB_LANGS:
        for p in directory.glob(f"{lang}.VZ-*.tab"):
            found[p.name] = p
    return found


# Legacy filenames previously written to the pak root by older build.py versions.
# They were never loaded by Simutrans (wrong location, wrong filename convention),
# but they linger in PAK_TARGET_DIR and should be cleaned up on install.
_LEGACY_TAB_PATTERNS = ("en_VZ-*.tab", "cz_VZ-*.tab", "VZ-*.en.tab", "VZ-*.cs.tab")


def install_paks(target_dir: Path, assume_yes: bool) -> int:
    """Sync VZ-*.pak from dist/ into target_dir and <lang>.VZ-*.tab from
    dist/text/ into target_dir/text/.

    Any VZ artifact in either target location without a counterpart in dist is
    an orphan; prompt once before deleting (``assume_yes`` skips the prompt).
    Returns the count of files copied."""
    dist_paks = _collect_paks(DIST)
    dist_tabs = _collect_tabs(DIST / TAB_DIRNAME)
    target_text = target_dir / TAB_DIRNAME

    pak_orphans = [
        p for n, p in sorted(_collect_paks(target_dir).items()) if n not in dist_paks
    ]
    tab_orphans = [
        p for n, p in sorted(_collect_tabs(target_text).items()) if n not in dist_tabs
    ]
    # Legacy tabs at the pak root from old build.py versions are always orphans.
    legacy_orphans: list[Path] = []
    for pattern in _LEGACY_TAB_PATTERNS:
        legacy_orphans.extend(target_dir.glob(pattern))
    orphans = pak_orphans + tab_orphans + legacy_orphans

    if orphans:
        print(f"\n{len(orphans)} VZ artifact(s) in {target_dir} have no match in dist/:")
        for o in orphans:
            print(f"  - {o.relative_to(target_dir)}")
        if assume_yes:
            print("  (auto-deleting, -y given)")
            delete = True
        else:
            try:
                ans = input("Delete these orphans? [y/N] ").strip().lower()
            except EOFError:
                ans = ""
            delete = ans in ("y", "yes")
        if delete:
            for o in orphans:
                o.unlink()
                print(f"  removed {o.relative_to(target_dir)}")
        else:
            print("  keeping orphans")

    copied = 0
    for name, src in sorted(dist_paks.items()):
        shutil.copy2(src, target_dir / name)
        copied += 1
    if dist_tabs:
        target_text.mkdir(exist_ok=True)
        for name, src in sorted(dist_tabs.items()):
            shutil.copy2(src, target_text / name)
            copied += 1
    if copied:
        print(f"\ninstalled {copied} file(s) to {target_dir}")
    return copied


def run_install(assume_yes: bool) -> None:
    target = os.environ.get("PAK_TARGET_DIR")
    if not target:
        print("\nPAK_TARGET_DIR not set — skipping install step")
        return
    target_dir = Path(target)
    if not target_dir.is_dir():
        print(
            f"\nPAK_TARGET_DIR={target} does not exist or is not a directory — "
            "skipping install step",
            file=sys.stderr,
        )
        return
    install_paks(target_dir, assume_yes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build VZ pak128 addons.")
    parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        help="Optional path to narrow the build. Resolves to the agency-mode pak(s) it belongs to.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe build/ and dist/ before building.",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip copying built paks into PAK_TARGET_DIR even when it is set.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Auto-confirm orphan deletion during the install step.",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    if args.clean:
        for d in (BUILD, DIST):
            if d.exists():
                shutil.rmtree(d)
                print(f"cleaned {d.relative_to(ROOT)}")

    families = all_families()
    if not families:
        print("no families found", file=sys.stderr)
        return 1

    all_groups = group_by_agency_mode(families)
    prune_stale_artifacts(planned_pak_names(all_groups), planned_tab_names(all_groups))

    target_groups = select_target_groups(args.target, all_groups)
    if not target_groups:
        return 1

    total_ok = total_fail = 0
    for (agency, mode), fys in sorted(target_groups.items()):
        pak_bn = pak_basename_for(agency, mode)
        family_list = ", ".join(sorted(fy.parent.name for fy in fys))
        print(f"== {pak_bn} ({family_list}) ==")
        ok, fail = build_pak(agency, mode, fys)
        total_ok += ok
        total_fail += fail

    print(f"\nbuilt {total_ok} liveries | failed {total_fail}")

    if total_fail == 0 and not args.no_install:
        run_install(assume_yes=args.yes)

    return 0 if total_fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
