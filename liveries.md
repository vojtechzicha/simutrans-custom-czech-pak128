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

## Regional liveries on RegioNova — how to read these

The three regional variants below all sit on the **same Najbrt-style base coat** (dark-blue lower trim, light-grey/white upper body, dark roof) and differ only in the *accent colors* — door panels, side stripes, and the kraj graphics. So start from the Najbrt 2 base palette and swap the accent zones for each region.

Validated against photos on [seznam-autobusu.cz — RegioNova Duo, ČD](https://seznam-autobusu.cz/seznam?iddopravce=5943&ntyp=RegioNova&typ=RegioNova+Duo).

Shared base for all three regional liveries:

| Zone                  | RAL    | RGB (decimal)    | Hex     |
| --------------------- | ------ | ---------------- | ------- |
| Upper body            | 9010   | Reinweiß / off-white | `244, 244, 244` | #F4F4F4 |
| Lower trim            | 5003   | Saphirblau (dark blue) | `31, 56, 85` | #1F3855 |
| Roof                  | 7022   | Umbragrau        | `76, 74, 68`     | #4C4A44 |
| Under-frame (black)   | 9005   | Tiefschwarz      | `10, 10, 10`     | #0A0A0A |

(The upper body in the photos reads white, not the RAL 7035 grey used on Najbrt 2 corporate trains — these are visibly whiter.)

---

## Plzeňský kraj (`plzenskykraj`)

"modro-bílá s grafikou Plzeňského kraje" — Najbrt-style white + dark-blue base with **light-blue (RAL 5015) accent band** wrapping the lower window line, and the kraj's three-curve logo graphic on the side. Verified: [unit 914 013-6 (foto-busy)](https://foto-busy.eu-central-1.linodeobjects.com/385235.jpg).

| Zone                   | RAL/PMS    | RGB (decimal)    | Hex     |
| ---------------------- | ---------- | ---------------- | ------- |
| Accent band            | RAL 5015 Himmelblau | `0, 124, 176` | #007CB0 |
| Logo curve — blue      | logo blue  | `0, 114, 188`    | #0072BC |
| Logo curve — green     | logo green | `141, 198, 63`   | #8DC63F |
| Logo curve — yellow    | logo yellow| `255, 214, 0`    | #FFD600 |

The kraj's three-curve colors only appear in the side decal, not as body fields. Reference: [plzensky-kraj.cz/symboly-pk](https://www.plzensky-kraj.cz/symboly-pk).

---

## Pardubický kraj (`pardubickykraj`)

"modro-bílá s červeným pruhem a žlutými dveřmi" — white body, bright **yellow doors**, a **red horizontal stripe** along the window line, and the dark-blue Najbrt trim at the bottom. Verified visually (a class 841 RegioSpider example in the same livery is clear evidence of the same color spec used across kraj rolling stock).

| Zone                  | RAL/PMS     | RGB (decimal)    | Hex     |
| --------------------- | ----------- | ---------------- | ------- |
| Doors                 | RAL 1023 Verkehrsgelb | `247, 181, 0` | #F7B500 |
| Side stripe (red)     | RAL 3020 / PMS 485 C | `237, 41, 57` | #ED2939 |
| Kraj logo — blue field| PMS 293 C   | `0, 61, 165`     | #003DA5 |
| Kraj logo — yellow    | PMS 109 C   | `255, 209, 0`    | #FFD100 |

Reference: [Pardubický kraj — logo manuál (PDF)](https://pardubice.eu/data/files/5c/2ff/175fe0bcb5a6eb94d4cbff2ba381f368b1f/logomanual.pdf), [zdopravy.cz](https://zdopravy.cz/drahy-oblekly-regionovu-do-barev-pardubickeho-kraje-za-200-tisic-korun-13370/).

---

## Kraj Vysočina (`vysocina`)

"modro-bílá se zeleným pruhem a zelenými dveřmi" — white body, **bright green doors**, a green stripe along the window line, dark-blue Najbrt trim below. Verified: [unit 814 041-0 — Pardubice, 16.3.2025 (bmhd.cz)](https://static.bmhd.cz/data-mhdfoto/f/2025/03/24/67e1b240a8e94__thumb_P1190044.JPG).

| Zone                  | RAL/PMS     | RGB (decimal)    | Hex     |
| --------------------- | ----------- | ---------------- | ------- |
| Doors + side stripe   | PMS 368 C / RAL 6018 | `120, 190, 33` | #78BE21 |
| Kraj logotype         | PMS 2748 C  | `0, 24, 113`     | #001871 |

The kraj's green graphic mark is the dominant accent — applied as both door fill and a continuous band; logotype text on the side is dark blue. Reference: [Kraj Vysočina — logomanuál (PDF)](https://ezak.kr-vysocina.cz/document_47757/f2d420d542be55d09e1d4bb5d27d3e9a-logomanual-pdf).

---

## PID šedo-červená (`pidsedocervena`)

The PID unified visual style as applied to ČD trains. The rolling-stock application is a simplified two-color version of the broader PID manual: **light-grey body with red vertical door bands** plus a thin red strip running along the top edge of the bodyside. The blue (RAL 5005) and white (RAL 9010) zones from the full PID design manual are used on buses and trams — trains get only grey + red. Validated against [unit 814 139-2 (bmhd.cz)](https://static.bmhd.cz/data-mhdfoto/f/2025/07/07/686bfe1f34a1d__P1290884.JPG).

| Zone                       | RAL    | Name              | RGB (decimal)    | Hex     |
| -------------------------- | ------ | ----------------- | ---------------- | ------- |
| Body                       | 7035   | Lichtgrau         | `203, 208, 204`  | #CBD0CC |
| Door pillars (vertical) + top-edge strip | 3020 | Verkehrsrot | `204, 6, 5` | #CC0605 |
| Roof                       | 7016   | Anthrazitgrau     | `41, 49, 51`     | #293133 |
| Under-frame (black)        | 9005   | Tiefschwarz       | `10, 10, 10`     | #0A0A0A |

The signature element is the **full-height red vertical band at every door position** — wraps from below the windows down to the skirt, doors included. The folder/livery name `pidsedocervena` ("grey-red") is accurate for the train application.

Reference: [pid.cz — Veřejná doprava v Praze bude mít novou podobu](https://pid.cz/verejna-doprava-praze-bude-mit-novou-podobu/) (full design manual; trains use the simplified grey+red subset).
