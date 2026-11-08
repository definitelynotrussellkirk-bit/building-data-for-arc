"""Canonical framed-cell propagation curriculum for ARC task b3d7f3a15b3d.

The input is a rectangular array of 4x4 framed cells separated, including at
its outer edge, by zero rows and columns.  Every cell starts with a common 2x2
interior color.  Other colors appear at matching local interior offsets.  For
each color and local offset independently, occurrences in the same cell-row or
cell-column fill every intervening cell at that offset.

The Racket program pinned by ``RULE_HASH`` remains the label authority.  The
Python rule mirror, structural checker, rivals, and task-local reference probe
exist to make the generator auditable without weakening that authority.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b3d7f3a15b3d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "032c15e97118"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "In a zero-separated array of identical framed cells, propagate every "
    "non-common interior color across the span between matching local-offset "
    "anchors in each cell-row and cell-column."
)

INVARIANTS = [
    "zero separator rows and columns occur at the outer edge and every fifth coordinate",
    "each non-separator block is a 4x4 frame with one shared nonzero border color",
    "the 2x2 interiors have one unique modal nonzero color distinct from the border",
    "at least two colors expose real span filling and both horizontal and vertical propagation",
    "the four scene profiles exactly cover the canonical shape/palette support",
]

# (number of cell rows, number of cell columns, total palette size including 0)
SCENE_PROFILES = {
    "canonical_3x3_p5": (3, 3, 5),
    "canonical_4x4_p5": (4, 4, 5),
    "canonical_5x4_p6": (5, 4, 6),
    "canonical_5x5_p7": (5, 5, 7),
}
SCHEDULE_PROFILES = tuple(SCENE_PROFILES)
_PROFILE_SCHEDULE = tuple(SCENE_PROFILES)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-step schedule spanning every canonical shape/palette profile",
        "valid": "canonical_3x3_p5|canonical_4x4_p5|canonical_5x4_p6|canonical_5x5_p7",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
_LOCAL_OFFSETS = ((1, 1), (1, 2), (2, 1), (2, 2))


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        value = overrides["scene_profile"]
        if type(value) is not str or value not in SCENE_PROFILES:
            raise ValueError(
                "scene_profile must be one of " + ", ".join(SCENE_PROFILES)
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic ordinary-draw schedule; explicit overrides still win."""
    del seed, difficulty
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def _cell_origin(cell_row: int, cell_col: int) -> tuple[int, int]:
    return 1 + 5 * cell_row, 1 + 5 * cell_col


def _gapped_span(rng, count: int) -> list[int]:
    """Choose two anchors with a strict interior gap and optional extra anchors."""
    candidates = [
        (start, stop)
        for start in range(count)
        for stop in range(start + 2, count)
    ]
    if not candidates:
        raise ValueError("a gapped span needs at least three cells")
    start, stop = rng.choice(candidates)
    middle = list(range(start + 1, stop))
    # Keep only a strict subset, so at least one location must be synthesized.
    keep_count = rng.randint(0, len(middle) - 1)
    return [start, *sorted(rng.sample(middle, keep_count)), stop]


def _put_marker(
    grid: list[list[int]],
    cell_row: int,
    cell_col: int,
    offset: tuple[int, int],
    color: int,
) -> None:
    row0, col0 = _cell_origin(cell_row, cell_col)
    dr, dc = offset
    grid[row0 + dr][col0 + dc] = color


def _put_pattern(
    grid: list[list[int]],
    *,
    cell_rows: int,
    cell_cols: int,
    offset: tuple[int, int],
    color: int,
    orientation: str,
    rng,
) -> None:
    if orientation in ("horizontal", "both"):
        cell_row = rng.randrange(cell_rows)
        for cell_col in _gapped_span(rng, cell_cols):
            _put_marker(grid, cell_row, cell_col, offset, color)
    if orientation in ("vertical", "both"):
        cell_col = rng.randrange(cell_cols)
        for cell_row in _gapped_span(rng, cell_rows):
            _put_marker(grid, cell_row, cell_col, offset, color)


