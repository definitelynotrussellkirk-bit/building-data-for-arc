"""Generator for 5d59b75cb58e — add the main-diagonal transpose.

Every nonzero input cell is preserved and copied from ``(r, c)`` to ``(c, r)``.
The public examples happen to place every source below the main diagonal, so
normal lessons deliberately rotate through lower-only, upper-only, and mixed
source layouts.  That schedule refutes the tempting but wrong shortcut
"copy only the lower triangle into the upper triangle".
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5d59b75cb58e"
TASK_ID = "5d59b75cb58e"
VERSION = "3.0.0"
RULE_HASH = "2b970065d6a3"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a square zero-background grid, preserve every nonzero cell and add a "
    "same-colored copy at its main-diagonal transpose position (r, c) -> "
    "(c, r). Sources may lie below the diagonal, above it, or on both sides; "
    "the rule is bidirectional transpose-add, not a one-triangle copy rule."
)

INVARIANTS = [
    "the grid is square with background color 0",
    "two or three distinct colors each form one 4-connected off-diagonal blob",
    "no source cell or source blob is already occupied at its transpose location",
    "at least one blob is non-rectangular, so copying a bounding box is wrong",
    "the output preserves the input and adds each cell's same-colored transpose",
]

AXES = {
    "side": {
        "type": "int",
        "default": "difficulty-weighted canonical anchors",
        "valid": "8..12",
        "doc": "Square canvas side length.",
    },
    "n_blobs": {
        "type": "int",
        "default": "difficulty-weighted 2 or 3",
        "valid": "2..3",
        "doc": "Number of uniquely colored connected source blobs.",
    },
    "blob_size": {
        "type": "int",
        "default": "difficulty-weighted 3..5",
        "valid": "3..5",
        "doc": "Exact cell count of every generated source blob.",
    },
    "source_sides": {
        "type": "str",
        "default": "three-slot lower|upper|both teaching schedule",
        "valid": "lower|upper|both",
        "doc": "Which side(s) of the main diagonal contain source blobs.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
SCHEDULE_PROFILES = ("lower", "upper", "both")

_BAND_DEFAULTS = {
    "easy": {
        "side": (8, 8, 9, 10),
        "n_blobs": (2, 2, 2, 3),
        "blob_size": (3, 3, 4),
    },
    "medium": {
        "side": (8, 9, 9, 10, 11),
        "n_blobs": (2, 2, 3),
        "blob_size": (3, 4, 4, 5),
    },
    "hard": {
        "side": (8, 9, 10, 11, 12),
        "n_blobs": (2, 3, 3),
        "blob_size": (4, 4, 5),
    },
}

_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_sample_index(sample_index: Any) -> None:
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every consecutive three-example window contains all source-side modes."""
    del seed, difficulty
    _validate_sample_index(sample_index)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    _validate_sample_index(sample_index)
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _draw_int_axis(ctx, overrides, name: str, defaults: tuple[int, ...], lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return int(ctx.draw_choice(name, defaults))


def _normalize_shape(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape_variants(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    for base in _BASE_SHAPES[size]:
        for reflect in (False, True):
            for turns in range(4):
                transformed: list[tuple[int, int]] = []
                for r, c in base:
                    x, y = r, (-c if reflect else c)
                    for _ in range(turns):
                        x, y = y, -x
                    transformed.append((x, y))
                variants.add(_normalize_shape(transformed))
    return tuple(sorted(variants))


_SHAPE_VARIANTS = {size: _shape_variants(size) for size in _BASE_SHAPES}


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _placements(
    side: int,
    shape: tuple[tuple[int, int], ...],
    triangle: str,
) -> list[frozenset[tuple[int, int]]]:
    sh, sw = _shape_dims(shape)
    out: list[frozenset[tuple[int, int]]] = []
    for r0 in range(side - sh + 1):
        for c0 in range(side - sw + 1):
            cells = frozenset((r0 + r, c0 + c) for r, c in shape)
            if triangle == "lower" and all(r > c for r, c in cells):
                out.append(cells)
            elif triangle == "upper" and all(r < c for r, c in cells):
                out.append(cells)
    return out


def _source_triangles(profile: str, n_blobs: int, rng) -> list[str]:
    if profile == "lower":
        return ["lower"] * n_blobs
    if profile == "upper":
        return ["upper"] * n_blobs
    triangles = ["lower", "upper"]
    while len(triangles) < n_blobs:
        triangles.append(rng.choice(("lower", "upper")))
    rng.shuffle(triangles)
    return triangles


def _place_blobs(
    side: int,
    n_blobs: int,
    blob_size: int,
    source_sides: str,
    rng,
) -> list[frozenset[tuple[int, int]]]:
    triangles = _source_triangles(source_sides, n_blobs, rng)
    candidate_pools: list[list[frozenset[tuple[int, int]]]] = []
    for triangle in triangles:
        pool: list[frozenset[tuple[int, int]]] = []
        for shape in _SHAPE_VARIANTS[blob_size]:
            pool.extend(_placements(side, shape, triangle))
        rng.shuffle(pool)
        candidate_pools.append(pool)

    placed: list[frozenset[tuple[int, int]]] = []
    occupied: set[tuple[int, int]] = set()
    reserved: set[tuple[int, int]] = set()

    def backtrack(index: int) -> bool:
        if index == n_blobs:
            return True
        for cells in candidate_pools[index]:
            mirrors = {(c, r) for r, c in cells}
            if cells & (occupied | reserved):
                continue
            if mirrors & (occupied | cells):
                continue
            occupied.update(cells)
            reserved.update(mirrors)
            placed.append(cells)
            if backtrack(index + 1):
                return True
            placed.pop()
            occupied.difference_update(cells)
            reserved.difference_update(mirrors)
        return False

    if not backtrack(0):
        raise ValueError(
            "could not place requested non-overlapping off-diagonal blobs: "
            f"side={side}, n_blobs={n_blobs}, blob_size={blob_size}, "
            f"source_sides={source_sides}"
        )
    return placed


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        return []
    rows: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)):
            return []
        rows.append(list(row))
    return rows


def _components_for_color(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        component = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
                    component.append(nxt)
        components.append(component)
    return components


def _color_components(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    colors = sorted({value for row in grid for value in row if value != 0})
    result: dict[int, list[tuple[int, int]]] = {}
    for color in colors:
        components = _components_for_color(grid, color)
        if len(components) == 1:
            result[color] = components[0]
    return result


def _bbox_area(cells: list[tuple[int, int]]) -> int:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid task grammar, including all three canonical inputs."""
    del difficulty, meta
    rows = _coerce_grid(grid)
    if not rows or not rows[0]:
        return ["grid must be a nonempty rectangular list of rows"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return ["grid must be rectangular"]

    errors: list[str] = []
    side = len(rows)
    if width != side:
        errors.append(f"grid must be square, got {side}x{width}")
        return errors
    if not 8 <= side <= 12:
        errors.append(f"grid side must be 8..12, got {side}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC colors at {invalid[:3]}")
        return errors

    colors = sorted({value for row in rows for value in row if value != 0})
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected two or three nonzero blob colors, got {len(colors)}")
        return errors

    components: dict[int, list[tuple[int, int]]] = {}
    for color in colors:
        found = _components_for_color(rows, color)
        if len(found) != 1:
            errors.append(f"color {color} must form exactly one 4-connected blob")
            continue
        cells = found[0]
        components[color] = cells
        if not 2 <= len(cells) <= 5:
            errors.append(f"color {color} blob size must be 2..5, got {len(cells)}")
        if any(r == c for r, c in cells):
            errors.append(f"color {color} touches the main diagonal")
        if not (all(r > c for r, c in cells) or all(r < c for r, c in cells)):
            errors.append(f"color {color} must lie wholly on one side of the diagonal")

    nonzero = {(r, c) for r in range(side) for c in range(side) if rows[r][c] != 0}
    overlaps = sorted((r, c) for r, c in nonzero if (c, r) in nonzero)
    if overlaps:
        errors.append(
            "source cells may not already occupy transpose partners; first "
            f"overlap at {overlaps[0]}"
        )

    if components and not any(len(cells) < _bbox_area(cells) for cells in components.values()):
        errors.append("at least one blob must be non-rectangular inside its bounding box")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact public axis from a generated input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    rows = _coerce_grid(grid)
    components = _color_components(rows)
    sizes = {len(cells) for cells in components.values()}
    if len(sizes) != 1:
        raise ValueError("generated exact blob_size axis is not recoverable")
    has_lower = any(r > c for cells in components.values() for r, c in cells)
    has_upper = any(r < c for cells in components.values() for r, c in cells)
    source_sides = "both" if has_lower and has_upper else ("lower" if has_lower else "upper")
    return {
        "side": len(rows),
        "n_blobs": len(components),
        "blob_size": next(iter(sizes)),
        "source_sides": source_sides,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = {key: value for key, value in overrides.items() if value is not None}
    _validate_call(seed, sample_index, difficulty, overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    defaults = _BAND_DEFAULTS[band]
    side = _draw_int_axis(ctx, overrides, "side", defaults["side"], 8, 12)
    n_blobs = _draw_int_axis(ctx, overrides, "n_blobs", defaults["n_blobs"], 2, 3)
    blob_size = _draw_int_axis(ctx, overrides, "blob_size", defaults["blob_size"], 3, 5)
    if "source_sides" in overrides:
        source_sides = ctx.draw_choice("source_sides", SCHEDULE_PROFILES)
    else:
        source_sides = ctx.draw_choice(
            "source_sides", (schedule_profile(seed, sample_index, band),)
        )

    layout_rng = ctx.draw_rng("layout")
    blobs = _place_blobs(side, n_blobs, blob_size, source_sides, layout_rng)
    colors = ctx.draw_distinct_colors("colors", n=n_blobs, exclude={0})
    grid = full_grid(side, side, 0)
    for color, cells in zip(colors, blobs, strict=True):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("generated invalid transpose-add scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "side": side,
        "n_blobs": n_blobs,
        "blob_size": blob_size,
        "source_sides": source_sides,
    }
    if observed != expected:
        raise ValueError(f"rendered axes disagree with keyed draws: {observed} != {expected}")
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Python analysis mirror only; the Racket rule remains output authority."""
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                out[c][r] = value
    return out


def _transpose_replace(grid):
    rows = _coerce_grid(grid)
    return [[rows[c][r] for c in range(len(rows))] for r in range(len(rows))]


def _one_triangle_add(grid, source: str):
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for r in range(len(rows)):
        for c in range(len(rows)):
            if rows[r][c] == 0:
                continue
            if (source == "lower" and r > c) or (source == "upper" and r < c):
                out[c][r] = rows[r][c]
    return out


def _lower_only_add(grid):
    return _one_triangle_add(grid, "lower")


def _upper_only_add(grid):
    return _one_triangle_add(grid, "upper")


def _anti_diagonal_add(grid):
    rows = _coerce_grid(grid)
    n = len(rows)
    out = [row[:] for row in rows]
    for r in range(n):
        for c in range(n):
            if rows[r][c] != 0:
                out[n - 1 - c][n - 1 - r] = rows[r][c]
    return out


def _vertical_add(grid):
    rows = _coerce_grid(grid)
    n = len(rows)
    out = [row[:] for row in rows]
    for r in range(n):
        for c in range(n):
            if rows[r][c] != 0:
                out[r][n - 1 - c] = rows[r][c]
    return out


def _horizontal_add(grid):
    rows = _coerce_grid(grid)
    n = len(rows)
    out = [row[:] for row in rows]
    for r in range(n):
        for c in range(n):
            if rows[r][c] != 0:
                out[n - 1 - r][c] = rows[r][c]
    return out


def _modal_color_only(grid):
    rows = _coerce_grid(grid)
    counts = Counter(value for row in rows for value in row if value != 0)
    modal = min((-count, color) for color, count in counts.items())[1]
    out = [row[:] for row in rows]
    for r in range(len(rows)):
        for c in range(len(rows)):
            if rows[r][c] == modal:
                out[c][r] = modal
    return out


def _bbox_transpose_add(grid):
    rows = _coerce_grid(grid)
    out = [row[:] for row in rows]
    for color, cells in _color_components(rows).items():
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[c][r] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "lower_only_add": _lower_only_add,
    "upper_only_add": _upper_only_add,
    "transpose_replace": _transpose_replace,
    "anti_diagonal_add": _anti_diagonal_add,
    "vertical_add": _vertical_add,
    "horizontal_add": _horizontal_add,
    "modal_color_only": _modal_color_only,
    "bbox_transpose_add": _bbox_transpose_add,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"lower_only_add": _lower_only_add}


def _analysis(grid) -> dict[str, Any]:
    rows = _coerce_grid(grid)
    errors = self_check(rows)
    if errors:
        return {"errors": errors}
    components = _color_components(rows)
    has_lower = any(r > c for cells in components.values() for r, c in cells)
    has_upper = any(r < c for cells in components.values() for r, c in cells)
    official = rule_mirror(rows)
    return {
        "errors": [],
        "lower_sources": has_lower and not has_upper,
        "upper_sources": has_upper and not has_lower,
        "both_sides": has_lower and has_upper,
        "nonrectangular_blob": any(
            len(cells) < _bbox_area(cells) for cells in components.values()
        ),
        "multicolor": len(components) >= 2,
        "rival_disagreements": {
            name: rival(rows) != official for name, rival in SEMANTIC_RIVALS.items()
        },
    }


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid):
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])

    return predicate


SEMANTIC_WITNESSES = {
    "lower_sources": _witness("lower_sources"),
    "upper_sources": _witness("upper_sources"),
    "both_sides": _witness("both_sides"),
    "nonrectangular_blob": _witness("nonrectangular_blob"),
    "multicolor": _witness("multicolor"),
}
WITNESS_RIVALS = {
    "lower_sources": ["upper_only_add"],
    "upper_sources": ["lower_only_add"],
    "both_sides": ["lower_only_add", "upper_only_add"],
    "nonrectangular_blob": ["bbox_transpose_add"],
    "multicolor": ["modal_color_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson on which a named plausible wrong rule survives."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits_demos and rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a "
                    "different query output"
                )
        except Exception as exc:
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
