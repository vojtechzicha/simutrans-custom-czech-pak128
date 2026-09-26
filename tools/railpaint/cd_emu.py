#!/usr/bin/env python3
"""Regenerate every painted ČD EMU sheet: the RegioPanter-bodied families
(cd_panter.py) and the InterPanter (interpanter.py).

    python tools/railpaint/cd_emu.py                    # all families
    python tools/railpaint/cd_emu.py 650_2 660_1        # only these family dirs
    python tools/railpaint/cd_emu.py --preview DIR      # also write 4x previews to DIR
    python tools/railpaint/cd_emu.py --yaml [family …]  # also rewrite the Panter
                                                        # family.yaml files (review the diff)

Writes vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png. Needs numpy and
Pillow. The sheets are zone-map repaints of TommPa9's upstream drawings (frozen
in src/); change the livery dicts / painters and regenerate instead of painting
the PNGs by hand.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

INTERPANTER = ("660_0", "660_1")


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
    yaml = "--yaml" in args
    args = [a for a in args if a != "--yaml"]
    import cd_panter
    import interpanter
    panter_fams = [f for f in args if f in cd_panter.FAMILIES] if args else list(cd_panter.FAMILIES)
    unknown = [f for f in args if f not in cd_panter.FAMILIES and f not in INTERPANTER]
    if unknown:
        sys.exit(f"unknown family dir(s): {', '.join(unknown)}")
    if panter_fams:
        cd_panter.run(panter_fams, prev)
        if yaml:
            import cd_panter_yaml
            sys.argv = [sys.argv[0]] + panter_fams
            cd_panter_yaml.main()
    if not args or any(f in INTERPANTER for f in args):
        interpanter.run(prev)


if __name__ == "__main__":
    main()
