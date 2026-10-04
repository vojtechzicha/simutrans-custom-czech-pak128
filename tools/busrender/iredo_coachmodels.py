"""IREDO (Královéhradecký kraj) regional coaches and the newer SOR ICN as box
models on the iredo_models pipeline (RegioBus body, Livery classes, KHK rear
sticker, rj_vrender raycaster, lane placement by rj_buses.row_for).

Bodies here: Setra S 415 / S 418 LE business, Iveco Evadys 12M, Irisbus
Evadys H 12,8M, Irisbus Arway 12M, Karosa Axer 12M, Karosa C 955 Récréo,
Irizar i4 14M and the SOR ICN 12,3 / 10,5 / 9,5. Each class reproduces the
type's signature at pak128 scale (one row = 0.238 m, one side column ~0.17 m),
taken from the seznam-autobusu.cz photos named in its docstring:

- Setra LE business: very deep side glazing in the low-floor part that sweeps
  up three rows over the rear axle(s), windscreen with a black lower band, the
  silver SETRA bar between the headlamps, wheel covers in body colour.
- Iveco Evadys: high coach window line, the black swoosh behind the front
  door, a black mask under the windscreen with the silver IVECO bar.
- Irisbus Evadys H: the raised roof cap (red on P-transport) over a silver
  roof-edge strip, black EVADYS band under the windscreen, round lamps.
- Irisbus Arway: rounded roof edges, the first side window dipping towards
  the front, Irisbus badge face with the headlamps in the bumper.
- Karosa Axer: boxy, narrow black strip under the windscreen, the twin round
  headlamps in a black band across the lower front.
- Karosa Récréo: framed sliding windows, glazed folding front door, IVECO
  letters under the windscreen, headlamps in the bumper.
- Irizar i4: tag axle, raised roof cap over the front, deep black lower
  windscreen, black rear corner columns with the round lamps.
- SOR ICN: flat roof (no CN hump), deep glazing all along, black rub line,
  black mask from the windscreen down to the lamps, silver brow and teardrop
  headlamp pods, middle door just ahead of the rear axle, rear louvres.

Positions are REAL metres from the front (x); rows k count up from Z0, as in
iredo_models.
"""
from rj_vrender import Box, Sh, PXZ
import rj_busmodels as C
from rj_busmodels import lerp, W2
import iredo_models as M
from iredo_models import (RegioBus, Livery, GLASS, GLASS_HI, SCREEN, SCREEN_HI, BLACK,
                          PILLAR, HEAD, TAIL, PLATE, CHROME, GRILLE, GRILLE_DK,
                          GREY_LINE, LED, SCREEN_L, SCREEN_LHI, KHK_PANEL)


# ====================================================================== liveries
SILVER = (0xB4, 0xB8, 0xBC)       # plain silver (never the special greys)
SILVER_DK = (0x8E, 0x92, 0x96)


# ====================================================================== base
class CoachBus(RegioBus):
    """RegioBus with a few extra hooks for these types:

    band_k0(x)    lowest glazing row at x (sweeps / steps), default BAND;
    deco()        side paint evaluated before the RegioBus side (swooshes,
                  roof-edge strips), None = fall through;
    WRAP_K0       lowest row of the windscreen wrap on the side (x < 0.14);
    HUB_COVER     wheel covers in body colour (hub_r sets their size);
    FAIRING       (x0, x1, inset, height) raised roof cap in the livery's
                  A/C colour (Evadys H) or roof colour (FAIRING_ROOF)."""
    WRAP_K0 = 4
    HUB_COVER = False
    FAIRING = None
    FAIRING_ROOF = False

    def band_k0(self, x):
        return None

    def band_at(self, x):
        b = super().band_at(x)
        if b is None:
            return None
        k0 = self.band_k0(x)
        return (k0, b[1]) if k0 is not None else b

    def hub(self, z):
        if self.HUB_COVER:
            return Sh(self.lv.body)
        return super().hub(z)

    def deco(self, x, k, right):
        return None

    def side(self, u, z, right):
        x = self.X(u)
        k = self.row(z)
        w = self.wheel(u, z)
        if w is not None:
            return w
        if right:
            d = self.door(x, k)
            if d is not None:
                return d
        c = self.deco(x, k, right)
        if c is not None:
            return c
        if x < 0.14 and 4 <= k < self.WRAP_K0:
            d = self.lv.side(self, x, k, right)
            return Sh(d) if d is not None else Sh(self.lv.body)
        return super().side(u, z, right)

    def fairing(self, face, u, v, z):
        top = self.lv.roof if self.FAIRING_ROOF else self.lv.ac
        if face == "+z":
            return top
        if face in ("+v", "-v"):
            return Sh(tuple(c * 0.94 for c in top))
        return Sh(tuple(c * 0.86 for c in top))

    def model(self):
        L, boxes, lines = super().model()
        if self.FAIRING:
            x0, x1, inset, h = self.FAIRING
            z0 = self.zr(self.R_TOP) + 0.08
            boxes.append(Box(self.U(x1), self.U(x0), -W2 + inset, W2 - inset, z0 - 0.02, z0 + h,
                             self.fairing))
        return L, boxes, lines


