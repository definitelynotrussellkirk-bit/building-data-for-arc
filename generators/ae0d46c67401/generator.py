"""Input generator for reflecting sparse cells across the main diagonal.

The canonical Racket authority overlays the input with its transpose.  This
sampler places one source in each selected transpose orbit, so every generated
source has an empty mirrored target and the teaching effect is explicit.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ae0d46c67401"
TASK_ID = GENERATOR_ID
RULE_HASH = "2b970065d6a3"
VERSION = "3.0.0"

SUMMARY = (
    "Square 5-14 grids on background 0 contain 3-9 colored source cells in "
    "distinct transpose orbits. Sources may lie above, below, or on both sides "
    "of the main diagonal; their transposed targets start empty. The output "
    "keeps every source and copies its color to (column,row), producing the "
    "union of the input and its transpose."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SIDE_PROFILES = ("above", "below", "mixed")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "background is 0 and the grid is square",
    "all source cells are strictly off the main diagonal",
    "at most one cell is occupied in each transpose orbit",
    "every advertised override is recoverable from returned pixels",
]

AXES = {
    "size": {
        "type": "int",
        "default": "scheduled 5..14 with canonical-size anchors in every band",
        "valid": "5..14",
    },
    "cells": {
        "type": "int",
        "default": "difficulty-weighted schedule over 3..9",
        "valid": "3..9",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
    "side_profile": {
        "type": "str",
        "default": "four-step mixed/above/mixed/below teaching schedule",
        "valid": "above|below|mixed",
    },
    "anchor_corner": {
        "type": "bool",
        "default": "scheduled true|false",
        "valid": "true|false",
    },
}

_SIZE_CYCLES = {
    None: (5, 6, 7, 8, 9, 10, 11, 12, 13, 14),
    "easy": (5, 6, 5, 7, 6, 8),
    "medium": (5, 6, 7, 8, 9, 10, 11),
    "hard": (9, 10, 11, 12, 13, 14),
}
_CELL_CYCLES = {
    None: (3, 4, 5, 6, 7, 8, 9),
    "easy": (3, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9),
    "medium": (3, 4, 5, 6, 7, 8, 9),
    "hard": (9, 8, 7, 9, 6, 8, 5, 7, 4, 6, 3, 9),
}
_SIDE_SCHEDULE = ("mixed", "above", "mixed", "below")
_ANCHOR_SCHEDULE = (False, True, True, False)
SCHEDULE_PROFILES = ("mixed-open", "above-corner", "mixed-corner", "below-open")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-step teaching schedule used by production lessons."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    integer_bounds = {"size": (5, 14), "cells": (3, 9), "palette_size": (1, 3)}
    for name, (lo, hi) in integer_bounds.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    if "side_profile" in overrides:
        value = overrides["side_profile"]
        if type(value) is not str:
            raise TypeError("side_profile override must be a string")
        if value not in SIDE_PROFILES:
            raise ValueError(f"side_profile override must be one of {SIDE_PROFILES}")

    if "anchor_corner" in overrides and type(overrides["anchor_corner"]) is not bool:
        raise TypeError("anchor_corner override must be a boolean")


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int, overrides) -> int:
    if label in overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_choice(ctx, label: str, options, scheduled, overrides):
    if label in overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_size(sample_index: int, difficulty) -> int:
    # Every five requested positions re-enter the canonical 5x5/6x6 profile,
    # including hard lessons.  Other positions retain band-specific breadth.
    if sample_index % 5 == 0:
        return 5 + ((sample_index // 5) % 2)
    cycle = _SIZE_CYCLES[difficulty]
    return cycle[sample_index % len(cycle)]


def _draw_positions(size: int, cells: int, side_profile: str, anchor_corner: bool, rng):
    corner_orbit = (0, size - 1)
    orbits = [(row, col) for row in range(size) for col in range(row + 1, size)]
    selectable = [orbit for orbit in orbits if orbit != corner_orbit]

    chosen: list[tuple[int, int]] = []
    if anchor_corner:
        chosen.append(corner_orbit)
    chosen.extend(rng.sample(selectable, cells - len(chosen)))
    rng.shuffle(chosen)

    if side_profile == "above":
        orientations = ["above"] * cells
    elif side_profile == "below":
        orientations = ["below"] * cells
    else:
        # Both sides are structural, not probabilistic: every mixed instance
        # contains at least one source on each side of the diagonal.
        orientations = ["above", "below"]
        orientations.extend(rng.choice(("above", "below")) for _ in range(cells - 2))
        rng.shuffle(orientations)

    return [
        (row, col) if orientation == "above" else (col, row)
        for (row, col), orientation in zip(chosen, orientations)
    ]


def _draw_colors(cells: int, palette_size: int, rng) -> list[int]:
    palette = rng.sample(range(1, 10), palette_size)
    colors = list(palette)
    colors.extend(rng.choice(palette) for _ in range(cells - palette_size))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    size = _scheduled_int(
        ctx,
        "size",
        5,
        14,
        _scheduled_size(sample_index, difficulty),
        overrides,
    )
    cell_cycle = _CELL_CYCLES[difficulty]
    cells = _scheduled_int(
        ctx,
        "cells",
        3,
        9,
        cell_cycle[sample_index % len(cell_cycle)],
        overrides,
    )
    palette_size = _scheduled_int(
        ctx,
        "palette_size",
        1,
        3,
        1 + sample_index % 3,
        overrides,
    )
    side_profile = _scheduled_choice(
        ctx,
        "side_profile",
        SIDE_PROFILES,
        _SIDE_SCHEDULE[sample_index % len(_SIDE_SCHEDULE)],
        overrides,
    )
    anchor_corner = _scheduled_choice(
        ctx,
        "anchor_corner",
        (False, True),
        _ANCHOR_SCHEDULE[sample_index % len(_ANCHOR_SCHEDULE)],
        overrides,
    )

    layout_rng = ctx.draw_rng("layout")
    positions = _draw_positions(size, cells, side_profile, anchor_corner, layout_rng)
    colors = _draw_colors(cells, palette_size, ctx.draw_rng("palette"))
    grid = full_grid(size, size, 0)
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color
    return grid


def _shape_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty square grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"], len(grid), 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], len(grid), width
    return [], len(grid), width


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors, height, width = _shape_errors(grid)
    if errors:
        return errors
    if height != width:
        errors.append(f"grid is not square: {height}x{width}")
    if not 5 <= height <= 14:
        errors.append(f"grid size {height} outside [5,14]")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (booleans are not colors)")
        return errors

    sources = [(row, col, value) for row in range(height) for col in range(width)
               if (value := grid[row][col]) != 0]
    if not 2 <= len(sources) <= 9:
        errors.append(f"nonzero source count {len(sources)} outside [2,9]")
    palette = {value for _, _, value in sources}
    if len(palette) > 3:
        errors.append(f"nonzero palette has {len(palette)} colors; maximum is 3")

    diagonal = [(row, col) for row, col, _ in sources if row == col]
    if diagonal:
        errors.append(f"nonzero cells on the main diagonal: {diagonal[:3]}")
    paired = [
        (row, col)
        for row, col, _ in sources
        if row < width and col < height and grid[col][row] != 0
    ]
    if paired:
        errors.append(f"occupied transpose targets: {paired[:3]}")
    return errors


def strict_canonical_like(grid):
    """The supported sparse-orbit manifold, including every canonical input."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    sources = [(row, col, value) for row, values in enumerate(grid)
               for col, value in enumerate(values) if value]
    sides = {"above" if row < col else "below" for row, col, _ in sources}
    side_profile = next(iter(sides)) if len(sides) == 1 else "mixed"
    size = len(grid)
    return {
        "size": size,
        "cells": len(sources),
        "palette_size": len({value for _, _, value in sources}),
        "side_profile": side_profile,
        "anchor_corner": any(
            (row, col) in ((0, size - 1), (size - 1, 0))
            for row, col, _ in sources
        ),
    }


