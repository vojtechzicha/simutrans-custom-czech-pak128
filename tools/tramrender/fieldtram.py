"""Two-section, one-way low-floor tram on the field raymarcher (fieldrender.py).

The body model behind dpo_39t.py (Škoda 39T) and dpo_tango.py (Stadler Tango
NF2 "nOVA"); a driver passes one parameter dict `p` and gets the sheet back:

    img = fieldtram.render_sheet(p)

Model coordinates are those of fieldrender.py: u = carunits behind the nose of
the front section A, v = lateral (+v = right-hand side, the door side of a
one-way tram), z = px above the rail. Section A runs from the nose to the joint
at u = len_a, section B from the joint to the tail; the bellows are split at
the joint so each section is drawn complete with its half (see
fieldrender.vehicle_tile).

Layout keys of `p` (carunits): len_a, len_b, nose, tail, joint (bellows u0, u1),
doors_a / doors_b (right side), bogies, pillars_r / pillars_l (window pillars),
panto_u, cab_left (cab mask length on the left side), tail_mask_u (black end
of the rear section's window band), back_u (where the rear face starts).
Shape keys: W (half width), z_bot / z_top (skirt bottom, roof crown, px),
shoulder, rake / nose_plan / cap / chin (front), tail_rake / tail_plan (rear),
ws (windscreen bottom and top, px). Livery keys: z_white, z_white_front,
z_win_top, blue, roof_top, panto_arm, panto_head, wedge (white line sweeping
down to the front corner), roof_gear (dark equipment between the roof
fairings, list of u ranges), ac_box (light grey box on the roof, u range).
"""
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

# Front anchor (screen px of u = 0, v = 0, z = 0 of the drawn section) per view:
# the placement of the native DPO trams (fitted to the in-game-checked 39T sheet
# of 2026-09-25 and TommPa9's Tango NF2, within 1 px).
ANCHOR = {"w": (41.25, 84.25), "nw": (64.0, 76.25), "n": (85.5, 85.25), "ne": (84.0, 97.25),
          "e": (75.75, 101.9), "se": (64.0, 106.0), "s": (52.1, 101.9), "sw": (36.5, 96.25)}


