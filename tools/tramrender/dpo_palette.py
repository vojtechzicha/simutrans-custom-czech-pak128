"""DP Ostrava tram livery colours (the turquoise scheme, `dpotyrkysova`).

Decided 2026-10-18 for the redrawn Škoda 39T, to be used for the other DPO
trams too, "as real as possible while distinctive":

- BODY 00ADD6. DPO's design manual gives the turquoise as Pantone 312 C /
  RAL 5012 (screen 1DD3FF); Pantone 312 C is about 00A9CE, and sunlit sides on
  photos of 39T 1751-1768 sample at hue 192-200 deg, fully saturated. 00ADD6 is
  within a few per cent of the Pantone value and is already the blue of every
  DPO bus, trolleybus and tram sheet in the set, so it stays.
- ROOF 44C1E4. The roof fairings are the same turquoise paint, and from above
  (39T 1758, a pair at a stop) the roof reads lighter and a little greyer than
  the sides: tops catch the sky. The earlier dark teal roof (007B94) made the
  trams duller than the real ones; painting the roof in the body colour loses
  the roof edge. A sunlit tint keeps both the real colour and the shape.
- SHOULDER: one in-between step where the body curves into the roof, sides
  flat in every view (one blue on every side, as the DPO sheets always had),
  so the roof edge reads the same in all 8 views.
- Black front mask, white line and white door frames from the photos; window
  glass stays on the lit-at-night specials.
"""

BODY = 0x00ADD6
ROOF = 0x44C1E4
WHITE = 0xECEEEE
DOOR_FRAME = 0xE4E6E6
MASK = 0x1A1C1E
MASK_TOP = 0x24282B
CAB_GLASS = 0x34444E
CAB_GLASS_TOP = 0x40525C
PILLAR = 0x1C1E20
SKIRT_RECESS = 0x17323E
BELLOWS = 0xB4B6B8
BELLOWS_FOLD = 0x8A8C8E
WHEEL = 0x26282A
PANTO_ARM = (0x44, 0x48, 0x4C)
PANTO_HEAD = (0x1E, 0x20, 0x22)
GLASS = 0x4D4D4D          # special: passenger glass, lit at night when loaded
HEADLIGHT = 0xFFFF53      # special: always lit
TAIL_LIGHT = 0xFF211D     # special: always lit