def _copy(grid):
    return [list(row) for row in grid]


def reference_output(grid):
    """Python mirror of the selected rule, used only for semantic probes."""
    out = _copy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value and out[col][row] == 0:
                out[col][row] = value
    return out


def _identity(grid):
    return _copy(grid)


def _transpose_only(grid):
    return [list(row) for row in zip(*grid)]


def _one_sided(grid, side):
    out = _copy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if not value:
                continue
            if side == "above" and row >= col:
                continue
            if side == "below" and row <= col:
                continue
            if out[col][row] == 0:
                out[col][row] = value
    return out


def _above_only(grid):
    return _one_sided(grid, "above")


def _below_only(grid):
    return _one_sided(grid, "below")


def _single_color_mirror(grid):
    colors = sorted({value for row in grid for value in row if value})
    mirror_color = colors[0] if colors else 1
    out = _copy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value and out[col][row] == 0:
                out[col][row] = mirror_color
    return out


def _has_above(grid):
    return any(value and row < col for row, values in enumerate(grid) for col, value in enumerate(values))


def _has_below(grid):
    return any(value and row > col for row, values in enumerate(grid) for col, value in enumerate(values))


def _has_multiple_colors(grid):
    return len({value for row in grid for value in row if value}) > 1


def _has_offdiag_source(grid):
    return any(value and row != col for row, values in enumerate(grid) for col, value in enumerate(values))


SEMANTIC_RIVALS = {
    "identity": _identity,
    "transpose_only": _transpose_only,
    "above_only": _above_only,
    "below_only": _below_only,
    "single_color": _single_color_mirror,
}
SEMANTIC_WITNESSES = {
    "off_diagonal_copy": _has_offdiag_source,
    "source_above": _has_above,
    "source_below": _has_below,
    "multiple_colors": _has_multiple_colors,
}
WITNESS_RIVALS = {
    "off_diagonal_copy": ["identity", "transpose_only"],
    "source_above": ["below_only"],
    "source_below": ["above_only"],
    "multiple_colors": ["single_color"],
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report declared competitors that fit demos but change the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
