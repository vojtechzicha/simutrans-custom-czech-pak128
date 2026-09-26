# simutrans-custom-czech-pak128

Custom Czech addon set for Simutrans (Extended) pak128. Maintained by vojtechzicha.

## How the build works

`.dat`, `.tab`, and `.pak` files are **generated**, not hand-written. Each vehicle family is described once in a `family.yaml`; the build script (`build.py`) groups families by `(agency, transport-mode)`, expands every livery, drops the result into a shared `build/VZ-<Agency>-<mode>/` directory, and invokes `makeobj` once per group to produce `dist/VZ-<Agency>-<mode>.pak`.

```
python build.py                # build every agency-mode pak
python build.py --clean        # wipe build/ and dist/ first
python build.py <path>         # narrow to one agency-mode pak (family dir,
                               # family.yaml, or agency dir all work — the
                               # target is always expanded to the full
                               # agency-mode group, never partial)
python build.py --no-install   # skip the post-build install step
python build.py -y             # auto-confirm orphan deletion during install
.\build.ps1                    # PowerShell wrapper, same args
```

On every run the build also **auto-prunes** stale artifacts in `dist/`: any `dist/VZ-*.pak` or `dist/text/<lang>.VZ-*.tab` whose name no longer matches a current agency-mode group is deleted so `dist/` stays in sync with the source tree.

After a successful build, if `PAK_TARGET_DIR` is set in `.env` (or the process environment) and points to an existing directory, `build.py` syncs both layers into it: `dist/VZ-*.pak` → `PAK_TARGET_DIR/`, and `dist/text/<lang>.VZ-*.tab` → `PAK_TARGET_DIR/text/`. Tabs MUST live in the pak's `text/` subfolder and use a dot-separated language prefix (`cz.VZ-…tab`, not `cz_VZ-…tab`) — Simutrans's `translator::load_files_from_folder` only scans `text/*.tab` and only matches the dot form. Any VZ artifact in the target without a counterpart in `dist/` is an orphan and the user is prompted before it's deleted (`-y` auto-confirms); legacy tab filenames at the pak root from older build.py versions (`<lang>_VZ-*.tab`, `VZ-*.<lang>.tab`) are also swept up. If `PAK_TARGET_DIR` is unset, missing, or `--no-install` is passed, the install step is skipped.

`makeobj` is located via the `MAKEOBJ_PATH` environment variable; if unset, the build runs `makeobj` from `PATH`. Requires `pyyaml` and `Pillow` (`pip install pyyaml pillow`) and Python 3.7+.

**Do not hand-edit `.dat` or `.tab` files.** Edit the relevant `family.yaml` or the per-livery PNG instead.

## Naming convention

Two distinct names matter — one for the shipped `.pak` and one for individual objects/sprites inside it.

**Pak filename** (one per agency × transport-mode): `VZ-<Agency>-<mode>.pak`

- `Agency` — PascalCase Czech transport agency name (e.g. `CeskeDrahy`, `RegioJet`, `LeoExpress`, `DPP`).
- `mode` — the `vehicle-*/` root folder slug without the `vehicle-` prefix (`rail`, `road`, `water`, `air`).
- Example: `dist/VZ-CeskeDrahy-rail.pak` contains every ČD rail family and every livery thereof.

**Object basename** (used for `name=`, per-livery PNG file inside the build dir, and sprite refs in `.dat`): `VZ-<Agency>-<Type>-<Color>`

- `Type` — class designation of the lead/named unit of the family; dots replaced with underscores (e.g. `814.0` → `814_0`).
- `Color` — livery name in Czech without diacritics (e.g. `zlutozelena`, `najbrt2`, `pidsedocervena`).
- Final object `name=` adds the per-vehicle id suffix: `VZ-CeskeDrahy-814_0-zlutozelena-914`.

A single `family.yaml` + `<color>.png` pair holds the entire matched set (e.g. cab + motor of one DMU). The build emits one `.dat` + one `.png` per family×livery inside the shared agency-mode build dir, plus one `.en.tab` and one `.cs.tab` per agency-mode pak listing every object's display string.

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