# ====================================================================== Setra
class SetraFace:
    """Setra S 4xx LE business front: the windscreen and a black lower band
    fill everything down to 1.25 m, thin body-colour cap with the LED display
    inside the glass, the wide silver SETRA bar between the headlamps,
    orange indicators over the lamps."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            return Sh(self.lv.body)                      # thin cap over the glass
        if k == top - 2:
            if av > W2 - 0.07:
                return BLACK
            return LED if av < 0.95 else BLACK
        if k >= 5:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 3 else SCREEN
        if k == 4:
            if av > W2 - 0.45:
                return Sh(M.MARKER)                     # indicators over the lamps
            return BLACK                                  # black lower windscreen band
        if k == 3:
            if av > W2 - 0.45:
                return HEAD
            if av < W2 - 0.55:
                return Sh(SILVER)                         # the SETRA bar
            return Sh(self.lv.body)
        if d is not None and k <= 2:
            return Sh(d)
        if k == 2:
            return Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.30 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class SetraS415LE(SetraFace, CoachBus):
    """Setra S 415 LE business (2014+), 12.18 x 2.55 x 3.13 m, doors 1-2-0
    (single front door, double middle door right ahead of the rear axle).
    The side glazing reaches down to 1.25 m over the low-floor part and
    sweeps up three rows behind the middle door over the rear axle; a thin
    body-colour strip over the glazing; wheel covers in body colour; roof
    A/C pod over the rear half. Photos 411316 (TAD, right side + front),
    436517 (CDS front), 383667 / 372175 (S 418, left side), 426363."""
    real_len = 12.18
    axles = (2.72, 8.72)
    R_TOP = 12
    R_BAND0 = 5                    # livery reference: CDS lettering rows 0-3
    BAND = ((0.0, 12.18, 4, 11),)
    RISE = (8.20, 10.00)           # glazing sill rises from row 4 to row 7
    DOORS = ((0.30, 1.25, "le"), (6.95, 8.15, "le"))
    REAR_GLASS = (7, 10)
    HUB_COVER = True               # body-colour wheel covers (hub-sized, or they read as letters)
    AC = (4.6, 8.6)
    HATCHES = (3.4, 10.3)
    GLASS_HI_ROWS = 2

    def band_k0(self, x):
        a, b = self.RISE
        if x < a:
            return 4
        if x >= b:
            return 7
        return 4 + int(round(3 * (x - a) / (b - a)))

    def pillars(self, right):
        if right:
            return (2.45, 3.95, 5.45, 9.90, 11.1)
        return (2.45, 3.95, 5.45, 6.95, 8.45, 9.90, 11.1)

    def markers(self):
        return (1.9, self.axles[0] + 1.6, self.axles[1] - 1.6, self.real_len - 0.45)


class SetraS418LE(SetraS415LE):
    """Setra S 418 LE business (2016+), 14.64 m, three axles (tag axle),
    doors 1-2-0 with the middle door ahead of the drive axle; the sill
    sweeps up over the rear bogie. Photos 383667, 372175, 425238 (CDS)."""
    real_len = 14.64
    axles = (2.72, 9.68, 11.13)
    BAND = ((0.0, 14.64, 4, 11),)
    RISE = (9.05, 10.85)
    DOORS = ((0.30, 1.25, "le"), (7.80, 9.00, "le"))
    AC = (5.2, 9.6)
    HATCHES = (3.6, 12.6)

    def pillars(self, right):
        if right:
            return (2.45, 3.95, 5.45, 6.70, 10.85, 12.3, 13.5)
        return (2.45, 3.95, 5.45, 6.95, 8.45, 9.95, 11.4, 12.8)

    def markers(self):
        return (1.9, 4.6, 7.4, 10.4, self.real_len - 0.45)


# ====================================================================== Evadys
class EvadysFace:
    """Iveco Evadys (2013+) front: windscreen with the display in a black top
    band, a deep black mask under the glass down to the lamps, the silver
    IVECO bar across between the silver-rimmed headlamps, white bumper with
    a black slot."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av > W2 - 0.07:
                return BLACK
            return LED if av < 0.95 else BLACK
        if k >= 6:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k in (4, 5):
            return BLACK                                  # the black mask
        if k == 3:
            if av > W2 - 0.50:
                return HEAD
            if av < 0.85:
                return Sh(SILVER)                         # IVECO bar
            return BLACK
        if d is not None:
            return Sh(d)
        if k == 2:
            if av > W2 - 0.50:
                return Sh(SILVER_DK)                      # lamp housings
            return Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return BLACK if av < 0.75 else Sh(self.lv.bumper or self.lv.seam)


