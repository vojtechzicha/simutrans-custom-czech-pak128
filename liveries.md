# ČD livery — color reference

Background color and zone-by-zone RAL/RGB/hex values for the liveries shipped by this addon set. RAL → RGB conversions from [rgb.to/ral](https://rgb.to/ral); Najbrt details from [Wikipedia (cs)](https://cs.wikipedia.org/wiki/Najbrt_(korpor%C3%A1tn%C3%AD_styl_%C4%8CD)) and standard **TNŽ 280070**.

Simutrans pak128 transparent background is `RGB(231, 255, 255)` (see CLAUDE.md) — keep it distinct from any body grey.

---

## Najbrt 2 (`najbrt2`) — 2011+ corporate

Post-2011 inverted scheme: dark-blue roof + frame, light-grey body, light-blue window band.

| Zone                            | RAL    | Name              | RGB (decimal)    | Hex     |
| ------------------------------- | ------ | ----------------- | ---------------- | ------- |
| Roof                            | 5003   | Saphirblau        | `31, 56, 85`     | #1F3855 |
| Stripe / doors / frame          | 5003   | Saphirblau        | `31, 56, 85`     | #1F3855 |
| Window band — general / 2nd cl. | 5015   | Himmelblau        | `0, 124, 176`    | #007CB0 |
| Window band — 1st class         | 1003   | Signalgelb        | `249, 168, 0`    | #F9A800 |
| Window band — 2nd class (alt.)  | 7035   | Lichtgrau         | `203, 208, 204`  | #CBD0CC |
| Body / lower                    | 7035   | Lichtgrau         | `203, 208, 204`  | #CBD0CC |

The "white" body is RAL 7035 light grey, not pure white.

---

## Najbrt 1 (`najbrt1`) — 2008–2011 original corporate

First-generation scheme. Light body with grey roof and dark-blue lower stripe; window band is the same blue used in Najbrt 2.

| Zone                            | RAL    | Name              | RGB (decimal)    | Hex     |
| ------------------------------- | ------ | ----------------- | ---------------- | ------- |
| Roof                            | 7022   | Umbragrau         | `76, 74, 68`     | #4C4A44 |
| Body / upper                    | 7035   | Lichtgrau         | `203, 208, 204`  | #CBD0CC |
| Window band — general / 2nd cl. | 5015   | Himmelblau        | `0, 124, 176`    | #007CB0 |
| Window band — 1st class         | 1003   | Signalgelb        | `249, 168, 0`    | #F9A800 |
| Lower stripe / doors / frame    | 5003   | Saphirblau        | `31, 56, 85`     | #1F3855 |

Differences vs. Najbrt 2:
- Roof: warm grey (7022) instead of dark blue.
- Dark blue (5003) sits at the bottom as a stripe, not on roof/frame.
- The cab front carried trapezoidal blue accents; Najbrt 2 dropped these in favor of a continuous side band.

---

## RegioNova žlutozelená (`zlutozelena`) — original 814/914 livery

Original livery of the 814 RegioNova DMU, designed by **Konting** at the time of the 2005 rebuild. The official paint specification is not publicly documented — values below are best-match standard RAL shades by visual reference. Adjust freely against reference photos.

| Zone                       | RAL    | Name              | RGB (decimal)    | Hex     |
| -------------------------- | ------ | ----------------- | ---------------- | ------- |
| Body — green               | 6018   | Gelbgrün (žlutozelená) | `97, 153, 59` | #61993B |
| Front warning panel — yellow | 1023 | Verkehrsgelb (dopravní) | `247, 181, 0` | #F7B500 |
| Roof                       | 7022   | Umbragrau         | `76, 74, 68`     | #4C4A44 |
| Window frames / skirt grey | 7035   | Lichtgrau         | `203, 208, 204`  | #CBD0CC |
| Doors / underframe (black) | 9005   | Tiefschwarz       | `10, 10, 10`     | #0A0A0A |

Notes:
- RAL 6018 is the Czech standard "žlutozelená" and is the closest match to the 814 body color in photos.
- The front yellow on Czech rolling stock is typically RAL 1023 (traffic yellow); some sources for related ČD vehicles use RAL 1003 (signal yellow) instead — they're close.
- Reference photos: [vagonweb 814+914 gallery](https://www.vagonweb.cz/fotogalerie/CZ/CD_814,914.php), [atlaslokomotiv 814](https://www.atlaslokomotiv.net/loko-814.html).

---

## Regional liveries — one name, several designs

A regional livery is the kraj's design for one vehicle type, so the same slug can
look different on different classes. The zones below come from photo research
(September 2026); the shipped values are in each family's painter notes.

## Plzeňský kraj (`plzenskykraj`)

IDPK design: **royal-blue body** with **yellow doors**, the kraj's three-arc logo
(yellow / green / white) and thin green / yellow / white swooshes on the lower
side, and a dark anthracite skirt.

- **814 + 914** (6 units, Český les, since 2023): blue roof and body, a white
  cantrail band and white window frames, white cab hood / windscreen surround,
  dark-blue headlight mask, blue lower front, yellow bottom strip.
- **844** (7 units, 2026) and **847** (10 units): white roof and cab hood (847:
  bare-aluminium roof equipment), blue sides with the arc motif and swooshes,
  blue lower front, grey skirt.
- **650.2 RegioPanter** (13 units, Plzeň, since 2021): the design chosen by a
  public poll in 2017, the same one Arriva's ex-ČD 650s carry on line P1. White
  cant rail and cab hood, dark-blue roof boxes, royal-blue body, yellow doors,
  long green / white / yellow swooshes, a yellow bar over the 1st class, mid-blue
  front panel with the kraj emblem, dark-grey skirt, yellow anti-climber.

| Zone          | RGB (approx.)     | Hex     |
| ------------- | ----------------- | ------- |
| Royal blue    | `21–31, 78–86, 158–168` | #1F4E9E |
| Door yellow   | `242, 194, 0`     | #F2C200 |
| Swoosh green  | `18–68, 160–165, 71–122` | #44A547 |
| Skirt         | `58–95, 63–97, 66–99` | #3A3F42 |

---

## Pardubický kraj (`pardubickykraj`)

"modro-bílá s červeným proužkem a žlutými dveřmi" — **white body, navy (dark
blue) roof and bottom band, a thin red strip along the roof edge, yellow doors**,
the kraj emblem and lettering in navy.

- **814 + 914** (from 2018): the red strip continues down the cab as a red frame
  round the windscreen and headlight mask; light-grey mask, navy lower front,
  yellow bottom strip.
- **841.2** RS1 (11 cars, 2023–24), **844** (2 units) and **847** (7 units): navy
  roof (white A/C boxes on the RS1), red cantrail line, white body, yellow doors
  (in navy frames on the RS1), navy bottom line and lower front.
- **810** (2019) is a different application, see below.

| Zone          | RGB (approx.)     | Hex     |
| ------------- | ----------------- | ------- |
| Navy          | `24–38, 51–58, 95–128` | #26365F |
| Red           | `216–228, 47–64, 40–46` | #D8342E |
| White         | `236, 238, 239`   | #ECEEEF |
| Door yellow   | `230–246, 190–210, 0–30` | #F2CF1A |

### Pardubický kraj on the 810 (2019)

Eight 810s modernised by DPOV in 2019 (810 245, 810 094, …) got a different application: **light-grey body top to bottom** (no sky-blue band), **dark-blue roof, cab visor and underframe**, a **red strip under the roof edge**, a **red windscreen surround**, a dark-blue stripe under the windows and **yellow doors**. Shipped: grey `210, 215, 218`, blue `30, 56, 104`, red `222, 36, 42`, yellow `246, 192, 0`. No 010 trailer wore it, so the set has no 010 in it.

---

## Kraj Vysočina (`vysocina`)

Only on the RegioNova, and only on three single cars (814 041, 814 048, 914 018),
each coupled to a Pardubický kraj partner — a pure Vysočina set in the game is an
idealisation. The layout is the Pardubický kraj RegioNova one (white body,
dark-blue roof, bottom band and lower front, yellow bottom strip) with the
roof-edge strip, the windscreen frame and the **doors in light green**
(≈ RAL 6018, `109, 190, 69` #6DBE45), the VDV arrow emblem and a large
"RegioNova" wordmark.

---

## PID šedo-červená (`pidsedocervena`)

The PID unified visual style as applied to ČD trains. The rolling-stock application is a simplified two-color version of the broader PID manual: **light-grey body with red vertical door bands** plus a thin red strip running along the top edge of the bodyside. The blue (RAL 5005) and white (RAL 9010) zones from the full PID design manual are used on buses and trams — trains get only grey + red. Validated against [unit 814 139-2 (bmhd.cz)](https://static.bmhd.cz/data-mhdfoto/f/2025/07/07/686bfe1f34a1d__P1290884.JPG).

| Zone                       | RAL    | Name              | RGB (decimal)    | Hex     |
| -------------------------- | ------ | ----------------- | ---------------- | ------- |
| Body                       | 7035   | Lichtgrau         | `203, 208, 204`  | #CBD0CC |
| Door pillars (vertical) + top-edge strip | 3020 | Verkehrsrot | `204, 6, 5` | #CC0605 |
| Roof                       | 7016   | Anthrazitgrau     | `41, 49, 51`     | #293133 |
| Under-frame (black)        | 9005   | Tiefschwarz       | `10, 10, 10`     | #0A0A0A |

Where the red goes depends on the class: on the 847 one red stripe beside each door (and one right of centre on the fronts), on the RS1 (841.2 / 841.3) a red block over the short end section behind each cab, on the RegioNova red bands at the doors. On the RegioPanter 640.2 (ROPID 2025 rules: RAL 7038 grey, RAL 3020 red, RAL 9005 black window band and doors, RAL 7022 roof gear) one red block stands on the car-end side of each door, from the cant down to the skirt with the black window band crossing it, and the front is grey on the left and red on the right of centre with the white ČD logo. On the 471 CityElefant the inner half of every single-deck end section is red over its full height, the upper and lower decks sit in continuous black window bands, and the cab front has a black mask with one vertical red band right of centre.

The signature element is the **full-height red vertical band at every door position** — wraps from below the windows down to the skirt, doors included. The folder/livery name `pidsedocervena` ("grey-red") is accurate for the train application.

Reference: [pid.cz — Veřejná doprava v Praze bude mít novou podobu](https://pid.cz/verejna-doprava-praze-bude-mit-novou-podobu/) (full design manual; trains use the simplified grey+red subset).

---

## DÚK zeleno-bílá (`dukzelenobila`)

DÚK ("Doprava Ústeckého kraje") regional design: **bright green body** with
**light-grey / near-white** panels.

- **642** Desiro Classic (6 ČD units at Děčín since 2024): green body and window
  band, light-grey roof, a diagonal white swoosh down each cab side, a white
  floor-level stripe, white door leaves, green cab dome and front number strip,
  dark-grey skirts.
- **841.2** RS1 (13 cars since 2023): the HzL layout idea in DÚK colours —
  yellow-green body, **light-grey slanted parallelogram panels round each door**,
  a light-grey bottom band and roof, light-grey front mask with green corners.

| Zone              | RGB (shipped)                    | Hex     |
| ----------------- | -------------------------------- | ------- |
| Green (642 / RS1) | `58, 166, 74` / `92, 178, 74`    | #3AA64A |
| Light grey        | `220–228, 224–231, 226–232`      | #DCE0E2 |

---

## HzL krémovo-červená (`hzlkremovacervena`) — 841.2, historical

The Hohenzollerische Landesbahn scheme the 22 ex-HzL RS1s ran in with ČD logos
from 2021 until their repaint (last cars mid-2024): **cream body**, **raspberry-red
slanted panels round each door** and red doors, a **red bottom band**, red lower
front. Cream `232, 224, 196`, red `184, 36, 60`.

---

## Liberecký kraj (`libereckykraj`) — 840, from 2026

IDOL red-white: **white body**, **red doors**, a **red bottom band sweeping up into
red cab fronts** (red below the windscreen, thin red windscreen frame), thin red
"route-map" lines and red ring pictograms. Eight wrap variants exist; the sprite
shows the common base. Red `200, 32, 30` (≈ RAL 3020).

---

## Světle šedá (`svetlesheda`) — 841.2

Plain light grey (`210, 214, 217`) on 841.225–227 since 2025, roof included; dark
lower front, yellow skirt edge, dark ČD lettering.

---

## Červeno-žlutá (`cervenozluta`) — 809 281

ČSD "unifik 88": the 810-family red-cream layout with a **golden-yellow band**
(`235, 185, 50`) instead of cream, **crossing the doors**, on red `160, 32, 44`.
Only 809 281 (repainted 2006) still runs in it.

---

## Najbrt on the Panter family (RegioPanter 440 / 640 / 650, InterPanter 660)

On the Škoda Panter body Najbrt 2 is a **sky-blue body** (RAL 5015) between a
**near-white cant rail** and a **sapphire waist line**, then a light-grey stripe
and a **sapphire valance**; **sapphire doors**, a light-grey roof with **sapphire
roof boxes**, a light-grey GRP cab hood slanting back past the cab-side window, a
sapphire visor over the black windscreen, a sky-blue front panel with the white
ČD logo, sapphire skirt and a yellow anti-climber. A yellow stripe under the cant
marks the 1st class. The InterPanter wears the same scheme with one door per side.

## Najbrt 1.2 (`najbrt1_2`) — Panter as delivered, 2011–13

The first RegioPanters (640.001–003, 650.001–004 and ten of the twelve 440 /
640.1) still carry the transitional scheme they were delivered in. It is Najbrt 2
with five differences: **dark-grey roof boxes** (RAL 7022), a **dark-grey cap**
above the windscreen, a **sapphire diagonal wedge** under the cab-side window, and
a **wide light-grey lower band without the sapphire valance**; the lower front
corners are dark grey on some photos and sapphire on others.

## Najbrt on the 471 CityElefant

The double-decker splits the corporate colours by deck. **Najbrt 1** (028–030,
061–075): light-grey roof and upper deck (no dark band), a sky-blue band from under
the upper windows down to the lower deck, a thin sapphire stripe, light-grey lower
deck, **dark-grey skirt**, sapphire doors, a sapphire block round the cab door and
a sky-blue cab mask. **Najbrt 2** (076–083): **sapphire roof and upper-deck zone**,
a thin light line that also crosses the front above the windscreen, the sky-blue
band (now including the cab-side window), sapphire stripe, light-grey lower deck,
**sapphire skirt** and doors.

## CityElefant bílo-modro-červená (`cityelefantcervena`) — 471, 2006 scheme

The scheme the 471 got with the CityElefant name in 2006 (units 031–060 and the
older units repainted at overhaul; all seven CityElefant-liveried Bohumín units
still wear it). Silver-white body and roof; on the double-deck middle, from the top:
**light-blue** band with the upper windows, thin white line, **red** band between
the decks, white line, light-blue band with the lower windows, white line and a
**dark blue-grey skirt**. **Red doors**. Behind each cab the stack starts in a
curved swoosh ending in a red crescent, with the white "CityElefant" wordmark; the
cab front has a dark-grey mask round the windscreen. The original 1997–2006
"ledovec" (white with a royal-blue band, left service 2024) is not modelled.

| Zone        | RGB (shipped)      | Hex     |
| ----------- | ------------------ | ------- |
| Light blue  | `90, 143, 196`     | #5A8FC4 |
| Red         | `210, 71, 47`      | #D2472F |
| Silver      | `213, 215, 212`    | #D5D7D4 |
| Skirt       | `78, 90, 100`      | #4E5A64 |
| Cab mask    | `86, 91, 97`       | #565B61 |

## Stříbrno-tyrkysová (`cdpendolino`) — 680 Pendolino

Patrik Kotas's design, the only livery the 680 has ever worn (renewed in film at
the 2017–18 modernisation). **Silver-grey body**, an **anthracite window band**
edged below by a **thin yellow line** that turns up at the band ends, a
**turquoise cant-rail stripe**, a **turquoise lower band and skirt**, grey roof with
dark pantograph wells. The cab cars have an anthracite "helmet" (cab roof and
windscreen surround) and a broad yellow band sweeping forward across the nose with
the headlights, silver below it and a turquoise lower nose.

| Zone        | RGB (shipped)      | Hex     |
| ----------- | ------------------ | ------- |
| Silver      | `208, 212, 218`    | #D0D4DA |
| Turquoise   | `34, 166, 190`     | #22A6BE |
| Yellow      | `240, 194, 30`     | #F0C21E |
| Anthracite  | —                  | #3F454D |

## ČD zeleno-modro-bílá (`cdzelenomodrobila`) — 690.2 battery RegioPanter

The four battery units of 2024 (690.247–250, Ostrava – Veřovice). Each car is
**green at its cab end** and **sapphire at its inner end**, joined by a band of
interlocking loops, so a unit reads green – loops – navy | navy – loops – green.
Below that it is Najbrt 2: sapphire line, light-grey stripe, sapphire valance and
doors; light-grey roof with navy battery boxes, white cant rail, a yellow stripe
over the 1st class, and a two-tone green front panel under a sapphire visor.

## Jihomoravský kraj (`jihomoravskykraj`) — Moravia 530 / 550

The Moravia units owned by Jihomoravský kraj (operated by ČD) all wear one JMK
scheme: **magenta** (Pantone 1787 C, #FB5271) roof shoulders running into the cab
corners, and magenta doors; a white / light-grey body with a **black window band**
and a black skirt; over each bogie the black rises to the roof band above a tall
white panel, stepping down in 30° diagonals. The cab face is black with the white
number and the "jmk" logo, the plough edge yellow. No ČD logo and no 1st class.

## Najbrt 2 on the PESA units (844 / 847) and the GTW (848)

Same corporate colours, different split: light cantrail line (yellow over the
1st class), sky-blue window band, sapphire stripe, **light-grey lower band** and a
**sapphire bottom band** rising at the cab ends; sky-blue ČD panel and black
windscreen band on the fronts. The 848 adds a white stripe between the sapphire
roof and the sky band and carries Olomoucký kraj decals.

---

## Červeno-krémová (`cervenokremova`) — ČD 1990s scheme

The same idea on every class: **cherry-red body with one cream band at lamp
level**, running round the cab fronts, doors red. On the 842/843/943/043, 854 and
its 954/054 trailers the band sits just below the windows and is about a quarter
of the side height; the roof is light grey / stainless.

### On the 810 / 010 — ČD 1998 variant

Not the 1970s ČSD scheme with cream round the windows. The **window band, pillars, windscreen surround, doors and lower body are cherry red**; a **cream band about 600 mm high runs just below the windows**, round the whole car and across the cab fronts at lamp level (it stops at the doors). Roof light grey; plough edge yellow. Reference: 810 245 (2008), Btax 780 048.

| Zone            | RGB (shipped)      | Hex     |
| --------------- | ------------------ | ------- |
| Red             | `178, 30, 40`      | #B21E28 |
| Cream band      | `234, 222, 184`    | #EADEB8 |
| Roof            | `168, 168, 163`    | #A8A8A3 |

---

## PID červeno-modro-bílá (`pidcervenomodrobila`) — old PID scheme

The **older** PID design in horizontal zones (not the newer vertical grey-red `pidsedocervena`), carried by 810 263 (2021) and 810 289: **blue roof, visor and window band** (down to just below the sills), **white lower body** with the lamps, **red doors, bottom edge and underframe skirts**, red buffer beam, yellow plough edge. No 010 trailer wore it, so the set has no 010 in it.

| Zone            | RGB (shipped)      | Hex     |
| --------------- | ------------------ | ------- |
| Blue            | `22, 92, 172`      | #165CAC |
| White           | `236, 236, 236`    | #ECECEC |
| Red             | `218, 34, 44`      | #DA222C |
