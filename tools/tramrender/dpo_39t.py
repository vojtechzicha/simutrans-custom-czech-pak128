"""Škoda 39T ForCity Smart Ostrava (DPO) rendered on the field raymarcher.

    python tools/tramrender/dpo_39t.py [--variant NAME] [--out PNG] [--preview DIR]

Variants: `final` (shipped) and `darkroof` (the same car in the earlier DPO
palette with the dark teal roof, for comparison).

Without --out the sheet goes to vehicle-tram/dpo/39t_forcitysmart/sprites/
dpotyrkysova.png. Change the model here and regenerate, never edit the PNG.

The real car (cs.wikipedia, Škoda): 26.6 m, 2.5 m wide, 3.555 m high, two
sections, 2'Bo'Bo' (the front section on one bogie, the rear section on two),
unidirectional, five double doors on the right side only. The split was measured
on three side photos (1753, 1766, 1768) with a perspective fit of the lower body
band: front section ~14.3 m to the joint, rear ~12.3 m, so 10 + 8 carunits.
Doors (right side, from 1755): front section 3 (behind the cab, then two near
the joint), rear section 2 (one mid, one at the tail). Bogies: front section
~6.8 m from the nose, rear section at ~17 m and ~23.5 m.

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

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fieldrender as fr  # noqa: E402
from fieldrender import Paint, Lit, Solid, round_rect, ZS  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "railrender"))
import style  # noqa: E402
import dpo_palette as pal  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SHEET = os.path.join(ROOT, "vehicle-tram", "dpo", "39t_forcitysmart", "sprites", "dpotyrkysova.png")

# Front anchor (screen px of u = 0, v = 0, z = 0 of the drawn section) per view.
ANCHOR = {"w": (41.25, 84.25), "nw": (64.0, 76.25), "n": (85.5, 85.25), "ne": (84.0, 97.25),
          "e": (75.75, 101.9), "se": (64.0, 106.0), "s": (52.1, 101.9), "sw": (36.5, 96.25)}

LEN_A, LEN_B = 10, 8

# ------------------------------------------------------------------ variants
BASE = dict(
    W=0.95,            # half width, carunits (natives: 11 px in the nw/se views)
    z_bot=1.0,         # skirt bottom, px
    z_top=14.0,        # roof crown, px
    nose=0.06, tail=17.94,
    joint=(9.80, 10.20),
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
)
VARIANTS = {
    "final": dict(),
    "darkroof": dict(roof_top=0x007B94),
}

DOORS_A = [(2.30, 3.40), (6.20, 7.20), (8.30, 9.30)]
DOORS_B = [(12.70, 13.80), (16.55, 17.55)]
BOGIES = [4.8, 11.8, 16.0]
# window pillars (u): the right side has big panes between the doors, the left
# side (no doors) an even rhythm of ~1.25 carunits
PILLARS_R = [4.8, 11.45, 15.2]
PILLARS_L = [3.2, 4.45, 5.7, 6.95, 8.2, 9.45, 11.4, 12.6, 13.8, 15.0, 16.2]
PANTO_U = 3.6


def build(p):
    W = p["W"]
    zb, zt = p["z_bot"] / ZS, p["z_top"] / ZS
    rs = p["shoulder"]
    j0, j1 = p["joint"]

    def cross(v, zs, w=W, top=zt, bot=zb, r=rs):
        hh = (top - (bot - 1.0)) / 2.0
        zc = (top + bot - 1.0) / 2.0
        return np.maximum(round_rect(v, zs - zc, w, hh, r), bot - zs)

    def plan(v, rp):
        q = np.maximum(0.0, np.abs(v) - (W - rp))
        return rp - np.sqrt(np.maximum(0.0, rp * rp - q * q))

    def end_profile(zs, rake, z_ws0=6.6, z_ws1=12.4):
        z = zs * ZS
        sb = np.zeros_like(z)
        sb = np.where(z < 2.0, 0.10 * (2.0 - z) / 2.0, sb)                    # bumper chamfer
        t = np.clip((z - z_ws0) / (z_ws1 - z_ws0), 0.0, 1.0)
        sb = sb + rake * t                                                    # raked glass
        c = np.clip((z - z_ws1) / (p["z_top"] - z_ws1), 0.0, 1.0)
        sb = sb + p["cap"] * (1.0 - np.sqrt(np.maximum(0.0, 1.0 - c * c)))    # roof cap
        return sb

    def section_a(u, v, zs):
        f = cross(v, zs)
        f = np.maximum(f, p["nose"] + end_profile(zs, p["rake"]) + plan(v, p["nose_plan"]) - u)
        return np.maximum(f, u - j0)

    def section_b(u, v, zs):
        f = cross(v, zs)
        f = np.maximum(f, j1 - u)
        return np.maximum(f, u - (p["tail"] - end_profile(zs, p["tail_rake"]) - plan(v, p["tail_plan"])))

    def bellows(u, v, zs):
        f = cross(v, zs, w=W - 0.05, top=zt - 0.22, bot=zb + 0.1, r=rs * 0.8)
        return np.maximum(f, np.abs(u - 10.0) - (j1 - j0) / 2.0 - 0.02)

    def wheels(u, v, zs):
        d = np.min([np.abs(u - b) for b in BOGIES], axis=0) - 0.8
        return np.maximum(np.maximum(d, np.abs(v) - (W - 0.18)), np.abs(zs - 0.8 / ZS) - 0.8 / ZS)

    zw0, zw1 = p["z_white"]
    zf0, zf1 = p["z_white_front"]
    zwt = p["z_win_top"]

    def side_zones(u, v, z, doors, cab, tail_end):
        zone = np.full(u.shape, "body", dtype=object)
        bog = np.min([np.abs(u - b) for b in BOGIES], axis=0) < 0.85
        zone = np.where(bog & (z < 2.4), "recess", zone)
        win = (z >= zw1) & (z < zwt)
        zone = np.where((z >= zw0) & (z < zw1), "white", zone)
        pr = np.min([np.abs(u - q) for q in PILLARS_R], axis=0) < 0.07
        pl = np.min([np.abs(u - q) for q in PILLARS_L], axis=0) < 0.07
        pill = np.where(v > 0, pr, pl)
        zone = np.where(win, np.where(pill, "pillar", "glass"), zone)
        if cab:
            # cab side: black mask over the window band, the driver's window in it
            cabm = (u < 1.95) & (z >= zf1 - 0.4) & (z < zwt + 0.3)
            dwin = (u > 0.55) & (u < 1.75) & (z >= 7.0) & (z < 11.0)
            zone = np.where(cabm, np.where(dwin, "cabglass", "mask"), zone)
        if tail_end:
            tm = (u > 17.15) & (z >= zw1) & (z < zwt)
            zone = np.where(tm, "mask", zone)
        right = v > 0
        for (d0, d1) in doors:
            ind = right & (u >= d0) & (u <= d1) & (z >= 1.3) & (z < zwt + 0.4)
            edge = (u - d0 < 0.13) | (d1 - u < 0.13) | (z >= zwt - 0.2) | (z < 1.9)
            mid = np.abs(u - (d0 + d1) / 2.0) < 0.045
            zone = np.where(ind, np.where(edge, "doorframe", np.where(mid, "pillar", "doorglass")), zone)
        return zone

    def front_zones(u, v, z, nu, nz):
        zone = np.full(u.shape, "body", dtype=object)
        zone = np.where((z >= zf0) & (z < zf1), "white", zone)
        upper = z >= zf1
        zone = np.where(upper, "mask", zone)
        ws = upper & (z >= 6.9) & (z < 12.2) & (np.abs(v) < W - 0.16)
        zone = np.where(ws, "cabglass", zone)
        hl = (z >= zf1) & (z < zf1 + 1.1) & (np.abs(v) > 0.42) & (np.abs(v) < 0.80)
        zone = np.where(hl, "head", zone)
        return zone

    def rear_zones(u, v, z):
        zone = np.full(u.shape, "body", dtype=object)
        zone = np.where((z >= zw0) & (z < zw1), "white", zone)
        upper = (z >= zw1) & (z < zwt + 0.4)
        zone = np.where(upper, "mask", zone)
        rw = upper & (z >= 7.0) & (z < 11.2) & (np.abs(v) < W - 0.28)
        zone = np.where(rw, "cabglass", zone)
        tl = (z >= zw1) & (z < zw1 + 1.0) & (np.abs(v) > 0.50) & (np.abs(v) < 0.82)
        zone = np.where(tl, "tail", zone)
        return zone

    def zone_a(P):
        u, v, z, nu, nz = P["u"], P["v"], P["z"], P["nu"], P["nz"]
        zone = side_zones(u, v, z, DOORS_A, cab=True, tail_end=False)
        nose = (u < 0.62) & (nu < -0.35)
        zone = np.where(nose, front_zones(u, v, z, nu, nz), zone)
        # black cap over the top front edge
        visor = (u < 0.95) & (nz > 0.3) & (u < 0.62 + (np.abs(v) < 0.6) * 0.33)
        zone = np.where(visor & (z > 12.0), "mask", zone)
        return zone

    def zone_b(P):
        u, v, z, nu = P["u"], P["v"], P["z"], P["nu"]
        zone = side_zones(u, v, z, DOORS_B, cab=False, tail_end=True)
        back = (u > 17.4) & (nu > 0.35)
        zone = np.where(back, rear_zones(u, v, z), zone)
        return zone

    def zone_bellows(P):
        u = P["u"]
        k = np.floor((u - j0) / 0.1).astype(int)
        return np.where(k % 2 == 0, "bellows", "bellows_d")

    solids = [
        Solid(section_a, zone_a, "A"),
        Solid(section_b, zone_b, "B"),
        Solid(lambda u, v, zs: np.maximum(bellows(u, v, zs), u - 10.0), zone_bellows, "A"),
        Solid(lambda u, v, zs: np.maximum(bellows(u, v, zs), 10.0 - u), zone_bellows, "B"),
        Solid(lambda u, v, zs: np.maximum(wheels(u, v, zs), u - 10.0), lambda P: np.full(len(P["u"]), "wheel", dtype=object), "A"),
        Solid(lambda u, v, zs: np.maximum(wheels(u, v, zs), 10.0 - u), lambda P: np.full(len(P["u"]), "wheel", dtype=object), "B"),
    ]

    # pantograph: knee trailing, dark arms, 2-px head bar
    zr = p["z_top"] - 0.2
    arm, head = p["panto_arm"], pal.PANTO_HEAD
    ub, uk, uh = PANTO_U, PANTO_U + 1.15, PANTO_U + 0.1
    zk, zh = zr + 4.2, zr + 8.6
    lines = [
        ((ub - 0.3, -0.35, zr), (ub + 0.3, -0.35, zr), arm, "A"),
        ((ub - 0.3, 0.35, zr), (ub + 0.3, 0.35, zr), arm, "A"),
        ((ub, 0.0, zr), (uk, 0.0, zk), arm, "A"),
        ((uk, 0.0, zk), (uh, 0.0, zh), arm, "A"),
        ((uh, -0.62, zh), (uh, 0.62, zh), head, "A", True),
    ]

    blue = p["blue"]
    livery = {
        "body": Paint(blue, top=p["roof_top"]),
        "recess": Paint(pal.SKIRT_RECESS),
        "white": Paint(pal.WHITE),
        "glass": Lit(pal.GLASS),             # passenger glass, lit at night when loaded
        "doorglass": Lit(pal.GLASS),
        "pillar": Paint(pal.PILLAR),
        "doorframe": Paint(pal.DOOR_FRAME),
        "mask": Paint(pal.MASK, top=pal.MASK_TOP),
        "cabglass": Paint(pal.CAB_GLASS, top=pal.CAB_GLASS_TOP),
        "head": Lit(pal.HEADLIGHT),
        "tail": Lit(pal.TAIL_LIGHT),
        "bellows": Paint(pal.BELLOWS),
        "bellows_d": Paint(pal.BELLOWS_FOLD),
        "wheel": Paint(pal.WHEEL),
    }
    return solids, lines, livery


def render_sheet(p):
    solids, lines, livery = build(p)
    rows = []
    for (u_front, keep) in ((0.0, {"A"}), (float(LEN_A), {"B"})):
        tiles = []
        for d in fr.DIRS:
            tiles.append(fr.vehicle_tile(solids, lines, d, u_front, keep, ANCHOR[d], livery,
                                         zmax=p["z_top"] + 2.0, step=0.08,
                                         flat=p["flat"], top_steps=p["top_steps"]))
        rows.append(tiles)
    sheet = np.zeros((128 * len(rows), 1024, 3), np.uint8)
    sheet[:, :] = fr.T
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            sheet[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128] = t
    img = Image.fromarray(sheet)
    if p.get("polish"):
        img = style.polish(img, **p["polish"])
    return img


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
