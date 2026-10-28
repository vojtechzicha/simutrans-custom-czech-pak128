"""Solaris Urbino 18 and Škoda 26Tr / 27Tr town fleets on the dpo_solaris.py
bodies: render the sprite sheets of their vehicle-bus / vehicle-trolleybus
families. Until 2026-10-28 these were TommPa9's hand-drawn sheets; the owner
then asked for one drawing per bus type (the render) and for every 18 m
articulated bus at 8 + 6 carunits. The family.yaml files are written by hand.

    python tools/busrender/solaris_town.py [family ...] [--preview DIR]

The liveries are sor_town.py's town palettes (TOWNS: body, roof, cant, the
lower-body skirt / stripe / sill bands, front and rear bumpers, display
colour), painted by SVeh on the Solaris model.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import numpy as np                             # noqa: E402
from PIL import Image                          # noqa: E402
import dpo_solaris as DS                       # noqa: E402
import sor_town as ST                          # noqa: E402

sh = DS.sh


class SVeh(DS.Solaris):
    """a Solaris body in a sor_town.py town palette"""

    def setup_livery(self):
        P = self.P = ST.TOWNS[self.liv]
        self.BODY = P["body"]
        self.ROOF = P["roof"]
        self.EDGE = P["body"]                          # the roof cap; a red top row is cant()
        self.SHOULDER = P["roof"]
        self.FAIR_TOP = P.get("pod", P["roof"])
        self.FAIR_SIDE = P["body"]

    @property
    def old(self):
        return False

    def tex_for(self, i):
        tex = super().tex_for(i)
        disp = self.P["disp"]

        def paint(p):
            c = tex(p)
            return disp if c == DS.AMBER else c
        return paint

    def cant(self, p, u, right):
        if self.face == "u4":
            return super().cant(p, u, right)
        if self.P.get("cant") and p.z >= self.ZR - 0.25:
            return self.P["cant"]
        return DS.MASK if p.z < self.ZWIN1 + 0.25 else self.BODY

    def lower(self, p, u, right):
        """sor_town.TVeh.lower's bands from the body's bottom Z0"""
        z = p.z
        P = self.P
        if P.get("sill") and z >= self.ZWIN0 - 0.33:
            return P["sill"]
        sk = P.get("skirt")
        if sk and z < self.Z0 + sk[0]:
            return sk[1]
        st = P.get("stripe")
        if st and self.Z0 + st[0] <= z < self.Z0 + st[1]:
            return st[2]
        return P.get("lower", P["body"])

    def tex_front(self, p, dz=0.0):
        if p.z + dz < 0.55:
            return sh(self.P["front"]["bumper"], "front")
        return super().tex_front(p, dz)

    def tex_rear(self, p):
        a = abs(p.t)
        if p.z < 0.55 and not (a > DS.HW - 0.28 and p.z >= 0.55):
            return sh(self.P["rear"]["bumper"], "rear")
        return super().tex_rear(p)


def build(model, liv, lens):
    sp = DS.MODELS[model]
    m = SVeh(sp, liv, DS.OPTS)
    rows = []
    for i, l in enumerate(m.cu):
        L = m.sec_len(i)
        tiles = []
        for d in DS.DIRS:
            o = np.array(DS.H.origin_for(d)) + (4 - lens[i] / 2.0) * DS.H.PER_CU[d]
            img, _ = DS.render(d, m.boxes(i), m.tex_for(i), L, o)
            if m.poles:
                pb = m.M(m.poles[0])
                if m.U[i] <= pb < m.U[i + 1]:
                    DS.draw_poles(img, d, L, o, m.U[i + 1] - pb, m.roof_top(pb) + 0.16, m.poles[1], sp["polecol"])
            tiles.append(img)
        rows.append(tiles)
    return rows


# family -> (yaml lengths per section, {livery colour: [(model, town palette), ...]})
FAMILIES = {
    "vehicle-trolleybus/dpmb/26tr": ([8], {"dpmbbilocervena": [("26tr", "dpmb_uw")]}),
    "vehicle-trolleybus/dpmp/26tr": ([8], {"dpmpbilocervena": [("26tr", "dpmp_uw")]}),
    "vehicle-trolleybus/mdpo/26tr": ([8], {"mdpobilocervena": [("26tr", "mdpo_uw"), ("26tr", "mdpo_uw")]}),
    "vehicle-trolleybus/dpmb/27tr": ([8, 6], {"dpmbbilocervena": [("27tr", "dpmb_uw")]}),
    "vehicle-bus/dpmb/solaris_urbino_18": ([8, 6], {"dpmbbilocervena": [("u18_3", "dpmb_uw")]}),
    "vehicle-bus/dpmo/solaris_urbino_18": ([8, 6], {"dpmobilomodrocervena": [("u18_3", "dpmo")]}),
    "vehicle-bus/dpmo/solaris_urbino_18_iv": ([8, 6], {"dpmobilomodrocervena": [("u18_4", "dpmo")]}),
    "vehicle-bus/mhd-tabor/solaris_urbino_18_iii_cng": ([8, 6], {"comettbila": [("u18_3cng", "tabor_uw")]}),
}


def main(argv):
    prev = None
    if "--preview" in argv:
        i = argv.index("--preview")
        prev = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    for fam, (lens, livs) in FAMILIES.items():
        short = fam.split("/", 1)[1]
        if argv and short not in argv and fam.split("/")[-1] not in argv:
            continue
        d = os.path.join(REPO, *fam.split("/"), "sprites")
        for colour, parts in livs.items():
            rows = []
            for model, liv in parts:
                rows += build(model, liv, lens)
            a = DS.sheet(rows)
            DS.check_specials(a, fam)
            Image.fromarray(a).save(os.path.join(d, colour + ".png"))
            if prev:
                os.makedirs(prev, exist_ok=True)
                DS.H.preview(a, os.path.join(prev, f"{short.replace('/', '-')}-{colour}.png"))
            print(f"{fam}/sprites/{colour}.png  rows={len(rows)}")


if __name__ == "__main__":
    main(sys.argv[1:])
