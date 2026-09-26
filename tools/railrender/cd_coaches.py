#!/usr/bin/env python3
"""ČD loco-hauled coaches: sprite sheets and family.yaml of every coach family.

    python tools/railrender/cd_coaches.py                  # all families
    python tools/railrender/cd_coaches.py coach_obb        # only these family dirs
    python tools/railrender/cd_coaches.py --preview DIR    # also write 4x previews
    python tools/railrender/cd_coaches.py --yaml           # also rewrite family.yaml

Sheets: vehicle-rail/ceske-drahy/<family>/sprites/<livery>.png, rendered by
cdcoach.py from vagonWEB side drawings (change the model there and regenerate).
The ComfortJet family reuses the CZR ComfortJet / railjet art (Lubak91) frozen
in src/czr_cd_jets.png; its Afmpz 880 cab car is the CZR railjet Afmpz 890 cab
car and its BRmpz 882 the ARbmpz 892 without the 1st-class line.

family.yaml is generated from FAMILIES below (one generator keeps roles,
capacities and constraints uniform); review the diff after --yaml.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
FAM_DIR = os.path.join(REPO, "vehicle-rail", "ceske-drahy")

import cdcoach  # noqa: E402
import railkit as R  # noqa: E402
from render import T  # noqa: E402

LIV = {
    "najbrt2": ("Najbrt 2", "Najbrt 2"),
    "najbrt1": ("Najbrt 1", "Najbrt 1"),
    "najbrtbd2": ("Najbrt BD 2", "Najbrt BD 2"),
    "najbrtbd1": ("Najbrt BD 1", "Najbrt BD 1"),
    "obb": ("ÖBB grey-red", "ÖBB šedo-červená"),
    "comfortjet": ("ComfortJet", "ComfortJet"),
}

# roles: (en, cs)
ROLE = {
    "A": ("1st class compartment coach", "oddílový vůz 1. třídy"),
    "Ao": ("1st class open coach", "velkoprostorový vůz 1. třídy"),
    "AB": ("1st/2nd class compartment coach", "oddílový vůz 1./2. třídy"),
    "ABo": ("1st/2nd class open coach", "velkoprostorový vůz 1./2. třídy"),
    "B": ("2nd class compartment coach", "oddílový vůz 2. třídy"),
    "Bo": ("2nd class open coach", "velkoprostorový vůz 2. třídy"),
    "Bbike": ("2nd class coach with bicycle space", "vůz 2. třídy s prostorem pro kola"),
    "Bprm": ("2nd class coach for wheelchairs and bicycles", "vůz 2. třídy pro vozíčkáře a kola"),
    "Bkids": ("2nd class coach with children's compartment", "vůz 2. třídy s dětským oddílem"),
    "BD": ("2nd class coach with luggage room", "vůz 2. třídy se služebním oddílem"),
    "BDD": ("double-deck coach", "patrový vůz"),
    "Bcab": ("2nd class driving trailer", "řídicí vůz 2. třídy"),
    "ABcab": ("1st/2nd class driving trailer", "řídicí vůz 1./2. třídy"),
    "WR": ("restaurant car", "restaurační vůz"),
    "AR": ("1st class coach with bistro", "vůz 1. třídy s bistrem"),
    "WL": ("sleeping car", "lůžkový vůz"),
    "Bc": ("couchette car", "lehátkový vůz"),
    "BR": ("2nd class coach with restaurant", "vůz 2. třídy s restaurací"),
    "Bmid": ("2nd class coach", "vůz 2. třídy"),
    "Bend": ("2nd class end coach", "koncový vůz 2. třídy"),
    "Bmp": ("2nd class multi-purpose coach", "vůz 2. třídy s víceúčelovým prostorem"),
}

# code -> display id, role, payload, speed, weight t, (intro y, m), retire y or None
CARS = {
    "Ampz143": ("Ampz 143", "Ao", 58, 200, 48, (2006, 6), None),
    "Ampz146": ("Ampz 146", "Ao", 58, 200, 47, (1998, 9), None),
    "Bmz241": ("Bmz 241", "B", 66, 200, 47, (2006, 6), None),
    "Bmz245": ("Bmz 245", "B", 66, 200, 46, (1999, 9), None),
    "WRmz815": ("WRmz 815", "WR", 34, 200, 52, (1997, 6), None),
    "WLABmz826": ("WLABmz 826", "WL", 36, 200, 56, (2006, 12), None),
    "Bmz226": ("Bmz 226", "B", 66, 200, 46, (2016, 3), None),
    "Bmz232": ("Bmz 232", "B", 66, 200, 46, (2014, 6), None),
    "Bmz234": ("Bmz 234", "B", 66, 160, 45, (2017, 3), None),
    "Bmz235": ("Bmz 235", "B", 66, 200, 46, (2015, 6), None),
    "Bmz229": ("Bmz 229", "Bkids", 60, 200, 46, (2016, 6), None),
    "Bmz224": ("Bmz 224", "B", 60, 200, 46, (2019, 6), None),
    "Bdmz223": ("Bdmz 223", "Bbike", 60, 200, 46, (2019, 9), None),
    "Bdmpz227": ("Bdmpz 227", "Bbike", 72, 200, 46, (2016, 3), None),
    "Bhmpz228": ("Bhmpz 228", "Bprm", 58, 200, 47, (2016, 3), None),
    "ABmz346": ("ABmz 346", "AB", 60, 200, 46, (2016, 9), None),
    "Amz138": ("Amz 138", "A", 46, 200, 46, (2018, 6), None),
    "WRmz817": ("WRmz 817", "WR", 40, 200, 52, (2015, 6), None),
    "Bcmz834": ("Bcmz 834", "Bc", 60, 160, 47, (2016, 12), None),
    "Bbdgmee236": ("Bbdgmee 236", "Bprm", 41, 160, 46, (2012, 6), None),
    "Bdmpee233": ("Bdmpee 233", "Bo", 80, 160, 44, (2013, 6), None),
    "ARmpee829": ("ARmpee 829", "AR", 36, 160, 47, (2018, 6), None),
    "ARmpee832": ("ARmpee 832", "AR", 36, 160, 47, (2009, 12), None),
    "WLABmee823": ("WLABmee 823", "WL", 30, 160, 55, (2000, 12), None),
    "Bdmtee281": ("Bdmtee 281", "Bbike", 96, 160, 40, (1989, 6), 2035),
    "Bdmtee275": ("Bdmtee 275", "Bo", 96, 160, 40, (1990, 6), 2035),
    "Bdmtee267": ("Bdmtee 267", "Bo", 78, 160, 41, (2008, 6), 2040),
    "Aee140": ("Aee 140", "A", 54, 160, 41, (2000, 6), None),
    "Apee139": ("Apee 139", "Ao", 60, 160, 41, (2002, 6), None),
    "Bee238": ("Bee 238", "B", 60, 160, 41, (2001, 6), None),
    "Bpee237": ("Bpee 237", "Bo", 78, 160, 41, (2001, 6), None),
    "Aee145": ("Aee 145", "A", 54, 140, 39, (2004, 6), 2035),
    "AB349": ("AB 349", "AB", 64, 140, 38, (1979, 6), 2030),
    "Bee272": ("Bee 272", "Bo", 58, 140, 39, (1994, 6), 2032),
    "Bee273": ("Bee 273", "B", 53, 140, 39, (1994, 6), 2032),
    "Bd264": ("Bd 264", "Bbike", 72, 140, 38, (1999, 6), 2032),
    "BDs449": ("BDs 449", "BD", 40, 140, 38, (1981, 6), 2032),
    "Bdpee231": ("Bdpee 231", "Bbike", 72, 160, 40, (2015, 1), None),
    "ABpee347": ("ABpee 347", "ABo", 70, 140, 40, (2006, 6), 2040),
    "Bdtee276": ("Bdtee 276", "Bbike", 84, 140, 38, (2004, 6), 2035),
    "Bdt279": ("Bdt 279", "Bbike", 88, 120, 37, (1992, 6), 2030),
    "Bdt280": ("Bdt 280", "Bo", 88, 120, 37, (1992, 6), 2030),
    "Bfhpvee295": ("Bfhpvee 295", "Bcab", 58, 140, 42, (2007, 6), None),
    "ABfhpvee395": ("ABfhpvee 395", "ABcab", 50, 140, 42, (2007, 6), None),
    "Bdmteeo294": ("Bdmteeo 294", "BDD", 126, 100, 50, (1995, 6), 2030),
    "Bdmteeo296": ("Bdmteeo 296", "BDD", 128, 100, 50, (1995, 6), 2030),
    "ABfbdmteeo396": ("ABfbdmteeo 396", "ABcab", 81, 160, 56, (2021, 6), None),
    "Bdmteeo297": ("Bdmteeo 297", "BDD", 112, 160, 52, (2021, 6), None),
    "Bdmteeo298": ("Bdmteeo 298", "Bmp", 112, 160, 52, (2021, 6), None),
}


def cost_of(code):
    _, role, pay, speed, _, (y, _), _ = CARS[code]
    base = 2300000 if speed >= 200 else (1500000 if speed >= 160 else 950000)
    if role in ("A", "Ao", "AR", "WL", "WR"):
        base = int(base * 1.2)
    if CARS[code][1] in ("Bcab", "ABcab"):
        base = int(base * 1.5)
    return base


# family dir -> dict(type, family names, comment, vehicles: [(id, code, cab, liveries)])
N2 = ["najbrt2"]
FAMILIES = {
    "coach_uicz": dict(type="UICZ", en="UIC-Z", cs="UIC-Z", cars=[
        ("Ampz143", "Ampz143", None, N2), ("Ampz146", "Ampz146", None, N2),
        ("Bmz241", "Bmz241", None, N2), ("Bmz245", "Bmz245", None, N2),
        ("WRmz815", "WRmz815", None, N2), ("WLABmz826", "WLABmz826", None, N2)],
        comment="""# ČD UIC-Z 26.4 m coaches built for ČD by Siemens / SGP (1997-2007): the EC/IC
