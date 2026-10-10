#!/usr/bin/env python3
"""ČD Škoda Eso / Peršing / Bastard (362, 162, 163, 371): TommPa9's pak128.cs
drawings, repainted in every livery.

    python tools/railpaint/cd_eso.py [362|162|163|371 ...] [--preview DIR]

The user chose TommPa9's hand-drawn Eso over every box render (2026-10-10,
variant E3 of the review page). All 21 of his sheets of this body share one
silhouette (frozen in src/tommpa9_eso/, lifted 4 px to source coordinates):
ČD 362 / 162 / 163 / 371 / 363 / 372, their "balkan" Najbrt 1.2 versions,
ČD Cargo, ČSD, ZSSK and ŽSR. handpaint.HandBase aligns them all to get exact
face rows (side wall K 0-7, end face K 0-7) in every view.

Each class keeps the details of its own sheet: CD_362_Rychle_Eso (portholes on
side A, louvre band on side B), CD_162_Rychly_Pershing, CD_163_Pershing and
CD_371_Bastard (small square windows instead of portholes). The paint is
either rules (Najbrt 2) or the layout of his sheet in that livery, every
colour of it mapped to a zone and recoloured from the shared ČD palette:

  najbrt2        rules, measured on the photos (362 039, 362 174): sky down to
                 the headlights (K 0-4), white band (K 5-6, ends K 5-7),
                 sapphire sill (K 7) and buffer beam, white windscreen frames,
                 the louvre band dark sky, a white ČD mark on the sides.
  najbrt1_2      his balkan sheet of the class: light grey cab ends and fronts,
                 a sapphire wedge behind each cab, sky between, dark grey sill.
  modrokremova   (362) his CD_362_Rychle_Eso: dark blue, cream band K 4-5.
  zelenokremova  (162) his CD_162: ČSD green, cream band.
  zelenozluta    (163) his CD_163: ČD green, yellow band, yellow windscreen
                 frames (163 068).
  cervenozluta   (371) his CD_371: red, yellow line, cream band, red sill
                 (371 005 "Pepin").

Every livery gets the E3 roof: TommPa9's grey roof and equipment with a dark
gutter where the roof meets the side, grey pantographs on the Najbrt schemes
(his yellow ones on the older schemes). Face shading follows his palette steps
(handpaint.FACT).
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, "src", "tommpa9_eso")
FAM = os.path.join(REPO, "vehicle-rail", "ceske-drahy")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "railrender"))
from handpaint import HandBase, T, hexarr, load, lum, save, scale, shade, template_zones, unspecial  # noqa: E402
import cd_loco_livery as CL  # noqa: E402

REFS = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".png"))
BASE = {"362": "CD_362_Rychle_Eso", "162": "CD_162_Rychly_Pershing",
        "163": "CD_163_Pershing", "371": "CD_371_Bastard"}
BALKAN = {"362": "CD_362_Rychle_Eso_(balkan)", "162": "CD_162_Rychly_Pershing_(balkan)",
          "163": "CD_163_Pershing_(balkan)", "371": "CD_371_Bastard_(balkan)"}

# ---------------------------------------------------------------- colours
SKY, WHITE, SAPPHIRE, LGREY = CL.LOCO_SKY, CL.WHITE, CL.SAPPHIRE, CL.LGREY
SILL_GREY = (58, 61, 64)            # Najbrt 1.2 sill and buffer beam
LOUVRE_GREY = (164, 168, 170)       # aluminium louvre band of the older schemes
GUTTER = (0x3A, 0x3A, 0x3A)         # where the roof meets the side (E3)
PANTO_GREY = (0x84, 0x84, 0x84)
GREEN = (44, 110, 62)               # ČSD green (162 green-cream)
N2_LOUVRE = (37, 91, 132)           # the louvre band on Najbrt 2: sky x 0.62

# his colours, every view's shade of one paint (pure / lit / shaded)
GREYS_LOUVRE = (0xA5A5A5, 0xADADAD, 0x9C9C9C)
CMAP = {
    "balkan": {**{h: "sky" for h in (0x0063C5, 0x1073E6, 0x004A9C)},
               **{h: "cab" for h in (0xB5BDC5, 0xD6DEE6, 0x8C949C)},
               **{h: "navy" for h in (0x001942, 0x102152, 0x001031, 0x001029, 0x003173, 0x00295A, 0x103A8C)},
               **{h: "sill" for h in (0x3A3A3A, 0x313131, 0x424242)},
               **{h: "louvre" for h in (0x0052B5, 0x086BD6, 0x00428C)}},
    "CD_362_Rychle_Eso": {**{h: "body" for h in (0x003A73, 0x00428C, 0x00316B)},
                          **{h: "stripe" for h in (0xF7E68C, 0xF7EF9C, 0xF7E684)},
                          **{h: "louvre" for h in GREYS_LOUVRE}},
    "CD_162_Rychly_Pershing": {**{h: "body" for h in (0x005200, 0x006B00, 0x004200)},
                               **{h: "stripe" for h in (0xF7E68C, 0xF7EF9C, 0xF7E684)},
                               **{h: "louvre" for h in GREYS_LOUVRE}},
    "CD_163_Pershing": {**{h: "body" for h in (0x005200, 0x006B00, 0x004200)},
                        **{h: "stripe" for h in (0xE6B500, 0xEFBD00, 0xD6AD00)},
                        **{h: "louvre" for h in GREYS_LOUVRE}},
    "CD_371_Bastard": {**{h: "body" for h in (0xB53A00, 0xC54200, 0x9C3100)},
                       **{h: "band" for h in (0xC5C58C, 0xCECEA5, 0xBDBD7B)},
                       **{h: "stripe" for h in (0xF7F700, 0xFFFF00, 0xEFEF00)},
                       **{h: "louvre" for h in GREYS_LOUVRE}},
    "CSD_ES_499.1_Eso": {**{h: "body" for h in (0x0829AD, 0x0831CE, 0x08218C)},
                         **{h: "stripe" for h in (0xEFDE00, 0xFFEF00, 0xE6D600)},
                         **{h: "louvre" for h in GREYS_LOUVRE}},
    "ZSSK_361.1_Pershing": {**{h: "body" for h in (0xAD0000, 0xBD0000, 0x9C0000)},
                            **{h: "band" for h in (0xE6E6E6, 0xEFEFEF, 0xDEDEDE)},
                            **{h: "frame" for h in (0xA5A5A5, 0xB5B5B5)},
                            **{h: "louvre" for h in (0x840000,)}},
}


class Livery:
    """zones: zone -> albedo. The zone of a face pixel comes from `rules`
    (callable(face, K, U, view) -> zone name; Najbrt 2 by default) or from `template`
    (one of his sheets, CMAP). frames / beam: windscreen frame and buffer beam
    colour or None (keep the drawing); logo: white side mark (Najbrt 2); panto:
    pantograph colour or None (his); roof: roof colour or None (his grey);
    gutter: the roof edge along the sides; extra: callable(hb, put,
    zone_colour) drawn last (lettering); drop_marks: paint over his red side
    marks and plates (set by logo)."""

    def __init__(self, zones, template=None, frames=None, beam=None, logo=False, panto=PANTO_GREY,
                 rules=None, roof=None, gutter=GUTTER, extra=None, drop_marks=False):
        self.zones, self.template = zones, template
        self.frames, self.beam, self.logo, self.panto = frames, beam, logo, panto
        self.rules = rules or (None if template else (lambda f, k, u, c: n2_zone(f, k)))
        self.roof, self.gutter, self.extra = roof, gutter, extra
        self.drop_marks = drop_marks or logo


def livery(fam, name):
    if name == "najbrt2":
        return Livery({"sky": SKY, "white": WHITE, "sapphire": SAPPHIRE, "louvre": N2_LOUVRE},
                      frames=WHITE, beam=SAPPHIRE, logo=True)
    if name == "najbrt1_2":
        return Livery({"sky": SKY, "cab": LGREY, "navy": SAPPHIRE, "sill": SILL_GREY,
                       "louvre": N2_LOUVRE}, template=BALKAN[fam], beam=SILL_GREY)
    if name == "modrokremova":
        return Livery({"body": CL.BC_BLUE, "stripe": CL.BC_CREAM, "louvre": LOUVRE_GREY},
                      template="CD_362_Rychle_Eso", panto=None)
    if name == "zelenokremova":
        return Livery({"body": GREEN, "stripe": CL.BC_CREAM, "louvre": LOUVRE_GREY},
                      template="CD_162_Rychly_Pershing", panto=None)
    if name == "zelenozluta":
        return Livery({"body": CL.GY_GREEN, "stripe": CL.GY_YELLOW, "louvre": LOUVRE_GREY},
                      template="CD_163_Pershing", frames=CL.GY_YELLOW, panto=None)
    if name == "cervenozluta":
        return Livery({"body": CL.RY_RED, "band": CL.RC_CREAM, "stripe": CL.RY_YELLOW, "louvre": LOUVRE_GREY},
                      template="CD_371_Bastard", panto=None)
    raise ValueError(name)


JOBS = {
    "362": ["najbrt2", "najbrt1_2", "modrokremova"],
    "162": ["najbrt2", "najbrt1_2", "zelenokremova"],
    "163": ["najbrt2", "zelenozluta", "najbrt1_2"],
    "371": ["najbrt2", "najbrt1_2", "cervenozluta"],
}

# a base sheet's own CMAP lists its paint (the 371's lit yellow line 0xFFFF00 is
# paint on the walls; the same colour on the roof is a pantograph); every other
# pixel of it is one of his details and stays
PANTO_YELLOW = {0xFFFF00, 0xE6E600, 0xFFEF00}
RED_MARK, PLATE = 0xFF0000, 0xC5C5C5


def n2_zone(face, k):
    if face == "S":
        return "sky" if k <= 4 else ("white" if k <= 6 else "sapphire")
    return "sky" if k <= 4 else "white"


_bases = {}


def hand_base(name):
    """HandBase of one of his sheets, aligned with all 21 sheets of the body."""
    if name not in _bases:
        names = [name] + [n for n in REFS if n != name]
        _bases[name] = HandBase([load(os.path.join(SRC, n + ".png")) for n in names], 0,
                                {3: 83, 7: 83}, {1: 81, 5: 89}, 8, 8)
    return _bases[name]


def paint(fam, name):
    return paint_livery(BASE[fam], livery(fam, name))


def paint_livery(base_name, L):
    hb = hand_base(base_name)
    own = CMAP[base_name]
    v = hexarr(hb.base)
    out = hb.base.copy()
    painted = np.zeros(hb.solid.shape, bool)
    zones = None
    if L.template:
        zones = template_zones(hb, load(os.path.join(SRC, L.template + ".png")),
                               CMAP["balkan" if "balkan" in L.template else L.template])

    def put(y, x, c, face=None):
        out[y, x] = shade(c, hb.factor(y, x, face))
        painted[y, x] = True

    def zone_colour(y, x):
        if zones is None:
            return L.zones[L.rules(hb.face[y, x], hb.K[y, x], hb.U[y, x], hb.col[y, x])]
        z = zones[y, x]
        return L.zones.get(z) if z else None

    for y, x in zip(*np.where(hb.solid)):
        f, k, hv = hb.face[y, x], hb.K[y, x], v[y, x]
        if f == "R":
            if hv in PANTO_YELLOW and L.panto is not None:
                out[y, x] = L.panto
                painted[y, x] = True
            elif hv == 0x848484 and k >= -2:
                out[y, x] = L.gutter
                painted[y, x] = True
            elif L.roof is not None and lum(hb.base[y, x]) >= 30:
                out[y, x] = shade(L.roof, min(1.4, max(0.6, lum(hb.base[y, x]) / 66.0)))
                painted[y, x] = True
            continue
        if f not in ("S", "E"):
            continue
        zb = own.get(hv)
        if zb == "louvre" and f == "S":
            put(y, x, L.zones["louvre"])
        elif (zb is not None and zb != "louvre") or (L.drop_marks and hv in (RED_MARK, PLATE)):
            c = zone_colour(y, x)
            if c is not None:
                put(y, x, c)
    # buffer beam: the row under each end face (his near-black, not the buffers)
    if L.beam is not None:
        for c in range(8):
            ends = hb.end_columns(c)
            for x in ends:
                X = c * 128 + x
                for y in np.where((hb.face[:, X] == "U") & (hb.K[:, X] == 8))[0]:
                    if v[y, X] == 0x101010:
                        put(y, X, L.beam, face="E")
    # windscreen frames: face pixels beside the glass, rows 1-3
    if L.frames is not None:
        glass = v == 0x6B6B6B
        for y, x in zip(*np.where((hb.face == "E") & (hb.K >= 1) & (hb.K <= 3))):
            if glass[y, x] or not painted[y, x]:
                continue
            if any(glass[y, xx] for xx in (x - 1, x + 1) if xx // 128 == x // 128):
                put(y, x, L.frames)
    # Najbrt 2: the side logo is a 3-px white mark on the sky, not his red one
    if L.logo:
        for c in range(8):
            X0 = c * 128
            xs = sorted(set(np.where((v[:, X0:X0 + 128] == RED_MARK) & (hb.face[:, X0:X0 + 128] == "S"))[1].tolist()))
            for x in xs:
                for y in np.where((hb.face[:, X0 + x] == "S") & (hb.K[:, X0 + x] == 3))[0]:
                    put(y, X0 + x, WHITE)
    if L.extra is not None:
        L.extra(hb, put, zone_colour)
    return unspecial(out, painted)


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    for fam in (args or list(JOBS)):
        for name in JOBS[fam]:
            a = paint(fam, name)
            path = os.path.join(FAM, fam, "sprites", f"{name}.png")
            save(a, path)
            print("wrote", os.path.relpath(path, REPO))
            if prev:
                g = a.astype(np.uint8).copy()
                g[np.all(g == T, axis=2)] = (104, 124, 76)
                Image.fromarray(g).resize((3072, 384), Image.NEAREST).save(os.path.join(prev, f"{fam}_{name}.png"))


if __name__ == "__main__":
    main()
