"""family.yaml of the ČD RegioPanter families and the JMK Moravia 530 / 550
(one generator so the Panter families stay uniform: roles, constraints, multi-
unit coupling, 680 kW per car).

  python tools/railpaint/cd_panter_yaml.py [family ...]      (default: all)

The yaml files in the repo are the source of truth for build.py; rerun this only
after changing FAM / the templates here, and review the diff.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAM_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "vehicle-rail", "ceske-drahy")

LIV = {
    "najbrt1_2": ("Najbrt 1.2", "Najbrt 1.2"),
    "najbrt2": ("Najbrt 2", "Najbrt 2"),
    "pidsedocervena": ("PID grey-red", "PID šedo-červená"),
    "plzenskykraj": ("Plzeňský kraj", "Plzeňský kraj"),
    "cdzelenomodrobila": ("ČD green-blue-white", "ČD zeleno-modro-bílá"),
    "jihomoravskykraj": ("Jihomoravský kraj", "Jihomoravský kraj"),
}

FAM = {
    "440": dict(
        ids=["440", "442", "441"], intro=(2012, 12), retire=(2022, 12), livs=["najbrt1_2", "najbrt2"],
        comment="""# Škoda 7Ev RegioPanter, 3-car 440 + 442 + 441, 3 kV DC only, 12 units built
# 2012–13 for Ústecký, Pardubický and Královéhradecký kraj. Historical: all 12
# were converted to dual-system class 640.1 in 2021–22 (see 640_1), so the class
# ends in 2022. Najbrt 1.2 on 440.001–009 / 011, Najbrt 2 on 440.010 / 012.
# Same drawing and sheets as 640.1."""),
    "640": dict(
        ids=["640", "642", "641"], intro=(2013, 6), retire=(2050, 12), livs=["najbrt1_2", "najbrt2"],
        comment="""# Škoda 7Ev RegioPanter, 3-car 640 + 642 + 641, 3 kV DC + 25 kV AC, 8 units
# (Olomoucký kraj 2013, Jihomoravský kraj 2014). Najbrt 1.2 on 640.001–003 as
# delivered, Najbrt 2 on 640.004–008."""),
    "640_1": dict(
        ids=["640.1", "642.1", "641.1"], intro=(2021, 7), retire=(2050, 12), livs=["najbrt1_2", "najbrt2"],
        comment="""# Class 640.1: the 12 former 440s after their dual-system conversion (2021–22),
# 3-car 640.1 + 642.1 + 641.1, since 2025 mostly in Pardubický kraj. They kept
# their paint: Najbrt 1.2 on 10 units, Najbrt 2 on 640.110 / 112."""),
    "640_2": dict(
        ids=["640.2", "642.2", "641.2"], intro=(2023, 6), retire=(2060, 12), livs=["najbrt2", "pidsedocervena"],
        comment="""# Škoda 20Ev RegioPanter (second generation), 3-car 640.2 + 642.2 + 641.2,
# dual-system, ETCS, 60 units delivered 2023–24. Najbrt 2 on 38 units (with small
# kraj logo decals), PID grey-red on the 22 Prague units 640.234–255 (1st class at
# both cab ends)."""),
    "650": dict(
        ids=["650", "651"], intro=(2012, 12), retire=(2050, 12), livs=["najbrt1_2", "najbrt2"],
        comment="""# Škoda 7Ev RegioPanter, 2-car 650 + 651, dual-system. 17 built; the 9 Plzeň
# units went to Arriva in Dec 2023 (vehicle-rail/arriva/650), ČD keeps
# 650.001–008: Najbrt 1.2 on 001–004, Najbrt 2 on 005–008."""),
    "650_2": dict(
        ids=["650.2", "651.2"], intro=(2021, 8), retire=(2060, 12), livs=["najbrt2", "plzenskykraj"],
        comment="""# Škoda 15Ev RegioPanter (second generation), 2-car 650.2 + 651.2, dual-system,
# ETCS, 46 units delivered 2021–24 (Jihočeský, Plzeňský, Karlovarský,
# Královéhradecký kraj, Vysočina, MSK, Ústecký kraj). Najbrt 2 on 33 units; the
# 13 Plzeň units (650.201, 202, 205–215) wear the Plzeňský kraj (IDPK) scheme,
# the same design as the Arriva 650 (vehicle-rail/arriva/650)."""),
    "690_2": dict(
        ids=["690.2", "691.2"], intro=(2024, 12), retire=(2060, 12), livs=["cdzelenomodrobila"],
        engine="Battery",
        comment="""# Škoda 15Ev3 battery RegioPanter, 2-car 690.2 + 691.2: the last 4 units of the
# 650.2 framework (690.247–250), fitted with traction batteries (>= 80 km off the
# wire at up to 120 km/h, 160 km/h under 3 kV / 25 kV). In service since
# 15 Dec 2024 on S8 Ostrava – Studénka – Veřovice (Moravskoslezský kraj). Their
# own ČD green-blue-white scheme: green cab halves, a loop-chain band, navy
# inner halves, Najbrt 2 lower body. The 15 new-generation 690.0 (3 doors per
# side) are not in passenger service yet (due by March 2027) and are not
# modelled. engine_type Battery: runs with or without catenary."""),
    "530": dict(
        ids=["530", "533", "532", "531"], intro=(2023, 1), retire=(2060, 12), livs=["jihomoravskykraj"],
        family=("Moravia", "Moravia"), payload=[93, 127, 118, 111],
        comment="""# Škoda 18Ev "Moravia", 4-car 530 + 533 + 532 + 531, 25 kV 50 Hz only, 31 units
# (2023) owned by Jihomoravský kraj and run by ČD under the IDS JMK contract
# (Dec 2024 – Dec 2034) on S2, S3, S9 and S51 around Brno. Second-generation
# RegioPanter body, 2nd class only (333 seats). JMK scheme: magenta roof band,
# cab corners and doors, white and black body, black blocks over the bogies.
# Pantographs on the two end cars (531 seen raised, 530 lowered)."""),
    "550": dict(
        ids=["550", "551"], intro=(2022, 9), retire=(2060, 12), livs=["jihomoravskykraj"],
        family=("Moravia", "Moravia"), payload=[92, 110],
        comment="""# Škoda 19Ev "Moravia", 2-car 550 + 551, 25 kV 50 Hz only, 6 units (from Sep
# 2022) owned by Jihomoravský kraj and run by ČD under the IDS JMK contract
# (Dec 2024 – Dec 2034). Second-generation RegioPanter body, 2nd class only
# (146 seats), same JMK scheme as the 530. Pantograph on the 550."""),
}

