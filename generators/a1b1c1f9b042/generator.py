"""Stable left-packing lessons with an explicit order-preservation witness.

Only inputs are sampled here.  The unchanged canonical Racket rule owns labels.
Every generated input contains a shifted row whose nonzero sequence includes a
strict descent, so the plausible "sort colours, then pack" rival is visibly
wrong in every demonstration rather than only in a held-out query.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a1b1c1f9b042"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "8cd149b15ecf"
SUMMARY = "Pack each row's nonzeros left while preserving their original order."
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular integer grid, background 0, height 2..8 and width 4..10",
    "every row contains 1..3 nonzero cells and at least one row needs a left shift",
    "at least two nonzero colours occur",
    "default samples contain a descending left-to-right colour pair",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical/extended profile", "valid": "2..8"},
    "grid_w": {"type": "int", "default": "scheduled canonical/extended profile", "valid": "4..10"},
    "palette_size": {"type": "int", "default": "difficulty-weighted", "valid": "2..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("canonical_3x6", "canonical_4x5", "extended")
_ALLOWED_H = tuple(range(2, 9))
_ALLOWED_W = tuple(range(4, 11))


def schedule_profile(seed, sample_index, difficulty=None):
    """Three-step default profile schedule; explicit dimensions take precedence."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _incompatible(message, axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(axes))
    raise error


def _controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    for name, value in active.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if name == "grid_h" and value not in _ALLOWED_H:
            raise ValueError("grid_h must be in 2..8")
        if name == "grid_w" and value not in _ALLOWED_W:
            raise ValueError("grid_w must be in 4..10")
        if name == "palette_size" and not 2 <= value <= 9:
            raise ValueError("palette_size must be in 2..9")
    if (
        "grid_h" in active
        and "palette_size" in active
        and active["palette_size"] > 3 * active["grid_h"]
    ):
        axes = {"grid_h", "palette_size"}
        if "grid_w" in active:
            axes.add("grid_w")
        _incompatible(
            "grid height cannot provide enough row slots for palette_size",
            axes,
        )
    return active


def _shape(ctx, active, difficulty, sample_index):
    required_slots = active.get("palette_size", 2)
    shapes = [
        (h, w)
        for h in _ALLOWED_H
        for w in _ALLOWED_W
        if h == active.get("grid_h", h)
        and w == active.get("grid_w", w)
        and 3 * h >= required_slots
    ]
    if not shapes:
        axes = set(active) or {"grid_h", "grid_w", "palette_size"}
        _incompatible("requested controls have no feasible row-packing grid", axes)

    explicit_dimensions = "grid_h" in active or "grid_w" in active
    if not explicit_dimensions:
        profile = schedule_profile(ctx.seed, sample_index, difficulty)
        if profile == "canonical_3x6":
            shapes = [(3, 6)]
        elif profile == "canonical_4x5":
            shapes = [(4, 5)]
        else:
            ranges = {
                "easy": (range(2, 5), range(4, 7)),
                "medium": (range(3, 7), range(5, 9)),
                "hard": (range(4, 9), range(6, 11)),
            }
            heights, widths = ranges.get(difficulty, (range(3, 7), range(5, 9)))
            extended = [
                pair
                for pair in shapes
                if pair[0] in heights
                and pair[1] in widths
                and pair not in {(3, 6), (4, 5)}
            ]
            if extended:
                shapes = extended

    heights = sorted({h for h, _ in shapes})
    h = ctx.draw_choice("grid_h", heights)
    widths = sorted({w for hh, w in shapes if hh == h})
    w = ctx.draw_choice("grid_w", widths)
    return h, w


def _palette_size(ctx, active, h, difficulty, profile=None):
    maximum = min(9, 3 * h)
    if "palette_size" in active:
        values = [active["palette_size"]]
    elif profile == "canonical_3x6":
        values = [7, 8]
    elif profile == "canonical_4x5":
        values = [9]
    else:
        values = list(range(2, maximum + 1))
        preferred = {
            "easy": (2, 3, 4),
            "medium": (3, 4, 5, 6),
            "hard": (5, 6, 7, 8, 9),
        }.get(difficulty, (3, 4, 5, 6))
        values = values + [value for value in preferred if value in values] * 4
    return ctx.draw_choice("palette_size", values)