# stock of the Silesia, Ostravan, Valašský expres, Jan Perner and night trains."""),
    "coach_obb": dict(type="exOBB", en="ex-ÖBB", cs="ex-ÖBB", cars=[
        ("Bmz226", "Bmz226", None, N2), ("Bmz232", "Bmz232", None, ["najbrt2", "obb"]),
        ("Bmz234", "Bmz234", None, N2), ("Bmz235", "Bmz235", None, N2),
        ("Bmz229", "Bmz229", None, N2), ("Bmz224", "Bmz224", None, N2),
        ("Bdmz223", "Bdmz223", None, N2), ("Bdmpz227", "Bdmpz227", None, N2),
        ("Bhmpz228", "Bhmpz228", None, N2), ("ABmz346", "ABmz346", None, N2),
        ("Amz138", "Amz138", None, N2), ("WRmz817", "WRmz817", None, N2),
        ("Bcmz834", "Bcmz834", None, N2)],
        comment="""# Ex-ÖBB Eurofima / Z1 UIC-Z 26.4 m coaches bought by ČD 2014-2019, many rebuilt
# by Pars nova / DPOV. The bodies are the same; the window frames tell them apart
# (vagonWEB variants: white -br, black -cr, blue -mr), plus roof equipment and
# pictograms. Four Bmz 232 still wear the ÖBB grey-red (livery obb)."""),
    "coach_bautzen": dict(type="Bautzen", en="Bautzen", cs="Bautzen", cars=[
        ("Bbdgmee236", "Bbdgmee236", None, N2), ("Bdmpee233", "Bdmpee233", None, N2),
        ("ARmpee829", "ARmpee829", None, N2), ("ARmpee832", "ARmpee832", None, N2),
        ("WLABmee823", "WLABmee823", None, N2)],
        comment="""# Ex-DR Bautzen UIC-Z/X 26.4 m coaches rebuilt with AC (ŽOS, MOVO, Pars nova, DPOV):
# the Bbdgmee 236 bike / wheelchair car of almost every Ex and R train, the open
# Bdmpee 233, the 1st class + bistro ARmpee 829 / 832 and the WLABmee 823 sleeper."""),
    "coach_honecker": dict(type="Honecker", en="honecker", cs="honecker", cars=[
        ("Bdmtee281", "Bdmtee281", None, N2), ("Bdmtee275", "Bdmtee275", None, N2),
        ("Bdmtee267", "Bdmtee267", None, N2)],
        comment="""# "Honecker" UIC-X 26.4 m open coaches (Bautzen 1989-90), doors at 1/4 and 3/4 of
# the length: Bdmtee 281 (two bike areas), 275 (one rebuilt into a service
# compartment) and the refurbished 263 / 265-268 with fixed windows (as 267)."""),
    "coach_uicy": dict(type="UICY", en="UIC-Y", cs="UIC-Y", cars=[
        ("Aee140", "Aee140", None, N2), ("Apee139", "Apee139", None, N2),
        ("Bee238", "Bee238", None, N2), ("Bpee237", "Bpee237", None, N2)],
        comment="""# UIC-Y 24.5 m coaches with Hungarian (RÁBA Győr) bodies, rebuilt with AC by DVJ
# Dunakeszi / MOVO / ŽOS Trnava: R10, R11, R16, R17."""),
    "coach_y70": dict(type="Y70", en="Y/B 70", cs="Y/B 70", cars=[
        ("Aee145", "Aee145", None, N2), ("AB349", "AB349", None, N2),
        ("Bee272", "Bee272", None, N2), ("Bee273", "Bee273", None, N2),
        ("Bd264", "Bd264", None, N2),
        ("BDs449", "BDs449", None, ["najbrt2", "najbrtbd2", "najbrtbd1"])],
        comment="""# Bautzen Y/B 70 UIC-Y 24.5 m coaches (1970s-80s): R9 Vysočina, R12, R20 and
# regional trains. BDs 449 runs in plain Najbrt 2 and in the BD scheme (blue lower
# body as well), with a blue (BD 2) or grey (BD 1) roof."""),
    "coach_studenka": dict(type="Studenka", en="Studénka", cs="Studénka", cars=[
        ("Bdpee231", "Bdpee231", None, N2), ("ABpee347", "ABpee347", None, N2),
        ("Bdtee276", "Bdtee276", None, N2), ("Bdt279", "Bdt279", None, ["najbrt2", "najbrt1"]),
        ("Bdt280", "Bdt280", None, ["najbrt2", "najbrt1"]),
        ("Bfhpvee295-front", "Bfhpvee295", "front", ["najbrt2", "najbrt1"]),
        ("Bfhpvee295-rear", "Bfhpvee295", "rear", ["najbrt2", "najbrt1"]),
        ("ABfhpvee395-front", "ABfhpvee395", "front", ["najbrt1"]),
        ("ABfhpvee395-rear", "ABfhpvee395", "rear", ["najbrt1"])],
        comment="""# Vagónka Studénka UIC-Y 24.5 m coaches: the Bdpee 231 panorama-window saloon
# (ex Bp 282), ABpee 347, Bdtee 276, the Bdt 279 / 280 and the "sysel" driving
# trailers Bfhpvee 295 / ABfhpvee 395. A driving trailer comes twice: -front
# with the cab leading (the locomotive pushes at the rear) and -rear with the cab
# at the tail of a hauled train; the cab end takes nothing beyond it."""),
    "coach_patrove": dict(type="Patrove", en="double-deck", cs="patrový", cars=[
        ("Bdmteeo294", "Bdmteeo294", None, N2), ("Bdmteeo296", "Bdmteeo296", None, N2)],
        comment="""# Görlitz DDm double-deck coaches (26.8 m, 100 km/h): Bdmteeo 294 (bike area) and
# 296, Prague and České Budějovice regional sets."""),
    "13ev": dict(type="13Ev", en="Škoda 13Ev", cs="Škoda 13Ev", cars=[
        ("ABfbdmteeo396-front", "ABfbdmteeo396", "front", N2),
        ("ABfbdmteeo396-rear", "ABfbdmteeo396", "rear", N2),
        ("Bdmteeo297", "Bdmteeo297", None, N2), ("Bdmteeo298", "Bdmteeo298", None, N2)],
        comment="""# Škoda Vagonka 13Ev double-deck push-pull sets (2020-21), ABfbdmteeo 396 driving
# trailer + Bdmteeo 297 + Bdmteeo 298 (multi-purpose space), with class 750.7 on
# Ostrava - Frýdlant n. O. - Frenštát p. R. The driving trailer comes as -front
# (cab leading) and -rear (cab at the tail)."""),
}

