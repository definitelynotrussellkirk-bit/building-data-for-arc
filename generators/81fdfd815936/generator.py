"""Generator for selecting the first left-right-symmetric object crop.

Canonical rule
--------------
Extract same-colour 4-connected nonzero objects, keep the objects whose tight
bounding-box masks are invariant under a left-right reflection, sort those
candidates by ``(top_row, left_col)``, and return the tight crop of the first.

The two-profile teaching schedule always includes two symmetric candidates.
One profile places an asymmetric object before the selected candidate and makes
the selected candidate larger than the later symmetric candidate; the other
places the selected candidate first and makes it smaller.  Any three consecutive
examples, including every three-of-four query rotation, therefore refute
``first object``, ``smallest symmetric``, ``largest symmetric``, and ``last
symmetric`` shortcuts while preserving the canonical three-object / three-colour
grammar.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81fdfd815936"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "320c881d146b"

SUMMARY = (
    "A 10..12 by 12..14 zero-background grid contains exactly three separated "
    "monochrome objects in three distinct colours. At least one object is "
    "left-right symmetric. Among the symmetric candidates sorted by "
    "(top_row, left_col), output the tight crop of the first candidate."
)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "asymmetric_first_selected_larger",
    "selected_first_selected_smaller",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid dimensions are 10..12 rows by 12..14 columns",
    "background is 0 and all cells are integer ARC colours 0..9",
    "there are exactly three separated same-colour 4-connected objects",
    "the three objects use three distinct nonzero colours",
    "at least one object is LR-symmetric and at least one is LR-asymmetric",
    "the output is the crop of the first LR-symmetric object by (top,left)",
    "generated defaults contain two symmetric candidates and teach the ordering tie-break",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed rng 10..12",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed rng 12..14",
        "valid": "12..14",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Component = tuple[int, list[tuple[int, int]]]
Shape = tuple[tuple[int, int], ...]

# Connected, irregular, exact LR-symmetric masks.  The two banks have disjoint
# cell-count ranges so the schedule can produce explicit size-order witnesses.
_SMALL_SYMMETRIC: tuple[Shape, ...] = (
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
)
_LARGE_SYMMETRIC: tuple[Shape, ...] = (
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 2), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4)),
    ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
     (2, 1), (2, 2), (2, 3)),
)
_ASYMMETRIC: tuple[Shape, ...] = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
)


def _validate_call(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    limits = {"grid_h": (10, 12), "grid_w": (12, 14)}
    for label, (low, high) in limits.items():
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{label} override must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"{label} override {value} is outside {low}..{high}")


def _bbox(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _shape_dims(shape: Shape | list[tuple[int, int]]) -> tuple[int, int]:
    row0, col0, row1, col1 = _bbox(shape)
    return row1 - row0 + 1, col1 - col0 + 1


def _components4(grid: Grid) -> list[Component]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[Component] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return sorted(components, key=lambda component: _bbox(component[1])[:2])


def _is_lr_symmetric(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> bool:
    row0, col0, _, col1 = _bbox(cells)
    normalized = {(row - row0, col - col0) for row, col in cells}
    width = col1 - col0 + 1
    return all((row, width - 1 - col) in normalized for row, col in normalized)


def _crop_component(grid: Grid, component: Component) -> Grid:
    _, cells = component
    row0, col0, row1, col1 = _bbox(cells)
    return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]


def _analysis(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"], None
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"], None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid rows must have equal width"], None

    height = len(grid)
    errors: list[str] = []
    if not 10 <= height <= 12 or not 12 <= width <= 14:
        errors.append(f"expected dimensions 10..12 by 12..14, got {height}x{width}")

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) is not an integer ARC colour 0..9"
                )
                if len(errors) >= 4:
                    return errors, None

    components = _components4(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three 4-connected objects, found {len(components)}")

    colors = {color for color, _ in components}
    if len(colors) != 3:
        errors.append(f"expected three distinct nonzero object colours, found {len(colors)}")

    symmetric_indices: list[int] = []
    asymmetric_indices: list[int] = []
    for index, (_, cells) in enumerate(components):
        shape_height, shape_width = _shape_dims(cells)
        if len(cells) < 3:
            errors.append(f"object {index} is too small ({len(cells)} cells)")
        if shape_height < 2 or shape_width < 2:
            errors.append(
                f"object {index} has degenerate {shape_height}x{shape_width} bounding box"
            )
        if _is_lr_symmetric(cells):
            symmetric_indices.append(index)
        else:
            asymmetric_indices.append(index)

    if not symmetric_indices:
        errors.append("expected at least one LR-symmetric object")
    if not asymmetric_indices:
        errors.append("expected at least one LR-asymmetric object")

    analysis = {
        "height": height,
        "width": width,
        "components": components,
        "symmetric_indices": symmetric_indices,
        "asymmetric_indices": asymmetric_indices,
        "target_index": symmetric_indices[0] if symmetric_indices else None,
    }
    return errors, analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full canonical three-object domain without overfitting tie counts."""
    del difficulty, meta
    errors, _ = _analysis(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the structural manifold shared by all official inputs."""
    errors, _ = _analysis(grid)
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover both advertised dimension axes exactly from a valid grid."""
    errors, analysis = _analysis(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {"grid_h": analysis["height"], "grid_w": analysis["width"]}


def rule_mirror(grid: Grid) -> Grid:
    """Pure-Python mirror of the pinned canonical Racket authority."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("outside rule domain: empty or malformed grid")
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("outside rule domain: ragged grid")
    candidates = [component for component in _components4(grid) if _is_lr_symmetric(component[1])]
    if not candidates:
        raise ValueError("outside rule domain: no LR-symmetric object")
    return _crop_component(grid, candidates[0])


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternate the two shortcut-refuting teaching profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _profile_shape_pools(difficulty: str | None):
    # Easy favors the canonical T/plus silhouettes; hard uses the full irregular
    # bank.  The semantic size ordering is unchanged in every band.
    if difficulty == "easy":
        return _SMALL_SYMMETRIC[:4], _LARGE_SYMMETRIC[:4], _ASYMMETRIC[:4]
    if difficulty == "medium" or difficulty is None:
        return _SMALL_SYMMETRIC[:5], _LARGE_SYMMETRIC[:5], _ASYMMETRIC[:5]
    return _SMALL_SYMMETRIC, _LARGE_SYMMETRIC, _ASYMMETRIC


def _paint_shape(grid: Grid, shape: Shape, color: int, row0: int, col0: int) -> None:
    for dr, dc in shape:
        row, col = row0 + dr, col0 + dc
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            raise RuntimeError("internal placement overflow")
        if grid[row][col] != 0:
            raise RuntimeError("internal object overlap")
        grid[row][col] = color


def _place_three(grid: Grid, shapes: list[Shape], colors: list[int], rng) -> None:
    """Place objects in stable row-major slots with at least one blank separator."""
    height, width = len(grid), len(grid[0])
    dims = [_shape_dims(shape) for shape in shapes]
    top_row = rng.randint(1, 2)

    left_height, left_width = dims[0]
    right_height, right_width = dims[1]
    bottom_height, bottom_width = dims[2]
    del left_height, right_height

    left_col = rng.randint(1, 6 - left_width)
    right_col = rng.randint(7, width - right_width)
    bottom_row = rng.randint(max(top_row + 4, height - 4), height - bottom_height)
    bottom_col = rng.randint(1, width - bottom_width - 1)

    placements = (
        (top_row, left_col),
        (top_row, right_col),
        (bottom_row, bottom_col),
    )
    for shape, color, (row0, col0) in zip(shapes, colors, placements):
        _paint_shape(grid, shape, color, row0, col0)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_strict("grid_h", 10, 12)
    width = ctx.draw_int_strict("grid_w", 12, 14)
    shape_rng = ctx.draw_rng("shape_family")
    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("palette")

    small_pool, large_pool, asymmetric_pool = _profile_shape_pools(difficulty)
    small = shape_rng.choice(small_pool)
    large = shape_rng.choice(large_pool)
    asymmetric = shape_rng.choice(asymmetric_pool)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "asymmetric_first_selected_larger":
        shapes = [asymmetric, large, small]
    elif profile == "selected_first_selected_smaller":
        shapes = [small, asymmetric, large]
    else:  # pragma: no cover - closed schedule
        raise RuntimeError(f"unknown internal schedule profile: {profile}")

    colors = color_rng.sample(range(1, 10), 3)
    grid = full_grid(height, width, 0)
    _place_three(grid, shapes, colors, layout_rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator defect: {errors}")
    return grid


def _safe_components(grid) -> list[Component]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return []
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return []
    return _components4(grid)


def _first_object(grid):
    components = _safe_components(grid)
    return _crop_component(grid, components[0]) if components else []


def _symmetric_candidates(grid) -> list[Component]:
    return [component for component in _safe_components(grid) if _is_lr_symmetric(component[1])]


def _smallest_symmetric(grid):
    candidates = _symmetric_candidates(grid)
    if not candidates:
        return []
    selected = min(enumerate(candidates), key=lambda item: (len(item[1][1]), item[0]))[1]
    return _crop_component(grid, selected)


def _largest_symmetric(grid):
    candidates = _symmetric_candidates(grid)
    if not candidates:
        return []
    selected = max(enumerate(candidates), key=lambda item: (len(item[1][1]), -item[0]))[1]
    return _crop_component(grid, selected)


def _last_symmetric(grid):
    candidates = _symmetric_candidates(grid)
    return _crop_component(grid, candidates[-1]) if candidates else []


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_object": _first_object,
    "smallest_symmetric": _smallest_symmetric,
    "largest_symmetric": _largest_symmetric,
    "last_symmetric": _last_symmetric,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {
    "smallest_symmetric": _smallest_symmetric,
}


def _valid_analysis(grid) -> dict[str, Any] | None:
    errors, analysis = _analysis(grid)
    return analysis if not errors else None


def _asymmetric_before_selected(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    target = analysis["target_index"]
    return any(index < target for index in analysis["asymmetric_indices"])


def _selected_not_smallest(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None or len(analysis["symmetric_indices"]) < 2:
        return False
    components = analysis["components"]
    target_size = len(components[analysis["target_index"]][1])
    return target_size > min(len(components[index][1]) for index in analysis["symmetric_indices"])


def _selected_not_largest(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None or len(analysis["symmetric_indices"]) < 2:
        return False
    components = analysis["components"]
    target_size = len(components[analysis["target_index"]][1])
    return target_size < max(len(components[index][1]) for index in analysis["symmetric_indices"])


def _selected_not_last(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and len(analysis["symmetric_indices"]) >= 2
        and analysis["target_index"] != analysis["symmetric_indices"][-1]
    )


def _multiple_symmetric_candidates(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["symmetric_indices"]) >= 2


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "asymmetric_before_selected": _asymmetric_before_selected,
    "selected_not_smallest": _selected_not_smallest,
    "selected_not_largest": _selected_not_largest,
    "selected_not_last": _selected_not_last,
    "multiple_symmetric_candidates": _multiple_symmetric_candidates,
}
WITNESS_RIVALS = {
    "asymmetric_before_selected": ["first_object"],
    "selected_not_smallest": ["smallest_symmetric"],
    "selected_not_largest": ["largest_symmetric"],
    "selected_not_last": ["last_symmetric"],
}
BRANCH_WITNESSES = ("multiple_symmetric_candidates",)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared shortcut survives all demonstrations."""
    reasons: list[str] = []
    if len(demos) != EXAMPLES_NEEDED:
        reasons.append(f"expected {EXAMPLES_NEEDED} demonstrations, found {len(demos)}")

    usable_demos = []
    for index, pair in enumerate(demos):
        errors = self_check(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} is outside the rule domain: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the first-symmetric rule")
            continue
        usable_demos.append(pair)

    query_errors = self_check(query.get("input"))
    if query_errors:
        reasons.append("query is outside the rule domain: " + "; ".join(query_errors))
        return reasons
    query_answer = rule_mirror(query["input"])
    if query.get("output") != query_answer:
        reasons.append("query label disagrees with the first-symmetric rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in usable_demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons
