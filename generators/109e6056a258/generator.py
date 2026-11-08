"""Generator for arc_puzzle_bank_21_set23_bundle:hard_p05 — keyed boolean overlay of two shapes.

Rule (per canonical Racket): cell (0,0) holds an OP key, cell (0, cols-1)
holds a TRANSFORM key. Both corners are then cleared and the grid's two
4-connected components (by top-left order) are cropped as shapes A and B.
B is transformed by the tf-key (1=id, 2=rot-cw, 3=flip-lr, 4=flip-ud,
5=rot180, 6=rot-ccw). A and the transformed B are normalized and
boolean-overlaid per op-key on a max-size canvas:
  op 1 = both->8, only-A->2, only-B->3, neither->0
  op 2 = AND -> 8 else 0
  op 3 = XOR -> A-only 2 / B-only 3
  op 4 = A minus B -> 2
  op 5 (else) = B minus A -> 3
Output dims = max(bbox of A, transformed B). Shape COLORS are irrelevant
to the rule (it uses components, not specific colors).

Combinatorial axes: grid_h/w, op_key (1..5), tf_key (1..6), the two
shapes A/B, their colors and positions.
Degenerates: no_op, missing_shape, identical_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "109e6056a258"
VERSION = "2.1.0"  # POISON: tf-key corner (0,cols-1) was never set (transform branch dead) and op-key never hit 5. Now set BOTH corner keys, op 1..5 and tf 1..6, exercising all branches; shapes are components (rule color-agnostic)
TASK_ID = "109e6056a258"

SUMMARY = "(0,0)=op key (1..5), (0,cols-1)=transform key (1..6); two component shapes A,B boolean-overlaid (B transformed first)."

INVARIANTS = [
    "background is 0",
    "(0, 0) holds op key in 1..5; (0, cols-1) holds transform key in 1..6",
    "exactly two 4-connected component shapes (each >=3 cells), non-touching",
    "the two shapes use distinct colors so they stay separate components",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_op", "missing_shape", "identical_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "op_key":            {"type": "int", "default": "rng 1..5", "valid": "1..5"},
    "tf_key":            {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "4 (op+tf+2 shapes)", "valid": "3..5"},
    "position_bias":     {"type": "str", "default": "two_corner_keys_plus_two_shapes",
                          "valid": "two_corner_keys_plus_two_shapes"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n_lo, n_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 13)
        n_lo, n_hi = 4, 5
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n_lo, n_hi = 3, 5
    rng = ctx.draw_rng("layout")

    def _place(g, cells, color):
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        for _ in range(100):
            # keep shapes off row 0 (the corner-key row) so they never merge
            # with a corner key into one component.
            r0 = rng.randint(2, h - sh); c0 = rng.randint(0, w - sw)
            cells_p = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
            # require a 1-cell pad clear so this shape stays a separate component
            pad = set()
            for (r, c) in cells_p:
                for ddr in (-1, 0, 1):
                    for ddc in (-1, 0, 1):
                        pad.add((r + ddr, c + ddc))
            if any(0 <= r < len(g) and 0 <= c < len(g[0]) and g[r][c] != 0
                   for r, c in pad):
                continue
            for r, c in cells_p:
                g[r][c] = color
            return True
        return False

    for outer in range(60):
        g = full_grid(h, w, 0)
        op = rng.choice([1, 2, 3, 4, 5])
        tf = rng.choice([1, 2, 3, 4, 5, 6])
        g[0][0] = op
        g[0][w - 1] = tf
        # two distinct shape colors (rule is color-agnostic but distinct colors
        # keep the two shapes as separate components even if bboxes are near).
        col_a, col_b = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)
        cells_a = _build_motif(rng, rng.randint(n_lo, n_hi))
        cells_b = _build_motif(rng, rng.randint(n_lo, n_hi))
        if not _place(g, cells_a, col_a):
            continue
        if not _place(g, cells_b, col_b):
            continue
        return g
    raise ValueError("could not realize set23 p05 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_op":
        # (0,0) is bg -> op-key 0 -> falls through op cond to the else branch.
        g[0][w - 1] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[5 + dr][7 + dc] = 3
        return g
    if name == "missing_shape":
        # Only one component -> rule returns a trivial (list (list 0)).
        g[0][0] = 1
        g[0][w - 1] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[3 + dr][3 + dc] = 2
        return g
    if name == "identical_shapes":
        # Two congruent shapes -> AND/OR collapse, XOR/diff empty.
        g[0][0] = 2
        g[0][w - 1] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][7 + dc] = 3
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if grid[0][0] not in (1, 2, 3, 4, 5):
        msgs.append(f"bad op key {grid[0][0]}")
    if grid[0][w - 1] not in (1, 2, 3, 4, 5, 6):
        msgs.append(f"bad transform key {grid[0][w - 1]}")
    body = [row[:] for row in grid]
    body[0][0] = 0
    body[0][w - 1] = 0
    comps = components(body, same_color=True)
    if len(comps) != 2:
        msgs.append(f"expected exactly two same-color component shapes after clearing keys, got {len(comps)}")
    else:
        if len({c["color"] for c in comps}) != 2:
            msgs.append("shape colors are not distinct")
        if any(len(c["cells"]) < 3 for c in comps):
            msgs.append("a component has fewer than three cells")
        if any(any(r < 2 for r, _ in c["cells"]) for c in comps):
            msgs.append("a component touches the key rows")
    return msgs
