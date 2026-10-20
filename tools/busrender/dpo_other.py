"""DP Ostrava buses and trolleybuses outside the Solaris family: generate the
sheets.

  bus/dpo/ekovaelectron12    Ekova Electron 12 (5005-5007), rendered on the
                             dpmhk.py body (dpo_other_bodies.py)
  bus/dpo/sor_ebn105         SOR EBN 10.5 (5001-5004), rendered on the dpmhk.py
                             SOR EBN body, 10.37 m (dpo_other_bodies.py)
  bus/dpo/dekstrale37        Iveco-Dekstra LE 37 (7304-7310) and
  bus/dpo/roserofirst        Rosero First FCLEI CNG (7311-7312): VTPsim's LE 37
                             art from the Prague package, repainted in DPO
                             turquoise (dpo_other_rebase.py)
  bus/dpo/scaniaunviurbisdd  Unvi Urbis DD (7991-7992): patched
  trolleybus/dpo/21tr        Skoda 21Tr: patched
  trolleybus/dpo/36trsolaris Skoda 36Tr (Temsa): patched
  trolleybus/dpo/sor_tnb_12  SOR TNB 12 (3912): patched (dpo_other_patch.py)

The patched and re-based sheets start from frozen copies in
tools/busrender/src/dpo/ (the sheets as they were, and the two Prague sheets),
so a run reproduces the PNGs byte for byte. Every sheet ends at the lane
position dpo_lane.py gives it (front where a native 12 m bus has its front),
so `dpo_lane.py --dry-run` reports them "ok". Trolley poles are aimed at the
wires of dpmhk.py.

usage: python tools/busrender/dpo_other.py [family ...] [--preview DIR]
       [--variant ekova=B] [--variant ebn=B]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dpo_otherkit as K                      # noqa: E402
import dpo_other_bodies as B                  # noqa: E402
import dpo_other_patch as PT                  # noqa: E402
import dpo_other_rebase as RB                 # noqa: E402

REPO = K.REPO
SRC = K.SRC

# the variants put to the owner; the first one is committed
VARIANTS = {
    "ekova": {"A": (B.Ekova, B.EKOVA_A), "B": (B.Ekova, B.EKOVA_B)},
    "ebn": {"A": (B.Ebn105, B.EBN_A), "B": (B.Ebn105, B.EBN_B)},
}


def render_body(key, var):
    cls, sp = VARIANTS[key][var]
    return B.build(cls, sp)


def from_src(name, fn):
    return lambda var=None: fn(K.load(os.path.join(SRC, name)))


# family dir -> (livery colour, builder, variant key or None, has poles)
FAMILIES = {
    "vehicle-bus/dpo/ekovaelectron12": ("dpotyrkysova", lambda var: render_body("ekova", var), "ekova", False),
    "vehicle-bus/dpo/sor_ebn105": ("dpomodrozluta", lambda var: render_body("ebn", var), "ebn", False),
    "vehicle-bus/dpo/dekstrale37": ("dpotyrkysova", from_src("vtpsim-stratos_le_37.png", RB.dekstra), None, False),
    "vehicle-bus/dpo/roserofirst": ("dpotyrkysova", from_src("vtpsim-stratos_le_37.png", RB.rosero), None, False),
    "vehicle-bus/dpo/scaniaunviurbisdd": ("dpotyrkysova",
                                          from_src("scaniaunviurbisdd-dpotyrkysova.png", PT.patch_urbis), None, False),
    "vehicle-trolleybus/dpo/21tr": ("dpomodrozluta", from_src("21tr-dpomodrozluta.png", PT.patch_21tr), None, True),
    "vehicle-trolleybus/dpo/36trsolaris": ("dpotyrkysova",
                                           from_src("36trsolaris-dpotyrkysova.png", PT.patch_36tr), None, True),
    "vehicle-trolleybus/dpo/sor_tnb_12": ("bilamodrastrecha",
                                          from_src("sor_tnb_12-bilamodrastrecha.png", PT.patch_tnb), None, True),
}


def generate(fam, var=None):
    color, builder, key, poles = FAMILIES[fam]
    rows = builder(var or "A")
    rows, shifts = K.lane(rows)
    if poles and any(s != (0, 0) for s in shifts):
        # the poles are aimed on the frozen footprint; a trolleybus must not move
        raise SystemExit(f"{fam}: unexpected lane shift {shifts}")
    return color, rows


def main():
    args = sys.argv[1:]
    pv = None
    if "--preview" in args:
        i = args.index("--preview")
        pv = args[i + 1]
        del args[i:i + 2]
        os.makedirs(pv, exist_ok=True)
    chosen = {}
    while "--variant" in args:
        i = args.index("--variant")
        k, v = args[i + 1].split("=")
        chosen[k] = v
        del args[i:i + 2]
    for fam in FAMILIES:
        name = fam.split("/")[-1]
        if args and name not in args:
            continue
        color, builder, key, poles = FAMILIES[fam]
        color, rows = generate(fam, chosen.get(key))
        path = os.path.join(REPO, *fam.split("/"), "sprites", color + ".png")
        K.save(rows, path)
        print(f"{fam}/sprites/{color}.png")
        if pv:
            labels, rl = [name], [rows[0]]
            if key:
                for var in sorted(VARIANTS[key]):
                    _, vr = generate(fam, var)
                    rl.append(vr[0]); labels.append(f"variant {var}")
            K.preview(os.path.join(pv, f"{name}-{color}.png"), rl, labels)


if __name__ == "__main__":
    main()
