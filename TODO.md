# Sprite TODO list

Placeholder sprites have been copied from the closest-color upstream source for every
new DMU livery. Each item below names the placeholder you'll see in-game today, the
livery it has to become, and any real-world caveats. All work here is manual pixel art —
no programmatic recoloring has been run.

Convention:
- placeholder: file currently shipped under `vehicle-rail/.../sprites/<color>.png`
- target: the livery the file needs to represent
- direct match = sprite already correct, no repaint needed

Legend for livery palettes:
- **Najbrt 1**: grey roof, sky-blue window band, thin sapphire stripe under the windows, light-grey lower body, sapphire doors (ČD 2008–2011; no red anywhere)
- **Najbrt 2**: Najbrt 1 with sapphire roof, cab visor and underframe plus a thin light stripe under the roof edge; doors stay sapphire (ČD 2011+)
- **červeno-krémová**: red lower half, cream upper half, narrow grey roof (1960s-90s ČSD/ČD legacy). On the 810/010 it is the ČD 1998 variant instead: red window band and doors, cream band below the windows running across the fronts, light-grey roof
- **Pardubický kraj**: white body + red waistband + yellow/gold detail. On the 810 (2019): light-grey body, dark-blue roof, red strip under the roof edge and red windscreen surround, dark-blue sill stripe, yellow doors
- **Plzeňský kraj**: red ends, white middle, blue stripe
- **Kraj Vysočina**: white body + green waistband
- **PID červeno-modro-bílá**: the old PID scheme, in horizontal zones: blue roof and window band, white lower body, red doors and bottom edge (810 263 / 289). Not the newer vertical grey-red PID style (`pidsedocervena`)
- **PID šedo-červená**: silver/grey body + vertical red door bands (the newer PID style used on ČD DMUs/EMUs)
- **DÚK zeleno-bílá**: white body + green waistband, "Doprava Ústeckého kraje"
- **HZL krémovo-červená**: cream body + red waistband (Hradecké železniční lokálky)

---

## 642 Siemens Desiro Classic

- [x] `642/sprites/dukzelenobila.png` — placeholder is DB-red Desiro from pak128cs. Recolor to **DÚK zeleno-bílá** (white body, green DÚK band, green ends).

## 809 "Šukafon"

- [x] `809/sprites/{najbrt1,najbrt2,cervenokremova}.png` — every livery real 809s wore; same body and art as the 810 railcar.

## 810 "Šukafon" + 010 trailer

Both repainted zone by zone from photos (research notes: 810 245, 810 290, 810 578,
809 179, 810 263, Btax 229 …). Row 0 = 810 railcar, row 1 = 010 (Btax 780) trailer,
which only exists in the liveries real 010s wore (Najbrt 1, Najbrt 2, red-cream).

- [x] `810/sprites/najbrt1.png` — **Najbrt 1**.
- [x] `810/sprites/najbrt2.png` — **Najbrt 2**.
- [x] `810/sprites/cervenokremova.png` — ČD 1998 **red-cream** (red window band, cream band below the windows; the old placeholder was the 1970s ČSD scheme with cream round the windows).
- [x] `810/sprites/pardubickykraj.png` — the real 2019 **Pardubický kraj** 810 scheme (810 only).
- [x] `810/sprites/pidcervenomodrobila.png` — old horizontal **PID** scheme (810 263 / 289; 810 only).

## 811 RegioMouse

- [ ] `811/sprites/najbrt2.png` — placeholder is red ČD 811 cab. Recolor to **Najbrt 2**.

## 840 RegioSpider

- [x] `840/sprites/najbrt1.png` — placeholder is ZSSK silver/blue RS1. Repaint to **Najbrt 1** (navy + white). Also: the source's middle "zssk_840_b" engine pod is dropped — our model is a single car, so the cab silhouette should be the only thing visible.

## 841 RegioSpider

- [x] `841/sprites/najbrt1.png` — same source/work as 840.

## 841.2 RegioSpider

- [x] `841_2/sprites/dukzelenobila.png` — ZSSK silver source → **DÚK zeleno-bílá** (white body, green waistband).
- [x] `841_2/sprites/hzlkremovacervena.png` — ZSSK silver source → **HZL krémovo-červená** (cream + red).
- [x] `841_2/sprites/pardubickykraj.png` — ZSSK silver source → **Pardubický kraj** (white+red+gold).
- [x] `841_2/sprites/pidsedocervena.png` — ZSSK silver source → **PID šedo-červená** (grey body + red door pillars).

## 842 "Kvatro"

- [ ] `842/sprites/najbrt1.png` — placeholder is red ČD 842. Recolor to **Najbrt 1**.
- [ ] `842/sprites/najbrt2.png` — placeholder is red ČD 842. Recolor to **Najbrt 2**.

## 843 "Rakev"

- [ ] `843/sprites/najbrt1.png` — placeholder is red ČD 843. Recolor to **Najbrt 1**.
- [ ] `843/sprites/najbrt2.png` — placeholder is red ČD 843. Recolor to **Najbrt 2**.
- [ ] `843/sprites/cervenokremova.png` — placeholder is red ČD 843. Almost correct; ensure upper half reads as cream rather than light grey if the upstream is the wrong shade.

## 844 RegioShark

- [x] `844/sprites/najbrt1.png` — pak128_czr 844 blue is already Najbrt 1. **Direct match, no recolor needed.** Spot-check that the red door accents read correctly at 128 px.
- [ ] `844/sprites/pardubickykraj.png` — ČD blue source → **Pardubický kraj** (white+red+gold). Both halves of the consist need repainting.