# ------------------------------------------------------------------ CZR ports
# The ČD railjet, InterJet and ComfortJet sets keep the CZR art (Lubak91,
# CZR-vehicles-rail-pass-CD.pak) frozen in src/czr_cd_jets.png, in the pak's
# object order. Each object is ported 1:1 with its CZR coupling lists (read from
# the pak: an empty list = no constraint on that side) and its cost, capacity,
# speed and weight. id -> (display id, role, sheet row, cost, payload, speed,
# weight t, prev, next, drop the yellow line)
CZR = {
    "comfortjet": [
        ("Bdmpz883", "Bdmpz 883", "Bend", 0, 2351400, 141, 230, 50, "any", "any", False),
        ("Ampz881", "Ampz 881", "Ao", 1, 2351400, 139, 230, 50,
         ["Bdmpz883", "Bbmpz884", "BRmpz882"], ["Bbmpz884", "Bdmpz883", "Afmpz880"], False),
        ("Bbmpz884", "Bbmpz 884", "Bprm", 2, 2351400, 122, 230, 50,
         ["Ampz881", "Bmpz885"], ["Bmpz885", "Ampz881", "BRmpz882"], False),
        ("Bmpz885", "Bmpz 885", "Bmid", 3, 2351400, 159, 230, 50,
         ["Bbmpz884", "Bmpz885", "Bdmpz883"], ["Bdmpz883", "Bmpz885", "Bbmpz884"], False),
        # added: the restaurant car (from the railjet ARbmpz 892, 1st-class line removed)
        # and the driving trailer (the railjet Afmpz 890 cab car)
        ("BRmpz882", "BRmpz 882", "BR", 19, 2646400, 44, 230, 50, ["Bbmpz884"], ["Ampz881"], True),
        ("Afmpz880", "Afmpz 880", "ABcab", 20, 2646400, 97, 230, 54, ["Ampz881"], [], False),
    ],
    "interjet": [
        ("Bdmpz896-1", "Bdmpz 896", "Bend", 4, 2351400, 141, 200, 50, "any", ["Bmpz895-2"], False),
        ("Bmpz895-2", "Bmpz 895", "Bmid", 5, 2351400, 159, 200, 50, ["Bdmpz896-1"], ["Bmpz895-3", "Bbmpz897-4"], False),
        ("Bmpz895-3", "Bmpz 895", "Bmid", 6, 2351400, 159, 200, 50, ["Bmpz895-2"], ["Bbmpz897-4"], False),
        ("Bbmpz897-4", "Bbmpz 897", "Bprm", 7, 2351400, 122, 200, 50, ["Bmpz895-2", "Bmpz895-3"], ["Ampz894-5"], False),
        ("Ampz894-5", "Ampz 894", "Ao", 8, 2351400, 139, 200, 50, ["Bbmpz897-4"], "any", False),
        ("Ampz894-R1", "Ampz 894", "Ao", 9, 2351400, 139, 200, 50, "any", ["Bbmpz897-R2"], False),
        ("Bbmpz897-R2", "Bbmpz 897", "Bprm", 10, 2351400, 122, 200, 50, ["Ampz894-R1"], ["Bmpz895-R3"], False),
        ("Bmpz895-R3", "Bmpz 895", "Bmid", 11, 2351400, 159, 200, 50, ["Bbmpz897-R2"], ["Bmpz895-R4", "Bdmpz896-R5"], False),
        ("Bmpz895-R4", "Bmpz 895", "Bmid", 12, 2351400, 159, 200, 50, ["Bmpz895-R3"], ["Bdmpz896-R5"], False),
        ("Bdmpz896-R5", "Bdmpz 896", "Bend", 13, 2351400, 141, 200, 50, ["Bmpz895-R4", "Bmpz895-R3"], "any", False),
    ],
    "railjet": [
        ("Bmpz893-1", "Bmpz 893", "Bbike", 14, 2351400, 141, 230, 50, "any", ["Bmpz891-2"], False),
        ("Bmpz891-2", "Bmpz 891", "Bo", 15, 2351400, 141, 230, 50, ["Bmpz893-1"], ["Bmpz891-3"], False),
        ("Bmpz891-3", "Bmpz 891", "Bo", 16, 2351400, 141, 230, 50, ["Bmpz891-2"], ["Bmpz891-4"], False),
        ("Bmpz891-4", "Bmpz 891", "Bo", 17, 2351400, 141, 230, 50, ["Bmpz891-3"], ["Bmpz891-5"], False),
        ("Bmpz891-5", "Bmpz 891", "Bo", 18, 2351400, 141, 230, 50, ["Bmpz891-4"], ["ARbmpz892-6"], False),
        ("ARbmpz892-6", "ARbmpz 892", "AR", 19, 2646400, 30, 230, 50, ["Bmpz891-5"], ["Afmpz890-7"], False),
        ("Afmpz890-7", "Afmpz 890", "ABcab", 20, 2646400, 97, 230, 54, ["ARbmpz892-6"], "any", False),
        ("Afmpz890-R1", "Afmpz 890", "ABcab", 21, 2646400, 97, 230, 54, "any", ["ARbmpz892-R2"], False),
        ("ARbmpz892-R2", "ARbmpz 892", "AR", 22, 2646400, 30, 230, 50, ["Afmpz890-R1"], ["Bmpz891-R3"], False),
        ("Bmpz891-R3", "Bmpz 891", "Bo", 23, 2351400, 141, 230, 50, ["ARbmpz892-R2"], ["Bmpz891-R4"], False),
        ("Bmpz891-R4", "Bmpz 891", "Bo", 24, 2351400, 141, 230, 50, ["Bmpz891-R3"], ["Bmpz891-R5"], False),
        ("Bmpz891-R5", "Bmpz 891", "Bo", 25, 2351400, 141, 230, 50, ["Bmpz891-R4"], ["Bmpz891-R6"], False),
        ("Bmpz891-R6", "Bmpz 891", "Bo", 26, 2351400, 141, 230, 50, ["Bmpz891-R5"], ["Bmpz893-R7"], False),
        ("Bmpz893-R7", "Bmpz 893", "Bbike", 27, 2351400, 141, 230, 50, ["Bmpz891-R6"], "any", False),
    ],
}
CZR_META = {
    "comfortjet": ("ComfortJet", "ComfortJet", "comfortjet", """# ČD ComfortJet (Siemens Viaggio Comfort, 2022-26), 20 nine-car sets:
# loco + Bdmpz 883 + 4x Bmpz 885 + Bbmpz 884 + BRmpz 882 + Ampz 881 + Afmpz 880 driving
# trailer (push-pull since 6/2026). The 883 / 885 / 884 / 881 are the CZR ComfortJet
# ported 1:1 (the set couples either way round, as in CZR); the Afmpz 880 reuses the
# CZR railjet Afmpz 890 cab car and the BRmpz 882 the CZR ARbmpz 892 without the
# 1st-class line (same Siemens family, same painted style). The middle cars look
# alike on purpose: the fixed order of the set tells them apart."""),
    "interjet": ("InterJet", "InterJet", "interjet", """# ČD InterJet (Siemens Viaggio, 2020-21), 10 five-car sets based in Cheb (R15, IC
# Západní expres): Bdmpz 896 + 2x Bmpz 895 + Bbmpz 897 + Ampz 894. The CZR InterJet
# ported 1:1: ids -1..-5 are the set with the Bdmpz 896 next to the locomotive,
# -R1..-R5 the same set turned round (Ampz 894 next to the locomotive)."""),
    "railjet": ("Railjet", "railjet", "railjet", """# ČD railjet (Siemens Viaggio, 2014), 7 seven-car sets, now on the Praha - Budapest
# "Metropolitan": Bmpz 893 + 4x Bmpz 891 + ARbmpz 892 + Afmpz 890 driving trailer. The
# CZR railjet ported 1:1: ids -1..-7 are the set with the Bmpz 893 next to the
# locomotive and the cab car at the tail, -R1..-R7 the set with the cab car leading."""),
}


