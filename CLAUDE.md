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

**The installed pakset must always be what `main` builds, on every PC.** On the owner's desktop `PAK_TARGET_DIR` is `D:\OneDrive\Games\Simutrans\pak128.cs`: the pak128.cs folder of the Steam game on this PC *and* on the owner's other PCs is a junction to it (their `Games\Simutrans\install.ps1` sets that up), so whatever is installed there is what every PC plays, and a pak missing there makes the owner's save fail to load on all of them. So:
- After every change merged to `main`, build and install it (`python build.py`, or `python build.py <path>` for the touched pak). Never leave a commit on `main` uninstalled, and never install from a branch or worktree that is not merged: the next install from `main` would silently replace it.
- Install only into that folder, never into a Steam folder's `pak128.cs` directly.
- A set built with the fork makeobj (`makeobj: fork`) needs a fork exe that knows its keys; the fork repo's `tools/windows/steam-fork.sh update` installs the exe on this PC and in OneDrive for the other PCs.
- To check: `python build.py --no-install`, then every `dist/VZ-*.pak` and `dist/text/*.tab` must be byte-identical to the file in `PAK_TARGET_DIR` (on 2026-10-16 all 71 were, after `VZ-DPMostLitvinov-bus` from 6f9742a was installed). The install step copies only the files that differ, since OneDrive uploads every file written.

`makeobj` is located via the `MAKEOBJ_PATH` environment variable; if unset, the build runs `makeobj` from `PATH`. Requires `pyyaml` and `Pillow` (`pip install pyyaml pillow`) and Python 3.7+.

The owner's MacBook builds the same paks byte for byte (all 213 files on 2026-10-16), so it may build and install from `main` too. makeobj writes objects in the order it finds the `.dat` files; Windows lists them in NTFS order, but macOS (APFS) returns them unordered, so outside Windows `build.py` passes the files in NTFS order instead of the directory. On the Mac, run the build with `.venv/bin/python` (a uv venv with pyyaml, Pillow, numpy and scipy, which the generators need). makeobj there is built from a clean `git archive origin/main` of `../simutrans-122.0` into its git-ignored `build/makeobj-src/` (`make -C makeobj CFG=mac-release`); `.env` points both `MAKEOBJ_PATH` and `MAKEOBJ_FORK_PATH` at it, and `PAK_TARGET_DIR` at `~/Library/CloudStorage/OneDrive-Personal/Games/Simutrans/pak128.cs`, the same OneDrive folder.

**Do not hand-edit `.dat` or `.tab` files.** Edit the relevant `family.yaml` or the per-livery PNG instead.

## Naming convention

Two distinct names matter — one for the shipped `.pak` and one for individual objects/sprites inside it.

**Pak filename** (one per agency × transport-mode): `VZ-<Agency>-<mode>.pak`

- `Agency` — PascalCase Czech transport agency name (e.g. `CeskeDrahy`, `RegioJet`, `LeoExpress`, `DPPraha`).
- `mode` — the `vehicle-*/` root folder slug without the `vehicle-` prefix (`rail`, `bus`, `tram`, `trolleybus`, `water`, `air`).
- Example: `dist/VZ-CeskeDrahy-rail.pak` contains every ČD rail family and every livery thereof.

**Object basename** (used for `name=`, per-livery PNG file inside the build dir, and sprite refs in `.dat`): `VZ-<Agency>-<Type>-<Color>`

- `Type` — class designation of the lead/named unit of the family; dots replaced with underscores (e.g. `814.0` → `814_0`).
- `Color` — livery name in Czech without diacritics (e.g. `zlutozelena`, `najbrt2`, `pidsedocervena`).
- Final object `name=` adds the per-vehicle id suffix: `VZ-CeskeDrahy-814_0-zlutozelena-914`.

A single `family.yaml` + `<color>.png` pair holds the entire matched set (e.g. cab + motor of one DMU). The build emits one `.dat` + one `.png` per family×livery inside the shared agency-mode build dir, plus one `en.` and one `cz.` `.tab` per agency-mode pak (in `dist/text/`) listing every object's display string.

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

Transport modes: `vehicle-rail/`, `vehicle-bus/`, `vehicle-tram/`, `vehicle-trolleybus/`, `vehicle-water/` and `vehicle-air/` (no families yet). Bus, tram and trolleybus are separate modes rather than one generic `vehicle-road/`, so each pak holds one kind of rolling stock. The build script walks every `vehicle-*/...family.yaml` regardless of depth and groups by the `agency:` field plus the `vehicle-*` mode root. Family folder names are conventionally the slugified type (`814.0` → `814_0`); the agency folder name is organizational only — the canonical agency identifier is the `agency:` field inside `family.yaml`. Station objects live in parallel `station-*/` roots, city industries in `industry-*/` roots and rail signals in `signal-*/` roots (see "Stations", "Industries" and "Signals" below).

## `family.yaml` schema

