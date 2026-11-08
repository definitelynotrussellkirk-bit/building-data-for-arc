"""Primitive registry for the generic generator family — SCAFFOLD.

Each primitive is a small, self-inverse-free transformation with:
  - apply(grid, params, rng) -> grid      (Python; derives the output)
  - racket(params) -> str                 (the equivalent Racket program, the
                                           model's supervision target)
  - sample(rng, grid) -> params           (draw legal params for this grid)

Compose 1-3 of these into a chain (compose.py) to manufacture NOVEL task
concepts. The backlog from the eval-miss audit (C1-C5) tells us which families
matter most; the ones we already have a Racket primitive for are implemented,
the rest are stubbed with a TODO + the target Racket head.

Grid = list[list[int]], background = 0 unless a primitive says otherwise.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# helpers
def _dims(g): return len(g), len(g[0])
def _copy(g): return [row[:] for row in g]
def _colors(g, bg=0): return sorted({v for row in g for v in row if v != bg})


# --------------------------------------------------------------------------
# IMPLEMENTED primitives (we have the Racket head for each)

class RecolorMap:
    name = "recolor_map"
    def sample(self, rng, g):
        cs = _colors(g) or [1]
        src = rng.choice(cs)
        dst = rng.choice([c for c in range(1, 10) if c != src])
        return {"src": src, "dst": dst}
    def apply(self, g, p, rng):
        return [[p["dst"] if v == p["src"] else v for v in row] for row in g]
    def racket(self, p):
        return f"(recolor g {p['src']} {p['dst']})"


class Dihedral:
    name = "dihedral"
    _ops = ["flip-lr", "flip-ud", "rotate-cw", "rotate-ccw", "rotate-180", "transpose"]
    def sample(self, rng, g): return {"op": rng.choice(self._ops)}
    def apply(self, g, p, rng):
        op = p["op"]
        if op == "flip-lr": return [row[::-1] for row in g]
        if op == "flip-ud": return g[::-1]
        if op == "rotate-cw": return [list(r) for r in zip(*g[::-1])]
        if op == "rotate-ccw": return [list(r) for r in zip(*g)][::-1]
        if op == "rotate-180": return [row[::-1] for row in g[::-1]]
        return [list(r) for r in zip(*g)]                       # transpose
    def racket(self, p): return f"({p['op']} g)"


class Gravity:
    name = "gravity"
    def sample(self, rng, g): return {"dir": rng.choice(["down", "up", "left", "right"])}
    def apply(self, g, p, rng):
        h, w = _dims(g); d = p["dir"]; out = [[0] * w for _ in range(h)]
        if d in ("down", "up"):
            for c in range(w):
                col = [g[r][c] for r in range(h) if g[r][c] != 0]
                if d == "down":
                    for i, v in enumerate(reversed(col)): out[h - 1 - i][c] = v
                else:
                    for i, v in enumerate(col): out[i][c] = v
        else:
            for r in range(h):
                row = [v for v in g[r] if v != 0]
                if d == "right":
                    for i, v in enumerate(reversed(row)): out[r][w - 1 - i] = v
                else:
                    for i, v in enumerate(row): out[r][i] = v
        return out
    def racket(self, p): return f'(gravity g "{p["dir"]}")'


class RaySmear:
    """From every cell of `color`, shoot a ray in `direction` until it hits a
    wall or a non-bg cell, painting the trail in `color`. Explodes component
    count from a scattered field -> the 142ca369 eval-miss family (same-size
    grid, comps 8 -> 60). Exactly mirrors the prelude `smear-color`: row-major
    source order, and already-painted trail cells block later rays.
    """
    name = "ray_smear"
    _dirs = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

    def _smear(self, g, color, d):
        h, w = _dims(g); dr, dc = self._dirs[d]; out = _copy(g)
        for r in range(h):
            for c in range(w):
                if g[r][c] != color:
                    continue
                rr, cc = r + dr, c + dc
                while 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                    out[rr][cc] = color; rr += dr; cc += dc
        return out

    def sample(self, rng, g):
        cs = _colors(g) or [1]
        opts = [(col, d) for col in cs for d in self._dirs]   # prefer non-no-op
        rng.shuffle(opts)
        for col, d in opts:
            if self._smear(g, col, d) != g:
                return {"color": col, "dir": d}
        return {"color": cs[0], "dir": "down"}

    def apply(self, g, p, rng):
        return self._smear(g, p["color"], p["dir"])

    def racket(self, p):
        return f"(smear-color g {p['color']} '{p['dir']})"


class Denoise:
    """Remove minority single-cell specks (keeps the dominant structure)."""
    name = "denoise"
    def sample(self, rng, g): return {}
    def apply(self, g, p, rng):
        h, w = _dims(g); out = _copy(g)
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0: continue
                same = any(0 <= r+dr < h and 0 <= c+dc < w and g[r+dr][c+dc] == g[r][c]
                           for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if not same: out[r][c] = 0       # isolated speck -> bg
        return out
    def racket(self, p):
        return "(denoise-grid g)"                # prelude head (verified parity)


# --------------------------------------------------------------------------
# STUBBED primitives — from the eval-miss backlog (C1-C5). Each names the
# target Racket head; fill apply() when promoting from scaffold.

class BilateralGravity:           # backlog B2 / C5
    name = "bilateral_gravity"
    def sample(self, rng, g): raise NotImplementedError
    def apply(self, g, p, rng): raise NotImplementedError    # objects fall toward a central block from both sides
    def racket(self, p): return "(gravity-toward-block g block-rows)"

class PeriodColorOverride:        # backlog B1 / C3
    name = "period_color_override"
    def sample(self, rng, g): raise NotImplementedError
    def apply(self, g, p, rng): raise NotImplementedError    # pair defines period, singleton overrides fill color
    def racket(self, p): return "(tile-period-with-override g)"

class SubshapeRecolor:            # backlog B3 / C3
    name = "subshape_recolor"
    def sample(self, rng, g): raise NotImplementedError
    def apply(self, g, p, rng): raise NotImplementedError    # detect embedded plus/T/square, recolor it
    def racket(self, p): return "(recolor-embedded-subshape g sub color)"

class PeriodicRepair:             # backlog B5 / C2
    name = "periodic_repair"
    def sample(self, rng, g): raise NotImplementedError
    def apply(self, g, p, rng): raise NotImplementedError    # reconstruct an occluded rectangle from the tile period
    def racket(self, p): return "(repair-occlusion g 8)"


# IMPLEMENTED = composable now; BACKLOG = promote next (have Racket head, need apply()).
IMPLEMENTED = [RecolorMap(), Dihedral(), Gravity(), Denoise(), RaySmear()]
BACKLOG = [BilateralGravity(), PeriodColorOverride(), SubshapeRecolor(), PeriodicRepair()]
REGISTRY = {p.name: p for p in IMPLEMENTED}
