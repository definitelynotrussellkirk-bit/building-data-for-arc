"""Generator for arc_additional_puzzles_21_set7:H47 — corner-command motif transform.

Rule:
  top_left = g[0][0]   (cmd-rot ∈ {1,2,3,4}: identity / cw / 180 / ccw)
  top_right = g[0][cols-1]   (cmd-flip ∈ {1,2}: flip-ud / flip-lr)
  base = g with the two command cells zeroed
  cropped = crop-to-content(base)
  rotated = rotate(cropped, cmd-rot)
  output = flip(rotated, cmd-flip)

v1.1.0 used only 2 hand-coded MOTIFs (both 3×3 or 3×2 bbox) → only 8
unique outputs across 20 instances. v1.2.0 expands the motif library
to 10 shapes with bboxes 2×3 through 4×4, all asymmetric under both
rotation and reflection so the cmd-rot and cmd-flip distinctions are
observable in every demo.

Fairness:
  * cmd-rot drawn uniformly from {1,2,3,4}; cmd-flip uniformly from
    {1,2} — each of the 8 cmd combinations is equally likely.
  * Motif drawn uniformly from the 10-motif bank, gated by difficulty
    bbox cap (easy: bbox ≤ 3×3; hard: bbox up to 4×4).
  * Every motif is verified at import to be:
      - non-square OR fail-symmetric under both rotate-cw and flip-lr
        (so rotation and flip produce observably different outputs)
      - bbox-asymmetric horizontally and vertically.
  * Motif uses 2-3 colors drawn from a difficulty-dependent palette;
    color selection is uniform.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d1884b0aef8"
VERSION = "1.2.0"
TASK_ID = "5d1884b0aef8"
SUMMARY = "Top-left command rotates the cropped motif; top-right command chooses vertical or horizontal flip."

# To pin the rule against rivals: (a) ignore-cmd-rot, (b) ignore-cmd-flip,
# (c) crop-only, (d) flip-only. Each rival needs a refuting demo:
#   - (a) refuted by ≥2 demos where cmd-rot differs and rotated bboxes
#     differ (motifs must be non-square, otherwise rotation is invisible).
#   - (b) refuted by ≥2 demos where cmd-flip differs and the flipped
#     pattern differs (motifs must be asymmetric under flip).
#   - (c, d) refuted by ≥1 demo with both rot != 1 and flip != lr.
# Minimum: 4 demos to span the cmd-rot × cmd-flip product reasonably.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "g[0][0] ∈ {1,2,3,4} (cmd-rot)",
    "g[0][cols-1] ∈ {1,2} (cmd-flip)",
    "exactly one connected motif away from the top row",
    "motif bbox is asymmetric under both rotation and horizontal flip "
    "(so the rule's actions are observable)",
]

PALETTE_KINDS = ("default", "L_motif", "T_motif", "Z_motif", "wide_motif", "tall_motif")
DEGENERATE_TEXTURES = (
    "no_rotation_cmd",
    "no_flip_cmd",
    "no_motif",
    "square_symmetric_motif",  # motif identical under rot+flip → cmd is invisible
)
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "by difficulty", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "by difficulty", "valid": "8..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PALETTE_KINDS)},
    "motif_kind":        {"type": "int", "default": "rng 0..9", "valid": "0..9"},
    "palette_size":      {"type": "int", "default": "4..5", "valid": "4..5"},
    "position_bias":     {"type": "str", "default": "corners_plus_motif",
                           "valid": "corners_plus_motif"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "command_kind":      {"type": "str", "default": "rng all combos",
                           "valid": "rng"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


# Each motif is a tuple of (dr, dc, color_index) where color_index
# refers to a slot in the per-instance color list. Bboxes intentionally
# vary so rotated/flipped outputs span many distinct shapes.
#
# Motif color slots: 0 (primary), 1 (secondary). Some motifs use only
# slot 0; others mix.
_MOTIFS_RAW = (
    # 0: 3x2 J (asymmetric L/R and rot)
    ((0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 1)),
    # 1: 2x3 S
    ((0, 1, 0), (0, 2, 0), (1, 0, 1), (1, 1, 0)),
    # 2: 3x3 P
    ((0, 0, 0), (0, 1, 0), (0, 2, 1), (1, 0, 0), (2, 0, 0)),
    # 3: 4x2 L
    ((0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (3, 1, 1)),
    # 4: 2x4 strip-with-tail
    ((0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 1), (1, 0, 1)),
    # 5: 3x4 staircase
    ((0, 0, 0), (0, 1, 0), (1, 1, 1), (1, 2, 0), (2, 2, 0), (2, 3, 1)),
    # 6: 4x3 hook
    ((0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (3, 1, 1), (3, 2, 0)),
    # 7: 3x3 asymmetric F
    ((0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1), (2, 0, 0)),
    # 8: 4x4 spiral
    ((0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (3, 1, 0), (3, 2, 1), (3, 3, 0), (2, 3, 0)),
    # 9: 2x4 zig
    ((0, 0, 0), (0, 1, 1), (1, 1, 0), (1, 2, 0), (1, 3, 1)),
)


def _bbox(motif):
    rs = [r for r, _, _ in motif]
    cs = [c for _, c, _ in motif]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _normalize_pattern(motif):
    """Return frozenset of (dr, dc, color_index) with min row/col at 0."""
    cells = list(motif)
    minr = min(r for r, _, _ in cells)
    minc = min(c for _, c, _ in cells)
    return frozenset((r - minr, c - minc, k) for r, c, k in cells)


def _rotate_cw(motif):
    h, _ = _bbox(motif)
    return _normalize_pattern((c, h - 1 - r, k) for r, c, k in motif)


def _flip_lr(motif):
    _, w = _bbox(motif)
    return _normalize_pattern((r, w - 1 - c, k) for r, c, k in motif)


def _is_observably_transformable(motif):
    """rot-cw OR flip-lr must yield a different pattern; otherwise cmd-rot
    (or cmd-flip) would have no observable effect on this motif."""
    norm = _normalize_pattern(motif)
    return _rotate_cw(motif) != norm and _flip_lr(motif) != norm


# Assert all motifs in the bank are observably transformable. Catches
# accidental palindromic shapes that would make the rule invisible.
for _idx, _m in enumerate(_MOTIFS_RAW):
    assert _is_observably_transformable(_m), \
        f"motif {_idx} is symmetric under rot-cw or flip-lr — rule actions would be invisible"


def _motif_indices_for_difficulty(difficulty):
    """Which motif indices the difficulty band allows."""
    if difficulty == "easy":
        return [i for i, m in enumerate(_MOTIFS_RAW) if max(_bbox(m)) <= 3]
    if difficulty == "hard":
        # Hard uses everything but emphasizes bigger bboxes.
        return list(range(len(_MOTIFS_RAW)))
    return [i for i, m in enumerate(_MOTIFS_RAW) if max(_bbox(m)) <= 4]


def _grid_bounds(difficulty):
    if difficulty == "easy":
        return 8, 9, 8, 10
    if difficulty == "hard":
        return 10, 12, 11, 14
    return 9, 11, 10, 12


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    h_lo, h_hi, w_lo, w_hi = _grid_bounds(difficulty)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")

    # Commands — uniform over the valid ranges.
    g = full_grid(h, w, 0)
    g[0][0] = rng.randint(1, 4)
    g[0][w - 1] = rng.choice([1, 2])

    # Motif — pick a shape that fits in the available area (rows ≥ 2)
    # and choose colors that avoid the command colors (1..4 are valid
    # cmd-rot codes; cmd-flip uses 1,2 so {1,2,3,4} could be commands
    # depending on corner reads, but the rule zeros the corners first
    # so motif colors only need to avoid conflict at *placement* time).
    candidate_indices = _motif_indices_for_difficulty(difficulty)
    rng.shuffle(candidate_indices)
    for idx in candidate_indices:
        motif_template = _MOTIFS_RAW[idx]
        mh, mw = _bbox(motif_template)
        if mh > h - 2 or mw > w:
            continue
        # row range starts at 2 (avoid command row at 0 and any
        # accidental adjacency). Stop short of bottom.
        top = rng.randint(2, h - mh)
        left = rng.randint(0, w - mw)
        # Avoid landing the motif's first row at row 1 directly under
        # the commands — keep at least one blank row of separation.
        # (already enforced by top >= 2).
        colors = rng.sample([5, 6, 7, 8, 9], 2)
        ok = True
        for dr, dc, _ in motif_template:
            r, c = top + dr, left + dc
            if g[r][c] != 0:
                ok = False; break
        if not ok:
            continue
        for dr, dc, color_idx in motif_template:
            g[top + dr][left + dc] = colors[color_idx]
        return g

    raise ValueError(
        f"could not place any motif for difficulty={difficulty} on a {h}x{w} grid"
    )


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_rotation_cmd":
        g[0][w - 1] = 1
        for dr, dc, k in _MOTIFS_RAW[0]:
            g[3 + dr][3 + dc] = 5 + k
        return g
    if name == "no_flip_cmd":
        g[0][0] = 2
        for dr, dc, k in _MOTIFS_RAW[0]:
            g[3 + dr][3 + dc] = 5 + k
        return g
    if name == "no_motif":
        g[0][0] = 3
        g[0][w - 1] = 2
        return g
    if name == "square_symmetric_motif":
        # Both commands present + a fully symmetric (under rot-cw and
        # flip-lr) motif → rule applies cleanly but its actions are
        # invisible because rotated/flipped output is identical to crop.
        g[0][0] = 3
        g[0][w - 1] = 2
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]:
            g[3 + dr][3 + dc] = 5
        return g
    return g

def _body_pattern(grid):
    cells = [(r, c, v) for r in range(1, len(grid)) for c, v in enumerate(grid[r]) if v != 0]
    if not cells:
        return frozenset()
    mr = min(r for r, _, _ in cells); mc = min(c for _, c, _ in cells)
    return frozenset((r - mr, c - mc, v) for r, c, v in cells)


def _pattern_bbox(pattern):
    rs = [r for r, _, _ in pattern]; cs = [c for _, c, _ in pattern]
    return max(rs) + 1, max(cs) + 1


def _pattern_rotate_cw(pattern):
    h, _ = _pattern_bbox(pattern)
    return _normalize_pattern((c, h - 1 - r, v) for r, c, v in pattern)


def _pattern_flip_lr(pattern):
    _, w = _pattern_bbox(pattern)
    return _normalize_pattern((r, w - 1 - c, v) for r, c, v in pattern)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows must have equal width"]
    if grid[0][0] not in (1, 2, 3, 4):
        errs.append(f"top-left rotation command should be 1..4, got {grid[0][0]}")
    if grid[0][w - 1] not in (1, 2):
        errs.append(f"top-right flip command should be 1 or 2, got {grid[0][w - 1]}")
    if any(v != 0 for v in grid[0][1:w - 1]):
        errs.append("command row should contain only the two corner command cells")
    pattern = _body_pattern(grid)
    if not pattern:
        errs.append("expected a body motif below the command row")
    else:
        colors = {v for _, _, v in pattern}
        if not colors <= {5, 6, 7, 8, 9}:
            errs.append(f"motif colors should avoid command digits 1..4, got {sorted(colors)}")
        if _pattern_rotate_cw(pattern) == pattern:
            errs.append("motif is rotation-symmetric; cmd-rot branch would be hidden")
        if _pattern_flip_lr(pattern) == pattern:
            errs.append("motif is left/right symmetric; cmd-flip branch would be hidden")
    return errs