class IvecoEvadys(EvadysFace, CoachBus):
    """Iveco Evadys 12M (2014+), 12.11 x 2.55 x 3.5 m, high-floor intercity
    coach, doors 1-1-0. High window line (1.97-3.15 m) with big panes, the
    black swoosh that drops from the glazing behind the front door and the
    driver's window towards the skirt, roof A/C over the rear half. Photos
    369542 (front-right 3/4), 357822 and 444378 (fronts)."""
    real_len = 12.11
    axles = (2.66, 8.76)
    R_TOP = 13
    R_BAND0 = 7
    BAND = ((0.0, 12.11, 7, 12),)
    DOORS = ((0.30, 1.25, "hf"), (7.10, 8.05, "hf"))
    WRAP_K0 = 6
    REAR_GLASS = (8, 11)
    AC = (6.4, 10.0)
    AC_H = 0.18
    HATCHES = (4.0,)
    SWOOSH = (1.30, 0.45, 1.00)    # start x, width at the skirt, width at the sill

    def deco(self, x, k, right):
        x0, w_lo, w_hi = self.SWOOSH
        k0 = self.R_BAND0
        if 1 <= k < k0 and x >= x0:
            t = (k - 1) / max(1, k0 - 2)
            if x < x0 + lerp(w_lo, w_hi, t * t):
                return BLACK
        return None

    def pillars(self, right):
        if right:
            return (2.60, 4.70, 6.80, 8.30, 10.20)
        return (2.60, 4.55, 6.50, 8.45, 10.30)

    def markers(self):
        return (2.4, self.axles[0] + 1.6, self.axles[1] - 1.5, self.real_len - 0.45)

    def seams(self, right):
        return (4.0, 5.9, 9.8) if right else (4.0, 5.9, 7.6, 9.8)


