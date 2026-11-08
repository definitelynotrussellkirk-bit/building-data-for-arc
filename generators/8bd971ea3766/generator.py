"""Input generator for canonical task 8bd971ea3766.

Selected rule: scan every row of the original input.  Whenever a nonzero cell,
one background cell, and the same nonzero color form ``a, 0, a``, fill the
middle cell with ``a``.  All qualifying horizontal windows are applied; other
cells and vertical lookalikes are unchanged.

Every ordinary generated input contains a compact teaching core that separates
the selected rule from five plausible shortcuts while still varying source-scale
profiles, palettes, placement, reflection, and surrounding noise.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8bd971ea3766"
TASK_ID = GENERATOR_ID
RULE_HASH = "4c32e7924ca5"
VERSION = "2.0.0"
SUMMARY = (
    "Horizontal same-color one-cell gaps are completed amid multiple targets, "
    "longer same-color spans, different-color flanks, busy rows, and vertical decoys."
)

INVARIANTS = [
    "background is color 0 and all cells are ARC colors 0..9",
    "at least one horizontal original-input window has the form a,0,a with a nonzero",
    "ordinary generated inputs contain a source-bound teaching core that refutes declared rivals",
]

_SHAPES = {
    "4x7": (4, 7),
    "5x8": (5, 8),
    "5x9": (5, 9),
    "6x10": (6, 10),
    "8x12": (8, 12),
}
_PALETTES = {
    "low": (1, 2, 3, 4),
    "high": (6, 7, 8, 9),
    "mixed": (1, 4, 7, 9),
}
_CANONICAL_PROFILES = (
    ("4x7", 4),  # canonical train profile: 4x7 with 4 nonzero colors
    ("5x8", 3),  # canonical train profile: 5x8 with 3 nonzero colors
    ("5x9", 4),  # canonical test profile: 5x9 with 4 nonzero colors
)

AXES = {
    "grid_shape": {
        "type": "str",
        "default": "source profile every other sample; otherwise difficulty-scaled broad profile",
        "valid": "4x7|5x8|5x9|6x10|8x12",
    },
    "n_colors": {
        "type": "int",
        "default": "3 or 4 in source profiles; otherwise 2..4",
        "valid": "2..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "uniform among three observable palettes",
        "valid": "low|high|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def _validate_request(sample_index: int, difficulty: Any, overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    if overrides.get("grid_shape") is not None:
        value = overrides["grid_shape"]
        if type(value) is not str or value not in _SHAPES:
            raise ValueError(f"grid_shape must be one of {sorted(_SHAPES)}, got {value!r}")
    if overrides.get("n_colors") is not None:
        value = overrides["n_colors"]
        if type(value) is not int:
            raise TypeError("n_colors must be an integer (not bool)")
        if value not in (2, 3, 4):
            raise ValueError("n_colors must be in 2..4")
    if overrides.get("palette_kind") is not None:
        value = overrides["palette_kind"]
        if type(value) is not str or value not in _PALETTES:
            raise ValueError(f"palette_kind must be one of {sorted(_PALETTES)}, got {value!r}")


def _axis_choice(ctx, overrides: dict[str, Any], name: str, domain, default):
    """Record scheduled defaults while preserving the full override domain."""
    options = tuple(domain) if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


def _scheduled_defaults(ctx, seed: int, sample_index: int, difficulty: Any) -> tuple[str, int, str]:
    # Exact source profiles recur in every difficulty band.  This is a profile
    # schedule, not canonical-grid replay: colors, transforms, offsets, and noise
    # remain independently keyed.
    if sample_index % 2 == 0:
        profile = _CANONICAL_PROFILES[(abs(int(seed)) + sample_index // 2) % len(_CANONICAL_PROFILES)]
        shape, n_colors = profile
    else:
        shape_options = {
            "easy": ("4x7", "5x8", "5x9", "6x10"),
            "medium": tuple(_SHAPES),
            "hard": ("5x9", "6x10", "8x12"),
        }.get(difficulty, tuple(_SHAPES))
        shape = ctx.draw_rng("default_grid_shape").choice(shape_options)
        n_colors = ctx.draw_rng("default_n_colors").choice((2, 3, 4))
    palette_kind = ctx.draw_rng("default_palette_kind").choice(tuple(_PALETTES))
    return shape, n_colors, palette_kind


def _teaching_core(colors: tuple[int, ...]) -> list[list[int]]:
    """A 4x7 witness core; roles wrap while realizing every selected color.

    Row 0 has two true targets.  Row 1 has one true target beside a
    longer same-color span.  Row 2 has different-colored flanks.  Column 4 across
    rows 1..3 is a vertical a,0,a lookalike that the selected rule ignores.
    """
    a, b, c, d = (colors[index % len(colors)] for index in range(4))
    return [
        [a, 0, a, 0, b, 0, b],
        [c, 0, 0, c, d, 0, d],
        [a, 0, b, 0, 0, 0, c],
        [0, c, 0, 0, d, 0, 0],
    ]


def _transform_core(core: list[list[int]], code: int) -> list[list[int]]:
    transformed = [row[:] for row in core]
    if code & 1:
        transformed = [row[::-1] for row in transformed]
    if code & 2:
        transformed = transformed[::-1]
    return transformed


def _add_outer_noise(
    grid: list[list[int]],
    footprint: set[tuple[int, int]],
    colors: tuple[int, ...],
    rng,
    difficulty: Any,
) -> None:
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (row, col) not in footprint
    ]
    if not candidates:
        return
    cap = {"easy": 1, "medium": 3, "hard": 5}.get(difficulty, 3)
    count = rng.randint(0, min(cap, len(candidates)))
    for index, (row, col) in enumerate(rng.sample(candidates, count)):
        grid[row][col] = colors[index % len(colors)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_shape, default_n_colors, default_palette = _scheduled_defaults(
        ctx, seed, sample_index, difficulty
    )
    shape_name = _axis_choice(ctx, overrides, "grid_shape", _SHAPES, default_shape)
    n_colors = _axis_choice(ctx, overrides, "n_colors", (2, 3, 4), default_n_colors)
    palette_kind = _axis_choice(ctx, overrides, "palette_kind", _PALETTES, default_palette)

    height, width = _SHAPES[shape_name]
    selected = list(_PALETTES[palette_kind][:n_colors])
    ctx.draw_rng("role_permutation").shuffle(selected)
    colors = tuple(selected)

    core = _transform_core(_teaching_core(colors), ctx.draw_rng("core_transform").randrange(4))
    row0 = ctx.draw_rng("core_row").randrange(height - len(core) + 1)
    col0 = ctx.draw_rng("core_col").randrange(width - len(core[0]) + 1)

    grid = full_grid(height, width, 0)
    footprint: set[tuple[int, int]] = set()
    for dr, row in enumerate(core):
        for dc, value in enumerate(row):
            rr, cc = row0 + dr, col0 + dc
            grid[rr][cc] = value
            footprint.add((rr, cc))

    _add_outer_noise(grid, footprint, colors, ctx.draw_rng("outer_noise"), difficulty)
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer ARC color 0..9"
                )
                return errors
    return errors


def _horizontal_targets(grid) -> list[tuple[int, int, int]]:
    targets: list[tuple[int, int, int]] = []
    for row_index, row in enumerate(grid):
        for col in range(len(row) - 2):
            left, middle, right = row[col : col + 3]
            if left != 0 and middle == 0 and right == left:
                targets.append((row_index, col + 1, left))
    return targets


def rule_mirror(grid):
    """Independent Python mirror of the selected simultaneous-window rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    out = [list(row) for row in grid]
    for row, col, color in _horizontal_targets(grid):
        out[row][col] = color
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the true task domain rather than one sampler layout."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    if not _horizontal_targets(grid):
        errors.append("grid must contain at least one horizontal nonzero,0,same-nonzero target")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The selected rule accepts any lawful rectangular ARC grid with a target."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    shape = f"{len(grid)}x{len(grid[0])}"
    if shape not in _SHAPES:
        raise ValueError(f"grid shape {shape} is outside the declared generator domain")
    colors = tuple(sorted({value for row in grid for value in row if value != 0}))
    if len(colors) not in (2, 3, 4):
        raise ValueError(f"expected 2..4 realized nonzero colors, found {len(colors)}")
    matches = [
        name
        for name, palette in _PALETTES.items()
        if colors == tuple(sorted(palette[: len(colors)]))
    ]
    if len(matches) != 1:
        raise ValueError(f"realized colors {colors} do not identify one palette kind")
    return {"grid_shape": shape, "n_colors": len(colors), "palette_kind": matches[0]}


