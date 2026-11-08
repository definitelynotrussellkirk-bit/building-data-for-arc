"""Eight-Way Room Weave: canonical palette, movable chamber, periodic rays.

Ordinary three-demo windows contain a full chamber, a deep-inset chamber,
and a long-ray corner seed. The last two refute canonical-fitting shortcuts:
clipping to a fixed canvas inset and stopping all rays after seven steps.
Training outputs still come only from the unchanged canonical Racket rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "11ebef5b0986"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "37be31441b18"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (0, 1, 2)
SUMMARY = (
    "Three distinct legend colors from 2..8 at row 0 columns 1..3; one closed "
    "color-1 rectangular chamber and one interior color-9 seed. Paint eight "
    "rays with the legend cycle, stopping at the actual frame. Ordinary "
    "three-example windows cover gray 5, deep insets and rays beyond distance 7."
)
INVARIANTS = [
    "0 background; exactly three distinct legend colors in 2..8 at row 0 cols 1..3",
    "one closed hollow color-1 rectangular frame, separate from row 0 and canvas edges",
    "one color-9 seed strictly inside the frame; all other body cells are 0",
    "outputs are the unchanged canonical Racket rule, never the diagnostic Python mirror",
]
PALETTE_KINDS = ("default", "warm_palette", "cool_palette", "varied_palette")
AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical/extended size", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "scheduled canonical/extended size", "valid": "8..16"},
    "frame_mode": {"type": "str", "default": "fit, inset, fit by three-slot schedule", "valid": "fit|inset"},
    "seed_pos": {"type": "str", "default": "random_interior, random_interior, corner", "valid": "random_interior|corner"},
    "palette_kind": {"type": "str", "default": "varied_palette in slot 0; default otherwise", "valid": "|".join(PALETTE_KINDS)},
}
# All Cartesian combinations of declared axis values are supported. Former
# inert/constant axes and invalid-input textures are deliberately not advertised.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def schedule_profile(seed, sample_index, difficulty=None):
    """A visible deterministic schedule; seed still controls actual scenes."""
    return sample_index % 3


def _draw_size(ctx, label, lo, hi, default):
    # Difficulty sets ordinary defaults, never narrows legal caller overrides.
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _draw_mode(ctx, label, options, default):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _validate_arguments(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer and sample_index a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}; allowed={sorted(AXES)}")
    for name in ("grid_h", "grid_w"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_arguments(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == 0:
        # Canonical-scale shapes, not copied canonical grids or labels.
        shapes = ((9, 11), (10, 10), (8, 12), (11, 9), (10, 13))
    elif profile == 1:
        shapes = ((10, 12), (11, 13), (12, 14))
    elif difficulty == "hard":
        shapes = ((14, 16), (15, 16), (16, 15))
    elif difficulty == "medium":
        shapes = ((12, 14), (13, 15), (14, 13))
    else:
        shapes = ((11, 13), (12, 14), (13, 12))
    dh, dw = ctx.draw_choice("shape", shapes)
    h = _draw_size(ctx, "grid_h", 7, 16, dh)
    w = _draw_size(ctx, "grid_w", 8, 16, dw)
    mode = _draw_mode(ctx, "frame_mode", ("fit", "inset"), "inset" if profile == 1 else "fit")
    seed_pos = _draw_mode(ctx, "seed_pos", ("random_interior", "corner"),
                          "corner" if profile == 2 else "random_interior")
    kind = _draw_mode(ctx, "palette_kind", PALETTE_KINDS,
                     "varied_palette" if profile == 0 else "default")
    # Preserve canonical geometry across bands without duplicating whole scenes.
    rng = ctx.draw_rng(f"palette:{difficulty}")
    if kind == "warm_palette":
        palette = rng.sample((2, 4, 6, 7), 3)
    elif kind == "cool_palette":
        palette = rng.sample((3, 5, 6, 8), 3)
    elif kind == "varied_palette":
        palette = [5] + rng.sample((2, 3, 4, 6, 7, 8), 2)
        rng.shuffle(palette)
    else:
        palette = rng.sample((2, 3, 4, 5, 6, 7, 8), 3)
    grid = full_grid(h, w, 0)
    grid[0][1:4] = palette
    top, bottom, left, right = 1, h - 2, 1, w - 2
    if mode == "inset":
        # Leave an actual blank strip outside the frame but inside the rival's
        # canvas-derived chamber. A one-cell inset cannot expose that shortcut.
        side = ctx.draw_choice("inset_side", ("top", "bottom", "left", "right"))
        limit = (h if side in ("top", "bottom") else w) - 4
        margin = ctx.draw_int("inset_margin", 3, min(5, limit))
        if side == "top":
            top = margin
        elif side == "bottom":
            bottom = h - 1 - margin
        elif side == "left":
            left = margin
        else:
            right = w - 1 - margin
    draw_frame(grid, top, left, bottom, right, 1)
    if seed_pos == "corner":
        sr = ctx.draw_choice("seed_row", (top + 1, bottom - 1))
        sc = ctx.draw_choice("seed_col", (left + 1, right - 1))
    else:
        sr = ctx.draw_int("seed_row", top + 1, bottom - 1)
        sc = ctx.draw_int("seed_col", left + 1, right - 1)
    grid[sr][sc] = 9
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the entire input grammar, not just the three salient objects."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular list of integer rows"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid rows must be nonempty integer lists"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9 (not bools)"]
    if not (7 <= h <= 16 and 8 <= w <= 16):
        return ["grid must be within declared 7..16 by 8..16 domain"]
    errors = []
    palette = grid[0][1:4]
    if len(set(palette)) != 3 or any(v not in range(2, 9) for v in palette):
        errors.append("legend must contain three distinct colors in 2..8")
    if [c for c, v in enumerate(grid[0]) if v] != [1, 2, 3]:
        errors.append("legend must occupy exactly row 0 columns 1..3")
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(seeds) != 1:
        errors.append("expected exactly one color-9 seed")
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1}
    if not cells:
        return errors + ["color-1 frame is missing"]
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    if not (1 <= top < bottom < h - 1 and 1 <= left < right < w - 1):
        errors.append("frame must be separated from row 0 and canvas edges")
    if bottom - top < 2 or right - left < 2:
        errors.append("frame must have a nonempty interior")
    expected = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)}
    if cells != expected:
        errors.append("color-1 cells must form exactly one closed hollow rectangle")
    if len(seeds) == 1 and not (top < seeds[0][0] < bottom and left < seeds[0][1] < right):
        errors.append("seed must lie strictly inside the frame")
    if any(v not in (0, 1, 9) for row in grid[1:] for v in row):
        errors.append("stray colored cells outside the row-0 legend")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _ray_paint(grid, *, fixed_chamber=False, max_distance=None):
    """Diagnostic-only arithmetic mirror/rivals on this closed-rectangle domain."""
    h, w = len(grid), len(grid[0])
    sr, sc = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
    walls = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    top, bottom = min(r for r, c in walls), max(r for r, c in walls)
    left, right = min(c for r, c in walls), max(c for r, c in walls)
    if fixed_chamber:
        top, bottom, left, right = 1, h - 2, 1, w - 2
    palette = grid[0][1:4]
    out = [list(row) for row in grid]
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            dr, dc = abs(r - sr), abs(c - sc)
            distance = max(dr, dc)
            if not distance or (dr != 0 and dc != 0 and dr != dc):
                continue
            if max_distance is not None and distance > max_distance:
                continue
            if grid[r][c] == 0:
                out[r][c] = palette[(distance - 1) % 3]
    return out


def rule_mirror(grid):
    """Test oracle only; Racket remains the training-label authority."""
    return _ray_paint(grid)


def fixed_canvas_chamber(grid):
    """Rival: ignore real frame extent; clip rays to a fixed canvas inset."""
    return _ray_paint(grid, fixed_chamber=True)


def stop_after_seven(grid):
    """Rival: repeat correctly, but paint no cell more than 7 steps away."""
    return _ray_paint(grid, max_distance=7)


def _inset_witness(grid):
    return rule_mirror(grid) != fixed_canvas_chamber(grid)


def _long_ray_witness(grid):
    return rule_mirror(grid) != stop_after_seven(grid)


def _gray_witness(grid):
    return 5 in grid[0][1:4]


SEMANTIC_WITNESSES = {
    "actual_frame_extent": _inset_witness,
    "cycle_beyond_seven": _long_ray_witness,
    "gray_legend_color": _gray_witness,
}
SEMANTIC_RIVALS = {
    "fixed_canvas_chamber": fixed_canvas_chamber,
    "stop_after_seven": stop_after_seven,
}
WITNESS_RIVALS = {
    "actual_frame_extent": ["fixed_canvas_chamber"],
    "cycle_beyond_seven": ["stop_after_seven"],
}
BRANCH_WITNESSES = ("gray_legend_color",)
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query):
    """Finite-rival identifiability, not a claim of unique logical induction."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or not {"input", "output"} <= pair.keys():
            reasons.append(f"pair {index} lacks input/output")
        elif self_check(pair["input"]):
            reasons.append(f"pair {index} violates the input grammar")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} disagrees with the diagnostic rule mirror")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"unrefuted rival changes query: {name}")
    return reasons
