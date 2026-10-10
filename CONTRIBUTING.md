# Contributing

Thanks for the interest. This repo ships a generated Simutrans pakset, so the
contribution model is a bit unusual — please read [`CLAUDE.md`](CLAUDE.md) first; it
documents the full data model and build pipeline. The notes below are the short
version.

## Ground rules

- **Never edit generated files.** `.dat` and `.tab` files under `build/` and any
  shipped `.pak` are produced by `build.py`. Edit the source `family.yaml` or the
  per-livery PNG instead and re-run the build.
- **Edit `family.yaml`, not the build script**, for vehicle data changes (cost,
  speed, weight, intro/retire year, constraints, …). The schema is described in
  detail in `CLAUDE.md` under "`family.yaml` schema".
- **One PNG per livery.** Place it at `<family>/sprites/<color>.png`, sized
  `1024 × (vehicles × 128)`. Transparency color is RGB `(231, 255, 255)`.
- **Regenerate, don't paint over generated sheets.** Most sheets come from a
  renderer, painter or generator under `tools/` (see "How the art is made" in the
  README). Change the script and rerun it; a hand edit is lost on the next run.
- **Use the `VZ-` filename prefix** on every shipped asset so this addon set never
  collides with the upstream pak being shadowed.
- **Preserve upstream credit.** Set `family.copyright` to the original upstream
  source (e.g. `Sim`); the build appends `vojtechzicha` automatically.
- **Don't ship variants nobody asked for.** Upstream sets sometimes include trio,
  bike-carrier, etc. variants — leave them out unless explicitly requested.
- **Strip unreferenced sprite columns/rows** before committing a PNG; keep them
  minimal.

## Workflow

1. Add or edit `vehicle-<mode>/<agency>/<family>/family.yaml` and the matching
   `sprites/<color>.png`.
2. Run `python build.py <family-dir> --no-install`. This builds the whole
   agency-mode pak your family belongs to, e.g. `dist/VZ-CeskeDrahy-rail.pak`,
   plus its translations `dist/text/en.VZ-….tab` and `cz.VZ-….tab`.
3. Copy that pak into your pak128.CS folder and its two tabs into the folder's
   `text/` subfolder, then check the result in the depot and in motion. For
   multi-section vehicles, also run `tools/consist_preview.py` on the sheet.
4. Commit only the YAML, PNG and tool changes — `build/`, `dist/`, and `*.pak`
   are `.gitignore`d.

## Branch model

Everything lives on `main`: the families, the art tooling and the notes
(`TODO.md`, `liveries.md`). Larger pieces of work are developed on a short-lived
feature branch, rebased on `origin/main` and merged back. The README lists what
ships; `TODO.md` lists what is still open (borrowed art, missing types).

## Reporting issues

Use GitHub Issues. Helpful things to include:

- Family + livery (e.g. `814.0 zlutozelena`)
- Simutrans build / version (Standard or Extended; revision number)
- What you expected vs. what you saw
- A screenshot if it's a visual issue

## Licensing of contributions

By submitting a contribution you agree it can be released under the project's
[Artistic License 1.0](LICENSE). If your contribution adapts artwork from another
pakset, name the upstream source in the family's `copyright` field (or, for art-
heavy contributions, in the PR description) so attribution survives through the
build.