def _row_counts(h, palette_size, rng, profile=None):
    if profile == "canonical_3x6" and palette_size in (7, 8):
        return [3, 2, 2] if palette_size == 7 else [3, 3, 2]
    if profile == "canonical_4x5" and palette_size == 9:
        return [3, 2, 2, 2]

    counts = [2] * h
    rows = list(range(h))
    rng.shuffle(rows)
    for row in rows:
        if sum(counts) >= palette_size:
            break
        counts[row] = 3
    for row in rows:
        if counts[row] == 2 and rng.random() < 0.45:
            counts[row] = 3
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of: easy, medium, hard, or None")
    active = _controls(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )
    h, w = _shape(ctx, active, difficulty, sample_index)
    default_profile = None
    if "grid_h" not in active and "grid_w" not in active:
        default_profile = schedule_profile(seed, sample_index, difficulty)
    palette_size = _palette_size(ctx, active, h, difficulty, default_profile)

    layout_rng = ctx.draw_rng("layout")
    counts = _row_counts(h, palette_size, layout_rng, default_profile)
    slots = []
    for row, count in enumerate(counts):
        if row == 0:
            if count == 2:
                columns = [1, w - 1]
            else:
                columns = sorted({1, max(2, w // 2), w - 1})
                if len(columns) < 3:
                    columns = [1, 2, w - 1]
        else:
            columns = sorted(layout_rng.sample(range(w), count))
        slots.extend((row, column) for column in columns)

    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), palette_size)
    high, low = max(palette), min(palette)
    remaining = [value for value in palette if value not in (high, low)]
    assignment_rng = ctx.draw_rng("colour_assignment")
    assignment_rng.shuffle(remaining)
    colours = [high, low, *remaining]
    colours.extend(assignment_rng.choices(palette, k=len(slots) - len(colours)))

    grid = full_grid(h, w, 0)
    for (row, column), colour in zip(slots, colours):
        grid[row][column] = colour
    return grid


def observe_overrides(grid):
    colours = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len(colours),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colours 0..9 (not booleans)"]

    h, w = len(grid), width
    errors = []
    if h not in _ALLOWED_H or w not in _ALLOWED_W:
        errors.append("dimensions must be height 2..8 and width 4..10")

    counts = [sum(value != 0 for value in row) for row in grid]
    if any(not 1 <= count <= 3 for count in counts):
        errors.append("every row must contain 1..3 nonzero cells")
    if not any(count >= 2 for count in counts):
        errors.append("at least one row must contain two or more nonzero cells")

    colours = {value for row in grid for value in row if value != 0}
    if len(colours) < 2:
        errors.append("at least two distinct nonzero colours are required")

    needs_shift = any(
        [column for column, value in enumerate(row) if value != 0]
        != list(range(count))
        for row, count in zip(grid, counts)
    )
    if not needs_shift:
        errors.append("all nonzero cells are already packed left")
    return errors


def strict_canonical_like(grid):
    """Canonical task-domain membership, separate from the richer default schedule."""
    return self_check(grid)


def _stable_pack(grid):
    return [
        [value for value in row if value != 0]
        + [0] * sum(value == 0 for value in row)
        for row in grid
    ]


def _sort_then_pack_left(grid):
    return [
        sorted(value for value in row if value != 0)
        + [0] * sum(value == 0 for value in row)
        for row in grid
    ]


def _identity(grid):
    return [list(row) for row in grid]


def _pack_right_preserve_order(grid):
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        output.append([0] * (len(row) - len(values)) + values)
    return output


def _descending_row(grid):
    for row in grid:
        values = [value for value in row if value != 0]
        if any(left > right for left, right in zip(values, values[1:])):
            return True
    return False


SEMANTIC_WITNESSES = {"descending_order_pair": _descending_row}
SEMANTIC_RIVALS = {"sort_then_pack_left": _sort_then_pack_left}
WITNESS_RIVALS = {"descending_order_pair": ["sort_then_pack_left"]}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": _identity,
    "pack_right_preserve_order": _pack_right_preserve_order,
}


def lesson_identifiable(demos, query):
    """Reject only declared rivals that fit demos and alter the held-out answer."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and (
            rival(query["input"]) != query["output"]
        ):
            reasons.append(
                f"declared rival {name} survives demonstrations and changes query"
            )
    return reasons