HEAD = """agency: CeskeDrahy
type: "{type}"
copyright: TommPa9

# Windows light up at night only while passengers are aboard.
windows_lit_when_loaded: true

display:
  agency_en: "ČD"
  agency_cs: "ČD"
  family_en: "{fam_en}"
  family_cs: "{fam_cs}"

{comment}
# Every car has one powered bogie (2 x 340 kW); units of any livery couple end
# to end. Sources: TommPa9's RegioPanter drawing (pak128cs rail-psg
# mail/440_640_650, the same body as the pak128_czr sheets), repainted per livery.
# Sprite rows: {rows}.

vehicles:
"""

CAR = """  - id: "{id}"
    role_en: "{role_en}"
    role_cs: "{role_cs}"
    row: {row}
    head: {head}
    tail: {tail}
    prev: [{prev}]
    next: [{next}]
{couple}    fields:
      cost: {cost}
      payload: {payload}
      speed: 160
      weight: {weight}
      runningcost: {rc}
      fixed_cost: {fc}
      intro_year: {iy}
      intro_month: {im}
      retire_year: {ry}
      retire_month: {rm}
      waytype: track
      freight: Passagiere
      length: 13
      engine_type: {engine}
      power: 680
      gear: 180
    extended:
      axles: 4

"""


def q(ids):
    return ", ".join(f'"{i}"' for i in ids)


def render(fam):
    """-> the family.yaml text of one family dir."""
    f = FAM[fam]
    ids = f["ids"]
    typ = ids[0]
    rows = ", ".join(f"row {r} = {i}" for r, i in enumerate(ids))
    fam_en, fam_cs = f.get("family", ("RegioPanter", "RegioPanter"))
    out = HEAD.format(type=typ, comment=f["comment"], rows=rows, fam_en=fam_en, fam_cs=fam_cs)
    lead, rear = ids[0], ids[-1]
    for r, i in enumerate(ids):
        if r == 0:
            role = ("front motor car", "přední motorový vůz")
            head, tail, prev, nxt = "true", "false", [rear], [ids[1]]
            couple = "    couple_liveries: prev\n"
            payload, weight, rc, fc = 110, 53, 60, 614
        elif r == len(ids) - 1:
            role = ("rear motor car", "zadní motorový vůz")
            head, tail, prev, nxt = "false", "true", [ids[r - 1]], [lead]
            couple = "    couple_liveries: next\n"
            payload, weight, rc, fc = 110, 53, 50, 520
        else:
            role = ("middle motor car", "vložený motorový vůz")
            head, tail, prev, nxt = "false", "false", [ids[r - 1]], [ids[r + 1]]
            couple = ""
            payload, weight, rc, fc = 136, 54, 45, 420
        if "payload" in f:
            payload = f["payload"][r]
        out += CAR.format(id=i, role_en=role[0], role_cs=role[1], row=r, head=head, tail=tail,
                          prev=q(prev), next=q(nxt), couple=couple, cost=18384000, payload=payload,
                          weight=weight, rc=rc, fc=fc, iy=f["intro"][0], im=f["intro"][1],
                          ry=f["retire"][0], rm=f["retire"][1], engine=f.get("engine", "Electric"))
    out += "liveries:\n"
    for lv in f["livs"]:
        en, cs = LIV[lv]
        out += f'  - color: {lv}\n    name_en: "{en}"\n    name_cs: "{cs}"\n'
    return out


def main():
    only = sys.argv[1:]
    for fam in FAM:
        if only and fam not in only:
            continue
        p = os.path.join(FAM_DIR, fam, "family.yaml")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8", newline="\n").write(render(fam))
        print("wrote", os.path.relpath(p, os.path.dirname(os.path.dirname(HERE))))


if __name__ == "__main__":
    main()