def _empty_row():
    t = np.zeros((128, 128, 3), np.uint8)
    t[:, :] = T
    return [t.copy() for _ in range(8)]


def coach_rows(fam, liv):
    rows = []
    for (vid, code, cab, livs) in FAMILIES[fam]["cars"]:
        rows.append(cdcoach.tiles(code, liv, cab) if liv in livs else _empty_row())
    return rows


def czr_rows(fam):
    """Rows from the frozen CZR sheet (pak-extracted: 4 px low, so lifted)."""
    from PIL import Image
    src = np.array(Image.open(os.path.join(HERE, "src", "czr_cd_jets.png")).convert("RGB"))
    rows = []
    for car in CZR[fam]:
        r, noyellow = car[3], car[10]
        band = src[r * 128:(r + 1) * 128].copy()
        lifted = np.zeros_like(band)
        lifted[:, :] = T
        lifted[:-4] = band[4:]
        if noyellow:
            # the 1st-class line is orange-yellow; repaint it in the body blue below it
            px = lifted.reshape(-1, 3).astype(int)
            yel = (px[:, 0] > 180) & (px[:, 1] > 110) & (px[:, 2] < 80)
            for i in np.where(yel)[0]:
                y, x = divmod(i, 1024)
                lifted[y, x] = lifted[min(y + 1, 127), x]
        rows.append([lifted[:, c * 128:(c + 1) * 128] for c in range(8)])
    return rows


