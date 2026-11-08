"""Input sampler for row-wise stable left compaction.

The unchanged Racket authority removes zeroes from each row, preserves the
remaining left-to-right order, and pads the row with zeroes on the right.
This sampler makes both parts of that rule identifiable: every instance has a
row that visibly needs compaction and a non-monotone row that distinguishes
stable compaction from a tempting sort-then-pack shortcut.
"""
from __future__ import annotations

from collections.abc import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ba9d8eb0cd5a"
TASK_ID = GENERATOR_ID
RULE_HASH = "8cd149b15ecf"
VERSION = "2.0.0"
SUMMARY = (
    "Compact each row's nonzero cells flush left while preserving their "
    "original left-to-right order."
)

INVARIANTS = [
    "background is integer color 0 and all foreground colors are in 1..9",
    "rows transform independently and at least one row visibly needs compaction",
    "at least one active row already touches the left edge",
    "at least one row has a non-monotone nonzero sequence, proving order preservation",
    "the advertised nonzero-color count is realized exactly",
]

# These are the only facts this generator can recover exactly from returned
# pixels. Keeping the contract small prevents metadata from promising dead or
# lossy controls.
AXES = {
    "grid_h": {"type": "int", "default": "weighted 4..12", "valid": "4..12"},
    "grid_w": {"type": "int", "default": "weighted 7..16", "valid": "7..16"},
    "n_colors": {
        "type": "int",
        "default": "weighted 2..9; canonical-scale component favors 9",
        "valid": "2..9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_BOUNDS = {
    "grid_h": (4, 12),
    "grid_w": (7, 16),
    "n_colors": (2, 9),
}
_CANONICAL_SHAPES = ((4, 9), (5, 8), (6, 7))
_BROAD_ANCHORS = {
    "easy": (5, 8, 3),
    "medium": (8, 11, 6),
    "hard": (11, 15, 9),
}


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:  # reject bool as well as float/string coercions
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name: str, *, anchor: int, canonical_profile: bool) -> int:
    """Draw from the full advertised domain while weighting useful scales.

    Every legal value remains in ``options`` in every difficulty band, so an
    override is never clipped or silently discarded. The canonical component
    only changes probability; it never replays a canonical grid.
    """
    lo, hi = _BOUNDS[name]
    choices = list(range(lo, hi + 1))
    choices.extend([anchor] * (96 if canonical_profile else 4))
    return ctx.draw_choice(name, tuple(choices))


def _difficulty_anchor(difficulty: object) -> tuple[int, int, int]:
    return _BROAD_ANCHORS.get(difficulty, _BROAD_ANCHORS["medium"])


def _row_nonzeros(row: Sequence[int]) -> list[int]:
    return [value for value in row if value != 0]


def _packed_row(row: Sequence[int]) -> list[int]:
    values = _row_nonzeros(row)
    return values + [0] * (len(row) - len(values))


def _needs_pack(row: Sequence[int]) -> bool:
    return bool(_row_nonzeros(row)) and list(row) != _packed_row(row)


def _has_order_witness(grid: Sequence[Sequence[int]]) -> bool:
    for row in grid:
        values = _row_nonzeros(row)
        if len(values) >= 2 and values != sorted(values):
            return True
    return False


