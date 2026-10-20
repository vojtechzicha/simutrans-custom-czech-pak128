# TODO

Open work only. What ships is listed in [`README.md`](README.md); livery colours
are in [`liveries.md`](liveries.md). Last checked 2026-10-20.

## Art still borrowed or shared

Sheets that show another type's drawing. Other identical sheets in the repo are
deliberate: the same body under another package or operator (DPP / Praha, DPMP /
Kolín NovoCiti), the RegioPanter 440 / 640 / 640.1, 840 / 841, T3G / T3P,
T3R.PV / T3R.EV. Their
`family.yaml` comments say so.


## Missing types and liveries

- [ ] ČD **841.3** in Liberecký kraj colours, when the 9 ex-SWEG cars start on
  13 Dec 2026 (Frýdlant lines): reuse the 840 `libereckykraj` paint.
- [ ] ČD **690.0** battery units (Škoda 15Ev5, 15 units) when passenger service starts
  in early 2027 (S7 Ostrava – Český Těšín – Frýdek-Místek): the 690.2 green-blue-white
  scheme, 3 doors per side, roof battery boxes along both cars.
- [ ] Havířovsko III (kraj contract, Transdev Slezsko): 4 hydrogen SOR NSF 12 + 9
  CNG buses in the red ODIS scheme from 12/2027 on the Havířov – Ostrava lines.
  They go into `VZ-ODIS-bus` once the CNG type is known.
- [ ] ODIS Českotěšínsko II: check the final fleet after 13 Dec 2026 (the tender
  estimated about 38 buses; `VZ-ODIS-bus` has the red SOR ICNG 12,3 / 10,5 and
  Crossway LE LINE 12M NP 2025 already).


## Re-check against new photos

- [ ] DPMHK **32Tr**: no photo of the left side yet (checked 2026-10-20; the right
  side and the 33Tr's both sides match the drawing).
- [ ] GW Train Regio: further IDESKA repaints of the Šumava RS1s, 841 278 (TRD
  silver, at Hranice since April 2026, due for IDESKA), and whether 841 275 has the
  IDESKA decals yet (the drawing of `oranzovozelena` shows them).

## Build limitations

- [ ] No `bidirectional=1` support in this Simutrans build: single-ended
  modelling of bidirectional trams (Most EVO2) and push-pull trains.

## Left out on purpose

Not open work; listed so nobody adds them by accident.

- Advertising and promo wraps on any vehicle, except the standing Fashion Arena
  livery of Prague line 238.
- Pardubický kraj: the subcontract stand-ins in other operators' paint (Wrocław and
  brown SOR CN, Alto Adige and ICOM Crossways). CAR-TOUR's two Setra S 415 LE on
  BusLine KHK line 611109 are the white `bilapk` object, which names CAR-TOUR.
- PID regional: the Vehixel vans (Lutan, Martin Uher) and the trikolóra Rošero First
  (ČSAD Benešov) are registered but were not seen in service in October 2026.
- ČD diesel units: delivery-state schemes of second-hand RS1s (NEB, BWEGT, OSB,
  BSB), the retro 854.021 / 1969 854.225 museum schemes, and ČD 812 (sold to AŽD
  in 2026).
- ČD electric units: the 1997–2006 471 "ledovec" scheme (left service 2024), kraj
  decals on the Najbrt 2 640.2 / 650.2, and the withdrawn 451/452, 460/560 and 470.
- Arriva: the Škoda 26Ev (from December 2028) and the Plzeň BEMU (from 2030,
  no design published).
- Narrow-gauge trains (Gepard Express at Jindřichův Hradec, Osoblaha): pak128.cs
  has no narrow-gauge track.
