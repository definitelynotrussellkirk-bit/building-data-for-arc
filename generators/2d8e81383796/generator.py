"""Generator for arc_puzzle_bank_21_set14_s:S14_E5.

Combinatorial axes (8): height, width, palette_kind, distractor_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_target, no_distractors, tied_peaks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2d8e81383796"
VERSION = "2.0.1"  # distinct=7: output = winning target shape cropped to 8, capped at the 7 fixed _TARGETS. Now random targets (vertical spine height k + random attachments) so the winning crop varies widely; distractors stay peak<k.
TASK_ID = "2d8e81383796"
SUMMARY = (
    "0-bg grid with N (2-5) connected non-bg components, each in its "
    "own distinct color. Rule: for each component, compute its "
    "max-col-peak (max over columns of the count of cells the "
    "component occupies in that column) — equivalently, the longest "
    "vertical run within the component's footprint. Pick the "
    "component with the STRICTLY LARGEST max-col-peak (ties broken by "
    "size, then top-left). Output is that component's bbox crop, "
    "recolored so non-bg cells become 8 (bbox holes stay 0)."
)

# Rivals: 'output is input' refuted by demos (output is small crop).
# 'pick largest by size' refuted by demos where the winner has fewer
# cells but a taller column. 'pick by max-row-peak (widest)' refuted
# by demos where winner has narrow but tall profile. 'output the
# crop in original color' refuted by demos showing the recolor to 8.
# 'output the bbox painted solid 8' refuted by demos where bbox holes
# stay 0. 3 demos with target having distinctly tallest column and
# distractors of varied widths pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 connected non-bg components (rule's selection is invisible with 1)",
    "exactly one component has STRICTLY largest max-col-peak (no ties on the primary criterion)",
    "components use distinct colors so each is its own 4-conn component",
    "components are separated by ≥1 bg cell on all sides",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_target", "no_distractors", "tied_peaks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 12..15", "valid": "10..20"},
    "width":          {"type": "int", "default": "rng 10..13", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "distractor_count": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "target_plus_distractors",
                       "valid": "target_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TARGETS = [
    [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (1, 2)],           # T-shape h=4
    [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2)],           # Z-shape h=4
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],                   # I-5 vertical h=5
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1)],           # L-6 h=5
    [(0, 0), (1, 0), (2, 0), (3, 0), (2, 1), (2, 2)],           # plus-tall h=4
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (0, 1)],           # mirrored L
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],           # I-6 h=6
]
_DISTRACTORS = [
    [(0, 0), (0, 1), (0, 2)],                                   # I-3 horizontal h=1
    [(0, 0), (1, 0), (1, 1)],                                   # L h=2
    [(0, 0), (0, 1), (1, 1), (1, 2)],                           # S-tetromino h=2
    [(0, 0), (1, 0), (0, 1)],                                   # L-tromino h=2
    [(0, 0), (0, 1), (0, 2), (0, 3)],                           # I-4 horizontal h=1
    [(0, 0), (0, 1), (1, 0), (1, 1)],                           # 2×2 square h=2
    [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)],                   # P-shape h=2
    [(0, 0), (0, 1), (0, 2), (1, 1)],                           # T-down h=2
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return
    raise ValueError("could not place component")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 distinct non-bg colors (components for max-col-peak rule)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        return [f"expected >=2 distinct non-bg colors, got {len(colors)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 11, 13)
        w = ctx.draw_int("width", 10, 12)
        distractor_count = ctx.draw_int("distractor_count", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 16, 20)
        w = ctx.draw_int("width", 14, 18)
        distractor_count = ctx.draw_int("distractor_count", 3, 4)
    else:
        h = ctx.draw_int("height", 13, 16)
        w = ctx.draw_int("width", 11, 14)
        distractor_count = ctx.draw_int("distractor_count", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Sample a wider color pool so each component has a distinct color
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 1 + distractor_count)
    # output = the WINNING target's crop recolored to 8, so distinct outputs were
    # capped at the 7 fixed _TARGETS. Build a RANDOM target: a tall vertical spine
    # (height k) guarantees max-col-peak=k > every distractor's, plus random
    # attachments in other columns -> the winning crop shape varies widely.
    if difficulty == "easy":
        k = rng.randint(3, 4)
    elif difficulty == "hard":
        k = rng.randint(5, 7)
    else:
        k = rng.randint(4, 6)
    target_shape = _rand_target(rng, k)
    target_col_peak = _max_col_peak(target_shape)
    # Pick distractors that ALL have strictly smaller max-col-peak.
    valid_distractors = [d for d in _DISTRACTORS
                         if _max_col_peak(d) < target_col_peak]
    if len(valid_distractors) < distractor_count:
        valid_distractors = _DISTRACTORS
    rng.shuffle(valid_distractors)
    _place(g, rng, target_shape, colors[0])
    for color, shape in zip(colors[1:], valid_distractors[:distractor_count]):
        _place(g, rng, shape, color)
    return g


def _rand_target(rng, k):
    """Random component whose max-col-peak is exactly k: a height-k vertical spine
    at col 0 plus 1-5 random attachments in columns >=1 (so no other column reaches
    k). Normalized to the origin."""
    from collections import Counter
    cells = {(r, 0) for r in range(k)}
    extra = rng.randint(1, 5)
    tries = 0
    while extra > 0 and tries < 80:
        tries += 1
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(0, 1), (1, 1), (-1, 1), (0, 1)])  # bias rightward
        nr, nc = r + dr, c + dc
        if (nr, nc) in cells or nc < 1 or nr < 0 or nr >= k:
            continue
        # keep every non-spine column strictly below k
        col_count = sum(1 for (rr, cc) in cells if cc == nc)
        if col_count + 1 >= k:
            continue
        cells.add((nr, nc)); extra -= 1
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _max_col_peak(shape):
    """Max over columns of the count of cells of `shape` in that column."""
    from collections import Counter
    cols = Counter(c for _, c in shape)
    return max(cols.values()) if cols else 0


def _draw_from_degenerate(name, rng):
    h, w = 13, 11
    g = full_grid(h, w, 0)
    if name == "no_target":
        # Distractors only, no target with tall column peak — rule has no winner.
        for dr, dc in _DISTRACTORS[0]: g[2 + dr][2 + dc] = 3
        for dr, dc in _DISTRACTORS[1]: g[6 + dr][2 + dc] = 4
        return g
    if name == "no_distractors":
        # Single target, no distractors — rule's selection is trivial.
        for dr, dc in _TARGETS[0]: g[2 + dr][2 + dc] = 3
        return g
    if name == "tied_peaks":
        # Two targets share max column peak — winner is ambiguous.
        for dr, dc in _TARGETS[0]: g[2 + dr][2 + dc] = 3
        for dr, dc in _TARGETS[1]: g[2 + dr][7 + dc] = 4
        return g
    return g
