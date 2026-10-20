# TODO

Open work only. What ships is listed in [`README.md`](README.md); livery colours
are in [`liveries.md`](liveries.md). Last checked 2026-10-10.

## Art still borrowed or shared

Sheets that show another type's drawing. Other identical sheets in the repo are
deliberate: the same body under another package or operator (DPP / Praha, DPMP /
Kolín NovoCiti), the RegioPanter 440 / 640 / 640.1, 840 / 841, T3G / T3P,
T3R.PV / T3R.EV, the DPO 26Tr / 27Tr partial-trolleybus variants. Their
`family.yaml` comments say so.


## Missing types and liveries

- [ ] DPO trams: **Vario LFR.S** (16 cars) and **Vario LF2R.S** (2). Candidates with
  roof A/C units and equipment boxes were rejected (2026-10-10): don't add roof
  boxes to the Vario body.
- [ ] ČD **841.3** in Liberecký kraj colours, when the cars start in December 2026.
- [ ] ČD **690.0** battery units, when passenger service starts in 2027.
- [ ] Pardubický kraj **IREDO** buses, into the same `VZ-IREDO-bus.pak`.
- [ ] A **PID** package for the regional (non-city) lines around Prague.
- [ ] Uninstall the `CZR-ODIS-*` pak and drop the `CZ-ODIS-*` objects once no save
  uses them any more; `VZ-ODIS-bus` replaces them (migration plan of 2026-10-20 in
  the ODIS memory note).
- [ ] ODIS Českotěšínsko II (Transdev Slezsko, from 13 Dec 2026): red ODIS buses,
  among them the **SOR ICNG 10,5**, a body the repo doesn't have yet.
- [ ] Havířovsko III (kraj contract, Transdev Slezsko): 4 hydrogen SOR NSF 12 + 9
  CNG buses in the red ODIS scheme from 12/2027 on the Havířov – Ostrava lines.
  They go into `VZ-ODIS-bus`.
- [ ] ODIS one-offs left out: Z-Group's SOR CN 12 63-1401 in the BORS Břeclav
  yellow-blue, the two Transdev Slezsko SOR CNG 12 with a green CNG pod.
- [ ] MHD Orlová: add the Dekstra LF 38 CNG 448 if it comes back from storage (out of
  service since mid-2025).


## DPO follow-ups

- [ ] Drop the turquoise **Urbino 10** (`VZ-DPOstrava-SolarisUrbino10_s3-dpotyrkysova-…`):
  no DPO Urbino 10 ever ran in turquoise and the owner dropped it, but every save
  references it (14 times in FORK-CZR-VZ.sve). Migrate the live save first.
- [ ] yaml dates that disagree with the art: 27Tr partial `intro_year: 2015` while it is
  drawn as the 2024 Urbino IV batch; Rošero First `intro_year: 2018` against the 2021
  delivery.
- [ ] The Urbino 12 III and 18 III CNG batches have no object of their own; they share
  the diesel art. `dpo_solaris.py` already draws the blue CNG fairing.


## Re-check against new photos

- [ ] DPMHK **32Tr** (12 m): no side photo existed, so its yellow stripe ahead of
  the rear axle is inferred from the 33Tr. Check once the cars run (from
  October 2026).
- [ ] Arriva **845**: the window band differs between units (945.107 / 945.205
  dark, 845.301 / 845.317 blue pillars); the drawing uses blue pillars.
- [ ] GW Train Regio: further IDESKA repaints of the Šumava RS1s, and whether
  841 278 gets a livery (TRD silver now).
- [ ] The ČD 848 (Lubak91's ZSSK 840 art) looks unlike the Arriva 848 render.

## Build limitations

- [ ] No `bidirectional=1` support in this Simutrans build: single-ended
  modelling of bidirectional trams (Most EVO2) and push-pull trains.

## Left out on purpose

Not open work; listed so nobody adds them by accident.

- Advertising and promo wraps on any vehicle, except the standing Fashion Arena
  livery of Prague line 238.
- ČD diesel units: delivery-state schemes of second-hand RS1s (NEB, BWEGT, OSB,
  BSB), the retro 854.021 / 1969 854.225 museum schemes, and ČD 812 (sold to AŽD
  in 2026).
- ČD electric units: the 1997–2006 471 "ledovec" scheme (left service 2024), kraj
  decals on the Najbrt 2 640.2 / 650.2, and the withdrawn 451/452, 460/560 and 470.
- Arriva: the Škoda 26Ev (from December 2028) and the Plzeň BEMU (from 2030,
  no design published).
- Narrow-gauge trains (Gepard Express at Jindřichův Hradec, Osoblaha): pak128.cs
  has no narrow-gauge track.
