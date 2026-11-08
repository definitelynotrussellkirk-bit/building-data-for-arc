"""Constructive sampler for XOR of two top-left-normalized shapes.

Every generated input contains exactly one connected blue object and one
connected red object.  Their normalized shapes overlap, and each also has at
least one exclusive cell, so the labeled output visibly distinguishes XOR from
union, intersection, and either one-shape shortcut.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "094e0794786c"
TASK_ID = GENERATOR_ID
RULE_HASH = "e94c733a8465"
VERSION = "3.0.0"
SUMMARY = (
    "Place one connected color-1 object and one connected color-2 object on a "
    "zero background. Crop and top-left-normalize both objects, then output "
    "color 8 exactly on their symmetric difference. Every sample contains a "
    "normalized overlap plus exclusive cells from both objects."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input palette is exactly a zero background plus colors 1 and 2",
    "each colored object is a single 4-connected polyomino with 3..7 cells",
    "the two global objects are separated by at least one background cell",
    "after top-left normalization the objects overlap and each contributes exclusive cells",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 8..12, favoring canonical heights 8 and 9",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 9..14, favoring canonical widths 9 and 10",
        "valid": "9..14",
    },
    "n_cells_1": {
        "type": "int",
        "default": "difficulty-weighted 3..7 with full support in every band",
        "valid": "3..7",
    },
    "n_cells_2": {
        "type": "int",
        "default": "difficulty-weighted 3..7 with full support in every band",
        "valid": "3..7",
    },
}

# Every Cartesian product of the advertised axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells):
    """Return an immutable top-left-normalized cell set."""
    cells = tuple(cells)
    if not cells:
        return tuple()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _bbox(shape):
    if not shape:
        return 0, 0
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


@lru_cache(maxsize=5)
def _polyominoes(size):
    """Enumerate fixed 4-connected polyominoes inside a 4x4 bounding box.

    Growth plus translation-normalization is finite and deterministic. Keeping
    orientations distinct supplies broad shape diversity without rejection
    loops or disconnected/sparse impostors.
    """
    if not 3 <= size <= 7:
        raise ValueError(f"polyomino size {size} outside [3, 7]")
    shapes = {((0, 0),)}
    for _ in range(1, size):
        grown = set()
        for shape in shapes:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in _NEIGHBORS:
                    point = (r + dr, c + dc)
                    if point in occupied:
                        continue
                    candidate = _normalize((*occupied, point))
                    h, w = _bbox(candidate)
                    if h <= 4 and w <= 4:
                        grown.add(candidate)
        shapes = grown
    return tuple(sorted(shapes))


def _distinguishes_shortcuts(first, second):
    a, b = set(first), set(second)
    return bool(a & b and a - b and b - a)


def _choose_shapes(ctx, n_cells_1, n_cells_2):
    """Choose a finite, guaranteed-compatible normalized shape pair."""
    first_bank = _polyominoes(n_cells_1)
    second_bank = _polyominoes(n_cells_2)
    start = ctx.draw_rng("shape_1").randrange(len(first_bank))
    for offset in range(len(first_bank)):
        first = first_bank[(start + offset) % len(first_bank)]
        compatible = tuple(
            second
            for second in second_bank
            if _distinguishes_shortcuts(first, second)
        )
        if compatible:
            second = ctx.draw_rng("shape_2").choice(compatible)
            return first, second
    raise RuntimeError("finite polyomino bank has no distinguishing shape pair")


def _origins(h, w, shape):
    shape_h, shape_w = _bbox(shape)
    return tuple(
        (r, c)
        for r in range(h - shape_h + 1)
        for c in range(w - shape_w + 1)
    )


def _translated(shape, origin):
    return {(origin[0] + r, origin[1] + c) for r, c in shape}


def _choose_placements(ctx, h, w, first, second):
    """Place both objects with Manhattan distance greater than one.

    The search is over finite origin sets. It does not silently shorten shapes,
    retry a capped random loop, or fall back to a different axis assignment.
    """
    first_origins = _origins(h, w, first)
    second_origins = _origins(h, w, second)
    start = ctx.draw_rng("position_1").randrange(len(first_origins))
    for offset in range(len(first_origins)):
        origin_1 = first_origins[(start + offset) % len(first_origins)]
        cells_1 = _translated(first, origin_1)
        blocked = set(cells_1)
        for r, c in cells_1:
            blocked.update((r + dr, c + dc) for dr, dc in _NEIGHBORS)
        feasible_2 = tuple(
            origin
            for origin in second_origins
            if _translated(second, origin).isdisjoint(blocked)
        )
        if feasible_2:
            origin_2 = ctx.draw_rng("position_2").choice(feasible_2)
            return origin_1, origin_2
    raise RuntimeError("advertised grid cannot place two separated objects")


def _draw_axis(ctx, name, lo, hi, favored):
    # Duplicates are intentional weights; every valid value remains available
    # to overrides and has nonzero default probability in every difficulty.
    return ctx.draw_choice(name, tuple(range(lo, hi + 1)) + tuple(favored))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_axis(ctx, "grid_h", 8, 12, (8,) * 16 + (9,) * 16)
    w = _draw_axis(ctx, "grid_w", 9, 14, (9,) * 16 + (10,) * 16)

    if difficulty == "easy":
        size_weights = (3,) * 8 + (4,) * 6 + (5,) * 2
    elif difficulty == "hard":
        size_weights = (5,) * 2 + (6,) * 6 + (7,) * 8
    else:
        size_weights = (3,) * 2 + (4,) * 5 + (5,) * 7 + (6,) * 5 + (7,) * 2
    n_cells_1 = _draw_axis(ctx, "n_cells_1", 3, 7, size_weights)
    n_cells_2 = _draw_axis(ctx, "n_cells_2", 3, 7, tuple(reversed(size_weights)))

    first, second = _choose_shapes(ctx, n_cells_1, n_cells_2)
    origin_1, origin_2 = _choose_placements(ctx, h, w, first, second)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in _translated(first, origin_1):
        grid[r][c] = 1
    for r, c in _translated(second, origin_2):
        grid[r][c] = 2
    return grid


def _color_cells(grid, color):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def observe_overrides(grid):
    """Recover all advertised exact axes from the returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells_1": len(_color_cells(grid, 1)),
        "n_cells_2": len(_color_cells(grid, 2)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["expected a nonempty rectangular grid"]
    if any(type(value) is not int for row in grid for value in row):
        return ["all cells must be integer colors"]

    errors = []
    h, w = len(grid), width
    if not 8 <= h <= 12:
        errors.append(f"grid height {h} outside [8, 12]")
    if not 9 <= w <= 14:
        errors.append(f"grid width {w} outside [9, 14]")

    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 2}:
        errors.append(f"input contains colors outside 0,1,2: {sorted(palette - {0, 1, 2})}")

    first = _color_cells(grid, 1)
    second = _color_cells(grid, 2)
    for name, cells in (("color-1", first), ("color-2", second)):
        if not 3 <= len(cells) <= 7:
            errors.append(f"{name} object must contain 3..7 cells, found {len(cells)}")
        if cells and _component_count(cells) != 1:
            errors.append(f"{name} cells must form exactly one 4-connected object")

    if first and second:
        distance = min(
            abs(r1 - r2) + abs(c1 - c2)
            for r1, c1 in first
            for r2, c2 in second
        )
        if distance <= 1:
            errors.append("the two colored objects must be separated by background")

        norm_1 = set(_normalize(first))
        norm_2 = set(_normalize(second))
        if not norm_1 & norm_2:
            errors.append("normalized objects must overlap")
        if not norm_1 - norm_2:
            errors.append("color-1 must contribute an exclusive normalized cell")
        if not norm_2 - norm_1:
            errors.append("color-2 must contribute an exclusive normalized cell")
    return errors