```yaml
agency: CeskeDrahy            # PascalCase, goes into basename verbatim
type: "814.0"                 # used as basename Type token; dots → underscores when emitted
copyright: Sim                # original upstream credit; build appends ", vojtechzicha"
#                             # required: fully original art uses `copyright: vojtechzicha`
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
    # couple_sibling_liveries: true  # (or prev / next) sibling partners resolve to that vehicle in
    #                         # EVERY livery of the sibling family, e.g. a red-cream T3R.P with a
    #                         # wine-silver T3R.PLF. Set it on both sides with couple_liveries.
    # prev: any / next: any   # no constraint on that side at all: couples with anything, like native
    #                         # locomotives and coaches (loco-hauled stock, the front of a Talgo set)
    # loaded_row: 3           # sheet row of a separately drawn loaded image (upstream ports whose
    #                         # loaded image differs; families without windows_lit_when_loaded only)
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
    # Optional per livery (used to port an upstream object 1:1 into a family):
    # copyright: "TommPa9"   # this livery's upstream credit instead of the family's
    # fields: {cost: 4251600, intro_year: 1993, retire_year: 2009}  # override the
    #                        # vehicles' fields in this livery only
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

- Draw all window glass in the lit-at-night specials: `0x4D4D4D` (special 28, dark grey by day, warm yellow at night) for glass, `0x57656F` (special 16) for lighter glass/reflections. Headlights `0xFFFF53` and tail lights `0xFF211D` are always lit and unaffected. Cab and driver glass stays plain (a step off the specials, e.g. `0x4D4D4E`), so a driver's cab stays dark at night. The whole DPO fleet follows this since 2026-10-20; some older VZ buses still draw the windscreen lit.
- Set `windows_lit_when_loaded: true` in `family.yaml` (every family does). The build then copies the sheet as the loaded image (`freightimage`, shown whenever at least one passenger is aboard) and writes a derived `<basename>-unlit.png` for `emptyimage`, where each lit-window special is swapped for a plain colour one step away (`0x4D4D4D` → `0x4D4D4E`, …). The two look identical by day; at night only a loaded vehicle's windows glow.
- Needs Pillow at build time.

### Rendered rail sprites (`tools/railrender/`)

The Leo Express families (`vehicle-rail/leo-express/`) are original art rendered from box models, not painted: `render.py` is an orthographic box raycaster in the pak128 projection, and `railkit.py` calibrates it to native pak128.cs rail art. That calibration covers the front anchor per view (source-sheet pixels before the default rail `image_offset` [0, 4]), body half-width 0.92 carunit, side wall height 10 model px, the ne/sw views drawn 18 % taller, and per-face shading. It fits CD_Bmz241 in all 8 views to within 1 px. Scale is 26.4 m = 13 carunits.

The model scripts are `vectron.py`, `ric.py` (ex-DB IC coaches and the RDC couchette), `flirt.py`, `lint.py` (LINT 41/27 with the livery as a colour table) and `talgo.py`. Regenerate the sheets with `python tools/railrender/leo.py [family …] [--preview DIR]`; change a model and regenerate rather than editing the PNGs.

The RegioJet families (`vehicle-rail/regiojet/`) use the same renderer; `python tools/railrender/regiojet.py [family …] [--preview DIR]` regenerates them. `rjcoach.py` draws every coach type from its vagonWEB side drawing (10 px = 1 m): one window/door list per body (in metres from the front buffer), the roof profile (flat Eurofima, ex-DB with the thin yellow line, Astra, round UIC-X with sloping ends) and small lettering. At 70 px per coach the window rhythm, door type and roof colour are what keeps the types apart, so keep those exact. Vehicle ids are the RJ car codes (A000, Bp200, …). The other scripts are `rj_locos.py`, `rj_pesa.py`, `rj_665.py`, `rj_628.py` (Arriva's `db628.py` geometry), `rj_shunters.py` and `rj_regiopanter.py`. The last one paints the DÚK scheme as a zone dict on the shared RegioPanter body of `tools/railpaint/panter.py`.

The Arriva (`vehicle-rail/arriva/`) and GW Train Regio (`vehicle-rail/gw-train-regio/`) families work the same way with their own drivers, `arriva.py` and `gwtr.py`. They use the models `db628.py` (ex-DB 628.2, shared by both operators), `desiro.py`, `gtw.py`, `arriva_lint.py` (on `lint.py`) and `regiosprinter.py`. The ČD 848 is the same GTW model in Najbrt 2 (`cd_848.py`, the owner's pick of 2026-10-20 over the repainted ZSSK 840 drawing). Where an operator runs the same body as a ČD family, the sheet is a zone-map repaint of the ČD sheet instead, so the two operators share one silhouette: `regiopanter_idpk.py` (ČD 650), `gwtr_rs1.py` (ČD 841.2) and `gwtr_m152.py` (ČD 810 / 814.0). Those scripts read the ČD sheet at run time, so regenerate them after changing it.

The ČD loco-hauled coaches (`vehicle-rail/ceske-drahy/coach_*`, `13ev`, `comfortjet`) come from `cdcoach.py` + the driver `cd_coaches.py`, which also writes their `family.yaml` (`python tools/railrender/cd_coaches.py [family …] [--yaml] [--preview DIR]`; review the yaml diff). Same vagonWEB method as `rjcoach.py` (drawings `popisy/img/CD/<name>-a.gif`), 24.5 m cars as length 12, 26.4–26.9 m as 13, in Najbrt 2 (Najbrt 1 = grey roof, no light line; BD = blue lower body; restaurant / sleeper / couchette cars take the dark window band). The yellow 1st-class line covers only the 1st-class part (`first` spans). Look-alike types keep the real details that differ: window rhythm, plug / folding / honecker doors, AC units vs roof vents, pictograms, and on the ex-ÖBB cars the window frame colour (vagonWEB variants `-br` / `-cr` / `-mr` = white / black / blue frames). Driving trailers (sysel, 13Ev) come as `-front` (cab leading) and `-rear` (cab at the tail), each rendered, not `reverse`d. Their cabs are modelled from horizontal slabs along a nose profile (`sysel_nose_m`, `ev_nose_m`), after the vagonWEB drawings and photos: the Sysel's sky-blue cab with the dark-blue hood and lamp, and the 13Ev's long raked nose. The Sysel head is raked further back than on the drawing so it reads at 1×; the user picked that over the measured version (2026-10-11). Double-deckers use `dd()`. The `railjet`, `interjet` and `comfortjet` families are 1:1 ports of the CZR sets (art frozen in `src/czr_cd_jets.png` in the CZR pak's object order, lifted 4 px, the pak-extract offset; coupling lists, cost, capacity, speed and weight as read from the pak, table `CZR` in `cd_coaches.py`). The ComfortJet adds the Afmpz 880 (the CZR railjet cab car) and the BRmpz 882 (the ARbmpz 892 without the yellow line).

The ČD locomotives (`vehicle-rail/ceske-drahy/`: 111, 113, 151, 162, 163, 193, 210, 242, 362, 371, 380, 384, 704, 714, 743_2, 750, 750_7, 754, 794, 799, 1216) are rendered the same way, one script per body group, each taking `[family …] [--preview DIR]`: `cd_loco_modern.py` (193/384 on `vectron.py`), `cd_loco_classic.py` (the 1216 Taurus; its `Taurus` class also paints the ÖBB 1116/1216 and PKP EU44 through `taurus.py`), `cd_loco_centrecab.py` (111/113/210), `cd_loco_hood.py` (714, 743.2) and `cd_loco_shunter.py` (704/794/799). Three classes keep TommPa9's hand-drawn pak128.cs sheets because the user preferred them to any render: the 151, 242 and 380 (static sheets, extracted and shifted up 4 px to source coordinates, credited per family). Two body groups are TommPa9's drawings repainted instead, the user's pick over every render (2026-10-10): the Eso / Peršing / Bastard (162, 163, 362, 371) from `tools/railpaint/cd_eso.py` and the Brejlovec (754, 750.7, 750) from `tools/railpaint/cd_brejlovec.py` (see "Painted rail sprites"). All paint comes from `cd_loco_livery.py` (colour slugs and names too): Najbrt 2 on a loco is `LOCO_SKY` upper body, a white stripe at headlight level and sapphire below, lighter than the RAL 5015 on the units, as every loco photo shows.

The Prague metro and the Petřín funicular (`vehicle-rail/dpp/`: 81_71m, m1, lanovka_1985, lanovka_2026 → `VZ-DPPraha-rail.pak`) come from `dpp_metro.py` (`python tools/railrender/dpp_metro.py [family …] [--preview DIR]`). Metro cars (19.2–19.5 m) are length 9, like TommPa9's native Metro_8171M, at coach width (the true 2.71 m section looked skinny next to the natives). Each five-car set is only buildable whole: separate rows for the lead and rear cab cars (length 9, so no `reverse`), and the repeated middle car (4Mt, M1.2) appears twice as `-2` / `-4` on one row. The metro is `electric` like the native one. The funicular cars (length 6) are drawn level, since the engine draws every vehicle level on slopes, and are `battery` vehicles, so the funicular track needs no catenary.

#### Render style (agreed 2026-09-26)

Box renders lost against the hand-drawn pak128.cs art, and the ČD 362 "Eso" render read as a rounded "Laminatka". The user picked the agreed style over four rounds of variants. `tools/railrender/style.py` holds its rules and constants, and `tools/railrender/src/style_ref_362.png` is the approved 362. Every new rendered family follows it:

- **Shape before paint.** Take the class's signature shape from photos. A boxy loco gets sharp corners, a vertical front and a flat roof with a hard edge; chamfers, stepped roofs and leaning fronts are only for rounded bodies.
- **Roof edge.** A dark gutter where roof meets body, never a light rim.
- **Livery zones.** Use the photo's proportions; measure them.
- **Signature detail.** Ribbing, louvre bands and roof equipment where the real loco has them. No 1-px side lettering.
- **Pantographs.** Light arms with a dark 2-px head bar.
- **Post-process.** Run `style.polish(img, **style.POLISH)` on every rendered sheet.

Before a rendered family ships, publish a comparison page for the user to pick from. Show photos, the native or hand-drawn reference, and 2–4 variants at 1× and 3× on grass. Existing sheets were drawn before this style and stay as they are unless the user asks.

Where TommPa9 drew the class himself, repaint his drawing rather than render the class. On 2026-10-10 the user replaced the ČD Eso and Brejlovec renders with repaints of his sheets ("this is what I expected"); see `handpaint.py` under "Painted rail sprites".

The small and foreign operator families (KŽC, AŽD, Die Länderbahn, DB Regio, ÖBB, ZSSK, MÁV, PKP Intercity, Koleje Dolnośląskie / Śląskie, European Sleeper, …) have one model script each; `ops.py` lists them and regenerates the ones without a main of their own. `coachkit.py` is the shared builder for loco-hauled coaches: length, windows and doors in metres off the vagonWEB side drawings (both sides), bogies, roof type, and the livery as a colour table with horizontal bands, 1-px lines and marks; `ops_coaches.py`, `es_coaches.py`, `zssk_coaches.py` and `mav_pkp_coaches.py` drive it. To give an existing model another operator's livery, write a wrapper (`ops_desiro.py`, `ops_vectron.py`, `ops_regiosprinter.py`, `arriva_lint.py`) instead of editing the shared model, so the other families' sheets stay byte-identical.

The ÖBB railjet (`vehicle-rail/obb/railjet`) is the CZR set (Lubak91) ported 1:1, art frozen in `src/czr_obb_railjet.png`, regenerated by `obb_railjet.py`. Unlike CZR, every car exists both ways round: ids -1..-7 run with the locomotive leading and the Afmpz cab at the tail, ids -R1..-R7 are the set travelling the other way with the Afmpz cab leading. A turned car is its column c + 4 tile moved onto the bounding box of its own column-c tile. This reproduces CZR's hand-drawn reversed ČD Afmpz 890 to 1 px. Its railjet livery has a train end, so the 1216 has a second object, `1216-rear` (`taurus.py` `TURNED`): the loco turned round, for pushing at the tail of an -R set.

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
| `cd_642.py` | 642 Desiro |
| `cd_814.py` | 814.0 + 914, 814.2 trio |
| `cd_471.py` | 471 CityElefant |
| `cd_680.py` | 680 Pendolino |
| `cd_panter.py`, `interpanter.py` (driver `cd_emu.py`) | 440, 640, 640.1, 640.2, 650, 650.2, 690.2, 530, 550, 660.0, 660.1 |
| `cd_eso.py` (on `handpaint.py`) | locomotives 162, 163, 362, 371 |
| `cd_brejlovec.py` (on `handpaint.py`) | locomotives 754, 750.7, 750 |
| `ops_eso.py` (on `cd_eso.py`) | RegioJet 162, 362.2; ZSSK 361.1; ŽSR 362 |

The two locomotive painters use `handpaint.py` instead of `body.py` / `warp.py`. It aligns every TommPa9 sheet of the body (21 of the Eso in `src/tommpa9_eso/`, 11 of the Brejlovec in `src/tommpa9_brejlovec/`) column by column against the pure views' row profile and forces the face tops onto exact 2:1 stairs, so each pixel gets a face (side, end, roof, under), an exact row K and a position U. On these sheets `warp.py`'s sheared row map came out a row off in every other diagonal column, which breaks the one-row stripes of a loco this small. A livery is either rules on (face, K), such as Najbrt 2, or the layout of his own sheet in that livery: each of his colours maps to a zone and the zone takes a colour from `palette.py` / `cd_loco_livery.py`. Faces are shaded per view in his palette steps (`FACT`). Every Eso keeps the details of its class's own sheet and gets a dark roof gutter. `ops_eso.py` paints the other operators' locos on the same body: the RegioJet 162 and 362.2 on his CD 162 sheet, with his own "|| REGIOJET" lettering taken pixel for pixel from his RJ 162 (`src/tommpa9_eso_other/`), the ZSSK 361.1 on his ZSSK sheet and the ŽSR 362 (`VZ-ZSR-rail.pak`) on his ŽSR sheet. Every Brejlovec gets the 754's details redrawn: louvre panels behind cab 1, six portholes, a small louvre before cab 2, the radiator grille raised a pixel above the roof and goggle frames wrapping round the cab corners. The 750.7 gets one wide windscreen.

Regenerate everything with `python tools/railpaint/cd.py [family …] [--preview DIR]`, or one group with its module (`python tools/railpaint/cd_814.py [--preview DIR]`, `cd_emu.py [family …] [--yaml]` for the Panters). `cd.py` runs each painter in its own process, because `paint.py` caches shading per body name. A clean run leaves `git status` unchanged. Change the painters and regenerate rather than editing the PNGs. The upstream bases are frozen in `tools/railpaint/src/` in **source coordinates**. Sprites extracted from compiled paks with `tools/pak_extract.py` usually sit **4 px lower**, because makeobj already applied the rail `image_offset` [0, 4]. Check the wheel line against the rule below, and shift such a base up 4 px before painting on it, or the vehicle will ride 4 px low. All ČD rail sheets have their wheels at y = 93 in the ne/sw views.

### Rendered bus sprites (`tools/busrender/`)

The DPMHK Hradec Králové families (`vehicle-bus/dpmhk/`, `vehicle-trolleybus/dpmhk/`) are rendered, not painted: `render.py` is the orthographic box raycaster in the pak128 road projection (1.5 px/m across, 4 px/m up; the same one the Prague/Brno SOR NS renders used) and `dpmhk.py` holds one parametric body model (SOR NS, SOR NB, Iveco Urbanway, SOR EBN), the DPMHK liveries as texture rules, trolley poles aimed at the pak128.cs wire of the own lane, and the per-view lane origins (a bare 12 m box on the median footprint of native 12 m buses). Single vehicles are drawn at real length; articulated sections at 4/3 m per carunit with the (4 − L/2) shift, joints at the real positions. Livery bands are whole multiples of 0.25 m, i.e. whole pixel rows in every view. Regenerate with `python tools/busrender/dpmhk.py [family …] [--preview DIR]`; change the model and regenerate rather than editing the PNGs.

The Iveco Streetway 12M / 18M has its own `dpmhk.py` body (`SW12` / `SW18`, faces `sw`), similar to the Urbanway but not the same (owner, 2026-10-28), after 38 photos of DPP, Havířov, Karviná and the Pardubice demonstrator: the sill at 1.35 m with the black band up to the roof edge, the off-side black sweep down to the front corner and the rear louvre grille (`sw_side`), the all-black arched windscreen over a black lamp strip, the black upper rear with the window on the right and the grille on the left, white rear corner pillars, the dark roof box over the rear on the diesels. Drivers paint its faces through `sw_paint(role, t)`. The DPP / Praha cars come from praha.py (PID grey-red), Pardubice and Krnov from sor_town.py, Havířov and Karviná from odis_town.py (`sw_rows`, the sor_town palettes).

The SOR city bodies take the common SOR base too (owner, 2026-10-24). These are the specs with `sor=True`: NS, NB, EBN, the Praha NC 18, the DPO EBN 10,5 and the Škoda 30Tr–33Tr built on them. `dpmhk.SOR_SHAPE` (`low`, or `orig` for the bodies before) starts the body one pixel row higher (`SKIRT`), so the bus stands on its wheels, and runs the black window band to the roof edge. Paint that marks the bottom of the body (skirt strips, door steps) is laid from `ZB`, the body's lowest point, not from `Z0`. On fronts and rears the bottom holds face-only parts (bumpers, aprons, lamps), so `Veh.face_split` paints the face below that height plus `SKIRT` as it was one row lower, and the row above it (plain panel, mask or windscreen) is the one given up. It is set per class and face: dpmhk NB / EBN fronts and NS / NB rears, praha NS / NB fronts, khk_town EBN, sor_town fronts. Livery bands that wrap round from the sides keep their heights (odis_town, the DPO EBN 10,5, the Prague red rear band).

Every SOR body on the base except the NB has its window line one pixel row higher (`dpmhk.WINRISE` 0.25 m, the owner's pick B for the towns, 2026-10-24), so one body has one window line in every pak. On 2026-10-28 it went from the town and DPP bodies to all of them, so a Prague TNS trolleybus lines up with the NS bus beside it. A spec's `winrise` overrides it. The NB 12 / NB 18 bodies (`nb=True`, the 30Tr / 31Tr / TNB too) have their own roof, `dpmhk.NB_SHAPE`. The owner picked `bold` on 2026-10-28, because the plain box (`box`) read like an Urbanway. Both roof ends are rounded off in two steps: the top row stops 0.8 m short of the front and rear, and the row under it 0.3 m. The outer roof strip is a shade darker, so the roof edge reads rounded. The NB keeps its own low window line (`winrise` 0) with the black band up to the roof edge, the owner's window line B of 2026-10-28: with the raised sill and a roof-coloured top row it had two rows less glass than VTPsim's NB and the real bus. A livery with a roof-edge colour of its own (sor_town `roofedge`, the DPO TNB) keeps it on the top row of the side. The 2-2-2 NB 12 (DPMB, Chrudim) is `NB12_3D`, the DPP layout without its third door. On the front the windscreen runs up over the lower step and the destination display sits on the recessed middle step, as the glass curves up into the dome on the real bus. Each ledge takes the colour of the end face above it. Roof boxes start behind the rounded ends. `dome` (one step) and `shoulder` (one step plus the edge) stay selectable.

Every SOR NS / NB / NBG / EBN town family and the trolleybuses on those bodies come from `tools/busrender/sor_town.py`: Kladno, Most, DPMB, DPMO, MDPO, Frýdek-Místek, Havířov, Krnov, Třinec, Trutnov, Chrudim (`iredo/sor_nb_12`), Hranice, Nový Jičín, Přerov, the DPO TNB 12, and since 2026-10-28 the DPMB 31Tr / 32Tr and DPMP 30Tr / 32Tr (VTPsim's hand art before), so every SOR trolleybus is drawn on the body of its bus. It also paints the Iveco Urbanway 12M / 10,5M / 18M and Irisbus Citelis 12M / 18M (the Urbanway body with the older `uw1` face; Havířov's through odis_town `town_rows`) town fleets (DPMB, Mladá Boleslav, Pardubice, Kladno, Opava, Frýdek-Místek, Tábor, Třinec) on the `dpmhk.py` Urbanway body, faces `uw1` / `uw2` and rear `uw` in the palette (`<town>_uw`), since 2026-10-28 instead of Lubak91's sheets (owner: one drawing per bus type). The IREDO copy (pk_town.py), the ODIS 10,5M (odis.py) and the Havířov, Karviná and Orlová Urbanways (odis_town.py `UW_SRC`) are built from those renders. It paints the `dpmhk.py` bodies from one palette per town (`TOWNS`: body, roof, lower body, skirt, front and rear colours, decals). The town liveries need the raised window line (`dpmhk.WINRISE`): without it their lower bands came out too thin. The windscreen and the driver's window are plain glass, dark at night. Articulated sections follow the bodies: NS 18 8 + 6, NB 18 9 + 5 carunits. The yamls are hand-written. Run `python tools/busrender/sor_town.py [family …] [--preview DIR]`.

The RegioJet coach buses (`vehicle-bus/regiojet/`) come from `tools/busrender/rj_buses.py`. It uses its own vectorised copy of the DP Ostrava bus raycaster (`rj_vrender.py`), with the models in `rj_busmodels.py` and lane placement in `rj_lane.py`. The long coaches are drawn about 1.08 × their real length, like the native Citywide 15 and the upstream Irizar. The per-view shift is measured on a plain box of the model's footprint and then applied to the model, so a longer body extends along the lane and never sideways.

The DP Ostrava buses and trolleybuses are all generated:

- **Solaris family.** The Urbino 10/12/15/18 III (12 / 18 also CNG) and IV, 26Tr, 27Tr and Trollino 12/15/18 (`vehicle-bus/dpo/`, `vehicle-trolleybus/dpo/`) come from `tools/busrender/dpo_solaris.py`, one parametric model on the `dpmhk.py` renderer. It places every vehicle itself by the section rule. Usage: `[family …] [--preview DIR] [--opt key=value]`; `--variants DIR` writes the look options without touching `sprites/`. The defaults are the owner's pick of 2026-10-20; the B options (subtle IV cap, subtle III dome, lighter fairing tops, blue Trollino roof) stay available through `--opt`.
- **All the others** come from `python tools/busrender/dpo_other.py [family …] [--preview DIR] [--variant ekova=B|ebn=B]`.
  - The Ekova Electron 12 and the SOR EBN 10.5 are rendered as subclasses of the `dpmhk.py` body (`dpo_other_bodies.py`); variant A of each ships.
  - The Dekstra LE 37 and the Rošero First are VTPsim's LE 37 art from the Prague package, repainted zone by zone in DPO turquoise (`dpo_other_rebase.py`).
  - The Urbis DD, 21Tr and 36Tr are patched (`dpo_other_patch.py`) from frozen copies in `tools/busrender/src/dpo/`, so a run is byte-identical.
  - The SOR TNB 12 comes from `sor_town.py` (above).
  - A box frame fitted to each frozen sheet gives the side faces their u/z coordinates. The trolley poles are re-drawn in their photographed colours and aimed at the `dpmhk.py` wires, which match the pak128.cs `elec_trolleybus_plain_2000` wire in the straight views.

`tools/busrender/dpo_lane.py` moves a sheet along the road only (no sideways move, so poles stay on the wire) to the native 12 m position by the length rule. It and `odis_town.port_native` measure against VTPsim's native-placed DPP NB 12, frozen in `tools/busrender/src/sor_nb_12-lane-ref.png`. Both generators apply that position themselves, so `dpo_lane.py --dry-run` reports every DPO sheet "ok". Turquoise sheets use `tools/tramrender/dpo_palette.py`: body `00ADD6`, roof `44C1E4`, plain cab glass.

### Rendered tram sprites (`tools/tramrender/`)

The DPO Škoda 39T (`vehicle-tram/dpo/39t_forcitysmart`) comes from `dpo_39t.py`. It is a parameter set for `fieldtram.py`, the two-section one-way tram model, which draws on `fieldrender.py`, an implicit-surface raymarcher in the rail projection of `tools/railrender/render.py`. A solid is a field function, so a nose rounded in plan, a raked windscreen and a curved roof shoulder are one expression each, where the box renderers stack bricks. One ray per pixel centre keeps edges and livery bands crisp. `flat=True` paints every side in one colour in every view, with `top_steps` steps on the shoulder, like the native DPO trams. Regenerate with `python tools/tramrender/dpo_39t.py [--variant NAME] [--out PNG]`.

Every section is drawn complete, the way the native trams are. The engine's draw order covers the hidden end of a section. Cutting each tile to the pixels its section owns in a straight consist would leave a notch on curves. Each section's front sits on the front anchor of the native DPO trams, so any section lengths close at the joints (check with `consist_preview.py`).

The DPO Tango NF2 comes from `dpo_tango.py`, another parameter set for `fieldtram.py` (9 + 8, after the Stadler type sketch). Its `--variant` keeps the roof options; `soft` ships (the owner's pick of 2026-10-20). That is slate equipment between the fairings plus the AC box over the cab.

`dpo_palette.py` holds the DPO turquoise scheme chosen on 2026-10-18 for every DPO vehicle: body `00ADD6` (Pantone 312 C), roof `44C1E4` (the same paint lit from above, lighter on photos), flat sides with one shoulder step.

`tramkit.py` and `dpo_trio.py` edit existing tram sheets in place (roof boxes, ASCII pixel patches). The DPO KT8D5R.N1, T3 (drawn as the T3R.P that runs today), T3SUCS (the classic look, kept as its own object) and T6A5 are TommPa9's / Lubak91's drawings patched by `dpo_tatra.py`. It handles the single-arm pantograph, the KT8's saloon rear end, lamps and plain cab glass, and paints the turquoise KT8 from a zone map. Its AC pods (owner-approved 2026-10-20) can be left out with `--no-ac`. `dpo_astra.py` does the Astra and the Trio. All of them start from bases frozen in `src/dpo/`. The DPO Varios (`variolf`, `variolf2`, `variolf2_plus`, `variolf3`, `variolf3_s2`) are TommPa9's drawings painted by `dpo_vario.py`: one per-pixel zone map of the shared Pelikán module, built from his blue-yellow sheets frozen in `src/dpo_vario/`, paints every livery. A colour map of one livery into another loses lines; paint from the zones instead.

### Prague and Brno packages for other operators (`vehicle-bus/praha/`, `vehicle-bus/brno/`, `vehicle-water/praha/`)

City vehicles of operators other than the city's transit company go into one package per city, not one per operator: agency `Praha` builds `VZ-Praha-bus.pak` and `VZ-Praha-water.pak`, and agency `Brno` builds `VZ-Brno-bus.pak`. `VZ-DPPraha-*` and `VZ-DPBrno-*` stay the transit company's own fleet, and the regional PID lines have their own package (next section). There is one object per type × livery, shared by every operator that runs it. The operator is never in `name=`; it appears only in the livery display name, e.g. `name_en: "PID red-blue-white · Arriva City, ABOUT ME"`.

The scope is the vehicles seen on city lines (Prague 100–299 and the 900s), in every real livery, as agreed with the Prague and Brno timetable sessions. Advert wraps get no object, except the standing Fashion Arena livery of line 238. The PID schemes are operator-independent: `pidsedocervena` (grey with red columns, 2021+) and `pidcervenomodrobila` (the older red-blue-white) must read the same as on the DPP families.

Sheets that are repaints of upstream or VZ art are kept as PNGs, like the DPP repaints. The rendered ones regenerate with `python tools/busrender/<driver>.py [family …] [--preview DIR]`:

- `praha.py` holds the PID liveries on the `dpmhk.py` bodies: SOR NS 12 / NS 18 / NC 18, the Urbanway 12M, the DPP NS 18, the DPP Urbanway 18M Hybrid (8 + 6) and the Brno Urbanway. It also draws the DPP SOR NB 12 / NB 18, ENS 12 and TNS 12 / TNS 18 and the Praha NB 12 on the same bodies.
- `praha_man.py` draws MAN Lion's City 12C (and EfficientHybrid), L (14.7 m, length 10), NL 293 / NL 283 (old generation) and Lion's Intercity LE 12.
- `praha_small.py` draws BMC Neocity 8.5, BMC Procity 10.6, TEMSA MD9 LE and the Erduman Sprinter 519. `length` follows the DPP scale: 12 m = 8, about 9.5 m = 7, about 9 m = 6, 7.5 m = 5.
- `dpp_coaches.py` (on the RegioJet coach modules) draws DPP's Crossway PRO 10.8M / 12M and the Tourismo RHD / 15 RHD (length 10). The Crossway PROs follow `iredo_models.SHAPE` like the regional Crossways.
- `sor_city.py` draws the SORs outside the IREDO / PID / ODIS drivers on the common SOR base (`iredo_models.SHAPE`): the Praha CN 9,5 and ICN 9,5, the DPP and DPMB ICN 9,5, the Brno CN 12 (IDS JMK) and the BN / BNG city SORs of Praha, DPP, DPMP, Studénka, Krnov and Frýdek-Místek. The owner asked on 2026-10-24 for every SOR to move onto that base, body by body. The families' yamls are hand-written. The BN bodies (`iredo_models.SorBN12`, `SorBN12R`, `SorBNG12`, `SorBN105`, `SorBN95`, `SorBN95R`, `SorBN85`) are the CN body with city doors: a double centre door just ahead of the rear axle, the step behind it, sometimes a rear door. The Orlová and Nový Jičín BN (odis_town.py), the Trutnov BN 8,5 (khk_town.py) and the IREDO BN 8,5 (pk_town.py) render on them too.

The PID ferries (Naomi type for P1 / P5 / P6, Kazi type Baba for P2, Holka 2 for P4) come from `python tools/shiprender/praha_ferries.py [family …] [--preview DIR]` (models in `boatkit.py`). They sit on the water lane of the native small ferries (`fitlane.py` re-derives it from `src/`), with `image_offset: [0, 0]` and `length: 8`. Only the Naomi and Kazi wheelhouse glass lights up.

### PID regional lines (`vehicle-bus/pid/`)

Agency `PID` builds `VZ-PID-bus.pak` with the buses of the suburban and regional PID contracts (35 areas from 12/2024, 13 operators, about 1,530 buses; October 2026 rosters). It holds only the type × livery combinations that `VZ-Praha` / `VZ-DPPraha` don't already have, because the regional lines use those city objects as they are. 92 % of the fleet wears the PID 2021 grey-red, 6 % the old trikolóra; operators' own schemes and advert wraps get no object.

`tools/busrender/pid.py` paints the IREDO coach-pipeline bodies (and the odis.py CNG roofs) with two liveries:
- `pidsedocervena`: grey body, a black glazing band up to the roof edge, and a red column behind the front axle and one over the rear axle (body `PID_COLS` overrides). Each column covers the lower body and the cant and crosses the roof as a band. A red block sits on the vehicle's left of the lower front and rear.
- `pidcervenomodrobila`: blue roof and cant, white band, red lower body.

The colours are those of praha.py "A" / "B". The articulated types come from two more models:
- `praha_man.py`'s `Artic` mixin draws the MAN Lion's City 18C (on the 12C body), the Lion's City G (on the NL 293 body) and the Mercedes-Benz Citaro C2 GÜ (`CitaroC2`, a Citaro face on the NewGen box). Positions are given in real metres and mapped onto the drawn sections (7 + 6 carunits of `MPU` m). Each section is placed by the section rule and has its own bellows half (`build_artic_rows`).
- `praha_man.LionsCity10E` is the 12C body shortened to 10.575 m with the battery roof. `build_row_rule` places a single-section body by the section rule instead of centring it.
- `pid.PSolaris` is a subclass of `dpo_solaris.Solaris` that paints the DPO Urbino 18 III / IV models in both PID liveries ("pa" / "pb"). The DPO sheets stay untouched.

Run `python tools/busrender/pid.py [family …] [--yaml] [--preview DIR]`. Still to come (TODO): the one-off bodies the repo doesn't have.

### Královéhradecký kraj (`vehicle-bus/iredo/`, `vehicle-bus/mhd-<town>/`)

The kraj's regional buses are named after the integrated system: agency `IREDO` builds `VZ-IREDO-bus.pak`, which also holds the town lines integrated in IREDO (Náchod, Rychnov nad Kněžnou, Týniště, Vrchlabí, Dvůr Králové). Town systems outside IREDO get their own `MHD<Town>` pak (Trutnov, Špindlerův Mlýn, Jičín, Nová Paka, Kostelec nad Orlicí). As in Prague, there is one object per type × livery and the operator appears only in the livery display name.

Pardubický kraj's IREDO buses are in the same pak (October 2026: 8 areas, 2022–2032 contracts).
- Its white buses carry no KHK sticker, so they are the livery `bilapk`. A livery switches the sticker off with `sticker = False`, in both iredo_models and khk_small. The SOR CN roof step is painted black.
- Further liveries: Arriva's turquoise-cream, ZDAR's white-blue-red, BORS, and the PID trikolóra on the older SOR CN 12.
- CAR-TOUR's one-offs: the Setra S 419 UL is pid.py's body in `bilapk` (iredo_coaches.py falls back to pid.py for models it lacks), and the Citaro C2 LE Ü is `praha_man.CitaroC2LEU` repainted white by pk_town.py.
- Its integrated town lines (Chrudim, Přelouč) are in VZ-IREDO too. Ústí nad Orlicí, Litomyšl and Polička have their own `MHD<Town>` paks, built by `tools/busrender/pk_town.py` from copies and repaints of repo sheets.

The kraj has no uniform IREDO paint. Each contract operator keeps its own scheme: `bila` (BusLine KHK, KAD), `transdev` (white with the big red Transdev figure), `cds` (CDS Náchod yellow with the red CDS), `ptransport` (P-transport yellow-red), plus the legacy BusLine `buslinezelena` / `buslinezlutozelena`. Every IREDO bus carries the kraj sticker, drawn as a light panel over the upper rear window; town-pak buses don't. The scope is the vehicles each operator ran in October 2026. On seznam-autobusu.cz, count only operator periods that are open-ended ("od m/yyyy"): a vehicle in service elsewhere has already left.

The art regenerates with:

- `iredo.py` (models in `iredo_models.py`, on the RegioJet coach modules): the SOR CN / C and Crossway families. The SOR CN's signature (raised rear roof and window line, the middle door rising into it, rounded caps, hopper windows) is drawn exaggerated, as the user required, so it reads like the VTPsim hand art.
- `iredo_coaches.py` (models in `iredo_coachmodels.py`): Setra S 415 / 418 LE, Evadys, Arway, Irizar i4, Axer, SOR ICN, the Mercedes-Benz Intouro / Integro II L and the Scania Citywide II LE (the last two also used by pid.py).
- `khk_small.py`: midibuses and vans, rendered on `praha_small.py` or repainted from VTPsim's sheets.
- `khk_town.py`: the SOR EBN on the `dpmhk.py` bodies, and the Trutnov and Špindlerův Mlýn fleets (Trutnov's SOR NB 12 / NBG 18 come from `sor_town.py`).

Each driver takes `[family …] [--yaml] [--preview DIR]`; `--yaml` regenerates the family.yaml files from the driver's tables.

Every box body with a `low()` takes the body shape `iredo_models.SHAPE`, and so do the drivers built on these models (pid.py, odis.py, odis_town.py). The default is `low`, the owner's pick of 2026-10-24 after the SORs read "too tall and boxy at the bottom" next to the CZR / VTPsim hand art:
- 2.76 m wide, the lowest body row left off so the bus stands on its wheels (`SKIRT`);
- the window band up to the roof edge, and a one-row SOR hump;
- 1 px roof pods, and the livery's own (white) roof;
- the SOR rear as photographed (`SOR_REAR "photo"`): rear window under the roof cap, red marker lamps at its corners, a louvre line, tall lamp clusters, the plate, the bumper.

The owner turned down a raised body on bigger wheels with the rub strip (shape `raised`): the front wheel became a black block. The first draft (`low1`: grey roofs, a plain block rear) and the shape before 2026-10-22 (`orig`) also stay selectable. Use `odis.py --shape NAME [--out DIR]`, or set `iredo_models.SHAPE[0]` before running another driver. A body's `low()` returns its own rows (wall top, glazing, rear window) and can read the shape's common keys.

The Iveco and coach bodies took the shape the same day. The Crossway family (`CrosswayLELine.low()`: every length and the Irisbus fronts) keeps its measured 3.16 m wall (`LOW_TOP` 12; 11 is the SOR height, turned down) with the glazing from 1.73 m up to the roof edge, two rows of the lighter glass, the lighter windscreen and its own rear (`CrosswayLELine.rear`: rear window under the roof, brake lamps over it, tall tail-lamp clusters down the corners, the plate in the bumper). Every other `CoachBus` (Setra S 4xx / 5xx LE, Evadys, Arway, Karosa Axer, Irizar i4, Mercedes Intouro / Integro II L, Scania Citywide II LE) takes the width, wheels and roof but keeps its own height and window line. The DPP Crossway PRO (`dpp_coaches.py`) reads the same `SHAPE`.

### Solaris town fleets (`tools/busrender/solaris_town.py`)

Since 2026-10-28 the TommPa9 Škoda 26Tr (Brno, Pardubice, Opava) and 27Tr (Brno) and Solaris Urbino 18 (Brno, Olomouc, Tábor), Urbino 12 III / IV (Olomouc, Tábor) and Urbino 10,5 (DPP; its PID grey-red through pid.solaris) sheets are rendered on the `dpo_solaris.py` bodies instead (owner: one drawing per bus type, every 18 m articulated bus at 8 + 6 carunits). `SVeh` paints the Solaris model from sor_town.py's town palettes (`TOWNS`). Run `python tools/busrender/solaris_town.py [family …] [--preview DIR]`; the yamls are hand-written.

### Crossway LE town fleets (`tools/busrender/crossway_town.py`)

Since 2026-10-28 every Iveco / Irisbus Crossway LE town family (Brno, DPMB, DPMP, DPP, Praha, Český Těšín, Frýdek-Místek, Přerov, Příbram, Tábor) is rendered on the `iredo_models.py` Crossway bodies instead of Lubak91's sheets (owner: one drawing per bus type). The town variants live in `iredo_models.py` too: `CrosswayLECity145` (2-2-1), `CrosswayLECity108x3`, `CrosswayLECity12Hybrid` (the DPMP battery box) and the low-entry `IrisbusCrosswayLE128`, which PID's 12,8M uses as well. A town livery is a `TownBands` row scheme (`skirt` / `sill` / `lower` bands) registered by `town()`; the PID, 3ČSAD and plain-white liveries come from their own drivers. The Trutnov car stays in khk_town.py, rendered in the same Arriva blue. Run `python tools/busrender/crossway_town.py [family …] [--preview DIR]`; the yamls are hand-written.

### Moravskoslezský kraj (ODIS) town buses (`vehicle-bus/mhd-<town>/`)

Every ODIS town with MHD has its own `MHD<Town>` pak (user, 2026-10-20). The ODIS regional pak (`VZ-ODIS-bus`, next section) holds only regional buses, never a town fleet. Ostrava (`DPOstrava`), Opava (`DPOpava`), Frýdek-Místek, Třinec, Český Těšín, Nový Jičín, Studénka and Krnov already had one. The four towns the region had folded in got theirs from `tools/busrender/odis_town.py`:

- `MHDHavirov`: the blue city scheme on everything except the three 2018 e-buses.
- `MHDKarvina`: the white-black SOR NS 12, plus 3ČSAD white-green and white.
- `MHDOrlova`: 3ČSAD white-green and the white Isuzu.
- `MHDBruntal`: one SOR CNG 12 with the BRUNTÁL logo and the kraj ring in green.

The scope is what each town runs in October 2026, including depot buses that work its lines every day (the Orlová Stratos 619, Crossways 600 / 411 and the Irisbus Crossway LE 393 / 401). The Dekstra 448 came back from storage in October 2026. It leaves out stored buses, other reserves and regional stand-ins; a regional bus that works a town line is the town line's VZ-ODIS object. The old `CZ-ODIS-*` (VTPsim, `CZ-vehicle-bus.pak`) and `CZR-ODIS-*` objects stay installed. The green CZ-ODIS buses are the 3ČSAD white-green group scheme; the CZR "Red" ones are Transdev Morava regional and the "WhiteGray" ones the plain kraj regional scheme.

`odis_town.py` picks the method per type:

- The SOR NS 12 / NSG 12 / NSG 18 are painted on the `dpmhk.py` bodies by its `OVeh`. The cars from 2023 on get the 2023 SOR face.
- The SOR CN (CNG 10,5, BNG 10,5, CNG 12) and the Crossway LE LINE 10,8M use the `iredo_models.py` classes, with liveries registered from the driver.
- Every other type is a repo sheet repainted zone by zone (`repaint`). The fitted box splits roof from side, so the Havířov roof gets the lighter blue. Shading comes from each pixel's luminance over its zone median. Roof boxes are added with `add_pods`, and the city logo and slogan follow the window band line.
- Types the repo had no body of are ported from VTPsim's ODIS sheets, frozen in `tools/busrender/src/odis/`: the Citelis, Citywide LE 15M, BN 9,5 and Stratos LF 38. `port_native` turns their glass into the lit specials (driver's glass plain) and moves every view onto the native lane by the length rule.
- Same body and same paint as an existing family is a copy of its sheet: the F-M 3ČSAD Urbanway / Citywide (displays turned white LED) and the 2018 3ČSAD e-bus.

The 3ČSAD white-green is one paint in every package: `CsadWG` with the green `CSAD["green"]` 57A639, a yellow-green near RAL 6018. The owner picked it on 2026-10-24 over the emerald 22B14C, which read "too green". The white band from the skirt to the windows is never shorter than the green, because in the game the bus must read white and green. `CSAD_GREEN` (the emerald) is only the key that VTPsim's green is ported as before a repaint. The static Frýdek-Místek 3ČSAD sheets are frozen as ported in `src/odis/FM-*`. `odis_town.py --csad-static` writes the F-M sheets from them in the new green. The Havířov, Karviná and Orlová sheets also read them, so the Havířov blue repaints don't change.

Run `python tools/busrender/odis_town.py [family …] [--yaml] [--preview DIR]`. A run is byte-identical.

### Moravskoslezský kraj (ODIS) regional buses (`vehicle-bus/odis/`)

Agency `ODIS` builds `VZ-ODIS-bus.pak` with the kraj's regional buses only. As in IREDO there is one object per type × livery, and the operator appears only in the livery display name. The scope is the October 2026 fleet of the three contract operators: Transdev Morava, Transdev Slezsko and Z-Group bus. No other operator holds a kraj contract.

The kraj sets no body colour, so each operator keeps its own scheme. Every scheme adds the kraj ring over the rear axle on both sides, in the operator's colours:

- `transdev`: Transdev Morava, white with the big red figure and the ring in reds.
- `3csadbilozelena`: Transdev Slezsko, the 3ČSAD white-green (odis_town's `CsadWG`, see the town section) with the ring in greens. The unchosen greens stay available for previews: `--variant csad=B|C|old`.
- `bila`: Z-Group bus, white with the ring in the kraj's grey, red and blue.
- `bilazelenykruh` / `bilacervenykruh`: Transdev Slezsko's white buses, green ring in Havířovsko and red in Hlučínsko.
- `odiscervenocerna`: the uniform red ODIS scheme of the contracts from 12/2025 (Jablunkovsko–Třinecko). It has no ring.

`tools/busrender/odis.py` builds every sheet and imports `odis_town.py` for its repaint tools:

- **The ring:** `Ring` follows the kraj design manual (three bands of twelve segments, open at the lower front). It is drawn 2.1 m across, centred 0.4 m behind the rear axle and 1.4 m up, and tinted on the glass.
- **SOR CN / CNG / C / ICN, Crossway LE LINE / LE CITY, Setra S 415 LE:** the IREDO box models with the `Regio` mixin, which handles the ring on the glass, white LED displays and a second roof box (`REAR_AC`). Their CNG fairings follow the photos.
  - The NP Crossways are CNG (Iveco's Natural Power) with a long flat fairing.
  - The 2025 Crossway and the ICNG 12,3 get their own faces, `CrosswayFace2024` and `IcnFace2025`.
- **Scania Citywide LE 12M / Suburban 12,6M / LE 13,7M / LE 15M / Suburban 15M:** VTPsim's ODIS sheets frozen in `tools/busrender/src/odis/`, ported by `port_native`. VTPsim's stand-in for the ring is painted out (`strip_marks`), then the sheet is repainted and gets its CNG pods and the ring (`ring_decal`).
- **Dekstra LE 37 L CNG, Rošero First CNG, Urbanway 10,5M CNG:** repaints of the IREDO and MDPO sheets. The 3ČSAD skirt is painted by height (`skirt_decal`) and the red ODIS decals by `odis_red_decal`.
- **MAN Lion's City Ü CNG:** `praha_man.OldGen` with two doors and the CNG roof.

Run `python tools/busrender/odis.py [family …] [--yaml] [--preview DIR]`. A run is byte-identical.

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

`reverse: true` is only exact for `length: 8` sections: a 180°-rotated sprite keeps its body offset, which is wrong for any other length (see "Section placement"). Units whose end cars are not 8 carunits long (e.g. the Leo Express FLIRT 480, LINT 41, and the RegioSprinter's cab module A 5 + middle module M 2 + cab module B 5) draw the rear cab car as its own row instead.

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

### Bus layover bays (`station-road/odstavne-stani/`)

`VZ-Stations-road.pak` holds three road stops where buses wait out their layover beside the road: `BusLayover-DeadEnd` (`layover=3`, 4 layouts in stock terminal order, two bays at ±0.25 tile and a paved turning area), `BusLayover-OneSide` (`layover=1`, 4 layouts: N-S bays east, E-W bays north, N-S bays west, E-W bays south, two bays at 0.275 / 0.415) and `BusLayover-BothSides` (`layover=2`, 2 layouts, bays at ±0.40). An object sets `layouts:` in station.yaml when it has fewer than 16. The `layover` key exists only in the simutrans-122.0 fork, so the set is `makeobj: fork`; installed since 2026-10-10 with fork exe d2dd317. The engine parks buses at these bay centres (map frame, tile units from the road centre line; native asphalt ±0.335, lanes ±0.135), so keep `tools/gen_layover.py` and the engine in step. Regenerate with `python tools/gen_layover.py station-road/odstavne-stani`.

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

`industry-city/restaurace/` (`group: Restaurants`, `VZ-Restaurants-city.pak`) holds upstream city factories ported 1:1 instead: Sarlock's Simutrans Fried Chicken from pak128.cs `factories.pak`, with its art, goods, productivity and range unchanged and the passenger and mail values of a 1×2 supermarket. Upstream it had passenger demand 50 against 3 for a supermarket, and distribution weight 40, so a map filled up with them (owner, 2026-10-25). The port spawns at weight 2. The native stays installed by the owner's choice, so the port is named "Simutrans Fried Chicken (VZ)" to tell the two apart in the Build industry list; the save's SFCs were renamed to the port. Keep `productivity` as upstream: a factory's passenger demand is scaled by its saved production base over the type's `productivity`. `python tools/factory_extract.py <pak> <factory name> <out.png> [--front-offset X Y]` writes such a sheet from a compiled pak and prints its data in industry.yaml terms. An animated sign is front images: an object with `front: {offset: [X, Y]}` has them below the back images (row `8 + (season * 4 + layout) * tiles + tile`, column = phase), drawn X, Y px up-left of their place so a sign that overhangs its tile fits its cell; build.py emits them with that offset.

## Signals (`signal.yaml`)

Rail signals live under `signal-rail/signals/signal.yaml` (`group: Signals` → `dist/VZ-Signals-rail.pak`). Object `name=` is `VZ-Signals-<id>`; `fields` are the makeobj roadsign keys (`is_signal`, `is_presignal`, `free_route`, `is_longblocksignal`, `single_way`, `end_of_choose`, `min_speed`, `cost`, `offset_left`, `intro_year`, …). The build emits `obj=roadsign`, `waytype=track`, `Image[4*row+col]` for every state row, then `cursor` and `icon`.

Sheet layout (from `tools/sign_extract.py` and `tools/gen_signals.py`): 4 columns, the image directions N, S, W, E, by one row per state, plus a last row with the cursor in col 0 and the 32×32 icon in col 1. The engine uses states 0 (red) and 1 (green) for plain, long, P and hradlo signals, and state 2 for presignals, so those ship 8 and 12 images. In the simutrans-122.0 fork choose and LT signals (e43fc17) and autoblocks (c9ac259) with exactly 12 images also show state 2, yellow. Don't go past those counts: a plain signal with 16+ images has its images 8+ read as a second set for electrified track (`signal_t::calc_image`).

Two keys exist only in the simutrans-122.0 fork (PR #4): `is_platformsignal=1` (P, with `is_signal=1`; 8 images) and `station_boundary=1` (LT: 4 images for a static board like D3-LT, or 8 / 12 for red, green and yellow aspects; the fork shows an LT's aspects instead of treating it as a traffic light). A third, `is_blockpost=1` (with `is_signal=1`; 8 images), marks the hradlo (block post) signals, and a fourth, `is_autoblock=1` (with `is_signal=1`; 12 images: red, green, yellow), the automatic block signals: red while the block ahead up to the next signal is reserved or occupied by another train, otherwise green when the block ends at another autoblock and yellow (since fork c9ac259) when it has a switch or ends at any other signal, a station boundary or a buffer stop (an 8-image autoblock shows green instead); running and reservation are those of a plain signal. Autoblocks belong on double track or plain block lines, not between a P and its LT (a signal there turns the P's section mode off). The fork's tool places autoblocks one-way only (clicking again turns them round); a Block signal placed two-way before fork 4740a3e stays two-way, where its aspect can be wrong though driving is not affected. The stock makeobj silently drops them, so the set says `makeobj: fork` and builds with `MAKEOBJ_FORK_PATH`. Where that variable is unset, the build skips the pak and the install step keeps the installed copy. (`install: false` on a set would build it into `dist/hold/`, which is never installed.)

- **D1**, in three styles: `New` (AŽD 70), `Old` (SSSR mast signals) and `Dwarf` (SSSR dwarfs). Each style has Block, Main, Shunt, PreSignal, Choose, Long, P and LT (`VZ-Signals-D1-<Style>-<Function>`). The style is only the look; the function is shown by a plate (štítek) under the head in the real D1 colours, except Main. Block is the automatic block signal (`is_autoblock`, generator function `autoblock`): white plate and white mast (D1 čl. 69), in 12 images: red, green, yellow (one yellow lamp, výstraha; the dwarf's green lamp recoloured). Main is the plain signal (red until a train reserves the block) with the hradlo's look on a two-lamp head (red and green only, red-white mast) and no plate at all, the only D1 signal without one. Shunt blue, presignal black, long red, choose red plus a direction indicator box on top of the head, lit when a route is set, in 12 images: red, green, yellow (the train was sent to another platform than its schedule's, or through a diverging route; two yellows on AŽD 70 and SSSR, one on the dwarf), P red plus a white track-number plate. LT is the style's entry signal (vjezdové návěstidlo): the entry-signal head, a solid red plate with a white L and no direction box, in 12 images: red (no train let in), green (straight route through the throat), yellow (diverging route: two yellows, 40 km/h, on the AŽD 70 5-lamp head with the calling-on lamp and on the SSSR double head; one yellow on the dwarf). Hradlo signals: `D1-New-AH` (automatic, AŽD 70 with a relay cabinet) and `D1-Old-Hradlo` (manual, SSSR with the block post hut, drawn in the N and W images only so a placed pair shows one hut); both have the red plate and red-white mast band that ČD D1 čl. 67 gives every main signal except automatic block ones.
- **D3**: `VZ-Signals-D3-LT` is the plain lichoběžníková tabulka (D1 čl. 976, drawing Ž09-3). `VZ-Signals-D3-P` is a low Místo zastavení board (čl. 988) with no lamp, so red and green look the same (user's choice: the train's behaviour shows the state). Boards stand across the track and are drawn in the pak128 projection, like pak128.cs's `Minimum*` boards: the painted face in the N/W images, the grey back in S/E, slanting 1 px per 2 px.
- **1:1 ports**: the one-way and end-of-choose signs, the Minimum speed boards and RailGate, under `VZ-Signals-<original name>`.

The D1/D3 sheets are generated from the extracted pak128.cs art in `signal-rail/pak128cs-source/` (all 76 objects of `infrastructure.rail_signals.pak`, with `objects.yaml`): run `python tools/gen_signals.py signal-rail/signals [--only ID] [--preview DIR]`. To change the art, change the generator. Lamps use the always-lit specials `FF211D`, `01DD01`, `FFFF53` and `0101FF`. `signal-rail/migration-map.tsv` maps every old pak128.cs signal name to its VZ successor, keeping the same function flag, for the savegame migration. The mechanical ČSD semaphores (`Mechanic_*`) are not in the VZ pak. They are kept, with their original names, in `legacy/rail-signals-mechanic/infrastructure.rail_signals_mechanic.pak`, a committed backup built with the stock makeobj from the `.dat` and sprites next to it.

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

The set of class-prefix modes is defined as `MODES_WITH_CLASS_PREFIX` in `build.py` (currently `{"rail"}`). `<id>` uses the natural dotted form (e.g. `Class 814.0`). Encoding: UTF-8 with BOM (see above). Czech display strings use full diacritics; diacritics-free forms are reserved for filenames and object `name=`.

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
