"""RegioJet ÚK RegioPanters in the DÚK green-yellow livery:
  650.2 = Škoda 15Ev, 2 cars (650 + 651), and
  640.2 = Škoda 20Ev, 3 cars (640 + 642 + 641).

Painted on the shared RegioPanter body of tools/railpaint/panter.py (TommPa9's
drawings), so RegioJet's units have exactly the silhouette of every ČD, Arriva
and JMK RegioPanter in game (RegioJet's 15Ev / 20Ev are structurally identical
to ČD's, zeleznicni-magazin.cz 15 Jun 2026). The livery is one zone dict:

  * side: lime-green body with a lighter-green cant band, continuous black
    window band, dark-grey sill, silver-grey door leaves, the silver sweep
    behind the cab (hood + the panel under the cab window), and a yellow-orange
    stripe under the windows of the high-floor inner ends, carrying the red /
    blue "|| REGIOJET" logo;
  * cab front: black face (visor, windscreen, panel with the white DÚK logo)
    inside a yellow-orange outline (hood edges, pods), dark coupler area,
    yellow-orange skirt and anti-climber;
  * grey roof skin and equipment boxes.

Colours from photos, 12-15 Jun 2026, Ústí n. L.: the zdopravy.cz gallery
"Obrazem: RegioJet vyjíždí s novými vlaky v Ústeckém kraji",
zeleznicni-magazin.cz 641.264 on U3, Commons "Škoda 15 Ev pro Regiojet". Lime
green sunlit #77BC28 / #63BB3B; vagonWEB's #00A508 is far too dark. Orange
#F4A30C, silver sweep #C0C4CD, doors vagonWEB #7F868C.

    python tools/railrender/regiojet.py 650_2 640_2
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "railpaint"))
import panter  # noqa: E402  (tools/railpaint)

# ------------------------------------------------------------------ colours
GREEN = (0x6C, 0xBE, 0x2C)        # lime green body
GREEN_LT = (0x9E, 0xDC, 0x52)     # lighter cant band
BLACK = (0x1A, 0x1D, 0x20)        # window band, cab face
ORANGE = (0xF4, 0xA3, 0x0C)       # cab outline, skirt, side stripe
SILVER = (0xC4, 0xC9, 0xCF)       # sweep behind the cab (not the special 0xC9C9C9)
DOOR = (0x9C, 0xA3, 0xA9)         # silver-grey door leaves
SILL = (0x40, 0x45, 0x48)         # dark-grey lower edge
COUPLER = (0x2E, 0x31, 0x34)      # dark area around the coupler, above the skirt
ROOF = (0xB4, 0xBA, 0xBF)         # roof skin
BOX = (0x78, 0x7E, 0x84)          # roof equipment boxes
WHITE = (0xEE, 0xF1, 0xF3)
RJ_RED = (0xE3, 0x34, 0x2F)
RJ_BLUE = (0x1F, 0x3A, 0x93)
CAB_GLASS = (panter.CABGLASS, "flat")
CAM = ((30, 32, 36), "flat")


def stripe_span(g):
    """(from, to) spans in u from the car's rear of the orange stripe: the
    high-floor inner end(s) between the outermost door and the car end, away
    from the cab."""
    m = 3 * g.px
    first = min(u0 for u0, u1 in g.doors)
    last = max(u1 for u0, u1 in g.doors)
    spans = []
    if g.cab != "rear":                      # A, M: rear end is an inner end
        spans.append((m, first - m))
    if g.cab != "front":                     # B, M: front end is an inner end
        spans.append((last + m, 1 - m))
    return spans


def in_stripe(ctx):
    return any(a <= ctx["ur"] <= b for a, b in stripe_span(ctx["geo"]))


def side_low(ctx):
    """k6 / k7 under the windows: green, or the orange stripe at inner ends."""
    return ORANGE if in_stripe(ctx) else GREEN


def outline(ctx):
    """Cab front: black face, the yellow-orange outline only along its two
    outer edges (u = fraction across the end view)."""
    return ORANGE if ctx["u"] < 0.17 or ctx["u"] > 0.83 else BLACK


def skirt(ctx):
    return COUPLER if ctx["k"] <= 14 else ORANGE


def logo_marks(car):
    """Red "|| REGIO" + blue "JET" on the orange stripe (u from the car's rear)."""
    g = panter.geo(car)
    out = []
    for a, b in stripe_span(g):
        mid = (a + b) / 2
        out += [(mid - 1.5 * g.px, 3 * g.px, 7, RJ_RED), (mid + 1.5 * g.px, 2 * g.px, 7, RJ_BLUE)]
    return out


def livery(car):
    liv = {
        "ROOF_EDGE": GREEN_LT,
        "S_CANT": GREEN_LT, "S_TOP": GREEN, "S_BODY": BLACK, "S_LINE": side_low, "S_GREY": side_low,
        "S_VAL": SILL, "S_FIRST": GREEN, "S_DOOR": DOOR, "S_HOOD": SILVER, "S_CABWIN": CAB_GLASS,
        "S_WEDGE": SILVER,
        "E_CANT": GREEN_LT, "E_TOP": GREEN, "E_BODY": BLACK, "E_LINE": GREEN, "E_GREY": GREEN,
        "E_VAL": SILL, "E_GANG": (38, 40, 44),
        "E_HOOD": outline, "E_VISOR": outline, "E_CAM": CAM, "WSCREEN": CAB_GLASS, "E_WIN": CAB_GLASS,
        "E_PANEL": BLACK, "E_SKIRT": skirt, "E_BEAM": ORANGE,
        "_roof": (ROOF, BOX),
        "_end_marks": [(0.5, 0.14, 10, WHITE)],      # white DÚK logo on the black panel
        "_marks": logo_marks(car),
    }
    return liv


def rows_for(cars):
    """Sprite rows (8 tiles each) for the given car types, e.g. "AB" / "AMB"."""
    rows = []
    for c in cars:
        a = panter.paint_car(c, livery(c))
        rows.append([a[:, i * 128:(i + 1) * 128].copy() for i in range(8)])
    return rows


LIVERY = "dukzelenozluta"
JOBS = {
    "650_2": [(LIVERY, (lambda: rows_for("AB")), ["650", "651"])],
    "640_2": [(LIVERY, (lambda: rows_for("AMB")), ["640", "642", "641"])],
}

if __name__ == "__main__":
    import regiojet
    regiojet.main()