def jobs():
    out = {}
    for fam in FAMILIES:
        livs = []
        for (_, _, _, lv) in FAMILIES[fam]["cars"]:
            for x in lv:
                if x not in livs:
                    livs.append(x)
        out[fam] = [(liv, (lambda f=fam, l=liv: coach_rows(f, l)),
                     [v for (v, _, _, _) in FAMILIES[fam]["cars"]]) for liv in livs]
    for fam in CZR:
        out[fam] = [(CZR_META[fam][2], (lambda f=fam: czr_rows(f)), [c[0] for c in CZR[fam]])]
    return out


# ------------------------------------------------------------------ yaml
def _q(s):
    return '"' + str(s).replace('"', '\\"') + '"'


def _fields(code_or_vals):
    return code_or_vals


def vehicle_yaml(vid, disp, role, row, payload, speed, weight, intro, retire, length, cost,
                 prev="any", nxt="any", head=None, tail=None, liveries=None, all_livs=None):
    en, cs = ROLE[role]
    lines = [f"  - id: {_q(vid)}", f"    display_id: {_q(disp)}", f"    role_en: {_q(en)}",
             f"    role_cs: {_q(cs)}", f"    row: {row}"]
    for key, val in (("head", head), ("tail", tail)):
        if val is not None:
            lines.append(f"    {key}: {'true' if val else 'false'}")
    for key, val in (("prev", prev), ("next", nxt)):
        if val == "any":
            lines.append(f"    {key}: any")
        else:
            lines.append(f"    {key}: [" + ", ".join(_q(x) for x in val) + "]")
    if liveries and all_livs and set(liveries) != set(all_livs):
        lines.append("    liveries: [" + ", ".join(liveries) + "]")
    running = max(10, int(round(payload * 0.25 + speed * 0.05)))
    fixed = int(round(cost / 9000))
    lines += ["    fields:", f"      cost: {cost}", f"      payload: {payload}", f"      speed: {speed}",
              f"      weight: {weight}", f"      runningcost: {running}", f"      fixed_cost: {fixed}",
              f"      intro_year: {intro[0]}", f"      intro_month: {intro[1]}"]
    if retire:
        lines += [f"      retire_year: {retire}", "      retire_month: 12"]
    lines += ["      waytype: track", "      freight: Passagiere", f"      length: {length}",
              "    extended:", "      axles: 4", ""]
    return lines


