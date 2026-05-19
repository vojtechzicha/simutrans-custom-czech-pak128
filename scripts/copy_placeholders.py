"""One-shot helper that copies inspiration sprites into the family sprites/ folders
as placeholders. No recoloring — purely picks the closest-color source per livery.

Trims the upstream 9th column of stacked extras, keeping only the 8 standard direction
tiles (1024 px wide). Multi-row outputs concatenate rows in the order requested.

Run once from the repo root:
    python scripts/copy_placeholders.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAK128CS = ROOT / "inspiration" / "pak128cs" / "simutrans-code-r2081-pak128.CS" / "vehicles" / "rail-psg mail"
PAK128_CZR = ROOT / "inspiration" / "pak128_czr" / "vehicles-rail-dmu"
PAK128_CZR_EMU = ROOT / "inspiration" / "pak128_czr" / "vehicles-rail-emu"

TILE = 128
TRANSPARENT_BG = (231, 255, 255, 255)


def extract_rows(source: Path, rows: list[int]) -> Image.Image:
    """Crop columns 0-7 from each requested source row and stack them vertically."""
    src = Image.open(source).convert("RGBA")
    h_src = src.height
    out = Image.new("RGBA", (8 * TILE, len(rows) * TILE), TRANSPARENT_BG)
    for out_row, src_row in enumerate(rows):
        y0 = src_row * TILE
        if y0 + TILE > h_src:
            raise ValueError(f"{source.name}: row {src_row} out of bounds (height={h_src})")
        for col in range(8):
            x0 = col * TILE
            tile = src.crop((x0, y0, x0 + TILE, y0 + TILE))
            out.paste(tile, (col * TILE, out_row * TILE), tile)
    return out


def write(target: Path, image: Image.Image) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)
    print(f"  wrote {target.relative_to(ROOT)}")


# (source_png, source_rows, dest_path)
JOBS: list[tuple[Path, list[int], Path]] = [
    # 642 Desiro: db_desiro.png rows 0 (642a) + 1 (642b)
    (PAK128CS / "db_desiro.png", [0, 1], ROOT / "vehicle-rail/ceske-drahy/642/sprites/dukzelenobila.png"),

    # 809 Šukafon: 809.png row 0 (freight = with passengers)
    (PAK128CS / "810/809.png", [0], ROOT / "vehicle-rail/ceske-drahy/809/sprites/najbrt1.png"),
    (PAK128CS / "810/809.png", [0], ROOT / "vehicle-rail/ceske-drahy/809/sprites/najbrt2.png"),

    # 810 Šukafon: closest-color sources per livery
    (PAK128CS / "810/810_modry.png", [0], ROOT / "vehicle-rail/ceske-drahy/810/sprites/najbrt1.png"),
    (PAK128CS / "810/810_modry.png", [0], ROOT / "vehicle-rail/ceske-drahy/810/sprites/najbrt2.png"),
    (PAK128CS / "810/810_CSD.png", [0], ROOT / "vehicle-rail/ceske-drahy/810/sprites/cervenokremova.png"),
    (PAK128CS / "810/810.png", [0], ROOT / "vehicle-rail/ceske-drahy/810/sprites/pardubickykraj.png"),
    (PAK128CS / "810/810.png", [0], ROOT / "vehicle-rail/ceske-drahy/810/sprites/pidcervenomodrobila.png"),

    # 811 RegioMouse
    (PAK128CS / "810/811_predni.png", [0], ROOT / "vehicle-rail/ceske-drahy/811/sprites/najbrt2.png"),

    # 840/841/841.2 RegioSpider — ZSSK silver/blue source as placeholder
    (PAK128CS / "840_841/zssk_840_a_freight.png", [0], ROOT / "vehicle-rail/ceske-drahy/840/sprites/najbrt1.png"),
    (PAK128CS / "840_841/zssk_840_a_freight.png", [0], ROOT / "vehicle-rail/ceske-drahy/841/sprites/najbrt1.png"),
    (PAK128CS / "840_841/zssk_840_a_freight.png", [0], ROOT / "vehicle-rail/ceske-drahy/841_2/sprites/dukzelenobila.png"),
    (PAK128CS / "840_841/zssk_840_a_freight.png", [0], ROOT / "vehicle-rail/ceske-drahy/841_2/sprites/hzlkremovacervena.png"),
    (PAK128CS / "840_841/zssk_840_a_freight.png", [0], ROOT / "vehicle-rail/ceske-drahy/841_2/sprites/pardubickykraj.png"),

    # 842 Kvatro: 842.png row 0 (freight motor)
    (PAK128CS / "842_843/842.png", [0], ROOT / "vehicle-rail/ceske-drahy/842/sprites/najbrt1.png"),
    (PAK128CS / "842_843/842.png", [0], ROOT / "vehicle-rail/ceske-drahy/842/sprites/najbrt2.png"),

    # 843 Rakev: 843.png row 0 (freight motor)
    (PAK128CS / "842_843/843.png", [0], ROOT / "vehicle-rail/ceske-drahy/843/sprites/najbrt1.png"),
    (PAK128CS / "842_843/843.png", [0], ROOT / "vehicle-rail/ceske-drahy/843/sprites/najbrt2.png"),
    (PAK128CS / "842_843/843.png", [0], ROOT / "vehicle-rail/ceske-drahy/843/sprites/cervenokremova.png"),

    # 844 RegioShark — pak128_czr blue is a direct ČD najbrt1 match
    (PAK128_CZR / "CD/844.png", [1, 0], ROOT / "vehicle-rail/ceske-drahy/844/sprites/najbrt1.png"),
    (PAK128_CZR / "CD/844.png", [1, 0], ROOT / "vehicle-rail/ceske-drahy/844/sprites/pardubickykraj.png"),

    # 847 RegioFox — PID and Plzeň are direct livery matches
    (PAK128_CZR / "CD/847.png", [1, 0], ROOT / "vehicle-rail/ceske-drahy/847/sprites/najbrt2.png"),
    (PAK128_CZR / "CD/847_PID.png", [1, 0], ROOT / "vehicle-rail/ceske-drahy/847/sprites/pidsedocervena.png"),
    (PAK128_CZR / "CD/847_Plzen.png", [1, 0], ROOT / "vehicle-rail/ceske-drahy/847/sprites/plzenskykraj.png"),
    (PAK128_CZR / "CD/847_Plzen.png", [1, 0], ROOT / "vehicle-rail/ceske-drahy/847/sprites/pardubickykraj.png"),

    # 854 Hydra — 851 is the same body (854 is a 851 rebuild); 851_CSD is a direct color match for červeno-krémová
    (PAK128CS / "850_851/851_CSD.png", [0], ROOT / "vehicle-rail/ceske-drahy/854/sprites/cervenokremova.png"),
    (PAK128CS / "850_851/851.png", [0], ROOT / "vehicle-rail/ceske-drahy/854/sprites/najbrt2.png"),

    # ============ EMUs ============

    # 471 CityElefant — cd_471a.png rows 0/1/2 = 471/071/971; red+white+blue livery
    (PAK128CS / "471_671/cd_471a.png", [0, 1, 2], ROOT / "vehicle-rail/ceske-drahy/471/sprites/cityelefantcervena.png"),
    (PAK128CS / "471_671/cd_471a.png", [0, 1, 2], ROOT / "vehicle-rail/ceske-drahy/471/sprites/pidsedocervena.png"),
    (PAK128CS / "471_671/cd_471a.png", [0, 1, 2], ROOT / "vehicle-rail/ceske-drahy/471/sprites/najbrt1.png"),
    (PAK128CS / "471_671/cd_471a.png", [0, 1, 2], ROOT / "vehicle-rail/ceske-drahy/471/sprites/najbrt2.png"),

    # 660.0 InterPanter (3-car) — pak128_czr 640.png rows 0/2/1 = front cab / middle / rear cab
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/660_0/sprites/najbrt2.png"),

    # 660.1 InterPanter (5-car) — reuse 640.png; middle three cars all use the middle motor row
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 2, 2, 1], ROOT / "vehicle-rail/ceske-drahy/660_1/sprites/najbrt2.png"),

    # 681 Pendolino — cd_680_pendolino.png rows 0-6 = 681/081/683/084/684/082/682
    (PAK128CS / "680/cd_680_pendolino.png", [0, 1, 2, 3, 4, 5, 6], ROOT / "vehicle-rail/ceske-drahy/681/sprites/cdpendolino.png"),

    # 650 RegioPanter (2-car) — 650_P2.png row 0=650, row 1=651
    (PAK128_CZR_EMU / "CD/650_P2.png", [0, 1], ROOT / "vehicle-rail/ceske-drahy/650/sprites/najbrt1_2.png"),
    (PAK128_CZR_EMU / "CD/650_P2.png", [0, 1], ROOT / "vehicle-rail/ceske-drahy/650/sprites/najbrt2.png"),

    # 640 RegioPanter (3-car) — 640.png rows 0=640, 2=642, 1=641
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/640/sprites/najbrt1_2.png"),
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/640/sprites/najbrt2.png"),

    # 440 RegioPanter (3-car) — cd_440_panther.png rows 0=440, 2=442, 1=441
    (PAK128CS / "440_640_650/cd_440_panther.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/440/sprites/najbrt1_2.png"),
    (PAK128CS / "440_640_650/cd_440_panther.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/440/sprites/najbrt2.png"),

    # 640.1 RegioPanter (3-car) — reuse pak128_czr 640.png
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/640_1/sprites/najbrt1_2.png"),
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/640_1/sprites/najbrt2.png"),

    # 640.2 RegioPanter (3-car) — pid uses 640_PID.png, najbrt 2 uses 640.png
    (PAK128_CZR_EMU / "CD/640_PID.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/640_2/sprites/pidsedocervena.png"),
    (PAK128_CZR_EMU / "CD/640.png", [0, 2, 1], ROOT / "vehicle-rail/ceske-drahy/640_2/sprites/najbrt2.png"),

    # 690.2 RegioPanter (2-car) — 690.png row 0=690, row 1=691; green+blue battery livery
    (PAK128_CZR_EMU / "CD/690.png", [0, 1], ROOT / "vehicle-rail/ceske-drahy/690_2/sprites/cdzelenomodrobila.png"),
]


def main() -> int:
    for src, rows, dest in JOBS:
        if not src.exists():
            print(f"  [skip] {src} missing")
            continue
        img = extract_rows(src, rows)
        write(dest, img)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
