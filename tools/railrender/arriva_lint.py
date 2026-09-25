"""Arriva vlaky LINT 41 (846) / LINT 27 (832), Zlínský kraj: the Leo Express
LINT model (lint.py, geometry shared with the LE set) in the Arriva liveries:
  arrivamodra   Arriva blue wrap (Apr/May 2020-): LE white -> Arriva blue,
                anthracite roof shoulder / cab / swoosh / skirt and the orange
                anti-climber kept, silver doors, white "arriva" wordmarks on the
                sides behind the cab and on the lamp band.
  bilooranzova  Dec 2019 - Apr 2020: the LE Tenders white scheme with the Leo
                Express branding removed (no "leo" lettering, no front wordmark).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from railkit import Paint  # noqa: E402
import lint as L  # noqa: E402

BLUE = Paint(0x1C82CE)
WHITE = Paint(0xF2F4F6)
ANTH = Paint(0x3B3E43)

LIVERIES = {
    "arrivamodra": {
        "base": "bilooranzova",
        "body": BLUE, "patch": BLUE, "frontcorner": BLUE,
        "door": Paint(0xC9CDD2), "doorsplit": Paint(0x5A5F66),
        "letters": None, "grille": Paint(0x166AA8),
        "logo_front": (0xF2, 0xF4, 0xF6), "logo_dot": (0xF2, 0xF4, 0xF6),
        "wordmark": WHITE,
    },
    "bilooranzova": {"base": "bilooranzova", "letters": None, "logo_front": ANTH, "logo_dot": ANTH},
}

# white "arriva" wordmark on each side, below the first windows behind the cab
# (car-local metres from the cab nose, model z)
WORD_M = (4.0, 6.6)
WORD_Z = (3.75, 4.45)

_side = L.Car.side


def _side_with_wordmark(self, m, z, cs):
    wm = self.C.get("wordmark")
    if wm is not None:
        mc, _ = self.cab_local(m)
        if WORD_M[0] <= mc <= WORD_M[1] and WORD_Z[0] <= z <= WORD_Z[1]:
            # broken into letter blocks so it reads as lettering, not a stripe
            x = (mc - WORD_M[0]) / (WORD_M[1] - WORD_M[0])
            if x < 0.14 or int(x * 11) % 2 == 1 or z > WORD_Z[1] - 0.25:
                return wm
    return _side(self, m, z, cs)


# only liveries with a "wordmark" key are affected; the LE tables have none
L.Car.side = _side_with_wordmark


def rows_for(kind, color):
    """kind "lint41" | "lint27", color a key of LIVERIES."""
    return L.rows_for(kind, LIVERIES[color])
