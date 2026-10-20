"""Stadler Tango NF2 "nOVA" of DP Ostrava (1701-1740), on fieldtram.py.

    python tools/tramrender/dpo_tango.py [--variant NAME] [--out PNG] [--preview DIR]

Without --out the sheet goes to vehicle-tram/dpo/tangonf2/sprites/dpotyrkysova.png.
Change the model here and regenerate, never edit the PNG.

The real car: 24.9 m, two sections, one-way, four double doors on the right
side only, three bogies with turquoise skirts. Layout from the Stadler type
sketch (Commons "Stadler DPO nOVA.png", checked against the side photo of 1727),
in metres from the nose: joint 13.8 (front section 13.8 m, rear 11.1 m, so
9 + 8 carunits); doors 1.5-3.1, 7.3-8.8 | 15.6-17.3, 21.6-23.0; bogies 4.8,
11.5 | 20.1; orange-yellow single-arm pantograph over the front bogie (3.1-4.4).

Look (photos of 1704, 1708, 1724, 1727, 1739 from above): a tall, nearly
vertical front, black from the roof down to the lamp pods with the windscreen
in it, the lower front jutting out in turquoise; the white line under the
windows sweeps down to the lower front corner; a light grey air-conditioning
box over the cab; tall turquoise roof fairings with the dark equipment between
them; doors in white frames; colours from dpo_palette.py.
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fieldtram  # noqa: E402
import dpo_palette as pal  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SHEET = os.path.join(ROOT, "vehicle-tram", "dpo", "tangonf2", "sprites", "dpotyrkysova.png")

LEN_A, LEN_B = 9, 8
JOINT = float(LEN_A)


def m_to_u(m):
    """Real metres from the nose -> carunits, the joint (13.8 m) on the boundary."""
    if m <= 13.8:
        return m * LEN_A / 13.8
    return LEN_A + (m - 13.8) * LEN_B / 11.1


def span(a, b):
    return (round(m_to_u(a), 2), round(m_to_u(b), 2))


BASE = dict(
    len_a=LEN_A, len_b=LEN_B,
    W=0.95, z_bot=1.0, z_top=14.0,
    nose=0.06, tail=LEN_A + LEN_B - 0.06,
    joint=(JOINT - 0.20, JOINT + 0.20),
    rake=0.32, nose_plan=0.5, cap=0.42,
    chin=0.30, chin_z=5.6,          # the lower front juts out below the lamp pods
    ws=(6.6, 12.8),
    tail_plan=0.45, tail_rake=0.15,
    shoulder=0.40,
    z_white=(5.0, 6.0),
    z_white_front=(4.4, 5.4),
    wedge=(1.2, 2.0),               # white line sweeping down to the front corner
    z_win_top=11.4,
    roof_top=pal.ROOF,
    blue=pal.BODY,
    panto_arm=(0xF0, 0xA0, 0x1E),   # orange-yellow Stadler pantograph
    panto_head=(0x26, 0x28, 0x2A),
    flat=True, top_steps=2,
    polish=dict(outline=0.22, edges=0.15, punch=0.0),
    doors_a=[span(1.5, 3.1), span(7.3, 8.8)],
    doors_b=[span(15.6, 17.3), span(21.6, 23.0)],
    bogies=[round(m_to_u(m), 2) for m in (4.8, 11.5, 20.1)],
    pillars_r=[round(m_to_u(m), 2) for m in (5.2, 11.0, 19.4)],
    pillars_l=[2.6, 3.85, 5.1, 6.35, 7.6, 10.4, 11.6, 12.8, 14.0, 15.2],
    panto_u=round(m_to_u(3.75), 2),
    cab_left=1.3, tail_mask_u=LEN_A + LEN_B - 0.85, back_u=LEN_A + LEN_B - 0.6,
    ac_box=(0.75, 1.65, 0.45, 1.2),
    zmax_extra=1.0,
    roof_gear=[(1.75, 8.55), (9.45, 12.4)],
    fairing=0.30,
)
VARIANTS = {
    "fairings": dict(),                               # dark equipment between the fairings + AC box
    "soft": dict(gear_col=0x5E7880),                  # the same, equipment in a softer slate
    "plain": dict(roof_gear=[]),                      # AC box only
    "bare": dict(roof_gear=[], ac_box=None),          # nothing on the roof but the pantograph
}


def params(name):
    p = dict(BASE)
    p.update(VARIANTS[name])
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="fairings", choices=sorted(VARIANTS))
    ap.add_argument("--out")
    ap.add_argument("--preview")
    a = ap.parse_args()
    img = fieldtram.render_sheet(params(a.variant))
    out = a.out or SHEET
    img.save(out)
    print("wrote", out)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        big = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
        big.save(os.path.join(a.preview, f"tango_{a.variant}_x3.png"))


if __name__ == "__main__":
    main()
