"""Generator for ARC task 2d4e8c8fa10e: keep exact magenta 2x2 objects.

The authoritative rule treats cardinally connected magenta (6) components as
objects.  It copies a component to the output iff the *entire component* is a
solid 2x2 square; every other magenta component is erased.  The curriculum
therefore includes same-size tetrominoes in both horizontal and vertical
orientations plus 2x2-with-a-tail objects, not only smaller distractors, so
local-square, object-size, bounding-box, and largest-object shortcuts are
explicitly falsified.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2d4e8c8fa10e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "dbcfc990f307"

SUMMARY = (
    "On a black background, keep every cardinally connected magenta object "
    "whose whole shape is exactly a solid 2x2 square; erase every other "
    "magenta object, including horizontal/vertical tetrominoes and 2x2 squares "
    "with an attached tail."
)

INVARIANTS = [
    "the input is an 8..10 by 9..11 rectangular grid using exactly colors 0 and 6",
    "there are 1..3 exact solid 2x2 magenta components",
    "there are 1..3 non-square magenta components",
    "all components are separated, so object identity is unambiguous",
    "the output keeps whole components iff the component is exactly a 2x2 square",
]

COUNTER_HYPOTHESES = [
    "keep every four-cell object",
    "keep every four-cell object whose bounding-box height is two",
    "keep any object that contains a local solid 2x2 block",
    "keep only the largest object or objects",
    "keep only the first solid 2x2 object",
    "return the input unchanged",
]

# Every public axis is exact, finite, consumed by GenCtx, and recovered from the
# returned grid by observe_overrides().  The full Cartesian boundary set fits
# even in the smallest 8x9 canvas.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile canonical schedule",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile canonical schedule",
        "valid": "9..11",
    },
    "square_count": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
    "distractor_count": {
        "type": "int",
        "default": "2",
        "valid": "1..3",
    },
    "distractor_profile": {
        "type": "str",
        "default": "scheduled semantic control",
        "valid": "triomino|tetromino|square_tail",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORHOOD = tuple(
    (dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
)
_DISTRACTOR_PROFILES = ("triomino", "tetromino", "square_tail")
_CANONICAL_DIMS = {(8, 9), (9, 10), (10, 11)}

# Shapes are normalized. Tetrominoes deliberately cover both 3x2 and 2x3
# bounding boxes so a height-two bounding-box shortcut is observable.
_TETROMINO_VERTICAL = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
)
_TETROMINO_HORIZONTAL = tuple(
    tuple(sorted((col, row) for row, col in shape))
    for shape in _TETROMINO_VERTICAL
)

_SHAPES: dict[str, tuple[tuple[tuple[int, int], ...], ...]] = {
    "triomino": (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    "tetromino": _TETROMINO_VERTICAL + _TETROMINO_HORIZONTAL,
    "square_tail": (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
}

_PROFILES: tuple[dict[str, object], ...] = (
    {
        "name": "canonical_8x9_triomino",
        "grid_h": 8,
        "grid_w": 9,
        "square_count": 1,
        "distractor_count": 2,
        "distractor_profile": "triomino",
    },
    {
        "name": "canonical_9x10_tetromino_control",
        "grid_h": 9,
        "grid_w": 10,
        "square_count": 2,
        "distractor_count": 2,
        "distractor_profile": "tetromino",
    },
    {
        "name": "canonical_10x11_square_tail_control",
        "grid_h": 10,
        "grid_w": 11,
        "square_count": 3,
        "distractor_count": 2,
        "distractor_profile": "square_tail",
    },
)
SCHEDULE_PROFILES = tuple(str(profile["name"]) for profile in _PROFILES)


def _validate_identity(seed: int, sample_index: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic three-example teaching profile."""
    _validate_identity(seed, sample_index)
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    index = (int(sample_index) + offsets[difficulty]) % len(_PROFILES)
    return str(_PROFILES[index]["name"])


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, object]:
    name = schedule_profile(0, sample_index, difficulty)
    return next(profile for profile in _PROFILES if profile["name"] == name)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    int_bounds = {
        "grid_h": (8, 10),
        "grid_w": (9, 11),
        "square_count": (1, 3),
        "distractor_count": (1, 3),
    }
    for name, (lo, hi) in int_bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")

    profile = overrides.get("distractor_profile")
    if profile is not None:
        if type(profile) is not str:
            raise ValueError("distractor_profile must be a string")
        if profile not in _DISTRACTOR_PROFILES:
            raise ValueError(
                "distractor_profile must be triomino, tetromino, or square_tail"
            )