class EvadysHFace:
    """Irisbus Evadys H front: windscreen up to the roof cap with the display
    inside, a black EVADYS band under the glass, livery-coloured face, round
    twin lamps low at the corners."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av > W2 - 0.07:
                return BLACK
            return LED if av < 0.95 else BLACK
        if k >= 6:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 5:
            return Sh(CHROME) if av < 0.40 else BLACK     # EVADYS badge on the band
        if k in (1, 2) and W2 - 0.48 < av < W2 - 0.10:
            return HEAD                                   # round lamps
        if d is not None:
            return Sh(d)
        if k in (3, 4):
            return Sh(self.lv.body)
        if k == 2:
            return Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class IrisbusEvadysH(EvadysHFace, CoachBus):
    """Irisbus Evadys H 12,8M (2005-2013), 12.8 x 2.55 x 3.47 m, high floor,
    doors 1-1-0 (middle door just ahead of the rear axle). Signature: the
    raised roof cap over the whole roof (red on P-transport), the silver
    roof-edge strip along the top of the side over the glazing, high window
    line. Photos 362213 (front-left 3/4), 291201 (front)."""
    real_len = 12.8
    axles = (2.65, 9.10)
    R_TOP = 13
    R_BAND0 = 7
    BAND = ((0.0, 12.8, 7, 12),)
    DOORS = ((0.30, 1.25, "hf"), (7.45, 8.40, "hf"))
    WRAP_K0 = 6
    REAR_GLASS = (8, 11)
    AC = None
    HATCHES = ()
    FAIRING = (0.35, 12.35, 0.22, 0.22)

    def deco(self, x, k, right):
        if k == self.R_TOP - 1 and 0.10 <= x < self.real_len - 0.12:
            return Sh(SILVER)                             # roof-edge strip
        return None

    def pillars(self, right):
        if right:
            return (2.60, 4.55, 6.50, 9.40, 11.10)
        return (2.60, 4.55, 6.50, 8.45, 10.40)

    def markers(self):
        return (2.4, self.axles[0] + 1.6, self.axles[1] - 1.6, self.real_len - 0.45)

    def seams(self, right):
        return (4.0, 6.0, 10.2) if right else (4.0, 6.0, 8.0, 10.2)


# ====================================================================== Arway
class ArwayFace:
    """Irisbus Arway front: windscreen under a thin body-colour cap, a black
    strip at its foot, smooth body-colour mask with the round Irisbus badge,
    rectangular headlamps set into the bumper corners with a dark slot."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av > W2 - 0.20:
                return Sh(self.lv.body)
            return LED if av < 0.90 else BLACK
        if k >= 6:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 5:
            return BLACK
        if d is not None and k >= 3:
            return Sh(d)
        if k == 4:
            return Sh(self.lv.body)
        if k == 3:
            return Sh(CHROME) if av < 0.14 else Sh(self.lv.body)    # badge
        if k == 2:
            if av > W2 - 0.55:
                return HEAD
            return Sh(GRILLE_DK) if av < 0.70 else Sh(self.lv.bumper or self.lv.body)
        if d is not None:
            return Sh(d)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class IrisbusArway(ArwayFace, CoachBus):
    """Irisbus Arway 12M (2006-2013), 12.0 x 2.55 x 3.3 m, high-floor
    intercity, doors 1-1-0. Rounded roof edges and corners, the first side
    window behind the driver / the front door dipping down towards the
    front, roof A/C pod over the front half. Photos 291240 (BusLine fronts),
    438698 (KAD, left side)."""
    real_len = 12.0
    axles = (2.65, 8.70)
    R_TOP = 13
    R_BAND0 = 7
    BAND = ((0.0, 12.0, 7, 12),)
    DOORS = ((0.30, 1.25, "hf"), (7.02, 7.97, "hf"))
    WRAP_K0 = 6
    REAR_GLASS = (8, 11)
    ROUND = 0.28
    AC = (2.6, 5.8)
    HATCHES = (8.6,)
    DIP = (1.30, 3.10, 5)          # the first window: sill drops to row 5 at the front

    def band_k0(self, x):
        a, b, k = self.DIP
        if x < a:
            return k
        if x < b:
            return int(round(lerp(k, self.R_BAND0, (x - a) / (b - a))))
        return None

    def pillars(self, right):
        if right:
            return (3.10, 4.75, 6.40, 8.10, 9.75, 11.10)
        return (3.10, 4.75, 6.40, 8.05, 9.70, 11.10)

    def markers(self):
        return (2.4, self.axles[0] + 1.6, self.axles[1] - 1.5, self.real_len - 0.45)

    def seams(self, right):
        return (4.1, 5.8, 9.9) if right else (4.1, 5.8, 7.4, 9.9)