def strict_canonical_like(grid):
    """Accept exactly the lawful two-object manifold used by this sampler."""
    return self_check(grid)


def _shape_data(grid):
    first = set(_normalize(_color_cells(grid, 1)))
    second = set(_normalize(_color_cells(grid, 2)))
    out_h = max(_bbox(first)[0], _bbox(second)[0])
    out_w = max(_bbox(first)[1], _bbox(second)[1])
    return first, second, out_h, out_w


def _render(cells, h, w):
    if not cells:
        return [[0]]
    return [
        [8 if (r, c) in cells else 0 for c in range(w)]
        for r in range(h)
    ]


def _intended_output(grid):
    """Independent Python mirror used only for validation and rival probes."""
    first, second, out_h, out_w = _shape_data(grid)
    return _render(first ^ second, out_h, out_w)


def _union_output(grid):
    first, second, out_h, out_w = _shape_data(grid)
    return _render(first | second, out_h, out_w)


def _first_shape_output(grid):
    first, _second, out_h, out_w = _shape_data(grid)
    return _render(first, out_h, out_w)


def _second_shape_output(grid):
    _first, second, out_h, out_w = _shape_data(grid)
    return _render(second, out_h, out_w)


def _intersection_output(grid):
    first, second, out_h, out_w = _shape_data(grid)
    return _render(first & second, out_h, out_w)


def _normalized_overlap(grid):
    first, second, _h, _w = _shape_data(grid)
    return bool(first & second)


def _both_shapes_contribute(grid):
    first, second, _h, _w = _shape_data(grid)
    return bool(first - second and second - first)


SEMANTIC_WITNESSES = {
    "normalized_overlap": _normalized_overlap,
    "both_shapes_contribute": _both_shapes_contribute,
}
SEMANTIC_RIVALS = {
    "normalized_union": _union_output,
    "first_shape_only": _first_shape_output,
    "second_shape_only": _second_shape_output,
    "normalized_intersection": _intersection_output,
}
WITNESS_RIVALS = {
    "normalized_overlap": ["normalized_union"],
    "both_shapes_contribute": [
        "first_shape_only",
        "second_shape_only",
        "normalized_intersection",
    ],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject lessons where a declared plausible wrong rule remains viable."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson requires at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    errors = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output grids")
            continue
        findings = self_check(pair["input"])
        if findings:
            errors.append(f"pair {index} input is unlawful: {'; '.join(findings)}")
            continue
        if _intended_output(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output disagrees with normalized XOR")
    if errors:
        return errors

    expected_query = _intended_output(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != expected_query:
            errors.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return errors
