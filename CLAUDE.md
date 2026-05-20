# simutrans-custom-czech-pak128

Custom Czech addon set for Simutrans (Extended) pak128. Maintained by vojtechzicha.

## How the build works

`.dat`, `.tab`, and per-livery `.pak` files are **generated**, not hand-written. Each vehicle family is described once in a `family.yaml`; the build script (`build.py`) expands that file across every livery, drops the result into `build/<basename>/`, and invokes `makeobj` to produce `dist/<basename>.pak`.

```
python build.py                # build everything
python build.py --clean        # wipe build/ and dist/ first
python build.py <family-dir>   # build one family
.\build.ps1                    # PowerShell wrapper, same args
```

`makeobj` is located via the `MAKEOBJ_PATH` environment variable; if unset, the build runs `makeobj` from `PATH`. Requires `pyyaml` (`pip install pyyaml`) and Python 3.7+.

**Do not hand-edit `.dat` or `.tab` files.** Edit the relevant `family.yaml` or the per-livery PNG instead.

## File-naming convention

`VZ-<Agency>-<Type>-<Color>`

- `Agency` — PascalCase Czech transport agency name (e.g. `CeskeDrahy`, `RegioJet`, `LeoExpress`, `DPP`).
- `Type` — class designation of the lead/named unit of the family; dots replaced with underscores (e.g. `814.0` → `814_0`).
- `Color` — livery name in Czech without diacritics (e.g. `zlutozelena`, `modra`, `cervena`, `najbrt2`).

Generated extensions per livery: `.dat`, `.png`, `.en.tab`, `.cs.tab`, `.pak`. A single `.dat` + `.png` pair holds the entire matched set (e.g. cab + motor of one DMU).

## Directory layout

```
simutrans-custom-czech-pak128/
  build.py, build.ps1, .gitignore, CLAUDE.md
  build/                          # generated per-livery source trees (git-ignored)
  dist/                           # final .pak files (git-ignored)
  vehicle-rail/                   # one folder per transport mode
    <agency>/                     # e.g. ceske-drahy/  — pure container, no files
      <family>/                   # e.g. 814_0/  — one vehicle family
        family.yaml               # data model: base + liveries
        sprites/
          <color>.png             # one consolidated 1024×N PNG per livery
```

Transport modes: `vehicle-rail/`, `vehicle-road/`, `vehicle-water/`, `vehicle-air/`. The build script walks every `vehicle-*/...family.yaml` regardless of depth, so the agency level is purely organizational. Family folder names are conventionally the slugified type (`814.0` → `814_0`) so they match the generated `.pak` filename.

## `family.yaml` schema

```yaml
agency: CeskeDrahy            # PascalCase, goes into basename verbatim
type: "814.0"                 # used as basename Type token; dots → underscores when emitted
copyright: Sim                # original upstream credit; build appends ", vojtechzicha"

display:
  agency_en: "ČD"
  agency_cs: "ČD"
  family_en: "RegioNova"
  family_cs: "RegioNova"

vehicles:
  - id: "914"                 # unique key; suffix on object name=; dots → underscores
    role_en: "cab car"
    role_cs: "řídicí vůz"
    row: 0                    # row in sprites/<color>.png (0-indexed)
    # Optional:
    # display_id: "914"       # override id for display strings (used when id has a -front/-rear discriminator)
    # head: true              # whether Constraint[Prev] gets `none` (default true)
    # tail: true              # whether Constraint[Next] gets `none` (default true)
    # prev: ["partner_id", …] # explicit Constraint[Prev] partners (default: all OTHER vehicles in family)
    # next: ["partner_id", …] # explicit Constraint[Next] partners (default: all OTHER vehicles in family)
    # reverse: false          # if true, share another row's sprites but rotate direction labels 180°
    #                         # (col index shifts by +4 mod 8 — used for the rear motor of a trio)
    fields:                   # core simutrans vehicle fields, emitted in order
      cost: 979000
      payload: 97
      …
    extended:                 # `# extended` section; omit/empty to skip entirely
      axles: 2

  - id: "814.0"
    …

liveries:
  - color: zlutozelena
    name_en: "yellow-green"
    name_cs: "žluto-zelená"
  - color: najbrt2
    name_en: "Najbrt 2"
    name_cs: "Najbrt 2"
