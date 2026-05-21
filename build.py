#!/usr/bin/env python3
"""Build script for the VZ pak128 addon set.

Walks every ``vehicle-*/.../family.yaml`` under the project root, groups them by
(agency, mode), and emits one ``.pak`` per group into ``dist/`` — e.g.
``dist/VZ-CeskeDrahy-rail.pak`` contains every family and livery for ČD's rail
fleet. Per-livery DAT / PNG files live side-by-side inside one shared build
directory so a single ``makeobj`` invocation bundles them.

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


def mode_for(family_yaml: Path) -> str:
    """Derive the transport mode from the top-level folder (vehicle-rail → rail)."""
    rel = family_yaml.relative_to(ROOT)
    top = rel.parts[0]
    assert top.startswith("vehicle-"), f"unexpected top folder: {top}"
    return top[len("vehicle-"):]


def pak_basename_for(agency: str, mode: str) -> str:
    """The output .pak basename: VZ-<Agency>-<mode>."""
    return f"VZ-{agency}-{mode}"


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
        obj_name = f"{bn}-{slug(v['id'])}"
        if use_class:
            disp_id = v.get("display_id", v["id"])
            display = f"{agency} {class_word} {disp_id} {fam_name} {v[role_key]} ({livery_name})"
        else:
            display = f"{agency} {fam_name} {v[role_key]} ({livery_name})"
        out.append(obj_name)
        out.append(display)
    return out


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
    """Build a single agency-mode pak from the given family.yaml files.
    Returns (succeeded_liveries, failed_liveries)."""
    pak_bn = pak_basename_for(agency, mode)
    out_dir = BUILD / pak_bn
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    DIST.mkdir(exist_ok=True)

    tab_lines: dict[str, list[str]] = {lang: [] for lang in TAB_LANGS}

    ok = fail = 0
    for fy in sorted(family_yamls):
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
    """All family.yaml files anywhere under a vehicle-* root."""
    return [
        p
        for p in ROOT.rglob("family.yaml")
        if p.relative_to(ROOT).parts and p.relative_to(ROOT).parts[0].startswith("vehicle-")
    ]


def group_by_agency_mode(family_yamls: list[Path]) -> dict[tuple[str, str], list[Path]]:
    groups: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for fy in family_yamls:
        family = yaml.safe_load(fy.read_text(encoding="utf-8"))
        groups[(family["agency"], mode_for(fy))].append(fy)
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

    if target.is_file() and target.name == "family.yaml":
        family = yaml.safe_load(target.read_text(encoding="utf-8"))
        key = (family["agency"], mode_for(target))
        return {key: all_groups.get(key, [])} if key in all_groups else {}

    if target.is_dir():
        selected: dict[tuple[str, str], list[Path]] = {}
        for key, fys in all_groups.items():
            if any(target in fy.parents for fy in fys):
                selected[key] = fys
        if selected:
            return selected

    print(f"no family.yaml found at or under {target}", file=sys.stderr)
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