# ====================================================================== Axer
class AxerFace:
    """Karosa Axer front: flat windscreen in a black frame under a body-colour
    cap, a narrow black strip under the glass, plain body-colour panel, a
    black band across the lower front carrying the twin round headlamps."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av > W2 - 0.22:
                return Sh(self.lv.body)
            return LED if av < 0.85 else BLACK
        if k >= 6:
            if av > W2 - 0.10:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 5:
            return BLACK                                  # strip under the glass
        if k == 2:
            if W2 - 0.62 < av < W2 - 0.12:
                return HEAD                               # twin round lamps
            return BLACK                                  # the black lamp band
        if d is not None:
            return Sh(d)
        if k in (3, 4):
            return Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class KarosaAxer(AxerFace, CoachBus):
    """Karosa Axer 12M C 956.1074 (2002-2006), 12.0 x 2.55 x 3.18 m, high
    floor, doors 2-2-0 (double front door, double middle door between the
    axles). Boxy body with a flat roof, straight high window line, small
    A/C pod, engine louvres at both rear corners. Photos 236262 / 334530 /
    303996 (brown metallic, front 3/4, front, rear 3/4), 137684 (white, left
    rear 3/4)."""
    real_len = 12.0
    axles = (2.70, 8.70)
    R_TOP = 12
    R_BAND0 = 6
    BAND = ((0.0, 12.0, 6, 11),)
    DOORS = ((0.25, 1.40, "hf"), (5.55, 6.75, "hf"))
    WRAP_K0 = 6
    REAR_GLASS = (7, 10)
    AC = (3.0, 5.4)
    AC_H = 0.18
    HATCHES = (8.0,)

    def deco(self, x, k, right):
        L = self.real_len
        if not right and L - 1.10 <= x < L - 0.35 and k in (4, 5):
            return Sh(GRILLE) if k == 5 else Sh(GRILLE_DK)  # left rear louvres
        return None

    def pillars(self, right):
        if right:
            return (2.85, 4.25, 6.85, 8.40, 9.90, 11.20)
        return (2.85, 4.25, 5.65, 7.05, 8.45, 9.85, 11.20)

    def seams(self, right):
        return (4.2, 9.9) if right else (1.5, 4.2, 5.6, 7.1, 9.9)


# ====================================================================== Récréo
class RecreoFace:
    """Karosa Récréo front: big windscreen up to a thin roof cap (display in
    the glass), dark IVECO letters on the body-colour panel under it, the
    rectangular headlamps set in the bumper corners."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            return Sh(self.lv.body) if av > W2 - 0.12 else (LED if av < 0.85 else BLACK)
        if k >= 5:
            if av > W2 - 0.10:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 4:
            if av < 0.45 and int((v + 2) / 0.17) % 2:
                return BLACK                              # IVECO letters
            return Sh(self.lv.body)
        if k == 1 and av > W2 - 0.45:
            return HEAD
        if d is not None:
            return Sh(d)
        if k in (2, 3):
            return Sh(self.lv.body)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class KarosaRecreo(RecreoFace, CoachBus):
    """Karosa C 955 Récréo (2001-2006), 12.0 x 2.5 x 3.1 m, high floor,
    doors 2-2-0 (glazed folding front door, double middle door between the
    axles). Framed sliding windows (frame line across every pane), flat
    roof with hatches and no A/C. Photos 298395 / 284409 (P-transport,
    front 3/4 and front)."""
    real_len = 12.0
    axles = (2.55, 8.55)
    R_TOP = 12
    R_BAND0 = 6
    BAND = ((0.0, 12.0, 6, 11),)
    DOORS = ((0.25, 1.35, "le"), (5.50, 6.70, "hf"))
    REAR_GLASS = (7, 10)
    AC = None
    HATCHES = (3.2, 6.4, 9.4)
    PANES = True

    def deco(self, x, k, right):
        # sliding-window frame: a black line across every pane one row
        # under the top of the band (the RegioBus HOPPER marks only every
        # other pane)
        b = self.band_at(x)
        if b and k == b[1] - 3 and 1.30 <= x < self.real_len - 0.22:
            if not (right and any(d0 <= x < d1 for d0, d1, _ in self.DOORS)):
                return BLACK
        return None

    def pillars(self, right):
        if right:
            return (2.55, 3.95, 7.10, 8.50, 9.90, 11.15)
        return (2.55, 3.95, 5.35, 6.75, 8.15, 9.55, 10.95)

    def seams(self, right):
        return (4.0, 9.7) if right else (1.4, 4.0, 5.4, 7.0, 9.7)