```

Vehicle IDs keep their natural form with dots (`"814.0"`) in YAML; the build emits the dot→underscore conversion only where required (filename and object `name=`). Display strings in `.tab` files use the dotted form (or `display_id` if set).

Canonical examples: `vehicle-rail/ceske-drahy/814_0/family.yaml` (simple 2-car push-pull), `vehicle-rail/ceske-drahy/814_2/family.yaml` (3-car trio with separate front/rear motor definitions).

## Object naming inside `.dat`

The `name=` field is `<basename>-<id_underscored>`. Every object in a multi-vehicle file gets a unique suffix. Examples:

- `VZ-CeskeDrahy-814_0-zlutozelena-914`    (control trailer, class 914)
- `VZ-CeskeDrahy-814_0-zlutozelena-814_0`  (motor car, class 814.0)

## Copyright

Every object's `copyright=` line carries the **original upstream credit first**, then `vojtechzicha` at the end, comma-separated. The build assembles this from `family.copyright` automatically. Example: `copyright=Sim, vojtechzicha`.

## Sprites / PNG

- One PNG per livery, located at `<family>/sprites/<color>.png`. Pre-composited at the final size — the build copies it verbatim.
- Tile size is 128×128 (pak128). Width is `8 × 128 = 1024 px`; height is `vehicles × 128 px`.
- **One set of images per vehicle** — `emptyimage` only, no `freightimage`.
- Rows in the PNG correspond to vehicles in `family.yaml`, in declaration order. The DAT references tiles via `<basename>.<row>.<col>`.
- Column ordering is the Simutrans 8-direction convention: `0=w, 1=nw, 2=n, 3=ne, 4=e, 5=se, 6=s, 7=sw`.
- Drop any source columns/rows that are not referenced — upstream files often include a 9th column of stacked extras intended for other pak sizes.
- Background transparent color is RGB `(231, 255, 255)`; preserve it when compositing or recoloring.

## Multi-vehicle consists

This Simutrans build does **not** support `bidirectional=1` (auto-flip) or `can_lead_from_rear=1`. Don't emit them. Multi-vehicle consists are modelled by **separate vehicle definitions per consist position**, each with its own sprite row.

### Simple 2-car (cab + motor), e.g. 814.0

The cab and motor sprite series in the source already have their cabs at opposite physical ends, so one definition per vehicle is enough. Each gets reciprocal constraints with `none`:

```
Constraint[Prev][0]=none
Constraint[Prev][1]=<partner>
Constraint[Next][0]=none
Constraint[Next][1]=<partner>
```

The depot builds the consist in either order. Note: with no `bidirectional` support, sprites are correct only in the consist's natural direction of travel; the reverse direction will look as if the vehicles are moving backwards (the cabs don't visually flip). That matches Simutrans's standard behavior for non-bidirectional vehicles.

### Trio with end-pieces (motor + middle + motor), e.g. 814.2

The two motor cars sit at opposite ends with cabs pointing outward — visually identical but mirrored. We model this with **two motor definitions** (`-front` and `-rear`) that **share the same sprite row** but emit shifted direction indices via `reverse: true`. The PNG only needs one motor row plus one middle row.

How the index shift works: every Simutrans 8-direction column gets remapped by +4 (mod 8) for the reversed vehicle, so the rear motor's `[w]` direction draws the front motor's column-4 (`[e]`) sprite, etc. The result: the rear motor's cab appears on the opposite physical end from the front motor in every compass direction.

```yaml
vehicles:
  - id: "814.2-front"
    display_id: "814.2"        # display strings still say "Class 814.2"
    row: 0
    head: true                 # Constraint[Prev][0]=none
    tail: false                # NO Constraint[Next][0]=none
    prev: []                   # nothing valid in front (must be at head)
    next: ["014"]              # only the middle car can follow
    …

  - id: "014"
    row: 1
    head: false                # cannot lead
    tail: false                # cannot trail
    prev: ["814.2-front"]
    next: ["814.2-rear"]
    …

  - id: "814.2-rear"
    display_id: "814.2"
    row: 0                     # same row as front motor
    reverse: true              # shifts column indices by +4
    head: false
    tail: true
    prev: ["014"]
    next: []
    …
```

PNG layout: row 0 = motor sprites, row 1 = middle sprites. Total 1024×256.

With these constraints, the only buildable consist is `front + middle + rear`.

## Localization

For each `<basename>.dat`, the build emits `<basename>.en.tab` and `<basename>.cs.tab`. Each `.tab` file:

```
# Language: <Name>

<object name #1>
<display name in this language>

<object name #2>
<display name in this language>
```

Display string templates (built into `build.py`):
- EN: `<agency_en> Class <id> <family_en> <role_en> (<name_en>)`
- CS: `<agency_cs> řada <id> <family_cs> <role_cs> (<name_cs>)`

`<id>` uses the natural dotted form (e.g. `Class 814.0`). Encoding: UTF-8 (no BOM). Czech display strings use full diacritics; diacritics-free forms are reserved for filenames and object `name=`.

### Livery `name_en` / `name_cs` convention

Translate color descriptions; keep proper nouns (agency names, region names, designer names) in Czech in both languages.

- `žluto-zelená` → `name_en: "yellow-green"` (color: translated)
- `šedo-červená` → `name_en: "grey-red"` (color: translated)
- `PID šedo-červená` → `name_en: "PID grey-red"` (PID kept; color translated)
- `Plzeňský kraj`, `Pardubický kraj`, `Kraj Vysočina` → `name_en` stays identical to `name_cs` (region names not translated, retain diacritics)
- `Najbrt 2` → `name_en` stays identical to `name_cs` (designer name)

## Scope rules

- Only ship variants the user has explicitly asked for. Upstream sets often include trio, bike-carrier, etc. variants — leave them out unless requested.
- Strip unreferenced sprite columns/rows; keep PNGs minimal.
- All addon assets use the `VZ-` filename prefix so this addon set never collides with the upstream pak being shadowed.
