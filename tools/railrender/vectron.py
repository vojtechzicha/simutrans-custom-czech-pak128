"""Siemens Vectron MS (Railpool class 193) for Leo Express.

Real: 18.98 m over buffers, 3.01 m wide, 4.25 m high, bogie centres 9.5 m.
Drawn as length 10 (pak128.cs draws its 19 m locos - 1216, 1116, ES64U2 - at 10).
u: 0 = front buffer face (cab 1), 10 = rear buffer face (cab 2).
z: model px above rail (coach roof edge = 10, 1 px ~ 0.375 m).

Liveries (photos in research/photos/vectron):
  bilooranzova : 7193 226 only - near-white/pale silver body, orange cab roof
                 caps + curved band down each cab side edge, orange cab doors,
                 charcoal front mask, aluminium buffer beam, large dark
                 "leo express" logo (orange dots + slash) mid-body.
  railpool     : 7193 197/198/227/228/231/232 - silver-grey, black front mask,
                 light-blue vertical band behind cab 2.
"""
import numpy as np
import railkit as R
from railkit import Paint, Part, Lit
from render import DIRS

L = 10.0
W = 0.92
ZB = 2.6          # body side bottom (silver skirt reaches low, photos)
ZS = 11.6         # side top (roof edge); natives draw locos ~2-3 px taller
                  # than coaches (CD 363 / 380 / 1216), so the Vectron does too
ZR = 12.4         # roof cap top
UB = 0.30         # buffer depth
UN = 0.46         # nose (lower front) face
UWT = 0.78        # windscreen top recedes to here
UCAB = 1.30       # end of cab section (side)

BLACKGREY = Paint(0x1E2022)
BOGIE = Paint(0x26282A)
BOGIE_HI = Paint(0x3C3F42)
ROOFEQ = Paint(0x4A5054, top=0x565C60)
ROOFEQ_DK = Paint(0x3A3F43, top=0x444A4E)
ALU = Paint(0xB8BCBE)
WS = (0x2A343D)
WS_HI = (0x4F6272)
DOORWIN = (0x2A343D)
PANTO = (0x8A2A22)       # red-brown pantograph frames (photo)
PANTO_DK = (0x5A5E62)
PANTO_HEAD = (0x2A2A2C)


def livery(name):
    if name == "bilooranzova":
        return dict(body=Paint(0xE3E6E7), roofcap=Paint(0xE8EAEB, top=0xD4D8DA),
                    orange=Paint(0xF26A0A, top=0xF47A20), mask=Paint(0x33383C),
                    lower=ALU, door=Paint(0xF06A0C), logo=Paint(0x2E3032),
                    band=None, cabroof=Paint(0xF26A0A, top=0xF47A20))
    return dict(body=Paint(0xA9AEB1), roofcap=Paint(0xA9AEB1, top=0x9EA3A6),
                orange=None, mask=Paint(0x222426), lower=Paint(0x8E9396),
                door=Paint(0xA3A8AB), logo=None, band=Paint(0x1E8FD8),
                cabroof=Paint(0xA9AEB1, top=0x9EA3A6))


def nose_u(z):
    """Front face position at height z (lower nose vertical, windscreen raked)."""
    if z < 7.4:
        return UN
    t = min(1.0, (z - 7.4) / (ZS - 7.4))
    return UN + (UWT - UN) * t