def _blank_scene(
    cell_rows: int,
    cell_cols: int,
    border: int,
    common: int,
) -> list[list[int]]:
    height, width = 5 * cell_rows + 1, 5 * cell_cols + 1
    grid = full_grid(height, width, 0)
    for cell_row in range(cell_rows):
        for cell_col in range(cell_cols):
            row0, col0 = _cell_origin(cell_row, cell_col)
            for dr in range(4):
                for dc in range(4):
                    if dr in (0, 3) or dc in (0, 3):
                        grid[row0 + dr][col0 + dc] = border
                    else:
                        grid[row0 + dr][col0 + dc] = common
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", tuple(SCENE_PROFILES))
    cell_rows, cell_cols, palette_size = SCENE_PROFILES[profile]

    colors = list(
        ctx.draw_distinct_colors("colors", n=palette_size - 1, exclude={0})
    )
    border, common, *specials = colors
    grid = _blank_scene(cell_rows, cell_cols, border, common)

    offsets = list(_LOCAL_OFFSETS)
    ctx.draw_rng("local_offsets").shuffle(offsets)
    # Difficulty changes presentation, not ownership: every band retains every
    # canonical profile and semantic branch, but maps colors to different local
    # offsets.  This prevents a dead difficulty knob without making any band a
    # weaker or narrower grammar.
    band_shift = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 3)
    band_shift %= len(offsets)
    offsets = offsets[band_shift:] + offsets[:band_shift]

    orientations = ["horizontal", "vertical"]
    orientations.extend("both" for _ in range(len(specials) - 2))
    ctx.draw_rng("orientation_assignment").shuffle(orientations)
    orientation_shift = band_shift % len(orientations)
    orientations = orientations[orientation_shift:] + orientations[:orientation_shift]
    pattern_rng = ctx.draw_rng("anchor_patterns")
    for color, offset, orientation in zip(specials, offsets, orientations):
        _put_pattern(
            grid,
            cell_rows=cell_rows,
            cell_cols=cell_cols,
            offset=offset,
            color=color,
            orientation=orientation,
            rng=pattern_rng,
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid framed-cell scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"scene_profile": ctx.axis_value("scene_profile")}
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost keyed axis values: expected {expected}, observed {observed}"
        )
    return grid


