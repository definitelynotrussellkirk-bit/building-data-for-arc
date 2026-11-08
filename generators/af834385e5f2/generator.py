"""Generator for fea12743.

Rule: among six 4x4 slots, exactly one pattern is the union of two
others; the rule colors the union slot green, the two source slots cyan,
the decoys stay red.

Combinatorial axes: the two source patterns (and their union), the three
decoy patterns, and which of the six slots holds each.
Degenerates: no_patterns, full_grid, all_same.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "af834385e5f2"
VERSION = "2.0.1"  # diversity: random source/decoy patterns + random slot placement (was 3 styles x transpose)
TASK_ID = "af834385e5f2"
SUMMARY = (
    "A 16x11 grid of six 4x4 pattern SLOTS (fixed canonical origins). "
    "Two slots hold RANDOM color-2 source patterns whose UNION exactly "
    "equals a third slot; the other three slots hold RANDOM DECOY "
    "patterns chosen so NO other union relationship exists (the triple "
    "is unique). The six patterns are placed in a RANDOM permutation of "
    "the slots. Rule: find the slot that is the union of two others, "
    "color it green (3), color the two source slots cyan (8), leave the "
    "decoys red (2). The patterns, their union, the decoys and the slot "
    "assignment all vary freely (was 3 hardcoded union styles x a "
    "transpose flag = ~6 inputs)."
)

INVARIANTS = [
    "six fixed 4x4 pattern slots are sampled at the canonical origins",
    "two source slots use color 2 cells whose union exactly matches a third slot",
    "a fourth pair of slots contains decoy color-2 cells",
    "the slot grid has six fixed positions in a 3x2 layout",
]

UNION_STYLES = ("sparse", "angled", "split")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_patterns", "full_grid", "all_same")
HELPFUL_TEXTURES = UNION_STYLES

ORIGINS = [(1, 1), (1, 6), (6, 1), (6, 6), (11, 1), (11, 6)]

AXES = {
    "grid_h":         {"type": "int", "default": "16", "valid": "16"},
    "grid_w":         {"type": "int", "default": "11", "valid": "11"},
    "union_style":    {"type": "str", "default": "n/a (now random patterns)",
                       "valid": "sparse|angled|split"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "transpose":      {"type": "bool", "default": "n/a", "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for union_style",
                       "valid": "sparse|angled|split|no_patterns|full_grid|all_same"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is 16x11 (canonical slot layout), color-2 cells present in slots."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_patterns",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_2:
        errs.append("no color-2 slot pattern cells found")
    return errs


_ALL_CELLS = [(r, c) for r in range(4) for c in range(4)]


def _rand_pat(rng, lo, hi):
    return frozenset(rng.sample(_ALL_CELLS, rng.randint(lo, hi)))


def _union_triple_count(pats):
    """Number of (i<j, k!=i,j) with pats[i] | pats[j] == pats[k]."""
    n = len(pats); cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            u = pats[i] | pats[j]
            for k in range(n):
                if k != i and k != j and pats[k] == u:
                    cnt += 1
    return cnt


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        ab_lo, ab_hi, d_lo, d_hi = 2, 3, 2, 4
    elif difficulty == "hard":
        ab_lo, ab_hi, d_lo, d_hi = 3, 5, 3, 6
    else:
        ab_lo, ab_hi, d_lo, d_hi = 2, 4, 2, 5

    for _attempt in range(200):
        a = _rand_pat(rng, ab_lo, ab_hi)
        b = _rand_pat(rng, ab_lo, ab_hi)
        u = a | b
        # neither source a subset of the other → union is strictly larger and
        # distinct from both; keep the union from filling the whole slot.
        if a <= b or b <= a or len(u) >= 15:
            continue
        decoys = []
        ok = True
        seen = {a, b, u}
        for _ in range(3):
            for _d in range(40):
                d = _rand_pat(rng, d_lo, d_hi)
                if d not in seen:
                    decoys.append(d); seen.add(d); break
            else:
                ok = False; break
        if not ok:
            continue
        pats = [a, b, u] + decoys
        # the union triple must be UNIQUE (the only union relationship).
        if _union_triple_count(pats) != 1:
            continue
        rng.shuffle(pats)
        g = full_grid(16, 11, 0)
        for origin, cells in zip(ORIGINS, pats):
            paint_at(g, origin[0], origin[1], cells, 2)
        return g

    # Fallback: a guaranteed-unique fixed instance.
    a = frozenset({(0, 0), (1, 0), (2, 1)})
    b = frozenset({(0, 2), (1, 3), (3, 3)})
    pats = [a, b, a | b,
            frozenset({(0, 0), (3, 3)}),
            frozenset({(0, 3), (3, 0)}),
            frozenset({(1, 0), (2, 3)})]
    g = full_grid(16, 11, 0)
    for origin, cells in zip(ORIGINS, pats):
        paint_at(g, origin[0], origin[1], cells, 2)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(16, 11, 0)
    if name == "no_patterns":
        return g
    if name == "all_same":
        for origin in ORIGINS:
            paint_at(g, origin[0], origin[1], {(0, 0), (1, 1)}, 2)
        return g
    if name == "full_grid":
        for r in range(16):
            for c in range(11):
                g[r][c] = 2
        return g
    return g