def _fill_first_target_per_row(grid):
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for col in range(len(row) - 2):
            left, middle, right = row[col : col + 3]
            if left != 0 and middle == 0 and right == left:
                out[row_index][col + 1] = left
                break
    return out


def _fill_any_flanked_zero(grid):
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for col in range(len(row) - 2):
            left, middle, right = row[col : col + 3]
            if left != 0 and middle == 0 and right != 0:
                out[row_index][col + 1] = left
    return out


def _fill_same_color_spans(grid):
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append(col)
        for color, cols in positions.items():
            for left, right in zip(cols, cols[1:]):
                for col in range(left + 1, right):
                    if row[col] == 0:
                        out[row_index][col] = color
    return out


def _fill_horizontal_and_vertical(grid):
    out = rule_mirror(grid)
    height, width = len(grid), len(grid[0])
    for row in range(height - 2):
        for col in range(width):
            top, middle, bottom = grid[row][col], grid[row + 1][col], grid[row + 2][col]
            if top != 0 and middle == 0 and bottom == top:
                out[row + 1][col] = top
    return out


def _fill_isolated_target_rows(grid):
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        if sum(value != 0 for value in row) != 2:
            continue
        for col in range(len(row) - 2):
            left, middle, right = row[col : col + 3]
            if left != 0 and middle == 0 and right == left:
                out[row_index][col + 1] = left
    return out