def family_yaml(fam):
    F = FAMILIES[fam]
    all_livs = []
    for (_, _, _, lv) in F["cars"]:
        for x in lv:
            if x not in all_livs:
                all_livs.append(x)
    out = [F["comment"],
           "# Original art drawn from scratch: box models from the vagonWEB scale side drawings,",
           "# rendered by tools/railrender/cdcoach.py (regenerate with",
           f"# `python tools/railrender/cd_coaches.py {fam}`). Najbrt 2: RAL 7035 lower body,",
           "# RAL 5003 line and doors, RAL 5015 window band, light line, RAL 5003 roof; the yellow",
           "# RAL 1003 line marks the 1st-class part only.",
           "", "agency: CeskeDrahy", f"type: {_q(F['type'])}",
           "copyright: vojtechzicha      # original art, drawn from scratch",
           "windows_lit_when_loaded: true", "", "display:", '  agency_en: "ČD"', '  agency_cs: "ČD"',
           f"  family_en: {_q(F['en'])}", f"  family_cs: {_q(F['cs'])}", "", "vehicles:"]
    for row, (vid, code, cab, livs) in enumerate(F["cars"]):
        disp, role, pay, speed, weight, intro, retire = CARS[code]
        prev = nxt = "any"
        head = tail = None
        if cab == "front":
            prev, head = [], True
        elif cab == "rear":
            nxt, tail = [], True
        out += vehicle_yaml(vid, disp, role, row, pay, speed, weight, intro, retire,
                            cdcoach.length(code), cost_of(code), prev, nxt, head, tail, livs, all_livs)
    out += ["liveries:"]
    for liv in all_livs:
        en, cs = LIV[liv]
        out += [f"  - color: {liv}", f"    name_en: {_q(en)}", f"    name_cs: {_q(cs)}"]
    return "\n".join(out) + "\n"


