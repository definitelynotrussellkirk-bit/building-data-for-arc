"""Input sampler for alternating fills between matched row endpoints.

The unchanged Racket authority owns labels.  Default draws stay on exact
canonical (height, width, palette-size) profiles, while a three-step schedule
adds same-row mismatched-colour distractors often enough that every ordinary
three-demo lesson teaches the equal-colour precondition.  Every draw also has
an odd endpoint span, which distinguishes the left-anchored alternating phase.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7de2798953a7"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3bca54d68914"
SUMMARY = (
    "Rows contain two equal-colour endpoints with a zero gap. Fill interior "
    "cells at offsets 1, 3, 5, ... from the left endpoint. Default lessons "
    "retain canonical profiles and include scheduled unequal-colour distractors."
)
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("canonical", "contrast")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "4..10 by 7..14 background-0 grid with 1..4 valid endpoint-pair rows",
    "each valid row has exactly two equal nonzero endpoints and at least two zero gap cells",
    "valid pair colours are distinct; default draws contain 2 or 3 pairs",
    "every default draw has an odd endpoint span to reveal left-anchored phase",
    "easy uses compact spans; hard uses widest legal spans without changing canonical profiles",
    "contrast draws add one unequal-colour two-endpoint row that the rule leaves unchanged",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical profile schedule", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "canonical profile schedule", "valid": "7..14"},
    "n_pairs": {"type": "int", "default": "canonical profile schedule", "valid": "1..4"},
}

# Exact canonical (height, width, number of nonzero colours) support is obtained
# by using n_pairs distinct colours; background contributes the final palette item.
_CANONICAL_PROFILES = (
    (6, 7, 3),
    (5, 8, 3),
    (4, 9, 2),
    (4, 8, 2),
)
_PAIR_PALETTE = tuple(range(1, 10))


def schedule_profile(seed, sample_index, difficulty=None):
    """Three-step teaching schedule; seed/band never alter witness placement."""
    del seed, difficulty
    return "canonical" if sample_index % 3 == 0 else "contrast"


def _controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    bounds = {"grid_h": (4, 10), "grid_w": (7, 14), "n_pairs": (1, 4)}
    for name, value in active.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    return active


def _scheduled_draw(ctx, active, name, default, lo, hi):
    """Use a fixed default profile while retaining exact override provenance."""
    if name in active:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _span_and_start(ctx, pair_index, width, difficulty):
    spans = list(range(3, width))
    if pair_index == 0:
        candidates = [span for span in spans if span % 2 == 1]
    elif pair_index == 1:
        candidates = [span for span in spans if span % 2 == 0]
    else:
        candidates = spans
    if not candidates:
        candidates = spans

    # Difficulty changes composition, not the exact canonical profile: easy
    # uses compact intervals, hard uses the widest legal interval, and the
    # default/medium band retains seeded span variety.
    if difficulty == "easy":
        span = min(candidates)
    elif difficulty == "hard":
        span = max(candidates)
    else:
        span = ctx.draw_rng(f"pair_{pair_index}_span").choice(candidates)
    left = ctx.draw_rng(f"pair_{pair_index}_left").randint(0, width - span - 1)
    return left, left + span


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _controls(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )
    profile = _CANONICAL_PROFILES[(sample_index // 3) % len(_CANONICAL_PROFILES)]
    default_h, default_w, default_pairs = profile
    n_pairs = _scheduled_draw(ctx, active, "n_pairs", default_pairs, 1, 4)
    h = _scheduled_draw(ctx, active, "grid_h", default_h, 4, 10)
    w = _scheduled_draw(ctx, active, "grid_w", default_w, 7, 14)

    grid = full_grid(h, w, 0)
    use_contrast = schedule_profile(seed, sample_index, difficulty) == "contrast" and h > n_pairs
    row_count = n_pairs + int(use_contrast)
    rows = ctx.draw_rng("active_rows").sample(range(h), row_count)
    pair_rows = rows[:n_pairs]
    colours = ctx.draw_rng("pair_colours").sample(_PAIR_PALETTE, n_pairs)

    for index, (row, colour) in enumerate(zip(pair_rows, colours)):
        left, right = _span_and_start(ctx, index, w, difficulty)
        grid[row][left] = colour
        grid[row][right] = colour

    if use_contrast:
        row = rows[-1]
        left, right = _span_and_start(ctx, n_pairs + 7, w, difficulty)
        if len(colours) >= 2:
            left_colour, right_colour = colours[:2]
        else:
            left_colour = colours[0]
            right_colour = ctx.draw_rng("contrast_colour").choice(
                [colour for colour in _PAIR_PALETTE if colour != left_colour]
            )
        grid[row][left] = left_colour
        grid[row][right] = right_colour
    return grid


def _pair_rows(grid):
    result = []
    for row_index, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for colour, count in counts.items():
            positions = [c for c, value in enumerate(row) if value == colour]
            if (
                count == 2
                and positions[1] - positions[0] >= 3
                and all(value == 0 for value in row[positions[0] + 1 : positions[1]])
            ):
                result.append((row_index, colour, positions[0], positions[1]))
    return result


def _mismatched_rows(grid):
    result = []
    for row_index, row in enumerate(grid):
        occupied = [(c, value) for c, value in enumerate(row) if value != 0]
        if (
            len(occupied) == 2
            and occupied[0][1] != occupied[1][1]
            and occupied[1][0] - occupied[0][0] >= 3
            and all(value == 0 for value in row[occupied[0][0] + 1 : occupied[1][0]])
        ):
            result.append(row_index)
    return result


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_pairs": len(_pair_rows(grid))}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a nonempty rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colours 0..9 (booleans are not colours)"]

    errors = []
    h, w = len(grid), width
    if not 4 <= h <= 10:
        errors.append("grid height must be in 4..10")
    if not 7 <= w <= 14:
        errors.append("grid width must be in 7..14")

    pairs = _pair_rows(grid)
    if not 1 <= len(pairs) <= 4:
        errors.append("expected 1..4 valid endpoint-pair rows")
    pair_by_row = {row: (colour, left, right) for row, colour, left, right in pairs}
    if len(pair_by_row) != len(pairs):
        errors.append("each active row must contain only one valid pair")
    colours = [colour for _, colour, _, _ in pairs]
    if len(colours) != len(set(colours)):
        errors.append("valid endpoint-pair colours must be distinct")

    mismatch_rows = set(_mismatched_rows(grid))
    if len(mismatch_rows) > 1:
        errors.append("at most one unequal-colour distractor row is supported")
    for row_index, row in enumerate(grid):
        occupied = [(c, value) for c, value in enumerate(row) if value != 0]
        if not occupied:
            continue
        if row_index in pair_by_row:
            colour, left, right = pair_by_row[row_index]
            if occupied != [(left, colour), (right, colour)]:
                errors.append(f"row {row_index} contains extra cells beyond its endpoint pair")
        elif row_index not in mismatch_rows:
            errors.append(f"row {row_index} is neither a valid pair nor a supported distractor")
    return errors


def strict_canonical_like(grid):
    """Lawful task-domain membership; exact profile support is checked separately."""
    return self_check(grid)


def _solid_fill(grid):
    out = [list(row) for row in grid]
    for row, colour, left, right in _pair_rows(grid):
        for c in range(left + 1, right):
            out[row][c] = colour
    return out


def _right_phase(grid):
    out = [list(row) for row in grid]
    for row, colour, left, right in _pair_rows(grid):
        for step, c in enumerate(range(right - 1, left, -1), start=1):
            if step % 2 == 1:
                out[row][c] = colour
    return out


def _any_two_nonzero(grid):
    """Rival: alternates between any two row endpoints, ignoring colour equality."""
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        occupied = [(c, value) for c, value in enumerate(row) if value != 0]
        if len(occupied) != 2:
            continue
        (left, colour), (right, _) = occupied
        if right - left < 3 or not all(value == 0 for value in row[left + 1 : right]):
            continue
        for step, c in enumerate(range(left + 1, right), start=1):
            if step % 2 == 1:
                out[row_index][c] = colour
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _has_fillable_pair(grid):
    return bool(_pair_rows(grid))


def _has_odd_span(grid):
    return any((right - left) % 2 == 1 for _, _, left, right in _pair_rows(grid))


def _has_mismatched_row(grid):
    return bool(_mismatched_rows(grid))


SEMANTIC_WITNESSES = {
    "alternation_not_solid": _has_fillable_pair,
    "left_anchored_phase": _has_odd_span,
    "same_colour_required": _has_mismatched_row,
}
SEMANTIC_RIVALS = {
    "solid_fill": _solid_fill,
    "right_phase": _right_phase,
    "any_two_nonzero": _any_two_nonzero,
}
WITNESS_RIVALS = {
    "alternation_not_solid": ["solid_fill"],
    "left_anchored_phase": ["right_phase"],
    "same_colour_required": ["any_two_nonzero"],
}
CANONICAL_SHORTCUTS = {"any_two_nonzero": _any_two_nonzero}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": _identity,
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; query is accepted for the shared hook API."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
