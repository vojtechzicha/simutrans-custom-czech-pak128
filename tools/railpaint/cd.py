#!/usr/bin/env python3
"""Regenerate every painted ČD rail sheet (the DMUs and EMUs of
VZ-CeskeDrahy-rail) by running the family painters in this folder.

    python tools/railpaint/cd.py                   # every painted ČD family
    python tools/railpaint/cd.py 810 471 650_2     # only these family dirs
    python tools/railpaint/cd.py --preview DIR     # also write previews to DIR/<painter>/

Each painter runs in its own process: paint.py caches per-body shading by body
name, so painters must not share one interpreter. Writes
vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png; a clean run leaves
`git status` unchanged.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# painter module -> the family dirs it writes (single-family painters take no
# family arguments)
PAINTERS = {
    "cd_sukafon": ["809", "810", "811"],
    "cd_rs1": ["840", "841", "841_2", "841_3"],
    "cd_84x_85x": ["842", "843", "854"],
    "cd_pesa": ["844", "847"],
    "cd_642_848": ["642", "848"],
    "cd_814": ["814_0", "814_2"],
    "cd_471": ["471"],
    "cd_680": ["680"],
    "cd_emu": ["440", "640", "640_1", "640_2", "650", "650_2", "690_2", "530", "550",
               "660_0", "660_1"],
}
SINGLE = {"cd_471", "cd_680"}


def main():
    args = sys.argv[1:]
    prev = None
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
    known = {f for fams in PAINTERS.values() for f in fams}
    unknown = [f for f in args if f not in known]
    if unknown:
        sys.exit(f"unknown family dir(s): {', '.join(unknown)} (painted: {', '.join(sorted(known))})")
    failed = []
    for mod, fams in PAINTERS.items():
        want = [f for f in fams if f in args] if args else fams
        if not want:
            continue
        cmd = [sys.executable, os.path.join(HERE, mod + ".py")]
        if mod not in SINGLE and args:
            cmd += want
        if prev:
            d = os.path.join(prev, mod)
            os.makedirs(d, exist_ok=True)
            cmd += ["--preview", d]
        print(f"== {mod}: {' '.join(want)}", flush=True)
        if subprocess.run(cmd).returncode:
            failed.append(mod)
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
