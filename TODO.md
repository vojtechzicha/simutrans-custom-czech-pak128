# TODO

Open work only. What ships is listed in [`README.md`](README.md); livery colours
are in [`liveries.md`](liveries.md). Last checked 2026-10-10.

## Art still borrowed or shared

Sheets that show another type's drawing. Other identical sheets in the repo are
deliberate: the same body under another package or operator (DPP / Praha, DPMP /
Kolín NovoCiti), the RegioPanter 440 / 640 / 640.1, 840 / 841, T3G / T3P,
T3R.PV / T3R.EV, the DPO 26Tr / 27Tr partial-trolleybus variants. Their
`family.yaml` comments say so.

- [ ] **DPmML Tatra T3M.3** (`vehicle-tram/dp-most-litvinov/t3m3`): still the
  former Most T3 sheet. The TV14 modernisation's dash and door windows are not
  drawn yet.
- [ ] **DPO Inekon 01 Trio** and **Astra** (`t2001_trio`, `ltm1008_astra`) share
  one sheet. They are sister designs, but the Trio has a rounder nose.
- [ ] **DPO Solaris Urbino 12 Electric** is covered only by the Urbino 12 IV art.

## Missing types and liveries

- [ ] DPO trams: **Vario LFR.S** (16 cars) and **Vario LF2R.S** (2).
- [ ] DPO trolleybus: the **SOR TNB 12** prototype.
- [ ] ČD **841.3** in Liberecký kraj colours, when the cars start in December 2026.
- [ ] ČD **690.0** battery units, when passenger service starts in 2027.
- [ ] Pardubický kraj **IREDO** buses, into the same `VZ-IREDO-bus.pak`.
- [ ] A **PID** package for the regional (non-city) lines around Prague.

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

- [ ] `build.py` has no per-livery dates, so a livery is buildable for the whole
  intro–retire span of its family (e.g. Arriva's DB red).
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
