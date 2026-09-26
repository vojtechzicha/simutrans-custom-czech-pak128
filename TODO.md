# Sprite TODO list

The ČD diesel and electric units are finished (see below). Entries further down
still ship placeholder sprites copied from the closest-colour upstream source; each
item names the placeholder you'll see in-game today, the livery it has to become,
and any real-world caveats.

Convention:
- placeholder: file currently shipped under `vehicle-rail/.../sprites/<color>.png`
- target: the livery the file needs to represent
- direct match = sprite already correct, no repaint needed

Legend for livery palettes:
- **Najbrt 1**: grey roof, sky-blue window band, thin sapphire stripe under the windows, light-grey lower body, sapphire doors (ČD 2008–2011; no red anywhere)
- **Najbrt 2**: Najbrt 1 with sapphire roof, cab visor and underframe plus a thin light stripe under the roof edge; doors stay sapphire (ČD 2011+)
- **červeno-krémová**: red lower half, cream upper half, narrow grey roof (1960s-90s ČSD/ČD legacy). On the 810/010 it is the ČD 1998 variant instead: red window band and doors, cream band below the windows running across the fronts, light-grey roof
- **Pardubický kraj**: regional scheme with navy / white / red / yellow elements; it differs per class (RS1, 844/847: navy roof, red cantrail line, white body, yellow doors). On the 810 (2019): light-grey body, dark-blue roof, red strip under the roof edge and red windscreen surround, dark-blue sill stripe, yellow doors
- **Plzeňský kraj** (IDPK): royal-blue body with white cantrail / roof (and white cab hood on the PESA units), yellow doors, green/yellow/white swooshes and the arc logo, anthracite skirt
- **Kraj Vysočina**: the Pardubický kraj RegioNova layout (white body, dark-blue roof and bottom band) with light-green roof-edge strip, windscreen frame and doors
- **PID červeno-modro-bílá**: the old PID scheme, in horizontal zones: blue roof and window band, white lower body, red doors and bottom edge (810 263 / 289). Not the newer vertical grey-red PID style (`pidsedocervena`)
- **PID šedo-červená**: silver/grey body + vertical red door bands (the newer PID style used on ČD DMUs/EMUs)
- **DÚK zeleno-bílá**: "Doprava Ústeckého kraje" bright green with light-grey / white panels (slanted door panels on the RS1, a cab swoosh on the Desiro)
- **HzL krémovo-červená**: Hohenzollerische Landesbahn cream + raspberry red, the scheme the ex-HzL RS1s (841.2) ran in until their repaint

---

## ČD diesel units (DMUs) — done

Every ČD diesel class and DMU trailer in service in September 2026 is in the set,
in every livery it runs in (plus a few real older schemes kept from before).
All sheets were repainted on one upstream body per class with the zone painter
(photo-researched colours, shared Najbrt palette, lit glass only when loaded) and
checked in-game on the rail test rings.

- [x] **642** Desiro Classic (6 ex-HLB units at Děčín since 2024): DÚK zeleno-bílá.
- [x] **809**: Najbrt 1, Najbrt 2, červeno-krémová, červeno-žlutá (809 281, ČSD unifik 88).
- [x] **810** + **010** trailer: Najbrt 1, Najbrt 2, červeno-krémová; 810 also Pardubický kraj, old PID.
- [x] **811** (2020 MSK rebuild) + **012** (BDtax 782) trailer: Najbrt 2 + Moravskoslezský kraj.
- [x] **814.0 + 914**, **814.2 + 014**: žluto-zelená, Najbrt 2, PID; 814.0 also Plzeňský kraj, Pardubický kraj, Kraj Vysočina.
- [x] **840**: Najbrt 1, Liberecký kraj (2026). **841**: Najbrt 1.
- [x] **841.2** (ex-German RS1): DÚK, Pardubický kraj, PID (841.224), Najbrt 2 (841.223), světle šedá, HzL (historical).
- [x] **841.3** (ex-German RS1, 2025): PID. (Liberecký kraj 841.3s start Dec 2026 — add then.)
- [x] **842** + **054** (Bdtn 756) + **954** (Bfbrdtn 794 / ABfbrdtn 795): 842 Najbrt 1/2, trailers Najbrt 2 / červeno-krémová.
- [x] **843** + **043** (Btn 753) + **943** (Bftn 791): Najbrt 1, Najbrt 2, červeno-krémová (943 Najbrt only).
- [x] **844** RegioShark (2 powered sections): Najbrt 2, Pardubický kraj, Plzeňský kraj (2026).
- [x] **847** RegioFox (2 powered sections): Najbrt 2, PID, Plzeňský kraj, Pardubický kraj.
- [x] **848** Stadler GTW 2/6 (ex-DB, Olomoucký kraj): Najbrt 2 with Olomoucký kraj decals.
- [x] **854** Hydra (reserve only since May 2026): Najbrt 2, červeno-krémová.

