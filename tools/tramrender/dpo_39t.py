"""Škoda 39T ForCity Smart Ostrava (DPO) rendered on the field raymarcher.

    python tools/tramrender/dpo_39t.py [--variant NAME] [--out PNG] [--preview DIR]

Variants: `final` (shipped) and `darkroof` (the same car in the earlier DPO
palette with the dark teal roof, for comparison).

Without --out the sheet goes to vehicle-tram/dpo/39t_forcitysmart/sprites/
dpotyrkysova.png. Change the model here and regenerate, never edit the PNG.

The real car (cs.wikipedia, Škoda): 26.6 m, 2.5 m wide, 3.555 m high, two
sections, 2'Bo'Bo' (the front section on one bogie, the rear section on two),
unidirectional, five double doors on the right side only. Layout measured on a
near-orthographic side photo of 1760 (Commons "20230422 Skoda 39T DPO
Vystaviste - U hradu 01.jpg"), in metres from the nose: joint centre 12.4
(front section 12.4 m, rear 14.25 m, so 8 + 10 carunits); doors 1.35-2.9,
6.9-8.5, 9.9-11.5 | 16.8-18.4, 23.8-25.4; bogies 4.9 | 14.8, 21.9; pantograph
base 4.2. The window counts of the left side (1768: cab + 6 bays in front,
7 behind) agree. Positions below are carunits, mapped piecewise so the joint
lands on the section boundary.

Livery (photos of 1751-1779, colours in dpo_palette.py): DPO turquoise on the
body, a sunlit tint of it on the roof; black glazing band from the nose to the
tail with a white line under it that runs across the front below the
headlights; the front is a black mask (windscreen, black cap over the top front
edge, LED headlights at its lower corners) and the rear end repeats it with
tail lights; doors are dark glass in white frames; silver bellows; one dark
single-arm pantograph on the front section, knee trailing.

Shape (the user's pick of four variants, 2026-10-18): the cab is drawn bolder
than measured (windscreen raked ~0.6 carunit, nose corners 0.7) so it reads at
1x; sides are flat (one blue in every view) with one shoulder step.

Placement: each section's front sits on the front anchor of the native DPO
trams (fitted to the previous, in-game-checked 39T sheet and TommPa9's Tango
NF2, within 1 px), so the joints close in all 8 views at any section length.
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
SHEET = os.path.join(ROOT, "vehicle-tram", "dpo", "39t_forcitysmart", "sprites", "dpotyrkysova.png")

LEN_A, LEN_B = 8, 10
JOINT = float(LEN_A)

# ------------------------------------------------------------------ variants
BASE = dict(
    len_a=LEN_A, len_b=LEN_B,
    W=0.95,            # half width, carunits (natives: 11 px in the nw/se views)
    z_bot=1.0,         # skirt bottom, px
    z_top=14.0,        # roof crown, px
    nose=0.06, tail=17.94,
    joint=(JOINT - 0.20, JOINT + 0.20),
    rake=0.62,         # windscreen set-back at its top, carunits (measured ~0.3)
    nose_plan=0.7,     # plan radius of the nose corners (measured ~0.55)
    tail_plan=0.45,
    tail_rake=0.18,
    cap=0.6,           # roof cap rounding at both ends, carunits
    shoulder=0.42,     # roof shoulder radius, carunits
    z_white=(5.0, 6.0),
    z_white_front=(4.0, 5.0),
    z_win_top=11.4,
    roof_top=pal.ROOF,
    blue=pal.BODY,
    panto_arm=pal.PANTO_ARM,
    flat=True,         # one blue on every side in every view
    top_steps=2,       # one in-between step on the roof shoulder
    polish=dict(outline=0.22, edges=0.15, punch=0.0),
    # layout (carunits), see the docstring
    doors_a=[(0.87, 1.87), (4.45, 5.46), (6.41, 7.43)],
    doors_b=[(11.10, 12.18), (16.01, 17.10)],
    bogies=[3.18, 9.71, 14.65],
    # window pillars: big panes between the doors on the right; on the left
    # (no doors) 6 bays on the front section and 7 on the rear
    pillars_r=[3.03, 9.68, 13.40, 14.69],
    pillars_l=[2.03, 3.16, 4.29, 5.42, 6.55, 9.59, 10.85, 12.11, 13.37, 14.63, 15.90],
    panto_u=2.73,
    cab_left=1.3, tail_mask_u=17.15, back_u=17.4,
)
VARIANTS = {
    "final": dict(),
    "darkroof": dict(roof_top=0x007B94),
}


def render_sheet(p):
    return fieldtram.render_sheet(p)


def params(name):
    p = dict(BASE)
    p.update(VARIANTS[name])
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="final", choices=sorted(VARIANTS))
    ap.add_argument("--out")
    ap.add_argument("--preview")
    a = ap.parse_args()
    img = render_sheet(params(a.variant))
    out = a.out or SHEET
    img.save(out)
    print("wrote", out)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        big = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
        big.save(os.path.join(a.preview, f"39t_{a.variant}_x3.png"))


if __name__ == "__main__":
    main()