Transport modes: `vehicle-rail/`, `vehicle-bus/`, `vehicle-tram/`, `vehicle-water/`, `vehicle-air/` (plus any future `vehicle-trolleybus/` etc.). Bus and tram are split into their own modes rather than bundled under a generic `vehicle-road/` so trolleybuses can later live alongside buses without mixing rolling stock. The build script walks every `vehicle-*/...family.yaml` regardless of depth and groups by the `agency:` field plus the `vehicle-*` mode root. Family folder names are conventionally the slugified type (`814.0` → `814_0`); the agency folder name is organizational only — the canonical agency identifier is the `agency:` field inside `family.yaml`. Station objects live in parallel `station-*/` roots and city industries in `industry-*/` roots (see "Stations" and "Industries" below).

## `family.yaml` schema

```yaml
agency: CeskeDrahy            # PascalCase, goes into basename verbatim
type: "814.0"                 # used as basename Type token; dots → underscores when emitted
copyright: Sim                # original upstream credit; build appends ", vojtechzicha"
# image_offset: [0, 4]        # optional x,y pixel offset makeobj applies to every image
#                             # (default [0, 4], suited to the rail sources); road families
#                             # whose sprites are already placed at the native pak128.cs
#                             # lane position use [0, 0]
# windows_lit_when_loaded: true  # the sheet as drawn becomes the loaded (freight) image and
#                             # the build derives an empty image whose window glass never
#                             # lights up; see "Night-lit windows" below

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
    #                         # a partner "<family folder>/<id>" names a vehicle of a SIBLING family in the
    #                         # same agency-mode pak (e.g. prev: ["t3r_p/T3R.P"] lets a T3R.PLF couple with
    #                         # a T3R.P); it resolves to the same livery and is skipped where the sibling
    #                         # lacks that livery. Declare it on both vehicles (Prev and Next must agree).
    # prev: any / next: any   # no constraint on that side at all: couples with anything, like native
    #                         # locomotives and coaches (loco-hauled stock, the front of a Talgo set)
    # reverse: false          # if true, share another row's sprites but rotate direction labels 180°
    #                         # (col index shifts by +4 mod 8 — used for the rear motor of a trio)
    # couple_liveries: false  # if true, each prev/next partner id resolves to that vehicle in EVERY
    #                         # livery of the family, so cars of different paint can couple into one
    #                         # consist (e.g. a tram that runs solo or as a mixed-livery 2-car set)
    #                         # `prev` / `next` limit it to that side: multiple units of any livery
    #                         # couple end to end (lead car `prev`, rear car `next`) while the cars
    #                         # inside one unit match, so the depot still auto-completes a unit
    # liveries: [color, …]    # only build this vehicle in the listed liveries (default: all), e.g. a
    #                         # trailer that never wore a railcar's regional scheme (810 family's 010).
    #                         # Partner constraints skip liveries the partner doesn't exist in, and
    #                         # the sheets of the other liveries don't need its row
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

The `name=` field is `<object-basename>-<id_underscored>`, where the object basename is the per-livery `VZ-<Agency>-<Type>-<Color>` form (not the agency-mode pak basename). Every object in a multi-vehicle file gets a unique suffix. Examples:

- `VZ-CeskeDrahy-814_0-zlutozelena-914`    (control trailer, class 914)
- `VZ-CeskeDrahy-814_0-zlutozelena-814_0`  (motor car, class 814.0)

Object names are stable across the per-livery → per-agency-mode pak repackaging: existing savegames that reference these names continue to work.

## Copyright

Every object's `copyright=` line carries the **original upstream credit first**, then `vojtechzicha` at the end, comma-separated. The build assembles this from `family.copyright` automatically. Example: `copyright=Sim, vojtechzicha`.

## Sprites / PNG

- One PNG per livery, located at `<family>/sprites/<color>.png`. Pre-composited at the final size — the build copies it verbatim.
- Tile size is 128×128 (pak128). Width is `8 × 128 = 1024 px`; height is `vehicles × 128 px`.
- **One set of images per vehicle** in the source PNG. The build may derive a second set from it (see "Night-lit windows"); never draw a separate loaded/empty sheet.
- Rows in the PNG correspond to vehicles in `family.yaml`, in declaration order. The DAT references tiles via `<basename>.<row>.<col>`.
- Column ordering is the Simutrans 8-direction convention: `0=w, 1=nw, 2=n, 3=ne, 4=e, 5=se, 6=s, 7=sw`.
- Drop any source columns/rows that are not referenced — upstream files often include a 9th column of stacked extras intended for other pak sizes.
- Background transparent color is RGB `(231, 255, 255)`; preserve it when compositing or recoloring.
- Some exact RGB values are Simutrans **special colours** (`image_t::rgbtab`): makeobj stores them as player colours, lamps or night-lit windows instead of plain pixels. Avoid them unless intended; notably plain `0x6B6B6B` / `0x9B9B9B` become non-darkening greys (use `0x6B6B6C` etc.). `tools/pak_extract.py` writes extracted specials as their exact rgbtab colour so they round-trip.

### Night-lit windows

Convention: a vehicle's windows light up at night **only while passengers are aboard**.

- Draw all window glass in the lit-at-night specials: `0x4D4D4D` (special 28, dark grey by day, warm yellow at night) for glass, `0x57656F` (special 16) for lighter glass/reflections. Headlights `0xFFFF53` and tail lights `0xFF211D` are always lit and unaffected.
- Set `windows_lit_when_loaded: true` in `family.yaml` (every family does). The build then copies the sheet as the loaded image (`freightimage`, shown whenever at least one passenger is aboard) and writes a derived `<basename>-unlit.png` for `emptyimage`, where each lit-window special is swapped for a plain colour one step away (`0x4D4D4D` → `0x4D4D4E`, …). The two look identical by day; at night only a loaded vehicle's windows glow.
- Needs Pillow at build time.

### Rendered rail sprites (`tools/railrender/`)

The Leo Express families (`vehicle-rail/leo-express/`) are original art rendered from box models, not painted: `render.py` is an orthographic box raycaster in the pak128 projection, and `railkit.py` calibrates it to native pak128.cs rail art. That calibration covers the front anchor per view (source-sheet pixels before the default rail `image_offset` [0, 4]), body half-width 0.92 carunit, side wall height 10 model px, the ne/sw views drawn 18 % taller, and per-face shading. It fits CD_Bmz241 in all 8 views to within 1 px. Scale is 26.4 m = 13 carunits.

The model scripts are `vectron.py`, `ric.py` (ex-DB IC coaches and the RDC couchette), `flirt.py`, `lint.py` (LINT 41/27 with the livery as a colour table) and `talgo.py`. Regenerate the sheets with `python tools/railrender/leo.py [family …] [--preview DIR]`; change a model and regenerate rather than editing the PNGs.

The RegioJet families (`vehicle-rail/regiojet/`) use the same renderer; `python tools/railrender/regiojet.py [family …] [--preview DIR]` regenerates them. `rjcoach.py` draws every coach type from its vagonWEB side drawing (10 px = 1 m): one window/door list per body (in metres from the front buffer), the roof profile (flat Eurofima, ex-DB with the thin yellow line, Astra, round UIC-X with sloping ends) and small lettering. At 70 px per coach the window rhythm, door type and roof colour are what keeps the types apart, so keep those exact. Vehicle ids are the RJ car codes (A000, Bp200, …). The other scripts are `rj_locos.py`, `rj_pesa.py`, `rj_665.py`, `rj_628.py` (Arriva's `db628.py` geometry), `rj_shunters.py` and `rj_regiopanter.py`. The last one paints the DÚK scheme as a zone dict on the shared RegioPanter body of `tools/railpaint/panter.py`.

The Arriva (`vehicle-rail/arriva/`) and GW Train Regio (`vehicle-rail/gw-train-regio/`) families work the same way with their own drivers, `arriva.py` and `gwtr.py`. They use the models `db628.py` (ex-DB 628.2, shared by both operators), `desiro.py`, `gtw.py`, `arriva_lint.py` (on `lint.py`) and `regiosprinter.py`. Where an operator runs the same body as a ČD family, the sheet is a zone-map repaint of the ČD sheet instead, so the two operators share one silhouette: `regiopanter_idpk.py` (ČD 650), `gwtr_rs1.py` (ČD 841.2) and `gwtr_m152.py` (ČD 810 / 814.0). Those scripts read the ČD sheet at run time, so regenerate them after changing it.

Articulated units are modelled on one u axis and each car's tile keeps only its own pixels. Lettering must read left to right as seen: on the +v side screen-left is the vehicle's rear, on the -v side its front. Locomotives are drawn about 2–3 px taller than coaches, like the natives (ČD 363, 380, ÖBB 1216).

### Painted rail sprites (`tools/railpaint/`)

Every ČD diesel and electric unit family (`vehicle-rail/ceske-drahy/`) is painted, not rendered: its sheets are zone-map repaints of upstream pak128.CS / pak128_czr drawings (TommPa9, Sim and others), so they keep the native pak128.cs look and shading. `body.py` builds a per-pixel zone map of one sprite row from row rules in the pure views (ne/sw sides, nw/se ends), and `warp.py` carries it into the diagonal views (each is a sheared copy of a pure view). Every pixel gets a zone, a row offset k and a position u along the car. `paint.py` then recolours zone by zone, multiplying by each pixel's shade factor so the original lighting survives. `palette.py` holds the shared colours: Najbrt, PID, ČD red-cream, IDPK, the battery-unit scheme and JMK.

`panter.py` is the shared RegioPanter body: cars `A` (pantograph cab, cab at the front), `M` (middle) and `B` (cab at the rear), plus `P` in `cd_panter.py` (a B car with A's pantograph, via `panto_xfer.py`). A livery is a dict of zone → colour or callable(ctx). The zone names and the `paint_car` / `sheet` / `geo` API are documented at the top of `panter.py`. To add a scheme on the same silhouette, write one more dict (see the ČD ones in `cd_panter.py`) and add its family to `FAMILIES`. `interpanter.py` recolours the InterPanter class by class; it has only one livery. `cd_panter_yaml.py` generates the Panter `family.yaml` files so they stay uniform.

One module paints each group of families:

| Module | Families |
| --- | --- |
| `cd_sukafon.py` (on the older `zonemap.py` framework) | 809, 810 + 010, 811 + 012 |
| `cd_rs1.py` | 840, 841, 841.2, 841.3 |
| `cd_84x_85x.py` | 842 + 054 / 954, 843 + 043 / 943, 854 |
| `cd_pesa.py` | 844, 847 |
| `cd_642_848.py` | 642 Desiro, 848 GTW |
| `cd_814.py` | 814.0 + 914, 814.2 trio |
| `cd_471.py` | 471 CityElefant |
| `cd_680.py` | 680 Pendolino |
| `cd_panter.py`, `interpanter.py` (driver `cd_emu.py`) | 440, 640, 640.1, 640.2, 650, 650.2, 690.2, 530, 550, 660.0, 660.1 |

Regenerate everything with `python tools/railpaint/cd.py [family …] [--preview DIR]`, or one group with its module (`python tools/railpaint/cd_814.py [--preview DIR]`, `cd_emu.py [family …] [--yaml]` for the Panters). `cd.py` runs each painter in its own process, because `paint.py` caches shading per body name. A clean run leaves `git status` unchanged. Change the painters and regenerate rather than editing the PNGs. The upstream bases are frozen in `tools/railpaint/src/` in **source coordinates**. Sprites extracted from compiled paks with `tools/pak_extract.py` usually sit **4 px lower**, because makeobj already applied the rail `image_offset` [0, 4]. Check the wheel line against the rule below, and shift such a base up 4 px before painting on it, or the vehicle will ride 4 px low. All ČD rail sheets have their wheels at y = 93 in the ne/sw views.

### Rendered bus sprites (`tools/busrender/`)

The DPMHK Hradec Králové families (`vehicle-bus/dpmhk/`, `vehicle-trolleybus/dpmhk/`) are rendered, not painted: `render.py` is the orthographic box raycaster in the pak128 road projection (1.5 px/m across, 4 px/m up; the same one the Prague/Brno SOR NS renders used) and `dpmhk.py` holds one parametric body model (SOR NS, SOR NB, Iveco Urbanway, SOR EBN), the DPMHK liveries as texture rules, trolley poles aimed at the pak128.cs wire of the own lane, and the per-view lane origins (a bare 12 m box on the median footprint of native 12 m buses). Single vehicles are drawn at real length; articulated sections at 4/3 m per carunit with the (4 − L/2) shift, joints at the real positions. Livery bands are whole multiples of 0.25 m, i.e. whole pixel rows in every view. Regenerate with `python tools/busrender/dpmhk.py [family …] [--preview DIR]`; change the model and regenerate rather than editing the PNGs.

The RegioJet coach buses (`vehicle-bus/regiojet/`) come from `tools/busrender/rj_buses.py`. It uses its own vectorised copy of the DP Ostrava bus raycaster (`rj_vrender.py`), with the models in `rj_busmodels.py` and lane placement in `rj_lane.py`. The long coaches are drawn about 1.08 × their real length, like the native Citywide 15 and the upstream Irizar. The per-view shift is measured on a plain box of the model's footprint and then applied to the model, so a longer body extends along the lane and never sideways.

## Multi-vehicle consists

This Simutrans build does **not** support `bidirectional=1` (auto-flip) or `can_lead_from_rear=1`. Don't emit them. Multi-vehicle consists are modelled by **separate vehicle definitions per consist position**, each with its own sprite row.

### Section placement for `length` ≠ 8 (gaps at the joints)

Simutrans anchors every vehicle at its **front** and places the next vehicle's anchor `length` carunits behind it (16 carunits = 1 tile; `convoi_t`: `dist = driven - vlen`). A sprite drawn like a native 8-carunit section (body centred in the tile) has its body centre 4 carunits behind its anchor. So a section of length `L` must have its body shifted **along its direction of travel by (4 − L/2) carunits** relative to a tile-centred drawing: `L = 12` → 2 carunits backward, `L = 10` → 1 backward, `L = 6` → 1 forward. Centring every section regardless of length leaves gaps or overlaps between sections of different lengths (a 12 + 6 tram drawn centred shows a 3-carunit gap). The body must also be `L` carunits long (1 carunit = 1.5 m in these sprites).

Screen pixels per carunit of travel: n/s/e/w `(±4, ±2)`, ne/sw `(±5.66, 0)`, nw/se `(0, ±2.83)`.

Check every multi-section vehicle with `python tools/consist_preview.py <sheet.png> <len0,len1,...> <out.png>` (lengths in consist order, lead first; `--rows` to pick sprite rows). It composites the rows with the engine's spacing and draw order in all 8 directions; sections must meet at the joints in every view. Upstream multi-section sprites (e.g. the DPO Tango NF2, 8 + 6) already follow this.

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

`reverse: true` is only exact for `length: 8` sections: a 180°-rotated sprite keeps its body offset, which is wrong for any other length (see "Section placement"). Units whose end cars are not 8 carunits long (e.g. the Leo Express FLIRT 480, LINT 41) draw the rear cab car as its own row instead.

### Loco-hauled stock

Locomotives and coaches that run in mixed trains set `prev: any` and `next: any`, so no `Constraint` lines are emitted and they couple with any locomotive or coach, VZ or native (e.g. `vehicle-rail/leo-express/193` Vectron, `ic` ex-DB coaches). Fixed articulated sets hauled by a locomotive (Talgo) use `prev: any` only on the car that faces the locomotive. Locomotives carry no passengers, so their families set `windows_lit_when_loaded: false` and draw the cab glass in plain colours.

## Stations (`station.yaml`)

Station objects live under `station-<mode>/<set>/station.yaml` (e.g. `station-rail/uzke-nastupiste/`) and are grouped by the `group:` field instead of `agency:`: every set with `group: Stations` in `station-rail/` goes into `dist/VZ-Stations-rail.pak` (+ `en.`/`cz.VZ-Stations-rail.tab`). Object `name=` is `VZ-<group>-<id>` (e.g. `VZ-Stations-UzkeNastupiste-deska-prechod`); display names come verbatim from `name_en` / `name_cs`. `copyright:` is optional upstream credit (original work omits it and gets plain `vojtechzicha`).

```yaml
group: Stations
objects:
  - id: UzkeNastupiste-deska          # name= suffix
    sprite: uzke-deska                # sprites/uzke-deska.png
    generate: {style: deska}          # parameters for tools/gen_platforms.py
    name_en: "Narrow platform (concrete slabs)"
    name_cs: "Úzké nástupiště (betonové desky)"
    fields: {level: 1, enables_pax: 1, intro_year: 1960}   # extra .dat fields
