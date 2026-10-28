"""Solaris Urbino 18 and Škoda 26Tr / 27Tr town fleets on the dpo_solaris.py
bodies: render the sprite sheets of their vehicle-bus / vehicle-trolleybus
families. Until 2026-10-28 these were TommPa9's hand-drawn sheets; the owner
then asked for one drawing per bus type (the render) and for every 18 m
articulated bus at 8 + 6 carunits. The family.yaml files are written by hand.

    python tools/busrender/solaris_town.py [family ...] [--preview DIR]

The liveries are sor_town.py's town palettes (TOWNS: body, roof, cant, the
lower-body skirt / stripe / sill / bands, front and rear bumpers, display
colour), painted by SVeh on the Solaris model. The palettes of this module
(added to TOWNS below) also use:
    cant4          the Urbino IV's band over the windows (default black)
    cant_zone      f(veh, u, z) -> True where the band over the windows is
                   black up to the roof edge (the DPMB 27Tr)
    arch           (colour, width): a band round each wheel arch
    fair_wedge     colour of the wedges at the ends of the big roof fairings
    polecol        trolley pole colours (a key of dpo_solaris.POLECOL)
    front          also stripe (the row through the headlight tops), apron
                   (the lower front up to the headlights), bumper_mid (the
                   bumper between the lamps), patch (colours of a chequered
                   patch at the lower front corner)
The details were checked against photos and the old sheets (2026-10-28).
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
        self.FAIR_TOP = P["roof"]                     # roof equipment in roof colour (a palette's
        self.FAIR_SIDE = P["body"]                    # "pod" colours the SOR bodies' boxes only)

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

    def tex_side(self, p, u, U1):
        c = super().tex_side(p, u, U1)
        ov = self.P.get("overlay")
        if ov and c is not None:
            o = ov(self, p, u, p.face == "right")
            if o is not None:
                return sh(o, p.face)
        return c

    def cant(self, p, u, right):
        if self.face == "u4":
            c = super().cant(p, u, right)
            return self.P.get("cant4", c) if c == DS.MASK else c
        zone = self.P.get("cant_zone")
        if zone and zone(self, u, p.z):
            return DS.MASK
        if self.P.get("cant") and p.z >= self.ZR - 0.25:
            return self.P["cant"]
        return DS.MASK if p.z < self.ZWIN1 + 0.25 else self.BODY

    def lower(self, p, u, right):
        """sor_town.TVeh.lower's bands from the body's bottom Z0"""
        z = p.z
        P = self.P
        dec = P.get("decal")
        if dec:
            c = dec(self, p, u, right)
            if c is not None:
                return c
        if P.get("sill") and z >= self.ZWIN0 - 0.33:
            return P["sill"]
        sk = P.get("skirt")
        if sk and z < self.Z0 + sk[0]:
            return sk[1]
        arch = P.get("arch")
        if arch:
            for a in self.axles:
                if abs(u - a) < 0.62 + arch[1] and DS.math.hypot(u - a, z - self.WR) < 0.62 + arch[1]:
                    return arch[0]
        st = P.get("stripe")
        if st and self.Z0 + st[0] <= z < self.Z0 + st[1]:
            return st[2]
        for ztop, c in P.get("bands", ()):
            if z < ztop:
                return c
        return P.get("lower", P["body"])

    def tex_kit(self, p, u, k):
        w = self.P.get("fair_wedge")
        if w and k["kind"] == "fair" and k["h"] >= 0.30 and p.face in ("left", "right"):
            r = min(1.0, max(0.0, (p.z - self.ZR - k.get("z0", 0.0)) / k["h"]))
            if u - k["a"] < 0.45 + 1.10 * r or k["b"] - u < 0.30 + 0.70 * r:
                return sh(w, p.face, DS.POD)
        return super().tex_kit(p, u, k)

    def tex_front(self, p, dz=0.0):
        F = self.P["front"]
        z, a = p.z + dz, abs(p.t)
        pat = F.get("patch")
        if pat and z < 1.05 and p.t > DS.HW - 0.62:
            return sh(pat[(int(z / 0.25) + int((DS.HW - p.t) / 0.20)) % 2], "front")
        if z < 0.55:
            if F.get("bumper_mid") and a < DS.HW - 0.46:
                return sh(F["bumper_mid"], "front")
            return sh(F["bumper"], "front")
        if F.get("apron") and z < 0.80 and not (DS.HW - 0.46 < a < DS.HW - 0.12):
            return sh(F["apron"], "front")
        if F.get("stripe") and inr(z, 0.80, 1.05):
            return sh(F["stripe"], "front")
        return super().tex_front(p, dz)

    def tex_rear(self, p):
        a = abs(p.t)
        if p.z < 0.55 and not (a > DS.HW - 0.28 and p.z >= 0.55):
            return sh(self.P["rear"]["bumper"], "rear")
        return super().tex_rear(p)


inr = DS.inr
MODELS = DS.MODELS
DS.POLECOL.update({
    # DPMB 27Tr: light grey with yellow upper ends and a dark base (photos of 3655, 3656)
    "dpmb27": ([(0.15, DS.rgb(0x404246)), (0.75, DS.rgb(0xA4A8AC)), (1.01, DS.rgb(0xF2C800))], DS.rgb(0xF2C800)),
    # DPMP 26Tr: yellow (photos of 323, 325, 328)
    "yellow": ([(0.12, DS.rgb(0x1E1E20)), (1.01, DS.rgb(0xF2C800))], DS.rgb(0x2A2A2C)),
})


def dpmb27_black(v, u, z):
    """the DPMB 27Tr: the black band up to the roof edge over the front half of
    the front section, ended by a slanting white edge, and over the rear
    section except next to the joint (DPMB drawing tr27.png, photos of 3655,
    3656)"""
    if v.cur_i == 0:
        return u < v.U[1] * 0.5 - 0.9 * (z - v.ZWIN1)
    return u > v.U[1] + 1.20


ST.TOWNS.update({
    # DPMB 27Tr: the black band zones, the red arch panels over the skirt
    "dpmb_27tr": dict(ST.TOWNS["dpmb_uw"], cant_zone=dpmb27_black, arch=(ST.DPMB_RED, 0.25), polecol="dpmb27"),
    # DPMP 26Tr: the raised red band and front stripe of dpmp_uw, yellow poles
    "dpmp_26tr": dict(ST.TOWNS["dpmp_uw"], polecol="yellow"),
    # MDPO 26Tr: the red row under the roof edge, the red lower body up to the
    # wheel-arch tops (photos of 310, 313)
    "mdpo_26tr": dict(ST.TOWNS["mdpo_uw"], cant=ST.MDPO_RED, skirt=(0.70, ST.MDPO_RED)),
    # DPMO on the Urbino III: the navy skirt two rows tall under the red stripe,
    # the red line across the front over the navy bumper (photos of 411, 626)
    "dpmo_sol3": dict(ST.TOWNS["dpmo"], skirt=(0.50, ST.DPMO_NAVY), stripe=(0.50, 0.75, ST.DPMO_RED),
                      front=dict(ST.TOWNS["dpmo"]["front"], stripe=ST.DPMO_RED)),
    # on the Urbino IV: navy wedges at the ends of the white roof fairings, the
    # red bumper with navy corners (photos of 425, 648)
    "dpmo_sol4": dict(ST.TOWNS["dpmo"], skirt=(0.50, ST.DPMO_NAVY), stripe=(0.50, 0.75, ST.DPMO_RED),
                      fair_wedge=ST.DPMO_NAVY,
                      front=dict(ST.TOWNS["dpmo"]["front"], bumper_mid=ST.DPMO_RED)),
    # Třinec on the Perun (Urbino IV): the lime band over the windows with the
    # white wedges, lime round the wheel arches, the tall lime apron (photos
    # 528214, 528221, 803570)
    "trinec_sol": dict(ST.TOWNS["trinec"], cant4=ST.TRINEC_LIME, arch=(ST.TRINEC_LIME, 0.12),
                       front=dict(ST.TOWNS["trinec"]["front"], apron=ST.TRINEC_LIME)),
    # Tábor COMETT e-bus: the orange and black chequered patch at the lower
    # front corner (Commons "Elektrobusy v Táboře")
    "tabor_sol_e": dict(ST.TOWNS["tabor_uw"],
                        front=dict(ST.TOWNS["tabor_uw"]["front"], patch=(ST.COMETT_ORANGE, ST.BLACK))),
})


def build(model, liv, lens):
    if liv.startswith("pid:"):                  # pid.py's PID grey-red / trikolóra painter
        import pid
        key, reds = PID[model]
        return pid.solaris(model, liv[4:], reds, lens=lens)()
    sp = MODELS[model]
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
                    DS.draw_poles(img, d, L, o, m.U[i + 1] - pb, m.roof_top(pb) + 0.16, m.poles[1],
                                  m.P.get("polecol", sp["polecol"]))
            tiles.append(img)
        rows.append(tiles)
    return rows


# the PID columns per model for "pid:pa" / "pid:pb" (pid.solaris)
PID = {"u10": ("pa", [(1.60, 3.50), (6.50, 8.30)])}

# family -> (yaml lengths per section, {livery colour: [(model, town palette), ...]})
FAMILIES = {
    "vehicle-trolleybus/dpmb/26tr": ([8], {"dpmbbilocervena": [("26tr", "dpmb_uw")]}),
    "vehicle-trolleybus/dpmp/26tr": ([8], {"dpmpbilocervena": [("26tr", "dpmp_26tr")]}),
    "vehicle-trolleybus/mdpo/26tr": ([8], {"mdpobilocervena": [("26tr", "mdpo_26tr"), ("26tr", "mdpo_26tr")]}),
    "vehicle-trolleybus/dpmb/27tr": ([8, 6], {"dpmbbilocervena": [("27tr", "dpmb_27tr")]}),
    "vehicle-bus/dpmb/solaris_urbino_18": ([8, 6], {"dpmbbilocervena": [("u18_3", "dpmb_uw")]}),
    "vehicle-bus/dpmo/solaris_urbino_18": ([8, 6], {"dpmobilomodrocervena": [("u18_3", "dpmo_sol3")]}),
    "vehicle-bus/dpmo/solaris_urbino_18_iv": ([8, 6], {"dpmobilomodrocervena": [("u18_4", "dpmo_sol4")]}),
    "vehicle-bus/dpmo/solaris_urbino_12": ([8], {"dpmobilomodrocervena": [("u12_3", "dpmo_sol3")],
                                                 "zelena": [("u12_3", "dpmo_green")]}),
    "vehicle-bus/dpmo/solaris_urbino_12_iv": ([8], {"dpmobilomodrocervena": [("u12_4", "dpmo_sol4")]}),
    "vehicle-bus/mhd-tabor/solaris_urbino_12_electric": ([8], {"comettbila": [("u12_4e", "tabor_sol_e")]}),
    "vehicle-bus/dpp/urbino_10_5": ([7], {"dppcervenobila": [("u10", "most_dpp18")],
                                          "pidsedocervena": [("u10", "pid:pa")]}),
    # the Perun 26BB HE on the Urbino 12 IV electric body, as in Trutnov
    "vehicle-bus/mhd-trinec/perun_26bb_he": ([8], {"trinecbilozelena": [("u12_4e", "trinec_sol")]}),
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