## 847 RegioFox

- [ ] `847/sprites/najbrt2.png` — placeholder is ČD blue 847 (Najbrt 1 look). Touch up door frames and waistband to **Najbrt 2** (Najbrt 1 → 2 is mostly a door-color change).
- [x] `847/sprites/pidsedocervena.png` — pak128_czr 847_PID livery — **direct match**.
- [x] `847/sprites/plzenskykraj.png` — pak128_czr 847_Plzen livery — **direct match**.
- [ ] `847/sprites/pardubickykraj.png` — Plzeňský kraj source as closest red/white → repaint waistband to gold to land **Pardubický kraj**.

## 854 "Hydra"

The 854 is a rebuild of class 851, so the pak128cs **851** sprites are the same body
silhouette — no reshaping needed, just paint.

- [x] `854/sprites/cervenokremova.png` — pak128cs 851_CSD (ČSD cream+red) is already the
  red-cream livery on the correct body. **Effectively a direct match.** Only fine-detail
  touch-ups (e.g. ČD logo, modernized front headlights vs the classic ČSD look) if you
  want it to read as the post-1996 rebuild rather than the 1960s original.
- [ ] `854/sprites/najbrt2.png` — placeholder is ČD red 851. Recolor to **Najbrt 2** (navy + bright red doors).

---

## 814 RegioNova / RegioNova Trio (existing families)

The existing 814.0 and 814.2 sprites are hand-drawn upstream and ship as-is. Each
livery's source has been annotated in the corresponding `family.yaml` so the link
to the original art is recorded. Nothing else to do here unless a livery needs a
refresh.

---

# EMUs

## 471 CityElefant

3-car formation (471 motor + 071 trailer + 971 cab trailer). All four placeholders
use the same source: pak128cs `cd_471a.png` (3 rows already laid out front motor
→ middle → rear cab).

- [x] `471/sprites/cityelefantcervena.png` — pak128cs CityElefant red/white/blue —
  **direct match.** Optional: bring small details (logo, current ČD typography) in line
  with the 2020s look.
- [ ] `471/sprites/pidsedocervena.png` — CityElefant red source → **PID šedo-červená**
  (silver body + red doors + grey roof).
- [ ] `471/sprites/najbrt1.png` — CityElefant red source → **Najbrt 1** (navy + white
  waistband, red door frames).
- [ ] `471/sprites/najbrt2.png` — CityElefant red source → **Najbrt 2** (navy + bright
  red doors).

## 660.0 InterPanter (3-car)

- [ ] `660_0/sprites/najbrt2.png` — pak128_czr 640.png (RegioPanter Najbrt 2 livery).
  Body shells of InterPanter and RegioPanter are visually similar. **Close match for
  the livery**, but the InterPanter front mask differs slightly from the suburban
  RegioPanter (different headlight cluster, longer nose) — touch up the cab profile.

## 660.1 InterPanter (5-car)

- [ ] `660_1/sprites/najbrt2.png` — same caveat as 660.0. The middle three vehicles
  (662.1, 064.1, 662.2) all reuse the middle motor row of `640.png` as placeholder; the
  middle trailer (064.1) should ideally be redrawn without pantographs.

## 681 Pendolino

- [x] `681/sprites/cdpendolino.png` — pak128cs `cd_680_pendolino.png` (ČD Pendolino
  livery, all 7 cars laid out). **Direct match.** Upstream is filed under class 680;
  ČD reclassified the set to 681 in 2008 — only the model badge differs.

## 650 RegioPanter (2-car)

- [ ] `650/sprites/najbrt1_2.png` — pak128_czr `650_P2.png` (Najbrt 2 base) → repaint
  waistband to **Najbrt 1.2** (transitional dark-blue + slimmer yellow band).
- [x] `650/sprites/najbrt2.png` — pak128_czr `650_P2.png` is already **Najbrt 2**. Direct match.

## 640 RegioPanter (3-car)

- [ ] `640/sprites/najbrt1_2.png` — pak128_czr `640.png` Najbrt 2 base → repaint to **Najbrt 1.2**.
- [x] `640/sprites/najbrt2.png` — pak128_czr `640.png` is already **Najbrt 2**. Direct match.

## 440 RegioPanter (3-car)

- [ ] `440/sprites/najbrt1_2.png` — pak128cs `cd_440_panther.png` (early Panter blue
  livery) → adjust to **Najbrt 1.2** if it doesn't read close enough.
- [ ] `440/sprites/najbrt2.png` — pak128cs `cd_440_panther.png` → tweak door colors for
  **Najbrt 2** (early Panter livery is similar to Najbrt 1; bright red doors needed).

## 640.1 RegioPanter (3-car)

- [ ] `640_1/sprites/najbrt1_2.png` — pak128_czr `640.png` → repaint waistband to
  **Najbrt 1.2**.
- [x] `640_1/sprites/najbrt2.png` — pak128_czr `640.png` is already **Najbrt 2**. Direct match.

## 640.2 RegioPanter (3-car)

- [x] `640_2/sprites/pidsedocervena.png` — pak128_czr `640_PID.png` is already the **PID
  šedo-červená** livery. Direct match.
- [x] `640_2/sprites/najbrt2.png` — pak128_czr `640.png` is already **Najbrt 2**. Direct match.

## 690.2 RegioPanter (2-car, battery)

- [x] `690_2/sprites/cdzelenomodrobila.png` — pak128_czr `690.png` is already the
  battery-electric **ČD zeleno-modro-bílá** livery. Direct match.

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
