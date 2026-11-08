"""Constructive sampler for the exact-vertical-triple ARC rule.

Find every blue component whose normalized shape is exactly a three-cell
vertical line and recolor that component red.  All other blue components stay
blue.  Ordinary generated inputs always contain both a horizontal triple and a
vertical length-four distractor, so a lesson cannot silently teach either
"recolor every three-cell object" or "recolor every vertical/tall object".
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "17b0b2791dd2"
TASK_ID = GENERATOR_ID
RULE_HASH = "1deed242f221"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Generate separated blue vertical triples, a horizontal triple, and a "
    "vertical length-four exactness witness; recolor only exact vertical "
    "triples red."
)

INVARIANTS = [
    "background is color 0 and every input object is blue 1",
    "all blue objects are separate 4-connected components",
    "at least one component is exactly a vertical length-3 line",
    "at least one component is exactly a horizontal length-3 line",
    "ordinary generated draws include a vertical length-4 stay-blue witness",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile-weighted full-domain draw",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile-weighted full-domain draw",
        "valid": "8..14",
    },
    "vertical_count": {
        "type": "int",
        "default": "difficulty/profile-weighted full-domain draw",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_AXIS_BOUNDS = {
    "grid_h": (8, 14),
    "grid_w": (8, 14),
    "vertical_count": (1, 3),
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Grid = list[list[int]]

_VERTICAL3: Shape = ((0, 0), (1, 0), (2, 0))
_VERTICAL4: Shape = ((0, 0), (1, 0), (2, 0), (3, 0))
_HORIZONTAL3: Shape = ((0, 0), (0, 1), (0, 2))
_ALLOWED_SHAPES = {
    _VERTICAL3: "vertical3",
    _VERTICAL4: "vertical4",
    _HORIZONTAL3: "horizontal3",
}

# The first three profiles reproduce the canonical canvas/count profiles.  The
# remaining entries span every public dimension and vertical-count boundary.
_PROFILE_SCHEDULE = (
    (8, 8, 1),
    (9, 9, 2),
    (10, 10, 2),
    (11, 12, 3),
    (12, 14, 1),
    (13, 11, 2),
    (14, 13, 3),
)
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _draw_weighted_axis(ctx, label: str, preferred: int, *, weight: int = 40) -> int:
    """Draw from the complete public domain while strongly preferring a profile."""
    lo, hi = _AXIS_BOUNDS[label]
    if label in ctx.overrides:
        return ctx.draw_int_strict(label, lo, hi)
    domain = tuple(range(lo, hi + 1))
    return int(ctx.draw_choice(label, (preferred,) * weight + domain))


def _translated(shape: Shape, top: int, left: int) -> frozenset[Cell]:
    return frozenset((top + row, left + col) for row, col in shape)


def _guard(cells: Iterable[Cell], height: int, width: int) -> frozenset[Cell]:
    guarded = set(cells)
    for row, col in tuple(guarded):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = row + dr, col + dc
            if 0 <= rr < height and 0 <= cc < width:
                guarded.add((rr, cc))
    return frozenset(guarded)


def _placements(shape: Shape, height: int, width: int):
    max_row = max(row for row, _ in shape)
    max_col = max(col for _, col in shape)
    for top in range(height - max_row):
        for left in range(width - max_col):
            cells = _translated(shape, top, left)
            yield cells, _guard(cells, height, width)


def _construct_layout(
    height: int, width: int, vertical_count: int, rng
) -> list[frozenset[Cell]]:
    """Place all objects by randomized backtracking with one-cell separation."""
    shapes = [_VERTICAL4, _HORIZONTAL3] + [_VERTICAL3] * vertical_count
    # Largest first minimizes search.  The random tie-break changes repeated
    # vertical-triple placement order without weakening determinism.
    shapes.sort(key=lambda shape: (-len(shape), rng.random()))
    candidates = [list(_placements(shape, height, width)) for shape in shapes]
    for options in candidates:
        rng.shuffle(options)

    placed: list[frozenset[Cell]] = []

    def search(index: int, blocked: frozenset[Cell]) -> bool:
        if index == len(candidates):
            return True
        for cells, guarded in candidates[index]:
            if not cells.isdisjoint(blocked):
                continue
            placed.append(cells)
            if search(index + 1, blocked | guarded):
                return True
            placed.pop()
        return False

    if not search(0, frozenset()):
        raise RuntimeError(
            "declared object counts unexpectedly do not fit the selected grid"
        )
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, override-exact lawful input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _PROFILE_SCHEDULE[
        (sample_index + _BAND_OFFSETS[difficulty]) % len(_PROFILE_SCHEDULE)
    ]
    height = _draw_weighted_axis(ctx, "grid_h", profile[0])
    width = _draw_weighted_axis(ctx, "grid_w", profile[1])
    vertical_count = _draw_weighted_axis(
        ctx, "vertical_count", profile[2], weight=28
    )

    grid = full_grid(height, width, 0)
    layout = _construct_layout(
        height, width, vertical_count, ctx.draw_rng("constructive_layout")
    )
    for cells in layout:
        for row, col in cells:
            grid[row][col] = 1

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator produced invalid grid: {errors}")
    expected = {
        "grid_h": height,
        "grid_w": width,
        "vertical_count": vertical_count,
    }
    if observe_overrides(grid) != expected:
        raise RuntimeError("constructive generator failed exact override recovery")
    if not _has_vertical_four(grid):
        raise RuntimeError("constructive generator omitted exactness witness")
    return grid


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a non-empty sequence of rows"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid rows must be non-empty sequences"
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return "grid rows must have equal non-zero width"
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid cells must be integer ARC colors 0..9 (not bools)"
    return None


def _components_of_one(grid: Sequence[Sequence[int]]) -> list[list[Cell]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Cell] = set()
    components: list[list[Cell]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _normalize(cells: Sequence[Cell]) -> Shape:
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _analyze(grid: Any) -> tuple[dict[str, int], list[str]]:
    stats = {
        "grid_h": 0,
        "grid_w": 0,
        "vertical_count": 0,
        "horizontal3_count": 0,
        "vertical4_count": 0,
    }
    error = _grid_error(grid)
    if error:
        return stats, [error]

    height = len(grid)
    width = len(grid[0])
    stats["grid_h"] = height
    stats["grid_w"] = width
    errors: list[str] = []
    if not 8 <= height <= 14:
        errors.append(f"grid height {height} outside 8..14")
    if not 8 <= width <= 14:
        errors.append(f"grid width {width} outside 8..14")

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("input must contain background color 0")
    illegal = sorted(palette - {0, 1})
    if illegal:
        errors.append(f"input may use only colors 0 and 1, found {illegal}")

    for cells in _components_of_one(grid):
        shape = _normalize(cells)
        name = _ALLOWED_SHAPES.get(shape)
        if name == "vertical3":
            stats["vertical_count"] += 1
        elif name == "vertical4":
            stats["vertical4_count"] += 1
        elif name == "horizontal3":
            stats["horizontal3_count"] += 1
        else:
            errors.append(
                "every blue component must be an exact vertical-3, "
                "vertical-4, or horizontal-3 line"
            )

    if not 1 <= stats["vertical_count"] <= 3:
        errors.append(
            "expected 1..3 exact vertical length-3 targets, found "
            f"{stats['vertical_count']}"
        )
    if stats["horizontal3_count"] < 1:
        errors.append("missing horizontal length-3 stay-blue distractor")
    if stats["horizontal3_count"] > 4:
        errors.append("too many horizontal length-3 distractors")
    if stats["vertical4_count"] > 2:
        errors.append("too many vertical length-4 distractors")
    return stats, errors


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    """Recover every public axis exactly from a lawful returned input."""
    stats, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return {
        "grid_h": stats["grid_h"],
        "grid_w": stats["grid_w"],
        "vertical_count": stats["vertical_count"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete declared input grammar, including canonicals."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _apply_rule(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    for cells in _components_of_one(grid):
        if _normalize(cells) == _VERTICAL3:
            for row, col in cells:
                output[row][col] = 2
    return output


rule_mirror = _apply_rule


def _is_vertical_line(cells: Sequence[Cell]) -> bool:
    rows = sorted(row for row, _ in cells)
    cols = {col for _, col in cells}
    return len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1))


def _recolor_every_vertical_line(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    for cells in _components_of_one(grid):
        if _is_vertical_line(cells):
            for row, col in cells:
                output[row][col] = 2
    return output


def _recolor_every_three_cell_component(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    for cells in _components_of_one(grid):
        if len(cells) == 3:
            for row, col in cells:
                output[row][col] = 2
    return output


def _has_vertical_four(grid: Sequence[Sequence[int]]) -> bool:
    return any(_normalize(cells) == _VERTICAL4 for cells in _components_of_one(grid))


def _has_horizontal_three(grid: Sequence[Sequence[int]]) -> bool:
    return any(
        _normalize(cells) == _HORIZONTAL3 for cells in _components_of_one(grid)
    )


SEMANTIC_WITNESSES: dict[
    str, Callable[[Sequence[Sequence[int]]], bool]
] = {
    "vertical_length_four_distractor": _has_vertical_four,
    "horizontal_length_three_distractor": _has_horizontal_three,
}
SEMANTIC_RIVALS: dict[
    str, Callable[[Sequence[Sequence[int]]], Grid]
] = {
    "recolor_every_vertical_line": _recolor_every_vertical_line,
    "recolor_every_three_cell_component": _recolor_every_three_cell_component,
}
WITNESS_RIVALS = {
    "vertical_length_four_distractor": ["recolor_every_vertical_line"],
    "horizontal_length_three_distractor": [
        "recolor_every_three_cell_component"
    ],
}
CANONICAL_SHORTCUTS = {
    "recolor_every_vertical_line": _recolor_every_vertical_line,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _validate_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the declared grammar: {errors[0]}"]
    if pair["output"] != _apply_rule(pair["input"]):
        return [f"{label} output disagrees with exact-vertical-triple rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared plausible competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    reasons.extend(_validate_pair(query, "query"))
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(deepcopy(demo["input"])) == demo["output"]
            for demo in demos
        ):
            reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