def _has_multiple_targets_one_row(grid) -> bool:
    counts: dict[int, int] = {}
    for row, _, _ in _horizontal_targets(grid):
        counts[row] = counts.get(row, 0) + 1
    return any(count >= 2 for count in counts.values())


def _has_different_color_flanks(grid) -> bool:
    return any(
        left != 0 and middle == 0 and right != 0 and left != right
        for row in grid
        for left, middle, right in zip(row, row[1:], row[2:])
    )


def _has_long_same_color_span(grid) -> bool:
    for row in grid:
        for left in range(len(row)):
            color = row[left]
            if color == 0:
                continue
            for right in range(left + 3, len(row)):
                if row[right] == color and all(value == 0 for value in row[left + 1 : right]):
                    return True
    return False


def _has_vertical_gap(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        grid[row][col] != 0
        and grid[row + 1][col] == 0
        and grid[row + 2][col] == grid[row][col]
        for row in range(height - 2)
        for col in range(width)
    )


def _has_busy_target_row(grid) -> bool:
    target_rows = {row for row, _, _ in _horizontal_targets(grid)}
    return any(sum(value != 0 for value in grid[row]) > 2 for row in target_rows)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "multiple_targets_one_row": _has_multiple_targets_one_row,
    "different_color_flanks": _has_different_color_flanks,
    "long_same_color_span": _has_long_same_color_span,
    "vertical_gap_is_distractor": _has_vertical_gap,
    "busy_target_row": _has_busy_target_row,
}
SEMANTIC_RIVALS = {
    "first_target_per_row": _fill_first_target_per_row,
    "any_nonzero_flanks": _fill_any_flanked_zero,
    "fill_between_matching_pairs": _fill_same_color_spans,
    "horizontal_and_vertical": _fill_horizontal_and_vertical,
    "isolated_target_rows_only": _fill_isolated_target_rows,
}
WITNESS_RIVALS = {
    "multiple_targets_one_row": ["first_target_per_row"],
    "different_color_flanks": ["any_nonzero_flanks"],
    "long_same_color_span": ["fill_between_matching_pairs"],
    "vertical_gap_is_distractor": ["horizontal_and_vertical"],
    "busy_target_row": ["isolated_target_rows_only"],
}
# The canonical examples contain no vertical a,0,a witness, so this broader
# orientation shortcut fits every canonical pair and must be taught away.
CANONICAL_SHORTCUTS = {"horizontal_and_vertical": _fill_horizontal_and_vertical}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a named rival survives demos and changes query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["need at least one labeled demonstration"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    try:
        query_expected = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons
    if "output" in query and query["output"] != query_expected:
        reasons.append("query output disagrees with the selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query_expected:
                reasons.append(f"rival {name!r} fits every demo but changes the query answer")
    return reasons