def czr_yaml(fam):
    typ, fname, liv, comment = CZR_META[fam]
    out = [comment,
           "# Art: CZR (Lubak91, CZR-vehicles-rail-pass-CD.pak), frozen in",
           "# tools/railrender/src/czr_cd_jets.png; regenerate with",
           f"# `python tools/railrender/cd_coaches.py {fam}`. Cost, capacity, speed, weight and",
           "# coupling lists as in the CZR pak (intro 2008/12, retire 2048 kept from CZR).",
           "", "agency: CeskeDrahy", f"type: {_q(typ)}", "copyright: Lubak91",
           "windows_lit_when_loaded: true", "", "display:", '  agency_en: "ČD"', '  agency_cs: "ČD"',
           f"  family_en: {_q(fname)}", f"  family_cs: {_q(fname)}", "", "vehicles:"]
    for row, (vid, disp, role, _, cost, pay, speed, weight, prev, nxt, _) in enumerate(CZR[fam]):
        # CZR lists never contain "none": a listed side takes only those partners
        head = None if prev == "any" else (prev == [])
        tail = None if nxt == "any" else (nxt == [])
        out += vehicle_yaml(vid, disp, role, row, pay, speed, weight, (2008, 12), 2048, 13, cost,
                            prev, nxt, head, tail)
    out += ["liveries:", f"  - color: {liv}", f"    name_en: {_q(fname)}", f"    name_cs: {_q(fname)}"]
    return "\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    prev = None
    write_yaml = "--yaml" in args
    if write_yaml:
        args.remove("--yaml")
    if "--preview" in args:
        i = args.index("--preview")
        prev = args[i + 1]
        del args[i:i + 2]
        os.makedirs(prev, exist_ok=True)
    todo = jobs()
    for fam in (args or list(todo)):
        d = os.path.join(FAM_DIR, fam)
        for liv, make, labels in todo[fam]:
            rows = make()
            out = os.path.join(d, "sprites", f"{liv}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            R.save_rows(rows, out)
            if prev:
                R.preview(rows, os.path.join(prev, f"{fam}_{liv}.png"), z=4, labels=labels)
            print("wrote", os.path.relpath(out, REPO))
        if write_yaml:
            with open(os.path.join(d, "family.yaml"), "w", encoding="utf-8", newline="\n") as f:
                f.write(czr_yaml(fam) if fam in CZR else family_yaml(fam))
            print("wrote", os.path.relpath(os.path.join(d, "family.yaml"), REPO))


if __name__ == "__main__":
    main()
