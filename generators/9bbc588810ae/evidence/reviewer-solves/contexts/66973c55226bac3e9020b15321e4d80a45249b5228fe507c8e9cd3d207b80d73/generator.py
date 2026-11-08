"""Input sampler for task 9bbc588810ae: match a prototype up to symmetry.

The unchanged Racket authority splits a 5x23 grid at three full-height color-9
columns.  The first three 5x5 panels are colored source prototypes and the last
panel is a query.  It scans the source panels from left to right and selects the
first whose cropped shape can be transformed into the normalized query shape by
one of the authority's supported transforms.  The 5x5 answer keeps the query's
position and recolors its cells with that source panel's color.

The authority's ``rot270`` branch is accidentally identical to transpose.  This
sampler therefore exposes the seven distinct source-to-query operations that the
frozen authority actually supports, not an idealized eight-element dihedral set.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9bbc588810ae"
TASK_ID = GENERATOR_ID
RULE_HASH = "a63dd2ae1f7a"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Four 5x5 panels are separated by color-9 columns.  Exactly one of the "
    "first three colored source shapes maps to the last-panel query under one "
    "of the seven distinct transforms implemented by the frozen authority; "
    "paint the query cells with that source color.  A scheduled same-size, "
    "same-bounding-box decoy refutes the strongest canonical-fitting shortcut."
)

INVARIANTS = [
    "the input is exactly 5x23 with full color-9 dividers at columns 5, 11, and 17",
    "each 5x5 panel contains one nonempty 4-connected shape in its own distinct color",
    "exactly one source panel matches the query under the authority's seven distinct transforms",
    "ordinary draws use four query cells through eight query cells and an asymmetric query shape",
    "one nonmatching source has the same cell count and bounding-box dimensions as the query",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
MATCH_TRANSFORMS = ("id", "r1", "r2", "fh", "fv", "tr", "atr")
ALL_GEOMETRIC_TRANSFORMS = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
INVERSE_TRANSFORM = {
    "id": "id",
    "r1": "r3",
    "r2": "r2",
    "fh": "fh",
    "fv": "fv",
    "tr": "tr",
    "atr": "atr",
}

AXES = {
    "palette_kind": {
        "type": "enum",
        "default": "uniform",
        "valid": "default|warm|cool|varied",
        "doc": "Exact four-color palette family; recoverable from returned pixels.",
    },
    "transform": {
        "type": "enum",
        "default": "uniform over the seven distinct authority operations",
        "valid": "id|r1|r2|fh|fv|tr|atr",
        "doc": "Exact operation applied by the authority from the matching source to the query.",
    },
    "match_panel": {
        "type": "int",
        "default": "uniform 0..2",
        "valid": "0..2",
        "doc": "Exact zero-based source panel selected by the rule.",
    },
    "query_cells": {
        "type": "int",
        "default": "band-aware weighted choice over 4..8",
        "valid": "4..8",
        "doc": "Exact number of foreground cells in the query and matching source.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "bbox_lower_color_witness",
    "bbox_match_low",
    "permuted_colors",
)
_SCHEDULE_CYCLE = (
    "bbox_lower_color_witness",
    "bbox_match_low",
    "bbox_lower_color_witness",
    "permuted_colors",
)

_PALETTES = {
    "default": (1, 2, 3, 4),
    "warm": (2, 4, 7, 8),
    "cool": (1, 3, 5, 6),
    "varied": (2, 3, 6, 8),
}
_PALETTE_BY_SET = {frozenset(values): name for name, values in _PALETTES.items()}
_PANEL_STARTS = (0, 6, 12, 18)
_DIVIDERS = (5, 11, 17)
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive samples always cover the decisive witness profile."""
    del seed, difficulty
    return _SCHEDULE_CYCLE[int(sample_index) % len(_SCHEDULE_CYCLE)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _dimensions(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    if not points:
        return 0, 0
    return max(row for row, _ in points) + 1, max(col for _, col in points) + 1


def _transform(cells: Iterable[tuple[int, int]], code: str) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    height, width = _dimensions(points)
    if code == "id":
        raw = points
    elif code == "r1":
        raw = tuple((col, height - 1 - row) for row, col in points)
    elif code == "r2":
        raw = tuple((height - 1 - row, width - 1 - col) for row, col in points)
    elif code == "r3":
        raw = tuple((width - 1 - col, row) for row, col in points)
    elif code == "fh":
        raw = tuple((row, width - 1 - col) for row, col in points)
    elif code == "fv":
        raw = tuple((height - 1 - row, col) for row, col in points)
    elif code == "tr":
        raw = tuple((col, row) for row, col in points)
    elif code == "atr":
        raw = tuple((width - 1 - col, height - 1 - row) for row, col in points)
    else:
        raise ValueError(f"unknown transform code {code!r}")
    return _normalize(raw)


def _orbit(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    return frozenset(_transform(cells, code) for code in ALL_GEOMETRIC_TRANSFORMS)


def _signature(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int]:
    points = _normalize(cells)
    height, width = _dimensions(points)
    short, long = sorted((height, width))
    return len(points), short, long


@lru_cache(maxsize=8)
def _fixed_polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All fixed 4-connected polyominoes of ``size`` that fit a 5x5 panel."""
    if type(size) is not int or not 1 <= size <= 8:
        raise ValueError("polyomino size must be an integer in 1..8")
    shapes: set[tuple[tuple[int, int], ...]] = {((0, 0),)}
    for _ in range(1, size):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in shapes:
            occupied = set(shape)
            for row, col in shape:
                for dr, dc in _DIRECTIONS:
                    point = (row + dr, col + dc)
                    if point in occupied:
                        continue
                    candidate = _normalize((*shape, point))
                    height, width = _dimensions(candidate)
                    if height <= 5 and width <= 5:
                        expanded.add(candidate)
        shapes = expanded
    return tuple(sorted(shapes))


@lru_cache(maxsize=5)
def _query_choices(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Asymmetric queries with a same-signature non-dihedral decoy available."""
    shapes = _fixed_polyominoes(size)
    by_signature: dict[tuple[int, int, int], list[tuple[tuple[int, int], ...]]] = {}
    for shape in shapes:
        by_signature.setdefault(_signature(shape), []).append(shape)
    choices = []
    for shape in shapes:
        shape_orbit = _orbit(shape)
        if len(shape_orbit) != 8:
            continue
        if any(candidate not in shape_orbit for candidate in by_signature[_signature(shape)]):
            choices.append(shape)
    if not choices:
        raise RuntimeError(f"no asymmetric query choices for {size} cells")
    return tuple(choices)


@lru_cache(maxsize=4096)
def _same_signature_decoys(
    query: tuple[tuple[int, int], ...],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    query = _normalize(query)
    query_orbit = _orbit(query)
    return tuple(
        shape
        for shape in _fixed_polyominoes(len(query))
        if _signature(shape) == _signature(query) and shape not in query_orbit
    )


def _query_cell_options(difficulty) -> tuple[int, ...]:
    # Repetition changes only default weights; every legal override remains
    # present in every band and therefore passes the same validity gate.
    if difficulty == "easy":
        return (4, 4, 4, 5, 5, 6, 7, 8)
    if difficulty == "hard":
        return (4, 5, 6, 7, 7, 8, 8, 8)
    if difficulty == "medium":
        return (4, 5, 5, 6, 6, 7, 7, 8)
    return (4, 5, 6, 7, 8)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    palette = overrides.get("palette_kind")
    if palette is not None and (type(palette) is not str or palette not in PALETTE_KINDS):
        raise ValueError(f"palette override must be one of {PALETTE_KINDS}")

    transform = overrides.get("transform")
    if transform is not None and (type(transform) is not str or transform not in MATCH_TRANSFORMS):
        raise ValueError(
            "transform override must be one of "
            f"{MATCH_TRANSFORMS}; r3 is not implemented by the frozen authority"
        )

    panel = overrides.get("match_panel")
    if panel is not None:
        if type(panel) is not int:
            raise TypeError("match_panel override must be an integer panel index, not bool/float")
        if not 0 <= panel <= 2:
            raise ValueError("match_panel override must be in 0..2")

    cells = overrides.get("query_cells")
    if cells is not None:
        if type(cells) is not int:
            raise TypeError("query_cells override must be an integer cell count, not bool/float")
        if not 4 <= cells <= 8:
            raise ValueError("query_cells override must be in 4..8")


def _place(
    grid: list[list[int]],
    panel_index: int,
    cells: Iterable[tuple[int, int]],
    color: int,
    rng,
) -> None:
    points = _normalize(cells)
    height, width = _dimensions(points)
    row0 = rng.randint(0, 5 - height)
    col0 = rng.randint(0, 5 - width)
    left = _PANEL_STARTS[panel_index]
    for row, col in points:
        grid[row0 + row][left + col0 + col] = color


def _color_assignment(
    palette_kind: str,
    profile: str,
    match_panel: int,
    decoy_panel: int,
    other_panel: int,
    rng,
) -> tuple[list[int], int]:
    palette = list(_PALETTES[palette_kind])
    palette.sort()
    source_colors = [0, 0, 0]
    if profile == "bbox_lower_color_witness":
        source_colors[decoy_panel] = palette[0]
        source_colors[other_panel] = palette[1]
        source_colors[match_panel] = palette[2]
        query_color = palette[3]
    elif profile == "bbox_match_low":
        source_colors[match_panel] = palette[0]
        source_colors[other_panel] = palette[1]
        source_colors[decoy_panel] = palette[2]
        query_color = palette[3]
    else:
        shuffled = palette[:]
        rng.shuffle(shuffled)
        source_colors[match_panel] = shuffled[0]
        source_colors[decoy_panel] = shuffled[1]
        source_colors[other_panel] = shuffled[2]
        query_color = shuffled[3]
    return source_colors, query_color


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
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    transform = ctx.draw_choice("transform", MATCH_TRANSFORMS)
    match_panel = ctx.draw_int_strict("match_panel", 0, 2)
    query_cells = ctx.draw_choice("query_cells", _query_cell_options(difficulty))

    # Difficulty controls only the default distribution, never override validity.
    # Include the band in non-axis draw labels so the three curricula do not
    # collapse to the same geometry whenever their exact axis values coincide.
    band = difficulty if difficulty in ("easy", "medium", "hard") else "all"
    query = ctx.draw_rng(f"query_shape:{band}").choice(_query_choices(query_cells))
    decoy = ctx.draw_rng(f"same_signature_decoy:{band}").choice(_same_signature_decoys(query))
    secondary_size = 4 + ((query_cells - 4 + 2) % 5)
    secondary = ctx.draw_rng(f"secondary_distractor:{band}").choice(_fixed_polyominoes(secondary_size))
    matching_source = _transform(query, INVERSE_TRANSFORM[transform])

    remaining = [panel for panel in range(3) if panel != match_panel]
    decoy_panel = ctx.draw_rng(f"decoy_panel:{band}").choice(remaining)
    other_panel = next(panel for panel in remaining if panel != decoy_panel)
    profile = schedule_profile(seed, sample_index, difficulty)
    source_colors, query_color = _color_assignment(
        palette_kind,
        profile,
        match_panel,
        decoy_panel,
        other_panel,
        ctx.draw_rng(f"color_permutation:{band}"),
    )

    source_shapes = [secondary, secondary, secondary]
    source_shapes[match_panel] = matching_source
    source_shapes[decoy_panel] = decoy
    source_shapes[other_panel] = secondary

    grid = full_grid(5, 23, 0)
    for divider in _DIVIDERS:
        for row in range(5):
            grid[row][divider] = 9
    for panel in range(3):
        _place(
            grid,
            panel,
            source_shapes[panel],
            source_colors[panel],
            ctx.draw_rng(f"panel_{panel}_position:{band}"),
        )
    _place(grid, 3, query, query_color, ctx.draw_rng(f"query_position:{band}"))
    return grid


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or len(grid) != 5:
        return "grid must contain exactly five rows"
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return "every grid row must be a list or tuple"
    if any(len(row) != 23 for row in grid):
        return "every grid row must contain exactly 23 cells"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "grid values must be integer colors in 0..9 (not bool)"
    return None


def _panel_info(grid, panel_index: int) -> dict[str, Any]:
    left = _PANEL_STARTS[panel_index]
    positions = [
        (row, col)
        for row in range(5)
        for col in range(5)
        if grid[row][left + col] != 0
    ]
    colors = {grid[row][left + col] for row, col in positions}
    return {
        "positions": tuple(sorted(positions)),
        "shape": _normalize(positions),
        "colors": colors,
        "color": next(iter(colors)) if len(colors) == 1 else None,
    }


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen = set(stack)
    while stack:
        row, col = stack.pop()
        for dr, dc in _DIRECTIONS:
            neighbor = (row + dr, col + dc)
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == remaining


def _matching_codes(source_shape, query_shape) -> tuple[str, ...]:
    query = _normalize(query_shape)
    return tuple(
        code for code in MATCH_TRANSFORMS if _transform(source_shape, code) == query
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    shape_error = _shape_error(grid)
    if shape_error:
        return [shape_error]

    errors: list[str] = []
    for divider in _DIVIDERS:
        if any(grid[row][divider] != 9 for row in range(5)):
            errors.append(f"column {divider} must be a full-height color-9 divider")
    if any(
        grid[row][col] == 9
        for row in range(5)
        for col in range(23)
        if col not in _DIVIDERS
    ):
        errors.append("color 9 may occur only in the three divider columns")

    panels = [_panel_info(grid, index) for index in range(4)]
    for index, panel in enumerate(panels):
        if not panel["positions"]:
            errors.append(f"panel {index} must contain a nonempty shape")
            continue
        if len(panel["colors"]) != 1:
            errors.append(f"panel {index} must contain exactly one foreground color")
        if not _connected(panel["positions"]):
            errors.append(f"panel {index} foreground must be 4-connected")
    colors = [panel["color"] for panel in panels]
    if all(color is not None for color in colors) and len(set(colors)) != 4:
        errors.append("the four panel foreground colors must be distinct")
    if errors:
        return errors

    query = panels[3]["shape"]
    matches = [
        index
        for index in range(3)
        if _matching_codes(panels[index]["shape"], query)
    ]
    if len(matches) != 1:
        errors.append(f"expected exactly one matching source panel, found {matches}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    panels = [_panel_info(grid, index) for index in range(4)]
    query = panels[3]
    match_panel = next(
        index
        for index in range(3)
        if _matching_codes(panels[index]["shape"], query["shape"])
    )
    output = full_grid(5, 5, 0)
    color = panels[match_panel]["color"]
    for row, col in query["positions"]:
        output[row][col] = color
    return output


def observe_axes(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    panels = [_panel_info(grid, index) for index in range(4)]
    query = panels[3]
    hits = [
        (index, code)
        for index in range(3)
        for code in _matching_codes(panels[index]["shape"], query["shape"])
    ]
    if len(hits) != 1:
        raise ValueError(f"axes are not uniquely observable; matching hits={hits}")
    palette_set = frozenset(panel["color"] for panel in panels)
    if palette_set not in _PALETTE_BY_SET:
        raise ValueError(f"unknown generated palette {sorted(palette_set)}")
    match_panel, transform = hits[0]
    return {
        "palette_kind": _PALETTE_BY_SET[palette_set],
        "transform": transform,
        "match_panel": match_panel,
        "query_cells": len(query["positions"]),
    }


# The generic override checker recognizes this conventional name.
observe_overrides = observe_axes


def _bbox_count_lowest_color(grid) -> list[list[int]]:
    """Wrong but canonical-fitting rule: choose the lowest-color signature peer."""
    shape_error = _shape_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    panels = [_panel_info(grid, index) for index in range(4)]
    if any(not panel["positions"] or len(panel["colors"]) != 1 for panel in panels):
        raise ValueError("shortcut requires four nonempty single-color panels")
    query = panels[3]
    signature = _signature(query["shape"])
    candidates = [
        panel for panel in panels[:3] if _signature(panel["shape"]) == signature
    ]
    output = full_grid(5, 5, 0)
    if not candidates:
        return output
    color = min(panel["color"] for panel in candidates)
    for row, col in query["positions"]:
        output[row][col] = color
    return output


def _bbox_counterexample(grid) -> bool:
    try:
        return self_check(grid) == [] and _bbox_count_lowest_color(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "bbox_count_lowest_color_counterexample": _bbox_counterexample,
}
SEMANTIC_RIVALS = {
    "bbox_count_lowest_color": _bbox_count_lowest_color,
}
WITNESS_RIVALS = {
    "bbox_count_lowest_color_counterexample": ["bbox_count_lowest_color"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the prototype-match rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the prototype-match rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        competitor_answer = competitor(query["input"])
        if survives and competitor_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small reproducible malformed cases for local and intake mutation probes."""
    valid = generate(7001, 0, difficulty="medium")
    missing_query = [row[:] for row in valid]
    for row in range(5):
        for col in range(18, 23):
            missing_query[row][col] = 0

    broken_divider = [row[:] for row in valid]
    broken_divider[2][11] = 0

    duplicate_match = [row[:] for row in valid]
    panels = [_panel_info(valid, index) for index in range(4)]
    current_match = observe_axes(valid)["match_panel"]
    target_panel = next(index for index in range(3) if index != current_match)
    left = _PANEL_STARTS[target_panel]
    for row in range(5):
        for col in range(5):
            duplicate_match[row][left + col] = 0
    query_shape = panels[3]["shape"]
    _place(duplicate_match, target_panel, query_shape, panels[target_panel]["color"], _ZeroRng())

    return [
        ("missing_query", missing_query),
        ("broken_divider", broken_divider),
        ("duplicate_match", duplicate_match),
    ]


class _ZeroRng:
    """Deterministic placement helper used only by mutation_fixtures."""

    @staticmethod
    def randint(lo, hi):
        del hi
        return lo
