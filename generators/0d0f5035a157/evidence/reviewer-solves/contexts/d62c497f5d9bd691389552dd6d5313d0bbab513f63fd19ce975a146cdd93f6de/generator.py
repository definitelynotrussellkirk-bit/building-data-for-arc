"""Input sampler for ARC task 0d0f5035a157, Left-Pack Each Row.

The selected authority independently removes zeros from every row, preserves the
remaining values' left-to-right order, writes those values from column zero, and
fills the rest of the row with zero.

The sampler exposes only six exact pixel-observable axes.  Ordinary lessons
alternate a canonical-sized sparse case with a dense moved row.  The dense row
is a counterexample to the strongest simple shortcut left open by all canonical
demonstrations: "only compact rows containing at most four nonzero cells."
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d0f5035a157"
TASK_ID = GENERATOR_ID
RULE_HASH = "8b15a51d568d"
VERSION = "3.0.0"
SUMMARY = (
    "Compact each row independently: delete zeros, preserve the nonzero values' "
    "left-to-right order, write them from the left edge, and zero-fill the suffix. "
    "Generated lessons mix already-packed rows with rows containing leading or "
    "internal gaps, and regularly include a moved row with at least five values."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0 and all cells are ARC colors 0..9",
    "each input has at least three nonempty rows and at least one empty or varied row role",
    "zero to two nonempty rows are already packed prefixes; all other nonempty rows require compaction",
    "at least one moved row contains two or more nonzero cells",
    "the stable left-to-right order of nonzero values is the only row payload order",
    "every advertised override is exact and recoverable from returned pixels",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5..10, weighted toward canonical heights 5 and 6",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "8..14, weighted toward canonical widths 8, 9, and 10",
        "valid": "8..14",
    },
    "palette_size": {
        "type": "int",
        "default": "1..9 distinct nonzero colors, weighted toward canonical 8 and 9",
        "valid": "1..9",
    },
    "max_cells_per_row": {
        "type": "int",
        "default": "alternating schedule: 3..4 then 5..7",
        "valid": "3..7",
    },
    "n_empty_rows": {
        "type": "int",
        "default": "0..2, weighted toward one canonical empty row",
        "valid": "0..2",
    },
    "n_packed_rows": {
        "type": "int",
        "default": "0..2 nonempty rows already left-packed",
        "valid": "0..2",
    },
}

SCHEDULE_PROFILES = ("dense_counterexample", "canonical_sparse")
_CANONICAL_PROFILES = {
    "c5x8p8": (5, 8, 8),
    "c5x9p9": (5, 9, 9),
    "c5x10p9": (5, 10, 9),
    "c6x9p8": (6, 9, 8),
}


def _profile_options(difficulty) -> tuple[str, ...]:
    if difficulty == "easy":
        return ("c5x8p8",) * 5 + ("c5x9p9",) * 4 + ("c5x10p9",) + ("c6x9p8",)
    if difficulty == "hard":
        return ("c6x9p8",) * 5 + ("c5x10p9",) * 4 + ("c5x9p9",) + ("c5x8p8",)
    return tuple(_CANONICAL_PROFILES) * 3


def _weighted_axis(ctx, name: str, values: Iterable[int], anchor: int, weight: int) -> int:
    return ctx.draw_choice(name, tuple(values) + (anchor,) * weight)


def _validate_override_types(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic semantic role used by ordinary generation.

    Consecutive sample indexes alternate dense and sparse roles.  Any four-pair
    lesson window therefore contains two dense counterexamples; after rotating
    any one pair into the query, at least one dense counterexample remains among
    the three demonstrations.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _internal_gap_positions(count: int, rng) -> list[int]:
    """A non-prefix placement that starts at column zero."""
    # count is at least three for the designated max row.  Keep count+1 as the
    # right edge and remove one interior position, producing a visible gap.
    gap = rng.randint(1, count - 1)
    return [column for column in range(count + 1) if column != gap]


def _moved_positions(count: int, width: int, rng) -> list[int]:
    """A non-prefix placement, sometimes with an internal rather than leading gap."""
    if count >= 2 and rng.random() < 0.5:
        gap = rng.randint(1, count - 1)
        return [column for column in range(count + 1) if column != gap]
    return sorted(rng.sample(range(1, width), count))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_name = ctx.draw_choice("curriculum_profile", _profile_options(difficulty))
    target_h, target_w, target_palette = _CANONICAL_PROFILES[profile_name]
    h = _weighted_axis(ctx, "grid_h", range(5, 11), target_h, 24)
    w = _weighted_axis(ctx, "grid_w", range(8, 15), target_w, 24)
    palette_size = _weighted_axis(
        ctx, "palette_size", range(1, 10), target_palette, 18
    )

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "max_cells_per_row" in overrides:
        max_cells = ctx.draw_choice("max_cells_per_row", tuple(range(3, 8)))
    elif scheduled == "dense_counterexample":
        dense_options = (5,) if difficulty == "easy" else ((6, 7) if difficulty == "hard" else (5, 6, 7))
        max_cells = ctx.draw_choice("max_cells_per_row", dense_options)
    else:
        max_cells = ctx.draw_choice("max_cells_per_row", (3, 4))

    n_empty = _weighted_axis(ctx, "n_empty_rows", range(0, 3), 1, 5)
    n_packed = _weighted_axis(ctx, "n_packed_rows", range(0, 3), 0, 4)

    layout_rng = ctx.draw_rng("row_layout")
    rows = list(range(h))
    layout_rng.shuffle(rows)
    empty_rows = set(rows[:n_empty])
    active_rows = sorted(set(rows[n_empty:]))

    # Domains are chosen so this is always constructive: h-n_empty >= 3 and
    # n_packed <= 2.  Keep the maximum-count row moved so every draw is nontrivial.
    max_row = layout_rng.choice(active_rows)
    packed_candidates = [row for row in active_rows if row != max_row]
    packed_rows = set(layout_rng.sample(packed_candidates, n_packed))

    counts = {row: 1 for row in active_rows}
    counts[max_row] = max_cells
    missing = max(0, palette_size - sum(counts.values()))
    while missing:
        candidates = [row for row in active_rows if counts[row] < max_cells]
        if not candidates:  # Defensive; declared domains make this unreachable.
            raise ValueError("axis combination cannot realize the requested palette")
        row = layout_rng.choice(candidates)
        counts[row] += 1
        missing -= 1

    color_rng = ctx.draw_rng("row_values")
    palette = color_rng.sample(list(range(1, 10)), palette_size)
    stream = list(palette)
    color_rng.shuffle(stream)
    while len(stream) < sum(counts.values()):
        stream.append(color_rng.choice(palette))

    grid = full_grid(h, w, 0)
    cursor = 0
    for row in active_rows:
        count = counts[row]
        values = stream[cursor : cursor + count]
        cursor += count
        if row in packed_rows:
            columns = list(range(count))
        elif row == max_row:
            columns = _internal_gap_positions(count, layout_rng)
        else:
            columns = _moved_positions(count, w, layout_rng)
        for column, value in zip(columns, values):
            grid[row][column] = value

    # `empty_rows` is intentionally referenced: it documents the exact role set
    # and protects against accidental future assignment into those rows.
    assert all(not any(grid[row]) for row in empty_rows)
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _nonzero_positions(row) -> list[int]:
    return [index for index, value in enumerate(row) if value != 0]


def _is_packed_nonempty(row) -> bool:
    positions = _nonzero_positions(row)
    return bool(positions) and positions == list(range(len(positions)))


def observe_overrides(grid) -> dict[str, int]:
    shape = _shape(grid)
    if shape is None:
        raise ValueError("cannot observe axes from a malformed grid")
    nonzero_counts = [sum(value != 0 for value in row) for row in grid]
    return {
        "grid_h": shape[0],
        "grid_w": shape[1],
        "palette_size": len({value for row in grid for value in row if value != 0}),
        "max_cells_per_row": max(nonzero_counts, default=0),
        "n_empty_rows": sum(count == 0 for count in nonzero_counts),
        "n_packed_rows": sum(_is_packed_nonempty(row) for row in grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    h, w = shape
    errors: list[str] = []
    if not (5 <= h <= 10 and 8 <= w <= 14):
        errors.append("grid dimensions must be within 5..10 by 8..14")
    if any(type(value) is not int or not (0 <= value <= 9) for row in grid for value in row):
        return errors + ["every cell must be an integer ARC color 0..9"]

    counts = [sum(value != 0 for value in row) for row in grid]
    palette_size = len({value for row in grid for value in row if value != 0})
    active = sum(count > 0 for count in counts)
    empty = h - active
    packed = sum(_is_packed_nonempty(row) for row in grid)
    moved_rows = [
        row for row in grid if _nonzero_positions(row) and not _is_packed_nonempty(row)
    ]

    if not (1 <= palette_size <= 9):
        errors.append("grid must use between one and nine nonzero colors")
    if active < 3:
        errors.append("grid must contain at least three nonempty rows")
    if not (0 <= empty <= 2):
        errors.append("grid must contain zero to two empty rows")
    if not (0 <= packed <= 2):
        errors.append("grid must contain zero to two already-packed nonempty rows")
    if not counts or not (1 <= max(counts) <= 7):
        errors.append("no row may contain more than seven nonzero cells")
    if not moved_rows:
        errors.append("at least one nonempty row must require compaction")
    if not any(sum(value != 0 for value in row) >= 2 for row in moved_rows):
        errors.append("at least one moved row must contain two or more nonzero cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def teaching_check(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror of the selected per-row Racket authority."""
    result = []
    for row in grid:
        values = [value for value in row if value != 0]
        result.append(values + [0] * (len(row) - len(values)))
    return result


def _pack_at_most_four(grid):
    """Canonical-fitting rival: leave rows with five or more values untouched."""
    result = []
    for row in grid:
        values = [value for value in row if value != 0]
        if len(values) <= 4:
            result.append(values + [0] * (len(row) - len(values)))
        else:
            result.append(list(row))
    return result


def _dense_moved_row(grid) -> bool:
    shape = _shape(grid)
    if shape is None:
        return False
    return any(
        len(_nonzero_positions(row)) >= 5 and not _is_packed_nonempty(row)
        for row in grid
    )


SEMANTIC_WITNESSES = {"dense_moved_row": _dense_moved_row}
SEMANTIC_RIVALS = {"pack_at_most_four": _pack_at_most_four}
WITNESS_RIVALS = {"dense_moved_row": ["pack_at_most_four"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Finite declared-rival check; this is not a universal induction claim."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match stable row compaction")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
