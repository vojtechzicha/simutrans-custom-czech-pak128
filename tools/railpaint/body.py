"""Zone maps for any pak128 railcar body, built from pure-view rules + warp.

A Body is one sprite row drawn identically (same silhouette) in one or more
reference liveries. Its config gives, for the pure views, the row where the
painted side / end face starts and rules that name each row band; the diagonal
views get their zones through warp.py. Zones:

  T, FIX (keep base pixel), GLASS, HEAD, TAIL, ROOF, ROOF_EDGE (lowest roof row
  along the side, computed), S_* side face, E_* end face.

Every labelled pixel also carries k (row offset inside its face band, 0 = the
first painted row under the roof) and u (0..1 along the side / across the end).
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warp

T = np.array((231, 255, 255))
DIRS = ["w", "nw", "n", "ne", "e", "se", "s", "sw"]
SIDE_COLS, END_COLS, DIAG_COLS = (3, 7), (1, 5), (0, 2, 4, 6)
LIT = (0x4D4D4D, 0x57656F)


def hexarr(a):
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


class Body:
    """cfg keys:
      name, refs [(path,row),...], base (index of the ref used for FIX pixels),
      side_top {3:y, 7:y}, end_top {1:y, 5:y},
      side_rows [(k0, k1, zone), ...]  (inclusive; rows past the last -> FIX),
      end_rows  [(k0, k1, zone), ...],
      doors {3: [(x0,x1),...], 7: [...]} tile x ranges, door_rows (k0,k1),
      glass_extra: callable(refs_tile, col) -> bool mask of extra glass pixels,
      fix: callable(body, col, lab) -> lab   (final per-body touch-ups)
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.name = cfg["name"]
        self.refs = np.stack([np.array(Image.open(p).convert("RGB"))[r * 128:(r + 1) * 128, :1024]
                              for p, r in cfg["refs"]]).astype(int)
        m0 = np.all(self.refs[0] == T, axis=-1)
        for i in range(1, len(self.refs)):
            if (np.all(self.refs[i] == T, axis=-1) != m0).sum() > 40:
                print(f"warning {self.name}: ref {i} silhouette differs by "
                      f"{(np.all(self.refs[i] == T, axis=-1) != m0).sum()} px")
        self.base = self.refs[cfg.get("base", 0)].copy()
        self.zones = ["T", "FIX", "GLASS", "HEAD", "TAIL", "ROOF", "ROOF_EDGE", "S_DOOR"]
        for rows in (cfg["side_rows"], cfg["end_rows"]):
            allrows = [r for v in rows.values() for r in v] if isinstance(rows, dict) else rows
            for _, _, z in allrows:
                if z not in self.zones:
                    self.zones.append(z)
        for z in cfg.get("extra_zones", []):
            if z not in self.zones:
                self.zones.append(z)
        self.Z = {n: i for i, n in enumerate(self.zones)}
        self.lab = np.full((128, 1024), self.Z["FIX"], int)
        self.K = np.full((128, 1024), -99, int)
        self.U = np.full((128, 1024), -1.0)
        self.face = np.zeros((128, 1024), "U1")   # 'S', 'E', 'R' (roof) or ''
        self.build()

    # ---- pure views -------------------------------------------------------
    def specials(self, col):
        t = self.refs[:, :, col * 128:(col + 1) * 128]
        v = hexarr(t)
        glass = np.isin(v, LIT).any(axis=0)
        if "glass_extra" in self.cfg:
            glass |= self.cfg["glass_extra"](t, col)
        head = (v == 0xFFFF53).any(axis=0)
        tail = (v == 0xFF211D).any(axis=0)
        return glass, head, tail

    def pure(self, col, top, rows, face):
        Z = self.Z
        if isinstance(rows, dict):
            rows = rows[col]
        t = self.refs[:, :, col * 128:(col + 1) * 128]
        body = ~np.all(t[0] == T, axis=-1)
        glass, head, tail = self.specials(col)
        lab = np.full((128, 128), Z["FIX"], int)
        lab[~body] = Z["T"]
        K = np.full((128, 128), -99, int)
        ys, xs = np.where(body)
        x0, x1 = xs.min(), xs.max()
        U = np.full((128, 128), -1.0)
        for y, x in zip(ys, xs):
            k = y - top
            K[y, x] = k
            U[y, x] = (x - x0) / max(1, x1 - x0)
            if k < 0:
                lab[y, x] = Z["ROOF"]
                continue
            for k0, k1, z in rows:
                if k0 <= k <= k1:
                    lab[y, x] = Z[z]
                    break
        if face == "S":
            dr = self.cfg.get("door_rows")
            doors = self.cfg.get("doors", {})
            doors = doors(self, col, top) if callable(doors) else doors.get(col, [])
            self.door_ranges = getattr(self, "door_ranges", {})
            self.door_ranges[col] = doors
            for a, b in doors:
                for y in range(128):
                    for x in range(a, b + 1):
                        if body[y, x] and dr and dr[0] <= K[y, x] <= dr[1]:
                            lab[y, x] = Z["S_DOOR"]
        lab[glass & body] = Z["GLASS"]
        lab[head & body] = Z["HEAD"]
        lab[tail & body] = Z["TAIL"]
        return lab, K, U

    # ---- all views --------------------------------------------------------
    def build(self):
        cfg, Z = self.cfg, self.Z
        for col in SIDE_COLS:
            lab, K, U = self.pure(col, cfg["side_top"][col], cfg["side_rows"], "S")
            self.put(col, lab, K, U, "S")
        for col in END_COLS:
            lab, K, U = self.pure(col, cfg["end_top"][col], cfg["end_rows"], "E")
            self.put(col, lab, K, U, "E")
        self.fits = {}
        for col in DIAG_COLS:
            self.diag(col)
        if cfg.get("windscreen"):
            self.windscreen(**cfg["windscreen"]) if isinstance(cfg["windscreen"], dict) else self.windscreen()
        if "fix" in cfg:
            for col in range(8):
                cfg["fix"](self, col)
        self.roof_edge()

    def put(self, col, lab, K, U, face):
        sl = slice(col * 128, (col + 1) * 128)
        self.lab[:, sl], self.K[:, sl], self.U[:, sl] = lab, K, U
        f = np.where(lab == self.Z["ROOF"], "R", face)
        f[lab == self.Z["T"]] = ""
        self.face[:, sl] = f

    def diag(self, col):
        Z = self.Z
        key = (self.name, col)
        fr = warp.fit_view(self.refs, col, self.cfg["end_top"], verbose=False)
        self.fits[col] = fr
        (ys, xs), m = warp.source_maps(self.refs, col, fr, self.cfg["end_top"])
        sx, sy, sok, sd, sinb = m["side"]
        ex, ey, eok, ed, einb = m["end"]
        sl = slice(col * 128, (col + 1) * 128)
        lab = np.full((128, 128), Z["T"], int)
        K = np.full((128, 128), -99, int)
        U = np.full((128, 128), -1.0)
        face = np.full((128, 128), "", "U1")
        glass, head, tail = self.specials(col)
        sc, ec = warp.SIDE_SRC[col], warp.END_SRC[col]
        stop = self.cfg["side_top"][sc]
        for i in range(len(xs)):
            y, x = ys[i], xs[i]
            use_end = eok[i] and (ed[i] < sd[i] or not sok[i])
            if use_end:
                lab[y, x] = self.lab[ey[i], ec * 128 + ex[i]]
                K[y, x] = self.K[ey[i], ec * 128 + ex[i]]
                U[y, x] = self.U[ey[i], ec * 128 + ex[i]]
                face[y, x] = "E"
            elif sok[i]:
                lab[y, x] = self.lab[sy[i], sc * 128 + sx[i]]
                K[y, x] = self.K[sy[i], sc * 128 + sx[i]]
                U[y, x] = self.U[sy[i], sc * 128 + sx[i]]
                face[y, x] = "R" if lab[y, x] == Z["ROOF"] else "S"
            else:
                # outside both faces: roof above the side face, else fixed parts
                if sy[i] < stop:
                    lab[y, x] = Z["ROOF"]; face[y, x] = "R"
                    K[y, x] = sy[i] - stop
                else:
                    lab[y, x] = Z["FIX"]
            if lab[y, x] in (Z["GLASS"], Z["HEAD"], Z["TAIL"]) and not (glass[y, x] or head[y, x] or tail[y, x]):
                # the source was glass / a lamp but this pixel isn't: it is the
                # frame around it. Opt-in (cfg diag_glass): glass-like pixels
                # stay glass, the rest take the face zone of their row;
                # default: keep the base pixel
                dg = self.cfg.get("diag_glass")
                if dg is not None and lab[y, x] == Z["GLASS"]:
                    if dg(self.base[y, sl][x]):
                        continue
                    lab[y, x] = self.row_zone(face[y, x], K[y, x], sc if face[y, x] == "S" else ec)
                else:
                    lab[y, x] = Z["FIX"]
        lab[glass & (lab != Z["T"])] = Z["GLASS"]
        lab[head] = Z["HEAD"]
        lab[tail] = Z["TAIL"]
        self.lab[:, sl], self.K[:, sl], self.U[:, sl] = lab, K, U
        self.face[:, sl] = face

    def row_zone(self, face, k, col):
        """Zone the row rules give to row offset k on a face of pure view col."""
        rows = self.cfg["side_rows"] if face == "S" else self.cfg["end_rows"]
        if isinstance(rows, dict):
            rows = rows[col]
        for k0, k1, z in rows:
            if k0 <= k <= k1:
                return self.Z[z]
        return self.Z["FIX"]

    def roof_edge(self):
        """ROOF pixels touching the first side-face row (the roof's lower edge
        along the side wall) -> ROOF_EDGE; a continuous staircase line in the
        diagonal views."""
        Z = self.Z
        top = (self.face == "S") & (self.K == 0)
        edge = np.zeros_like(top)
        edge[:-1] |= top[1:]                      # directly above
        for col in DIAG_COLS:
            sl = slice(col * 128, (col + 1) * 128)
            t = top[:, sl]
            e = np.zeros_like(t)
            e[:, 1:] |= t[:, :-1]                 # left / right neighbours
            e[:, :-1] |= t[:, 1:]
            edge[:, sl] |= e
        self.lab[edge & (self.lab == Z["ROOF"])] = Z["ROOF_EDGE"]

    def windscreen(self, zones=("E_WIN",), chroma=18, face="E"):
        """Neutral grey pixels inside the given end zones are windscreen glass
        (not lit): zone WSCREEN, painted as the base pixel."""
        Z = self.Z
        if "WSCREEN" not in Z:
            self.zones.append("WSCREEN"); Z["WSCREEN"] = len(self.zones) - 1
        b = self.base.astype(int)
        neutral = (b.max(axis=-1) - b.min(axis=-1)) < chroma
        for z in zones:
            self.lab[(self.lab == Z[z]) & neutral & (self.face == face)] = Z["WSCREEN"]

    # ---- shading ----------------------------------------------------------
    def shade(self, edge_tol=0.14, lo=0.55, hi=1.35):
        """Per-pixel lighting factor relative to each zone's median in the
        pure views, median over the reference liveries; face-level per tile
        except clear edge highlights / shadows."""
        L = lum(self.refs.astype(float))
        fac = np.ones((128, 1024))
        for zn, zi in self.Z.items():
            if zn in ("T", "FIX", "GLASS", "HEAD", "TAIL"):
                continue
            m = self.lab == zi
            if not m.any():
                continue
            pure = np.zeros_like(m)
            cols = END_COLS if zn.startswith("E_") else SIDE_COLS
            for c in cols:
                pure[:, c * 128:(c + 1) * 128] = m[:, c * 128:(c + 1) * 128]
            if not pure.any():
                pure = m
            rel = np.median(np.stack([L[i] / max(np.median(L[i][pure]), 1.0) for i in range(len(L))]), axis=0)
            if zn in ("ROOF", "ROOF_EDGE"):
                fac[m] = rel[m]
                continue
            for c in range(8):
                mc = np.zeros_like(m); mc[:, c * 128:(c + 1) * 128] = m[:, c * 128:(c + 1) * 128]
                if not mc.any():
                    continue
                face = np.median(rel[mc])
                px = rel[mc]
                fac[mc] = np.where(np.abs(px - face) > edge_tol, px, face)
        return np.clip(fac, lo, hi)

    # ---- previews ---------------------------------------------------------
    PAL = [(231, 255, 255), (60, 60, 60), (0, 0, 0), (255, 255, 0), (255, 0, 0), (130, 130, 130), (200, 200, 255)]

    def falsecolor(self):
        rng = np.random.RandomState(3)
        pal = list(self.PAL) + [tuple(int(v) for v in rng.randint(40, 255, 3)) for _ in range(len(self.zones))]
        out = np.zeros((128, 1024, 3), np.uint8)
        for n, i in self.Z.items():
            out[self.lab == i] = pal[i]
        return out, {n: pal[i] for n, i in self.Z.items()}


def auto_doors(k_probe, min_w=2, dark=85):
    """Door x-ranges in a pure side view: columns where the base reference is
    dark blue/navy at row offset k_probe (Najbrt doors)."""
    def f(body, col, top):
        t = body.base[:, col * 128:(col + 1) * 128]
        y = top + k_probe
        xs = [x for x in range(128) if lum(t[y, x].astype(float)) < dark and t[y, x][2] > t[y, x][0] + 15]
        runs, cur = [], []
        for x in xs:
            if cur and x != cur[-1] + 1:
                runs.append(cur); cur = []
            cur.append(x)
        if cur:
            runs.append(cur)
        return [(r[0], r[-1]) for r in runs if len(r) >= min_w]
    return f