```

The build emits `obj=building`, `type=stop`, `waytype=track`, `noinfo=1`, `dims=1,1,16` plus `fields`, and references only non-empty sheet cells. Every station object is a **16-layout through stop** on one standard 1024×1152 sheet: rows 0–1 back images and rows 2–3 front images for season 0 (layouts 0–7 / 8–15 across the columns), rows 4–7 the same for season 1 (snow), row 8 col 0 = build cursor, col 1 = 32×32 toolbar icon (top-left of the cell). Image offset is 0,0 (the art is drawn at the true tile diamond, top vertex at y≈64.5).

Layout bits, set by the engine (`simtool.cc` `tool_station_aux`, `hausbauer_t::build_station_extension_depot`): `1` = east–west track, `2` = no stop tile at the south/east end (ramp there), `4` = none at the north/west end, `8` = platform on the near (east/south, lower-on-screen) side instead of the far side. Near-side platforms go into the **front** image (drawn over the train on that tile); everything at ground level (crossing panels) stays in the **back** image. Map rotation remaps layouts through bit 8 (`gebaeude_t::rotate90`), so the side must always follow bit 8; an object cannot pin its platform to one fixed side.

The engine picks bit 8, not the pak: a tile with no oriented stop around it gets the far side, a tile with a stop on the same track copies that tile's side, and a tile next to a stop on the neighbouring track only gets the opposite side (adjacent platform tracks alternate and form islands). To put several narrow platforms on the same side of their tracks, start each one on a tile with nothing beside it and extend it along the track.

Sheets are **generated**: `python tools/gen_platforms.py station-rail/uzke-nastupiste [--only <sprite>]` (needs numpy + Pillow) ray-marches a small heightfield per layout with pak128 lighting (sun from the south, flat top ×1.0, south faces ×0.835, east faces ×0.61) and writes `sprites/<sprite>.png`. Geometry is matched to pak128.cs: platform edge 0.115 tile from the track axis, like the asphalt platforms, and the crossing band spans a = 0.365–0.635 of the tile, like `Asfaltove_nastupiste_se_sluzebnim_prejezdem`, so a crossing row continues through both. `crossing_end: true` makes the "konec přechodu" variant for the last track: the path covers only the platform side and ramps up onto the platform (which keeps its full height), so it never crosses the track into nothing; the engine can't know which track is the last one, so this is a separate object. Rails over crossing panels are redrawn in screen space on the pak128.cs rail pixels (they sit ½ px below the geometric axis). Change the art in the generator and regenerate; don't paint the sheets by hand.

## Industries (`industry.yaml`)

City consumer industries live under `industry-<location>/<set>/industry.yaml` (e.g. `industry-city/supermarkety/`) and are grouped by `group:` like stations: `group: Supermarkets` in `industry-city/` builds `dist/VZ-Supermarkets-city.pak`. Object `name=` is `VZ-<group>-<id>` (e.g. `VZ-Supermarkets-Kaufland`); `name_en` / `name_cs` are the display names and the optional `details_en` / `details_cs` become the `factory_<name>_details` text of the info window's Details tab.

```yaml
group: Supermarkets
defaults: {location: city, electricity_amount: 0, electricity_boost: 0, mapcolor: 147}
goods:                                # input goods profiles
  store:
    - {good: food, capacity: 25, suppliers: 1, factor: 5}   # inputgood/-capacity/-supplier/-factor
