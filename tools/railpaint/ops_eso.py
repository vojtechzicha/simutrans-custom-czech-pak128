#!/usr/bin/env python3
"""RegioJet 162 / 362.2, ZSSK 361.1 and ŽSR 362: TommPa9's Eso / Peršing drawing
repainted, the same way as the ČD 162 / 163 / 362 / 371 (cd_eso.py, variant E3).

    python tools/railpaint/ops_eso.py [regiojet/162|regiojet/362_2|zssk/361_1|zsr/362 ...] [--preview DIR]

Every family takes the details of one of his class sheets (src/tommpa9_eso/)
and the paint of its own photos, in the colours of the operator's other VZ
vehicles (rj_locos.py, the former zssk361.py render), with the E3 roof: his grey roof gear and a
dark gutter where the roof meets the side.

  regiojet/162    CD_162 details, RJ yellow, anthracite sill, the dark louvre band
                  on side B, red-brown pantographs, grey roof, and the big
                  "|| REGIOJET" on side A taken pixel for pixel from his own RJ 162
                  sheet (src/tommpa9_eso_other/rj_162_Pershing.png, same
                  silhouette).
  regiojet/362_2  one row per loco (each sheet leaves the rows before it empty):
                  362.212 csdmodrozluta on the layout of his CSD_ES_499.1 (ČSD
                  blue, yellow waist band, cream roof, roof edge and louvre band,
                  yellow window frames and pantographs), 362.220 fnmzelenosediva
                  (FNM green over silver, the dark blue line dropping to the lamp
                  row at the cab ends, red beams and pantographs), 362.213 zluta
                  (the 162 with a black louvre band and a dark roof), 362.219
                  zlutosediva (lemon yellow, dark grey mask and lower band).
  zssk/361_1      cervenobila on his own ZSSK_361.1_Pershing (red, off-white band,
                  grey frame, white window frames, yellow beam); korporatni by
                  rule (361 129): the machine room red with a white line along
                  the top, a white wedge before the right-hand cab door as seen,
                  the big white arc logo, the off-white band only on the left.
  zsr/362         modrobezova on his own ZSR_362_Pershing: the 1990s ŽSR dark blue
                  with the beige band, his yellow pantographs (ported because the
                  user's save runs it; kept a ŽSR loco at the user's wish).
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import cd_eso as E  # noqa: E402
from handpaint import T, load, save  # noqa: E402

OTHER = os.path.join(HERE, "src", "tommpa9_eso_other")

# RegioJet (rj_locos.py) and ZSSK (the former zssk361.py render) colours
RJ_YELLOW = (0xFF, 0xB6, 0x12)
RJ_LEMON = (0xFF, 0xC7, 0x0E)
RJ_RED = (0xE3, 0x34, 0x2F)
RJ_BLUE = (0x1F, 0x3A, 0x93)
RJ_ANTH = (0x2E, 0x31, 0x33)
RJ_BLACK = (0x1C, 0x1E, 0x20)
RJ_ROOF = (0x6C, 0x73, 0x7A)
RJ_LOUVRE = (0x6E, 0x57, 0x22)
RJ_PANTO = (0x8A, 0x2A, 0x22)
CSD_BLUE = (0x24, 0x61, 0xE0)
CSD_YELLOW = (0xF2, 0xBA, 0x1E)
CSD_CREAM = (0xDD, 0xD5, 0xCC)
CSD_PANTO = (0xE8, 0xC0, 0x1C)
FNM_GREEN = (0x3F, 0xAE, 0x3C)
FNM_SILVER = (0xCD, 0xD2, 0xD5)
FNM_BLUE = (0x1F, 0x2F, 0x66)
FNM_RED = (0xD2, 0x2A, 0x20)
FNM_PANTO = (0xC4, 0x30, 0x2A)
DARK_MASK = (0x3A, 0x3E, 0x44)
LAMP_GREY = (0xB8, 0xBC, 0xC0)
Z_RED = (0xB8, 0x20, 0x2A)
Z_WHITE = (0xE6, 0xE2, 0xDA)
Z_GREY = (0x8E, 0x8A, 0x86)
Z_FRAMEW = (0xEE, 0xEC, 0xE6)
Z_YELLOW = (0xE8, 0xC2, 0x1A)
Z_ROOF = (0xA4, 0xA6, 0xA8)
Z_LOUVRE = (0x7A, 0x14, 0x18)
ZSR_BEIGE = (0xD2, 0xCC, 0xA0)        # his beige band (0xC5C58C seen square-on)


def as_seen(u, col):
    """0 left .. 1 right as seen: the front is at the left in sw / w / s."""
    return u if col in (7, 0, 6) else 1 - u


def lettering(hb, put, zone_colour):
    """his big "|| REGIOJET" (red REGIO, blue JET) and the small front logos,
    pixel for pixel from his own RJ 162 sheet of the same silhouette."""
    rj = load(os.path.join(OTHER, "rj_162_Pershing.png"))
    r, g, b = rj[..., 0], rj[..., 1], rj[..., 2]
    face = (hb.face == "S") | (hb.face == "E")
    red = face & (r > 150) & (g < 100) & (b < 120)
    blue = face & (b > r + 30) & (b > 70)
    for y, x in zip(*np.where(red)):
        put(y, x, RJ_RED)
    for y, x in zip(*np.where(blue)):
        put(y, x, RJ_BLUE)


def rj_yellow(face, k, u, col):
    return "sill" if face == "S" and k == 7 else "body"


def fnm(face, k, u, col):
    if face == "E":
        return "green" if k <= 3 else "line" if k == 4 else "silver"
    cab = u < 0.12 or u > 0.88
    line = 6 if cab else 4                  # the line drops to the lamp row at the cab ends
    if k == 7:
        return "line"                        # dark blue sill
    return "green" if k < line else "line" if k == line else "silver"


def zlutosediva(face, k, u, col):
    if face == "E":
        return "mask" if k <= 4 else "lamp" if k <= 6 else "mask"
    return "body" if k <= 5 else "mask"


def zssk_corp(face, k, u, col):
    if face == "E":
        return "body" if k <= 4 else "band" if k <= 6 else "frame"
    s = as_seen(u, col)
    if s < 0.12 or s > 0.88:                 # cabs as on the red-white scheme
        return "body" if k <= 4 else "band" if k <= 6 else "frame"
    if k == 7:
        return "frame"
    t = (s - 0.12) / 0.76                    # machine room, 0 left .. 1 right as seen
    hz = 1 - k / 7.0                         # 1 at the top .. 0 at the frame
    if k == 0:
        return "band"                        # thin white line along the top
    if t >= 0.93 - 0.13 * hz:
        return "band"                        # white wedge before the right-hand door
    if t < 0.58 and k >= 5:
        return "band"                        # off-white band only on the left part
    return "body"


ARC = [".###.",
       "##..#",
       "#.#.#",
       "#...#",
       ".###."]


def zssk_arc(hb, put, zone_colour):
    """the big white ZSSK arc logo, low on the red in front of the wedge."""
    for c in (0, 2, 3, 4, 6, 7):
        X0 = c * 128
        cols = sorted(x for x in range(128) if (hb.face[:, X0 + x] == "S").any())
        if not cols:
            continue
        cu = {x: float(np.median(hb.U[hb.face[:, X0 + x] == "S", X0 + x])) for x in cols}
        span = [x for x in cols if 0.62 <= (as_seen(cu[x], c) - 0.12) / 0.76 <= 0.78]
        if len(span) < 3:
            continue
        n = min(5, len(span))
        mid = len(span) // 2
        pick = span[max(0, mid - n // 2):max(0, mid - n // 2) + n]
        for i, x in enumerate(pick):
            ci = int(round(i * (len(ARC[0]) - 1) / max(1, n - 1)))
            for j in range(5):
                if ARC[j][ci] != "#":
                    continue
                for y in np.where((hb.face[:, X0 + x] == "S") & (hb.K[:, X0 + x] == 2 + j))[0]:
                    put(y, X0 + x, Z_FRAMEW)


def liveries():
    rj162 = E.Livery({"body": RJ_YELLOW, "sill": RJ_ANTH, "louvre": RJ_LOUVRE}, rules=rj_yellow,
                     beam=RJ_BLACK, panto=RJ_PANTO, roof=RJ_ROOF, extra=lettering, drop_marks=True)
    return {
        ("regiojet/162", "zluta"): ("CD_162_Rychly_Pershing", rj162, 0),
        ("regiojet/362_2", "csdmodrozluta"): (
            "CD_162_Rychly_Pershing",
            E.Livery({"body": CSD_BLUE, "stripe": CSD_YELLOW, "louvre": CSD_CREAM}, template="CSD_ES_499.1_Eso",
                     frames=CSD_YELLOW, beam=CSD_BLUE, panto=CSD_PANTO, roof=CSD_CREAM, gutter=CSD_CREAM), 0),
        ("regiojet/362_2", "fnmzelenosediva"): (
            "CD_162_Rychly_Pershing",
            E.Livery({"green": FNM_GREEN, "silver": FNM_SILVER, "line": FNM_BLUE, "louvre": FNM_SILVER},
                     rules=fnm, beam=FNM_RED, panto=FNM_PANTO, roof=FNM_SILVER, drop_marks=True), 1),
        ("regiojet/362_2", "zluta"): (
            "CD_162_Rychly_Pershing",
            E.Livery({"body": RJ_YELLOW, "sill": RJ_ANTH, "louvre": (0x2B, 0x2D, 0x30)}, rules=rj_yellow,
                     beam=RJ_BLACK, panto=(0x3A, 0x3D, 0x40), roof=(0x58, 0x5E, 0x64), extra=lettering,
                     drop_marks=True), 2),
        ("regiojet/362_2", "zlutosediva"): (
            "CD_162_Rychly_Pershing",
            E.Livery({"body": RJ_LEMON, "mask": DARK_MASK, "lamp": LAMP_GREY, "louvre": (0x34, 0x38, 0x3C)},
                     rules=zlutosediva, beam=DARK_MASK, panto=(0x2E, 0x31, 0x34), roof=(0x50, 0x55, 0x5A),
                     drop_marks=True), 3),
        ("zssk/361_1", "cervenobila"): (
            "ZSSK_361.1_Pershing",
            E.Livery({"body": Z_RED, "band": Z_WHITE, "frame": Z_GREY, "louvre": Z_LOUVRE},
                     template="ZSSK_361.1_Pershing", frames=Z_FRAMEW, beam=Z_YELLOW, roof=Z_ROOF), 0),
        ("zsr/362", "modrobezova"): (
            "ZSR_362_Pershing",
            E.Livery({"body": E.CL.BC_BLUE, "stripe": ZSR_BEIGE, "louvre": E.LOUVRE_GREY},
                     template="ZSR_362_Pershing", panto=None), 0),
        ("zssk/361_1", "korporatni"): (
            "ZSSK_361.1_Pershing",
            E.Livery({"body": Z_RED, "band": Z_WHITE, "frame": Z_GREY, "louvre": Z_LOUVRE}, rules=zssk_corp,
                     frames=Z_FRAMEW, beam=Z_YELLOW, roof=Z_ROOF, extra=zssk_arc), 0),
    }


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    jobs = liveries()
    fams = args or sorted({f for f, _ in jobs})
    for (fam, name), (base, L, row) in jobs.items():
        if fam not in fams:
            continue
        a = E.paint_livery(base, L).astype(np.uint8)
        sheet = np.zeros(((row + 1) * 128, 1024, 3), np.uint8)
        sheet[:] = T
        sheet[row * 128:] = a
        path = os.path.join(REPO, "vehicle-rail", fam, "sprites", f"{name}.png")
        save(sheet, path)
        print("wrote", os.path.relpath(path, REPO))
        if prev:
            g = a.copy()
            g[np.all(g == T, axis=2)] = (104, 124, 76)
            Image.fromarray(g).resize((3072, 384), Image.NEAREST).save(
                os.path.join(prev, f"{fam.replace('/', '_')}_{name}.png"))


if __name__ == "__main__":
    main()