Not modelled on purpose: advertising / promo wraps (842.026 ETCS, 848.016/026,
841.0 town wraps, 814 EU / tourism wraps), delivery-state schemes of second-hand
RS1s (NEB, BWEGT, OSB, BSB), the retro 854.021 / 1969 854.225 museum schemes, and
ČD 812 (sold to AŽD in 2026).

---

## ČD electric units (EMUs) — done

Every ČD-operated EMU class in service in September 2026 is in the set, in every
livery it runs in, repainted with the zone painter on the upstream TommPa9 bodies
(the RegioPanters share one body module, so every Panter scheme sits on the same
silhouette) and checked in-game on catenary test rings. Units of one family
couple into pairs across liveries.

- [x] **471** CityElefant + 071 + 971: CityElefant bílo-modro-červená (2006), PID šedo-červená, Najbrt 1, Najbrt 2.
- [x] **640** / **640.1** (ex-440) RegioPanter: Najbrt 1.2, Najbrt 2. **440** kept as the historical 3 kV class (to 2022).
- [x] **640.2**: Najbrt 2, PID šedo-červená.
- [x] **650**: Najbrt 1.2, Najbrt 2. **650.2**: Najbrt 2, Plzeňský kraj.
- [x] **690.2** battery RegioPanter: ČD zeleno-modro-bílá.
- [x] **660.0** / **660.1** InterPanter: Najbrt 2 (one door per side; 064.1 unpowered).
- [x] **680** Pendolino (was filed as 681): Kotas stříbrno-tyrkysová.
- [x] **530** / **550** Moravia (Jihomoravský kraj, operated by ČD): Jihomoravský kraj.

Not modelled on purpose: the 1997–2006 471 "ledovec" scheme (left service 2024),
advertising wraps (650.233 ODIS, 471 "20 let PID", 680 ad wraps), kraj decals on
the Najbrt 2 640.2 / 650.2, the 690.0 battery units (passenger service from 2027),
and the withdrawn 451/452, 460/560 and 470. RegioJet's, Arriva's and Leo
Express's EMUs live in their own agency paks.

---

# DPO Ostrava (bus / tram / trolleybus)

Most DPO rolling stock was extracted from the upstream `CZ-vehicle-bus.pak` /
`CZ-vehicle-tram.pak` / `CZ-vehicle-trolleybus.pak` via `tools/pak_extract.py`,
so its sprites already carry the correct DPO modro-žlutá and tyrkysová liveries
— no repaint work pending there. Two newer fleet additions ship with placeholder
art borrowed from a visually similar family until proper sprites exist.

## Škoda 39T ForCity Smart (tram)

- [ ] `vehicle-tram/dpo/39t_forcitysmart/sprites/dpotyrkysova.png` — placeholder is
  the Stadler Tango NF2 (2-section) sprite. The 39T is a 7-section, 100% low-floor,
  bidirectional 31 m car (delivered 2021–2024, 38 cars in DPO turquoise) — its
  silhouette is longer, sleeker, and symmetrical end-to-end. Repaint or redraw to
  match the real ForCity Smart Ostrava body.

## Rošero First CNG (bus)

- [ ] `vehicle-bus/dpo/roserofirst/sprites/dpotyrkysova.png` — placeholder is the
  Iveco-Dekstra LE 37 sprite. The Rošero First is also an ~8 m Iveco-Daily-based
  CNG midibus so the body proportions are close, but the front and roof gas-tank
  silhouette differ. Touch up to match the Rošero First profile.