classes:                              # size classes: default goods profile + shared fields
  store: {goods: store, fields: {productivity: 55, range: 55, passenger_demand: 1, passenger_boost: 12}}
objects:
  - id: Zabka                         # name= suffix
    sprite: zabka                     # sprites/zabka.png
    dims: [1, 1]
    class: store
    # goods: cash_carry               # optional: another goods profile
    generate: {model: store, brand: zabka}   # tools/gen_shops.py model + brand
    fields: {distributionweight: 3, intro_year: 2008}
    name_en: "Žabka"
    name_cs: "Žabka"
```

The build emits `obj=factory` with `defaults`, the class fields and the object fields (in that order, later ones win), the goods profile as `inputgood[i]`…, and `dims=X,Y,4`. Every object has **four layouts and two seasons** on one sheet: row = `season * 4 + layout`, column = tile `y * w + x` of that layout (odd layouts swap the dims). makeobj keys tile images as `backimage[layout][y][x][height][phase][season]`. Map rotation turns layout L into L − 1 (`gebaeude_t::rotate90`), so layout L + 1 must be layout L turned a quarter anticlockwise: layout 0 has the shop front facing south, 1 east, 2 north, 3 west. Only use goods that some pak128.cs factory produces; `sugar` and `soft_drinks`, which the upstream shops list, have no producer.

Sheets are **generated**: `python tools/gen_shops.py industry-city/supermarkety [--only <sprite>] [--preview <dir>]` (needs numpy + Pillow). It ray-casts axis-aligned boxes and ellipsoids over a textured ground plane with the same pak128 lighting as `gen_platforms.py`, assigns every sample to the tile its surface stands on (anything that can hide a surface stands further south or east, so the engine's back-to-front tile order reassembles the building), and stamps pixel-font signs onto walls and roof logos in world orientation, so they read left to right in every layout. There is one building model per size class (`store` 1×1, `market` 1×2, `hyper` 2×2), shared by all chains of that class; a chain (`BRANDS` in the generator) sets the colours, sign lockup, emblem, roof logo and lorry livery. Shop glass uses the lit-window specials and sign lettering or lightbox boards the lamp specials, so shops glow at night; roof logos and lorries use plain colours. Grass and snow match the pak128.CS temperate and snow ground textures. Change the art in the generator and regenerate; don't paint the sheets by hand.

## Localization

For each agency-mode pak, the build emits one `en.<pak-basename>.tab` and one `cz.<pak-basename>.tab` (e.g. `en.VZ-CeskeDrahy-rail.tab`, `cz.VZ-CeskeDrahy-rail.tab`) into `dist/text/`, covering every object across every family and livery in the pak. These files install into `PAK_TARGET_DIR/text/` alongside the pak's main `cz.tab` / `en.tab` — that's the only place Simutrans's translator scans for loose translation files. Filename rules (from `translator::load_files_from_folder`): the language code must be a dot-separated prefix or suffix (`cz.foo.tab` or `foo.cz.tab` both match; `cz_foo.tab` does not). Czech uses `cz`, not `cs`, to match this pak's language code. Files are UTF-8 with BOM — Simutrans's `is_unicode_file()` auto-detects the BOM and decodes correctly for any language, so full Czech diacritics are preserved in both `cz` and `en` strings. Each `.tab` file is a bare list of pairs:

```
<object name #1>
<display name in this language>

<object name #2>
<display name in this language>
```

Display string templates (built into `build.py`) — vary by mode:
- Rail (uses Czech railway "class/řada" nomenclature):
  - EN: `<agency_en> Class <id> <family_en> <role_en> (<name_en>)`
  - CS: `<agency_cs> řada <id> <family_cs> <role_cs> (<name_cs>)`
- Bus, tram, and all other modes (no class numbering scheme — the family name names the model):
  - EN: `<agency_en> <family_en> <role_en> (<name_en>)`
  - CS: `<agency_cs> <family_cs> <role_cs> (<name_cs>)`

The set of class-prefix modes is defined as `MODES_WITH_CLASS_PREFIX` in `build.py` (currently `{"rail"}`). `<id>` uses the natural dotted form (e.g. `Class 814.0`). Encoding: UTF-8 (no BOM). Czech display strings use full diacritics; diacritics-free forms are reserved for filenames and object `name=`.

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
