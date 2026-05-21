# simutrans-custom-czech-pak128

A custom Czech addon set for [Simutrans (Extended)](https://www.simutrans.com/) pak128.
Ships Czech rail, bus, and tram vehicles (and eventually water / air) in real-world
liveries, matching pak128 art conventions.

The addon prefix `VZ-` is used on every shipped `.pak` so the set never collides with
the upstream pak being shadowed.

> **Status:** early development. `main` ships only the families considered production-
> ready; everything else lives on the [`inprogress`](../../tree/inprogress) branch.

## What `main` currently ships

A single pak file per agency and transport mode — for example, every shipped
ČD rail family lives in `dist/VZ-CeskeDrahy-rail.pak`.

| Family | Liveries on `main` |
| --- | --- |
| ČD řada 814.0 (RegioNova) | žluto-zelená, Najbrt 2, Plzeňský kraj, Pardubický kraj, Kraj Vysočina, PID šedo-červená |
| ČD řada 814.2 (RegioNova Trio) | žluto-zelená, Najbrt 2, PID šedo-červená |
| ČD řada 642 (Siemens Desiro Classic) | DÚK zeleno-bílá |
| ČD řada 840 (Stadler RegioSpider) | Najbrt 1 |
| ČD řada 841 (Stadler RegioSpider) | Najbrt 1 |
| ČD řada 841.2 (Stadler RegioSpider) | DÚK zeleno-bílá, HZL krémovo-červená, Pardubický kraj, PID šedo-červená |
| DPmML Irisbus Citelis 12M (bus) | Most žluto-červená |
| DPmML SOR NBG 12 (bus) | Most žluto-červená |
| DPmML Iveco Urbanway 18M (bus) | Most žluto-červená |
| DPmML Inekon EVO 2 (tram) | Most žluto-červená |
| DPmML Tatra T3 (tram) | Most žluto-červená |
| DPmML Pragoimex Vario LF (tram) | Most žluto-červená |

Additional vehicle families are in progress and live on the
[`inprogress`](../../tree/inprogress) branch.

## Requirements

- Python 3.7+
- [`pyyaml`](https://pypi.org/project/PyYAML/) (`pip install pyyaml`)
- `makeobj` from a matching Simutrans build, on `PATH` or pointed to by
  `MAKEOBJ_PATH` (see [Configuration](#configuration))

## Configuration

`build.py` auto-loads a `.env` file from the project root on startup. Copy the
template and edit:

```sh
cp .env.example .env
```

Variables:

| Variable | Purpose |
| --- | --- |
| `MAKEOBJ_PATH` | Absolute path to the matching Simutrans `makeobj` binary. If unset, the build runs `makeobj` from `PATH`. |
| `PAK_TARGET_DIR` | Optional. Absolute path to your Simutrans pakset / addons directory. When set, the build syncs `dist/VZ-*.pak` there after each successful run (see [Install step](#install-step)). |

Variables already set in the process environment take precedence over `.env`.
`.env` is git-ignored; `.env.example` is the template that's committed.

## Install step

If `PAK_TARGET_DIR` points to an existing directory, after a successful build
`build.py` syncs the freshly built `.pak` files into it:

1. Scans the target for `VZ-*.pak` files with **no matching file in `dist/`**
   (orphans — likely paks from a deleted family or a renamed agency-mode group).
2. If any orphans exist, prints the list and prompts before deleting them.
   Pass `-y` (or `--yes`) to auto-confirm. Answer `n` (the default) to keep them.
3. Copies every `dist/VZ-*.pak` into the target, overwriting any same-named file.

If `PAK_TARGET_DIR` is unset, missing, or you pass `--no-install`, the install
step is skipped silently.

## Building

```sh
python build.py                # build every agency-mode pak
python build.py --clean        # wipe build/ and dist/ first
python build.py <path>         # narrow to the agency-mode pak that contains
                               # <path> (family.yaml, family dir, or agency dir)
python build.py --no-install   # skip the post-build install step
python build.py -y             # auto-confirm orphan deletion during install

# Windows
.\build.ps1                    # same arguments
```

Each run also auto-prunes any stale `VZ-*.pak` in `dist/` that no longer matches
a current agency-mode group (for instance, legacy per-livery paks).

Final `.pak` files land in `dist/` — one per agency × transport mode, e.g.
`VZ-CeskeDrahy-rail.pak`. Drop them into your Simutrans `addons/pak128/` folder
(or the equivalent for your install).

## How the build works

`.dat`, `.tab`, and `.pak` files are **generated** from one `family.yaml` per
vehicle family. The build script groups families by `(agency, transport-mode)`,
expands every livery into a shared `build/VZ-<Agency>-<mode>/` directory, and
calls `makeobj` once per group to produce `dist/VZ-<Agency>-<mode>.pak`.

**Do not hand-edit `.dat` or `.tab` files** — edit the `family.yaml` or the per-livery
PNG instead. The full schema, naming convention, sprite layout, and multi-vehicle
consist rules are documented in [`CLAUDE.md`](CLAUDE.md).

## Directory layout

```
simutrans-custom-czech-pak128/
├── build.py, build.ps1        # build entry points
├── CLAUDE.md                  # full project conventions / schema reference
├── vehicle-rail/              # one folder per transport mode
│   └── <agency>/<family>/
│       ├── family.yaml        # data model: base + liveries
│       └── sprites/<color>.png
├── build/                     # generated source trees (git-ignored)
└── dist/                      # final .pak files (git-ignored)
```

Other transport-mode roots (`vehicle-road/`, `vehicle-water/`, `vehicle-air/`) are
supported by the build script — the agency level is purely organizational and the
build walks every `vehicle-*/.../family.yaml` regardless of depth.

## Naming convention

**Pak filename** (one per agency × transport-mode): `VZ-<Agency>-<mode>.pak` —
for example `dist/VZ-CeskeDrahy-rail.pak`.

**Object basename** (inside the pak, for `name=`, sprite refs, and per-livery
PNGs in the build dir): `VZ-<Agency>-<Type>-<Color>` — for example
`VZ-CeskeDrahy-814_0-zlutozelena`.

- **Agency** — PascalCase Czech operator name (`CeskeDrahy`, `RegioJet`, `LeoExpress`, `DPP`, …)
- **mode** — transport mode slug derived from the `vehicle-*/` folder (`rail`, `road`, `water`, `air`)
- **Type** — class designation; dots replaced with underscores (`814.0` → `814_0`)
- **Color** — livery name in Czech without diacritics (`zlutozelena`, `najbrt2`, …)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). In short: edit `family.yaml` or PNGs, never
the generated `.dat` / `.tab` files; keep PNGs at 128×128 per tile, RGB
`(231, 255, 255)` for transparency; use the `VZ-` prefix on everything shipped.

## License

Released under the [Artistic License 1.0](LICENSE), the convention for Simutrans
paksets.

Each generated object carries the **original upstream credit first** (set via
`family.copyright` in YAML — e.g. `Sim`) plus `vojtechzicha`, comma-separated, so
attribution is preserved end-to-end through the build.

## Acknowledgements

- The Simutrans and Simutrans Extended teams for the engine and the tooling
- Upstream pak128 / pak128.CS / pak128_czr artists whose work is credited per
  object via the `copyright=` field in each generated `.dat`