# ====================================================================== Irizar i4
class I4Face:
    """Irizar i4 front: deep windscreen whose lower part is black, a body-
    colour brow with the display inside the glass, the chrome Irizar line,
    slim headlamps at the corners, a small dark grille."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            return Sh(self.lv.body) if av > W2 - 0.25 else (LED if av < 0.90 else BLACK)
        if k >= 6:
            if av > W2 - 0.07:
                return BLACK
            return SCREEN_HI if k == top - 2 else SCREEN
        if k == 5:
            return BLACK
        if k == 4:
            return Sh(CHROME) if av < 0.35 else BLACK     # Irizar line on the black
        if k == 3:
            if av > W2 - 0.52:
                return HEAD
            return Sh(d) if d is not None else Sh(self.lv.body)
        if k == 2:
            return Sh(GRILLE_DK) if av < 0.22 else Sh(self.lv.body)
        if d is not None:
            return Sh(d)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class IrizarI4(I4Face, CoachBus):
    """Irizar i4 14M (Scania, 2010+), 13.97 x 2.55 x 3.5 m, high-floor
    intercity coach, three axles (tag axle), doors 1-1-0 with the middle
    door ahead of the rear bogie. Raised roof cap over the front half, high
    window line with big panes, black rear corner columns (the i4's rear
    lamp clusters) that wrap onto the sides. Photos 392863 (KAD, right
    side), 423806 (rear-left 3/4), 446538 (front)."""
    real_len = 13.97
    axles = (2.70, 9.25, 10.60)
    R_TOP = 13
    R_BAND0 = 7
    BAND = ((0.0, 13.97, 7, 12),)
    DOORS = ((0.30, 1.25, "hf"), (7.55, 8.45, "hf"))
    WRAP_K0 = 6
    REAR_GLASS = (8, 11)
    AC = None
    HATCHES = (11.2,)
    FAIRING = (0.55, 7.00, 0.24, 0.20)
    FAIRING_ROOF = True

    def deco(self, x, k, right):
        L = self.real_len
        if x >= L - 0.28 and 1 <= k < self.R_TOP - 1:
            return TAIL if k in (3, 4) else BLACK         # rear corner column
        return None

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        if av > W2 - 0.28 and 1 <= k < self.R_TOP - 1:
            if k in (3, 4):
                return TAIL
            if k == 6:
                return Sh(SILVER)                         # round reversing lamp ring
            return BLACK
        if k == 6 and av < 0.70:
            return BLACK                                  # black slits under the window
        return super().rear(v, z)

    def pillars(self, right):
        if right:
            return (2.75, 4.65, 6.55, 9.30, 11.20, 12.80)
        return (2.75, 4.65, 6.55, 8.45, 10.35, 12.25)

    def markers(self):
        return (2.4, 5.2, 7.2, 11.6, self.real_len - 0.50)

    def seams(self, right):
        return (4.3, 6.4, 12.2) if right else (4.3, 6.4, 8.4, 12.2)


# ====================================================================== SOR ICN
class IcnFace:
    """SOR ICN front: one black mask from the display down to 1.25 m (the
    very deep windscreen), the silver brow under it, big silver teardrop
    headlamp pods at the lower corners, light lower front."""

    def front_face(self, v, av, k, d):
        top = self.R_TOP
        if k >= top:
            return Sh(self.lv.roof)
        if k == top - 1:
            if av > W2 - 0.08:
                return BLACK
            return LED if av < 0.95 else BLACK
        if k >= 5:
            if av > W2 - 0.08:
                return BLACK
            return SCREEN_LHI if k >= top - 3 else SCREEN_L
        if k == 4:
            return BLACK                                  # foot of the black mask
        if k == 3:
            if av > W2 - 0.60:
                return Sh(SILVER) if av < W2 - 0.48 else HEAD   # pod rim + lamp
            return Sh(SILVER)                             # the silver brow
        if k == 2:
            if av > W2 - 0.55:
                return Sh(SILVER) if av > W2 - 0.12 else HEAD
            return Sh(d) if d is not None else Sh(self.lv.body)
        if d is not None:
            return Sh(d)
        if k == 1:
            return PLATE if av < 0.28 else Sh(self.lv.bumper or self.lv.body)
        return Sh(self.lv.bumper or self.lv.seam)


class SorICN(IcnFace, CoachBus):
    """SOR ICN 12,3 (2022+), 12.33 x 2.55 x 3.15 m, low-entry interurban,
    doors 1-2-0 with the double middle door just ahead of the rear axle.
    Unlike the CN: flat roof without the rear hump, deep flush glazing all
    along (1.25-2.85 m) under one row of body colour, a black rub line,
    near-square corners, roof A/C over the rear half; rear: KHK sticker
    over the rear window, louvres under it, slim vertical tail lamps.
    Photos 425211 (BusLine, rear-right 3/4 with the KHK sticker), 450544
    (front 3/4), 422941 / 437294 (ICN 10,5 KAD, left side, front)."""
    real_len = 12.33
    axles = (2.60, 9.10)
    R_TOP = 12
    R_BAND0 = 5                    # livery reference: CDS lettering rows 0-3
    BAND = ((0.0, 12.33, 4, 11),)
    RUB_ROW = 2                    # thin dark rub line (drawn by deco, not under lettering)
    RUB_C = (0x3A, 0x3C, 0x3F)
    DOORS = ((0.30, 1.25, "le"), (7.30, 8.50, "le"))
    REAR_GLASS = (7, 10)
    ROUND = 0.16
    GLASS_HI_ROWS = 2
    AC = (5.0, 8.9)
    AC_H = 0.22
    HATCHES = (3.6, 10.8)

    def deco(self, x, k, right):
        if k != self.RUB_ROW or x < 0.14 or x >= self.real_len - 0.10:
            return None
        if self.lv.slug == "cds":
            # keep the line out of the big CDS lettering between the axles
            mid = (self.axles[0] + self.axles[1]) / 2
            half = len(self.lv.TXT[0]) * self.pw() / 2 + 0.25
            if abs(x - mid) < half:
                return None
        return Sh(self.RUB_C)

    def rear(self, v, z):
        av = abs(v)
        k = self.row(z)
        g0, g1 = self.REAR_GLASS
        if g0 <= k <= g1 and av < W2 - 0.22:
            return super().rear(v, z)
        if k >= self.top_row(self.real_len - 0.1):
            return Sh(self.lv.roof)
        if 2 <= k <= 5 and W2 - 0.20 < av < W2 - 0.06:
            return TAIL                                   # slim vertical lamps
        if k in (5, 6) and av < W2 - 0.38:
            return Sh(GRILLE) if k == 6 else Sh(GRILLE_DK)   # louvres
        if k == 2 and av < 0.30:
            return PLATE
        if k == 0:
            return Sh(self.lv.bumper or self.lv.seam)
        d = self.lv.rear(self, v, k)
        return Sh(d) if d is not None else Sh(self.lv.body)

    def pillars(self, right):
        if right:
            return (2.45, 4.05, 5.70, 9.90, 11.20)
        return (2.45, 4.10, 5.75, 7.40, 9.05, 10.70)

    def markers(self):
        return (1.9, self.axles[0] + 1.6, self.axles[1] - 1.5, self.real_len - 0.45)


class SorICN105(SorICN):
    """SOR ICN 10,5: 10.6 m, middle door ahead of the rear axle."""
    real_len = 10.6
    axles = (2.55, 8.00)
    BAND = ((0.0, 10.6, 4, 11),)
    DOORS = ((0.30, 1.25, "le"), (6.25, 7.45, "le"))
    AC = (4.3, 7.8)
    HATCHES = (3.4, 9.2)

    def pillars(self, right):
        if right:
            return (2.45, 4.30, 8.80, 9.80)
        return (2.45, 4.10, 5.75, 7.40, 9.05)


class SorICN95(SorICN):
    """SOR ICN 9,5: 9.55 x 2.525 x 3.12 m (as the DPP / Praha ICN 9,5)."""
    real_len = 9.55
    axles = (2.45, 7.05)
    BAND = ((0.0, 9.55, 4, 11),)
    DOORS = ((0.30, 1.25, "le"), (5.35, 6.55, "le"))
    AC = (3.9, 7.0)
    HATCHES = (3.0, 8.3)

    def pillars(self, right):
        if right:
            return (2.45, 3.95, 7.85, 8.80)
        return (2.45, 4.00, 5.55, 7.10, 8.50)

    def markers(self):
        return (1.9, 4.2, self.axles[1] - 1.4, self.real_len - 0.45)


class KarosaAxerTown(KarosaAxer):
    """The Axer on a town line outside IREDO (MHD Nová Paka): no kraj sticker."""
    KHK_STICKER = False