def build(p):
    W = p["W"]
    zb, zt = p["z_bot"] / ZS, p["z_top"] / ZS
    rs = p["shoulder"]
    j0, j1 = p["joint"]
    JOINT = float(p["len_a"])
    DOORS_A, DOORS_B, BOGIES = p["doors_a"], p["doors_b"], p["bogies"]
    PILLARS_R, PILLARS_L = p["pillars_r"], p["pillars_l"]
    ws0, ws1 = p.get("ws", (6.6, 12.4))

    def cross(v, zs, w=W, top=zt, bot=zb, r=rs):
        hh = (top - (bot - 1.0)) / 2.0
        zc = (top + bot - 1.0) / 2.0
        return np.maximum(round_rect(v, zs - zc, w, hh, r), bot - zs)

    def plan(v, rp):
        q = np.maximum(0.0, np.abs(v) - (W - rp))
        return rp - np.sqrt(np.maximum(0.0, rp * rp - q * q))

    def end_profile(zs, rake, z_ws0=ws0, z_ws1=ws1, chin=0.0):
        z = zs * ZS
        sb = np.zeros_like(z)
        sb = np.where(z < 2.0, 0.10 * (2.0 - z) / 2.0, sb)                    # bumper chamfer
        if chin:
            # the lower front juts out: everything above the chin sits further back
            sb = sb + chin * np.clip((z - p["chin_z"] + 0.6) / 1.2, 0.0, 1.0)
        t = np.clip((z - z_ws0) / (z_ws1 - z_ws0), 0.0, 1.0)
        sb = sb + rake * t                                                    # raked glass
        c = np.clip((z - z_ws1) / (p["z_top"] - z_ws1), 0.0, 1.0)
        sb = sb + p["cap"] * (1.0 - np.sqrt(np.maximum(0.0, 1.0 - c * c)))    # roof cap
        return sb

    def section_a(u, v, zs):
        f = cross(v, zs)
        f = np.maximum(f, p["nose"] + end_profile(zs, p["rake"], chin=p.get("chin", 0.0))
                       + plan(v, p["nose_plan"]) - u)
        return np.maximum(f, u - j0)

    def section_b(u, v, zs):
        f = cross(v, zs)
        f = np.maximum(f, j1 - u)
        return np.maximum(f, u - (p["tail"] - end_profile(zs, p["tail_rake"]) - plan(v, p["tail_plan"])))

    def bellows(u, v, zs):
        f = cross(v, zs, w=W - 0.05, top=zt - 0.22, bot=zb + 0.1, r=rs * 0.8)
        return np.maximum(f, np.abs(u - JOINT) - (j1 - j0) / 2.0 - 0.02)

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
        if cab and p.get("wedge"):
            # the white line sweeps down to the lower front corner
            u1, drop = p["wedge"]
            k = np.clip((u1 - u) / u1, 0.0, 1.0) * drop
            zone = np.where((u < u1) & (z >= zw0 - k) & (z < zw1 - k), "white", zone)
        pr = np.min([np.abs(u - q) for q in PILLARS_R], axis=0) < 0.07
        pl = np.min([np.abs(u - q) for q in PILLARS_L], axis=0) < 0.07
        pill = np.where(v > 0, pr, pl)
        zone = np.where(win, np.where(pill, "pillar", "glass"), zone)
        if cab:
            # cab side: black mask over the window band, the driver's window in it
            # (up to the first door on the right, a little further on the left)
            cab_end = np.where(v > 0, DOORS_A[0][0] - 0.01, p["cab_left"])
            cabm = (u < cab_end) & (z >= zf1 - 0.4) & (z < zwt + 0.3)
            dwin = (u > 0.35) & (u < cab_end - 0.08) & (z >= 7.0) & (z < 11.0)
            zone = np.where(cabm, np.where(dwin, "cabglass", "mask"), zone)
        if tail_end:
            tm = (u > p["tail_mask_u"]) & (z >= zw1) & (z < zwt)
            zone = np.where(tm, "mask", zone)
        right = v > 0
        for (d0, d1) in doors:
            ind = right & (u >= d0) & (u <= d1) & (z >= 1.3) & (z < zwt + 0.4)
            edge = (u - d0 < 0.13) | (d1 - u < 0.13) | (z >= zwt - 0.2) | (z < 1.9)
            mid = np.abs(u - (d0 + d1) / 2.0) < 0.045
            zone = np.where(ind, np.where(edge, "doorframe", np.where(mid, "pillar", "doorglass")), zone)
        return zone

    def roof_zones(zone, u, v, nz):
        for (g0, g1) in p.get("roof_gear", ()):
            gear = (nz > 0.75) & (np.abs(v) < W - p.get("fairing", 0.3)) & (u >= g0) & (u <= g1)
            zone = np.where(gear, "roofgear", zone)
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
        zone = roof_zones(zone, u, v, nz)
        nose = (u < p.get("nose_zone", 0.62)) & (nu < -0.35)
        zone = np.where(nose, front_zones(u, v, z, nu, nz), zone)
        # black cap over the top front edge
        visor = (u < 0.95) & (nz > 0.3) & (u < 0.62 + (np.abs(v) < 0.6) * 0.33)
        zone = np.where(visor & (z > 12.0), "mask", zone)
        return zone

    def zone_b(P):
        u, v, z, nu, nz = P["u"], P["v"], P["z"], P["nu"], P["nz"]
        zone = side_zones(u, v, z, DOORS_B, cab=False, tail_end=True)
        zone = roof_zones(zone, u, v, nz)
        back = (u > p["back_u"]) & (nu > 0.35)
        zone = np.where(back, rear_zones(u, v, z), zone)
        return zone

    def zone_bellows(P):
        u = P["u"]
        k = np.floor((u - j0) / 0.1).astype(int)
        return np.where(k % 2 == 0, "bellows", "bellows_d")

    def const(name):
        return lambda P: np.full(len(P["u"]), name, dtype=object)

    solids = [
        Solid(section_a, zone_a, "A"),
        Solid(section_b, zone_b, "B"),
        Solid(lambda u, v, zs: np.maximum(bellows(u, v, zs), u - JOINT), zone_bellows, "A"),
        Solid(lambda u, v, zs: np.maximum(bellows(u, v, zs), JOINT - u), zone_bellows, "B"),
        Solid(lambda u, v, zs: np.maximum(wheels(u, v, zs), u - JOINT), const("wheel"), "A"),
        Solid(lambda u, v, zs: np.maximum(wheels(u, v, zs), JOINT - u), const("wheel"), "B"),
    ]
    if p.get("ac_box"):
        a0, a1, hw, h = p["ac_box"]
        zr0 = (p["z_top"] - 1.0) / ZS

        def ac(u, v, zs):
            f = round_rect(u - (a0 + a1) / 2.0, v, (a1 - a0) / 2.0, hw, 0.15)
            return np.maximum(f, np.abs(zs - (zr0 + h / ZS / 2.0 + 0.5 / ZS)) - (h / ZS / 2.0 + 0.5 / ZS))
        solids.append(Solid(ac, const("acbox"), "A"))

    # pantograph: knee trailing, 1-px arms, 2-px head bar
    zr = p["z_top"] - 0.2
    arm, head = p["panto_arm"], p.get("panto_head", pal.PANTO_HEAD)
    PANTO_U = p["panto_u"]
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
        "roofgear": Paint(p.get("gear_col", 0x3E4448)),
        "acbox": Paint(p.get("ac_col", 0xC4C8CC), top=p.get("ac_top", 0xD4D8DC)),
    }
    return solids, lines, livery


def render_sheet(p):
    solids, lines, livery = build(p)
    rows = []
    for (u_front, keep) in ((0.0, {"A"}), (float(p["len_a"]), {"B"})):
        tiles = []
        for d in fr.DIRS:
            tiles.append(fr.vehicle_tile(solids, lines, d, u_front, keep, ANCHOR[d], livery,
                                         zmax=p["z_top"] + 2.0 + p.get("zmax_extra", 0.0), step=0.08,
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