def _rectangular_shape(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError("every row must be a nonempty sequence")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def _geometry(grid) -> tuple[int, int]:
    height, width = _rectangular_shape(grid)
    if (height - 1) % 5 or (width - 1) % 5:
        raise ValueError("shape must have outer separators and 4x4 cells")
    cell_rows, cell_cols = (height - 1) // 5, (width - 1) // 5
    if not (3 <= cell_rows <= 5 and 3 <= cell_cols <= 5):
        raise ValueError("expected 3..5 cell rows and columns")
    for row in range(0, height, 5):
        if any(grid[row][col] != 0 for col in range(width)):
            raise ValueError(f"separator row {row} must be all zero")
    for col in range(0, width, 5):
        if any(grid[row][col] != 0 for row in range(height)):
            raise ValueError(f"separator column {col} must be all zero")
    return cell_rows, cell_cols


def _interior_values(grid, cell_rows: int, cell_cols: int) -> list[int]:
    return [
        grid[1 + 5 * cell_row + dr][1 + 5 * cell_col + dc]
        for cell_row in range(cell_rows)
        for cell_col in range(cell_cols)
        for dr in (1, 2)
        for dc in (1, 2)
    ]


def _common_color(grid, cell_rows: int, cell_cols: int) -> int:
    values = _interior_values(grid, cell_rows, cell_cols)
    if not values:
        raise ValueError("missing cell interiors")
    counts = Counter(values)
    common, frequency = counts.most_common(1)[0]
    if common == 0:
        raise ValueError("the common interior color must be nonzero")
    if len(counts) > 1 and counts.most_common(2)[1][1] == frequency:
        raise ValueError("the common interior color must be uniquely modal")
    return common


def _apply_rule(
    grid,
    *,
    horizontal: bool = True,
    vertical: bool = True,
    color_filter: Callable[[int], bool] | None = None,
) -> list[list[int]]:
    """Exact diagnostic mirror of the pinned selected Racket authority."""
    cell_rows, cell_cols = _geometry(grid)
    common = _common_color(grid, cell_rows, cell_cols)
    colors = sorted({value for row in grid for value in row} - {0, common})
    if color_filter is not None:
        colors = [color for color in colors if color_filter(color)]
    out = [list(row) for row in grid]
    for color in colors:
        for dr, dc in _LOCAL_OFFSETS:
            if horizontal:
                for cell_row in range(cell_rows):
                    matches = [
                        cell_col
                        for cell_col in range(cell_cols)
                        if grid[1 + 5 * cell_row + dr][1 + 5 * cell_col + dc]
                        == color
                    ]
                    if len(matches) >= 2:
                        for cell_col in range(min(matches), max(matches) + 1):
                            out[1 + 5 * cell_row + dr][
                                1 + 5 * cell_col + dc
                            ] = color
            if vertical:
                for cell_col in range(cell_cols):
                    matches = [
                        cell_row
                        for cell_row in range(cell_rows)
                        if grid[1 + 5 * cell_row + dr][1 + 5 * cell_col + dc]
                        == color
                    ]
                    if len(matches) >= 2:
                        for cell_row in range(min(matches), max(matches) + 1):
                            out[1 + 5 * cell_row + dr][
                                1 + 5 * cell_col + dc
                            ] = color
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Public Python mirror for tests and diagnostics; Racket stays authoritative."""
    return _apply_rule(grid)


def _analysis(grid) -> dict[str, Any]:
    errors: list[str] = []
    try:
        cell_rows, cell_cols = _geometry(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}

    height, width = len(grid), len(grid[0])
    border_values: list[int] = []
    interior_values: list[int] = []
    for cell_row in range(cell_rows):
        for cell_col in range(cell_cols):
            row0, col0 = _cell_origin(cell_row, cell_col)
            for dr in range(4):
                for dc in range(4):
                    value = grid[row0 + dr][col0 + dc]
                    if dr in (0, 3) or dc in (0, 3):
                        border_values.append(value)
                    else:
                        interior_values.append(value)

    border = border_values[0] if border_values else None
    if not border_values or len(set(border_values)) != 1 or border == 0:
        errors.append("all frame borders must share one nonzero color")

    counts = Counter(interior_values)
    common = None
    if not counts:
        errors.append("missing 2x2 interiors")
    else:
        common, common_count = counts.most_common(1)[0]
        if common == 0:
            errors.append("the common interior color must be nonzero")
        if len(counts) > 1 and counts.most_common(2)[1][1] == common_count:
            errors.append("the common interior color must be uniquely modal")
        if common == border:
            errors.append("border and common interior colors must differ")

    palette = sorted({value for row in grid for value in row})
    profile = next(
        (
            name
            for name, signature in SCENE_PROFILES.items()
            if signature == (cell_rows, cell_cols, len(palette))
        ),
        None,
    )
    if profile is None:
        errors.append(
            "shape/palette signature is outside the canonical profiles: "
            f"{cell_rows}x{cell_cols} cells with {len(palette)} colors"
        )

    specials = sorted(set(interior_values) - ({common} if common is not None else set()))
    if len(specials) < 2:
        errors.append("at least two non-common interior colors are required")

    changed: dict[tuple[int, int], int] = {}
    horizontal_changes: set[tuple[int, int]] = set()
    vertical_changes: set[tuple[int, int]] = set()
    output = None
    if common is not None:
        try:
            output = _apply_rule(grid)
        except ValueError as exc:
            errors.append(str(exc))
        if output is not None:
            changed = {
                (row, col): output[row][col]
                for row in range(height)
                for col in range(width)
                if output[row][col] != grid[row][col]
            }
            for color in specials:
                for dr, dc in _LOCAL_OFFSETS:
                    for cell_row in range(cell_rows):
                        matches = [
                            cell_col
                            for cell_col in range(cell_cols)
                            if grid[1 + 5 * cell_row + dr][
                                1 + 5 * cell_col + dc
                            ]
                            == color
                        ]
                        if len(matches) >= 2:
                            for cell_col in range(min(matches), max(matches) + 1):
                                point = (
                                    1 + 5 * cell_row + dr,
                                    1 + 5 * cell_col + dc,
                                )
                                if point in changed:
                                    horizontal_changes.add(point)
                    for cell_col in range(cell_cols):
                        matches = [
                            cell_row
                            for cell_row in range(cell_rows)
                            if grid[1 + 5 * cell_row + dr][
                                1 + 5 * cell_col + dc
                            ]
                            == color
                        ]
                        if len(matches) >= 2:
                            for cell_row in range(min(matches), max(matches) + 1):
                                point = (
                                    1 + 5 * cell_row + dr,
                                    1 + 5 * cell_col + dc,
                                )
                                if point in changed:
                                    vertical_changes.add(point)

    changed_colors = set(changed.values())
    if not horizontal_changes:
        errors.append("scene must expose a real horizontal span fill")
    if not vertical_changes:
        errors.append("scene must expose a real vertical span fill")
    if len(changed_colors) < 2:
        errors.append("at least two colors must synthesize previously missing cells")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "cell_rows": cell_rows,
        "cell_cols": cell_cols,
        "palette": palette,
        "palette_size": len(palette),
        "scene_profile": profile,
        "border": border,
        "common": common,
        "specials": specials,
        "output": output,
        "changed": changed,
        "changed_colors": changed_colors,
        "horizontal_changes": horizontal_changes,
        "vertical_changes": vertical_changes,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Full ownership contract, not a weak shape-only acceptance predicate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes on invalid grid: " + analysis["errors"][0])
    return {"scene_profile": analysis["scene_profile"]}


def _horizontal_only(grid):
    return _apply_rule(grid, horizontal=True, vertical=False)


def _vertical_only(grid):
    return _apply_rule(grid, horizontal=False, vertical=True)


def _first_special_only(grid):
    cell_rows, cell_cols = _geometry(grid)
    common = _common_color(grid, cell_rows, cell_cols)
    specials = sorted(set(_interior_values(grid, cell_rows, cell_cols)) - {common})
    if not specials:
        return deepcopy(grid)
    first = specials[0]
    return _apply_rule(grid, color_filter=lambda color: color == first)


SEMANTIC_RIVALS = {
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "first_special_only": _first_special_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of these rivals solves every canonical pair; no canonical shortcut is
# intentionally retained as an ambiguity in the teaching distribution.
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def _has_horizontal_propagation(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["horizontal_changes"])


def _has_vertical_propagation(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["vertical_changes"])


def _has_multiple_special_colors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["changed_colors"]) >= 2


SEMANTIC_WITNESSES = {
    "horizontal_propagation": _has_horizontal_propagation,
    "vertical_propagation": _has_vertical_propagation,
    "multiple_special_colors": _has_multiple_special_colors,
}
WITNESS_RIVALS = {
    "horizontal_propagation": ["vertical_only"],
    "vertical_propagation": ["horizontal_only"],
    "multiple_special_colors": ["first_special_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named rival survives demos but changes the query."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} input is outside the teaching grammar: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output does not match bidirectional span propagation")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Targeted malformed scenes that the structural checker must reject."""
    base = generate(431, 1, scene_profile="canonical_4x4_p5")

    separator = deepcopy(base)
    separator[0][1] = 9

    frame = deepcopy(base)
    frame[1][1] = 9

    erased_special = deepcopy(base)
    analysis = _analysis(base)
    color = max(analysis["specials"])
    for row in range(len(erased_special)):
        for col in range(len(erased_special[0])):
            if erased_special[row][col] == color:
                erased_special[row][col] = analysis["common"]

    non_integer = deepcopy(base)
    non_integer[2][2] = True

    ragged = deepcopy(base)
    ragged[-1].pop()

    return [
        ("nonzero_separator", separator),
        ("inconsistent_frame", frame),
        ("erased_special_color", erased_special),
        ("boolean_cell", non_integer),
        ("ragged_grid", ragged),
    ]