def build(liv):
    C = livery(liv)
    parts, lines = [], []
    own = "V"

    def cab_local(u):
        """distance into the cab from the nearer end, and which end."""
        return (u, "f") if u < L / 2 else (L - u, "r")

    def logo_px(u, z, side):
        # LE logo on the body side: dots + slash + two text rows, reading left
        # to right as seen. The -v side (seen with cab 1 on the left, Naumburg
        # photo) has it towards cab 2; the +v side is the 180 deg rotation.
        uu = u if side < 0 else L - u
        if not (5.0 <= uu <= 7.6 and 5.2 <= z <= 10.6):
            return None
        # three orange dots descending, then an orange slash
        dots = [(5.10, 9.9), (5.35, 9.0), (5.60, 8.1)]
        for (du, dz) in dots:
            if abs(uu - du) < 0.13 and abs(z - dz) < 0.45:
                return C["orange"]
        if 5.05 <= uu <= 5.65 and 5.4 <= z <= 7.4 and abs((uu - 5.05) - (7.4 - z) * 0.28) < 0.16:
            return C["orange"]
        # "leo" (upper row) and "express" (lower row): bold dark bars so the
        # two-line wordmark reads at 1x (single letters would alias to noise)
        if 5.95 <= uu <= 6.80 and 8.3 <= z <= 10.3:
            return C["logo"]
        if 5.95 <= uu <= 7.55 and 5.6 <= z <= 7.5:
            return C["logo"]
        return None

    def side(f, u, v, z, d):
        sgn = 1 if f == "+v" else -1
        cu, end = cab_local(u)
        # cab door just behind the cab (both ends, both sides)
        if 1.36 <= cu <= 1.80 and 3.2 <= z <= 10.8:
            if 7.4 <= z <= 10.2 and 1.44 <= cu <= 1.72:
                return DOORWIN
            return C["door"]
        # cab side window (small, behind the windscreen)
        if 0.62 <= cu <= 1.18 and 8.0 <= z <= 10.6:
            return WS_HI if z > 9.9 else WS
        if C["orange"] is not None:
            # orange cab roof cap (top of cab side) and the curved band that
            # follows the windscreen edge down to the headlight line
            if cu < UCAB and z >= 10.6:
                return C["orange"]
            if cu < 0.62 + (z - 5.6) * 0.06 and z >= 5.6:
                return C["orange"]
        if C["band"] is not None:
            # Railpool: light-blue band behind cab 2
            uu = u
            if 8.05 <= uu <= 8.70 and z >= ZB:
                return C["band"]
        if C["logo"] is not None:
            lp = logo_px(u, z, sgn)
            if lp is not None:
                return lp
        if z < ZB + 0.9:
            return C["lower"] if C["orange"] is not None else C["body"]
        return C["body"]

    def front_face(f, u, v, z, d, rear=False):
        # v > 0 is the loco's right; for the face at the front the viewer sees
        # it mirrored, irrelevant for this symmetric face.
        av = abs(v)
        if z >= ZS - 0.3:
            return C["cabroof"]
        if z >= 7.4:
            # windscreen framed by the mask
            if av < W - 0.16 and z < ZS - 0.7:
                return WS_HI if z > ZS - 1.6 and v > 0.1 else WS
            return C["mask"]
        if z >= 5.4:
            if av > 0.50 and z < 6.6 and av < W - 0.08:
                return R.TAIL if rear else R.HEAD
            if C["orange"] is not None and z < 5.9:
                return C["lower"]
            return C["mask"]
        return C["lower"] if C["orange"] is not None else C["mask"]

    def body_mat(f, u, v, z, d):
        if f == "+z" and z < ZS - 0.05:
            # tops of the stepped windscreen slabs read as the sloped screen
            return front_face(f, u, v, z, d, rear=(u > L / 2))
        if f == "+z":
            cu, _ = cab_local(u)
            return C["cabroof"] if cu < UCAB else ROOFEQ
        if f in ("+v", "-v"):
            return side(f, u, v, z, d)
        if f == "-u":
            return front_face(f, u, v, z, d, rear=False)
        return front_face(f, u, v, z, d, rear=True)

    # main body between the cabs (full height)
    parts.append(Part(UWT, L - UWT, -W, W, ZB, ZS, body_mat, own))
    # stepped nose slabs at both ends (lower nose vertical, windscreen raked)
    for z0 in np.arange(ZB, ZS, 0.5):
        z1 = min(ZS, z0 + 0.5)
        uf = nose_u((z0 + z1) / 2)
        taper = 0.10 if z0 >= 7.4 else 0.0
        parts.append(Part(uf, UWT, -W + taper, W - taper, z0, z1, body_mat, own))
        parts.append(Part(L - UWT, L - uf, -W + taper, W - taper, z0, z1, body_mat, own))
    # roof cap (inset) - cab caps take the cab roof colour
    def roof_mat(f, u, v, z, d):
        cu, _ = cab_local(u)
        if cu < UCAB:
            return C["cabroof"]
        return ROOFEQ if f == "+z" else ROOFEQ_DK
    parts.append(Part(UWT + 0.06, L - UWT - 0.06, -W + 0.18, W - 0.18, ZS, ZR, roof_mat, own))
    # roof equipment block between the pantographs
    parts.append(Part(3.2, 6.8, -0.50, 0.50, ZR, ZR + 0.7, lambda *a: ROOFEQ_DK, own))
    # underframe: bogies + equipment boxes
    for bc in (2.5, 7.5):
        parts.append(Part(bc - 1.25, bc + 1.25, -W + 0.10, W - 0.10, 0.0, ZB,
                          lambda f, u, v, z, d: BOGIE_HI if (f in ("+v", "-v") and 1.2 < z < 1.9) else BOGIE, own))
    parts.append(Part(3.8, 6.2, -W + 0.20, W - 0.20, 0.9, ZB, lambda *a: BLACKGREY, own))
    # buffer beams + buffers
    for (a, b) in ((UB, UN + 0.02), (L - UN - 0.02, L - UB)):
        parts.append(Part(a, b, -W + 0.05, W - 0.05, 1.6, ZB + 0.4,
                          lambda f, u, v, z, d: ALU if C["orange"] is not None else Paint(0x5A5E62), own))
    for (a, b) in ((0.0, UB), (L - UB, L)):
        for vc in (-0.62, 0.62):
            parts.append(Part(a, b, vc - 0.12, vc + 0.12, 2.3, 2.9, lambda *a: Paint(0x3A3D40), own))
    # pantographs: two per end; the rear-most one raised
    for (a, b) in ((1.75, 2.85), (7.15, 8.25)):
        parts.append(Part(a, b, -0.42, 0.42, ZR, ZR + 0.45, lambda *a: Paint(0x6E3028), own))
    lines += R.pantograph(7.55, ZR + 0.45, own, fold=-1, reach=0.9, height=5.2,
                          col=(0x70, 0x74, 0x78), head=PANTO_HEAD, half_head=0.62, thick=False)
    return parts, lines


def sheet(liv, out):
    parts, lines = build(liv)
    row = [R.vehicle_tile(parts, lines, d, 0.0, {"V"}) for d in DIRS]
    R.save_rows([row], out)
    return row


if __name__ == "__main__":
    import leo
    leo.main()
