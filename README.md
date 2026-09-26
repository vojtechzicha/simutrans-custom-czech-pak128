# simutrans-custom-czech-pak128

A custom Czech addon set for [Simutrans (Extended)](https://www.simutrans.com/) pak128.
Ships Czech rail, bus, and tram vehicles (and eventually water / air) in real-world
liveries, matching pak128 art conventions.

The addon prefix `VZ-` is used on every shipped `.pak` so the set never collides with
the upstream pak being shadowed.

> **Status:** early development. Everything is on `main`; the table below lists the
> families considered finished, and the list after it the ones still being refined.

## Finished families

A single pak file per agency and transport mode — for example, every shipped
ČD rail family lives in `dist/VZ-CeskeDrahy-rail.pak`.

| Family | Liveries |
| --- | --- |
| ČD řada 111 ("Tyristorka", shunting electric) | Najbrt 2, Najbrt 1.2 |
| ČD řada 113 ("Žehlička", Tábor–Bechyně) | oranžovo-krémová, zeleno-krémová |
| ČD řada 151 ("Krysa", pak128.cs art) | modrá |
| ČD řada 162 ("Peršing") | Najbrt 2, Najbrt 1.2; also zeleno-krémová and modrá (pak128.cs art) |
| ČD řada 163 ("Peršing") | Najbrt 2, zeleno-žlutá; also zeleno-žlutá and modrá (pak128.cs art) |
| ČD řada 193 (Siemens Vectron MS) | ČD Vectron, ČD Vectron RS Lease; also bílá and modrá (CZR art) |
| ČD řada 210 ("Jezevec") | Najbrt 2, modro-krémová, červeno-žlutá |
| ČD řada 242 ("Plecháč", pak128.cs art) | červeno-krémová |
| ČD řada 362 ("Eso", incl. the 362.2 rebuilds) | Najbrt 2, Najbrt 1.2; also modro-krémová and modrá (pak128.cs art) |
| ČD řada 371 ("Bastard") | Najbrt 2; also červeno-žlutá and modrá (pak128.cs art) |
| ČD řada 380 (Škoda 109E) | ČD 109E, Najbrt 2; also ČD 109E and bílo-modrá (pak128.cs art) |
| ČD řada 384 (Siemens Vectron MS 230) | ČD 230 km/h |
| ČD řada 440 (RegioPanter, 3 kV; renumbered 640.1 in 2021–22) | Najbrt 1.2, Najbrt 2 |
| ČD řada 471 (CityElefant) + 071 + 971 | CityElefant bílo-modro-červená, PID šedo-červená, Najbrt 1, Najbrt 2 |
| ČD řada 530 / 550 (Moravia, owned by Jihomoravský kraj) | Jihomoravský kraj |
| ČD řada 640, 640.1 (RegioPanter) | Najbrt 1.2, Najbrt 2 |
| ČD řada 640.2 (RegioPanter) | Najbrt 2, PID šedo-červená |
| ČD řada 642 (Siemens Desiro Classic) | DÚK zeleno-bílá |
| ČD řada 650 (RegioPanter) | Najbrt 1.2, Najbrt 2 |
| ČD řada 650.2 (RegioPanter) | Najbrt 2, Plzeňský kraj |
| ČD řada 660.0, 660.1 (InterPanter) | Najbrt 2 |
| ČD řada 680 (Pendolino) | stříbrno-tyrkysová (Kotas) |
| ČD řada 690.2 (battery RegioPanter) | ČD zeleno-modro-bílá |
| ČD řada 704 (ČKD T 238.0 shunter) | červeno-krémová, Najbrt 2, Najbrt 1.2 |
| ČD řada 714 ("Velká krava") | červeno-modrá, Najbrt 2, Najbrt 1.2 |
| ČD řada 743.2 (CZ LOKO EffiShunter 1000M) | Najbrt 2 |
| ČD řada 750 ("Brejlovec", pak128.cs art) | zeleno-šedá, modrá |
| ČD řada 750.7 ("Brejlovec", CZ LOKO rebuild) | Najbrt 2, Najbrt 1.2 |
| ČD řada 754 ("Brejlovec") | Najbrt 2, Najbrt 1.2, Najbrt 1, červeno-žlutá, modro-krémová; also modro-žlutá and modrá (pak128.cs art) |
| ČD řada 794 (CZ LOKO shunter) | Najbrt 2 |
| ČD řada 799 ("Adéla" depot shunter) | oranžovo-modrá, Najbrt 2 |
| ČD řada 809 ("Šukafon") | Najbrt 1, Najbrt 2, červeno-krémová, červeno-žlutá |
| ČD řada 810 ("Šukafon") + 010 trailer | Najbrt 1, Najbrt 2, červeno-krémová; 810 also in Pardubický kraj and PID červeno-modro-bílá |
| ČD řada 811 (RegioMouse) + 012 trailer | Najbrt 2, Moravskoslezský kraj |
| ČD řada 814.0 (RegioNova) | žluto-zelená, Najbrt 2, Plzeňský kraj, Pardubický kraj, Kraj Vysočina, PID šedo-červená |
| ČD řada 814.2 (RegioNova Trio) | žluto-zelená, Najbrt 2, PID šedo-červená |
| ČD řada 840 (Stadler RegioSpider) | Najbrt 1, Liberecký kraj |
| ČD řada 841 (Stadler RegioSpider) | Najbrt 1 |
| ČD řada 841.2 (Stadler RegioSpider) | DÚK zeleno-bílá, HzL krémovo-červená, Pardubický kraj, PID šedo-červená, Najbrt 2, světle šedá |
| ČD řada 841.3 (Stadler RegioSpider) | PID šedo-červená |
| ČD řada 842 ("Kvatro") + 054 / 954 trailers | Najbrt 1, Najbrt 2; trailers Najbrt 2, červeno-krémová |
| ČD řada 843 ("Rakev") + 043 / 943 trailers | Najbrt 1, Najbrt 2, červeno-krémová (943 Najbrt only) |
| ČD řada 844 (PESA RegioShark) | Najbrt 2, Pardubický kraj, Plzeňský kraj |
| ČD řada 847 (PESA RegioFox) | Najbrt 2, PID šedo-červená, Plzeňský kraj, Pardubický kraj |
| ČD řada 848 (Stadler GTW 2/6) | Najbrt 2 with Olomoucký kraj decals |
| ČD řada 854 ("Hydra") | Najbrt 2, červeno-krémová |
| ČD řada 1216 (Siemens Taurus, CZR / pak128.cs art; railjet pair runs cab-first) | Najbrt 2, railjet |
| ČD coaches built for ČD, UIC-Z: Ampz 143, Ampz 146, Bmz 241, Bmz 245, WRmz 815, WLABmz 826 | Najbrt 2 |
| ČD ex-ÖBB coaches: Bmz 226 / 232 / 234 / 235 / 229 / 224, Bdmz 223, Bdmpz 227, Bhmpz 228, ABmz 346, Amz 138, WRmz 817, Bcmz 834 | Najbrt 2; Bmz 232 also ÖBB šedo-červená |
| ČD rebuilt Bautzen coaches: Bbdgmee 236, Bdmpee 233, ARmpee 829 / 832, WLABmee 823 | Najbrt 2 |
| ČD "honecker" coaches: Bdmtee 281, 275, 267 | Najbrt 2 |
| ČD UIC-Y coaches: Aee 140, Apee 139, Bee 238, Bpee 237; Aee 145, AB 349, Bee 272 / 273, Bd 264, BDs 449 | Najbrt 2; BDs 449 also Najbrt BD 2 / BD 1 |
| ČD Studénka coaches: Bdpee 231, ABpee 347, Bdtee 276, Bdt 279 / 280, "sysel" driving trailers Bfhpvee 295 / ABfhpvee 395 | Najbrt 2, Najbrt 1 |
| ČD double-deck coaches: Görlitz Bdmteeo 294 / 296, Škoda 13Ev set (ABfbdmteeo 396 + Bdmteeo 297 / 298) | Najbrt 2 |
| ČD ComfortJet, 9-car set incl. Afmpz 880 driving trailer and BRmpz 882 (CZR art) | ComfortJet |
| ČD railjet (7-car) and InterJet (5-car), each also turned round (CZR art, ported 1:1) | railjet, InterJet |
| DPmML SOR NB 12, NS 12, NB 18 and NS 18 (bus) | Most žluto-červená |
| DPmML Irisbus Citelis 12M and Citelis 18M (bus) | Most žluto-červená |
| DPmML Iveco Urbanway 18M (bus) | Most žluto-červená |
| DPmML Iveco E-Way 12M (bus) | Iveco předváděcí |
| DPmML Pragoimex EVO2 and EVO1 (tram) | Most žluto-červená |
| DPmML Tatra T3M.3 (tram) | Most žluto-červená |
| DPmML Pragoimex VarioLFR.S and Vario LF plus (tram) | Most žluto-červená |
| Narrow platforms + track crossings (rail stations, `VZ-Stations-rail.pak`) | concrete slabs, paving blocks, gravel with Sudop edge — each plain, with a crossing, and as the end of a crossing; crossing-only tiles in concrete, rubber and wood (sprites generated by `tools/gen_platforms.py`) |

## Work in progress

Also on `main`, still being refined (see [`TODO.md`](TODO.md)):

- **DP Ostrava (DPO)** — full city fleet across all three urban modes (introduces
  the `vehicle-trolleybus/` mode): 11 bus families, 12 tram families, 9 trolleybus
  families. Verified against the 2025–2026 active roster; real-world retirement
  dates set on the handful of types that have left service.
- **DP města Pardubic (DPMP)** — the full active 2026 bus and trolleybus fleet:
  Irisbus Citybus 12M, Irisbus Citelis 12M (diesel + CNG), Iveco Crossway LE
  City 12M (diesel + hybrid), Iveco Urbanway 12M (diesel + CNG), Iveco Streetway
  12M, Isuzu NovoCiti Life, SOR BN 9,5, and Škoda 26Tr, 28Tr, 30Tr and 32Tr
  trolleybuses, in the DPMP white-red scheme (32Tr in its black-front variant).
- **DP města Hradce Králové (DPMHK)** — the active September 2026 bus and
  trolleybus fleet, drawn from scratch with a box renderer (`tools/busrender/`),
  with night-lit windows only when loaded: Škoda 30Tr (plus the battery and
  diesel-generator cars), 31Tr, and the new 32Tr and 33Tr; SOR NS 12 (diesel and
  electric), NS 18, Iveco Urbanway 12M (diesel and Hybrid), Urbanway 18M Hybrid,
  Irisbus Citelis 18M, and the one-off SOR EBN 9,5 (Zelená linka) and EBN 11.
  Liveries: the classic DPMHK red-yellow-white (white-front and SOR NS
  black-front executions) and the 2026 vertical design with the crowned G.
- **DP hl. m. Prahy (DPP) and DP města Brna (DPMB)** — the complete active
  September 2026 bus, tram and trolleybus fleets of both cities as VZ families,
  replacing the upstream CZR/CZ Praha and Brno paks. Placeholder art was redrawn
  (several types from scratch), wrong liveries were repainted, and every sprite
  sits at the native lane/track position with night-lit windows only when loaded:
  - DPP trams: Škoda 52T ForCity Plus (5 sections), 15T, 15T4, 14T (PID and
    original), Tatra KT8D5.RN2P (PID and classic), T3R.P and T3R.PLF (red-cream
    and wine-silver), T3R.PV, T3M.2-DVC; mixed T3 sets such as T3R.PLF + T3R.P.
  - DPP buses: Iveco Streetway 12M/18M, Urbanway 18M Hybrid, SOR NB 12, NB 18,
    BN 12, ENS 12 (with its tram-style charging pantograph), ICN 9,5, Škoda
    E'City 36BB, Solaris Urbino 8,9 LE and 10,5, Iveco Crossway LE 12,8M and
    LE CITY 14,5M (3 axles).
  - DPP trolleybuses: SOR TNS 12 and TNS 18, Škoda-Solaris 24m, Bozankaya SNG
    12T, Škoda 36Tr.
  - DPMB trams: Škoda 45T and Pragoimex EVO2 (drawn from scratch), 13T, 03T6
    Anitra, Pars nova K3R-N, KT8D5R.N2 and KT8D5N, VarioLFR.E and VarioLF2R.E,
    T6A5, T3G, T3R, T3R.PV and T3R.EV.
  - DPMB buses: Iveco Urbanway 12M (diesel and CNG) and 18M CNG, SOR NBG 12,
    NS 12, ICN 9,5, Irisbus Citelis 12M CNG, Iveco Crossway LE CITY 12M NP,
    LE CITY 14,5M and LE LINE 12M, Solaris Urbino 18.
  - DPMB trolleybuses: Škoda 26Tr, 27Tr, 31Tr, 32Tr and SOR TNS 12.
- **Other city (MHD) fleets** — the active September 2026 rosters of 16 more
  towns, imported from the older pak128_czr sets and completed. Placeholder and
  wrong-livery art was repainted, missing types were drawn from the closest body,
  and every sprite sits at the native lane position with night-lit windows only
  when loaded:
  - DPMO Olomouc: Solaris Urbino 12/18 (gen. III and IV), Alpino 8.6,
    SOR NS 12 electric; trams T3R.P, VarioLF, VarioLF plus/o, EVO1, EVO1/o,
    Inekon 01 Trio.
  - MDPO Opava: Irisbus Citelis, Iveco Urbanway 10,5/12M CNG, SOR NSG 12 and
    NS 12 electric; Škoda 26Tr, 32Tr and 36Tr trolleybuses.
  - Frýdek-Místek, Třinec, Český Těšín, Nový Jičín, Studénka, Krnov, Hranice
    and Přerov (contracted MHD, town or operator schemes).
  - Kladno, DPMLB Mladá Boleslav, Kolín, Příbram, Benešov and Tábor.
- **Die Länderbahn CZ** — 654 Pesa LINK II.
- **Supermarkets** (city industries, `VZ-Supermarkets-city.pak`) — 14 Czech
  chains as consumer industries in three size classes: 1×1 stores (Žabka, Tesco
  Expres, Albert, COOP), 1×2 supermarkets (Lidl, Penny, Billa, Norma, Tesco) and
  2×2 hypermarkets (Kaufland, Globus, Albert Hypermarket, Tesco Hypermarket,
  Makro). Four rotations, summer and snow, shop windows and signs lit at night;
  sprites generated by `tools/gen_shops.py`.
- **Leo Express** (`VZ-LeoExpress-rail.pak`) — the whole group as of 2026, drawn
  from scratch: Stadler FLIRT 480 (black-gold, black, black-orange), Coradia
  LINT 41 (846) and LINT 27 (832) of Leo Express Tenders, LINT 41 (648) of
  Leo Express Slovensko in BRB colours, the Talgo VI set, Siemens Vectron MS
  193 (Leo Express 7193 226 and Railpool silver-blue), ex-DB IC coaches
  Avmmz 106.5 / Bpmmz 284.5 / Bpmmbz 285.3 and the hired RDC couchette
  Bvcmz 248.5. Locomotives and coaches couple freely (`prev/next: any`).
- **Arriva vlaky** (`VZ-Arriva-rail.pak`) — every Arriva train in Czech
  passenger service in 2026, drawn from scratch (sprites generated by
  `tools/railrender/arriva.py`): 845 + 945 ex-DB 628.2 (Arriva blue with the
  roof AC, turquoise-cream, DB red), 642 Siemens Desiro Classic (Arriva blue,
  Crystal Valley, DB red), 846 / 832 Coradia LINT 41 / 27 of Zlínský kraj
  (Arriva blue, the early white-orange), 848 Stadler GTW 2/6 (Arriva blue,
  Jihomoravský kraj, Plzeňský kraj) and the 650 RegioPanter of line P1
  (Plzeňský kraj, a repaint of the ČD 650). Units of any livery couple in
  multiple (`couple_liveries: prev|next`).
- **RegioJet** (`VZ-RegioJet-rail.pak`, `VZ-RegioJet-bus.pak`) — the September
  2026 fleet plus confirmed arrivals, drawn from scratch (sprites generated by
  `tools/railrender/regiojet.py` and `tools/busrender/rj_buses.py`):
  - Locomotives: TRAXX 386.2 and 388.2 / 1388 (RegioJet yellow and RegioJet
    Pool), 162 (the two different sides), the 362.2 rebuilds in their ČSD
    blue-yellow, FNM green-grey, RegioJet 2011 and yellow-grey retro schemes,
    the ELL Vectron 193 in RegioJet yellow (2014–2024), and the depot shunters
    703.602, 740.832 and 730.625 in the colours they really wear.
  - Units: Pesa Elf.eu 654 (DÚK, Ústecký kraj) and 655 (PID), CRRC 665 Sirius
    (R23), RegioPanter 650.2 / 640.2 and the ex-DB 628.2 (DÚK), Pesa
    InterRegio 200 666 / 667 (R9, from 12/2026).
  - Coaches: 22 car types by their RJ codes (ex-ÖBB Ampz / ABmz / Bmz, ex-SBB
    Amz / Bmpz, ex-DB Avmz / Avmmz / Bmpz / Apmmz / Bpmz, the Astra Bmpz and the
    UIC-X couchettes), each drawn from its vagonWEB scale drawing so the window
    rhythm, doors and roof tell them apart; foil-wrapped ex-ÖBB cars also with
    the red ÖBB roof.
  - Coach buses: Irizar i8 (incl. the ex-DB batch with silver lockers), Setra
    S 531 DT double-decker and the Irizar PB (2006–2026).
- **GW Train Regio** (`VZ-GWTrainRegio-rail.pak`) — every GWTR train in 2026
  (sprites generated by `tools/railrender/gwtr.py`): 845 + 945 ex-DB 628.2
  and the twin-motor 845 + 845 pairs (GWTR orange-green, DÚK green-orange),
  818 Siemens-Duewag RegioSprinter in both front versions (ex-RTB with
  buffers, ex-Vogtlandbahn with a centre coupler), all drawn from scratch;
  841.2 Regio-Shuttle RS1 (Plzeňský kraj, IDESKA, orange-green), 810 (orange-
  green, the yellow-black "Jarek"), the rebuilt 816 and the RegioNova 814.5 +
  914.5, repainted from the ČD sheets.

## Requirements

- Python 3.7+
- [`pyyaml`](https://pypi.org/project/PyYAML/) and [`Pillow`](https://pypi.org/project/pillow/)
  (`pip install pyyaml pillow`); Pillow derives the unlit empty-vehicle images
  (see "Night-lit windows" in [`CLAUDE.md`](CLAUDE.md))
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