def _draw_exact_int(ctx, overrides: dict[str, Any], label: str,
                    default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_exact_choice(ctx, overrides: dict[str, Any], label: str,
                       default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = list(cells)
    if not values:
        return ()
    r0 = min(row for row, _ in values)
    c0 = min(col for _, col in values)
    return tuple(sorted((row - r0, col - c0) for row, col in values))


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _bbox_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    return _shape_dims(_normalize(points))


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            text = row.strip()
            if not text or any(ch not in "0123456789" for ch in text):
                raise ValueError("string rows must contain ARC digits")
            values = [int(ch) for ch in text]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("grid cells must be integer ARC colors in 0..9")
        rows.append(values)
    return rows


def _components(grid: list[list[int]], color: int = 6) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == color
    }
    components: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(tuple(sorted(cells)))
    return sorted(components, key=lambda cells: min(cells))


def _is_exact_square(cells: Iterable[tuple[int, int]]) -> bool:
    return _normalize(cells) == _SQUARE


def _contains_local_square(cells: Iterable[tuple[int, int]]) -> bool:
    points = set(cells)
    return any(
        {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
        <= points
        for row, col in points
    )


def _is_square_tail(cells: Iterable[tuple[int, int]]) -> bool:
    points = set(cells)
    if len(points) != 5 or not _contains_local_square(points):
        return False
    return any(_is_exact_square(points - {cell}) for cell in points)


def _distractor_kind(cells: Iterable[tuple[int, int]]) -> str | None:
    points = tuple(cells)
    if len(points) == 3:
        return "triomino"
    if len(points) == 4 and not _is_exact_square(points):
        return "tetromino"
    if _is_square_tail(points):
        return "square_tail"
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    colors = {value for row in values for value in row}
    components = _components(values)
    squares = [cells for cells in components if _is_exact_square(cells)]
    distractors = [cells for cells in components if not _is_exact_square(cells)]
    kinds = [_distractor_kind(cells) for cells in distractors]

    errors: list[str] = []
    if not 8 <= h <= 10 or not 9 <= w <= 11:
        errors.append(f"grid dimensions {h}x{w} must be within 8..10 by 9..11")
    if colors != {0, 6}:
        errors.append(f"input colors must be exactly {{0,6}}, found {sorted(colors)}")
    if not 1 <= len(squares) <= 3:
        errors.append(f"expected 1..3 exact 2x2 components, found {len(squares)}")
    if not 1 <= len(distractors) <= 3:
        errors.append(f"expected 1..3 distractor components, found {len(distractors)}")
    if any(kind is None for kind in kinds):
        bad_sizes = [len(cells) for cells, kind in zip(distractors, kinds) if kind is None]
        errors.append(
            "every distractor must be a triomino, non-square tetromino, or "
            f"2x2-with-one-tail object; bad sizes/shapes={bad_sizes}"
        )
    kind_set = {kind for kind in kinds if kind is not None}
    if len(kind_set) > 1:
        errors.append(f"all distractors must share one profile, found {sorted(kind_set)}")

    # A diagonal touch does not merge under the Racket object's cardinal
    # connectivity, but excluding it keeps object boundaries visually explicit.
    object_of: dict[tuple[int, int], int] = {}
    for index, cells in enumerate(components):
        for cell in cells:
            object_of[cell] = index
    touching: set[tuple[int, int]] = set()
    for (row, col), index in object_of.items():
        for dr, dc in _NEIGHBORHOOD:
            other = object_of.get((row + dr, col + dc))
            if other is not None and other != index:
                touching.add(tuple(sorted((index, other))))
    if touching:
        errors.append(f"distinct components must not touch, including diagonally: {sorted(touching)}")

    profile = next(iter(kind_set), None) if len(kind_set) == 1 else None
    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "colors": colors,
        "components": components,
        "squares": squares,
        "distractors": distractors,
        "square_count": len(squares),
        "distractor_count": len(distractors),
        "distractor_profile": profile,
        "magenta_count": sum(value == 6 for row in values for value in row),
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def _translated(shape: tuple[tuple[int, int], ...], row0: int, col0: int) -> tuple[tuple[int, int], ...]:
    return tuple((row0 + row, col0 + col) for row, col in shape)


def _all_candidates(shape: tuple[tuple[int, int], ...], h: int, w: int, rng) -> list[tuple[tuple[int, int], ...]]:
    sh, sw = _shape_dims(shape)
    candidates = [
        _translated(shape, row, col)
        for row in range(h - sh + 1)
        for col in range(w - sw + 1)
    ]
    rng.shuffle(candidates)
    return candidates


def _place_backtracking(
    shapes: list[tuple[tuple[int, int], ...]], h: int, w: int, rng
) -> list[tuple[tuple[int, int], ...]] | None:
    # Larger footprints first make dead ends visible early. A keyed random tie
    # breaker preserves diversity without using process-global randomness.
    order = list(range(len(shapes)))
    tie = {index: rng.random() for index in order}
    order.sort(key=lambda index: (-len(shapes[index]), tie[index]))
    candidates = {
        index: _all_candidates(shapes[index], h, w, rng)
        for index in order
    }
    chosen: dict[int, tuple[tuple[int, int], ...]] = {}

    def search(depth: int, blocked: set[tuple[int, int]]) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for cells in candidates[index]:
            if any(cell in blocked for cell in cells):
                continue
            next_blocked = set(blocked)
            for row, col in cells:
                for dr, dc in _NEIGHBORHOOD:
                    next_blocked.add((row + dr, col + dc))
            chosen[index] = cells
            if search(depth + 1, next_blocked):
                return True
            chosen.pop(index, None)
        return False

    if not search(0, set()):
        return None
    return [chosen[index] for index in range(len(shapes))]


def _fallback_slots(
    shapes: list[tuple[tuple[int, int], ...]], h: int, w: int, rng
) -> list[tuple[tuple[int, int], ...]]:
    """Deterministic exhaustive fallback that supports either orientation."""
    del rng

    class _OrderedRng:
        @staticmethod
        def random() -> float:
            return 0.0

        @staticmethod
        def shuffle(values) -> None:
            del values

    placed = _place_backtracking(shapes, h, w, _OrderedRng())
    if placed is None:
        raise AssertionError(
            f"no separated placement for {len(shapes)} supported objects on {h}x{w}"
        )
    return placed


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_identity(seed, sample_index)
    _validate_call(difficulty, overrides)
    profile = _profile_for(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", int(profile["grid_h"]), 8, 10)
    w = _draw_exact_int(ctx, overrides, "grid_w", int(profile["grid_w"]), 9, 11)
    square_count = _draw_exact_int(
        ctx, overrides, "square_count", int(profile["square_count"]), 1, 3
    )
    distractor_count = _draw_exact_int(
        ctx, overrides, "distractor_count", int(profile["distractor_count"]), 1, 3
    )
    distractor_profile = _draw_exact_choice(
        ctx,
        overrides,
        "distractor_profile",
        str(profile["distractor_profile"]),
        _DISTRACTOR_PROFILES,
    )
    rng = ctx.draw_rng("layout")

    shapes: list[tuple[tuple[int, int], ...]] = [_SQUARE] * square_count
    for index in range(distractor_count):
        # Two or more tetromino controls always include both bounding-box
        # orientations. A single overridden control alternates by sample index.
        if distractor_profile == "tetromino":
            variants = (
                _TETROMINO_VERTICAL
                if (sample_index + index) % 2 == 0
                else _TETROMINO_HORIZONTAL
            )
        else:
            variants = _SHAPES[distractor_profile]
        variant = variants[rng.randrange(len(variants))]
        shapes.append(variant)
    rng.shuffle(shapes)

    placements = _place_backtracking(shapes, h, w, rng)
    if placements is None:
        placements = _fallback_slots(shapes, h, w, rng)
    grid = full_grid(h, w, 0)
    for cells in placements:
        for row, col in cells:
            grid[row][col] = 6

    requested = {
        "grid_h": h,
        "grid_w": w,
        "square_count": square_count,
        "distractor_count": distractor_count,
        "distractor_profile": distractor_profile,
    }
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.overrides_used()},
    )
    if errors:
        raise AssertionError("generator produced invalid task grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != requested:
        raise AssertionError(f"exact-axis mismatch: requested={requested}, observed={observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides")
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(
                    f"meta {axis} requested {value!r}, observed {observed[axis]!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "square_count": analysis["square_count"],
        "distractor_count": analysis["distractor_count"],
        "distractor_profile": analysis["distractor_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    """The exact task grammar; all canonical inputs and all ordinary draws pass."""
    analysis = _analyze(grid)
    return list(analysis.get("errors", []))


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    analysis = _analysis_or_raise(grid)
    out = full_grid(analysis["height"], analysis["width"], 0)
    for cells in analysis["squares"]:
        for row, col in cells:
            out[row][col] = 6
    return out


def _paint_components(analysis: dict[str, Any], selected: Iterable[Iterable[tuple[int, int]]]) -> list[list[int]]:
    out = full_grid(analysis["height"], analysis["width"], 0)
    for cells in selected:
        for row, col in cells:
            out[row][col] = 6
    return out


def _rival_keep_all_size4(grid):
    analysis = _analysis_or_raise(grid)
    selected = [cells for cells in analysis["components"] if len(cells) == 4]
    return _paint_components(analysis, selected)


def _rival_keep_size4_height2(grid):
    """Canonical-fitting shortcut: keep size-four objects two rows high."""
    analysis = _analysis_or_raise(grid)
    selected = [
        cells
        for cells in analysis["components"]
        if len(cells) == 4 and _bbox_dims(cells)[0] == 2
    ]
    return _paint_components(analysis, selected)


def _rival_keep_any_local_2x2(grid):
    analysis = _analysis_or_raise(grid)
    selected = [cells for cells in analysis["components"] if _contains_local_square(cells)]
    return _paint_components(analysis, selected)


def _rival_keep_largest_components(grid):
    analysis = _analysis_or_raise(grid)
    largest = max(len(cells) for cells in analysis["components"])
    selected = [cells for cells in analysis["components"] if len(cells) == largest]
    return _paint_components(analysis, selected)


def _rival_keep_first_square_only(grid):
    analysis = _analysis_or_raise(grid)
    return _paint_components(analysis, analysis["squares"][:1])


def _rival_keep_everything(grid):
    analysis = _analysis_or_raise(grid)
    return [row[:] for row in analysis["grid"]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "keep_all_size4": _rival_keep_all_size4,
    "keep_size4_height2": _rival_keep_size4_height2,
    "keep_any_local_2x2": _rival_keep_any_local_2x2,
    "keep_largest_components": _rival_keep_largest_components,
    "keep_first_square_only": _rival_keep_first_square_only,
    "keep_everything": _rival_keep_everything,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "keep_all_size4": _rival_keep_all_size4,
    "keep_size4_height2": _rival_keep_size4_height2,
    "keep_any_local_2x2": _rival_keep_any_local_2x2,
    "keep_largest_components": _rival_keep_largest_components,
}


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


SEMANTIC_WITNESSES = {
    "canonical_linked_dimensions": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and (analysis["height"], analysis["width"]) in _CANONICAL_DIMS
    ),
    "keep_and_erase_branches": lambda grid: _valid_analysis(grid) is not None,
    "same_size_tetromino_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["distractor_profile"] == "tetromino"
    ),
    "horizontal_tetromino_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["distractor_profile"] == "tetromino"
        and any(_bbox_dims(cells) == (2, 3) for cells in analysis["distractors"])
    ),
    "square_tail_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["distractor_profile"] == "square_tail"
    ),
    "multiple_kept_squares": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["square_count"] >= 2
    ),
}

WITNESS_RIVALS = {
    "canonical_linked_dimensions": ["keep_everything"],
    "keep_and_erase_branches": ["keep_everything"],
    "same_size_tetromino_control": [
        "keep_all_size4",
        "keep_largest_components",
    ],
    "horizontal_tetromino_control": ["keep_size4_height2"],
    "square_tail_control": [
        "keep_any_local_2x2",
        "keep_largest_components",
    ],
    "multiple_kept_squares": ["keep_first_square_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} input violates teaching grammar: {errors[0]}")
            continue
        try:
            expected = rule_mirror(pair["input"])
            actual = _coerce_grid(pair["output"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"{label} could not be checked: {exc}")
            continue
        if expected != actual:
            reasons.append(f"{label} output disagrees with exact-component filtering")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == _coerce_grid(demo["output"])
            for demo in demos
        )
        if survives:
            if competitor(query["input"]) != _coerce_grid(query["output"]):
                reasons.append(
                    f"competing rule {name!r} fits every demo but answers the query differently"
                )
            else:
                reasons.append(f"competing rule {name!r} survives every demo and query")
    return reasons