def _build_sequences(
    palette: tuple[int, ...], active_count: int, width: int, rng, difficulty: object
) -> list[list[int]]:
    """Build row-local color sequences before choosing their columns."""
    sequences: list[list[int]] = [[] for _ in range(active_count)]

    # This first adjacent pair is a guaranteed counterexample to sorting.
    high, low = max(palette), min(palette)
    sequences[0].extend((high, low))

    # Row 1 will be placed at column 0. Seed every additional active row so
    # active_count remains a real layout choice even when n_colors is small.
    sequences[1].append(rng.choice(palette))
    for index in range(2, active_count):
        sequences[index].append(rng.choice(palette))

    present = {value for seq in sequences for value in seq}
    capacities = [width - 1] + [width] + [width - 1] * (active_count - 2)

    # Realize every selected palette color exactly at least once.
    for value in palette:
        if value in present:
            continue
        candidates = [
            index
            for index, seq in enumerate(sequences)
            if len(seq) < capacities[index]
        ]
        if not candidates:
            raise RuntimeError("constructive palette placement exhausted row capacity")
        target = min(candidates, key=lambda index: (len(sequences[index]), index))
        sequences[target].append(value)
        present.add(value)

    spare = sum(capacity - len(seq) for capacity, seq in zip(capacities, sequences))
    if difficulty == "easy":
        extra_hi = min(spare, 2)
        extra_lo = 0
    elif difficulty == "hard":
        extra_hi = min(spare, max(4, active_count + len(palette) // 2))
        extra_lo = min(extra_hi, 2)
    else:
        extra_hi = min(spare, max(3, active_count))
        extra_lo = min(extra_hi, 1)
    extra_count = rng.randint(extra_lo, extra_hi) if extra_hi else 0

    for _ in range(extra_count):
        candidates = [
            index
            for index, seq in enumerate(sequences)
            if len(seq) < capacities[index]
        ]
        target = rng.choice(candidates)
        sequences[target].append(rng.choice(palette))

    return sequences


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_profile = (
        ctx.draw_choice("curriculum_profile", ("canonical", "broad"))
        == "canonical"
    )
    if canonical_profile:
        anchor_h, anchor_w = ctx.draw_rng("canonical_shape").choice(
            _CANONICAL_SHAPES
        )
        anchor_colors = 9
    else:
        anchor_h, anchor_w, anchor_colors = _difficulty_anchor(difficulty)

    height = _draw_axis(
        ctx, "grid_h", anchor=anchor_h, canonical_profile=canonical_profile
    )
    width = _draw_axis(
        ctx, "grid_w", anchor=anchor_w, canonical_profile=canonical_profile
    )
    n_colors = _draw_axis(
        ctx,
        "n_colors",
        anchor=anchor_colors,
        canonical_profile=canonical_profile,
    )

    palette = tuple(
        ctx.draw_rng("palette").sample(tuple(range(1, 10)), n_colors)
    )
    layout_rng = ctx.draw_rng("layout")
    active_count = layout_rng.randint(2, min(height, 6))
    active_rows = layout_rng.sample(tuple(range(height)), active_count)
    sequences = _build_sequences(
        palette, active_count, width, layout_rng, difficulty
    )

    grid = full_grid(height, width, 0)
    for sequence_index, (row_index, sequence) in enumerate(
        zip(active_rows, sequences)
    ):
        if sequence_index == 0:
            # Guaranteed leading gap: this row must visibly move.
            columns = sorted(layout_rng.sample(tuple(range(1, width)), len(sequence)))
        elif sequence_index == 1:
            # Guaranteed anchored row: canonical inputs include both anchored
            # and gappy rows, so a leading gap is not a task invariant.
            columns = [0]
            if len(sequence) > 1:
                columns.extend(
                    sorted(
                        layout_rng.sample(
                            tuple(range(1, width)), len(sequence) - 1
                        )
                    )
                )
        elif layout_rng.random() < 0.55:
            columns = sorted(layout_rng.sample(tuple(range(1, width)), len(sequence)))
        else:
            columns = [0]
            if len(sequence) > 1:
                columns.extend(
                    sorted(
                        layout_rng.sample(
                            tuple(range(1, width)), len(sequence) - 1
                        )
                    )
                )
        for column, color in zip(columns, sequence):
            grid[row_index][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(
            "constructive generator violated its own contract: " + "; ".join(errors)
        )
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from the returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len(
            {value for row in grid for value in row if value != 0}
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-semantic training manifold, not one visual layout."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["ragged grid"]

    errors: list[str] = []
    height = len(grid)
    if not _BOUNDS["grid_h"][0] <= height <= _BOUNDS["grid_h"][1]:
        errors.append(f"grid_h={height} outside 4..12")
    if not _BOUNDS["grid_w"][0] <= width <= _BOUNDS["grid_w"][1]:
        errors.append(f"grid_w={width} outside 7..16")

    bad_cells = [
        (row_index, column_index, value)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"cells must be integer ARC colors 0..9: {bad_cells[:3]}")
        return errors

    active_rows = [row for row in grid if _row_nonzeros(row)]
    colors = {value for row in grid for value in row if value != 0}
    if len(active_rows) < 2:
        errors.append("expected at least two active rows")
    if not _BOUNDS["n_colors"][0] <= len(colors) <= _BOUNDS["n_colors"][1]:
        errors.append(f"expected 2..9 distinct nonzero colors, found {len(colors)}")
    if not any(_needs_pack(row) for row in active_rows):
        errors.append("expected at least one row that visibly needs left compaction")
    if not any(row[0] != 0 for row in active_rows):
        errors.append("expected at least one active row anchored at column 0")
    if not _has_order_witness(grid):
        errors.append(
            "expected a non-monotone row to distinguish stable packing from sorting"
        )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _sort_then_pack(grid):
    """Rival hypothesis: sort each row's colors before packing them left."""
    output = []
    for row in grid:
        values = sorted(_row_nonzeros(row))
        output.append(values + [0] * (len(row) - len(values)))
    return output


SEMANTIC_WITNESSES = {"order_preservation": _has_order_witness}
SEMANTIC_RIVALS = {"sort_then_pack": _sort_then_pack}
WITNESS_RIVALS = {"order_preservation": ["sort_then_pack"]}
LESSON_COMPETITORS = {"sort_then_pack": _sort_then_pack}
