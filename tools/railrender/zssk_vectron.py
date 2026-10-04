#!/usr/bin/env python3
"""ZSSK Siemens Vectron MS (RS Lease 6193 025 / 032, 7193 131-135 / 141-145)
in the "Držíme Slovensko v pohybe" livery: the Leo Express Vectron model
(vectron.py, geometry shared, not edited), painted through ops_vectron.py's
lettering helpers.

    python tools/railrender/zssk_vectron.py [--variant A|B|C] [--preview DIR]

writes vehicle-rail/zssk/193/sprites/pohyb.png.

Livery (railpage.net photos of 6193 032 / 025, Bratislava Dec 2024): bright
ZSSK red body; black windscreen surround that wraps a little round the cab
corner, black cab roof caps, anthracite machine-room roof; red front below the
windscreen with the black "whiskers" panel between the headlights;
anthracite underframe band and lower front. Machine-room side: white
"DRŽÍME SLOVENSKO / V POHYBE" behind the cab-1 door, a bundle of thin white
wave lines rising from the door towards the white ZSSK ring logo at about
two thirds of the length. The same layout as seen on both sides.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM = os.path.join(REPO, "vehicle-rail", "zssk", "193")

import numpy as np  # noqa: E402
import railkit as R  # noqa: E402
from railkit import Paint  # noqa: E402
from render import DIRS  # noqa: E402
import vectron as V  # noqa: E402
import ops_vectron as O  # noqa: E402

L, ZS = V.L, V.ZS
Z_LOW = O.Z_LOW
Z_FRONT_LOW = O.Z_FRONT_LOW
CAB_ROOF = O.CAB_ROOF
DOOR = O.DOOR

RED = 0xD81E2A
DOOR_RED = 0xCC1C27
BLACK = 0x1F2124
ROOF = 0x3A3D42
ROOF_TOP = 0x464A50
LOW = 0x35383C
FRONT_LOW = 0x2A2C30
WHITE = (0xF4, 0xF2, 0xF2)

# side artwork, x = cu from the LEFT end as seen, z = model px
LOGO = (6.75, 8.6, 1.7)       # ZSSK ring: centre x, centre z, radius (z units)

VARIANT = "B"   # chosen by the user 2026-10-04 (A and C kept for --variant previews)


def _wave_base(t):
    """Lowest line of the wave fan at t (0 = behind the cab-1 door, 1 = the
    cab-2 end): the lines leave one point low behind the door and fan out,
    rising to the logo and easing down towards cab 2 (photos)."""
    rise = np.sin(np.pi * min(1.0, t / 0.6) / 2) ** 2
    return 4.4 + 2.2 * rise - 0.9 * max(0.0, t - 0.6) / 0.4


def side_art(x, cu, z):
    """Variants: A = wave fan + logo + slogan strokes, B = wave fan + logo,
    C = the fan filled pale red between its white edge lines + logo + slogan."""
    body = O.rgb(RED)
    if cu < 1.9:
        return None
    lx, lz, r = LOGO
    dx, dz = (x - lx) * 4.0, z - lz          # 1 cu = 4 model px across
    rr = np.hypot(dx, dz)
    if rr <= r:
        return WHITE if rr >= r * 0.45 else body       # ZSSK ring
    if VARIANT in ("A", "C"):
        # the slogan as two short white strokes (real lettering is ~1 px)
        if (2.3 <= x <= 5.0 and 9.6 <= z < 10.4) or (3.0 <= x <= 4.3 and 8.2 <= z < 9.0):
            return O.mix(body, WHITE, 0.8)
    t = (x - 1.95) / (L - 1.95 - 0.9)
    if not (0.0 <= t <= 1.0):
        return None
    if abs(dx) < r + 0.6 and abs(dz) < r + 0.6:
        return None                                     # red margin round the logo
    base = _wave_base(t)
    gap = 0.4 + 1.5 * min(1.0, t / 0.6)                 # the fan opens up
    n = 3
    if VARIANT == "C":
        top = base + (n - 1) * gap
        if base < z < top - 0.4:
            return O.mix(body, WHITE, 0.25)
    for k in range(n):
        zk = base + k * gap
        if zk - 0.4 <= z < zk + 0.4:
            return O.mix(body, WHITE, 0.9 if k != 1 else 0.7)
    return None


def body_paint(f, u, v, z, d, orig):
    cu = min(u, L - u)
    if f in ("+v", "-v"):
        if isinstance(orig, (int, tuple)):
            # vectron.py's cab side window (not on the real MS): paint it over
            if not (0.60 <= cu <= 1.20 and 7.9 <= z <= 10.7):
                return orig
        if z > ZS + 0.01:                                   # roof cap sides
            return Paint(BLACK) if cu < CAB_ROOF else Paint(ROOF)
        if z < Z_LOW:
            return Paint(LOW)
        if cu < 0.62 + (z - 8.4) * 0.12 and z >= 8.4:
            return Paint(BLACK)                             # mask wrap at the corner
        if DOOR[0] <= cu <= DOOR[1] and 3.2 <= z <= 10.8:
            return Paint(DOOR_RED)
        x = u if f == "-v" else L - u
        art = side_art(x, cu, z)
        return Paint(art) if art is not None else Paint(RED)
    if f == "+z":
        if isinstance(orig, (int, tuple)):
            return orig                                     # windscreen tops
        if z < ZS - 0.05:
            return Paint(BLACK) if z >= 7.4 else Paint(RED)  # sloped nose steps
        return Paint(BLACK) if cu < CAB_ROOF else Paint(ROOF, top=ROOF_TOP)
    # cab fronts
    if isinstance(orig, (int, tuple)):
        return orig                                         # windscreen, lamps
    if z < Z_FRONT_LOW:
        return Paint(FRONT_LOW)
    if z >= 7.4:
        return Paint(BLACK)                                 # windscreen surround
    if abs(v) < 0.40:
        return Paint(BLACK)                                 # the black "whiskers"
    return Paint(RED)


def build(liv="pohyb"):
    parts, lines = V.build("gmpbila")    # any ops_vectron table: every body face is repainted
    for p in parts:
        if getattr(p.mat, "__name__", "") in ("body_mat", "roof_mat"):
            p.mat = (lambda m: lambda f, u, v, z, d: body_paint(f, u, v, z, d, m(f, u, v, z, d)))(p.mat)
    return parts, lines


def rows_for(liv="pohyb"):
    """In the agreed 2026-09-26 style (style.py); main() runs style.polish()."""
    import restyle_kit as K
    parts, lines = build(liv)
    K.roof_restyle(parts, V.ZS, V.ZR)
    lines = K.restyle_lines(lines)
    return [[R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]]


def main():
    global VARIANT
    args = sys.argv[1:]
    prev = None
    out = os.path.join(FAM, "sprites", "pohyb.png")
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    if "--variant" in args:
        i = args.index("--variant")
        VARIANT = args[i + 1]
        del args[i:i + 2]
        if prev:
            out = os.path.join(prev, f"pohyb_{VARIANT}.png")
    rows = rows_for()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    import restyle_kit as K
    K.save_styled(rows, out)
    if prev:
        R.preview(rows, os.path.join(prev, f"vectron_pohyb_{VARIANT}_x4.png"), z=4, labels=["193 " + VARIANT])
    print("wrote", os.path.relpath(out, REPO))


if __name__ == "__main__":
    main()
