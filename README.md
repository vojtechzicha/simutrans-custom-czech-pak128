# simutrans-custom-czech-pak128

A custom Czech addon set for [Simutrans (Extended)](https://www.simutrans.com/) pak128.
Ships Czech rail vehicles (and eventually road / water / air) in real-world liveries,
matching pak128 art conventions.

The addon prefix `VZ-` is used on every shipped `.pak` so the set never collides with
the upstream pak being shadowed.

> **Status:** early development. `main` ships only the families considered production-
> ready; everything else lives on the [`inprogress`](../../tree/inprogress) branch.

## What `main` currently ships

| Family | Liveries on `main` |
| --- | --- |
| ČD řada 814.0 (RegioNova) | žluto-zelená, Najbrt 2, Plzeňský kraj, Pardubický kraj, Kraj Vysočina, PID šedo-červená |
| ČD řada 814.2 (RegioNova Trio) | žluto-zelená, Najbrt 2, PID šedo-červená |
| ČD řada 642 (Siemens Desiro Classic) | DÚK zeleno-bílá |

Additional vehicle families are in progress and live on the
[`inprogress`](../../tree/inprogress) branch.

## Requirements

- Python 3.7+
- [`pyyaml`](https://pypi.org/project/PyYAML/) (`pip install pyyaml`)
- `makeobj` from a matching Simutrans build, on `PATH` or pointed to by
  `MAKEOBJ_PATH`

## Building

```sh
python build.py                # build every family across every livery
python build.py --clean        # wipe build/ and dist/ first
python build.py <family-dir>   # build a single family

# Windows
.\build.ps1                    # same arguments
```

Final `.pak` files land in `dist/`. Drop them into your Simutrans `addons/pak128/`
folder (or the equivalent for your install).

## How the build works

`.dat`, `.tab`, and per-livery `.pak` files are **generated** from a single
`family.yaml` per vehicle family. The build script expands that file across every
livery into `build/<basename>/`, then calls `makeobj` to produce
`dist/<basename>.pak`.

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

## File-naming convention

`VZ-<Agency>-<Type>-<Color>` — for example `VZ-CeskeDrahy-814_0-zlutozelena.pak`.

- **Agency** — PascalCase Czech operator name (`CeskeDrahy`, `RegioJet`, `LeoExpress`, `DPP`, …)
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
